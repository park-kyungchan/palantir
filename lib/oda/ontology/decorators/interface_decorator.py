"""
Orion ODA v4.0 - Interface Implementation Decorator
====================================================

Provides the @implements_interface decorator for ObjectTypes to declare
which interfaces they implement.

The decorator:
1. Validates required properties exist
2. Validates required methods exist
3. Registers the implementation in InterfaceRegistry
4. Adds interface metadata to the class

Palantir Pattern:
- Interface compliance is validated at class definition time
- Failures are detected early (import time) not at runtime
- Implementation registration enables interface-based queries

Example:
    ```python
    @implements_interface("IVersionable", "IAuditable")
    class Document(OntologyObject):
        version: int = 1
        created_by: str
        updated_by: str

        def bump_version(self) -> int:
            self.version += 1
            return self.version
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import functools
import logging
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar("T")


class InterfaceImplementationError(Exception):
    """
    Raised when an ObjectType fails to implement a required interface.

    Attributes:
        object_type: Name of the ObjectType
        interface_id: ID of the interface
        errors: List of validation error messages
    """

    def __init__(
        self,
        object_type: str,
        interface_id: str,
        errors: List[str],
    ) -> None:
        self.object_type = object_type
        self.interface_id = interface_id
        self.errors = errors
        message = (
            f"ObjectType '{object_type}' does not implement interface '{interface_id}':\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
        super().__init__(message)


def implements_interface(
    *interface_ids: str,
    strict: bool = True,
    register: bool = True,
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to declare that an ObjectType implements one or more interfaces.

    Args:
        *interface_ids: One or more interface IDs to implement
        strict: If True, raise error on validation failure (default True)
        register: If True, register implementation in InterfaceRegistry (default True)

    Returns:
        Decorated class with interface metadata

    Raises:
        InterfaceImplementationError: If strict=True and validation fails

    Example:
        ```python
        @implements_interface("IVersionable")
        class Document(OntologyObject):
            version: int = 1

            def bump_version(self) -> int:
                self.version += 1
                return self.version
        ```

    Multiple interfaces:
        ```python
        @implements_interface("IVersionable", "IAuditable", "ITaggable")
        class Document(OntologyObject):
            ...
        ```

    Non-strict mode (warnings only):
        ```python
        @implements_interface("IVersionable", strict=False)
        class Document(OntologyObject):
            ...  # Missing methods will be warned, not error
        ```
    """
    if not interface_ids:
        raise ValueError("At least one interface_id must be provided")

    def decorator(cls: Type[T]) -> Type[T]:
        # Import here to avoid circular imports
        from lib.oda.ontology.registry import get_interface_registry

        registry = get_interface_registry()
        class_name = cls.__name__

        # Track which interfaces this class implements
        implemented: List[str] = []
        all_errors: List[tuple[str, List[str]]] = []

        for interface_id in interface_ids:
            # Get the interface definition
            interface = registry.get_interface(interface_id)

            if interface is None:
                error_msg = f"Interface '{interface_id}' not found in registry"
                if strict:
                    raise InterfaceImplementationError(
                        object_type=class_name,
                        interface_id=interface_id,
                        errors=[error_msg],
                    )
                else:
                    logger.warning(
                        f"[implements_interface] {class_name}: {error_msg}"
                    )
                    continue

            # Validate implementation
            result = registry.validate_implementation(cls, interface_id)

            if not result.is_valid:
                error_messages = [e.detail for e in result.errors]
                all_errors.append((interface_id, error_messages))

                if strict:
                    raise InterfaceImplementationError(
                        object_type=class_name,
                        interface_id=interface_id,
                        errors=error_messages,
                    )
                else:
                    for error in error_messages:
                        logger.warning(
                            f"[implements_interface] {class_name} -> {interface_id}: {error}"
                        )
            else:
                # Register the implementation
                if register:
                    registry.register_implementation(cls, interface_id, skip_validation=True)
                implemented.append(interface_id)
                logger.debug(
                    f"[implements_interface] {class_name} implements {interface_id}"
                )

        # Add metadata to the class
        if not hasattr(cls, "_implements"):
            cls._implements = []

        # Extend with newly implemented interfaces
        cls._implements = list(set(cls._implements + implemented))

        # Add validation timestamp
        cls._interface_validated_at = datetime.now(timezone.utc).isoformat()

        return cls

    return decorator


def implements(*interface_ids: str, strict: bool = True) -> Callable[[Type[T]], Type[T]]:
    """
    Shorthand alias for @implements_interface.

    Example:
        ```python
        @implements("IVersionable", "IAuditable")
        class Document(OntologyObject):
            ...
        ```
    """
    return implements_interface(*interface_ids, strict=strict)


def check_interface(
    cls: Type,
    interface_id: str,
) -> bool:
    """
    Check if a class implements a specific interface.

    Args:
        cls: The class to check
        interface_id: ID of the interface

    Returns:
        True if the class implements the interface

    Example:
        ```python
        if check_interface(Document, "IVersionable"):
            doc.bump_version()
        ```
    """
    # Check class attribute first
    if hasattr(cls, "_implements"):
        if interface_id in cls._implements:
            return True

    # Fall back to registry check
    from lib.oda.ontology.registry import get_interface_registry

    registry = get_interface_registry()
    return registry.implements(cls.__name__, interface_id)


def get_implemented_interfaces(cls: Type) -> List[str]:
    """
    Get all interfaces implemented by a class.

    Args:
        cls: The class to check

    Returns:
        List of interface IDs

    Example:
        ```python
        interfaces = get_implemented_interfaces(Document)
        # ['IVersionable', 'IAuditable']
        ```
    """
    if hasattr(cls, "_implements"):
        return list(cls._implements)

    from lib.oda.ontology.registry import get_interface_registry

    registry = get_interface_registry()
    return registry.get_interfaces_for_object(cls.__name__)


def require_interface(interface_id: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to require that a function parameter implements a specific interface.

    Args:
        interface_id: Required interface ID

    Example:
        ```python
        @require_interface("IVersionable")
        def process_versionable(obj):
            obj.bump_version()
        ```

    Note:
        This validates at call time, not at definition time.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check first positional argument
            if args:
                obj = args[0]
                if hasattr(obj, "__class__"):
                    if not check_interface(obj.__class__, interface_id):
                        raise TypeError(
                            f"First argument must implement interface '{interface_id}', "
                            f"got {obj.__class__.__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Exception
    "InterfaceImplementationError",
    # Decorators
    "implements_interface",
    "implements",
    "require_interface",
    # Utilities
    "check_interface",
    "get_implemented_interfaces",
]
