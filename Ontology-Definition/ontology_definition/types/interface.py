"""
Interface Definition for Ontology.

An Interface defines a contract that ObjectTypes can implement,
enabling polymorphism in Palantir Foundry Ontology:
    - Required properties that all implementers must have
    - Interface inheritance (extends other interfaces)
    - Interface-level actions
    - Type-safe querying across implementing types

This supports polymorphic operations:
    - Query all objects implementing "Auditable" interface
    - Define actions that work on any "Trackable" implementer
    - Share common property contracts across ObjectTypes

Example:
    auditable = Interface(
        api_name="Auditable",
        display_name="Auditable Entity",
        description="Interface for entities that track audit information",
        required_properties=[
            InterfacePropertyRequirement(
                property_api_name="createdAt",
                data_type=DataTypeSpec(type=DataType.TIMESTAMP),
                description="When the entity was created"
            ),
            InterfacePropertyRequirement(
                property_api_name="createdBy",
                data_type=DataTypeSpec(type=DataType.STRING),
                description="Who created the entity"
            ),
        ],
    )
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology_definition.core.base import OntologyEntity
from ontology_definition.core.enums import ObjectStatus
from ontology_definition.core.identifiers import generate_rid
from ontology_definition.core.metadata import InterfaceMetadata
from ontology_definition.types.property_def import DataTypeSpec


class InterfaceStatus(str, Enum):
    """
    Lifecycle status for Interfaces.

    Similar to ObjectStatus but without ENDORSED
    (interfaces themselves are not endorsed, implementers are).
    """

    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    ACTIVE = "ACTIVE"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class InterfacePropertyRequirement(BaseModel):
    """
    Definition of a property required by an Interface.

    When an ObjectType implements an Interface, it must have properties
    that match all InterfacePropertyRequirements.

    Note: This defines the CONTRACT, not the actual property.
    The implementing ObjectType's PropertyDefinition must be compatible.
    """

    property_api_name: str = Field(
        ...,
        description="apiName that implementing ObjectTypes must use.",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        alias="propertyApiName",
    )

    data_type: DataTypeSpec = Field(
        ...,
        description="Required data type for this property.",
        alias="dataType",
    )

    description: Optional[str] = Field(
        default=None,
        description="Documentation for this property requirement.",
        max_length=4096,
    )

    # Constraint requirements (implementers must match or be stricter)
    required: bool = Field(
        default=False,
        description="If true, implementers must have this as required property.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "propertyApiName": self.property_api_name,
            "dataType": self.data_type.to_foundry_dict(),
        }
        if self.description:
            result["description"] = self.description
        if self.required:
            result["required"] = True
        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "InterfacePropertyRequirement":
        """Create from Foundry JSON format."""
        return cls(
            property_api_name=data["propertyApiName"],
            data_type=DataTypeSpec.from_foundry_dict(data["dataType"]),
            description=data.get("description"),
            required=data.get("required", False),
        )


class InterfaceActionDefinition(BaseModel):
    """
    Action defined at the Interface level.

    Interface-level actions can operate on any ObjectType
    implementing the interface, enabling polymorphic actions.

    Note: This is a reference to an ActionType, not a full definition.
    The actual ActionType must be defined separately and reference
    this interface in its scope.
    """

    action_api_name: str = Field(
        ...,
        description="apiName of the ActionType defined for this interface.",
        min_length=1,
        max_length=255,
        alias="actionApiName",
    )

    description: Optional[str] = Field(
        default=None,
        description="Documentation for this interface action.",
    )

    # Whether the action is abstract (must be implemented per ObjectType)
    is_abstract: bool = Field(
        default=False,
        description="If true, each implementing ObjectType must provide implementation.",
        alias="isAbstract",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "actionApiName": self.action_api_name,
        }
        if self.description:
            result["description"] = self.description
        if self.is_abstract:
            result["isAbstract"] = True
        return result


class Interface(OntologyEntity):
    """
    Interface schema definition - enabling polymorphism in Palantir Ontology.

    An Interface defines a contract that ObjectTypes can implement:
    - Required properties with type constraints
    - Interface inheritance (extends parent interfaces)
    - Interface-level actions for polymorphic operations

    Key Features:
    - Property contract enforcement on implementers
    - Multi-inheritance support (implements multiple interfaces)
    - Interface inheritance (interface extends interfaces)
    - Polymorphic querying and actions

    Note: Interfaces do NOT support ENDORSED status (GAP-005).
    Endorsement applies to ObjectTypes, not contracts.

    Example:
        >>> trackable = Interface(
        ...     api_name="Trackable",
        ...     display_name="Trackable Entity",
        ...     required_properties=[
        ...         InterfacePropertyRequirement(
        ...             property_api_name="trackingId",
        ...             data_type=DataTypeSpec(type=DataType.STRING),
        ...             required=True
        ...         )
        ...     ],
        ...     status=InterfaceStatus.ACTIVE,
        ... )

        >>> auditable = Interface(
        ...     api_name="Auditable",
        ...     display_name="Auditable Entity",
        ...     extends=["Trackable"],  # Inherits Trackable's requirements
        ...     required_properties=[
        ...         InterfacePropertyRequirement(
        ...             property_api_name="auditLog",
        ...             data_type=DataTypeSpec(type=DataType.JSON)
        ...         )
        ...     ],
        ... )
    """

    # Override RID to use interface-specific format
    rid: str = Field(
        default_factory=lambda: generate_rid("ontology", "interface"),
        description="Resource ID - globally unique identifier for this Interface.",
        pattern=r"^ri\.ontology\.[a-z]+\.interface\.[a-zA-Z0-9-]+$",
        json_schema_extra={"readOnly": True, "immutable": True},
    )

    # Interface Inheritance
    extends: list[str] = Field(
        default_factory=list,
        description="List of parent Interface apiNames this interface extends. "
                    "Implementing ObjectTypes must satisfy all parent requirements.",
    )

    # Required Properties
    required_properties: list[InterfacePropertyRequirement] = Field(
        default_factory=list,
        description="Properties that implementing ObjectTypes must have.",
        alias="requiredProperties",
    )

    # Interface-level Actions
    interface_actions: list[InterfaceActionDefinition] = Field(
        default_factory=list,
        description="Actions defined at the interface level for polymorphic operations.",
        alias="interfaceActions",
    )

    # Lifecycle Status
    status: InterfaceStatus = Field(
        default=InterfaceStatus.EXPERIMENTAL,
        description="Lifecycle status of the Interface.",
    )

    # Implementing ObjectTypes (for registry tracking, not serialized to Foundry)
    # This is populated by the registry, not by users
    _implementers: list[str] = []

    # Extended Metadata
    metadata: Optional[InterfaceMetadata] = Field(
        default=None,
        description="Extended metadata for versioning and audit.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "x-palantir-entity-type": "interface",
            "x-palantir-indexing": ["api_name", "rid", "status"],
        },
    )

    @model_validator(mode="after")
    def validate_unique_property_names(self) -> "Interface":
        """Validate that all required property apiNames are unique."""
        names = [p.property_api_name for p in self.required_properties]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate required property apiNames found: {set(duplicates)}"
            )
        return self

    @model_validator(mode="after")
    def validate_unique_action_names(self) -> "Interface":
        """Validate that all interface action apiNames are unique."""
        names = [a.action_api_name for a in self.interface_actions]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate interface action apiNames found: {set(duplicates)}"
            )
        return self

    @model_validator(mode="after")
    def validate_no_circular_inheritance(self) -> "Interface":
        """
        Basic validation that interface doesn't extend itself.

        Note: Full circular dependency detection requires registry access
        and is done at registration time, not at model validation.
        """
        if self.api_name in self.extends:
            raise ValueError(
                f"Interface '{self.api_name}' cannot extend itself"
            )
        return self

    def get_required_property(
        self, api_name: str
    ) -> Optional[InterfacePropertyRequirement]:
        """Get a required property by its apiName."""
        for prop in self.required_properties:
            if prop.property_api_name == api_name:
                return prop
        return None

    def get_interface_action(
        self, api_name: str
    ) -> Optional[InterfaceActionDefinition]:
        """Get an interface action by its apiName."""
        for action in self.interface_actions:
            if action.action_api_name == api_name:
                return action
        return None

    def has_parent(self, interface_api_name: str) -> bool:
        """Check if this interface extends the given interface."""
        return interface_api_name in self.extends

    def get_all_required_property_names(self) -> set[str]:
        """
        Get all required property apiNames (direct only).

        Note: For full inheritance resolution including parents,
        use InterfaceRegistry.get_all_requirements().
        """
        return {p.property_api_name for p in self.required_properties}

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result = super().to_foundry_dict()

        result["status"] = self.status.value

        if self.extends:
            result["extends"] = self.extends

        if self.required_properties:
            result["requiredProperties"] = [
                p.to_foundry_dict() for p in self.required_properties
            ]

        if self.interface_actions:
            result["interfaceActions"] = [
                a.to_foundry_dict() for a in self.interface_actions
            ]

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "Interface":
        """Create Interface from Palantir Foundry JSON format."""
        required_properties = []
        if data.get("requiredProperties"):
            required_properties = [
                InterfacePropertyRequirement.from_foundry_dict(p)
                for p in data["requiredProperties"]
            ]

        interface_actions = []
        if data.get("interfaceActions"):
            interface_actions = [
                InterfaceActionDefinition(
                    action_api_name=a["actionApiName"],
                    description=a.get("description"),
                    is_abstract=a.get("isAbstract", False),
                )
                for a in data["interfaceActions"]
            ]

        return cls(
            rid=data.get("rid", generate_rid("ontology", "interface")),
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            extends=data.get("extends", []),
            required_properties=required_properties,
            interface_actions=interface_actions,
            status=InterfaceStatus(data.get("status", "EXPERIMENTAL")),
        )


class InterfaceImplementation(BaseModel):
    """
    Tracks which ObjectTypes implement which Interfaces.

    This is used by the registry to validate implementation
    and enable polymorphic queries.
    """

    interface_api_name: str = Field(
        ...,
        description="apiName of the Interface being implemented.",
        alias="interfaceApiName",
    )

    object_type_api_name: str = Field(
        ...,
        description="apiName of the implementing ObjectType.",
        alias="objectTypeApiName",
    )

    # Validation status
    is_valid: bool = Field(
        default=True,
        description="Whether the implementation satisfies all requirements.",
        alias="isValid",
    )

    validation_errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors if implementation is invalid.",
        alias="validationErrors",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "interfaceApiName": self.interface_api_name,
            "objectTypeApiName": self.object_type_api_name,
            "isValid": self.is_valid,
        }
        if self.validation_errors:
            result["validationErrors"] = self.validation_errors
        return result
