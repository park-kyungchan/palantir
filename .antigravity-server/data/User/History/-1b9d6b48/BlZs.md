# Markdown (MMD) Parsing to IR

## Overview
The `MarkdownParser` (`lib/parsers/markdown_parser.py`) is the bridge between Mathpix's Markdown output (MMD) and the pipeline's internal Intermediate Representation (IR).

## 1. Parsing Logic
The parser uses a regular expression-based state machine to identify document structure and inline elements.

### 1.1 Structural Blocks
- **Headings (`#`, `##`, etc.)**: Mapped to `Paragraph` objects with a `"Header"` style.
- **Paragraphs**: Sequences of text separated by newlines.
- **Semantic Tagging**: The parser applies the same heuristic patterns as the `SemanticTagger` to assign styles:
    - **ProblemBox**: `^\s*(\d+\s*\.|\(?\d+\)?)` (e.g., "7.", "(1)")
    - **AnswerBox**: `^\s*(정답|답)`

### 1.2 Inline Elements
The parser tokenizes lines into atomic elements using a priority-based regex split:
1. **Display Math (`$$...$$`)** -> `IREquation`
2. **Images (`![alt](url)`)** -> `IRImage` (Detects and extracts remote URLs)
3. **Inline Math (`$...$`)** -> `IREquation`
4. **Bold Text (`**...**`)** -> `IRTextRun(is_bold=True)`
5. **Regular Text** -> `IRTextRun`

#### 1.2.1 Image Parsing Implementation
The parser handles images by identifying the `IMAGE_PATTERN` using a regex split that preserves capturing groups:
- **Structure**: `['text_before', 'alt_text', 'image_url', 'text_after']`
- **Recursive Processing**: Text fragments around images are recursively passed to math and bold parsers to ensure nested formatting (like bold text next to an image) is preserved.

## 2. Advantages over Raw OCR
By parsing structured Markdown instead of raw bounding boxes:
- **Logical Flow**: Mathpix already determines reading order and table structures.
- **Formatting Preservation**: Bold icons and italic math are explicitly flagged in MMD.
- **Robustness**: Reduces the complexity of the `IR Mapping` stage as much of the de-rendering is handled by Mathpix.

## 3. Implementation Detail: IR Schema Alignment
During implementation, a conflict was identified between the legacy IR names (e.g., `IRTextRun`) and the runtime IR classes (e.g., `TextRun` in `lib/ir.py`).

- **Resolution**: `lib/parsers/markdown_parser.py` uses explicit aliases and type-matching:
  ```python
  from lib.ir import Document, Section, Paragraph, TextRun, Equation, Image
  IRTextRun = TextRun  # Alias for backward-compatible consumption logic
  IREquation = Equation
  ```
- **Structural Integrity**: It was identified that `lib.ir.Section` uses `elements` for its child collection, not `paragraphs`. The parser was updated to use `current_section.elements.append(para)`.
- **Benefit**: Ensures the parser remains compatible with the `Compiler` which expects these specific class types for its `isinstance` checks and the correct attribute names.

## 4. Future Enhancements
- **Table Support**: Implement GFM table parsing to `IRTable`.
- **Advanced Layouts**: Parsing complex LaTeX-style column indicators from MMD metadata.
