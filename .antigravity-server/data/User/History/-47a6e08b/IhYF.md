# Implementation: Parsing Quality Verification Utility

To ensure word-level and structural fidelity, a dedicated verification script `scripts/verify_parsing_quality.py` is used to audit the output of the ingestion engine.

## 1. Functional Logic

The utility performs the following steps:
1.  **Ingestion Execution**: Initializes the `DoclingIngestor` with high-fidelity settings:
    - `enable_ocr=True`
    - `enable_table_structure=True`
    - `enable_layout_enhancement=True`
2.  **Structural Audit**: Traverses the resulting IR `Document` and extracts key information:
    - Paragraph text content
    - Table dimensions and cell content
    - Figure paths and captions
3.  **Human-Readable Dump**: Generates a flattened text representation (`.dump.txt`) specifically designed for manual side-by-side comparison with the source PDF and previous text extractions.

## 2. Benchmark Metrics

The script outputs completion statistics for each processed file:
- **Total Paragraphs**: Count of extracted text blocks.
- **Total Tables**: Number of reconstructed table structures.
- **Total Figures**: Count of images/figures identified.

## 3. Usage Pattern

Processing is handled **sequentially** to respect system memory limits (16GB RAM), as the Docling model and layout enhancement engines are resource-intensive.

```bash
# Executed within the project virtual environment
.venv/bin/python scripts/verify_parsing_quality.py
```

Outputs are saved to a `verification_output/` directory for analysis.
