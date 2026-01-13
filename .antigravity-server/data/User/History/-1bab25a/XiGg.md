# Native OWPML Generation & Template-Based Reconstruction

This document outlines the technical implementation of native HWPX (OWPML XML) generation, moving beyond win32com automation to a stable, Linux-native pipeline.

## 1. Architectural Evolution

The native OWPML pipeline evolved from manual XML assembly to **Template-Based Reconstruction (TBR)** to handle the extreme complexity of OWPML headers.

### 1.1 The ID-Reference Mechanism
OWPML uses an ID-Reference system. Formatting entities (Para Shapes, Char Shapes, Borders) are defined in `header.xml` and assigned integer IDs, which are then referenced in `section0.xml` (e.g., `paraPrIDRef="0"`).

## 2. Mandatory OWPML Structure (Anti-Corruption)

Hancom Office 2024 enforces strict validation of both ZIP structure and XML logic.

### 2.1 ZIP Package Integrity
- **Mimetype**: Must be the first file and uncompressed (`Stored`).
- **Required Root Files**: `version.xml` (version info), `settings.xml` (cursor state), `META-INF/manifest.xml`.
- **Logical Linkage**: `META-INF/container.rdf` is mandatory to associate ZIP parts with OWPML roles (`HeaderFile`, `SectionFile`).

### 2.2 Body Integrity (`section0.xml`)
- **Section Properties (`hp:secPr`)**: The first paragraph **MUST** contain `secPr` in its first run to define paper size/margins.
- **Layout Cache**: Paragraphs should include a skeletal `hp:linesegarray` for renderer stability.

## 3. Strategy: Template-Based Reconstruction (TBR)

Due to the 40KB+ complexity of `header.xml` (containing multi-language font definitions and nested property tags), the system uses a verified "Golden Template" (e.g., `Skeleton.hwpx`).

1.  **Template Reuse**: The generator copies all metadata, manifests, and complex header structures from the template.
2.  **Substitution**: Only `Contents/section0.xml` is replaced with dynamically generated OWPML Body XML.
3.  **Stability**: This approach guarantees 100% compatibility with Hancom 2024's strict rendering engine.

## 5. Phase 10: Community-Driven API Integration (`python-hwpx`)

To move beyond static template substitution, the pipeline is migrating to the **`python-hwpx`** library for dynamic document building.

### 5.1 Architectural Shift
Instead of manually replacing `section0.xml`, the system uses a high-level API to manipulate document objects:
- **Dynamic Styling**: Allows creating new paragraph properties (`paraPr`) and character properties (`charPr`) on-the-fly.
- **Object Mapping**: Maps `HwpAction` (SetParaShape, InsertText) directly to library methods like `add_paragraph()` or `add_table()`.

### 5.2 Technical Constraints & Discovery
During the integration of `python-hwpx` v1.9, several critical API patterns were identified:
1.  **Template Requirement**: The `HwpxDocument` constructor requires an existing `HwpxPackage` and a `root` (HwpxOxmlDocument). New documents should be initialized using `hwpx.templates.blank_document_bytes()`.
2.  **Package Loading**: Use `HwpxPackage.open(path)` to load a template. The document is then instantiated as `HwpxDocument(package, package.get_xml(package.HEADER_PATH))`.
3.  **Namespace Sensitivity**: The library handles common OWPML namespaces (ha, hp, hs, hh) automatically, but custom attribute injections may require manual namespace registration.

### 5.3 Style Management Pattern (Proposed)
```python
from hwpx.document import HwpxDocument
# Load from blank skeleton
doc = HwpxDocument.from_bytes(templates.blank_document_bytes())
# Access/Modify styles
para_style = doc.para_properties[0] 
# Add content
doc.add_paragraph("Content", style=para_style)
```

For a detailed analysis of the underlying community standards, refer to [Community Standards Audit](../overview/community_standards_audit.md).
