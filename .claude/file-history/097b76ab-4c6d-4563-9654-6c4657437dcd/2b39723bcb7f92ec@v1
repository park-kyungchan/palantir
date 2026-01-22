"""
Registration Decorators for Ontology Types.

Provides decorator-based registration for ObjectType, LinkType, ActionType,
and Interface definitions. These decorators automatically register types
with the OntologyRegistry singleton when the class/instance is created.

Usage Patterns:

    # Pattern 1: Class decorator (for class-based definitions)
    @register_object_type
    class Employee(ObjectType):
        api_name = "Employee"
        ...

    # Pattern 2: Instance decorator (for instance-based definitions)
    @register_object_type
    def employee_type():
        return ObjectType(api_name="Employee", ...)

    # Pattern 3: Direct registration with instance
    employee_type = ObjectType(api_name="Employee", ...)
    register_object_type(employee_type)

Example:
    from ontology_definition.registry import register_object_type

    @register_object_type
    employee_type = ObjectType(
        api_name="Employee",
        display_name="Employee",
        primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
        properties=[...],
    )

    # Now accessible via registry
    from ontology_definition.registry import get_registry
    emp = get_registry().get_object_type("Employee")
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable, TypeVar, Union, overload

from ontology_definition.registry.ontology_registry import get_registry

if TYPE_CHECKING:
    from ontology_definition.types.object_type import ObjectType
    from ontology_definition.types.link_type import LinkType
    from ontology_definition.types.action_type import ActionType
    from ontology_definition.types.interface import Interface

T = TypeVar("T")
OT = TypeVar("OT", bound="ObjectType")
LT = TypeVar("LT", bound="LinkType")
AT = TypeVar("AT", bound="ActionType")
IF = TypeVar("IF", bound="Interface")


# =============================================================================
# ObjectType Registration
# =============================================================================


@overload
def register_object_type(obj: OT) -> OT:
    """Register an ObjectType instance."""
    ...


@overload
def register_object_type(obj: Callable[[], OT]) -> Callable[[], OT]:
    """Register a factory function that returns an ObjectType."""
    ...


def register_object_type(
    obj: Union[OT, Callable[[], OT]]
) -> Union[OT, Callable[[], OT]]:
    """
    Register an ObjectType with the global registry.

    Can be used as:
    1. Direct registration: register_object_type(object_type_instance)
    2. Factory decorator: @register_object_type on a function returning ObjectType

    Args:
        obj: Either an ObjectType instance or a callable that returns one.

    Returns:
        The same object/callable, after registration.

    Raises:
        ValueError: If ObjectType with same apiName already exists.

    Example:
        # Direct registration
        employee_type = ObjectType(api_name="Employee", ...)
        register_object_type(employee_type)

        # Factory decorator
        @register_object_type
        def create_employee_type():
            return ObjectType(api_name="Employee", ...)
    """
    if callable(obj) and not _is_pydantic_model(obj):
        # It's a factory function - call it and register the result
        @wraps(obj)
        def wrapper() -> OT:
            result = obj()
            get_registry().register_object_type(result)
            return result

        # Execute immediately to register
        wrapper()
        return wrapper  # type: ignore
    else:
        # It's an instance - register directly
        get_registry().register_object_type(obj)  # type: ignore
        return obj


# =============================================================================
# LinkType Registration
# =============================================================================


@overload
def register_link_type(obj: LT) -> LT:
    """Register a LinkType instance."""
    ...


@overload
def register_link_type(obj: Callable[[], LT]) -> Callable[[], LT]:
    """Register a factory function that returns a LinkType."""
    ...


def register_link_type(obj: Union[LT, Callable[[], LT]]) -> Union[LT, Callable[[], LT]]:
    """
    Register a LinkType with the global registry.

    Can be used as:
    1. Direct registration: register_link_type(link_type_instance)
    2. Factory decorator: @register_link_type on a function returning LinkType

    Args:
        obj: Either a LinkType instance or a callable that returns one.

    Returns:
        The same object/callable, after registration.

    Raises:
        ValueError: If LinkType with same apiName already exists.

    Example:
        # Direct registration
        reports_to = LinkType(api_name="ReportsTo", ...)
        register_link_type(reports_to)

        # Factory decorator
        @register_link_type
        def create_reports_to():
            return LinkType(api_name="ReportsTo", ...)
    """
    if callable(obj) and not _is_pydantic_model(obj):
        @wraps(obj)
        def wrapper() -> LT:
            result = obj()
            get_registry().register_link_type(result)
            return result

        wrapper()
        return wrapper  # type: ignore
    else:
        get_registry().register_link_type(obj)  # type: ignore
        return obj


# =============================================================================
# ActionType Registration
# =============================================================================


@overload
def register_action_type(obj: AT) -> AT:
    """Register an ActionType instance."""
    ...


@overload
def register_action_type(obj: Callable[[], AT]) -> Callable[[], AT]:
    """Register a factory function that returns an ActionType."""
    ...


def register_action_type(
    obj: Union[AT, Callable[[], AT]]
) -> Union[AT, Callable[[], AT]]:
    """
    Register an ActionType with the global registry.

    Can be used as:
    1. Direct registration: register_action_type(action_type_instance)
    2. Factory decorator: @register_action_type on a function returning ActionType

    Args:
        obj: Either an ActionType instance or a callable that returns one.

    Returns:
        The same object/callable, after registration.

    Raises:
        ValueError: If ActionType with same apiName already exists.

    Example:
        # Direct registration
        create_employee = ActionType(api_name="CreateEmployee", ...)
        register_action_type(create_employee)

        # Factory decorator
        @register_action_type
        def create_employee_action():
            return ActionType(api_name="CreateEmployee", ...)
    """
    if callable(obj) and not _is_pydantic_model(obj):
        @wraps(obj)
        def wrapper() -> AT:
            result = obj()
            get_registry().register_action_type(result)
            return result

        wrapper()
        return wrapper  # type: ignore
    else:
        get_registry().register_action_type(obj)  # type: ignore
        return obj


# =============================================================================
# Interface Registration
# =============================================================================


@overload
def register_interface(obj: IF) -> IF:
    """Register an Interface instance."""
    ...


@overload
def register_interface(obj: Callable[[], IF]) -> Callable[[], IF]:
    """Register a factory function that returns an Interface."""
    ...


def register_interface(obj: Union[IF, Callable[[], IF]]) -> Union[IF, Callable[[], IF]]:
    """
    Register an Interface with the global registry.

    Can be used as:
    1. Direct registration: register_interface(interface_instance)
    2. Factory decorator: @register_interface on a function returning Interface

    Args:
        obj: Either an Interface instance or a callable that returns one.

    Returns:
        The same object/callable, after registration.

    Raises:
        ValueError: If Interface with same apiName already exists.

    Example:
        # Direct registration
        auditable = Interface(api_name="Auditable", ...)
        register_interface(auditable)

        # Factory decorator
        @register_interface
        def create_auditable():
            return Interface(api_name="Auditable", ...)
    """
    if callable(obj) and not _is_pydantic_model(obj):
        @wraps(obj)
        def wrapper() -> IF:
            result = obj()
            get_registry().register_interface(result)
            return result

        wrapper()
        return wrapper  # type: ignore
    else:
        get_registry().register_interface(obj)  # type: ignore
        return obj


# =============================================================================
# Batch Registration
# =============================================================================


def register_all(
    object_types: list["ObjectType"] | None = None,
    link_types: list["LinkType"] | None = None,
    action_types: list["ActionType"] | None = None,
    interfaces: list["Interface"] | None = None,
) -> dict[str, int]:
    """
    Register multiple ontology types at once.

    Args:
        object_types: List of ObjectTypes to register.
        link_types: List of LinkTypes to register.
        action_types: List of ActionTypes to register.
        interfaces: List of Interfaces to register.

    Returns:
        Dictionary with counts of registered types.

    Raises:
        ValueError: If any type with duplicate apiName is encountered.

    Example:
        register_all(
            object_types=[employee_type, department_type],
            link_types=[reports_to, belongs_to],
            action_types=[create_employee, update_employee],
        )
    """
    registry = get_registry()
    counts = {
        "object_types": 0,
        "link_types": 0,
        "action_types": 0,
        "interfaces": 0,
    }

    if object_types:
        for ot in object_types:
            registry.register_object_type(ot)
            counts["object_types"] += 1

    if link_types:
        for lt in link_types:
            registry.register_link_type(lt)
            counts["link_types"] += 1

    if action_types:
        for at in action_types:
            registry.register_action_type(at)
            counts["action_types"] += 1

    if interfaces:
        for iface in interfaces:
            registry.register_interface(iface)
            counts["interfaces"] += 1

    return counts


# =============================================================================
# Helper Functions
# =============================================================================


def _is_pydantic_model(obj: object) -> bool:
    """Check if obj is a Pydantic model instance (not a class or callable)."""
    # Check for Pydantic BaseModel instance
    return hasattr(obj, "model_dump") and hasattr(obj, "model_fields")


def clear_registry() -> None:
    """
    Clear all registered types from the registry.

    USE WITH CAUTION - primarily for testing purposes.
    """
    from ontology_definition.registry.ontology_registry import OntologyRegistry

    OntologyRegistry.reset_instance()
