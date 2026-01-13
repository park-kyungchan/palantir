# HWPX Technical Audit: KS X 6101 OWPML Specification

> **Date:** January 7, 2026
> **Target:** `docs/ks-x-6101-owpml.md`
> **Scope:** Compliance for Programmatic Control

## 1. Executive Summary
The audit confirmed that the OWPML (Open Word Processor Markup Language) standard (KS X 6101:2018) provides a robust, fully documented XML framework suitable for AI-driven programmatic document generation. The core strengths are its deterministic measurement unit (HwpUnit) and clear hierarchical structure (ZIP/OCF).

## 2. Key Technical Findings

### 2.1 Measurement System (HwpUnit)
- **Base Unit**: 1/7200 inch.
- **Conversion Constants**: 
  - 1 mm ≈ 283.46 HwpUnit
  - 1 pt = 100 HwpUnit
- **Usage**: Mandatory for all coordinates (X, Y) and dimensions (width, height, margins).

### 2.2 Table Schema (`hp:tbl`)
- **Cell Merging**: Handled by `<hp:cellSpan>` within `<hp:tc>`.
- **Constraint**: No "empty" or "ghost" cells should exist in the XML for merged regions. The row's `<hp:tc>` count must strictly match the visual cell count.
- **Addressing**: `<hp:cellAddr>` defines the logical row/col index.

### 2.3 Control Objects (`hp:ctrl`)
- **Images (`hp:pic`)**: Must reference `BinData/` items. Requirements include `<hp:originalSize>` and `<hp:curSize>`.
- **Shapes (`hp:rect`, `hp:polygon`, etc.)**: Complex drawing objects with their own sub-namespaces. Used for text boxes and callouts.

### 2.4 Packaging (OCF)
- **ZIP Ordering**: The `mimetype` file MUST be the first entry, uncompressed (`Stored`).
- **Required Parts**: `version.xml`, `META-INF/container.xml`, `Contents/content.hpf`, `Contents/header.xml`, `Contents/section0.xml`.

## 3. Implementation Gaps & Actions

| Finding | Impact | Action | Status |
| :--- | :--- | :--- | :--- |
| Missing `python-hwpx` dependency | Code fails in fresh environments. | Add to `requirements.txt`. | ✅ FIXED |
| Hardcoded ID References | Prevents multiple unique styles. | Implement `HeaderManager` (Phase 2). | ✅ FIXED |
| Missing Image Handler | No visual image support. | Implement `InsertImage` (Phase 6). | 📅 PLANNED |
| Missing Shape Handler | No text box support. | Implement `InsertTextBox` (Phase 6). | 📅 PLANNED |

## 4. Verification Results
- **Environment**: `python-hwpx>=0.0.19` installation verified.
- **OCF Compliance**: `python-hwpx` library defaults to correct ZIP ordering for `mimetype`.
- **Unit Logic**: `lib/owpml/units.py` verified against spec constants.
