# Architecture: Digital Twin & SVDOM Paradigm

The "Digital Twin" approach is a strategic pivot in the HWPX Reconstruction Pipeline, moving from traditional OCR/Layout analysis to a **Vision-Native De-rendering** strategy.

## 1. The Semantic-Visual DOM (SVDOM)

The core data structure is a Hybrid JSON Schema called the SVDOM. Unlike traditional document models that interleave properties, the SVDOM enforces strict separation of concerns across three vectors:

1.  **Content (The "What")**: The raw data, such as plain text, LaTeX math formulas, or image references.
2.  **Style (The "How")**: Visual presentation metadata including alignment, font-weights, padding, and margins. This allows for CSS-like manipulation of the document.
3.  **Geometry (The "Where")**: Physical bounding boxes (`bbox`) on the page (expressed in % or pixels). This is used for "Vision-Native" verification—ensuring the regenerated document matches the spatial layout of the original ground truth.

## 2. Strategic Objectives

- **Fidelity**: Use Vision LLMs (e.g., Gemini 3.0 Pro) to directly "de-render" pixels into the SVDOM, bypassing the catastrophic structural failures of open-source OCR engines (like `doclayout-yolo` version mismatches).
- **Interactivity**: Enable natural language editing of the document structure (e.g., "Add 10px padding to all questions").
- **Precision**: Extract math formulas as clean LaTeX and tables as semantic 2D arrays, rather than garbled text blocks.

## 3. Data Flow

1.  **De-rendering**: Vision Model parses the PDF image -> SVDOM JSON.
2.  **Digital Twin Editor**: User/Agent modifies the SVDOM (Content or Style fields).
3.  **Reconstruction**: The modified SVDOM is compiled via a rendering engine (HTML/CSS or direct OLE automation) into the target format (PDF/HWPX).
