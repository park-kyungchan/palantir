
"""
Orion ODA V3 - API Dependency Injection
======================================
Provides Database Sessions and Service instances to Routes.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from scripts.ontology.storage.database import DatabaseManager, Database
from scripts.ontology.storage.proposal_repository import ProposalRepository

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yields an active AsyncSession from the global pool."""
    db: Database = DatabaseManager.get()  # V3.1: Use DatabaseManager
    async with db.transaction() as session:
        yield session

async def get_repository() -> AsyncGenerator[ProposalRepository, None]:
    """Provides a fresh Repository wrapper around the session."""
    # Note: ProposalRepository currently takes 'db' (manager) in its constructor.
    # Refactoring Step: Ideal repo takes 'session'.
    # For ODA V3 Prototype, we will implement a lightweight wrapper or usage pattern here.
    
    # Existing Pattern: Repo(db) -> internally uses `async with db.transaction()`
    # We will yield the Repo instance directly.
    db = DatabaseManager.get()  # V3.1: Use DatabaseManager
    yield ProposalRepository(db)

