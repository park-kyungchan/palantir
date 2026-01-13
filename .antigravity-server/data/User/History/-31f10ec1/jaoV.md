# HWPX Native: OWPML & Spec Compliance (KS X 6101)

This document outlines the requirements and implementation details for generating native HWPX (XML) files that are 100% compatible with Hancom Office 2024.

## 1. Specification Compliance
All XML construction follows the **KS X 6101:2024** (revised 2024-10-30) national standard. We avoid "simulated" formatting and instead use native OWPML elements. This version emphasizes **data interoperability** and **AI compatibility**.

For a deep dive into the 2024 changes and Agentic RAG implementation, see: `ks_x_6101_2024_research.md`.

### 1.1 HwpUnit Conversion Formulas
**1 HwpUnit = 1/7200 inch** (approx. 0.00353mm).

| Conversion | Formula | Example |
|---|---|---|
| HwpUnit → pt | `pt = hwpunit / 100` | 1000 HwpUnit = 10pt |
| HwpUnit → mm | `mm = hwpunit / 283.46` | 283 HwpUnit ≈ 1mm |
| pt → HwpUnit | `hwpunit = pt * 100` | 12pt = 1200 HwpUnit |
| mm → HwpUnit | `hwpunit = mm * 283.46` | 25.4mm = 7200 HwpUnit |

## 2. Template-Based Reconstruction (TBR)
Due to the OWPML header's extreme complexity (IDs for fonts, styles, borders), the engine uses a "Golden Template".
- **Source**: `Skeleton.hwpx` (official base).
- **Process**: Copy all ZIP parts except `Contents/section0.xml`.
- **Dynamic Content**: Inject generated paragraph and run data into `section0.xml`.

## 3. Control Elements (`hp:ctrl`)
Critical layout and mathematical objects are **Controls**, not attributes.
- **Columns (`hp:colPr`)**: Must be inserted after `<hp:secPr>` in the first run of a section. Use attributes `colCount`, `type="NEWSPAPER"`, `sameSz="1"`, and `sameGap`.
- **Equations (`hp:eqEdit`)**: Requires transpilation from LaTeX -> HWP Script -> `<hp:eqEdit>`.
- **Tables (`hp:tbl`)**: Hierarchical structure with `<hp:tr>` (rows) and `<hp:tc>` (cells).
- **Images (`hp:pic`)**: References `BinData/` items via `binaryItemIDRef`. Use `<hp:originalSize>` and `<hp:curSize>` for dimensions.
- **Shapes (`hp:rect`, `hp:ellipse`, etc.)**: Drawing objects with absolute positioning in HwpUnit.

### 3.1 Table Merge Logic (KS X 6101)
Cell merging is handled by the `<hp:cellSpan>` child element within `<hp:tc>`, not by attributes on the cell itself.

```xml
<hp:tc>
  <hp:cellAddr colAddr="0" rowAddr="0"/>
  <hp:cellSpan colSpan="2" rowSpan="3"/>
</hp:tc>
```

**Key Requirement**: HWPX does not allow "ghost cells" in merged regions. If cells are merged, the number of `<hp:tc>` elements in the row decreases. Logical coordinates must be tracked via `cellAddr`.

### 3.2 Implementation Pattern (DocumentBuilder)
To implement complex tables with merges, the following pattern is used in `_create_table`:
1. **Lookahead Action Search**: The builder iterates through the pending action list starting from the `CreateTable` index to find subsequent `MergeCells` actions before the next table or breaking action.
2. **Merge Map Construction**: Creates a map `(row, col) -> (row_span, col_span)` for the top-left cell of every merge.
3. **Ghost Cell Tracking**: A `covered_cells` set tracks all logical `(r, c)` coordinates that should be skipped because they are within a span of a previous cell.
4. **OWPML Generation**:
    - Iterate `r` in `rows`, `c` in `cols`.
    - If `(r, c)` in `covered_cells`, skip creating `<hp:tc>`.
    - Else, create `<hp:tc>`, calculate `cellSz` (width * colSpan, height * rowSpan), and add `<hp:cellAddr>` and `<hp:cellSpan>`.
    - Add all cells covered by the current span to `covered_cells`.
