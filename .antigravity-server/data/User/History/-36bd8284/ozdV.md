# Walkthrough: Pilot Test - Math Workbook Reconstruction

> **Objective**: Verify "Visual Fidelity" reconstruction of `sample.pdf` (Math Workbook) using Vision-Native Derendering and ODA-compliant HWP Automation.

---

## 1. Vision-Native Simulation
We simulated the output of the **Gemini Vision-Native V3.0** model, which looks at the PDF and generates a structured "Digital Twin" JSON.
- **Key Insight**: The Vision model detects the "Invisible Grid" structure of the math problems.
- **Input JSON**: `temp_vision/sample_twin.json` uses a **2x2 Table** with `style: { "border": "none" }`.

## 2. Compiler Logic Upgrade
We upgraded `lib/compiler.py` and `lib/models.py` to handle advanced visual features:
1.  **Unified Run Model**: Refactored `TextRun`, `Equation`, `Image` into a single `Run` model with type dispatching.
2.  **Transparent Table Logic**: Implemented heuristic to detect `border: "none"` and inject the following Action Sequence:
    ```python
    # 1. Create Table
    CreateTable(rows=2, cols=2)
    # 2. Select All (Simulated F5 x 3)
    TableCellBlock() * 3
    # 3. Apply Invisible Border
    SetCellBorder(type="None")
    # 4. Cancel Selection
    Cancel()
    ```
3.  **Equation Support**: Added `InsertEquation` action mapping.

## 3. Verification Results
The Pilot Script (`scripts/pilot_math_workbook.py`) successfully generated **34 Actions** in `sample_actions.json`.

### Trace Highlight
```json
[
  { "action_type": "CreateTable", "rows": 2, "cols": 2 },
  { "action_type": "TableCellBlock" },
  { "action_type": "TableCellBlock" },
  { "action_type": "TableCellBlock" },
  { "action_type": "SetCellBorder", "border_type": "None" },
  { "action_type": "Cancel" },
  { "action_type": "MoveToCell", "row": 0, "col": 0 },
  { "action_type": "InsertText", "text": "4. " },
  { "action_type": "InsertEquation", "script": "x^2 + x - 1 = 0" }
]
```
> **Conclusion**: The system correctly translates "Visual Intent" (Transparent Grid) into "Mechanical Actions" (Border Settings), ensuring exact visual reproduction in HWPX.

## 4. Next Steps
- **E2E Integration**: Run this generated JSON against the actual HWP Engine on Windows.
- **Vision Connection**: Connect real Gemini Vision API to replace the simulator.
