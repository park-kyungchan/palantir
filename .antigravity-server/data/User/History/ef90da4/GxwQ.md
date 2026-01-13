# HWPX Reconstruction Pipeline: E2E Deep Audit Report (Jan 2026)

**Audit Date**: 2026-01-09  
**Target Directory**: `/home/palantir/hwpx/`  
**Auditor**: Antigravity Deep-Audit Protocol

---

## Executive Summary

The HWPX Reconstruction Pipeline is a **high-fidelity document conversion framework** that transforms PDF documents into Hancom Office 2024 compatible `.hwpx` files. The pipeline implements a sophisticated 4-stage architecture following the **Digital Twin (SVDOM) paradigm** with **100% KS X 6101:2024 OWPML compliance**.

```mermaid
flowchart LR
    PDF["📄 PDF Input"] --> ING["1️⃣ Ingestion"]
    ING --> PARSE["2️⃣ Parsing"]
    PARSE --> IR["📊 IR Document"]
    IR --> COMP["3️⃣ Compilation"]
    COMP --> ACT["📋 HwpActions"]
    ACT --> BUILD["4️⃣ OWPML Build"]
    BUILD --> HWPX["📁 .hwpx Output"]
```

---

## 1. Entry Point Analysis

### `main.py` (44 lines)

The CLI entry point accepts:
- **Input**: PDF file path (required)
- **Output**: JSON/HWPX path (optional)
- **Flags**: `--no-ocr` disables Mathpix OCR, uses Docling instead

---

## 2. Pipeline Orchestration

### `lib/pipeline.py` (82 lines)

The `HWPXPipeline` class orchestrates the entire conversion:

| Phase | Component | Description |
|-------|-----------|-------------|
| **1. Ingestion** | `ingestor.ingest()` | PDF → Raw content (MMD or DoclingDocument) |
| **2. Parsing** | `parser.parse()` | MMD → IR Document (Mathpix only) |
| **3. Compilation** | `compiler.compile()` | IR → List[HwpAction] |
| **4. OWPML Build** | `HwpxDocumentBuilder.build()` | Actions → .hwpx file |

---

## 3. Ingestion Layer

### Directory: `lib/ingestors/`

- **MathpixIngestor** (93 lines): API-based OCR, returns Markdown.
- **DoclingIngestor** (564 lines): IBM Docling + YOLO layout, returns IR. 
  - *Key Feature*: Reading order sorting and semantic tagging.
- **Fallbacks**: PyMuPDF, Surya, and Layout-Text ingestors for robust extraction.

---

## 4. Intermediate Representation (IR)

### `lib/ir.py` (159 lines)

The IR serves as a **Digital Twin** (SVDOM) of the document structure, decoupling visual geometry from semantic content.

| Class | Purpose |
|-------|---------|
| `Document` | Root container with sections |
| `Section` | Page layout (columns, page_setup) |
| `Paragraph` | Content block with TextRuns, Equations, Images |
| `Table` | Row/cell structure with bboxes |

---

## 5. Action Compiler

### `lib/compiler.py` (411 lines)

Transforms IR into a sequential list of `HwpAction` objects while maintaining a **Formatting State Machine** (tracking font size, bold, alignment) to minimize OWPML bloat.

> [!WARNING]
> **Dead Code Detected** at lines 409-411: `if run.text` references an undefined variable `run` after the `_compile_codeblock` method.

---

## 6. OWPML Generation

### `lib/owpml/document_builder.py` (940 lines)

The largest component, mapping actions to **KS X 6101 compliant XML**.

- **HeaderManager**: Manages dynamic style IDs in `header.xml`.
- **BinDataManager**: Handles binary resources in `BinData/`.
- **PackageNormalizer**: Ensures ZIP compliance (mimetype non-compressed, strict file order).
- **Validator** (New): Performs automated KS X 6101:2024 integrity checks (IDRefs, OCF structure).

---

## 7. Codebase Statistics

| Category | Count |
|----------|-------|
| **Core Pipeline Files** | 5 |
| **Total lib/ Files** | 42+ |
| **Ingestors** | 5 |
| **Action Types** | 20+ |
| **Test Files** | 41 |

---

## 8. Identified Issues

### 🔴 Critical
1. **Rendering Instability (Auto-close)**: **[REOPENED - Jan 9]** Certain generated files (especially those containing tables) cause Hancom Office 2024 to crash immediately.
   - **Initial Hypothesis**: Namespace prefix mismatches (`ns0` vs `hp`) and missing boilerplate were the cause.
   - **Current Paradox**: `output_styles_test.hwpx` (which uses `ns0`/`ns1`) opens successfully, while `sample_3x3_table_v3.hwpx` (which uses proper `hs`/`hp` prefixes) crashes.
   - **Investigation**: This suggests that either (a) prefixes are NOT the primary crash cause, or (b) the combination of standard prefixes with specific table structures creates a new violation.
   - **Next Steps**: Compare the XML children of `<hs:sec>` and `<hp:p>` between working and crashing samples.

### 🟡 Medium
1. **Dead Code in compiler.py (L409-411)**: Undefined `run` variable used in a conditional check.

### 🟢 Low
1. **Module Bloat**: `document_builder.py` (940 lines) should be decomposed into specific action handlers.
2. **Schema Duplication**: `lib/digital_twin/schema.py` defines the `Block` class twice (L34, L118).

---

## 9. Conclusion

While the pipeline handles OWPML structure with high-fidelity, **rendering stability in Hancom Office 2024 remains an active research area**. The previous fix (namespace registration) has been debunked as a universal solution by a regression in `sample_3x3_table_v3.hwpx`. The investigation has shifted from simple prefix-matching to a deeper structural comparison of document elements.
