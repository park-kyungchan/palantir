# HWPX Native: OWPML & Spec Compliance (KS X 6101)

This document outlines the requirements and implementation details for generating native HWPX (XML) files that are 100% compatible with Hancom Office 2024.

## 1. Specification Compliance
All XML construction follows the **KS X 6101** national standard. We avoid "simulated" formatting and instead use native OWPML elements.

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
