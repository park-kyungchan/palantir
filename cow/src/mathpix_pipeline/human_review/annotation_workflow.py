"""
AnnotationWorkflow for Human Review system.

Manages the annotation process including:
- Session management
- Annotation saving and validation
- Review submission
- Second opinion requests

Module Version: 1.0.0
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .models.task import (
    ReviewTask,
    ReviewStatus,
    ReviewDecision,
)
from .models.annotation import (
    Annotation,
    AnnotationSession,
    Correction,
    SessionStatus,
)
from .models.reviewer import Reviewer
from .exceptions import (
    AnnotationError,
    SessionExpiredError,
    TaskNotFoundError,
    ReviewTaskError,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AnnotationWorkflowConfig:
    """Configuration for AnnotationWorkflow."""
    # Session settings
    session_timeout_minutes: int = 60
    max_session_duration_minutes: int = 120
    auto_save_interval_seconds: int = 30

    # Validation settings
    require_reason_for_reject: bool = True
    require_correction_for_modify: bool = True
    min_review_time_seconds: int = 10

    # Second opinion settings
    enable_second_opinion: bool = True
    auto_second_opinion_threshold: float = 0.35


# =============================================================================
# Review Result
# =============================================================================

class ReviewResult:
    """Result of a completed review."""

    def __init__(
        self,
        result_id: str,
        task_id: str,
        session_id: str,
        reviewer_id: str,
        decision: ReviewDecision,
        annotation: Optional[Annotation],
        review_time_ms: float,
    ):
        self.result_id = result_id
        self.task_id = task_id
        self.session_id = session_id
        self.reviewer_id = reviewer_id
        self.decision = decision
        self.annotation = annotation
        self.review_time_ms = review_time_ms
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "reviewer_id": self.reviewer_id,
            "decision": self.decision.value,
            "annotation": self.annotation.model_dump() if self.annotation else None,
            "review_time_ms": self.review_time_ms,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# AnnotationWorkflow
# =============================================================================

class AnnotationWorkflow:
    """Manages the annotation workflow for human review.

    Provides:
    - Session lifecycle management
    - Annotation creation and validation
    - Review submission with validation
    - Second opinion handling

    Usage:
        workflow = AnnotationWorkflow()

        # Start annotation
        session = await workflow.start_annotation("task-123", "reviewer-456")

        # Save annotation
        await workflow.save_annotation(session.session_id, annotation)

        # Submit review
        result = await workflow.submit_review(
            session.session_id,
            ReviewDecision.APPROVE
        )
    """

    def __init__(
        self,
        config: Optional[AnnotationWorkflowConfig] = None,
    ):
        """Initialize workflow.

        Args:
            config: Workflow configuration
        """
        self.config = config or AnnotationWorkflowConfig()

        # In-memory storage (for demo; use proper DB in production)
        self._sessions: Dict[str, AnnotationSession] = {}
        self._tasks: Dict[str, ReviewTask] = {}
        self._results: Dict[str, ReviewResult] = {}
        self._reviewers: Dict[str, Reviewer] = {}

        # Locks
        self._lock = asyncio.Lock()

        logger.info("AnnotationWorkflow initialized")

    # =========================================================================
    # Session Management
    # =========================================================================

    async def start_annotation(
        self,
        task_id: str,
        reviewer_id: str,
        task: Optional[ReviewTask] = None,
    ) -> AnnotationSession:
        """Start an annotation session for a task.

        Args:
            task_id: Task to annotate
            reviewer_id: Reviewer starting the session
            task: Optional task object (fetched if not provided)

        Returns:
            AnnotationSession

        Raises:
            TaskNotFoundError: If task not found
            ReviewTaskError: If task cannot be annotated
        """
        async with self._lock:
            # Get or validate task
            if task:
                self._tasks[task_id] = task
            elif task_id not in self._tasks:
                raise TaskNotFoundError(
                    message=f"Task not found: {task_id}",
                    task_id=task_id,
                )

            current_task = self._tasks[task_id]

            # Validate task status
            if current_task.status not in (
                ReviewStatus.ASSIGNED,
                ReviewStatus.IN_PROGRESS,
            ):
                raise ReviewTaskError(
                    message=f"Task cannot be annotated in status {current_task.status.value}",
                    task_id=task_id,
                    status=current_task.status.value,
                )

            # Validate assignment
            if (
                current_task.assigned_to
                and current_task.assigned_to != reviewer_id
            ):
                raise ReviewTaskError(
                    message="Task assigned to different reviewer",
                    task_id=task_id,
                    reviewer_id=reviewer_id,
                )

            # Create session
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            session = AnnotationSession(
                session_id=session_id,
                task_id=task_id,
                reviewer_id=reviewer_id,
                timeout_minutes=self.config.session_timeout_minutes,
                max_duration_minutes=self.config.max_session_duration_minutes,
            )

            # Create empty annotation
            annotation = Annotation(
                annotation_id=f"ann-{uuid.uuid4().hex[:8]}",
                task_id=task_id,
                reviewer_id=reviewer_id,
            )
            session.annotation = annotation

            # Update task status
            current_task.start()
            self._tasks[task_id] = current_task

            # Store session
            self._sessions[session_id] = session

            logger.info(
                f"Started annotation session {session_id} "
                f"for task {task_id} by reviewer {reviewer_id}"
            )

            return session

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[AnnotationSession]:
        """Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            AnnotationSession or None
        """
        return self._sessions.get(session_id)

    async def extend_session(
        self,
        session_id: str,
        additional_minutes: int = 30,
    ) -> AnnotationSession:
        """Extend a session's timeout.

        Args:
            session_id: Session to extend
            additional_minutes: Minutes to add

        Returns:
            Updated session
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionExpiredError(
                    message=f"Session not found: {session_id}",
                    session_id=session_id,
                )

            if session.status != SessionStatus.ACTIVE:
                raise SessionExpiredError(
                    message=f"Session not active: {session.status.value}",
                    session_id=session_id,
                )

            # Extend expiration
            session.expires_at = session.expires_at + timedelta(
                minutes=additional_minutes
            )
            session.record_activity()
            self._sessions[session_id] = session

            logger.info(f"Extended session {session_id} by {additional_minutes} minutes")

            return session

    # =========================================================================
    # Annotation Management
    # =========================================================================

    async def save_annotation(
        self,
        session_id: str,
        annotation: Annotation,
    ) -> None:
        """Save annotation progress.

        Args:
            session_id: Session identifier
            annotation: Annotation to save

        Raises:
            SessionExpiredError: If session expired
            AnnotationError: If validation fails
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionExpiredError(
                    message=f"Session not found: {session_id}",
                    session_id=session_id,
                )

            if session.is_expired:
                session.expire()
                self._sessions[session_id] = session
                raise SessionExpiredError(
                    message="Session has expired",
                    session_id=session_id,
                    expired_at=session.expires_at.isoformat(),
                )

            # Validate annotation
            if annotation.task_id != session.task_id:
                raise AnnotationError(
                    message="Annotation task_id mismatch",
                    annotation_id=annotation.annotation_id,
                    session_id=session_id,
                )

            # Save annotation
            session.save_progress(annotation)
            self._sessions[session_id] = session

            logger.debug(
                f"Saved annotation for session {session_id}: "
                f"{annotation.correction_count} corrections"
            )

    async def add_correction(
        self,
        session_id: str,
        correction: Correction,
    ) -> Annotation:
        """Add a correction to the current annotation.

        Args:
            session_id: Session identifier
            correction: Correction to add

        Returns:
            Updated annotation
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionExpiredError(
                    message=f"Session not found: {session_id}",
                    session_id=session_id,
                )

            if session.is_expired:
                session.expire()
                raise SessionExpiredError(
                    message="Session has expired",
                    session_id=session_id,
                )

            if session.annotation is None:
                raise AnnotationError(
                    message="No annotation in session",
                    session_id=session_id,
                )

            session.annotation.add_correction(correction)
            session.record_activity()
            self._sessions[session_id] = session

            return session.annotation

    async def remove_correction(
        self,
        session_id: str,
        correction_id: str,
    ) -> bool:
        """Remove a correction from the current annotation.

        Args:
            session_id: Session identifier
            correction_id: Correction to remove

        Returns:
            True if removed
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session or session.annotation is None:
                return False

            removed = session.annotation.remove_correction(correction_id)
            if removed:
                session.record_activity()
                self._sessions[session_id] = session

            return removed

    # =========================================================================
    # Review Submission
    # =========================================================================

    async def submit_review(
        self,
        session_id: str,
        decision: ReviewDecision,
        reason: Optional[str] = None,
    ) -> ReviewResult:
        """Submit the review for a session.

        Args:
            session_id: Session identifier
            decision: Review decision
            reason: Optional reason for decision

        Returns:
            ReviewResult

        Raises:
            SessionExpiredError: If session expired
            AnnotationError: If validation fails
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                raise SessionExpiredError(
                    message=f"Session not found: {session_id}",
                    session_id=session_id,
                )

            if session.is_expired:
                session.expire()
                raise SessionExpiredError(
                    message="Session has expired",
                    session_id=session_id,
                )

            # Validate review
            self._validate_review(session, decision, reason)

            # Get task
            task = self._tasks.get(session.task_id)
            if not task:
                raise TaskNotFoundError(
                    message=f"Task not found: {session.task_id}",
                    task_id=session.task_id,
                )

            # Create result
            result = ReviewResult(
                result_id=f"result-{uuid.uuid4().hex[:8]}",
                task_id=session.task_id,
                session_id=session_id,
                reviewer_id=session.reviewer_id,
                decision=decision,
                annotation=session.annotation,
                review_time_ms=session.duration_ms,
            )

            # Update task
            task.complete(decision, reason)
            self._tasks[session.task_id] = task

            # Complete session
            session.complete()
            self._sessions[session_id] = session

            # Store result
            self._results[result.result_id] = result

            logger.info(
                f"Review submitted for task {session.task_id}: "
                f"decision={decision.value}, "
                f"time={session.duration_ms:.0f}ms"
            )

            return result

    def _validate_review(
        self,
        session: AnnotationSession,
        decision: ReviewDecision,
        reason: Optional[str],
    ) -> None:
        """Validate review before submission."""
        # Check minimum review time
        if session.duration_ms < self.config.min_review_time_seconds * 1000:
            raise AnnotationError(
                message=(
                    f"Review time too short: {session.duration_ms}ms "
                    f"(minimum: {self.config.min_review_time_seconds}s)"
                ),
                session_id=session.session_id,
            )

        # Require reason for reject
        if (
            self.config.require_reason_for_reject
            and decision == ReviewDecision.REJECT
            and not reason
        ):
            raise AnnotationError(
                message="Reason required for rejection",
                session_id=session.session_id,
            )

        # Require correction for modify
        if (
            self.config.require_correction_for_modify
            and decision == ReviewDecision.MODIFY
        ):
            if (
                session.annotation is None
                or session.annotation.correction_count == 0
            ):
                raise AnnotationError(
                    message="Correction required for modify decision",
                    session_id=session.session_id,
                )

    # =========================================================================
    # Second Opinion
    # =========================================================================

    async def request_second_opinion(
        self,
        task_id: str,
        reason: str,
        requester_id: str,
    ) -> ReviewTask:
        """Request a second opinion on a task.

        Args:
            task_id: Task to get second opinion on
            reason: Reason for request
            requester_id: Who is requesting

        Returns:
            Updated task (ready for re-assignment)
        """
        if not self.config.enable_second_opinion:
            raise ReviewTaskError(
                message="Second opinion not enabled",
                task_id=task_id,
            )

        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise TaskNotFoundError(
                    message=f"Task not found: {task_id}",
                    task_id=task_id,
                )

            # Escalate task
            task.escalate(f"Second opinion requested: {reason}")

            # Store context for second reviewer
            task.context.stage_context["second_opinion_requested"] = True
            task.context.stage_context["original_reviewer"] = requester_id
            task.context.stage_context["second_opinion_reason"] = reason

            self._tasks[task_id] = task

            logger.info(
                f"Second opinion requested for task {task_id} "
                f"by {requester_id}: {reason}"
            )

            return task

    async def check_needs_second_opinion(
        self,
        task_id: str,
    ) -> bool:
        """Check if a task should have second opinion.

        Based on confidence and configuration threshold.

        Args:
            task_id: Task to check

        Returns:
            True if second opinion recommended
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        return (
            self.config.enable_second_opinion
            and task.context.original_confidence < self.config.auto_second_opinion_threshold
        )

    # =========================================================================
    # Session Cleanup
    # =========================================================================

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        cleaned = 0

        async with self._lock:
            for session_id, session in list(self._sessions.items()):
                if session.is_expired and session.status == SessionStatus.ACTIVE:
                    session.expire()
                    self._sessions[session_id] = session
                    cleaned += 1

                    # Release task
                    task = self._tasks.get(session.task_id)
                    if task and task.status == ReviewStatus.IN_PROGRESS:
                        task.status = ReviewStatus.ASSIGNED
                        self._tasks[session.task_id] = task

                    logger.info(f"Cleaned up expired session {session_id}")

        return cleaned

    async def abandon_session(
        self,
        session_id: str,
    ) -> None:
        """Abandon a session.

        Args:
            session_id: Session to abandon
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return

            session.abandon()
            self._sessions[session_id] = session

            # Release task
            task = self._tasks.get(session.task_id)
            if task:
                task.status = ReviewStatus.ASSIGNED
                task.assigned_to = None
                self._tasks[session.task_id] = task

            logger.info(f"Session {session_id} abandoned")


# =============================================================================
# Factory Function
# =============================================================================

def create_annotation_workflow(
    config: Optional[AnnotationWorkflowConfig] = None,
) -> AnnotationWorkflow:
    """Create an AnnotationWorkflow instance.

    Args:
        config: Optional configuration

    Returns:
        AnnotationWorkflow instance
    """
    return AnnotationWorkflow(config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "AnnotationWorkflowConfig",
    "ReviewResult",
    "AnnotationWorkflow",
    "create_annotation_workflow",
]
