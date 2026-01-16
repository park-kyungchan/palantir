"""
Orion ODA v4.0 - Schema to Prompt Converter
===========================================

Converts Pydantic models and ODA schemas to natural language descriptions.
Generates documentation for ObjectTypes and Actions suitable for LLM prompts.

This module provides:
- Pydantic model to natural language conversion
- Markdown documentation generation for ObjectTypes
- Action documentation for system prompts
- Field constraint extraction and description
"""

from __future__ import annotations

import inspect
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from lib.oda.ontology.ontology_types import OntologyObject, PropertyType
from lib.oda.ontology.actions import ActionType
from lib.oda.ontology.registry import get_registry

logger = logging.getLogger(__name__)


# =============================================================================
# TYPE DESCRIPTIONS
# =============================================================================


TYPE_DESCRIPTIONS = {
    "str": "text string",
    "string": "text string",
    "int": "integer number",
    "integer": "integer number",
    "float": "decimal number",
    "double": "decimal number",
    "bool": "true/false",
    "boolean": "true/false",
    "list": "array of values",
    "array": "array of values",
    "dict": "key-value mapping",
    "object": "key-value mapping",
    "datetime": "timestamp (ISO 8601 format)",
    "date": "date (YYYY-MM-DD format)",
    "Optional": "optional",
    "Any": "any type",
    "None": "null/empty",
}


PROPERTY_TYPE_DESCRIPTIONS = {
    PropertyType.STRING: "text string",
    PropertyType.INTEGER: "integer number",
    PropertyType.LONG: "large integer",
    PropertyType.FLOAT: "decimal number",
    PropertyType.DOUBLE: "high-precision decimal",
    PropertyType.BOOLEAN: "true or false",
    PropertyType.DATE: "date (YYYY-MM-DD)",
    PropertyType.TIMESTAMP: "timestamp (ISO 8601)",
    PropertyType.ARRAY: "list of values",
    PropertyType.STRUCT: "nested object",
    PropertyType.GEOPOINT: "geographic coordinates",
    PropertyType.GEOSHAPE: "geographic shape",
    PropertyType.TIMESERIES: "time-series data",
    PropertyType.VECTOR: "numerical vector",
}


# =============================================================================
# PYDANTIC MODEL CONVERTER
# =============================================================================


