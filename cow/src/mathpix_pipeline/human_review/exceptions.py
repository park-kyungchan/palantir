"""
Human Review module exception hierarchy.

Provides specific exception types for different review failure modes:
- HumanReviewError: Base exception for all review errors
- QueueError: Queue operation failures
- AnnotationError: Annotation operation failures
- ReviewTaskError: Review task failures

Schema Version: 2.0.0
"""

from typing import Any, Dict, Optional


class HumanReviewError(Exception):
    """Base exception for all human review-related errors.

    Attributes:
        message: Human-readable error description
        details: Additional context about the error
        recoverable: Whether the error is potentially recoverable
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable

    def __str__(self) -> str:
        base = self.message
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base = f"{base} ({detail_str})"
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


class QueueError(HumanReviewError):
    """Raised when queue operations fail."""

    def __init__(
        self,
        message: str,
        queue_name: Optional[str] = None,
        operation: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        details = {}
        if queue_name:
            details["queue_name"] = queue_name
        if operation:
            details["operation"] = operation
        if task_id:
            details["task_id"] = task_id

        super().__init__(
            message=message,
            details=details,
            recoverable=True,
        )
        self.queue_name = queue_name
        self.operation = operation
        self.task_id = task_id


class AnnotationError(HumanReviewError):
    """Raised when annotation operations fail."""

    def __init__(
        self,
        message: str,
        annotation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        details = {}
        if annotation_id:
            details["annotation_id"] = annotation_id
        if session_id:
            details["session_id"] = session_id
        if reason:
            details["reason"] = reason

        super().__init__(
            message=message,
            details=details,
            recoverable=True,
        )
        self.annotation_id = annotation_id
        self.session_id = session_id
        self.reason = reason


class ReviewTaskError(HumanReviewError):
    """Raised when review task operations fail."""

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        reviewer_id: Optional[str] = None,
        status: Optional[str] = None,
    ):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if reviewer_id:
            details["reviewer_id"] = reviewer_id
        if status:
            details["status"] = status

        super().__init__(
            message=message,
            details=details,
            recoverable=True,
        )
        self.task_id = task_id
        self.reviewer_id = reviewer_id
        self.status = status


class FeedbackLoopError(HumanReviewError):
    """Raised when feedback loop operations fail."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        data_type: Optional[str] = None,
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if data_type:
            details["data_type"] = data_type

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.operation = operation
        self.data_type = data_type


class SessionExpiredError(HumanReviewError):
    """Raised when a review session has expired."""

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        expired_at: Optional[str] = None,
    ):
        details = {}
        if session_id:
            details["session_id"] = session_id
        if expired_at:
            details["expired_at"] = expired_at

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.session_id = session_id
        self.expired_at = expired_at


class TaskNotFoundError(HumanReviewError):
    """Raised when a task is not found."""

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
    ):
        details = {}
        if task_id:
            details["task_id"] = task_id

        super().__init__(
            message=message,
            details=details,
            recoverable=False,
        )
        self.task_id = task_id


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "HumanReviewError",
    "QueueError",
    "AnnotationError",
    "ReviewTaskError",
    "FeedbackLoopError",
    "SessionExpiredError",
    "TaskNotFoundError",
]
