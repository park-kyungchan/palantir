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
from scripts.ontology.storage.database import Database


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
