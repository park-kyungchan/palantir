# Architecture Design: COW Pipeline Redesign

**Architect:** architect-1
**Date:** 2026-02-09
**Phase:** 3 (Architecture)
**Complexity:** COMPLEX

---

## 1. Overview

The COW (Content/Layout Separation) pipeline processes Korean math/science documents through 6 stages: input validation, OCR extraction, visual analysis, AI verification, interactive composition, and PDF export. The system is designed as a set of MCP (Model Context Protocol) servers that Claude Code CLI orchestrates natively through its Agent Teams infrastructure.

### Design Philosophy
- **MCP-native:** Business logic exposed as MCP tools, not wrapped in subprocess calls
- **Claude-native reasoning:** Verification and composition stages leverage Claude Opus 4.6 directly
- **Domain-agnostic infrastructure:** MCP servers are reusable; pipeline logic lives in orchestration
- **Incremental development:** Each MCP server is independently testable and deployable

---

## 2. System Architecture

```
User (tmux)
    │
    ▼
Claude Code CLI (Orchestrator)
    │
    ├── [MCP] cow-ingest ──── Pillow, PyPDF
    ├── [MCP] cow-ocr ─────── Mathpix API v3
    ├── [MCP] cow-vision ──── Gemini 3.0 Pro API
    ├── [NATIVE] VERIFY ───── Claude Opus 4.6 reasoning
    ├── [NATIVE] COMPOSE ──── Claude Opus 4.6 + user dialog
    ├── [MCP] cow-export ──── XeLaTeX + kotex
    ├── [MCP] cow-review ──── SQLite (HITL queue)
    └── [MCP] cow-storage ─── Filesystem
```

### Orchestration Model
Claude Code CLI reads the pipeline configuration and calls MCP tools in sequence. For VERIFY and COMPOSE stages, Claude uses its own reasoning capabilities — no external tool call is needed. The user interacts with Claude directly during COMPOSE for editing decisions.

---

## 3. Pipeline Stages

### Stage 1: INGEST
**Purpose:** Validate and preprocess input files.
**Engine:** Python pure logic (Pillow, PyPDF)
**MCP Server:** cow-ingest

**Tools:**
- `validate_image(path) → IngestResult` — Check format (PNG/JPG/TIFF/WebP), dimensions, DPI, color space. Normalize to standard format.
- `validate_pdf(path, pages?) → IngestResult` — Check page count (max 2 initially), extract pages, render to images for downstream processing.

**Reuses:** Pillow (existing dependency), basic validation logic from current codebase.

### Stage 2: OCR
**Purpose:** Extract text, equations, bounding boxes, and classify diagrams.
**Engine:** Mathpix API v3
**MCP Server:** cow-ocr

**Tools:**
- `mathpix_ocr_image(path, options?) → OcrResult` — Send image to Mathpix, parse response into structured result with text, math elements, regions, and diagrams.
- `mathpix_ocr_pdf(path, pages?) → OcrResult` — Send PDF to Mathpix, process per-page results.
- `get_cache(content_hash) → OcrResult?` — Check disk cache before API call to save costs.

**Reuses:** mathpix/client.py (modernized), semantic/separator.py (cnt→region conversion).

**Key technical details:**
- Mathpix returns `cnt` (polygon contours) and `region` (rectangle bounding boxes)
- separator.py `_cnt_to_region()` converts polygons to axis-aligned bounding boxes
- Document tree hierarchy from Mathpix SuperNet (April 2025+) provides parent-child relationships
- Output format: MMD (Mathpix Markdown) primary, with raw JSON preserved for downstream
- Caching by content hash (imagehash + diskcache, existing dependencies)

### Stage 3: VISION
**Purpose:** Detect diagram internal elements, analyze layout coordinates, supplement Mathpix bbox.
**Engine:** Gemini 3.0 Pro API
**MCP Server:** cow-vision

**Tools:**
- `gemini_detect_elements(image_path, regions?) → DiagramInternals` — Send image region to Gemini for internal element detection (axes, labels, data points, geometric shapes).
- `gemini_layout_analysis(image_path, ocr_regions?) → LayoutAnalysis` — Analyze reading order, column structure, spatial relationships between elements.

