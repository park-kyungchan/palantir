# ProposalRepository SQLite Implementation

> **Target Agent**: Antigravity IDE (Gemini 3.0 Pro)
> **Date**: 2025-12-20
> **Purpose**: Persistent storage for Proposal governance workflow
> **Dependencies**: ODA V3.0 Refactoring (commit 9962a58)

---

## Instruction for Antigravity Agent

Create the following files to implement SQLite persistence for the Proposal governance system.
This enables:
1. Persistent Proposal storage across system restarts
2. Query pending/approved/rejected proposals
3. Full audit trail with transaction history
4. Concurrent access with WAL mode

---

## File 1: `scripts/ontology/storage/database.py`

```python
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
```

---

## File 2: `scripts/ontology/storage/proposal_repository.py`

```python
"""
ODA V3.0 - Proposal Repository
==============================

Provides CRUD operations for Proposal persistence with:
- SQLite storage with WAL mode
- Full history tracking
- Optimistic locking (version-based)
- Query filtering and pagination

Usage:
    repo = ProposalRepository(db)
    
    # Save a proposal
    await repo.save(proposal)
    
    # Query pending proposals
    pending = await repo.find_by_status(ProposalStatus.PENDING)
    
    # Get with history
    proposal, history = await repo.get_with_history(proposal_id)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from scripts.ontology.objects.proposal import (
    Proposal,
    ProposalPriority,
    ProposalStatus,
)
from scripts.ontology.ontology_types import ObjectStatus, utc_now
from scripts.ontology.storage.database import Database, get_database

logger = logging.getLogger(__name__)


# =============================================================================
# DATA TRANSFER OBJECTS
# =============================================================================

@dataclass
class ProposalHistoryEntry:
    """A single entry in the proposal history."""
    id: int
    proposal_id: str
    action: str
    actor_id: Optional[str]
    timestamp: datetime
    previous_status: Optional[str]
    new_status: Optional[str]
    comment: Optional[str]
    metadata: Optional[Dict[str, Any]]


@dataclass
class ProposalQuery:
    """Query parameters for proposal search."""
    status: Optional[ProposalStatus] = None
    action_type: Optional[str] = None
    created_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    priority: Optional[ProposalPriority] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
    order_by: str = "created_at"
    order_desc: bool = True


@dataclass
class PaginatedResult:
    """Paginated query result."""
    items: List[Proposal]
    total: int
    limit: int
    offset: int
    has_more: bool


# =============================================================================
# EXCEPTIONS
# =============================================================================

class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class ProposalNotFoundError(RepositoryError):
    """Raised when a proposal is not found."""
    def __init__(self, proposal_id: str):
        self.proposal_id = proposal_id
        super().__init__(f"Proposal not found: {proposal_id}")


class OptimisticLockError(RepositoryError):
    """Raised when optimistic lock fails (concurrent modification)."""
    def __init__(self, proposal_id: str, expected_version: int, actual_version: int):
        self.proposal_id = proposal_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Optimistic lock failed for {proposal_id}: "
            f"expected version {expected_version}, found {actual_version}"
        )


# =============================================================================
# PROPOSAL REPOSITORY
# =============================================================================

class ProposalRepository:
    """
    Repository for Proposal persistence operations.
    
    Provides:
    - CRUD operations with automatic history tracking
    - Optimistic locking for concurrent access
    - Flexible querying with filters and pagination
    - Bulk operations for batch processing
    
    Example:
        ```python
        db = await initialize_database()
        repo = ProposalRepository(db)
        
        # Create and save
        proposal = Proposal(action_type="deploy_service", created_by="agent-001")
        proposal.submit()
        await repo.save(proposal)
        
        # Query
        pending = await repo.find_by_status(ProposalStatus.PENDING)
        for p in pending:
            print(f"{p.id}: {p.action_type}")
        ```
    """
    
    def __init__(self, db: Database | None = None):
        self.db = db or get_database()
    
    # =========================================================================
    # SERIALIZATION
    # =========================================================================
    
    def _serialize_proposal(self, proposal: Proposal) -> Dict[str, Any]:
        """Convert Proposal to database row."""
        return {
            "id": proposal.id,
            "action_type": proposal.action_type,
            "payload": json.dumps(proposal.payload),
            "status": proposal.status.value,
            "priority": proposal.priority.value,
            "created_by": proposal.created_by,
            "created_at": proposal.created_at.isoformat(),
            "updated_at": proposal.updated_at.isoformat(),
            "version": proposal.version,
            "reviewed_by": proposal.reviewed_by,
            "reviewed_at": proposal.reviewed_at.isoformat() if proposal.reviewed_at else None,
            "review_comment": proposal.review_comment,
            "executed_at": proposal.executed_at.isoformat() if proposal.executed_at else None,
            "execution_result": json.dumps(proposal.execution_result) if proposal.execution_result else None,
            "tags": json.dumps(proposal.tags),
            "object_status": proposal.status.value if hasattr(proposal, 'status') else 'active',
        }
    
    def _deserialize_proposal(self, row: Dict[str, Any]) -> Proposal:
        """Convert database row to Proposal."""
        return Proposal(
            id=row["id"],
            action_type=row["action_type"],
            payload=json.loads(row["payload"]) if row["payload"] else {},
            status=ProposalStatus(row["status"]),
            priority=ProposalPriority(row["priority"]),
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            version=row["version"],
            reviewed_by=row["reviewed_by"],
            reviewed_at=datetime.fromisoformat(row["reviewed_at"]) if row["reviewed_at"] else None,
            review_comment=row["review_comment"],
            executed_at=datetime.fromisoformat(row["executed_at"]) if row["executed_at"] else None,
            execution_result=json.loads(row["execution_result"]) if row["execution_result"] else None,
            tags=json.loads(row["tags"]) if row["tags"] else [],
        )
    
    def _deserialize_history(self, row: Dict[str, Any]) -> ProposalHistoryEntry:
        """Convert database row to history entry."""
        return ProposalHistoryEntry(
            id=row["id"],
            proposal_id=row["proposal_id"],
            action=row["action"],
            actor_id=row["actor_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            previous_status=row["previous_status"],
            new_status=row["new_status"],
            comment=row["comment"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        )
    
    # =========================================================================
    # CRUD OPERATIONS
    # =========================================================================
    
    async def save(
        self,
        proposal: Proposal,
        actor_id: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Proposal:
        """
        Save a proposal (insert or update).
        
        Args:
            proposal: The proposal to save
            actor_id: ID of the actor performing the save
            comment: Optional comment for history
        
        Returns:
            The saved proposal with updated version
        
        Raises:
            OptimisticLockError: If concurrent modification detected
        """
        existing = await self.find_by_id(proposal.id)
        
        if existing is None:
            return await self._insert(proposal, actor_id, comment)
        else:
            return await self._update(proposal, existing.version, actor_id, comment)
    
    async def _insert(
        self,
        proposal: Proposal,
        actor_id: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Proposal:
        """Insert a new proposal."""
        data = self._serialize_proposal(proposal)
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data.keys())
        
        async with self.db.transaction() as conn:
            await conn.execute(
                f"INSERT INTO proposals ({columns}) VALUES ({placeholders})",
                data
            )
            
            # Record history
            await self._record_history(
                conn,
                proposal.id,
                action="created",
                actor_id=actor_id or proposal.created_by,
                new_status=proposal.status.value,
                comment=comment,
            )
        
        logger.info(f"Inserted proposal: {proposal.id}")
        return proposal
    
    async def _update(
        self,
        proposal: Proposal,
        expected_version: int,
        actor_id: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Proposal:
        """Update an existing proposal with optimistic locking."""
        # Get current state for history
        current = await self.find_by_id(proposal.id)
        if current is None:
            raise ProposalNotFoundError(proposal.id)
        
        if current.version != expected_version:
            raise OptimisticLockError(proposal.id, expected_version, current.version)
        
        # Increment version
        proposal.version = expected_version + 1
        proposal.updated_at = utc_now()
        
        data = self._serialize_proposal(proposal)
        
        set_clause = ", ".join(f"{k} = :{k}" for k in data.keys() if k != "id")
        
        async with self.db.transaction() as conn:
            result = await conn.execute(
                f"""
                UPDATE proposals 
                SET {set_clause}
                WHERE id = :id AND version = :expected_version
                """,
                {**data, "expected_version": expected_version}
            )
            
            if result.rowcount == 0:
                # Race condition - version changed
                actual = await self.find_by_id(proposal.id)
                raise OptimisticLockError(
                    proposal.id,
                    expected_version,
                    actual.version if actual else -1
                )
            
            # Record history
            await self._record_history(
                conn,
                proposal.id,
                action="updated",
                actor_id=actor_id or proposal.updated_by,
                previous_status=current.status.value,
                new_status=proposal.status.value,
                comment=comment,
            )
        
        logger.info(f"Updated proposal: {proposal.id} (v{proposal.version})")
        return proposal
    
    async def delete(
        self,
        proposal_id: str,
        actor_id: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a proposal.
        
        Args:
            proposal_id: ID of the proposal to delete
            actor_id: ID of the actor performing deletion
            hard_delete: If True, permanently remove. Otherwise soft-delete.
        
        Returns:
            True if deleted, False if not found
        """
        if hard_delete:
            async with self.db.transaction() as conn:
                # Delete history first (foreign key)
                await conn.execute(
                    "DELETE FROM proposal_history WHERE proposal_id = ?",
                    (proposal_id,)
                )
                result = await conn.execute(
                    "DELETE FROM proposals WHERE id = ?",
                    (proposal_id,)
                )
                return result.rowcount > 0
        else:
            proposal = await self.find_by_id(proposal_id)
            if proposal is None:
                return False
            
            proposal.soft_delete(deleted_by=actor_id)
            await self.save(proposal, actor_id, "Soft deleted")
            return True
    
    # =========================================================================
    # QUERY OPERATIONS
    # =========================================================================
    
    async def find_by_id(self, proposal_id: str) -> Optional[Proposal]:
        """Find a proposal by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM proposals WHERE id = ?",
            (proposal_id,)
        )
        
        if row is None:
            return None
        
        return self._deserialize_proposal(dict(row))
    
    async def find_by_status(
        self,
        status: ProposalStatus,
        limit: int = 100
    ) -> List[Proposal]:
        """Find proposals by status."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM proposals 
            WHERE status = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (status.value, limit)
        )
        
        return [self._deserialize_proposal(dict(row)) for row in rows]
    
    async def find_pending(self, limit: int = 100) -> List[Proposal]:
        """Find all pending proposals (convenience method)."""
        return await self.find_by_status(ProposalStatus.PENDING, limit)
    
    async def find_by_action_type(
        self,
        action_type: str,
        limit: int = 100
    ) -> List[Proposal]:
        """Find proposals by action type."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM proposals 
            WHERE action_type = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (action_type, limit)
        )
        
        return [self._deserialize_proposal(dict(row)) for row in rows]
    
    async def find_by_creator(
        self,
        created_by: str,
        limit: int = 100
    ) -> List[Proposal]:
        """Find proposals by creator."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM proposals 
            WHERE created_by = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (created_by, limit)
        )
        
        return [self._deserialize_proposal(dict(row)) for row in rows]
    
    async def query(self, query: ProposalQuery) -> PaginatedResult:
        """
        Execute a flexible query with filters and pagination.
        
        Args:
            query: Query parameters
        
        Returns:
            Paginated result with proposals
        """
        conditions = []
        params = {}
        
        if query.status:
            conditions.append("status = :status")
            params["status"] = query.status.value
        
        if query.action_type:
            conditions.append("action_type = :action_type")
            params["action_type"] = query.action_type
        
        if query.created_by:
            conditions.append("created_by = :created_by")
            params["created_by"] = query.created_by
        
        if query.reviewed_by:
            conditions.append("reviewed_by = :reviewed_by")
            params["reviewed_by"] = query.reviewed_by
        
        if query.priority:
            conditions.append("priority = :priority")
            params["priority"] = query.priority.value
        
        if query.created_after:
            conditions.append("created_at >= :created_after")
            params["created_after"] = query.created_after.isoformat()
        
        if query.created_before:
            conditions.append("created_at <= :created_before")
            params["created_before"] = query.created_before.isoformat()
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        order_direction = "DESC" if query.order_desc else "ASC"
        
        # Get total count
        count_row = await self.db.fetchone(
            f"SELECT COUNT(*) as count FROM proposals WHERE {where_clause}",
            params
        )
        total = count_row["count"] if count_row else 0
        
        # Get paginated results
        rows = await self.db.fetchall(
            f"""
            SELECT * FROM proposals 
            WHERE {where_clause}
            ORDER BY {query.order_by} {order_direction}
            LIMIT :limit OFFSET :offset
            """,
            {**params, "limit": query.limit, "offset": query.offset}
        )
        
        items = [self._deserialize_proposal(dict(row)) for row in rows]
        
        return PaginatedResult(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
            has_more=(query.offset + len(items)) < total,
        )
    
    # =========================================================================
    # HISTORY OPERATIONS
    # =========================================================================
    
    async def _record_history(
        self,
        conn,
        proposal_id: str,
        action: str,
        actor_id: Optional[str] = None,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a history entry."""
        await conn.execute(
            """
            INSERT INTO proposal_history 
            (proposal_id, action, actor_id, timestamp, previous_status, new_status, comment, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id,
                action,
                actor_id,
                utc_now().isoformat(),
                previous_status,
                new_status,
                comment,
                json.dumps(metadata) if metadata else None,
            )
        )
    
    async def get_history(self, proposal_id: str) -> List[ProposalHistoryEntry]:
        """Get full history for a proposal."""
        rows = await self.db.fetchall(
            """
            SELECT * FROM proposal_history 
            WHERE proposal_id = ?
            ORDER BY timestamp ASC
            """,
            (proposal_id,)
        )
        
        return [self._deserialize_history(dict(row)) for row in rows]
    
    async def get_with_history(
        self,
        proposal_id: str
    ) -> Tuple[Optional[Proposal], List[ProposalHistoryEntry]]:
        """Get proposal with full history."""
        proposal = await self.find_by_id(proposal_id)
        history = await self.get_history(proposal_id) if proposal else []
        return proposal, history
    
    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================
    
    async def save_many(
        self,
        proposals: List[Proposal],
        actor_id: Optional[str] = None
    ) -> List[Proposal]:
        """Save multiple proposals in a single transaction."""
        results = []
        
        async with self.db.transaction() as conn:
            for proposal in proposals:
                data = self._serialize_proposal(proposal)
                columns = ", ".join(data.keys())
                placeholders = ", ".join(f":{k}" for k in data.keys())
                
                await conn.execute(
                    f"""
                    INSERT OR REPLACE INTO proposals ({columns})
                    VALUES ({placeholders})
                    """,
                    data
                )
                
                await self._record_history(
                    conn,
                    proposal.id,
                    action="bulk_saved",
                    actor_id=actor_id,
                    new_status=proposal.status.value,
                )
                
                results.append(proposal)
        
        logger.info(f"Bulk saved {len(results)} proposals")
        return results
    
    async def count_by_status(self) -> Dict[str, int]:
        """Get count of proposals by status."""
        rows = await self.db.fetchall(
            """
            SELECT status, COUNT(*) as count 
            FROM proposals 
            GROUP BY status
            """
        )
        
        return {row["status"]: row["count"] for row in rows}
    
    # =========================================================================
    # GOVERNANCE HELPERS
    # =========================================================================
    
    async def approve(
        self,
        proposal_id: str,
        reviewer_id: str,
        comment: Optional[str] = None
    ) -> Proposal:
        """
        Approve a proposal (convenience method).
        
        Args:
            proposal_id: ID of the proposal
            reviewer_id: ID of the reviewer
            comment: Optional approval comment
        
        Returns:
            Updated proposal
        
        Raises:
            ProposalNotFoundError: If proposal not found
            InvalidTransitionError: If not in PENDING status
        """
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        
        proposal.approve(reviewer_id=reviewer_id, comment=comment)
        
        async with self.db.transaction() as conn:
            await self._update_status(conn, proposal)
            await self._record_history(
                conn,
                proposal.id,
                action="approved",
                actor_id=reviewer_id,
                previous_status=ProposalStatus.PENDING.value,
                new_status=ProposalStatus.APPROVED.value,
                comment=comment,
            )
        
        return proposal
    
    async def reject(
        self,
        proposal_id: str,
        reviewer_id: str,
        reason: str
    ) -> Proposal:
        """
        Reject a proposal (convenience method).
        
        Args:
            proposal_id: ID of the proposal
            reviewer_id: ID of the reviewer
            reason: Rejection reason
        
        Returns:
            Updated proposal
        """
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        
        proposal.reject(reviewer_id=reviewer_id, reason=reason)
        
        async with self.db.transaction() as conn:
            await self._update_status(conn, proposal)
            await self._record_history(
                conn,
                proposal.id,
                action="rejected",
                actor_id=reviewer_id,
                previous_status=ProposalStatus.PENDING.value,
                new_status=ProposalStatus.REJECTED.value,
                comment=reason,
            )
        
        return proposal
    
    async def execute(
        self,
        proposal_id: str,
        executor_id: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> Proposal:
        """
        Mark a proposal as executed (convenience method).
        
        Args:
            proposal_id: ID of the proposal
            executor_id: ID of the executor
            result: Execution result details
        
        Returns:
            Updated proposal
        """
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        
        proposal.execute(executor_id=executor_id, result=result)
        
        async with self.db.transaction() as conn:
            await self._update_status(conn, proposal)
            await self._record_history(
                conn,
                proposal.id,
                action="executed",
                actor_id=executor_id,
                previous_status=ProposalStatus.APPROVED.value,
                new_status=ProposalStatus.EXECUTED.value,
                metadata=result,
            )
        
        return proposal
    
    async def _update_status(self, conn, proposal: Proposal) -> None:
        """Update proposal status fields."""
        await conn.execute(
            """
            UPDATE proposals SET
                status = ?,
                updated_at = ?,
                version = version + 1,
                reviewed_by = ?,
                reviewed_at = ?,
                review_comment = ?,
                executed_at = ?,
                execution_result = ?
            WHERE id = ?
            """,
            (
                proposal.status.value,
                utc_now().isoformat(),
                proposal.reviewed_by,
                proposal.reviewed_at.isoformat() if proposal.reviewed_at else None,
                proposal.review_comment,
                proposal.executed_at.isoformat() if proposal.executed_at else None,
                json.dumps(proposal.execution_result) if proposal.execution_result else None,
                proposal.id,
            )
        )
```

