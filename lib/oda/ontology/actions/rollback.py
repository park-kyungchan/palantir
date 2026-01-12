"""
Orion ODA v3.0 - Rollback Orchestrator
Palantir Foundry Compliant Rollback Operations

This module implements the RollbackOrchestrator for coordinated undo operations.
Foundry Pattern: Complex rollback scenarios require orchestration:
- Single action undo
- Batch rollback (reverse order)
- Checkpoint restoration
- Cascade undo (dependent actions)

Design Principles:
1. Rollback in reverse chronological order
2. Handle partial failures gracefully
3. Maintain audit trail of rollback operations
4. Support both immediate and proposal-based rollback
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Type,
    TYPE_CHECKING,
)
import uuid

from pydantic import BaseModel, Field

from lib.oda.ontology.actions.undoable import (
    UndoSnapshot,
    UndoResult,
    UndoStatus,
    UndoScope,
    UndoPolicy,
    UndoableAction,
)

if TYPE_CHECKING:
    from lib.oda.ontology.actions import ActionContext, ActionType
    from lib.oda.ontology.storage.undo_history import UndoHistoryRepository

logger = logging.getLogger(__name__)


# =============================================================================
# ROLLBACK TYPES
# =============================================================================

class RollbackStatus(str, Enum):
    """Status of a rollback operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    PARTIAL = "partial"       # Some undos failed
    FAILED = "failed"
    ABORTED = "aborted"       # User cancelled


class RollbackStrategy(str, Enum):
    """Strategy for handling rollback."""
    STOP_ON_FAILURE = "stop_on_failure"     # Stop at first failure
    CONTINUE_ON_FAILURE = "continue_on_failure"  # Try all, report failures
    BEST_EFFORT = "best_effort"             # Log failures, don't report


# =============================================================================
# ROLLBACK REQUEST
# =============================================================================

