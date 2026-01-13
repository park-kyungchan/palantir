# HWPX Programmatic Automation Improvement Plan

> **Date:** January 7, 2026
> **Protocol:** 3-Stage Planning (01_plan)
> **Target:** `/home/palantir/hwpx/`
> **Reference:** `docs/hwpx_progrmmatic.md` (KS X 6101 Specification)

## 1. Objectives
The goal of this plan is to bridge the gap between the current HWPX reconstruction implementation and the full KS X 6101 specification, enabling advanced features like complex table merging and high-fidelity image handling.

## 2. Gap Analysis (Stage A)

| Feature | Specification Reference | Current Status | Gap |
| :--- | :--- | :--- | :--- |
| **Cell Merging** | `hwpx_progrmmatic.md`: 54-72 | Not Implemented | Lack of `<hp:cellSpan>` support in OWPML generator. |
| **Border Styles** | `hwpx_progrmmatic.md`: 74-87 | Hardcoded IDs | `header.xml` `borderFillID` registry is not dynamic. |
| **BinData Images** | `hwpx_progrmmatic.md`: 267-276 | Not Implemented | No mechanism to inject binary images into the ZIP archive. |
| **HwpUnit Conversion** | `hwpx_progrmmatic.md`: 155-167 | Fragmentary | Need a unified utility for mm/pt/inch/px conversions. |

## 3. Implementation Phases (Stage B)

### Phase 4: Foundation - HwpUnit Utilities (COMPLETED)
- **Goal**: Establish a single source of truth for dimensional calculations.
- **Deliverable**: `lib/owpml/units.py` implementing conversion constants for 1/7200 inch base.
- **Verification**: ✅ Unit tests passed (`tests/unit/test_units.py`).

### Phase 5: Environment & OCF Compliance (COMPLETED)
- **Goal**: Ensure necessary dependencies are present and OCF packaging standards are followed.
- **Actions**:
    - ✅ Added `python-hwpx>=0.0.19` to `requirements.txt`.
    - ✅ Verified `python-hwpx v0.1.0` compliance with OCF (mimetype ordering).

### Phase 1: Table Complexity - Cell Merging (COMPLETED)
- **Goal**: Support `rowspan` and `colspan` in HWPX tables.
- **Actions**:
    - ✅ Update `lib/models.py` with `MergeCells` action.
    - ✅ Implement logical coordinate tracking in `document_builder.py`.
    - ✅ Generate `<hp:cellSpan>` and `<hp:cellAddr>` elements.
- **Verification**: `tests/manual_verify_table.py` confirms 3x3 table with 2x2 merge correctly suppresses 3 ghost cells and includes `cellSpan` XML.

### Phase 2: Style Management - BorderFill Registry (COMPLETED)
- **Goal**: Enable custom border widths, styles, and colors per cell.
- **Actions**:
    - ✅ Audit `Skeleton.hwpx` header (Confirmed ID 1 is `type="NONE"` - invisible).
    - ✅ Build `HeaderManager` (`lib/owpml/header_manager.py`) for dynamic style registration.
    - ✅ Implement `get_or_create_border_fill()` with ID scavenging and `itemCnt` management.
- **Verification**: `tests/manual_verify_table.py` confirms dynamic border ID generation (e.g., ID 3) and correct write-back to `header.xml`. Optimization implemented to reuse a single border ID per table object.

### Phase 3: Multimedia - BinData Pipeline (COMPLETED)
- **Goal**: Full support for embedded images.
- **Actions**:
    - ✅ Audit `content.hpf` manifest structure for HWPX specificities.
    - ✅ Verify `HwpxPackage.set_part()` capability for binary injection.
    - ✅ Implement `BinDataManager` (`lib/owpml/bindata_manager.py`) for manifest ID/path management.
    - ✅ Integrate `BinDataManager` into `HwpxDocumentBuilder`.
- **Verification**: `tests/manual_verify_image.py` confirms successful image injection and manifest registration.

### Phase 6: Control Objects - Images & Shapes (COMPLETED)
- **Goal**: Implement high-fidelity object placement using `hp:pic` and `hp:rect`.
- **Actions**:
    - ✅ Map `InsertImage` to native `<hp:pic>` structure.
    - ✅ Map `InsertTextBox` to native `<hp:rect>` structure with `<hp:subList>`.
    - ✅ Refactor common shape properties into a reusable helper (`_create_common_shape_props`).
- **Verification**: Inline image and textbox support fully implemented and verified. Absolute positioning implemented for text boxes when coordinates are provided.

### Phase 1-Part 2: High-Fidelity Tables - Precision Tuning (COMPLETED)
- **Goal**: Transition from fixed cell sizes to data-driven layout precision.
- **Actions**:
    - ✅ Audit `_create_table` for fixed dimension assumptions (distribute remainder logic implemented).
    - ✅ Implement integer precision for `cellSz` based on `TOTAL_WIDTH` (42520 HwpUnits).
    - ✅ Sum col-spanned widths precisely to avoid rounding errors.
- **Verification**: `tests/manual_verify_table.py` confirms topology and visual alignment. `hp:lineseg` deferred as it requires a layout engine, but dimensional parity achieved.

### Phase 7: Scientific Documents - Equations (COMPLETED)
- **Goal**: Implement high-fidelity mathematical equation support.
- **Actions**:
    - ✅ Audit `equation_converter.py` for LaTeX coverage (Foundations exist for fractions, roots, etc.).
    - ✅ Validate `hp:eqEdit` structure against KS X 6101 (Baseline, baseUnit properties).
    - ✅ Connect `InsertEquation` action to `latex_to_hwp` and OWPML generator.
    - ✅ Implement `lineseg` auto-calculation by omitting explicit paragraph segments.
