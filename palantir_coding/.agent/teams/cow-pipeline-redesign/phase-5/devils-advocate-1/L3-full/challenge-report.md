# Phase 5 Challenge Report — COW Pipeline Redesign Implementation Plan

**Devil's Advocate:** devils-advocate-1
**Date:** 2026-02-09
**Plan Under Review:** `docs/plans/2026-02-09-cow-pipeline-redesign.md` (1274 lines)
**Architecture Under Review:** `.agent/teams/cow-pipeline-redesign/phase-3/architect-1/L3-full/architecture-design.md`
**GC Version:** GC-v4

---

## Category 1: Correctness

### CH-1.1: cnt_to_bbox() behavioral regression vs _cnt_to_region() — HIGH

**Evidence:**
- Original (`separator.py:288-327`): Returns `None` for `len(cnt) < 2`; clamps negative coords to 0 via `max(0, min_x)`; forces minimum dimension via `if width < 1: width = 1`; catches `IndexError`/`TypeError` gracefully.
- Plan (`§5.11, lines 696-706`): Raises `ValueError("Empty contour")` for empty input; does NOT check `len(cnt) < 2`; relies on Pydantic `BBox(ge=0)` validator for coord clamping (raises `ValidationError` instead of silent clamp); relies on Pydantic `ge=1` for min dimensions (raises `ValidationError` instead of silent minimum).

**Impact:** The plan's version will **raise runtime errors** where the original silently recovered. A Mathpix API response with a 1-point contour or negative coordinates (valid in some coordinate systems) will crash the OCR pipeline instead of producing a degraded-but-usable result.

**Mitigation:** Preserve the original's error-handling semantics: return `None` (or optional BBox) for degenerate contours, clamp coordinates before constructing BBox, add explicit minimum dimension logic before Pydantic validation.

### CH-1.2: ReviewDatabase sync→async migration not acknowledged — MEDIUM

**Evidence:**
- Existing `cow-cli/review/database.py` uses **synchronous SQLAlchemy** (`create_engine`, `sessionmaker`, `@contextmanager`, no `async` anywhere).
- Plan §5.14 says: "Keep SQLAlchemy + aiosqlite pattern."
- T-6 AC-4 says: "uses SQLAlchemy + aiosqlite, keeps same table schema."

**Impact:** The existing code has zero async code. The plan claims to "keep" an aiosqlite pattern that doesn't exist. This is not "adaptation" — it's a rewrite from synchronous to asynchronous ORM pattern, which involves:
1. Replacing `create_engine` with `create_async_engine`
2. Replacing `sessionmaker` with `async_sessionmaker`
3. Replacing `@contextmanager` with `@asynccontextmanager`
4. All database methods becoming `async def`

**Mitigation:** Either acknowledge this as a full rewrite (increasing T-6 complexity estimate), or keep synchronous SQLAlchemy (simpler, MCP server can use `asyncio.to_thread()` for sync DB calls). The second option is safer and matches "keep same table schema" intent.

### CH-1.3: MathpixMcpClient missing exception classes — MEDIUM

**Evidence:**
- Existing `cow-cli/mathpix/client.py` imports 7 exception classes from `cow_cli.mathpix.exceptions`: `MathpixError`, `MathpixAuthError`, `MathpixRateLimitError`, `MathpixTimeoutError`, `MathpixNetworkError`, `MathpixAPIError`, `parse_api_error`.
- Plan §5.10 mentions "keeps async httpx + retry logic intact" but doesn't mention recreating or importing exception classes.
- No exception module appears in §3 file ownership, §4 task list, or §9 dependencies.

**Impact:** The retry logic in client.py catches these specific exception types. Without them, the modernized client either needs to recreate them locally or use generic exceptions, which degrades error diagnostics.

**Mitigation:** Add an `ocr/exceptions.py` file to the plan (Impl-2 ownership) or document that generic `httpx.HTTPError` will replace the custom hierarchy.

### CH-1.4: plan's `OcrRegion.bbox` is required but Mathpix regions don't always have bbox — MEDIUM

