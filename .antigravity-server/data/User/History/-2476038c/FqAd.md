# E2E Pipeline Logic Trace (January 2026)

This document provides a detailed trace of the HWPX Reconstruction Pipeline's data flow, as audited in January 2026.

## 1. Entry Point: `main.py`
The pipeline is invoked via `main.py`, which handles CLI arguments and initializes the orchestrator.

- **Inputs**: PDF file path, optional output path, `--no-ocr` flag.
- **Logic**:
  1. Validates input path.
  2. Resolves output JSON path (default: `{input}_actions.json`).
  3. Initializes `HWPXPipeline(use_mathpix=not args.no_ocr)`.
  4. Calls `pipeline.run(input_path, output_path)`.

## 2. Orchestration: `lib/pipeline.py` (`HWPXPipeline`)
The `HWPXPipeline` class manages the lifecycle of document conversion.

### 2.1 Initialization
- Selects **Ingestor**: `MathpixIngestor` (if OCR enabled) or `DoclingIngestor` (if OCR disabled).
- Selects **Parser**: `MarkdownParser` is used if Mathpix is the ingestor (to process MMD output).
- Initializes **Compiler**: `lib/compiler.py` for IR-to-Action translation.

### 2.2 Execution Flow (`run`)
1. **Ingestion**: `ingestor.ingest(input_path)` returns raw content (MMD string or internal Document object).
2. **Parsing**: If using Mathpix, `parser.parse(raw_output)` converts MMD to the **Intermediate Representation (IR)** defined in `lib/ir.py`.
3. **Compilation**: `compiler.compile(doc)` translates IR objects (Sections, Paragraphs, Tables) into a list of `HwpAction` models.
4. **Serialization**: Saves the list of action dictionaries to the output JSON file.
5. **OWPML Building**: If outputting HWPX, `HwpxDocumentBuilder.build(actions, output_path)` produces the final `.hwpx` file.

## 3. Data Transformation Trace

### 3.1 Intermediate Representation (`lib/ir.py`)
The IR acts as a "Digital Twin" of the document structure:
- `Document`: Root container.
- `Section`: Page layout divisions.
- `Paragraph`: Content blocks with `elements` (TextRun, Equation, Image, Table, Figure).
- `Container` / `MultiColumnContainer`: Support for complex absolute layouts and multi-column flows.

### 3.2 Action Compiler (`lib/compiler.py`)
The `Compiler` translates hierarchical IR into a sequential list of HWP Actions (Ontology-driven).
- **State Tracking**: Maintains context for current table, cell, and formatting.
- **Translation Logic**:
  - `_compile_paragraph` -> `InsertText`, `SetParaShape`.
  - `_compile_table` -> `CreateTable`, `MoveToCell`, etc.
  - `_compile_equation` -> `InsertEquation`.

### 3.3 HWPX Generation (`lib/owpml/document_builder.py`)
The `HwpxDocumentBuilder` maps HWP Actions to the **OWPML (KS X 6101)** XML schema.
- **Namespace Handling**: Correctly applies `hp`, `hs`, `hh` namespaces.
- **Cursor State Machine**: Simulates the HWP cursor within the XML structure (e.g., using `<hp:subList>` for nested content).
- **Packaging**: Uses `normalize_hwpx_package` to ensure ZIP structure compatibility with Hancom Office 2024.

## 4. Component Directory Mapping (Stage A Audit)

| Directory | Responsibility |
|---|---|
| `lib/ingestors/` | Engine-specific PDF/Image extraction (Mathpix, Docling, Surya, PyMuPDF). |
| `lib/parsers/` | Converts engine-specific output (e.g., Markdown) to IR. |
| `lib/owpml/` | Low-level OWPML XML construction and HWPX packaging logic. |
| `lib/layout/` | Structural analysis for absolute positioning and column detection. |
| `lib/math/` | Tools for LaTeX and HWP Script conversion. |
| `scripts/` | Validation and verification utilities for pipeline stages. |
| `docs/` | Technical references and automation manuals for the AI agent. |