**Why Gemini, not Claude:**
- Claude bbox is NOT FEASIBLE (Anthropic official limitation)
- Gemini 3.0 Pro has native bbox support with mAP ~0.43
- Gemini Korean text ~94% accuracy (supplementary to Mathpix 95%+)

**Integration:** Results merged with Mathpix OCR output to create `VisionResult` with combined regions from both sources, tagged by origin (mathpix/gemini/merged).

### Stage 4: VERIFY
**Purpose:** Verify OCR accuracy, detect math errors, find logic issues.
**Engine:** Claude Opus 4.6 (native reasoning)
**MCP Server:** None — Claude Code IS the processor

**How it works:**
1. Claude reads the VisionResult (OCR text + bbox + layout + diagram info)
2. Claude verifies Korean text accuracy against visual context
3. Claude checks mathematical equations for typographical and logical errors
4. Claude identifies logic issues (e.g., contradictory conditions, impossible scenarios)
5. Claude produces VerificationResult with corrections and confidence scores

**Why native:**
- Opus 4.6 has the BEST math reasoning capabilities
- Logic error detection requires deep understanding, not pattern matching
- No coordinate-based output needed — verification is semantic-level

### Stage 5: COMPOSE
**Purpose:** Reconstruct the document with user-directed edits.
**Engine:** Claude Opus 4.6 (native reasoning + user dialog)
**MCP Server:** None — Claude Code manages the interactive session

**How it works:**
1. Claude presents the verified content to the user
2. User directs edits (text changes, equation modifications, layout adjustments)
3. Claude applies edits while maintaining consistency
4. Claude generates complete LaTeX source for the document
5. User approves final composition

**HITL Integration:**
- cow-review MCP server manages the review queue
- Each verification finding is a review item
- User can approve, modify, or reject each finding
- Claude tracks edit history for audit

### Stage 6: EXPORT
**Purpose:** Generate final PDF from LaTeX source.
**Engine:** XeLaTeX + kotex (primary), Mathpix converter (backup)
**MCP Server:** cow-export

**Tools:**
- `generate_latex(composition, template?) → LatexSource` — Generate complete LaTeX document with kotex preamble, Noto CJK KR font configuration, math packages.
- `compile_pdf(latex_path) → ExportResult` — Run `xelatex` via subprocess, handle compilation errors, retry with fixes.
- `mathpix_mmd_to_pdf(mmd_content) → ExportResult` — Fallback: send MMD to Mathpix /v3/converter for cloud PDF generation.

**LaTeX configuration:**
```latex
\documentclass[a4paper]{article}
\usepackage{xetexko}
\usepackage{kotex}
\setmainfont{Noto Serif CJK KR}
\setsansfont{Noto Sans CJK KR}
\setmonofont{Noto Sans Mono CJK KR}
\usepackage{amsmath, amssymb, amsthm}
\usepackage{tikz, pgfplots}
\usepackage{graphicx}
```

---

## 4. MCP Server Infrastructure

### Server Protocol
All MCP servers use **stdio** transport (standard for Claude Code integration).
Each server is a Python module in the `cow-mcp` package.

### Registration (`.mcp.json` or project-level)
```json
{
  "mcpServers": {
    "cow-ingest": {
      "command": "python",
      "args": ["-m", "cow_mcp.ingest"],
      "env": {}
    },
    "cow-ocr": {
      "command": "python",
      "args": ["-m", "cow_mcp.ocr"],
      "env": { "MATHPIX_APP_ID": "", "MATHPIX_APP_KEY": "" }
    },
    "cow-vision": {
      "command": "python",
      "args": ["-m", "cow_mcp.vision"],
      "env": { "GEMINI_API_KEY": "" }
    },
    "cow-review": {
      "command": "python",
      "args": ["-m", "cow_mcp.review"],
      "env": {}
    },
    "cow-export": {
      "command": "python",
      "args": ["-m", "cow_mcp.export"],
      "env": {}
    },
    "cow-storage": {
      "command": "python",
      "args": ["-m", "cow_mcp.storage"],
      "env": {}
    }
  }
}
```

