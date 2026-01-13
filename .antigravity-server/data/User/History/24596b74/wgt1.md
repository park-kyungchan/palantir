# Page Layout Logic (Phase 9)

## 1. Overview
Page layout in HWPX is governed by Section Properties (`<hp:secPr>`). Each document section defines its own margins, paper size, and orientation within this element.

- **Location**: In a standard HWPX document, the `secPr` for the first section is typically found inside the first paragraph's text run: `<hp:p><hp:run><hp:secPr>...</hp:secPr></hp:run></hp:p>`.
- **Reference**: OWPML (KS X 6101) Section 5.1.

## 2. Page Properties (`hp:pagePr`)
The `<hp:pagePr>` element defines the physical paper dimensions and orientation.

### 2.1 Dimensions and Orientation
- **Attributes**:
    - `width`: Page width in HwpUnits (e.g., A4 is 59528).
    - `height`: Page height in HwpUnits (e.g., A4 is 84186).
    - `landscape`: Enum indicating orientation.
        - `NARROWLY`: Portrait (Default).
        - `WIDELY`: Landscape.
- **Orientation Swap**: When switching to Landscape, the `width` and `height` values must be swapped, and the `landscape` attribute set to `WIDELY`.

### 2.2 Paper Size Constants (A4)
- **HwpUnits**: 1 mm = 283.465 HwpUnits.
- **A4 Portrait**: Width = 210mm (59528 units), Height = 297mm (84186 units).

## 3. Page Margins (`hp:margin`)
Margins are defined within the `<hp:margin>` child of `<hp:pagePr>`.

- **Attributes**: `left`, `right`, `top`, `bottom`, `header`, `footer`, `gutter`.
- **Unit Calculation**:
    - Input: Millimeters (mm).
    - Output: HwpUnits (int(mm * 283.465)).
- **Example**: 15mm margin ≈ 4252 HwpUnits.

## 4. Implementation Strategy
The `HwpxDocumentBuilder` utilizes a targeted search to locate the existing `secPr` and modify its children.

1. **Locate secPr**: Scan the first run of the first paragraph for the `<hp:secPr>` element.
2. **Retrieve/Create pagePr**: Ensure the `<hp:pagePr>` element exists.
3. **Update Attributes**: Apply the new dimensions, landscape setting, and margins derived from the `SetPageSetup` action.
4. **Consistency**: Ensure that any changes to page size are mirrored across all `pagePr` elements if multiple sections or layouts (like `pageBorderFill`) are present.

## 5. Preliminary Research Findings (January 2026)
- **Skeleton Defaults**: Standard documents start with A4 Portrait and specific margins (Left/Right: 30mm, Top: 20mm, Bottom: 15mm).
- **Coordinate System**: All layout measurements in `secPr` use HwpUnits, maintaining parity with table and shape coordinate systems.
- **Namespace Integrity**: `secPr` and its children must reside in the `http://www.hancom.co.kr/hwpml/2011/paragraph` namespace inside the section XML.
