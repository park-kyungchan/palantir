# Implementation: Ingestion Strategies

The HWPX Pipeline supports multiple ingestion strategies to balance speed, reliability, and fidelity.

## 1. Vision-Native De-rendering (Primary)
The preferred strategy for complex, layout-dense documents (e.g., math sheets, tables). It leverages Gemini 3.0 Pro's vision capabilities to "reverse engineer" document images into a Digital Twin (SVDOM).

### 1.1 Process Flow
1. **Pre-processing**: PDF pages are converted to high-DPI images via `pdf_to_image.py`.
2. **Vision Call**: Images are sent to the Vision API with the `vision_derender.md` prompt.
3. **Atomic De-rendering**: Every paragraph, equation, and table cell is mapped as a separate block.
4. **Validation**: The resulting JSON is validated against the `DigitalTwin` Pydantic schema.

### 1.2 Validated System Prompt
The prompt enforces a strict JSON structure and instructs the model on:
- **Math Parsing**: Converting formulas to LaTeX.
- **Table Structure**: Recognizing cells as a 2D array.
- **Layout Awareness**: Distinguishing headers, body text, and captions.

## 2. Docling Ingestion (Deprecated/ML-Fallback)
The `DoclingIngestor` uses IBM's Docling for ML-based document understanding.

### 2.1 Core Pipeline
1. **Conversion**: Uses `DocumentConverter` with `EasyOcrOptions`.
2. **Table Structure**: Automatic grid detection.
3. **Layout Enhancement**: Uses `doclayout-yolo` for semantic reordering.

### 2.2 Known Limitations
- **Brittleness**: High sensitivity to version mismatches in layout models.
- **Data Loss**: Potential for catastrophic failure on dense tabular Korean documents.

## 3. PyMuPDF Ingestion (Fast Fallback)
A lightweight fallback (`_ingest_with_pymupdf`) that provides raw text extraction. It is fast but cannot recover tables or complex layouts with high fidelity.
