# Pilot Trace: PDF Ingestion & HWPX Reconstruction

This artifact tracks the execution strategy and debugging history for reconstructing complex PDFs (e.g., `sample.pdf`) into the HWPX format.

## 0. Overall Strategy
The pipeline follows a 3-phase execution model:
1. **P1: Layout Analysis**: Detect structural regions using DocLayout-YOLO.
2. **P2: Content Ingestion**: Vision-Native OCR (EasyOCR) extraction for identified regions.
3. **P3: IR Unification**: Mapping extracted items to the unified SVDOM (Intermediate Representation).
4. **P4: HWPX Compilation**: Translating IR styles to native HWP Action sequences.
5. **P5: HWPX Builder (Automation)**: Transpiling actions into an executable Windows-native script (`reconstruct.py`).
6. **P6: Native Generation (Linux)**: Direct OWPML/XML construction for zero-dependency HWPX creation.

---

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

### 5.4 Attempts 5-8: Fine-Grained Logic Refinement
- **Attempt 5: IndentationError**: A deep refactor introduced a nesting error in the `_compile_paragraph` loop. This confirmed the need for strict loop separation between high-level elements (Tables) and low-level typography (Runs).
- **Attempt 6: Garbage Logic in Table Handlers**: Discovered leftover code snippets (`fig.path`) in the `_compile_table` logic during a copy-paste refactor. Fixed by explicitly rewriting the HWP table navigation logic.
- **Attempt 7: Missing Dispatch Methods**: Encountered `AttributeError` for `_compile_equation`. Realized that modularizing the compiler required restoring specific handlers that were accidentally pruned during the "Atomic Refactor".
- **Attempt 8: SyntaxError in Image Parameters**: A duplicate `height` parameter in the `InsertImage` call blocked execution. This highlighted the sensitivity of the `HwpAction` Pydantic models to exact keyword repetition.

- **Resolution**: Adjusting the `Compiler` to return a list of `HwpAction` objects (or adjusting the script to handle dict-based dumping). This finalized the stability of the "Action Generation" phase.

### 5.6 Attempt 10: Final Success & Verification
- **Execution**: The 10th run of `scripts/pilot_math_workbook.py` completed successfully.
- **Outcome**: Generated **34 Actions** in `sample_actions.json`.
- **Validation**: 
    - The `CreateTable` (2x2) was correctly followed by the **Selection Pattern** (`TableCellBlock` x3).
    - `SetCellBorder(border_type="None")` was applied to the entire selection.
    - `MoveToCell` correctly navigated the grid.
    - `InsertEquation` scripts matched the simulated LaTeX input exactly.
- **Trace Snippet**:
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
## 4. PDF Parsing Pilot Test (Jan 2026)

This pilot focuses on high-fidelity parsing of `sample.pdf` into a structured Intermediate Representation (IR) using the **Docling + LayoutDetector** pipeline.

### 4.1 Execution Plan
The plan is divided into three distinct phases to ensure layout and content fidelity:

| Phase | Objective | Deliverables |
| :--- | :--- | :--- |
| **P1: Layout Analysis** | Verify region detection | YOLO-detected bounding boxes (Title, Table, Body) |
| **P2: Content Ingestion** | Extract text and math | `DoclingDocument` with reading order optimization |
| **P3: IR Mapping** | Convert to Internal IR | `lib.ir.Document` with Paragraphs, Tables, and Equations |

### 4.2 Verification Strategy
- **Manual Visual Audit**: Compare the rendered PDF against the serialized IR JSON structure.
- **Math Precision Check**: Verify that formulas in `sample.pdf` are accurately captured as LaTeX/Equation objects.
- **Structural Integrity**: Ensure multi-column layouts (if any) are correctly sequenced based on the `ReadingOrderSorter`.

### 4.3 Phase 3 Verification Results (IR Unification)
The final stage of the parsing pilot focused on unifying the Vision-Native extraction and the Docling-based structural enhancement.

