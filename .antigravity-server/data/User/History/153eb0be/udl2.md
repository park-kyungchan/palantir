# Native OWPML Generation Protocol & Implementation

This document outlines the technical implementation of native HWPX (OWPML XML) generation, utilizing the ID-Reference mechanism to move beyond win32com automation on Windows.

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

## 3. Implementation: HeaderManager Class

The `HeaderManager` (implemented in `lib/owpml/header_manager.py`) provides the core logic for managing style registries and ID assignments.

### 3.1 Responsibilities
- **Style Registry**: Maintains lists of `paraPr` (Paragraph Properties) encountered during generation.
- **De-duplication**: Uses a feature-based hash (left margin, indent, etc.) to map unique property sets to single IDs, preventing XML bloat.
- **XML Generation**: Aggregates all registered styles into the final `header.xml` output.

### 3.2 Unit Mapping Logic
- **Base Unit**: OWPML utilizes HWP Units (approximately $1/7200$ inch).
- **Rule of Thumb**: $1 \text{ pt} = 100 \text{ HWP Units}$.
- **Hanging Indents**: Represented by negative `indent` values in the `<hp:margin>` tag.

## 4. Implementation Challenges & Resolutions

1.  **ID Management**: **Resolved** via `HeaderManager` stateful registry. Styles are reused across paragraphs sharing the same visual properties.
2.  **Unit Consistency**: **Standardized** on $100 \times$ factor for point-to-unit mapping.
3.  **Namespace Handling**: **Implemented** standard schema prefixes (`hs`, `hp`, `hh`) in `HWPGenerator`.
