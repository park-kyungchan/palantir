"""
OntologyEntity - Base class for all ontology schema entities.

This module provides the foundational base class for ObjectType, LinkType,
ActionType, and other schema definitions in the Palantir Foundry-aligned
ontology system.

Key Features:
    - RID (Resource ID) for global unique identification
    - apiName for programmatic access (immutable after ACTIVE)
    - Audit fields (created/modified timestamps and actors)
    - Version tracking for optimistic locking
    - Lifecycle status management

Usage:
    class MyObjectType(OntologyEntity):
        # Additional fields specific to ObjectType
        pass
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ontology_definition.core.identifiers import generate_rid, generate_uuid


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


class OntologyEntity(BaseModel):
    """
    Base class for all Ontology schema entities.

    This is the foundation for:
    - ObjectType: Entity schema definitions
    - LinkType: Relationship schema definitions
    - ActionType: Action/mutation schema definitions
    - Interface: Shared property contract definitions
    - ValueType: Reusable value constraint definitions
    - StructType: Nested structure definitions

    Attributes:
        rid: Resource ID - globally unique identifier (auto-generated)
        api_name: Programmatic identifier (immutable once ACTIVE)
        display_name: Human-friendly name for UI display
        description: Documentation string
        created_at: Creation timestamp (UTC)
        created_by: Actor who created this entity
        modified_at: Last modification timestamp (UTC)
        modified_by: Actor who last modified this entity
        version: Optimistic locking version number

    Example:
        >>> class Employee(OntologyEntity):
        ...     department_id: str
        ...     email: str
    """

    # Primary Identifiers
    rid: str = Field(
        default_factory=lambda: generate_rid("ontology", "entity"),
        description="Resource ID - globally unique identifier",
        json_schema_extra={"readOnly": True, "immutable": True},
    )

    api_name: str = Field(
        ...,
        description="Programmatic identifier. Must be unique within scope. "
                    "Cannot be changed once status is ACTIVE.",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        json_schema_extra={"x-palantir-immutable-after": "ACTIVE"},
    )

    display_name: str = Field(
        ...,
        description="Human-friendly name for UI display.",
        min_length=1,
        max_length=255,
    )

    description: Optional[str] = Field(
        default=None,
        description="Documentation describing the entity's purpose and usage.",
        max_length=4096,
    )

    # Audit Fields
    created_at: datetime = Field(
        default_factory=utc_now,
        description="Creation timestamp (UTC).",
        json_schema_extra={"readOnly": True},
    )

    created_by: Optional[str] = Field(
        default=None,
        description="ID of the user/system that created this entity.",
        json_schema_extra={"readOnly": True},
    )

    modified_at: datetime = Field(
        default_factory=utc_now,
        description="Last modification timestamp (UTC).",
        json_schema_extra={"readOnly": True},
    )

    modified_by: Optional[str] = Field(
        default=None,
        description="ID of the user/system that last modified this entity.",
        json_schema_extra={"readOnly": True},
    )

    # Version Control
    version: int = Field(
        default=1,
        description="Version number for optimistic locking. Increments on each update.",
        ge=1,
        json_schema_extra={"readOnly": True},
    )

    # Class Variables
    _entity_type: ClassVar[str] = "OntologyEntity"

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "x-palantir-entity-type": "schema-definition",
            "x-palantir-indexing": ["api_name", "rid", "created_at"],
        },
    )

    @field_validator("api_name")
    @classmethod
    def validate_api_name(cls, v: str) -> str:
        """
        Validate apiName follows Palantir naming conventions.

        Rules:
        - Must start with a letter
        - Only alphanumeric and underscore allowed
        - PascalCase recommended for types, camelCase for properties
        """
        if not v:
            raise ValueError("api_name cannot be empty")
        if not v[0].isalpha():
            raise ValueError("api_name must start with a letter")
        return v

    def touch(self, modified_by: Optional[str] = None) -> None:
        """
        Update modification timestamp and version.
        Call this before any update operation.

        Args:
            modified_by: ID of the actor performing the update
        """
        object.__setattr__(self, "modified_at", utc_now())
        object.__setattr__(self, "version", self.version + 1)
        if modified_by:
            object.__setattr__(self, "modified_by", modified_by)

    def to_foundry_dict(self) -> dict[str, Any]:
        """
        Export to Palantir Foundry-compatible dictionary format.

        Returns:
            Dictionary matching Foundry ontology JSON structure
        """
        return {
            "rid": self.rid,
            "apiName": self.api_name,
            "displayName": self.display_name,
            "description": self.description,
            "metadata": {
                "createdAt": self.created_at.isoformat(),
                "createdBy": self.created_by,
                "modifiedAt": self.modified_at.isoformat(),
                "modifiedBy": self.modified_by,
                "version": self.version,
            },
        }

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "OntologyEntity":
        """
        Create instance from Palantir Foundry JSON format.

        Args:
            data: Dictionary from Foundry ontology export

        Returns:
            New OntologyEntity instance
        """
        metadata = data.get("metadata", {})
        return cls(
            rid=data.get("rid", generate_rid("ontology", "entity")),
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            created_at=datetime.fromisoformat(metadata.get("createdAt", utc_now().isoformat())),
            created_by=metadata.get("createdBy"),
            modified_at=datetime.fromisoformat(metadata.get("modifiedAt", utc_now().isoformat())),
            modified_by=metadata.get("modifiedBy"),
            version=metadata.get("version", 1),
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(api_name='{self.api_name}', rid='{self.rid}')"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.api_name})"
