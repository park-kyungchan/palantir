# Native OWPML Generation Protocol

This document outlines the technical requirements for implementing native HWPX (OWPML XML) generation, moving beyond win32com automation on Windows.

## 1. Architectural Pattern: ID-Reference Mechanism

Unlike HTML where styles can be defined inline, OWPML follows a strict **Separation of Definition and Reference** (similar to CSS classes but using integer IDs).

### 1.1 Implementation Workflow
1.  **Header Definition (`Contents/header.xml`)**: Define formatting entities (Paragraph Shapes, Character Shapes, Borders) in their respective lists and assign/retrieve a unique ID.
2.  **Body Reference (`Contents/section0.xml`)**: Reference these IDs using attributes like `paraPrIDRef` or `charPrIDRef` on structural tags.

## 2. Paragraph Shape (`SetParaShape`) Mapping

To implement `SetParaShape(left_margin, indent, line_spacing)` in OWPML:

### 2.1 Unit Conversion
Native HWPX uses **HWP Units**. 
- **Standard Conversion**: 1 point (pt) $\approx$ 100 HWP Units.
- **Example**: `left_margin: 20pt` $\rightarrow$ `2000` HWP Units.

### 2.2 XML Structure (`header.xml`)
Define the shape in the `<hh:paraPrList>`.

```xml
<hh:paraPr id="0" type="normal">
    <hp:align horizontal="left" />
    <hp:margin left="2000" right="0" top="0" bottom="0" indent="-2000" />
    <hp:lineSpacing type="percent" val="160" unit="percent" />
</hh:paraPr>
```
*Note: A negative `indent` represents a **Hanging Indent** (내어쓰기).*

### 2.3 XML Structure (`section0.xml`)
Apply the ID to the paragraph tag.

```xml
<hp:p paraPrIDRef="0">
    <hp:run>
        <hp:t>Content goes here...</hp:t>
    </hp:run>
</hp:p>
```

## 3. Implementation Challenges

1.  **ID Management**: The `HWPGenerator` must maintain a registry or dictionary of seen styles to reuse IDs and avoid bloated header files.
2.  **Unit Consistency**: High-precision layout depends on exact HWP Unit calculation (especially for mathematical formulas where 1/7200 inch is the base unit).
3.  **Namespace Handling**: Correctly prefixing tags with `hs`, `hp`, and `hh` as defined in the OWPML schema.
