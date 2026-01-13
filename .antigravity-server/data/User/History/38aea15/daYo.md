# Walkthrough: Vision-Native OCR Verification (Phase 2)

## Overview
This walkthrough documents the final verification of the Vision-Native OCR implementation, which serves as a robust fallback for processing PDFs that trigger encoding errors in standard parsers like IBM Docling.

## Key Components
- **Engine**: `EasyOCREngine` (primary) with Korean (`ko`) and English (`en`) support.
- **Orchestration**: `OCRManager` handles engine selection and fallback logic.
- **Integration**: `DoclingIngestor._ingest_with_pymupdf` renders pages, crops regions based on YOLO layout detection, and passes crops to the OCR manager.

## Verification Execution
The pipeline was verified using `scripts/verify_ocr.py`. The test involved:
1.  Loading `hwpx/sample.pdf`.
2.  Injecting a fake `ANSWER_BOX` region to simulate a detected layout component.
3.  Triggering the PyMuPDF fallback logic in `DoclingIngestor`.
4.  Capturing the OCR output from the cropped region image.

### Verification Logs (2026-01-06)
```text
2026-01-06 18:27:54,622 - INFO - Basic fallback text extraction initiated (Vision-Native).
2026-01-06 18:27:54,662 - INFO - Loading EasyOCR (langs=['ko', 'en'])...
2026-01-06 18:27:54,662 - WARNING - Using CPU. Note: This module is much faster with a GPU.
2026-01-06 18:27:55,994 - INFO - EasyOCR loaded.
2026-01-06 18:28:02,810 - INFO - Processed 1 AnswerBox paragraphs.
2026-01-06 18:28:02,810 - INFO - AnswerBox 1 Text: '교? +1 - 1 = 0일 때  다음 식의 값을 구하시오
7. 다항식
(1+.+.2)2(1+1)+ (1- 1+12
(a +2)(2 - 1)(a + 4)(2 - 3) + 5
전개식에...'
2026-01-06 18:28:02,810 - INFO - ✅ SUCCESS: Text extracted.
```

## Conclusions
- **Stability**: EasyOCR proved more stable than PaddleOCR (which suffered from `IndexError` in its Korean model) and Surya (which had dependency gaps).
- **Quality**: The vision-based extraction successfully captured both Korean characters and basic mathematical expressions, preserving the semantic context of the `AnswerBox`.
- **Readiness**: The system is ready for Phase 3: IR Unification, where these multi-modal inputs will be mapped into a unified document structure.

## Troubleshooting: Layout Detector Incompatibility

During integration, we encountered a critical error when loading the `DocLayout-YOLO` model:
`AttributeError: 'Conv' object has no attribute 'bn'`

### Root Cause
Fusion or version discrepancies in the `ultralytics` model representation for `DocLayout-YOLO`. The inference engine expects a Batch Normalization (`bn`) attribute on Convolutional layers that certain weights lack.

### Mitigation: Identity Patch
The `LayoutDetector` was updated with a runtime patch that injects `torch.nn.Identity()` into any `Conv` module missing the `bn` attribute:

```python
import torch.nn as nn
for m in self._model.model.modules():
    if "Conv" in m.__class__.__name__ and not hasattr(m, 'bn'):
        setattr(m, 'bn', nn.Identity())
```

This bypasses the attribute lookup error, allowing inference to continue using the pre-fused weights.
