# Parsing Execution Plan: PDF -> IR

## Goal
Implement a robust parsing pipeline for `hwpx/sample.pdf` that generates a structured Intermediate Representation (IR) ready for HWPX conversion.
**Scope Boundary**: Stop at IR generation (`lib.ir.Document`). Do not implement `Compiler` or HWPX Action generation.

## User Review Required
- **Validation Strategy**: Are `print` statements and JSON dumps sufficient for verification?
- **Vision Integration**: Confirm if `vision_derender` prompt should be reactivated or if we strictly use Docling. (Assumption: Use Docling + LayoutDetector).

## Proposed Changes

### [Phase 1] Layout analysis Integration
- [ ] **Verify `LayoutDetector`**: Ensure YOLO model loads and detects regions of `sample.pdf`.
- [ ] **Result**: JSON/Debug output of regions (Header, Footer, Table, Body).

### [Phase 2] Content Ingestion (Docling)
- [ ] **Enhance `DoclingIngestor`**:
    - [ ] Ensure `_apply_layout_enhancement` correctly merges YOLO regions with Docling text.
    - [ ] Debug "Atomic" parameter handling (as per user request "De-rendering Depth").
- [ ] **Output**: `DoclingDocument` object populated with correct reading order.

### [Phase 3] IR Mapping
- [ ] **Map to `lib.ir.Document`**:
    - [ ] `DocItem` -> `Paragraph` -> `TextRun`
    - [ ] `TableItem` -> `Table` (Verify matrix structure)
    - [ ] `PictureItem` -> `Image` (Stub or extract)
    - [ ] Handle `Equation` (LaTeX extraction)

## Verification Plan
### Automated Tests
1. **Unit Test**: `tests/test_ingestor.py` (Create new if missing).
2. **Integration Script**: `scripts/verify_parsing.py`
    - Run `ingestor.ingest("sample.pdf")`
    - Serialize `Document` to JSON.
    - Assert `len(sections) > 0`, `len(paragraphs) > 0`.

