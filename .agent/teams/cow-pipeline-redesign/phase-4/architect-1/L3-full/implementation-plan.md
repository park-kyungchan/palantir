# COW Pipeline Redesign — Implementation Plan

> **For Lead:** This plan is designed for Agent Teams native execution.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.
> Spawn implementers per §3 File Ownership Map. Each task has AC-0 plan verification.

**Goal:** Build the cow-mcp Python package — 6 MCP servers exposing the COW pipeline's
business logic as Claude Code CLI tools, with Pydantic interface contracts between all stages.

**Architecture Source:** `.agent/teams/cow-pipeline-redesign/phase-3/architect-1/L3-full/architecture-design.md`
**Global Context:** `.agent/teams/cow-pipeline-redesign/global-context.md` (GC-v3)
**Design Decisions:** D-1 through D-9 (see GC-v3 §Architecture Decisions)

**Pipeline:** Full Phase 6 — 3 implementers, parallel where possible.

---

## §1 Overview

**Feature:** COW Pipeline Redesign — MCP Server-centric architecture
**Complexity:** COMPLEX
**Estimated files:** ~30 new Python files + 1 pyproject.toml + 1 .mcp.json

### Success Criteria
1. All 6 MCP servers start via `python -m cow_mcp.{server}` with stdio transport
2. All 6 interface contracts (IngestResult → OcrResult → VisionResult → VerificationResult → CompositionResult → ExportResult) are Pydantic-validated
3. cow-ocr successfully calls Mathpix API v3/text and v3/pdf with caching
4. cow-vision successfully calls Gemini 3.0 Pro API for bbox detection
5. cow-export generates compilable XeLaTeX + kotex documents
6. cow-review manages SQLite review queue via MCP tools
7. cow-storage saves/loads session results to filesystem
8. All servers registered in `.mcp.json` with correct environment variables

---

## §2 Architecture Summary

### Pipeline Architecture (D-1, D-2)
```
Claude Code CLI (Orchestrator)
    ├── [MCP] cow-ingest ──── Pillow, PyPDF (validation)
    ├── [MCP] cow-ocr ─────── Mathpix API v3 (OCR + bbox)
    ├── [MCP] cow-vision ──── Gemini 3.0 Pro API (bbox + layout)
    ├── [NATIVE] VERIFY ───── Claude Opus 4.6 reasoning
    ├── [NATIVE] COMPOSE ──── Claude Opus 4.6 + user dialog
    ├── [MCP] cow-export ──── XeLaTeX + kotex (PDF generation)
    ├── [MCP] cow-review ──── SQLite (HITL queue)
    └── [MCP] cow-storage ─── Filesystem (session persistence)
```

### Key Decisions
- **D-1:** MCP Server-centric (Claude Code = native orchestrator)
- **D-2:** 6-stage pipeline (INGEST→OCR→VISION→VERIFY→COMPOSE→EXPORT)
- **D-3:** Gemini 3.0 Pro for bbox (Claude bbox NOT FEASIBLE)
- **D-4:** VERIFY/COMPOSE as Claude native reasoning (no MCP tool)
- **D-5:** XeLaTeX + kotex primary, Mathpix /v3/converter backup
- **D-7:** Reuse separator.py bbox logic from cow-cli
- **D-8:** No Anthropic API dependency (MAX X20 only)

### Package Structure
```
cow/cow-mcp/
├── pyproject.toml
├── cow_mcp/
│   ├── __init__.py
│   ├── models/           # Shared Pydantic interface contracts
│   │   ├── __init__.py
│   │   ├── common.py     # BBox, Region, Dimensions, SessionInfo
│   │   ├── ingest.py     # IngestResult
│   │   ├── ocr.py        # OcrResult, MathElement, OcrRegion, Diagram
│   │   ├── vision.py     # VisionResult, DiagramInternals, LayoutAnalysis
│   │   ├── verify.py     # VerificationResult, OcrCorrection, MathError
│   │   ├── compose.py    # CompositionResult, EditAction
│   │   └── export.py     # ExportResult, LatexSource
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── __main__.py   # MCP server entry point (stdio)
│   │   └── validator.py  # Image/PDF validation logic
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── client.py     # Modernized Mathpix client (from cow-cli)
│   │   ├── separator.py  # BBox conversion (from cow-cli)
│   │   └── cache.py      # Disk-based OCR cache
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── gemini.py     # Gemini 3.0 Pro client
│   ├── review/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── database.py   # SQLite HITL database (from cow-cli)
│   │   └── models.py     # SQLAlchemy ORM models (from cow-cli)
│   ├── export/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── latex.py      # LaTeX source generation with kotex
│   │   └── compiler.py   # XeLaTeX subprocess compilation
│   └── storage/
│       ├── __init__.py
│       ├── __main__.py
│       └── filesystem.py # Session-based file storage
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_ingest.py
    ├── test_ocr.py
    ├── test_vision.py
    ├── test_review.py
    ├── test_export.py
    └── test_storage.py
```

---

## §3 File Ownership Map

### Implementer-1: Foundation + Ingest + Storage (core infrastructure)
```
cow/cow-mcp/pyproject.toml                    (NEW)
cow/cow-mcp/cow_mcp/__init__.py               (NEW)
cow/cow-mcp/cow_mcp/models/__init__.py         (NEW)
cow/cow-mcp/cow_mcp/models/common.py           (NEW) — BBox, Region, Dimensions, SessionInfo
cow/cow-mcp/cow_mcp/models/ingest.py           (NEW) — IngestResult
cow/cow-mcp/cow_mcp/models/ocr.py              (NEW) — OcrResult, MathElement, OcrRegion, Diagram
cow/cow-mcp/cow_mcp/models/vision.py           (NEW) — VisionResult, DiagramInternals, LayoutAnalysis
cow/cow-mcp/cow_mcp/models/verify.py           (NEW) — VerificationResult, OcrCorrection, MathError
cow/cow-mcp/cow_mcp/models/compose.py          (NEW) — CompositionResult, EditAction
cow/cow-mcp/cow_mcp/models/export.py           (NEW) — ExportResult, LatexSource
cow/cow-mcp/cow_mcp/ingest/__init__.py         (NEW)
cow/cow-mcp/cow_mcp/ingest/__main__.py         (NEW) — MCP server entry point
cow/cow-mcp/cow_mcp/ingest/validator.py        (NEW) — Image/PDF validation
cow/cow-mcp/cow_mcp/storage/__init__.py        (NEW)
cow/cow-mcp/cow_mcp/storage/__main__.py        (NEW) — MCP server entry point
cow/cow-mcp/cow_mcp/storage/filesystem.py      (NEW) — Session filesystem operations
```
**File count:** 16 (all CREATE, small boilerplate files — most are <50 lines)
**Rationale:** Models are the shared foundation ALL other servers depend on. Grouping with
simple servers (ingest, storage) that have no external API dependencies lets Implementer-1
deliver early, unblocking Implementer-2 and Implementer-3.

