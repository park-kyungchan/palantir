"""
Orion ODA v4.0 - Status Transition Validator
=============================================

This module provides validation for resource lifecycle status transitions,
ensuring only valid state changes are permitted.

Validation Rules:
- Transitions must follow the defined valid paths
- Invalid transitions raise ValidationError
- Each transition is validated against the transition matrix

Example:
    ```python
    validator = StatusTransitionValidator()

    # Valid transition
    validator.validate_transition(
        ResourceLifecycleStatus.DRAFT,
        ResourceLifecycleStatus.EXPERIMENTAL
    )  # Returns True

    # Invalid transition
    validator.validate_transition(
        ResourceLifecycleStatus.DELETED,
        ResourceLifecycleStatus.ACTIVE
    )  # Raises StatusTransitionError
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from lib.oda.ontology.types.status_types import (
    ResourceLifecycleStatus,
    VALID_TRANSITIONS,
    get_allowed_transitions,
    is_valid_transition,
)


class StatusTransitionError(Exception):
    """
    Raised when an invalid status transition is attempted.

    Attributes:
        from_status: The current status
        to_status: The attempted target status
        allowed_transitions: List of valid target statuses
        message: Detailed error message
    """

    def __init__(
        self,
        from_status: ResourceLifecycleStatus,
        to_status: ResourceLifecycleStatus,
        allowed_transitions: Optional[List[ResourceLifecycleStatus]] = None,
        message: Optional[str] = None,
    ):
        self.from_status = from_status
        self.to_status = to_status
        self.allowed_transitions = allowed_transitions or get_allowed_transitions(from_status)

        if message:
            self.message = message
        else:
            allowed_str = ", ".join(s.value for s in self.allowed_transitions) or "none"
            self.message = (
                f"Invalid status transition from '{from_status.value}' to '{to_status.value}'. "
                f"Allowed transitions: [{allowed_str}]"
            )

        super().__init__(self.message)


@dataclass
class TransitionValidationResult:
    """
    Result of a transition validation check.

    Attributes:
        is_valid: Whether the transition is allowed
        from_status: Source status
        to_status: Target status
        error_message: Explanation if invalid
        warnings: Non-blocking warnings about the transition
    """
    is_valid: bool
    from_status: ResourceLifecycleStatus
    to_status: ResourceLifecycleStatus
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "error_message": self.error_message,
            "warnings": self.warnings,
        }


class StatusTransitionValidator:
    """
    Validator for resource lifecycle status transitions.

    Provides both strict validation (raises exceptions) and soft validation
    (returns results) for different use cases.

    Features:
    - Validates against defined transition rules
    - Provides detailed error messages
    - Supports custom transition rules
    - Generates warnings for risky transitions
    """

    # Transitions that should generate warnings
    RISKY_TRANSITIONS: Set[Tuple[ResourceLifecycleStatus, ResourceLifecycleStatus]] = {
        (ResourceLifecycleStatus.ACTIVE, ResourceLifecycleStatus.DEPRECATED),
        (ResourceLifecycleStatus.STABLE, ResourceLifecycleStatus.DEPRECATED),
        (ResourceLifecycleStatus.ARCHIVED, ResourceLifecycleStatus.DELETED),
    }

    # Transitions that skip intermediate states (for warnings)
    SKIP_TRANSITIONS: Set[Tuple[ResourceLifecycleStatus, ResourceLifecycleStatus]] = {
        (ResourceLifecycleStatus.DRAFT, ResourceLifecycleStatus.ACTIVE),
        (ResourceLifecycleStatus.DEPRECATED, ResourceLifecycleStatus.ARCHIVED),
    }

    def __init__(self, custom_transitions: Optional[Dict[ResourceLifecycleStatus, Set[ResourceLifecycleStatus]]] = None):
        """
        Initialize the validator.

        Args:
            custom_transitions: Optional custom transition rules to override defaults
        """
        self._transitions = custom_transitions or VALID_TRANSITIONS

    def validate_transition(
        self,
        from_status: ResourceLifecycleStatus,
        to_status: ResourceLifecycleStatus,
        raise_on_invalid: bool = True,
    ) -> TransitionValidationResult:
        """
        Validate a status transition.

        Args:
            from_status: Current resource status
            to_status: Target status
            raise_on_invalid: If True, raises StatusTransitionError on invalid transition

        Returns:
            TransitionValidationResult with validation details

        Raises:
            StatusTransitionError: If transition is invalid and raise_on_invalid is True
        """
        warnings: List[str] = []

        # Check if transition is in the allowed set
        allowed = self._transitions.get(from_status, set())
        is_valid = to_status in allowed

        error_message = None
        if not is_valid:
            allowed_str = ", ".join(s.value for s in allowed) or "none"
            error_message = (
                f"Cannot transition from '{from_status.value}' to '{to_status.value}'. "
                f"Valid targets: [{allowed_str}]"
            )

            if raise_on_invalid:
                raise StatusTransitionError(
                    from_status=from_status,
                    to_status=to_status,
                    allowed_transitions=list(allowed),
                    message=error_message,
                )
        else:
            # Generate warnings for valid but risky transitions
            transition_pair = (from_status, to_status)

            if transition_pair in self.RISKY_TRANSITIONS:
                warnings.append(
                    f"Warning: Transitioning from '{from_status.value}' to '{to_status.value}' "
                    f"is a significant lifecycle change. Ensure dependent resources are updated."
                )

            if transition_pair in self.SKIP_TRANSITIONS:
                warnings.append(
                    f"Warning: This transition skips intermediate lifecycle stages. "
                    f"Consider following the standard progression for better tracking."
                )

            # Special warnings for terminal states
            if to_status == ResourceLifecycleStatus.DELETED:
                warnings.append(
                    "Warning: DELETED is a terminal state. "
                    "The resource cannot be transitioned out of this state."
                )

        return TransitionValidationResult(
            is_valid=is_valid,
            from_status=from_status,
            to_status=to_status,
            error_message=error_message,
            warnings=warnings,
        )

    def get_allowed_transitions(self, status: ResourceLifecycleStatus) -> List[ResourceLifecycleStatus]:
        """
        Get all valid target statuses for a given status.

        Args:
            status: Current resource status

        Returns:
            List of allowed target statuses
        """
        return list(self._transitions.get(status, set()))

    def can_transition_to(
        self,
        from_status: ResourceLifecycleStatus,
        to_status: ResourceLifecycleStatus,
    ) -> bool:
        """
        Quick check if a transition is valid.

        Args:
            from_status: Current status
            to_status: Target status

        Returns:
            True if transition is allowed
        """
        return to_status in self._transitions.get(from_status, set())

    def get_transition_path(
        self,
        from_status: ResourceLifecycleStatus,
        to_status: ResourceLifecycleStatus,
    ) -> Optional[List[ResourceLifecycleStatus]]:
        """
        Find the shortest valid transition path between two statuses.

        Uses BFS to find the optimal path through valid transitions.

        Args:
            from_status: Starting status
            to_status: Target status

        Returns:
            List of statuses representing the path, or None if no path exists
        """
        if from_status == to_status:
            return [from_status]

        # BFS for shortest path
        from collections import deque

        queue = deque([(from_status, [from_status])])
        visited = {from_status}

        while queue:
            current, path = queue.popleft()

            for next_status in self._transitions.get(current, set()):
                if next_status == to_status:
                    return path + [next_status]

                if next_status not in visited:
                    visited.add(next_status)
                    queue.append((next_status, path + [next_status]))

        return None  # No valid path exists


# Convenience functions
def validate_transition(
    from_status: ResourceLifecycleStatus,
    to_status: ResourceLifecycleStatus,
) -> TransitionValidationResult:
    """
    Validate a status transition using the default validator.

    Args:
        from_status: Current status
        to_status: Target status

    Returns:
        TransitionValidationResult
    """
    validator = StatusTransitionValidator()
    return validator.validate_transition(from_status, to_status, raise_on_invalid=False)


def assert_valid_transition(
    from_status: ResourceLifecycleStatus,
    to_status: ResourceLifecycleStatus,
) -> None:
    """
    Assert that a transition is valid, raising on failure.

    Args:
        from_status: Current status
        to_status: Target status

    Raises:
        StatusTransitionError: If transition is invalid
    """
    validator = StatusTransitionValidator()
    validator.validate_transition(from_status, to_status, raise_on_invalid=True)


__all__ = [
    "StatusTransitionError",
    "TransitionValidationResult",
    "StatusTransitionValidator",
    "validate_transition",
    "assert_valid_transition",
]
