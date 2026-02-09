---
version: GC-v6
created: 2026-02-09
feature: cow-pipeline-redesign
complexity: COMPLEX
---

# Global Context — COW Pipeline Redesign

## Scope

**Goal:** Complete ground-up redesign of the COW (Content/Layout Separation) pipeline for Korean math/science document processing — from SDK-based 9-stage architecture to MCP Server-centric 6-stage architecture orchestrated by Claude Code CLI.

**In Scope:**
- 6-stage pipeline: INGEST → OCR → VISION → VERIFY → COMPOSE → EXPORT
- MCP Server infrastructure (cow-mcp Python package) exposing business logic as tools
- Mathpix API v3 integration (OCR, bbox, diagram classification)
- Gemini 3.0 Pro API integration (bbox detection, layout analysis)
- Claude Opus 4.6 native reasoning (OCR verification, logic error detection, content composition)
- XeLaTeX + kotex PDF generation with Korean math support
- HITL (Human-in-the-Loop) step-by-step confirmation workflow
- Reuse of pure logic modules: mathpix/client.py, semantic/separator.py, review/database.py, export/, config.py

**Out of Scope:**
- Anthropic API usage (Claude MAX X20 subscription only)
- Handwritten Korean OCR (Mathpix limitation)
- Batch/mass processing (deferred to post-stabilization)
- claude-agent-sdk dependency (removed entirely)
- HWP format support (PDF output only)

**Success Criteria:**
- Process 1-2 images or 1-2 PDF pages of Korean math/science content end-to-end
- Produce clean, edited PDF with correct equations, diagrams, and layout
- All OCR results verified by Claude Opus 4.6 before human review
- Logic errors detected and flagged during editing phase

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED — Discovery + Requirements R1-R10)
- Phase 2: COMPLETE (Gate 2 APPROVED — 3 feasibility reports)
- Phase 3: COMPLETE (Gate 3 APPROVED — 6-stage pipeline + MCP Server architecture)
- Phase 4: COMPLETE (Gate 4 APPROVED — 10-section implementation plan, 1274 lines)
- Phase 5: COMPLETE (Gate 5 CONDITIONAL_PASS — 24 findings, 0 CRITICAL, 4 HIGH mitigated)
- Phase 6: COMPLETE (Gate 6 APPROVED — 33 files, 3 implementers, all 4 conditions met)
- Phase 7-8: DEFERRED (self-tested; full integration requires API keys + TeX Live)

## Phase 5 Validation Results
- **Verdict:** CONDITIONAL_PASS (24 findings: 0C/4H/10M/10L)
- **HIGH issues mitigated:** cnt_to_bbox regression, MCP SDK stability, Gemini bbox format, merge_regions() spec
- **Conditions for Phase 6:** 4 conditions tracked (all addressable via implementer directives)
- **Notable MEDIUM:** ReviewDatabase sync→async, missing exception module, OcrRegion.bbox optionality, kotex/xetexko redundancy

## Implementation Plan Reference
- **Plan:** docs/plans/2026-02-09-cow-pipeline-redesign.md (1274 lines)
- **Implementers:** 3 (Foundation+Ingest+Storage, OCR+Vision, Review+Export)
- **Tasks:** 8 (T-1 through T-8)
- **New files:** ~33 Python files + pyproject.toml + .mcp.json
- **Dependency graph:** T-1 → (T-2,T-3 | T-4,T-5 | T-6,T-7) → T-8

## Task Decomposition
| Task | Implementer | Files | Dependencies |
|------|-------------|-------|-------------|
| T-1 | Impl-1 | pyproject.toml, models/ (8 files) | none |
| T-2 | Impl-1 | ingest/ (3 files) | T-1 |
| T-3 | Impl-1 | storage/ (3 files) | T-1 |
| T-4 | Impl-2 | ocr/ (5 files) | T-1 |
| T-5 | Impl-2 | vision/ (3 files) | T-1 |
| T-6 | Impl-3 | review/ (4 files) | T-1 |
| T-7 | Impl-3 | export/ (4 files) | T-1 |
| T-8 | Impl-3 | .mcp.json | T-2..T-7 |

## File Ownership Map
- Impl-1: cow/cow-mcp/pyproject.toml, cow_mcp/__init__.py, models/ (8), ingest/ (3), storage/ (3) = 16 files
- Impl-2: cow_mcp/ocr/ (5), vision/ (3) = 8 files
- Impl-3: cow_mcp/review/ (4), export/ (4), cow/.mcp.json = 9 files

