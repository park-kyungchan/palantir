"""
Orion ODA v3.0 - Undoable Actions Framework
Palantir Foundry Compliant Undo/Rollback Support

This module implements the UndoableAction pattern for reversible operations.
Foundry Pattern: Actions that modify state should be undoable for:
- Error recovery
- User-initiated rollback
- Batch operation partial failure handling

Design Principles:
1. Capture state BEFORE mutation for undo capability
2. Undo operations should be idempotent
3. Undo history is persisted for audit trail
4. Support both single-action and batch rollback
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
)

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import OntologyObject, utc_now

logger = logging.getLogger(__name__)


# =============================================================================
# UNDO TYPES
# =============================================================================

class UndoStatus(str, Enum):
    """Status of an undo operation."""
    PENDING = "pending"           # Undo not yet executed
    IN_PROGRESS = "in_progress"   # Currently undoing
    SUCCESS = "success"           # Undo completed successfully
    FAILED = "failed"             # Undo failed
    PARTIAL = "partial"           # Partially undone (batch)
    SKIPPED = "skipped"           # Skipped (already undone or not undoable)


class UndoScope(str, Enum):
    """Scope of undo operation."""
    SINGLE = "single"     # Undo single action
    BATCH = "batch"       # Undo batch of actions
    SESSION = "session"   # Undo entire session
    CHECKPOINT = "checkpoint"  # Undo to checkpoint


# =============================================================================
# UNDO SNAPSHOT
# =============================================================================

@dataclass
class UndoSnapshot:
    """
    Captures the state before an action for undo capability.

    Foundry Pattern: Before any mutation, capture:
    - Original object state (if exists)
    - Action parameters
    - Context for replay

    This enables:
    - Restoring previous state on undo
    - Audit trail of changes
    - Debugging and analysis
    """
    action_id: str                          # Unique ID of the action execution
    action_api_name: str                    # API name of the action
    timestamp: datetime                     # When the action was executed
    actor_id: str                           # Who executed the action

    # State capture
    object_type: Optional[str] = None       # Type of affected object
    object_id: Optional[str] = None         # ID of affected object
    previous_state: Optional[Dict[str, Any]] = None  # State before action
    new_state: Optional[Dict[str, Any]] = None       # State after action

    # Action parameters for replay
    params: Dict[str, Any] = field(default_factory=dict)

    # Undo metadata
    is_undoable: bool = True                # Can this be undone?
    undo_method: Optional[str] = None       # Method name for undo
    undo_params: Optional[Dict[str, Any]] = None  # Custom undo parameters

    # Tracking
    correlation_id: Optional[str] = None    # Trace ID
    parent_batch_id: Optional[str] = None   # If part of batch

    # Status
    undo_status: UndoStatus = UndoStatus.PENDING
    undo_timestamp: Optional[datetime] = None
    undo_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_api_name": self.action_api_name,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "params": self.params,
            "is_undoable": self.is_undoable,
            "undo_method": self.undo_method,
            "undo_params": self.undo_params,
            "correlation_id": self.correlation_id,
            "parent_batch_id": self.parent_batch_id,
            "undo_status": self.undo_status.value,
            "undo_timestamp": self.undo_timestamp.isoformat() if self.undo_timestamp else None,
            "undo_error": self.undo_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UndoSnapshot":
        """Create UndoSnapshot from dictionary."""
        return cls(
            action_id=data["action_id"],
            action_api_name=data["action_api_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            actor_id=data["actor_id"],
            object_type=data.get("object_type"),
            object_id=data.get("object_id"),
            previous_state=data.get("previous_state"),
            new_state=data.get("new_state"),
            params=data.get("params", {}),
            is_undoable=data.get("is_undoable", True),
            undo_method=data.get("undo_method"),
            undo_params=data.get("undo_params"),
            correlation_id=data.get("correlation_id"),
            parent_batch_id=data.get("parent_batch_id"),
            undo_status=UndoStatus(data.get("undo_status", "pending")),
            undo_timestamp=datetime.fromisoformat(data["undo_timestamp"]) if data.get("undo_timestamp") else None,
            undo_error=data.get("undo_error"),
        )


# =============================================================================
# UNDO RESULT
# =============================================================================

@dataclass
class UndoResult:
    """
    Result of an undo operation.
    """
    snapshot_id: str                    # ID of the snapshot being undone
    action_api_name: str                # Action that was undone
    status: UndoStatus                  # Status of undo
    message: Optional[str] = None       # Human-readable message
    restored_state: Optional[Dict[str, Any]] = None  # State after undo
    error: Optional[str] = None         # Error message if failed
    timestamp: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "action_api_name": self.action_api_name,
            "status": self.status.value,
            "message": self.message,
            "restored_state": self.restored_state,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# UNDOABLE ACTION BASE CLASS
# =============================================================================

T = TypeVar("T", bound=OntologyObject)


class UndoableAction(ABC, Generic[T]):
    """
    Base class for actions that can be undone.

    Foundry Pattern: UndoableAction extends ActionType with:
    1. capture_snapshot(): Capture state before mutation
    2. undo(): Reverse the action's effects
    3. can_undo(): Check if undo is still possible

    Usage:
        @register_action
        class UpdateTaskAction(UndoableAction[Task]):
            api_name = "task.update"
            object_type = Task

            async def capture_snapshot(
                self,
                params: Dict[str, Any],
                context: ActionContext
            ) -> UndoSnapshot:
                # Fetch current state before mutation
                task = await self._get_task(params["task_id"])
                return UndoSnapshot(
                    action_id=context.correlation_id or uuid4().hex,
                    action_api_name=self.api_name,
                    timestamp=context.timestamp,
                    actor_id=context.actor_id,
                    object_type="Task",
                    object_id=task.id,
                    previous_state=task.model_dump(),
                    params=params,
                )

            async def undo(
                self,
                snapshot: UndoSnapshot,
                context: ActionContext
            ) -> UndoResult:
                # Restore previous state
                await self._restore_task(
                    snapshot.object_id,
                    snapshot.previous_state
                )
                return UndoResult(
                    snapshot_id=snapshot.action_id,
                    action_api_name=self.api_name,
                    status=UndoStatus.SUCCESS,
                )
    """

    # Class attributes from ActionType
    api_name: ClassVar[str]
    object_type: ClassVar[Type[T]]
    is_undoable: ClassVar[bool] = True  # Override to False for non-undoable actions

    @abstractmethod
    async def capture_snapshot(
        self,
        params: Dict[str, Any],
        context: "ActionContext"
    ) -> UndoSnapshot:
        """
        Capture state before the action is executed.

        This method is called BEFORE apply_edits() and should:
        1. Fetch the current state of affected objects
        2. Store any data needed to reverse the action
        3. Return an UndoSnapshot with previous_state populated

        Args:
            params: Action parameters
            context: Execution context

        Returns:
            UndoSnapshot capturing pre-action state
        """
        ...

    @abstractmethod
    async def undo(
        self,
        snapshot: UndoSnapshot,
        context: "ActionContext"
    ) -> UndoResult:
        """
        Undo the action using the captured snapshot.

        This method should:
        1. Restore the previous_state from snapshot
        2. Handle any side effects of undoing
        3. Return UndoResult with status

        Args:
            snapshot: The captured snapshot from capture_snapshot()
            context: Execution context for the undo operation

        Returns:
            UndoResult indicating success or failure
        """
        ...

    async def can_undo(
        self,
        snapshot: UndoSnapshot,
        context: "ActionContext"
    ) -> tuple[bool, str]:
        """
        Check if the action can still be undone.

        Override this method to add custom checks, such as:
        - Time-based restrictions (can only undo within 24 hours)
        - State-based restrictions (can't undo if object was further modified)
        - Permission checks

        Args:
            snapshot: The snapshot to potentially undo
            context: Current execution context

        Returns:
            Tuple of (can_undo: bool, reason: str)
        """
        # Default implementation: always allow if snapshot exists
        if snapshot.undo_status != UndoStatus.PENDING:
            return False, f"Snapshot already has status: {snapshot.undo_status.value}"

        if not snapshot.is_undoable:
            return False, "Snapshot marked as not undoable"

        return True, "Undo allowed"

    async def validate_undo(
        self,
        snapshot: UndoSnapshot,
        context: "ActionContext"
    ) -> List[str]:
        """
        Validate that undo can be performed safely.

        Override to add custom validation. Returns list of error messages.

        Args:
            snapshot: The snapshot to validate
            context: Execution context

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check basic validity
        if not snapshot.previous_state:
            errors.append("No previous state captured in snapshot")

        if not snapshot.object_id:
            errors.append("No object ID in snapshot")

        return errors


# =============================================================================
# UNDO-AWARE ACTION MIXIN
# =============================================================================

class UndoAwareMixin:
    """
    Mixin that adds undo capability to existing ActionType classes.

    Use this when you can't extend UndoableAction directly:

        class MyAction(ActionType[MyObject], UndoAwareMixin):
            ...
    """

    _snapshot: Optional[UndoSnapshot] = None

    def set_snapshot(self, snapshot: UndoSnapshot) -> None:
        """Store snapshot for later undo."""
        self._snapshot = snapshot

    def get_snapshot(self) -> Optional[UndoSnapshot]:
        """Retrieve stored snapshot."""
        return self._snapshot

    def clear_snapshot(self) -> None:
        """Clear stored snapshot."""
        self._snapshot = None


# =============================================================================
# NON-UNDOABLE MARKER
# =============================================================================

def non_undoable(cls: Type) -> Type:
    """
    Decorator to mark an action as non-undoable.

    Usage:
        @non_undoable
        @register_action
        class DeletePermanentlyAction(ActionType[Task]):
            api_name = "task.delete_permanent"
            ...
    """
    cls.is_undoable = False
    return cls


# =============================================================================
# UNDO POLICY
# =============================================================================

@dataclass
class UndoPolicy:
    """
    Policy configuration for undo behavior.

    Foundry Pattern: Configure undo restrictions per action type.
    """
    max_undo_age_hours: int = 24           # Max hours since action for undo
    require_same_actor: bool = False        # Must same actor undo?
    require_approval: bool = False          # Undo requires proposal?
    allow_cascade_undo: bool = True         # Undo dependent actions?
    preserve_audit_trail: bool = True       # Keep undo in audit log?

    @classmethod
    def default(cls) -> "UndoPolicy":
        """Get default undo policy."""
        return cls()

    @classmethod
    def strict(cls) -> "UndoPolicy":
        """Get strict undo policy (same actor, time-limited)."""
        return cls(
            max_undo_age_hours=1,
            require_same_actor=True,
            require_approval=False,
            allow_cascade_undo=False,
        )

    @classmethod
    def permissive(cls) -> "UndoPolicy":
        """Get permissive undo policy (no restrictions)."""
        return cls(
            max_undo_age_hours=720,  # 30 days
            require_same_actor=False,
            require_approval=False,
            allow_cascade_undo=True,
        )


# =============================================================================
# TYPE ANNOTATIONS FOR FORWARD REFERENCES
# =============================================================================

# Import ActionContext for type hints (avoid circular import)
if __name__ != "__main__":
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from . import ActionContext
