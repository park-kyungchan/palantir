"""
Orion ODA V4.0 - LinkType Metadata and Constraints
===================================================
Foundry-aligned LinkType definitions with full metadata support.

This module provides:
- LinkTypeMetadata: Complete link type definition (source, target, cardinality, policies)
- LinkTypeConstraints: Validation constraints for links
- CascadePolicy: Cascade delete/update policies (source and target side)
- LinkDirection: Directed vs bidirectional links
- LinkConstraint: Validation rules for link creation/modification
- ReferentialIntegrityChecker: Validates link consistency
- IntegrityViolation: Represents a referential integrity violation

Palantir Pattern Reference:
- M:N links require explicit backing table (join table)
- Each LinkType has a unique link_type_id
- Bidirectional links have reverse_link_id for navigation
- Cascade policies defined separately for source and target side

Schema Version: 4.0.0
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================


class CascadePolicy(str, Enum):
    """
    Cascade behavior for link operations when source/target is deleted or updated.

    Aligned with Palantir Foundry Link cascade policies.

    - RESTRICT: Prevent operation if linked objects exist
    - CASCADE: Propagate delete/update to linked objects
    - SET_NULL: Set foreign key to null (requires nullable FK)
    - SET_DEFAULT: Set to default value
    - NO_ACTION: Do nothing (may cause orphaned references)
    - NONE: Alias for NO_ACTION (backward compatibility)
    - DELETE: Alias for CASCADE (backward compatibility)
    - NULLIFY: Alias for SET_NULL (backward compatibility)
    """
    RESTRICT = "restrict"
    CASCADE = "cascade"
    SET_NULL = "set_null"
    SET_DEFAULT = "set_default"
    NO_ACTION = "no_action"
    # Backward compatibility aliases
    NONE = "no_action"
    DELETE = "cascade"
    NULLIFY = "set_null"


class LinkDirection(str, Enum):
    """
    Link directionality for navigation.

    - DIRECTED: Source -> Target (one-way navigation)
    - BIDIRECTIONAL: Source <-> Target (two-way navigation with reverse_link_id)
    """
    DIRECTED = "directed"
    BIDIRECTIONAL = "bidirectional"


class IntegrityViolationType(str, Enum):
    """Types of referential integrity violations."""
    ORPHANED_SOURCE = "orphaned_source"
    ORPHANED_TARGET = "orphaned_target"
    MISSING_BACKING_TABLE = "missing_backing_table"
    CARDINALITY_VIOLATION = "cardinality_violation"
    DUPLICATE_LINK = "duplicate_link"
    INVALID_OBJECT_TYPE = "invalid_object_type"
    STATUS_CONSTRAINT_VIOLATION = "status_constraint_violation"
    IMMUTABILITY_VIOLATION = "immutability_violation"
    CUSTOM_VALIDATION_FAILED = "custom_validation_failed"


# =============================================================================
# INTEGRITY VIOLATION (Dataclass for results)
# =============================================================================


@dataclass(frozen=True)
class IntegrityViolation:
    """
    Represents a referential integrity violation.

    Attributes:
        violation_type: Type of violation detected
        link_type_id: The link type where violation occurred
        source_id: Source object ID (if applicable)
        target_id: Target object ID (if applicable)
        message: Human-readable description
        severity: "error" or "warning"
    """
    violation_type: IntegrityViolationType
    link_type_id: str
    source_id: Optional[str]
    target_id: Optional[str]
    message: str
    severity: str = "error"


# =============================================================================
# LINK CONSTRAINTS
# =============================================================================


class LinkConstraint(BaseModel):
    """
    Validation constraints for LinkTypes (Phase 1.2.2).

    Attributes:
        min_links: Minimum number of linked objects (0 = optional)
        max_links: Maximum number of linked objects (None = unlimited)
        unique: If True, each target can only be linked once from any source
        immutable_after_creation: If True, link cannot be modified after creation
        required_target_status: Target must have this status to be linkable
        forbidden_target_status: Target with these statuses cannot be linked
        custom_validator: Optional custom validation function name
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    # Cardinality constraints
    min_links: int = Field(default=0, ge=0, description="Minimum required linked objects")
    max_links: Optional[int] = Field(default=None, ge=1, description="Maximum allowed linked objects")

    # Uniqueness
    unique: bool = Field(default=False, description="Each target can only be linked once")

    # Mutability
    immutable_after_creation: bool = Field(
        default=False,
        description="Link cannot be modified after creation"
    )

    # Status-based constraints
    required_target_status: Optional[str] = Field(
        default=None,
        description="Target must have this status to be linked"
    )
    forbidden_target_status: Optional[Set[str]] = Field(
        default=None,
        description="Target with these statuses cannot be linked"
    )

    # Custom validation
    custom_validator: Optional[str] = Field(
        default=None,
        description="Name of custom validator function in validators registry"
    )

    @field_validator("max_links")
    @classmethod
    def max_links_gte_min(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure max_links >= min_links if both are set."""
        min_links = info.data.get("min_links", 0)
        if v is not None and v < min_links:
            raise ValueError(f"max_links ({v}) must be >= min_links ({min_links})")
        return v


class LinkTypeConstraints(BaseModel):
    """
    Validation constraints for LinkType (backward compatible, wraps LinkConstraint).

    Attributes:
        min_cardinality: Minimum required links (default 0)
        max_cardinality: Maximum allowed links (None = unlimited)
        unique_target: Prevent duplicate targets
        required: At least one link required
        allowed_source_statuses: Source object statuses that allow linking
        allowed_target_statuses: Target object statuses that allow linking
    """
    min_cardinality: int = Field(default=0, ge=0)
    max_cardinality: Optional[int] = Field(default=None, ge=1)
    unique_target: bool = Field(default=True, description="Prevent duplicate target links")
    required: bool = Field(default=False, description="At least one link required")
    allowed_source_statuses: List[str] = Field(
        default_factory=lambda: ["active"],
        description="Source statuses that allow linking"
    )
    allowed_target_statuses: List[str] = Field(
        default_factory=lambda: ["active"],
        description="Target statuses that allow linking"
    )

    @model_validator(mode="after")
    def validate_cardinality_range(self) -> "LinkTypeConstraints":
        """Ensure min <= max if max is specified."""
        if self.max_cardinality is not None:
            if self.min_cardinality > self.max_cardinality:
                raise ValueError(
                    f"min_cardinality ({self.min_cardinality}) cannot exceed "
                    f"max_cardinality ({self.max_cardinality})"
                )
        return self

    def to_link_constraint(self) -> LinkConstraint:
        """Convert to the new LinkConstraint model."""
        return LinkConstraint(
            min_links=self.min_cardinality,
            max_links=self.max_cardinality,
            unique=self.unique_target,
            required_target_status=self.allowed_target_statuses[0] if self.allowed_target_statuses else None,
        )


class LinkTypeMetadata(BaseModel):
    """
    Complete LinkType definition with full metadata.

    Palantir Pattern:
    - LinkTypes are first-class citizens in the Ontology
    - Each link has a unique link_type_id for identification
    - M:N cardinality requires backing_table_name
    - Bidirectional links define reverse_link_id

    Example:
        ```python
        task_depends_on = LinkTypeMetadata(
            link_type_id="task_depends_on_task",
            source_type="Task",
            target_type="Task",
            cardinality="N:N",
            backing_table_name="task_dependencies",
            direction=LinkDirection.BIDIRECTIONAL,
            reverse_link_id="task_depended_by",
            description="Task dependency relationship"
        )
        ```
    """

    # Identity
    link_type_id: str = Field(
        ...,
        description="Unique identifier for this link type (snake_case)",
        min_length=3,
        max_length=100
    )

    # ObjectType References
    source_type: str = Field(
        ...,
        description="Source ObjectType name"
    )
    target_type: str = Field(
        ...,
        description="Target ObjectType name"
    )

    # Relationship Properties
    cardinality: str = Field(
        default="1:N",
        description="Cardinality: 1:1, 1:N, N:1, N:N"
    )
    direction: LinkDirection = Field(
        default=LinkDirection.DIRECTED,
        description="Link directionality"
    )

    # Bidirectional Navigation
    reverse_link_id: Optional[str] = Field(
        default=None,
        description="Reverse link ID for bidirectional navigation"
    )

    # Storage Configuration
    backing_table_name: Optional[str] = Field(
        default=None,
        description="Backing table for M:N links (required for N:N)"
    )
    is_materialized: bool = Field(
        default=True,
        description="Whether link is materialized in storage"
    )

    # Cascade Policies (Phase 1.2.3)
    on_source_delete: CascadePolicy = Field(
        default=CascadePolicy.CASCADE,
        description="Action when source object is deleted"
    )
    on_target_delete: CascadePolicy = Field(
        default=CascadePolicy.SET_NULL,
        description="Action when target object is deleted"
    )
    on_source_update: CascadePolicy = Field(
        default=CascadePolicy.CASCADE,
        description="Action when source PK is updated"
    )
    on_target_update: CascadePolicy = Field(
        default=CascadePolicy.CASCADE,
        description="Action when target PK is updated"
    )

    # Backward compatibility aliases
    @property
    def on_delete(self) -> CascadePolicy:
        """Backward compatible alias for on_source_delete."""
        return self.on_source_delete

    @property
    def on_update(self) -> CascadePolicy:
        """Backward compatible alias for on_source_update."""
        return self.on_source_update

    # Constraints
    constraints: LinkTypeConstraints = Field(
        default_factory=LinkTypeConstraints,
        description="Validation constraints"
    )

    # Metadata
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Classification tags"
    )

    # Audit
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    created_by: Optional[str] = Field(default=None)

    # Schema version for migrations
    schema_version: str = Field(default="1.0.0")

    @field_validator("link_type_id")
    @classmethod
    def validate_link_type_id(cls, v: str) -> str:
        """Enforce snake_case naming convention."""
        if not v:
            raise ValueError("link_type_id cannot be empty")
        if not v.replace("_", "").isalnum():
            raise ValueError(f"link_type_id must be snake_case alphanumeric: {v}")
        if v[0].isdigit():
            raise ValueError(f"link_type_id cannot start with a digit: {v}")
        return v

    @field_validator("cardinality")
    @classmethod
    def validate_cardinality(cls, v: str) -> str:
        """Validate cardinality format."""
        valid = {"1:1", "1:N", "N:1", "N:N"}
        if v not in valid:
            raise ValueError(f"cardinality must be one of {valid}, got: {v}")
        return v

    @model_validator(mode="after")
    def validate_nn_backing(self) -> "LinkTypeMetadata":
        """Palantir Pattern: M:N links require backing table."""
        if self.cardinality == "N:N" and not self.backing_table_name:
            raise ValueError(
                f"LinkType '{self.link_type_id}' has N:N cardinality but no "
                "backing_table_name. Palantir Pattern: N:N links require "
                "explicit backing table (join table)."
            )
        return self

    @model_validator(mode="after")
    def validate_bidirectional_reverse(self) -> "LinkTypeMetadata":
        """Bidirectional links should have reverse_link_id."""
        if self.direction == LinkDirection.BIDIRECTIONAL and not self.reverse_link_id:
            # Auto-generate reverse link ID if not provided
            self.reverse_link_id = f"{self.link_type_id}_reverse"
        return self

    @property
    def is_many_to_many(self) -> bool:
        """Check if this is an N:N link type."""
        return self.cardinality == "N:N"

    @property
    def is_one_to_one(self) -> bool:
        """Check if this is a 1:1 link type."""
        return self.cardinality == "1:1"

    @property
    def is_one_to_many(self) -> bool:
        """Check if this is a 1:N link type."""
        return self.cardinality == "1:N"

    @property
    def is_many_to_one(self) -> bool:
        """Check if this is an N:1 link type."""
        return self.cardinality == "N:1"

    @property
    def requires_join_table(self) -> bool:
        """Check if this link type requires a join table."""
        return self.is_many_to_many

    def to_json(self) -> Dict[str, Any]:
        """Export link type to JSON-serializable dict."""
        return {
            "link_type_id": self.link_type_id,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "cardinality": self.cardinality,
            "direction": self.direction.value,
            "reverse_link_id": self.reverse_link_id,
            "backing_table_name": self.backing_table_name,
            "is_materialized": self.is_materialized,
            "on_delete": self.on_delete.value,
            "on_update": self.on_update.value,
            "constraints": self.constraints.model_dump(),
            "description": self.description,
            "tags": self.tags,
            "schema_version": self.schema_version,
        }

    def __repr__(self) -> str:
        return (
            f"LinkTypeMetadata(id='{self.link_type_id}', "
            f"{self.source_type} --[{self.cardinality}]--> {self.target_type})"
        )


# =============================================================================
# REFERENTIAL INTEGRITY CHECKER (Phase 1.2.4)
# =============================================================================


class ReferentialIntegrityChecker:
    """
    Validates referential integrity for LinkTypes.

    Palantir Pattern: Links must maintain referential integrity:
    - Source object must exist (unless soft-deleted)
    - Target object must exist (unless soft-deleted and SET_NULL policy)
    - Cardinality constraints must be satisfied
    - No duplicate links in unique constraints

    Example:
        ```python
        checker = ReferentialIntegrityChecker()

        # Check cardinality constraint
        violation = checker.validate_cardinality(
            metadata=link_metadata,
            current_link_count=5,
            adding=True
        )

        # Check unique constraint
        violation = checker.validate_unique_constraint(
            metadata=link_metadata,
            target_id="agent-456",
            existing_target_ids={"agent-123", "agent-789"}
        )

        # Check target status
        violation = checker.validate_target_status(
            metadata=link_metadata,
            target_status="archived"
        )
        ```
    """

    def __init__(self) -> None:
        """Initialize the integrity checker."""
        self._custom_validators: Dict[str, Callable] = {}

    def register_validator(self, name: str, validator: Callable) -> None:
        """
        Register a custom validator function.

        Args:
            name: Validator name (referenced in LinkConstraint.custom_validator)
            validator: Callable that takes (source_id, target_id, context) and returns
                       True (valid), False (invalid), or str (error message)
        """
        self._custom_validators[name] = validator

    def validate_cardinality(
        self,
        metadata: LinkTypeMetadata,
        current_link_count: int,
        adding: bool = True,
    ) -> Optional[IntegrityViolation]:
        """
        Validate cardinality constraints.

        Args:
            metadata: LinkType metadata
            current_link_count: Current number of links
            adding: True if adding a link, False if removing

        Returns:
            IntegrityViolation if constraint violated, None otherwise
        """
        new_count = current_link_count + (1 if adding else -1)
        constraints = metadata.constraints

        # Check minimum constraint
        if not adding and new_count < constraints.min_cardinality:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.CARDINALITY_VIOLATION,
                link_type_id=metadata.link_type_id,
                source_id=None,
                target_id=None,
                message=(
                    f"Cannot remove link: minimum {constraints.min_cardinality} "
                    f"links required for {metadata.link_type_id}"
                ),
                severity="error",
            )

        # Check maximum constraint
        max_links = constraints.max_cardinality
        if adding and max_links is not None and new_count > max_links:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.CARDINALITY_VIOLATION,
                link_type_id=metadata.link_type_id,
                source_id=None,
                target_id=None,
                message=(
                    f"Cannot add link: maximum {max_links} "
                    f"links allowed for {metadata.link_type_id}"
                ),
                severity="error",
            )

        # Check required constraint
        if constraints.required and not adding and new_count < 1:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.CARDINALITY_VIOLATION,
                link_type_id=metadata.link_type_id,
                source_id=None,
                target_id=None,
                message=(
                    f"Cannot remove link: at least one link required "
                    f"for {metadata.link_type_id}"
                ),
                severity="error",
            )

        return None

    def validate_unique_constraint(
        self,
        metadata: LinkTypeMetadata,
        target_id: str,
        existing_target_ids: Set[str],
    ) -> Optional[IntegrityViolation]:
        """
        Validate unique constraint (each target linked at most once).

        Args:
            metadata: LinkType metadata
            target_id: Target object ID being linked
            existing_target_ids: Set of already-linked target IDs

        Returns:
            IntegrityViolation if duplicate detected, None otherwise
        """
        if not metadata.constraints.unique_target:
            return None

        if target_id in existing_target_ids:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.DUPLICATE_LINK,
                link_type_id=metadata.link_type_id,
                source_id=None,
                target_id=target_id,
                message=(
                    f"Duplicate link: target {target_id} is already linked "
                    f"via {metadata.link_type_id} (unique constraint)"
                ),
                severity="error",
            )

        return None

    def validate_source_status(
        self,
        metadata: LinkTypeMetadata,
        source_status: str,
    ) -> Optional[IntegrityViolation]:
        """
        Validate source object status constraints.

        Args:
            metadata: LinkType metadata
            source_status: Status of the source object

        Returns:
            IntegrityViolation if status constraint violated, None otherwise
        """
        constraints = metadata.constraints
        allowed = constraints.allowed_source_statuses

        if allowed and source_status not in allowed:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.STATUS_CONSTRAINT_VIOLATION,
                link_type_id=metadata.link_type_id,
                source_id=None,
                target_id=None,
                message=(
                    f"Source status '{source_status}' not in allowed statuses "
                    f"{allowed} for {metadata.link_type_id}"
                ),
                severity="error",
            )

        return None

    def validate_target_status(
        self,
        metadata: LinkTypeMetadata,
        target_status: str,
    ) -> Optional[IntegrityViolation]:
        """
        Validate target object status constraints.

        Args:
            metadata: LinkType metadata
            target_status: Status of the target object

        Returns:
            IntegrityViolation if status constraint violated, None otherwise
        """
        constraints = metadata.constraints
        allowed = constraints.allowed_target_statuses

        if allowed and target_status not in allowed:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.STATUS_CONSTRAINT_VIOLATION,
                link_type_id=metadata.link_type_id,
                source_id=None,
                target_id=None,
                message=(
                    f"Target status '{target_status}' not in allowed statuses "
                    f"{allowed} for {metadata.link_type_id}"
                ),
                severity="error",
            )

        return None

    def validate_all(
        self,
        metadata: LinkTypeMetadata,
        source_id: str,
        target_id: str,
        source_status: str,
        target_status: str,
        current_link_count: int,
        existing_target_ids: Set[str],
        adding: bool = True,
    ) -> List[IntegrityViolation]:
        """
        Run all validation checks.

        Args:
            metadata: LinkType metadata
            source_id: Source object ID
            target_id: Target object ID
            source_status: Source object status
            target_status: Target object status
            current_link_count: Current number of links
            existing_target_ids: Set of already-linked target IDs
            adding: True if adding a link, False if removing

        Returns:
            List of IntegrityViolation objects (empty if all valid)
        """
        violations: List[IntegrityViolation] = []

        # Cardinality check
        v = self.validate_cardinality(metadata, current_link_count, adding)
        if v:
            violations.append(v)

        # Unique constraint check
        if adding:
            v = self.validate_unique_constraint(metadata, target_id, existing_target_ids)
            if v:
                violations.append(v)

        # Source status check
        v = self.validate_source_status(metadata, source_status)
        if v:
            violations.append(v)

        # Target status check
        v = self.validate_target_status(metadata, target_status)
        if v:
            violations.append(v)

        return violations

    async def run_custom_validator(
        self,
        metadata: LinkTypeMetadata,
        source_id: str,
        target_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[IntegrityViolation]:
        """
        Run custom validator if defined in constraints.

        This method supports LinkConstraint's custom_validator field.

        Args:
            metadata: LinkType metadata
            source_id: Source object ID
            target_id: Target object ID
            context: Optional context for validation

        Returns:
            IntegrityViolation if custom validation fails, None otherwise
        """
        # Check if LinkTypeConstraints has been converted to LinkConstraint
        constraint = metadata.constraints
        validator_name = getattr(constraint, "custom_validator", None)

        if not validator_name:
            return None

        validator = self._custom_validators.get(validator_name)
        if not validator:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.CUSTOM_VALIDATION_FAILED,
                link_type_id=metadata.link_type_id,
                source_id=source_id,
                target_id=target_id,
                message=f"Custom validator '{validator_name}' not found",
                severity="warning",
            )

        try:
            # Support both sync and async validators
            if asyncio.iscoroutinefunction(validator):
                result = await validator(source_id, target_id, context or {})
            else:
                result = validator(source_id, target_id, context or {})

            if result is False:
                return IntegrityViolation(
                    violation_type=IntegrityViolationType.CUSTOM_VALIDATION_FAILED,
                    link_type_id=metadata.link_type_id,
                    source_id=source_id,
                    target_id=target_id,
                    message=f"Custom validator '{validator_name}' rejected link",
                    severity="error",
                )

            # Validator can return a string with custom message
            if isinstance(result, str):
                return IntegrityViolation(
                    violation_type=IntegrityViolationType.CUSTOM_VALIDATION_FAILED,
                    link_type_id=metadata.link_type_id,
                    source_id=source_id,
                    target_id=target_id,
                    message=result,
                    severity="error",
                )
        except Exception as e:
            return IntegrityViolation(
                violation_type=IntegrityViolationType.CUSTOM_VALIDATION_FAILED,
                link_type_id=metadata.link_type_id,
                source_id=source_id,
                target_id=target_id,
                message=f"Custom validator '{validator_name}' error: {e}",
                severity="error",
            )

        return None
