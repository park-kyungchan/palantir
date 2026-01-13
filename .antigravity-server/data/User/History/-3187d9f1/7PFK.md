# Parsing Quality Verification Report
**Date:** 2026-01-05
**Subject:** High-Fidelity Parsing Verification of `ActionTable_2504.pdf`

## Executive Summary
**Result:** 🔴 **CRITICAL FAILURE**
The current parsing pipeline failed to extract meaningful content from the test document. The process resulted in near-total data loss, with zero tables and zero images recovered. The "High Fidelity" goal is currently not met.

| Metric | Target | Actual Result | Status |
| :--- | :--- | :--- | :--- |
| **Text Recovery** | > 99% | < 1% (18 paragraphs) | 🔴 FAILED |
| **Table Structure** | Precise | 0 Tables Found | 🔴 FAILED |
| **Image Extraction** | Full Content | 0 Images (Stubbed) | 🔴 FAILED |

## Deep Dive Findings

### 1. Layout Detection Failure
The `doclayout-yolo` model, which is responsible for detecting page structure (Text vs Table vs Image), failed on **every single page** of the 52-page document.
```text
WARNING - Layout detection failed for page 14: 'Conv' object has no attribute 'bn'
...
WARNING - Layout detection failed for page 52: 'Conv' object has no attribute 'bn'
```
*Root Cause:* Likely a compatibility issue between `doclayout-yolo` model weights and the CPU-only `torch` environment or version mismatch.

### 2. Image Extraction Stub
Code analysis of `lib/ingestors/docling_ingestor.py` confirmed that image extraction is explicitly **stubbed**:
```python
def _process_picture(self, section: Section, item: PictureItem):
    # For now, we stub path. Real impl needs temp file.
    section.add_paragraph().elements.append(Figure(path="embedded_image_stub"))
```
Even if layout detection worked, images would not be saved to disk.

### 3. Data Loss
The output dump (`ActionTable_2504.pdf.dump.txt`) contains only 18 paragraphs, mostly headers or isolated lines. The vast majority of the document (Action Tables) was completely ignored due to the layout failure.

## Recommendations
1.  **Fix Dependencies:** Investigate the `doclayout-yolo` / `torch` version conflict to enable layout detection on CPU.
2.  **Implement Image Handling:** Replace the `embedded_image_stub` with actual image extraction logic (saving `PIL.Image` to disk).
3.  **Alternative Pipeline:** If `doclayout-yolo` remains unstable on CPU, fallback to a purely `pymupdf` or `surya-ocr` based extraction for tables.

## Next Steps
- Await approval to implement fixes for `DoclingIngestor`.
- Pause verification of other files until the pipeline is functional.
