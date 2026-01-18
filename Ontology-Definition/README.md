# ontology_definition

A Python package for defining and managing Palantir Foundry-compatible ontology schemas.

## Features

- **Type Definitions**: ObjectType, LinkType, ActionType, Interface, StructType
- **Validation**: JSON Schema (Draft 2020-12) + Pydantic runtime validation
- **Registry**: Thread-safe singleton registry with decorators
- **Export**: Foundry JSON, JSON Schema, LLM-friendly formats
- **Import**: Foundry JSON with version migration support

## Installation

```bash
pip install ontology_definition
```

## Quick Start

```python
from ontology_definition import (
    ObjectType,
    PropertyDefinition,
    PrimaryKeyDefinition,
    DataType,
    DataTypeDef,
)

# Define an ObjectType
employee = ObjectType(
    api_name="Employee",
    display_name="Employee",
    primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
    properties=[
        PropertyDefinition(
            api_name="employeeId",
            display_name="Employee ID",
            data_type=DataTypeDef(type=DataType.STRING),
        ),
        PropertyDefinition(
            api_name="name",
            display_name="Name",
            data_type=DataTypeDef(type=DataType.STRING),
        ),
    ],
)

# Export to Foundry JSON
from ontology_definition.export import FoundryExporter
exporter = FoundryExporter()
json_str = exporter.export_object_type(employee)
```

## Package Structure

```
ontology_definition/
├── core/           # Base classes, enums, identifiers
├── constraints/    # Property constraints, MandatoryControl
├── types/          # ObjectType, LinkType, ActionType, etc.
├── security/       # RestrictedViewPolicy, access control
├── registry/       # OntologyRegistry, decorators
├── validation/     # Schema, cross-ref, runtime validation
├── export/         # Foundry, JSON Schema, LLM exporters
├── import_/        # Foundry import, version migration
└── schemas/        # Bundled JSON Schema files
```

## License

MIT
