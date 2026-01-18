"""
Orion ODA v4.0 - Shared Property Definitions
=============================================

Provides Palantir-style Shared Properties that can be reused across multiple ObjectTypes.

Shared properties enable:
- Consistent property definitions across ObjectTypes
- Audit properties (created_at, modified_by) shared by all auditable objects
- Tracking properties (version, last_sync) shared by versionable objects
- Reduced duplication and improved consistency

Palantir Pattern:
- Similar to Palantir's "shared property types"
- Properties are defined once and reused across ObjectTypes
- Usage is tracked for dependency analysis
- Type compatibility is validated at decoration time

Example:
    ```python
    # Register a shared property
    created_at = register_shared_property(SharedPropertyDefinition(
        property_id="created_at",
        description="Timestamp when the object was created",
        type_hint="datetime",
        category="audit",
        is_indexed=True,
    ))

    # Use the shared property
    @uses_shared_property("created_at", "modified_by")
    class Task(OntologyObject):
        title: str
        # created_at and modified_by are automatically injected
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Type

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# SHARED PROPERTY DEFINITION
# =============================================================================


class SharedPropertyDefinition(BaseModel):
    """
    Definition for a shared property that can be reused across ObjectTypes.

    Attributes:
        property_id: Unique identifier (e.g., "created_at", "modified_by")
        description: Human-readable description
        type_hint: Python type hint as string (e.g., "datetime", "str", "int")
        default_value: Optional default value for the property
        default_factory: Optional factory function name for default value
        validators: List of validator function references
        is_required: Whether the property must have a value (default False)
        is_indexed: Whether the property should be indexed for queries (default False)
        category: Property category for organization (e.g., "audit", "metadata", "tracking")
        metadata: Additional metadata for the property

    Example:
        ```python
        SharedPropertyDefinition(
            property_id="created_at",
            description="Timestamp when the object was created",
            type_hint="datetime",
            default_factory="datetime.now",
            category="audit",
            is_indexed=True,
        )
        ```
    """

    property_id: str = Field(
        ...,
        description="Unique property identifier (e.g., 'created_at')",
        min_length=1,
        pattern=r"^[a-z_][a-z0-9_]*$",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the property",
    )
    type_hint: str = Field(
        ...,
        description="Python type hint as string (e.g., 'datetime', 'str', 'List[str]')",
    )
    default_value: Optional[Any] = Field(
        default=None,
        description="Default value for the property",
    )
    default_factory: Optional[str] = Field(
        default=None,
        description="Factory function name for default value (e.g., 'list', 'dict', 'datetime.now')",
    )
    validators: List[str] = Field(
        default_factory=list,
        description="List of validator function references",
    )
    is_required: bool = Field(
        default=False,
        description="Whether the property must have a value",
    )
    is_indexed: bool = Field(
        default=False,
        description="Whether the property should be indexed for query optimization",
    )
    category: str = Field(
        default="general",
        description="Property category (e.g., 'audit', 'metadata', 'tracking')",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the property",
    )

    @field_validator("property_id")
    @classmethod
    def validate_property_id(cls, v: str) -> str:
        """Ensure property ID follows Python naming conventions."""
        if v.startswith("__"):
            raise ValueError("Property ID cannot start with double underscore")
        if v in ("class", "self", "cls", "return", "def", "import", "from"):
            raise ValueError(f"Property ID cannot be a reserved keyword: {v}")
        return v

    @field_validator("type_hint")
    @classmethod
    def validate_type_hint(cls, v: str) -> str:
        """Validate type hint is non-empty."""
        if not v.strip():
            raise ValueError("Type hint cannot be empty")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Normalize category to lowercase."""
        return v.lower()

    @model_validator(mode="after")
    def validate_default_consistency(self) -> "SharedPropertyDefinition":
        """Ensure default_value and default_factory are not both set."""
        if self.default_value is not None and self.default_factory is not None:
            raise ValueError(
                "Cannot specify both default_value and default_factory"
            )
        return self

    def get_pydantic_field_info(self) -> Dict[str, Any]:
        """
        Get Pydantic Field() parameters for this shared property.

        Returns:
            Dictionary of Field parameters suitable for dynamic field creation
        """
        field_params: Dict[str, Any] = {
            "description": self.description,
        }

        if self.default_value is not None:
            field_params["default"] = self.default_value
        elif self.default_factory is not None:
            # Note: actual factory function needs to be resolved by caller
            field_params["default_factory_name"] = self.default_factory
        elif not self.is_required:
            field_params["default"] = None

        return field_params


# =============================================================================
# SHARED PROPERTY USAGE
# =============================================================================


