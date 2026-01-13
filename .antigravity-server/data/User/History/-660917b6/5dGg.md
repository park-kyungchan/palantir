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
- **Hybrid Fallback**: If Docling fails, the system automatically falls back to **PyMuPDF** (`fitz`) while maintaining layout detection.

### 4.2 Structural Enhancement (Hybrid Ingestion)
The ingestor is enhanced with a **DocLayout-YOLO** detector and a custom **Reading Order Sorter** to handle complex math workbooks:
1. **Layout Detection**: `LayoutDetector` identifies regions (`LayoutLabel.TITLE`, `LayoutLabel.TEXT`, `LayoutLabel.TABLE`, `LayoutLabel.ANSWER_BOX`, `LayoutLabel.PROBLEM_BOX`, etc.) on the PDF page using YOLO.
2. **IR Extension**: IR models (`Paragraph`, `Table`, `Figure`, `CodeBlock`) were extended to include a `bbox: tuple` field (storing PDF-space `[l, t, r, b]`) and a `style: str` field for semantic tagging.
3. **Alignment (Center-Point Containment)**: `DoclingIngestor._apply_external_layout_enhancement` implements a containment strategy rather than strict IoU. It calculates the geometric center of Docling-extracted items and checks if they fall within any YOLO-detected `ANSWER_BOX` or `PROBLEM_BOX` regions.
4. **Enum-Driven Semantic Tagging**: Refined logic uses the `LayoutLabel` Enum members for comparison. Items matched to specific YOLO regions are tagged (e.g., `para.style = "AnswerBox"`), enabling the compiler to apply specialized HWPX formatting (e.g. transparent table borders).
5. **Sorting**: `ReadingOrderSorter` organizes regions into a logical flow based on topological sorting (Y-first, then X-center) before mapping to the IR.

### 4.3 IR Mapping Logic
Document items are processed and mapped from the Docling internal representation to the unified `lib.ir.Document` model:
- `DocItemLabel.TEXT/PARAGRAPH` → `Paragraph` + `TextRun` (with `bbox` preservation).
- `DocItemLabel.FORMULA` → `Equation` (LaTeX script).
- `TableItem` → `Table` with row/column spans, header detection, and positional `bbox`.
- **Coordinate Risk**: Discrepancies between PDF points (Docling) and image pixels (YOLO) require `CoordinateScaler` logic to ensure robust overlap detection.

## 5. Legacy/Fallback PDF Ingestor

The `PdfIngestor` (`lib/ingest_pdf.py`) remains as a lightweight fallback using `pypdf`.
- **PUA Decoding**: Contains a manual `pua_map` for Private Use Area characters (`` → `0`, `` → `x`) often found in specialized math PDFs created with proprietary fonts.
- **Heuristic Layout**: Simple center-coordinate analysis to detect 2-column layouts and line grouping.

## 6. Knowledge Base Construction

The ingestion outputs are consolidated into the **Action Knowledge Base** (`lib/knowledge/hwpx/action_db.json`).

- **Storage & Isolation**: HWPX-specific knowledge is isolated from core logic to ensure modularity.
## 7. Runtime Environment & Dependencies

The hybrid ingestion pipeline has complex runtime requirements due to the integration of computer vision and deep learning models:

- **Core Dependencies**:
    - `docling`: Primary document understanding engine.
    - `ultralytics`: Required for YOLOv8/v10 layout detection.
    - `pymupdf` (`fitz`): Used for PDF rendering and fallback extraction.
    - `numpy`: Critical shared dependency. Discrepancies in `numpy` versions (especially when using pre-compiled `ultralytics` binaries) can lead to `ModuleNotFoundError` if not properly isolated.
- **Model Storage**: Models are lazily downloaded to the `models/` directory using `huggingface_hub`.
- **Compute Device**: `LayoutDetector` automatically detects and uses CUDA (GPU), MPS (Apple Silicon), or CPU in that order. High-fidelity parsing of complex PDFs like `sample.pdf` is significantly faster on GPU.
