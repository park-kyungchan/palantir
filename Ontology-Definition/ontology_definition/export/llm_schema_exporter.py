"""
LLM Schema Exporter - Export schemas in LLM-friendly formats.

Generates schema representations optimized for use with Large Language Models:
    - Compact YAML-like format for context efficiency
    - Markdown documentation for human-AI collaboration
    - TypeScript-style type definitions
    - Natural language descriptions

These formats are designed to fit within LLM context windows while
providing maximum semantic information about the ontology.

Example:
    from ontology_definition.export import LLMSchemaExporter

    exporter = LLMSchemaExporter()

    # Generate compact schema for LLM context
    compact = exporter.to_compact_yaml(employee_type)

    # Generate markdown documentation
    docs = exporter.to_markdown(employee_type)

    # Generate TypeScript-style types
    ts_types = exporter.to_typescript_types(employee_type)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ontology_definition.registry.ontology_registry import OntologyRegistry
    from ontology_definition.types.object_type import ObjectType


class LLMSchemaExporter:
    """
    Exporter for LLM-friendly schema representations.

    Generates compact, readable schema formats optimized for
    inclusion in LLM prompts and context windows.
    """

    # TypeScript type mapping
    TS_TYPE_MAP: dict[str, str] = {
        "STRING": "string",
        "BOOLEAN": "boolean",
        "INTEGER": "number",
        "LONG": "number",
        "FLOAT": "number",
        "DOUBLE": "number",
        "DECIMAL": "string",
        "DATE": "string",
        "TIMESTAMP": "string",
        "BYTE": "number",
        "SHORT": "number",
        "BINARY": "string",
        "ATTACHMENT": "string",
        "GEOHASH": "string",
        "GEOPOINT": "{ latitude: number; longitude: number }",
        "GEOSHAPE": "object",
        "TIMESERIES": "Array<{ timestamp: string; value: number }>",
        "ARRAY": "Array",
        "STRUCT": "object",
        "OBJECT_REFERENCE": "string",
        "MARKING": "string",
    }

    def __init__(
        self,
        include_descriptions: bool = True,
        max_description_length: int = 100,
    ) -> None:
        """
        Initialize the LLMSchemaExporter.

        Args:
            include_descriptions: Include field descriptions.
            max_description_length: Truncate descriptions at this length.
        """
        self._include_descriptions = include_descriptions
        self._max_desc_length = max_description_length

    def _truncate(self, text: str | None, max_len: int) -> str:
        """Truncate text with ellipsis if needed."""
        if not text:
            return ""
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    def _get_type_string(self, prop: Any) -> str:
        """Get type string from property definition."""
        if not hasattr(prop, "data_type") or not prop.data_type:
            return "string"

        data_type = prop.data_type.type
        if not data_type:
            return "string"

        type_name = data_type.value
        ts_type = self.TS_TYPE_MAP.get(type_name, "any")

        # Handle array types
        if type_name == "ARRAY" and prop.data_type.item_type:
            item_type = self.TS_TYPE_MAP.get(prop.data_type.item_type.value, "any")
            return f"Array<{item_type}>"

        return ts_type

    def to_compact_yaml(
        self,
        object_type: ObjectType,
    ) -> str:
        """
        Generate compact YAML-like representation for LLM context.

        Optimized for token efficiency while preserving semantic meaning.

        Args:
            object_type: The ObjectType to export.

        Returns:
            Compact YAML-like string.
        """
        lines: list[str] = []
        lines.append(f"# {object_type.api_name}")

        if object_type.description:
            desc = self._truncate(object_type.description, self._max_desc_length)
            lines.append(f"# {desc}")

        lines.append(f"pk: {object_type.primary_key.property_api_name}")

        if object_type.interfaces:
            lines.append(f"implements: [{', '.join(object_type.interfaces)}]")

        lines.append("properties:")

        for prop in object_type.properties:
            type_str = self._get_type_string(prop)

            # Build property line
            flags: list[str] = []
            if prop.constraints and prop.constraints.required:
                flags.append("required")
            if prop.constraints and prop.constraints.unique:
                flags.append("unique")
            if prop.is_mandatory_control:
                flags.append("MCP")  # Mandatory Control Property

            flag_str = f" [{', '.join(flags)}]" if flags else ""

            if self._include_descriptions and prop.description:
                desc = self._truncate(prop.description, 60)
                lines.append(f"  {prop.api_name}: {type_str}{flag_str}  # {desc}")
            else:
                lines.append(f"  {prop.api_name}: {type_str}{flag_str}")

        return "\n".join(lines)

    def to_markdown(
        self,
        object_type: ObjectType,
    ) -> str:
        """
        Generate Markdown documentation for an ObjectType.

        Human-readable format suitable for documentation or AI-assisted development.

        Args:
            object_type: The ObjectType to export.

        Returns:
            Markdown formatted string.
        """
        lines: list[str] = []

        # Header
        lines.append(f"## {object_type.display_name}")
        lines.append(f"**API Name:** `{object_type.api_name}`")

        if object_type.description:
            lines.append(f"\n{object_type.description}")

        # Status and endorsement
        status_line = f"**Status:** {object_type.status.value}"
        if object_type.endorsed:
            status_line += " ✓ Endorsed"
        lines.append(f"\n{status_line}")

        # Primary key
        lines.append(f"\n**Primary Key:** `{object_type.primary_key.property_api_name}`")

        # Interfaces
        if object_type.interfaces:
            interfaces = ", ".join(f"`{i}`" for i in object_type.interfaces)
            lines.append(f"\n**Implements:** {interfaces}")

        # Properties table
        lines.append("\n### Properties")
        lines.append("")
        lines.append("| Name | Type | Required | Description |")
        lines.append("|------|------|----------|-------------|")

        for prop in object_type.properties:
            type_str = self._get_type_string(prop)
            required = "✓" if prop.constraints and prop.constraints.required else ""
            desc = self._truncate(prop.description or "", 50)
            lines.append(f"| `{prop.api_name}` | {type_str} | {required} | {desc} |")

        # Security info if present
        if object_type.security_config:
            mcp_props = object_type.get_mandatory_control_properties()
            if mcp_props:
                lines.append("\n### Security")
                lines.append("**Mandatory Control Properties:**")
                for mcp in mcp_props:
                    lines.append(f"- `{mcp.api_name}`")

        return "\n".join(lines)

    def to_typescript_types(
        self,
        object_type: ObjectType,
    ) -> str:
        """
        Generate TypeScript-style type definitions.

        Useful for code generation or TypeScript documentation.

        Args:
            object_type: The ObjectType to export.

        Returns:
            TypeScript interface definition.
        """
        lines: list[str] = []

        # JSDoc comment
        if object_type.description:
            lines.append("/**")
            lines.append(f" * {object_type.description}")
            lines.append(" */")

        lines.append(f"interface {object_type.api_name} {{")

        for prop in object_type.properties:
            type_str = self._get_type_string(prop)
            optional = "" if prop.constraints and prop.constraints.required else "?"

            # Property JSDoc
            if self._include_descriptions and prop.description:
                lines.append(f"  /** {prop.description} */")

            lines.append(f"  {prop.api_name}{optional}: {type_str};")

        lines.append("}")

        return "\n".join(lines)

    def to_natural_language(
        self,
        object_type: ObjectType,
    ) -> str:
        """
        Generate natural language description of an ObjectType.

        Suitable for inclusion in LLM prompts as context.

        Args:
            object_type: The ObjectType to export.

        Returns:
            Natural language description.
        """
        # Build property descriptions
        required_props: list[str] = []
        optional_props: list[str] = []

        for prop in object_type.properties:
            type_str = self._get_type_string(prop)
            desc = f"{prop.api_name} ({type_str})"

            if prop.description:
                desc += f" - {self._truncate(prop.description, 50)}"

            if prop.constraints and prop.constraints.required:
                required_props.append(desc)
            else:
                optional_props.append(desc)

        # Build description
        text = f"The {object_type.display_name} ({object_type.api_name}) "

        if object_type.description:
            text += f"{object_type.description.rstrip('.')}. "
        else:
            text += "is an entity type. "

        text += f"It is identified by {object_type.primary_key.property_api_name}. "

        if required_props:
            text += f"Required fields: {', '.join(required_props)}. "

        if optional_props:
            text += f"Optional fields: {', '.join(optional_props)}."

        if object_type.interfaces:
            text += f" Implements: {', '.join(object_type.interfaces)}."

        return text

    def export_all_compact(
        self,
        registry: OntologyRegistry | None = None,
        separator: str = "\n---\n",
    ) -> str:
        """
        Export all ObjectTypes in compact format.

        Args:
            registry: OntologyRegistry to use. Uses global if None.
            separator: Separator between type definitions.

        Returns:
            Combined compact representation.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        schemas = []
        for object_type in registry.list_object_types():
            schemas.append(self.to_compact_yaml(object_type))

        return separator.join(schemas)

    def export_all_markdown(
        self,
        registry: OntologyRegistry | None = None,
    ) -> str:
        """
        Export all ObjectTypes as Markdown documentation.

        Args:
            registry: OntologyRegistry to use. Uses global if None.

        Returns:
            Combined Markdown documentation.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        lines: list[str] = ["# Ontology Schema Documentation\n"]

        # Table of contents
        lines.append("## Table of Contents\n")
        for object_type in registry.list_object_types():
            lines.append(f"- [{object_type.display_name}](#{object_type.api_name.lower()})")
        lines.append("")

        # Type documentation
        for object_type in registry.list_object_types():
            lines.append(self.to_markdown(object_type))
            lines.append("")

        return "\n".join(lines)

    def export_all_typescript(
        self,
        registry: OntologyRegistry | None = None,
    ) -> str:
        """
        Export all ObjectTypes as TypeScript definitions.

        Args:
            registry: OntologyRegistry to use. Uses global if None.

        Returns:
            Combined TypeScript definitions.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        lines: list[str] = [
            "// Auto-generated TypeScript definitions for Ontology types",
            "// Generated by ontology_definition package",
            "",
        ]

        for object_type in registry.list_object_types():
            lines.append(self.to_typescript_types(object_type))
            lines.append("")

        return "\n".join(lines)

    def export_to_file(
        self,
        content: str,
        path: str | Path,
    ) -> Path:
        """Export content to a file."""
        path = Path(path)
        path.write_text(content, encoding="utf-8")
        return path


# Convenience functions
def to_compact_yaml(object_type: ObjectType) -> str:
    """Generate compact YAML representation using default exporter."""
    return LLMSchemaExporter().to_compact_yaml(object_type)


def to_markdown(object_type: ObjectType) -> str:
    """Generate Markdown documentation using default exporter."""
    return LLMSchemaExporter().to_markdown(object_type)


def to_typescript(object_type: ObjectType) -> str:
    """Generate TypeScript types using default exporter."""
    return LLMSchemaExporter().to_typescript_types(object_type)
