# Parsing Execution Plan: PDF -> IR (Pre-HWPX)

## Goal
Implement a robust parsing pipeline for `hwpx/sample.pdf` that generates a structured Intermediate Representation (IR) ready for HWPX conversion.
**Constraint**: Context stops at `lib.ir.Document` generation. No HWPX compilation.

## User Review Required
- **Integration Strategy**: Current `DoclingIngestor` does **NOT** use `LayoutDetector`.
    - **Proposal**: Implement a "Hybrid Ingestion" where `LayoutDetector` (YOLO) defines regions (Header/Footer/Table/Body) and `Docling` extracts content within those regions.
- **Risk Acceptance**: Korean Math (LaTeX) quality depends on Docling v2 capabilities.

## Proposed Changes

### [Phase 1] Layout Analysis (Vision Layer)
- **Goal**: Reliable Region Detection.
- **Action**:
    - Update `lib/ingestors/docling_ingestor.py` to allow injecting external layout hints.
    - Verify `lib/layout/detector.py` execution on `sample.pdf`.
    - **Output**: `layout_map.json` (Bboxes for 2-column, Answer Boxes).
- **Test**: `scripts/verify_layout.py` (Visualizing bboxes on PDF image).

### Phase 2: Vision-Native Content Extraction
- **Goal**: Extract text and math from PDF using pure vision-based approach (bypassing Docling parser errors).
- **Strategy**:
    1. **Render PDF to Image**: Use `pdf2image` or `pymupdf` (fitz).
    2. **Layout-Driven Cropping**: Use `LayoutRegion` bboxes (from Phase 1) to crop images.
    3. **OCR Routing**:
        - **Text Regions**: Pass crop to `OCRManager` (EasyOCR/Surya/Paddle).
        - **Math Regions**: Pass crop to LaTeX OCR endpoint (or stub for now).
        - **Tables**: Send crop to Table Structure Recognition (Docling TableFormer or similar).
    4. **IR Assembly**: Construct `Section`/`Paragraph` objects from OCR results.
