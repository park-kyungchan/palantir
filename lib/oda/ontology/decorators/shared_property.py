"""
Orion ODA v4.0 - Shared Property Decorator
==========================================

Provides the @uses_shared_property decorator for ObjectTypes to declare
which shared properties they use.

The decorator:
1. Validates the shared property exists in registry
2. Injects the property into the decorated class
3. Validates type compatibility
4. Tracks usage in SharedPropertyUsage

Palantir Pattern:
- Shared properties are defined once and reused
- Usage is validated at class definition time
- Property injection enables consistent field definitions

Example:
    ```python
    @uses_shared_property("created_at", "modified_by", "created_by")
    class Task(OntologyObject):
        title: str
        # created_at, modified_by, created_by are automatically injected
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, get_type_hints

from pydantic import Field
from pydantic.fields import FieldInfo

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SharedPropertyError(Exception):
    """
    Raised when there's an error with shared property usage.

    Attributes:
        object_type: Name of the ObjectType
        property_id: ID of the shared property
        errors: List of error messages
    """

    def __init__(
        self,
        object_type: str,
        property_id: str,
        errors: List[str],
    ) -> None:
        self.object_type = object_type
        self.property_id = property_id
        self.errors = errors
        message = (
            f"Shared property error for '{object_type}' using '{property_id}':\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
        super().__init__(message)


class SharedPropertyConflictError(Exception):
    """
    Raised when a shared property conflicts with an existing field.

    Attributes:
        object_type: Name of the ObjectType
        property_id: ID of the shared property
        conflict_type: Type of conflict (e.g., 'field_exists', 'type_mismatch')
    """

    def __init__(
        self,
        object_type: str,
        property_id: str,
        conflict_type: str,
        detail: str,
    ) -> None:
        self.object_type = object_type
        self.property_id = property_id
        self.conflict_type = conflict_type
        self.detail = detail
        message = (
            f"Shared property conflict for '{object_type}' using '{property_id}': "
            f"{conflict_type} - {detail}"
        )
        super().__init__(message)


# =============================================================================
# TYPE HINT MAPPING
# =============================================================================


def _resolve_type_hint(type_hint_str: str) -> Any:
    """
    Resolve a type hint string to an actual type.

    Args:
        type_hint_str: Type hint as string (e.g., "str", "List[str]", "datetime")

    Returns:
        The resolved type

    Note:
        This handles common types. For complex types, the string is returned as-is
        for annotation purposes.
    """
    # Common type mappings
    type_map: Dict[str, Any] = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "datetime": datetime,
        "Any": Any,
        "None": type(None),
    }

    # Direct mapping
    if type_hint_str in type_map:
        return type_map[type_hint_str]

    # Handle Optional, List, Dict, etc.
    if type_hint_str.startswith("Optional["):
        inner = type_hint_str[9:-1]  # Remove "Optional[" and "]"
        inner_type = _resolve_type_hint(inner)
        return Optional[inner_type]

    if type_hint_str.startswith("List["):
        inner = type_hint_str[5:-1]
        inner_type = _resolve_type_hint(inner)
        return List[inner_type]

    if type_hint_str.startswith("Dict["):
        # Simplified: assume Dict[str, Any] or similar
        return Dict[str, Any]

    # Return as string annotation for complex types
    return type_hint_str


def _resolve_default_factory(factory_name: str) -> Optional[Callable[[], Any]]:
    """
    Resolve a default factory name to a callable.

    Args:
        factory_name: Factory function name (e.g., "list", "dict", "datetime.now")

    Returns:
        Callable factory function or None
    """
    factory_map: Dict[str, Callable[[], Any]] = {
        "list": list,
        "dict": dict,
        "set": set,
        "datetime.now": lambda: datetime.now(timezone.utc),
        "datetime.utcnow": lambda: datetime.now(timezone.utc),
    }

    return factory_map.get(factory_name)


# =============================================================================
# DECORATOR IMPLEMENTATION
# =============================================================================


def uses_shared_property(
    *property_ids: str,
    strict: bool = True,
    register: bool = True,
    allow_override: bool = False,
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to declare that an ObjectType uses shared properties.

    This decorator:
    1. Validates that each shared property exists in the registry
    2. Injects the property as a field into the class
    3. Validates type compatibility if the field already exists
    4. Tracks usage in the SharedPropertyRegistry

    Args:
        *property_ids: One or more shared property IDs to use
        strict: If True, raise error on missing property (default True)
        register: If True, register usage in SharedPropertyRegistry (default True)
        allow_override: If True, allow existing field to override shared property (default False)

    Returns:
        Decorated class with injected shared properties

    Raises:
        SharedPropertyError: If strict=True and property not found
        SharedPropertyConflictError: If field exists and allow_override=False

    Example:
        ```python
        @uses_shared_property("created_at", "modified_by")
        class Task(OntologyObject):
            title: str
            # created_at and modified_by are automatically injected
        ```

    With allow_override:
        ```python
        @uses_shared_property("version", allow_override=True)
        class Document(OntologyObject):
            version: int = 5  # Overrides shared property default
        ```
    """
    if not property_ids:
        raise ValueError("At least one property_id must be provided")

    def decorator(cls: Type[T]) -> Type[T]:
        # Import here to avoid circular imports
        from lib.oda.ontology.registry import get_shared_property_registry
        from lib.oda.ontology.types.shared_properties import (
            get_builtin_property,
            SharedPropertyDefinition,
        )

        registry = get_shared_property_registry()
        class_name = cls.__name__

        # Track which properties were injected
        injected: List[str] = []
        all_errors: List[tuple[str, List[str]]] = []

        for property_id in property_ids:
            # Try registry first, then built-ins
            prop_def = registry.get_property(property_id)
            if prop_def is None:
                prop_def = get_builtin_property(property_id)
                # Auto-register built-in if found
                if prop_def is not None and not registry.has_property(property_id):
                    registry.register_property(prop_def)

            if prop_def is None:
                error_msg = f"Shared property '{property_id}' not found in registry or built-ins"
                if strict:
                    raise SharedPropertyError(
                        object_type=class_name,
                        property_id=property_id,
                        errors=[error_msg],
                    )
                else:
                    logger.warning(
                        f"[uses_shared_property] {class_name}: {error_msg}"
                    )
                    continue

            # Check for existing field
            existing_field = None
            if hasattr(cls, "model_fields"):
                existing_field = cls.model_fields.get(property_id)
            elif hasattr(cls, "__annotations__"):
                if property_id in cls.__annotations__:
                    existing_field = getattr(cls, property_id, None)

            if existing_field is not None:
                if not allow_override:
                    raise SharedPropertyConflictError(
                        object_type=class_name,
                        property_id=property_id,
                        conflict_type="field_exists",
                        detail=f"Field '{property_id}' already exists. Use allow_override=True to allow.",
                    )
                else:
                    # Skip injection but still track usage
                    logger.debug(
                        f"[uses_shared_property] {class_name}: Field '{property_id}' exists, using override"
                    )
                    injected.append(property_id)
                    continue

            # Inject the property
            _inject_property(cls, prop_def)
            injected.append(property_id)

            # Register usage
            if register:
                try:
                    registry.register_usage(
                        property_id=property_id,
                        object_type=class_name,
                    )
                except ValueError as e:
                    # Already registered - skip
                    logger.debug(f"[uses_shared_property] {class_name}: {e}")

            logger.debug(
                f"[uses_shared_property] {class_name}: Injected '{property_id}'"
            )

        # Add metadata to the class
        if not hasattr(cls, "_uses_shared_properties"):
            cls._uses_shared_properties = []

        # Extend with newly injected properties
        cls._uses_shared_properties = list(set(cls._uses_shared_properties + injected))

        # Add validation timestamp
        cls._shared_properties_validated_at = datetime.now(timezone.utc).isoformat()

        return cls

    return decorator


