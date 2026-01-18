"""
Orion ODA v4.0 - Property Type Definitions
==========================================

Foundry-aligned PropertyDefinition with full constraint support.

This module provides:
- PropertyDefinition: Complete property definition with constraints
- PropertyConstraint: Validation constraints for properties
- PropertyType enum (re-exported from ontology_types)
- Constraint validators for common patterns

Palantir Pattern Reference:
- Properties have explicit types and constraints
- Required/unique/default constraints are first-class
- Pattern matching for string validation
- Min/max for numeric and string length
- Computed properties are cached and invalidated on dependency change

Schema Version: 4.0.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from functools import cached_property
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# ENUMS
# =============================================================================


class PropertyDataType(str, Enum):
    """
    Supported property data types.
    Aligned with Palantir Ontology Property Types.
    """
    STRING = "string"
    INTEGER = "integer"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    ARRAY = "array"
    STRUCT = "struct"
    GEOPOINT = "geopoint"
    GEOSHAPE = "geoshape"
    TIMESERIES = "timeseries"
    VECTOR = "vector"
    # Extended types
    UUID = "uuid"
    EMAIL = "email"
    URL = "url"
    JSON = "json"
    MARKDOWN = "markdown"


class ConstraintType(str, Enum):
    """Types of property constraints."""
    REQUIRED = "required"
    UNIQUE = "unique"
    IMMUTABLE = "immutable"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    PATTERN = "pattern"
    ENUM = "enum"
    CUSTOM = "custom"


class ConstraintSeverity(str, Enum):
    """Severity level for constraint violations."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# =============================================================================
# CONSTRAINT VIOLATION
# =============================================================================


@dataclass(frozen=True)
class ConstraintViolation:
    """
    Represents a property constraint violation.

    Attributes:
        property_name: Name of the property that failed validation
        constraint_type: Type of constraint that was violated
        message: Human-readable error message
        severity: Error level (error, warning, info)
        expected: Expected value/pattern
        actual: Actual value that failed
    """
    property_name: str
    constraint_type: ConstraintType
    message: str
    severity: ConstraintSeverity = ConstraintSeverity.ERROR
    expected: Optional[Any] = None
    actual: Optional[Any] = None


# =============================================================================
# PROPERTY CONSTRAINT
# =============================================================================


