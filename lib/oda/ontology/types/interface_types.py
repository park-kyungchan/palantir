"""
Orion ODA v4.0 - Interface Type Definitions
============================================

Provides interface support for ObjectTypes, enabling Palantir-style polymorphism.

Interfaces define contracts that ObjectTypes can implement:
- Required properties (PropertySpec)
- Required methods (MethodSpec)
- Interface inheritance (extends)

This enables:
- Type-safe polymorphism across ObjectTypes
- Interface-based queries (find all IVersionable objects)
- Contract enforcement at registration time

Palantir Pattern:
- Interfaces are similar to Palantir's "shared property types"
- Multiple ObjectTypes can implement the same interface
- Interface compliance is validated at registration time

Example:
    ```python
    # Define an interface
    IVersionable = InterfaceDefinition(
        interface_id="IVersionable",
        description="Objects that support versioning",
        required_properties=[
            PropertySpec(name="version", type_hint="int"),
            PropertySpec(name="version_history", type_hint="List[str]"),
        ],
        required_methods=[
            MethodSpec(name="bump_version", signature="(self) -> int"),
        ],
    )

    # Implement the interface
    @implements_interface("IVersionable")
    class Document(OntologyObject):
        version: int = 1
        version_history: List[str] = []

        def bump_version(self) -> int:
            self.version += 1
            return self.version
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import re
from typing import Any, Callable, List, Optional, Type, get_type_hints

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# PROPERTY SPECIFICATION
# =============================================================================


class PropertySpec(BaseModel):
    """
    Specification for a required property in an interface.

    Attributes:
        name: Property name (must match ObjectType field name)
        type_hint: Type hint as string (e.g., "str", "int", "List[str]")
        description: Human-readable description
        required: Whether the property must be present (default True)
        default_allowed: Whether a default value is acceptable (default True)

    Example:
        PropertySpec(
            name="version",
            type_hint="int",
            description="Object version number",
            required=True,
        )
    """

    name: str = Field(
        ...,
        description="Property name",
        min_length=1,
        pattern=r"^[a-z_][a-z0-9_]*$",
    )
    type_hint: str = Field(
        ...,
        description="Type hint as string (e.g., 'str', 'int', 'List[str]')",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the property",
    )
    required: bool = Field(
        default=True,
        description="Whether this property must be present",
    )
    default_allowed: bool = Field(
        default=True,
        description="Whether a default value is acceptable",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure property name follows Python naming conventions."""
        if v.startswith("__"):
            raise ValueError("Property name cannot start with double underscore")
        return v


# =============================================================================
# METHOD SPECIFICATION
# =============================================================================