### Package Structure
```
cow/cow-mcp/
├── pyproject.toml
├── cow_mcp/
│   ├── __init__.py
│   ├── models/           # Pydantic models for all interface contracts
│   │   ├── __init__.py
│   │   ├── ingest.py     # IngestResult
│   │   ├── ocr.py        # OcrResult, MathElement, Region, Diagram
│   │   ├── vision.py     # VisionResult, DiagramInternals, LayoutAnalysis
│   │   ├── verify.py     # VerificationResult, OcrCorrection, MathError
│   │   ├── compose.py    # CompositionResult, EditAction
│   │   └── export.py     # ExportResult, LatexSource
│   ├── ingest/           # cow-ingest server
│   │   ├── __init__.py
│   │   ├── __main__.py   # MCP server entry point
│   │   └── validator.py
│   ├── ocr/              # cow-ocr server
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── client.py     # Modernized from cow-cli mathpix/client.py
│   │   ├── separator.py  # Reused from cow-cli semantic/separator.py
│   │   └── cache.py
│   ├── vision/           # cow-vision server
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── gemini.py     # Gemini 3.0 Pro client
│   ├── review/           # cow-review server
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── database.py   # Reused from cow-cli review/database.py
│   ├── export/           # cow-export server
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── latex.py      # LaTeX generation with kotex
│   │   └── compiler.py   # XeLaTeX subprocess compilation
│   └── storage/          # cow-storage server
│       ├── __init__.py
│       ├── __main__.py
│       └── filesystem.py
└── tests/
    ├── test_ingest.py
    ├── test_ocr.py
    ├── test_vision.py
    ├── test_review.py
    ├── test_export.py
    └── test_storage.py
```

---

## 5. Data Flow

```
Image/PDF
    │
    ▼
[INGEST] validate + preprocess
    │ IngestResult
    ▼
[OCR] Mathpix API → text, equations, bbox, diagrams
    │ OcrResult
    ▼
[VISION] Gemini API → diagram internals, layout coords
    │ VisionResult (merged OCR + Vision)
    ▼
[VERIFY] Claude reasoning → corrections, math errors, logic issues
    │ VerificationResult
    ▼
[COMPOSE] Claude + User → edit, reconstruct, approve
    │ CompositionResult (LaTeX source)
    ▼
[EXPORT] XeLaTeX → PDF
    │ ExportResult
    ▼
Final PDF
```

### Data Persistence
- Each stage result saved via cow-storage after completion
- Session-based directory structure: `~/.cow/sessions/{session-id}/`
- Results are JSON-serializable Pydantic models
- Cache layer for OCR results (avoid re-processing same images)

---

## 6. Error Handling Strategy

### Per-Stage Error Handling
| Stage | Error Type | Strategy |
|-------|-----------|----------|
| INGEST | Invalid file format | Reject with clear message, suggest conversion |
| INGEST | File too large | Reject with size limit info |
| OCR | Mathpix API failure | Retry once, then inform user |
| OCR | Low confidence result | Flag for VERIFY stage, continue pipeline |
| VISION | Gemini API failure | Degrade gracefully — skip to VERIFY with OCR-only data |
| VISION | Rate limit | Exponential backoff, max 3 retries |
| VERIFY | Claude disagreement | Present both versions to user in COMPOSE |
| COMPOSE | User cancellation | Save partial work to cow-storage |
| EXPORT | XeLaTeX compilation failure | Auto-fix common errors, fallback to Mathpix converter |
| EXPORT | Font missing | Check font availability at startup, warn user |

### Global Error Handling
- All MCP tool calls wrapped in try/except with structured error responses
- Pydantic validation on all stage inputs/outputs
- Session recovery: partial results saved at each stage boundary
- Cost tracking: log API calls and costs per session

---

## 7. Key Decisions with Rationale