class PropertyConstraint(BaseModel):
    """
    Validation constraints for a property.

    Supports:
    - Required: Must have a non-null value
    - Unique: Value must be unique across all instances
    - Immutable: Cannot be changed after creation
    - Min/Max value: Numeric range constraints
    - Min/Max length: String length constraints
    - Pattern: Regex pattern matching
    - Enum: Value must be in allowed list
    - Custom: Custom validator function name

    Example:
        ```python
        PropertyConstraint(
            required=True,
            min_length=1,
            max_length=255,
            pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$"
        )
        ```
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    # Required/Unique
    required: bool = Field(
        default=False,
        description="Property must have a non-null value"
    )
    unique: bool = Field(
        default=False,
        description="Value must be unique across all instances"
    )

    # Mutability
    immutable: bool = Field(
        default=False,
        description="Cannot be changed after object creation"
    )

    # Numeric constraints
    min_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Minimum numeric value (inclusive)"
    )
    max_value: Optional[Union[int, float]] = Field(
        default=None,
        description="Maximum numeric value (inclusive)"
    )

    # String length constraints
    min_length: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum string length"
    )
    max_length: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum string length"
    )

    # Pattern constraint
    pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern for string validation"
    )

    # Enum constraint
    allowed_values: Optional[List[Any]] = Field(
        default=None,
        description="List of allowed values"
    )

    # Default value
    default_value: Optional[Any] = Field(
        default=None,
        description="Default value if not provided"
    )

    # Custom validator
    custom_validator: Optional[str] = Field(
        default=None,
        description="Name of custom validator function"
    )

    @field_validator("pattern")
    @classmethod
    def validate_pattern_syntax(cls, v: Optional[str]) -> Optional[str]:
        """Validate regex pattern syntax."""
        if v is not None:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        return v

    @model_validator(mode="after")
    def validate_range_consistency(self) -> "PropertyConstraint":
        """Ensure min <= max for both value and length constraints."""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"min_value ({self.min_value}) cannot exceed "
                    f"max_value ({self.max_value})"
                )

        if self.min_length is not None and self.max_length is not None:
            if self.min_length > self.max_length:
                raise ValueError(
                    f"min_length ({self.min_length}) cannot exceed "
                    f"max_length ({self.max_length})"
                )

        return self


# =============================================================================
# PROPERTY DEFINITION
# =============================================================================


class PropertyDefinition(BaseModel):
    """
    Complete property definition with metadata and constraints.

    Palantir Pattern:
    - Properties are first-class schema elements
    - Each property has explicit type, description, constraints
    - Indexing hints for query optimization
    - Computed properties reference dependencies

    Example:
        ```python
        PropertyDefinition(
            name="email",
            property_type=PropertyDataType.EMAIL,
            description="User's email address",
            constraints=PropertyConstraint(
                required=True,
                unique=True,
                pattern=r"^[\\w.-]+@[\\w.-]+\\.\\w+$"
            ),
            indexed=True,
            searchable=True
        )
        ```
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    # Identity
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Property name (snake_case recommended)"
    )

    # Type
    property_type: PropertyDataType = Field(
        ...,
        description="Data type for this property"
    )

    # For array/struct types
    element_type: Optional[PropertyDataType] = Field(
        default=None,
        description="Element type for ARRAY properties"
    )
    struct_schema: Optional[Dict[str, "PropertyDefinition"]] = Field(
        default=None,
        description="Schema for STRUCT properties"
    )

    # Constraints
    constraints: PropertyConstraint = Field(
        default_factory=PropertyConstraint,
        description="Validation constraints"
    )

    # Metadata
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Human-readable description"
    )
    display_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Display name for UI"
    )

    # Indexing hints
    indexed: bool = Field(
        default=False,
        description="Create database index for this property"
    )
    searchable: bool = Field(
        default=False,
        description="Include in full-text search"
    )
    sortable: bool = Field(
        default=True,
        description="Allow sorting by this property"
    )

    # Computed property support
    is_computed: bool = Field(
        default=False,
        description="Property value is computed from other properties"
    )
    compute_dependencies: List[str] = Field(
        default_factory=list,
        description="Properties this computed property depends on"
    )
    compute_function: Optional[str] = Field(
        default=None,
        description="Name of compute function for computed properties"
    )

    # Audit
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    schema_version: str = Field(default="1.0.0")

    @field_validator("name")
    @classmethod
    def validate_property_name(cls, v: str) -> str:
        """Enforce snake_case naming convention."""
        if not v:
            raise ValueError("Property name cannot be empty")
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(
                f"Property name must be lowercase snake_case: {v}"
            )
        return v

    @model_validator(mode="after")
    def validate_array_element_type(self) -> "PropertyDefinition":
        """Array properties should specify element_type."""
        if self.property_type == PropertyDataType.ARRAY and not self.element_type:
            # Default to STRING if not specified
            object.__setattr__(self, "element_type", PropertyDataType.STRING)
        return self

    @model_validator(mode="after")
    def validate_computed_dependencies(self) -> "PropertyDefinition":
        """Computed properties must have dependencies and function."""
        if self.is_computed:
            if not self.compute_dependencies:
                raise ValueError(
                    "Computed properties must specify compute_dependencies"
                )
            if not self.compute_function:
                raise ValueError(
                    "Computed properties must specify compute_function"
                )
        return self

    @property
    def is_required(self) -> bool:
        """Check if property is required."""
        return self.constraints.required

    @property
    def is_unique(self) -> bool:
        """Check if property must be unique."""
        return self.constraints.unique

    @property
    def is_immutable(self) -> bool:
        """Check if property is immutable after creation."""
        return self.constraints.immutable

    @property
    def has_default(self) -> bool:
        """Check if property has a default value."""
        return self.constraints.default_value is not None

    def to_json_schema(self) -> Dict[str, Any]:
        """Export to JSON Schema format."""
        schema: Dict[str, Any] = {
            "type": self._type_to_json_schema_type(),
            "description": self.description or f"Property: {self.name}",
        }

        if self.constraints.min_value is not None:
            schema["minimum"] = self.constraints.min_value
        if self.constraints.max_value is not None:
            schema["maximum"] = self.constraints.max_value
        if self.constraints.min_length is not None:
            schema["minLength"] = self.constraints.min_length
        if self.constraints.max_length is not None:
            schema["maxLength"] = self.constraints.max_length
        if self.constraints.pattern:
            schema["pattern"] = self.constraints.pattern
        if self.constraints.allowed_values:
            schema["enum"] = self.constraints.allowed_values
        if self.constraints.default_value is not None:
            schema["default"] = self.constraints.default_value

        return schema

    def _type_to_json_schema_type(self) -> str:
        """Map PropertyDataType to JSON Schema type."""
        mapping = {
            PropertyDataType.STRING: "string",
            PropertyDataType.INTEGER: "integer",
            PropertyDataType.LONG: "integer",
            PropertyDataType.FLOAT: "number",
            PropertyDataType.DOUBLE: "number",
            PropertyDataType.BOOLEAN: "boolean",
            PropertyDataType.DATE: "string",
            PropertyDataType.TIMESTAMP: "string",
            PropertyDataType.ARRAY: "array",
            PropertyDataType.STRUCT: "object",
            PropertyDataType.UUID: "string",
            PropertyDataType.EMAIL: "string",
            PropertyDataType.URL: "string",
            PropertyDataType.JSON: "object",
            PropertyDataType.MARKDOWN: "string",
        }
        return mapping.get(self.property_type, "string")


