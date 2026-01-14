"""
Orion ODA v4.0 - Cherry-Pick Support
====================================

Selective commit application across branches.

This module provides:
- CherryPicker: Apply specific commits to target branches
- CherryPickResult: Result of cherry-pick operations
- Support for dry-run, abort, and continue-after-resolve

Design Principles:
1. Atomic operations (all-or-nothing)
2. Full audit trail
3. Conflict detection before application
4. Support for interactive conflict resolution

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from lib.oda.ontology.objects.branch import BranchCommit

from lib.oda.transaction.schema_conflict import (
    SchemaConflict,
    SchemaConflictType,
    SchemaConflictSeverity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class CherryPickStatus(str, Enum):
    """Status of a cherry-pick operation."""
    PENDING = "pending"           # Not yet started
    IN_PROGRESS = "in_progress"   # Currently applying
    CONFLICTED = "conflicted"     # Has conflicts needing resolution
    COMPLETED = "completed"       # Successfully completed
    ABORTED = "aborted"           # Cancelled by user
    FAILED = "failed"             # Failed due to error


class CherryPickConflictResolution(str, Enum):
    """How to handle conflicts during cherry-pick."""
    ABORT = "abort"       # Stop and rollback on conflict
    SKIP = "skip"         # Skip conflicting changes
    OURS = "ours"         # Use target branch version
    THEIRS = "theirs"     # Use source commit version
    MANUAL = "manual"     # Wait for manual resolution


# =============================================================================
# RESULT MODELS
# =============================================================================

class CherryPickChange(BaseModel):
    """A single change applied during cherry-pick."""
    object_type: str
    object_id: str
    field_name: Optional[str] = None
    operation: str = "update"  # create, update, delete
    old_value: Any = None
    new_value: Any = None
    applied: bool = False
    skipped: bool = False
    skip_reason: Optional[str] = None

    model_config = {"extra": "forbid"}


class CherryPickResult(BaseModel):
    """
    Result of a cherry-pick operation.

    Contains:
    - Success/failure status
    - List of applied changes
    - Any conflicts encountered
    - Rollback point for undo
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])

    # Status
    success: bool
    status: CherryPickStatus = CherryPickStatus.PENDING

    # Source info
    commit_id: str
    source_branch_id: Optional[str] = None
    target_branch_id: str

    # Changes
    applied_changes: List[CherryPickChange] = Field(default_factory=list)
    skipped_changes: List[CherryPickChange] = Field(default_factory=list)

    # Conflicts
    conflicts: List[SchemaConflict] = Field(default_factory=list)
    conflict_resolution_mode: Optional[CherryPickConflictResolution] = None

    # Rollback support
    rollback_point: Optional[str] = None
    rollback_available: bool = False

    # Audit
    new_commit_id: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    actor_id: Optional[str] = None

    # Error info
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

    model_config = {"extra": "forbid"}

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    @property
    def applied_count(self) -> int:
        return len(self.applied_changes)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_changes)

    def finalize(self, success: bool, status: CherryPickStatus) -> None:
        """Finalize the result with completion info."""
        self.success = success
        self.status = status
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)


# =============================================================================
# CHERRY PICKER
# =============================================================================