class SharedPropertyUsage(BaseModel):
    """
    Tracks which ObjectTypes use which shared properties.

    Attributes:
        property_id: ID of the shared property
        object_type: Name of the ObjectType using this property
        registered_at: Timestamp when the usage was registered
        field_alias: Optional alias used in the ObjectType (if different from property_id)
        override_default: Optional override for the default value
        is_active: Whether this usage is currently active

    Example:
        ```python
        SharedPropertyUsage(
            property_id="created_at",
            object_type="Task",
            registered_at="2024-01-15T10:00:00Z",
        )
        ```
    """

    property_id: str = Field(
        ...,
        description="ID of the shared property",
    )
    object_type: str = Field(
        ...,
        description="Name of the ObjectType using this property",
    )
    registered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when usage was registered",
    )
    field_alias: Optional[str] = Field(
        default=None,
        description="Optional alias used in the ObjectType",
    )
    override_default: Optional[Any] = Field(
        default=None,
        description="Optional override for the default value",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this usage is currently active",
    )


# =============================================================================
# SHARED PROPERTY REGISTRY
# =============================================================================


class SharedPropertyRegistry:
    """
    Registry for Shared Property definitions and their usages.

    Provides:
    - Property registration and lookup
    - Usage tracking across ObjectTypes
    - Category-based property grouping
    - Export capabilities

    Example:
        ```python
        registry = SharedPropertyRegistry()

        # Register a shared property
        registry.register_property(SharedPropertyDefinition(
            property_id="created_at",
            description="Creation timestamp",
            type_hint="datetime",
            category="audit",
        ))

        # Track usage
        registry.register_usage(
            property_id="created_at",
            object_type="Task",
        )

        # Query usages
        usages = registry.get_usages_for_property("created_at")
        # ['Task', 'Document', ...]
        ```
    """

    def __init__(self) -> None:
        self._properties: Dict[str, SharedPropertyDefinition] = {}
        self._usages: List[SharedPropertyUsage] = []
        self._usage_index: Dict[str, Set[str]] = {}  # property_id -> set of object_types
        self._object_properties: Dict[str, Set[str]] = {}  # object_type -> set of property_ids

    def register_property(self, property_def: SharedPropertyDefinition) -> None:
        """
        Register a shared property definition.

        Args:
            property_def: SharedPropertyDefinition to register

        Raises:
            ValueError: If property_id is already registered
        """
        if property_def.property_id in self._properties:
            raise ValueError(
                f"Shared property '{property_def.property_id}' is already registered"
            )

        self._properties[property_def.property_id] = property_def
        self._usage_index[property_def.property_id] = set()

    def get_property(self, property_id: str) -> Optional[SharedPropertyDefinition]:
        """Get a shared property definition by ID."""
        return self._properties.get(property_id)

    def has_property(self, property_id: str) -> bool:
        """Check if a shared property is registered."""
        return property_id in self._properties

    def list_properties(self) -> List[SharedPropertyDefinition]:
        """List all registered shared properties."""
        return list(self._properties.values())

    def list_property_ids(self) -> List[str]:
        """List all registered property IDs."""
        return list(self._properties.keys())

    def list_properties_by_category(self, category: str) -> List[SharedPropertyDefinition]:
        """
        List shared properties in a specific category.

        Args:
            category: Category name (e.g., "audit", "metadata")

        Returns:
            List of SharedPropertyDefinitions in the category
        """
        return [
            prop for prop in self._properties.values()
            if prop.category.lower() == category.lower()
        ]

    def get_categories(self) -> List[str]:
        """Get all unique categories of registered properties."""
        return list(set(prop.category for prop in self._properties.values()))

    # =========================================================================
    # USAGE TRACKING
    # =========================================================================

    def register_usage(
        self,
        property_id: str,
        object_type: str,
        field_alias: Optional[str] = None,
        override_default: Optional[Any] = None,
    ) -> SharedPropertyUsage:
        """
        Register that an ObjectType uses a shared property.

        Args:
            property_id: ID of the shared property
            object_type: Name of the ObjectType
            field_alias: Optional alias for the field in the ObjectType
            override_default: Optional override for the default value

        Returns:
            SharedPropertyUsage record

        Raises:
            ValueError: If property is not registered
            ValueError: If usage is already registered for this ObjectType
        """
        if property_id not in self._properties:
            raise ValueError(
                f"Shared property '{property_id}' is not registered"
            )

        # Check for duplicate usage
        if object_type in self._usage_index.get(property_id, set()):
            raise ValueError(
                f"ObjectType '{object_type}' already uses property '{property_id}'"
            )

        usage = SharedPropertyUsage(
            property_id=property_id,
            object_type=object_type,
            field_alias=field_alias,
            override_default=override_default,
        )

        self._usages.append(usage)
        self._usage_index[property_id].add(object_type)

        if object_type not in self._object_properties:
            self._object_properties[object_type] = set()
        self._object_properties[object_type].add(property_id)

        return usage

    def get_usages_for_property(self, property_id: str) -> List[str]:
        """
        Get all ObjectType names that use a shared property.

        Args:
            property_id: ID of the shared property

        Returns:
            List of ObjectType names
        """
        return list(self._usage_index.get(property_id, set()))

    def get_properties_for_object(self, object_type: str) -> List[str]:
        """
        Get all shared property IDs used by an ObjectType.

        Args:
            object_type: Name of the ObjectType

        Returns:
            List of property IDs
        """
        return list(self._object_properties.get(object_type, set()))

    def get_usage(
        self,
        property_id: str,
        object_type: str,
    ) -> Optional[SharedPropertyUsage]:
        """
        Get the usage record for a specific property-ObjectType pair.

        Args:
            property_id: ID of the shared property
            object_type: Name of the ObjectType

        Returns:
            SharedPropertyUsage or None if not found
        """
        for usage in self._usages:
            if usage.property_id == property_id and usage.object_type == object_type:
                return usage
        return None

    def get_all_usages(self) -> List[SharedPropertyUsage]:
        """Get all usage records."""
        return list(self._usages)

    def is_property_used(self, property_id: str) -> bool:
        """Check if a shared property is used by any ObjectType."""
        return len(self._usage_index.get(property_id, set())) > 0

    def count_usages(self, property_id: str) -> int:
        """Count how many ObjectTypes use a shared property."""
        return len(self._usage_index.get(property_id, set()))

    # =========================================================================
    # EXPORT
    # =========================================================================

    def export_dict(self) -> Dict[str, Any]:
        """
        Export registry to dictionary format.

        Returns:
            Dictionary containing all properties and usages
        """
        return {
            "properties": {
                prop_id: {
                    "description": prop.description,
                    "type_hint": prop.type_hint,
                    "default_value": prop.default_value,
                    "default_factory": prop.default_factory,
                    "validators": prop.validators,
                    "is_required": prop.is_required,
                    "is_indexed": prop.is_indexed,
                    "category": prop.category,
                    "metadata": prop.metadata,
                    "usages": self.get_usages_for_property(prop_id),
                }
                for prop_id, prop in sorted(self._properties.items())
            },
            "statistics": {
                "total_properties": len(self._properties),
                "total_usages": len(self._usages),
                "by_category": {
                    cat: len(self.list_properties_by_category(cat))
                    for cat in self.get_categories()
                },
            },
        }


