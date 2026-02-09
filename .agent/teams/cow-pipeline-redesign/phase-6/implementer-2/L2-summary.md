# L2 Summary — Implementer-2 (OCR + Vision Servers)

## Overview

Implemented 8 files across 2 MCP servers: cow-ocr (T-4, 5 files) and cow-vision (T-5, 3 files).
Both servers use FastMCP pattern (consistent with Impl-1's ingest/storage servers).

## T-4: cow-ocr MCP Server

### Architecture
- `client.py` (MathpixMcpClient): Modernized from cow-cli/mathpix/client.py.
  - Env var config (`MATHPIX_APP_ID`, `MATHPIX_APP_KEY`) replaces keyring/config module.
  - Returns `OcrResult` Pydantic model instead of MathpixResponse.
  - New `_response_to_ocr_result()` maps Mathpix JSON → OcrResult (text, math_elements, regions, diagrams).
  - Preserved: async httpx, exponential backoff retry (3 retries, codes 429/500/502/503/504).
  - PDF support: multipart upload → polling → lines.json merge across pages.

- `separator.py`: Extracted `cnt_to_bbox()` from cow-cli `_cnt_to_region()`.
  - **COND-1 compliance verified**: None-return for len < 2, `max(0, min_x)` clamping, `max(1, width)` minimum.
  - All clamping happens BEFORE BBox Pydantic validation.
  - `process_mathpix_regions()`: converts Mathpix line_data → list[OcrRegion].

- `cache.py`: diskcache with SHA256(image_bytes + options_json) keys. 512MB limit.

- `__main__.py`: FastMCP tools: `cow_mathpix_ocr_image`, `cow_mathpix_ocr_pdf`, `cow_ocr_get_cache`.

### Acceptance Criteria
- AC-0: `python -m cow_mcp.ocr` starts via stdio — VERIFIED
- AC-1: mathpix_ocr_image calls v3/text → OcrResult — IMPLEMENTED
- AC-2: mathpix_ocr_pdf calls v3/pdf → OcrResult — IMPLEMENTED
- AC-3: get_cache returns cached OcrResult or null — IMPLEMENTED
- AC-4: client.py modernized (no cow_cli imports, env config, OcrResult) — VERIFIED
- AC-5: separator.py preserves _cnt_to_region semantics (COND-1) — VERIFIED (5 test cases)
- AC-6: Cache uses diskcache + SHA256 — IMPLEMENTED

## T-5: cow-vision MCP Server

### Architecture
- `gemini.py` (GeminiVisionClient): google-genai SDK integration.
  - Env var config (`GEMINI_API_KEY`).
  - `detect_elements()`: sends image + structured prompt → DiagramInternals list.
  - `analyze_layout()`: sends image → LayoutAnalysis (columns, reading_order, spatial_relations).
  - **COND-3 compliance**: `_normalize_bbox()` detects [0,1] vs pixel coords, converts to pixels.
  - Confidence threshold filtering (default 0.3, configurable).
  - Exponential backoff retry (3 retries). Graceful degradation (returns empty, never crashes).
  - Structured JSON output via `response_json_schema` config.

- `__main__.py`: FastMCP tools + merge_regions() algorithm.
  - Tools: `cow_gemini_detect_elements`, `cow_gemini_layout_analysis`, `cow_merge_regions`.
  - **COND-4 compliance verified**: IoU-based greedy matching, threshold 0.5.
    - IoU > 0.5 → MERGED (bbox=union, content=Mathpix preferred, confidence=max).
    - IoU ≤ 0.5 → separate MATHPIX/GEMINI CombinedRegions.

### Acceptance Criteria
- AC-0: `python -m cow_mcp.vision` starts via stdio — VERIFIED
- AC-1: gemini_detect_elements → DiagramInternals list — IMPLEMENTED
- AC-2: gemini_layout_analysis → LayoutAnalysis — IMPLEMENTED
- AC-3: Uses google-genai SDK with structured output — VERIFIED
- AC-4: Results tagged source="gemini" — IMPLEMENTED
- AC-5: Graceful degradation (returns empty on failure) — IMPLEMENTED
- AC-6: Bbox normalization (COND-3) + confidence filtering — VERIFIED
- AC-7: merge_regions() IoU algorithm (COND-4) — VERIFIED (3 test scenarios)

## Decisions
1. merge_regions() placed in vision/__main__.py (not gemini.py) — it's an MCP tool that
   combines data from both servers, not pure Gemini logic.
2. Gemini structured output uses raw JSON schema (not Pydantic response_schema) for
   maximum control over the output format.
3. BBox normalization uses all-values ≤ 1.0 heuristic to detect normalized coordinates.

## Self-Test Results
- All imports: PASS
- COND-1 (5 cases): PASS — empty, single-point, negative, zero-dim, normal
- COND-4 (3 cases): PASS — overlap merge, unmatched mathpix, unmatched gemini
- Server startup (both): PASS — no import errors, clean stdio wait
