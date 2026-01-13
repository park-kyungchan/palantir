# Research: PDF Reconstruction Track

## 1. Requirement
The user requested a pivot to **PDF output** (Phase 8), skipping the path to HWPX for specific use cases or rapid validation. This involves converting the Intermediate Representation (IR) or the Mathpix Markdown (MMD) directly to a PDF file.

## 2. Environment Constraints (WSL2)
A survey of common Python PDF libraries revealed significant environment gaps:
- **Pandoc**: Not found.
- **WeasyPrint**: Not found.
- **ReportLab**: Not found.
- **FPDF**: Not found.
- **Matplotlib**: **Available**. Can be used for LaTeX rendering if necessary.

## 3. Mathpix Cloud Rendering
The Mathpix API supports a conversion track for MMD to PDF.
- **Mechanism**: The Mathpix Python SDK supports `conversion_new(mmd=..., convert_to_pdf=True)`.
- **Advantage**: Bypasses the need for a local TeX distribution or complex CSS-to-PDF engines (like WeasyPrint). Mathpix handles the LaTeX math rendering in the cloud.
- **Cost**: Likely counts as a standard conversion transaction.

## 4. Proposed Architecture
1. **Target Selector**: `HWPXPipeline` accepts an `output_format` parameter.
2. **PDF Track**:
    - **Step 1**: Ingest PDF to MMD (Mathpix).
    - **Step 2 (Bypass)**: Instead of parsing to IR and HWP Actions, the MMD is sent back to the Mathpix conversion endpoint for PDF generation.
    - **Step 3**: Optional annotation or watermarking (using Matplotlib or basic PDF merging if a library is added).
