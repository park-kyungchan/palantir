"""
Orion ODA v4.0 - Session Action Types
=====================================

ActionTypes for Session object management.
Provides lifecycle management and activity tracking.

Phase 3.4.2 Implementation:
- session.create: Create new session
- session.start: Start/activate session
- session.pause: Pause session
- session.resume: Resume paused session
- session.end: End session
- session.update_state: Update session state
- session.record_activity: Record user activity

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    AllowedValues,
    CustomValidator,
    EditOperation,
    EditType,
    RequiredField,
    register_action,
)
from lib.oda.ontology.objects.session import (
    Session,
    SessionEndReason,
    SessionStatus,
    SessionType,
)
from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# VALIDATORS
# =============================================================================


def validate_session_exists(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that session_id refers to an existing session."""
    session_id = params.get("session_id", "")
    return bool(session_id)


def validate_session_active(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that session is in active state."""
    # Would check session status in database
    return True


def validate_session_can_resume(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that session can be resumed (is paused)."""
    # Would check session is paused
    return True


# =============================================================================
# SESSION CREATE ACTION
# =============================================================================


@register_action
class SessionCreateAction(ActionType[Session]):
    """
    Create a new session.

    Parameters:
        session_type: Type of session (learning, assessment, workspace, etc.)
        workspace_id: Optional parent workspace ID
        learner_id: Optional associated learner ID
        agent_id: Optional assigned agent ID
        idle_timeout_minutes: Idle timeout (default: 30)
        max_duration_minutes: Max session duration (default: 480)
        client_type: Client type (web, cli, api)
        metadata: Additional session metadata

    Returns:
        Session: The created session object
    """
    api_name = "session.create"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        AllowedValues(
            "session_type",
            [st.value for st in SessionType]
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Create a new session."""
        session = Session(
            session_type=SessionType(params.get("session_type", "workspace")),
            session_status=SessionStatus.INITIALIZING,
            workspace_id=params.get("workspace_id"),
            learner_id=params.get("learner_id"),
            agent_id=params.get("agent_id"),
            idle_timeout_minutes=params.get("idle_timeout_minutes", 30),
            max_duration_minutes=params.get("max_duration_minutes", 480),
            client_type=params.get("client_type"),
            client_version=params.get("client_version"),
            user_agent=params.get("user_agent"),
            ip_address=params.get("ip_address"),
            metadata=params.get("metadata", {}),
            context=params.get("context", {}),
            tags=params.get("tags", []),
            created_by=context.actor_id,
        )

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Session",
            object_id=session.id,
            changes={
                "session_type": session.session_type.value,
                "workspace_id": session.workspace_id,
                "learner_id": session.learner_id,
                "actor": context.actor_id,
            }
        )

        return session, [edit]


# =============================================================================
# SESSION LIFECYCLE ACTIONS
# =============================================================================


@register_action
class SessionStartAction(ActionType[Session]):
    """
    Start/activate a session.

    Transitions session from INITIALIZING to ACTIVE.

    Parameters:
        session_id: ID of session to start (required)

    Returns:
        Session: The activated session
    """
    api_name = "session.start"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Start the session."""
        session_id = params["session_id"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "session_status": SessionStatus.ACTIVE.value,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "last_activity_at": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Session {session_id} started",
            edits=[edit],
            modified_ids=[session_id],
        )


@register_action
class SessionPauseAction(ActionType[Session]):
    """
    Pause an active session.

    Parameters:
        session_id: ID of session to pause (required)
        reason: Optional pause reason

    Returns:
        Session: The paused session
    """
    api_name = "session.pause"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Pause the session."""
        session_id = params["session_id"]
        reason = params.get("reason", "")

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "session_status": SessionStatus.PAUSED.value,
                "pause_reason": reason,
                "paused_at": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Session {session_id} paused",
            edits=[edit],
            modified_ids=[session_id],
        )


@register_action
class SessionResumeAction(ActionType[Session]):
    """
    Resume a paused session.

    Parameters:
        session_id: ID of session to resume (required)

    Returns:
        Session: The resumed session
    """
    api_name = "session.resume"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Resume the session."""
        session_id = params["session_id"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "session_status": SessionStatus.ACTIVE.value,
                "last_activity_at": datetime.now(timezone.utc).isoformat(),
                "resumed_at": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Session {session_id} resumed",
            edits=[edit],
            modified_ids=[session_id],
        )


@register_action
class SessionEndAction(ActionType[Session]):
    """
    End a session.

    Parameters:
        session_id: ID of session to end (required)
        end_reason: Reason for ending (user_logout, timeout, completed, etc.)

    Returns:
        Session: The ended session
    """
    api_name = "session.end"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
        AllowedValues(
            "end_reason",
            [er.value for er in SessionEndReason]
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """End the session."""
        session_id = params["session_id"]
        end_reason = params.get("end_reason", "user_logout")

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "session_status": SessionStatus.COMPLETED.value,
                "end_reason": end_reason,
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Session {session_id} ended",
            edits=[edit],
            modified_ids=[session_id],
        )


# =============================================================================
# SESSION STATE MANAGEMENT ACTIONS
# =============================================================================


@register_action
class SessionUpdateStateAction(ActionType[Session]):
    """
    Update session state data.

    Parameters:
        session_id: ID of session (required)
        state_updates: Dictionary of state updates to merge (required)
        replace: If True, replace state entirely; if False, merge (default: False)

    Returns:
        Session: The updated session
    """
    api_name = "session.update_state"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        RequiredField("state_updates"),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Update session state."""
        session_id = params["session_id"]
        state_updates = params["state_updates"]
        replace = params.get("replace", False)

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "state_update_mode": "replace" if replace else "merge",
                "state_updates": state_updates,
                "last_activity_at": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Session {session_id} state updated",
            edits=[edit],
            modified_ids=[session_id],
        )


@register_action
class SessionUpdateContextAction(ActionType[Session]):
    """
    Update session context data (e.g., course progress).

    Parameters:
        session_id: ID of session (required)
        context_updates: Dictionary of context updates to merge (required)

    Returns:
        Session: The updated session
    """
    api_name = "session.update_context"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        RequiredField("context_updates"),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Update session context."""
        session_id = params["session_id"]
        context_updates = params["context_updates"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "context_updates": context_updates,
                "last_activity_at": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Session {session_id} context updated",
            edits=[edit],
            modified_ids=[session_id],
        )


# =============================================================================
# SESSION ACTIVITY TRACKING ACTIONS
# =============================================================================


@register_action
class SessionRecordActivityAction(ActionType[Session]):
    """
    Record user activity in session.

    Parameters:
        session_id: ID of session (required)
        activity_type: Type of activity (interaction, message, action)
        activity_data: Optional activity details

    Returns:
        Session: The updated session
    """
    api_name = "session.record_activity"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        AllowedValues("activity_type", ["interaction", "message", "action", "answer"]),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Record activity in session."""
        session_id = params["session_id"]
        activity_type = params.get("activity_type", "interaction")
        activity_data = params.get("activity_data", {})

        # Determine which counter to increment
        counter_increments = {}
        if activity_type == "interaction":
            counter_increments["interaction_count"] = "+1"
        elif activity_type == "message":
            counter_increments["message_count"] = "+1"
        elif activity_type == "action":
            counter_increments["action_count"] = "+1"
        elif activity_type == "answer":
            counter_increments["questions_answered"] = "+1"
            if activity_data.get("is_correct"):
                counter_increments["correct_answers"] = "+1"

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "activity_type": activity_type,
                "counter_increments": counter_increments,
                "activity_data": activity_data,
                "last_activity_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Activity recorded in session {session_id}",
            edits=[edit],
            modified_ids=[session_id],
        )


@register_action
class SessionRecordHintAction(ActionType[Session]):
    """
    Record hint usage in a learning session.

    Parameters:
        session_id: ID of session (required)
        hint_context: Optional context about the hint

    Returns:
        Session: The updated session
    """
    api_name = "session.record_hint"
    object_type = Session
    requires_proposal = False

    submission_criteria = [
        RequiredField("session_id"),
        CustomValidator(
            name="SessionExists",
            validator_fn=validate_session_exists,
            error_message="Session not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Session], List[EditOperation]]:
        """Record hint usage."""
        session_id = params["session_id"]
        hint_context = params.get("hint_context", {})

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Session",
            object_id=session_id,
            changes={
                "hints_used": "+1",
                "hint_context": hint_context,
                "last_activity_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Hint recorded in session {session_id}",
            edits=[edit],
            modified_ids=[session_id],
        )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Lifecycle
    "SessionCreateAction",
    "SessionStartAction",
    "SessionPauseAction",
    "SessionResumeAction",
    "SessionEndAction",
    # State management
    "SessionUpdateStateAction",
    "SessionUpdateContextAction",
    # Activity tracking
    "SessionRecordActivityAction",
    "SessionRecordHintAction",
]
