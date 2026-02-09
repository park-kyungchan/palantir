# L2 Summary — Phase 5 Plan Validation: COW Pipeline Redesign

**Reviewer:** devils-advocate-1
**Date:** 2026-02-09
**Verdict:** CONDITIONAL_PASS

## Overview

Reviewed the 1274-line implementation plan across 6 challenge categories. Found 24 issues:
0 CRITICAL, 4 HIGH, 10 MEDIUM, 10 LOW. No issues require architectural restructuring.

## HIGH Issues (4)

### CH-1.1: cnt_to_bbox behavioral regression
The plan's `cnt_to_bbox()` (§5.11) raises runtime errors where the original `_cnt_to_region()`
silently recovers — specifically for degenerate contours (len<2), negative coordinates, and
zero-dimension boxes. The Pydantic validators (`ge=0`, `ge=1`) turn graceful degradation into
`ValidationError` crashes.
**Fix:** Preserve original's `None`-return and clamp-before-validate pattern.

### CH-4.2: MCP SDK API stability uncertain
The plan uses `from mcp.server import Server; from mcp.server.stdio import stdio_server`
with `@server.list_tools()` and `@server.call_tool()` decorators. If the `mcp>=1.0.0` package
has different API shapes (e.g., `FastMCP`), all 6 server __main__.py files need rewriting.
**Fix:** Run import verification before Phase 6 starts.

### CH-4.3: Gemini bbox coordinate format unspecified
Plan assumes Gemini 3.0 Pro returns structured bbox JSON but doesn't specify whether
coordinates are normalized [0,1] or pixel absolute. This affects all downstream merge math.
**Fix:** Document coordinate format; add confidence threshold filter (skip <0.3).

### CH-6.1: merge_regions() algorithm unspecified
The most complex algorithm (dual-source bbox reconciliation, risk hotspot R-1) has only
prose description. IoU threshold, merge priority, bbox union/intersection strategy, and
confidence weighting are all unspecified.
**Fix:** Add §5.X code spec with explicit IoU logic.

## Key MEDIUM Issues

- **CH-1.2:** ReviewDatabase claimed as "keep SQLAlchemy + aiosqlite" but existing code is
  100% synchronous. Either acknowledge as full rewrite or keep sync (use asyncio.to_thread).
- **CH-1.3/2.1:** OCR client missing exception hierarchy (7 classes in original). Add
  `ocr/exceptions.py` to plan.
- **CH-1.4:** `OcrRegion.bbox` is required but some Mathpix elements lack bbox data.
  Should be `Optional[BBox]`.
- **CH-2.4:** Same as CH-6.1 — merge_regions needs a spec.
- **CH-2.6:** Mathpix PDF polling workflow (~130 lines) not mentioned in §5.10.
- **CH-4.4:** Loading both `xetexko` AND `kotex` is redundant — kotex auto-loads xetexko.

## What's Good

- §3/§4 file ownership and task decomposition are fully consistent
- Dependency graph is sound (T-1 → parallel T-2..T-7 → T-8)
- Pydantic model specs are detailed with proper validation rules
- Risk register covers the right areas (R-1 through R-5)
- Migration plan correctly identifies reusable vs removable modules
- XeLaTeX failure recovery chain is well-specified

## Verdict Rationale

CONDITIONAL_PASS because:
- No CRITICAL issues
- All 4 HIGH issues have clear, bounded mitigations
- No architectural changes needed
- Estimated plan revision effort: ~2 hours

## Detailed Report

Full challenge analysis with evidence and mitigations:
`L3-full/challenge-report.md`