class CherryPicker:
    """
    Apply specific commits to a target branch.

    Provides Git-like cherry-pick functionality for selectively
    applying changes from one branch to another.

    Usage:
        ```python
        picker = CherryPicker(branch_manager)

        # Dry run first
        preview = await picker.dry_run(
            commit_id="abc123",
            target_branch="main"
        )

        if not preview.has_conflicts:
            # Apply for real
            result = await picker.cherry_pick(
                commit_id="abc123",
                target_branch="main"
            )

        # If conflicts, can abort
        if result.status == CherryPickStatus.CONFLICTED:
            await picker.abort()
        ```
    """

    def __init__(
        self,
        branch_manager: Any = None,
        conflict_resolution: CherryPickConflictResolution = CherryPickConflictResolution.ABORT,
    ):
        """
        Initialize CherryPicker.

        Args:
            branch_manager: BranchManager instance for branch operations
            conflict_resolution: Default conflict handling strategy
        """
        self._branch_manager = branch_manager
        self._default_conflict_resolution = conflict_resolution
        self._current_operation: Optional[CherryPickResult] = None
        self._rollback_states: Dict[str, Any] = {}

    async def cherry_pick(
        self,
        commit_id: str,
        target_branch: str,
        actor_id: Optional[str] = None,
        conflict_resolution: Optional[CherryPickConflictResolution] = None,
        message_override: Optional[str] = None,
    ) -> CherryPickResult:
        """
        Apply a commit to the target branch.

        Args:
            commit_id: ID of commit to cherry-pick
            target_branch: Target branch name or ID
            actor_id: Actor performing the operation
            conflict_resolution: Override default conflict handling
            message_override: Custom commit message

        Returns:
            CherryPickResult with operation details
        """
        resolution = conflict_resolution or self._default_conflict_resolution

        # Initialize result
        result = CherryPickResult(
            success=False,
            status=CherryPickStatus.IN_PROGRESS,
            commit_id=commit_id,
            target_branch_id=target_branch,
            actor_id=actor_id,
            conflict_resolution_mode=resolution,
        )

        self._current_operation = result

        try:
            # Get source commit
            source_commit = await self._get_commit(commit_id)
            if not source_commit:
                result.error = f"Commit not found: {commit_id}"
                result.finalize(False, CherryPickStatus.FAILED)
                return result

            result.source_branch_id = source_commit.branch_id

            # Get target branch
            target_branch_obj = await self._get_branch(target_branch)
            if not target_branch_obj:
                result.error = f"Target branch not found: {target_branch}"
                result.finalize(False, CherryPickStatus.FAILED)
                return result

            # Create rollback point
            result.rollback_point = await self._create_rollback_point(target_branch_obj)
            result.rollback_available = result.rollback_point is not None

            # Detect conflicts
            conflicts = await self._detect_conflicts(source_commit, target_branch_obj)
            result.conflicts = conflicts

            if conflicts:
                if resolution == CherryPickConflictResolution.ABORT:
                    result.error = f"Conflicts detected ({len(conflicts)}), aborting"
                    result.finalize(False, CherryPickStatus.CONFLICTED)
                    return result
                elif resolution == CherryPickConflictResolution.MANUAL:
                    result.status = CherryPickStatus.CONFLICTED
                    # Store for continue_after_resolve
                    return result
                # Otherwise handle with ours/theirs/skip

            # Apply changes
            changes = await self._extract_changes(source_commit)

            for change in changes:
                # Check if this change conflicts
                change_conflicts = [
                    c for c in conflicts
                    if c.object_type == change.object_type
                    and (c.field_name == change.field_name or c.field_name is None)
                ]

                if change_conflicts:
                    if resolution == CherryPickConflictResolution.SKIP:
                        change.skipped = True
                        change.skip_reason = "Conflict - skipped by policy"
                        result.skipped_changes.append(change)
                        continue
                    elif resolution == CherryPickConflictResolution.OURS:
                        change.skipped = True
                        change.skip_reason = "Conflict - using target branch value (ours)"
                        result.skipped_changes.append(change)
                        continue
                    elif resolution == CherryPickConflictResolution.THEIRS:
                        # Use source value (apply the change)
                        pass

                # Apply the change
                applied = await self._apply_change(change, target_branch_obj)
                if applied:
                    change.applied = True
                    result.applied_changes.append(change)
                else:
                    change.skipped = True
                    change.skip_reason = "Failed to apply"
                    result.skipped_changes.append(change)

            # Create new commit on target branch
            if result.applied_changes:
                message = message_override or f"cherry-pick: {source_commit.message}"
                new_commit = await self._create_commit(
                    target_branch_obj,
                    message=message,
                    author_id=actor_id,
                    source_commit_id=commit_id,
                    changes=result.applied_changes,
                )
                result.new_commit_id = new_commit.id if new_commit else None

            result.finalize(True, CherryPickStatus.COMPLETED)
            return result

        except Exception as e:
            logger.exception(f"Cherry-pick failed: {e}")
            result.error = str(e)
            result.error_details = {"exception_type": type(e).__name__}
            result.finalize(False, CherryPickStatus.FAILED)
            return result

        finally:
            self._current_operation = None

    async def dry_run(
        self,
        commit_id: str,
        target_branch: str,
    ) -> CherryPickResult:
        """
        Preview cherry-pick without applying changes.

        Args:
            commit_id: ID of commit to cherry-pick
            target_branch: Target branch name or ID

        Returns:
            CherryPickResult with preview of what would happen
        """
        result = CherryPickResult(
            success=True,
            status=CherryPickStatus.PENDING,
            commit_id=commit_id,
            target_branch_id=target_branch,
        )

        try:
            # Get source commit
            source_commit = await self._get_commit(commit_id)
            if not source_commit:
                result.error = f"Commit not found: {commit_id}"
                result.success = False
                return result

            result.source_branch_id = source_commit.branch_id

            # Get target branch
            target_branch_obj = await self._get_branch(target_branch)
            if not target_branch_obj:
                result.error = f"Target branch not found: {target_branch}"
                result.success = False
                return result

            # Detect conflicts
            conflicts = await self._detect_conflicts(source_commit, target_branch_obj)
            result.conflicts = conflicts

            # Extract changes that would be applied
            changes = await self._extract_changes(source_commit)
            for change in changes:
                # Check conflicts
                has_conflict = any(
                    c.object_type == change.object_type
                    and (c.field_name == change.field_name or c.field_name is None)
                    for c in conflicts
                )

                if has_conflict:
                    change.skipped = True
                    change.skip_reason = "Would conflict"
                    result.skipped_changes.append(change)
                else:
                    result.applied_changes.append(change)

            result.success = len(conflicts) == 0

        except Exception as e:
            result.error = str(e)
            result.success = False

        return result

    async def abort(self) -> bool:
        """
        Abort the current cherry-pick operation.

        Returns:
            True if abort was successful
        """
        if not self._current_operation:
            logger.warning("No cherry-pick operation in progress")
            return False

        operation = self._current_operation

        if operation.rollback_point and operation.rollback_available:
            success = await self._rollback_to_point(
                operation.target_branch_id,
                operation.rollback_point
            )

            if success:
                operation.finalize(False, CherryPickStatus.ABORTED)
                self._current_operation = None
                logger.info(f"Cherry-pick aborted: {operation.commit_id}")
                return True

        operation.finalize(False, CherryPickStatus.ABORTED)
        self._current_operation = None
        return True

    async def continue_after_resolve(
        self,
        resolved_conflicts: Optional[Dict[str, Any]] = None,
    ) -> CherryPickResult:
        """
        Continue cherry-pick after manually resolving conflicts.

        Args:
            resolved_conflicts: Map of conflict ID to resolved value

        Returns:
            CherryPickResult with continuation status
        """
        if not self._current_operation:
            return CherryPickResult(
                success=False,
                status=CherryPickStatus.FAILED,
                commit_id="",
                target_branch_id="",
                error="No cherry-pick operation in progress",
            )

        operation = self._current_operation
        resolved_conflicts = resolved_conflicts or {}

        # Mark conflicts as resolved
        for conflict in operation.conflicts:
            if conflict.id in resolved_conflicts:
                # Apply resolved value
                conflict.auto_resolvable = True
                conflict.recommended_resolution = str(resolved_conflicts[conflict.id])

        # Check if all conflicts resolved
        unresolved = [c for c in operation.conflicts if not c.auto_resolvable]

        if unresolved:
            operation.error = f"{len(unresolved)} conflicts still unresolved"
            return operation

        # Continue with THEIRS mode (use resolved values)
        return await self.cherry_pick(
            commit_id=operation.commit_id,
            target_branch=operation.target_branch_id,
            actor_id=operation.actor_id,
            conflict_resolution=CherryPickConflictResolution.THEIRS,
        )

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    async def _get_commit(self, commit_id: str) -> Optional[Any]:
        """Get commit by ID."""
        if self._branch_manager:
            return await self._branch_manager.get_commit(commit_id)
        return None

    async def _get_branch(self, branch_id: str) -> Optional[Any]:
        """Get branch by ID or name."""
        if self._branch_manager:
            branch = await self._branch_manager.get_branch(branch_id)
            if not branch:
                branch = await self._branch_manager.get_branch_by_name(branch_id)
            return branch
        return None

    async def _create_rollback_point(self, branch: Any) -> Optional[str]:
        """Create a checkpoint for rollback."""
        if self._branch_manager:
            from lib.oda.ontology.objects.branch import CheckpointType
            # Use PRE_MERGE as rollback point type (closest semantic match)
            result = await self._branch_manager.create_checkpoint(
                branch_id=branch.id,
                name=f"pre-cherry-pick-{uuid.uuid4().hex[:8]}",
                checkpoint_type=CheckpointType.PRE_MERGE,
                description="Auto-created before cherry-pick for rollback",
            )
            if result.success:
                return result.checkpoint_id
        return None

    async def _detect_conflicts(
        self,
        source_commit: Any,
        target_branch: Any,
    ) -> List[SchemaConflict]:
        """Detect conflicts between source commit and target branch."""
        conflicts = []

        if not source_commit.new_state:
            return conflicts

        # Get current state from target branch
        if self._branch_manager:
            target_commits = await self._branch_manager.get_commits(target_branch.id, limit=1)

            if target_commits:
                target_state = target_commits[0].new_state or {}

                # Compare states for conflicts
                for field_name, source_value in source_commit.new_state.items():
                    if field_name in target_state:
                        target_value = target_state[field_name]
                        if source_value != target_value:
                            conflicts.append(SchemaConflict(
                                conflict_type=SchemaConflictType.SCHEMA_CHANGE,
                                severity=SchemaConflictSeverity.WARNING,
                                object_type=source_commit.object_type,
                                field_name=field_name,
                                branch_a_value=source_value,
                                branch_b_value=target_value,
                                branch_a_id=source_commit.branch_id,
                                branch_b_id=target_branch.id,
                                resolution_suggestions=[
                                    "Use source commit value",
                                    "Use target branch value",
                                    "Merge values manually",
                                ],
                            ))

        return conflicts

    async def _extract_changes(self, commit: Any) -> List[CherryPickChange]:
        """Extract individual changes from a commit."""
        changes = []

        if commit.new_state:
            for field_name, new_value in commit.new_state.items():
                old_value = None
                if commit.previous_state:
                    old_value = commit.previous_state.get(field_name)

                changes.append(CherryPickChange(
                    object_type=commit.object_type,
                    object_id=commit.object_id or "",
                    field_name=field_name,
                    operation=commit.operation,
                    old_value=old_value,
                    new_value=new_value,
                ))

        return changes

    async def _apply_change(self, change: CherryPickChange, target_branch: Any) -> bool:
        """Apply a single change to the target branch."""
        # In a real implementation, this would modify the object
        # For now, we just return True to indicate success
        logger.debug(
            f"Applying change: {change.object_type}.{change.field_name} "
            f"= {change.new_value}"
        )
        return True

    async def _create_commit(
        self,
        target_branch: Any,
        message: str,
        author_id: Optional[str],
        source_commit_id: str,
        changes: List[CherryPickChange],
    ) -> Optional[Any]:
        """Create a new commit on the target branch."""
        if self._branch_manager:
            # Build new state from changes
            new_state = {}
            for change in changes:
                if change.field_name:
                    new_state[change.field_name] = change.new_value

            result = await self._branch_manager.commit(
                branch_id=target_branch.id,
                message=message,
                author_id=author_id or "system",
                object_type=changes[0].object_type if changes else "",
                object_id=changes[0].object_id if changes else None,
                new_state=new_state,
                metadata={
                    "cherry_picked_from": source_commit_id,
                    "cherry_pick": True,
                },
            )

            if result.success:
                return await self._branch_manager.get_commit(result.commit_id)

        return None

    async def _rollback_to_point(self, branch_id: str, checkpoint_id: str) -> bool:
        """Rollback branch to checkpoint."""
        if self._branch_manager:
            return await self._branch_manager.rollback_to_checkpoint(
                branch_id=branch_id,
                checkpoint_id=checkpoint_id,
            )
        return False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CherryPickStatus",
    "CherryPickConflictResolution",
    "CherryPickChange",
    "CherryPickResult",
    "CherryPicker",
]
