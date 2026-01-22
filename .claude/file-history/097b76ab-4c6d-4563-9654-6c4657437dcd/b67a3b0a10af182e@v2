"""
Registry module - Singleton registry for ontology types.

Exports:
    - OntologyRegistry: Central registry singleton
    - get_registry: Get global registry instance
    - register_object_type: Decorator for ObjectType registration
    - register_link_type: Decorator for LinkType registration
    - register_action_type: Decorator for ActionType registration
    - register_interface: Decorator for Interface registration
    - register_all: Batch registration utility
    - InterfaceRegistry: Interface inheritance tracking
    - get_interface_registry: Get global interface registry instance
"""

from ontology_definition.registry.ontology_registry import (
    OntologyRegistry,
    TypeRegistry,
    get_registry,
)

from ontology_definition.registry.decorators import (
    register_object_type,
    register_link_type,
    register_action_type,
    register_interface,
    register_all,
    clear_registry,
)

from ontology_definition.registry.interface_registry import (
    InterfaceRegistry,
    get_interface_registry,
)

__all__ = [
    # Core Registry
    "OntologyRegistry",
    "TypeRegistry",
    "get_registry",
    # Decorators
    "register_object_type",
    "register_link_type",
    "register_action_type",
    "register_interface",
    "register_all",
    "clear_registry",
    # Interface Inheritance
    "InterfaceRegistry",
    "get_interface_registry",
]
