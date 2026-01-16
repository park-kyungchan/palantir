"""
Orion ODA V3 - Storage Layer Exceptions
========================================
Centralized exception definitions for data access layer.
"""

from __future__ import annotations


class ConcurrencyError(Exception):
    """
    Raised on optimistic locking failure.
    Aligned with Palantir's version-based concurrency control pattern.

    Attributes:
        expected_version: The version that was expected in the database
        actual_version: The version that was actually found
    """
    def __init__(
        self,
        message: str,
        expected_version: int = None,
        actual_version: int = None
    ):
        super().__init__(message)
        self.expected_version = expected_version
        self.actual_version = actual_version


# Alias for compatibility with different naming conventions
OptimisticLockError = ConcurrencyError


class ProposalNotFoundError(Exception):
    """Raised when a proposal is not found."""
    pass


class EntityNotFoundError(Exception):
    """Generic exception for entity not found scenarios."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID '{entity_id}' not found")


class ValidationError(Exception):
    """Raised when domain validation fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation failed for '{field}': {message}")