# =============================================================================
# CONSTRAINT VALIDATORS
# =============================================================================


class PropertyConstraintValidator:
    """
    Validates property values against constraints.

    Supports registering custom validators for extensibility.

    Example:
        ```python
        validator = PropertyConstraintValidator()

        # Register custom validator
        validator.register_validator("email_domain", lambda v, ctx: v.endswith("@company.com"))

        # Validate a value
        violations = validator.validate(
            definition=email_property_def,
            value="user@example.com"
        )
        ```
    """

    def __init__(self) -> None:
        """Initialize the validator with default validators."""
        self._custom_validators: Dict[str, Callable[[Any, Dict[str, Any]], bool]] = {}

    def register_validator(
        self,
        name: str,
        validator: Callable[[Any, Dict[str, Any]], bool]
    ) -> None:
        """
        Register a custom validator function.

        Args:
            name: Validator name (referenced in PropertyConstraint.custom_validator)
            validator: Function that takes (value, context) and returns True if valid
        """
        self._custom_validators[name] = validator

    def validate(
        self,
        definition: PropertyDefinition,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        is_update: bool = False,
    ) -> List[ConstraintViolation]:
        """
        Validate a value against property constraints.

        Args:
            definition: Property definition with constraints
            value: Value to validate
            context: Optional context for custom validators
            is_update: True if this is an update operation

        Returns:
            List of constraint violations (empty if valid)
        """
        violations: List[ConstraintViolation] = []
        constraints = definition.constraints
        prop_name = definition.name

        # Required check
        if constraints.required and value is None:
            violations.append(ConstraintViolation(
                property_name=prop_name,
                constraint_type=ConstraintType.REQUIRED,
                message=f"Property '{prop_name}' is required",
                expected="non-null value",
                actual=None,
            ))
            return violations  # Early return if required and null

        # Skip remaining checks if value is None
        if value is None:
            return violations

        # Immutable check (only on update)
        if is_update and constraints.immutable:
            violations.append(ConstraintViolation(
                property_name=prop_name,
                constraint_type=ConstraintType.IMMUTABLE,
                message=f"Property '{prop_name}' is immutable and cannot be changed",
                severity=ConstraintSeverity.ERROR,
            ))

        # Numeric range checks
        if isinstance(value, (int, float)):
            if constraints.min_value is not None and value < constraints.min_value:
                violations.append(ConstraintViolation(
                    property_name=prop_name,
                    constraint_type=ConstraintType.MIN_VALUE,
                    message=f"Value {value} is below minimum {constraints.min_value}",
                    expected=f">= {constraints.min_value}",
                    actual=value,
                ))

            if constraints.max_value is not None and value > constraints.max_value:
                violations.append(ConstraintViolation(
                    property_name=prop_name,
                    constraint_type=ConstraintType.MAX_VALUE,
                    message=f"Value {value} exceeds maximum {constraints.max_value}",
                    expected=f"<= {constraints.max_value}",
                    actual=value,
                ))

        # String length checks
        if isinstance(value, str):
            if constraints.min_length is not None and len(value) < constraints.min_length:
                violations.append(ConstraintViolation(
                    property_name=prop_name,
                    constraint_type=ConstraintType.MIN_LENGTH,
                    message=f"Length {len(value)} is below minimum {constraints.min_length}",
                    expected=f">= {constraints.min_length} chars",
                    actual=len(value),
                ))

            if constraints.max_length is not None and len(value) > constraints.max_length:
                violations.append(ConstraintViolation(
                    property_name=prop_name,
                    constraint_type=ConstraintType.MAX_LENGTH,
                    message=f"Length {len(value)} exceeds maximum {constraints.max_length}",
                    expected=f"<= {constraints.max_length} chars",
                    actual=len(value),
                ))

            # Pattern check
            if constraints.pattern:
                if not re.match(constraints.pattern, value):
                    violations.append(ConstraintViolation(
                        property_name=prop_name,
                        constraint_type=ConstraintType.PATTERN,
                        message=f"Value does not match pattern: {constraints.pattern}",
                        expected=constraints.pattern,
                        actual=value,
                    ))

        # Enum check
        if constraints.allowed_values is not None:
            if value not in constraints.allowed_values:
                violations.append(ConstraintViolation(
                    property_name=prop_name,
                    constraint_type=ConstraintType.ENUM,
                    message=f"Value '{value}' not in allowed values",
                    expected=constraints.allowed_values,
                    actual=value,
                ))

        # Custom validator
        if constraints.custom_validator:
            validator = self._custom_validators.get(constraints.custom_validator)
            if validator:
                try:
                    if not validator(value, context or {}):
                        violations.append(ConstraintViolation(
                            property_name=prop_name,
                            constraint_type=ConstraintType.CUSTOM,
                            message=f"Custom validation '{constraints.custom_validator}' failed",
                        ))
                except Exception as e:
                    violations.append(ConstraintViolation(
                        property_name=prop_name,
                        constraint_type=ConstraintType.CUSTOM,
                        message=f"Custom validator error: {e}",
                        severity=ConstraintSeverity.ERROR,
                    ))
            else:
                violations.append(ConstraintViolation(
                    property_name=prop_name,
                    constraint_type=ConstraintType.CUSTOM,
                    message=f"Custom validator '{constraints.custom_validator}' not found",
                    severity=ConstraintSeverity.WARNING,
                ))

        return violations


