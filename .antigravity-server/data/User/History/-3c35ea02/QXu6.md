# Control Objects Implementation (Phase 6)

## 1. Overview
Control objects in HWPX (Images, Shapes, TextBoxes) share a common foundation in OWPML. To ensure consistency and reduce duplication, the implementation uses a unified helper for common shape properties (size, position, margins).

## 2. Shared Shape Foundation
The `_create_common_shape_props` helper in `HwpxDocumentBuilder` handles the four mandatory child elements for all shape-based control objects:

1.  **`<hp:sz>` (Size)**: Defines width and height in HwpUnits.
2.  **`<hp:pos>` (Position)**:
    *   **Inline (`treatAsChar="1"`)**: Flows with text like a character.
    *   **Floating (`treatAsChar="0"`)**: Absolute positioning relative to Paper or Page.
3.  **`<hp:outMargin>`**: External margins (left, right, top, bottom).
4.  **`<hp:shapeComment>`**: Optional comment metadata.

### Implementation Pattern:
```python
def _create_common_shape_props(self, parent: ET.Element, width: int, height: int, 
                             is_inline: bool = True, x: int = 0, y: int = 0):
    # sz: width, height, widthRelTo, heightRelTo
    # pos: treatAsChar, flowWithText, vertRelTo, horzRelTo, vertOffset, horzOffset
    # outMargin, shapeComment
```

## 3. Image Controls (`hp:pic`)
Images are represented by the `<hp:pic>` element, which acts as a container for the common shape properties and a specific `<hp:img>` element.

### XML Structure:
```xml
<hp:pic id="7XXXX" zOrder="0" numberingType="PICTURE">
    <hp:sz ... />
    <hp:pos ... />
    <hp:outMargin ... />
    <hp:shapeComment />
    <hp:img binaryItemIDRef="binXXXX" imageType="REAL_PIC" />
</hp:pic>
```
- **binaryItemIDRef**: References an entry in `content.hpf` (managed by `BinDataManager`).

## 4. TextBox Controls (`hp:rect`)
Text boxes are implemented using the `<hp:rect>` element. Unlike simple shapes, text boxes contain an internal document structure via `<hp:subList>`.

### XML Structure:
```xml
<hp:rect id="8XXXX" zOrder="0" numberingType="SHAPE">
    <hp:sz ... />
    <hp:pos ... />
    <hp:outMargin ... />
    <hp:shapeComment />
    <hp:subList textDirection="HORIZONTAL" vertAlign="CENTER">
        <hp:p>
            <hp:run>
                <hp:t>Text Content</hp:t>
            </hp:run>
        </hp:p>
    </hp:subList>
</hp:rect>
```
- **`<hp:subList>`**: Acts as a nested section container, allowing paragraphs (`<hp:p>`) inside the shape.

## 5. Integration Trace
1.  **Action Dispatch**: `document_builder` maps `InsertImage` or `InsertTextBox` to respective handlers.
2.  **Property Calculation**: mm dimensions are converted to HwpUnits (1mm ≈ 283.46 HwpUnits).
3.  **Hierarchy Construction**:
    - For Images: `ctrl` → `pic` → `img` + `Common Props`.
    - For TextBoxes: `ctrl` → `rect` → `subList` → `p` + `Common Props`.
4.  **Save Cycle**: `set_part` injects binaries (for images) and `set_xml` persists the updated `section0.xml`.