- **Outcome**: The `scripts/verify_ir.py` tool successfully generated a unified `ir_output.json`.
- **Key Resolution (Temporal Coupling Bug)**: Initial runs reported 0 `AnswerBox`/`ProblemBox` tags because the `SemanticTagger` was executing on empty regions. Refactoring to a **2-pass loop** (Pass 1: OCR Extraction -> Pass 2: Heuristic Tagging) solved this.
- **Finding (OCR Math Noise)**: High-resolution math formulas sometimes introduce "noise" characters in the OCR result (e.g., `(2? + 1)` instead of `(x+1)`), requiring robust/fuzzy regex patterns in the `SemanticTagger` to maintain high recall for `ProblemBox` detection.
- **Coordinate Integrity**: Verified that flipping the Y-axis and scaling coordinates correctly aligned pixel-based YOLO regions with PDF-point-based Docling items, enabling accurate **IoU-based tag propagation**.
- **Final Validation (Step ID 1058)**:
    - **Outcome**: `✅ SUCCESS: Detected semantic regions.`
    - **Metrics**: **9 ProblemBox** paragraphs found in `sample.pdf`.
    - **Stability**: The 3-stage flow (Detection -> OCR -> Tagging) confirmed as the stable standard for math workbook ingestion.

- **Phase 4 Planning (Step ID 1083)**:
    - **Blueprint**: Strategy defined for IR-to-HWP mapping.
    - **Styles**: `ProblemBox` -> `SetParaShape(hanging)` | `AnswerBox` -> 1x1 Table.
    - **Gap Identification**: Identified the need to implement the `SetParaShape` action in the HWPX ontology.

### 4.4 Phase 4 Execution Trace (January 2026)
Following the Phase 3 success, the compilation layer was implemented and tested using `scripts/verify_compilation.py`.

- **Attempt 1: ImportError (Step ID 1103)**: Encountered `cannot import name 'Document' from 'lib.digital_twin.schema'`.
    - **Resolution**: Updated `verify_compilation.py` to use the standardized `DigitalTwin` root object.
- **Attempt 2: Pydantic ValidationError (Step ID 1114)**: Verification failed because the `Paragraph.style` field in the SVDOM schema expects a `Style` object, while the test script passed a string (e.g., `"Header"`).
    - **Resolution**: Refined the `Paragraph` instantiation in the test script to use the proper `Style` model. This highlighted the difference between high-level tags used during ingestion and the structured properties required in the Digital Twin IR.
- **Attempt 3: Zero Action Result / Type Mismatch (Step ID 1151)**: Even with specific tests passing, the full pipeline (`scripts/run_pipeline.py`) returned 0 actions.
    - **Cause**: `DoclingIngestor` outputs `lib.ir.Paragraph` dataclasses, but the `Compiler` was using `isinstance(x, Paragraph)` where `Paragraph` referred to the Pydantic class in `lib.digital_twin.schema`.
    - **Resolution**: Refined `lib/compiler.py` with multi-schema awareness:
        - Implemented cross-import aliasing for `IRParagraph` and `Paragraph` (SVDOM).
        - Added multi-type checks: `isinstance(elem, (Paragraph, IRParagraph))`.
        - Normalized attribute access using `getattr(para, 'runs', None) or getattr(para, 'elements', [])`.
- **Attempt 4: AttributeError on Run Attributes (Step ID 1167, 1178)**: Encountered `AttributeError: 'TextRun' object has no attribute 'type'` and `'TextRun' object has no attribute 'style'`.
    - **Cause**: Schema drift between legacy `TextRun` (flat) and new `Run` (nested style).
    - **Resolution**: Implemented recursive attribute checking and class-based type detection in `_compile_run`. 
- **Final Outcome (Step ID 1189)**: Full pipeline orchestration verified. `sample.pdf` compiles into **54 HWP Actions** (including 9 ProblemBoxes with hanging indents).

### 4.5 Phase 5 Execution Trace: HWPX Builder (Serialization)

The final stage of the pipeline translates `HwpAction` objects into an executable Python script for Windows via `win32com`.

- **Outcome**: The `scripts/verify_builder.py` tool successfully generated `test_reconstruct.py`.
- **Transpilation Success**: Verified the conversion of `SetParaShape`, `CreateTable`, and `InsertText`.
- **Key Strategy (HWP Security)**: Implemented `hwp.RegisterModule('FilePathCheckDLL', 'SecurityModule')` in the builder's header to ensure seamless execution on target Windows machines without manual file access prompts.
- **Verification Result (Step ID 1240)**: 
    - `✅ SUCCESS: test_reconstruct.py created.`
    - `✅ CHECK: SetParaShape logic found.`
    - `✅ CHECK: CreateTable logic found.`
- **End-to-End Status**: The pipeline is now functionally complete from PDF input to the final Windows-Ready Automation Script.

