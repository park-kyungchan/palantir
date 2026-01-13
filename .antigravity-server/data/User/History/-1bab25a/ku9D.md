# Native OWPML Generation & Template-Based Reconstruction

This document outlines the technical implementation of native HWPX (OWPML XML) generation, moving beyond win32com automation to a stable, Linux-native pipeline.

## 1. Architectural Evolution

The native OWPML pipeline evolved from manual XML assembly to **Template-Based Reconstruction (TBR)** to handle the extreme complexity of OWPML headers.

## 2. Theoretical Framework: Spec-First Native Integration

As mandated in Phase 12, the pipeline follows a **Spec-First** strategy. We no longer attempt to simulate HWPX behavior by manipulating high-level paragraph flags (which are often ignored by the HWP 2024 rendering engine if the supporting control structure is missing).

Instead, we identify the **Native Capability** in the **KS X 6101** specification (e.g., `hp:colPr` for columns, `hp:eqEdit` for math) and inject the strictly compliant XML structure into the document's body runs.

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

## 4. Strategy: Template-Based Reconstruction (TBR)

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

### 5.3 Technical Implementation: `HwpxDocumentBuilder` (Phase 10)

The finalized `HwpxDocumentBuilder` implements a robust workflow using `python-hwpx`:
1. **Template Bootstrapping**: Uses `hwpx.templates.blank_document_bytes()` to retrieve a valid HWPX skeleton.
2. **Package Serialization**: Writes the blank bytes to a temporary file (as `HwpxPackage.open()` requires a physical file path) then opens the package.
3. **Internal Path Resolution**: Accesses active sections via `pkg.section_paths()` (which returns a list of internal ZIP paths).
6.  **Layout Pre-Scanning**: Before processing text actions, the builder scans for `MultiColumn` actions to define the section's `colPr` structure in the first paragraph, ensuring consistent flow.
7.  **XML Modification**: Retrieves the `Contents/section0.xml` tree via `pkg.get_xml()`.

### 5.4 XML Engine Compatibility: `xml.etree.ElementTree`
A critical discovery during implementation was that `python-hwpx` v1.9 interacts with `xml.etree.ElementTree.Element` objects. Attempts to use `lxml` directly caused type errors during `pkg.set_xml()`.
- **Backend**: Standard library `xml.etree.ElementTree` (ET).
- **Tag Formatting**: Uses the universal `{namespace}tag` format (e.g., `{http://www.hancom.co.kr/hwpml/2011/paragraph}p`).

### 5.5 Namespace Helper Pattern
To maintain readability when manually constructing OWPML tags, a helper pattern was adopted:

```python
HP_NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'

def _hp(tag: str) -> str:
    """Helper to create hp: namespace tag."""
    return f'{{{HP_NS}}}{tag}'

# Usage:
p = ET.SubElement(section_elem, _hp('p'), {'id': '1'})
```

### 5.6 Stability Requirements (Body Construction)
- **Para ID Management**: Each `<hp:p>` requires a unique `id` attribute. Implementation uses a sequential `para_counter`.
- **Default Styles**: Newly created paragraphs reference `paraPrIDRef="0"` and `charPrIDRef="0"` from the template.
- **Line Segment Arrays**: Mandatory for HWP 2024. A skeletal `<hp:lineseg>` is injected into every paragraph; the HWP renderer recalculates precise values on first open.

### 5.7 Verification & Success
Phase 10 was successfully verified by processing a complex Action set (118 actions):
- **Stability**: Generated files open in Hancom Office 2024 without corruption errors.
- **Fidelity**: Paragraph shapes and text flows are correctly preserved via the ID-reference mechanism.

## 6. Phase 11: Specialized Logic & Machine-Readable Models

Building upon the successful API integration, Phase 11 addresses complex structural requirements for workbooks (Multi-column layouts, borders) and ensures document portability via a Unified Document Model.

### 6.1 Unified Document Model (UDM)
To ensure documents are "Machine-Readable" as per the OWPML architecture analysis, a **UDM JSON Schema** (`lib/schemas/udm_schema.json`) was established. 
- **De-referencing**: The UDM resolves style IDs into actual property values (font family, size, margins) so that downstream AI/ETL processes do not need to parse `header.xml`.
- **Semantic Tagging**: Paragraphs are assigned a `semantic_type` (e.g., `ProblemNumber`, `Equation`, `Answer`) derived from style name and pattern analysis.

See [UDM Schema Specification](./udm_schema_spec.md) for full details.

