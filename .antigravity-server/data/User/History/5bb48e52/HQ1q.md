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

## 4. Quality Gate (Stage C)
- **Coverage**: Each phase requires dedicated unit tests (e.g., `test_table_merge.py`).
- **Integration**: Real-world verification using `sample.pdf` comparisons.
- **Compliance**: All generated XML must validate against HWPX schema definitions (KS X 6101).
