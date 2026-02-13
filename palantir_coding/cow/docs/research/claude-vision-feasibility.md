# Claude Opus 4.6 Vision Feasibility Study: Korean Math Document Analysis

**Date:** 2026-02-09
**Researcher:** Claude Opus 4.6 (Researcher Agent)
**Scope:** Evaluate Claude Opus 4.6 vision capabilities for replacing or complementing Gemini in the COW pipeline (Korean mathematical document processing)

---

## Executive Summary

Claude Opus 4.6 **cannot replace Gemini** for bounding box detection and spatial layout analysis in Korean math documents. Anthropic's official documentation explicitly acknowledges limited spatial reasoning capabilities. However, Claude provides **significant complementary value** for semantic analysis, mathematical reasoning, error detection, and cross-modal alignment — stages where Gemini is weaker.

**Recommendation: Hybrid architecture** — Gemini for spatial/coordinate tasks (Stage C), Claude for semantic/reasoning tasks (Stages D, E, F).

---

## 1. Image Understanding Capabilities

### 1.1 Supported Formats and Limits

| Parameter | Value |
|-----------|-------|
| Formats | JPEG, PNG, GIF, WebP |
| Max image size | 8000x8000 px (2000x2000 if >20 images per request) |
| Max file size | 5MB (API), 10MB (claude.ai) |
| Images per request | Up to 100 (API), 20 (claude.ai) |
| Optimal long edge | 1568 px (beyond this, auto-downscaled) |
| Token cost formula | `(width_px * height_px) / 750` |
| Cost per 1K images (1MP) | ~$4.00 at $3/M input tokens |

**Source:** [Anthropic Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision)

### 1.2 What Claude Can Do Well

- **Chart and graph interpretation**: Reads axis labels, understands what is being measured, interprets relationships between values, explains chart meaning in context
- **Technical diagram analysis**: Processes flowcharts, architecture diagrams, process flows through step-by-step reasoning about component interactions
- **Cross-reference understanding**: Connects figures to descriptions in text, explains how visual elements support claims
- **Multi-page document reasoning**: Images processed sequentially; can link methodology descriptions to corresponding figures across pages
- **Following complex instructions**: Compare charts, identify inconsistencies between text and figures, perform structured visual analysis

### 1.3 Korean Text Recognition (OCR)

