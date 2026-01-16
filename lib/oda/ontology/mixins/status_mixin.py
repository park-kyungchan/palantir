"""
Orion ODA v4.0 - Status Mixin
==============================

This module provides the StatusMixin class that can be added to OntologyObjects
to enable lifecycle status management with validated transitions.

Features:
- transition_to(): Perform validated status transitions
- can_transition_to(): Check if a transition is valid
- get_allowed_transitions(): List all valid target statuses
- Automatic history tracking (when StatusHistory is available)

Example:
    ```python
    class Project(OntologyObject, StatusMixin):
        name: str
        description: str

    project = Project(name="Alpha", description="Test project")
    project.initialize_status()  # Sets to DRAFT

    # Check what transitions are allowed
    allowed = project.get_allowed_transitions()
    # [EXPERIMENTAL, ACTIVE, DELETED]

    # Transition to a new status
    project.transition_to(ResourceLifecycleStatus.EXPERIMENTAL, actor_id="user-123")
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type

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

if TYPE_CHECKING:
    from lib.oda.ontology.tracking.status_history import StatusHistoryTracker

logger = logging.getLogger(__name__)


@dataclass
class StatusTransitionContext:
    """
    Context information for a status transition.

    Contains metadata about who initiated the transition and why.

    Attributes:
        actor_id: ID of the user/agent performing the transition
        reason: Optional explanation for the transition
        timestamp: When the transition occurred
        metadata: Additional context information
    """
    actor_id: str
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "actor_id": self.actor_id,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class StatusMixin:
    """
    Mixin class providing lifecycle status management for OntologyObjects.

    This mixin adds:
    - _status: Current lifecycle status
    - _status_changed_at: Timestamp of last status change
    - _status_changed_by: Actor who last changed status

    Methods:
    - initialize_status(): Set initial status to DRAFT
    - transition_to(): Perform validated status transition
    - can_transition_to(): Check if transition is valid
    - get_allowed_transitions(): List valid target statuses
    - get_status(): Get current status
    """

    # These will be set on the class that uses this mixin
    _status: ResourceLifecycleStatus = ResourceLifecycleStatus.DRAFT
    _status_changed_at: Optional[datetime] = None
    _status_changed_by: Optional[str] = None

    # Optional history tracker (injected if available)
    _status_history_tracker: Optional["StatusHistoryTracker"] = None

    # Transition hooks
    _pre_transition_hooks: List[Callable[["StatusMixin", ResourceLifecycleStatus, ResourceLifecycleStatus], None]] = []
    _post_transition_hooks: List[Callable[["StatusMixin", ResourceLifecycleStatus, ResourceLifecycleStatus], None]] = []

    def initialize_status(
        self,
        status: ResourceLifecycleStatus = ResourceLifecycleStatus.DRAFT,
        actor_id: str = "system",
    ) -> None:
        """
        Initialize the status for a new object.

        Args:
            status: Initial status (default: DRAFT)
            actor_id: Actor creating the object
        """
        self._status = status
        self._status_changed_at = datetime.now(timezone.utc)
        self._status_changed_by = actor_id

        logger.debug(
            f"Initialized status to {status.value} for {self.__class__.__name__}"
        )

    def get_status(self) -> ResourceLifecycleStatus:
        """
        Get the current lifecycle status.

        Returns:
            Current ResourceLifecycleStatus
        """
        return self._status

    def get_status_info(self) -> Dict[str, Any]:
        """
        Get full status information including change metadata.

        Returns:
            Dictionary with status, changed_at, and changed_by
        """
        return {
            "status": self._status.value,
            "changed_at": self._status_changed_at.isoformat() if self._status_changed_at else None,
            "changed_by": self._status_changed_by,
            "is_usable": self._status.is_usable(),
            "is_modifiable": self._status.is_modifiable(),
            "stage": self._status.get_stage(),
        }

    def can_transition_to(self, target_status: ResourceLifecycleStatus) -> bool:
        """
        Check if a transition to the target status is valid.

        Args:
            target_status: The status to transition to

        Returns:
            True if the transition is allowed
        """
        return is_valid_transition(self._status, target_status)

    def get_allowed_transitions(self) -> List[ResourceLifecycleStatus]:
        """
        Get all valid target statuses from the current status.

        Returns:
            List of ResourceLifecycleStatus values that can be transitioned to
        """
        return get_allowed_transitions(self._status)

    def transition_to(
        self,
        new_status: ResourceLifecycleStatus,
        actor_id: str,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        skip_validation: bool = False,
    ) -> TransitionValidationResult:
        """
        Transition to a new lifecycle status.

        This method:
        1. Validates the transition is allowed
        2. Executes pre-transition hooks
        3. Updates the status
        4. Records the transition in history (if tracker available)
        5. Executes post-transition hooks

        Args:
            new_status: Target status
            actor_id: ID of actor performing the transition
            reason: Optional explanation for the transition
            metadata: Additional context information
            skip_validation: If True, skip transition validation (use with caution)

        Returns:
            TransitionValidationResult with validation details

        Raises:
            StatusTransitionError: If transition is invalid and skip_validation is False
        """
        old_status = self._status
        context = StatusTransitionContext(
            actor_id=actor_id,
            reason=reason,
            metadata=metadata or {},
        )

        # Validate transition
        validator = StatusTransitionValidator()
        result = validator.validate_transition(
            from_status=old_status,
            to_status=new_status,
            raise_on_invalid=not skip_validation,
        )

        if not result.is_valid and not skip_validation:
            return result

        # Execute pre-transition hooks
        for hook in self._pre_transition_hooks:
            try:
                hook(self, old_status, new_status)
            except Exception as e:
                logger.error(f"Pre-transition hook failed: {e}")
                raise StatusTransitionError(
                    from_status=old_status,
                    to_status=new_status,
                    message=f"Pre-transition hook failed: {e}",
                )

        # Perform the transition
        self._status = new_status
        self._status_changed_at = context.timestamp
        self._status_changed_by = actor_id

        # Record in history
        if self._status_history_tracker:
            try:
                self._status_history_tracker.record_transition(
                    object_id=getattr(self, "id", str(id(self))),
                    object_type=self.__class__.__name__,
                    from_status=old_status,
                    to_status=new_status,
                    context=context,
                )
            except Exception as e:
                logger.warning(f"Failed to record status history: {e}")

        # Execute post-transition hooks
        for hook in self._post_transition_hooks:
            try:
                hook(self, old_status, new_status)
            except Exception as e:
                logger.warning(f"Post-transition hook failed: {e}")

        logger.info(
            f"Status transition: {self.__class__.__name__} "
            f"{old_status.value} -> {new_status.value} by {actor_id}"
        )

        return result

    def set_history_tracker(self, tracker: "StatusHistoryTracker") -> None:
        """
        Set the status history tracker for recording transitions.

        Args:
            tracker: StatusHistoryTracker instance
        """
        self._status_history_tracker = tracker

    def add_pre_transition_hook(
        self,
        hook: Callable[["StatusMixin", ResourceLifecycleStatus, ResourceLifecycleStatus], None],
    ) -> None:
        """
        Add a hook to be called before status transitions.

        Args:
            hook: Callable that takes (self, old_status, new_status)
        """
        self._pre_transition_hooks.append(hook)

    def add_post_transition_hook(
        self,
        hook: Callable[["StatusMixin", ResourceLifecycleStatus, ResourceLifecycleStatus], None],
    ) -> None:
        """
        Add a hook to be called after status transitions.

        Args:
            hook: Callable that takes (self, old_status, new_status)
        """
        self._post_transition_hooks.append(hook)

    def is_usable(self) -> bool:
        """Check if the resource can be actively used."""
        return self._status.is_usable()

    def is_modifiable(self) -> bool:
        """Check if the resource can be modified."""
        return self._status.is_modifiable()

    def is_visible(self) -> bool:
        """Check if the resource should be visible in listings."""
        return self._status.is_visible()


__all__ = [
    "StatusMixin",
    "StatusTransitionContext",
]