### 4.6 Phase 6 Execution Trace: Native HWPX Generation (Linux)

Direct OWPML generation on Linux was implemented to allow immediate viewing of results without a Windows host.

- **Status (Step ID 1315)**: **DEPRECATED**. User reported "File Damaged" errors and poor layout accuracy. The pipeline shifted focus back to high-fidelity Windows Builder reconstruction.

### 4.7 Phase 7 Execution Trace: Mathpix Cloud Migration (January 2026)

To resolve the quality issues with Native Generation (Phase 6) and local OCR (Docling), the pipeline pivoted to the **Mathpix API**.

- **Outcome (Step ID 1335)**: The pipeline was rewired to use `MathpixIngestor` and `MarkdownParser`.
- **Implementation (Step ID 1318 - 1493)**:
    - **Cloud OCR**: PDF pages are processed by Mathpix into `.mmd` (Markdown).
    - **IR Mapping**: The `MarkdownParser` translates MMD logic (headings, math, bold) into the internal SVDOM.
    - **Robust Ingestion**: Introduced **Lazy Loading** for heavyweight local ML libraries to ensure the Cloud Ingestor remains responsive and avoids timeout-based `KeyboardInterrupt` crashes.
    - **Schema Sync**: Resolved `ImportError` by aliasing `TextRun` to `IRTextRun`.
    - **Debugging (API Payload)**: Diagnosed an `Internal error` (`KeyError: 'pdf_id'`) caused by invalid multipart structure for nested options. Solved by migrating to the `options_json` payload field.
    - **Debugging (Process SigKill)**: Resolved recurring `KeyboardInterrupt` and `ModuleNotFoundError` during background execution by standardizing on `nohup env PYTHONPATH=.` for the production run.
    - **Implementation (Schema Logic)**: Fixed a `TypeError` in `MarkdownParser` by switching from `Section(paragraphs=...)` to `Section().elements.append()`, reflecting the actual IR schema.
    - **Compiler Patch**: Fixed an `AttributeError` in `lib/compiler.py` where the engine accessed `run.type` directly; replaced with a polymorphic `rtype` variable check.
    - **Image Integration**: Updated `MarkdownParser` to detect `![alt](url)` patterns. Integrated `requests`-based image downloading in the `Compiler` to convert cloud-hosted thumbnails into local HWPX assets.
- **Results**: High-fidelity math extraction (equations) and robust image retention. Successfully generated **123 HWP Actions** from `sample.pdf` (including **21 Equations** and **1 Image** download).
- **Verification**: User-provided API Key was verified via `curl` and subsequently used to successfully re-generate `output_actions.json` for `sample.pdf`.
- **Final End-to-End Status**: Successfully generated high-fidelity `output_actions.py` reconstruction script and `output_actions.hwpx` native file using Mathpix content. The pipeline is now fully operational in Mathpix Cloud mode.

 ### 4.8 Phase 8: PDF-to-PDF Reconstruction (Success)
 
- **Goal**: Re-implement the pipeline to output high-fidelity PDF by bypassing the HWPX reconstruction layer.
- **Implementation (Step ID 1559 - 1698)**:
    - **Environment**: identified missing local PDF libraries (Pandoc, WeasyPrint, etc.).
    - **Capability**: Confirmed Mathpix API's `v3/converter` capability for high-fidelity asynchronous MMD-to-PDF rendering.
    - **Architecture**: Implemented `PDFGenerator` and added a `--pdf` flag to `scripts/run_pipeline.py`.
    - **Bypass Logic**: When `--pdf` is set, the pipeline skips the HWP Compiler/Builder and sends the `raw_output` (MMD) directly to the Mathpix Cloud Converter.
    - **Debugging (Async Polling)**: Encountered a race condition where the main conversion status was `completed` but the internal PDF task was still `processing`. Implemented granular sub-status polling in `lib/generators/pdf_generator.py`.
    - **Debugging (Missing Resource URL)**: Discovered that even after `pdf.status == "completed"`, the JSON response might not contain a signed URL. Implemented a fallback to construct the resource URL explicitly as `/{id}.pdf`, ensuring reliable asset retrieval.
    - **Debugging (401 Unauthorized)**: Observed that direct downloads of constructed URLs require `app_id` and `app_key` headers. Resolved by injecting authentication into the `requests.get` call within the download handler.
- **Outcome**: Successfully generated `reconstructed.pdf` with perfect mathematical rendering and image preservation.
