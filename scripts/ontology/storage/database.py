"""
ODA V3.0 - Database Connection Manager
======================================

Provides SQLite connection management with:
- WAL mode for high concurrency
- Connection pooling simulation
- Transaction context managers
- Schema migration support

Usage:
    db = Database("/path/to/ontology.db")
    async with db.transaction() as conn:
        await conn.execute("INSERT INTO ...")
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import aiosqlite

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: Path
    wal_mode: bool = True
    timeout: float = 30.0
    check_same_thread: bool = False
    journal_size_limit: int = 67108864  # 64MB


class Database:
    """
    Async SQLite database manager.
    
    Features:
    - WAL mode for concurrent reads/writes
    - Automatic schema initialization
    - Transaction context manager
    - Connection health checks
    
    Example:
        ```python
        db = Database(Path("/home/palantir/orion.db"))
        await db.initialize()
        
        async with db.transaction() as conn:
            await conn.execute("INSERT INTO proposals ...")
            # Auto-commits on exit, rolls back on exception
        ```
    """
    
    def __init__(self, path: Path | str, config: DatabaseConfig | None = None):
        self.path = Path(path)
        self.config = config or DatabaseConfig(path=self.path)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database with schema."""
        if self._initialized:
            return
        
        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(
            self.path,
            timeout=self.config.timeout
        ) as conn:
            # Enable WAL mode for concurrency
            if self.config.wal_mode:
                await conn.execute("PRAGMA journal_mode=WAL;")
                await conn.execute(
                    f"PRAGMA journal_size_limit={self.config.journal_size_limit};"
                )
            
            # Performance optimizations
            await conn.execute("PRAGMA synchronous=NORMAL;")
            await conn.execute("PRAGMA cache_size=-64000;")  # 64MB cache
            await conn.execute("PRAGMA temp_store=MEMORY;")
            
            # Run schema migrations
            await self._run_migrations(conn)
            await conn.commit()
        
        self._initialized = True
        logger.info(f"Database initialized: {self.path}")
    
    async def _run_migrations(self, conn: aiosqlite.Connection) -> None:
        """Run schema migrations."""
        # Create migrations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)
        
        # Get applied migrations
        cursor = await conn.execute("SELECT name FROM _migrations")
        applied = {row[0] for row in await cursor.fetchall()}
        
        # Apply pending migrations
        for name, sql in MIGRATIONS.items():
            if name not in applied:
                logger.info(f"Applying migration: {name}")
                await conn.executescript(sql)
                await conn.execute(
                    "INSERT INTO _migrations (name, applied_at) VALUES (?, ?)",
                    (name, datetime.now(timezone.utc).isoformat())
                )
    
    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get a database connection."""
        if not self._initialized:
            await self.initialize()
        
        async with aiosqlite.connect(
            self.path,
            timeout=self.config.timeout
        ) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """
        Get a connection with automatic transaction management.
        
        Commits on successful exit, rolls back on exception.
        """
        async with self.connection() as conn:
            try:
                yield conn
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
    
    async def execute(
        self,
        sql: str,
        params: Tuple | Dict = ()
    ) -> aiosqlite.Cursor:
        """Execute a single SQL statement."""
        async with self.transaction() as conn:
            return await conn.execute(sql, params)
    
    async def executemany(
        self,
        sql: str,
        params_list: List[Tuple | Dict]
    ) -> aiosqlite.Cursor:
        """Execute SQL statement with multiple parameter sets."""
        async with self.transaction() as conn:
            return await conn.executemany(sql, params_list)
    
    async def fetchone(
        self,
        sql: str,
        params: Tuple | Dict = ()
    ) -> Optional[aiosqlite.Row]:
        """Fetch a single row."""
        async with self.connection() as conn:
            cursor = await conn.execute(sql, params)
            return await cursor.fetchone()
    
    async def fetchall(
        self,
        sql: str,
        params: Tuple | Dict = ()
    ) -> List[aiosqlite.Row]:
        """Fetch all rows."""
        async with self.connection() as conn:
            cursor = await conn.execute(sql, params)
            return await cursor.fetchall()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.connection() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# =============================================================================
# SCHEMA MIGRATIONS
# =============================================================================

MIGRATIONS = {
    "001_create_proposals": """
        CREATE TABLE IF NOT EXISTS proposals (
            id TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            payload TEXT NOT NULL,  -- JSON
            status TEXT NOT NULL DEFAULT 'draft',
            priority TEXT NOT NULL DEFAULT 'medium',
            
            -- Audit fields
            created_by TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            
            -- Review fields
            reviewed_by TEXT,
            reviewed_at TEXT,
            review_comment TEXT,
            
            -- Execution fields
            executed_at TEXT,
            execution_result TEXT,  -- JSON
            
            -- Metadata
            tags TEXT,  -- JSON array
            object_status TEXT NOT NULL DEFAULT 'active'
        );
        
        CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
        CREATE INDEX IF NOT EXISTS idx_proposals_action_type ON proposals(action_type);
        CREATE INDEX IF NOT EXISTS idx_proposals_created_by ON proposals(created_by);
        CREATE INDEX IF NOT EXISTS idx_proposals_created_at ON proposals(created_at);
    """,
    
    "002_create_proposal_history": """
        CREATE TABLE IF NOT EXISTS proposal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id TEXT NOT NULL,
            action TEXT NOT NULL,  -- 'created', 'submitted', 'approved', 'rejected', 'executed', 'cancelled'
            actor_id TEXT,
            timestamp TEXT NOT NULL,
            previous_status TEXT,
            new_status TEXT,
            comment TEXT,
            metadata TEXT,  -- JSON
            
            FOREIGN KEY (proposal_id) REFERENCES proposals(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_proposal_history_proposal_id ON proposal_history(proposal_id);
        CREATE INDEX IF NOT EXISTS idx_proposal_history_timestamp ON proposal_history(timestamp);
    """,
    
    "003_create_edit_operations": """
        CREATE TABLE IF NOT EXISTS edit_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id TEXT,
            edit_type TEXT NOT NULL,
            object_type TEXT NOT NULL,
            object_id TEXT NOT NULL,
            changes TEXT NOT NULL,  -- JSON
            timestamp TEXT NOT NULL,
            actor_id TEXT,
            
            FOREIGN KEY (proposal_id) REFERENCES proposals(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_edit_operations_proposal_id ON edit_operations(proposal_id);
        CREATE INDEX IF NOT EXISTS idx_edit_operations_object_id ON edit_operations(object_id);
        CREATE INDEX IF NOT EXISTS idx_edit_operations_timestamp ON edit_operations(timestamp);
    """
}


# =============================================================================
# GLOBAL DATABASE INSTANCE
# =============================================================================

_db_instance: Optional[Database] = None


def get_database(path: Path | str | None = None) -> Database:
    """
    Get or create the global database instance.
    
    Args:
        path: Database path. If None, uses default.
    
    Returns:
        Database instance
    """
    global _db_instance
    
    if _db_instance is None:
        default_path = Path("/home/palantir/orion-orchestrator-v2/data/ontology.db")
        _db_instance = Database(path or default_path)
    
    return _db_instance


async def initialize_database(path: Path | str | None = None) -> Database:
    """Initialize and return the database."""
    db = get_database(path)
    await db.initialize()
    return db
