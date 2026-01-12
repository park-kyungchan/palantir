
"""
Orion ODA V3.0 - Database Connection Manager (Async SQLAlchemy)
============================================================
Provides SQLAlchemy Async Engine and Session Factory.

Key Features:
- **Async Engine**: Non-blocking I/O with `aiosqlite`.
- **WAL Mode**: Enforced via event listeners for high concurrency.
- **Session Management**: Async context manager for transactional scope.
- **Schema Initialization**: Auto-recreates tables via `Base.metadata`.
- **Connection Pooling**: Configurable pool_size, max_overflow, pool_recycle.
"""

from __future__ import annotations

import logging
import os
import warnings
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncGenerator, Union

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine import Engine

# Import Base for schema creation
from lib.oda.ontology.storage.models import Base
from lib.oda.ontology.storage.orm import AsyncOntologyObject 

from lib.oda.asyncio_compat import ensure_threadsafe_wakeup

logger = logging.getLogger(__name__)

ensure_threadsafe_wakeup()


# Enforce WAL Mode on SQLite Connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


# =============================================================================
# DATABASE CONFIGURATION (New in V3.1)
# =============================================================================

@dataclass
class DatabaseConfig:
    """
    Database connection pool configuration.
    
    Aligns with SQLAlchemy QueuePool best practices:
    - pool_size: Base number of persistent connections (default: 5)
    - max_overflow: Extra connections allowed during bursts (default: 10)
    - pool_recycle: Recycle connections after N seconds to prevent stale (default: 3600)
    - pool_pre_ping: Test connection health before checkout (default: True)
    - echo: Enable SQL query logging for debugging (default: False)
    
    Usage:
        config = DatabaseConfig(url="/path/to/db.sqlite", pool_size=10)
        db = Database(config)
    """
    url: Union[str, Path]
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600  # 1 hour
    pool_pre_ping: bool = True
    echo: bool = False


class Database:
    """
    SQLAlchemy Async Database Manager.
    Does NOT use manual SQL migrations anymore; relies on ORM Metadata.
    
    Accepts either a path/URL string or a DatabaseConfig for full control.
    """
    
    def __init__(self, url_or_config: Union[str, Path, DatabaseConfig]):
        # Handle both legacy (path only) and new (config) initialization
        if isinstance(url_or_config, DatabaseConfig):
            config = url_or_config
            raw_url = config.url
        else:
            # Legacy: simple path/url, use defaults
            config = DatabaseConfig(url=url_or_config)
            raw_url = url_or_config
        
        # Convert path to async sqlite url if needed
        if isinstance(raw_url, Path) or (isinstance(raw_url, str) and not raw_url.startswith("sqlite")):
            self.url = f"sqlite+aiosqlite:///{raw_url}"
        else:
            self.url = str(raw_url)
        
        # Create engine with pool configuration
        # Note: In-memory SQLite uses StaticPool and doesn't accept pool_size/max_overflow
        is_memory_db = ":memory:" in self.url or raw_url == ":memory:"
        
        if is_memory_db:
            # In-memory DB: StaticPool with no pool params
            from sqlalchemy.pool import StaticPool
            self.engine: AsyncEngine = create_async_engine(
                self.url,
                echo=config.echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            # File-based DB: QueuePool with full config
            self.engine: AsyncEngine = create_async_engine(
                self.url,
                echo=config.echo,
                pool_size=config.pool_size,
                max_overflow=config.max_overflow,
                pool_recycle=config.pool_recycle,
                pool_pre_ping=config.pool_pre_ping,
            )
        
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        self._initialized = False
        self._config = config  # Store for introspection

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        if self._initialized: return

        if os.environ.get("ORION_DB_INIT_MODE") == "sync":
            from sqlalchemy import create_engine
            sync_url = self.url.replace("+aiosqlite", "")
            engine = create_engine(sync_url)
            Base.metadata.create_all(bind=engine)
            engine.dispose()
            logger.info(f"Database Schema Initialized (sync) at {sync_url}")
            self._initialized = True
            return

        async with self.engine.begin() as conn:
            # In production, use Alembic. For ODA V3 Prototype, create_all is acceptable.
            await conn.run_sync(Base.metadata.create_all)

        logger.info(f"Database Schema Initialized at {self.url}")
        self._initialized = True

    async def dispose(self) -> None:
        """Dispose the underlying engine and close all connections."""
        await self.engine.dispose()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Transactional Scope.
        Commits on exit, Rolls back on exception.
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self) -> bool:
        try:
             async with self.transaction() as session:
                 await session.execute(text("SELECT 1"))
             return True
        except Exception as e:
            logger.error(f"Health Check Failed: {e}")
            return False


