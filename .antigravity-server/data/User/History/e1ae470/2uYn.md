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
- [ ] Verify `equation_converter.py` limits handling (Unit Test)
- [ ] Implement `_insert_equation` (Remove linesegarray, use eqEdit)
- [ ] Verify End-to-End Equation Insertion
