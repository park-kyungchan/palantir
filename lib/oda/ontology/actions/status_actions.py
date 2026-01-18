"""
Orion ODA v4.0 - Status Lifecycle Actions
==========================================

This module registers Actions for managing resource lifecycle statuses.
All status mutations go through the Action layer for governance and auditing.

Actions:
- status.transition: Change resource status (HAZARDOUS - requires proposal)
- status.rollback: Revert to previous status (HAZARDOUS - requires proposal)
- status.history: Get status transition history (non-hazardous)

Example:
    ```python
    from lib.oda.ontology.actions import action_registry, ActionContext

    # Get an action
    TransitionAction = action_registry.get("status.transition")
    action = TransitionAction()

    # Execute with context
    result = await action.execute(
        params={
            "object_id": "proj-001",
            "object_type": "Project",
            "target_status": "experimental",
            "reason": "Ready for testing"
        },
        context=ActionContext(actor_id="user-123")
    )
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional, Type

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    AllowedValues,
    SubmissionCriterion,
    ValidationError,
    register_action,
)
from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.types.status_types import (
    ResourceLifecycleStatus,
    get_allowed_transitions,
    is_valid_transition,
)
from lib.oda.ontology.validators.status_validator import (
    StatusTransitionError,
    StatusTransitionValidator,
    TransitionValidationResult,
)
from lib.oda.ontology.tracking.status_history import (
    StatusHistoryEntry,
    StatusHistoryTracker,
    get_default_tracker,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM VALIDATORS
# =============================================================================


class ValidStatusValue(SubmissionCriterion):
    """Validates that a status value is a valid ResourceLifecycleStatus."""

    def __init__(self, field_name: str = "target_status"):
        self.field_name = field_name
        self._valid_values = [s.value for s in ResourceLifecycleStatus]

    @property
    def name(self) -> str:
        return f"ValidStatusValue({self.field_name})"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        value = params.get(self.field_name)
        if value is None:
            return True  # Let RequiredField handle missing values

        if isinstance(value, ResourceLifecycleStatus):
            return True

        if isinstance(value, str) and value in self._valid_values:
            return True

        raise ValidationError(
            criterion=self.name,
            message=f"Invalid status value: '{value}'. Valid values: {self._valid_values}",
            details={"field": self.field_name, "value": value, "valid_values": self._valid_values}
        )


class ValidTransitionValidator(SubmissionCriterion):
    """Validates that a status transition is allowed."""

    @property
    def name(self) -> str:
        return "ValidTransition"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        current_status = params.get("current_status")
        target_status = params.get("target_status")

        if current_status is None or target_status is None:
            return True  # Let RequiredField validators handle missing values

        # Convert strings to enum if needed
        if isinstance(current_status, str):
            try:
                current_status = ResourceLifecycleStatus(current_status)
            except ValueError:
                raise ValidationError(
                    criterion=self.name,
                    message=f"Invalid current_status: '{current_status}'",
                    details={"current_status": current_status}
                )

        if isinstance(target_status, str):
            try:
                target_status = ResourceLifecycleStatus(target_status)
            except ValueError:
                raise ValidationError(
                    criterion=self.name,
                    message=f"Invalid target_status: '{target_status}'",
                    details={"target_status": target_status}
                )

        if not is_valid_transition(current_status, target_status):
            allowed = get_allowed_transitions(current_status)
            allowed_str = ", ".join(s.value for s in allowed) or "none"
            raise ValidationError(
                criterion=self.name,
                message=(
                    f"Invalid transition from '{current_status.value}' to '{target_status.value}'. "
                    f"Allowed: [{allowed_str}]"
                ),
                details={
                    "current_status": current_status.value,
                    "target_status": target_status.value,
                    "allowed_transitions": [s.value for s in allowed],
                }
            )

        return True


# =============================================================================
# STATUS TRANSITION ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class StatusTransitionAction(ActionType[OntologyObject]):
    """
    Transition a resource to a new lifecycle status.

    This action is HAZARDOUS and requires a proposal for approval.
    It validates the transition, updates the status, and records history.

    Parameters:
        object_id: ID of the object to transition
        object_type: Type name of the object
        current_status: Current status (for validation)
        target_status: Target status to transition to
        reason: Optional explanation for the transition

    Returns:
        ActionResult with the transition details
    """

    api_name: ClassVar[str] = "status.transition"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("object_id"),
        RequiredField("object_type"),
        RequiredField("current_status"),
        RequiredField("target_status"),
        ValidStatusValue("current_status"),
        ValidStatusValue("target_status"),
        ValidTransitionValidator(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """Apply the status transition."""
        object_id = params["object_id"]
        object_type = params["object_type"]
        current_status_value = params["current_status"]
        target_status_value = params["target_status"]
        reason = params.get("reason")

        # Convert to enum
        if isinstance(current_status_value, str):
            current_status = ResourceLifecycleStatus(current_status_value)
        else:
            current_status = current_status_value

        if isinstance(target_status_value, str):
            target_status = ResourceLifecycleStatus(target_status_value)
        else:
            target_status = target_status_value

        # Record in history
        tracker = get_default_tracker()
        entry = tracker.record_transition(
            object_id=object_id,
            object_type=object_type,
            from_status=current_status,
            to_status=target_status,
            actor_id=context.actor_id,
            reason=reason,
            metadata=context.metadata,
        )

        # Create edit operation for audit trail
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type=object_type,
            object_id=object_id,
            changes={
                "status": {
                    "old": current_status.value,
                    "new": target_status.value,
                },
                "reason": reason,
                "history_entry_id": entry.entry_id,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Status transition: {object_type}:{object_id} "
            f"{current_status.value} -> {target_status.value} by {context.actor_id}"
        )

        # Return ActionResult with transition details
        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "object_id": object_id,
                "object_type": object_type,
                "from_status": current_status.value,
                "to_status": target_status.value,
                "history_entry_id": entry.entry_id,
                "reason": reason,
            },
            edits=[edit],
            modified_ids=[object_id],
            message=f"Transitioned {object_type}:{object_id} from {current_status.value} to {target_status.value}",
        )


# =============================================================================
# STATUS ROLLBACK ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class StatusRollbackAction(ActionType[OntologyObject]):
    """
    Rollback a resource to its previous status.

    This action is HAZARDOUS and requires a proposal for approval.
    It finds the previous status from history and transitions back.

    Parameters:
        object_id: ID of the object to rollback
        object_type: Type name of the object
        reason: Explanation for the rollback

    Returns:
        ActionResult with the rollback details
    """

    api_name: ClassVar[str] = "status.rollback"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("object_id"),
        RequiredField("object_type"),
        RequiredField("reason"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """Apply the status rollback."""
        object_id = params["object_id"]
        object_type = params["object_type"]
        reason = params["reason"]

        tracker = get_default_tracker()

        # Get history to find previous status
        history = tracker.get_history(object_id, limit=2, ascending=False)

        if len(history) < 2:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error="Cannot rollback: insufficient history",
                error_details={
                    "object_id": object_id,
                    "history_count": len(history),
                    "message": "At least 2 history entries needed for rollback",
                },
            )

        # Current status is the to_status of the most recent transition
        current_status = history[0].to_status
        # Previous status is the from_status of the most recent transition
        previous_status = history[0].from_status

        # Record the rollback transition
        entry = tracker.record_transition(
            object_id=object_id,
            object_type=object_type,
            from_status=current_status,
            to_status=previous_status,
            actor_id=context.actor_id,
            reason=f"ROLLBACK: {reason}",
            metadata={
                "is_rollback": True,
                "rolled_back_entry_id": history[0].entry_id,
                **context.metadata,
            },
        )

        # Create edit operation
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type=object_type,
            object_id=object_id,
            changes={
                "status": {
                    "old": current_status.value,
                    "new": previous_status.value,
                },
                "reason": reason,
                "is_rollback": True,
                "history_entry_id": entry.entry_id,
            },
            timestamp=context.timestamp,
        )

        logger.info(
            f"Status rollback: {object_type}:{object_id} "
            f"{current_status.value} -> {previous_status.value} by {context.actor_id}"
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "object_id": object_id,
                "object_type": object_type,
                "from_status": current_status.value,
                "to_status": previous_status.value,
                "history_entry_id": entry.entry_id,
                "rolled_back_entry_id": history[0].entry_id,
            },
            edits=[edit],
            modified_ids=[object_id],
            message=f"Rolled back {object_type}:{object_id} from {current_status.value} to {previous_status.value}",
        )


# =============================================================================
# STATUS HISTORY ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class StatusHistoryAction(ActionType[OntologyObject]):
    """
    Get status transition history for a resource.

    This action is non-hazardous (read-only) and does not require approval.

    Parameters:
        object_id: ID of the object to get history for
        limit: Maximum number of entries to return (default: 100)
        ascending: If True, oldest first (default: False)

    Returns:
        ActionResult with the history entries
    """

    api_name: ClassVar[str] = "status.history"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("object_id"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[OntologyObject], List[EditOperation]]:
        """Get status history (no edits)."""
        object_id = params["object_id"]
        limit = params.get("limit", 100)
        ascending = params.get("ascending", False)

        tracker = get_default_tracker()
        history = tracker.get_history(
            object_id=object_id,
            limit=limit,
            ascending=ascending,
        )

        history_data = [entry.to_dict() for entry in history]

        return ActionResult(
            action_type=self.api_name,
            success=True,
            data={
                "object_id": object_id,
                "history": history_data,
                "count": len(history_data),
            },
            edits=[],  # Read-only, no edits
            message=f"Retrieved {len(history_data)} history entries for {object_id}",
        )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    "StatusTransitionAction",
    "StatusRollbackAction",
    "StatusHistoryAction",
    "ValidStatusValue",
    "ValidTransitionValidator",
]
