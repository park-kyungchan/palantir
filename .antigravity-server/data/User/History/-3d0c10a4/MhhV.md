# HWPX Implementation Walkthrough (Phases 9 - 12)

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
+
## Phase 12: Context-Aware Inline Controls
Standardized placement logic for all inline objects to ensure they respect the cursor context (e.g., insertion into table cells).

### Logic:
- **Universal Container Logic**: Updated `_insert_image`, `_insert_textbox`, and `_insert_equation` to apply the same `container = self._current_container if self._current_container is not None else self.section_elem` pattern.
- **Clean-up**: Removed stale/erroneous state-reset logic (`self._current_table = None` etc.) that was accidentally injected into control methods during previous refactoring attempts.
- **Verification**: `tests/manual_verify_controls.py` used a 2x2 table to verify:
    - **Cell (0,1)**: Embedded Image (`hp:pic`).
    - **Cell (1,0)**: Embedded TextBox (`hp:rect`).
    - **Cell (1,1)**: Embedded Equation (`hp:eqEdit`).
    Successfully confirmed all controls were parented by their respective `hp:tc` elements.

## Phase 13: Advanced Lists
Implemented support for hierarchical bulleted and numbered lists.

### Implementation:
- **Style Generation**: `HeaderManager.get_or_create_numbering` creates `<hh:numbering>` definitions with up to 7 levels.
- **State Activation**: `_set_numbering` tracks the current `numbering_id`.
- **Paragraph Linking**: `_insert_text` passes `numbering_id` to `get_or_create_para_pr`, which sets the `numberingIDRef` attribute on `<hh:paraPr>`.

## Phase 14: Validation & Cleanup
Final stabilization and regression remediation.

### Key Remediations:
- **Style Case-Sensitivity**: Removed `.upper()` from `SetAlign` to match `HeaderManager`'s Title Case expectations.
- **Defensive XML Creation**: Updated `SetPageSetup` to auto-create missing `<hp:margin>` elements in the skeleton.
- **"Truth Value" Fix**: Updated verification scripts to use `is not None` for Element comparison to avoid boolean traps with empty elements.
- **Final Sync**: Established the "Global Git Sync" pattern for workspace releases.

## Refactoring Lessons Learned
During Phase 10, several regressions occurred due to imprecise regex automation scripts:
1. **Regex Over-matching**: Searching for common state resets like `self._pending_column_break = False` matched multiple locations, injecting code into the wrong methods.
2. **"Zombie Code"**: Improperly bounded replacements left fragments of old docstrings at the end of methods.
3. **Initialization Errors**: Failure to initialize new `_current_*` state variables in `__init__` led to `AttributeError`.

**Remediation**: Reverted to manual patching for complex state logic and established a strict "verification first" protocol using manual test scripts for every architectural change.