5. **Sub-namespace Reference**: Uses `_hp` helper (e.g. `http://www.hancom.co.kr/hwpml/2011/paragraph`) for all table elements.

### 3.4 Numbering & Bullets (`hh:numbering`)
List structures rely on the linkage between `hp:paraPr` in the section and `hh:numbering` in the header.

- **Linkage**: The `hp:paraPr` element uses the `numberingIDRef` attribute to point to a specific `<hh:numbering>` entry.
- **Header Structure**: `<hh:numbering>` contains level definitions (`<hh:paraHead>`) for each indentation depth (1-8+).
- **Format String**: The character format is stored as **text content** within `<hh:paraHead>`.
  - Numbered: uses `^n` placeholders (e.g., `^1.` for level 1).
  - Bullets: uses fixed symbols (e.g., `•`).
- **Attributes**: `numFormat` (e.g. `DIGIT`, `HANGUL_SYLLABLE`, `CIRCLED_DIGIT`) and `start` (level-specific starting value).

### 3.3 Builder Logic: Context Injection
To support lookahead features like `MergeCells`, the `HwpxDocumentBuilder._process_action` signature was updated:
- **Change**: `_process_action(self, action: HwpAction, actions: List[HwpAction])`.
- **Reason**: Allows individual handlers (like `_create_table`) to scan subsequent actions for context-related modifiers (Merges, Borders).

## 4. Header Management (Phase 2 & TBR)
The `Contents/header.xml` file is the central registry for IDs. Every `styleIDRef`, `paraPrIDRef`, and `borderFillIDRef` MUST exist in `header.xml`.

