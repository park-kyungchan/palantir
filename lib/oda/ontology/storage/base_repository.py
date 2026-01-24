"""
ODA Storage - Base Repository Primitives
======================================

Repositories should participate in an existing database transaction when one
is already active. This enables proper rollback semantics for higher-level
workflows (e.g., ActionRunner transactions).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from lib.oda.ontology.storage.database import Database, DatabaseManager


class TransactionalRepository:
    """
    Base repository that reuses an active AsyncSession when available.
    """

    def __init__(self, db: Database):
        self.db = db

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        existing = DatabaseManager.get_session()
        if existing is not None:
            yield existing
            return

        async with self.db.transaction() as session:
            yield session


__all__ = ["TransactionalRepository"]

