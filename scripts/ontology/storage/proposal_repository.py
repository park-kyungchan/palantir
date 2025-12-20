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
    status_in: Optional[List[ProposalStatus]] = None  # Added for cleanup job
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
        comment: Optional[str] = None,
        action: Optional[str] = None
    ) -> Proposal:
        """
        Save a proposal (insert or update).
        
        Args:
            proposal: The proposal to save
            actor_id: ID of the actor performing the save
            comment: Optional comment for history
            action: Optional action name for history (default: created/updated)
        
        Returns:
            The saved proposal with updated version
        
        Raises:
            OptimisticLockError: If concurrent modification detected
        """
        existing = await self.find_by_id(proposal.id)
        
        if existing is None:
            return await self._insert(proposal, actor_id, comment, action)
        
        # Calculate expected version to handle self-managed versioning of Proposal objects
        if proposal.version == existing.version:
            # If versions match but timestamps differ, it's a concurrent update collision
            # (User's vN is different from DB's vN)
            if proposal.updated_at != existing.updated_at:
                raise OptimisticLockError(proposal.id, proposal.version, existing.version)
            expected_version = proposal.version
        else:
            # Normal case: User has v(N+1), expects DB to be v(N)
            expected_version = proposal.version - 1

        return await self._update(proposal, expected_version, actor_id, comment, action)
    
    async def _insert(
        self,
        proposal: Proposal,
        actor_id: Optional[str] = None,
        comment: Optional[str] = None,
        action: Optional[str] = None
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
                action=action or "created",
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
        comment: Optional[str] = None,
        action: Optional[str] = None
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
                action=action or "updated",
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

        if query.status_in:
            placeholders = [f":status_{i}" for i in range(len(query.status_in))]
            conditions.append(f"status IN ({', '.join(placeholders)})")
            for i, status in enumerate(query.status_in):
                params[f"status_{i}"] = status.value
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Count total
        count_sql = f"SELECT COUNT(*) FROM proposals {where_clause}"
        total_row = await self.db.fetchone(count_sql, params)
        total = total_row[0] if total_row else 0
        
        # Fetch items
        order_dir = "DESC" if query.order_desc else "ASC"
        sql = f"""
            SELECT * FROM proposals 
            {where_clause}
            ORDER BY {query.order_by} {order_dir}
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = query.limit
        params["offset"] = query.offset
        
        rows = await self.db.fetchall(sql, params)
        items = [self._deserialize_proposal(dict(row)) for row in rows]
        
        return PaginatedResult(
            items=items,
            total=total,
            limit=query.limit,
            offset=query.offset,
            has_more=len(items) == query.limit and (query.offset + query.limit) < total
        )
    
    async def count_by_status(self) -> Dict[str, int]:
        """Count proposals by status."""
        rows = await self.db.fetchall(
            "SELECT status, COUNT(*) as count FROM proposals GROUP BY status"
        )
        return {row["status"]: row["count"] for row in rows}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Calculate proposal metrics.
        
        Returns:
            Dict containing:
            - total_count
            - status_counts (dict)
            - avg_approval_time_seconds (float or None)
        """
        # Status counts
        status_counts = await self.count_by_status()
        total = sum(status_counts.values())
        
        # Avg approval time
        # (reviewed_at - created_at) for approved proposals
        rows = await self.db.fetchall(
            """
            SELECT 
                AVG(strftime('%s', reviewed_at) - strftime('%s', created_at)) as avg_time
            FROM proposals 
            WHERE status = ? AND reviewed_at IS NOT NULL
            """,
            (ProposalStatus.APPROVED.value,)
        )
        avg_time = rows[0]["avg_time"] if rows and rows[0]["avg_time"] is not None else 0.0
        
        return {
            "total_count": total,
            "status_counts": status_counts,
            "avg_approval_time_seconds": float(avg_time)
        }
        
    async def delete_expired(
        self, 
        older_than: datetime,
        statuses: List[ProposalStatus]
    ) -> int:
        """
        Hard delete proposals older than a certain date with specific statuses.
        
        Args:
            older_than: Cutoff date
            statuses: List of statuses to verify (e.g., REJECTED, EXECUTED)
            
        Returns:
            Count of deleted proposals
        """
        status_values = [s.value for s in statuses]
        placeholders = ", ".join("?" for _ in status_values)
        
        async with self.db.transaction() as conn:
            # 1. Find IDs to delete (for history)
            rows = await conn.execute_fetchall(
                f"""
                SELECT id FROM proposals 
                WHERE created_at < ? AND status IN ({placeholders})
                """,
                (older_than.isoformat(), *status_values)
            )
            ids = [row[0] for row in rows]
            
            if not ids:
                return 0
                
            # 2. Delete history
            id_placeholders = ", ".join("?" for _ in ids)
            await conn.execute(
                f"DELETE FROM proposal_history WHERE proposal_id IN ({id_placeholders})",
                tuple(ids)
            )
            
            # 3. Delete proposals
            cursor = await conn.execute(
                f"DELETE FROM proposals WHERE id IN ({id_placeholders})",
                tuple(ids)
            )
            
            return cursor.rowcount
    
    async def get_history(self, proposal_id: str) -> List[ProposalHistoryEntry]:
        """Get history for a proposal."""
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
        """Get proposal and its history."""
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            return None, []
        
        history = await self.get_history(proposal_id)
        return proposal, history
    
    async def save_many(
        self,
        proposals: List[Proposal],
        actor_id: str
    ) -> List[Proposal]:
        """Save multiple proposals in one transaction."""
        async with self.db.transaction() as conn:
            for p in proposals:
                # This calls _insert or _update which use their own transaction blocks
                # Nested transactions in aiosqlite/sqlite use SAVEPOINT
                await self.save(p, actor_id=actor_id)
        
        return proposals
    
    # =========================================================================
    # GOVERNANCE HELPERS
    # =========================================================================
    
    async def approve(
        self,
        proposal_id: str,
        reviewer_id: str,
        comment: Optional[str] = None
    ) -> Proposal:
        """Approve a proposal."""
        # We need to load it, change state, and save
        # To ensure atomicity and handle race conditions, we use a loop with version check
        
        # Simple implementation relying on optimistic locking in save()
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        
        proposal.approve(reviewer_id, comment)
        return await self.save(proposal, reviewer_id, comment, action="approved")
    
    async def reject(
        self,
        proposal_id: str,
        reviewer_id: str,
        reason: str
    ) -> Proposal:
        """Reject a proposal."""
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        
        proposal.reject(reviewer_id, reason)
        return await self.save(proposal, reviewer_id, reason, action="rejected")
    
    async def execute(
        self,
        proposal_id: str,
        executor_id: str,
        result: Dict[str, Any]
    ) -> Proposal:
        """Mark a proposal as executed."""
        proposal = await self.find_by_id(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(proposal_id)
        
        proposal.execute(executor_id, result)
        return await self.save(proposal, executor_id, "Executed", action="executed")
    
    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================
    
    async def _record_history(
        self,
        conn: Any,
        proposal_id: str,
        action: str,
        actor_id: Optional[str],
        timestamp: Optional[datetime] = None,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a history entry."""
        if timestamp is None:
            timestamp = utc_now()
            
        await conn.execute(
            """
            INSERT INTO proposal_history (
                proposal_id, action, actor_id, timestamp, 
                previous_status, new_status, comment, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal_id, action, actor_id, timestamp.isoformat(),
                previous_status, new_status, comment,
                json.dumps(metadata) if metadata else None
            )
        )
