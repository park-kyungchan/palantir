"""
Orion ODA v4.0 - Backward Compatibility Layer
==============================================

Provides backward compatibility support for ObjectType evolution:
- PropertyMapping: Map old property names to new ones
- TypeCoercion: Convert between property types
- DeprecatedProperty: Handle deprecated properties

Features:
- Transparent property renames
- Automatic type conversions
- Deprecation warnings
- Multi-version compatibility

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
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

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.versioning.schema import SchemaVersion, parse_version

logger = logging.getLogger(__name__)


# =============================================================================
# COMPATIBILITY TYPES
# =============================================================================


class DeprecationLevel(str, Enum):
    """Level of deprecation."""

    WARNING = "warning"  # Log warning but continue
    ERROR = "error"  # Raise exception
    SILENT = "silent"  # Silently handle


class CoercionType(str, Enum):
    """Type of value coercion."""

    CAST = "cast"  # Simple type cast
    TRANSFORM = "transform"  # Custom transformation
    DEFAULT = "default"  # Use default value


# =============================================================================
# PROPERTY MAPPING
# =============================================================================


@dataclass
class PropertyMapping:
    """
    Maps an old property name to a new one.

    Supports:
    - Simple rename
    - Value transformation
    - Multi-property merge

    Example:
        ```python
        # Simple rename
        PropertyMapping(
            old_name="user_id",
            new_name="assigned_to_id",
        )

        # With transformation
        PropertyMapping(
            old_name="priority_level",
            new_name="priority",
            transform=lambda v: {"1": "low", "2": "medium", "3": "high"}[v],
        )
        ```
    """

    old_name: str
    new_name: str
    transform: Optional[Callable[[Any], Any]] = None
    bidirectional: bool = True
    version_introduced: Optional[str] = None
    version_removed: Optional[str] = None

    def apply_forward(self, value: Any) -> Any:
        """Apply mapping in forward direction (old -> new)."""
        if self.transform:
            return self.transform(value)
        return value

    def apply_backward(self, value: Any) -> Any:
        """Apply mapping in backward direction (new -> old)."""
        if not self.bidirectional:
            raise ValueError(f"Mapping {self.old_name} -> {self.new_name} is not bidirectional")
        # For bidirectional, assume identity (or implement reverse transform)
        return value

    def is_active_for_version(self, version: Union[str, SchemaVersion]) -> bool:
        """Check if this mapping applies to a version."""
        if isinstance(version, str):
            version = parse_version(version)

        if self.version_introduced:
            introduced = parse_version(self.version_introduced)
            if version < introduced:
                return False

        if self.version_removed:
            removed = parse_version(self.version_removed)
            if version >= removed:
                return False

        return True


@dataclass
class TypeCoercion:
    """
    Handles type conversions between versions.

    Example:
        ```python
        # String to int
        TypeCoercion(
            property_name="count",
            from_type=str,
            to_type=int,
            coerce=lambda v: int(v) if v else 0,
        )

        # Enum change
        TypeCoercion(
            property_name="status",
            from_type=str,
            to_type=StatusEnum,
            coerce=lambda v: StatusEnum(v),
        )
        ```
    """

    property_name: str
    from_type: Type
    to_type: Type
    coerce: Callable[[Any], Any]
    coercion_type: CoercionType = CoercionType.TRANSFORM
    version_introduced: Optional[str] = None
    default_value: Any = None

    def apply(self, value: Any) -> Any:
        """Apply the type coercion."""
        if value is None and self.default_value is not None:
            return self.default_value

        if self.coercion_type == CoercionType.CAST:
            return self.to_type(value)
        elif self.coercion_type == CoercionType.DEFAULT:
            return self.default_value
        else:
            return self.coerce(value)


@dataclass
class DeprecatedProperty:
    """
    Represents a deprecated property.

    Example:
        ```python
        DeprecatedProperty(
            name="assignee",
            deprecated_in="2.0.0",
            removed_in="3.0.0",
            replacement="assigned_to_id",
            message="Use 'assigned_to_id' instead of 'assignee'",
        )
        ```
    """

    name: str
    deprecated_in: str
    removed_in: Optional[str] = None
    replacement: Optional[str] = None
    message: Optional[str] = None
    level: DeprecationLevel = DeprecationLevel.WARNING
    default_value: Any = None

    def check(self, version: Union[str, SchemaVersion]) -> None:
        """Check if property is deprecated/removed for version."""
        if isinstance(version, str):
            version = parse_version(version)

        deprecated_version = parse_version(self.deprecated_in)

        if self.removed_in:
            removed_version = parse_version(self.removed_in)
            if version >= removed_version:
                if self.level == DeprecationLevel.ERROR:
                    raise ValueError(
                        f"Property '{self.name}' was removed in version {self.removed_in}. "
                        f"{self.message or ''}"
                    )
                logger.warning(
                    f"Property '{self.name}' was removed in {self.removed_in}. "
                    f"{self.message or ''}"
                )
                return

        if version >= deprecated_version:
            msg = (
                f"Property '{self.name}' is deprecated since version {self.deprecated_in}. "
                f"{self.message or ''}"
            )
            if self.replacement:
                msg += f" Use '{self.replacement}' instead."

            if self.level == DeprecationLevel.WARNING:
                warnings.warn(msg, DeprecationWarning, stacklevel=3)
            elif self.level == DeprecationLevel.ERROR:
                raise DeprecationWarning(msg)
            # SILENT: do nothing

    @property
    def is_removed(self) -> bool:
        """Check if property has been removed."""
        return self.removed_in is not None


# =============================================================================
# COMPATIBILITY LAYER
# =============================================================================


class ObjectTypeCompatibility(BaseModel):
    """
    Compatibility definition for an ObjectType.

    Defines how to handle data from different versions.
    """

    object_type: str
    current_version: str
    property_mappings: List[PropertyMapping] = Field(default_factory=list)
    type_coercions: List[TypeCoercion] = Field(default_factory=list)
    deprecated_properties: List[DeprecatedProperty] = Field(default_factory=list)
    min_supported_version: str = "1.0.0"

    model_config = {"arbitrary_types_allowed": True}

    def get_mapping_for(self, old_name: str) -> Optional[PropertyMapping]:
        """Get property mapping for an old property name."""
        for mapping in self.property_mappings:
            if mapping.old_name == old_name:
                return mapping
        return None

    def get_coercion_for(self, property_name: str) -> Optional[TypeCoercion]:
        """Get type coercion for a property."""
        for coercion in self.type_coercions:
            if coercion.property_name == property_name:
                return coercion
        return None

    def get_deprecation_for(self, property_name: str) -> Optional[DeprecatedProperty]:
        """Get deprecation info for a property."""
        for deprecated in self.deprecated_properties:
            if deprecated.name == property_name:
                return deprecated
        return None


class CompatibilityLayer:
    """
    Central compatibility layer for handling ObjectType evolution.

    Features:
    - Property rename handling
    - Type coercion
    - Deprecation warnings
    - Multi-version support

    Usage:
        ```python
        layer = get_compat_layer()

        # Register compatibility rules
        layer.register_mapping(
            "Task",
            PropertyMapping("user_id", "assigned_to_id"),
        )

        # Transform data
        data = layer.transform(
            "Task",
            old_data,
            from_version="1.0.0",
            to_version="2.0.0",
        )
        ```
    """

    _instance: Optional[CompatibilityLayer] = None

    def __init__(self) -> None:
        # object_type -> ObjectTypeCompatibility
        self._compatibilities: Dict[str, ObjectTypeCompatibility] = {}
        # object_type -> set of aliases
        self._type_aliases: Dict[str, Set[str]] = {}

    @classmethod
    def get_instance(cls) -> CompatibilityLayer:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.debug("CompatibilityLayer singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    def register_object_type(
        self,
        object_type: str,
        current_version: str,
        min_supported_version: str = "1.0.0",
    ) -> ObjectTypeCompatibility:
        """
        Register an ObjectType for compatibility handling.

        Args:
            object_type: Name of the ObjectType
            current_version: Current schema version
            min_supported_version: Minimum supported version

        Returns:
            ObjectTypeCompatibility instance
        """
        compat = ObjectTypeCompatibility(
            object_type=object_type,
            current_version=current_version,
            min_supported_version=min_supported_version,
        )
        self._compatibilities[object_type] = compat
        return compat

    def get_compatibility(self, object_type: str) -> Optional[ObjectTypeCompatibility]:
        """Get compatibility definition for an ObjectType."""
        return self._compatibilities.get(object_type)

    def register_mapping(
        self,
        object_type: str,
        mapping: PropertyMapping,
    ) -> None:
        """
        Register a property mapping.

        Args:
            object_type: ObjectType name
            mapping: PropertyMapping to register
        """
        if object_type not in self._compatibilities:
            self.register_object_type(object_type, "1.0.0")

        self._compatibilities[object_type].property_mappings.append(mapping)
        logger.debug(
            f"Registered mapping for {object_type}: "
            f"{mapping.old_name} -> {mapping.new_name}"
        )

    def register_coercion(
        self,
        object_type: str,
        coercion: TypeCoercion,
    ) -> None:
        """
        Register a type coercion.

        Args:
            object_type: ObjectType name
            coercion: TypeCoercion to register
        """
        if object_type not in self._compatibilities:
            self.register_object_type(object_type, "1.0.0")

        self._compatibilities[object_type].type_coercions.append(coercion)
        logger.debug(
            f"Registered coercion for {object_type}.{coercion.property_name}: "
            f"{coercion.from_type.__name__} -> {coercion.to_type.__name__}"
        )

    def register_deprecation(
        self,
        object_type: str,
        deprecation: DeprecatedProperty,
    ) -> None:
        """
        Register a deprecated property.

        Args:
            object_type: ObjectType name
            deprecation: DeprecatedProperty to register
        """
        if object_type not in self._compatibilities:
            self.register_object_type(object_type, "1.0.0")

        self._compatibilities[object_type].deprecated_properties.append(deprecation)
        logger.debug(
            f"Registered deprecation for {object_type}.{deprecation.name} "
            f"(deprecated in {deprecation.deprecated_in})"
        )

    def register_type_alias(
        self,
        object_type: str,
        alias: str,
    ) -> None:
        """
        Register an alias for an ObjectType.

        Useful when ObjectTypes are renamed.

        Args:
            object_type: Current ObjectType name
            alias: Old name (alias)
        """
        if object_type not in self._type_aliases:
            self._type_aliases[object_type] = set()
        self._type_aliases[object_type].add(alias)
        logger.debug(f"Registered type alias: {alias} -> {object_type}")

    def resolve_type_alias(self, type_name: str) -> str:
        """
        Resolve a type alias to the current type name.

        Args:
            type_name: Type name (possibly an alias)

        Returns:
            Current type name
        """
        for current, aliases in self._type_aliases.items():
            if type_name in aliases:
                return current
        return type_name

    def transform(
        self,
        object_type: str,
        data: Dict[str, Any],
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        check_deprecations: bool = True,
    ) -> Dict[str, Any]:
        """
        Transform data for compatibility.

        Applies:
        1. Property mappings (renames)
        2. Type coercions
        3. Deprecation checks

        Args:
            object_type: ObjectType name
            data: Data to transform
            from_version: Source version (for filtering rules)
            to_version: Target version
            check_deprecations: Whether to check for deprecated properties

        Returns:
            Transformed data
        """
        # Resolve any type alias
        object_type = self.resolve_type_alias(object_type)

        compat = self.get_compatibility(object_type)
        if not compat:
            return data

        target_version = to_version or compat.current_version
        source_version = from_version

        result = dict(data)

        # Apply property mappings
        for mapping in compat.property_mappings:
            if source_version and not mapping.is_active_for_version(source_version):
                continue

            if mapping.old_name in result:
                old_value = result.pop(mapping.old_name)
                new_value = mapping.apply_forward(old_value)
                result[mapping.new_name] = new_value
                logger.debug(
                    f"Applied mapping: {mapping.old_name} -> {mapping.new_name}"
                )

        # Apply type coercions
        for coercion in compat.type_coercions:
            if coercion.property_name in result:
                old_value = result[coercion.property_name]
                try:
                    new_value = coercion.apply(old_value)
                    result[coercion.property_name] = new_value
                    logger.debug(
                        f"Applied coercion for {coercion.property_name}: "
                        f"{type(old_value).__name__} -> {type(new_value).__name__}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Coercion failed for {coercion.property_name}: {e}"
                    )

        # Check deprecations
        if check_deprecations:
            for deprecated in compat.deprecated_properties:
                if deprecated.name in result:
                    deprecated.check(parse_version(target_version))

                    # Apply replacement if available
                    if deprecated.replacement and deprecated.replacement not in result:
                        result[deprecated.replacement] = result[deprecated.name]

        return result

    def validate_version(
        self,
        object_type: str,
        version: Union[str, SchemaVersion],
    ) -> bool:
        """
        Check if a version is supported.

        Args:
            object_type: ObjectType name
            version: Version to check

        Returns:
            True if version is supported
        """
        if isinstance(version, str):
            version = parse_version(version)

        compat = self.get_compatibility(object_type)
        if not compat:
            return True  # No compat rules = all versions supported

        min_version = parse_version(compat.min_supported_version)
        return version >= min_version

    def get_deprecated_properties(
        self,
        object_type: str,
        version: Optional[str] = None,
    ) -> List[DeprecatedProperty]:
        """
        Get deprecated properties for an ObjectType.

        Args:
            object_type: ObjectType name
            version: Optional version to filter by

        Returns:
            List of deprecated properties
        """
        compat = self.get_compatibility(object_type)
        if not compat:
            return []

        if version:
            v = parse_version(version)
            return [
                d for d in compat.deprecated_properties
                if parse_version(d.deprecated_in) <= v
            ]

        return list(compat.deprecated_properties)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def get_compat_layer() -> CompatibilityLayer:
    """Get the global CompatibilityLayer instance."""
    return CompatibilityLayer.get_instance()


# =============================================================================
# DECORATORS
# =============================================================================


def deprecated_property(
    deprecated_in: str,
    removed_in: Optional[str] = None,
    replacement: Optional[str] = None,
    message: Optional[str] = None,
) -> Callable:
    """
    Decorator to mark a property as deprecated.

    Example:
        ```python
        class Task(OntologyObject):
            @deprecated_property("2.0.0", replacement="assigned_to_id")
            @property
            def assignee(self) -> Optional[str]:
                return self.assigned_to_id
        ```
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(self: Any) -> Any:
            warnings.warn(
                f"Property '{func.__name__}' is deprecated since {deprecated_in}. "
                f"{message or ''}"
                f"{f' Use {replacement} instead.' if replacement else ''}",
                DeprecationWarning,
                stacklevel=2,
            )
            return func(self)

        # Preserve property behavior
        if isinstance(func, property):
            return property(wrapper)
        return wrapper

    return decorator
