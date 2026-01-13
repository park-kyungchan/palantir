# HWPX Reconstruction Pipeline: Deep Technical Audit (January 2026)

This document provides a low-level technical analysis of the pipeline's core components, focusing on the mapping between the Digital Twin (IR) and the OWPML specification (KS X 6101).

## 1. Coordinate Systems & Units
- **Precision**: The pipeline uses **HwpUnits** (1/7200 inch) as the master coordinate system.
- **Conversion**: 1 mm is standardized as **283.46 HwpUnits**.
- **Page Dimensions**: A standard A4 page is modeled as **151240 x 213940 HwpUnits** (~533 x 755 points). The content area (accounting for 30mm margins) is approximately **108260 HwpUnits** wide.

## 2. OWPML XML Structural Nuances

### 2.1 Nested Column Layout (`colPr`)
- **Discovery**: Multi-column definitions must be placed in a `<hp:ctrl>` block within the *first paragraph's run* of a section, immediately following the `<hp:secPr>` element.
- **Implementation**: `HwpxDocumentBuilder._set_column_layout` performs a pre-scan of the action stream to inject this correctly before content processing begins.

### 2.2 Equation Rendering (`eqEdit`)
- **Discovery**: HWP math equations (`eqEdit`) are sensitive to the presence of `<hp:linesegarray>`.
- **Finding**: Manually calculating line segments often leads to render artifacts in Hancom Office.
- **Best Practice**: The pipeline intentionally **omits** the `linesegarray` child. This triggers the Hancom rendering engine to auto-calculate the layout upon opening, ensuring pixel-perfect math fonts.

### 2.3 Table Merging Logic
- **Discovery**: OWPML uses a "No Ghost Cell" policy. Merged regions are defined solely at the top-left origin cell via `<hp:cellSpan>`, and subsequent cells covered by the span are omitted from the XML stream.
- **Implementation**: The `Compiler` tracks a `covered_cells` set while iterating through the grid to prevent emitting orphaned `<hp:tc>` elements.

## 3. Compiler State Machine (`lib/compiler.py`)
The `Compiler` maintains a persistent state during IR traversal to minimize XML bloat:
- **Style Sticky-ness**: It only emits `SetFontSize` or `SetFontBold` actions when the IR `TextRun` differs from the current compiler state.
- **Paragraph Shapes**: Semantic styles like `ProblemBox` are mapped to specific point-based indent increments (e.g., -20pt hanging indent for "1. ").

## 4. Package Normalization
The `package_normalizer.py` ensures the ZIP archive is compliant with the strict ordering required by Hancom Office 2024:
1. `mimetype` must be the first file and uncompressed.
2. XML declarations must be normalized.
3. Logical ordering of section files within the `Contents/` directory must match the `content.hpf` manifest.

## 5. Ingestion Engine Comparison

| Feature | Mathpix (OCR-Native) | Docling (Structural-Native) |
|---|---|---|
| **Primary Strength** | Math symbols, chemical formulas | Document structure, reading order |
| **Parsing Path** | MMD -> MarkdownParser -> IR | PDF Stream -> Docling IR -> IR |
| **Layout Enhancement**| N/A | DocLayout-YOLO (Semantic Tagging) |
| **Best For** | STEM Workbooks | Legal/Corporate Reports |

---
*Audit conducted via the Orion ODA Deep-Audit Protocol (Jan 2026).*
