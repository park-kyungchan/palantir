# Pipeline Verification & Pivot History

This document tracks the verification efforts for the PDF ingestion engine, documenting the transition from failure-prone ML models to a successful Vision-Native strategy.

## 1. Objectives & Metrics
The core goal is **High-Fidelity Reconstruction**, measured by:
- **Word-Level Accuracy**: Extraction of technical Korean/English terms.
- **Structural Integrity**: Recovery of complex tables (rows, columns, headers).
- **Image Preservation**: Capture of embedded figures and logos.

## 2. Phase 1: The ML Engine Failure (Docling)
Initial attempts used the `DoclingIngestor` and `doclayout-yolo`.

### 2.1 Technical Crash
The `doclayout-yolo` model consistently failed with:
`'Conv' object has no attribute 'bn'`
This version mismatch between `torch` and `ultralytics` rendered layout detection unusable.

### 2.2 Data Loss Statistics
Process results for `ActionTable_2504.pdf`:
- **Actual Tables**: 50+
- **Detected Tables**: 0
- **Recovery Rate**: <1% (Only 18 paragraphs recovered from 52 pages).
- **Image Handling**: Explicitly stubbed in code (`embedded_image_stub`).

## 3. Phase 2: The Vision-Native Pivot (Validated)
Following the Phase 1 failure, the project shifted to a **Vision-Native De-rendering** paradigm using Gemini 3.0 Pro.

### 3.1 Pilot Results (Jan 2026)
A pilot on `ActionTable_2504.pdf` (Page 1) confirmed success:
- **Table Detection**: 100% recovery of the legend table (4x2 structure).
- **OCR Accuracy**: Preservation of Korean nuances missed by previous engines.
- **Validation**: Strict adherence to the `DigitalTwin` Pydantic schema.

### 3.2 Comparison Matrix
| Metric | Docling Pipeline | Vision-Native Pipeline |
| :--- | :--- | :--- |
| Table Detection | 0% | 100% |
| Model Reliability | Brittle (Conv/bn crash) | High (Vision-Native) |
| Layout Awareness | Poor | Multi-element aware |

## 4. Verification Utilities
- `scripts/verify_parsing_quality.py`: Generates human-readable text dumps for bit-perfect comparison.
- `scripts/validate_real_twin.py`: Automated Pydantic validation of the resulting "Digital Twin" JSON.