### Implementer-2: OCR + Vision servers (external API integration)
```
cow/cow-mcp/cow_mcp/ocr/__init__.py            (NEW)
cow/cow-mcp/cow_mcp/ocr/__main__.py            (NEW) — MCP server entry point
cow/cow-mcp/cow_mcp/ocr/client.py              (NEW) — Mathpix client (modernized from cow-cli)
cow/cow-mcp/cow_mcp/ocr/separator.py           (NEW) — BBox conversion (adapted from cow-cli)
cow/cow-mcp/cow_mcp/ocr/cache.py               (NEW) — Disk cache for OCR results
cow/cow-mcp/cow_mcp/vision/__init__.py         (NEW)
cow/cow-mcp/cow_mcp/vision/__main__.py         (NEW) — MCP server entry point
cow/cow-mcp/cow_mcp/vision/gemini.py           (NEW) — Gemini 3.0 Pro client
```
**File count:** 8
**Rationale:** OCR and Vision are both external API integration servers. They share the
OcrResult→VisionResult interface boundary — the most complex merge logic in the pipeline.
Same implementer ensures interface consistency.

### Implementer-3: Review + Export servers (output generation)
```
cow/cow-mcp/cow_mcp/review/__init__.py         (NEW)
cow/cow-mcp/cow_mcp/review/__main__.py         (NEW) — MCP server entry point
cow/cow-mcp/cow_mcp/review/database.py         (NEW) — SQLite database (adapted from cow-cli)
cow/cow-mcp/cow_mcp/review/models.py           (NEW) — SQLAlchemy ORM models (from cow-cli)
cow/cow-mcp/cow_mcp/export/__init__.py         (NEW)
cow/cow-mcp/cow_mcp/export/__main__.py         (NEW) — MCP server entry point
cow/cow-mcp/cow_mcp/export/latex.py            (NEW) — LaTeX generation with kotex
cow/cow-mcp/cow_mcp/export/compiler.py         (NEW) — XeLaTeX subprocess compilation
cow/.mcp.json                                   (NEW) — MCP server registration
```
**File count:** 9
**Rationale:** Review and Export are the pipeline's output-side servers. Both adapt existing
cow-cli modules (review/database.py → cow-mcp, export/latex.py → cow-mcp). The .mcp.json
registration file naturally belongs here since it references all servers and is the last
piece needed for integration.

### Test files (owned by Phase 7 tester, not Phase 6 implementers)
```
cow/cow-mcp/tests/__init__.py
cow/cow-mcp/tests/conftest.py
cow/cow-mcp/tests/test_models.py
cow/cow-mcp/tests/test_ingest.py
cow/cow-mcp/tests/test_ocr.py
cow/cow-mcp/tests/test_vision.py
cow/cow-mcp/tests/test_review.py
cow/cow-mcp/tests/test_export.py
cow/cow-mcp/tests/test_storage.py
```

---

## §4 Task List

### T-1: Create package infrastructure and Pydantic models
**Implementer:** Implementer-1
**Files:** pyproject.toml, cow_mcp/__init__.py, models/ (8 files)
**Dependencies:** None (first task)

- **AC-0:** Verify pyproject.toml installs correctly with `pip install -e .`
- **AC-1:** All 8 model files importable: `from cow_mcp.models import IngestResult, OcrResult, VisionResult, VerificationResult, CompositionResult, ExportResult`
- **AC-2:** All Pydantic models have type annotations matching §6 Interface Contracts
- **AC-3:** models/common.py exports BBox, Region, Dimensions, SessionInfo shared types
- **AC-4:** JSON serialization round-trip works for all models

### T-2: Build cow-ingest MCP server
**Implementer:** Implementer-1
**Files:** ingest/__init__.py, ingest/__main__.py, ingest/validator.py
**Dependencies:** T-1

- **AC-0:** Server starts with `python -m cow_mcp.ingest` and accepts stdio MCP calls
- **AC-1:** `validate_image(path)` returns IngestResult for valid PNG/JPG/TIFF/WebP files
- **AC-2:** `validate_pdf(path, pages?)` returns IngestResult for valid PDF (max 2 pages)
- **AC-3:** Invalid files produce structured error responses (not crashes)
- **AC-4:** Image normalization (resize to max 4000px long edge, convert to PNG)

### T-3: Build cow-storage MCP server
**Implementer:** Implementer-1
**Files:** storage/__init__.py, storage/__main__.py, storage/filesystem.py
**Dependencies:** T-1

- **AC-0:** Server starts with `python -m cow_mcp.storage` and accepts stdio MCP calls
- **AC-1:** `save_result(session_id, stage, data)` saves JSON to `~/.cow/sessions/{id}/{stage}.json`
- **AC-2:** `load_result(session_id, stage)` returns Pydantic model or null
- **AC-3:** `list_sessions()` returns all sessions with metadata
- **AC-4:** Directory creation is automatic and idempotent

### T-4: Build cow-ocr MCP server
**Implementer:** Implementer-2
**Files:** ocr/__init__.py, ocr/__main__.py, ocr/client.py, ocr/separator.py, ocr/cache.py
**Dependencies:** T-1 (needs models/)

- **AC-0:** Server starts with `python -m cow_mcp.ocr` and accepts stdio MCP calls
- **AC-1:** `mathpix_ocr_image(path, options?)` calls Mathpix v3/text and returns OcrResult
- **AC-2:** `mathpix_ocr_pdf(path, pages?)` calls Mathpix v3/pdf and returns OcrResult
- **AC-3:** `get_cache(content_hash)` returns cached OcrResult or null
- **AC-4:** client.py modernized from cow-cli/mathpix/client.py: removed cow_cli imports, uses cow_mcp.models, keeps async httpx + retry logic
- **AC-5:** separator.py adapted from cow-cli/semantic/separator.py: `_cnt_to_region()` conversion preserved, output uses cow_mcp.models.common.BBox
- **AC-6:** Cache uses diskcache with content-hash keys (SHA256 of image bytes + options)

### T-5: Build cow-vision MCP server
**Implementer:** Implementer-2
**Files:** vision/__init__.py, vision/__main__.py, vision/gemini.py
**Dependencies:** T-1 (needs models/)

