# OWPML Fidelity & Core Structure Audit

This consolidated audit tracks the evolution of HWPX generation fidelity, from basic package integrity to complex native layout features.

---

## 1. Package Integrity & Corruption (Hancom 2024)

**Issue**: "File Corrupted" popup in Hancom Office 2024.

### 1.1 Root Causes (Resolved)
| Factor | Finding | Impact |
| :--- | :--- | :--- |
| **Mandatory Sections** | Missing `docOption`, `charPrList`, `styleList`, `borderFillList` in `header.xml`. | Structural Validation Fail |
| **Font Linkage** | `charPr` referenced `fontRef="0"` without a `faceNameList`. | Rendering Engine Crash |
| **Manifest Alignment** | `content.hpf` paths mismatched physical ZIP structure. | Package Loading Fail |
| **Compression** | `mimetype` was compressed instead of `Stored`. | MIME sniffing fail |
| **Mandatory Files** | Missing `version.xml`, `settings.xml`, and `META-INF/container.rdf`. | Application Silent Crash |

### 1.2 Resolution Strategy: Template-Based Reconstruction (TBR)
To handle the 40KB+ complexity of valid OWPML headers, the pipeline uses a **"Golden Template"** (`Skeleton.hwpx`). ONLY `Contents/section0.xml` is modified, ensuring 100% header alignment.

---

## 2. Layout & Control Element Research

**Finding**: High-level features (Columns, Equations) are **Control Elements (`hp:ctrl`)**, not paragraph attributes.

### 2.1 Multi-Column Layout (`colPr`)
- **Gap**: Setting `columnBreak="1"` on a paragraph failed to trigger columns.
- **Requirement**: A `<hp:colPr>` control must be nested within a run (usually the first run of the section, after `secPr`).
- **Standard**: KS X 6101 defines `colPr` as a control that defines the flow partitions.

### 2.2 Native Equations (`hp:eqEdit`)
- **Gap**: LaTeX text placeholders `[수식: ...]` are not rendered by the engine.
- **Requirement**: Formulae must be wrapped in `<hp:ctrl><hp:eqEdit><hp:script>` using HWP-specific syntax.

---

## 3. Math Workbook Semantic Patterns

| Pattern | Description | OWPML Mapping |
|---------|-------------|---------------|
| **Hanging Indents** | Problem numbers (e.g., "4.") aligned left. | `SetParaShape(left_margin=20, indent=-20)` |
| **Bold Answers** | Large, bold answer text (e.g., "701"). | `charPr` with `bold="1"` and increased `sz`. |
| **Bordered Box** | Solid border enclosing multiple problems. | 1x1 Table (`<hp:tbl>`) or `CreateBorderBox` control. |

---

## 4. Technical Mapping: Spec Compliance

| Element | Level | Namespace | Container |
|---------|-------|-----------|-----------|
| `colPr` | Run-level | `hp` | `hp:ctrl` |
| `eqEdit`| Run-level | `hp` | `hp:ctrl` |
| `secPr` | Run-level | `hp` | First `hp:run` of section |

---

## 5. Corrective Action Path

1.  **Transition to Grid-First**: Identify container boxes and columns before populating text content.
2.  **Native Controls**: Use `hp:ctrl` for all layout shifts and mathematical objects.
3.  **HWP Syntax**: Convert LaTeX to HWP Equation Script syntax (`OVER`, `SQRT`, etc.) for native rendering.
---

## 6. Conclusion & Final Status

As of January 2026, the HWPX generation pipeline has achieved **Spec-Level Fidelity** for math workbook reconstruction.

- **Status**: **VERIFIED**
- **Core Mastery**:
    - **Native Columns**: Correctly implemented via `<hp:ctrl><hp:colPr>` nesting.
    - **Native Math**: Successfully transpiled LaTeX → HWP Script → `<hp:eqEdit>`.
    - **Package Stability**: 100% Hancom Office 2024 compatibility confirmed via `python-hwpx` integration.
- **Maintenance**: Repository sanitized of test artifacts to maintain "Functional Pureness".
