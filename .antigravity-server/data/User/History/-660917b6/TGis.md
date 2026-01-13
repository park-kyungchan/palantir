# HWPX Ingestion Framework

The HWPX Pipeline utilizes a multi-modal ingestion framework to transform various source formats (PDF manuals, HWPX documents, images) into a structured Digital Twin or Knowledge Base.

## 1. Vision-Native De-rendering (SVDOM Generation)

The primary strategy for complex, layout-dense documents. It leverages Gemini 3.0 Pro's vision capabilities to "reverse engineer" document images into a Structured Visual Document Object Model (SVDOM).

### 1.1 Process Flow
1. **Pre-processing**: PDF pages are converted to high-DPI images via `pdf_to_image.py`.
2. **Vision Call**: Images are sent to the Vision API with the `vision_derender.md` prompt.
3. **Atomic De-rendering**: Every paragraph, equation, and table cell is mapped as a separate block with geometry (bounding boxes) and styles.
4. **Validation**: The resulting JSON is validated against the `DigitalTwin` Pydantic schema.

### 1.2 Batch Processing Pipeline
The `BatchProcessor` (`scripts/batch_processor.py`) automates the multi-stage flow for multi-page documents, tracking page status and aggregating individual JSON blocks into a document-wide twin.

## 2. Layout-Based Hybrid Ingestion (Reference Manuals)

For structured reference manuals like `ActionTable_2504.pdf`, a high-speed **Layout-based Ingestor** (`lib/ingestors/layout_text_ingestor.py`) is utilized. This approach uses `pdftotext -layout` to preserve visual alignment.

### 2.1 Action Table Parsing
- **Data Source**: `ActionTable_2504.pdf` (Reference manual).
- **Fixed-Width Slicing**: Extracts data using character offsets (Action ID at 0-24, ParameterSet at 24-44, Description at 44+).
- **Stateful Row Merging**: Detects new records via the presence of an Action ID and appends overflow text to the description column until the next ID appears.
- **Symbol Resolution**: Handles specific markings (`+`, `-`, `*`) to determine execution behavior (e.g., `run_blocked` status).

### 2.2 Parameter Set Table Parsing
The `LayoutParameterIngestor` (`lib/ingestors/parameter_ingestor.py`) handles the hierarchical `ParameterSetTable_2504.pdf`.
- **Dependency Flow**: **Action ID** → **ParameterSet ID** → **Parameter Items**.
- **Section Segmentation**: Uses regex (`^\s*\d+\)\s+(\w+)\s*:`) to split the document into discrete parameter set definitions.
- **Hierarchical Table Parsing**: Uses tuned offsets (ID: 0-19, Type: 19-40, Desc: 40+) to extract parameter item IDs, types (e.g., `PIT_BSTR`), and descriptions (including enums).

### 2.3 Heuristic Filtering for Dirty Manuals
To prevent column pollution from embedded code blocks in reference manuals, the ingestors apply heuristic validation:
- **Code Symbol Rejection**: Lines containing `=`, `;`, `(`, or `.` in identifying columns (Action ID or ParameterSet ID) are treated as description continuations rather than new records.
- **Structure Enforcement**: Valid identifiers are expected to follow CamelCase or specific naming patterns (e.g., no spaces in internal IDs).
- **Leakage Routing**: Anything failing validation in the ID columns is automatically routed to the `Description` field of the previous active record, preserving 100% of the manual's content without polluting the search keys.

### 2.4 Technical Guide Ingestion (Events)
The `TextEventIngestor` (`lib/ingestors/event_ingestor.py`) extracts HWP Automation Events from technical C++ guides like `한글오토메이션EventHandler추가_2504.pdf`.
- **Regex Extraction**: Patterns like `STDMETHOD\s*\(\s*(\w+)\s*\)\s*\((.*?)\)` target COM interface definitions.
- **Mapping**: Converts C++ `STDMETHOD` signatures into `EventDefinition` objects for the Knowledge Base.

### 2.5 API Reference Ingestion (Methods & Properties)
The `APIIngestor` (`lib/ingestors/api_ingestor.py`) parses the core automation guide `HwpAutomation_2504.pdf`.
- **Target**: Extracts the primary API surface of the `HwpObject` / `HwpCtrl`.
- **Pattern Matching**: Scans for `Name(Method)` and `Name(Property)` anchors in the layout text.
- **Scale**: Captured **138 Methods** and **223 Properties**, enabling deep programmatic control beyond standard Action triggers.

## 3. Native HWPX XML Ingestion

The `HwpxIngestor` (`lib/ingest_hwpx.py`) extracts structure and styles directly from OOXML-compliant HWPX ZIP archives.

### 3.1 Mapping to IR
- **Paragraphs (`hp:p`)**: Maps to `Paragraph` IR nodes, preserving alignment and text runs.
- **Tables (`hp:tbl`)**: Navigates XML grid nodes to reconstruct rows and cells.
- **Namespace Handling**: Precise parsing using Hancom-specific namespaces (`hp`, `hc`, `hh`).

