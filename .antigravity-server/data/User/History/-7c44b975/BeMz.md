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
- **InsertText**: Inserts plain text at the cursor position.
- **SetFontSize**: Adjusts font size in points.
- **SetFontBold**: Toggles bold formatting (True/False).
- **SetLetterSpacing**: Adjusts "Ja-gan" (spacing between characters).
- **SetLineSpacing**: Adjusts "Jul-gan-gyeok" (percentage).
- **SetAlign**: Sets paragraph alignment (Left, Center, Right, Justify).
- **SetParaShape**: Complex paragraph shaping (margins, indentation, heading type).
- **BreakPara**: Inserts a new paragraph break.
- **InsertCaption**: Adds a caption to the currently selected object.

### 3.2 Tables
- **CreateTable**: Creates a grid with specified rows and columns.
- **MoveToCell**: Navigates the cursor to a specific (row, col) within a table.
- **SetCellBorder**: Sets border style, width, and color for selected cells.
- **MergeCells**: Merges table cells using logical coordinates (`cellSpan`).

### 3.3 Layout & Structure
- **MultiColumn**: Defines a multi-column layout (count, gap).
- **BreakColumn**: Forces a "Dan-nanugi" (column break).
- **BreakSection**: Forces a "Gu-yeok-nanugi" (section break), enabling different layouts on the same page.
- **SetPageSetup**: Configures paper margins and orientation.
- **InsertTextBox**: Creates a floating "Gle-sang-ja" with absolute positioning.
- **CreateBorderBox**: Wraps content in a decorative border box.

### 3.4 Specialized & Multimedia
- **InsertEquation**: Injects a math formula using LaTeX or HWP EQ script.
- **InsertImage**: Embeds an image file with sizing and "treat-as-character" options.
- **InsertCodeBlock**: Specialized container for source code with language tagging.
- **Figure**: Represents a complex graphical container.

### 3.5 Automation & Navigation
- **Open**: Opens an existing document (PDF, HWPX, HWP).
- **FileSaveAs**: Saves the current document in a target format.
- **MoveToField**: Navigates to a "Click Here" field/Named field for partial updates.

## 4. Semantic Mapping Patterns
- **ProblemBox**: Mapped to `Paragraph` with `SetParaShape` (Hanging Indent).
- **AnswerBox**: Mapped to a 1x1 Invisible Table to ensure strict bounding.
- **Header**: Mapped to Bold runs with increased font size.
