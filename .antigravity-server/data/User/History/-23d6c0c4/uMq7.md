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
- **Encoding Failures (Korean PDF)**: Docling's `DocumentConverter` failed on `sample.pdf` with `'utf-8' codec can't decode byte 0xb9`. This indicates a limitation in Docling's current handling of Korean-encoded PDF metadata or content, necessitating robust fallback mechanisms.
- **YOLO Model Compatibility**: The `DocLayout-YOLO` model experienced a runtime error (`'Conv' object has no attribute 'bn'`) when running in the `.venv` environment, likely due to a version mismatch in `ultralytics` or `torch`. This forced a logic verification using "fake regions" until model weights/environment are synchronized.
- **Spatial Metadata in Fallback**: Standard text extraction (`page.get_text()`) in PyMuPDF discards bounding box information. Logic that depends on layout alignment (like semantic tagging) requires block-based extraction (`get_text("blocks")`) to reconstruct the IR with proper spatial coordinates.
- **Vision-Native OCR Pivot**: Continuous failures in Docling's UTF-8 decoder for Korean text have forced a pivot to a vision-first approach for Phase 2. The pipeline now utilizes `OCRManager` to perform image-based text extraction on identified layout regions.
- **Dependency Gap: Surya OCR**: Initial execution of the `Vision-Native` pipeline failed due to a missing `surya.model` module in the `.venv`. The system requires `surya-ocr` for the primary vision path; `paddleocr` serves as the secondary fallback but requires model weight verification.
- **IR Persistence Bug**: Confirmed that `Section.paragraphs.append(para)` fails silently because the property returns a copy of the list. Implementation logic was corrected to use `Section.elements.append(para)` to ensure persistent document construction.
- **PaddleOCR Initialization Failures**:
    - Identified that `PaddleOCR` does not support `show_log`, `use_gpu`, or `cls` (in `ocr()` method) in the current environment's target version, causing `AttributeError`, `TypeError`, and `TypeError` respectively.
    - Fixed a `SyntaxError` (stray comma) introduced during iterative patching of the `OCREngine`.
- **OCR Input Validation**: Instrumentation confirmed that image crops passed to PaddleOCR (e.g., size 1350x1350) are non-zero, shifting the investigation of the `string index out of range` error toward internal post-processing or model connectivity issues.
- **Runtime OCR Errors**: Encountered a persistent `IndexError: string index out of range` within `PaddleOCR.ocr()` during inference on Korean image crops. This error persists after removing non-standard parameters (`cls`, `use_gpu`, `show_log`), suggesting a potential internal post-processing bug in the `korean_PP-OCRv5_mobile_rec` model or its interaction with specific crop dimensions. 
- **OCR Instrumentation**: Added shape and raw result logging to `lib/ocr/engine.py` to diagnose whether invalid image properties or specific detected text strings are triggering the internal index crash.
- **Verification Progress**: While `scripts/verify_ocr.py` successfully exercises the full routing logic (PDF -> Image -> YOLO -> OCR Manager -> PaddleOCR), the actual text extraction into IR is currently blocked by a persistent `IndexError: string index out of range` in the PaddleOCR Korean model. The pipeline itself is architecturally validated, but the extraction content validation is pending engine-level remediation.
- **Vision-Native Routing**: Verified that the `DoclingIngestor` fallback correctly routes specific layout regions (e.g. `ANSWER_BOX`) to the `OCRManager` and successfully populates the IR with text, bypassing PDF-level encoding errors.