class MethodSpec(BaseModel):
    """
    Specification for a required method in an interface.

    Attributes:
        name: Method name (must match ObjectType method name)
        signature: Method signature as string (e.g., "(self, arg: Type) -> ReturnType")
        description: Human-readable description
        is_async: Whether the method is async (default False)
        is_classmethod: Whether the method is a classmethod (default False)
        is_staticmethod: Whether the method is a staticmethod (default False)

    Example:
        MethodSpec(
            name="bump_version",
            signature="(self) -> int",
            description="Increment version and return new version number",
        )
    """

    name: str = Field(
        ...,
        description="Method name",
        min_length=1,
        pattern=r"^[a-z_][a-z0-9_]*$",
    )
    signature: str = Field(
        ...,
        description="Method signature (e.g., '(self, arg: Type) -> ReturnType')",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the method",
    )
    is_async: bool = Field(
        default=False,
        description="Whether this is an async method",
    )
    is_classmethod: bool = Field(
        default=False,
        description="Whether this is a classmethod",
    )
    is_staticmethod: bool = Field(
        default=False,
        description="Whether this is a staticmethod",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure method name follows Python naming conventions."""
        if v.startswith("__") and not v.endswith("__"):
            raise ValueError("Method name cannot start with double underscore unless dunder")
        return v

    @field_validator("signature")
    @classmethod
    def validate_signature(cls, v: str) -> str:
        """Validate signature format."""
        if not v.startswith("("):
            raise ValueError("Signature must start with '('")
        if "->" not in v:
            raise ValueError("Signature must include return type (use '-> None' for void)")
        return v


# =============================================================================
# INTERFACE DEFINITION
# =============================================================================


class InterfaceDefinition(BaseModel):
    """
    Defines an interface that ObjectTypes can implement.
    Palantir-style polymorphism for ODA.

    Attributes:
        interface_id: Unique interface identifier (e.g., 'IVersionable')
        description: Human-readable description
        required_properties: List of properties that implementers must have
        required_methods: List of methods that implementers must have
        extends: List of parent interface IDs (for interface inheritance)
        is_abstract: Whether this interface can be directly implemented

    Example:
        ```python
        IVersionable = InterfaceDefinition(
            interface_id="IVersionable",
            description="Objects that support versioning",
            required_properties=[
                PropertySpec(name="version", type_hint="int"),
            ],
            required_methods=[
                MethodSpec(name="bump_version", signature="(self) -> int"),
            ],
        )
        ```
    """

    interface_id: str = Field(
        ...,
        description="Unique interface identifier (e.g., 'IVersionable')",
        min_length=1,
    )
    description: str = Field(
        ...,
        description="Human-readable description of the interface",
    )
    required_properties: List[PropertySpec] = Field(
        default_factory=list,
        description="List of properties that implementers must have",
    )
    required_methods: List[MethodSpec] = Field(
        default_factory=list,
        description="List of methods that implementers must have",
    )
    extends: Optional[List[str]] = Field(
        default=None,
        description="List of parent interface IDs for inheritance",
    )
    is_abstract: bool = Field(
        default=False,
        description="Whether this interface can be directly implemented",
    )

    @field_validator("interface_id")
    @classmethod
    def validate_interface_id(cls, v: str) -> str:
        """
        Validate interface ID format.
        Convention: PascalCase starting with 'I' (e.g., IVersionable, IAuditable)
        """
        # Allow flexibility but warn on non-standard naming
        if not re.match(r"^I[A-Z][a-zA-Z0-9]*$", v):
            # Still allow it but it's not following convention
            pass
        return v

    @model_validator(mode="after")
    def validate_extends_not_self(self) -> "InterfaceDefinition":
        """Ensure interface doesn't extend itself."""
        if self.extends and self.interface_id in self.extends:
            raise ValueError(f"Interface '{self.interface_id}' cannot extend itself")
        return self

    def get_all_property_names(self) -> List[str]:
        """Get all required property names."""
        return [prop.name for prop in self.required_properties]

    def get_all_method_names(self) -> List[str]:
        """Get all required method names."""
        return [method.name for method in self.required_methods]

    def get_property_spec(self, name: str) -> Optional[PropertySpec]:
        """Get property specification by name."""
        for prop in self.required_properties:
            if prop.name == name:
                return prop
        return None

    def get_method_spec(self, name: str) -> Optional[MethodSpec]:
        """Get method specification by name."""
        for method in self.required_methods:
            if method.name == name:
                return method
        return None


# =============================================================================
# INTERFACE VALIDATION RESULT
# =============================================================================


class InterfaceValidationError(BaseModel):
    """
    Represents a single validation error when checking interface implementation.

    Attributes:
        error_type: Type of error (missing_property, missing_method, type_mismatch)
        interface_id: The interface being validated against
        detail: Human-readable error description
        property_name: Property name (if property-related error)
        method_name: Method name (if method-related error)
        expected: Expected value/type
        actual: Actual value/type found
    """

    error_type: str = Field(
        ...,
        description="Type of validation error",
    )
    interface_id: str = Field(
        ...,
        description="Interface being validated against",
    )
    detail: str = Field(
        ...,
        description="Human-readable error description",
    )
    property_name: Optional[str] = Field(
        default=None,
        description="Property name if property-related error",
    )
    method_name: Optional[str] = Field(
        default=None,
        description="Method name if method-related error",
    )
    expected: Optional[str] = Field(
        default=None,
        description="Expected value or type",
    )
    actual: Optional[str] = Field(
        default=None,
        description="Actual value or type found",
    )


class InterfaceValidationResult(BaseModel):
    """
    Result of validating an ObjectType against an interface.

    Attributes:
        is_valid: Whether the ObjectType implements the interface correctly
        object_type: Name of the ObjectType being validated
        interface_id: ID of the interface being validated against
        errors: List of validation errors (empty if is_valid is True)
        warnings: List of non-fatal warnings
    """

    is_valid: bool = Field(
        ...,
        description="Whether validation passed",
    )
    object_type: str = Field(
        ...,
        description="ObjectType being validated",
    )
    interface_id: str = Field(
        ...,
        description="Interface being validated against",
    )
    errors: List[InterfaceValidationError] = Field(
        default_factory=list,
        description="List of validation errors",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of non-fatal warnings",
    )

    @classmethod
    def success(cls, object_type: str, interface_id: str) -> "InterfaceValidationResult":
        """Create a successful validation result."""
        return cls(
            is_valid=True,
            object_type=object_type,
            interface_id=interface_id,
        )

    @classmethod
    def failure(
        cls,
        object_type: str,
        interface_id: str,
        errors: List[InterfaceValidationError],
    ) -> "InterfaceValidationResult":
        """Create a failed validation result."""
        return cls(
            is_valid=False,
            object_type=object_type,
            interface_id=interface_id,
            errors=errors,
        )


# =============================================================================
# IMPLEMENTATION METADATA
# =============================================================================


class InterfaceImplementation(BaseModel):
    """
    Tracks that an ObjectType implements a specific interface.

    Attributes:
        object_type: Name of the implementing ObjectType
        interface_id: ID of the implemented interface
        validated_at: Timestamp when implementation was validated
        validation_result: Result of the validation
    """

    object_type: str = Field(
        ...,
        description="Name of the implementing ObjectType",
    )
    interface_id: str = Field(
        ...,
        description="ID of the implemented interface",
    )
    validated_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when implementation was validated",
    )
    validation_result: Optional[InterfaceValidationResult] = Field(
        default=None,
        description="Result of the validation",
    )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Core types
    "PropertySpec",
    "MethodSpec",
    "InterfaceDefinition",
    # Validation
    "InterfaceValidationError",
    "InterfaceValidationResult",
    # Implementation tracking
    "InterfaceImplementation",
]
