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

## 3. Native HWPX XML Ingestion

The `HwpxIngestor` (`lib/ingest_hwpx.py`) extracts structure and styles directly from OOXML-compliant HWPX ZIP archives.

### 3.1 Mapping to IR
- **Paragraphs (`hp:p`)**: Maps to `Paragraph` IR nodes, preserving alignment and text runs.
- **Tables (`hp:tbl`)**: Navigates XML grid nodes to reconstruct rows and cells.
- **Namespace Handling**: Precise parsing using Hancom-specific namespaces (`hp`, `hc`, `hh`).

## 4. Knowledge Base Construction

The ingestion outputs are consolidated into the **Action Knowledge Base** (`lib/knowledge/hwpx/action_db.json`).

- **Storage & Isolation**: HWPX-specific knowledge is isolated from core logic to ensure modularity.
- **Compiler Integration**: The compiler uses the database to validate document intents, retrieve required parameter sets, and generate valid OLE automation code.
