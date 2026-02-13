# L2 Summary — Implementer-3 (Review + Export + .mcp.json)

## Status: COMPLETE

## Tasks Completed

### T-6: cow-review MCP server (4 files, ~454 lines total)

**Key decisions:**
- Full async rewrite (CH-1.2): `create_async_engine` + `async_sessionmaker` + `aiosqlite` driver
- Simplified from cow-cli's 600+ line ReviewDatabase to 3 MCP-facing operations
- Added `session_id` column (not in cow-cli) to support multi-session review queues
- Removed ReviewerStats ORM (not needed for MCP — review is per-session, not per-reviewer)
- Kept audit logging for all operations (queue, review)

**Adaptation from cow-cli:**
- `models.py`: Same enums (ReviewStatus, ReviewDecision, AuditAction). ReviewItem schema adapted: replaced `image_path` with `session_id`, `element_data` with `original_content`, `modifications` with `modified_content`. Removed `confidence_rate`. Added `session_id` index.
- `database.py`: Every sync method → async. `@contextmanager` → `@asynccontextmanager`. `session.execute()` → `await session.execute()`. `Base.metadata.create_all()` → `conn.run_sync(Base.metadata.create_all)`.

**MCP tools:**
- `cow_queue_review(session_id, items_json)` — bulk queue verification findings
- `cow_get_queue(session_id, status?)` — filtered list with stats
- `cow_submit_review(item_id, decision, modified_content?, comment?)` — record decision

### T-7: cow-export MCP server (4 files, ~495 lines total)

**Key decisions:**
- Complete LaTeX rewrite (NOT adaptation) — cow-cli used pdfLaTeX, we use XeLaTeX
- CH-4.4 applied: `\usepackage{kotex}` only, no separate xetexko
- Preamble includes: kotex, Noto CJK KR (3 fonts), amsmath, amssymb, mathtools, tikz, pgfplots, graphicx, geometry, hyperref
- `_compose_body()` extracts body from CompositionResult.latex_source (handles both wrapped and unwrapped LaTeX)
- Metadata applied as LaTeX commands: \title, \date, \maketitle, plus subject/grade display

**compiler.py:**
- Async subprocess execution via `asyncio.create_subprocess_exec`
- Multi-pass compilation (up to 3) for cross-references
- Font availability check via `fc-list`
- Auto-fix: font not found → fallback chain, missing pgfplots → auto-add
- Mathpix /v3/converter backup: POST MMD content → poll for PDF → download

**MCP tools:**
- `cow_generate_latex(composition_json, template?)` — CompositionResult → LatexSource + temp .tex file
- `cow_compile_pdf(latex_path, output_dir?)` — xelatex compilation with font check
- `cow_mathpix_mmd_to_pdf(mmd_content)` — Mathpix API fallback

### T-8: .mcp.json (1 file, 47 lines)

All 6 servers registered with `python -m cow_mcp.{name}` pattern:
- cow-ingest, cow-ocr, cow-vision, cow-review, cow-export, cow-storage
- API key placeholders: MATHPIX_APP_ID, MATHPIX_APP_KEY (ocr+export), GEMINI_API_KEY (vision)
- All cwd: "cow/cow-mcp"

## Self-Test Results

10 import/functional tests + 6 async database tests = **ALL PASSED**:
1. Review module imports
2. Export module imports
3. Models integration
4. LatexGenerator functional test (Korean math composition)
5. Package extraction (13 packages)
6. AsyncReviewDatabase instantiation
7. ReviewItem ORM schema validation
8. LatexSource Pydantic model
9. ExportResult Pydantic model
10. CH-4.4 compliance (no xetexko usepackage)
11. Async DB initialize
12. Async queue_review (2 items)
13. Async get_queue (filtered)
14. Async submit_review (approved)
15. Async get_queue_stats (total/pending/reviewed)
16. .mcp.json validity (6 servers, correct structure)

## Risks and Notes

- XeLaTeX compilation untested on this machine (no TeX Live installed in WSL)
- Mathpix /v3/converter endpoint may have different response format than implemented (needs real API test)
- Font fallback chain only handles Noto → Nanum. If neither available, compilation will fail.
