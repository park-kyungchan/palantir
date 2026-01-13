# HWPX Programmatic Improvement Tasks

## Phase 4: HwpUnit Conversion Utilities
- [x] Create `lib/owpml/units.py`
- [x] Add unit tests (19 passed)

## Phase 1: Advanced Table Merging
- [x] Add `MergeCells` action
- [x] Implement `_create_table()` with cellSpan
- [x] Refine cell width calculation (Precision Tuning)

## Phase 5: Dependency & CI Fixes
- [x] Add `python-hwpx==1.9` to requirements.txt
- [x] Verify OCF compliance

## Phase 2: BorderFill ID Management
- [x] Create `lib/owpml/header_manager.py`

## Phase 3: BinData Image Pipeline
- [x] Create `lib/owpml/bindata_manager.py`

## Phase 6: Control Objects (Images & Shapes)
- [x] Implement `_insert_image` via hp:pic
- [x] Implement `_insert_textbox` via hp:rect

## Phase 7: Math/Equations
- [x] Verify `equation_converter.py` limits handling (Unit Test)
- [x] Implement `_insert_equation` (Remove linesegarray, use eqEdit)
- [x] Verify End-to-End Equation Insertion

## Phase 8: Styles & Formatting
- [x] Implement `HeaderManager.get_or_create_char_pr` (Size, Bold)
- [x] Implement `HeaderManager.get_or_create_para_pr` (Align, Spacing, Indent)
- [x] Wire `HwpxDocumentBuilder` to use dynamic Style IDs
- [x] Verify Text Layout (Align, Indent, Bold)

## Phase 9: Page Layout (PageSetup)
- [x] Update `SetPageSetup` model (Orientation, A4/Letter)
- [x] Implement `HwpxDocumentBuilder._update_page_setup`
- [x] Verify Page Setup (Margins, Orientation)

## Phase 10: Table Formatting (Borders & Fills)
- [ ] Update `SetCellBorder` model (Add `fill_color`)
- [ ] Implement `HeaderManager.get_or_create_border_fill` (Solid/Dash/None, Width, Color)
- [ ] Implement `MoveToCell` State Logic (Cursor Context)
- [ ] Update `_insert_text` to support Table Cell Context
- [ ] Verify Table Border/Fill (Manual Test)

