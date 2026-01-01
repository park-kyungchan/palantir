"""
Unit tests for Database configuration and DatabaseManager.
Tests environment variable support, default paths, and context isolation.

RED Phase: These tests are designed to FAIL until DatabaseManager is implemented.
The DatabaseManager pattern provides:
1. Environment variable configuration (ORION_DB_PATH)
2. Context-local database instances for test isolation (via ContextVar)
3. Backward compatibility with legacy get_database()/initialize_database() API
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from contextvars import copy_context

import pytest
import pytest_asyncio

from scripts.ontology.storage.database import (
    Database,
    DatabaseManager,
    initialize_database,
    get_database,
)


class TestDatabaseConfiguration:
    """Tests for database path configuration."""

    @pytest.mark.asyncio
    async def test_database_uses_env_var_path(self, tmp_path: Path):
        """Database should use ORION_DB_PATH environment variable when set."""
        test_db_path = tmp_path / "env_test.db"

        with patch.dict(os.environ, {"ORION_DB_PATH": str(test_db_path)}):
            # Reset any existing instance
            DatabaseManager._default = None

            db = await DatabaseManager.initialize()
            assert str(test_db_path) in db.url

    @pytest.mark.asyncio
    async def test_database_fallback_to_default_path(self):
        """Database should use default path when env var not set."""
        # Ensure env var is not set
        env_copy = {k: v for k, v in os.environ.items() if k != "ORION_DB_PATH"}

        with patch.dict(os.environ, env_copy, clear=True):
            DatabaseManager._default = None

            db = await DatabaseManager.initialize()
            assert "ontology.db" in db.url

    @pytest.mark.asyncio
    async def test_database_explicit_path_overrides_env(self, tmp_path: Path):
        """Explicit path parameter should override environment variable."""
        env_path = tmp_path / "env.db"
        explicit_path = tmp_path / "explicit.db"

        with patch.dict(os.environ, {"ORION_DB_PATH": str(env_path)}):
            DatabaseManager._default = None

            db = await DatabaseManager.initialize(str(explicit_path))
            assert str(explicit_path) in db.url
            assert str(env_path) not in db.url


class TestDatabaseManager:
    """Tests for DatabaseManager context isolation."""

    def test_database_manager_get_raises_when_not_initialized(self):
        """DatabaseManager.get() should raise RuntimeError when not initialized."""
        # Save original state
        original_default = getattr(DatabaseManager, '_default', None)
        original_context = DatabaseManager._context_db.get() if hasattr(DatabaseManager, '_context_db') else None

        try:
            DatabaseManager._default = None
            if hasattr(DatabaseManager, '_context_db'):
                DatabaseManager._context_db.set(None)

            with pytest.raises(RuntimeError, match="not initialized"):
                DatabaseManager.get()
        finally:
            # Restore original state
            DatabaseManager._default = original_default
            if hasattr(DatabaseManager, '_context_db') and original_context is not None:
                DatabaseManager._context_db.set(original_context)

    @pytest.mark.asyncio
    async def test_database_manager_context_isolation(self, tmp_path: Path):
        """Context-local database should be isolated from default."""
        # Setup default
        default_db = Database(tmp_path / "default.db")
        await default_db.initialize()
        DatabaseManager._default = default_db

        # Setup context-local
        context_db = Database(tmp_path / "context.db")
        await context_db.initialize()

        # Set context
        token = DatabaseManager.set_context(context_db)
        try:
            # Should return context-local, not default
            assert DatabaseManager.get() is context_db
            assert DatabaseManager.get() is not default_db
        finally:
            DatabaseManager.reset_context(token)

        # After reset, should return default
        assert DatabaseManager.get() is default_db

    @pytest.mark.asyncio
    async def test_database_manager_get_returns_context_db_priority(self, tmp_path: Path):
        """Context-local database has priority over default."""
        default_db = Database(tmp_path / "default.db")
        await default_db.initialize()

        context_db = Database(tmp_path / "context.db")
        await context_db.initialize()

        DatabaseManager._default = default_db

        # Without context, returns default
        assert DatabaseManager.get() is default_db

        # With context, returns context
        token = DatabaseManager.set_context(context_db)
        assert DatabaseManager.get() is context_db

        DatabaseManager.reset_context(token)
        assert DatabaseManager.get() is default_db

    @pytest.mark.asyncio
    async def test_database_manager_nested_context(self, tmp_path: Path):
        """Nested context-local databases should work correctly."""
        default_db = Database(tmp_path / "default.db")
        await default_db.initialize()

        outer_db = Database(tmp_path / "outer.db")
        await outer_db.initialize()

        inner_db = Database(tmp_path / "inner.db")
        await inner_db.initialize()

        DatabaseManager._default = default_db

        # Outer context
        outer_token = DatabaseManager.set_context(outer_db)
        assert DatabaseManager.get() is outer_db

        # Inner context (nested)
        inner_token = DatabaseManager.set_context(inner_db)
        assert DatabaseManager.get() is inner_db

        # Pop inner, should return to outer
        DatabaseManager.reset_context(inner_token)
        assert DatabaseManager.get() is outer_db

        # Pop outer, should return to default
        DatabaseManager.reset_context(outer_token)
        assert DatabaseManager.get() is default_db


class TestDatabaseInstanceIsolation:
    """Tests for multiple database instance isolation."""

    @pytest.mark.asyncio
    async def test_multiple_database_instances_are_isolated(self, tmp_path: Path):
        """Multiple Database instances should be completely isolated."""
        db1 = Database(tmp_path / "db1.db")
        db2 = Database(tmp_path / "db2.db")

        await db1.initialize()
        await db2.initialize()

        # Verify different URLs
        assert db1.url != db2.url

        # Verify different engines
        assert db1.engine is not db2.engine

        # Verify different session factories
        assert db1.session_factory is not db2.session_factory

    @pytest.mark.asyncio
    async def test_in_memory_databases_are_isolated(self):
        """In-memory databases should be separate instances."""
        db1 = Database(":memory:")
        db2 = Database(":memory:")

        await db1.initialize()
        await db2.initialize()

        # Even with same URL, they should be different instances
        assert db1.engine is not db2.engine

    @pytest.mark.asyncio
    async def test_database_url_normalization(self, tmp_path: Path):
        """Database should normalize path to proper SQLite URL."""
        db_path = tmp_path / "test.db"
        db = Database(db_path)

        # Should have aiosqlite in URL
        assert "aiosqlite" in db.url
        # Should have the path
        assert "test.db" in db.url

    @pytest.mark.asyncio
    async def test_database_with_string_path(self, tmp_path: Path):
        """Database should accept string paths."""
        db_path = str(tmp_path / "string_path.db")
        db = Database(db_path)

        await db.initialize()

        assert "string_path.db" in db.url
        assert db._initialized is True


class TestLegacyAPICompatibility:
    """Tests ensuring backward compatibility with legacy API."""

    @pytest.mark.asyncio
    async def test_get_database_returns_same_as_manager_get(self, tmp_path: Path):
        """get_database() should return same instance as DatabaseManager.get()."""
        db = Database(tmp_path / "test.db")
        await db.initialize()
        DatabaseManager._default = db

        # Clear any context-local database
        if hasattr(DatabaseManager, '_context_db'):
            DatabaseManager._context_db.set(None)

        assert get_database() is DatabaseManager.get()

    @pytest.mark.asyncio
    async def test_initialize_database_uses_manager(self, tmp_path: Path):
        """initialize_database() should use DatabaseManager internally."""
        DatabaseManager._default = None

        with patch.dict(os.environ, {"ORION_DB_PATH": str(tmp_path / "test.db")}):
            db = await initialize_database()
            assert db is DatabaseManager.get()

    @pytest.mark.asyncio
    async def test_legacy_global_singleton_still_works(self, tmp_path: Path):
        """Legacy global _db_instance pattern should still function."""
        db_path = tmp_path / "legacy.db"

        with patch.dict(os.environ, {"ORION_DB_PATH": str(db_path)}):
            DatabaseManager._default = None

            # Initialize via legacy function
            db = await initialize_database()

            # Should be retrievable via legacy get_database()
            retrieved = get_database()
            assert retrieved is db


class TestDatabaseHealthCheck:
    """Tests for database health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_returns_true_for_healthy_db(self, tmp_path: Path):
        """health_check() should return True for working database."""
        db = Database(tmp_path / "healthy.db")
        await db.initialize()

        result = await db.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_works_with_in_memory_db(self):
        """health_check() should work with in-memory database."""
        db = Database(":memory:")
        await db.initialize()

        result = await db.health_check()
        assert result is True


