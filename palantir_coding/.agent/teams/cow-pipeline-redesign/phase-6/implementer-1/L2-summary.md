# Implementer-1 Summary — Foundation + Ingest + Storage

## Overview
Built the foundation layer for the COW MCP pipeline: package infrastructure,
all Pydantic interface contracts, and two MCP servers (ingest, storage).
16 files created, all acceptance criteria verified.

## T-1: Package Infrastructure + Pydantic Models (Critical Path)

### Package Setup
- Created `cow/cow-mcp/` with pyproject.toml containing all dependencies from plan §9
- Fixed build-backend: plan specified `setuptools.backends._legacy:_Backend` (doesn't exist),
  corrected to `setuptools.build_meta`
- Created venv at `cow/cow-mcp/.venv/`, all deps installed successfully
- Key versions: mcp 1.26.0, pydantic 2.12.5, Pillow 12.1.0, pypdf 6.7.0

### Pydantic Models
All 8 model files follow plan §5.1-§5.7 exactly:
- **common.py**: BBox (with x2/y2/area/center properties), Dimensions, SessionInfo, RegionSource enum
- **ingest.py**: IngestResult (file_path, file_type, dimensions, preprocessed_path, dpi, color_space)
- **ocr.py**: OcrResult, MathElement, OcrRegion, Diagram — most complex model file
- **vision.py**: VisionResult, DiagramElement, DiagramInternals, SpatialRelation, LayoutAnalysis, CombinedRegion
- **verify.py**: VerificationResult, OcrCorrection, MathError, LogicIssue
- **compose.py**: CompositionResult, EditAction, DocumentMetadata
- **export.py**: ExportResult, LatexSource
- **models/__init__.py**: Re-exports all 22 model classes with __all__

### Verification
- All imports work from `cow_mcp.models`
- JSON round-trip verified for every model type
- Pydantic validation constraints (ge, le, Literal) all functional

## T-2: cow-ingest MCP Server

### Implementation
- **validator.py**: `validate_image()` and `validate_pdf()` with full validation
  - Image: format check (PNG/JPEG/TIFF/WebP), normalization (resize >4000px, convert to PNG)
  - PDF: page count check (max 2), dimension extraction, copy to session dir
  - Structured error handling for all failure modes
- **__main__.py**: FastMCP server with `cow_validate_image` and `cow_validate_pdf` tools
  - Uses FastMCP decorator pattern (Lead-approved deviation from plan's low-level Server pattern)
  - Error responses as JSON with error field, not exceptions

### Design Decisions
- Tool names prefixed with `cow_` to avoid collisions with other MCP servers
- Session directories created per-validation call with uuid-based IDs
- Color mode conversion handled (CMYK → RGB) before PNG save

## T-3: cow-storage MCP Server

### Implementation
- **filesystem.py**: `SessionStorage` class with save/load/list/create operations
  - Base dir: `~/.cow/sessions/` (plan §5.17)
  - JSON files at `{base_dir}/{session_id}/{stage}.json`
  - Metadata stored in `metadata.json` per session
- **__main__.py**: FastMCP server with 4 tools:
  - `cow_save_result(session_id, stage, data)` — save JSON data
  - `cow_load_result(session_id, stage)` — load or return null
  - `cow_list_sessions()` — list all sessions
  - `cow_create_session(session_id, source_path, source_type, page_count)` — create with metadata

### Design Decisions
- `data` parameter as JSON string (not dict) in MCP tool — MCP tool args are strings
- `list_sessions()` handles both metadata.json sessions and bare directories gracefully
- `create_session()` added beyond plan spec — needed for proper session lifecycle

## Plan Deviations
1. **DEV-1**: pyproject.toml build-backend fixed (setuptools.build_meta)
2. **DEV-2**: FastMCP pattern for all servers (Lead-approved)
3. **DEV-3**: Added `cow_create_session` tool to storage server (not in plan, but needed for session metadata)
4. **DEV-4**: Tool names prefixed with `cow_` (avoids namespace collisions)
