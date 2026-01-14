"""
Orion ODA v4.0 - Resource Lifecycle Status Types
=================================================

This module defines the extended lifecycle statuses for ODA resources,
following the Palantir pattern for resource lifecycle management.

Lifecycle Flow:
    DRAFT -> EXPERIMENTAL -> ALPHA -> BETA -> ACTIVE -> STABLE -> DEPRECATED -> SUNSET -> ARCHIVED -> DELETED

Design Principles:
1. Resources progress through defined lifecycle stages
2. Status transitions are validated and audited
3. Each status has specific implications for usage and visibility

Schema Version: 4.0.0
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Set


class ResourceLifecycleStatus(str, Enum):
    """
    Extended lifecycle statuses for ODA resources.
    Palantir-style resource lifecycle management.

    Development Stages:
        - DRAFT: Initial creation, not ready for use
        - EXPERIMENTAL: Early exploration, highly unstable
        - ALPHA: First testable version, expect breaking changes
        - BETA: Feature complete, testing phase

    Production Stages:
        - ACTIVE: General availability, actively maintained
        - STABLE: Mature, minimal changes expected

    Deprecation Stages:
        - DEPRECATED: No longer recommended, still functional
        - SUNSET: Scheduled for removal, limited support

    End of Life:
        - ARCHIVED: Read-only, preserved for reference
        - DELETED: Marked for removal (soft delete)
    """
    # Development
    DRAFT = "draft"
    EXPERIMENTAL = "experimental"
    ALPHA = "alpha"
    BETA = "beta"

    # Production
    ACTIVE = "active"
    STABLE = "stable"

    # Deprecation
    DEPRECATED = "deprecated"
    SUNSET = "sunset"

    # End of Life
    ARCHIVED = "archived"
    DELETED = "deleted"

    @classmethod
    def development_statuses(cls) -> Set["ResourceLifecycleStatus"]:
        """Return all development stage statuses."""
        return {cls.DRAFT, cls.EXPERIMENTAL, cls.ALPHA, cls.BETA}

    @classmethod
    def production_statuses(cls) -> Set["ResourceLifecycleStatus"]:
        """Return all production stage statuses."""
        return {cls.ACTIVE, cls.STABLE}

    @classmethod
    def deprecation_statuses(cls) -> Set["ResourceLifecycleStatus"]:
        """Return all deprecation stage statuses."""
        return {cls.DEPRECATED, cls.SUNSET}

    @classmethod
    def end_of_life_statuses(cls) -> Set["ResourceLifecycleStatus"]:
        """Return all end-of-life statuses."""
        return {cls.ARCHIVED, cls.DELETED}

    def is_usable(self) -> bool:
        """Check if resource in this status can be actively used."""
        return self in (
            ResourceLifecycleStatus.ACTIVE,
            ResourceLifecycleStatus.STABLE,
            ResourceLifecycleStatus.BETA,  # Usable for testing
        )

    def is_modifiable(self) -> bool:
        """Check if resource in this status can be modified."""
        return self not in (
            ResourceLifecycleStatus.ARCHIVED,
            ResourceLifecycleStatus.DELETED,
        )

    def is_visible(self) -> bool:
        """Check if resource in this status should be visible in listings."""
        return self != ResourceLifecycleStatus.DELETED

    def get_stage(self) -> str:
        """Return the lifecycle stage name."""
        if self in self.development_statuses():
            return "development"
        elif self in self.production_statuses():
            return "production"
        elif self in self.deprecation_statuses():
            return "deprecation"
        else:
            return "end_of_life"


class StatusCategory(str, Enum):
    """Categories for grouping lifecycle statuses."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    DEPRECATION = "deprecation"
    END_OF_LIFE = "end_of_life"


# Valid transition rules mapping
# Key: From status, Value: Set of allowed target statuses
VALID_TRANSITIONS: Dict[ResourceLifecycleStatus, Set[ResourceLifecycleStatus]] = {
    ResourceLifecycleStatus.DRAFT: {
        ResourceLifecycleStatus.EXPERIMENTAL,
        ResourceLifecycleStatus.ACTIVE,  # Fast-track for simple resources
        ResourceLifecycleStatus.DELETED,  # Abandon draft
    },
    ResourceLifecycleStatus.EXPERIMENTAL: {
        ResourceLifecycleStatus.ALPHA,
        ResourceLifecycleStatus.DEPRECATED,  # Abandon experiment
    },
    ResourceLifecycleStatus.ALPHA: {
        ResourceLifecycleStatus.BETA,
        ResourceLifecycleStatus.DEPRECATED,  # Abandon alpha
    },
    ResourceLifecycleStatus.BETA: {
        ResourceLifecycleStatus.ACTIVE,
        ResourceLifecycleStatus.DEPRECATED,  # Abandon beta
    },
    ResourceLifecycleStatus.ACTIVE: {
        ResourceLifecycleStatus.STABLE,
        ResourceLifecycleStatus.DEPRECATED,
    },
    ResourceLifecycleStatus.STABLE: {
        ResourceLifecycleStatus.DEPRECATED,
    },
    ResourceLifecycleStatus.DEPRECATED: {
        ResourceLifecycleStatus.SUNSET,
        ResourceLifecycleStatus.ARCHIVED,  # Skip sunset if no dependencies
    },
    ResourceLifecycleStatus.SUNSET: {
        ResourceLifecycleStatus.ARCHIVED,
    },
    ResourceLifecycleStatus.ARCHIVED: {
        ResourceLifecycleStatus.DELETED,
    },
    ResourceLifecycleStatus.DELETED: set(),  # Terminal state
}


def get_allowed_transitions(status: ResourceLifecycleStatus) -> List[ResourceLifecycleStatus]:
    """
    Get the list of valid target statuses for a given status.

    Args:
        status: Current resource lifecycle status

    Returns:
        List of allowed target statuses
    """
    return list(VALID_TRANSITIONS.get(status, set()))


def is_valid_transition(from_status: ResourceLifecycleStatus, to_status: ResourceLifecycleStatus) -> bool:
    """
    Check if a status transition is valid.

    Args:
        from_status: Current status
        to_status: Target status

    Returns:
        True if transition is allowed
    """
    allowed = VALID_TRANSITIONS.get(from_status, set())
    return to_status in allowed


__all__ = [
    "ResourceLifecycleStatus",
    "StatusCategory",
    "VALID_TRANSITIONS",
    "get_allowed_transitions",
    "is_valid_transition",
]
