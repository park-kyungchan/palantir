# Ingestion Strategy: Docling & Mathpix Integration

## 1. The Challenge: UTF-8 Decoding Failures
During large-scale PDF ingestion using IBM Docling, certain documents (e.g., `sample.pdf` with specific Korean/symbol encodings) trigger `utf-8 decode byte 0xb9` errors. 

- **Root Cause**: Low-level PDF stream anomalies or encoding mismatches in the Docling preprocessing layer.
- **Impact**: Blocks the IR (Intermediate Representation) generation, halting the pipeline.

## 2. Resolved Strategy: Mathpix Fallback/Primary
To ensure high-fidelity text and formula extraction without relying on fragile direct PDF parsing, the pipeline is transitioning to a **Mathpix-First** or **Mathpix-Fallback** strategy.

### 2.1 Methodology
1. **Initial Scan**: Attempt Docling ingestion for layout and table structure.
2. **Error Detection**: If `UnicodeDecodeError` or model access (HuggingFace DNS) failures occur.
3. **Mathpix Relay**:
    - Convert PDF pages to images.
    - Submit to Mathpix OCR for high-fidelity Markdown/LaTeX extraction.
    - Map Mathpix Markdown back to the ODA Internal Representation (Paragraph, Equation, Table).
4. **OWPML-Only Generation**: Ensure all extracted text/formulas are reconstructed using `HwpxDocumentBuilder` (Native OWPML) rather than legacy OLE Automation.

## 3. Constraint: Native Generation Only
The ODA has strictly deprecated the use of `HAction` and `executor_win.py`. 
- **Legacy Path**: Direct Windows automation.
- **Native Path**: Building HWPX package from scratch (ZIP + XML).
- **Enforcement**: Ingestors must produce IR elements that the `HwpxDocumentBuilder` can serialize natively.

---

## 4. PyMuPDF Fallback & Diagnostic
During the implementation of this strategy, a critical regression was identified in the `PyMuPDFIngestor`.

- **Finding**: The ingestor was attempting to append to `section.paragraphs`, which had become a read-only property in the revised IR.
- **Resolution**: Updated `PyMuPDFIngestor` to use `section.elements.append()` for direct IR storage.
- **Outcome**: PyMuPDF now correctly extracts text layer content from non-scanned PDFs (e.g., `sample.pdf`) providing a robust baseline when Docling fails.

---
**Status**: VALIDATED. Strategy refined with PyMuPDF as a verified backup.
