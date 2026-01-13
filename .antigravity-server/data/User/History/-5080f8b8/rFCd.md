# Table Formatting Logic (Phase 10)

## 1. Overview
Phase 10 focuses on extending table capabilities from structural creation to visual formatting, specifically cell borders and background fills. This requires managing `<hh:borderFill>` registries in `header.xml` and referencing them within table cells in `sectionN.xml`.

## 2. Border & Fill Registry (`borderFill`)
In OWPML, borders and fills are not defined inline. Instead, they are registered in the document header as `borderFill` entries.

- **Location**: `header.xml` inside `<hh:borderFills>`.
- **Structure**:
- **Structure (Audited from Skeleton.hwpx)**:
    ```xml
    <hh:borderFill xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" 
                   xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core"
                   id="1" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">
      <hh:slash type="NONE" Crooked="0" isCounter="0" />
      <hh:backSlash type="NONE" Crooked="0" isCounter="0" />
      <hh:leftBorder type="NONE" width="0.1 mm" color="#000000" />
      <hh:rightBorder type="NONE" width="0.1 mm" color="#000000" />
      <hh:topBorder type="NONE" width="0.1 mm" color="#000000" />
      <hh:bottomBorder type="NONE" width="0.1 mm" color="#000000" />
      <hh:diagonal type="SOLID" width="0.1 mm" color="#000000" />
      <!-- Optional Fill -->
      <hc:fillBrush>
        <hc:winBrush faceColor="none" hatchColor="#999999" alpha="0" />
      </hc:fillBrush>
    </hh:borderFill>
    ```

## 3. Cursor-Based Table State Machine
To implement complex formatting (like setting specific borders for specific cells), `HwpxDocumentBuilder` utilizes a **Cursor-Based State Machine**:

1.  **State Variables**:
    *   `self._current_table`: Stores reference to the `<hp:tbl>` element currently being edited.
    *   `self._current_cell`: Stores reference to the active `<hp:tc>` element.
    *   `self._current_container`: The target XML element for text insertion; switches between `section_elem` and the active cell's `<hp:tc>`.

2.  **Implementation of `_move_to_cell`**:
    Iterates through row and column elements within the active table:
    ```python
    def _move_to_cell(self, action: MoveToCell):
        rows = self._current_table.findall(f'.//{{hp_ns}}tr')
        tr = rows[action.row]
        cols = tr.findall(f'.//{{hp_ns}}tc')
        self._current_cell = cols[action.col]
        self._current_container = self._current_cell
    ```

3.  **Context-Aware `InsertText`**:
    Instead of always appending to the document body, the builder now targets `self._current_container`:
    ```python
    container = self._current_container if self._current_container is not None else self.section_elem
    p = ET.SubElement(container, _hp('p'), ...)
    ```

### 3.1 Logical Sequence
1.  `CreateTable`: Resets `self._current_table` to the new table, resets `_current_cell` to None, and sets `_current_container` to the document body.
2.  `MoveToCell(r, c)`: Sets the cursor to a specific cell.
3.  `SetCellBorder`: Applies a `borderFillID` to the `_current_cell`.
4.  `InsertText`: Injects content into the active cell (the `_current_container`).

### 3.2 Remediation (Resolved)
- **Refactoring Bug**: The `IndentationError` at line 327 within `document_builder.py` was resolved by manually restoring the loop integrity after a global regex replacement error.
- **Syntax Error**: A `SyntaxError` at line 270 of `header_manager.py` (unterminated triple-quoted string) was fixed by removing duplicate method fragments left over from an incorrect byte-range replacement.
- **Missing Initialization**: An `AttributeError` for `_current_container` was resolved by manually adding state variable initialization to `__init__` and `_init_document`, fixing a failure in the automated refactoring script.

## 4. Implementation Strategy
1. **Header Registration**: `HeaderManager` will be expanded with `get_or_create_border_fill(border_params, fill_params)` to return an ID.
2. **Cell Application**: The table builder logic will inject `borderFillIDRef` into the `<hp:tc>` (Table Cell) element.
3. **Border Types**: Standard HWP border types include `SOLID`, `DOTTED`, `DASHED`, `DOUBLE_SLIM`, etc.
4. **Width Units**: Widths are typically specified in millimeters (e.g., `0.1 mm`) or points in the XML, maintaining consistent visual scale across different viewers.

### 4.1 HeaderManager Implementation Detail
The `get_or_create_border_fill` method in `HeaderManager` translates high-level style parameters into registered OWPML entries:

```python
def get_or_create_border_fill(self, border_type: str = "Solid", width: str = "0.1mm", color: str = "#000000", fill_color: Optional[str] = None) -> str:
    # 1. Map inputs to OWPML Enums (e.g., 'Solid' -> 'SOLID')
    # 2. Locate <hh:borderFills> container in header.xml
    # 3. Create <hh:borderFill> with new ID
    # 4. Inject 4-way borders in 'head' (hh) namespace
    # 5. Inject <hc:fillBrush> in 'core' (hc) namespace if fill_color provided
    # 6. Update itemCnt in container
```

## 5. Audit Results (January 2026)
- **ID 1**: Standard default (Transparent borders, solid diagonal).
- **ID 2**: Similar to ID 1 but includes a `fillBrush` with `hatchColor="#999999"`.
- **Observation**: The `fillBrush` element resides in the `http://www.hancom.co.kr/hwpml/2011/core` (hc) namespace, while the borders are in `http://www.hancom.co.kr/hwpml/2011/head` (hh).

## 6. Implementation Notes
- **Deduplication**: `HeaderManager` will implement a lookup table to reuse `borderFill` IDs for identical border/fill combinations.
- **State Switch**: The builder will maintain an `active_table` context to allow `MoveToCell(r, c)` actions to efficiently find and wrap the targeted `<hp:tc>` element.

### Status Update (January 2026)
- **Model**: `SetCellBorder` action model fully integrated.
- **HeaderManager**: Namespace support for `hc` (Core) and `hh` (Head) fully operational. `get_or_create_border_fill` supports background colors and custom line types.
- **Builder**: Cursor-based state machine successfully implements `MoveToCell`, allowing targeted cell formatting and content insertion.
- **Verification**: Verified through `tests/manual_verify_table_formatting.py` and structural XML analysis. Phase 10 is considered **COMPLETED**.