- **AC-0:** Server starts with `python -m cow_mcp.vision` and accepts stdio MCP calls
- **AC-1:** `gemini_detect_elements(image_path, regions?)` calls Gemini 3.0 Pro and returns DiagramInternals
- **AC-2:** `gemini_layout_analysis(image_path, ocr_regions?)` returns LayoutAnalysis
- **AC-3:** gemini.py uses google-genai SDK with structured output prompting
- **AC-4:** Results tagged with source="gemini" for origin tracking
- **AC-5:** Graceful degradation when Gemini API fails (return empty results, not crash)
- **AC-6:** Rate limit handling with exponential backoff (max 3 retries)

### T-6: Build cow-review MCP server
**Implementer:** Implementer-3
**Files:** review/__init__.py, review/__main__.py, review/database.py, review/models.py
**Dependencies:** T-1 (needs models/)

- **AC-0:** Server starts with `python -m cow_mcp.review` and accepts stdio MCP calls
- **AC-1:** `queue_review(session_id, items)` adds verification findings to review queue
- **AC-2:** `get_queue(session_id, status?)` returns review items with filtering
- **AC-3:** `submit_review(item_id, decision, modified_content?)` records review decision
- **AC-4:** database.py adapted from cow-cli/review/database.py: removed cow_cli imports, uses SQLAlchemy + aiosqlite, keeps same table schema
- **AC-5:** models.py adapted from cow-cli/review/models.py: same ORM models, updated imports

### T-7: Build cow-export MCP server
**Implementer:** Implementer-3
**Files:** export/__init__.py, export/__main__.py, export/latex.py, export/compiler.py
**Dependencies:** T-1 (needs models/)

- **AC-0:** Server starts with `python -m cow_mcp.export` and accepts stdio MCP calls
- **AC-1:** `generate_latex(composition, template?)` generates complete LaTeX document with kotex preamble
- **AC-2:** `compile_pdf(latex_path)` runs xelatex subprocess and returns ExportResult
- **AC-3:** `mathpix_mmd_to_pdf(mmd_content)` sends MMD to Mathpix /v3/converter as backup
- **AC-4:** LaTeX preamble includes: xetexko, kotex, Noto CJK KR fonts, amsmath, amssymb, tikz, pgfplots, graphicx
- **AC-5:** Compilation error auto-fix for common issues (missing package, undefined control sequence)
- **AC-6:** Font availability check before compilation

### T-8: Create .mcp.json registration file
**Implementer:** Implementer-3
**Files:** cow/.mcp.json
**Dependencies:** T-2, T-3, T-4, T-5, T-6, T-7 (all servers must be defined)

- **AC-0:** Verify .mcp.json is valid JSON and all 6 servers are registered
- **AC-1:** Each server entry has command, args, and env fields matching architecture spec
- **AC-2:** Environment variables for MATHPIX_APP_ID, MATHPIX_APP_KEY, GEMINI_API_KEY are placeholders (empty strings)
- **AC-3:** All servers use `python -m cow_mcp.{name}` command pattern

### Dependency Graph
```
T-1 (models + package)
 ├── T-2 (ingest)      ── Implementer-1
 ├── T-3 (storage)     ── Implementer-1
 ├── T-4 (ocr)         ── Implementer-2
 ├── T-5 (vision)      ── Implementer-2
 ├── T-6 (review)      ── Implementer-3
 └── T-7 (export)      ── Implementer-3
      └── T-8 (.mcp.json) ── Implementer-3 (after T-7)
```

**Parallel execution:** After T-1 completes, T-2/T-3 (Impl-1), T-4/T-5 (Impl-2), and T-6/T-7 (Impl-3) run in parallel.
T-8 is Implementer-3's final task after T-7. It only needs the server module paths (not running servers).

---

## §5 Detailed Design Specs

### 5.1 cow_mcp/models/common.py — V-HIGH
**Purpose:** Shared types used across all stage models.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

class BBox(BaseModel):
    """Axis-aligned bounding box in pixel coordinates."""
    x: int = Field(..., ge=0, description="Top-left X")
    y: int = Field(..., ge=0, description="Top-left Y")
    width: int = Field(..., ge=1, description="Width in pixels")
    height: int = Field(..., ge=1, description="Height in pixels")

    @property
    def x2(self) -> int: return self.x + self.width
    @property
    def y2(self) -> int: return self.y + self.height
    @property
    def area(self) -> int: return self.width * self.height
    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

class Dimensions(BaseModel):
    """Image or page dimensions."""
    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)

class SessionInfo(BaseModel):
    """Session metadata."""
    session_id: str
    created_at: str  # ISO 8601
    source_path: str
    source_type: Literal["image", "pdf"]
    page_count: int = 1

class RegionSource(str, Enum):
    """Origin of a detected region."""
    MATHPIX = "mathpix"
    GEMINI = "gemini"
    MERGED = "merged"
```

### 5.2 cow_mcp/models/ingest.py — V-MED
**Purpose:** IngestResult for Stage 1→2 transition.

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from cow_mcp.models.common import Dimensions

class IngestResult(BaseModel):
    """Output of INGEST stage. Input to OCR stage."""
    file_path: str = Field(..., description="Validated input file path")
    file_type: Literal["image", "pdf"]
    page_count: int = Field(1, ge=1, description="1 for images, 1-2 for PDFs")
    dimensions: Dimensions
    preprocessed_path: str = Field(..., description="Normalized image/PDF path")
    dpi: Optional[int] = Field(None, description="Detected DPI if available")
    color_space: Optional[str] = Field(None, description="RGB, CMYK, Grayscale")
```

### 5.3 cow_mcp/models/ocr.py — V-HIGH
**Purpose:** OcrResult for Stage 2→3 transition. Most complex model — carries Mathpix output.

**Existing reference:** cow-cli/mathpix/schemas.py (MathpixResponse, LineData, WordData)
— these Pydantic models define Mathpix API response structure. The new OcrResult is a
**pipeline-level** abstraction that wraps Mathpix output into domain-specific types.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from cow_mcp.models.common import BBox

class MathElement(BaseModel):
    """A detected mathematical expression."""
    id: str
    latex: str = Field(..., description="LaTeX representation")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Optional[BBox] = None
    is_inline: bool = Field(True, description="Inline vs display math")

class OcrRegion(BaseModel):
    """A detected content region with bounding box."""
    id: str
    type: Literal["text", "math", "table", "diagram", "chart", "figure", "equation_number"]
    bbox: BBox
    content: Optional[str] = Field(None, description="Text content if applicable")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    parent_id: Optional[str] = None
    children_ids: list[str] = Field(default_factory=list)

class Diagram(BaseModel):
    """A detected diagram or chart."""
    id: str
    type: Literal["chart", "figure", "table", "geometry", "graph", "flowchart", "other"]
    subtype: Optional[str] = Field(None, description="e.g., bar_chart, pie_chart")
    bbox: BBox
    caption: Optional[str] = None
    text_content: Optional[str] = Field(None, description="Extracted text from diagram")

