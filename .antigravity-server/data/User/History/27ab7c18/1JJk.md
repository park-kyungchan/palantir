# Implementation: Parsing Verification Failure Analysis

Following the execution of `verify_parsing_quality.py`, a major failure in the ingestion pipeline was identified, particularly regarding layout detection and table recovery.

## 1. Technical Bug: Doclayout-YOLO Crash

The layout enhancement engine, which uses `doclayout-yolo`, consistently failed across all test pages with the following error:

```text
WARNING - Layout detection failed for page [X]: 'Conv' object has no attribute 'bn'
```

### Analysis:
- **Root Cause**: This is typically an indicator of a version mismatch or incompatibility between the `yolov8`/`ultralytics` model weights and the specific version of `torch` or `doclayout-yolo` installed. The error suggests that the model being loaded expects a Batch Normalization (`bn`) attribute on a Convolutional layer that is either missing or has a different structure in the current environment's `torch`/`ultralytics` implementation.
- **Impact**: Without layout detection, the system cannot distinguish between text, tables, and figures. It defaults to a basic serial extraction that completely failed to recognize the dense tabular content of the HWP automation reference documents.

## 2. Structural Data Loss (0 Tables Found)

The verification dump for `ActionTable_2504.pdf` (52 pages) showed:
- **Actual Tables**: ~50+ complex tables.
- **Detected Tables**: 0.
- **Extracted Text**: 18 paragraphs.

### Implication:
The `DoclingIngestor`'s reliance on successful layout enhancement is a single point of failure. When the ML model fails, the fallback mechanism (or lack thereof for structural elements) leads to catestrophic data loss, making the current pipeline unfit for "High-Fidelity" reconstruction.

## 3. Image Handling Deficit

Code audit of `lib/ingestors/docling_ingestor.py` confirmed that `PictureItem` processing is intentionally bypassed:

```python
def _process_picture(self, section: Section, item: PictureItem):
    # For now, we stub path. Real impl needs temp file.
    section.add_paragraph().elements.append(Figure(path="embedded_image_stub"))
```

### Implication:
Even if layout detection is fixed, the system currently lacks the "materialization" logic to save images to disk and pass valid paths to the Windows reconstruction engine.

## 4. Remediation Requirements

To achieve the project goals, the following fixes are mandatory:
1.  **Dependency Alignment**: Pin `torch`, `ultralytics`, and `doclayout-yolo` to compatible versions to fix the `'Conv' object has no attribute 'bn'` crash.
2.  **Implementation of `_process_picture`**: Replace the stub with logic that saves `PIL` images to a shared assets directory accessible via `wslpath`.
3.  **Fallback Engineering**: Implement a robust fallback that can at least extract tabular data using `pymupdf` or `easyocr` coordinate-based grouping if the primary layout model fails.