**Evidence:**
- Plan §5.3 defines `OcrRegion.bbox: BBox` (required field, no `Optional`).
- Existing `separator.py:198-202` shows `region = None` when no `cnt` is present — some Mathpix elements lack contour data.
- Original separator returns `None` for region when contour is missing.

**Impact:** Mathpix API responses can contain line items without `cnt` (contour) or `region` data. The Pydantic model will reject these with `ValidationError`, losing valid content data.

**Mitigation:** Make `OcrRegion.bbox: Optional[BBox] = None` to match reality.

---

## Category 2: Completeness

### CH-2.1: Missing error/exception module for OCR server — MEDIUM

**Evidence:** See CH-1.3. The original client.py relies on a rich exception hierarchy (7 classes). The plan doesn't list a replacement.

**Mitigation:** Add `cow_mcp/ocr/exceptions.py` to §3 Implementer-2 file list and T-4 file list.

### CH-2.2: Missing `models/__init__.py` re-export specification — LOW

**Evidence:**
- T-1 AC-1 says: "All 8 model files importable: `from cow_mcp.models import IngestResult, OcrResult, ...`"
- But `models/__init__.py` is listed in §3 as just "(NEW)" with no content spec in §5.
- The `__init__.py` needs explicit re-exports for the AC to pass.

**Mitigation:** Add a brief §5 spec for `models/__init__.py` showing the re-export pattern, or document it as an implicit part of T-1.

### CH-2.3: No cow-storage MCP server __main__.py spec — LOW

**Evidence:**
- §5.17 covers `storage/filesystem.py` but there's no §5.X for `storage/__main__.py`.
- §5.18 says "All 6 MCP servers follow the same pattern shown in §5.9" — but doesn't list the specific tools for cow-storage.
- The tool signatures `save_result`, `load_result`, `list_sessions` from T-3 need JSON Schema definitions.

**Mitigation:** Not blocking — the pattern is clear enough from §5.9 and T-3 ACs. Document this as "follow pattern from §5.9/§5.18."

### CH-2.4: No merge_regions() function specified — MEDIUM

**Evidence:**
- R-1 mitigation (§8, line 1068) says: "Implementation: `merge_regions()` function in vision/__main__.py"
- But §5 contains no spec for `merge_regions()`. The IoU-based merge strategy is described in prose but not in code spec.
- This is the most complex algorithmic component in the pipeline (dual-source bbox reconciliation).

**Mitigation:** Add a §5.X spec for `merge_regions()` in vision/__main__.py with the IoU threshold, merge logic, and output format. This is critical because it's identified as risk hotspot R-1.

### CH-2.5: Review server missing cow-review models.py spec — LOW

**Evidence:**
- §3 lists `review/models.py` as Impl-3's file.
- T-6 AC-5 says "models.py adapted from cow-cli/review/models.py: same ORM models, updated imports."
- But there's no §5.X spec for it — not even a brief reference spec.

**Mitigation:** Not blocking. The adaptation is straightforward (import path changes only).

### CH-2.6: Mathpix `process_pdf` polling logic not specified — MEDIUM

**Evidence:**
- Existing `client.py:333-463` shows PDF processing is **significantly more complex** than image processing: upload → get PDF ID → poll status URL → fetch lines.json on completion.
- Plan §5.10 specifies `ocr_pdf(self, path, pages)` as a simple method signature but doesn't mention the polling workflow, timeout handling, or the separate `lines.json` endpoint.
- This is ~130 lines of complex async code in the original.

**Mitigation:** Add a brief note in §5.10 acknowledging the polling workflow: upload, poll status, fetch `lines.json`, parse per-page results. Implementer-2 needs to know this isn't a simple API call.

---

## Category 3: Consistency

### CH-3.1: §3 file ownership vs §4 task list file count discrepancy — LOW