### D-1: MCP Server-centric Architecture
**Alternatives considered:**
- Option 1 (Subprocess): Claude Code spawns cow-cli as subprocess, parses stdout → Unreliable output parsing, fragile interface
- Option 2 (SDK Adapter): claude-agent-sdk wrapping Claude Code CLI → SDK requires Anthropic API, contradicts MAX X20 constraint
- **Option 3 (MCP Server): Business logic as MCP tools** → Claude Code's native tool protocol, type-safe, composable

### D-2: 6-stage Pipeline
**Rationale:** Original 9 stages (A→B→B1→C→D→E→F→G→H) were over-engineered with most unimplemented. Opus 4.6's reasoning capability allows merging:
- B+B1 → OCR (single Mathpix call handles both)
- D+E → VERIFY (Claude does alignment + semantic analysis together)
- F+G → COMPOSE (reconstruction + human review combined)

### D-3: Gemini for BBox
**Rationale:** Claude vision has "limited spatial reasoning" (Anthropic docs). Gemini 3.0 Pro provides native bbox detection with mAP ~0.43. Cost-effective at paid tier. Supplements Mathpix bbox with diagram internal element detection.

### D-4: Native Reasoning Stages
**Rationale:** Creating MCP tools for VERIFY and COMPOSE would be absurd — Claude would call a tool that calls Claude. Instead, the orchestrator (Claude Code) directly applies its reasoning during these stages.

### D-8: No Anthropic API
**Rationale:** User subscribes to Claude MAX X20 ($200/mo). Claude Code CLI with this subscription provides unlimited Opus 4.6 access. Using the Anthropic API would incur separate costs and duplicate the capability already available through the CLI.

---

## 8. Integration with ~/.claude/ Infrastructure

### MCP Registration
Add cow-mcp servers to project-level `.mcp.json` in the cow/ directory. Claude Code auto-discovers registered servers.

### Agent Teams Workflow
The pipeline can be orchestrated through Agent Teams:
- Lead manages the overall pipeline flow
- Implementers build individual MCP servers
- Testers validate each server independently
- Integrator ensures cross-server contracts hold

### API Key Management
- Mathpix: `MATHPIX_APP_ID`, `MATHPIX_APP_KEY` via environment
- Gemini: `GEMINI_API_KEY` via environment
- No keys in code, no keys in git (CLAUDE.md §8 safety)

---

## 9. Risk Register

| ID | Risk | Impact | Probability | Score | Mitigation |
|----|------|--------|-------------|-------|-----------|
| R-1 | Gemini API rate limits/costs | Pipeline blocked | LOW | 5 | Cache results, fallback to Mathpix-only mode |
| R-2 | Mathpix Korean accuracy gap | Wrong OCR text | MEDIUM | 4 | Claude verification stage catches errors |
| R-3 | XeLaTeX complex layout failure | No PDF output | MEDIUM | 6 | Mathpix converter backup, simplified layout fallback |
| R-4 | MCP Server complexity | Development time | LOW | 5 | Incremental development, server-per-domain isolation |
| R-5 | Claude Code image Read bug | Can't view images | HIGH | 7 | Pass image data via MCP tool, not Read tool |
| R-6 | Interface contract drift | Stage incompatibility | LOW | 4 | Pydantic models with runtime validation |

---

## 10. Phase 4 Requirements

### For the Phase 4 Architect
1. **Read all 3 feasibility reports** for technical constraints and API specifics
2. **Design each MCP server** in detail: tool signatures, error responses, configuration
3. **Define Pydantic models** for all 6 interface contracts with validation rules
4. **Plan codebase migration:** remove SDK modules, restructure cow-cli → cow-mcp
5. **Task decomposition:** non-overlapping file ownership per implementer
6. **Dependency graph:** which tasks can run in parallel vs sequential
7. **Test strategy:** per-server unit tests + integration tests for stage transitions
8. **~/.claude/ integration:** MCP server registration, environment configuration
9. **Migration of reusable modules:** how separator.py, client.py, database.py transfer
10. **Acceptance criteria:** per-task AC-0 (plan-vs-reality check) mandatory
