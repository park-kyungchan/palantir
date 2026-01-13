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

### Phase 1: Table Complexity - Cell Merging
- **Goal**: Support `rowspan` and `colspan` in HWPX tables.
- **Actions**:
    - Update `lib/models.py` with `MergeCells` action.
    - Implement logical coordinate tracking in `document_builder.py` (avoiding "ghost cells").
    - Generate `<hp:cellSpan>` and `<hp:cellAddr>` elements.

### Phase 2: Style Management - BorderFill Registry
- **Goal**: Enable custom border widths, styles, and colors per cell.
- **Actions**:
    - Build a `HeaderManager` to register unique border styles in `header.xml`.
    - Map `HwpAction` styles to `borderFillIDRef`.

### Phase 3: Multimedia - BinData Pipeline
- **Goal**: Full support for embedded images.
- **Actions**:
    - Implement `BinDataManager` to manage the `BinData/` directory inside the HWPX ZIP.
    - Update manifest and header XMLs to reference binary metadata.

## 4. Quality Gate (Stage C)
- **Coverage**: Each phase requires dedicated unit tests (e.g., `test_table_merge.py`).
- **Integration**: Real-world verification using `sample.pdf` comparisons.
- **Compliance**: All generated XML must validate against HWPX schema definitions.