- Claude achieves approximately **90% general OCR accuracy** (vs Gemini's 94%)
- No specific Korean math document benchmarks exist in published literature
- Gemini is acknowledged as stronger for non-English/Asian language OCR due to native multilingual training across 100+ languages
- For high-accuracy Korean math OCR, **Mathpix remains the gold standard** (and is already integrated in COW pipeline Stage B)

### 1.4 Mathematical Notation Recognition

- Claude can interpret mathematical expressions from images and describe their meaning
- Can convert visual math to LaTeX descriptions in natural language
- No published accuracy benchmarks specifically for image-to-LaTeX conversion
- For structured, high-accuracy math OCR, Mathpix (already in pipeline) significantly outperforms any VLM

---

## 2. Bounding Box / Spatial Reasoning

### 2.1 Claude's Limitations (CRITICAL)

Anthropic's official documentation states explicitly:

> "Claude's spatial reasoning abilities are limited. It may struggle with tasks requiring precise localization or layouts, like reading an analog clock face or describing exact positions of chess pieces."

**Key findings:**

| Capability | Claude Opus 4.6 | Status |
|-----------|-----------------|--------|
| Native bounding box output | NO | Not trained for coordinate output |
| Pixel-level coordinates | NO | No structured coordinate format |
| Consistent spatial output | NO | Coordinates vary between runs |
| Normalized coordinate format | NO | No standard like Gemini's [0-1000] |
| Multi-element layout detection | PARTIAL | Can describe relative positions verbally |
| Spatial relationship reasoning | WEAK | Verbal only ("A is above B"), no numeric |

### 2.2 Prompt-Engineered Workaround (Unreliable)

Community projects (e.g., [Claude Vision Object Detection](https://github.com/Doriandarko/Claude-Vision-Object-Detection)) have attempted to extract bounding boxes by:

1. Prompting Claude to return JSON with `[x1, y1, x2, y2]` normalized coordinates
2. Using strict format enforcement: "Output MUST be valid JSON"
3. Post-processing: converting normalized [0-1] coordinates to pixel values

**Result: UNRELIABLE**
- Bounding box coordinates are different when run multiple times on the same image
- Unable to accurately and precisely plot the location of objects
- Confidence scores are hallucinated (not grounded in actual detection confidence)
- Not suitable for production document layout analysis

### 2.3 Gemini's Native Bounding Box Support (The Standard)

Gemini provides **trained, native bounding box detection**:

| Capability | Gemini 2.5 Pro / 3 Pro |
|-----------|----------------------|
| Coordinate format | Normalized [0-1000], JSON output |
| Output structure | `[y0, x0, y1, x1]` with labels |
| mAP score | ~0.34 (2.5 Pro) to ~0.43 (3 Pro) |
| Equivalent to | YOLO v3-v4 level (2018-2020) |
| Known issues | Occasional malformed boxes `[0,0,0,0]`, coordinates outside range |
| Document layout | Specifically supported for document extraction |

**Source:** [Gemini Bounding Box Documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/bounding-box-detection), [Roboflow Multimodal Rankings](https://blog.roboflow.com/best-multimodal-models/)

### 2.4 Verdict on Spatial Capabilities

**Claude CANNOT replace Gemini for bounding box detection.** This is not a minor gap -- it is a fundamental architectural limitation. Claude was not trained for coordinate output, while Gemini was explicitly trained for it.

---

## 3. Mathematical Reasoning Capabilities

### 3.1 Where Claude Excels (Gemini Does Not Match)

| Capability | Claude Opus 4.6 | Gemini 3 Pro |
|-----------|-----------------|--------------|
| Logical error detection | STRONG | Moderate |
| Solution verification | STRONG | Moderate |
| Multi-step math reasoning | STRONG (1st place on many reasoning benchmarks) | Good |
| Cross-reference text vs diagram | STRONG | Moderate |
| Concept extraction from problems | STRONG | Good |
| Mathematical explanation quality | STRONG (human-preferred) | Good |

### 3.2 Applicable COW Pipeline Stages

Claude's mathematical reasoning strength maps directly to:

- **Stage D (Alignment)**: Semantically compare Mathpix OCR text against what Claude sees in the original image. Claude can detect if OCR missed a negative sign, swapped variables, or misread a Korean character -- without needing pixel coordinates.

- **Stage E (Semantic Graph)**: Build problem-solution-concept graphs. Claude's reasoning can infer mathematical relationships, prerequisite concepts, and solution strategies from OCR'd content.

- **Stage F (Regeneration)**: Verify regenerated LaTeX matches the original problem's mathematical intent. Claude can catch semantic errors that string-matching would miss.

- **New Potential Stage: Error Detection**: Claude could verify mathematical correctness of problems themselves (e.g., is this geometry problem solvable with the given constraints?).

---

## 4. Comparison: Claude vs Gemini vs Mathpix for COW

### 4.1 Head-to-Head Comparison

| Task | Claude Opus 4.6 | Gemini 3 Pro | Mathpix |
|------|-----------------|--------------|---------|
| Bounding box detection | NOT CAPABLE | STRONG (native) | N/A (not its purpose) |
| Layout analysis | Verbal description only | Coordinate-based | word_data with regions |
| Korean text OCR | ~90% | ~94% | 95%+ for math |
| Math notation OCR | Good (no structured output) | Good | BEST (purpose-built) |
| LaTeX conversion | Via reasoning (slow) | Via reasoning | Direct (fast, accurate) |
| Mathematical reasoning | BEST | Good | N/A |
| Error detection | BEST | Good | N/A |
| Semantic understanding | BEST | Good | N/A |
| Diagram description | STRONG | Moderate | N/A |
| Cost per 1K images | ~$4.00 | ~$1.50-3.00 | ~$10.00 |
| Latency | ~12s | ~5-8s | ~3-5s |

### 4.2 Multimodal Model Rankings (Roboflow 2026)

| Rank | Model | Score | Latency |
|------|-------|-------|---------|
| 2 | Gemini 2.5 Pro | 1275 | ~8s |
| 3 | Gemini 2.5 Flash | 1261 | ~3s |
| 5 | Gemini 3 Pro | 1232 | ~6s |
| 9 | Claude 4.1 Opus | 1213 | ~12s |

Note: Claude Opus 4.6 not yet benchmarked in this ranking at time of research. Claude 4.1 Opus ranked 9th. Gemini models dominate the top 5 for multimodal tasks.

### 4.3 Key Takeaway for COW

**Each tool has a clear role:**
- **Mathpix**: Primary OCR engine (highest accuracy for math, Korean support, structured output with coordinates) -- KEEP as Stage B
- **Gemini**: Vision detection engine (bounding boxes, layout analysis, visual element detection) -- KEEP for Stage C
- **Claude**: Semantic reasoning engine (alignment, error detection, graph construction, mathematical verification) -- ADD for Stages D, E, F

---

## 5. Claude Code + Image Integration

### 5.1 Read Tool for Images

Claude Code's Read tool documentation states it supports image files (PNG, JPG), presenting contents visually as Claude Code is a multimodal LLM.

**Current Status: BUGGY**

Active GitHub issues report problems:
- [Issue #18588](https://github.com/anthropics/claude-code/issues/18588): "Claude cannot interpret or see image content when reading image files"
- [Issue #20822](https://github.com/anthropics/claude-code/issues/20822): "Read tool returns empty result for image files"
- [Issue #618](https://github.com/anthropics/claude-code/issues/618): "Image Analysis Capability Limitation in Claude Code"

**Behavior:** Read tool returns "Tool ran without output or errors" -- the image data is not actually passed to the model.

### 5.2 Workarounds for Claude Code Image Analysis

| Method | How | Reliability |
|--------|-----|-------------|
| Paste into chat | Drag-and-drop or paste image directly | WORKS (image becomes part of API call) |
| MCP Vision servers | Z.AI Vision MCP, Read Images MCP, Google Cloud Vision MCP | WORKS (third-party MCP tools) |
| Claude API direct | Base64 encode image, send via Messages API | WORKS (most reliable) |
| Screenshot tool | Claude Code's native screenshot capability | WORKS for UI debugging |

### 5.3 MCP Vision Ecosystem (2026)

Several MCP servers provide vision capabilities that work with Claude Code:

1. **Z.AI Vision MCP Server** ([docs](https://docs.z.ai/devpack/mcp/vision-mcp-server))
   - Tools: `ui_to_artifact`, `extract_text_from_screenshot`, `diagnose_error_screenshot`
   - Uses GLM-4.6V backend

2. **Read Images MCP** ([GitHub](https://github.com/catalystneuro/mcp_read_images))
   - Analyzes images using OpenRouter vision models
   - Simple interface: specify image path in conversation

3. **Google Cloud Vision MCP** ([Composio](https://composio.dev/toolkits/google_cloud_vision/framework/claude-code))
   - OCR, label detection, face detection
   - Enterprise-grade accuracy

4. **MiniMax Coding Plan MCP** ([Medium](https://jpcaparas.medium.com/minimax-coding-plan-mcp-in-claude-code-search-vision-in-one-server-1ac0fc9150d3))
   - `web_search` + `understand_image` tools
   - Fills the gap for agent-based image analysis in Claude Code

### 5.4 Best Pattern for COW Pipeline

For the COW pipeline, the recommended approach for image analysis is:

```python
# Option 1: Direct API call (most reliable for production)
import anthropic
import base64

client = anthropic.Anthropic()

with open("math_problem.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data,
                },
            },
            {
                "type": "text",
                "text": "Analyze this Korean math problem. Describe: "
                        "1) The problem text and any Korean instructions, "
                        "2) Mathematical expressions present, "
                        "3) Any diagrams or figures and what they show, "
                        "4) Whether the problem appears complete and consistent."
            }
        ],
    }],
)
```

```python
# Option 2: Files API (for repeated analysis of same image)
# Upload once, use in multiple requests
file_upload = client.beta.files.upload(
    file=("math_problem.png", open("math_problem.png", "rb"), "image/png")
)

# Then reference file_id in messages
message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    betas=["files-api-2025-04-14"],
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {"type": "file", "file_id": file_upload.id},
            },
            {"type": "text", "text": "Verify this OCR result against the image..."},
        ],
    }],
)
```

---

## 6. Recommended Architecture for COW Pipeline

### 6.1 Current State (Implemented)

```
Stage A (Validation) --> Stage B (Mathpix OCR) --> Stage B1 (Layout/Content Separation)
[Haiku]                  [Sonnet+Mathpix]          [Haiku]
```

### 6.2 Planned State (Stages C-H Defined but Tools Commented Out)

```
A --> B --> B1 --> C (Gemini Vision) --> D (Alignment) --> E (Semantic Graph) --> F (Regen) --> G (HITL) --> H (Export)
```

### 6.3 Recommended Hybrid Architecture

```
                    +-------------------+
                    |   Stage A         |
                    |   Validation      |
                    |   [Claude Haiku]  |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Stage B         |
                    |   Mathpix OCR     |
                    |   [Sonnet+Mathpix]|
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Stage B1        |
                    |   Layout/Content  |
                    |   Separation      |
                    |   [Claude Haiku]  |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
    +---------v---------+     +-------------v----------+
    |   Stage C          |     |   Stage C-V            |
    |   Vision Parse     |     |   Visual Verification  |
    |   [GEMINI]         |     |   [CLAUDE OPUS]        |
    |   - Bbox detection |     |   - OCR verification   |
    |   - Layout coords  |     |   - Diagram description|
    |   - Element detect  |     |   - Error pre-check    |
    +---------+----------+     +-------------+----------+
              |                              |
              +--------------+---------------+
                             |
                    +--------v----------+
                    |   Stage D         |
                    |   Cross-Modal     |
                    |   Alignment       |
                    |   [CLAUDE SONNET] |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Stage E         |
                    |   Semantic Graph  |
                    |   [CLAUDE OPUS]   |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Stage F         |
                    |   Regeneration    |
                    |   [CLAUDE SONNET] |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Stage G         |
                    |   Human Review    |
                    |   [Claude Haiku]  |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   Stage H         |
                    |   Export          |
                    |   [Claude Haiku]  |
                    +-------------------+
```

### 6.4 New Stage C-V: Claude Visual Verification (Proposed)

A new parallel stage that runs alongside Gemini's Stage C:

| Aspect | Detail |
|--------|--------|
| Purpose | Verify Mathpix OCR against original image using Claude vision |
| Model | Claude Opus 4.6 |
| Input | Original image + Mathpix OCR output (layout + content) |
| Output | Verification report: confirmed/flagged/corrected elements |
| Key checks | Missing elements, OCR errors, diagram-text consistency |
| Does NOT require | Bounding box coordinates (works at semantic level) |

---

## 7. Risk Assessment

### 7.1 Risks of Using Claude for Bounding Box Tasks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Unreliable coordinates | CRITICAL | Do not use Claude for bbox -- use Gemini |
| Inconsistent results across runs | HIGH | No mitigation possible (architectural limit) |
| False confidence in spatial output | HIGH | Never trust Claude coordinate output without Gemini verification |

### 7.2 Risks of Using Claude for Semantic Tasks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Hallucinated mathematical content | MEDIUM | Cross-reference with Mathpix OCR output |
| Slow latency (~12s) | LOW | Acceptable for non-real-time pipeline |
| Cost at scale | MEDIUM | Use Haiku/Sonnet for simpler stages, Opus only for reasoning |
| Read tool bugs in Claude Code | LOW | Use API directly in pipeline code, not CLI |

---

## 8. Open Questions

1. **Will Anthropic add native bounding box support?** No public roadmap indication as of 2026-02-09. The spatial reasoning limitation has been present since Claude 3.

2. **Claude Opus 4.6 vs 4.5 for vision?** The 4.6 release notes emphasize coding and agentic improvements. No specific vision accuracy improvements mentioned.

3. **Could fine-tuned Claude improve spatial output?** Anthropic does not currently offer vision fine-tuning. Even if available, the architecture may not support coordinate-level output.

4. **MCP vision servers for production use?** Most are community-maintained. For production COW pipeline, direct API integration is more reliable than MCP wrappers.

---

## Sources

### Official Documentation
- [Anthropic Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision) -- Primary source for Claude vision capabilities, limits, and API usage
- [Anthropic Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview) -- Model specifications
- [Gemini Bounding Box Detection](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/bounding-box-detection) -- Google's official bbox documentation

### Benchmarks and Comparisons
- [Roboflow Best Multimodal Models 2026](https://blog.roboflow.com/best-multimodal-models/) -- Rankings: Gemini 2.5 Pro (1275) vs Claude 4.1 Opus (1213)
- [Claude Opus 4.6 vs 4.5 Benchmarks](https://ssntpl.com/blog-claude-opus-4-6-vs-4-5-benchmarks-testing/) -- Testing results
- [DataCamp Claude Opus 4.6](https://www.datacamp.com/blog/claude-opus-4-6) -- Features and benchmarks
- [Vellum Claude Opus 4.6 Benchmarks](https://www.vellum.ai/blog/claude-opus-4-6-benchmarks) -- Benchmark comparison

### Vision and OCR Analysis
- [Claude Vision for Document Analysis](https://getstream.io/blog/anthropic-claude-visual-reasoning/) -- Developer guide for Claude visual reasoning
- [Claude Vision Object Detection](https://github.com/Doriandarko/Claude-Vision-Object-Detection) -- Community bounding box approach (demonstrates unreliability)
- [Gemini Bounding Boxes (Simon Willison)](https://simonwillison.net/2024/Aug/26/gemini-bounding-box-visualization/) -- Gemini bbox visualization tool
- [OCR Comparison Study (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S2666720725000189) -- Math OCR model comparison
- [Gemini's Bounding Box Enterprise Adoption](https://medium.com/data-science-collective/gemini-2-5-pro-bounding-boxes-make-document-extraction-practical-57dc6d5b6821) -- Why bbox matters for document extraction

### Claude Code + Images
- [Claude Code Image Bug #18588](https://github.com/anthropics/claude-code/issues/18588) -- Read tool cannot interpret images
- [Claude Code Image Bug #20822](https://github.com/anthropics/claude-code/issues/20822) -- Read tool returns empty for images
- [Claude Code Image Limitation #618](https://github.com/anthropics/claude-code/issues/618) -- Image analysis capability limitation
- [CometAPI: Can Claude Code See Images?](https://www.cometapi.com/can-claude-code-see-images-and-how-does-that-work-in-2025/) -- Comprehensive guide
- [Z.AI Vision MCP Server](https://docs.z.ai/devpack/mcp/vision-mcp-server) -- MCP vision integration
- [Read Images MCP](https://github.com/catalystneuro/mcp_read_images) -- Image analysis MCP server

### Model Releases
- [Anthropic Claude Opus 4.6 Announcement](https://www.anthropic.com/claude/opus) -- Official release page
- [MarkTechPost Opus 4.6 Release](https://www.marktechpost.com/2026/02/05/anthropic-releases-claude-opus-4-6-with-1m-context-agentic-coding-adaptive-reasoning-controls-and-expanded-safety-tooling-capabilities/) -- Release details
