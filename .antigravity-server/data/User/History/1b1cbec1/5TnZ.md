# Heuristic-Based Semantic Tagging

In specialized document domains like math workbooks, off-the-shelf layout detection models (e.g., DocLayout-YOLO) often provide generic categories (Text, Title, List) that do not distinguish between functional regions such as "Problems" and "Answer/Solution Boxes".

The `SemanticTagger` (`lib/layout/semantic_tagger.py`) solves this by post-processing raw `LayoutRegion` detections using content-based heuristics and spatial rules.

## 1. Tagging Logic Architecture

The tagger operates as a pipeline step immediately after raw detection and before reading order sorting. It refines the `LayoutLabel` of identified regions.

```python
# Workflow Integration
regions = detector.detect(image)
refined_regions = tagger.tag(regions) # <--- Heuristic Refinement
sorted_regions = sorter.sort(refined_regions)
```

## 2. Heuristic Rule Set

### 2.1 ProblemBox Detection (Pattern-Based)
Identifies the start of a mathematical problem.
- **Criteria**: Region label is `TEXT`, `SECTION_HEADER`, or `TITLE`.
- **Primary Heuristic**: Text content starts with a numbering pattern.
- **Regex Patterns**:
    - `^\s*(\d+[\.)]|\(\d+\)|\[\d+\])\s+`
    - Matches: "1. ", "5)", "(12) ", "[01] "
- **Action**: Change `LayoutLabel` to `PROBLEM_BOX`.

### 2.2 AnswerBox Detection (Keyword-Based)
Identifies regions intended for student solutions or providing answers.
- **Criteria**: Region label is `TEXT`.
- **Primary Heuristic**: Text content starts with specific Korean/English solution keywords.
- **Keywords**:
    - "풀이" (Solution)
    - "정답" (Answer)
    - "해설" (Explanation)
- **Action**: Change `LayoutLabel` to `ANSWER_BOX`.

### 2.3 Spatial AnswerBox Detection (Future/Planned)
In cases where an AnswerBox is empty (no text keywords) but spatially associated with a problem.
- **Heuristic**: Large white-space region located:
    - Below a `PROBLEM_BOX`.
    - To the right of a `PROBLEM_BOX` in a multi-column layout.
- **IoU Check**: High vertical overlap with the previous problem but distinct horizontal position.

## 3. Integration into Ingestors

### 3.1 DoclingIngestor Integration
The `SemanticTagger` is used in both the primary Docling path and the Vision-Native fallback.

- **Vision-Native Path**: Tags regions used for image cropping and OCR. This ensures that the `Paragraph` objects created for a `PROBLEM_BOX` are assigned the `"ProblemBox"` style in the IR.
- **Hybrid Path**: Refines the YOLO regions used to reorder and tag Docling's natively detected items.

### 3.2 IR Style Mapping
The semantic labels are preserved in the `Paragraph.style` field in the `lib.ir.Document`:
- `LayoutLabel.PROBLEM_BOX` -> `style="ProblemBox"`
- `LayoutLabel.ANSWER_BOX` -> `style="AnswerBox"`
- `LayoutLabel.SECTION_HEADER` -> `style="Header"`

These styles trigger specialized formatting in the **HWPX Compiler**, such as creating boxes with specific border properties or adjusting paragraph indentation.

## 4. Scaling and Customization

For different workbook formats, the `SemanticTagger` can be extended with:
- **Language-Specific Regex**: Adding patterns for "Problem 1", "Question A".
- **Visual Marker Detection**: Detecting checkbox icons or line patterns using secondary YOLO models or basic CV (Contour detection).
