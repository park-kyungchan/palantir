"""
Shared pytest fixtures for Orion Orchestrator V2 tests.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from scripts.ontology.actions import ActionContext
from scripts.ontology.storage.database import Database, DatabaseManager


# =============================================================================
# ACTION CONTEXT FIXTURES
# =============================================================================

@pytest.fixture
def system_context() -> ActionContext:
    """Create a system-level action context."""
    return ActionContext.system()


@pytest.fixture
def user_context() -> ActionContext:
    """Create a user action context."""
    return ActionContext(
        actor_id="user-001",
        correlation_id="test-correlation-123",
        metadata={"source": "pytest"}
    )


@pytest.fixture
def admin_context() -> ActionContext:
    """Create an admin action context."""
    return ActionContext(
        actor_id="admin-001",
        metadata={"role": "administrator"}
    )


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def temp_db() -> AsyncGenerator[Database, None]:
    """Create a temporary in-memory database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_ontology.db"
        database = Database(db_path)
        await database.initialize()
        yield database


@pytest_asyncio.fixture
async def isolated_db() -> AsyncGenerator[Database, None]:
    """
    Create a fully isolated database for testing.

    This fixture not only creates a separate Database instance, but also
    sets it as the context-local database via DatabaseManager. This means
    ALL code paths that use get_database() or DatabaseManager.get() will
    receive this isolated instance.

    Usage:
        async def test_something(isolated_db):
            # Any code using get_database() will use isolated_db
            runner = ActionRunner()  # Uses get_database() internally
            # runner.db is now isolated_db!
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "isolated_test.db"
        database = Database(db_path)
        await database.initialize()

        # Set as context-local database
        token = DatabaseManager.set_context(database)
        try:
            yield database
        finally:
            # Reset context after test
            DatabaseManager.reset_context(token)


@pytest_asyncio.fixture
async def isolated_db_memory() -> AsyncGenerator[Database, None]:
    """
    Create an isolated in-memory database for fast tests.

    Same as isolated_db but uses SQLite :memory: for faster execution.
    Note: In-memory DBs are automatically destroyed when connection closes.
    """
    database = Database(":memory:")
    await database.initialize()

    token = DatabaseManager.set_context(database)
    try:
        yield database
    finally:
        DatabaseManager.reset_context(token)


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_instructor_client():
    """Mock InstructorClient for LLM action tests."""
    mock_client = MagicMock()
    mock_client.generate = MagicMock()
    mock_client.client = MagicMock()
    mock_client.client.chat.completions.create = MagicMock()
    return mock_client


@pytest.fixture
def clean_registry():
    """Create a fresh ActionRegistry for isolated tests."""
    from scripts.ontology.actions import ActionRegistry
    return ActionRegistry()
