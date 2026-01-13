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
2. **Inline Math (`$...$`)** -> `IREquation`
3. **Bold Text (`**...**`)** -> `IRTextRun(is_bold=True)`
4. **Regular Text** -> `IRTextRun`

## 2. Advantages over Raw OCR
By parsing structured Markdown instead of raw bounding boxes:
- **Logical Flow**: Mathpix already determines reading order and table structures.
- **Formatting Preservation**: Bold icons and italic math are explicitly flagged in MMD.
- **Robustness**: Reduces the complexity of the `IR Mapping` stage as much of the de-rendering is handled by Mathpix.

## 3. Future Enhancements
- **Table Support**: Implement GFM table parsing to `IRTable`.
- **Image Handling**: Map `![img](...)` to `IRImage` while potentially downloading assets from Mathpix's temporary storage.
