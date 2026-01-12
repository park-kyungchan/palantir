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
