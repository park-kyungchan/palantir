# TEAM-MEMORY — COW Pipeline Redesign

## Lead
- Phase 4 COMPLETE — Gate 4 APPROVED, GC-v4, PT-v2
- Phase 5 COMPLETE — Gate 5 CONDITIONAL_PASS, GC-v5, PT-v3
- Phase 6 COMPLETE — Gate 6 APPROVED, GC-v6, PT-v4
  - 33 files, 3 implementers, 8 tasks, ~2887 lines total
  - All 4 Phase 5 conditions met (COND-1..4)
  - 4 plan deviations documented (DEV-1..4)
  - Phase 7-8 DEFERRED (self-tested; full integration requires API keys + TeX Live)

## implementer-1
- **Status: COMPLETE** — T-1, T-2, T-3 all done, all ACs verified
- T-1 (critical path): 10 files — pyproject.toml + __init__.py + 8 model files. All 22 models importable, JSON round-trip verified.
- T-2 (cow-ingest): FastMCP server with cow_validate_image, cow_validate_pdf. Image normalization, PDF page limit, structured errors.
- T-3 (cow-storage): FastMCP server with cow_save_result, cow_load_result, cow_list_sessions, cow_create_session. Filesystem at ~/.cow/sessions/.
- **Key findings:**
  - pyproject.toml build-backend must be `setuptools.build_meta` (plan's `setuptools.backends._legacy:_Backend` doesn't exist)
  - MCP SDK v1.26.0 installed — FastMCP is the recommended pattern (Lead-approved deviation)
  - Venv at `cow/cow-mcp/.venv/` — Impl-2/Impl-3 must activate this venv
  - Tool names prefixed with `cow_` to avoid MCP namespace collisions
  - Added `cow_create_session` tool beyond plan spec (needed for session metadata lifecycle)

## implementer-2
- **Status: COMPLETE** — T-4, T-5 all done, all ACs verified, 5 COND-1 + 3 COND-4 tests passed
- T-4 (cow-ocr): 5 files. MathpixMcpClient modernized from cow-cli (env vars, OcrResult return). separator.py cnt_to_bbox() preserves original _cnt_to_region() semantics (COND-1). diskcache SHA256 keys. FastMCP: cow_mathpix_ocr_image, cow_mathpix_ocr_pdf, cow_ocr_get_cache.
- T-5 (cow-vision): 3 files. GeminiVisionClient with google-genai SDK, structured JSON output schemas. Bbox normalization [0,1]→pixel (COND-3). merge_regions() IoU algorithm (COND-4): greedy matching, IoU>0.5→MERGED, Mathpix text preferred, confidence=max. FastMCP: cow_gemini_detect_elements, cow_gemini_layout_analysis, cow_merge_regions.
- **Key findings:**
  - google-genai SDK async: `client.aio.models.generate_content()` for non-blocking calls
  - Structured output: `response_mime_type="application/json"` + `response_json_schema` config
  - Gemini bbox normalization heuristic: all values ≤ 1.0 → normalized [0,1], else pixel coords
  - merge_regions() in vision/__main__.py (not gemini.py) — it's a cross-server MCP tool
  - _cnt_to_region() original: None for len<2, max(0,x) clamping, max(1,width) minimum — all preserved

## implementer-3
- **Status: COMPLETE** — T-6, T-7, T-8 all done, 16 self-tests passed
- T-6 (cow-review): 4 files. Full async rewrite (CH-1.2) — `create_async_engine` + `async_sessionmaker` + aiosqlite. 3 MCP tools: cow_queue_review, cow_get_queue, cow_submit_review. Added `session_id` column for multi-session support.
- T-7 (cow-export): 4 files. Complete LaTeX rewrite for XeLaTeX+kotex (not adaptation). CH-4.4 applied: `\usepackage{kotex}` only. Noto CJK KR fonts. compiler.py: async subprocess, multi-pass, font check, auto-fix, Mathpix /v3/converter backup.
- T-8 (.mcp.json): All 6 servers registered, API key placeholders as empty strings.
- **Key findings:**
  - SQLAlchemy async requires `conn.run_sync(Base.metadata.create_all)` for table creation (cannot use `Base.metadata.create_all(engine)` directly with async engine)
  - CH-4.4 nuance: plan §5.15 shows BOTH xetexko+kotex in preamble — the directive correction (kotex only) is correct
  - cow-cli ReviewDatabase had 600+ lines with claim/release/expire/vacuum — simplified to 3 operations for MCP use case
  - `asyncio.create_subprocess_exec` for XeLaTeX compilation avoids blocking the event loop
  - Font fallback: Noto → Nanum → system default chain in auto-fix

## architect-1 (Phase 4 — COMPLETE)
- Read 10 existing source files before writing specs
- Key findings:
  - cow-cli export/latex.py uses pdfLaTeX → needs FULL rewrite for XeLaTeX+kotex
  - separator.py (712L) → only need cnt_to_bbox() (~30L) + new process_mathpix_regions()
  - config.py keyring pattern → replaced by env vars in MCP servers
  - MathpixClient (604L) → moderate rewrite for new imports + OcrResult return type
- Proposed 3 implementers (not 4): grouped by dependency chains
- 8 tasks with T-1 as foundation blocking all others
- 5 Phase 5 challenge targets identified (MCP SDK, Gemini structured output, XeLaTeX+kotex, Impl-1 file count, adaptation scope)
