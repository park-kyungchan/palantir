"""
Orion ODA Transaction - Checkpoint System
==========================================
Phase 5.3: Checkpoint creation, storage, and restoration.

Provides immutable state snapshots for:
- Point-in-time recovery
- Branch management
- State comparison (via DiffEngine)

Design Patterns:
- Memento Pattern: Capture and restore state
- Repository Pattern: Checkpoint persistence
- Builder Pattern: Checkpoint creation with optional metadata
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

from sqlalchemy import String, JSON, DateTime, Text, Integer, Index, select, delete
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from lib.oda.ontology.storage.orm import AsyncOntologyObject, Base
from lib.oda.ontology.storage.database import Database, DatabaseManager

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class SnapshotType(str, Enum):
    """Type of snapshot captured in checkpoint."""
    FULL = "full"           # Complete state snapshot
    INCREMENTAL = "incremental"  # Delta from previous checkpoint
    SELECTIVE = "selective"  # Specific object types only


# =============================================================================
# PYDANTIC MODELS (Domain Objects)
# =============================================================================

class CheckpointMetadata(BaseModel):
    """Metadata associated with a checkpoint."""
    model_config = ConfigDict(extra="forbid")

    description: str = ""
    tags: List[str] = Field(default_factory=list)
    created_by: str = "system"
    source_action: Optional[str] = None  # Action that triggered checkpoint
    parent_checkpoint_id: Optional[str] = None  # For incremental snapshots

    # Statistics
    object_count: int = 0
    size_bytes: int = 0


class ObjectSnapshot(BaseModel):
    """Snapshot of a single object's state."""
    model_config = ConfigDict(extra="forbid")

    object_type: str
    object_id: str
    version: int
    data: Dict[str, Any]
    created_at: datetime


class Checkpoint(BaseModel):
    """
    Immutable state snapshot at a point in time.

    A Checkpoint captures the complete or partial state of the system
    at a specific moment. Once created, checkpoints are immutable.

    Attributes:
        id: Unique checkpoint identifier
        name: Human-readable checkpoint name
        branch_id: ID of the branch this checkpoint belongs to
        created_at: Timestamp of checkpoint creation
        snapshot_type: Type of snapshot (full/incremental/selective)
        snapshot_data: Serialized state data
        metadata: Additional checkpoint metadata
    """
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    branch_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot_type: SnapshotType = SnapshotType.FULL
    snapshot_data: Dict[str, List[ObjectSnapshot]] = Field(default_factory=dict)
    metadata: CheckpointMetadata = Field(default_factory=CheckpointMetadata)

    def get_object_types(self) -> List[str]:
        """Get list of object types in this checkpoint."""
        return list(self.snapshot_data.keys())

    def get_objects(self, object_type: str) -> List[ObjectSnapshot]:
        """Get all snapshots for a specific object type."""
        return self.snapshot_data.get(object_type, [])

    def get_object_by_id(self, object_type: str, object_id: str) -> Optional[ObjectSnapshot]:
        """Find specific object snapshot by type and ID."""
        for obj in self.snapshot_data.get(object_type, []):
            if obj.object_id == object_id:
                return obj
        return None

    def to_json(self) -> str:
        """Serialize checkpoint to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "Checkpoint":
        """Deserialize checkpoint from JSON string."""
        return cls.model_validate_json(json_str)


# =============================================================================
# SQLALCHEMY MODEL
# =============================================================================

class CheckpointModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Checkpoint persistence.

    Maps 1:1 with the Checkpoint Pydantic model.
    """
    __tablename__ = "checkpoints"

    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    snapshot_type: Mapped[str] = mapped_column(String(20), default="full")

    # Snapshot data (JSON serialized)
    snapshot_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Metadata (JSON serialized)
    checkpoint_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Search and indexing
    fts_content: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (
        Index('idx_checkpoint_branch', 'branch_id'),
        Index('idx_checkpoint_created', 'created_at'),
        Index('idx_checkpoint_name', 'name'),
    )

    def __repr__(self) -> str:
        return f"<Checkpoint(id={self.id}, name={self.name}, type={self.snapshot_type})>"