class OcrResult(BaseModel):
    """Output of OCR stage. Input to VISION stage."""
    text: str = Field(..., description="Full text in MMD format")
    math_elements: list[MathElement] = Field(default_factory=list)
    regions: list[OcrRegion] = Field(default_factory=list)
    diagrams: list[Diagram] = Field(default_factory=list)
    raw_response: dict = Field(default_factory=dict, description="Mathpix raw JSON")
    page_dimensions: Optional[dict] = Field(None, description="{width, height} in pixels")
    detected_languages: list[str] = Field(default_factory=list)
    overall_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
```

### 5.4 cow_mcp/models/vision.py — V-HIGH
**Purpose:** VisionResult for Stage 3→4 transition. Merges Mathpix + Gemini data.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from cow_mcp.models.common import BBox, RegionSource
from cow_mcp.models.ocr import OcrResult, OcrRegion

class DiagramElement(BaseModel):
    """An internal element within a diagram (detected by Gemini)."""
    id: str
    type: Literal["axis", "label", "data_point", "line", "shape", "arrow", "text", "legend"]
    bbox: BBox
    content: Optional[str] = None

class DiagramInternals(BaseModel):
    """Internal structure of a diagram detected by Gemini vision."""
    diagram_id: str
    elements: list[DiagramElement] = Field(default_factory=list)
    bbox: BBox

class SpatialRelation(BaseModel):
    """Spatial relationship between two regions."""
    source_id: str
    target_id: str
    relation: Literal["above", "below", "left_of", "right_of", "contains", "adjacent"]

class LayoutAnalysis(BaseModel):
    """Layout analysis from Gemini vision."""
    columns: int = Field(1, ge=1, description="Detected column count")
    reading_order: list[str] = Field(default_factory=list, description="Region IDs in reading order")
    spatial_relations: list[SpatialRelation] = Field(default_factory=list)

class CombinedRegion(BaseModel):
    """A region with source attribution (Mathpix, Gemini, or merged)."""
    id: str
    type: str
    bbox: BBox
    source: RegionSource
    confidence: Optional[float] = None
    content: Optional[str] = None

class VisionResult(BaseModel):
    """Output of VISION stage. Input to VERIFY stage."""
    ocr_result: OcrResult
    diagram_internals: list[DiagramInternals] = Field(default_factory=list)
    layout_analysis: LayoutAnalysis = Field(default_factory=LayoutAnalysis)
    combined_regions: list[CombinedRegion] = Field(default_factory=list)
```

### 5.5 cow_mcp/models/verify.py — V-MED
**Purpose:** VerificationResult for Stage 4→5 transition.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from cow_mcp.models.vision import VisionResult

class OcrCorrection(BaseModel):
    """A correction to OCR output found during verification."""
    original: str
    corrected: str
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    region_id: Optional[str] = None

class MathError(BaseModel):
    """A mathematical error detected during verification."""
    element_id: str
    error_type: Literal["typographical", "logical", "notation", "missing_term", "other"]
    description: str
    suggestion: Optional[str] = None
    severity: Literal["low", "medium", "high", "critical"] = "medium"

class LogicIssue(BaseModel):
    """A logical issue detected in the document content."""
    location: str = Field(..., description="Description of where the issue occurs")
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    suggestion: Optional[str] = None

class VerificationResult(BaseModel):
    """Output of VERIFY stage. Input to COMPOSE stage."""
    vision_result: VisionResult
    ocr_corrections: list[OcrCorrection] = Field(default_factory=list)
    math_errors: list[MathError] = Field(default_factory=list)
    logic_issues: list[LogicIssue] = Field(default_factory=list)
    verified: bool = Field(False, description="True if no critical issues found")
    verification_notes: str = Field("", description="Summary of verification findings")
```

### 5.6 cow_mcp/models/compose.py — V-MED
**Purpose:** CompositionResult for Stage 5→6 transition.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class EditAction(BaseModel):
    """A single edit action applied during composition."""
    action: Literal["modify_text", "modify_equation", "adjust_layout",
                     "add_element", "remove_element", "reorder"]
    target: str = Field(..., description="Target element description")
    before: Optional[str] = None
    after: Optional[str] = None
    reason: Optional[str] = None

class DocumentMetadata(BaseModel):
    """Document-level metadata for the composition."""
    title: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    source_file: Optional[str] = None

class CompositionResult(BaseModel):
    """Output of COMPOSE stage. Input to EXPORT stage."""
    latex_source: str = Field(..., description="Complete LaTeX document source")
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    edit_history: list[EditAction] = Field(default_factory=list)
    user_approved: bool = Field(False, description="User approved final composition")
```

### 5.7 cow_mcp/models/export.py — V-MED
**Purpose:** ExportResult — final pipeline output.

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class ExportResult(BaseModel):
    """Output of EXPORT stage. Final pipeline result."""
    pdf_path: str
    method: Literal["xelatex", "mathpix_converter"]
    page_count: int = Field(..., ge=1)
    compilation_log: str = Field("", description="XeLaTeX compilation output")
    warnings: list[str] = Field(default_factory=list)
    file_size_bytes: Optional[int] = None

class LatexSource(BaseModel):
    """Generated LaTeX source document."""
    content: str = Field(..., description="Complete LaTeX source")
    preamble: str = Field(..., description="Document preamble")
    body: str = Field(..., description="Document body")
    packages: list[str] = Field(default_factory=list, description="Required packages")
```

### 5.8 cow_mcp/ingest/validator.py — V-MED
**Purpose:** Image and PDF validation logic.

**Existing reference:** cow-cli/preprocessing/validator.py and cow-cli/pdf/validator.py.

```python
from pathlib import Path
from PIL import Image
import io

SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "TIFF", "WEBP"}
MAX_LONG_EDGE = 4000  # pixels
MAX_PDF_PAGES = 2

async def validate_image(path: str) -> IngestResult:
    """Validate image file and normalize."""
    # 1. Check file exists and is readable
    # 2. Open with Pillow, check format in SUPPORTED_IMAGE_FORMATS
    # 3. Get dimensions, DPI, color space
    # 4. If long edge > MAX_LONG_EDGE, resize proportionally
    # 5. Save normalized PNG to session directory
    # 6. Return IngestResult

async def validate_pdf(path: str, pages: list[int] | None = None) -> IngestResult:
    """Validate PDF and extract pages."""
    # 1. Check file exists, use pypdf to open
    # 2. Check page count <= MAX_PDF_PAGES
    # 3. If pages specified, validate range
    # 4. Render pages to images for downstream OCR
    # 5. Return IngestResult with page_count
