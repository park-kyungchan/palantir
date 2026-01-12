"""
Orion ODA v4.0 - Session ObjectType
====================================

Session represents an interactive working session between
a user/learner and the system.

Palantir Pattern:
- Sessions track user interactions over time
- Session state is preserved for continuity
- Metrics and analytics per session

Schema Version: 4.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from lib.oda.ontology.ontology_types import Cardinality, Link, OntologyObject
from lib.oda.ontology.registry import register_object_type


class SessionType(str, Enum):
    """Type of session."""
    LEARNING = "learning"
    ASSESSMENT = "assessment"
    PRACTICE = "practice"
    TUTORING = "tutoring"
    COLLABORATION = "collaboration"
    WORKSPACE = "workspace"


class SessionStatus(str, Enum):
    """Session lifecycle status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class SessionEndReason(str, Enum):
    """Reason for session termination."""
    USER_LOGOUT = "user_logout"
    TIMEOUT = "timeout"
    COMPLETED = "completed"
    ERROR = "error"
    ADMIN_TERMINATED = "admin_terminated"
    SYSTEM_MAINTENANCE = "system_maintenance"


@register_object_type
class Session(OntologyObject):
    """
    ObjectType: Session

    Represents an interactive working session.
    Tracks user activity, state, and provides analytics.

    Links:
    - workspace: Workspace (Many-to-One)
    - learner: Learner (Many-to-One)
    - assessments: Assessment[] (One-to-Many)
    """

    # Session identity
    session_type: SessionType = Field(
        default=SessionType.WORKSPACE,
        description="Type of session"
    )
    session_status: SessionStatus = Field(
        default=SessionStatus.INITIALIZING,
        description="Current session status"
    )

    # Foreign keys
    workspace_id: Optional[str] = Field(
        default=None,
        description="Parent workspace ID"
    )
    learner_id: Optional[str] = Field(
        default=None,
        description="Associated learner ID"
    )
    agent_id: Optional[str] = Field(
        default=None,
        description="Assigned agent/tutor ID"
    )

    # Timing
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Session start time"
    )
    last_activity_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last activity timestamp"
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        description="Session end time"
    )
    end_reason: Optional[SessionEndReason] = Field(
        default=None,
        description="Reason for session end"
    )

    # Timeout settings
    idle_timeout_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,  # Max 24 hours
        description="Idle timeout in minutes"
    )
    max_duration_minutes: int = Field(
        default=480,  # 8 hours
        ge=1,
        description="Maximum session duration in minutes"
    )

    # State management
    state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session state data"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Session context (e.g., course progress)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    # Activity tracking
    interaction_count: int = Field(
        default=0,
        ge=0,
        description="Number of user interactions"
    )
    message_count: int = Field(
        default=0,
        ge=0,
        description="Number of messages exchanged"
    )
    action_count: int = Field(
        default=0,
        ge=0,
        description="Number of actions performed"
    )

    # Learning-specific metrics (for learning sessions)
    questions_answered: int = Field(
        default=0,
        ge=0,
        description="Questions answered in this session"
    )
    correct_answers: int = Field(
        default=0,
        ge=0,
        description="Correct answers in this session"
    )
    hints_used: int = Field(
        default=0,
        ge=0,
        description="Hints requested in this session"
    )

    # Client information
    client_type: Optional[str] = Field(
        default=None,
        description="Client type (web, cli, api)"
    )
    client_version: Optional[str] = Field(
        default=None,
        description="Client version"
    )
    user_agent: Optional[str] = Field(
        default=None,
        max_length=500,
        description="User agent string"
    )
    ip_address: Optional[str] = Field(
        default=None,
        description="Client IP address"
    )

    # Tags
    tags: List[str] = Field(
        default_factory=list,
        description="Session tags"
    )

    # Link definitions
    workspace: ClassVar[Link["Workspace"]] = Link(
        target="Workspace",
        link_type_id="session_belongs_to_workspace",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="workspace_has_sessions",
        description="Parent workspace",
    )

    learner: ClassVar[Link["Learner"]] = Link(
        target="Learner",
        link_type_id="session_belongs_to_learner",
        cardinality=Cardinality.MANY_TO_ONE,
        reverse_link_id="learner_has_sessions",
        description="Associated learner",
    )

    assessments: ClassVar[Link["Assessment"]] = Link(
        target="Assessment",
        link_type_id="session_has_assessments",
        cardinality=Cardinality.ONE_TO_MANY,
        reverse_link_id="assessment_in_session",
        description="Assessments taken in this session",
    )

    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds."""
        end = self.ended_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    @property
    def duration_minutes(self) -> float:
        """Get session duration in minutes."""
        return self.duration_seconds / 60

    @property
    def is_expired(self) -> bool:
        """Check if session has exceeded max duration."""
        if self.session_status in (SessionStatus.COMPLETED, SessionStatus.TERMINATED):
            return False
        max_end = self.started_at + timedelta(minutes=self.max_duration_minutes)
        return datetime.now(timezone.utc) > max_end

    @property
    def is_idle(self) -> bool:
        """Check if session is idle (no recent activity)."""
        if self.session_status != SessionStatus.ACTIVE:
            return False
        idle_threshold = self.last_activity_at + timedelta(minutes=self.idle_timeout_minutes)
        return datetime.now(timezone.utc) > idle_threshold

    @property
    def accuracy_rate(self) -> float:
        """Get accuracy rate for learning sessions."""
        if self.questions_answered == 0:
            return 0.0
        return (self.correct_answers / self.questions_answered) * 100

    def record_activity(self) -> None:
        """Record user activity."""
        self.last_activity_at = datetime.now(timezone.utc)
        self.interaction_count += 1
        self.touch()

    def record_message(self) -> None:
        """Record a message in the session."""
        self.message_count += 1
        self.record_activity()

    def record_action(self) -> None:
        """Record an action in the session."""
        self.action_count += 1
        self.record_activity()

    def record_answer(self, is_correct: bool) -> None:
        """Record an answer (for learning sessions)."""
        self.questions_answered += 1
        if is_correct:
            self.correct_answers += 1
        self.record_activity()

    def end_session(self, reason: SessionEndReason = SessionEndReason.USER_LOGOUT) -> None:
        """End the session."""
        self.session_status = SessionStatus.COMPLETED
        self.ended_at = datetime.now(timezone.utc)
        self.end_reason = reason
        self.touch()

    def pause(self) -> None:
        """Pause the session."""
        self.session_status = SessionStatus.PAUSED
        self.touch()

    def resume(self) -> None:
        """Resume a paused session."""
        if self.session_status == SessionStatus.PAUSED:
            self.session_status = SessionStatus.ACTIVE
            self.record_activity()

    def activate(self) -> None:
        """Activate an initializing session."""
        if self.session_status == SessionStatus.INITIALIZING:
            self.session_status = SessionStatus.ACTIVE
            self.touch()


# Forward reference resolution
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.oda.ontology.objects.workspace import Workspace
    from lib.oda.ontology.objects.learner import Learner
    from lib.oda.ontology.objects.assessment import Assessment