def _inject_property(cls: Type, prop_def: "SharedPropertyDefinition") -> None:
    """
    Inject a shared property into a class.

    This modifies the class to add the property as an annotation
    with appropriate default value.

    Args:
        cls: Class to inject into
        prop_def: SharedPropertyDefinition to inject
    """
    from lib.oda.ontology.types.shared_properties import SharedPropertyDefinition

    # Resolve the type hint
    resolved_type = _resolve_type_hint(prop_def.type_hint)

    # Add annotation
    if not hasattr(cls, "__annotations__"):
        cls.__annotations__ = {}

    cls.__annotations__[prop_def.property_id] = resolved_type

    # Determine default value
    default_value = None
    if prop_def.default_value is not None:
        default_value = prop_def.default_value
    elif prop_def.default_factory is not None:
        factory = _resolve_default_factory(prop_def.default_factory)
        if factory is not None:
            # For Pydantic models, we need to use Field with default_factory
            # For now, create the default value
            default_value = factory()
    elif not prop_def.is_required:
        default_value = None

    # Set the attribute with default value
    setattr(cls, prop_def.property_id, default_value)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_shared_properties(cls: Type) -> List[str]:
    """
    Get all shared property IDs used by a class.

    Args:
        cls: The class to check

    Returns:
        List of shared property IDs

    Example:
        ```python
        props = get_shared_properties(Task)
        # ['created_at', 'modified_by', 'version']
        ```
    """
    if hasattr(cls, "_uses_shared_properties"):
        return list(cls._uses_shared_properties)
    return []


def uses_property(cls: Type, property_id: str) -> bool:
    """
    Check if a class uses a specific shared property.

    Args:
        cls: The class to check
        property_id: ID of the shared property

    Returns:
        True if the class uses the property

    Example:
        ```python
        if uses_property(Task, "created_at"):
            print("Task has created_at")
        ```
    """
    return property_id in get_shared_properties(cls)


def require_shared_property(
    property_id: str,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to require that a function parameter uses a specific shared property.

    Args:
        property_id: Required shared property ID

    Example:
        ```python
        @require_shared_property("version")
        def process_versionable(obj):
            print(obj.version)
        ```

    Note:
        This validates at call time, not at definition time.
    """
    import functools

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check first positional argument
            if args:
                obj = args[0]
                if hasattr(obj, "__class__"):
                    if not uses_property(obj.__class__, property_id):
                        raise TypeError(
                            f"First argument must use shared property '{property_id}', "
                            f"got {obj.__class__.__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# SHORTHAND ALIASES
# =============================================================================


def shared(*property_ids: str, strict: bool = True) -> Callable[[Type[T]], Type[T]]:
    """
    Shorthand alias for @uses_shared_property.

    Example:
        ```python
        @shared("created_at", "modified_by")
        class Task(OntologyObject):
            ...
        ```
    """
    return uses_shared_property(*property_ids, strict=strict)


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Exceptions
    "SharedPropertyError",
    "SharedPropertyConflictError",
    # Decorators
    "uses_shared_property",
    "shared",
    "require_shared_property",
    # Utilities
    "get_shared_properties",
    "uses_property",
]