### 4.1 Skeleton.hwpx ID Audit
The "Golden Template" (`Skeleton.hwpx`) contains the following baseline registry:
- **`hh:borderFills`**: 2 items.
    - **ID 1**: Standard borders (type: **NONE**, width: **0.1mm**, color: **#000000**). *Note: Tables using ID 1 are invisible.*
    - **ID 2**: Borders with `fillBrush` (background colors).
- **`hh:charProperties`**: 7 items.
- **`hh:styles`**: 23 items.

**Rule**: Any new custom styles (e.g., specific cell borders) must increment the `itemCnt` and use a new unique `id` in `header.xml` to avoid document corruption.

### 4.2 HeaderManager Pattern (lib/owpml/header_manager.py)
To handle dynamic styling, the `HeaderManager` implements the following lifecycle:
1. **ID Scavenging**: On initialization, scans the existing `header.xml` for `hh:borderFills/hh:borderFill/@id` to determine the current `_border_max_id`.
2. **Registration**: `get_or_create_border_fill(type, width, color)` checks for trivial matches (e.g., `NONE` maps to ID 1) or generates a new ID.
3. **Registry Update**:
    - Creates a new `hh:borderFill` element with the next ID.
    - Appends 4 side borders (left, right, top, bottom) and a diagonal.
    - Increments the `itemCnt` attribute of the parent `<hh:borderFills>` element.
4. **Persistence**: The modified `header_elem` is written back to the HWPX package before saving.

## 5. Packaging and OCF Compliance
HWPX files must strictly follow Open Container Format (OCF) standards:
1. **mimetype**: Must be the **first file** in the ZIP archive, **uncompressed (Stored)**, and contain only `application/hwp+zip`.
2. **Mandatory Files**: `version.xml`, `Contents/content.hpf`, `Contents/header.xml`, `Contents/section0.xml`, `META-INF/container.xml`.
3. **OPF Spine**: The `content.hpf` spine defines the reading order of sections.

## 5. Tools and Libraries
- **python-hwpx**: Primary library for cross-platform programmatic control (no HWP installation required).
- **HwpUnit Utilities**: Centralized in `lib/owpml/units.py` for precision layout.

## 6. Stability Checklist
- **Paragraph IDs**: Every `<hp:p>` should have `paraPrIDRef` and optionally `styleIDRef`.
- **Lineseg**: Every paragraph must have a skeletal `<hp:linesegarray>` for renderer stability.
- **Namespace Consistency**: Always use standard OWPML 2011/2016 URIs.

## 7. External Ecosystem & Knowledge Resources (Jan 2026 Audit)
A deep audit for additional KS X 6101 materials identified the following external references and open-source implementations:

### 7.1 Key Document Standards & Specifications
- **LibreOffice Korean Team (KS X 6101)**: PDF presentation by DaeHyun Sung. Detailed insights into [OWPML document structure](https://conf.libreoffice.jp/slides/DaeHyun%20Sung_Korean%20Language.pdf) and character compatibility.
- **KS X 6101 (KS INFO)**: The official South Korean standard registry.

### 7.2 Notable GitHub Implementations
- **hwpx-owpml-model (hancom-io/hwpx-owpml-model)**: The official Hancom OWPML filter model (C++). Provides the definitive reference for OOXML-based OWPML structure.
- **pyhwp (mete0r/pyhwp)**: The most comprehensive and established Python library for parsing HWP v5 files.
- **hwpxParser (Wonsang222/hwpxParser)**: Active repository for HWPX parsing and structure analysis.
- **hwpxlib (neolord0/hwpxlib)**: A comprehensive C#-based library for HWPX manipulation (useful for cross-referencing attribute schemas).
- **hangle-parser (Joonmo-Ahn/hangle-parser)**: Recent (late 2025/early 2026) implementation focused on extracting layout and bounding box information from HWP/HWPX.
- **hwp-parser (hione0413/hwp-parser)**: Python-based parser for text, tables, and images.
- **pypandoc-hwpx (Arunpandi77/pypandoc-hwpx)**: A utility for converting Word, Markdown, and HTML to HWPX.

### 7.3 Strategic Utility
These resources serve as a secondary validation layer for our `HwpxDocumentBuilder`. Specifically, the official Hancom model (`hwpx-owpml-model`) serves as the ground truth for schema validation, while the coordinate and bounding box logic in `hangle-parser` provides a benchmark for our SVDOM (Digital Twin) layout analysis.
---

## 8. Technical Research Findings (Hancom C++ Model Audit)

### 8.1 Footnote & Endnote Structure
Audit of `SectionDefinitionType.h` and OWPML implementation in `Skeleton.hwpx` identified:
- **Primary Tag**: `<hp:footNote>` and `<hp:endNote>` wrapped in `<hp:ctrl>`.
- **Properties Container**: Properties like layout, separator lines, and numbering format are defined within `<hp:footNotePr>` and `<hp:endNotePr>` inside `<hp:secPr>`.
- **Nesting**: Footnotes must be contained within a paragraph run (`hp:run`) under a control element (`hp:ctrl`).
- **Content**: The note content resides within a `<hp:subList>` which can contain one or more paragraphs (`hp:p`).

**Implementation Pattern**:
```xml
<hp:p>
  <hp:run>
    <hp:ctrl>
      <hp:footNote id="unique_id">
        <hp:subList lineWrap="BREAK" vertAlign="BASELINE" ...>
          <hp:p paraPrIDRef="0" ...>
            <hp:run><hp:t>Footnote Text</hp:t></hp:run>
          </hp:p>
        </hp:subList>
      </hp:footNote>
    </hp:ctrl>
  </hp:run>
</hp:p>
```

### 8.2 Equation Object (`hp:eqEdit`)
- **Naming Discrepancy**: While the OWPML schema uses `eqEdit`, the Hancom C++ repository uses hierarchical class naming that abstracts the equation script type.
- **Transpilation Ground Truth**: The `hp:eqEdit` element remains the target for HWP script-based math rendering.

### 8.3 Control Hierarchy
- **`hp:ctrl` Base Class**: Comprehensive mapping of control attributes (size, position, wrapping) is found in `AbstractButtonObjectType.h` and `AbstractDrawingObjectType.h`.
- **Object Context**: High-fidelity controls must always reside within a paragraph run (`hp:run`) to ensure standard HWP layout computation.

---

## 9. Official Specification Availability (Hancom 2024 Audit)

As of January 2026, the status of official OWPML documentation is as follows:
- **Public/Open**: HWP 5.0 Binary Specification (2010), KS X 6101:2011 (Standard structure).
- **Restricted/Private**: The specific internal HWPX/OWPML schema for Hancom Office 2024 is **not publicly released** as a developer guide.
- **Reference Strategy**: We rely on **KS X 6101:2011** as the baseline, supplemented by the actual implementation in `Skeleton.hwpx` and the official SDK filter models (`hwpx-owpml-model`).

## 10. Ontology Design Principle: Hybrid Reconstruction

The OWPML generation logic in this pipeline follows a **Hybrid Strategy**:
1. **Direct Extraction (High Faith)**: Tags and properties (e.g., `<hp:footNotePr>`, `<hp:p>`) are extracted directly from `Skeleton.hwpx` or verified via standard OWPML parsers (`python-hwpx`).
2. **Structural Inference (Synthesized)**: Complex nesting structures (e.g., `<hp:subList>` internal layouts) are synthesized by cross-referencing GitHub research (`hwpxParser`, `hwpx-owpml-model`) and observing the behavior of the Hancom Word renderer.
3. **Black-box Verification**: All synthesized structures are validated by processing them through the pipeline and opening the resulting `.hwpx` in Hancom Office 2024 to ensure visual fidelity.
## 11. HWPX Action Inventory (Ontology v1.6)

These actions serve as the "Ontology" that the `Compiler` generates and the `HwpxDocumentBuilder` consumes.

### 11.1 Text & Formatting Actions
- `InsertText`: Standard text insertion.
- `InsertCodeBlock`: Code block with optional language.
- `InsertCaption`: Figure/Table caption.
- `SetFontSize`: Set font size in pt.
- `SetFontBold`: Toggle bold property.
- `SetAlign`: Paragraph alignment (Left, Center, Right, Justify).
- `SetLetterSpacing`: Ja-gan percentage (-50 to 50).
- `SetLineSpacing`: Jul-gan percentage (e.g., 160).
- `SetParaShape`: Margins, indents, and line spacing.

### 11.2 Table & Grid Actions
- `CreateTable`: Initialize table structure (rows, cols, width/height type).
- `MoveToCell`: Move cursor to cell (0-based row/col).
- `SetCellBorder`: Set border/fill for current cell.
- `MergeCells`: Merge block of cells (row_span, col_span).

### 11.3 Layout & Section Actions
- `SetPageSetup`: Paper size, orientation, and margins.
- `MultiColumn`: Column layout (count, gap).
- `BreakColumn` / `BreakSection` / `BreakPara`: Structural breaks.
- `SetNumbering`: List/Bullet style (Number, Bullet).

### 11.4 Object & Media Actions
- `InsertImage`: Insert picture (char-treated).
- `InsertTextBox`: Floating or inline text box (x, y, width, height).
- `InsertEquation`: Math formula (LaTeX/EQ transpilation).
- `CreateBorderBox`: Wrapped border container.
- `InsertFootnote` / `InsertEndnote`: Document annotations.

---

## 12. Native Menu Control Mapping (Jan 2026 Verification)

As verified during the January 2026 implementation phase, the pipeline provides programmatic control over the following standard Hancom Office menu features via native OWPML generation:

| Hancom Menu Feature | HwpAction Class | OWPML implementation | Verification Target |
|:---:|:---:|:---:|:---:|
| **Table** | `CreateTable`, `MoveToCell`, `MergeCells` | `<hp:tbl>`, `<hp:tc>`, `<hp:cellSpan>` | `output_table_test.hwpx` |
| **Cell Border/Fill** | `SetCellBorder` | `<hh:borderFill>` Registry | `output_table_formatting.hwpx` |
| **Equation Editor** | `InsertEquation` | `<hp:eqEdit>`, `<hp:script>` | `output_equation_test.hwpx` |
| **Insert Picture** | `InsertImage` | `<hp:pic>`, `BinData/` management | `output_image_test.hwpx` |
| **Text Box** | `InsertTextBox` | `<hp:rect>`, `<hp:subList>` | `output_textbox_test.hwpx` |
| **Column Settings** | `MultiColumn`, `BreakColumn` | Section Properties (`<hp:colPr>`) | `output_pilot.hwpx` |
| **Footnote/Endnote** | `InsertFootnote`, `InsertEndnote` | `<hp:footNote>`, `<hp:subList>` | `output_footnotes_test.hwpx` |
| **Page Setup** | `SetPageSetup` | `<hp:pagePr>`, `<hp:margin>` | `output_pagesetup_test.hwpx` |
| **Character Shape** | `SetFontSize`, `SetFontBold` | `<hh:charPr>` Registry | `output_styles_test.hwpx` |
| **Paragraph Shape** | `SetParaShape`, `SetAlign` | `<hh:paraPr>` Registry | `output_styles_test.hwpx` |
| **Bullets & Numbering** | `SetNumbering` | `<hh:numbering>` Registry | `output_lists.hwpx` |

---

## 14. Quick Start: Programmatic Table Generation

The following Python snippet creates a standard 3x3 table with sample data using the `HwpxDocumentBuilder`.

```python
from lib.models import CreateTable, MoveToCell, InsertText
from lib.owpml.document_builder import HwpxDocumentBuilder

# 1. Define actions for a 3x3 table
actions = [
    CreateTable(rows=3, cols=3),
    MoveToCell(row=0, col=0), InsertText(text='A1'),
    MoveToCell(row=0, col=1), InsertText(text='B1'),
    MoveToCell(row=0, col=2), InsertText(text='C1'),
    MoveToCell(row=1, col=0), InsertText(text='A2'),
    MoveToCell(row=1, col=1), InsertText(text='B2'),
    MoveToCell(row=1, col=2), InsertText(text='C2'),
    MoveToCell(row=2, col=0), InsertText(text='A3'),
    MoveToCell(row=2, col=1), InsertText(text='B3'),
    MoveToCell(row=2, col=2), InsertText(text='C3'),
]

# 2. Build and save the HWPX file
builder = HwpxDocumentBuilder()
builder.build(actions, 'sample_3x3_table.hwpx')
# Verified output: sample_3x3_table.hwpx (7.6KB, Valid OWPML)
```

## 15. Package Normalization Details (`lib/owpml/package_normalizer.py`)

To ensure that generated `.hwpx` files are not just XML-compliant, but also structurally valid according to the Hancom Office 2024 ZIP container requirements, the pipeline triggers `normalize_hwpx_package` during the save phase.

### 15.1 Critical Entry Ordering
HWPX/OCF requires the `mimetype` file to be the **first** entry in the ZIP archive, and it MUST be stored without compression (`ZIP_STORED`).
- **Priority**: `mimetype` (Index 0)
- **Secondary**: `version.xml`, `settings.xml`
- **Manifest Integrity**: Ensures `META-INF/manifest.xml` correctly references `Contents/header.xml`, `Contents/section0.xml`, etc.

### 15.2 Empty Directory Suppression
Standard HWPX filters sometimes fail if empty directories (like `BinData/` when no images are present) are declared but contain no files. The normalizer ensures structural cleanliness.

---
*Reference: Defined in `/home/palantir/hwpx/lib/models.py` and implemented in `lib/owpml/document_builder.py`.*
