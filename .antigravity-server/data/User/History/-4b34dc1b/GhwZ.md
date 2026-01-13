# Native HWPX Generation (Linux / OWPML)

## Overview
Native HWPX generation allows the pipeline to produce `.hwpx` files directly on a Linux environment without requiring a Windows host or Hancom Office installation. This is achieved by manipulating the OWPML (Open WYSIWYG Package Markup Language) XML schema and packaging it into an OOXML-compliant ZIP container.

## 1. Architectural Strategy
Instead of transpiling actions to Python scripts (as in Phase 5), this layer maps IR or `HwpAction` objects directly to XML fragments.

- **Container**: Standard ZIP archive renamed to `.hwpx`.
- **Mimetype**: `application/hwp+zip` (must be the first file in the ZIP and uncompressed).
- **Metadata**: Managed via `META-INF/container.xml` and `Contents/content.hpf`.
- **Content**: Expressed in `Contents/sectionN.xml` using the `hs` (section) and `hp` (paragraph) namespaces.

## 2. Core XML Mapping

### 2.1 Paragraph Structure
```xml
<hp:p>
  <hp:run>
    <hp:t>Text Content</hp:t>
  </hp:run>
</hp:p>
```

### 2.2 Namespace Requirements
Typical namespaces required for a valid section file:
- `xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"`
- `xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"`

## 3. Implementation Details (`lib/owpml/generator.py`)
- **State Machine**: Iterates through `HwpAction` objects. 
- **Text Handling**: `InsertText` actions are split by newlines, with each segment wrapped in `<hp:p><hp:run><hp:t>...</hp:t></hp:run></hp:p>`.
- **Escaping**: Manual XML escaping for characters like `&`, `<`, and `>`.
- **Packaging**: Uses `zipfile` with `ZIP_STORED` for the `mimetype` file and `ZIP_DEFLATED` for XML contents.

## 4. Current Limitations
- **Style Mapping**: Paragraph shapes (indentation, centering) are not yet mapped to OWPML property tags (`<hp:pPr>`).
- **Complex Objects**: Tables and Equations are not yet implemented in the native XML generator.
- **Single Section**: Currently only supports a single `section0.xml`.

## 5. Verification
Verified via `scripts/run_pipeline.py`, which generates `output_actions.hwpx`. The resulting file is valid and viewable in Hancom Office.
