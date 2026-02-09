# COW Pipeline — Quick Reference Card

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COW Pipeline — 6-Stage Architecture                      │
│         Korean Math/Science Document Processing (MCP Server-centric)        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ 1.INGEST │───▶│ 2. OCR   │───▶│ 3.VISION │───▶│ 4.VERIFY │              │
│  │ MCP Tool │    │ MCP Tool │    │ MCP Tool │    │ Claude   │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │               │                    │
│  IngestResult    OcrResult      VisionResult   VerificationResult          │
│                                                       │                    │
│                                      ┌──────────┐    │    ┌──────────┐    │
│                                      │ 6.EXPORT │◀───┴───▶│ 5.COMPOSE│    │
│                                      │ MCP Tool │         │ Claude   │    │
│                                      └──────────┘         └──────────┘    │
│                                           │                    │           │
│                                      ExportResult      CompositionResult   │
│                                        (PDF)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## MCP Servers & Tools

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SERVER          │ TOOLS                          │ EXTERNAL API            │
├──────────────────┼────────────────────────────────┼─────────────────────────┤
│  cow-ingest      │ cow_validate_image             │ None (Pillow/pypdf)     │
│                  │ cow_validate_pdf               │                         │
├──────────────────┼────────────────────────────────┼─────────────────────────┤
│  cow-ocr         │ cow_mathpix_ocr_image          │ Mathpix API v3          │
│                  │ cow_mathpix_ocr_pdf            │                         │
│                  │ cow_ocr_get_cache              │                         │
├──────────────────┼────────────────────────────────┼─────────────────────────┤
│  cow-vision      │ cow_gemini_detect_elements     │ Gemini 3.0 Pro          │
│                  │ cow_gemini_layout_analysis      │                         │
│                  │ cow_merge_regions              │                         │
├──────────────────┼────────────────────────────────┼─────────────────────────┤
│  cow-review      │ cow_queue_review               │ None (SQLite)           │
│                  │ cow_get_queue                  │                         │
│                  │ cow_submit_review              │                         │
├──────────────────┼────────────────────────────────┼─────────────────────────┤
│  cow-export      │ cow_generate_latex             │ Mathpix /v3/converter   │
│                  │ cow_compile_pdf                │  (backup only)          │
│                  │ cow_mathpix_mmd_to_pdf         │                         │
├──────────────────┼────────────────────────────────┼─────────────────────────┤
│  cow-storage     │ cow_save_result                │ None (filesystem)       │
│                  │ cow_load_result                │                         │
│                  │ cow_list_sessions              │                         │
│                  │ cow_create_session             │                         │
└──────────────────┴────────────────────────────────┴─────────────────────────┘
```

## Stage-by-Stage Usage Flow

```
┌─ STAGE 1: INGEST ──────────────────────────────────────────────────────────┐
│  Input:  Image (PNG/JPG/TIFF/WebP) or PDF (max 2 pages)                   │
│  Call:   cow_validate_image(path) or cow_validate_pdf(path)                │
│  Output: IngestResult { file_path, file_type, dimensions, page_count }     │
│  Save:   cow_save_result(session_id, "ingest", result)                     │
└────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ STAGE 2: OCR ─────────────────────────────────────────────────────────────┐
│  Input:  IngestResult.preprocessed_path                                    │
│  Call:   cow_mathpix_ocr_image(path) or cow_mathpix_ocr_pdf(path)          │
│  Output: OcrResult { text, math_elements[], regions[], diagrams[] }        │
│  Save:   cow_save_result(session_id, "ocr", result)                        │
│  Note:   Results cached by content hash (cow_ocr_get_cache)                │
└────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ STAGE 3: VISION ──────────────────────────────────────────────────────────┐
│  Input:  Image + OcrResult.regions                                         │
│  Call:   cow_gemini_detect_elements(image_path, regions)                    │
│          cow_gemini_layout_analysis(image_path, ocr_regions)               │
│          cow_merge_regions(mathpix_regions, gemini_regions)                 │
│  Output: VisionResult { combined_regions[], layout_analysis }              │
│  Save:   cow_save_result(session_id, "vision", result)                     │
│  Note:   Gemini bbox auto-normalized to pixel coords, IoU merge at 0.5     │
└────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ STAGE 4: VERIFY ──────────────────────────────────────────────────────────┐
│  Engine: Claude Opus 4.6 NATIVE REASONING (no MCP tool)                    │
│  Input:  OcrResult + VisionResult (read from storage or inline)            │
│  Tasks:  - Cross-check OCR text accuracy                                   │
│          - Verify math equation correctness                                │
│          - Detect logic errors in math/science problems                    │
│          - Flag low-confidence regions for human review                    │
│  Output: VerificationResult { corrections[], math_errors[], logic_issues[] }│
│  Save:   cow_save_result(session_id, "verify", result)                     │
│  HITL:   cow_queue_review(session_id, findings) → user reviews via         │
│          cow_get_queue / cow_submit_review                                 │
└────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ STAGE 5: COMPOSE ─────────────────────────────────────────────────────────┐
│  Engine: Claude Opus 4.6 NATIVE REASONING (no MCP tool)                    │
│  Input:  VerificationResult + approved review items                        │
│  Tasks:  - Apply corrections to content                                    │
│          - Reconstruct document with proper layout                         │
│          - Generate complete LaTeX source                                  │
│          - Track all edits (before/after)                                  │
│  Output: CompositionResult { latex_source, metadata, edit_history[] }      │
│  Save:   cow_save_result(session_id, "compose", result)                    │
└────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ STAGE 6: EXPORT ──────────────────────────────────────────────────────────┐
│  Input:  CompositionResult                                                 │
│  Call:   cow_generate_latex(composition_json) → .tex file + LatexSource    │
│          cow_compile_pdf(tex_path)            → ExportResult (PDF)         │
│  Backup: cow_mathpix_mmd_to_pdf(mmd_content) → Mathpix cloud fallback     │
│  Output: ExportResult { pdf_path, method, page_count }                     │
│  Save:   cow_save_result(session_id, "export", result)                     │
│  Stack:  XeLaTeX + kotex + Noto CJK KR + amsmath                          │
└────────────────────────────────────────────────────────────────────────────┘
```

## Data Models (Interface Contracts)

```
IngestResult ─────────── file_path, file_type, page_count, dimensions,
                         preprocessed_path

