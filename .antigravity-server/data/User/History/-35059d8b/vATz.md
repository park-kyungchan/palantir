# HWPX Programmatic Implementation: Master Guide & Improvement Plan

This document serves as the central reference for the HWPX (OWPML) reconstruction engine, detailing the architectural standards, implementation phases, and current project status.

## 1. Dimensional Standard & Precision (KS X 6101)
HWPX (OWPML) uses **HwpUnit** (1/7200 inch) as its internal coordinate system. All attribute values in the XML must be integers.

### 1.1 Precision Calculation
- **Base Conversion**: 1 mm ≈ 283.46 HwpUnits; 1 pt = 100 HwpUnits.
- **Remainder Distribution**: When dividing fixed container widths, the base width is `total // count`. Any remainder `total % count` is added to the final element to ensure 100% geometric conformance.
- **Spanned Cell Widths**: The width for a merged cell (`cellSpan`) is calculated by summing the precise widths of the spanned columns.

## 2. Document Reconstruction Architecture

### 2.1 Shared Resource Management (HeaderManager)
To maintain efficient document structures, styles and border fills are managed via a Request-and-Reuse pattern.
- **ID Scavenging**: Scans existing `header.xml` content for the highest `id` before registering new styles.
- **Deduplication**: Composite keys (e.g., `{align}_{indent}_{spacing}_{numberingID}`) ensure unique `paraPr` entries are created only when effective properties change.

### 2.2 Stateful Document Assembly (DocumentBuilder)
The `HwpxDocumentBuilder` operates as a cursor-based state machine.
- **Context Tracking**: Monitors the `_current_table`, `_current_cell`, and `_current_container` to enable nested structures (Tables within Tables).
- **Style State**: Tracks active typography and layout settings (Size, Bold, Align) across multiple `InsertText` actions.

## 3. Implementation Lifecycle (Phases 1-15)

### Foundation (Phases 4, 5, 9)
- **HwpUnit Utilities**: `lib/owpml/units.py` established conversion constants.
- **OCF Compliance**: Verification of ZIP packaging and `mimetype` uncompressed storage.
- **Page Layout**: Implementation of `<hp:pagePr>` for orientation, size, and margins.

### Core Structural Elements (Phases 1, 2, 10, 11)
- **Cell Merging**: Support for `<hp:cellSpan>` with logical coordinate tracking (`cellAddr`) and ghost cell suppression.
- **Dynamic Borders & Fills**: Dynamic registration of `hh:borderFill` in the header for per-cell formatting.
- **Nested Tables**: Recursive table structures using container context injection.

### Multimedia & Specialized Controls (Phases 3, 6, 7, 12, 13)
- **BinData Pipeline**: Mechanism for injecting binary images into the ZIP archive and registering them in the manifest.
- **Controls**: High-fidelity placement of Images (`hp:pic`), TextBoxes (`hp:rect`), and Equations (`hp:eqEdit`).
- **Equations**: LaTeX transpilation to HWP script and auto-layout calculation.
- **Advanced Lists**: 7-level hierarchical numbering and bullets with OWPML linkage.

### E2E Unification (Phases 14, 15)
- **Regression Suite**: 100% pass rate on core verification scripts.
- **Pipeline Integration**: Re-wiring of `main.py` and `lib/pipeline.py` to use `HwpxDocumentBuilder` as the primary engine.
- **Pilot Verification**: Success against `sample.pdf` generating valid OWPML packages.

## 4. Key Implementation Patterns

### 4.1 Table Merge Pattern
1. **Lookahead**: Handler scans subsequent `MergeCells` actions.
2. **Merge Map**: `(row, col) -> (row_span, col_span)`.
3. **Ghost Suppression**: Skip creating `<hp:tc>` for covered logical coordinates.

### 4.2 Control Object Pattern
Images, TextBoxes, and Equations share common shape properties:
- **`hp:sz`**: Absolute dimensions in HwpUnits.
- **`hp:pos`**: Inline (`treatAsChar="1"`) vs Floating positioning.

## 5. Stability & Quality Gate
- **Geometry**: Sum of `cellSz` must match table width.
- **ID Integrity**: All `Ref` attributes must point to valid `header.xml` entries.
- **Atomic Actions**: 20+ `HwpAction` types programmatically verified across the pipeline.