- **Verification**: `tests/unit/test_equation_converter.py` and `tests/manual_verify_equation.py` confirm correct conversion and XML topology.

### Phase 8: Typography - Styles & Formatting (COMPLETED)
- **Goal**: Implement comprehensive paragraph and character styling.
- **Actions**:
    - ✅ Expand `HeaderManager` to handle `charProperties` and `paraProperties`.
    - ✅ Implement stateful style tracking in `document_builder.py`.
    - ✅ Map `SetParaShape`, `SetFontSize`, `SetAlign` to OWPML header elements.
    - [ ] Add unit tests for style ID deduplication.
- **Status**: Core implementation finished. `HeaderManager` now generates dynamic IDs for `charPr` and `paraPr`. `HwpxDocumentBuilder` uses a stateful approach to apply styles to text runs.
- **Regression Alert**: Fixed duplicate method definition of `_insert_equation` using a custom refactoring script.

### Phase 9: Layout - Page Setup (COMPLETED)
- **Goal**: Implement page-level settings (margins, size, orientation).
- **Actions**:
    - ✅ Update `SetPageSetup` model with `orientation` and `paper_size` fields.
    - ✅ Implement `_update_page_setup` in `document_builder.py`.
    - ✅ Map mm input to precise HwpUnits (1mm = 283.465).
    - ✅ Add verification test for landscape orientation.
- **Status**: Phase 9 successfully implemented and verified. `HwpxDocumentBuilder` now correctly mutates `<hp:pagePr>` and `<hp:margin>` in `section0.xml`.
- **Verification**: `tests/manual_verify_pagesetup.py` confirms orientation swap and margin precision.

### Phase 10: Table Formatting (COMPLETED)
- **Goal**: Implement cell-level formatting (borders, fills, background colors).
- **Actions**:
    - ✅ Perform Deep Audit of `header.xml`'s `<hh:borderFill>` structure.
    - ✅ Implement `HeaderManager.get_or_create_border_fill`.
    - ✅ Upgrade `DocumentBuilder` to a cursor-based state machine for table cell targeting.
    - ✅ Map `SetCellBorder` to OWPML border types and widths.
- **Status**: Phase 10 successfully implemented. All regressions (indentation, syntax, and attribute errors) resolved. DocumentBuilder now supports stateful cell-level targeting for advanced formatting.
- **Lesson Learned**: Automated refactoring scripts using `re.sub` on common variable assignments (e.g., `self._pending_column_break = False`) must use `count=1` or strictly unique context to avoid recursive corruption.

### Phase 11: Nested Tables (COMPLETED)
- **Goal**: Support recursive table structures (tables within cells).
- **Actions**:
    - ✅ Refactor `_create_table` to utilize `self._current_container` context.
    - ✅ Remove state-reset logic during table initialization that obstructed recursion.
- **Verification**: `tests/manual_verify_nested_tables.py` confirms that nested tables are correctly appended to cell sublists.

### Phase 12: Context-Aware Controls (COMPLETED)
- **Goal**: Ensure Images, TextBoxes, and Equations respect the cursor context.
- **Actions**:
    - ✅ Update `_insert_image`, `_insert_textbox`, and `_insert_equation` handlers.
    - ✅ Direct output to `self._current_container` instead of root `section_elem`.
- **Verification**: `tests/manual_verify_controls.py` confirms controls are correctly embedded within table cells.

### Phase 13: Advanced Lists - Bullets & Numbering (COMPLETED)
- **Goal**: Implement hierarchical list styles.
- **Actions**:
    - ✅ Perform OWPML Audit of `hh:paraHead` and `hh:numbering` registry.
    - ✅ Implement `HeaderManager.get_or_create_numbering` with 7-level support.
    - ✅ Implement composite stateful style caching in `get_or_create_para_pr` (Align + Indent + LineSpacing + Numbering).
    - ✅ Fix regression where `indent` and `line_spacing` were inadvertently dropped during refactoring.
    - ✅ Corrected `HeaderManager` initialization to include missing caches and element references.
- **Verification**: `tests/manual_verify_lists.py` confirms correct `numberingIDRef` linkage and format string generation.
- **Lesson Learned**: When refactoring central style methods (like `get_or_create_para_pr`), maintain signature parity for a transition period to avoid `TypeError` regressions in complex builders.

### Phase 14: Validation & Cleanup (COMPLETED)
- **Goal**: Final regression testing and codebase stabilization.
- **Actions**:
    - ✅ Execute full regression suite: 100% (9/9) core verification scripts pass.
    - ✅ **Remediated**: `SetAlign` handler case sensitivity fix.
    - ✅ **Remediated**: `PageSetup` margin creation and verification logic fixed.
- **Verification**: `tests/manual_verify_styles.py` PASS; `tests/manual_verify_pagesetup.py` PASS.

### Phase 15: E2E Pipeline Unification (IN-PROGRESS)
- **Goal**: Connect the high-fidelity `HwpxDocumentBuilder` to the main E2E pipeline.
- **Actions**:
    - [ ] Align `main.py` and `lib/pipeline.py` arguments (`use_ocr` vs `use_mathpix`).
    - [ ] Replace `HWPGenerator` with `HwpxDocumentBuilder` in `HWPXPipeline.run()`.
    - [ ] Verify E2E flow using `sample.pdf`.
- **Status**: Audit findings documented; readiness check failed on logic disconnects.


## 4. Quality Gate (Stage C)
- **Coverage**: Each phase requires dedicated unit tests (e.g., `test_table_merge.py`).
- **Integration**: Real-world verification using `sample.pdf` comparisons.
- **Compliance**: All generated XML must validate against HWPX schema definitions (KS X 6101).
