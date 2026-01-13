# Implementation: HWP Action Ontology

The HWP Action Ontology defines the programmatic representation of Hancom Office API commands. These models serve as the "Instruction Set" for the `Executor` to rebuild documents on Windows.

## 1. Core Principles
- **Strict Typing**: Every HwpAction is a Pydantic model with validated parameters.
- **API Mapping**: Action names (e.g., `CreateTable`, `SetAlign`) map directly to HWP automation objects or sequences of OLE actions.
- **Resolution**: Geometry and style values are normalized (e.g., mm for margins, points for fonts).

## 2. Key Action Models

### 2.1 Text & Formatting
- `InsertText`: Inserts raw text content at the current caret position.
- `SetFontSize`: Changes the active font size (in points).
- `SetFontBold`: Boolean toggle for bold styling.
- `SetAlign`: Sets paragraph alignment (`Left`, `Center`, `Right`, `Justify`).
- `SetLetterSpacing`: Adjusts character spacing (Ja-gan).
- `SetLineSpacing`: Adjusts vertical paragraph spacing (Jul-gan-gyeok).

### 2.2 Tables
- `CreateTable`: Initializes a table with specified `rows` and `cols`.
- `MoveToCell`: Positions the caret inside a specific `row` and `col` for content insertion.

### 2.3 Layout & Structure
- `SetPageSetup`: Configures margins (Top, Bottom, Left, Right) and headers.
- `MultiColumn`: Defines the column layout (e.g., 2-column spread).
- `BreakSection`: Forces a section break, allowing for changing column layouts on a single page (`continuous=True`).
- `BreakColumn`: Forces a break to the next column.

### 2.4 Rich Content
- `InsertEquation`: Inserts a math formula using HWP script format.
- `InsertImage`: Embeds an image file from a local path.
- `InsertTextBox`: Creates a floating text box with absolute positioning.

## 3. Implementation Details
The ontology is implemented in `lib/models.py` using `pydantic.BaseModel`.

```python
class HwpAction(BaseModel):
    action_type: str = Field(..., description="Internal API name")

class InsertText(HwpAction):
    action_type: Literal["InsertText"] = "InsertText"
    text: str

class CreateTable(HwpAction):
    action_type: Literal["CreateTable"] = "CreateTable"
    rows: int
    cols: int
```

## 4. Knowledge Base Schema
The ontology is complemented by a Knowledge Base schema (`lib/knowledge/schema.py`) that stores the official API reference data.

- **ActionDefinition**: Links an Action ID (mnemonic) to its ParameterSet.
- **ParameterSetDefinition**: Describes a collection of parameters required by an action.
- **ParameterItem**: Defines an individual parameter's ID, type (e.g., `PIT_BSTR`, `PIT_UI`), and description.
- **EventDefinition**: Describes HWP Automation Events (e.g., `DocumentBeforeSave`) and their arguments.
- **APIMethodDefinition**: Registry of official HWP automation methods (e.g., `Open`, `SaveAs`).
- **APIPropertyDefinition**: Registry of automation properties (e.g., `PageCount`, `IsModified`).

This dual-layer ontology (Runtime Actions + Reference Knowledge) allows the compiler to validate generation logic against the official manual.