### 6.2 Reusable Action Templates
To accelerate document reconstruction, a **Math Workbook Template Library** (`lib/templates/math_workbook.py`) was implemented.
- **Functional Composition**: Methods like `problem_header(num)` and `answer_box(text)` return `List[HwpAction]`, enabling declarative document assembly.
- **Declarative Layout**: Templates handle the complex task of calculating "Hanging Indents" (`left_margin: 20`, `indent: -20`) automatically.

See [Math Workbook Template Patterns](./math_workbook_template_patterns.md) for usage examples.

### 6.4 Specialized Control Elements (`hp:ctrl`)
A critical discovery during the Phase 12 Deep Audit was that high-level layout features like 다단(Multi-column) and 수식(Equations) are not mere paragraph attributes, but **Control Elements** nested within runs.

#### 6.4.1 Multi-Column Layout (`colPr`)
Simply injecting `columnBreak="1"` into a paragraph is insufficient for HWP to recognize a multi-column region. It requires a `colPr` (Column Properties) control:
- **XML Structure**: 
  ```xml
  <hp:run>
    <hp:ctrl>
      <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="2" sameSz="1" sameGap="850"/>
    </hp:ctrl>
  </hp:run>
  ```
- **Nesting**: This control is typically placed in the first paragraph of a section, immediately following the `<hp:secPr>`.

#### 6.4.2 Native Equations (`hp:eqEdit`)
Native rendering of mathematical formulas requires the `<hp:eqEdit>` element within a control block:
- **XML Structure**:
  ```xml
  <hp:run>
    <hp:ctrl>
      <hp:eqEdit version="2" baseLine="850">
        <hp:script>x^{2} + y^{2} = r^{2}</hp:script>
      </hp:eqEdit>
    </hp:ctrl>
  </hp:run>
  ```
- **Script Syntax**: Uses a LaTeX-like but proprietary syntax. 
    - **Core Operators**: `OVER` (fraction), `SQRT` (root), `^` (sup), `_` (sub).
    - **Advanced Layout**: `PILE`/`LPILE` (stacking), `CASES` (conditional), `EQALIGN`/`&` (alignment), `MATRIX` (matrix).
    - **Special Symbols**: `SUM`, `INT`, `lim`, `Alpha`, `pi`, `therefore`, `neq`.
    - **scoping**: Uses `{ }` for grouping and `LEFT(`/`RIGHT)` for dynamic brackets.
- **Conversion Workflow**: The pipeline utilizes a specialized `LatexToHwpConverter` to map standard LaTeX math string patterns to the proprietary token set (e.g., `\\frac` → `OVER`, `\\sqrt` → `SQRT`) prior to XML injection.
- **Constraints**: Text placeholders or standard MathML do not trigger the native HWP renderer.

### 6.5 KS X 6101 Compliance & Native Mastery
To avoid "Whack-A-Mole" debugging, the pipeline now enforces a **Spec-First** approach:
- **Reference**: All XML modifications must align with the **KS X 6101** national standard.
- **Native Implementation**: Features must use native OWPML capabilities (Controls, Fields, Shapes) rather than simulation via text or paragraph flags.
- **State Tracking**: The `HwpxDocumentBuilder` tracks internal state (bold, size) and maps it to the `header.xml` ID-reference system for high-fidelity output.

See [KS X 6101 Native Capabilities](../implementation/ks_x_6101_native_capabilities.md) and [HWP Equation Script Reference](../implementation/hwp_equation_script_reference.md) for deeper technical mapping.
## 7. Production Readiness & Functional Pureness

Following the Phase 12 verification, the repository was sanitized to maintain a **"Functional Pureness"** standard.

### 7.1 Sanitization Protocol
Before finalizing the pipeline for production/deployment:
1.  **Artifact Removal**: All intermediate test files (`*.hwpx`, `*.json`) and debug logs must be removed.
2.  **Environment Cleanup**: Remove installation artifacts (e.g., `.deb` files) and Windows metadata (`Zone.Identifier`).
3.  **Template Integrity**: Preserve only non-generated, required templates like `Skeleton.hwpx`.

### 7.2 Functional Persistence
Only core library code (`lib/`), essential scripts (`scripts/`), and documentation remain in the repository. This ensures the pipeline is zero-noise and ready for integration into larger systems (e.g., Palantir OSDK).

See [Pilot Trace](./pilot_test_execution_math.md) for the final verification metrics.
