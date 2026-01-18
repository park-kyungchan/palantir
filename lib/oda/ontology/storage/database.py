"""
ODA Storage - Async Database Wrapper
===================================

This module provides a small SQLAlchemy AsyncEngine wrapper used throughout the
codebase (Actions, Repositories, API dependencies, and tests).

Design goals:
- Simple async transaction context manager (`Database.transaction`)
- Centralized global/context-local access (`DatabaseManager`)
- SQLite-first (Foundry-like local persistence for dev & tests)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from contextvars import ContextVar, Token
from pathlib import Path
from typing import AsyncGenerator, Optional, Union

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
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
    if db_path_str != ":memory:":
        # Normalize filesystem paths, but leave SQLAlchemy URLs intact.
        if "://" not in db_path_str:
            return str(Path(db_path_str).expanduser().resolve())
    return db_path_str


def _make_sqlalchemy_url(db_path: str) -> str:
    # Allow passing a full SQLAlchemy URL.
    if "://" in db_path:
        return db_path
    if db_path == ":memory:":
        return "sqlite+aiosqlite:///:memory:"
    return f"sqlite+aiosqlite:///{db_path}"


class Database:
    """
    Async SQLAlchemy database wrapper.

    The codebase assumes:
    - `await db.initialize()` is called before use
    - `db.engine` is an AsyncEngine
    - `db.session_factory()` returns an AsyncSession
    - `async with db.transaction() as session:` provides a transactional session
    """

    def __init__(self, db_path: Optional[DbPath] = None) -> None:
        self.db_path: str = _normalize_db_path(db_path)
        self.url: str = _make_sqlalchemy_url(self.db_path)

        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    async def initialize(self) -> None:
        if self.engine is not None and self.session_factory is not None:
            return

        engine_kwargs = {
            "future": True,
            "echo": False,
        }

        if self.db_path == ":memory:":
            engine_kwargs.update(
                {
                    "connect_args": {"check_same_thread": False},
                    "poolclass": StaticPool,
                }
            )

        self.engine = create_async_engine(self.url, **engine_kwargs)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False,
        )

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
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """
    Global/context-local database registry.

    - `initialize()` configures the global default database (async)
    - `get()` returns the context-local DB if set, else the default DB
    - `set_context()` temporarily overrides the DB (useful for tests)
    """

    _context_db: ContextVar[Optional[Database]] = ContextVar("oda_context_db", default=None)
    _default: Optional[Database] = None

    @classmethod
    async def initialize(cls, db_path: Optional[DbPath] = None) -> Database:
        if cls._default is None:
            cls._default = Database(db_path)
        elif db_path is not None:
            # Reconfigure default if an explicit path is provided.
            cls._default = Database(db_path)

        await cls._default.initialize()
        return cls._default

    @classmethod
    def get(cls) -> Database:
        ctx_db = cls._context_db.get()
        if ctx_db is not None:
            return ctx_db
        if cls._default is None:
            raise RuntimeError(
                "DatabaseManager is not initialized. Call await initialize_database() first."
            )
        return cls._default

    @classmethod
    def set_context(cls, db: Database) -> Token[Optional[Database]]:
        return cls._context_db.set(db)

    @classmethod
    def reset_context(cls, token: Token[Optional[Database]]) -> None:
        cls._context_db.reset(token)


async def initialize_database(db_path: Optional[DbPath] = None) -> Database:
    """Backwards-compatible helper for initializing the global database."""
    return await DatabaseManager.initialize(db_path=db_path)


def get_database() -> Database:
    """Backwards-compatible helper for fetching the active database."""
    return DatabaseManager.get()

