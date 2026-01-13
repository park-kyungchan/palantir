# Table Formatting Logic (Phase 10)

## 1. Overview
Phase 10 focuses on extending table capabilities from structural creation to visual formatting, specifically cell borders and background fills. This requires managing `<hh:borderFill>` registries in `header.xml` and referencing them within table cells in `sectionN.xml`.

## 2. Border & Fill Registry (`borderFill`)
In OWPML, borders and fills are not defined inline. Instead, they are registered in the document header as `borderFill` entries.

- **Location**: `header.xml` inside `<hh:borderFills>`.
- **Structure**:
    ```xml
    <hh:borderFill id="1" ...>
        <hh:slash type="NONE" ... />
        <hh:backSlash type="NONE" ... />
        <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000" />
        <hh:rightBorder ... />
        <hh:topBorder ... />
        <hh:bottomBorder ... />
        <hh:diagonal ... />
        <hh:fillBrush>
            <hh:winBrush faceColor="none" hatchColor="#000000" hatchStyle="NONE" alpha="0" />
        </hh:fillBrush>
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
4. **Width Units**: Widths are typically specified in millimeters (e.g., `0.12 mm`) or points in the XML, unlike HwpUnits used for layout.

## 5. Ongoing Research (Phase 10 Audit)
- **Skeleton Audit**: Identifying if the `Skeleton.hwpx` contains pre-defined border styles that can be reused.
- **Deduplication**: Implementing logic to reuse existing `borderFill` IDs for identical border/fill combinations to prevent header bloat.
