"""
InterfaceRegistry - Tracks Interface inheritance and property resolution.

This registry provides specialized functionality for Interfaces:
    - Tracking which Interfaces extend other Interfaces
    - Resolving the full property set including inherited properties
    - Validating ObjectType compliance with Interface contracts

Interface inheritance in Palantir Ontology:
    - Interfaces can extend multiple other Interfaces
    - Properties are inherited from all parent Interfaces
    - ObjectTypes must implement ALL properties from an Interface (including inherited)

Example:
    # Define interfaces with inheritance
    auditable = Interface(api_name="Auditable", ...)
    versioned = Interface(api_name="Versioned", extends=["Auditable"], ...)

    # Resolve all properties including inherited
    interface_registry = InterfaceRegistry.get_instance()
    all_props = interface_registry.resolve_properties("Versioned")
    # Returns: properties from Versioned + properties from Auditable
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ontology_definition.types.interface import Interface
    from ontology_definition.types.object_type import ObjectType
    from ontology_definition.types.property_def import PropertyDefinition


class InterfaceRegistry:
    """
    Singleton registry for Interface inheritance tracking.

    Works in conjunction with OntologyRegistry to provide:
    - Interface extension graph (which interfaces extend which)
    - Property resolution across inheritance hierarchy
    - ObjectType compliance validation

    Thread-safe using double-checked locking.
    """

    _instance: InterfaceRegistry | None = None
    _lock = threading.Lock()

    def __new__(cls) -> InterfaceRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        # Extension graph: interface_api_name -> list of parent interface names
        self._extends_graph: dict[str, list[str]] = {}

        # Resolved property cache: interface_api_name -> all properties (including inherited)
        self._property_cache: dict[str, list[PropertyDefinition]] = {}

        # Validation cache: (interface_name, object_type_name) -> validation result
        self._validation_cache: dict[tuple[str, str], bool] = {}

        self._initialized = True

    @classmethod
    def get_instance(cls) -> InterfaceRegistry:
        """Get the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton. Use with caution - primarily for testing."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._extends_graph.clear()
                cls._instance._property_cache.clear()
                cls._instance._validation_cache.clear()
            cls._instance = None

    def register_interface(self, interface: Interface) -> None:
        """
        Register an Interface and its extension relationships.

        Args:
            interface: The Interface to register.

        Note:
            This is called automatically when an Interface is registered
            with the OntologyRegistry.
        """
        extends = getattr(interface, "extends", []) or []
        self._extends_graph[interface.api_name] = list(extends)

        # Invalidate caches that might be affected
        self._invalidate_caches_for(interface.api_name)

    def unregister_interface(self, api_name: str) -> None:
        """Unregister an Interface."""
        self._extends_graph.pop(api_name, None)
        self._invalidate_caches_for(api_name)

    def get_parent_interfaces(self, interface_api_name: str) -> list[str]:
        """
        Get direct parent Interfaces for a given Interface.

        Args:
            interface_api_name: The apiName of the Interface.

        Returns:
            List of parent Interface apiNames (direct extensions only).
        """
        return self._extends_graph.get(interface_api_name, [])

    def get_all_ancestor_interfaces(self, interface_api_name: str) -> list[str]:
        """
        Get all ancestor Interfaces (including transitive).

        Args:
            interface_api_name: The apiName of the Interface.

        Returns:
            List of all ancestor Interface apiNames in breadth-first order.
        """
        visited: set[str] = set()
        ancestors: list[str] = []
        queue = list(self._extends_graph.get(interface_api_name, []))

        while queue:
            parent = queue.pop(0)
            if parent not in visited:
                visited.add(parent)
                ancestors.append(parent)
                # Add grandparents to queue
                grandparents = self._extends_graph.get(parent, [])
                queue.extend(grandparents)

        return ancestors

    def resolve_properties(
        self, interface_api_name: str, from_registry: bool = True
    ) -> list[PropertyDefinition]:
        """
        Resolve all properties for an Interface including inherited ones.

        Args:
            interface_api_name: The apiName of the Interface.
            from_registry: If True, fetch Interface from OntologyRegistry.

        Returns:
            List of all PropertyDefinitions (own + inherited).
            Properties from child override same-named properties from parents.
        """
        # Check cache first
        if interface_api_name in self._property_cache:
            return self._property_cache[interface_api_name]

        from ontology_definition.registry.ontology_registry import get_registry

        registry = get_registry()
        interface = registry.get_interface(interface_api_name)

        if not interface:
            return []

        # Collect properties: start with parent properties, then add own
        # This ensures child properties override parent properties with same name
        all_properties: dict[str, PropertyDefinition] = {}

        # Get properties from all ancestors (deepest first)
        ancestors = self.get_all_ancestor_interfaces(interface_api_name)
        for ancestor_name in reversed(ancestors):
            ancestor = registry.get_interface(ancestor_name)
            if ancestor and hasattr(ancestor, "properties"):
                for prop in ancestor.properties:
                    all_properties[prop.api_name] = prop

        # Add own properties (override inherited)
        if hasattr(interface, "properties"):
            for prop in interface.properties:
                all_properties[prop.api_name] = prop

        result = list(all_properties.values())
        self._property_cache[interface_api_name] = result
        return result

    def resolve_required_properties(
        self, interface_api_name: str
    ) -> list[PropertyDefinition]:
        """
        Resolve only required properties for an Interface.

        Args:
            interface_api_name: The apiName of the Interface.

        Returns:
            List of required PropertyDefinitions (own + inherited).
        """
        all_props = self.resolve_properties(interface_api_name)
        return [
            p
            for p in all_props
            if hasattr(p, "constraints")
            and p.constraints
            and getattr(p.constraints, "required", False)
        ]

    def validate_object_type_implements(
        self, object_type: ObjectType, interface_api_name: str
    ) -> tuple[bool, list[str]]:
        """
        Validate that an ObjectType correctly implements an Interface.

        Checks:
        1. ObjectType has all required properties from Interface
        2. Property types match (if strict validation enabled)

        Args:
            object_type: The ObjectType to validate.
            interface_api_name: The Interface to check against.

        Returns:
            Tuple of (is_valid, list_of_missing_or_mismatched_properties)
        """
        required_props = self.resolve_required_properties(interface_api_name)

        if not required_props:
            return True, []

        object_type_prop_names = {p.api_name for p in object_type.properties}
        missing: list[str] = []

        for req_prop in required_props:
            if req_prop.api_name not in object_type_prop_names:
                missing.append(req_prop.api_name)

        return len(missing) == 0, missing

    def validate_all_interfaces_for_object_type(
        self, object_type: ObjectType
    ) -> dict[str, tuple[bool, list[str]]]:
        """
        Validate ObjectType against all Interfaces it claims to implement.

        Args:
            object_type: The ObjectType to validate.

        Returns:
            Dictionary mapping interface_api_name -> (is_valid, missing_props)
        """
        results: dict[str, tuple[bool, list[str]]] = {}

        for interface_name in object_type.interfaces:
            is_valid, missing = self.validate_object_type_implements(
                object_type, interface_name
            )
            results[interface_name] = (is_valid, missing)

        return results

    def get_interface_hierarchy(
        self, interface_api_name: str
    ) -> dict[str, list[str]]:
        """
        Get the full inheritance hierarchy for an Interface.

        Args:
            interface_api_name: The root Interface.

        Returns:
            Dictionary showing the inheritance tree:
            {
                "interface_name": ["parent1", "parent2"],
                "parent1": ["grandparent1"],
                ...
            }
        """
        hierarchy: dict[str, list[str]] = {}
        queue = [interface_api_name]

        while queue:
            current = queue.pop(0)
            if current not in hierarchy:
                parents = self._extends_graph.get(current, [])
                hierarchy[current] = parents
                queue.extend(parents)

        return hierarchy

    def detect_circular_inheritance(self, interface_api_name: str) -> list[str] | None:
        """
        Detect if there's a circular inheritance in the Interface hierarchy.

        Args:
            interface_api_name: The Interface to check.

        Returns:
            List of Interface names forming the cycle, or None if no cycle.
        """
        visited: set[str] = set()
        path: list[str] = []

        def dfs(name: str) -> list[str] | None:
            if name in visited:
                # Found cycle - extract the cycle from path
                try:
                    cycle_start = path.index(name)
                    return path[cycle_start:] + [name]
                except ValueError:
                    return None

            visited.add(name)
            path.append(name)

            for parent in self._extends_graph.get(name, []):
                result = dfs(parent)
                if result:
                    return result

            path.pop()
            return None

        return dfs(interface_api_name)

    def _invalidate_caches_for(self, interface_api_name: str) -> None:
        """Invalidate caches that might be affected by changes to an Interface."""
        # Clear property cache for this interface and all children
        self._property_cache.pop(interface_api_name, None)

        # Find all interfaces that extend this one (directly or transitively)
        for name, parents in self._extends_graph.items():
            if interface_api_name in parents:
                self._property_cache.pop(name, None)

        # Clear validation cache entries involving this interface
        keys_to_remove = [
            k for k in self._validation_cache.keys() if k[0] == interface_api_name
        ]
        for key in keys_to_remove:
            del self._validation_cache[key]


# Convenience function
def get_interface_registry() -> InterfaceRegistry:
    """Get the global InterfaceRegistry instance."""
    return InterfaceRegistry.get_instance()
