# Pilot Test: Math Workbook Reconstruction (sample.pdf)

This pilot test validates the "Vision-Native to HWPX" pipeline using a complex math workbook sample.

## 1. Objectives
- **Exact Visual Fidelity**: Replicate the 2-column layout of `sample.pdf`.
- **Transparent Table Implementation**: Use invisible HWP tables to manage complex element positioning.
- **Formula Accuracy**: De-render visual formulas into HWP math scripts.

## 2. Test Input: Simulated Vision Output
Since the Vision API (v3.0) is in the prompt engineering phase, the test uses a manually constructed `sample_twin.json` that simulates the high-fidelity output of the **Vision-Native Derender Engine (v3.0)**.

### 2.1 Simulated SVDOM Structure
- **Container**: 3x2 Grid Table (Invisible).
- **Column 1**: Problems 4, 5, 6.
- **Column 2**: Problems 7, 8, 9.
- **Elements**: 
    - Text: "4. ", " 일 때, 다음 식의 값을 구하시오."
    - Equation: `x^2 + x - 1 = 0`, `(x+2)(x-1)(x+4)(x-3) + 5`
    - Answers: Represented as blue text runs (Answers for specific problems).

## 3. Implementation Workflow
1.  **Ontology Binding**: Map the internal `DigitalTwin` blocks to the `HwpAction` models (`InsertEquation`, `SetCellBorder`).
2.  **Compiler Logic**:
    - **Step 1**: Initialize Table (`CreateTable`).
    - **Step 2**: Apply Transparency (`SetCellBorder` with `border_type=None`).
    - **Step 3**: Iterate through Cells. For each cell, insert `Text` and `Equation` blocks in sequence.
3.  **Validation**: Verify that the generated HWPX opens without errors and preserves the 2-column visual arrangement without showing table borders.

## 4. Key Findings
- **Layout Stability**: Using a 2-column invisible table is significantly more stable for automated reconstruction than standard flow-based columns.
- **Equation Handling**: HWP math scripts derived from visual de-rendering require specific escaping/mapping (e.g., characters like `^`, `_`, `{`, `}`).
- **Transparency Logic**: The `CellBorderFill` action (SetCellBorder) is the preferred ODA-compliant method for hardening the "Transparent Layout Framework".

## 5. Execution Results & Debugging Trace (Pilot Attempt 1-3)

The pilot was executed using `scripts/pilot_math_workbook.py` against the simulated `sample_twin.json`.

### 5.1 Debugging: Schema & Model Integrity
- **Attempt 1: NameError (Schema)**: Discovered that `Page` and `Block` models were accidentally removed during schema expansion. Fixed by restoring legacy model support within the unified `Section` architecture.
- **Attempt 2: ImportError (Models)**: Identifying cyclic dependency issues in `lib/models.py`. Restored the `MoveToCell` class which was accidentally overwritten during the addition of `SetCellBorder`.

### 5.2 Finding: The "Zero Action" Logic Gap
- **Finding**: While the simulated twin successfully loads a `Table` block, the initial compiler run yielded **0 actions**. 
- **Cause Analysis**: Investigations revealed that the `_compile_table` logic expects a specific nested hierarchy (`Table -> TableRow -> Cell -> Paragraph -> Run`). The flat `block` list in the simulated JSON requires a robust pre-compiler transformation layer to bridge the "Simulated Vision" format to the "Rich HWP Action" format.
- **Resolution**: Implementation of a `load_simulated_twin` converter in the pilot script to explicitly map visual blocks into the rich hierarchical ontology.

### 5.3 Attempt 4: Unified Schema Alignment
- **Finding**: Even after fixing imports, a `NameError` for `TextRun` persisted in the `Compiler`.
- **Cause Analysis**: The `Compiler` was still attempting to use legacy class names from `lib.ir.py` (e.g., `TextRun`, `Equation`) which were renamed in the new `lib.digital_twin.schema.py` (e.g., `Run`, `Section.elements`).
- **Resolution**: A deep refactoring of `lib/compiler.py` was performed to migrate its dependency from `lib.ir` to `lib.digital_twin.schema`. This unifies the "Engine Brain" and ensures that the Vision API output directly maps to the Compiler's expected internal state.
- **Key Insight**: The naming shift from `TextRun` (legacy) to `Run(type="Text")` (schema) represents a move towards a more atomic and polymorphic data model.
