# Implementation: Vision-Native Prompt Engineering

To bridge the gap between "Pixels" (PDF Images) and "Structure" (SVDOM JSON), the pipeline uses a highly prescriptive system prompt for Vision Models (e.g., Gemini 3.0 Pro).

## 1. Prompt Objectives

The prompt is designed to minimize hallucination and maximize structural fidelity by:
- **Strict Format Enforcement**: Requiring RAW JSON output only.
- **Visual-Semantic Labeling**: Forcing the model to distinguish between content `type` (what it physically is) and `role` (how it functions).
- **Spatial Reasoning**: Explicitly requesting bounding boxes (`bbox`) in a normalized percentage-based coordinate system.

## 2. Core Instructions (De-rendering Rules)

### 2.1 Visual Handling
The model is instructed to never merge "Body Text" with "Tables". Tables must be treated as structural 2D arrays, preserving the internal flow and headers.

### 2.2 Mathematical Parsing
A critical component of "High-Fidelity" is the de-rendering of formulas into **LaTeX**. The model is instructed to ignore OCR artifacts and prioritize the mathematical logic of the visual expression.

### 2.3 De-rendering Depth: "Atomic"
The prompt sets a parameter `[De-rendering Depth] = High`. This instructs the model to split every distinct visual block (paragraph, equation, cell) into a separate SVDOM `Block`. This prevents large, uneditable "mega-blocks" of text.

## 3. Usage Pattern

The prompt is stored in `prompts/vision_derender.md` and should be used in a "Sequential Execution" loop:
1.  **Pre-processing**: Convert PDF pages to high-DPI images.
2.  **Vision Call**: Send image + System Prompt to the Vision API.
3.  **Ingestion**: Validate the resulting JSON against the `DigitalTwin` Pydantic schema to ensure downstream reliability.

## 4. Vision-Native Derendering Engine (v3.0)

Version 3.0 introduces adjustable control parameters to fine-tune parsing behavior for complex layouts like math workbooks.

### 4.1 Configuration Parameters
- **[Visual_Dependency_Factor]**: (Range: 0.0 ~ 1.0). Current: `1.0` (Pure Vision). Ignores hidden text layers to favor visual fidelity.
- **[Spatial_Grid_Resolution]**: (Range: 100 ~ 1000). Current: `1000`. Pixel-perfect precision on a normalized coordinate grid.
- **[Derendering_Depth]**: (Range: Level 1 ~ 5). Current: `Level 5` (Deep Extraction). Transcribes text inside images and converts formulas to LaTeX.
- **[Layout_Strictness]**: (Range: 0.0 ~ 1.0). Current: `0.95`. Strictly preserves multi-column layouts and visual separators.

### 4.2 Functional Execution Protocol
1.  **Pixel-Level Extraction**: Append bounding boxes to every content block: `Content {bbox: [ymin, xmin, ymax, xmax]}`.
2.  **Deep Image Parsing**: Reverse-engineer visual data points from charts and perform full OCR on embedded images.
3.  **Table Reconstruction**: Detect implicit (invisible) grid lines based on pixel alignment and handle merged cells.

### 4.3 High-Fidelity Prompt (v3.0)
```markdown
### SYSTEM ROLE: Gemini Vision-Native Derendering Engine (v3.0)
**MISSION:** Perform high-fidelity "Derendering" of the attached PDF. Convert visual pixels directly into structured data without relying on embedded text layers (OCR-on-OCR strategy).

[Parameters as defined in 4.1]

#### 1. Pixel-Level Extraction (Coordinate Mapping)
- **Action:** For every extracted content block (Header, Table, Image), append its Bounding Box.
- **Format:** Content {bbox: [ymin, xmin, ymax, xmax]}

#### 2. Deep Image Parsing (Image-in-PDF)
- **Charts:** Reverse-engineer the visual data points into a JSON array.
- **Handwriting:** Transcribe exactly and tag with [Handwritten].

#### 3. Table Reconstruction
- Detect implicit (invisible) grid lines based on pixel alignment.
- Represent merged cells (rowspan/colspan) accurately.
```