**Evidence:**
- §3 Implementer-1 lists 16 files. §4 T-1 says "Files: pyproject.toml, cow_mcp/__init__.py, models/ (8 files)" = 10 files. T-2 says 3 files. T-3 says 3 files. Total: 10+3+3 = 16. ✓ Consistent.
- §3 Implementer-2 lists 8 files. T-4 says 5 files. T-5 says 3 files. Total: 5+3 = 8. ✓ Consistent.
- §3 Implementer-3 lists 9 files. T-6 says 4 files. T-7 says 4 files. T-8 says 1 file. Total: 4+4+1 = 9. ✓ Consistent.

**Verdict:** §3 and §4 are fully consistent. No issue found.

### CH-3.2: Architecture design missing `common.py` in package structure — LOW

**Evidence:**
- Architecture design §4 package structure lists `models/` with: `ingest.py, ocr.py, vision.py, verify.py, compose.py, export.py` (6 files).
- Plan §2 and §3 list `models/` with: `__init__.py, common.py, ingest.py, ocr.py, vision.py, verify.py, compose.py, export.py` (8 files).
- The `common.py` (BBox, Region, Dimensions, SessionInfo, RegionSource) was added in Phase 4.

**Impact:** This is a Phase 4 design decision, not an inconsistency bug. The architecture design was at a higher level of abstraction.

**Verdict:** Not an issue. Phase 4 refined the architecture.

### CH-3.3: GC-v4 OcrResult `regions` field vs plan OcrRegion field mismatch — LOW

**Evidence:**
- GC-v4 interface (line 124): `regions: [{id, type, bbox, content}]` (4 fields)
- Plan §5.3 OcrRegion: `id, type, bbox, content, confidence, parent_id, children_ids` (7 fields)

**Impact:** The plan extends the GC-v4 contract with 3 additional optional fields. This is acceptable — the extra fields are all `Optional` with defaults.

**Verdict:** Acceptable extension, not a breaking inconsistency.

### CH-3.4: T-8 dependency listing incomplete — LOW

