# Implementation: Ingestion Strategies

The HWPX Pipeline supports multiple ingestion strategies to balance speed, reliability, and fidelity.

## 1. Vision-Native De-rendering (Primary)
The preferred strategy for complex, layout-dense documents (e.g., math sheets, tables). It leverages Gemini 3.0 Pro's vision capabilities to "reverse engineer" document images into a Digital Twin (SVDOM).

### 1.1 Process Flow
1. **Pre-processing**: PDF pages are converted to high-DPI images via `pdf_to_image.py`.
2. **Vision Call**: Images are sent to the Vision API with the `vision_derender.md` prompt.
3. **Atomic De-rendering**: Every paragraph, equation, and table cell is mapped as a separate block.
4. **Validation**: The resulting JSON is validated against the `DigitalTwin` Pydantic schema.

### 1.2 Batch Processing Pipeline
To handle large documents (e.g., 50+ pages), the `BatchProcessor` (`scripts/batch_processor.py`) automates the multi-stage flow:
- **Parallel Image Generation**: Uses `fitz` (PyMuPDF) with 2x zoom for high-DPI assets.
- **Workflow State**: Tracks `status: "image_ready_for_vision"` for each page.
- **Aggregation**: Combines individual page blocks into a single `full_doc_twin.json`.

## 2. Docling Ingestion (Deprecated/ML-Fallback)
The `DoclingIngestor` uses IBM's Docling for ML-based document understanding.

### 2.1 Core Pipeline
1. **Conversion**: Uses `DocumentConverter` with `EasyOcrOptions`.
2. **Table Reconstruction**: Automatic grid detection preserving `col_span`, `row_span`, and header status.
3. **Layout Enhancement**: Uses `doclayout-yolo` for semantic reordering.

### 2.2 Known Limitations
- **Brittleness**: High sensitivity to version mismatches in layout models (e.g., `'Conv' object has no attribute 'bn'` crash).
- **Data Loss**: Potential for catastrophic failure on dense tabular Korean documents (observed <1% recovery on some targets).

## 3. Image & Asset Handling
Capturing embedded images is critical for high-fidelity reconstruction.

### 3.1 Extraction Protocol
- **Docling**: Images are extracted as `PIL.Image` from `PictureItem`.
- **Materialization**: Images must be saved to a physical path accessible to the Windows `Executor` (e.g., via `wslpath -w`).
- **Vision-Native**: Images are processed as screenshots of the entire page, with individual elements referenced via `geometry.bbox` coordinates.

## 5. Hybrid Ingestor (Action Table PDF)
For specialized documents like the HWP Action Table (`ActionTable_2504.pdf`), a **Hybrid Ingestor** (`lib/ingestors/text_action_Ingestor.py`) is used to balance speed and accuracy.

### 5.1 Technical Implementation
- **Table Discovery**: Uses PyMuPDF's `page.find_tables()` (available in version 1.23+) to identify structural grids.
- **Bulk Extraction**: Scrapes text content directly from detected cells into a `table_data` 2D array within a `Block`.
- **Performance**: Capable of processing a 50+ page manual in seconds, compared to minutes/hours for full Vision-Native processing.

### 5.2 Role in Pipeline
The Hybrid Ingestor acts as a high-speed parser for "Knowledge Documents" that populate the system's internal databases (e.g., the Action Knowledge Base).