class PydanticToNaturalLanguage:
    """
    Converts Pydantic models to natural language descriptions.

    This converter extracts:
    - Field names and types
    - Field descriptions from docstrings
    - Constraints (min/max, patterns, etc.)
    - Optional/required status
    """

    @classmethod
    def describe_model(cls, model_class: Type[BaseModel]) -> str:
        """
        Generate a natural language description of a Pydantic model.

        Args:
            model_class: Pydantic model class

        Returns:
            Natural language description
        """
        lines = []

        # Model description
        model_doc = model_class.__doc__
        if model_doc:
            lines.append(model_doc.strip())
            lines.append("")

        # Fields
        lines.append("**Fields:**")
        lines.append("")

        for field_name, field_info in model_class.model_fields.items():
            field_desc = cls.describe_field(field_name, field_info)
            lines.append(f"- {field_desc}")

        return "\n".join(lines)

    @classmethod
    def describe_field(cls, name: str, field_info: FieldInfo) -> str:
        """
        Generate a natural language description of a field.

        Args:
            name: Field name
            field_info: Pydantic FieldInfo

        Returns:
            Field description string
        """
        parts = [f"**{name}**"]

        # Type description
        type_desc = cls._get_type_description(field_info.annotation)
        parts.append(f"({type_desc})")

        # Required/optional
        if field_info.is_required():
            parts.append("[required]")
        else:
            parts.append("[optional]")

        # Description
        if field_info.description:
            parts.append(f": {field_info.description}")

        # Constraints
        constraints = cls._extract_constraints(field_info)
        if constraints:
            parts.append(f"- Constraints: {', '.join(constraints)}")

        return " ".join(parts)

    @classmethod
    def _get_type_description(cls, annotation: Any) -> str:
        """Get natural language description of a type annotation."""
        if annotation is None:
            return "any"

        # Handle string annotations
        if isinstance(annotation, str):
            return TYPE_DESCRIPTIONS.get(annotation, annotation)

        # Get origin for generic types
        origin = get_origin(annotation)
        args = get_args(annotation)

        # Handle Optional
        if origin is Union:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                inner = cls._get_type_description(non_none[0])
                return f"optional {inner}"
            else:
                types = [cls._get_type_description(a) for a in non_none]
                return f"one of: {', '.join(types)}"

        # Handle List
        if origin is list:
            if args:
                inner = cls._get_type_description(args[0])
                return f"list of {inner}"
            return "list"

        # Handle Dict
        if origin is dict:
            if len(args) >= 2:
                key = cls._get_type_description(args[0])
                val = cls._get_type_description(args[1])
                return f"mapping of {key} to {val}"
            return "mapping"

        # Handle Enum
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            values = [e.value for e in annotation]
            if len(values) <= 5:
                return f"one of: {', '.join(str(v) for v in values)}"
            return f"enumeration ({len(values)} values)"

        # Handle basic types
        type_name = getattr(annotation, "__name__", str(annotation))
        return TYPE_DESCRIPTIONS.get(type_name, type_name)

    @classmethod
    def _extract_constraints(cls, field_info: FieldInfo) -> List[str]:
        """Extract constraint descriptions from field info."""
        constraints = []

        # Check metadata for constraints
        metadata = field_info.metadata or []

        for meta in metadata:
            meta_type = type(meta).__name__

            if meta_type == "Ge":
                constraints.append(f"minimum: {meta.ge}")
            elif meta_type == "Le":
                constraints.append(f"maximum: {meta.le}")
            elif meta_type == "Gt":
                constraints.append(f"greater than: {meta.gt}")
            elif meta_type == "Lt":
                constraints.append(f"less than: {meta.lt}")
            elif meta_type == "MinLen":
                constraints.append(f"min length: {meta.min_length}")
            elif meta_type == "MaxLen":
                constraints.append(f"max length: {meta.max_length}")
            elif hasattr(meta, "pattern"):
                constraints.append(f"pattern: {meta.pattern}")

        # Check json_schema_extra
        if field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if isinstance(extra, dict):
                if "minimum" in extra:
                    constraints.append(f"minimum: {extra['minimum']}")
                if "maximum" in extra:
                    constraints.append(f"maximum: {extra['maximum']}")
                if "minLength" in extra:
                    constraints.append(f"min length: {extra['minLength']}")
                if "maxLength" in extra:
                    constraints.append(f"max length: {extra['maxLength']}")
                if "pattern" in extra:
                    constraints.append(f"pattern: {extra['pattern']}")
                if "enum" in extra:
                    values = extra["enum"][:5]
                    constraints.append(f"values: {', '.join(str(v) for v in values)}")

        return constraints


# =============================================================================
# OBJECT TYPE DOCUMENTER
# =============================================================================


