# HWPX High-Fidelity Features Master Guide (Phases 7-13)

## 1. Scientific Equations (Phase 7)

### Overview
HWPX equations utilize a proprietary script format ("HWP Equation Script") embedded within a `<hp:eqEdit>` control. Use of the `latex_to_hwp` converter in `lib/owpml/equation_converter.py` is necessary for mathematical document reconstruction.

### OWPML Structure (`hp:eqEdit`)
Equations reside within a `<hp:ctrl>` inside a `<hp:run>`.

```xml
<hp:p id="...">
  <hp:run charPrIDRef="...">
    <hp:ctrl>
      <hp:eqEdit version="2" baseLine="BASE" textColor="#000000" baseUnit="PUNKT">
        <hp:script>{a} OVER {b}</hp:script>
      </hp:eqEdit>
    </hp:ctrl>
  </hp:run>
</hp:p>
```

### Implementation Highlights
- **Conversion**: Handles nested fractions, roots, and limits via recursive regex pattern matching.
- **Layout**: Omit `linesegarray` within the paragraph to allow the viewer to auto-calculate the equation's physical bounds.

---

## 2. Dynamic Style Management (Phase 8)

### Style Reference System
Styles are defined in `header.xml` and referenced by ID in `sectionN.xml` to ensure document efficiency.

- **Paragraph Shapes**: Defined in `<hh:paraProperties>` (`<hh:paraPr>`). Referenced by `paraPrIDRef` in `<hp:p>`.
- **Character Shapes**: Defined in `<hh:charProperties>` (`<hh:charPr>`). Referenced by `charPrIDRef` in `<hp:run>`.

### HeaderManager Implementation
- **Character Properties**: Multiplies font points by 100 (10pt = 1000). Handles dynamic ID generation for size, bold, and color.
- **Paragraph Properties**: Maps alignments (`LEFT`, `CENTER`, `RIGHT`, `JUSTIFY`, `DISTRIBUTE`) and HwUnit indentation.

---

## 3. Page Layout & Margins (Phase 9)

### Section Properties (`hp:secPr`)
Page settings are governed by Section Properties, typically located in the first character run of a section.

### Page Properties (`hp:pagePr`)
- **Dimensions**: Page width and height in HwpUnits (1mm = 283.465).
- **Orientation**: Supports `Portrait` and `Landscape`. Note that `Landscape` requires swapping the `width` and `height` attributes.
- **Margins**: Defined in `<hp:margin>` within `<hp:pagePr>`.

---

## 4. Advanced Table Formatting (Phase 10)

### Cursor-Based State Machine
To handle per-cell visual styling, `HwpxDocumentBuilder` implements a state machine that tracks the focused cell context.

- **State Variables**: `_current_table`, `_current_cell`, `_current_container`.
- **Logic Sequence**:
    1. `CreateTable`: Initializes a table and sets focus container.
    2. `MoveToCell(r, c)`: Targets a specific `hp:tc` element and sets it as the active container.
    3. `SetCellBorder`: Applies a `borderFillID` (style + fill) to the active cell.
    4. `InsertText`: Re-routed to the cell container if one is active.

### Border & Fill Registries (`hh:borderFill`)
Borders and fills must be registered in the header before use.
- **Namespace Split**: Border properties (Line type, width, color) reside in the `hh` (Head) namespace. Background fills (`fillBrush`) reside in the `hc` (Core) namespace.
- **Deduplication**: Recommended to implement a lookup table in `HeaderManager` to reuse existing style IDs.
---

## 5. Nested Tables (Phase 11)

### Enabling Recursion
To support tables-within-tables, the `_create_table` method was updated to use the cursor-based state machine context.

- **Contextual Placement**: Instead of always attaching the table paragraph to `self.section_elem`, the builder now checks `self._current_container`.
- **Target Container**: If `MoveToCell` has set the context to a table cell (`hp:tc`), the new table paragraph is appended directly to that cell.
- **Verification**: Confirmed via `tests/manual_verify_nested_tables.py`, ensuring the OWPML structure `tbl -> tr -> tc -> p -> ctrl -> tbl` is correctly generated.

---

## 6. Context-Aware Inline Controls (Phase 12)

### Universal Positioning
The architectural pattern established for Nested Tables was extended to all inline objects to ensure they can reside within table cells.

- **Refactored Controls**: `_insert_image`, `_insert_textbox`, and `_insert_equation`.
- **Logic Update**:
  ```python
  container = self._current_container if self._current_container is not None else self.section_elem
  p = ET.SubElement(container, _hp('p'), ...)
  ```
- **Impact**: Resolves the "root-locked" limitation where images or equations would always default to the document end, regardless of the active cursor position.
- **Verification**: `tests/manual_verify_controls.py` confirmed that Images, TextBoxes, and Equations are correctly inserted into designated table cells by verifying the OWPML hierarchy (`tbl -> tr -> tc -> p -> ctrl -> [pic|rect|eqEdit]`).

---

## 7. Advanced Lists & Numbering (Phase 13)

### OWPML Numbering Architecture
Lists in HWPX are governed by a link between section content (`sectionN.xml`) and the style header (`header.xml`).

- **Reference Linkage**:
    1. Paragraph Properties (`hp:paraPr`) reference a `numberingIDRef`.
    2. The Header (`header.xml`) contains a `<hh:numberings>` collection.
    3. Each `<hh:numbering>` defines its behavior for levels 1 through 7 via `<hh:paraHead>` elements.
- **Data Model**: The `SetNumbering` action (added to `models.py`) supports `numbering_type: Literal["None", "Number", "Bullet"]`.
- **Implementation Strategy**:
    - **HeaderManager**: Must support `get_or_create_numbering()` to register new bullet or numbering schemes.
    - **Format Strings**: Crucial finding from Skeleton audit - the format string (e.g., `^1.`, `^2)`, `•`) is stored as **text content** within the `<hh:paraHead>` element, not as an attribute.
    - **Start Values**: `paraHead` attributes control the starting number (e.g., `start="1"`).
    - **Number Formats**: Standard HWP types include `DIGIT`, `HANGUL_SYLLABLE`, `CIRCLED_DIGIT`, `ROMAN_SMALL`, etc.