## Phase 5 Validation Targets
1. MCP SDK compatibility (mcp Python package API stability)
2. google-genai structured output for bbox
3. XeLaTeX + kotex + amsmath coexistence
4. Implementer-1 file count (16 files, justified as mostly boilerplate)
5. cow-cli module adaptation scope estimates

## Phase 6 Entry Conditions
- Phase 5 PASS or CONDITIONAL_PASS
- Implementation plan unchanged or revised per Phase 5 findings
- All interface contracts frozen

## Component Map

### Pipeline Stages (6)
| Stage | Name | Engine | MCP Tool? |
|-------|------|--------|-----------|
| 1 | INGEST | Python pure logic | Yes (cow-ingest) |
| 2 | OCR | Mathpix API v3 | Yes (cow-ocr) |
| 3 | VISION | Gemini 3.0 Pro API | Yes (cow-vision) |
| 4 | VERIFY | Claude Opus 4.6 | No (native reasoning) |
| 5 | COMPOSE | Claude Opus 4.6 | No (native reasoning) |
| 6 | EXPORT | XeLaTeX + kotex | Yes (cow-export) |

### MCP Servers (6)
| Server | Tools | External API |
|--------|-------|-------------|
| cow-ingest | validate_image, validate_pdf | None |
| cow-ocr | mathpix_ocr_image, mathpix_ocr_pdf, get_cache | Mathpix API v3 |
| cow-vision | gemini_detect_elements, gemini_layout_analysis | Gemini 3.0 Pro |
| cow-review | queue_review, get_queue, submit_review | None (SQLite) |
| cow-export | generate_latex, compile_pdf, mathpix_mmd_to_pdf | Mathpix converter |
| cow-storage | save_result, load_result, list_sessions | None (filesystem) |

### Orchestrator
Claude Code CLI (Agent Teams mode, tmux) acts as the native orchestrator.
VERIFY and COMPOSE stages use Claude's own reasoning — no MCP tool call needed.

## Interface Contracts

### Stage 1 → 2 (INGEST → OCR)
```
IngestResult {
  file_path: str           # validated input file
  file_type: "image" | "pdf"
  page_count: int          # 1 for images
  dimensions: {w, h}       # pixels
  preprocessed_path: str   # normalized image/PDF
}
```

### Stage 2 → 3 (OCR → VISION)
```
OcrResult {
  text: str                # full text (MMD format)
  math_elements: [{latex, confidence, bbox}]
  regions: [{id, type, bbox, content}]
  diagrams: [{type, subtype, bbox, caption}]
  raw_response: dict       # Mathpix API raw JSON
}
```

### Stage 3 → 4 (VISION → VERIFY)
```
VisionResult {
  ocr_result: OcrResult                    # from Stage 2
  diagram_internals: [{id, elements, bbox}] # Gemini bbox detection
  layout_analysis: {columns, reading_order, spatial_relations}
  combined_regions: [{id, type, bbox, source}] # merged Mathpix + Gemini
}
```

### Stage 4 → 5 (VERIFY → COMPOSE)
```
VerificationResult {
  vision_result: VisionResult
  ocr_corrections: [{original, corrected, reason, confidence}]
  math_errors: [{element_id, error_type, suggestion}]
  logic_issues: [{location, description, severity}]
  verified: bool
  verification_notes: str
}
```

### Stage 5 → 6 (COMPOSE → EXPORT)
```
CompositionResult {
  latex_source: str         # complete LaTeX document
  metadata: {title, subject, grade_level}
  edit_history: [{action, target, before, after}]
  user_approved: bool
}
```

### Stage 6 Output (EXPORT)
```
ExportResult {
  pdf_path: str
  method: "xelatex" | "mathpix_converter"
  page_count: int
  compilation_log: str
}
```

## Phase 2 Research Findings

### R-1: Mathpix API (cow/docs/research/mathpix-api-feasibility.md, 690 lines)
- Math OCR: EXCELLENT (LaTeX, MathML, AsciiMath output)
- Korean printed text: GOOD (supported)
- Korean handwritten: NOT SUPPORTED
- Bbox: VERY GOOD — cnt (polygon contour) + region (rectangle), document tree hierarchy
- Diagram detection: type/subtype classification, 7 chart types, figure-caption linking
- Output formats: MMD, LaTeX, DOCX, HTML, PDF, JSON with per-element bboxes
- Pricing: $0.002/image, $0.005/PDF page
- Python SDK: mpxpy (MathpixClient)