**Evidence:**
- T-8 dependencies say: "T-2, T-3, T-4, T-5, T-6, T-7 (all servers must be defined)."
- But §4 dependency graph shows T-8 only after T-7 (Impl-3's final task).
- T-8 actually only needs the module paths to exist — it just writes a JSON file.
- The dependency graph correctly shows it under T-7, but T-8's textual deps list ALL tasks.

**Impact:** The textual dependency is overly conservative. T-8 writes a static JSON file that references module paths. It doesn't need the servers to be functional, just their `__main__.py` paths to exist.

**Mitigation:** Clarify T-8 only truly depends on knowing the module paths (available from §2 package structure). In practice, since Impl-3 writes it last, the dependency is naturally satisfied.

---

## Category 4: Feasibility

### CH-4.1: Implementer-1 file count (16 files) — Architect Target #4 — MEDIUM

**Evidence:**
- CLAUDE.md §6 Pre-Spawn Checklist says: ">4 files → MANDATORY split into multiple tasks/teammates."
- Impl-1 has 16 files across 3 tasks (T-1: 10, T-2: 3, T-3: 3).
- Plan's justification: "most are <30 line boilerplate (__init__.py, model files)."
- T-1 alone has 10 files (1 pyproject.toml + 1 __init__.py + 8 model files).

**Analysis:**
The BUG-002 lesson states large-task teammates auto-compact. However, T-1's 10 files are genuinely small:
- 7 `__init__.py` files: ~5-10 lines each
- 8 model files: ~30-60 lines each with full Pydantic specs provided in §5
- pyproject.toml: ~50 lines, provided in §9

T-1 is ~400 lines of new code with complete specs provided. T-2 and T-3 are ~100 lines each.
The real risk is context exhaustion from reading both existing cow-cli files AND writing new files.

**Verdict:** MEDIUM risk. The file count is high but complexity-per-file is low. BUG-002 suggests splitting T-1 into T-1a (pyproject + models) and T-1b (ingest + storage), but this is optional given the boilerplate nature.

**Mitigation:** If Impl-1 compacts during T-1, split T-1 into T-1a (models) and T-1b (ingest+storage) with a fresh spawn.

### CH-4.2: MCP Python SDK API stability — Architect Target #1 — HIGH

**Evidence:**
- Plan uses `from mcp.server import Server`, `from mcp.server.stdio import stdio_server`, `import mcp.types as types`.
- The `mcp` PyPI package exists but its API has evolved significantly.
- The plan specifies `mcp>=1.0.0` in dependencies.
- The specific pattern used (decorators `@server.list_tools()`, `@server.call_tool()`, `stdio_server()` context manager) needs verification against the current SDK version.
- Risk: If the SDK uses `FastMCP` or a different initialization pattern in current versions, ALL 6 `__main__.py` files need rewriting.

**Analysis:**
The MCP Python SDK has multiple versions with breaking changes. The pattern shown in §5.9 uses the low-level `Server` class, which is the stable API. However, the `stdio_server()` function may have moved or changed signatures. A single version pin check would resolve this.

**Mitigation:** Before implementation starts, Implementer-1 should run:
```bash
pip install mcp>=1.0.0
python -c "from mcp.server import Server; from mcp.server.stdio import stdio_server; import mcp.types as types; print('OK')"
```
If this fails, the __main__.py pattern needs updating. This is a 5-minute check that avoids 6-file rewrites.

### CH-4.3: google-genai structured output for bbox — Architect Target #2 — HIGH

**Evidence:**
- Plan §5.13 uses `import google.genai as genai` and `genai.Client(api_key=...)`.
- The import is `google.genai` (not `google.generativeai`).
- Plan assumes Gemini 3.0 Pro returns structured bbox JSON from a text prompt.
- Gemini bbox output format may use normalized coordinates [0,1] or pixel coordinates — this affects all downstream math.
- mAP ~0.43 means ~57% of bounding boxes will be inaccurate.

**Analysis:**
The `google-genai` package (not `google-generativeai`) is the newer SDK. It supports structured output via `response_schema` parameter. However:
1. Bbox output format (normalized vs pixel) is not specified in the plan.
2. The plan assumes bbox output from a generic text prompt, but Gemini's best bbox results come from specific structured output configuration.
3. At mAP ~0.43, the merge logic needs to weight Gemini results significantly lower than Mathpix.

**Mitigation:**
1. Specify coordinate format (normalized [0,1] or pixel absolute) in the plan.
2. Add a confidence threshold filter (e.g., skip Gemini regions with confidence < 0.3).
3. Document the structured output configuration for Gemini bbox requests.

### CH-4.4: XeLaTeX + kotex + amsmath coexistence — Architect Target #3 — MEDIUM

**Evidence:**
- Plan §5.15 preamble loads: `xetexko`, `kotex`, `amsmath`, `amssymb`, `amsthm`, `mathtools`, `tikz`, `pgfplots`.
- `xetexko` and `kotex` are both Korean TeX packages. Loading both is typically redundant — `xetexko` IS the XeLaTeX Korean support.
- `kotex` is the umbrella package that automatically selects the right backend. Under XeLaTeX, `\usepackage{kotex}` internally loads `xetexko`.
- Loading both `xetexko` AND `kotex` may cause option clashes or double-loading warnings.

**Analysis:**
Research report R-3 says "xetexko recommended over LuaLaTeX for Korean" and "kotex" is the standard. The typical pattern is:
- Either `\usepackage{kotex}` alone (which auto-selects xetexko under xelatex)
- Or `\usepackage{xetexko}` alone with manual font configuration

Loading both is unusual and may cause warnings or subtle issues with font selection priority.

**Mitigation:** Use only `\usepackage{kotex}` (which handles xetexko internally) OR only `\usepackage{xetexko}` with manual configuration. Remove the redundant package. Test the exact preamble before implementation.

### CH-4.5: cow-cli module adaptation scope — Architect Target #5 — MEDIUM

**Evidence:**
- `client.py` (604L): Plan says "moderate rewrite" — but the actual changes involve removing 7 cow_cli imports, removing keyring/config integration, changing return types to `OcrResult`, adding `_response_to_ocr_result()` conversion. This is ~40% of the file.
- `separator.py` (712L): Plan says "extract ONLY _cnt_to_region()" — this is correct. Only ~40 lines needed out of 712. The rest of the class is not needed. But `process_mathpix_regions()` is entirely NEW code (not adaptation).
- `database.py` (622L): Plan says "simplify to 3 MCP operations" — but the sync→async migration (CH-1.2) makes this more like 60% rewrite.
- `export/latex.py`: Plan acknowledges "FULL rewrite for XeLaTeX+kotex" — this is honest.

**Analysis:** The adaptation estimates are generally accurate except for `database.py` where the sync→async claim is misleading. Overall, the "adaptation" framing correctly sets expectations for `client.py` and `separator.py`, but `database.py` adaptation is underestimated.

**Mitigation:** Acknowledge `database.py` as "significant rewrite" rather than "adaptation." Consider keeping sync SQLAlchemy.

---

## Category 5: Robustness

### CH-5.1: Mathpix API failure has no pipeline bypass — MEDIUM

**Evidence:**
- Architecture §6 says: "OCR Mathpix API failure → Retry once, then inform user."
- But there's no alternative OCR path. If Mathpix is down, the entire pipeline is blocked.
- Gemini has graceful degradation (skip to VERIFY with OCR-only data) but OCR has no equivalent.

**Analysis:** This is acceptable for v0.1. Mathpix is the ONLY OCR source — there's no alternative for Korean math OCR at this quality level. The plan's approach (retry + inform user) is appropriate.

**Verdict:** Acceptable. No mitigation needed beyond the existing retry logic.

### CH-5.2: Gemini garbage bbox data propagation — MEDIUM

**Evidence:**
- R-3 mitigation says "source tagging allows downstream stages to weight confidence by source."
- But the VERIFY stage (Claude native reasoning) has no specification for how it consumes `RegionSource` tags.
- If Gemini returns bbox data with xy coordinates outside the image dimensions, the `CombinedRegion` will pass Pydantic validation (BBox only checks `ge=0`) but be semantically invalid.

**Mitigation:** Add bounds validation in the merge step: reject Gemini regions where bbox exceeds image dimensions (available from IngestResult.dimensions). Add this as an explicit check in `merge_regions()`.

### CH-5.3: XeLaTeX compilation failure recovery path — LOW

**Evidence:**
- Plan §5.16 `_auto_fix_errors()` handles: missing package, undefined control sequence, font not found.
- Fallback to Mathpix /v3/converter is documented.
- The recovery chain is: auto-fix → retry → Mathpix converter → fail gracefully.

**Verdict:** Well-specified. No additional mitigation needed.

### CH-5.4: Large MCP responses (>100KB JSON) — LOW

**Evidence:**
- R-5 identifies this risk and proposes: compact JSON + cow-storage persistence for large results.
- OcrResult with `raw_response: dict` (full Mathpix API JSON) could be >100KB for complex documents.

**Mitigation:** Already addressed in R-5. Consider adding a response size check in the __main__.py pattern — if result JSON exceeds a threshold, save to cow-storage and return a reference path instead.

### CH-5.5: No session cleanup / TTL for ~/.cow/sessions/ — LOW

**Evidence:**
- cow-storage saves all session results to `~/.cow/sessions/{id}/`.
- No cleanup mechanism specified — sessions accumulate indefinitely.
- Each session could store ~200KB-1MB of JSON across 6 stage files.

**Mitigation:** Add a `cleanup_old_sessions(max_age_days=30)` method to SessionStorage. Not blocking for v0.1.

---

## Category 6: Interface Contracts

### CH-6.1: VisionResult.combined_regions merge logic unspecified — HIGH

**Evidence:**
- The `combined_regions: list[CombinedRegion]` field is where Mathpix and Gemini data merge.
- R-1 mitigation describes IoU > 0.5 merge strategy in prose (§8, line 1066-1068).
- But there's no §5 code spec for this critical algorithm.
- Questions unanswered:
  1. What happens when IoU is between 0.3 and 0.5? (Neither clearly overlapping nor separate)
  2. When merging, which source's type classification takes priority?
  3. Is the merged bbox the union or intersection of the two originals?
  4. What's the merged confidence score calculation?

**Mitigation:** Add a §5.X spec for `merge_regions()` that defines: IoU thresholds, merge priority (Mathpix for type, Gemini for internal elements), merged bbox = union, merged confidence = weighted average by source.

### CH-6.2: VERIFY and COMPOSE stages have no MCP tool contracts — LOW

**Evidence:**
- Stages 4 (VERIFY) and 5 (COMPOSE) are Claude native reasoning — no MCP tools.
- This means the "interface" is Claude reading VisionResult JSON and producing VerificationResult JSON.
- The plan doesn't specify how Claude receives and produces these structured results during orchestration.
- In Agent Teams mode, Claude Code reads JSON from cow-storage and produces JSON to cow-storage.

**Analysis:** This is by design (D-4). The orchestrator (Claude Code CLI) handles this natively. The interface is implicit: read from storage → reason → write to storage.

**Verdict:** Acceptable. The implicit interface is clear enough for the orchestrator.

### CH-6.3: cow-export `generate_latex` takes CompositionResult but latex_source already exists in it — MEDIUM

**Evidence:**
- `CompositionResult.latex_source: str` already contains "Complete LaTeX document source" (§5.6).
- T-7 AC-1: `generate_latex(composition, template?)` generates complete LaTeX document with kotex preamble.
- But if COMPOSE stage (Claude reasoning) already produced `latex_source`, what does `generate_latex()` add?

**Analysis:** There's ambiguity about what `generate_latex()` does:
- Option A: It wraps `composition.latex_source` (the body) with the Korean math preamble.
- Option B: It regenerates LaTeX from structured content data.

The plan's §5.15 suggests Option A (taking composition and wrapping with preamble). But then `CompositionResult.latex_source` is misnamed — it should be `latex_body` if it's just the body.

**Mitigation:** Clarify: `CompositionResult.latex_source` contains the body content; `generate_latex()` wraps it with preamble. OR: `CompositionResult.latex_source` is the complete document; `generate_latex()` validates and reformats it. Pick one and document.

### CH-6.4: LatexSource model has overlapping fields with CompositionResult — LOW

**Evidence:**
- `LatexSource` (§5.7): `content` (complete), `preamble`, `body`, `packages`
- `CompositionResult` (§5.6): `latex_source` (complete)
- Both contain the full LaTeX document. LatexSource splits it into components.

**Analysis:** These serve different purposes: CompositionResult is the COMPOSE stage output, LatexSource is the EXPORT stage's internal representation. The overlap is intentional.

**Verdict:** Acceptable design. Not an issue.

### CH-6.5: JSON serialization format for MCP tool I/O not fully specified — LOW

**Evidence:**
- §5.9 shows `result.model_dump_json()` for serialization.
- §5.18 says all servers follow this pattern.
- Pydantic v2's `model_dump_json()` produces compact JSON by default.
- Deserialization on the Claude Code side happens automatically (Claude reads JSON text).

**Verdict:** Sufficiently specified. Pydantic v2 `model_dump_json()` is deterministic.

---

## Summary of Findings

| ID | Category | Severity | Title | Mitigation |
|----|----------|----------|-------|-----------|
| CH-1.1 | Correctness | **HIGH** | cnt_to_bbox behavioral regression | Preserve original error-handling semantics |
| CH-1.2 | Correctness | MEDIUM | ReviewDatabase sync→async not acknowledged | Keep sync SQLAlchemy or acknowledge rewrite |
| CH-1.3 | Correctness | MEDIUM | Missing exception classes for OCR client | Add ocr/exceptions.py to plan |
| CH-1.4 | Correctness | MEDIUM | OcrRegion.bbox should be Optional | Make bbox Optional[BBox] |
| CH-2.1 | Completeness | MEDIUM | Missing OCR exception module | Add to §3 and T-4 |
| CH-2.2 | Completeness | LOW | Missing models/__init__.py spec | Document re-export pattern |
| CH-2.3 | Completeness | LOW | No storage __main__.py spec | Follow §5.9 pattern |
| CH-2.4 | Completeness | MEDIUM | No merge_regions() spec | Add §5.X with IoU logic |
| CH-2.5 | Completeness | LOW | Missing review/models.py spec | Straightforward adaptation |
| CH-2.6 | Completeness | MEDIUM | PDF polling logic not specified | Note polling workflow |
| CH-3.1 | Consistency | — | §3 vs §4 file counts | ✓ Consistent (no issue) |
| CH-3.2 | Consistency | LOW | Architecture missing common.py | Phase 4 refinement (acceptable) |
| CH-3.3 | Consistency | LOW | GC-v4 vs plan field extension | Acceptable extension |
| CH-3.4 | Consistency | LOW | T-8 over-conservative dependencies | Clarify true deps |
| CH-4.1 | Feasibility | MEDIUM | Impl-1 16-file count | Monitor for BUG-002; split if needed |
| CH-4.2 | Feasibility | **HIGH** | MCP SDK API stability | Run import check before implementation |
| CH-4.3 | Feasibility | **HIGH** | Gemini structured bbox output | Specify coord format, add confidence filter |
| CH-4.4 | Feasibility | MEDIUM | XeLaTeX + kotex redundancy | Use one Korean package, not both |
| CH-4.5 | Feasibility | MEDIUM | Adaptation scope underestimated for database.py | Acknowledge as rewrite |
| CH-5.1 | Robustness | MEDIUM | No Mathpix bypass | Acceptable for v0.1 |
| CH-5.2 | Robustness | MEDIUM | Gemini garbage bbox propagation | Add bounds validation in merge |
| CH-5.3 | Robustness | LOW | XeLaTeX failure recovery | Well-specified |
| CH-5.4 | Robustness | LOW | Large MCP responses | Already addressed in R-5 |
| CH-5.5 | Robustness | LOW | No session cleanup | Add TTL mechanism (post-v0.1) |
| CH-6.1 | Interface | **HIGH** | merge_regions() logic unspecified | Add §5.X code spec |
| CH-6.2 | Interface | LOW | VERIFY/COMPOSE implicit interface | Acceptable by design (D-4) |
| CH-6.3 | Interface | MEDIUM | generate_latex vs CompositionResult ambiguity | Clarify body vs complete doc |
| CH-6.4 | Interface | LOW | LatexSource/CompositionResult overlap | Acceptable (different stages) |
| CH-6.5 | Interface | LOW | JSON serialization format | Sufficiently specified |

---

## Verdict: CONDITIONAL_PASS

**Reasoning:**

### No CRITICAL issues found.

### HIGH issues (4):
1. **CH-1.1 (cnt_to_bbox regression):** Behavioral change from silent recovery to runtime errors. Clear mitigation: preserve original semantics.
2. **CH-4.2 (MCP SDK stability):** Import path uncertainty affects 6 files. Clear mitigation: single import verification test before implementation.
3. **CH-4.3 (Gemini bbox format):** Coordinate format unspecified. Clear mitigation: document format and add confidence filter.
4. **CH-6.1 (merge_regions unspecified):** Risk hotspot R-1's core algorithm has no code spec. Clear mitigation: add spec before implementation.

### All 4 HIGH issues have viable mitigations that can be addressed without restructuring the plan.

### MEDIUM issues (10):
Most are documentation gaps or minor specification omissions. None require architectural changes.

### LOW issues (10):
All are acceptable at current plan maturity.

### Overall Assessment:
The implementation plan is thorough and well-structured. The 10-section format covers all necessary dimensions. The task decomposition is logical, file ownership is consistent, and the dependency graph is sound. The main gaps are in under-specified algorithmic components (merge_regions), behavioral regression in adapted code (cnt_to_bbox), and external dependency uncertainties (MCP SDK, Gemini API format). These are all addressable within the current architecture.

**Recommendation:** Address the 4 HIGH issues before entering Phase 6. Estimated effort: ~2 hours of plan revision, no architectural changes needed.
