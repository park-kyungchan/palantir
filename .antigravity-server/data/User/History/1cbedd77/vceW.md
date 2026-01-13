# HWPX Programmatic Implementation Master Guide (Phases 1-10)

## 1. Dimensional Standard & Precision
HWPX (OWPML) uses **HwpUnit** (1/7200 inch) as its internal coordinate system. All attribute values in the XML must be integers.

### 1.1 Precision Calculation
- **Base Conversion**: 1 mm ≈ 283.46 HwpUnits; 1 pt = 100 HwpUnits.
- **Remainder Distribution Strategy**: When dividing a fixed container width (e.g., 42520 HwpUnits for A4 content) among columns, the base width is `total // count`. Any remainder `total % count` MUST be added to the final column/element to ensure 100% geometric conformance.
- **Spanned Cell Widths**: The width for a merged cell (`cellSpan`) must be calculated by summing the precise widths of the spanned columns: `width = sum(col_widths[origin : origin + col_span])`.

## 2. Shared Resource Management (HeaderManager)
To prevent "Header Bloat" and maintain efficient document structures, styles and border fills are managed via a Request-and-Reuse pattern.

- **ID Scavenging**: The `HeaderManager` scans existing `header.xml` content for the highest `id` and `itemCnt` before registering new styles.
- **Reuse**: A single `borderFillIDRef` (e.g., a "SOLID" border) is generated once per high-level object (like a Table) and shared across all constituent elements (cells).

## 3. Table Structure & Merging
Advanced tables utilize logical grid coordinates.

### 3.1 Logical vs. Physical
- **Logical Addressing**: Every cell (`hp:tc`) must declare its `hp:cellAddr` (`colAddr`, `rowAddr`) based on the underlying grid.
- **Span Declaration**: `hp:cellSpan` defines the coverage (`colSpan`, `rowSpan`) at the origin cell.
- **Ghost Cell Suppression**: Cells covered by a span (excluding the origin) MUST be omitted from the XML structure. Failure to suppress these results in document corruption or layout overflows.

## 4. Multimedia & Control Objects
### 4.1 BinData Pipeline
Embedded binaries (Images) are handled via:
1. **Manifest Registration**: Entries in `Contents/content.hpf` with `isEmbeded="1"`.
2. **ZIP Injection**: Physical insertion into `BinData/` directory via `HwpxPackage.set_part()`.
3. **Reference**: `hp:pic` refers to the `binaryItemIDRef` defined in the manifest.

### 4.2 Unified Shape Logic
`hp:pic` (Images) and `hp:rect` (TextBoxes) share a common foundation created by the `_create_common_shape_props` helper:
- **`hp:sz`**: Absolute dimensions in HwpUnits.
- **`hp:pos`**: Handles **Inline** (`treatAsChar="1"`) vs **Floating** (`vertRelTo="PAPER"`) positioning.
- **`hp:outMargin`**: Standardized margins.

## 5. Scientific Equations (Phase 7)
Equations are embedded as `hp:eqEdit` controls.

### 5.1 LaTeX to HWP Script
Conversion requires mapping LaTeX commands to HWP Equation Script (e.g., `\frac` → `OVER`, `\sum` → `SUM`).
- **Nesting**: Recursive regex patterns handle nested structures (fractions within square roots, etc.).
- **Limits**: HWP Script natively supports `_` and `^` for subscripts and superscripts; these are preserved during conversion.

### 5.2 Layout & Auto-Calculation
- **Line Segments**: Research confirms that `linesegarray` should be **removed** for paragraphs containing equations. This forces the HWPX viewer to perform layout auto-calculation, preventing rendering errors caused by fixed placeholder segments.

## 6. Typography & Styles (Phase 8)
HWPX uses an ID-based reference system for efficiency. Styles are registered in `header.xml` and referenced by numerical IDs.

### 6.1 Character Styling (`hh:charPr`)
- **Unit Scale**: Font height is stored in 0.01pt increments (e.g., `1000` = 10pt).
- **Attributes**: Supports `bold`, `textColor`, and `fontRef` (font face mapping).

### 6.2 Paragraph Styling (`hh:paraPr`)
- **Alignment**: Standard OWPML horizontal values: `LEFT`, `CENTER`, `RIGHT`, `JUSTIFY`, `DISTRIBUTE`.
- **Indentation**: First-line indent is measured in HwUnits (1pt = 100 HwUnits).
- **Line Spacing**: Defined as `PERCENT` (e.g., `160%`) or `FIXED` units.

### 6.3 Stateful Implementation
The generation pipeline implements a "Style State Machine":
1. **State Tracking**: The `HwpxDocumentBuilder` tracks the current active style (Size, Bold, Align, Margin).
2. **Dynamic Registration**: For every `InsertText` action, the builder requests unique IDs from `HeaderManager`.
3. **ID Injection**: Character and Paragraph IDs are injected into `<hp:run charPrIDRef="...">` and `<hp:p paraPrIDRef="...">`.

## 7. Page Layout & Section Properties (Phase 9)
Global document layout is controlled via `<hp:secPr>`.

### 7.1 Page Dimensions
- **Orientation**: Managed by swapping `width` and `height` in `<hp:pagePr>` and setting the `landscape` attribute (`WIDELY` for landscape).
- **Paper Size**: A4 is the standard base (210mm x 297mm).

### 7.2 Margins
- **Mapping**: `<hp:margin>` handles `top`, `bottom`, `left`, `right`, `header`, `footer`, and `gutter`.
- **Unit Scale**: Conversion from millimeters to HwpUnits (1mm ≈ 283.46).

## 8. Table Formatting & Cell Styles (Phase 10)
Advanced table layout relies on per-cell formatting.

### 8.1 Border & Fill Registries
- **Mechanism**: Cell borders and backgrounds are defined in `header.xml`'s `<hh:borderFill>` elements and referenced by `borderFillIDRef` in `<hp:tc>`.
- **Properties**: Supports Slash/Backslash, 4-way borders, and WinBrush fills.
- **Namespaces**: Border properties reside in the `head` (hh) namespace, while background fills (`fillBrush`) reside in the `core` (hc) namespace.

### 8.2 State Machine Cursor
- **Concept**: The builder tracks the "Active Cell" within a table structure, allowing subsequent actions to modify the formatting of the targeted cell before moving the cursor.
- **State Variables**: 
    - `self._current_table`: References the active `<hp:tbl>`.
    - `self._current_cell`: References the active `<hp:tc>`.
    - `self._current_container`: Targets either the document section or a specific cell for content insertion.

## 9. Verification Patterns
- **Geometry**: Sum of `cellSz` widths in a row must exactly match the table width.
- **OCF Packaging**: `mimetype` must be the first file in the ZIP and stored without compression.
- **ID Integrity**: All `charPrIDRef`, `paraPrIDRef`, and `borderFillIDRef` must point to valid entries in `header.xml`.
- **Style Persistence**: Styles applied via `SetParaShape` or `SetAlign` must persist across multiple `InsertText` actions until explicitly modified.