# =============================================================================
# BUILT-IN SHARED PROPERTIES
# =============================================================================


# Common audit properties
BUILTIN_AUDIT_PROPERTIES: List[SharedPropertyDefinition] = [
    SharedPropertyDefinition(
        property_id="created_at",
        description="Timestamp when the object was created",
        type_hint="datetime",
        default_factory="datetime.now",
        category="audit",
        is_indexed=True,
    ),
    SharedPropertyDefinition(
        property_id="updated_at",
        description="Timestamp when the object was last updated",
        type_hint="datetime",
        default_factory="datetime.now",
        category="audit",
        is_indexed=True,
    ),
    SharedPropertyDefinition(
        property_id="created_by",
        description="ID of the user or agent that created the object",
        type_hint="str",
        default_value="system",
        category="audit",
        is_indexed=True,
    ),
    SharedPropertyDefinition(
        property_id="modified_by",
        description="ID of the user or agent that last modified the object",
        type_hint="str",
        default_value="system",
        category="audit",
        is_indexed=True,
    ),
]

# Common versioning properties
BUILTIN_VERSION_PROPERTIES: List[SharedPropertyDefinition] = [
    SharedPropertyDefinition(
        property_id="version",
        description="Version number of the object",
        type_hint="int",
        default_value=1,
        category="versioning",
    ),
    SharedPropertyDefinition(
        property_id="version_history",
        description="List of previous version identifiers",
        type_hint="List[str]",
        default_factory="list",
        category="versioning",
    ),
]

# Common metadata properties
BUILTIN_METADATA_PROPERTIES: List[SharedPropertyDefinition] = [
    SharedPropertyDefinition(
        property_id="tags",
        description="List of tags for categorization",
        type_hint="List[str]",
        default_factory="list",
        category="metadata",
        is_indexed=True,
    ),
    SharedPropertyDefinition(
        property_id="labels",
        description="Key-value labels for the object",
        type_hint="Dict[str, str]",
        default_factory="dict",
        category="metadata",
    ),
    SharedPropertyDefinition(
        property_id="annotations",
        description="Free-form annotations",
        type_hint="Dict[str, Any]",
        default_factory="dict",
        category="metadata",
    ),
]

# All built-in properties
BUILTIN_SHARED_PROPERTIES: List[SharedPropertyDefinition] = (
    BUILTIN_AUDIT_PROPERTIES +
    BUILTIN_VERSION_PROPERTIES +
    BUILTIN_METADATA_PROPERTIES
)


def get_builtin_property(property_id: str) -> Optional[SharedPropertyDefinition]:
    """Get a built-in shared property by ID."""
    for prop in BUILTIN_SHARED_PROPERTIES:
        if prop.property_id == property_id:
            return prop
    return None


def list_builtin_properties() -> List[str]:
    """List all built-in shared property IDs."""
    return [prop.property_id for prop in BUILTIN_SHARED_PROPERTIES]


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Core types
    "SharedPropertyDefinition",
    "SharedPropertyUsage",
    "SharedPropertyRegistry",
    # Built-in properties
    "BUILTIN_AUDIT_PROPERTIES",
    "BUILTIN_VERSION_PROPERTIES",
    "BUILTIN_METADATA_PROPERTIES",
    "BUILTIN_SHARED_PROPERTIES",
    # Utilities
    "get_builtin_property",
    "list_builtin_properties",
]
