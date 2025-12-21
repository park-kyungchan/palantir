
"""
Orion ODA V3.0 - Database Connection Manager (Async SQLAlchemy)
============================================================
Provides SQLAlchemy Async Engine and Session Factory.

Key Features:
- **Async Engine**: Non-blocking I/O with `aiosqlite`.
- **WAL Mode**: Enforced via event listeners for high concurrency.
- **Session Management**: Async context manager for transactional scope.
- **Schema Initialization**: Auto-recreates tables via `Base.metadata`.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine import Engine

# Import Base for schema creation
from scripts.ontology.storage.models import Base
from scripts.ontology.storage.orm import AsyncOntologyObject 

logger = logging.getLogger(__name__)

# Enforce WAL Mode on SQLite Connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

class Database:
    """
    SQLAlchemy Async Database Manager.
    Does NOT use manual SQL migrations anymore; relies on ORM Metadata.
    """
    
    def __init__(self, url: str | Path):
        # Convert path to async sqlite url if needed
        if isinstance(url, Path) or (isinstance(url, str) and not url.startswith("sqlite")):
             self.url = f"sqlite+aiosqlite:///{url}"
        else:
             self.url = url
             
        self.engine: AsyncEngine = create_async_engine(
            self.url,
            echo=False,  # Set to True for SQL debugging
            future=True
        )
        
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
        self._initialized = False

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        if self._initialized: return
        
        async with self.engine.begin() as conn:
            # In production, use Alembic. For ODA V3 Prototype, create_all is acceptable.
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info(f"Database Schema Initialized at {self.url}")
        self._initialized = True

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

# Global Singleton
_db_instance: Database | None = None

async def initialize_database(path: Path | str | None = None) -> Database:
    global _db_instance
    p = path or "/home/palantir/orion-orchestrator-v2/data/ontology.db"
    db = Database(p)
    await db.initialize()
    _db_instance = db
    return db

def get_database() -> Database:
    """Get the global database instance."""
    if _db_instance is None:
        # Fallback for scripts usage? Or raise?
        # For now, safe default path if not initialized is risky but convenient?
        # Better to raise if strict.
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return _db_instance