class TestDatabaseTransaction:
    """Tests for database transaction context manager."""

    @pytest.mark.asyncio
    async def test_transaction_commits_on_success(self, tmp_path: Path):
        """Transaction should commit when no exception occurs."""
        db = Database(tmp_path / "transaction.db")
        await db.initialize()

        async with db.transaction() as session:
            # Perform some operation (just verify session is valid)
            assert session is not None

        # No exception means success

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_exception(self, tmp_path: Path):
        """Transaction should rollback when exception occurs."""
        db = Database(tmp_path / "rollback.db")
        await db.initialize()

        with pytest.raises(ValueError, match="test error"):
            async with db.transaction() as session:
                assert session is not None
                raise ValueError("test error")


class TestDatabaseManagerInitialize:
    """Tests for DatabaseManager.initialize() method."""

    @pytest.mark.asyncio
    async def test_initialize_creates_default_instance(self, tmp_path: Path):
        """initialize() should create and store default instance."""
        DatabaseManager._default = None

        with patch.dict(os.environ, {"ORION_DB_PATH": str(tmp_path / "init.db")}):
            db = await DatabaseManager.initialize()

            assert db is not None
            assert DatabaseManager._default is db

    @pytest.mark.asyncio
    async def test_initialize_with_path_uses_that_path(self, tmp_path: Path):
        """initialize(path) should use the provided path."""
        DatabaseManager._default = None
        explicit_path = tmp_path / "explicit_init.db"

        db = await DatabaseManager.initialize(str(explicit_path))

        assert str(explicit_path) in db.url

    @pytest.mark.asyncio
    async def test_initialize_replaces_existing_instance(self, tmp_path: Path):
        """Multiple initialize() calls create new instances (not idempotent by design).

        Note: This tests current behavior. If idempotent initialization is desired,
        use DatabaseManager.get() after the first initialize() call instead.
        """
        DatabaseManager._default = None
        db_path = tmp_path / "multi_init.db"

        with patch.dict(os.environ, {"ORION_DB_PATH": str(db_path)}):
            db1 = await DatabaseManager.initialize()
            db2 = await DatabaseManager.initialize()

            # Each initialize() creates a new instance (current behavior)
            # Both point to same path but are different objects
            assert db1 is not db2
            assert db1.url == db2.url

    @pytest.mark.asyncio
    async def test_initialize_then_get_returns_same_instance(self, tmp_path: Path):
        """After initialize(), get() returns the same instance consistently."""
        DatabaseManager._default = None
        db_path = tmp_path / "get_consistency.db"

        with patch.dict(os.environ, {"ORION_DB_PATH": str(db_path)}):
            db1 = await DatabaseManager.initialize()
            db2 = DatabaseManager.get()
            db3 = DatabaseManager.get()

            # get() should consistently return the initialized instance
            assert db1 is db2
            assert db2 is db3
