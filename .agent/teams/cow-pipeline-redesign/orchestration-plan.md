---
feature: cow-pipeline-redesign
current_phase: 4
gc_version: GC-v3
---

# Orchestration Plan

## Gate History
- Phase 1: APPROVED (2026-02-09) — Discovery + Requirements R1-R10 confirmed
- Phase 2: APPROVED (2026-02-09) — 3 feasibility reports (Mathpix, Claude Vision, PDF Gen)
- Phase 3: APPROVED (2026-02-09) — 6-stage pipeline + MCP Server architecture

## Phase 1 Summary
Requirements R1-R10 crystallized through freeform Q&A with user.
Key decisions: MCP Server architecture (D-1), 6-stage pipeline (D-2), no Anthropic API (D-8).

## Phase 2 Summary
3 parallel researchers investigated feasibility:
- Mathpix API: Math OCR EXCELLENT, bbox VERY GOOD, Korean printed GOOD
- Claude Vision: bbox NOT FEASIBLE, math reasoning BEST, logic detection BEST
- PDF Generation: XeLaTeX + kotex = gold standard, Pandoc for automation

Key finding: Claude bbox limitation → Gemini 3.0 Pro API added (D-3).

## Phase 3 Summary
Architecture designed: 6-stage pipeline with MCP Server tools.
VERIFY/COMPOSE stages use Claude native reasoning (D-4).
Interface contracts defined for all stage transitions.

## Active Teammates
(none — Phase 4 will spawn architect)

## Phase 4 Plan
- Architect spawns to create detailed implementation plan
- Input: GC-v3 + 3 research reports + existing cow-cli/ codebase
- Expected output: 10-section implementation plan with file ownership, task decomposition
