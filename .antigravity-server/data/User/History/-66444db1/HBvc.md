# Implementation: Docling Ingestion Engine

The `DoclingIngestor` is the primary high-fidelity ingestion engine in the WSL environment, leveraging IBM's Docling for advanced document understanding.

## 1. Core Processing Pipeline

The `ingest()` method orchestrates the conversion from PDF to the internal Intermediate Representation (IR):
1.  **Conversion**: Uses `DocumentConverter` with specialized pipeline options:
    - **OCR**: Enabled using `EasyOcrOptions`, leveraging the GPU for high-speed multi-language extraction.
    - **Tables**: Table structure detection enabled for grid-perfect reconstruction.
2.  **Item Iteration**: Iterates through the `DoclingDocument` items.
3.  **Layout Enhancement**: If enabled, uses `doclayout-yolo` to reorder items based on a semantic reading order, improving the logical flow of the extracted content.
4.  **IR Mapping**: Maps Docling items (`TextItem`, `TableItem`, `PictureItem`, `SectionHeaderItem`) to internal IR components.

## 2. Table Reconstruction Logic (`_process_table`)

Docling's structural table data is mapped to the internal `Table` IR:
- **Grid Mapping**: Iterates through the table grid (rows and cells).
- **Attribute Preservation**: Captures `text`, `col_span`, `row_span`, and header status (`column_header` or `row_header`).
- **IR Result**: Generates a `Table` object containing `TableRow` and `TableCell` objects, ready for HWPX reconstruction.

## 3. Image Handling (`_process_picture`)

- **Current Implementation**: Captures the `PIL.Image` from `PictureItem`.
- **Placeholder Pattern**: Uses a `Figure` IR with a path. A production implementation requires saving the image to a temporary filesystem path that the Windows `HwpExecutor` can access.

## 4. Fallback Mechanism

If Docling ingestion fails (e.g., resource exhaustion or unsupported format), the system falls back to `_ingest_with_pymupdf`, which provides basic text extraction but limited layout fidelity compared to Docling.
