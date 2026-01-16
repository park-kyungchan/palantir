"""
Orion ODA v4.0 - Ontology Registry

Single source of truth for all ObjectType and LinkType definitions.
Provides:
- ObjectType registration via @register_object_type decorator
- LinkType registration via @register_link_type decorator
- Schema export to JSON with versioning
- Link schema export with referential integrity metadata
- Runtime introspection of registered types
- Integration with SchemaValidator for mutation validation

Schema Version: 4.0.0
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel

from lib.oda.ontology.ontology_types import Link, OntologyObject, PropertyType
from lib.oda.ontology.types.link_types import (
    CascadePolicy,
    LinkDirection,
    LinkTypeMetadata,
)
from lib.oda.ontology.types.interface_types import (
    InterfaceDefinition,
    InterfaceValidationError,
    InterfaceValidationResult,
    InterfaceImplementation,
    PropertySpec,
    MethodSpec,
)
from lib.oda.ontology.types.shared_properties import (
    SharedPropertyDefinition,
    SharedPropertyUsage,
    SharedPropertyRegistry,
    BUILTIN_SHARED_PROPERTIES,
)

# Schema version - increment on schema changes
SCHEMA_VERSION = "4.0.0"
SCHEMA_GENERATED_BY = "Orion ODA v4.0"


@dataclass(frozen=True)
class PropertyDefinition:
    name: str
    property_type: PropertyType
    required: bool
    description: str


@dataclass(frozen=True)
class LinkDefinition:
    link_type_id: str
    target: str
    cardinality: str
    reverse_link_id: Optional[str]
    description: Optional[str]
    backing_table_name: Optional[str]
    is_materialized: bool


@dataclass(frozen=True)
class ObjectDefinition:
    name: str
    description: str
    properties: Dict[str, PropertyDefinition] = field(default_factory=dict)
    links: Dict[str, LinkDefinition] = field(default_factory=dict)


# =============================================================================
# INTERFACE REGISTRY
# =============================================================================


class InterfaceRegistry:
    """
    Registry for Interface definitions and implementations.

    Provides:
    - Interface registration and lookup
    - Implementation validation
    - Interface inheritance resolution
    - ObjectType-to-Interface mapping

    Example:
        ```python
        registry = InterfaceRegistry()

        # Register an interface
        registry.register_interface(InterfaceDefinition(
            interface_id="IVersionable",
            description="Versionable objects",
            required_properties=[
                PropertySpec(name="version", type_hint="int"),
            ],
        ))

        # Validate implementation
        result = registry.validate_implementation(Task, "IVersionable")
        if result.is_valid:
            registry.register_implementation(Task, "IVersionable")
        ```
    """

    def __init__(self) -> None:
        self._interfaces: Dict[str, InterfaceDefinition] = {}
        self._implementations: Dict[str, List[str]] = {}  # interface_id -> [object_type_names]
        self._object_interfaces: Dict[str, List[str]] = {}  # object_type -> [interface_ids]

    def register_interface(self, interface: InterfaceDefinition) -> None:
        """
        Register an interface definition.

        Args:
            interface: InterfaceDefinition to register

        Raises:
            ValueError: If interface_id is already registered
        """
        if interface.interface_id in self._interfaces:
            raise ValueError(
                f"Interface '{interface.interface_id}' is already registered"
            )

        # Validate extends references exist
        if interface.extends:
            for parent_id in interface.extends:
                if parent_id not in self._interfaces:
                    raise ValueError(
                        f"Interface '{interface.interface_id}' extends unknown interface: '{parent_id}'"
                    )

        self._interfaces[interface.interface_id] = interface
        self._implementations[interface.interface_id] = []

    def get_interface(self, interface_id: str) -> Optional[InterfaceDefinition]:
        """Get an interface definition by ID."""
        return self._interfaces.get(interface_id)

    def list_interfaces(self) -> List[InterfaceDefinition]:
        """List all registered interfaces."""
        return list(self._interfaces.values())

    def list_interface_ids(self) -> List[str]:
        """List all registered interface IDs."""
        return list(self._interfaces.keys())

    def get_full_interface(self, interface_id: str) -> Optional[InterfaceDefinition]:
        """
        Get interface with all inherited properties and methods resolved.

        Returns a new InterfaceDefinition with properties and methods from
        all parent interfaces included.
        """
        interface = self._interfaces.get(interface_id)
        if not interface:
            return None

        if not interface.extends:
            return interface

        # Collect all properties and methods from parent interfaces
        all_properties: List[PropertySpec] = []
        all_methods: List[MethodSpec] = []
        seen_props: set = set()
        seen_methods: set = set()

        # Process parent interfaces first (depth-first)
        def collect_from_parents(iface_id: str) -> None:
            iface = self._interfaces.get(iface_id)
            if not iface:
                return

            # Process parents first
            if iface.extends:
                for parent_id in iface.extends:
                    collect_from_parents(parent_id)

            # Add properties not yet seen
            for prop in iface.required_properties:
                if prop.name not in seen_props:
                    all_properties.append(prop)
                    seen_props.add(prop.name)

            # Add methods not yet seen
            for method in iface.required_methods:
                if method.name not in seen_methods:
                    all_methods.append(method)
                    seen_methods.add(method.name)

        collect_from_parents(interface_id)

        return InterfaceDefinition(
            interface_id=interface.interface_id,
            description=interface.description,
            required_properties=all_properties,
            required_methods=all_methods,
            extends=interface.extends,
            is_abstract=interface.is_abstract,
        )

    def validate_implementation(
        self,
        object_type: Type,
        interface_id: str,
    ) -> InterfaceValidationResult:
        """
        Validate that an ObjectType correctly implements an interface.

        Args:
            object_type: The class to validate
            interface_id: ID of the interface to validate against

        Returns:
            InterfaceValidationResult with validation status and any errors
        """
        object_type_name = object_type.__name__

        # Get the full interface (with inherited requirements)
        interface = self.get_full_interface(interface_id)
        if not interface:
            return InterfaceValidationResult.failure(
                object_type=object_type_name,
                interface_id=interface_id,
                errors=[
                    InterfaceValidationError(
                        error_type="unknown_interface",
                        interface_id=interface_id,
                        detail=f"Interface '{interface_id}' not found in registry",
                    )
                ],
            )

        errors: List[InterfaceValidationError] = []

        # Check required properties
        for prop_spec in interface.required_properties:
            if not self._check_property(object_type, prop_spec, interface_id, errors):
                continue

        # Check required methods
        for method_spec in interface.required_methods:
            if not self._check_method(object_type, method_spec, interface_id, errors):
                continue

        if errors:
            return InterfaceValidationResult.failure(
                object_type=object_type_name,
                interface_id=interface_id,
                errors=errors,
            )

        return InterfaceValidationResult.success(
            object_type=object_type_name,
            interface_id=interface_id,
        )

    def _check_property(
        self,
        object_type: Type,
        prop_spec: PropertySpec,
        interface_id: str,
        errors: List[InterfaceValidationError],
    ) -> bool:
        """Check if object_type has the required property."""
        # Check in model_fields for Pydantic models
        if hasattr(object_type, "model_fields"):
            if prop_spec.name not in object_type.model_fields:
                if prop_spec.required:
                    errors.append(
                        InterfaceValidationError(
                            error_type="missing_property",
                            interface_id=interface_id,
                            detail=f"Missing required property '{prop_spec.name}'",
                            property_name=prop_spec.name,
                            expected=prop_spec.type_hint,
                        )
                    )
                    return False
        else:
            # Non-Pydantic class - check annotations
            annotations = getattr(object_type, "__annotations__", {})
            if prop_spec.name not in annotations:
                if prop_spec.required:
                    errors.append(
                        InterfaceValidationError(
                            error_type="missing_property",
                            interface_id=interface_id,
                            detail=f"Missing required property '{prop_spec.name}'",
                            property_name=prop_spec.name,
                            expected=prop_spec.type_hint,
                        )
                    )
                    return False

        return True

    def _check_method(
        self,
        object_type: Type,
        method_spec: MethodSpec,
        interface_id: str,
        errors: List[InterfaceValidationError],
    ) -> bool:
        """Check if object_type has the required method."""
        method = getattr(object_type, method_spec.name, None)

        if method is None:
            errors.append(
                InterfaceValidationError(
                    error_type="missing_method",
                    interface_id=interface_id,
                    detail=f"Missing required method '{method_spec.name}'",
                    method_name=method_spec.name,
                    expected=method_spec.signature,
                )
            )
            return False

        if not callable(method):
            errors.append(
                InterfaceValidationError(
                    error_type="not_callable",
                    interface_id=interface_id,
                    detail=f"'{method_spec.name}' is not callable",
                    method_name=method_spec.name,
                )
            )
            return False

        return True

    def register_implementation(
        self,
        object_type: Type,
        interface_id: str,
        skip_validation: bool = False,
    ) -> InterfaceValidationResult:
        """
        Register that an ObjectType implements an interface.

        Args:
            object_type: The class implementing the interface
            interface_id: ID of the interface being implemented
            skip_validation: If True, skip validation (use with caution)

        Returns:
            InterfaceValidationResult

        Raises:
            ValueError: If validation fails and skip_validation is False
        """
        object_type_name = object_type.__name__

        if not skip_validation:
            result = self.validate_implementation(object_type, interface_id)
            if not result.is_valid:
                error_details = "; ".join(e.detail for e in result.errors)
                raise ValueError(
                    f"ObjectType '{object_type_name}' does not implement interface "
                    f"'{interface_id}': {error_details}"
                )
        else:
            result = InterfaceValidationResult.success(object_type_name, interface_id)

        # Register the implementation
        if interface_id not in self._implementations:
            self._implementations[interface_id] = []
        if object_type_name not in self._implementations[interface_id]:
            self._implementations[interface_id].append(object_type_name)

        # Register reverse mapping
        if object_type_name not in self._object_interfaces:
            self._object_interfaces[object_type_name] = []
        if interface_id not in self._object_interfaces[object_type_name]:
            self._object_interfaces[object_type_name].append(interface_id)

        return result

    def get_implementations(self, interface_id: str) -> List[str]:
        """Get all ObjectType names that implement an interface."""
        return self._implementations.get(interface_id, [])

    def get_interfaces_for_object(self, object_type_name: str) -> List[str]:
        """Get all interface IDs that an ObjectType implements."""
        return self._object_interfaces.get(object_type_name, [])

    def implements(self, object_type_name: str, interface_id: str) -> bool:
        """Check if an ObjectType implements a specific interface."""
        return interface_id in self._object_interfaces.get(object_type_name, [])

    def export_json(self, path: Path) -> None:
        """
        Export interface registry to JSON.

        Output includes:
        - All interface definitions
        - Implementation mappings
        - Statistics
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "version": SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": SCHEMA_GENERATED_BY,
            "interfaces": {
                iface_id: {
                    "description": iface.description,
                    "required_properties": [
                        {
                            "name": p.name,
                            "type_hint": p.type_hint,
                            "description": p.description,
                            "required": p.required,
                        }
                        for p in iface.required_properties
                    ],
                    "required_methods": [
                        {
                            "name": m.name,
                            "signature": m.signature,
                            "description": m.description,
                            "is_async": m.is_async,
                        }
                        for m in iface.required_methods
                    ],
                    "extends": iface.extends,
                    "is_abstract": iface.is_abstract,
                    "implementations": self._implementations.get(iface_id, []),
                }
                for iface_id, iface in sorted(self._interfaces.items())
            },
            "statistics": {
                "total_interfaces": len(self._interfaces),
                "total_implementations": sum(
                    len(impls) for impls in self._implementations.values()
                ),
            },
        }

        target.write_text(json.dumps(payload, indent=2))


