"""
Orion ODA v3.0 - Undo History Storage
Palantir Foundry Compliant Undo Snapshot Persistence

This module implements persistent storage for undo snapshots.
Foundry Pattern: All undoable operations must persist their snapshots for:
- Cross-session undo capability
- Audit compliance
- Batch rollback support

Storage Design:
1. SQLAlchemy model for undo snapshots
2. Repository pattern for CRUD operations
3. Efficient querying by action, object, or time range
4. Automatic cleanup of old snapshots
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import String, JSON, DateTime, Text, Integer, Boolean, Index, select, and_, delete
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from lib.oda.ontology.storage.orm import AsyncOntologyObject, Base
from lib.oda.ontology.actions.undoable import UndoSnapshot, UndoStatus, UndoResult

logger = logging.getLogger(__name__)


# =============================================================================
# UNDO SNAPSHOT MODEL
# =============================================================================

class UndoSnapshotModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for persisting UndoSnapshots.

    Foundry Pattern: Undo snapshots are persisted for:
    - Cross-session recovery
    - Audit trail
    - Batch rollback operations
    """
    __tablename__ = "undo_snapshots"

    # Action identification
    action_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        unique=True,
        comment="Unique ID of the action execution"
    )
    action_api_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="API name of the action"
    )
    action_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the action was executed"
    )
    actor_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Who executed the action"
    )

    # Object reference
    object_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Type of affected object"
    )
    object_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="ID of affected object"
    )

    # State snapshots (JSON)
    previous_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Object state before action"
    )
    new_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Object state after action"
    )

    # Action parameters
    params: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        comment="Action parameters for replay"
    )

    # Undo configuration
    is_undoable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Whether this can be undone"
    )
    undo_method: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Custom undo method name"
    )
    undo_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Custom undo parameters"
    )

    # Tracking
    correlation_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Trace ID for distributed tracking"
    )
    parent_batch_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Batch ID if part of batch operation"
    )

    # Undo status tracking
    undo_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        index=True,
        comment="Status: pending, success, failed, skipped"
    )
    undo_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When undo was executed"
    )
    undo_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if undo failed"
    )

    __table_args__ = (
        # Composite indexes for common queries
        Index('idx_undo_object', 'object_type', 'object_id'),
        Index('idx_undo_actor_time', 'actor_id', 'action_timestamp'),
        Index('idx_undo_status_time', 'undo_status', 'action_timestamp'),
        Index('idx_undo_batch', 'parent_batch_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<UndoSnapshot(action_id={self.action_id}, "
            f"action={self.action_api_name}, status={self.undo_status})>"
        )

    def to_domain(self) -> UndoSnapshot:
        """Convert to domain UndoSnapshot object."""
        return UndoSnapshot(
            action_id=self.action_id,
            action_api_name=self.action_api_name,
            timestamp=self.action_timestamp,
            actor_id=self.actor_id,
            object_type=self.object_type,
            object_id=self.object_id,
            previous_state=self.previous_state,
            new_state=self.new_state,
            params=self.params or {},
            is_undoable=self.is_undoable,
            undo_method=self.undo_method,
            undo_params=self.undo_params,
            correlation_id=self.correlation_id,
            parent_batch_id=self.parent_batch_id,
            undo_status=UndoStatus(self.undo_status),
            undo_timestamp=self.undo_timestamp,
            undo_error=self.undo_error,
        )

    @classmethod
    def from_domain(cls, snapshot: UndoSnapshot) -> "UndoSnapshotModel":
        """Create model from domain UndoSnapshot object."""
        return cls(
            action_id=snapshot.action_id,
            action_api_name=snapshot.action_api_name,
            action_timestamp=snapshot.timestamp,
            actor_id=snapshot.actor_id,
            object_type=snapshot.object_type,
            object_id=snapshot.object_id,
            previous_state=snapshot.previous_state,
            new_state=snapshot.new_state,
            params=snapshot.params,
            is_undoable=snapshot.is_undoable,
            undo_method=snapshot.undo_method,
            undo_params=snapshot.undo_params,
            correlation_id=snapshot.correlation_id,
            parent_batch_id=snapshot.parent_batch_id,
            undo_status=snapshot.undo_status.value,
            undo_timestamp=snapshot.undo_timestamp,
            undo_error=snapshot.undo_error,
        )


# =============================================================================
# UNDO HISTORY REPOSITORY
# =============================================================================

class UndoHistoryRepository:
    """
    Repository for UndoSnapshot persistence.

    Foundry Pattern: Provides CRUD operations for undo history with:
    - Efficient querying by action, object, or time
    - Batch operations for rollback
    - Automatic cleanup of old snapshots
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, snapshot: UndoSnapshot) -> UndoSnapshotModel:
        """
        Save an undo snapshot to the database.

        Args:
            snapshot: The UndoSnapshot to persist

        Returns:
            The persisted model instance
        """
        model = UndoSnapshotModel.from_domain(snapshot)
        self.session.add(model)
        await self.session.flush()
        logger.debug(f"Saved undo snapshot: {snapshot.action_id}")
        return model

    async def get_by_action_id(self, action_id: str) -> Optional[UndoSnapshot]:
        """
        Get a snapshot by its action ID.

        Args:
            action_id: The unique action ID

        Returns:
            UndoSnapshot if found, None otherwise
        """
        stmt = select(UndoSnapshotModel).where(
            UndoSnapshotModel.action_id == action_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_object(
        self,
        object_type: str,
        object_id: str,
        limit: int = 100,
        include_undone: bool = False,
    ) -> List[UndoSnapshot]:
        """
        Get snapshots for a specific object.

        Args:
            object_type: Type of the object
            object_id: ID of the object
            limit: Maximum number of results
            include_undone: Include already-undone snapshots?

        Returns:
            List of UndoSnapshots (most recent first)
        """
        conditions = [
            UndoSnapshotModel.object_type == object_type,
            UndoSnapshotModel.object_id == object_id,
        ]

        if not include_undone:
            conditions.append(UndoSnapshotModel.undo_status == "pending")

        stmt = (
            select(UndoSnapshotModel)
            .where(and_(*conditions))
            .order_by(UndoSnapshotModel.action_timestamp.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def get_by_actor(
        self,
        actor_id: str,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[UndoSnapshot]:
        """
        Get snapshots created by a specific actor.

        Args:
            actor_id: The actor ID
            since: Optional start time filter
            limit: Maximum number of results

        Returns:
            List of UndoSnapshots (most recent first)
        """
        conditions = [
            UndoSnapshotModel.actor_id == actor_id,
            UndoSnapshotModel.undo_status == "pending",
        ]

        if since:
            conditions.append(UndoSnapshotModel.action_timestamp >= since)

        stmt = (
            select(UndoSnapshotModel)
            .where(and_(*conditions))
            .order_by(UndoSnapshotModel.action_timestamp.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def get_by_batch(self, batch_id: str) -> List[UndoSnapshot]:
        """
        Get all snapshots in a batch.

        Args:
            batch_id: The batch ID

        Returns:
            List of UndoSnapshots in execution order
        """
        stmt = (
            select(UndoSnapshotModel)
            .where(UndoSnapshotModel.parent_batch_id == batch_id)
            .order_by(UndoSnapshotModel.action_timestamp)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def get_pending_for_action_type(
        self,
        action_api_name: str,
        limit: int = 100,
    ) -> List[UndoSnapshot]:
        """
        Get pending (undoable) snapshots for an action type.

        Args:
            action_api_name: The action API name
            limit: Maximum number of results

        Returns:
            List of pending UndoSnapshots
        """
        stmt = (
            select(UndoSnapshotModel)
            .where(
                and_(
                    UndoSnapshotModel.action_api_name == action_api_name,
                    UndoSnapshotModel.undo_status == "pending",
                    UndoSnapshotModel.is_undoable == True,
                )
            )
            .order_by(UndoSnapshotModel.action_timestamp.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def update_undo_status(
        self,
        action_id: str,
        status: UndoStatus,
        error: Optional[str] = None,
    ) -> bool:
        """
        Update the undo status of a snapshot.

        Args:
            action_id: The action ID
            status: New undo status
            error: Optional error message

        Returns:
            True if updated, False if not found
        """
        stmt = select(UndoSnapshotModel).where(
            UndoSnapshotModel.action_id == action_id
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return False

        model.undo_status = status.value
        model.undo_timestamp = datetime.now(timezone.utc)
        if error:
            model.undo_error = error

        await self.session.flush()
        logger.debug(f"Updated undo status for {action_id}: {status.value}")
        return True

    async def get_recent_undoable(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[UndoSnapshot]:
        """
        Get recent undoable snapshots.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of results

        Returns:
            List of recent undoable snapshots
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = (
            select(UndoSnapshotModel)
            .where(
                and_(
                    UndoSnapshotModel.action_timestamp >= since,
                    UndoSnapshotModel.undo_status == "pending",
                    UndoSnapshotModel.is_undoable == True,
                )
            )
            .order_by(UndoSnapshotModel.action_timestamp.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def cleanup_old_snapshots(
        self,
        older_than_days: int = 30,
        keep_undone: bool = True,
    ) -> int:
        """
        Delete old undo snapshots.

        Args:
            older_than_days: Delete snapshots older than this
            keep_undone: Keep snapshots that were undone (for audit)?

        Returns:
            Number of deleted snapshots
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        conditions = [UndoSnapshotModel.action_timestamp < cutoff]

        if keep_undone:
            # Only delete pending snapshots that are too old
            conditions.append(UndoSnapshotModel.undo_status == "pending")

        stmt = delete(UndoSnapshotModel).where(and_(*conditions))
        result = await self.session.execute(stmt)
        await self.session.flush()

        deleted = result.rowcount
        logger.info(f"Cleaned up {deleted} old undo snapshots")
        return deleted

    async def count_pending(self) -> int:
        """Count pending undo snapshots."""
        from sqlalchemy import func

        stmt = select(func.count(UndoSnapshotModel.id)).where(
            UndoSnapshotModel.undo_status == "pending"
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about undo history.

        Returns:
            Dict with counts by status and action type
        """
        from sqlalchemy import func

        # Count by status
        status_stmt = (
            select(
                UndoSnapshotModel.undo_status,
                func.count(UndoSnapshotModel.id)
            )
            .group_by(UndoSnapshotModel.undo_status)
        )
        status_result = await self.session.execute(status_stmt)
        by_status = dict(status_result.all())

        # Count by action type (pending only)
        action_stmt = (
            select(
                UndoSnapshotModel.action_api_name,
                func.count(UndoSnapshotModel.id)
            )
            .where(UndoSnapshotModel.undo_status == "pending")
            .group_by(UndoSnapshotModel.action_api_name)
        )
        action_result = await self.session.execute(action_stmt)
        by_action = dict(action_result.all())

        return {
            "by_status": by_status,
            "by_action": by_action,
            "total_pending": by_status.get("pending", 0),
        }


# =============================================================================
# UNDO HISTORY MANAGER
# =============================================================================

class UndoHistoryManager:
    """
    High-level manager for undo history operations.

    Provides a clean interface for:
    - Recording action executions
    - Finding undoable operations
    - Performing undo operations
    """

    def __init__(self, repository: UndoHistoryRepository):
        self.repository = repository

    async def record_action(
        self,
        snapshot: UndoSnapshot,
    ) -> None:
        """
        Record an action execution for potential undo.

        Args:
            snapshot: The captured undo snapshot
        """
        await self.repository.save(snapshot)

    async def get_undoable_for_object(
        self,
        object_type: str,
        object_id: str,
    ) -> List[UndoSnapshot]:
        """
        Get actions that can be undone for an object.

        Args:
            object_type: Type of the object
            object_id: ID of the object

        Returns:
            List of undoable snapshots (most recent first)
        """
        return await self.repository.get_by_object(
            object_type=object_type,
            object_id=object_id,
            include_undone=False,
        )

    async def get_user_history(
        self,
        actor_id: str,
        hours: int = 24,
    ) -> List[UndoSnapshot]:
        """
        Get a user's undoable actions.

        Args:
            actor_id: The user/actor ID
            hours: Number of hours to look back

        Returns:
            List of undoable snapshots
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return await self.repository.get_by_actor(actor_id=actor_id, since=since)

    async def mark_undone(
        self,
        action_id: str,
        result: UndoResult,
    ) -> None:
        """
        Mark an action as undone.

        Args:
            action_id: The action ID
            result: The undo result
        """
        await self.repository.update_undo_status(
            action_id=action_id,
            status=result.status,
            error=result.error,
        )

    async def get_batch_snapshots(self, batch_id: str) -> List[UndoSnapshot]:
        """
        Get all snapshots in a batch for batch rollback.

        Args:
            batch_id: The batch ID

        Returns:
            List of snapshots in the batch
        """
        return await self.repository.get_by_batch(batch_id)
