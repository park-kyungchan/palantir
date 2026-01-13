# HWPX Implementation Walkthrough (Phases 9 - 11)

## Phase 9: Page Layout (PageSetup)
Implemented `SetPageSetup` feature to control physical document dimensions and orientation.

### Key Logic:
- **HwpUnit Conversions**: Utilized the `283.465` multiplier to convert millimeters (mm) to HWP Units.
- **Orientation Switching**: Implemented landscape support by swapping width and height attributes in the `<hp:pagePr>` element within `section0.xml`.
- **Margin Precision**: Updated `<hp:margin>` attributes for top, bottom, left, right, header, footer, and gutter.

## Phase 10: Table Formatting (Borders & Fills)
Transformed `HwpxDocumentBuilder` into a **Cursor-Based State Machine** to allow per-cell styling.

### Architectural Shift:
- **State Tracking**: Added `_current_table`, `_current_cell`, and `_current_container` to the builder.
- **Contextual Targeting**:
    - `MoveToCell(row, col)`: Navigates the XML tree of the active table to set the "active cell" context.
    - `InsertText`: Re-routed to append to `self._current_container` instead of always the document root.
- **Dynamic Style Registration**:
    - `HeaderManager.get_or_create_border_fill`: Dynamically creates `<hh:borderFill>` entries.
    - **Namespace Split**: Borders use the `hh` (Head) namespace, while background fills (`fillBrush`) use the `hc` (Core) namespace.

## Phase 11: Nested Tables
Enabled recursion by allowing tables to be created inside other table cells.

### Logic:
- **_create_table Update**: Modified to use `self._current_container` as the insertion point.
- **Flow**: `CreateTable (Outer)` -> `MoveToCell(0,0)` -> `CreateTable (Inner)`.
- **Verification**: `tests/manual_verify_nested_tables.py` confirmed that the inner table is correctly parented by the outer table's cell.

## Refactoring Lessons Learned
During Phase 10, several regressions occurred due to imprecise regex automation scripts:
1. **Regex Over-matching**: Searching for common state resets like `self._pending_column_break = False` matched multiple locations, injecting code into the wrong methods.
2. **"Zombie Code"**: Improperly bounded replacements left fragments of old docstrings at the end of methods.
3. **Initialization Errors**: Failure to initialize new `_current_*` state variables in `__init__` led to `AttributeError`.

**Remediation**: Reverted to manual patching for complex state logic and established a strict "verification first" protocol using manual test scripts for every architectural change.
