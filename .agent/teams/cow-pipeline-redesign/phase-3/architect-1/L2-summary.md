# L2 Summary: COW Pipeline Redesign Architecture

**Architect:** architect-1
**Date:** 2026-02-09
**Consumer:** Lead (Gate 3), Phase 4 architect, Phase 5 devils-advocate

---

## Executive Summary

The COW pipeline is redesigned from a 9-stage SDK-based architecture to a 6-stage MCP Server-centric architecture. Claude Code CLI acts as the native orchestrator via Agent Teams (tmux). Three external services provide specialized capabilities: Mathpix API v3 for OCR/bbox/diagram classification, Gemini 3.0 Pro API for bbox detection and layout analysis, and XeLaTeX + kotex for Korean math PDF generation. Two pipeline stages (VERIFY, COMPOSE) require no MCP tools — they leverage Claude Opus 4.6's native reasoning for OCR verification, logic error detection, and content composition.

---

## Architecture Decision Summary

| AD | Decision | Key Rationale |
|----|----------|---------------|
| D-1 | MCP Server-centric | Claude Code = native orchestrator; subprocess unreliable; SDK requires API |
| D-2 | 6-stage pipeline | Opus 4.6 merges semantic/reasoning tasks; 9 stages over-engineered |
| D-3 | Gemini 3.0 Pro for bbox | Claude bbox NOT FEASIBLE (Anthropic official); Gemini mAP ~0.43 |
| D-4 | VERIFY/COMPOSE native | No MCP tool needed — Claude IS the reasoning engine |
| D-5 | XeLaTeX primary | Gold standard for Korean math; Mathpix converter as backup |
| D-6 | Dual verification | Auto-verify OCR + HITL during composition |
| D-7 | Reuse separator.py | 712-line module with working bbox cnt→region conversion |
| D-8 | No Anthropic API | User constraint: MAX X20 only |
| D-9 | INFRA optimization | Integrate with existing ~/.claude/ Agent Teams infrastructure |

---

## Pipeline Design Highlights

**6-stage flow:** INGEST → OCR → VISION → VERIFY → COMPOSE → EXPORT

**Stage characteristics:**
- INGEST: Pure Python validation/preprocessing. Lightweight, no external API.
- OCR: Mathpix API v3 — text, equations, bbox, diagram classification. Primary data extraction.
- VISION: Gemini 3.0 Pro — diagram internal bbox, layout coordinate analysis. Supplements Mathpix.
- VERIFY: Claude Opus 4.6 — OCR correction, math error detection, logic verification. Native reasoning.
- COMPOSE: Claude Opus 4.6 — full document reconstruction, interactive editing with user. Native reasoning.
- EXPORT: XeLaTeX + kotex → PDF. Pandoc automation. Mathpix converter backup.

**Key insight:** VERIFY and COMPOSE don't need MCP tools because Claude Code itself IS the processor. The user converses with Claude directly during these stages.

---

## MCP Server Design

6 servers, each with focused responsibility:

| Server | Tools | Dependency |
|--------|-------|-----------|
| cow-ingest | validate_image, validate_pdf | Pillow, PyPDF |
| cow-ocr | mathpix_ocr_image, mathpix_ocr_pdf, get_cache | Mathpix API, mpxpy |
| cow-vision | gemini_detect_elements, gemini_layout_analysis | Gemini API |
| cow-review | queue_review, get_queue, submit_review | SQLite |
| cow-export | generate_latex, compile_pdf, mathpix_mmd_to_pdf | XeLaTeX, Pandoc |
| cow-storage | save_result, load_result, list_sessions | Filesystem |

---

## Technology Stack

- **Orchestrator:** Claude Code CLI (Agent Teams, tmux), MAX X20
- **MCP Server:** cow-mcp (Python, FastMCP or stdio)
- **OCR:** Mathpix API v3 via mpxpy SDK
- **Vision:** Gemini 3.0 Pro API (google-genai SDK)
- **Reasoning:** Claude Opus 4.6 (Claude Code native, no API)
- **PDF:** XeLaTeX + xetexko + kotex + Noto CJK KR fonts
- **Automation:** Pandoc + XeLaTeX pipeline
- **Storage:** Filesystem (session-based) + SQLite (review queue)
- **Models:** Pydantic v2 for all interface contracts
- **CLI:** Typer + Rich (existing, reused)

---

## Codebase Impact

**Reuse (5 modules):** mathpix/client.py (modernize API calls), semantic/separator.py (712L, bbox logic), review/database.py (SQLite), export/ (extend for XeLaTeX), config.py (configuration)

**Remove (3 modules, ~1485L):** claude/orchestrator.py, claude/stage_agents.py, claude/mcp_servers.py — all SDK-dependent, incompatible with MCP Server architecture.

**New:** cow-mcp package (6 MCP servers), Pydantic models for stage contracts, Gemini API client, XeLaTeX compilation module.

---

## Risk Assessment

6 identified risks, none CRITICAL unmitigated. Highest: R-5 (Claude vision image Read bug, score 7) mitigated by using MCP tool to pass image data instead of Read tool. R-3 (XeLaTeX complex layout, score 6) mitigated by Mathpix converter backup path.

---

## Phase 4 Input Summary

The architect for Phase 4 should:
1. Read all 3 feasibility reports for detailed technical constraints
2. Design MCP Server implementation details (protocol, tool signatures, error handling)
3. Plan the codebase migration (remove SDK modules, restructure into cow-mcp)
4. Define task decomposition with non-overlapping file ownership
5. Ensure Pydantic models enforce interface contracts at runtime
6. Plan ~/.claude/ integration (MCP server registration, workflow configuration)
