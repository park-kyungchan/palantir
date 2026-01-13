# Plan: High-Fidelity PDF Parsing & Verification

## Goal
Ensure `ParameterSetTable.txt`, `HwpAutomation.txt`, and `ActionTable.txt` are **perfectly parsed** from their source PDFs (`*_2504.pdf`), capturing:
1.  **Word-level accuracy** (vocabulary check)
2.  **Table structures** (rows/cols preservation)
3.  **Image contents** (OCR/Text-in-image extraction)

## User Review Required
> [!IMPORTANT]
> This process is computationally intensive (OCR). I will process files sequentially to respect the specific local hardware detailed by the user.

## Stage A: Blueprint (Current State Analysis)
- **Objective**: Assess current `.txt` quality vs. Docling capabilities.
- **Analysis Steps**:
    1.  Inspect existing `.txt` structure (Are they just raw text dumps? Do they contain table markdown? Image descriptions?).
    2.  Verify `docling` configuration in `lib/ingestors/docling_ingestor.py` to ensure `ocr=True` and `table_structure=True` are enabled.

## Stage B: Integration Trace (Verification & Execution Strategy)
- **Phase 1: Benchmark & Gap Analysis**
    - Run `docling` on a **sample page** (e.g., Page 3-5) of `ActionTable_2504.pdf`.
    - Compare output with the corresponding section in `ActionTable.txt`.
    - **Metric**: Presence of complex table borders, Korean text accuracy, image alt-text.
- **Phase 2: High-Fidelity Reparsing (The "Perfect" Parse)**
    - If Gap Identified (likely): Execute full parsing pipeline using `DoclingIngestor` with **enhanced settings** (OCR enabled, High-Res).
    - Output format: structured Markdown (cleaner than `.txt`).
- **Phase 3: Validation**
    - Semantic check: Random sampling of technical terms (e.g., "HwpAction").

## Stage C: Quality Gate
- [ ] Dependencies: `docling`, `easyocr` (or `surya-ocr`) confirmed ready.
- [ ] Resource Check: Process 1 file at a time (Sequential).

## Proposed Changes
### [hwpx/scripts]
#### [NEW] `verify_parsing_quality.py`
- Script to run side-by-side comparison on samples.
#### [MODIFY] `lib/ingestors/docling_ingestor.py`
- Ensure strict OCR constraints are applicable.

## Verification Plan
### Automated Tests
- `python scripts/verify_parsing_quality.py --target ActionTable`

### Manual Verification
- Output a "Diff Report" showing what was missing in the original `.txt` (e.g., "Found 15 missing table cells and 3 image captions").
