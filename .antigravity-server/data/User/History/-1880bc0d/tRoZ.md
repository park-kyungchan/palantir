# Strategy: Parsing Quality Verification

Ensuring perfect word-level and structural fidelity during PDF-to-HWPX conversion requires a rigorous verification pipeline.

## 1. Objectives

- **Word-Level Accuracy**: Verify that every word in the source PDF is correctly extracted, including technical terms and multi-language content (Korean/English).
- **Structural Integrity**: Ensure table dimensions (rows/cols), cell merges (rowspan/colspan), and headers are preserved.
- **Image Content Extraction**: Extract embedded images and their content (via OCR or metadata) for placement in the target HWPX.

## 2. Three-Stage Verification Plan

The verification is executed sequentially to manage resource constraints (e.g., 16GB RAM limits):

### Stage A: Benchmark & Gap Analysis
- Process a sample page from a target PDF (e.g., `ActionTable_2504.pdf`).
- Compare the output IR against the existing `.txt` artifacts to identify systemic discrepancies in text extraction or table layout.

### Stage B: High-Fidelity Execution
- Run the full `DoclingIngestor` pipeline on the target PDFs (`ActionTable_2504.pdf`, `HwpAutomation_2504.pdf`, `ParameterSetTable_2504.pdf`).
- Enable OCR (`enable_ocr=True`) and table structure detection (`enable_table_structure=True`).
- Use sequential processing (one file at a time) to avoid memory overflows.

### Stage C: Validation Report
- Generate a `Parsing_Quality_Report.md`.
- Compare the new parsing results against original source PDFs and legacy text files.
- Highlight any missing text or failed image extractions.

## 3. Resource Management

Given the intensive nature of OCR and Docling processing:
- **Serial Execution**: Tasks are never run in parallel.
- **Environment Isolation**: Prefer running within a virtual environment to manage heavy dependencies like `torch` and `docling`.