```

### 5.9 cow_mcp/ingest/__main__.py — V-MED
**Purpose:** MCP server entry point using mcp Python SDK.

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

server = Server("cow-ingest")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="validate_image",
            description="Validate and preprocess an image file for OCR",
            inputSchema={...}  # JSON Schema for path parameter
        ),
        types.Tool(
            name="validate_pdf",
            description="Validate and preprocess a PDF file for OCR",
            inputSchema={...}  # JSON Schema for path + pages parameters
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "validate_image":
        result = await validate_image(arguments["path"])
        return [types.TextContent(type="text", text=result.model_dump_json())]
    elif name == "validate_pdf":
        result = await validate_pdf(arguments["path"], arguments.get("pages"))
        return [types.TextContent(type="text", text=result.model_dump_json())]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 5.10 cow_mcp/ocr/client.py — V-HIGH
**Purpose:** Modernized Mathpix API client. Adapted from cow-cli/mathpix/client.py (604L).

**Existing reference:** cow-cli/cow_cli/mathpix/client.py — MathpixClient class with:
- `__init__`: credentials from config + keyring, httpx async client
- `_request_with_retry`: retry logic with exponential backoff (3 retries, status codes 429/500/502/503/504)
- `process_image`: v3/text endpoint, base64 encoding, cache integration
- `process_pdf`: v3/pdf endpoint, multipart upload, polling for completion
- `process_image_unified`: returns UnifiedResponse

**What changes in cow-mcp version:**
1. Remove `from cow_cli.config import load_config, get_mathpix_credentials` — replace with env var reads
2. Remove `from cow_cli.cache import ...` — use cow_mcp.ocr.cache instead
3. Remove `from cow_cli.mathpix.schemas import ...` — use cow_mcp.models instead
4. Keep async httpx + retry logic intact
5. Return `OcrResult` instead of `MathpixResponse`/`UnifiedResponse`
6. Add `_response_to_ocr_result()` conversion method that maps Mathpix API response to OcrResult

**Key functions:**
```python
class MathpixMcpClient:
    """Mathpix API client for cow-mcp OCR server."""

    def __init__(self, app_id: str | None = None, app_key: str | None = None):
        self._app_id = app_id or os.environ.get("MATHPIX_APP_ID", "")
        self._app_key = app_key or os.environ.get("MATHPIX_APP_KEY", "")
        # ... httpx client setup (same pattern as cow-cli)

    async def ocr_image(self, path: str, options: dict | None = None) -> OcrResult: ...
    async def ocr_pdf(self, path: str, pages: list[int] | None = None) -> OcrResult: ...
    def _response_to_ocr_result(self, response_data: dict) -> OcrResult: ...
```
**Verification Level:** V-HIGH — critical path, external API integration.

### 5.11 cow_mcp/ocr/separator.py — V-HIGH
**Purpose:** BBox conversion logic. Adapted from cow-cli/semantic/separator.py (712L).

**Existing reference:** cow-cli/cow_cli/semantic/separator.py — LayoutContentSeparator class.
Key method: `_cnt_to_region(cnt)` converts Mathpix polygon contours (list of [x,y] points)
to axis-aligned bounding boxes (Region with top_left_x, top_left_y, width, height).

**What changes in cow-mcp version:**
1. Extract ONLY the `_cnt_to_region()` function and related helpers
2. Remove the full LayoutContentSeparator class — not needed in MCP architecture
3. Convert output from cow_cli Region to cow_mcp BBox
4. Add `process_mathpix_regions()` that takes raw Mathpix line_data/word_data and
   produces list of `OcrRegion` with converted bounding boxes

```python
from cow_mcp.models.common import BBox
from cow_mcp.models.ocr import OcrRegion

def cnt_to_bbox(cnt: list[list[int]]) -> BBox:
    """Convert Mathpix polygon contour to axis-aligned bounding box.
    Preserved from cow-cli/semantic/separator.py _cnt_to_region().
    """
    if not cnt:
        raise ValueError("Empty contour")
    xs = [p[0] for p in cnt]
    ys = [p[1] for p in cnt]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    return BBox(x=x_min, y=y_min, width=x_max - x_min, height=y_max - y_min)

def process_mathpix_regions(line_data: list[dict]) -> list[OcrRegion]:
    """Convert Mathpix line_data into cow-mcp OcrRegions with bbox conversion."""
    ...
```
**Verification Level:** V-HIGH — bbox accuracy directly affects VISION merge quality.

### 5.12 cow_mcp/ocr/cache.py — V-LOW
**Purpose:** Disk-based OCR result cache. Adapted from cow-cli/cache.py.

Uses diskcache library. Key: SHA256(image_bytes + options_json). Value: OcrResult as JSON.
Same pattern as cow-cli/cache.py but simplified (no config integration).

### 5.13 cow_mcp/vision/gemini.py — V-HIGH
**Purpose:** Gemini 3.0 Pro API client for bbox detection and layout analysis.

```python
import google.genai as genai
from cow_mcp.models.common import BBox
from cow_mcp.models.vision import DiagramInternals, DiagramElement, LayoutAnalysis

class GeminiVisionClient:
    """Gemini 3.0 Pro client for visual analysis."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._client = genai.Client(api_key=self._api_key)
        self._model = "gemini-3.0-pro"

    async def detect_elements(
        self, image_path: str, regions: list[dict] | None = None
    ) -> list[DiagramInternals]:
        """Detect internal elements within diagram regions using Gemini bbox."""
        # 1. Load image
        # 2. For each diagram region, crop and send to Gemini with structured prompt
        # 3. Prompt: "Detect all visual elements (axes, labels, data points, shapes)
        #    and return their bounding boxes in JSON format"
        # 4. Parse Gemini response into DiagramInternals
        ...

    async def analyze_layout(
        self, image_path: str, ocr_regions: list[dict] | None = None
    ) -> LayoutAnalysis:
        """Analyze document layout: columns, reading order, spatial relations."""
        # 1. Send full image to Gemini
        # 2. Prompt: "Analyze this document's layout structure. Identify:
        #    - Number of columns
        #    - Reading order of content blocks
        #    - Spatial relationships between elements"
        # 3. Parse response into LayoutAnalysis
        ...
```
**Verification Level:** V-HIGH — Gemini API integration, bbox accuracy (mAP ~0.43).

### 5.14 cow_mcp/review/database.py — V-MED
**Purpose:** SQLite HITL review database. Adapted from cow-cli/review/database.py (622L).

**Existing reference:** cow-cli/cow_cli/review/database.py — ReviewDatabase class using
SQLAlchemy ORM with Session management. Key operations: create_item, get_items, update_status.

**What changes in cow-mcp version:**
1. Remove `from cow_cli.review.models import ...` → use local models.py
2. Keep SQLAlchemy + aiosqlite pattern
3. Simplify to 3 MCP-facing operations: queue_review, get_queue, submit_review
4. Database path: `~/.cow/review.db` (same as cow-cli)

### 5.15 cow_mcp/export/latex.py — V-HIGH
**Purpose:** LaTeX document generation with Korean math support.

**Existing reference:** cow-cli/cow_cli/export/latex.py — LaTeXExporter class. Uses standard
preamble with inputenc/fontenc (NOT Korean-optimized). The cow-mcp version needs XeLaTeX + kotex.

```python
KOREAN_MATH_PREAMBLE = r"""
\documentclass[a4paper,11pt]{article}

