"""
Property Constraints for Ontology Definition.

Provides validation constraint models for property definitions:
    - PropertyConstraints: Core validation rules (required, unique, pattern, etc.)
    - NumericConstraints: Min/max value constraints for numeric types
    - StringConstraints: Length and pattern constraints for strings
    - ArrayConstraints: Item count and uniqueness for arrays
    - DecimalConstraints: Precision and scale for DECIMAL type

These constraints are applied to PropertyDefinition to enforce
data quality rules at the schema level.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NumericConstraints(BaseModel):
    """
    Validation constraints for numeric types (INTEGER, LONG, FLOAT, DOUBLE, DECIMAL).
    """

    min_value: int | float | None = Field(
        default=None,
        description="Minimum allowed value (inclusive).",
        alias="minValue",
    )

    max_value: int | float | None = Field(
        default=None,
        description="Maximum allowed value (inclusive).",
        alias="maxValue",
    )

    exclusive_min: bool = Field(
        default=False,
        description="If true, min_value is exclusive (value must be > min).",
        alias="exclusiveMin",
    )

    exclusive_max: bool = Field(
        default=False,
        description="If true, max_value is exclusive (value must be < max).",
        alias="exclusiveMax",
    )

    multiple_of: int | float | None = Field(
        default=None,
        description="Value must be a multiple of this number.",
        alias="multipleOf",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_min_max(self) -> NumericConstraints:
        """Ensure min <= max when both are specified."""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"min_value ({self.min_value}) cannot be greater than max_value ({self.max_value})"
                )
        return self


class StringConstraints(BaseModel):
    """
    Validation constraints for STRING type.
    """

    min_length: int | None = Field(
        default=None,
        description="Minimum string length (inclusive).",
        ge=0,
        alias="minLength",
    )

    max_length: int | None = Field(
        default=None,
        description="Maximum string length (inclusive).",
        ge=0,
        alias="maxLength",
    )

    pattern: str | None = Field(
        default=None,
        description="Regular expression pattern for validation.",
    )

    rid_format: bool = Field(
        default=False,
        description="If true, value must be valid RID format.",
        alias="ridFormat",
    )

    uuid_format: bool = Field(
        default=False,
        description="If true, value must be valid UUID format.",
        alias="uuidFormat",
    )

    email_format: bool = Field(
        default=False,
        description="If true, value must be valid email format.",
        alias="emailFormat",
    )

    url_format: bool = Field(
        default=False,
        description="If true, value must be valid URL format.",
        alias="urlFormat",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> StringConstraints:
        """Ensure min_length <= max_length when both are specified."""
        if self.min_length is not None and self.max_length is not None:
            if self.min_length > self.max_length:
                raise ValueError(
                    f"min_length ({self.min_length}) cannot be greater than max_length ({self.max_length})"
                )
        return self


class ArrayConstraints(BaseModel):
    """
    Validation constraints for ARRAY type.
    """

    min_items: int | None = Field(
        default=None,
        description="Minimum number of items in array.",
        ge=0,
        alias="minItems",
    )

    max_items: int | None = Field(
        default=None,
        description="Maximum number of items in array.",
        ge=0,
        alias="maxItems",
    )

    unique_items: bool = Field(
        default=False,
        description="If true, all items in array must be unique.",
        alias="uniqueItems",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_items(self) -> ArrayConstraints:
        """Ensure min_items <= max_items when both are specified."""
        if self.min_items is not None and self.max_items is not None:
            if self.min_items > self.max_items:
                raise ValueError(
                    f"min_items ({self.min_items}) cannot be greater than max_items ({self.max_items})"
                )
        return self


class DecimalConstraints(BaseModel):
    """
    Validation constraints for DECIMAL type.

    DECIMAL is used for precise numeric values (e.g., currency).
    - precision: Total number of digits (1-38)
    - scale: Digits after decimal point (0-precision)
    """

    precision: int = Field(
        default=18,
        description="Total number of digits (1-38).",
        ge=1,
        le=38,
    )

    scale: int = Field(
        default=2,
        description="Digits after decimal point (0-precision).",
        ge=0,
        le=38,
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_precision_scale(self) -> DecimalConstraints:
        """Ensure scale <= precision."""
        if self.scale > self.precision:
            raise ValueError(
                f"scale ({self.scale}) cannot be greater than precision ({self.precision})"
            )
        return self


class VectorConstraints(BaseModel):
    """
    Validation constraints for VECTOR type (AI/ML embeddings).
    """

    dimension: int = Field(
        ...,
        description="Vector dimension size (required for VECTOR type).",
        ge=1,
    )

    model_config = ConfigDict(extra="forbid")


class PropertyConstraints(BaseModel):
    """
    Complete validation constraints for a property definition.

    Combines all constraint types with common flags:
    - required: Property cannot be null/empty
    - unique: Value must be unique across all instances
    - immutable: Value cannot be changed after initial set
    - enum: Allowed values list

    Usage:
        constraints = PropertyConstraints(
            required=True,
            unique=True,
            string=StringConstraints(min_length=1, max_length=100)
        )
    """

    # Common Flags
    required: bool = Field(
        default=False,
        description="If true, property cannot be null/empty.",
    )

    unique: bool = Field(
        default=False,
        description="If true, value must be unique across all instances.",
    )

    immutable: bool = Field(
        default=False,
        description="If true, value cannot be changed after initial set.",
    )

    # Enum Constraint
    enum: list[str | int | float | bool] | None = Field(
        default=None,
        description="List of allowed values for this property.",
    )

    # Default Value
    default_value: Any | None = Field(
        default=None,
        description="Default value if not provided. Cannot be set if isMandatoryControl is true.",
        alias="defaultValue",
    )

    # Type-specific Constraints
    numeric: NumericConstraints | None = Field(
        default=None,
        description="Constraints for numeric types.",
    )

    string: StringConstraints | None = Field(
        default=None,
        description="Constraints for STRING type.",
    )

    array: ArrayConstraints | None = Field(
        default=None,
        description="Constraints for ARRAY type.",
    )

    decimal: DecimalConstraints | None = Field(
        default=None,
        description="Constraints for DECIMAL type.",
    )

    vector: VectorConstraints | None = Field(
        default=None,
        description="Constraints for VECTOR type.",
    )

    # Custom Validation
    custom_validator: str | None = Field(
        default=None,
        description="Reference to custom validation function.",
        alias="customValidator",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @field_validator("enum")
    @classmethod
    def validate_enum_not_empty(cls, v: list | None) -> list | None:
        """Ensure enum list is not empty if provided."""
        if v is not None and len(v) == 0:
            raise ValueError("enum list cannot be empty")
        return v

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}

        if self.required:
            result["required"] = True
        if self.unique:
            result["unique"] = True
        if self.immutable:
            result["immutable"] = True
        if self.enum:
            result["enum"] = self.enum
        if self.default_value is not None:
            result["defaultValue"] = self.default_value

        if self.numeric:
            if self.numeric.min_value is not None:
                result["minValue"] = self.numeric.min_value
            if self.numeric.max_value is not None:
                result["maxValue"] = self.numeric.max_value

        if self.string:
            if self.string.min_length is not None:
                result["minLength"] = self.string.min_length
            if self.string.max_length is not None:
                result["maxLength"] = self.string.max_length
            if self.string.pattern:
                result["pattern"] = self.string.pattern
            if self.string.rid_format:
                result["ridFormat"] = True
            if self.string.uuid_format:
                result["uuidFormat"] = True

        if self.array:
            if self.array.min_items is not None:
                result["arrayMinItems"] = self.array.min_items
            if self.array.max_items is not None:
                result["arrayMaxItems"] = self.array.max_items
            if self.array.unique_items:
                result["arrayUnique"] = True

        if self.custom_validator:
            result["customValidator"] = self.custom_validator

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> PropertyConstraints:
        """Create from Foundry JSON format."""
        numeric = None
        string = None
        array = None

        # Build numeric constraints
        if "minValue" in data or "maxValue" in data:
            numeric = NumericConstraints(
                min_value=data.get("minValue"),
                max_value=data.get("maxValue"),
            )

        # Build string constraints
        if any(k in data for k in ["minLength", "maxLength", "pattern", "ridFormat", "uuidFormat"]):
            string = StringConstraints(
                min_length=data.get("minLength"),
                max_length=data.get("maxLength"),
                pattern=data.get("pattern"),
                rid_format=data.get("ridFormat", False),
                uuid_format=data.get("uuidFormat", False),
            )

        # Build array constraints
        if any(k in data for k in ["arrayMinItems", "arrayMaxItems", "arrayUnique"]):
            array = ArrayConstraints(
                min_items=data.get("arrayMinItems"),
                max_items=data.get("arrayMaxItems"),
                unique_items=data.get("arrayUnique", False),
            )

        return cls(
            required=data.get("required", False),
            unique=data.get("unique", False),
            immutable=data.get("immutable", False),
            enum=data.get("enum"),
            default_value=data.get("defaultValue"),
            numeric=numeric,
            string=string,
            array=array,
            custom_validator=data.get("customValidator"),
        )
