# Heuristic-Based Semantic Tagging

In specialized document domains like math workbooks, off-the-shelf layout detection models (e.g., DocLayout-YOLO) often provide generic categories (Text, Title, List) that do not distinguish between functional regions such as "Problems" and "Answer/Solution Boxes".

The `SemanticTagger` (`lib/layout/semantic_tagger.py`) solves this by post-processing raw `LayoutRegion` detections using content-based heuristics and spatial rules.

## 1. Tagging Logic Architecture

The tagger operates as a pipeline step immediately after raw detection and before reading order sorting. It refines the `LayoutLabel` of identified regions.

```python
# Workflow Integration (Correct Sequence)
regions = detector.detect(image)
# CRITICAL: Text must be populated for heuristic tagging
for r in regions:
    r.text = ocr_engine.extract(image, r.bbox) 

refined_regions = tagger.tag(regions) # <--- Heuristic Refinement (uses text)
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

### 2.4 Handling OCR Math Noise (LaTeX Interference)
In math workbook domains, OCR engines (like EasyOCR) often return text integrated with mathematical symbols at the very start of a region.
- **The Issue**: A problem starting with "7. $2^{x+1}$..." might be extracted as `7. (2? + 1)...`. If the regex `^\s*\d+\.\s+` is too strict about the following space or characters, it might fail.
- **Robust Pattern Strategy**:
    - Use broader numbering patterns (e.g., searching within the first 30 characters).
    - Incorporate "Fuzzy Keywords" that catch common OCR mis-transcriptions (e.g., `풀\s*이` to catch `풀 이` or `풀이`).
    - Use `re.search` instead of `re.match` for the first line to allow for leading OCR artifacts (like dots or stray marks).

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

### 3.3 Semantic Label Propagation (Hybrid Flow)
In the hybrid ingestion flow (using both Docling and DocLayout-YOLO), semantic labels must be explicitly propagated from detected `LayoutRegion`s to the natively identified `DocItem`s.

- **Matching Logic**: The `DoclingIngestor` uses an **Intersection over Union (IoU)** matching mechanism in `_match_and_reorder`.
- **Inheritance**: Any `DocItem` (Paragraph, Table, etc.) whose bounding box significantly overlaps with a semantically tagged `LayoutRegion` (e.g., `ANSWER_BOX`) inherits that label.
- **Implementation**: The matched label is passed to `_process_item`, which then sets the appropriate `style` on the resulting IR `Paragraph` or `Table` object. This ensures that even if Docling identifies the text, it receives the domain-specific semantic tagging provided by the YOLO+Heuristic layer.

### 3.4 Coordinate System Normalization (Top-Left vs. Bottom-Left)
A critical failure point in hybrid ingestion is the mismatch between coordinate systems:
- **YOLO Detection**: Operates on rendered images (Pixels, Top-Left origin).
- **Docling / PDF Standard**: Items are often defined in PDF points with a Bottom-Left origin (standard PDF) or Top-Left (PyMuPDF default).

In this pipeline, `LayoutDetector.detect_pdf_page` ensures alignment by:
1.  **Scaling**: Downsampling coordinates from the detection image (e.g., 2.0x zoom) back to PDF points.
2.  **Origin Alignment**: Explicitly converting `IMAGE` coordinate bboxes to `PDF` coordinate bboxes (flipping the Y-axis based on page height) to ensure that the Intersection over Union (IoU) calculation in `_match_and_reorder` compares overlapping regions accurately.

Without this normalization, IoU matching yields 0.0 overlap, causing semantic labels to be lost.

### 3.5 Resource Management (Closure Sequence Bug)
A subtle but critical bug was identified in the coordinate conversion workflow. When using `PyMuPDF` (fitz) to scale regions from Image-Space to PDF-Space:
- **The Issue**: Accessing `page.rect.height` (or any page property) after calling `doc.close()` triggers a `ValueError: page is None` or similar crash.
- **The Resolution**: Developers must cache the `page_height` *before* closing the document handle.
- **Implementation Pattern**:
  ```python
  page = doc[page_number]
  # ... render image ...
  page_height = page.rect.height # Cache height here
  doc.close()
  # Now safe to use page_height for coordinate flip
  pdf_bbox = img_bbox.to_pdf_coordinates(page_height)
  ```

### 3.6 Temporal Coupling (Text-Availability Requirement)
A significant integration challenge was identified during Phase 3 verification:
- **The Problem**: Raw `LayoutDetector` outputs (e.g., from `detect_pdf_page`) only contain geometric bounding boxes and generic labels; the `text` field is initially `None`.
- **The Constraint**: Since `PROBLEM_PATTERN` and `ANSWER_PATTERN` rely on regex matching against `region.text`, executing `tag()` immediately after detection results in 0 tags found.
- **The Solution**: The ingestion pipeline must perform **Segmented OCR** (extracting text for each identified region) *prior* to calling the `SemanticTagger`. Tagging is the final refinement step before mapping to IR.
- **Implementation Note (2-Pass Flow)**: 
    1. **Pass 1 (Extraction)**: Render and OCR each region to populate the `text` attribute.
    2. **Pass 2 (Refinement)**: Pass the text-populated list to `SemanticTagger.tag()`.
    3. **Pass 3 (Mapping)**: Construct IR elements using the refined labels.

### 3.7 Coordinate Symmetry in OCR Cropping
While `LayoutDetector` flips Y-coordinates from Image to PDF space for matching, the Ingestor must perform the **inverse flip** when cropping the rendered page image for OCR.
- **The PDF Coordinate**: `(rx0, ry0_pdf, rx1, ry1_pdf)` follows standard PDF/PyMuPDF logic.
- **The Image Coordinate**: Rendered pixmaps use a **Top-Left origin**.
- **Transformation Pattern**:
  ```python
  # Target top/bottom in image space
  img_y_top = page_height - pdf_y_bottom
  img_y_bottom = page_height - pdf_y_top
  # Resulting crop box (ignoring zoom/scaling for clarity)
  crop_box = (rx0, img_y_top, rx1, img_y_bottom)
  ```
Failure to apply this flip results in the ingestor cropping the Y-mirrored region of the page (e.g., cropping the footer when targeting the header), leading to empty OCR results and failed tagging.

These styles trigger specialized formatting in the **HWPX Compiler**, such as creating boxes with specific border properties or adjusting paragraph indentation.

## 4. Scaling and Customization

For different workbook formats, the `SemanticTagger` can be extended with:
- **Language-Specific Regex**: Adding patterns for "Problem 1", "Question A".
- **Visual Marker Detection**: Detecting checkbox icons or line patterns using secondary YOLO models or basic CV (Contour detection).
