"""
OntologyRegistry - Singleton registry for all ontology types.

The OntologyRegistry provides a central, thread-safe storage for:
    - ObjectTypes: Entity schema definitions
    - LinkTypes: Relationship definitions between ObjectTypes
    - ActionTypes: Mutation operation definitions
    - Interfaces: Shared property contracts

This is the single source of truth for all registered ontology definitions
at runtime. It supports lookup by apiName (unique identifier) and RID
(globally unique resource identifier).

Example:
    # Get the singleton instance
    registry = OntologyRegistry.get_instance()

    # Register types
    registry.register_object_type(employee_type)
    registry.register_link_type(reports_to_link)

    # Lookup
    employee = registry.get_object_type("Employee")
    link = registry.get_link_type_by_rid("ri.ontology.main.link-type.abc123")

    # List all
    all_objects = registry.list_object_types()
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

if TYPE_CHECKING:
    from ontology_definition.types.object_type import ObjectType
    from ontology_definition.types.link_type import LinkType
    from ontology_definition.types.action_type import ActionType
    from ontology_definition.types.interface import Interface


T = TypeVar("T")


class TypeRegistry(Generic[T]):
    """
    Generic registry for a specific ontology type.

    Provides O(1) lookup by both apiName and RID using dual dictionaries.
    Thread-safe for concurrent read/write operations.
    """

    def __init__(self, type_name: str) -> None:
        self._type_name = type_name
        self._by_api_name: dict[str, T] = {}
        self._by_rid: dict[str, T] = {}
        self._lock = threading.RLock()

    def register(self, item: T) -> None:
        """
        Register an item in the registry.

        Args:
            item: The ontology type instance to register.
                  Must have 'api_name' and 'rid' attributes.

        Raises:
            ValueError: If an item with the same apiName is already registered.
        """
        api_name = getattr(item, "api_name", None)
        rid = getattr(item, "rid", None)

        if not api_name:
            raise ValueError(f"{self._type_name} must have an api_name")

        with self._lock:
            if api_name in self._by_api_name:
                raise ValueError(
                    f"{self._type_name} with apiName '{api_name}' is already registered"
                )

            self._by_api_name[api_name] = item
            if rid:
                self._by_rid[rid] = item

    def unregister(self, api_name: str) -> Optional[T]:
        """
        Unregister an item by apiName.

        Args:
            api_name: The apiName of the item to unregister.

        Returns:
            The unregistered item, or None if not found.
        """
        with self._lock:
            item = self._by_api_name.pop(api_name, None)
            if item:
                rid = getattr(item, "rid", None)
                if rid:
                    self._by_rid.pop(rid, None)
            return item

    def get(self, api_name: str) -> Optional[T]:
        """Get an item by apiName."""
        with self._lock:
            return self._by_api_name.get(api_name)

    def get_by_rid(self, rid: str) -> Optional[T]:
        """Get an item by RID."""
        with self._lock:
            return self._by_rid.get(rid)

    def exists(self, api_name: str) -> bool:
        """Check if an item exists by apiName."""
        with self._lock:
            return api_name in self._by_api_name

    def list_all(self) -> list[T]:
        """List all registered items."""
        with self._lock:
            return list(self._by_api_name.values())

    def list_api_names(self) -> list[str]:
        """List all registered apiNames."""
        with self._lock:
            return list(self._by_api_name.keys())

    def count(self) -> int:
        """Return the number of registered items."""
        with self._lock:
            return len(self._by_api_name)

    def clear(self) -> None:
        """Clear all registered items. Use with caution - primarily for testing."""
        with self._lock:
            self._by_api_name.clear()
            self._by_rid.clear()


class OntologyRegistry:
    """
    Singleton registry for all ontology types.

    Thread-safe singleton pattern using double-checked locking.

    Usage:
        registry = OntologyRegistry.get_instance()
        registry.register_object_type(my_object_type)
        obj = registry.get_object_type("MyObjectType")
    """

    _instance: Optional["OntologyRegistry"] = None
    _lock = threading.RLock()  # Reentrant lock to prevent deadlock in __new__/get_instance

    def __new__(cls) -> "OntologyRegistry":
        """Enforce singleton pattern - prefer get_instance() for clarity."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize registries (only runs once due to singleton)."""
        if getattr(self, "_initialized", False):
            return

        self._object_types: TypeRegistry["ObjectType"] = TypeRegistry("ObjectType")
        self._link_types: TypeRegistry["LinkType"] = TypeRegistry("LinkType")
        self._action_types: TypeRegistry["ActionType"] = TypeRegistry("ActionType")
        self._interfaces: TypeRegistry["Interface"] = TypeRegistry("Interface")
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "OntologyRegistry":
        """
        Get the singleton instance of OntologyRegistry.

        This is the preferred way to access the registry.

        Returns:
            The singleton OntologyRegistry instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance. USE WITH CAUTION - primarily for testing.

        This clears all registered types and resets the singleton.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance._object_types.clear()
                cls._instance._link_types.clear()
                cls._instance._action_types.clear()
                cls._instance._interfaces.clear()
            cls._instance = None

    # =========================================================================
    # ObjectType Registration
    # =========================================================================

    def register_object_type(self, object_type: "ObjectType") -> None:
        """
        Register an ObjectType in the registry.

        Args:
            object_type: The ObjectType to register.

        Raises:
            ValueError: If ObjectType with same apiName already exists.
        """
        self._object_types.register(object_type)

    def unregister_object_type(self, api_name: str) -> Optional["ObjectType"]:
        """Unregister an ObjectType by apiName."""
        return self._object_types.unregister(api_name)

    def get_object_type(self, api_name: str) -> Optional["ObjectType"]:
        """Get an ObjectType by apiName."""
        return self._object_types.get(api_name)

    def get_object_type_by_rid(self, rid: str) -> Optional["ObjectType"]:
        """Get an ObjectType by RID."""
        return self._object_types.get_by_rid(rid)

    def has_object_type(self, api_name: str) -> bool:
        """Check if an ObjectType exists."""
        return self._object_types.exists(api_name)

    def list_object_types(self) -> list["ObjectType"]:
        """List all registered ObjectTypes."""
        return self._object_types.list_all()

    def list_object_type_names(self) -> list[str]:
        """List all registered ObjectType apiNames."""
        return self._object_types.list_api_names()

    # =========================================================================
    # LinkType Registration
    # =========================================================================

    def register_link_type(self, link_type: "LinkType") -> None:
        """
        Register a LinkType in the registry.

        Args:
            link_type: The LinkType to register.

        Raises:
            ValueError: If LinkType with same apiName already exists.
        """
        self._link_types.register(link_type)

    def unregister_link_type(self, api_name: str) -> Optional["LinkType"]:
        """Unregister a LinkType by apiName."""
        return self._link_types.unregister(api_name)

    def get_link_type(self, api_name: str) -> Optional["LinkType"]:
        """Get a LinkType by apiName."""
        return self._link_types.get(api_name)

    def get_link_type_by_rid(self, rid: str) -> Optional["LinkType"]:
        """Get a LinkType by RID."""
        return self._link_types.get_by_rid(rid)

    def has_link_type(self, api_name: str) -> bool:
        """Check if a LinkType exists."""
        return self._link_types.exists(api_name)

    def list_link_types(self) -> list["LinkType"]:
        """List all registered LinkTypes."""
        return self._link_types.list_all()

    def list_link_type_names(self) -> list[str]:
        """List all registered LinkType apiNames."""
        return self._link_types.list_api_names()

    # =========================================================================
    # ActionType Registration
    # =========================================================================

    def register_action_type(self, action_type: "ActionType") -> None:
        """
        Register an ActionType in the registry.

        Args:
            action_type: The ActionType to register.

        Raises:
            ValueError: If ActionType with same apiName already exists.
        """
        self._action_types.register(action_type)

    def unregister_action_type(self, api_name: str) -> Optional["ActionType"]:
        """Unregister an ActionType by apiName."""
        return self._action_types.unregister(api_name)

    def get_action_type(self, api_name: str) -> Optional["ActionType"]:
        """Get an ActionType by apiName."""
        return self._action_types.get(api_name)

    def get_action_type_by_rid(self, rid: str) -> Optional["ActionType"]:
        """Get an ActionType by RID."""
        return self._action_types.get_by_rid(rid)

    def has_action_type(self, api_name: str) -> bool:
        """Check if an ActionType exists."""
        return self._action_types.exists(api_name)

    def list_action_types(self) -> list["ActionType"]:
        """List all registered ActionTypes."""
        return self._action_types.list_all()

    def list_action_type_names(self) -> list[str]:
        """List all registered ActionType apiNames."""
        return self._action_types.list_api_names()

    # =========================================================================
    # Interface Registration
    # =========================================================================

    def register_interface(self, interface: "Interface") -> None:
        """
        Register an Interface in the registry.

        Args:
            interface: The Interface to register.

        Raises:
            ValueError: If Interface with same apiName already exists.
        """
        self._interfaces.register(interface)

    def unregister_interface(self, api_name: str) -> Optional["Interface"]:
        """Unregister an Interface by apiName."""
        return self._interfaces.unregister(api_name)

    def get_interface(self, api_name: str) -> Optional["Interface"]:
        """Get an Interface by apiName."""
        return self._interfaces.get(api_name)

    def get_interface_by_rid(self, rid: str) -> Optional["Interface"]:
        """Get an Interface by RID."""
        return self._interfaces.get_by_rid(rid)

    def has_interface(self, api_name: str) -> bool:
        """Check if an Interface exists."""
        return self._interfaces.exists(api_name)

    def list_interfaces(self) -> list["Interface"]:
        """List all registered Interfaces."""
        return self._interfaces.list_all()

    def list_interface_names(self) -> list[str]:
        """List all registered Interface apiNames."""
        return self._interfaces.list_api_names()

    # =========================================================================
    # Cross-Type Queries
    # =========================================================================

    def get_links_for_object_type(self, object_type_api_name: str) -> list["LinkType"]:
        """
        Get all LinkTypes that reference a given ObjectType.

        Args:
            object_type_api_name: The apiName of the ObjectType.

        Returns:
            List of LinkTypes where this ObjectType is source or target.
        """
        result = []
        for link_type in self._link_types.list_all():
            if (
                link_type.source_object_type == object_type_api_name
                or link_type.target_object_type == object_type_api_name
            ):
                result.append(link_type)
        return result

    def get_actions_for_object_type(
        self, object_type_api_name: str
    ) -> list["ActionType"]:
        """
        Get all ActionTypes that apply to a given ObjectType.

        Args:
            object_type_api_name: The apiName of the ObjectType.

        Returns:
            List of ActionTypes that have this ObjectType in applies_to.
        """
        result = []
        for action_type in self._action_types.list_all():
            applies_to = getattr(action_type, "applies_to", [])
            if object_type_api_name in applies_to:
                result.append(action_type)
        return result

    def get_object_types_implementing_interface(
        self, interface_api_name: str
    ) -> list["ObjectType"]:
        """
        Get all ObjectTypes that implement a given Interface.

        Args:
            interface_api_name: The apiName of the Interface.

        Returns:
            List of ObjectTypes implementing this Interface.
        """
        result = []
        for object_type in self._object_types.list_all():
            if interface_api_name in object_type.interfaces:
                result.append(object_type)
        return result

    # =========================================================================
    # Statistics
    # =========================================================================

    def stats(self) -> dict[str, int]:
        """
        Get registry statistics.

        Returns:
            Dictionary with counts for each type category.
        """
        return {
            "object_types": self._object_types.count(),
            "link_types": self._link_types.count(),
            "action_types": self._action_types.count(),
            "interfaces": self._interfaces.count(),
            "total": (
                self._object_types.count()
                + self._link_types.count()
                + self._action_types.count()
                + self._interfaces.count()
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Export registry contents to a dictionary.

        Useful for debugging or serialization.

        Returns:
            Dictionary containing all registered types as dicts.
        """
        return {
            "object_types": [
                ot.model_dump() if hasattr(ot, "model_dump") else str(ot)
                for ot in self._object_types.list_all()
            ],
            "link_types": [
                lt.model_dump() if hasattr(lt, "model_dump") else str(lt)
                for lt in self._link_types.list_all()
            ],
            "action_types": [
                at.model_dump() if hasattr(at, "model_dump") else str(at)
                for at in self._action_types.list_all()
            ],
            "interfaces": [
                i.model_dump() if hasattr(i, "model_dump") else str(i)
                for i in self._interfaces.list_all()
            ],
        }


# Convenience function for module-level access
def get_registry() -> OntologyRegistry:
    """
    Get the global OntologyRegistry instance.

    Shorthand for OntologyRegistry.get_instance().

    Returns:
        The singleton OntologyRegistry instance.
    """
    return OntologyRegistry.get_instance()
