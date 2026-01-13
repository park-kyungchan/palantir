# HWPX Automation: Workflow & Templates

This document covers high-level concepts for automating document creation and editing.

## 1. Reusable Action Templates
The `MathWorkbookTemplates` library (alias `T`) uses functional composition to simplify document assembly.

- **`problem_header(num)`**: Emits `SetParaShape` (hanging indent) + `InsertText`.
- **`answer_box(text)`**: Emits Bold/Enlarged formatting around a specific value.
- **`two_column_layout()`**: Emits `MultiColumn(count=2)`.

## 2. Reconstruction Patterns
To achieve 100% fidelity for workbooks like `sample.pdf`, use the following sequence:

1. **Outer Boundary**: `CreateBorderBox`.
2. **Layout Partition**: `MultiColumn(count=2)`.
3. **Left Flow**: Problems 4, 5, 6.
4. **Partition Transition**: `BreakColumn`.
5. **Right Flow**: Problems 7, 8, 9.

## 3. Interactive Editing Protocol
Enables natural language modification of the Digital Twin (SVDOM) without full re-compilation.
- **Protocol**: `EditAction` -> `SVDOM Update` -> `Partial Compilation` -> `Windows Automation`.

## 4. Pilot Test Verification
The "Math Workbook Pilot" successfully verified:
- **Accuracy**: 54 Actions generated for 9 Problems.
- **Fidelity**: Correct indentations and equation rendering.
- **Scaling**: Verified batch processing for multi-page documents.

## 5. Programmatic Codebase Maintenance
When codebase modifications involve multi-line structural changes (e.g., removing duplicate method stubs), manual replacement via LLM tools may fail.

- **Strategy**: Standalone Python scripts (e.g., `scripts/fix_builder.py`) for "Digital Twin" maintenance.
- **Protocol**:
    1. Identify structural issues (e.g., duplicate method `_insert_equation`).
    2. Load file in a maintenance script.
    3. Filter out unwanted indices (e.g., last instance of a method).
    4. Rewrite target logic (e.g., replacing `_insert_text` with style-aware version).
    5. Self-verify via regression tests.