% Korean support (XeLaTeX + kotex)
\usepackage{xetexko}
\usepackage{kotex}
\setmainfont{Noto Serif CJK KR}
\setsansfont{Noto Sans CJK KR}
\setmonofont{Noto Sans Mono CJK KR}

% Math packages
\usepackage{amsmath, amssymb, amsthm}
\usepackage{mathtools}

% Graphics
\usepackage{tikz, pgfplots}
\usepackage{graphicx}
\usepackage{float}

% Tables
\usepackage{booktabs, array, longtable}

% Page layout
\usepackage{geometry}
\geometry{margin=2.5cm}

% Hyperlinks
\usepackage{hyperref}
\hypersetup{colorlinks=true, linkcolor=blue, urlcolor=blue}
"""

class LatexGenerator:
    """Generate LaTeX documents from CompositionResult."""

    def generate(self, composition: CompositionResult, template: str | None = None) -> LatexSource:
        """Generate complete LaTeX document."""
        preamble = template or KOREAN_MATH_PREAMBLE
        body = self._compose_body(composition)
        content = f"{preamble}\n\\begin{{document}}\n{body}\n\\end{{document}}"
        return LatexSource(content=content, preamble=preamble, body=body,
                          packages=self._extract_packages(preamble))

    def _compose_body(self, composition: CompositionResult) -> str:
        """Convert composition content to LaTeX body."""
        # Parse the latex_source from CompositionResult
        # Apply metadata (title, subject, grade_level)
        # Return LaTeX body content
        ...
```
**Verification Level:** V-HIGH — Korean font + math package conflicts are a risk hotspot.

### 5.16 cow_mcp/export/compiler.py — V-MED
**Purpose:** XeLaTeX subprocess compilation with error handling.

```python
import subprocess
import tempfile
from pathlib import Path
from cow_mcp.models.export import ExportResult

class XeLatexCompiler:
    """Compile LaTeX to PDF using XeLaTeX."""

    XELATEX_CMD = "xelatex"
    MAX_COMPILE_PASSES = 3  # For cross-references
    TIMEOUT_SECONDS = 120

    async def compile(self, latex_path: str, output_dir: str | None = None) -> ExportResult:
        """Compile LaTeX file to PDF."""
        # 1. Check xelatex availability (shutil.which)
        # 2. Run xelatex -interaction=nonstopmode -output-directory=... latex_path
        # 3. If cross-references, run again (up to MAX_COMPILE_PASSES)
        # 4. Parse compilation log for errors/warnings
        # 5. Return ExportResult with pdf_path and compilation_log
        ...

    async def check_fonts(self) -> dict[str, bool]:
        """Check availability of required fonts."""
        # Run fc-list to check Noto CJK KR fonts
        ...

    def _auto_fix_errors(self, log: str, latex_path: str) -> bool:
        """Attempt to auto-fix common compilation errors."""
        # Handle: missing package → add \usepackage
        # Handle: undefined control sequence → remove or substitute
        # Handle: font not found → fall back to available font
        ...
```

### 5.17 cow_mcp/storage/filesystem.py — V-LOW
**Purpose:** Session-based file storage.

```python
from pathlib import Path
import json
from datetime import datetime
from cow_mcp.models.common import SessionInfo

SESSIONS_DIR = Path.home() / ".cow" / "sessions"

class SessionStorage:
    """Filesystem-based session storage."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or SESSIONS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_result(self, session_id: str, stage: str, data: dict) -> str:
        """Save stage result as JSON. Returns file path."""
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / f"{stage}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return str(path)

    async def load_result(self, session_id: str, stage: str) -> dict | None:
        """Load stage result. Returns None if not found."""
        path = self.base_dir / session_id / f"{stage}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    async def list_sessions(self) -> list[SessionInfo]:
        """List all sessions with metadata."""
        sessions = []
        for session_dir in sorted(self.base_dir.iterdir()):
            if session_dir.is_dir():
                meta_path = session_dir / "metadata.json"
                if meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    sessions.append(SessionInfo(**meta))
        return sessions
```

### 5.18 MCP Server __main__.py Pattern — V-MED
All 6 MCP servers follow the same pattern shown in §5.9 (cow-ingest). The pattern uses:
- `mcp` Python SDK (PyPI package `mcp`)
- `Server` class with `@server.list_tools()` and `@server.call_tool()` decorators
- `stdio_server()` transport
- Tool results serialized as Pydantic model JSON via `model_dump_json()`

Each server defines its tools matching the GC-v3 tool signatures.

---

## §6 Interface Contracts

### Stage 1→2: IngestResult
```python
class IngestResult(BaseModel):
    file_path: str               # validated input file
    file_type: Literal["image", "pdf"]
    page_count: int              # 1 for images, 1-2 for PDFs
    dimensions: Dimensions       # {width: int, height: int}
    preprocessed_path: str       # normalized image/PDF path
    dpi: Optional[int] = None
    color_space: Optional[str] = None
```
**Validation:** file_path must exist, page_count >= 1, dimensions > 0.

### Stage 2→3: OcrResult
```python
class OcrResult(BaseModel):
    text: str                    # full text in MMD format
    math_elements: list[MathElement]   # [{id, latex, confidence, bbox, is_inline}]
    regions: list[OcrRegion]     # [{id, type, bbox, content, confidence, parent_id}]
    diagrams: list[Diagram]      # [{id, type, subtype, bbox, caption}]
    raw_response: dict           # Mathpix API raw JSON
    page_dimensions: Optional[dict]
    detected_languages: list[str]
    overall_confidence: Optional[float]
```
**Validation:** text non-empty, all bbox fields >= 0, confidence 0.0-1.0.

### Stage 3→4: VisionResult
```python
class VisionResult(BaseModel):
    ocr_result: OcrResult                      # from Stage 2
    diagram_internals: list[DiagramInternals]  # [{diagram_id, elements, bbox}]
    layout_analysis: LayoutAnalysis            # {columns, reading_order, spatial_relations}
    combined_regions: list[CombinedRegion]      # [{id, type, bbox, source}]
