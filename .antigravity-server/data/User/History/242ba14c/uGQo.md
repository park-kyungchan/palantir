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

### [Phase 2] Content Ingestion (Semantics Layer)
- **Goal**: Text & Math Extraction.
- **Action**:
    - Configure `Docling` to respect "Reading Order" from Phase 1 (if possible) or post-process.
    - Extract LaTeX for equations (e.g., $x^2 + x - 1 = 0$).
    - **Output**: Raw Docling JSON with math.
- **Test**: Check specific equations from `sample.pdf` (e.g., "701", "211" in answer boxes).

### [Phase 3] IR Unification (Integration Layer)
- **Goal**: Unified `lib.ir.Document`.
- **Action**:
    - Map Docling logic to `lib.ir` classes (`Paragraph`, `Table`, `Image`).
    - **Critical**: Ensure `Box` items (Answer fields) are preserved as distinct IR elements (potentially new `IRField` or `IRBox` if needed, currently mapping to `Paragraph` with borders).
- **Test**: `scripts/verify_ir.py` -> dumps `ir_output.json`.

## Verification Plan
### Automated Tests
1. **Layout Test**: `python scripts/verify_layout.py` -> Checks for >4 answer boxes.
2. **IR Test**: `python scripts/verify_ir.py` -> Validates Pydantic schema of `lib.ir.Document`.
3. **Manual Check**: Review `ir_output.json` against `sample.pdf` visual structure.

### Risk Assessment
| Risk Type | Probability | Impact | Mitigation |
|-----------|-------------|--------|------------|
| Coordinates | High | High | Implement `CoordinateScaler` (PDF pt <-> Img px) |
| Math OCR | Medium | High | Use Docling's `math` model explicitly |