## 4. Next-Gen Ingestion: IBM Docling & DocLayout-YOLO

The refined ingestion pipeline (`lib/ingestors/docling_ingestor.py`) represents the current production standard, moving beyond simple OCR to comprehensive document understanding.

### 4.1 DoclingIngestor Logic
- **Primary Engine**: IBM Docling (`DocumentConverter`) provides the base for layout and table recognition.
- **Multilingual OCR**: Configured for `ko` (Korean) and `en` (English) via `EasyOcrOptions`.
- **Hybrid Fallback**: If Docling fails (e.g., encoding errors, service failure), the system triggers a **Vision-Native Fallback** handler (`_ingest_with_pymupdf`). This handler renders PDF pages to high-resolution images, crops them based on identified `layout_regions`, and passes the crops to `OCRManager` for text extraction.
- **Block Fallback (Safety)**: If no layout regions are detected, the handler falls back to PyMuPDF's `get_text("blocks")` to preserve spatial coordinates for raw text extraction.
- **Encoding Constraint**: A known critical limitation exists in Docling's internal decoder when processing certain Korean-encoded PDF metadata or content. Specifically, if a PDF page contains characters that cannot be decoded into standard UTF-8 (e.g., encountering invalid start bytes like `0xb9` in position 1), Docling will raise a `ConversionError` for that page.
- **Vision-Native Mitigation**: Since the encoding error is often tied to the PDF's text layer rather than its visual representation, the **Vision-Native Fallback** is the primary solution. This path ignores the problematic text encoding entirely and utilizes rendered images for extraction.

### 4.2 Structural Enhancement (Hybrid Ingestion)
The ingestor uses a two-stage layout analysis process to handle complex math workbooks:

1. **Raw Layout Detection**: `LayoutDetector` identifies generic structural regions (`LayoutLabel.TITLE`, `LayoutLabel.TEXT`, `LayoutLabel.TABLE`, `LayoutLabel.FIGURE`, etc.) using **DocLayout-YOLO**. 
2. **Vision-Native OCR Extraction (Pass 1)**: For each detected region, the ingestor renders the page crop and uses `OCRManager` to extract text. This populates the `text` attribute of the `LayoutRegion`.
3. **Heuristic Refinement (Pass 2: SemanticTagger)**: With text now available, the `SemanticTagger` post-processes these regions using content-based heuristics. This sequence resolves the **Temporal Coupling** issue where tagging failed on empty regions.
4. **IR Extension**: IR models (`Paragraph`, `Table`, `Figure`, `CodeBlock`) include a `bbox: tuple` field (storing PDF-space `[l, t, r, b]`) and a `style: str` field for semantic tagging.
5. **Alignment (IoU Matching)**: `DoclingIngestor._match_and_reorder` performs geometric matching between Docling's natively identified `DocItem`s and YOLO/Heuristic regions.
6. **Bi-directional Coordinate Mapping**: 
    - **Detection Phase**: `LayoutDetector.detect_pdf_page` converts Image pixels (Top-Left) to PDF points (Bottom-Left) for **IoU matching**.
    - **Extraction Phase**: `DoclingIngestor` converts PDF points back to Image pixels for **precise OCR cropping**.
    - Discrepancies resolved by flipping the Y-axis based on cached `page_height` at both boundaries.
7. **Semantic Style Assignment**: If an item falls within an `ANSWER_BOX` or `PROBLEM_BOX` (matched via IoU), it inherits the semantic label. The `DoclingIngestor._match_and_reorder` method returns enriched tuples including this label.
8. **Mapping to IR**: This label is propagated through `_process_item`, where it overrides the default `"Body"` style with `"AnswerBox"` or `"ProblemBox"`.
9. **Sorting**: `ReadingOrderSorter` organizes regions into a logical flow based on topological sorting (Y-first, then X-center) before mapping to the IR.

### 4.3 IR Mapping Logic
Document items are processed and mapped from the Docling internal representation to the unified `lib.ir.Document` model:
- `DocItemLabel.TEXT/PARAGRAPH` → `Paragraph` + `TextRun` (with `bbox` preservation).
- `DocItemLabel.FORMULA` → `Equation` (LaTeX script).
- `TableItem` → `Table` with row/column spans, header detection, and positional `bbox`.
- **Coordinate Normalization**: Resolved the discrepancy between PDF points (Docling) and image pixels (YOLO) by implementing a flip-and-scale transformation in the detection layer (mapping Image-Space Top-Left to PDF-Space Bottom-Left).

