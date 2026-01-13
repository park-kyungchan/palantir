# Implementation: Intermediate Representation (IR)

The IR serves as a platform-independent model of the document structure, allowing the pipeline to translate various input formats (PDF, HWPX) into a common format for reconstruction.

## 1. Document Structure

The IR is hierarchical and defined in `lib/ir.py` using Python `dataclasses`.

- **Document**: The root container, consisting of a list of `Section` objects.
- **Section**: Represents a major document division (like a page or a chapter). It holds layout properties like `columns`, `col_gap`, and a list of `elements`.
- **Paragraph**: A block of content containing one or more `elements` (TextRun, Equation, Image, etc.) and alignment/spacing properties.
- **Table**: A structured grid of `TableRow` and `TableCell` objects. Supports captions and width attributes.

## 2. Core Elements

- **TextRun**: The smallest unit of text, capturing content, `font_size`, `font_name`, `is_bold`, and `letter_spacing`.
- **Equation**: Stores math formulas in script format (LaTeX or HWP-specific script).
- **Image/Figure**: 
    - `Image`: Typically inline images with path, width, and height.
    - `Figure`: A more complex image object with support for captions.
- **Container**: A generic layout container used for text boxes or absolute positioned regions, containing nested paragraphs or tables.
- **MultiColumnContainer**: Explicitly handles multi-column layouts within a section, containing `Column` objects.

## 3. Data Flow

1.  **Ingestion**: `DoclingIngestor` (WSL side) converts source items into IR objects.
2.  **Mapping**: Docling's `TableItem` becomes an IR `Table`. `TextItem` becomes a `Paragraph` with `TextRun` elements.
3.  **Serializing**: The IR can be serialized to JSON (`lib/ir_serializer.py`) to be passed across the WSL-Windows bridge.
4.  **Reconstruction**: `HwpCompiler` (Windows side) parses the IR and executes OLE actions to rebuild the document in Hancom Office.