class OntologyRegistry:
    """
    Central registry for ObjectTypes and LinkTypes.

    Provides registration, introspection, and export capabilities
    for the ODA ontology schema.

    Example:
        ```python
        registry = get_registry()

        # Register types
        registry.register_object(Task)
        registry.register_link_type(task_depends_on_task)

        # Export schemas
        registry.export_json("schemas/ontology.json")
        registry.export_links_json("schemas/links.json")
        ```
    """

    def __init__(self) -> None:
        self._objects: Dict[str, ObjectDefinition] = {}
        self._link_types: Dict[str, LinkTypeMetadata] = {}

    def register_object(self, obj_cls: Type[OntologyObject]) -> None:
        definition = ObjectDefinition(
            name=obj_cls.__name__,
            description=(obj_cls.__doc__ or "").strip(),
            properties=self._extract_properties(obj_cls),
            links=self._extract_links(obj_cls),
        )
        self._objects[obj_cls.__name__] = definition

    def list_objects(self) -> Dict[str, ObjectDefinition]:
        return dict(self._objects)

    # =========================================================================
    # LINK TYPE REGISTRATION (Phase 1.4)
    # =========================================================================

    def register_link_type(self, link_type: LinkTypeMetadata) -> None:
        """
        Register a LinkType definition.

        Args:
            link_type: LinkTypeMetadata instance to register

        Raises:
            ValueError: If link_type_id already registered
        """
        if link_type.link_type_id in self._link_types:
            raise ValueError(
                f"LinkType '{link_type.link_type_id}' is already registered"
            )
        self._link_types[link_type.link_type_id] = link_type

    def get_link_type(self, link_type_id: str) -> Optional[LinkTypeMetadata]:
        """Get a registered LinkType by ID."""
        return self._link_types.get(link_type_id)

    def list_link_types(self) -> Dict[str, LinkTypeMetadata]:
        """List all registered LinkTypes."""
        return dict(self._link_types)

    def list_link_types_for_object(self, object_type: str) -> List[LinkTypeMetadata]:
        """
        List all LinkTypes where the object is source or target.

        Args:
            object_type: ObjectType name to find links for

        Returns:
            List of LinkTypeMetadata where object is involved
        """
        return [
            lt for lt in self._link_types.values()
            if lt.source_type == object_type or lt.target_type == object_type
        ]

    def get_outgoing_links(self, object_type: str) -> List[LinkTypeMetadata]:
        """Get LinkTypes where object is the source."""
        return [
            lt for lt in self._link_types.values()
            if lt.source_type == object_type
        ]

    def get_incoming_links(self, object_type: str) -> List[LinkTypeMetadata]:
        """Get LinkTypes where object is the target."""
        return [
            lt for lt in self._link_types.values()
            if lt.target_type == object_type
        ]

    def validate_link_consistency(self) -> List[str]:
        """
        Validate that all LinkTypes reference registered ObjectTypes.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        object_names = set(self._objects.keys())

        for link_id, link_type in self._link_types.items():
            if link_type.source_type not in object_names:
                errors.append(
                    f"LinkType '{link_id}' references unknown source_type: "
                    f"'{link_type.source_type}'"
                )
            if link_type.target_type not in object_names:
                errors.append(
                    f"LinkType '{link_id}' references unknown target_type: "
                    f"'{link_type.target_type}'"
                )

        return errors

    def export_json(self, path: str | Path) -> None:
        """
        Export registry to JSON schema file with versioning metadata.

        The exported schema includes:
        - $schema: JSON Schema draft reference
        - version: Semantic version for schema tracking
        - generated_at: ISO timestamp of generation
        - generated_by: Generator identification
        - objects: All registered ObjectType definitions
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "version": SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": SCHEMA_GENERATED_BY,
            "objects": {
                name: {
                    "description": obj.description,
                    "properties": {
                        prop.name: {
                            "type": prop.property_type.value,
                            "required": prop.required,
                            "description": prop.description,
                            "constraints": self._extract_constraints(name, prop.name),
                        }
                        for prop in obj.properties.values()
                    },
                    "links": {
                        link_id: {
                            "target": link.target,
                            "cardinality": link.cardinality,
                            "reverse_link_id": link.reverse_link_id,
                            "description": link.description,
                            "backing_table_name": link.backing_table_name,
                            "is_materialized": link.is_materialized,
                        }
                        for link_id, link in obj.links.items()
                    },
                }
                for name, obj in sorted(self._objects.items())
            }
        }
        target.write_text(json.dumps(payload, indent=2))

    def export_links_json(self, path: str | Path) -> None:
        """
        Export LinkType definitions to JSON schema file.

        The exported schema includes:
        - $schema: JSON Schema draft reference
        - version: Semantic version for schema tracking
        - generated_at: ISO timestamp of generation
        - generated_by: Generator identification
        - link_types: All registered LinkType definitions
        - statistics: Summary of link types by cardinality
        - object_graph: Adjacency list of object relationships

        Example output:
            ```json
            {
                "link_types": {
                    "task_depends_on_task": {
                        "source_type": "Task",
                        "target_type": "Task",
                        "cardinality": "N:N",
                        "direction": "directed",
                        "on_delete": "CASCADE",
                        ...
                    }
                },
                "statistics": {
                    "total": 5,
                    "by_cardinality": {"1:N": 3, "N:N": 2}
                },
                "object_graph": {
                    "Task": {
                        "outgoing": ["task_depends_on_task"],
                        "incoming": ["task_depends_on_task"]
                    }
                }
            }
            ```
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        # Build link types section
        link_types_payload = {}
        for link_id, link_type in sorted(self._link_types.items()):
            link_types_payload[link_id] = {
                "source_type": link_type.source_type,
                "target_type": link_type.target_type,
                "cardinality": link_type.cardinality,
                "direction": link_type.direction.value if link_type.direction else "directed",
                "on_delete": link_type.on_delete.value if link_type.on_delete else None,
                "on_update": link_type.on_update.value if link_type.on_update else None,
                "description": link_type.description,
                "is_materialized": link_type.is_materialized,
                "backing_table_name": link_type.backing_table_name,
                "reverse_link_id": link_type.reverse_link_id,
                "constraints": {
                    "min_cardinality": link_type.constraints.min_cardinality if link_type.constraints else None,
                    "max_cardinality": link_type.constraints.max_cardinality if link_type.constraints else None,
                    "unique_target": link_type.constraints.unique_target if link_type.constraints else True,
                    "required": link_type.constraints.required if link_type.constraints else False,
                    "allowed_source_statuses": link_type.constraints.allowed_source_statuses if link_type.constraints else ["active"],
                    "allowed_target_statuses": link_type.constraints.allowed_target_statuses if link_type.constraints else ["active"],
                } if link_type.constraints else None,
            }

        # Build statistics
        cardinality_counts: Dict[str, int] = {}
        for lt in self._link_types.values():
            cardinality_counts[lt.cardinality] = cardinality_counts.get(lt.cardinality, 0) + 1

        statistics = {
            "total": len(self._link_types),
            "by_cardinality": cardinality_counts,
            "materialized": sum(1 for lt in self._link_types.values() if lt.is_materialized),
            "with_backing_table": sum(1 for lt in self._link_types.values() if lt.backing_table_name),
        }

        # Build object graph (adjacency list)
        object_graph: Dict[str, Dict[str, List[str]]] = {}
        for link_id, lt in self._link_types.items():
            # Source object
            if lt.source_type not in object_graph:
                object_graph[lt.source_type] = {"outgoing": [], "incoming": []}
            object_graph[lt.source_type]["outgoing"].append(link_id)

            # Target object
            if lt.target_type not in object_graph:
                object_graph[lt.target_type] = {"outgoing": [], "incoming": []}
            object_graph[lt.target_type]["incoming"].append(link_id)

        payload = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "version": SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": SCHEMA_GENERATED_BY,
            "link_types": link_types_payload,
            "statistics": statistics,
            "object_graph": object_graph,
        }

        target.write_text(json.dumps(payload, indent=2))

    def _extract_constraints(self, obj_name: str, prop_name: str) -> Dict[str, Any]:
        """Extract field constraints from Pydantic model for a property."""
        # This would need access to the original class to extract Field constraints
        # For now, return empty dict - can be enhanced later
        return {}

    def _extract_properties(self, obj_cls: Type[OntologyObject]) -> Dict[str, PropertyDefinition]:
        properties: Dict[str, PropertyDefinition] = {}
        for name, field in obj_cls.model_fields.items():
            description = field.description or ""
            field_type = self._normalize_type(field.annotation)
            prop_type = self._map_property_type(field_type)
            properties[name] = PropertyDefinition(
                name=name,
                property_type=prop_type,
                required=field.is_required(),
                description=description,
            )
        return properties

    def _extract_links(self, obj_cls: Type[OntologyObject]) -> Dict[str, LinkDefinition]:
        links: Dict[str, LinkDefinition] = {}
        for name, value in obj_cls.__dict__.items():
            if isinstance(value, Link):
                target = value.target if isinstance(value.target, str) else value.target.__name__
                links[name] = LinkDefinition(
                    link_type_id=value.link_type_id,
                    target=target,
                    cardinality=value.cardinality.value,
                    reverse_link_id=value.reverse_link_id,
                    description=value.description,
                    backing_table_name=value.backing_table_name,
                    is_materialized=value.is_materialized,
                )
        return links

    def _normalize_type(self, annotation: Any) -> Any:
        origin = get_origin(annotation)
        if origin is None:
            return annotation
        args = get_args(annotation)
        if origin is Union:
            non_none = [a for a in args if a is not type(None)]
            return non_none[0] if non_none else args[0]
        if origin is list:
            return list
        if origin is dict:
            return dict
        if origin is tuple:
            return list
        return origin

    def _map_property_type(self, annotation: Any) -> PropertyType:
        if annotation in (str,):
            return PropertyType.STRING
        if annotation in (int,):
            return PropertyType.INTEGER
        if annotation in (float,):
            return PropertyType.DOUBLE
        if annotation in (bool,):
            return PropertyType.BOOLEAN
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return PropertyType.STRING
        if annotation in (dict,):
            return PropertyType.STRUCT
        if annotation in (list,):
            return PropertyType.ARRAY
        if getattr(annotation, "__name__", "") in ("datetime",):
            return PropertyType.TIMESTAMP
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return PropertyType.STRUCT
        return PropertyType.STRING


_REGISTRY = OntologyRegistry()
_INTERFACE_REGISTRY = InterfaceRegistry()
_SHARED_PROPERTY_REGISTRY = SharedPropertyRegistry()


def register_object_type(cls: Type[OntologyObject]) -> Type[OntologyObject]:
    """Decorator to register an ObjectType with the global registry."""
    _REGISTRY.register_object(cls)
    return cls


def register_link_type(link_type: LinkTypeMetadata) -> LinkTypeMetadata:
    """
    Register a LinkType with the global registry.

    Can be used as a function or with a pattern:

    Example:
        ```python
        # Direct registration
        task_depends_on_task = register_link_type(LinkTypeMetadata(
            link_type_id="task_depends_on_task",
            source_type="Task",
            target_type="Task",
            cardinality="N:N",
        ))
        ```
    """
    _REGISTRY.register_link_type(link_type)
    return link_type


def get_registry() -> OntologyRegistry:
    """Get the global OntologyRegistry instance."""
    return _REGISTRY


def get_interface_registry() -> InterfaceRegistry:
    """Get the global InterfaceRegistry instance."""
    return _INTERFACE_REGISTRY


def register_interface(interface: InterfaceDefinition) -> InterfaceDefinition:
    """
    Register an interface with the global registry.

    Example:
        ```python
        IVersionable = register_interface(InterfaceDefinition(
            interface_id="IVersionable",
            description="Versionable objects",
            required_properties=[
                PropertySpec(name="version", type_hint="int"),
            ],
        ))
        ```
    """
    _INTERFACE_REGISTRY.register_interface(interface)
    return interface


# =============================================================================
# SHARED PROPERTY REGISTRY FUNCTIONS
# =============================================================================


def get_shared_property_registry() -> SharedPropertyRegistry:
    """Get the global SharedPropertyRegistry instance."""
    return _SHARED_PROPERTY_REGISTRY


def register_shared_property(
    property_def: SharedPropertyDefinition,
) -> SharedPropertyDefinition:
    """
    Register a shared property with the global registry.

    Args:
        property_def: SharedPropertyDefinition to register

    Returns:
        The registered SharedPropertyDefinition

    Example:
        ```python
        created_at = register_shared_property(SharedPropertyDefinition(
            property_id="created_at",
            description="Creation timestamp",
            type_hint="datetime",
            category="audit",
        ))
        ```
    """
    _SHARED_PROPERTY_REGISTRY.register_property(property_def)
    return property_def


def get_shared_property(property_id: str) -> Optional[SharedPropertyDefinition]:
    """
    Get a shared property by ID.

    Args:
        property_id: ID of the shared property

    Returns:
        SharedPropertyDefinition or None if not found
    """
    return _SHARED_PROPERTY_REGISTRY.get_property(property_id)


def list_shared_properties() -> List[SharedPropertyDefinition]:
    """List all registered shared properties."""
    return _SHARED_PROPERTY_REGISTRY.list_properties()


def list_shared_property_ids() -> List[str]:
    """List all registered shared property IDs."""
    return _SHARED_PROPERTY_REGISTRY.list_property_ids()


def get_shared_property_usages(property_id: str) -> List[str]:
    """
    Get all ObjectType names that use a shared property.

    Args:
        property_id: ID of the shared property

    Returns:
        List of ObjectType names
    """
    return _SHARED_PROPERTY_REGISTRY.get_usages_for_property(property_id)


def export_shared_properties(path: str | Path) -> None:
    """
    Export shared properties registry to JSON.

    Args:
        path: Output file path
    """
    import json
    from pathlib import Path

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": SCHEMA_GENERATED_BY,
        **_SHARED_PROPERTY_REGISTRY.export_dict(),
    }

    target.write_text(json.dumps(payload, indent=2, default=str))


def load_default_shared_properties() -> None:
    """Load all built-in shared properties into the registry."""
    for prop_def in BUILTIN_SHARED_PROPERTIES:
        if not _SHARED_PROPERTY_REGISTRY.has_property(prop_def.property_id):
            _SHARED_PROPERTY_REGISTRY.register_property(prop_def)


def load_default_objects() -> None:
    """Load all default ObjectTypes into the registry."""
    from lib.oda.ontology.objects import proposal  # noqa: F401
    from lib.oda.ontology.objects import learning  # noqa: F401
    from lib.oda.ontology.objects import core_definitions  # noqa: F401
    from lib.oda.ontology.objects import task_types  # noqa: F401
    # Phase 2.2 ObjectTypes
    from lib.oda.ontology.objects import workspace  # noqa: F401
    from lib.oda.ontology.objects import session  # noqa: F401
    from lib.oda.ontology.objects import learner  # noqa: F401
    from lib.oda.ontology.objects import course  # noqa: F401
    from lib.oda.ontology.objects import assessment  # noqa: F401
    from lib.oda.ontology.objects import resource  # noqa: F401


def load_default_link_types() -> None:
    """Load all default LinkTypes into the registry."""
    # Link types can be defined in a dedicated module
    # from lib.oda.ontology.links import default_links  # noqa: F401
    pass  # To be implemented when link definitions are created


def export_registry(path: str | Path) -> None:
    """Export the full registry to JSON."""
    load_default_objects()
    _REGISTRY.export_json(path)


def export_links_registry(path: str | Path) -> None:
    """Export the LinkType registry to JSON."""
    load_default_objects()
    load_default_link_types()
    _REGISTRY.export_links_json(path)


if __name__ == "__main__":
    from importlib import import_module

    registry_module = import_module("scripts.ontology.registry")
    registry_module.export_registry(Path(".agent/schemas/ontology_registry.json"))
    registry_module.export_links_registry(Path(".agent/schemas/link_registry.json"))