### R-2: Claude Vision (cow/docs/research/claude-vision-feasibility.md, 449 lines)
- Bbox detection: NOT FEASIBLE (Anthropic official limitation — "spatial reasoning limited")
- Math reasoning: BEST (outperforms all competitors for logic/verification)
- Korean OCR: ~90% accuracy (vs Gemini ~94%, Mathpix 95%+)
- Logic error detection: BEST (Opus 4.6 unique strength)
- Claude Code Read tool for images: BUGGY (GitHub issues #18588, #20822)
- Recommendation: Use Claude for reasoning/verification, NOT for coordinate-based tasks

### R-3: PDF Generation (cow/docs/research/pdf-generation-feasibility.md, 848 lines)
- XeLaTeX + kotex: Gold standard for Korean LaTeX (maintained by Korean TeX Society)
- xetexko recommended over LuaLaTeX for Korean
- Fonts: Noto CJK KR (Google/Adobe primary), Nanum (Naver/Sandoll backup)
- PyLaTeX: Only Python lib with native LaTeX math + Korean, but subprocess xelatex better
- Pandoc + XeLaTeX: Best automation path for pipeline integration
- Mathpix /v3/converter: Cloud backup ($0.005/page)
- Typst: CJK incomplete, not production-ready

## Architecture Decisions
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | MCP Server-centric (not subprocess or SDK adapter) | Claude Code = native orchestrator; subprocess unreliable output parsing; SDK requires API | P1 |
| D-2 | 6-stage pipeline (from 9) | Opus 4.6 merges semantic/reasoning tasks; stages D/E/F/G collapsed into VERIFY+COMPOSE | P1 |
| D-3 | Gemini 3.0 Pro for bbox | Claude bbox NOT FEASIBLE; Gemini has native bbox support (mAP ~0.43) | P2 |
| D-4 | VERIFY/COMPOSE as Claude native reasoning | No MCP tool needed — Claude Code IS the reasoning engine | P3 |
| D-5 | XeLaTeX + kotex primary, Mathpix backup | Proven Korean math typesetting; cloud backup for reliability | P2 |
| D-6 | Dual OCR verification (auto + HITL) | OCR auto-verify by Claude after Mathpix; human confirms during COMPOSE | P1 |
| D-7 | Reuse separator.py bbox logic | cnt→region conversion already working correctly | P2 |
| D-8 | No Anthropic API dependency | User constraint: Claude MAX X20 only, CLI-only I/O | P1 |
| D-9 | ~/.claude/ INFRA optimization required | Integrate cow pipeline with existing Agent Teams infrastructure | P1 |

## Constraints
- Claude MAX X20 ($200/mo) — no Anthropic API billing
- Gemini 3.0 Pro API — paid tier, user-confirmed
- Mathpix API — ~$0.002/image, ~$0.005/page
- Python 3.11+ runtime
- CLI-only I/O (tmux + Agent Teams mode)
- Initial scope: 1-2 images or 1-2 PDF pages per run
- Korean math/science domain (equations, diagrams, charts)

## Existing Codebase (cow/cow-cli/)
**Reusable modules:**
- `mathpix/client.py` — Mathpix API client (needs modernization)
- `semantic/separator.py` (712L) — Layout/Content separator with bbox cnt→region conversion
- `review/database.py` — SQLite review queue
- `export/` — Export utilities
- `config.py` — Configuration management

**To be removed:**
- `claude/orchestrator.py` (~585L) — SDK-based, incompatible
- `claude/stage_agents.py` (~500L) — SDK-based, incompatible
- `claude/mcp_servers.py` (~400L) — SDK-based, incompatible

**Dependencies (pyproject.toml):**
Python 3.11+, typer>=0.21.0, rich>=14.0.0, pydantic>=2.0.0, httpx>=0.28.0,
keyring>=25.0.0, sqlalchemy>=2.0.0, aiosqlite>=0.22.0, python-docx>=1.2.0,
pylatex>=1.4.0, Pillow>=12.0.0, imagehash>=4.3.0, diskcache>=5.6.0, pyyaml>=6.0.0

## Phase 4 Entry Requirements
- All 3 feasibility reports reviewed and incorporated
- 6-stage pipeline architecture approved
- MCP Server tool design confirmed
- Interface contracts between stages defined
- Tech stack decisions finalized
- Reusable vs removable module classification complete
