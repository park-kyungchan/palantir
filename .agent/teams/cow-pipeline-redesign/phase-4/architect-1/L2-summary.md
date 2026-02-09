# L2 Summary — COW Pipeline Redesign Implementation Plan

**Phase:** 4 (Detailed Design)
**Architect:** architect-1
**Date:** 2026-02-09
**Plan Location:** `docs/plans/2026-02-09-cow-pipeline-redesign.md`

## Design Overview

Complete implementation plan for the cow-mcp Python package — 6 MCP servers
exposing the COW pipeline as Claude Code CLI tools with Pydantic interface contracts.

## Key Design Decisions

### Implementer Decomposition (3 implementers)

| Implementer | Servers | File Count | Rationale |
|-------------|---------|------------|-----------|
| Impl-1 | models/ + ingest + storage | 16 (mostly boilerplate) | Foundation first — unblocks all others |
| Impl-2 | ocr + vision | 8 | External API pair — shared interface boundary |
| Impl-3 | review + export + .mcp.json | 9 | Output-side pair — both adapt cow-cli modules |

### Task Dependency Graph
```
T-1 (models + package) ← Impl-1, no deps
 ├── T-2 (ingest) ← Impl-1, blocked by T-1
 ├── T-3 (storage) ← Impl-1, blocked by T-1
 ├── T-4 (ocr) ← Impl-2, blocked by T-1
 ├── T-5 (vision) ← Impl-2, blocked by T-1
 ├── T-6 (review) ← Impl-3, blocked by T-1
 └── T-7 (export) ← Impl-3, blocked by T-1
      └── T-8 (.mcp.json) ← Impl-3, blocked by T-7
```

### Source Code Reuse Strategy
- **Adapt (significant rewrite):** mathpix/client.py → ocr/client.py, separator.py → ocr/separator.py
- **Adapt (moderate rewrite):** review/database.py, review/models.py, cache.py
- **Replace (new design):** export/latex.py (XeLaTeX+kotex preamble replaces pdfLaTeX)
- **Not used:** claude/orchestrator.py, claude/stage_agents.py, claude/mcp_servers.py

### Critical Interface: OcrResult → VisionResult
The most complex interface transition. Requires merging Mathpix bbox (from OCR)
with Gemini bbox (from Vision). Merge strategy uses IoU > 0.5 threshold.
Both implementations owned by Implementer-2 to ensure consistency.

## Verification Levels (V-HIGH items)
- models/common.py, models/ocr.py, models/vision.py — shared foundation
- ocr/client.py — Mathpix API integration (604L adaptation)
- ocr/separator.py — bbox conversion accuracy
- vision/gemini.py — Gemini API integration (new code)
- export/latex.py — Korean font + math package configuration

## Risk Register
| Risk | Mitigation |
|------|-----------|
| Dual-source bbox reconciliation | IoU merge + source tagging + keep originals |
| XeLaTeX + kotex conflicts | Font check at startup + fallback chain + Mathpix backup |
| Gemini bbox low accuracy (mAP 0.43) | Use for diagram internals only + confidence weighting |
| separator.py adaptation | Unit test against cow-cli fixtures + preserve original cnt data |

## Phase 5 Targets (5 assumptions to challenge)
1. MCP SDK API stability
2. Gemini structured output for bbox
3. XeLaTeX + kotex + amsmath coexistence
4. Implementer-1 file count (16 exceeds 4-file guideline)
5. cow-cli module adaptation scope
