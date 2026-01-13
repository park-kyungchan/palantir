# Pipeline Verification & Pivot History

This document tracks the verification efforts for the PDF ingestion engine, documenting the transition from failure-prone ML models to a successful Vision-Native strategy.

## 1. Objectives & Metrics
The core goal is **High-Fidelity Reconstruction**, measured by:
- **Word-Level Accuracy**: Extraction of technical Korean/English terms.
- **Structural Integrity**: Recovery of complex tables (rows, columns, headers).
- **Image Preservation**: Capture of embedded figures and logos.

## 2. Verification Protocol (Audit v6.0)

### Stage A: Surface Scan (PASS)
- Verified repository structure has functional hybrid components (Bridge, Ingestor, Executor).
- Identified core artifacts: `convert_pipeline.py`, `executor_win.py`.

### Stage B: Structural Audit (FAILED)
- **Tooling**: `scripts/verify_parsing_quality.py` for bit-perfect side-by-side comparison.
- **Results**: 0 tables detected in dense tabular documents (`ActionTable_2504.pdf`).
- **Root Cause**: `doclayout-yolo` model crashes and stubbed image extraction logic.

## 3. The Vision-Native Pivot (VALIDATED)
Following categorical failure of ML layout models, the project pivoted to a **Vision-Native De-rendering** paradigm.

### 3.1 Pilot Success (Jan 2026)
- **Target**: `ActionTable_2504.pdf` (Page 1-15).
- **Recovery Rate**: 100% table detection (4x2 legend table recovered).
- **Validation**: Strict Pydantic SVDOM schema validation (`validate_real_twin.py`).

### 3.2 Comparison Matrix
| Metric | Docling Pipeline | Vision-Native Pipeline |
| :--- | :--- | :--- |
| Table Detection | 0% | 100% |
| Reliability | Brittle (Conv/bn crash) | High (Vision-Native) |
| Layout Accuracy| Poor | Multi-element aware |

## 4. Engineering Utilities
- `scripts/batch_processor.py`: Automates parallel image generation for 15+ page pilots.
- `scripts/validate_real_twin.py`: Confirms structural integrity of the generated Digital Twin.
- `scripts/pdf_to_image.py`: Refactored for high-DPI library use in batch workflows.
