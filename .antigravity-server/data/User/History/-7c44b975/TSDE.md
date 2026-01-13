# HWPX Core: Reconstruction, SVDOM, & Ontology

This document details the Intermediate Representation (IR) and the translation logic that powers the document reconstruction engine.

## 1. The Semantic-Visual DOM (SVDOM)
The SVDOM (defined in `lib/ir.py`) is a Hybrid JSON structure that enforces strict separation of concerns between Content, Style, and Geometry.

### 1.1 Core Components
- **Document**: Root object containing `Section` objects.
- **Section**: Page layout division supporting columns and page setup.
- **Paragraph**: Block of content with style attributes (alignment, line spacing).
- **TextRun**: Continuous string with specific formatting (font, bold, spacing).
- **Equation**: Math formula (LaTeX or HWP script).
- **Container**: Generic layout box (Text Box) with absolute (x, y) positioning.
- **Tables**: Hierarchical grid (`Table` -> `TableRow` -> `TableCell`).

## 2. IR-to-HWP Compiler (`lib/compiler.py`)
The `Compiler` translates SVDOM objects into a sequential list of HWP Actions.

### 2.1 Recursive Dispatch Logic
The compiler uses a recursive method stack:
- `_compile_section` -> `_compile_element`
- `_compile_paragraph` -> `_compile_run` / `_compile_equation`
- `_compile_table` -> `_compile_element` (recursion)

### 2.2 Formatting Optimization
To minimize API noise, the compiler tracks formatting state (Font size, Bold). It only emits `SetFontSize` or `SetFontBold` when a `TextRun` deviates from the current compiler state.

## 3. HWP Action Ontology (`lib/models.py`)
A comprehensive set of 27 Pydantic models defining the submission criteria for Hancom reconstruction.

### 3.1 Formatting & Text
- `InsertText`, `SetFontSize`, `SetFontBold`, `SetLetterSpacing`, `SetLineSpacing`, `SetAlign`, `SetParaShape`, `BreakPara`, `InsertCaption`.

### 3.2 Tables
- `CreateTable`, `MoveToCell`, `SetCellBorder`.

### 3.3 Layout
- `MultiColumn`, `BreakColumn`, `BreakSection`, `SetPageSetup`, `InsertTextBox`, `CreateBorderBox`.

### 3.4 Specialized
- `InsertEquation`, `InsertImage`, `InsertCodeBlock`, `Figure`.

### 3.5 Automation
- `Open`, `FileSaveAs`, `MoveToField`.

## 4. Semantic Mapping Patterns
- **ProblemBox**: Mapped to `Paragraph` with `SetParaShape` (Hanging Indent).
- **AnswerBox**: Mapped to a 1x1 Invisible Table to ensure strict bounding.
- **Header**: Mapped to Bold runs with increased font size.
