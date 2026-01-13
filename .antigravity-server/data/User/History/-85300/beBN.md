# HWPX Ingestion Stack

This document describes the multi-modal ingestion framework used to transform source documents into a structured Intermediate Representation (IR).

## 1. Evolution of the Ingestion Strategy

The pipeline evolved through three major phases to handle the complexity of math-heavy Korean workbooks:

1.  **Phase 1-6 (Local Hybrid)**: Utilized IBM Docling and DocLayout-YOLO for layout detection and local OCR (EasyOCR/Paddle).
2.  **Phase 7 (Mathpix Pivot)**: Replaced local OCR with Mathpix Cloud OCR to achieve pixel-perfect math formula extraction.
3.  **Phase 8 (Pipeless Reconstruction)**: Integrated Mathpix Converter API for direct MMD-to-PDF rendering.

---

## 2. Ingestion Engines

### 2.1 Mathpix Cloud Ingestor (Production Standard)
The `MathpixIngestor` (`lib/ingestors/mathpix_ingestor.py`) is the primary engine as of Phase 7.
- **Workflow**: Uploads PDF to `v3/pdf` -> Polls for conversion -> Retrieves Mathpix Markdown (MMD).
- **Advantages**: Superior Math OCR (fractions, roots), multi-column awareness, and CJK support.
- **Implementation Note**: Uses `options_json` to avoid multipart/form-data parsing errors on the server.
- **Asset Retrieval**: Discovered that JSON responses might not contain signed URLs even after completion. FALLBACK: Construct resource URL explicitly as `/{id}.pdf` and pass `app_id`/`app_key` headers in the GET request.

### 2.2 IBM Docling & DocLayout-YOLO (Legacy/Fallback)
Docling is used as a fallback for structural layout analysis.
- **DocLayout-YOLO Compliance**: Required extensive monkey-patching of `DilatedBlock` and `DocLayoutWrapper` to fix attribute errors (`bn`) and output format mismatches (`one2one` tensor dict vs tensor).
- **IoU Matching**: Aligns YOLO identified regions (Problem/Answer boxes) with Docling items using geometric Intersection over Union.

---

## 3. Mathpix Markdown (MMD) Parsing

The `MarkdownParser` (`lib/parsers/markdown_parser.py`) transforms MMD into the unified IR.

### 3.1 Structural Mapping
- **Blocks**: Headings (Style: "Header"), Paragraphs, and semantic containers matched via regex.
- **Inline Elements**: Tokenized via a priority-based regex split:
    1.  **Display Math** / **Inline Math**: Mapped to `Equation`.
    2.  **Images**: Mapped to `Image` with remote URL extraction.
    3.  **Formatting**: Bold (`**...**`) preserved as `TextRun.is_bold`.

### 3.2 Coordination and Schema Alignment
- **Section Structure**: Uses `Section.elements` for its child collection.
- **Image Stride**: Processes capturing groups in strides of 3 (`text`, `alt`, `url`) to ensure robust recursion for nested formatting.

---

## 4. Coordinate System Normalization

Bridging the gap between Image-Space (Top-Left) and PDF-Space (Bottom-Left) coordinates:
1.  **Flipping**: `LayoutDetector` flips the Y-axis based on page height for IoU matching.
2.  **Cropping**: The ingestor performs an inverse flip to correctly isolate page images for region-specific OCR.

---

## 5. Operations and Performance

- **Lazy-Loading**: Heavyweight libraries (Docling, Torch) are only imported if Mathpix is disabled, reducing startup time by ~30s.
- **Resilience**: Execution for cloud-polling tasks should utilize `nohup` to prevent termination during long-running API calls.