# =============================================================================
# CHECKPOINT MANAGER
# =============================================================================

class CheckpointManager:
    """
    Manages checkpoint lifecycle operations.

    Provides:
    - create_checkpoint(): Capture current state
    - restore_checkpoint(): Restore system to checkpoint state
    - list_checkpoints(): Query checkpoints by branch/time
    - delete_checkpoint(): Remove checkpoint (soft delete)

    Usage:
        manager = CheckpointManager(db)

        # Create checkpoint
        checkpoint = await manager.create_checkpoint(
            name="pre-migration",
            object_types=["Task", "Agent"],
            metadata={"description": "Before schema migration"}
        )

        # Restore checkpoint
        await manager.restore_checkpoint(checkpoint.id)
    """

    def __init__(self, db: Optional[Database] = None):
        """Initialize checkpoint manager with database connection."""
        self.db = db or DatabaseManager.get()

    async def create_checkpoint(
        self,
        name: str,
        branch_id: Optional[str] = None,
        object_types: Optional[List[str]] = None,
        snapshot_type: SnapshotType = SnapshotType.FULL,
        metadata: Optional[Dict[str, Any]] = None,
        actor_id: str = "system"
    ) -> Checkpoint:
        """
        Create a new checkpoint capturing current state.

        Args:
            name: Human-readable checkpoint name
            branch_id: Optional branch ID to associate with
            object_types: List of object types to capture (None = all)
            snapshot_type: Type of snapshot to create
            metadata: Optional metadata dict
            actor_id: ID of actor creating checkpoint

        Returns:
            Created Checkpoint instance
        """
        logger.info(f"Creating checkpoint: {name}")

        # Capture state snapshot
        snapshot_data = await self._capture_snapshot(
            object_types=object_types,
            snapshot_type=snapshot_type
        )

        # Build metadata
        checkpoint_metadata = CheckpointMetadata(
            created_by=actor_id,
            object_count=sum(len(objs) for objs in snapshot_data.values()),
            **(metadata or {})
        )

        # Create checkpoint domain object
        checkpoint = Checkpoint(
            name=name,
            branch_id=branch_id,
            snapshot_type=snapshot_type,
            snapshot_data=snapshot_data,
            metadata=checkpoint_metadata
        )

        # Persist to database
        async with self.db.transaction() as session:
            model = self._to_model(checkpoint, actor_id)
            session.add(model)

        logger.info(f"Checkpoint created: {checkpoint.id} ({checkpoint_metadata.object_count} objects)")
        return checkpoint

    async def restore_checkpoint(
        self,
        checkpoint_id: str,
        actor_id: str = "system",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Restore system state to a checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to restore
            actor_id: ID of actor performing restore
            dry_run: If True, only report what would change

        Returns:
            Dict with restore results: {"restored": [...], "errors": [...]}
        """
        logger.info(f"Restoring checkpoint: {checkpoint_id} (dry_run={dry_run})")

        checkpoint = await self.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        results = {
            "checkpoint_id": checkpoint_id,
            "checkpoint_name": checkpoint.name,
            "dry_run": dry_run,
            "restored": [],
            "skipped": [],
            "errors": []
        }

        if dry_run:
            # Report what would be restored
            for obj_type, objects in checkpoint.snapshot_data.items():
                for obj in objects:
                    results["restored"].append({
                        "type": obj_type,
                        "id": obj.object_id,
                        "version": obj.version
                    })
        else:
            # Actually restore state
            results = await self._apply_restore(checkpoint, actor_id)

        logger.info(f"Checkpoint restore complete: {len(results['restored'])} objects")
        return results

    async def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get checkpoint by ID."""
        async with self.db.transaction() as session:
            stmt = select(CheckpointModel).where(CheckpointModel.id == checkpoint_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def list_checkpoints(
        self,
        branch_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Checkpoint]:
        """
        List checkpoints with optional filters.

        Args:
            branch_id: Filter by branch ID
            since: Filter by creation time (after)
            until: Filter by creation time (before)
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of Checkpoint instances
        """
        async with self.db.transaction() as session:
            stmt = select(CheckpointModel).order_by(CheckpointModel.created_at.desc())

            if branch_id is not None:
                stmt = stmt.where(CheckpointModel.branch_id == branch_id)
            if since is not None:
                stmt = stmt.where(CheckpointModel.created_at >= since)
            if until is not None:
                stmt = stmt.where(CheckpointModel.created_at <= until)

            stmt = stmt.offset(offset).limit(limit)

            result = await session.execute(stmt)
            models = result.scalars().all()
            return [self._to_domain(m) for m in models]

    async def delete_checkpoint(
        self,
        checkpoint_id: str,
        actor_id: str = "system",
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to delete
            actor_id: ID of actor performing deletion
            hard_delete: If True, permanently remove; else soft delete

        Returns:
            True if deleted, False if not found
        """
        async with self.db.transaction() as session:
            if hard_delete:
                stmt = delete(CheckpointModel).where(CheckpointModel.id == checkpoint_id)
                result = await session.execute(stmt)
                return result.rowcount > 0
            else:
                # Soft delete by setting status
                from sqlalchemy import update
                stmt = (
                    update(CheckpointModel)
                    .where(CheckpointModel.id == checkpoint_id)
                    .values(status="deleted", updated_by=actor_id)
                )
                result = await session.execute(stmt)
                return result.rowcount > 0

    async def get_latest_checkpoint(self, branch_id: Optional[str] = None) -> Optional[Checkpoint]:
        """Get the most recent checkpoint, optionally filtered by branch."""
        checkpoints = await self.list_checkpoints(branch_id=branch_id, limit=1)
        return checkpoints[0] if checkpoints else None

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    async def _capture_snapshot(
        self,
        object_types: Optional[List[str]] = None,
        snapshot_type: SnapshotType = SnapshotType.FULL
    ) -> Dict[str, List[ObjectSnapshot]]:
        """
        Capture current state from database.

        For FULL snapshots, captures all objects of specified types.
        For SELECTIVE, only captures specified types.
        """
        snapshot_data: Dict[str, List[ObjectSnapshot]] = {}

        # Get all table models to snapshot
        from lib.oda.ontology.storage.models import (
            ProposalModel,
            OrionActionLogModel,
            OrionInsightModel,
            OrionPatternModel,
            TaskModel,
            AgentModel,
        )

        # Map object type names to models
        type_to_model = {
            "Proposal": ProposalModel,
            "ActionLog": OrionActionLogModel,
            "Insight": OrionInsightModel,
            "Pattern": OrionPatternModel,
            "Task": TaskModel,
            "Agent": AgentModel,
        }

        # Filter to requested types
        if object_types:
            type_to_model = {k: v for k, v in type_to_model.items() if k in object_types}

        async with self.db.transaction() as session:
            for obj_type, model_class in type_to_model.items():
                try:
                    stmt = select(model_class)
                    if snapshot_type != SnapshotType.FULL:
                        # For non-full, only get active items
                        stmt = stmt.where(model_class.status != "deleted")

                    result = await session.execute(stmt)
                    models = result.scalars().all()

                    snapshots = []
                    for model in models:
                        # Convert model to snapshot
                        snapshot = ObjectSnapshot(
                            object_type=obj_type,
                            object_id=model.id,
                            version=model.version,
                            data=self._model_to_dict(model),
                            created_at=model.created_at or datetime.now(timezone.utc)
                        )
                        snapshots.append(snapshot)

                    if snapshots:
                        snapshot_data[obj_type] = snapshots

                except Exception as e:
                    logger.warning(f"Failed to snapshot {obj_type}: {e}")

        return snapshot_data

    async def _apply_restore(
        self,
        checkpoint: Checkpoint,
        actor_id: str
    ) -> Dict[str, Any]:
        """Apply checkpoint restore to database."""
        results = {
            "checkpoint_id": checkpoint.id,
            "checkpoint_name": checkpoint.name,
            "dry_run": False,
            "restored": [],
            "skipped": [],
            "errors": []
        }

        # Import models for restore
        from lib.oda.ontology.storage.models import (
            ProposalModel,
            OrionActionLogModel,
            OrionInsightModel,
            OrionPatternModel,
            TaskModel,
            AgentModel,
        )

        type_to_model = {
            "Proposal": ProposalModel,
            "ActionLog": OrionActionLogModel,
            "Insight": OrionInsightModel,
            "Pattern": OrionPatternModel,
            "Task": TaskModel,
            "Agent": AgentModel,
        }

        async with self.db.transaction() as session:
            for obj_type, objects in checkpoint.snapshot_data.items():
                model_class = type_to_model.get(obj_type)
                if model_class is None:
                    for obj in objects:
                        results["skipped"].append({
                            "type": obj_type,
                            "id": obj.object_id,
                            "reason": "Unknown type"
                        })
                    continue

                for obj in objects:
                    try:
                        # Check if object exists
                        stmt = select(model_class).where(model_class.id == obj.object_id)
                        result = await session.execute(stmt)
                        existing = result.scalar_one_or_none()

                        if existing:
                            # Update existing
                            for key, value in obj.data.items():
                                if hasattr(existing, key) and key not in ("id", "created_at"):
                                    setattr(existing, key, value)
                            existing.updated_at = datetime.now(timezone.utc)
                            existing.updated_by = actor_id
                        else:
                            # Insert new
                            new_model = model_class(**obj.data)
                            new_model.created_by = actor_id
                            new_model.updated_by = actor_id
                            session.add(new_model)

                        results["restored"].append({
                            "type": obj_type,
                            "id": obj.object_id,
                            "action": "update" if existing else "insert"
                        })

                    except Exception as e:
                        results["errors"].append({
                            "type": obj_type,
                            "id": obj.object_id,
                            "error": str(e)
                        })

        return results

    def _model_to_dict(self, model: AsyncOntologyObject) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dict for snapshotting."""
        from sqlalchemy import inspect

        mapper = inspect(model.__class__)
        data = {}
        for column in mapper.columns:
            value = getattr(model, column.key)
            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            data[column.key] = value
        return data

    def _to_model(self, checkpoint: Checkpoint, actor_id: str) -> CheckpointModel:
        """Convert Checkpoint domain object to ORM model."""
        # Serialize snapshot_data
        snapshot_dict = {}
        for obj_type, objects in checkpoint.snapshot_data.items():
            snapshot_dict[obj_type] = [obj.model_dump(mode='json') for obj in objects]

        return CheckpointModel(
            id=checkpoint.id,
            name=checkpoint.name,
            branch_id=checkpoint.branch_id,
            snapshot_type=checkpoint.snapshot_type.value,
            snapshot_data=snapshot_dict,
            checkpoint_metadata=checkpoint.metadata.model_dump(mode='json'),
            created_at=checkpoint.created_at,
            created_by=actor_id,
            updated_by=actor_id,
            fts_content=f"{checkpoint.name} {checkpoint.metadata.description}",
        )

    def _to_domain(self, model: CheckpointModel) -> Checkpoint:
        """Convert ORM model to Checkpoint domain object."""
        # Deserialize snapshot_data
        snapshot_data = {}
        for obj_type, objects in (model.snapshot_data or {}).items():
            snapshot_data[obj_type] = [ObjectSnapshot(**obj) for obj in objects]

        return Checkpoint(
            id=model.id,
            name=model.name,
            branch_id=model.branch_id,
            created_at=model.created_at,
            snapshot_type=SnapshotType(model.snapshot_type),
            snapshot_data=snapshot_data,
            metadata=CheckpointMetadata(**(model.checkpoint_metadata or {}))
        )
