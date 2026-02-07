"""
ValueType Definition for Ontology.

A ValueType is a user-defined type derived from a base type with additional
constraints. ValueTypes are reusable across multiple Properties, enabling:
    - Consistent validation rules (e.g., EmailAddress, PhoneNumber)
    - Semantic typing (e.g., PositiveInteger, Priority)
    - Domain-specific constraints (e.g., ISO8601Date, Currency)

This enables DRY constraint definitions without repeating patterns across properties.

Example:
    email_type = ValueType(
        api_name="EmailAddress",
        display_name="Email Address",
        description="Valid email address format",
        base_type=ValueTypeBaseType.STRING,
        constraints=ValueTypeConstraints(
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            max_length=255,
            email_format=True,
        ),
    )
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology_definition.core.base import OntologyEntity
from ontology_definition.core.identifiers import generate_rid


class ValueTypeBaseType(str, Enum):
    """
    Primitive types that ValueTypes can extend.

    ValueTypes can only be based on primitive types,
    not complex types like ARRAY or STRUCT.
    """

    STRING = "STRING"
    INTEGER = "INTEGER"
    LONG = "LONG"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    DATETIME = "DATETIME"


class ValueTypeStatus(str, Enum):
    """Lifecycle status for ValueTypes."""

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


class ValueTypeConstraints(BaseModel):
    """
    Constraints that define a ValueType.

    At least one constraint must be specified to create a meaningful ValueType.
    These constraints are applied to all properties using this ValueType.

    Example:
        # Email format
        ValueTypeConstraints(
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            email_format=True,
            max_length=255,
        )

        # Positive integer
        ValueTypeConstraints(min_value=1)

        # Priority enum
        ValueTypeConstraints(enum=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    """

    # Enumeration constraint
    enum: Optional[list[Any]] = Field(
        default=None,
        description="Allowed values for this ValueType.",
    )

    # Numeric constraints
    min_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Minimum numeric value (inclusive).",
        alias="minValue",
    )

    max_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Maximum numeric value (inclusive).",
        alias="maxValue",
    )

    # String length constraints
    min_length: Optional[int] = Field(
        default=None,
        description="Minimum string length.",
        ge=0,
        alias="minLength",
    )

    max_length: Optional[int] = Field(
        default=None,
        description="Maximum string length.",
        ge=0,
        alias="maxLength",
    )

    # Pattern constraint
    pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern that values must match.",
    )

    # Format constraints
    rid_format: bool = Field(
        default=False,
        description="If true, must be valid RID format.",
        alias="ridFormat",
    )

    uuid_format: bool = Field(
        default=False,
        description="If true, must be valid UUID format.",
        alias="uuidFormat",
    )

    email_format: bool = Field(
        default=False,
        description="If true, must be valid email format.",
        alias="emailFormat",
    )

    url_format: bool = Field(
        default=False,
        description="If true, must be valid URL format.",
        alias="urlFormat",
    )

    date_format: Optional[str] = Field(
        default=None,
        description="Expected date format string (e.g., 'YYYY-MM-DD').",
        alias="dateFormat",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_at_least_one_constraint(self) -> "ValueTypeConstraints":
        """Ensure at least one constraint is specified."""
        has_constraint = any([
            self.enum is not None,
            self.min_value is not None,
            self.max_value is not None,
            self.min_length is not None,
            self.max_length is not None,
            self.pattern is not None,
            self.rid_format,
            self.uuid_format,
            self.email_format,
            self.url_format,
            self.date_format is not None,
        ])
        if not has_constraint:
            raise ValueError(
                "ValueTypeConstraints must specify at least one constraint"
            )
        return self

    @model_validator(mode="after")
    def validate_min_max_consistency(self) -> "ValueTypeConstraints":
        """Validate min/max values are consistent."""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"min_value ({self.min_value}) cannot be greater than "
                    f"max_value ({self.max_value})"
                )

        if self.min_length is not None and self.max_length is not None:
            if self.min_length > self.max_length:
                raise ValueError(
                    f"min_length ({self.min_length}) cannot be greater than "
                    f"max_length ({self.max_length})"
                )

        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}

        if self.enum is not None:
            result["enum"] = self.enum
        if self.min_value is not None:
            result["minValue"] = self.min_value
        if self.max_value is not None:
            result["maxValue"] = self.max_value
        if self.min_length is not None:
            result["minLength"] = self.min_length
        if self.max_length is not None:
            result["maxLength"] = self.max_length
        if self.pattern is not None:
            result["pattern"] = self.pattern
        if self.rid_format:
            result["ridFormat"] = True
        if self.uuid_format:
            result["uuidFormat"] = True
        if self.email_format:
            result["emailFormat"] = True
        if self.url_format:
            result["urlFormat"] = True
        if self.date_format is not None:
            result["dateFormat"] = self.date_format

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "ValueTypeConstraints":
        """Create from Foundry JSON format."""
        return cls(
            enum=data.get("enum"),
            min_value=data.get("minValue"),
            max_value=data.get("maxValue"),
            min_length=data.get("minLength"),
            max_length=data.get("maxLength"),
            pattern=data.get("pattern"),
            rid_format=data.get("ridFormat", False),
            uuid_format=data.get("uuidFormat", False),
            email_format=data.get("emailFormat", False),
            url_format=data.get("urlFormat", False),
            date_format=data.get("dateFormat"),
        )


class ValueType(OntologyEntity):
    """
    ValueType schema definition - reusable constrained type.

    A ValueType extends a primitive base type with validation constraints,
    enabling consistent typing across multiple properties without
    repeating constraint definitions.

    Key Features:
    - Based on primitive types only (STRING, INTEGER, LONG, etc.)
    - Constraint definition (enum, min/max, pattern, format)
    - Reusable across properties via valueTypeRef
    - Semantic naming for clarity

    Common ValueTypes:
    - EmailAddress: STRING with email pattern
    - PhoneNumber: STRING with phone pattern
    - PositiveInteger: INTEGER with minValue=1
    - Priority: STRING with enum [LOW, MEDIUM, HIGH, CRITICAL]
    - ISO8601Date: DATE with dateFormat

    Example:
        >>> positive_int = ValueType(
        ...     api_name="PositiveInteger",
        ...     display_name="Positive Integer",
        ...     description="Integer greater than zero",
        ...     base_type=ValueTypeBaseType.INTEGER,
        ...     constraints=ValueTypeConstraints(min_value=1),
        ... )

        >>> priority = ValueType(
        ...     api_name="Priority",
        ...     display_name="Priority Level",
        ...     base_type=ValueTypeBaseType.STRING,
        ...     constraints=ValueTypeConstraints(
        ...         enum=["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        ...     ),
        ... )
    """

    # Override RID to use value-type specific format
    rid: str = Field(
        default_factory=lambda: generate_rid("ontology", "value-type"),
        description="Resource ID - globally unique identifier for this ValueType.",
        pattern=r"^ri\.ontology\.[a-z]+\.value-type\.[a-zA-Z0-9-]+$",
        json_schema_extra={"readOnly": True, "immutable": True},
    )

    # Base type (REQUIRED)
    base_type: ValueTypeBaseType = Field(
        ...,
        description="Underlying primitive type this ValueType extends.",
        alias="baseType",
    )

    # Constraints (REQUIRED - must have at least one)
    constraints: ValueTypeConstraints = Field(
        ...,
        description="Validation constraints that define this ValueType.",
    )

    # Lifecycle Status
    status: ValueTypeStatus = Field(
        default=ValueTypeStatus.EXPERIMENTAL,
        description="Lifecycle status of the ValueType.",
    )

    # Usage tracking (auto-populated by registry)
    used_by_properties: list[str] = Field(
        default_factory=list,
        description="Property apiNames using this ValueType (auto-populated).",
        alias="usedByProperties",
        json_schema_extra={"readOnly": True},
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "x-palantir-entity-type": "value-type",
            "x-palantir-indexing": ["api_name", "rid", "status", "base_type"],
        },
    )

    @model_validator(mode="after")
    def validate_constraints_match_base_type(self) -> "ValueType":
        """Validate that constraints are appropriate for the base type."""
        c = self.constraints
        bt = self.base_type

        # String constraints only for STRING type
        string_constraints = [c.min_length, c.max_length, c.pattern,
                            c.email_format, c.url_format, c.rid_format,
                            c.uuid_format, c.date_format]
        if any(string_constraints) and bt != ValueTypeBaseType.STRING:
            # date_format is also valid for DATE/DATETIME/TIMESTAMP
            if c.date_format and bt in (
                ValueTypeBaseType.DATE,
                ValueTypeBaseType.DATETIME,
                ValueTypeBaseType.TIMESTAMP
            ):
                pass  # OK
            elif c.date_format is None or bt not in (
                ValueTypeBaseType.DATE,
                ValueTypeBaseType.DATETIME,
                ValueTypeBaseType.TIMESTAMP
            ):
                # Check if only date_format is set
                non_date_string_constraints = [
                    c.min_length, c.max_length, c.pattern,
                    c.email_format, c.url_format, c.rid_format, c.uuid_format
                ]
                if any(non_date_string_constraints):
                    raise ValueError(
                        f"String constraints (minLength, maxLength, pattern, "
                        f"format flags) are only valid for STRING base type, "
                        f"not {bt.value}"
                    )

        # Numeric constraints only for numeric types
        numeric_types = {
            ValueTypeBaseType.INTEGER, ValueTypeBaseType.LONG,
            ValueTypeBaseType.FLOAT, ValueTypeBaseType.DOUBLE
        }
        if (c.min_value is not None or c.max_value is not None):
            if bt not in numeric_types:
                raise ValueError(
                    f"Numeric constraints (minValue, maxValue) are only valid "
                    f"for numeric base types, not {bt.value}"
                )

        return self

    def is_enum_type(self) -> bool:
        """Check if this ValueType is an enumeration."""
        return self.constraints.enum is not None

    def is_range_constrained(self) -> bool:
        """Check if this ValueType has numeric range constraints."""
        return (
            self.constraints.min_value is not None
            or self.constraints.max_value is not None
        )

    def is_pattern_constrained(self) -> bool:
        """Check if this ValueType has a pattern constraint."""
        return self.constraints.pattern is not None

    def get_allowed_values(self) -> Optional[list[Any]]:
        """Get enum values if this is an enum type."""
        return self.constraints.enum

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result = super().to_foundry_dict()

        result["$type"] = "ValueType"
        result["baseType"] = self.base_type.value
        result["constraints"] = self.constraints.to_foundry_dict()
        result["status"] = self.status.value

        if self.used_by_properties:
            result["usedByProperties"] = self.used_by_properties

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "ValueType":
        """Create ValueType from Palantir Foundry JSON format."""
        return cls(
            rid=data.get("rid", generate_rid("ontology", "value-type")),
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            base_type=ValueTypeBaseType(data["baseType"]),
            constraints=ValueTypeConstraints.from_foundry_dict(data["constraints"]),
            status=ValueTypeStatus(data.get("status", "EXPERIMENTAL")),
            used_by_properties=data.get("usedByProperties", []),
        )


# Predefined common ValueTypes for convenience
class CommonValueTypes:
    """
    Factory for commonly used ValueTypes.

    Usage:
        email_type = CommonValueTypes.email_address()
        priority_type = CommonValueTypes.priority()
    """

    @staticmethod
    def email_address() -> ValueType:
        """Create an EmailAddress ValueType."""
        return ValueType(
            api_name="EmailAddress",
            display_name="Email Address",
            description="Valid email address format.",
            base_type=ValueTypeBaseType.STRING,
            constraints=ValueTypeConstraints(
                pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                max_length=255,
                email_format=True,
            ),
            status=ValueTypeStatus.ACTIVE,
        )

    @staticmethod
    def positive_integer() -> ValueType:
        """Create a PositiveInteger ValueType."""
        return ValueType(
            api_name="PositiveInteger",
            display_name="Positive Integer",
            description="Integer greater than zero.",
            base_type=ValueTypeBaseType.INTEGER,
            constraints=ValueTypeConstraints(min_value=1),
            status=ValueTypeStatus.ACTIVE,
        )

    @staticmethod
    def priority(
        levels: Optional[list[str]] = None
    ) -> ValueType:
        """Create a Priority ValueType with customizable levels."""
        if levels is None:
            levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        return ValueType(
            api_name="Priority",
            display_name="Priority Level",
            description="Task or item priority level.",
            base_type=ValueTypeBaseType.STRING,
            constraints=ValueTypeConstraints(enum=levels),
            status=ValueTypeStatus.ACTIVE,
        )

    @staticmethod
    def url() -> ValueType:
        """Create a URL ValueType."""
        return ValueType(
            api_name="URL",
            display_name="URL",
            description="Valid URL format.",
            base_type=ValueTypeBaseType.STRING,
            constraints=ValueTypeConstraints(
                url_format=True,
                max_length=2048,
            ),
            status=ValueTypeStatus.ACTIVE,
        )

    @staticmethod
    def uuid() -> ValueType:
        """Create a UUID ValueType."""
        return ValueType(
            api_name="UUID",
            display_name="UUID",
            description="Valid UUID format.",
            base_type=ValueTypeBaseType.STRING,
            constraints=ValueTypeConstraints(
                uuid_format=True,
                pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            ),
            status=ValueTypeStatus.ACTIVE,
        )

    @staticmethod
    def percentage() -> ValueType:
        """Create a Percentage ValueType (0-100)."""
        return ValueType(
            api_name="Percentage",
            display_name="Percentage",
            description="Percentage value between 0 and 100.",
            base_type=ValueTypeBaseType.DOUBLE,
            constraints=ValueTypeConstraints(
                min_value=0.0,
                max_value=100.0,
            ),
            status=ValueTypeStatus.ACTIVE,
        )
