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

### Stage B: Vision-Native Execution (Pivot)
- Following legacy model failures (Docling/Doclayout-YOLO), the pipeline pivoted to a Vision-Native approach using Gemini 3.0 Pro.
- Convert PDF pages to images.
- Use the validated System Prompt for structural de-rendering.

### Stage C: Validation Report
- Generate a `Parsing_Quality_Report.md`.
- Compare the new parsing results against original source PDFs and legacy text files.
- Highlight any missing text or failed image extractions.

### Stage D: Digital Twin Structural Validation
- JSON outputs are validated using `lib/digital_twin/schema.py` (Pydantic).
- Verification of table row/column counts and LaTeX formula integrity.
- Successful pilot confirmed with `ActionTable_2504.pdf` (Page 1).

## 3. Resource Management

Given the intensive nature of OCR and Docling processing:
- **Serial Execution**: Tasks are never run in parallel.
- **Environment Isolation**: Prefer running within a virtual environment to manage heavy dependencies like `torch` and `docling`.
