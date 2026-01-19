"""
ODA Storage - Async SQLAlchemy Database Wrapper
==============================================

Minimal async database wrapper used across the codebase:
- `Database`: manages AsyncEngine + AsyncSession factory
- `DatabaseManager`: provides global/context-local DB access for tests and runtime
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import AsyncGenerator, Optional, Union

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

DbPath = Union[str, Path]


def _project_root() -> Path:
    # lib/oda/ontology/storage/database.py -> project root
    return Path(__file__).resolve().parents[4]


def _normalize_db_path(db_path: Optional[DbPath]) -> str:
    if db_path is None:
        env_path = os.environ.get("ORION_DB_PATH")
        if env_path:
            db_path = env_path
        else:
            db_path = _project_root() / "relay.db"

    if isinstance(db_path, Path):
        return str(db_path.expanduser().resolve())

    db_path_str = str(db_path).strip()
    if db_path_str != ":memory:" and "://" not in db_path_str:
        return str(Path(db_path_str).expanduser().resolve())
    return db_path_str


def _make_sqlalchemy_url(db_path: str) -> str:
    if "://" in db_path:
        return db_path
    if db_path == ":memory:":
        return "sqlite+aiosqlite:///:memory:"
    return f"sqlite+aiosqlite:///{db_path}"


class Database:
    def __init__(self, db_path: Optional[DbPath] = None) -> None:
        self.db_path: str = _normalize_db_path(db_path)
        self.url: str = _make_sqlalchemy_url(self.db_path)

        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def initialize(self) -> None:
        if self.engine is not None and self.session_factory is not None:
            return

        engine_kwargs = {"future": True, "echo": False, "connect_args": {"check_same_thread": False}}

        if self.db_path == ":memory:":
            engine_kwargs.update(
                {
                    "poolclass": StaticPool,
                }
            )

        self.engine = create_async_engine(self.url, **engine_kwargs)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )

        # SQLite tuning + schema initialization (migrations-lite)
        # Ensure transaction ORM models are registered before schema creation.
        # Tests create a fresh database and then use the checkpoint system; the
        # checkpoints table must exist after `initialize()`.
        from lib.oda.transaction.checkpoint import CheckpointModel  # noqa: F401

        from lib.oda.ontology.storage.models import Base

        async with self.engine.begin() as conn:
            # WAL for concurrency (required by tests)
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.execute(text("PRAGMA synchronous=NORMAL;"))
            await conn.execute(text("PRAGMA foreign_keys=ON;"))

            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        if self.engine is None:
            return
        await self.engine.dispose()
        self.engine = None
        self.session_factory = None

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        if self.session_factory is None:
            raise RuntimeError("Database not initialized. Call await db.initialize() first.")

        session = self.session_factory()
        session_token = DatabaseManager._context_session.set(session)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            DatabaseManager._context_session.reset(session_token)
            await session.close()

    async def health_check(self) -> bool:
        """Lightweight connectivity check."""
        try:
            async with self.transaction() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False


class DatabaseManager:
    _context_db: ContextVar[Optional[Database]] = ContextVar("oda_context_db", default=None)
    _context_session: ContextVar[Optional[AsyncSession]] = ContextVar("oda_context_session", default=None)
    _default: Optional[Database] = None

    @classmethod
    async def initialize(cls, db_path: Optional[DbPath] = None) -> Database:
        if cls._default is None:
            cls._default = Database(db_path)
        elif db_path is not None:
            cls._default = Database(db_path)

        await cls._default.initialize()
        return cls._default

    @classmethod
    def get(cls) -> Database:
        ctx_db = cls._context_db.get()
        if ctx_db is not None:
            return ctx_db
        if cls._default is None:
            raise RuntimeError("DatabaseManager not initialized. Call await initialize_database() first.")
        return cls._default

    @classmethod
    def set_context(cls, db: Database) -> Token[Optional[Database]]:
        return cls._context_db.set(db)

    @classmethod
    def reset_context(cls, token: Token[Optional[Database]]) -> None:
        cls._context_db.reset(token)

    @classmethod
    def get_session(cls) -> Optional[AsyncSession]:
        return cls._context_session.get()


async def initialize_database(db_path: Optional[DbPath] = None) -> Database:
    return await DatabaseManager.initialize(db_path=db_path)


def get_database() -> Database:
    return DatabaseManager.get()
