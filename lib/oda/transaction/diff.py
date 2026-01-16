"""
Orion ODA Transaction - Diff Engine
====================================
Phase 5.3.4: Checkpoint comparison and diff operations.

Provides:
- DiffEngine: Compare checkpoints and generate diffs
- ChangedObject: Individual object change record
- CheckpointDiff: Collection of changes between checkpoints

Design Patterns:
- Strategy Pattern: Different diff algorithms
- Builder Pattern: Incremental diff construction
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

from lib.oda.transaction.checkpoint import (
    Checkpoint,
    CheckpointManager,
    ObjectSnapshot,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ChangeType(str, Enum):
    """Type of change detected between checkpoints."""
    ADD = "add"         # Object exists only in target
    MODIFY = "modify"   # Object exists in both but differs
    DELETE = "delete"   # Object exists only in source


class DiffMode(str, Enum):
    """Mode for diff generation."""
    FULL = "full"       # Include all fields in diff
    MINIMAL = "minimal" # Only changed fields
    STRUCTURAL = "structural"  # Only structural changes


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class FieldChange(BaseModel):
    """Change to a single field."""
    model_config = ConfigDict(extra="forbid")

    field_name: str
    old_value: Any = None
    new_value: Any = None


class ChangedObject(BaseModel):
    """
    Record of a single object change between checkpoints.

    Attributes:
        object_type: Type of the object (e.g., "Task", "Agent")
        object_id: Unique identifier of the object
        change_type: Type of change (ADD/MODIFY/DELETE)
        old_value: Previous state (None for ADD)
        new_value: New state (None for DELETE)
        changed_fields: List of fields that changed (for MODIFY)
        old_version: Version before change
        new_version: Version after change
    """
    model_config = ConfigDict(extra="forbid")

    object_type: str
    object_id: str
    change_type: ChangeType
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: List[FieldChange] = Field(default_factory=list)
    old_version: Optional[int] = None
    new_version: Optional[int] = None

    def is_addition(self) -> bool:
        """Check if this is an addition."""
        return self.change_type == ChangeType.ADD

    def is_modification(self) -> bool:
        """Check if this is a modification."""
        return self.change_type == ChangeType.MODIFY

    def is_deletion(self) -> bool:
        """Check if this is a deletion."""
        return self.change_type == ChangeType.DELETE


class CheckpointDiff(BaseModel):
    """
    Collection of changes between two checkpoints.

    Attributes:
        id: Unique diff identifier
        source_checkpoint_id: ID of the source (before) checkpoint
        target_checkpoint_id: ID of the target (after) checkpoint
        created_at: When the diff was generated
        changes: List of object changes
        summary: Summary statistics
    """
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_checkpoint_id: str
    target_checkpoint_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    changes: List[ChangedObject] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)

    def get_additions(self) -> List[ChangedObject]:
        """Get all additions in this diff."""
        return [c for c in self.changes if c.change_type == ChangeType.ADD]

    def get_modifications(self) -> List[ChangedObject]:
        """Get all modifications in this diff."""
        return [c for c in self.changes if c.change_type == ChangeType.MODIFY]

    def get_deletions(self) -> List[ChangedObject]:
        """Get all deletions in this diff."""
        return [c for c in self.changes if c.change_type == ChangeType.DELETE]

    def get_changes_by_type(self, object_type: str) -> List[ChangedObject]:
        """Get all changes for a specific object type."""
        return [c for c in self.changes if c.object_type == object_type]

    def has_conflicts(self) -> bool:
        """Check if diff contains potential conflicts."""
        # Conflicts are modifications to the same object
        seen_ids: Set[Tuple[str, str]] = set()
        for change in self.get_modifications():
            key = (change.object_type, change.object_id)
            if key in seen_ids:
                return True
            seen_ids.add(key)
        return False

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return len(self.changes)


# =============================================================================
# DIFF ENGINE
# =============================================================================

class DiffEngine:
    """
    Engine for comparing checkpoints and generating diffs.

    Provides:
    - generate_diff(): Compare two checkpoints
    - apply_diff(): Apply diff to current state
    - reverse_diff(): Generate reverse diff
    - merge_diffs(): Merge multiple diffs

    Usage:
        engine = DiffEngine(checkpoint_manager)

        # Generate diff
        diff = await engine.generate_diff(
            source_checkpoint_id="cp-001",
            target_checkpoint_id="cp-002"
        )

        # Apply diff
        result = await engine.apply_diff(diff)
    """

    def __init__(self, checkpoint_manager: Optional[CheckpointManager] = None):
        """Initialize diff engine with checkpoint manager."""
        # Lazy initialization: only create CheckpointManager when needed
        self._checkpoint_manager = checkpoint_manager

    @property
    def checkpoint_manager(self) -> CheckpointManager:
        """Lazy-loaded CheckpointManager."""
        if self._checkpoint_manager is None:
            self._checkpoint_manager = CheckpointManager()
        return self._checkpoint_manager

    async def generate_diff(
        self,
        source_checkpoint_id: str,
        target_checkpoint_id: str,
        mode: DiffMode = DiffMode.FULL,
        object_types: Optional[List[str]] = None
    ) -> CheckpointDiff:
        """
        Generate diff between two checkpoints.

        Args:
            source_checkpoint_id: ID of source (before) checkpoint
            target_checkpoint_id: ID of target (after) checkpoint
            mode: Diff generation mode
            object_types: Optional filter for specific object types

        Returns:
            CheckpointDiff containing all changes
        """
        logger.info(f"Generating diff: {source_checkpoint_id} -> {target_checkpoint_id}")

        # Load checkpoints
        source = await self.checkpoint_manager.get_checkpoint(source_checkpoint_id)
        target = await self.checkpoint_manager.get_checkpoint(target_checkpoint_id)

        if source is None:
            raise ValueError(f"Source checkpoint not found: {source_checkpoint_id}")
        if target is None:
            raise ValueError(f"Target checkpoint not found: {target_checkpoint_id}")

        return self.compare_checkpoints(source, target, mode, object_types)

    def compare_checkpoints(
        self,
        source: Checkpoint,
        target: Checkpoint,
        mode: DiffMode = DiffMode.FULL,
        object_types: Optional[List[str]] = None
    ) -> CheckpointDiff:
        """
        Compare two checkpoint objects directly.

        Args:
            source: Source (before) checkpoint
            target: Target (after) checkpoint
            mode: Diff generation mode
            object_types: Optional filter for specific object types

        Returns:
            CheckpointDiff containing all changes
        """
        changes: List[ChangedObject] = []

        # Get all object types from both checkpoints
        all_types = set(source.get_object_types()) | set(target.get_object_types())
        if object_types:
            all_types = all_types & set(object_types)

        # Compare each object type
        for obj_type in all_types:
            source_objects = {obj.object_id: obj for obj in source.get_objects(obj_type)}
            target_objects = {obj.object_id: obj for obj in target.get_objects(obj_type)}

            source_ids = set(source_objects.keys())
            target_ids = set(target_objects.keys())

            # Deletions: in source but not in target
            for obj_id in source_ids - target_ids:
                obj = source_objects[obj_id]
                changes.append(ChangedObject(
                    object_type=obj_type,
                    object_id=obj_id,
                    change_type=ChangeType.DELETE,
                    old_value=obj.data,
                    old_version=obj.version
                ))

            # Additions: in target but not in source
            for obj_id in target_ids - source_ids:
                obj = target_objects[obj_id]
                changes.append(ChangedObject(
                    object_type=obj_type,
                    object_id=obj_id,
                    change_type=ChangeType.ADD,
                    new_value=obj.data,
                    new_version=obj.version
                ))

            # Modifications: in both, check for differences
            for obj_id in source_ids & target_ids:
                source_obj = source_objects[obj_id]
                target_obj = target_objects[obj_id]

                if self._objects_differ(source_obj, target_obj):
                    changed_fields = self._get_changed_fields(
                        source_obj.data,
                        target_obj.data,
                        mode
                    )
                    changes.append(ChangedObject(
                        object_type=obj_type,
                        object_id=obj_id,
                        change_type=ChangeType.MODIFY,
                        old_value=source_obj.data if mode == DiffMode.FULL else None,
                        new_value=target_obj.data if mode == DiffMode.FULL else None,
                        changed_fields=changed_fields,
                        old_version=source_obj.version,
                        new_version=target_obj.version
                    ))

        # Build summary
        summary = {
            "total": len(changes),
            "additions": len([c for c in changes if c.change_type == ChangeType.ADD]),
            "modifications": len([c for c in changes if c.change_type == ChangeType.MODIFY]),
            "deletions": len([c for c in changes if c.change_type == ChangeType.DELETE])
        }

        return CheckpointDiff(
            source_checkpoint_id=source.id,
            target_checkpoint_id=target.id,
            changes=changes,
            summary=summary
        )

    async def apply_diff(
        self,
        diff: CheckpointDiff,
        actor_id: str = "system",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Apply diff to current database state.

        Args:
            diff: The diff to apply
            actor_id: ID of actor applying the diff
            dry_run: If True, only report what would change

        Returns:
            Dict with application results
        """
        logger.info(f"Applying diff: {diff.id} ({diff.total_changes} changes, dry_run={dry_run})")

        results = {
            "diff_id": diff.id,
            "dry_run": dry_run,
            "applied": [],
            "skipped": [],
            "errors": []
        }

        if dry_run:
            # Just report what would happen
            for change in diff.changes:
                results["applied"].append({
                    "type": change.object_type,
                    "id": change.object_id,
                    "action": change.change_type.value
                })
            return results

        # Actually apply changes
        from lib.oda.ontology.storage.database import DatabaseManager
        from lib.oda.ontology.storage.models import (
            ProposalModel,
            OrionActionLogModel,
            OrionInsightModel,
            OrionPatternModel,
            TaskModel,
            AgentModel,
        )
        from sqlalchemy import select, delete, update

        type_to_model = {
            "Proposal": ProposalModel,
            "ActionLog": OrionActionLogModel,
            "Insight": OrionInsightModel,
            "Pattern": OrionPatternModel,
            "Task": TaskModel,
            "Agent": AgentModel,
        }

        db = DatabaseManager.get()

        async with db.transaction() as session:
            for change in diff.changes:
                model_class = type_to_model.get(change.object_type)
                if model_class is None:
                    results["skipped"].append({
                        "type": change.object_type,
                        "id": change.object_id,
                        "reason": "Unknown type"
                    })
                    continue

                try:
                    if change.change_type == ChangeType.ADD:
                        # Insert new object
                        if change.new_value:
                            new_model = model_class(**change.new_value)
                            new_model.created_by = actor_id
                            new_model.updated_by = actor_id
                            session.add(new_model)

                    elif change.change_type == ChangeType.DELETE:
                        # Delete object (soft delete)
                        stmt = (
                            update(model_class)
                            .where(model_class.id == change.object_id)
                            .values(status="deleted", updated_by=actor_id)
                        )
                        await session.execute(stmt)

                    elif change.change_type == ChangeType.MODIFY:
                        # Update object
                        if change.new_value:
                            update_values = {
                                k: v for k, v in change.new_value.items()
                                if k not in ("id", "created_at", "created_by")
                            }
                            update_values["updated_at"] = datetime.now(timezone.utc)
                            update_values["updated_by"] = actor_id
                            stmt = (
                                update(model_class)
                                .where(model_class.id == change.object_id)
                                .values(**update_values)
                            )
                            await session.execute(stmt)

                    results["applied"].append({
                        "type": change.object_type,
                        "id": change.object_id,
                        "action": change.change_type.value
                    })

                except Exception as e:
                    results["errors"].append({
                        "type": change.object_type,
                        "id": change.object_id,
                        "error": str(e)
                    })

        logger.info(f"Diff applied: {len(results['applied'])} changes, {len(results['errors'])} errors")
        return results

    def reverse_diff(self, diff: CheckpointDiff) -> CheckpointDiff:
        """
        Generate reverse of a diff (for rollback).

        Args:
            diff: The diff to reverse

        Returns:
            New CheckpointDiff that undoes the original
        """
        reversed_changes: List[ChangedObject] = []

        for change in diff.changes:
            if change.change_type == ChangeType.ADD:
                # Addition becomes deletion
                reversed_changes.append(ChangedObject(
                    object_type=change.object_type,
                    object_id=change.object_id,
                    change_type=ChangeType.DELETE,
                    old_value=change.new_value,
                    old_version=change.new_version
                ))

            elif change.change_type == ChangeType.DELETE:
                # Deletion becomes addition
                reversed_changes.append(ChangedObject(
                    object_type=change.object_type,
                    object_id=change.object_id,
                    change_type=ChangeType.ADD,
                    new_value=change.old_value,
                    new_version=change.old_version
                ))

            elif change.change_type == ChangeType.MODIFY:
                # Modification reverses old/new
                reversed_fields = [
                    FieldChange(
                        field_name=f.field_name,
                        old_value=f.new_value,
                        new_value=f.old_value
                    )
                    for f in change.changed_fields
                ]
                reversed_changes.append(ChangedObject(
                    object_type=change.object_type,
                    object_id=change.object_id,
                    change_type=ChangeType.MODIFY,
                    old_value=change.new_value,
                    new_value=change.old_value,
                    changed_fields=reversed_fields,
                    old_version=change.new_version,
                    new_version=change.old_version
                ))

        # Swap source and target
        return CheckpointDiff(
            source_checkpoint_id=diff.target_checkpoint_id,
            target_checkpoint_id=diff.source_checkpoint_id,
            changes=reversed_changes,
            summary={
                "total": len(reversed_changes),
                "additions": len([c for c in reversed_changes if c.change_type == ChangeType.ADD]),
                "modifications": len([c for c in reversed_changes if c.change_type == ChangeType.MODIFY]),
                "deletions": len([c for c in reversed_changes if c.change_type == ChangeType.DELETE])
            }
        )

    def merge_diffs(
        self,
        diffs: List[CheckpointDiff],
        resolve_conflicts: bool = False
    ) -> CheckpointDiff:
        """
        Merge multiple diffs into a single diff.

        Args:
            diffs: List of diffs to merge
            resolve_conflicts: If True, attempt automatic conflict resolution

        Returns:
            Merged CheckpointDiff
        """
        if not diffs:
            raise ValueError("Cannot merge empty diff list")

        if len(diffs) == 1:
            return diffs[0]

        merged_changes: Dict[Tuple[str, str], ChangedObject] = {}

        for diff in diffs:
            for change in diff.changes:
                key = (change.object_type, change.object_id)

                if key in merged_changes:
                    existing = merged_changes[key]
                    # Handle conflict
                    if resolve_conflicts:
                        merged_changes[key] = self._resolve_conflict(existing, change)
                    else:
                        # Last write wins
                        merged_changes[key] = change
                else:
                    merged_changes[key] = change

        changes = list(merged_changes.values())

        return CheckpointDiff(
            source_checkpoint_id=diffs[0].source_checkpoint_id,
            target_checkpoint_id=diffs[-1].target_checkpoint_id,
            changes=changes,
            summary={
                "total": len(changes),
                "additions": len([c for c in changes if c.change_type == ChangeType.ADD]),
                "modifications": len([c for c in changes if c.change_type == ChangeType.MODIFY]),
                "deletions": len([c for c in changes if c.change_type == ChangeType.DELETE])
            }
        )

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _objects_differ(self, source: ObjectSnapshot, target: ObjectSnapshot) -> bool:
        """Check if two object snapshots are different."""
        # Quick version check
        if source.version != target.version:
            return True

        # Deep data comparison
        return source.data != target.data

    def _get_changed_fields(
        self,
        source_data: Dict[str, Any],
        target_data: Dict[str, Any],
        mode: DiffMode
    ) -> List[FieldChange]:
        """Get list of changed fields between two data dicts."""
        changes: List[FieldChange] = []

        all_keys = set(source_data.keys()) | set(target_data.keys())

        for key in all_keys:
            old_val = source_data.get(key)
            new_val = target_data.get(key)

            if old_val != new_val:
                changes.append(FieldChange(
                    field_name=key,
                    old_value=old_val if mode != DiffMode.STRUCTURAL else None,
                    new_value=new_val if mode != DiffMode.STRUCTURAL else None
                ))

        return changes

    def _resolve_conflict(
        self,
        existing: ChangedObject,
        incoming: ChangedObject
    ) -> ChangedObject:
        """
        Resolve conflict between two changes to same object.

        Strategy: Merge modifications, incoming wins for type conflicts.
        """
        # If same change type, merge
        if existing.change_type == incoming.change_type == ChangeType.MODIFY:
            # Merge field changes
            existing_fields = {f.field_name: f for f in existing.changed_fields}
            for field in incoming.changed_fields:
                existing_fields[field.field_name] = field

            # Merge new_value dicts
            merged_value = {}
            if existing.new_value:
                merged_value.update(existing.new_value)
            if incoming.new_value:
                merged_value.update(incoming.new_value)

            return ChangedObject(
                object_type=existing.object_type,
                object_id=existing.object_id,
                change_type=ChangeType.MODIFY,
                old_value=existing.old_value,
                new_value=merged_value,
                changed_fields=list(existing_fields.values()),
                old_version=existing.old_version,
                new_version=incoming.new_version
            )

        # Otherwise, incoming wins
        return incoming