class ObjectTypeDocumenter:
    """
    Generates markdown documentation for ObjectTypes.

    Creates human-readable documentation suitable for:
    - System prompts
    - API documentation
    - Developer guides
    """

    def __init__(self):
        self._registry = get_registry()

    def document_object_type(
        self,
        object_type: Union[str, Type[OntologyObject]],
        include_examples: bool = True,
    ) -> str:
        """
        Generate markdown documentation for an ObjectType.

        Args:
            object_type: ObjectType name or class
            include_examples: Include example JSON

        Returns:
            Markdown documentation
        """
        # Get type name
        if isinstance(object_type, type):
            type_name = object_type.__name__
        else:
            type_name = object_type

        # Get definition from registry
        objects = self._registry.list_objects()
        obj_def = objects.get(type_name)

        if not obj_def:
            return f"ObjectType '{type_name}' not found in registry."

        lines = []

        # Title
        lines.append(f"## {type_name}")
        lines.append("")

        # Description
        if obj_def.description:
            lines.append(obj_def.description)
            lines.append("")

        # Properties section
        lines.append("### Properties")
        lines.append("")

        if obj_def.properties:
            lines.append("| Property | Type | Required | Description |")
            lines.append("|----------|------|----------|-------------|")

            for prop_name, prop_def in obj_def.properties.items():
                type_desc = PROPERTY_TYPE_DESCRIPTIONS.get(
                    prop_def.property_type,
                    prop_def.property_type.value,
                )
                required = "Yes" if prop_def.required else "No"
                description = prop_def.description or "-"
                lines.append(f"| `{prop_name}` | {type_desc} | {required} | {description} |")

            lines.append("")

        # Links section
        if obj_def.links:
            lines.append("### Relationships")
            lines.append("")

            for link_name, link_def in obj_def.links.items():
                lines.append(f"- **{link_name}**")
                lines.append(f"  - Target: `{link_def.target}`")
                lines.append(f"  - Cardinality: {link_def.cardinality}")
                if link_def.description:
                    lines.append(f"  - Description: {link_def.description}")
                lines.append("")

        # Example
        if include_examples:
            lines.append("### Example")
            lines.append("")
            lines.append("```json")
            lines.append(self._generate_example_json(obj_def))
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def document_all_types(self) -> str:
        """
        Generate documentation for all registered ObjectTypes.

        Returns:
            Complete markdown documentation
        """
        lines = ["# ODA ObjectType Reference", ""]
        lines.append("This document describes all ObjectTypes in the ontology.")
        lines.append("")

        objects = self._registry.list_objects()

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for name in sorted(objects.keys()):
            lines.append(f"- [{name}](#{name.lower()})")
        lines.append("")

        # Documentation for each type
        for name in sorted(objects.keys()):
            lines.append(self.document_object_type(name))
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _generate_example_json(self, obj_def) -> str:
        """Generate example JSON for an ObjectType."""
        example = {}

        for prop_name, prop_def in obj_def.properties.items():
            example[prop_name] = self._generate_example_value(
                prop_def.property_type, prop_name
            )

        import json
        return json.dumps(example, indent=2)

    def _generate_example_value(self, prop_type: PropertyType, name: str) -> Any:
        """Generate an example value for a property type."""
        if prop_type == PropertyType.STRING:
            return f"example_{name}"
        elif prop_type == PropertyType.INTEGER:
            return 42
        elif prop_type == PropertyType.LONG:
            return 1234567890
        elif prop_type in (PropertyType.FLOAT, PropertyType.DOUBLE):
            return 3.14
        elif prop_type == PropertyType.BOOLEAN:
            return True
        elif prop_type == PropertyType.DATE:
            return "2024-01-15"
        elif prop_type == PropertyType.TIMESTAMP:
            return "2024-01-15T10:30:00Z"
        elif prop_type == PropertyType.ARRAY:
            return ["item1", "item2"]
        elif prop_type == PropertyType.STRUCT:
            return {"key": "value"}
        elif prop_type == PropertyType.GEOPOINT:
            return {"lat": 37.7749, "lng": -122.4194}
        elif prop_type == PropertyType.VECTOR:
            return [0.1, 0.2, 0.3]
        else:
            return None


# =============================================================================
# ACTION DOCUMENTER
# =============================================================================