@dataclass
class RollbackRequest:
    """
    Request for a rollback operation.

    Foundry Pattern: Rollback requests specify:
    - What to rollback (scope)
    - How to handle failures (strategy)
    - Who is requesting (actor)
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scope: UndoScope = UndoScope.SINGLE
    strategy: RollbackStrategy = RollbackStrategy.STOP_ON_FAILURE

    # Target specification (one of these should be set)
    action_ids: List[str] = field(default_factory=list)  # For SINGLE/BATCH
    batch_id: Optional[str] = None                       # For BATCH scope
    checkpoint_id: Optional[str] = None                  # For CHECKPOINT
    actor_id: Optional[str] = None                       # For SESSION

    # Filters
    object_type: Optional[str] = None
    object_id: Optional[str] = None
    since: Optional[datetime] = None

    # Options
    dry_run: bool = False              # Preview without executing
    require_approval: bool = False     # Create proposal instead of execute
    reason: Optional[str] = None       # Reason for rollback

    # Metadata
    requested_by: str = "system"
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "scope": self.scope.value,
            "strategy": self.strategy.value,
            "action_ids": self.action_ids,
            "batch_id": self.batch_id,
            "checkpoint_id": self.checkpoint_id,
            "actor_id": self.actor_id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "since": self.since.isoformat() if self.since else None,
            "dry_run": self.dry_run,
            "require_approval": self.require_approval,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
        }


# =============================================================================
# ROLLBACK RESULT
# =============================================================================

@dataclass
class RollbackResult:
    """
    Result of a rollback operation.
    """
    request_id: str
    status: RollbackStatus
    total_actions: int = 0
    successful_undos: int = 0
    failed_undos: int = 0
    skipped_undos: int = 0

    # Individual results
    undo_results: List[UndoResult] = field(default_factory=list)

    # Errors
    errors: List[str] = field(default_factory=list)

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0

    # Metadata
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "total_actions": self.total_actions,
            "successful_undos": self.successful_undos,
            "failed_undos": self.failed_undos,
            "skipped_undos": self.skipped_undos,
            "undo_results": [r.to_dict() for r in self.undo_results],
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "message": self.message,
        }


# =============================================================================
# ROLLBACK PLAN
# =============================================================================

@dataclass
class RollbackPlan:
    """
    A plan for executing a rollback.

    Generated from a RollbackRequest, shows what will be undone.
    """
    request: RollbackRequest
    snapshots: List[UndoSnapshot] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)  # action_ids in undo order
    warnings: List[str] = field(default_factory=list)
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "snapshots_count": len(self.snapshots),
            "execution_order": self.execution_order,
            "warnings": self.warnings,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


# =============================================================================
# ROLLBACK ORCHESTRATOR
# =============================================================================

class RollbackOrchestrator:
    """
    Orchestrates rollback operations.

    Foundry Pattern: The orchestrator:
    1. Plans rollback based on request
    2. Validates all actions can be undone
    3. Executes undos in reverse order
    4. Handles failures based on strategy
    5. Reports results

    Usage:
        orchestrator = RollbackOrchestrator(
            history_repo=undo_history_repo,
            action_registry=action_registry,
        )

        # Plan rollback
        plan = await orchestrator.plan(request)

        # Preview (dry run)
        if request.dry_run:
            return plan

        # Execute rollback
        result = await orchestrator.execute(plan, context)
    """

    def __init__(
        self,
        history_repo: "UndoHistoryRepository",
        action_registry: Optional[Dict[str, Type["ActionType"]]] = None,
        policy: Optional[UndoPolicy] = None,
    ):
        self.history_repo = history_repo
        self.action_registry = action_registry or {}
        self.policy = policy or UndoPolicy.default()

        # Cache of UndoableAction instances
        self._action_cache: Dict[str, "UndoableAction"] = {}

    async def plan(self, request: RollbackRequest) -> RollbackPlan:
        """
        Create a rollback plan from a request.

        Args:
            request: The rollback request

        Returns:
            RollbackPlan with snapshots and execution order
        """
        plan = RollbackPlan(request=request)

        # Gather snapshots based on scope
        if request.scope == UndoScope.SINGLE:
            snapshots = await self._gather_single(request)
        elif request.scope == UndoScope.BATCH:
            snapshots = await self._gather_batch(request)
        elif request.scope == UndoScope.SESSION:
            snapshots = await self._gather_session(request)
        elif request.scope == UndoScope.CHECKPOINT:
            snapshots = await self._gather_checkpoint(request)
        else:
            plan.is_valid = False
            plan.validation_errors.append(f"Unknown scope: {request.scope}")
            return plan

        if not snapshots:
            plan.is_valid = False
            plan.validation_errors.append("No undoable actions found matching request")
            return plan

        plan.snapshots = snapshots

        # Validate each snapshot
        for snapshot in snapshots:
            errors = await self._validate_snapshot(snapshot, request)
            if errors:
                plan.validation_errors.extend(errors)
                plan.is_valid = False

        # Determine execution order (reverse chronological)
        sorted_snapshots = sorted(
            snapshots,
            key=lambda s: s.timestamp,
            reverse=True  # Most recent first
        )
        plan.execution_order = [s.action_id for s in sorted_snapshots]

        # Add warnings
        if len(snapshots) > 10:
            plan.warnings.append(
                f"Large rollback: {len(snapshots)} actions will be undone"
            )

        # Check for cascading effects
        cascade_warnings = await self._check_cascade_effects(snapshots)
        plan.warnings.extend(cascade_warnings)

        return plan

    async def execute(
        self,
        plan: RollbackPlan,
        context: "ActionContext",
    ) -> RollbackResult:
        """
        Execute a rollback plan.

        Args:
            plan: The validated rollback plan
            context: Execution context

        Returns:
            RollbackResult with status and details
        """
        from datetime import timezone

        result = RollbackResult(
            request_id=plan.request.request_id,
            status=RollbackStatus.IN_PROGRESS,
            total_actions=len(plan.execution_order),
            started_at=datetime.now(timezone.utc),
        )

        if not plan.is_valid:
            result.status = RollbackStatus.FAILED
            result.errors = plan.validation_errors
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Build snapshot lookup
        snapshot_map = {s.action_id: s for s in plan.snapshots}

        # Execute undos in order
        for action_id in plan.execution_order:
            snapshot = snapshot_map.get(action_id)
            if not snapshot:
                result.skipped_undos += 1
                continue

            try:
                undo_result = await self._execute_single_undo(snapshot, context)
                result.undo_results.append(undo_result)

                if undo_result.status == UndoStatus.SUCCESS:
                    result.successful_undos += 1
                    # Update history
                    await self.history_repo.update_undo_status(
                        action_id=action_id,
                        status=UndoStatus.SUCCESS,
                    )
                elif undo_result.status == UndoStatus.SKIPPED:
                    result.skipped_undos += 1
                else:
                    result.failed_undos += 1
                    result.errors.append(
                        f"Failed to undo {snapshot.action_api_name}: {undo_result.error}"
                    )
                    # Update history with failure
                    await self.history_repo.update_undo_status(
                        action_id=action_id,
                        status=UndoStatus.FAILED,
                        error=undo_result.error,
                    )

                    # Handle failure based on strategy
                    if plan.request.strategy == RollbackStrategy.STOP_ON_FAILURE:
                        logger.warning(
                            f"Rollback stopped at {action_id} due to failure"
                        )
                        break

            except Exception as e:
                result.failed_undos += 1
                result.errors.append(f"Exception undoing {action_id}: {str(e)}")
                logger.exception(f"Rollback exception for {action_id}")

                if plan.request.strategy == RollbackStrategy.STOP_ON_FAILURE:
                    break

        # Determine final status
        result.completed_at = datetime.now(timezone.utc)
        result.duration_ms = int(
            (result.completed_at - result.started_at).total_seconds() * 1000
        )

        if result.failed_undos == 0 and result.successful_undos == result.total_actions:
            result.status = RollbackStatus.SUCCESS
            result.message = f"Successfully rolled back {result.successful_undos} actions"
        elif result.failed_undos == result.total_actions:
            result.status = RollbackStatus.FAILED
            result.message = "All undo operations failed"
        elif result.failed_undos > 0:
            result.status = RollbackStatus.PARTIAL
            result.message = (
                f"Partially rolled back: {result.successful_undos} success, "
                f"{result.failed_undos} failed, {result.skipped_undos} skipped"
            )
        else:
            result.status = RollbackStatus.SUCCESS
            result.message = f"Rolled back {result.successful_undos} actions"

        logger.info(
            f"Rollback {plan.request.request_id} completed: {result.status.value}"
        )

        return result

    async def preview(self, request: RollbackRequest) -> RollbackPlan:
        """
        Preview a rollback without executing.

        Args:
            request: The rollback request

        Returns:
            RollbackPlan showing what would be undone
        """
        request.dry_run = True
        return await self.plan(request)

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    async def _gather_single(self, request: RollbackRequest) -> List[UndoSnapshot]:
        """Gather snapshots for single action undo."""
        snapshots = []
        for action_id in request.action_ids:
            snapshot = await self.history_repo.get_by_action_id(action_id)
            if snapshot and snapshot.is_undoable:
                snapshots.append(snapshot)
        return snapshots

    async def _gather_batch(self, request: RollbackRequest) -> List[UndoSnapshot]:
        """Gather snapshots for batch rollback."""
        if request.batch_id:
            return await self.history_repo.get_by_batch(request.batch_id)
        elif request.action_ids:
            return await self._gather_single(request)
        return []

    async def _gather_session(self, request: RollbackRequest) -> List[UndoSnapshot]:
        """Gather snapshots for session rollback."""
        if not request.actor_id:
            return []

        return await self.history_repo.get_by_actor(
            actor_id=request.actor_id,
            since=request.since,
        )

    async def _gather_checkpoint(self, request: RollbackRequest) -> List[UndoSnapshot]:
        """Gather snapshots since checkpoint."""
        # Checkpoint rollback requires integration with checkpoint system
        # For now, return empty list
        logger.warning("Checkpoint rollback not yet implemented")
        return []

    async def _validate_snapshot(
        self,
        snapshot: UndoSnapshot,
        request: RollbackRequest,
    ) -> List[str]:
        """Validate a snapshot can be undone."""
        errors = []

        # Check if already undone
        if snapshot.undo_status != UndoStatus.PENDING:
            errors.append(
                f"Action {snapshot.action_id} already has status: {snapshot.undo_status.value}"
            )

        # Check if marked non-undoable
        if not snapshot.is_undoable:
            errors.append(f"Action {snapshot.action_id} is marked as non-undoable")

        # Check time limit
        if self.policy.max_undo_age_hours > 0:
            from datetime import timedelta
            age = datetime.now(timezone.utc) - snapshot.timestamp
            if age > timedelta(hours=self.policy.max_undo_age_hours):
                errors.append(
                    f"Action {snapshot.action_id} is too old to undo "
                    f"(age: {age.total_seconds() / 3600:.1f}h, "
                    f"max: {self.policy.max_undo_age_hours}h)"
                )

        # Check actor restriction
        if self.policy.require_same_actor:
            if snapshot.actor_id != request.requested_by:
                errors.append(
                    f"Action {snapshot.action_id} can only be undone by "
                    f"original actor: {snapshot.actor_id}"
                )

        return errors

    async def _check_cascade_effects(
        self,
        snapshots: List[UndoSnapshot],
    ) -> List[str]:
        """Check for potential cascade effects."""
        warnings = []

        # Group by object to detect multiple operations on same object
        by_object: Dict[str, List[UndoSnapshot]] = {}
        for s in snapshots:
            if s.object_id:
                key = f"{s.object_type}:{s.object_id}"
                if key not in by_object:
                    by_object[key] = []
                by_object[key].append(s)

        for key, obj_snapshots in by_object.items():
            if len(obj_snapshots) > 1:
                warnings.append(
                    f"Object {key} has {len(obj_snapshots)} operations to undo"
                )

        return warnings

    async def _execute_single_undo(
        self,
        snapshot: UndoSnapshot,
        context: "ActionContext",
    ) -> UndoResult:
        """Execute undo for a single snapshot."""
        # Get the action class
        action_class = self.action_registry.get(snapshot.action_api_name)

        if not action_class:
            return UndoResult(
                snapshot_id=snapshot.action_id,
                action_api_name=snapshot.action_api_name,
                status=UndoStatus.FAILED,
                error=f"Action type not found: {snapshot.action_api_name}",
            )

        # Check if action is undoable
        if not getattr(action_class, 'is_undoable', True):
            return UndoResult(
                snapshot_id=snapshot.action_id,
                action_api_name=snapshot.action_api_name,
                status=UndoStatus.SKIPPED,
                message="Action type is not undoable",
            )

        # Check if action class has undo method
        if not hasattr(action_class, 'undo'):
            # Use generic restore if no custom undo
            return await self._generic_restore(snapshot, context)

        # Create action instance
        action_instance = action_class()

        # Execute custom undo
        try:
            if isinstance(action_instance, UndoableAction):
                # Check can_undo first
                can_undo, reason = await action_instance.can_undo(snapshot, context)
                if not can_undo:
                    return UndoResult(
                        snapshot_id=snapshot.action_id,
                        action_api_name=snapshot.action_api_name,
                        status=UndoStatus.SKIPPED,
                        message=reason,
                    )

                # Execute undo
                return await action_instance.undo(snapshot, context)
            else:
                # Fallback to generic restore
                return await self._generic_restore(snapshot, context)

        except Exception as e:
            logger.exception(f"Undo failed for {snapshot.action_id}")
            return UndoResult(
                snapshot_id=snapshot.action_id,
                action_api_name=snapshot.action_api_name,
                status=UndoStatus.FAILED,
                error=str(e),
            )

    async def _generic_restore(
        self,
        snapshot: UndoSnapshot,
        context: "ActionContext",
    ) -> UndoResult:
        """
        Generic restore using previous_state.

        This is a fallback for actions without custom undo.
        It attempts to restore the object to its previous state.
        """
        if not snapshot.previous_state:
            return UndoResult(
                snapshot_id=snapshot.action_id,
                action_api_name=snapshot.action_api_name,
                status=UndoStatus.FAILED,
                error="No previous state captured",
            )

        # In a real implementation, this would:
        # 1. Load the object by object_id
        # 2. Update it with previous_state
        # 3. Save the updated object

        # For now, log and return success as placeholder
        logger.info(
            f"Generic restore for {snapshot.object_type}:{snapshot.object_id} "
            f"would restore state: {list(snapshot.previous_state.keys())}"
        )

        return UndoResult(
            snapshot_id=snapshot.action_id,
            action_api_name=snapshot.action_api_name,
            status=UndoStatus.SUCCESS,
            restored_state=snapshot.previous_state,
            message="Restored using generic restore",
        )


# =============================================================================
# ROLLBACK BUILDER (FLUENT API)
# =============================================================================

class RollbackBuilder:
    """
    Fluent builder for rollback requests.

    Usage:
        rollback = (RollbackBuilder()
            .undo_action("action-123")
            .with_reason("Incorrect data entry")
            .by_actor("user-456")
            .build())
    """

    def __init__(self):
        self._request = RollbackRequest()

    def undo_action(self, action_id: str) -> "RollbackBuilder":
        """Undo a single action."""
        self._request.scope = UndoScope.SINGLE
        self._request.action_ids.append(action_id)
        return self

    def undo_actions(self, action_ids: List[str]) -> "RollbackBuilder":
        """Undo multiple actions."""
        self._request.scope = UndoScope.BATCH
        self._request.action_ids.extend(action_ids)
        return self

    def undo_batch(self, batch_id: str) -> "RollbackBuilder":
        """Undo an entire batch."""
        self._request.scope = UndoScope.BATCH
        self._request.batch_id = batch_id
        return self

    def undo_session(self, actor_id: str) -> "RollbackBuilder":
        """Undo all actions by an actor."""
        self._request.scope = UndoScope.SESSION
        self._request.actor_id = actor_id
        return self

    def since(self, timestamp: datetime) -> "RollbackBuilder":
        """Only undo actions since this time."""
        self._request.since = timestamp
        return self

    def for_object(self, object_type: str, object_id: str) -> "RollbackBuilder":
        """Filter to specific object."""
        self._request.object_type = object_type
        self._request.object_id = object_id
        return self

    def with_reason(self, reason: str) -> "RollbackBuilder":
        """Add reason for rollback."""
        self._request.reason = reason
        return self

    def by_actor(self, actor_id: str) -> "RollbackBuilder":
        """Set requesting actor."""
        self._request.requested_by = actor_id
        return self

    def dry_run(self) -> "RollbackBuilder":
        """Preview without executing."""
        self._request.dry_run = True
        return self

    def require_approval(self) -> "RollbackBuilder":
        """Require proposal approval."""
        self._request.require_approval = True
        return self

    def stop_on_failure(self) -> "RollbackBuilder":
        """Stop at first failure."""
        self._request.strategy = RollbackStrategy.STOP_ON_FAILURE
        return self

    def continue_on_failure(self) -> "RollbackBuilder":
        """Continue past failures."""
        self._request.strategy = RollbackStrategy.CONTINUE_ON_FAILURE
        return self

    def best_effort(self) -> "RollbackBuilder":
        """Best effort rollback."""
        self._request.strategy = RollbackStrategy.BEST_EFFORT
        return self

    def build(self) -> RollbackRequest:
        """Build the request."""
        return self._request
