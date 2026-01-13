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

## 5. Mandatory OWPML Structure (Anti-Corruption)

A valid HWPX `header.xml` requires more than just paragraph properties. Missing any of the following triggers a "File Damaged" error in Hancom Office:

1.  **`<hh:docOption>`**: Must contain `<hh:linkinfo>` even if empty.
2.  **`<hh:charPrList>`**: Must contain at least one `charPr` (Character Property). Style 0 usually references `charPr` 0.
3.  **`<hh:styleList>`**: Critical for document opening. A "Normal" style (ID 0) must be defined and point to valid `paraPrIDRef` and `charPrIDRef`.
4.  **`<hh:borderFillList>`**: Referenced by character and paragraph properties. At least one default border fill (ID 0) is mandatory.
5.  **`<hh:faceNameList>`**: Mandatory if any `charPr` uses a `fontRef`. It must define the faces (e.g., "HamChorom Batang") for different scripts (hangul, latin, etc.).
6.  **`paraPr` ID 0**: HWPX often expects ID 0 to be the "Normal" paragraph properties. If the sequence starts with text before the first `SetParaShape`, or if `styleIDRef="0"` is used, `paraPr` ID 0 must exist.

### 5.1 Zip Packaging Caveats
- **Manifest Paths**: In `Contents/content.hpf`, items must use paths relative to the `Contents` folder (e.g., `href="header.xml"`) OR the generator must ensure the physical zip structure matches the manifest exactly.
- **Mimetype**: Must be the *first* file in the ZIP and **uncompressed** (`Stored`).
- **OPF Unique ID**: The `<opf:package>` tag's `unique-identifier` attribute must have a corresponding `<dc:identifier>` element with a matching `id` in the metadata section.
- **Mandatory External Files**: Official Hancom HWP 2024 requires specific files at the root level of the ZIP:
    - `version.xml`: Defines OWPML version and target application version.
    - `settings.xml`: Mandatory document state file (e.g., `<hs:CaretPosition>`).
    - `META-INF/manifest.xml`: A secondary manifest listing the mimetype and core XML files (distinct from `content.hpf`).

### 5.2 Mandatory Package Structure (KS X 6101 compliant)
```
├── mimetype (Stored)
├── version.xml
├── settings.xml
├── META-INF/
│   ├── container.xml
│   ├── container.rdf (CRITICAL: Logical linkage)
│   └── manifest.xml
└── Contents/
    ├── content.hpf
    ├── header.xml
    └── section0.xml
```

### 5.3 Logical Linkage (`container.rdf`)
Modern Hancom Office (2024+) uses `container.rdf` to find the specific parts of the OWPML package. If this file is missing or doesn't explicitly link `header.xml` and `section0.xml` as `HeaderFile` and `SectionFile` types, the application may crash while trying to resolve the document layout.

### 5.1 Style Linkage Diagram
```
[section0.xml] <hp:p paraPrIDRef="N">
      ↓
[header.xml] <hh:paraPr id="N">
      ↑
[header.xml] <hh:style id="0" paraPrIDRef="N"> (Optional but recommended)
```
While `section0.xml` can reference `paraPr` directly by ID, Hancom Office 2024 prefers strict alignment where the default font and paragraph settings are also mirrored in the `styleList`.

## 6. Logical Schema Validation & Application Stability

Even if the ZIP structure is 100% compliant and the "File Damaged" popup is resolved, the application (Hancom 2024) may **silently crash** (terminate immediately after splash screen) if the high-level OWPML XML content violates KS X 6101 logical rules.

### 6.1 Known Crash Triggers
- **Missing Linkage**: A `charPrIDRef` or `paraPrIDRef` in `section0.xml` pointing to an ID not defined in `header.xml`.
- **Incomplete Runs**: Paragraphs (`hp:p`) without children or with malformed `hp:run` / `hp:t` structures.
- **Cache Mismatch**: HWPX files often contain layout cache (e.g., `lineSegArray`). If the text is modified programmatically without clearing or correctly regenerating these caches, the renderer may crash.

### 6.2 External Framework Reference: `python-hwpx`
For deep schema verification and robust generation patterns, refer to the **`python-hwpx`** library (Source: [github.com/airmang/python-hwpx](https://github.com/airmang/python-hwpx)). 
- **Key Insight**: The `Skeleton.hwpx` structure in this library is the gold standard for minimal, compliant HWPX generation.
- **Critical Discovery**: `container.rdf` is used to define parts as `HeaderFile` and `SectionFile` types, which is essential for rendering engine stability.
