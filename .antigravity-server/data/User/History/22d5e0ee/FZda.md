# Plan: Pilot Test - Math Workbook Reconstruction (Vision-Native)

> **Protocol:** 01_plan (3-Stage Planning Protocol)
> **Goal:** Reconstruct `sample.pdf` with **Exact Visual Fidelity**, treating layout as "Invisible Tables" to strictly control positioning.

---

## Stage A: Blueprint (Surface Scan)

### 1. Requirements
*   **Source**: `sample.pdf` (Math Workbook).
*   **Visual Structure**:
    *   **2 Columns**: Left (Q4-6), Right (Q7-9).
    *   **Content**: Text + Math Formulas (Equations).
    *   **Layout**: "Invisible" Grid (Transparent Table).
*   **Constraint**: "Architecture-First" - Use `ActionDatabase` for all controls.

### 2. Architecture Map
*   **Vision Layer**: (Simulated) Generates `DigitalTwin` JSON with `style: { "border": "none" }`.
*   **Ontology Layer**:
    *   `InsertEquation`: New Action needed.
    *   `CellBorderFill`: Existing Action, needs "Transparent" parameter mapping.
*   **Logic Layer (`Compiler`)**:
    *   DETECT `block.style.border == 'none'`.
    *   EXECUTE `CreateTable` -> `SelectAll` -> `CellBorderFill(Type=0)`.

---

## Stage B: Integration Trace

### Phase 1: Ontology Expansion (`lib/models.py`)
*   **Goal**: Enable properties/methods needed for this task.
*   **Additions**:
    *   `InsertEquation(script: str)`
    *   `SetCellBorder(type: str)` (Abstraction for `CellBorderFill`)

### Phase 2: Vision Simulation (`temp_vision/sample_twin.json`)
*   **Goal**: Create a JSON file that mimics the output of the "Vision-Native V3" prompt.
*   **Structure**:
    ```json
    {
      "pages": [
        {
          "blocks": [
            {
              "type": "Table",
              "style": { "border": "none", "cols": 2 },
              "cells": [
                { "row": 0, "col": 0, "content": [ { "type": "Text", "text": "4. x^2 + ..." } ] },
                { "row": 0, "col": 1, "content": [ { "type": "Text", "text": "7. P(x) = ..." } ] }
              ]
            }
          ]
        }
      ]
    }
    ```

### Phase 3: Compiler Logic (`lib/compiler.py`)
*   **Goal**: Translate "Invisible Table" JSON to HWP Actions.
*   **Logic**:
    1.  `compiler.create_table(rows, cols)`
    2.  `compiler.run_action("TableCellBlock")` (Select All)
    3.  `compiler.execute_parameter_action("CellBorderFill", {"Type": "None"})` (Using DB)
    4.  `compiler.run_action("Cancel")` (Deselect)

---

## Stage C: Quality Gate (Verification)

### 1. Risk Assessment
*   **Risk**: `CellBorderFill` parameter structure is complex (`BorderFill` set has ~50 items).
*   **Mitigation**: Use `ActionDatabase` to find the *minimal* required keys. (Likely just `Type` or `Val` is enough for "None").
*   **Fallback**: If DB structure is too complex for manual dict creation, use `Run("TableBorderFill")` if available, or just standard border types first.

### 2. Success Metric
*   `sample_reconstructed.hwp` opens in HWP 2024.
*   Visual inspection shows 2 columns with **NO VISIBLE BORDERS**.

---

## Execution Command
```bash
# 1. Update Models
# 2. Create Twin JSON
# 3. Update Compiler
# 4. Run Compiler
python3 scripts/pilot_math_workbook.py
```
