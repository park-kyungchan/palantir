# Implementation: Action Knowledge Base Ontology

The Action Knowledge Base (KB) provides a structured representation of the Hancom Office OLE Automation manual. It defines the relationships between actions, parameter sets, and API methods.

## 1. Schema Definition (`lib/knowledge/schema.py`)

The KB is implemented using Pydantic models to ensure validation when ingesting manual data (e.g., from `ActionTable.pdf`).

### 1.1 Core Entities

- **ActionDefinition**: Represents an HWP API action (e.g., `InsertText`).
    - `action_id`: The string ID used in OLE calls.
    - `parameter_set_id`: Optional link to a required `ParameterSet`.
    - `requires_creation`: Flag for actions needing `CreateAction`.
- **ParameterSetDefinition**: Describes a collection of items used by an action (e.g., `CharShape`).
    - `items`: List of `ParameterItem` (ID, Type, Description).
- **EventDefinition**: For HWP Automation event handlers.
- **APIMethodDefinition / APIPropertyDefinition**: Metadata for the root automation object methods and properties.

### 1.2 ActionDatabase
The root container that groups all metadata into a single searchable entity.

```python
class ActionDatabase(BaseModel):
    actions: Dict[str, ActionDefinition]
    parameter_sets: Dict[str, ParameterSetDefinition]
    events: Dict[str, EventDefinition]
    methods: Dict[str, APIMethodDefinition]
    properties: Dict[str, APIPropertyDefinition]
```

## 2. Integration Pattern

The ontology is used by the **Compiler** to:
1.  **Validate Intent**: Verify if an IR component maps to a valid HWP Action.
2.  **Retrieve Parameters**: Lookup the necessary parameters for a given action.
3.  **Generate Scripts**: Provide documentation hints for generating OLE Automation code.