### 4.4 Vision-Native OCR Pillar
To overcome Docling's UTF-8 encoding limitations with Korean PDFs, a **Vision-Native OCR** strategy is implemented via the `OCRManager` (`lib/ocr/manager.py`):
- **Core Orchestration**: Manages primary (e.g., `surya`) and fallback (e.g., `paddle`) engines.
- **Region-Aware Extraction**: Uses `LayoutDetector` to isolate regions (Paragraphs, Equations) as image crops. Employs **Symmetric Coordinate Transformation** to ensure that PDF-space bounding boxes are accurately mapped back to the top-left-origin image pixmap for cropping.
- **Multilingual Support**: Specifically optimized for Korean (`ko`) and English (`en`) workbook content.
    - **Engine-Specific Configurations**:
        - **EasyOCR**: **Verified Production Primary** for Phase 2. Uses `easyocr.Reader(['ko', 'en'])`. Integrated via `EasyOCREngine` as a robust multilingual backend. Successfully bypassed the post-processing crashes found in Paddle and dependency gaps in Surya, providing high-fidelity text extraction from workbook crops.
        - **PaddleOCR**: Relegated to legacy fallback due to persistent `IndexError: string index out of range` in the Korean mobile model and lack of support for standard parameters (`show_log`, `use_gpu`, `cls`) in certain environments.
        - **Surya**: Deactivated in main path due to runtime environment constraints (`surya-ocr` dependency isolation).
- **Masking**: Supports masking out specific regions (like complex equations) to improve text OCR reliability.

## 5. Legacy/Fallback PDF Ingestor

The `PdfIngestor` (`lib/ingest_pdf.py`) remains as a lightweight fallback using `pypdf`.
- **PUA Decoding**: Contains a manual `pua_map` for Private Use Area characters (`` → `0`, `` → `x`) often found in specialized math PDFs created with proprietary fonts.
- **Heuristic Layout**: Simple center-coordinate analysis to detect 2-column layouts and line grouping.

## 6. Knowledge Base Construction

The ingestion outputs are consolidated into the **Action Knowledge Base** (`lib/knowledge/hwpx/action_db.json`).

- **Storage & Isolation**: HWPX-specific knowledge is isolated from core logic to ensure modularity.
## 7. Heuristic-Based Semantic Tagging

In specialized document domains like math workbooks, off-the-shelf layout detection models (e.g., DocLayout-YOLO) often provide generic categories. The `SemanticTagger` (`lib/layout/semantic_tagger.py`) refines these using content-based heuristics.

### 7.1 Rule Set and Patterns
- **ProblemBox**: Identifies starts like "7.", "(1)", or "[01]" using regex `^\s*(\d+[\.)]|\(\d+\)|\[\d+\])\s+`.
- **AnswerBox**: Identifies keywords like "풀이" (Solution), "정답" (Answer), or "해설" (Explanation).
- **OCR Robustness**: Patterns search within the first 30 characters and allow for leading "OCR noise" characters common in math extraction.

### 7.2 Semantic Label Propagation (Hybrid Flow)
In the hybrid ingestion flow, labels are propagated from detected `LayoutRegion`s to Docling `DocItem`s using **Intersection over Union (IoU)** matching. Any item significantly overlapping a tagged region inherits that label (e.g., `ANSWER_BOX` -> `style="AnswerBox"` in IR).

### 7.3 Coordinate System Normalization
A critical integration step is aligning the **Top-Left origin** (Images/YOLO) with the **Bottom-Left or standardized Top-Left** (PDF/Docling). 
- **The Flip**: `LayoutDetector.detect_pdf_page` converts image-space pixels to PDF-space points by flipping the Y-axis based on page height.
- **OCR Cropping**: Conversely, the ingestor must perform an inverse flip when cropping page images for OCR; otherwise, it crops the vertical mirror of the intended content.

## 8. Runtime Environment & Dependencies

The hybrid ingestion pipeline has complex runtime requirements due to the integration of computer vision and deep learning models:

- **Core Dependencies**: `docling`, `ultralytics`, `pymupdf` (`fitz`), `numpy`.
- **Model Incompatibility Patches**: 
    - **Attribute Error**: `LayoutDetector` includes a post-load runtime patch to inject `torch.nn.Identity()` into affected modules that lack `bn`.
    - **Output Format Error**: Uses a **Transparent Model Wrapper** to extract primary output tensors from models returning dicts.
- **Resource Management**: Developers must cache `page_height` *before* closing `doc` handles to avoid `ValueError` crashes during coordinate transformation.

## 9. Alternative: Vision-Native API (SVDOM) Approach

As an alternative to local layout detection, the pipeline supports a Gemini-native de-rendering strategy using high-DPI images and a prescriptive system prompt (`prompts/vision_derender.md`) to reverse-engineer pixels directly into JSON blocks.

## 10. Production Standard: Mathpix Cloud OCR (Phase 7)

Introduced in Jan 2026 as the primary engine for high-fidelity math extraction. 
- **Strategy**: Bypasses local OCR/Layout dependencies by sending PDF to Mathpix `v3/pdf`.
- **Output**: Retrieves Mathpix Markdown (MMD), which is then parsed into IR by `MarkdownParser`.
- **Benefit**: Pixel-perfect math de-rendering and robust multi-column handling.

## 11. Integrated Verification & Regression Testing

To ensure the stability of the IR output after pipeline changes, use `scripts/verify_ir.py`.
- **Structural Checks**: Validates presence of `Section` and `Paragraph` elements.
- **Semantic Tag Verification**: Explicitly checks for the presence of `AnswerBox` and `ProblemBox` styles.
