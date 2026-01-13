# Table Implementation Logic (Phase 1 & 2)

## 1. Overview
HWPX tables (`hp:tbl`) are grid-based structures following the OWPML schema. Implementing advanced tables (with merges and precise layouts) requires careful management of logical coordinates and physical dimensions.

## 2. Cell Merging & Addressing
HWPX identifies cells using logical coordinates regardless of their physical span.

### 2.1 Addressing (`hp:cellAddr`)
Each cell (`hp:tc`) must explicitly declare its target grid position:
```xml
<hp:cellAddr colAddr="0" rowAddr="1" />
```

### 2.2 Merging (`hp:cellSpan`)
Spanned cells are defined at their top-left origin:
```xml
<hp:cellSpan colSpan="2" rowSpan="2" />
```
**Ghost Cell Suppression**: In the OWPML XML, the "ghost cells" (occupied by the span but not the origin) must be entirely omitted from the `hp:tr` block. Failure to skip these results in table corruption or extra empty cells appearing in Hancom Office.

## 3. Precision Dimensional Tuning
To ensure tables align perfectly with page margins, integer division remainders must be handled.

### 3.1 Distribution Strategy
Assuming a total content width of **42520 HwpUnits** (A4):
1.  **Base Width**: `TOTAL_WIDTH // column_count`
2.  **Remainder**: `TOTAL_WIDTH % column_count`
3.  **Correction**: Add the remainder to the final column width.

### 3.2 Spanned Width Calculation
The width of a merged cell is the sum of the precise widths of the columns it spans:
```python
span_width = sum(col_widths[c + i] for i in range(col_span))
```
This ensures that `TableCell1.width + TableCell2.width` exactly equals the `Table.width` without rounding errors.

## 4. Resource Efficiency
To prevent "Header Bloat" (thousands of identical styling entries), the implementation follows a **Request-and-Reuse** pattern.

-   **Logic**: Call `HeaderManager.get_or_create_border_fill('SOLID')` once at the start of `_create_table`.
-   **Reuse**: Assign the resulting `borderFillIDRef` (e.g., `3`) to the parent `<hp:tbl>` and every constituent `<hp:tc>`.
-   **Impact**: A 10x10 table adds exactly **one** entry to `header.xml`, regardless of cell count.

## 5. Verification Patterns
- **Geometry**: Summing `cellSz` widths in a row must equal 42520.
- **Topology**: Total `hp:tc` elements in XML must equal `(Rows * Cols) - Sum(MergedCells - 1)`.