# =============================================================================
# BUILT-IN VALIDATORS
# =============================================================================


def validate_email(value: Any, context: Dict[str, Any]) -> bool:
    """Validate email format."""
    if not isinstance(value, str):
        return False
    pattern = r"^[\w.-]+@[\w.-]+\.\w{2,}$"
    return bool(re.match(pattern, value))


def validate_url(value: Any, context: Dict[str, Any]) -> bool:
    """Validate URL format."""
    if not isinstance(value, str):
        return False
    pattern = r"^https?://[\w.-]+(?:/[\w./-]*)?$"
    return bool(re.match(pattern, value))


def validate_uuid(value: Any, context: Dict[str, Any]) -> bool:
    """Validate UUID format."""
    if not isinstance(value, str):
        return False
    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(pattern, value.lower()))


def validate_slug(value: Any, context: Dict[str, Any]) -> bool:
    """Validate URL slug format."""
    if not isinstance(value, str):
        return False
    pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    return bool(re.match(pattern, value))


# =============================================================================
# DEFAULT VALIDATOR INSTANCE
# =============================================================================


_DEFAULT_VALIDATOR = PropertyConstraintValidator()
_DEFAULT_VALIDATOR.register_validator("email", validate_email)
_DEFAULT_VALIDATOR.register_validator("url", validate_url)
_DEFAULT_VALIDATOR.register_validator("uuid", validate_uuid)
_DEFAULT_VALIDATOR.register_validator("slug", validate_slug)


def get_property_validator() -> PropertyConstraintValidator:
    """Get the default property constraint validator."""
    return _DEFAULT_VALIDATOR


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "PropertyDataType",
    "ConstraintType",
    "ConstraintSeverity",
    # Models
    "PropertyConstraint",
    "PropertyDefinition",
    "ConstraintViolation",
    # Validator
    "PropertyConstraintValidator",
    "get_property_validator",
    # Built-in validators
    "validate_email",
    "validate_url",
    "validate_uuid",
    "validate_slug",
]
