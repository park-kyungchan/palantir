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
To implement complex formatting (like setting specific borders for specific cells), `HwpxDocumentBuilder` is transitioning to a **Cursor-Based Logic**:

1. **Table Context**: When a table is created, the builder enters a "Table Mode".
2. **Cell Targeting**: Actions like `SetCellBorder` or `SetCellBackground` should target the "Current Cell" or a range of cells.
3. **Stateful Application**: The builder tracks the state of the current table being built to apply formatting before the next `InsertText` or `CreateTable` action moves the cursor.

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
- **Model**: `SetCellBorder` action model expanded with `fill_color`.
- **HeaderManager**: Namespace support for `hc` (Core) added. `get_or_create_border_fill` implemented to support both line styles and background colors.
- **Next**: Finalize `DocumentBuilder` cursor logic and stateful cell targeting.
