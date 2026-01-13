# HWPX Engineering Manual: Reconstruction & Features

## 1. Architecture Overview

### 1.1 The Semantic-Visual DOM (SVDOM)
The SVDOM (defined in `lib/ir.py`) is a Hybrid JSON structure that enforces strict separation of concerns between Content, Style, and Geometry.
- **Section**: Page layout division supporting columns and page setup.
- **Paragraph**: Block of content with style attributes.
- **Tables**: Hierarchical grid (`Table` -> `TableRow` -> `TableCell`).
- **Controls**: Inline objects like Images, TextBoxes, and Equations.

### 1.2 IR-to-HWP Compiler (`lib/compiler.py`)
The `Compiler` translates SVDOM objects into a sequential list of HWP Actions (defined in `lib/models.py`). It uses a recursive dispatch logic and tracks formatting state to minimize API signal noise.

### 1.3 Stateful Document Assembly (DocumentBuilder)
The `HwpxDocumentBuilder` operates as a cursor-based state machine.
- **Context Tracking**: Monitors `_current_table`, `_current_cell`, and `_current_container` (active `hp:tc` or `section_elem`).
- **Style State**: Tracks active typography and layout settings (Size, Bold, Align) across multiple `InsertText` actions.

### 1.4 Quality Standards & Observability
Aligned with Orion ODA v6.0, the pipeline enforces strict observability:
- **No Silent Failures**: Bare `except: pass` blocks are prohibited.
- **Explicit Exceptions**: Specific error types (e.g., `ValueError`, `AttributeError`) must be caught and logged via `logger.debug`.
- **Traceability**: Crucial for parsing CSS-like font strings and table detection fallback logic.

---

## 2. Implementation Guide (Phases 1-15)

### 2.1 Dimensional Precision (KS X 6101)
- **Base Unit**: HwpUnit (1/7200 inch).
- **Formula**: 1 mm ≈ 283.46 HwpUnits; 1 pt = 100 HwpUnits.
- **Geometry**: Table widths use remainder distribution to ensure 100% conformance.

### 2.2 Shared Resource Management (HeaderManager)
- **Deduplication**: Composite keys for `charPr`, `paraPr`, and `borderFill` ensure style reuse.
- **ID Scavenging**: Scans `header.xml` to determine valid ID increments.

### 2.3 Structural Element Handling
- **Cell Merging**: Support for `<hp:cellSpan>` with logical coordinate tracking (`cellAddr`). HWPX prohibits "ghost cells".
- **Nested Tables**: Recursive structures enabled by container context injection into table paragraphe.
- **Advanced Lists**: 7-level hierarchical numbering linked via `numberingIDRef`.

---

## 3. High-Fidelity Features

### 3.1 Scientific Equations
Equations use a proprietary script format within `<hp:eqEdit>`.
- **Conversion**: LaTeX is transpilation via recursive regex in `lib/owpml/equation_converter.py`.
- **Placement**: Embedded within `<hp:ctrl>` inside a paragraph run.

### 3.2 Context-Aware Inline Controls
Images (`hp:pic`), TextBoxes (`hp:rect`), and Equations are re-routed to the active `_current_container`. This allows these objects to reside correctly within table cells.

### 3.3 Footnotes & Endnotes
Implemented via `<hp:footNote>` and `<hp:endNote>` controls.
- **Dynamic Content**: Uses a `<hp:subList>` container to host one or more paragraphs within the note.
- **Automation**: IDs are dynamically generated to ensure unique mapping within the document scope.

---

---

## 5. E2E Integration & Pipeline Unification

### 5.1 Convension Orchestrator Integration
The high-fidelity `HwpxDocumentBuilder` is now integrated as the primary conversion engine in `lib/pipeline.py`:
- **Interface Alignment**: `main.py` entry point correctly passes `use_mathpix` to the pipeline core.
- **Generator Swap**: Legacy `HWPGenerator` is bypassed in favor of `builder.build(self.compiler.actions, hwpx_output)`, enabling full structural support.

### 5.2 Case-Sensitive Style Resolution
- **Issue**: Standard HWP style keys are case-sensitive (e.g., "Center" vs "CENTER").
- **Fix**: Input alignment types are normalized to Title Case to match `HeaderManager` lookup tables.

---

## 6. E2E Pilot Test: `sample.pdf` (January 2026)

### 6.1 Validation Target
A complex math workbook (`sample.pdf`) containing:
- 2-column layouts (transparent tables).
- LaTeX-derived formulas.
- Multi-level numbering.

### 6.2 Results
- **Execution**: 54 HWP Actions generated.
- **Artifacts**: `output_pilot.hwpx` produced and verified.
- **Structural Integrity**: ZIP inspection of `section0.xml` confirmed high-fidelity XML nesting and correct `pagePr` margin application.
- **Digital Twin**: `output_pilot.py` correctly replicated indents and text flows using the `win32com` automation pattern.

**Status**: ✅ **E2E VALIDATED**

---

## 7. Programmatic Codebase Maintenance

When codebase modifications involve complex structural changes (e.g., resolving duplicate method stubs or deep indents), standard LLM replacement tools may conflict.

### 7.1 Automated Maintenance Protocol
- **Strategy**: Use standalone Python utility scripts (e.g., `scripts/fix_builder.py`) to parse and rewrite target files.
- **Workflow**:
    1. Identify structural corruption (e.g., triple-quoted string mismatch).
    2. Write script to locate specific line indices/blocks.
    3. Filter/Replace content using Python native string/list logic.
    4. Run regression suite (`tests/manual_verify_*.py`) to self-verify.

**Current Maintenance Status**: ACTIVE (Used during Phase 10 recursion fixes).

---

## 8. Post-Assembly Normalization

To ensure 100% compatibility with Hancom Office 2024, the pipeline utilizes a `package_normalizer` during the save phase.

### 8.1 ZIP Structure Enforcement
- **MIME Entry**: Forces `mimetype` to be the first, uncompressed entry in the ZIP bundle.
- **Manifest Integrity**: Validates `META-INF/manifest.xml` against the actual payload files.
- **Deterministic Ordering**: Sorts XML entries to ensure consistent checksums and load performance.

**Status**: ACTIVE (Integrated into `HwpxDocumentBuilder._save`).

---

## 9. IR Evolution & Integration Pitfalls

As the Intermediate Representation (IR) evolves to support more complex OWPML structures (e.g., Containers, Multi-column), structural changes to core classes (defined in `lib/ir.py`) can introduce regressions in Ingestors.

### 9.1 Attribute-to-Property Regressions
- **Scenario**: In January 2026, `Section.paragraphs` was converted from a list attribute to a read-only property to support a mixed-element `elements` storage.
- **Problem**: Ingestors using `section.paragraphs.append(...)` failed silently or produced empty documents because they type-checked against a temporary list returned by the property.
- **Resolution**: All ingestors must use `section.elements.append(Paragraph(...))` or the `section.add_paragraph()` factory method to ensure persistence in the IR.
- **Lesson**: Interface changes on core IR classes require a global search and update of all Ingestor implementations.
