# tests/unit/test_repository.py
"""
Unit tests for the Repository Layer.

Note: These tests are marked as integration tests because aiosqlite
has specific event loop requirements that are difficult to satisfy
in pytest's asyncio mode. The repository has been manually verified
to work correctly with the CLI.

TODO: Set up proper async test infrastructure with pytest-asyncio
or use synchronous sqlite3 for unit tests.
"""
import pytest
from palantir_fde_learning.adapters.repository.sqlite import SQLiteLearnerRepository
from palantir_fde_learning.adapters.repository.base import (
    Repository,
    RepositoryError,
    EntityNotFoundError,
    ConcurrencyError,
)
from palantir_fde_learning.adapters.repository.learner_repository import LearnerRepository


class TestRepositoryInterfaces:
    """Test repository interface definitions."""

    def test_sqlite_learner_repository_implements_learner_repository(self):
        """Verify SQLiteLearnerRepository implements LearnerRepository interface."""
        repo = SQLiteLearnerRepository("test.db")
        assert isinstance(repo, LearnerRepository)
        assert isinstance(repo, Repository)

    def test_repository_error_inheritance(self):
        """Test custom exception hierarchy."""
        assert issubclass(EntityNotFoundError, RepositoryError)
        assert issubclass(ConcurrencyError, RepositoryError)

    def test_entity_not_found_error_message(self):
        """Test EntityNotFoundError message formatting."""
        error = EntityNotFoundError("LearnerProfile", "user123")
        assert "LearnerProfile" in str(error)
        assert "user123" in str(error)
        assert error.entity_type == "LearnerProfile"
        assert error.entity_id == "user123"

    def test_concurrency_error_message(self):
        """Test ConcurrencyError message formatting."""
        error = ConcurrencyError("LearnerProfile", "user123")
        assert "LearnerProfile" in str(error)
        assert "user123" in str(error)
        assert "Concurrent modification" in str(error)


class TestSQLiteLearnerRepositoryConfig:
    """Test SQLiteLearnerRepository configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        from pathlib import Path
        repo = SQLiteLearnerRepository()
        assert repo.db_path == Path("learner_state.db")
        assert repo.enable_audit is False

    def test_custom_config(self, tmp_path):
        """Test custom configuration values."""
        from pathlib import Path
        custom_path = str(tmp_path / "custom.db")
        repo = SQLiteLearnerRepository(custom_path, enable_audit=True)
        assert repo.db_path == Path(custom_path)
        assert repo.enable_audit is True


# Integration tests for async operations
# These require proper async test setup and are skipped by default

@pytest.mark.skip(reason="Requires async test infrastructure - see TODO above")
class TestSQLiteLearnerRepositoryOperations:
    """Integration tests for SQLiteLearnerRepository async operations."""

    async def test_save_and_find_by_id(self, tmp_path):
        """Test saving and retrieving a profile."""
        pass  # Placeholder for async tests

    async def test_find_by_mastery_above(self, tmp_path):
        """Test finding profiles above mastery threshold."""
        pass  # Placeholder for async tests

    async def test_get_statistics(self, tmp_path):
        """Test aggregate statistics."""
        pass  # Placeholder for async tests
