"""
JSON Schema Exporter - Export ontology definitions to JSON Schema format.

Generates JSON Schema (Draft 2020-12) representations of ontology types.
Useful for:
    - Generating validation schemas for external systems
    - Documentation generation
    - OpenAPI/Swagger integration
    - Form generation from schemas

Example:
    from ontology_definition.export import JsonSchemaExporter

    exporter = JsonSchemaExporter()

    # Generate JSON Schema for an ObjectType's instance data
    schema = exporter.generate_instance_schema(employee_type)

    # Generate schema for all ObjectTypes
    schemas = exporter.generate_all_instance_schemas()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ontology_definition.registry.ontology_registry import OntologyRegistry
    from ontology_definition.types.object_type import ObjectType
    from ontology_definition.types.property_def import PropertyDefinition


class JsonSchemaExporter:
    """
    Exporter for JSON Schema format.

    Generates JSON Schemas that can validate instance data
    conforming to ObjectType definitions.
    """

    # Mapping from ontology DataType to JSON Schema type
    TYPE_MAPPING: dict[str, dict[str, Any]] = {
        "STRING": {"type": "string"},
        "BOOLEAN": {"type": "boolean"},
        "INTEGER": {"type": "integer"},
        "LONG": {"type": "integer", "format": "int64"},
        "FLOAT": {"type": "number", "format": "float"},
        "DOUBLE": {"type": "number", "format": "double"},
        "DECIMAL": {"type": "string", "format": "decimal"},
        "DATE": {"type": "string", "format": "date"},
        "TIMESTAMP": {"type": "string", "format": "date-time"},
        "BYTE": {"type": "integer", "minimum": -128, "maximum": 127},
        "SHORT": {"type": "integer", "minimum": -32768, "maximum": 32767},
        "BINARY": {"type": "string", "contentEncoding": "base64"},
        "ATTACHMENT": {"type": "string", "format": "uri"},
        "GEOHASH": {"type": "string"},
        "GEOPOINT": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "required": ["latitude", "longitude"],
        },
        "GEOSHAPE": {"type": "object"},
        "TIMESERIES": {"type": "array"},
        "ARRAY": {"type": "array"},
        "STRUCT": {"type": "object"},
        "OBJECT_REFERENCE": {"type": "string"},
        "MARKING": {"type": "string"},
    }

    def __init__(
        self,
        schema_id_base: str = "https://ontology.palantir.local/schemas",
        draft_version: str = "2020-12",
    ) -> None:
        """
        Initialize the JsonSchemaExporter.

        Args:
            schema_id_base: Base URI for schema $id fields.
            draft_version: JSON Schema draft version to target.
        """
        self._schema_id_base = schema_id_base
        self._draft_version = draft_version

    def _get_schema_dialect(self) -> str:
        """Get the $schema dialect URL."""
        return f"https://json-schema.org/draft/{self._draft_version}/schema"

    def _property_to_json_schema(
        self, prop: PropertyDefinition
    ) -> dict[str, Any]:
        """Convert a PropertyDefinition to JSON Schema property definition."""
        schema: dict[str, Any] = {}

        # Get base type
        if prop.data_type and prop.data_type.type:
            data_type_name = prop.data_type.type.value
            base_schema = self.TYPE_MAPPING.get(data_type_name, {"type": "string"})
            schema.update(base_schema)

            # Handle array types
            if data_type_name == "ARRAY" and prop.data_type.item_type:
                item_type_name = prop.data_type.item_type.value
                item_schema = self.TYPE_MAPPING.get(item_type_name, {"type": "string"})
                schema["items"] = item_schema

            # Handle struct types
            if data_type_name == "STRUCT" and prop.data_type.struct_definition:
                schema["additionalProperties"] = True  # Allow any struct fields
        else:
            schema["type"] = "string"

        # Add description
        if prop.description:
            schema["description"] = prop.description

        # Add constraints
        if prop.constraints:
            constraints = prop.constraints

            # String constraints
            if schema.get("type") == "string":
                if constraints.min_length is not None:
                    schema["minLength"] = constraints.min_length
                if constraints.max_length is not None:
                    schema["maxLength"] = constraints.max_length
                if constraints.pattern:
                    schema["pattern"] = constraints.pattern

            # Numeric constraints
            if schema.get("type") in ("integer", "number"):
                if constraints.min_value is not None:
                    schema["minimum"] = constraints.min_value
                if constraints.max_value is not None:
                    schema["maximum"] = constraints.max_value

            # Enum constraints
            if constraints.allowed_values:
                schema["enum"] = constraints.allowed_values

        return schema

    def generate_instance_schema(
        self,
        object_type: ObjectType,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """
        Generate JSON Schema for validating instance data of an ObjectType.

        Args:
            object_type: The ObjectType to generate schema for.
            include_metadata: Include schema metadata ($id, title, etc.)

        Returns:
            JSON Schema dictionary.
        """
        schema: dict[str, Any] = {
            "$schema": self._get_schema_dialect(),
            "type": "object",
        }

        if include_metadata:
            schema["$id"] = f"{self._schema_id_base}/{object_type.api_name}.schema.json"
            schema["title"] = object_type.display_name
            if object_type.description:
                schema["description"] = object_type.description

        # Generate properties
        properties: dict[str, Any] = {}
        required: list[str] = []

        for prop in object_type.properties:
            properties[prop.api_name] = self._property_to_json_schema(prop)

            # Check if required
            if prop.constraints and prop.constraints.required:
                required.append(prop.api_name)

        # Primary key is always required
        if object_type.primary_key.property_api_name not in required:
            required.append(object_type.primary_key.property_api_name)

        schema["properties"] = properties

        if required:
            schema["required"] = required

        # Additional properties allowed based on ObjectType settings
        schema["additionalProperties"] = False

        return schema

    def generate_all_instance_schemas(
        self,
        registry: OntologyRegistry | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Generate JSON Schemas for all ObjectTypes in registry.

        Args:
            registry: OntologyRegistry to use. Uses global if None.

        Returns:
            Dictionary mapping ObjectType apiName to JSON Schema.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        schemas: dict[str, dict[str, Any]] = {}

        for object_type in registry.list_object_types():
            schemas[object_type.api_name] = self.generate_instance_schema(object_type)

        return schemas

    def export_instance_schema(
        self,
        object_type: ObjectType,
        path: str | Path,
    ) -> Path:
        """
        Export instance schema to a file.

        Args:
            object_type: The ObjectType to generate schema for.
            path: File path to write to.

        Returns:
            Path to the written file.
        """
        path = Path(path)
        schema = self.generate_instance_schema(object_type)
        path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def export_all_instance_schemas(
        self,
        output_dir: str | Path,
        registry: OntologyRegistry | None = None,
    ) -> list[Path]:
        """
        Export all instance schemas to files.

        Args:
            output_dir: Directory to write schema files to.
            registry: OntologyRegistry to use. Uses global if None.

        Returns:
            List of created file paths.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files: list[Path] = []

        for object_type in registry.list_object_types():
            file_path = output_dir / f"{object_type.api_name}.schema.json"
            self.export_instance_schema(object_type, file_path)
            created_files.append(file_path)

        return created_files

    def generate_combined_schema(
        self,
        registry: OntologyRegistry | None = None,
    ) -> dict[str, Any]:
        """
        Generate a combined JSON Schema with all ObjectType definitions.

        Uses $defs to define each ObjectType schema as a reusable component.

        Args:
            registry: OntologyRegistry to use. Uses global if None.

        Returns:
            Combined JSON Schema dictionary.
        """
        if registry is None:
            from ontology_definition.registry.ontology_registry import get_registry

            registry = get_registry()

        schema: dict[str, Any] = {
            "$schema": self._get_schema_dialect(),
            "$id": f"{self._schema_id_base}/ontology.schema.json",
            "title": "Ontology Instance Schemas",
            "description": "Combined JSON Schemas for all ObjectType instances",
            "$defs": {},
        }

        for object_type in registry.list_object_types():
            # Generate schema without top-level metadata (will be in $defs)
            instance_schema = self.generate_instance_schema(
                object_type, include_metadata=False
            )
            instance_schema["title"] = object_type.display_name
            if object_type.description:
                instance_schema["description"] = object_type.description

            schema["$defs"][object_type.api_name] = instance_schema

        return schema


# Convenience functions
def generate_instance_schema(object_type: ObjectType) -> dict[str, Any]:
    """Generate JSON Schema for an ObjectType using default exporter."""
    return JsonSchemaExporter().generate_instance_schema(object_type)


def export_instance_schemas(
    output_dir: str | Path,
    registry: OntologyRegistry | None = None,
) -> list[Path]:
    """Export all instance schemas to files."""
    return JsonSchemaExporter().export_all_instance_schemas(output_dir, registry)
