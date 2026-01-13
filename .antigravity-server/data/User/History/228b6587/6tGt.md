# Implementation: Transparent Layout Framework

To achieve "Exact Visual Fidelity" (눈에 보이는 그대로) when reconstructing complex documents like math workbooks, the system utilizes a **Transparent Layout Framework**. This approach bypasses the limitations of flow-based text insertion by using anchored objects and invisible structures.

## 1. Core Concept: The Invisible Grid
Math workbooks often feature multi-column layouts, side-by-side problems, and precise equation positioning that standard paragraph flows cannot reliably replicate. The framework uses HWP Tables as a layout engine:
- **Invisible Tables**: Tables are created using `CreateTable`, but all borders are set to "None" using `TableCellBorderNo`.
- **Parameter Set**: `CellBorderFill`
- **Action**: `TableCellBorderNo` (verified in `action_db.json`).

## 2. Layout Patterns for Math Workbooks

### 2.1 Multi-Column Problem Spread
- Instead of using native HWP Columns (which can be difficult to control for individual elements), the system creates a 1x2 or 1x3 table.
- Each cell acts as an independent container for a math problem.
- **Advantage**: Prevents content from "leaking" into the next column during automated insertion.

### 2.2 Precise Equation Anchoring
- Math equations are inserted via `InsertEquation`.
- **Videlity Control**: Equations can be anchored as "Character-like" (`TreatAsChar=True`) or with "Absolute Positioning" (`TreatAsChar=False` + X/Y coordinates).
- For math workbooks, `TreatAsChar=True` inside a table cell is generally more stable for reconstruction.

## 3. Automation Logic (SVDOM to HWPX)
The `Compiler` maps the **Semantic-Visual DOM (SVDOM)** coordinates to table dimensions:
1.  **Detection**: Vision API identifies a 2-column problem spread.
2.  **Creation**: Compiler generates `CreateTable(rows=1, cols=2)`.
3.  **Hiding**: Compiler executes `TableCellBorderNo` for the entire table.
4.  **Populating**: Content (Text + Math) is inserted into specific cells via `MoveToCell`.

## 4. Verified Control Actions
Actions used from the Knowledge Base:
- `CreateTable`: Initialize structure.
- `TableCellBorderNo`: Remove visual clutter (achieve transparency).
- `InsertEquation`: Render math content.
- `MoveToCell`: Precise navigation.

This framework ensures that the resulting HWPX file matches the "looked and feel" of the source PDF, ensuring 100% layout fidelity.