---

## Verification Checklist

After applying this implementation, verify:

- [ ] Database file created at `/home/palantir/orion-orchestrator-v2/data/ontology.db`
- [ ] WAL mode enabled (`PRAGMA journal_mode` returns `wal`)
- [ ] All 3 tables created: `proposals`, `proposal_history`, `edit_operations`
- [ ] Optimistic locking prevents concurrent modifications
- [ ] History entries created for all state transitions

---

## Test Command

```bash
python -c "
import asyncio
from scripts.ontology.storage.database import initialize_database
from scripts.ontology.storage.proposal_repository import ProposalRepository
from scripts.ontology.objects.proposal import Proposal, ProposalStatus

async def test():
    # Initialize
    db = await initialize_database()
    repo = ProposalRepository(db)
    
    # Create proposal
    p = Proposal(action_type='deploy_service', created_by='agent-001')
    p.submit()
    await repo.save(p)
    print(f'✅ Saved: {p.id}')
    
    # Query
    pending = await repo.find_pending()
    print(f'✅ Found {len(pending)} pending proposals')
    
    # Approve
    await repo.approve(p.id, 'admin-001', 'LGTM')
    approved = await repo.find_by_id(p.id)
    assert approved.status == ProposalStatus.APPROVED
    print(f'✅ Approved: {approved.id}')
    
    # History
    _, history = await repo.get_with_history(p.id)
    print(f'✅ History entries: {len(history)}')
    for h in history:
        print(f'   - {h.action}: {h.previous_status} → {h.new_status}')
    
    print('✅ All tests passed!')

asyncio.run(test())
"
```
