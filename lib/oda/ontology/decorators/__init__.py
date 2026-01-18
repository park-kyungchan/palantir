"""
Orion ODA v4.0 - Ontology Decorators

This package provides decorators for ODA ObjectTypes:
- computed.py: Computed property decorator with caching and invalidation
- interface_decorator.py: Interface implementation decorator

Schema Version: 4.0.0
"""

from lib.oda.ontology.decorators.computed import (
    computed_property,
    cached_computed,
    invalidate_computed,
    ComputedPropertyMixin,
)

from lib.oda.ontology.decorators.interface_decorator import (
    implements_interface,
    implements,
    require_interface,
    check_interface,
    get_implemented_interfaces,
    InterfaceImplementationError,
)

from lib.oda.ontology.decorators.shared_property import (
    uses_shared_property,
    shared,
    require_shared_property,
    get_shared_properties,
    uses_property,
    SharedPropertyError,
    SharedPropertyConflictError,
)

__all__ = [
    # Computed property decorators
    "computed_property",
    "cached_computed",
    "invalidate_computed",
    "ComputedPropertyMixin",
    # Interface decorators
    "implements_interface",
    "implements",
    "require_interface",
    "check_interface",
    "get_implemented_interfaces",
    "InterfaceImplementationError",
    # Shared property decorators
    "uses_shared_property",
    "shared",
    "require_shared_property",
    "get_shared_properties",
    "uses_property",
    "SharedPropertyError",
    "SharedPropertyConflictError",
]
