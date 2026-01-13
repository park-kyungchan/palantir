# Audit: PDF Parsing Pipeline (January 2026)

This audit follows the `AuditProtocol` to verify the "Pre-HWPX" pipeline, focusing on the transformation from PDF to Intermediate Representation (IR).

## 1. Component Mapping (Stage A)

| File | Responsibility | Logic / Pattern |
| :--- | :--- | :--- |
| `lib/pipeline.py` | Orchestration | `PDF -> Ingestor -> IR -> Compiler` |
| `lib/ingest_pdf.py` | Legacy Ingestion | `pypdf` + Visitor Text + PUA Decoding |
| `lib/ingestors/docling_ingestor.py` | High-Fidelity Ingestion | IBM Docling + DocLayout-YOLO + Reading Order |
| `lib/models.py` | IR Definition | Pydantic models for HWP Actions |

## 2. Logic Trace: PDF to IR (Stage B)

### 2.1 docling_ingestor.py
- **Initialization**: Sets up `DocumentConverter` with `EasyOcrOptions`.
- **Flow**:
    1.  `ingest()` calls `converter.convert()`.
    2.  `_apply_layout_enhancement()` uses `LayoutDetector` (DocLayout-YOLO) to find regions.
    3.  `_match_and_reorder()` uses IoU to align Docling items with detected regions.
    4.  `_process_item()` maps Docling items (Text, Formula, Code) to IR objects (`Paragraph`, `Equation`, `CodeBlock`).
- **Safety**: Robust fallback to `PyMuPDF` if IBM Docling fails.

### 2.2 ingest_pdf.py (Fallback)
- **PUA Map**: Handles Private Use Area characters (`0xEA00` range) for math symbol reconstruction.
- **Deduplication**: Filters "shadow" or "bold" effects in PDF where the same text is printed twice with a slight offset.
- **Column Detection**: Heuristic based on text block distribution (center-gap analysis).

## 3. Quality Gate (Stage C)

- **Pattern Fidelity**: ALIGNED. Separation of concerns between ingestion (`DoclingIngestor`) and representation (`models.py`).
- **Signature Match**: PASS. `ingest(path: str) -> Document` is consistent across ingestors.
- **Safety Audit**: Type hints and Pydantic validation are utilized effectively.

## 4. Findings & Environment Insights (v5.0 Update)

- **Orphaned Artifacts**: `prompts/vision_derender.md` is detected as an **orphan**. While it contains high-quality Vision-Native de-rendering logic, it is currently disconnected from the main pipeline. 
- **Incomplete Implementation**: `_process_picture` and several OCR enhancement steps in `docling_ingestor.py` remain as stubs (`pass` blocks).
- **Environment Constraints**: The pipeline relies on a specific virtual environment; executing via system Python leads to `ModuleNotFoundError` for `pydantic`.
- **Math Precision**: Docling's formula extraction is being leveraged, but qualitative validation of Korean math symbols in `sample.pdf` is an ongoing risk.
- **Legacy Components**: `lib/ingest_pdf.py` is maintained as a fallback but is technically legacy compared to the Docling-based hybrid approach.
- **Dependency Isolation**: A conflict was identified where `ultralytics` and `docling` dependencies (specifically `numpy`) were not resolvable in the system environment. Resolution requires a dedicated virtual environment (`.venv`) to ensure bin/path consistency for the YOLO model.