OcrResult ────────────── text (MMD), math_elements[{latex, confidence, bbox}],
                         regions[{id, type, bbox, content}],
                         diagrams[{type, subtype, bbox, caption}],
                         raw_response

VisionResult ─────────── ocr_result, diagram_internals[{id, elements, bbox}],
                         layout_analysis{columns, reading_order, spatial_relations},
                         combined_regions[{id, type, bbox, source}]

VerificationResult ───── vision_result,
                         ocr_corrections[{original, corrected, reason}],
                         math_errors[{element_id, error_type, suggestion}],
                         logic_issues[{location, description, severity}],
                         verified, verification_notes

CompositionResult ────── latex_source, metadata{title, subject, grade_level},
                         edit_history[{action, target, before, after}],
                         user_approved

ExportResult ─────────── pdf_path, method("xelatex"|"mathpix_converter"),
                         page_count, compilation_log
```

## Environment Setup

```
┌─ Runtime Requirements ─────────────────────────────────────────────────────┐
│                                                                            │
│  Python:     cow/cow-mcp/.venv/  (pip install -e cow/cow-mcp)              │
│  MCP Config: cow/.mcp.json       (API keys — NOT in git)                   │
│  Sessions:   ~/.cow/sessions/    (auto-created)                            │
│  Review DB:  ~/.cow/review.db    (auto-created)                            │
│  OCR Cache:  ~/.cow/cache/       (diskcache, 512MB)                        │
│                                                                            │
│  XeLaTeX:    xelatex (TeX Live 2023)                                       │
│  Fonts:      Noto Serif/Sans CJK KR (16 variants)                         │
│  LaTeX Pkgs: kotex, amsmath, amssymb, tikz, pgfplots, graphicx            │
│                                                                            │
│  API Keys (in cow/.mcp.json env):                                          │
│    MATHPIX_APP_ID / MATHPIX_APP_KEY  → cow-ocr, cow-export                │
│    GEMINI_API_KEY                    → cow-vision                          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Build Pipeline (how this was created)

```
  Skill                           Phase   Gate      Artifacts
  ─────────────────────────────── ─────── ───────── ─────────────────────────
  /brainstorming-pipeline         P1-P3   3 PASS    GC-v3, 3 research reports
  /agent-teams-write-plan         P4      APPROVED  1274L plan, 3 implementers
  /plan-validation-pipeline       P5      COND_PASS 24 findings, 4 conditions
  /agent-teams-execution-plan     P6      APPROVED  33 files, ~7400 lines
  (deferred)                      P7-P8   —         self-tested only
  /delivery-pipeline              P9      DELIVERED  commit c14d592
```

## Quick Start Example

```
# 1. Create a session
cow_create_session(name="test-run-1")

# 2. INGEST — validate input
cow_validate_image("/path/to/math-problem.png")

# 3. OCR — extract text and math
cow_mathpix_ocr_image("/path/to/math-problem.png")

# 4. VISION — detect layout + merge regions
cow_gemini_detect_elements(image_path, regions)
cow_gemini_layout_analysis(image_path, ocr_regions)
cow_merge_regions(mathpix_regions, gemini_regions)

# 5. VERIFY — Claude native reasoning (no tool call)
#    → Read OCR+Vision results, cross-check, find errors

# 6. Review (HITL)
cow_queue_review(session_id, findings_json)
cow_get_queue(session_id)
cow_submit_review(item_id, "approved")

# 7. COMPOSE — Claude native reasoning (no tool call)
#    → Generate LaTeX from verified content

# 8. EXPORT — compile PDF
cow_generate_latex(composition_json)
cow_compile_pdf("/path/to/output.tex")
```