class ActionDocumenter:
    """
    Generates documentation for ODA Actions.

    Creates human-readable documentation for:
    - Available actions
    - Required parameters
    - Example usage
    """

    def __init__(self, registry=None):
        from lib.oda.ontology.actions import action_registry
        self._registry = registry or action_registry

    def document_action(
        self,
        action_type: Union[str, Type[ActionType]],
        include_examples: bool = True,
    ) -> str:
        """
        Generate markdown documentation for an Action.

        Args:
            action_type: Action API name or class
            include_examples: Include example usage

        Returns:
            Markdown documentation
        """
        # Get action class
        if isinstance(action_type, str):
            action_name = action_type
            action_cls = self._registry.get(action_name)
        else:
            action_cls = action_type
            action_name = action_cls.api_name

        if not action_cls:
            return f"Action '{action_name}' not found in registry."

        lines = []

        # Title
        lines.append(f"## `{action_name}`")
        lines.append("")

        # Badges
        metadata = self._registry.get_metadata(action_name)
        if metadata and metadata.requires_proposal:
            lines.append("> **Requires Approval** - This action creates a proposal")
            lines.append("")

        # Description
        doc = action_cls.__doc__
        if doc:
            lines.append(doc.strip())
            lines.append("")

        # Parameters
        schema = action_cls.get_parameter_schema()
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        if properties:
            lines.append("### Parameters")
            lines.append("")
            lines.append("| Parameter | Type | Required | Description |")
            lines.append("|-----------|------|----------|-------------|")

            for param_name, param_info in properties.items():
                is_required = "Yes" if param_name in required else "No"
                param_type = param_info.get("type", "any")

                # Check for enum
                if "enum" in param_info:
                    values = param_info["enum"][:3]
                    param_type = f"enum: {', '.join(str(v) for v in values)}..."

                description = param_info.get("description", "-")
                lines.append(
                    f"| `{param_name}` | {param_type} | {is_required} | {description} |"
                )

            lines.append("")

        # Example
        if include_examples:
            lines.append("### Example Usage")
            lines.append("")
            lines.append("```python")
            lines.append(f'await executor.execute_action("{action_name}", {{')
            for param in required[:3]:
                lines.append(f'    "{param}": "value",')
            lines.append("})")
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def document_all_actions(self, namespace: Optional[str] = None) -> str:
        """
        Generate documentation for all registered Actions.

        Args:
            namespace: Optional namespace filter

        Returns:
            Complete markdown documentation
        """
        lines = ["# ODA Action Reference", ""]
        lines.append("This document describes all available Actions.")
        lines.append("")

        all_actions = self._registry.list_actions()
        hazardous = set(self._registry.get_hazardous_actions())

        # Apply namespace filter
        if namespace:
            all_actions = [a for a in all_actions if a.startswith(namespace)]

        # Group by namespace
        namespaces: Dict[str, List[str]] = {}
        for action in sorted(all_actions):
            ns = action.split(".")[0] if "." in action else "general"
            if ns not in namespaces:
                namespaces[ns] = []
            namespaces[ns].append(action)

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for ns in sorted(namespaces.keys()):
            lines.append(f"### {ns.upper()}")
            for action in namespaces[ns]:
                badge = " [APPROVAL]" if action in hazardous else ""
                lines.append(f"- [`{action}`](#{action.replace('.', '')}){badge}")
            lines.append("")

        # Documentation for each action
        for ns in sorted(namespaces.keys()):
            lines.append(f"# {ns.upper()} Actions")
            lines.append("")
            for action in namespaces[ns]:
                lines.append(self.document_action(action))
                lines.append("---")
                lines.append("")

        return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def describe_model(model_class: Type[BaseModel]) -> str:
    """Get natural language description of a Pydantic model."""
    return PydanticToNaturalLanguage.describe_model(model_class)


def document_object_type(type_name: str) -> str:
    """Get markdown documentation for an ObjectType."""
    return ObjectTypeDocumenter().document_object_type(type_name)


def document_action(action_name: str) -> str:
    """Get markdown documentation for an Action."""
    return ActionDocumenter().document_action(action_name)


def generate_schema_prompt(
    include_objects: bool = True,
    include_actions: bool = True,
    object_filter: Optional[List[str]] = None,
    action_namespace: Optional[str] = None,
) -> str:
    """
    Generate a complete schema prompt for LLM context.

    Args:
        include_objects: Include ObjectType documentation
        include_actions: Include Action documentation
        object_filter: Only include these ObjectTypes
        action_namespace: Only include actions from this namespace

    Returns:
        Complete markdown schema prompt
    """
    sections = []

    if include_objects:
        obj_doc = ObjectTypeDocumenter()
        if object_filter:
            for obj_name in object_filter:
                sections.append(obj_doc.document_object_type(obj_name))
        else:
            sections.append(obj_doc.document_all_types())

    if include_actions:
        act_doc = ActionDocumenter()
        sections.append(act_doc.document_all_actions(namespace=action_namespace))

    return "\n\n".join(sections)
