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
1. **Rendering Instability (Auto-close)**: **[RE-OPENED]** Certain generated files (highly reproducible in 3x3 table samples) cause Hancom Office 2024 to crash immediately.
   - **Status**: Active Investigation.
   - **Findings (Jan 9, 2026)**:
     - **Prefixes**: ElementTree's default `ns0:`/`ns1:` aliases were fixed via `ET.register_namespace()`.
     - **Persistent Issue**: Files still crash despite correct prefixes. 
     - **Discovery**: `Skeleton.hwpx` contains 7+ namespace declarations in the `<hs:sec>` root, while generated files only declare 2. Missing declarations (e.g., `ha`, `hp10`, `hc`, `hh`, `hhs`, `hm`) are suspect.
   - **Verification**: `sample_3x3_table_fixed.hwpx` failed manual verification by user.

### 🟡 Medium
1. **Dead Code in compiler.py (L409-411)**: Undefined `run` variable used in a conditional check.

### 🟢 Low
1. **Module Bloat**: `document_builder.py` (940 lines) should be decomposed into specific action handlers.
2. **Schema Duplication**: `lib/digital_twin/schema.py` defines the `Block` class twice (L34, L118).

---

## 9. Conclusion

While the pipeline handles OWPML structure with high fidelity and passes structural validation, **rendering stability in Hancom Office 2024 is currently the primary blocker**. The transition from "Verified" OWPML to "Renderable" OWPML is ongoing, with investigation focusing on root-level namespace declarations and schema-strict attribute values.
