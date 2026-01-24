"""
Export module - Schema export to various formats.

Provides exporters for different output formats:
    - FoundryExporter: Palantir Foundry JSON format (GAP-003 P2-HIGH)
    - JsonSchemaExporter: JSON Schema Draft 2020-12 format
    - LLMSchemaExporter: LLM-friendly representations (compact, markdown, TypeScript)

Example:
    from ontology_definition.export import (
        FoundryExporter,
        JsonSchemaExporter,
        LLMSchemaExporter,
    )

    # Export to Foundry format
    foundry_exporter = FoundryExporter()
    json_str = foundry_exporter.export_object_type(my_object_type)

    # Generate JSON Schema for validation
    schema_exporter = JsonSchemaExporter()
    schema = schema_exporter.generate_instance_schema(my_object_type)

    # Generate LLM-friendly format
    llm_exporter = LLMSchemaExporter()
    compact = llm_exporter.to_compact_yaml(my_object_type)
"""

from ontology_definition.export.foundry_exporter import (
    FoundryExporter,
    FoundryBatchExporter,
    ExportMetadata,
    export_registry_to_foundry,
)

from ontology_definition.export.json_schema_exporter import (
    JsonSchemaExporter,
    generate_instance_schema,
    export_instance_schemas,
)

from ontology_definition.export.llm_schema_exporter import (
    LLMSchemaExporter,
    to_compact_yaml,
    to_markdown,
    to_typescript,
)

__all__ = [
    # Foundry Exporter (GAP-003)
    "FoundryExporter",
    "FoundryBatchExporter",
    "ExportMetadata",
    "export_registry_to_foundry",
    # JSON Schema Exporter
    "JsonSchemaExporter",
    "generate_instance_schema",
    "export_instance_schemas",
    # LLM Schema Exporter
    "LLMSchemaExporter",
    "to_compact_yaml",
    "to_markdown",
    "to_typescript",
]
