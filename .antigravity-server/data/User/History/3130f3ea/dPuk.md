# HWP Action and Knowledge Ontology

The HWP Action and Knowledge Ontology provides a comprehensive programmatic representation of the Hancom Office API. It bridge the gap between human-readable manuals and executable Python models.

## 1. Action Knowledge Base (KB) Schema (`lib/knowledge/schema.py`)

The KB is implemented using Pydantic models to ensure validation when ingesting manual data.

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

## 2. Runtime Action Models (`lib/models.py`)

These models serve as the "Instruction Set" for document reconstruction. Every `HwpAction` is a Pydantic model with validated parameters.

### 2.1 Key Action Examples
- `InsertText`: Inserts raw text content.
- `SetFontSize / SetFontBold / SetAlign / SetLineSpacing`: Formatting controls.
- `CreateTable / MoveToCell / SetCellBorder`: Table construction and styling.
- `InsertEquation`: Inserts math formulas using HWP script format.
- `InsertTextBox`: Absolute positioning (`x`, `y` in mm) for text boxes.

### 2.2 Type Mapping Matrix (PIT to Python)
| HWP Type | Description | Python Type |
| :--- | :--- | :--- |
| **PIT_BSTR** | Basic String | `str` |
| **PIT_UI / PIT_I** | Integer | `int` |
| **PIT_BOOL** | Boolean | `bool` |
| **PIT_FLOAT** | Float | `float` |

## 3. Control Patterns

Based on `ActionTable_2504.pdf`, three distinct patterns dictate HWP interaction:

1. **Direct Run**: No `ParameterSet`. Simple toggle commands. `hwp.Run("ActionID")`.
2. **Parameterized Action**: Requires a `ParameterSet`. Follows Lifecycle: `CreateAction` -> `CreateSet` -> `GetDefault` -> `SetItem` -> `Execute`.
3. **Dialog/Blocked Control**: Actions (marked `*`) that invoke UI. Require a `run_blocked = True` strategy.

## 4. Advanced Patterns

### 4.1 The "F5 Selection" Pattern
Used for table-wide styling:
1.  Emit `TableCellBlock` three times (select whole table).
2.  Emit target action (e.g., `SetCellBorder`).
3.  Emit `Cancel` (ESC).
