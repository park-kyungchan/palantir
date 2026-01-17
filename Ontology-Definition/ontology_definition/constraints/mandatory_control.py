"""
Mandatory Control Configuration for Row-Level Security (GAP-002 P1-CRITICAL).

Palantir Foundry's Mandatory Control Properties enforce row-level access control
based on security markings, organization membership, or classification levels.

Key Concepts:
    - Mandatory Control Property: A property that determines who can see/edit a row
    - Marking ID: UUID reference to a security marking definition
    - Restricted View: Filtered view of data based on user's markings

This is a P1-CRITICAL security feature in Palantir Foundry compliance.

Usage:
    security_config = MandatoryControlConfig(
        property_api_name="securityMarking",
        control_type=ControlType.MARKINGS,
        marking_column_mapping="security_markings",
        allowed_markings=["uuid1", "uuid2"]
    )
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ontology_definition.core.enums import ClassificationLevel, ControlType


class MandatoryControlConfig(BaseModel):
    """
    Configuration for a Mandatory Control Property.

    Mandatory Control Properties are the cornerstone of Palantir's row-level
    security model. When configured:
    1. Each row must have a value for this property
    2. Users can only see rows where their markings intersect with the row's markings
    3. The property cannot have a default value (must be explicitly set)

    Control Types:
        - MARKINGS: Most common. Uses security marking UUIDs.
        - ORGANIZATIONS: Based on organization membership.
        - CLASSIFICATIONS: For CBAC (Classification-Based Access Control).

    Example:
        >>> config = MandatoryControlConfig(
        ...     property_api_name="securityMarking",
        ...     control_type=ControlType.MARKINGS,
        ...     marking_column_mapping="security_markings",
        ...     allowed_markings=["550e8400-e29b-41d4-a716-446655440000"]
        ... )

    Attributes:
        property_api_name: apiName of the property serving as mandatory control
        control_type: Type of control (MARKINGS, ORGANIZATIONS, CLASSIFICATIONS)
        marking_column_mapping: Column in Restricted View containing marking IDs
        allowed_markings: For MARKINGS type, the set of valid marking UUIDs
        allowed_organizations: For ORGANIZATIONS type, valid organization UUIDs
        max_classification_level: For CLASSIFICATIONS type, maximum allowed level
    """

    property_api_name: str = Field(
        ...,
        description="apiName of the property designated as mandatory control.",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        alias="propertyApiName",
    )

    control_type: ControlType = Field(
        ...,
        description="Type of mandatory control mechanism.",
        alias="controlType",
    )

    marking_column_mapping: Optional[str] = Field(
        default=None,
        description="Column name in backing Restricted View containing marking IDs. "
                    "Must be STRING ARRAY of UUIDs.",
        alias="markingColumnMapping",
    )

    allowed_markings: Optional[list[str]] = Field(
        default=None,
        description="For MARKINGS type, the set of allowed marking UUIDs. "
                    "If not specified, all markings are allowed.",
        alias="allowedMarkings",
    )

    allowed_organizations: Optional[list[str]] = Field(
        default=None,
        description="For ORGANIZATIONS type, the set of allowed organization UUIDs.",
        alias="allowedOrganizations",
    )

    max_classification_level: Optional[ClassificationLevel] = Field(
        default=None,
        description="For CLASSIFICATIONS type (CBAC), the maximum classification level.",
        alias="maxClassificationLevel",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
    )

    @field_validator("allowed_markings", "allowed_organizations")
    @classmethod
    def validate_uuid_list(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate that all items in the list are valid UUID format."""
        if v is None:
            return v

        import uuid as uuid_module

        for item in v:
            try:
                uuid_module.UUID(item)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {item}")
        return v

    @model_validator(mode="after")
    def validate_control_type_requirements(self) -> "MandatoryControlConfig":
        """
        Validate that required fields are present based on control_type.

        - MARKINGS: Should have marking_column_mapping
        - ORGANIZATIONS: Should have allowed_organizations
        - CLASSIFICATIONS: Should have max_classification_level
        """
        if self.control_type == ControlType.MARKINGS:
            if not self.marking_column_mapping:
                raise ValueError(
                    "marking_column_mapping is required for MARKINGS control type"
                )

        elif self.control_type == ControlType.ORGANIZATIONS:
            if not self.allowed_organizations:
                raise ValueError(
                    "allowed_organizations is required for ORGANIZATIONS control type"
                )

        elif self.control_type == ControlType.CLASSIFICATIONS:
            if not self.max_classification_level:
                raise ValueError(
                    "max_classification_level is required for CLASSIFICATIONS control type"
                )

        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "propertyApiName": self.property_api_name,
            "controlType": self.control_type.value,
        }

        if self.marking_column_mapping:
            result["markingColumnMapping"] = self.marking_column_mapping

        if self.allowed_markings:
            result["allowedMarkings"] = self.allowed_markings

        if self.allowed_organizations:
            result["allowedOrganizations"] = self.allowed_organizations

        if self.max_classification_level:
            result["maxClassificationLevel"] = self.max_classification_level.value

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "MandatoryControlConfig":
        """Create from Foundry JSON format."""
        max_level = None
        if data.get("maxClassificationLevel"):
            max_level = ClassificationLevel(data["maxClassificationLevel"])

        return cls(
            property_api_name=data["propertyApiName"],
            control_type=ControlType(data["controlType"]),
            marking_column_mapping=data.get("markingColumnMapping"),
            allowed_markings=data.get("allowedMarkings"),
            allowed_organizations=data.get("allowedOrganizations"),
            max_classification_level=max_level,
        )


class MandatoryControlPropertyRequirements:
    """
    Static validation rules for Mandatory Control Properties.

    These rules must be enforced when a property is designated as
    mandatory control:
    1. Property must be REQUIRED (cannot be null)
    2. Property must NOT have a default value
    3. Property data type must be STRING or ARRAY[STRING] for marking IDs
    4. Property must be indexed for performance
    """

    @staticmethod
    def validate_property_for_mandatory_control(
        is_required: bool,
        has_default: bool,
        data_type: str,
        is_array: bool = False,
    ) -> list[str]:
        """
        Validate a property's suitability for mandatory control.

        Args:
            is_required: Whether the property is required
            has_default: Whether the property has a default value
            data_type: The property's data type
            is_array: Whether the property is an array type

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        if not is_required:
            errors.append(
                "Mandatory control property must be required (cannot be null)"
            )

        if has_default:
            errors.append(
                "Mandatory control property cannot have a default value"
            )

        valid_types = {"STRING"}
        if data_type not in valid_types and not (is_array and data_type == "STRING"):
            errors.append(
                f"Mandatory control property must be STRING or ARRAY[STRING], "
                f"got {data_type}"
            )

        return errors


class SecurityMarkingReference(BaseModel):
    """
    Reference to a Security Marking definition.

    Security Markings are defined at the Foundry level and referenced
    by their UUID in Mandatory Control configurations.
    """

    marking_id: str = Field(
        ...,
        description="UUID of the security marking.",
        alias="markingId",
    )

    display_name: Optional[str] = Field(
        default=None,
        description="Human-readable name for the marking.",
        alias="displayName",
    )

    description: Optional[str] = Field(
        default=None,
        description="Description of what this marking represents.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @field_validator("marking_id")
    @classmethod
    def validate_marking_uuid(cls, v: str) -> str:
        """Validate marking_id is a valid UUID."""
        import uuid as uuid_module

        try:
            uuid_module.UUID(v)
        except ValueError:
            raise ValueError(f"Invalid marking UUID: {v}")
        return v