# =============================================================================
# DATABASE MANAGER (Test Isolation Support)
# =============================================================================

class DatabaseManager:
    """
    Database Instance Manager with Context-Local Support.

    Provides:
    1. Default singleton for production use
    2. Context-local override for test isolation
    3. Backward-compatible with existing get_database()/initialize_database() API

    Usage in Tests:
        @pytest.fixture
        async def isolated_db(tmp_path):
            db = Database(tmp_path / "test.db")
            await db.initialize()
            token = DatabaseManager.set_context(db)
            try:
                yield db
            finally:
                DatabaseManager.reset_context(token)
    """
    _default: Database | None = None
    _context_db: ContextVar[Database | None] = ContextVar("orion_db_context", default=None)

    @classmethod
    async def initialize(cls, path: Path | str | None = None) -> Database:
        """
        Initialize the default database instance.

        Args:
            path: Optional explicit path. Falls back to ORION_DB_PATH env var,
                  then to default hardcoded path.

        Returns:
            Initialized Database instance
        """
        from lib.oda.paths import get_db_path
        p = path or os.getenv("ORION_DB_PATH") or str(get_db_path())
        db = Database(p)
        await db.initialize()
        cls._default = db
        return db

    @classmethod
    def get(cls) -> Database:
        """
        Get database instance.

        Priority:
        1. Context-local database (if set)
        2. Default singleton

        Raises:
            RuntimeError: If no database is available
        """
        # Check context-local first
        ctx_db = cls._context_db.get()
        if ctx_db is not None:
            return ctx_db

        # Fallback to default
        if cls._default is None:
            raise RuntimeError(
                "Database not initialized. Call initialize_database() or "
                "DatabaseManager.initialize() first."
            )
        return cls._default

    @classmethod
    def set_context(cls, db: Database) -> Token[Database | None]:
        """
        Set context-local database for test isolation.

        Args:
            db: Database instance to use in current context

        Returns:
            Token for resetting the context
        """
        return cls._context_db.set(db)

    @classmethod
    def reset_context(cls, token: Token[Database | None]) -> None:
        """
        Reset context-local database using token from set_context().

        Args:
            token: Token returned from set_context()
        """
        cls._context_db.reset(token)

    @classmethod
    def set_default(cls, db: Database | None) -> None:
        """
        Set or clear the default database instance.

        Args:
            db: Database instance or None to clear
        """
        cls._default = db


# =============================================================================
# LEGACY API (Backward Compatibility)
# =============================================================================

# Note: _db_instance is kept for direct access compatibility but DatabaseManager is preferred
_db_instance: Database | None = None


async def initialize_database(path: Path | str | None = None) -> Database:
    """
    Initialize the global database instance.

    This is the legacy API - consider using DatabaseManager.initialize() directly.
    """
    global _db_instance
    db = await DatabaseManager.initialize(path)
    _db_instance = db  # Keep sync with legacy global
    return db


def get_database() -> Database:
    """
    Get the global database instance.

    .. deprecated::
        Use DatabaseManager.get() instead. This function will be removed in V4.0.
    
    Uses DatabaseManager internally for context-local support.
    """
    warnings.warn(
        "get_database() is deprecated. Use DatabaseManager.get() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    global _db_instance
    try:
        db = DatabaseManager.get()
        _db_instance = db  # Keep sync with legacy global
        return db
    except RuntimeError:
        # Backward compatibility: check legacy global
        if _db_instance is not None:
            return _db_instance
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
