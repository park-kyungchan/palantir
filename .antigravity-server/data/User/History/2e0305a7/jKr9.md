# Audit: Math Workbook Semantic Patterns & Layout Logic Gap

This document analyzes the semantic structures present in generated `HwpAction` sequences for math workbooks and identifies the current limitations in layout detection.

## 1. Identified Semantic Patterns (from `output_actions.json`)

Based on the analysis of 123 actions generated from `sample.pdf`, the following patterns were identified for reusable templates:

### 1.1 Problem Numbering (Hanging Indents)
Problem numbers use a specific paragraph shape to achieve the "hanging" effect where the number is aligned to the left of the main text block.
- **Pattern**: `{"action_type": "SetParaShape", "left_margin": 20, "indent": -20, ...}`
- **Usage**: Immediately followed by `{"action_type": "InsertText", "text": "4. "}`.
- **Visual Result**: The "4." block is positioned in the left indentation space.

### 1.2 Sub-Problem Numbering
Follows a similar pattern to main problems but often nested within the same logical flow.
- **Pattern**: `(1)`, `(2)`, etc.
- **Style**: Shares the same hanging indent pattern (`left_margin: 20`, `indent: -20`).

### 1.3 Answer Formatting (Emphasis)
The pipeline identifies specific text runs (often at the end of problem sequences) as answers and applies visual emphasis.
- **Action Sequence**:
  1. `SetFontBold(is_bold=true)`
  2. `SetFontSize(size=14.0)`
  3. `InsertText(text="701")`
  4. `SetFontBold(is_bold=false)`
  5. `SetFontSize(size=10.0)`

### 1.4 Equation Integration
Equations are interleaved with text using LaTeX-style scripts.
- **Pattern**: `{"action_type": "InsertEquation", "script": "x^{2}+x-1=0"}`.
- **Technical Requirement**: Must be wrapped in `<hp:ctrl><hp:eq ... /></hp:ctrl>`. Simple text placeholders are insufficient for native HWP rendering.

---

## 2. Critical Audit: Layout Logic Gap

Despite high-fidelity content extraction (OCR/Math), the current parsing pipeline lacks **Structural Layout Awareness** for complex workbook containers.

### 2.1 The Container Box (Border)
- **Observed in `sample.pdf`**: Problems 4-9 are enclosed within a single black solid border box.
- **Missing Action**: The pipeline failed to generate a `CreateTable` or `SetBorder` action to encapsulate these problems.
- **Requirement**: Use a 1x1 table with `solid` borders as a structural container.

### 2.2 Multi-Column Flow (2-Column Layout)
- **Observed in `sample.pdf`**: A 2-column layout where Problems 4, 5, 6 are in the left column and 7, 8, 9 are in the right column.
- **Parsing Failure**: The OCR/Parser flattened the document into a single-column sequence (`4 -> 5 -> 6 -> 7 -> 8 -> 9`).
- **Technical Gap**: Identified that OWPML requires a `<hp:colPr>` control element within a `<hp:run>` for multi-column regions to be recognized and rendered by Hancom Office.

### 2.3 Structural Alignment Gap
The current "Sequential Parsing" approach (Top -> Bottom) is insufficient for workbooks. 
- **Solution**: The pipeline must transition to a **Grid-First Reconstruction** where the layout engine first identifies the container (Box) and its partitions (Columns) before populating them with content.

## 3. Recommended HwpAction Template for Workbooks

```json
[
  // 1. Create Container Table
  {"action_type": "CreateTable", "rows": 1, "cols": 1, "border_type": "solid"},
  {"action_type": "MoveToCell", "row": 0, "col": 0},
  
  // 2. Set Multi-Column Layout (or inner grid)
  {"action_type": "SetColumnLayout", "count": 2},
  
  // 3. Problem Block (Left Column)
  {"action_type": "SetParaShape", "left_margin": 20, "indent": -20},
  {"action_type": "InsertText", "text": "4. "},
  {"action_type": "InsertEquation", "script": "x^2 + x - 1 = 0"},
  
  // 4. Column Break (after Problem 6)
  {"action_type": "BreakColumn"}
]
```
