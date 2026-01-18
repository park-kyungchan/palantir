"""
SharedProperty Definition for Ontology.

A SharedProperty is a reusable property definition that can be shared across
multiple ObjectTypes for consistency. SharedProperties provide:
    - Consistent property schemas across ObjectTypes
    - Semantic typing for cross-ObjectType queries
    - Centralized constraint management
    - Mandatory control support for security properties

SharedProperties enable schema reuse patterns like:
    - createdAt, modifiedAt timestamps across all entities
    - createdBy, modifiedBy user references
    - securityMarkings for row-level security
    - status fields with consistent enum values

Example:
    created_at = SharedProperty(
        api_name="createdAt",
        display_name="Created At",
        description="Timestamp when this object was created",
        data_type=DataTypeSpec(type=DataType.TIMESTAMP),
        constraints=PropertyConstraints(required=True, immutable=True),
        semantic_type=SemanticType.CREATED_AT,
    )
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from ontology_definition.constraints.mandatory_control import MandatoryControlConfig
from ontology_definition.constraints.property_constraints import PropertyConstraints
from ontology_definition.core.base import OntologyEntity
from ontology_definition.core.enums import DataType
from ontology_definition.core.identifiers import generate_rid
from ontology_definition.types.property_def import DataTypeSpec


class SemanticType(str, Enum):
    """
    Semantic meaning of a property for cross-ObjectType consistency.

    SemanticType enables queries across ObjectTypes based on meaning,
    not just property name. For example, querying all "CREATED_AT"
    properties regardless of their actual apiName.
    """

    # Identity
    IDENTIFIER = "IDENTIFIER"
    NAME = "NAME"
    DESCRIPTION = "DESCRIPTION"

    # Temporal (Audit)
    TIMESTAMP = "TIMESTAMP"
    CREATED_AT = "CREATED_AT"
    MODIFIED_AT = "MODIFIED_AT"
    CREATED_BY = "CREATED_BY"
    MODIFIED_BY = "MODIFIED_BY"

    # Classification
    STATUS = "STATUS"
    CATEGORY = "CATEGORY"
    TAG = "TAG"

    # Contact
    URL = "URL"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    ADDRESS = "ADDRESS"

    # Numeric
    CURRENCY = "CURRENCY"
    PERCENTAGE = "PERCENTAGE"

    # Security
    SECURITY_MARKING = "SECURITY_MARKING"

    # Custom/Other
    CUSTOM = "CUSTOM"


class SharedPropertyStatus(str, Enum):
    """Lifecycle status for SharedProperties."""

    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    ALPHA = "ALPHA"
    BETA = "BETA"
    ACTIVE = "ACTIVE"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"
    SUNSET = "SUNSET"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class SharedProperty(OntologyEntity):
    """
    SharedProperty schema definition - reusable property across ObjectTypes.

    A SharedProperty defines a property schema that can be referenced by
    multiple ObjectTypes, ensuring consistent naming, types, and constraints.

    Key Features:
    - Reusable schema across ObjectTypes via sharedPropertyRef
    - Semantic typing for cross-ObjectType queries
    - Full constraint specification
    - Mandatory control support for security properties (GAP-002)

    Common SharedProperties:
    - createdAt: Creation timestamp (CREATED_AT)
    - modifiedAt: Modification timestamp (MODIFIED_AT)
    - createdBy: Creator user ID (CREATED_BY)
    - securityMarkings: Security markings (SECURITY_MARKING)
    - status: Lifecycle status (STATUS)

    Example:
        >>> created_at = SharedProperty(
        ...     api_name="createdAt",
        ...     display_name="Created At",
        ...     description="When this object was created",
        ...     data_type=DataTypeSpec(type=DataType.TIMESTAMP),
        ...     constraints=PropertyConstraints(required=True, immutable=True),
        ...     semantic_type=SemanticType.CREATED_AT,
        ...     status=SharedPropertyStatus.ACTIVE,
        ... )

        >>> security_markings = SharedProperty(
        ...     api_name="securityMarkings",
        ...     display_name="Security Markings",
        ...     data_type=DataTypeSpec(
        ...         type=DataType.ARRAY,
        ...         array_item_type=DataTypeSpec(type=DataType.STRING)
        ...     ),
        ...     is_mandatory_control=True,
        ...     mandatory_control_config=MandatoryControlConfig(
        ...         control_type=ControlType.MARKINGS,
        ...         enforcement_level=EnforcementLevel.STRICT,
        ...     ),
        ...     semantic_type=SemanticType.SECURITY_MARKING,
        ... )
    """

    # Override RID to use shared-property specific format
    rid: str = Field(
        default_factory=lambda: generate_rid("ontology", "shared-property"),
        description="Resource ID - globally unique identifier for this SharedProperty.",
        pattern=r"^ri\.ontology\.[a-z]+\.shared-property\.[a-zA-Z0-9-]+$",
        json_schema_extra={"readOnly": True, "immutable": True},
    )

    # Data Type (REQUIRED)
    data_type: DataTypeSpec = Field(
        ...,
        description="Data type specification for this property.",
        alias="dataType",
    )

    # Constraints (optional)
    constraints: PropertyConstraints | None = Field(
        default=None,
        description="Validation constraints for this property.",
    )

    # Mandatory Control (GAP-002)
    is_mandatory_control: bool = Field(
        default=False,
        description="If true, this is a security marking property for row-level access control.",
        alias="isMandatoryControl",
    )

    mandatory_control_config: MandatoryControlConfig | None = Field(
        default=None,
        description="Configuration when isMandatoryControl is true.",
        alias="mandatoryControlConfig",
    )

    # Semantic Type
    semantic_type: SemanticType | None = Field(
        default=None,
        description="Semantic meaning of this property for cross-ObjectType queries.",
        alias="semanticType",
    )

    # Lifecycle Status
    status: SharedPropertyStatus = Field(
        default=SharedPropertyStatus.EXPERIMENTAL,
        description="Lifecycle status of the SharedProperty.",
    )

    # Usage tracking (auto-populated by registry)
    used_by_object_types: list[str] = Field(
        default_factory=list,
        description="ObjectType apiNames using this SharedProperty (auto-populated).",
        alias="usedByObjectTypes",
        json_schema_extra={"readOnly": True},
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "x-palantir-entity-type": "shared-property",
            "x-palantir-indexing": ["api_name", "rid", "status", "semantic_type"],
        },
    )

    @model_validator(mode="after")
    def validate_mandatory_control_config(self) -> SharedProperty:
        """Validate mandatory control configuration."""
        if self.is_mandatory_control:
            # Must have mandatory control config
            if self.mandatory_control_config is None:
                raise ValueError(
                    "Mandatory control property must have mandatory_control_config"
                )

            # Must be required
            if not self.constraints or not self.constraints.required:
                raise ValueError(
                    "Mandatory control property must have required=True constraint"
                )

            # Cannot have default value
            if self.constraints and self.constraints.default_value is not None:
                raise ValueError(
                    "Mandatory control property cannot have a default value"
                )

            # Must be STRING or ARRAY[STRING]
            valid_type = (
                self.data_type.type == DataType.STRING
                or (
                    self.data_type.type == DataType.ARRAY
                    and self.data_type.array_item_type
                    and self.data_type.array_item_type.type == DataType.STRING
                )
            )
            if not valid_type:
                raise ValueError(
                    "Mandatory control property must be STRING or ARRAY[STRING] type"
                )

        return self

    @model_validator(mode="after")
    def validate_semantic_type_matches(self) -> SharedProperty:
        """Validate semantic type is appropriate for data type."""
        if self.semantic_type is None:
            return self

        # Temporal semantic types should have temporal data types
        temporal_semantics = {
            SemanticType.TIMESTAMP,
            SemanticType.CREATED_AT,
            SemanticType.MODIFIED_AT,
        }
        temporal_types = {DataType.TIMESTAMP, DataType.DATETIME, DataType.DATE}

        if self.semantic_type in temporal_semantics:
            if self.data_type.type not in temporal_types:
                raise ValueError(
                    f"Semantic type {self.semantic_type.value} requires a temporal "
                    f"data type (TIMESTAMP, DATETIME, DATE), not {self.data_type.type.value}"
                )

        # Security marking must be mandatory control
        if self.semantic_type == SemanticType.SECURITY_MARKING:
            if not self.is_mandatory_control:
                raise ValueError(
                    "SECURITY_MARKING semantic type requires is_mandatory_control=True"
                )

        return self

    def is_audit_property(self) -> bool:
        """Check if this is an audit-related property."""
        audit_semantics = {
            SemanticType.CREATED_AT,
            SemanticType.MODIFIED_AT,
            SemanticType.CREATED_BY,
            SemanticType.MODIFIED_BY,
        }
        return self.semantic_type in audit_semantics

    def is_security_property(self) -> bool:
        """Check if this is a security-related property."""
        return self.is_mandatory_control or self.semantic_type == SemanticType.SECURITY_MARKING

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result = super().to_foundry_dict()

        result["$type"] = "SharedProperty"
        result["dataType"] = self.data_type.to_foundry_dict()
        result["status"] = self.status.value

        if self.constraints:
            result["constraints"] = self.constraints.to_foundry_dict()

        if self.is_mandatory_control:
            result["isMandatoryControl"] = True
            if self.mandatory_control_config:
                result["mandatoryControlConfig"] = self.mandatory_control_config.to_foundry_dict()

        if self.semantic_type:
            result["semanticType"] = self.semantic_type.value

        if self.used_by_object_types:
            result["usedByObjectTypes"] = self.used_by_object_types

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> SharedProperty:
        """Create SharedProperty from Palantir Foundry JSON format."""
        constraints = None
        if data.get("constraints"):
            constraints = PropertyConstraints.from_foundry_dict(data["constraints"])

        mandatory_control_config = None
        if data.get("mandatoryControlConfig"):
            mandatory_control_config = MandatoryControlConfig.from_foundry_dict(
                data["mandatoryControlConfig"]
            )

        semantic_type = None
        if data.get("semanticType"):
            semantic_type = SemanticType(data["semanticType"])

        return cls(
            rid=data.get("rid", generate_rid("ontology", "shared-property")),
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            data_type=DataTypeSpec.from_foundry_dict(data["dataType"]),
            constraints=constraints,
            is_mandatory_control=data.get("isMandatoryControl", False),
            mandatory_control_config=mandatory_control_config,
            semantic_type=semantic_type,
            status=SharedPropertyStatus(data.get("status", "EXPERIMENTAL")),
            used_by_object_types=data.get("usedByObjectTypes", []),
        )


# Predefined common SharedProperties for convenience
class CommonSharedProperties:
    """
    Factory for commonly used SharedProperties.

    Usage:
        created_at = CommonSharedProperties.created_at()
        security_markings = CommonSharedProperties.security_markings()
    """

    @staticmethod
    def created_at() -> SharedProperty:
        """Create a createdAt SharedProperty."""
        return SharedProperty(
            api_name="createdAt",
            display_name="Created At",
            description="Timestamp when this object was created.",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP),
            constraints=PropertyConstraints(required=True, immutable=True),
            semantic_type=SemanticType.CREATED_AT,
            status=SharedPropertyStatus.ACTIVE,
        )

    @staticmethod
    def modified_at() -> SharedProperty:
        """Create a modifiedAt SharedProperty."""
        return SharedProperty(
            api_name="modifiedAt",
            display_name="Modified At",
            description="Timestamp when this object was last modified.",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP),
            constraints=PropertyConstraints(required=True),
            semantic_type=SemanticType.MODIFIED_AT,
            status=SharedPropertyStatus.ACTIVE,
        )

    @staticmethod
    def created_by() -> SharedProperty:
        """Create a createdBy SharedProperty."""
        return SharedProperty(
            api_name="createdBy",
            display_name="Created By",
            description="User ID who created this object.",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(required=True, immutable=True),
            semantic_type=SemanticType.CREATED_BY,
            status=SharedPropertyStatus.ACTIVE,
        )

    @staticmethod
    def modified_by() -> SharedProperty:
        """Create a modifiedBy SharedProperty."""
        return SharedProperty(
            api_name="modifiedBy",
            display_name="Modified By",
            description="User ID who last modified this object.",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(required=True),
            semantic_type=SemanticType.MODIFIED_BY,
            status=SharedPropertyStatus.ACTIVE,
        )

    @staticmethod
    def security_markings() -> SharedProperty:
        """Create a securityMarkings SharedProperty (mandatory control)."""
        from ontology_definition.constraints.mandatory_control import (
            EnforcementLevel,
            MandatoryControlConfig,
        )
        from ontology_definition.core.enums import ControlType

        return SharedProperty(
            api_name="securityMarkings",
            display_name="Security Markings",
            description="Mandatory control property for row-level security based on user markings.",
            data_type=DataTypeSpec(
                type=DataType.ARRAY,
                array_item_type=DataTypeSpec(type=DataType.STRING),
            ),
            constraints=PropertyConstraints(
                required=True,
                array={"unique_items": True},
            ),
            is_mandatory_control=True,
            mandatory_control_config=MandatoryControlConfig(
                control_type=ControlType.MARKINGS,
                enforcement_level=EnforcementLevel.STRICT,
            ),
            semantic_type=SemanticType.SECURITY_MARKING,
            status=SharedPropertyStatus.ACTIVE,
        )

    @staticmethod
    def status_field(
        allowed_values: list[str] | None = None
    ) -> SharedProperty:
        """Create a status SharedProperty with customizable values."""
        if allowed_values is None:
            allowed_values = ["DRAFT", "ACTIVE", "INACTIVE", "ARCHIVED"]

        return SharedProperty(
            api_name="status",
            display_name="Status",
            description="Lifecycle status of the object.",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(
                required=True,
                enum_values=allowed_values,
            ),
            semantic_type=SemanticType.STATUS,
            status=SharedPropertyStatus.ACTIVE,
        )

    @staticmethod
    def name_field() -> SharedProperty:
        """Create a name SharedProperty."""
        return SharedProperty(
            api_name="name",
            display_name="Name",
            description="Display name of the object.",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(
                required=True,
                string={"min_length": 1, "max_length": 255},
            ),
            semantic_type=SemanticType.NAME,
            status=SharedPropertyStatus.ACTIVE,
        )

    @staticmethod
    def description_field() -> SharedProperty:
        """Create a description SharedProperty."""
        return SharedProperty(
            api_name="description",
            display_name="Description",
            description="Detailed description of the object.",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(
                string={"max_length": 4096},
            ),
            semantic_type=SemanticType.DESCRIPTION,
            status=SharedPropertyStatus.ACTIVE,
        )