```
**Validation:** combined_regions source must be one of "mathpix"/"gemini"/"merged".

### Stage 4→5: VerificationResult
```python
class VerificationResult(BaseModel):
    vision_result: VisionResult
    ocr_corrections: list[OcrCorrection]  # [{original, corrected, reason, confidence}]
    math_errors: list[MathError]          # [{element_id, error_type, suggestion, severity}]
    logic_issues: list[LogicIssue]        # [{location, description, severity}]
    verified: bool
    verification_notes: str
```
**Validation:** severity must be one of "low"/"medium"/"high"/"critical".

### Stage 5→6: CompositionResult
```python
class CompositionResult(BaseModel):
    latex_source: str             # complete LaTeX document
    metadata: DocumentMetadata    # {title, subject, grade_level}
    edit_history: list[EditAction]  # [{action, target, before, after}]
    user_approved: bool
```
**Validation:** latex_source non-empty, user_approved should be True before export.

### Stage 6 Output: ExportResult
```python
class ExportResult(BaseModel):
    pdf_path: str
    method: Literal["xelatex", "mathpix_converter"]
    page_count: int
    compilation_log: str
    warnings: list[str]
    file_size_bytes: Optional[int]
```
**Validation:** pdf_path must point to existing file, page_count >= 1.

---

## §7 Validation Checklist

### V1: Unit Test Requirements
| Module | Tests | Priority |
|--------|-------|----------|
| models/ | All Pydantic models: creation, validation, serialization, edge cases | HIGH |
| ingest/validator.py | Valid/invalid images, PDF page limits, normalization | HIGH |
| ocr/client.py | API call mocking (respx), response parsing, retry logic | HIGH |
| ocr/separator.py | cnt→bbox conversion with real Mathpix contour data | HIGH |
| ocr/cache.py | Cache hit/miss, TTL expiry, hash consistency | MEDIUM |
| vision/gemini.py | API call mocking, response parsing, error handling | HIGH |
| review/database.py | CRUD operations, status transitions, audit log | MEDIUM |
| export/latex.py | Preamble generation, body composition, package detection | HIGH |
| export/compiler.py | Compilation success/failure, font check, auto-fix | HIGH |
| storage/filesystem.py | Save/load/list, missing session handling | LOW |

### V2: Integration Test Requirements
| Test | Description | Priority |
|------|-------------|----------|
| IngestResult → OcrResult | Validate model compatibility between stages | HIGH |
| OcrResult → VisionResult | Test OCR/Vision merge with combined_regions | HIGH |
| VisionResult → VerificationResult | Verify nested model serialization | MEDIUM |
| CompositionResult → ExportResult | Test LaTeX generation → compilation chain | HIGH |
| Full pipeline model chain | All 6 models created sequentially, each consuming previous | HIGH |

### V3: Pydantic Model Validation Tests
- All required fields raise ValidationError when missing
- All Optional fields accept None
- Literal types reject invalid values
- BBox rejects negative width/height
- Confidence values constrained to [0.0, 1.0]
- JSON round-trip: `Model(**model.model_dump()) == model` for all models

### V4: MCP Server Tool Call Tests
- Each server starts and responds to `list_tools` request
- Each tool accepts valid input and returns valid JSON
- Each tool returns structured error for invalid input
- Server gracefully handles malformed requests

### V5: End-to-End Pipeline Test
- Given a sample Korean math image:
  1. cow-ingest validates and normalizes it
  2. cow-ocr extracts text/equations (mocked Mathpix API)
  3. cow-vision detects diagram elements (mocked Gemini API)
  4. Data flows through VerificationResult → CompositionResult (mocked Claude reasoning)
  5. cow-export generates PDF (requires xelatex installed)
- Test with both image and PDF (2-page) inputs

### V6: Code Plausibility Review
| Item | Risk | Monitoring Plan |
|------|------|-----------------|
| VP-1 | MCP SDK `mcp` package import compatibility | Verify `pip install mcp` succeeds and Server/stdio_server import works — first 3 runs |
| VP-2 | google-genai SDK structured output for bbox | Verify Gemini returns parseable bbox JSON — first 3 runs with real API |
| VP-3 | XeLaTeX + kotex + Noto CJK KR font availability | Verify `xelatex --version` and `fc-list :family="Noto Serif CJK KR"` — first run |
| VP-4 | Mathpix UnifiedResponse → OcrResult mapping | Verify all fields preserved in conversion — test with real API response |
| VP-5 | cnt→bbox conversion accuracy | Compare cow-mcp output vs cow-cli output for same input — first 3 runs |
| VP-6 | MCP stdio transport reliability | Verify server doesn't hang on large responses (>100KB JSON) — first 3 runs |

---

## §8 Risk Mitigation

### R-1: OcrResult→VisionResult merge logic (dual-source bbox reconciliation)
**Risk:** Mathpix and Gemini produce overlapping bounding boxes for the same content.
**Mitigation:**
- Tag every region with `source: RegionSource` (mathpix/gemini/merged)
- Merge strategy: IoU (Intersection over Union) > 0.5 → create merged region
- Keep both original regions alongside merged version
- Implementation: `merge_regions()` function in vision/__main__.py

### R-2: XeLaTeX compilation (Korean font + math package conflicts)
**Risk:** Font loading failures or package conflicts when combining kotex with amsmath/tikz.
**Mitigation:**
- Font availability check at server startup (`check_fonts()` in compiler.py)
- Fallback font chain: Noto CJK KR → Nanum → system default
- Mathpix /v3/converter as backup when local compilation fails
- Auto-fix for common errors in `_auto_fix_errors()`

### R-3: Gemini API bbox accuracy (mAP ~0.43)
**Risk:** Low accuracy leads to incorrect diagram element detection.
**Mitigation:**
- Use Gemini primarily for diagram INTERNAL elements (axes, labels, data points)
- Mathpix provides primary document-level bbox (higher accuracy)
- Source tagging allows downstream stages to weight confidence by source
- Graceful degradation: skip Gemini results if confidence too low

### R-4: separator.py cnt→region conversion (complex polygon logic)
**Risk:** Simplified bbox conversion loses polygon detail for non-rectangular elements.
**Mitigation:**
- Preserve original `cnt` data alongside converted `BBox` in OcrRegion
- Unit test with real Mathpix contour data from cow-cli test fixtures
- Compare output with cow-cli's `_cnt_to_region()` for regression

### R-5: MCP Server complexity (stdio transport reliability)
**Risk:** Large JSON responses (>100KB) may cause stdio buffering issues.
**Mitigation:**
- Pydantic's `model_dump_json()` produces compact JSON
- For large results (e.g., raw_response), use cow-storage to persist and return path reference
- Test with realistic payload sizes during V5

---

## §9 Dependencies & Build

### Python Package Structure (pyproject.toml)
```toml
[project]
name = "cow-mcp"
version = "0.1.0"
description = "COW Pipeline MCP Servers — Korean math/science document processing"
requires-python = ">=3.11"
dependencies = [
    # MCP SDK
    "mcp>=1.0.0",

    # Data models
    "pydantic>=2.0.0",

    # HTTP clients
    "httpx>=0.28.0",

    # Image processing (INGEST)
    "Pillow>=12.0.0",
    "pypdf>=5.0.0",

    # Mathpix OCR (OCR)
    "imagehash>=4.3.0",
    "diskcache>=5.6.0",

    # Gemini Vision (VISION)
    "google-genai>=1.0.0",

    # Review database (REVIEW)
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.22.0",

    # Configuration
    "pyyaml>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.0",
    "pytest-asyncio>=1.0.0",
    "pytest-cov>=7.0.0",
    "pytest-mock>=3.15.0",
    "respx>=0.22.0",
]
```

### External Dependencies
| Dependency | Version | Purpose | Required By |
|-----------|---------|---------|-------------|
| mcp | >=1.0.0 | MCP SDK for server implementation | All servers |
| pydantic | >=2.0.0 | Data validation and serialization | All models |
| httpx | >=0.28.0 | Async HTTP client | cow-ocr, cow-export |
| Pillow | >=12.0.0 | Image processing | cow-ingest |
| pypdf | >=5.0.0 | PDF parsing | cow-ingest |
| google-genai | >=1.0.0 | Gemini API client | cow-vision |
| imagehash | >=4.3.0 | Image hashing for cache | cow-ocr |
| diskcache | >=5.6.0 | Disk-based cache | cow-ocr |
| sqlalchemy | >=2.0.0 | ORM for review database | cow-review |
| aiosqlite | >=0.22.0 | Async SQLite | cow-review |
| pyyaml | >=6.0.0 | YAML config parsing | Shared |

### System Requirements
- **xelatex:** Required for cow-export compilation. Install via TeX Live: `sudo apt install texlive-xetex`
- **kotex:** Korean TeX packages. Install via: `sudo apt install texlive-lang-korean`
- **Noto CJK KR fonts:** Required fonts. Install via: `sudo apt install fonts-noto-cjk`
- **Python 3.11+:** Required for type hint features used in models

### MCP Server Registration (.mcp.json)
```json
{
  "mcpServers": {
    "cow-ingest": {
      "command": "python",
      "args": ["-m", "cow_mcp.ingest"],
      "cwd": "/home/palantir/cow/cow-mcp",
      "env": {}
    },
    "cow-ocr": {
      "command": "python",
      "args": ["-m", "cow_mcp.ocr"],
      "cwd": "/home/palantir/cow/cow-mcp",
      "env": {
        "MATHPIX_APP_ID": "",
        "MATHPIX_APP_KEY": ""
      }
    },
    "cow-vision": {
      "command": "python",
      "args": ["-m", "cow_mcp.vision"],
      "cwd": "/home/palantir/cow/cow-mcp",
      "env": {
        "GEMINI_API_KEY": ""
      }
    },
    "cow-review": {
      "command": "python",
      "args": ["-m", "cow_mcp.review"],
      "cwd": "/home/palantir/cow/cow-mcp",
      "env": {}
    },
    "cow-export": {
      "command": "python",
      "args": ["-m", "cow_mcp.export"],
      "cwd": "/home/palantir/cow/cow-mcp",
      "env": {}
    },
    "cow-storage": {
      "command": "python",
      "args": ["-m", "cow_mcp.storage"],
      "cwd": "/home/palantir/cow/cow-mcp",
      "env": {}
    }
  }
}
```

---

## §10 Migration Plan

### Modules to Reuse (adapted, not copied verbatim)
| Source (cow-cli) | Target (cow-mcp) | Changes |
|-----------------|-------------------|---------|
| mathpix/client.py (604L) | ocr/client.py | Remove cow_cli imports, use env vars for config, return OcrResult |
| semantic/separator.py (712L) | ocr/separator.py | Extract cnt_to_bbox() + process_mathpix_regions(), remove LayoutContentSeparator class |
| review/database.py (622L) | review/database.py | Remove cow_cli imports, simplify to 3 MCP operations |
| review/models.py | review/models.py | Same ORM models, updated imports |
| export/latex.py | export/latex.py | Replace preamble with XeLaTeX + kotex, rewrite body composition |
| cache.py | ocr/cache.py | Remove cow_cli.config dependency, use env vars |
| config.py | N/A | Not needed — MCP servers use env vars for configuration |

### Modules to Remove (not used in cow-mcp)
| Module | Reason |
|--------|--------|
| claude/orchestrator.py (~585L) | SDK-based, incompatible with MCP architecture |
| claude/stage_agents.py (~500L) | SDK-based agent definitions, replaced by Claude Code orchestration |
| claude/mcp_servers.py (~400L) | SDK MCP server definitions, replaced by standalone MCP servers |
| claude/hooks.py | SDK hooks, not needed |

### Package Structure
- cow-mcp lives as a **sibling** package to cow-cli under `cow/`:
  ```
  cow/
  ├── cow-cli/     # Existing CLI (remains untouched in Phase 6)
  └── cow-mcp/     # New MCP server package
  ```
- No modifications to cow-cli in this phase
- cow-mcp has its own pyproject.toml and is independently installable
- Future phase may consolidate or deprecate cow-cli

### Backward Compatibility
- cow-cli remains fully functional and unmodified
- cow-mcp is additive only — no existing files are changed
- MCP server registration in .mcp.json is project-level, not system-level
- Environment variables for API keys are separate from cow-cli's keyring-based config

---

## Appendix A: Phase 5 Targets for Devils-Advocate

These assumptions should be challenged during Plan Validation:

1. **MCP SDK compatibility assumption:** We assume `mcp` Python package provides `Server`, `stdio_server`, and `types` as described. Risk if API has changed: all 6 server __main__.py files need rewriting.

2. **google-genai structured output assumption:** We assume Gemini 3.0 Pro can return bbox coordinates in parseable JSON via structured output. Risk if not: cow-vision gemini.py needs prompt engineering redesign.

3. **XeLaTeX + kotex + amsmath coexistence assumption:** We assume these packages don't conflict. Risk if they do: cow-export preamble needs careful package ordering.

4. **Implementer file count assumption:** Implementer-1 has 16 files, exceeding the 4-file guideline. Justification: most are <30 line boilerplate (__init__.py, model files). The functional complexity is equivalent to ~4 substantive files.

5. **cow-cli module adaptation scope assumption:** We assume "adapt" means significant rewrite (new imports, new return types) not copy-paste. Risk: underestimating adaptation effort for client.py (604L) and separator.py (712L).