- **Files**:
    - [MODIFY] [docling_ingestor.py](file:///home/palantir/hwpx/lib/ingestors/docling_ingestor.py) (Extend fallback logic)
    - [NEW] [vision_ingestor.py](file:///home/palantir/hwpx/lib/ingestors/vision_ingestor.py) (Optional: Clean separation?)
    - [MODIFY] [ocr/manager.py](file:///home/palantir/hwpx/lib/ocr/manager.py) (Ensure robust Korean support)
- **Verification**: `scripts/verify_ocr.py` running on `sample.pdf` (utf-8 error check).
- **Test**: Check specific equations from `sample.pdf` (e.g., "701", "211" in answer boxes).

### [Phase 3] IR Unification & Semantic Tagging
- **Goal**: Unified `lib.ir.Document` with semantic tags (AnswerBox, ProblemBox).
- **Issue**: `DocLayout-YOLO` natively output labels 0-13 (Title, Text, Table, Figure, etc.) do not include "AnswerBox".
- **Strategy (Heuristic-Based Tagging)**:
    1.  **ProblemBox Detection**: Define `ProblemBox` as `SECTION_HEADER` or `TEXT` starting with specific patterns (e.g., "7.", "8." or number circles).
    2.  **AnswerBox Detection**: Define `AnswerBox` as empty space or specific markers ("풀이", "정답") within a region, OR inference from spatial gaps between Problems.
    3.  **Refinement**: Implement `SemanticTagger` class to post-process `LayoutRegion`s.
        - **Critical Update**: Tagging requires text content. `DoclingIngestor` refactored to specific 2-pass flow:
            1. Layout Detection + OCR (Text Extraction)
            2. Semantic Tagging (using Text)
            3. IR Construction.
- **Files**:
    - [NEW] [lib/layout/semantic_tagger.py](file:///home/palantir/hwpx/lib/layout/semantic_tagger.py) (Heuristic logic)
    - [MODIFY] [lib/ingestors/docling_ingestor.py](file:///home/palantir/hwpx/lib/ingestors/docling_ingestor.py) (Integrate Tagger)
- **Test**: `scripts/verify_ir.py` -> Check `AnswerBox` count > 0.

### [Phase 4] HWPX Compilation (Compiler Layer)
- **Goal**: Convert verified IR into valid `.hwpx` file.
- **Challenge**: `lib/compiler.py` lacks heuristic-to-HWP style mapping.
- **Strategy**:
    1.  **Extensions**: Add `SetParaShape` to `lib.models` (for indenting).
    2.  **Mapping Logic**:
        -   **ProblemBox**: Map `style="ProblemBox"` -> `SetParaShape(indent=hanging)`.
        -   **AnswerBox**: Map `style="AnswerBox"` -> Compile as 1x1 Table with Border. (Robust layout isolation).
    3.  **Compiler Update**: Modify `_compile_paragraph` to branch logic based on `para.style`.
- **Files**:
    - [MODIFY] [lib/models.py](file:///home/palantir/hwpx/lib/models.py) (Add `SetParaShape`)
    - [MODIFY] [lib/compiler.py](file:///home/palantir/hwpx/lib/compiler.py) (Implement Style Mapping)
- **Verification**:
    -   Generate `sample.hwpx`.
    -   Manual Inspection (since we don't have headless HWP renderer).

### [Phase 5] HWPX Builder (Serialization Layer)
- **Goal**: Transform `HwpAction` objects into an executable HWP Automation Script (`reconstruct.py`) for the Windows Agent.
- **Dependency**: Requires `win32com` on the target Windows machine.
- **Strategy**:
    1.  **Builder Class**: Create `lib/builder.py`.
    2.  **Template Generation**: define standard boilerplate (Import, Open HWP, Security Module).
    3.  **Action Dispatch**: Map each `HwpAction` model to its `win32com` equivalent code block.
    4.  **Output**: `scripts/run_pipeline.py` -> `output_actions.py`.
- **Status**: Verified (Phase 5 Complete).

### [Phase 6] Native HWPX Generation (Linux)
- **Goal**: Generate valid `.hwpx` zip archives directly on Linux (Zero-Dependency).
- **Prototype**: `tests/manual/generate_linux_hwpx.py` acts as the proof-of-concept.
- **Strategy**:
    1.  **Migrate Prototype**: Move `generate_linux_hwpx.py` logic to `lib/owpml/`.
    2.  **Model Mapping**: Map `HwpAction` -> OWPML XML Tags (`<hp:run>`, `<hp:p>`, etc.).
    3.  **Zipper**: Implement `HWPXZipper` to package `Contents.xml`, `ContentHeader.xml`, `Version.xml`.
- **Files**:
    - [NEW] `lib/owpml/generator.py`
    - [NEW] `lib/owpml/models.py`
    - [MODIFY] `lib/pipeline.py` (Add ".hwpx" export option)
- **Verification**:
    -   Generate `.hwpx` on Linux.
    -   User validates by opening in Hancom Office (Mac/Web/Windows).
- **Result**: User reported "File Damaged" and poor quality. **DEPRECATED**.

### [Phase 7] Mathpix Migration (Ingestion Pivot)
- **Goal**: Replace `DoclingIngestor` with Mathpix API for high-fidelity OCR/Layout.
- **Requirement**: "Mathpix API" usage ($0.005/page).
- **Architecture**:
    1.  **Ingestion**: `MathpixIngestor` sends PDF to API, retrieves Markdown (`.mmd`).
    2.  **Parsing**: `MarkdownParser` converts MMD syntax -> `lib.ir.Document`.
        -   Maps `##` -> `Section`.
        -   Maps `**bold**` -> `IRTextRun(bold=True)`.
        -   Maps `$eqn$` -> `IREquation`.
        -   Maps `![img]` -> `IRImage`.
    3.  **Compilation**: Reuse existing `Compiler` to convert `lib.ir` -> `HwpActions`.
    4.  **Builder**: Reuse `Builder` to generate `reconstruct.py` (Windows Automation).
        -   *Note*: User rejected Native HWPX (Phase 6), so we rely on Windows Automation (Phase 5) for final file creation.
- **Files**:
    - [NEW] `lib/ingestors/mathpix_ingestor.py`
    - [NEW] `lib/parsers/markdown_parser.py`
- **Verification**:
    -   `scripts/verify_mathpix.py`: Check Markdown quality.
    -   `scripts/run_pipeline.py`: End-to-End run.

### [Phase 8: PDF Reconstruction (Pipeless)]
- **Goal**: Generate high-fidelity PDF directly from Mathpix Markdown, bypassing HWPX entirely.
- **Why**: User requested "reimplement as PDF" to skip the complexity of HWPX generation while maintaining visual quality.
- **Strategy**: 
    - Reuse `MathpixIngestor` for MMD extraction.
    - Implement `PDFGenerator` to send MMD -> Mathpix Converter API (`/v3/converter`).
    - Download result as `reconstructed.pdf`.

#### [NEW] [generators/pdf_generator.py](file:///home/palantir/hwpx/lib/generators/pdf_generator.py)
- **Role**: Handles interaction with Mathpix Converter API.
- **Methods**: `generate_pdf(mmd_content: str, output_path: str)`

#### [MODIFY] [pipeline.py](file:///home/palantir/hwpx/lib/pipeline.py)
- **Change**: Add `generate_pdf_only` flag or method to bypass Compiler/Builder.
### Automated Tests
1. **Layout Test**: `python scripts/verify_layout.py` -> Checks for >4 answer boxes.
2. **IR Test**: `python scripts/verify_ir.py` -> Validates Pydantic schema of `lib.ir.Document`.
3. **Compilation Test**: `python scripts/verify_compilation.py` -> Generates HWPX and checks Action sequence log.
4. **Builder Test**: `python scripts/verify_builder.py` -> Checks generated code structure.

### Manual Verification
1.  **Execution (Windows)**: Run `reconstruct.py` on Windows machine with Headerless HWP.
2.  **Visual Check**: Open `output.hwpx`.

### Risk Assessment
| Risk Type | Probability | Impact | Mitigation |
|-----------|-------------|--------|------------|
| Coordinates | High | High | Implement `CoordinateScaler` (PDF pt <-> Img px) |
| Math OCR | Medium | High | Use Docling's `math` model explicitly |


