# COW Pipeline v2.0 — Design Document

> Triple-Layer Verification Architecture with Interactive UX
> Date: 2026-02-09
> Status: DRAFT — Pending user approval
> Supersedes: COW Pipeline v1.0 (cow-mcp, cow-cli)

---

## 1. Executive Summary

COW Pipeline v2.0 is a complete redesign of the PDF reconstruction and editing system.
It replaces the existing MCP-server-centric architecture (v1.0) with a Python SDK + CLI
wrapper design, featuring Triple-Layer verification (Gemini L1+L2 + Opus L3) and
an interactive, progressively automated UX.

**Key changes from v1.0:**
- Delete all existing code (cow-cli/, cow-mcp/, 6 MCP servers)
- Python SDK with CLI wrapper instead of MCP tools
- Dual Gemini model quality loop (L1+L2) inside Python
- Opus 4.6 as pure logical verifier (L3) — no vision tasks
- Loop-based modular architecture (6 composable loops)
- Two pipelines: Reconstruction (required) + Editing (optional)
- Interactive UX with progressive automation (Level 1→2→3)
- All Gemini models must be 3.0 series — no fallback, fail-stop

---

## 2. Migration Plan — Delete Existing Code

### 2.1 Files to Delete

```
cow/
├── cow-cli/          ← DELETE ENTIRELY (legacy CLI pipeline)
├── cow-mcp/          ← DELETE ENTIRELY (6 MCP servers, 33 Python files)
├── *.png             ← DELETE (test artifacts)
├── *.pdf             ← DELETE (test artifacts)
├── PIPELINE-REFERENCE.md  ← DELETE (obsolete)
└── outputs/          ← DELETE (test outputs)
```

### 2.2 Files to Preserve

```
cow/
├── docs/             ← KEEP (reference documentation)
├── images/           ← KEEP (source test images)
├── sample.pdf        ← KEEP (test input)
├── sample2.pdf       ← KEEP (test input)
├── requirements.txt  ← REPLACE (new dependencies)
└── .gitignore        ← UPDATE
```

### 2.3 MCP Server Registration Cleanup

Remove cow-* entries from `.claude.json` project mcpServers:
- cow-ocr
- cow-vision
- cow-export
- cow-ingest
- cow-review
- cow-storage

API keys (Gemini, Mathpix) remain — referenced by new Python SDK via env vars.

---

## 3. Architecture — Triple-Layer Verification

### 3.1 Layer Definitions

```
LAYER 1 (L1): gemini-3-pro-image-preview
  Domain: Visual generation and analysis
  Tasks: OCR extraction, bbox detection, crop analysis, layout inspection
  Input: Images (PNG)
  Output: Structured results (text, JSON, coordinates)

LAYER 2 (L2): gemini-3-pro-preview
  Domain: Reasoning and cross-validation
  Tasks: Critique L1 results, identify errors, provide correction feedback
  Input: L1 results + original images
  Output: Verified results OR correction feedback to L1

LAYER 3 (L3): Opus 4.6 (Claude Code)
  Domain: Pure logical verification — NO VISION
  Tasks: Math correctness, LaTeX integrity, logic chains, orchestration, UX
  Input: text / LaTeX / JSON ONLY (images absolutely prohibited)
  Output: Verification reports, LaTeX edits, user-facing communication
```

### 3.2 Layer Boundaries

```
┌─────────────────────────────────────────────────┐
│ Python SDK (cow/core/)                          │
│                                                 │
│  L1: gemini-3-pro-image-preview ◄──┐           │
│    │ results                       │ feedback   │
│    ▼                               │            │
│  L2: gemini-3-pro-preview ─────────┘            │
│    │ converged text/JSON                        │
│    │ (NO images cross this boundary)            │
├─────────────────────────────────────────────────┤
│    ▼                                            │
│  CLI stdout: JSON result                        │
├─────────────────────────────────────────────────┤
│ Claude Code (Opus 4.6)                          │
│                                                 │
│  L3: Logical verification                       │
│    │ + User interaction (AskUserQuestion)        │
│    │ + LaTeX composition and editing             │
│    ▼                                            │
│  User approval                                  │
└─────────────────────────────────────────────────┘
```

### 3.3 Model Requirements

| Model | ID | Layer | Fallback |
|-------|----|-------|----------|
| Gemini Image | `gemini-3-pro-image-preview` | L1 | NONE — fail-stop |
| Gemini Reasoning | `gemini-3-pro-preview` | L2 | NONE — fail-stop |
| Opus | `claude-opus-4-6` | L3 | NONE — fail-stop |
| Mathpix | v3/text API | Optional OCR | NONE — fail-stop |

**AD-9: No Fallback — Fail-Stop Principle**
If any specified model is unavailable (404, deprecated, quota exceeded):
- Pipeline HALTS immediately
- Error reported to user with model ID and error details
- NO silent substitution with alternative models
- User decides: retry, change model, or abort

---

## 4. Loop Modules — 6 Composable Units

### 4.1 Loop A: Gemini Quality Loop (L1+L2)

```
Implementation: cow/core/gemini_loop.py
Participants: gemini-3-pro-image-preview + gemini-3-pro-preview
Character: Machine-internal loop (no user interaction)
Role: Reusable building block for ALL Gemini visual tasks

Flow:
  L1 (image model) → generates result
    │
    ▼
  L2 (reasoning model) → cross-validates
    │
    ├── PASS (confidence >= threshold) → return converged result (text/JSON)
    └── FAIL → generate feedback → L1 re-processes with feedback
         (repeat until max_iterations)

Dynamic Parameters (user-configurable per call):
  - image_model: str (default: "gemini-3-pro-image-preview")
  - reasoning_model: str (default: "gemini-3-pro-preview")
  - temperature: float (default: 0.1)
  - max_iterations: int (default: 3)
  - confidence_threshold: float (default: 0.9)

Used by: ocr.py, diagram.py, layout_design.py, layout_verify.py
```

### 4.2 Loop B: Logical Verification Loop (L3)

```
Implementation: Opus orchestration pattern (Claude Code)
Participants: Opus 4.6 + User
Character: Interactive — user final approval required (AD-16)
Input: text / LaTeX / JSON ONLY (no images)

Flow:
  Opus performs logical verification:
    - Mathematical correctness (computation checks)
    - Problem → Solution → Answer logic chain
    - LaTeX structural integrity (balanced braces, valid commands)
    - Cross-reference consistency
    - Completeness (all problems accounted for)
    │
    ▼
  Opus → reports verification result to User
    │
    ├── User: "Approve" → proceed to next stage
    ├── User: "Fix this: ..." → Opus re-verifies → re-reports
    └── User: "Cancel" → rollback
```

### 4.3 Loop C: Layout Design Loop

```
Implementation: cow/core/layout_design.py (uses Loop A) + Opus UX
Participants: Gemini (visual analysis) + Opus (relay/adjust) + User (decision)
Character: Proactive decision-making — "HOW should the document be structured?"

Scope:
  - Column configuration (1-col, 2-col, minipage)
  - Problem box styling (fbox, tcolorbox, plain)
  - Diagram placement strategy (inline, float, margin)
  - Font size, line spacing, margins
  - Header/footer, page numbering
  - Section/problem numbering style

Flow (Reconstruction):
  Python: original PNG → Gemini L1+L2 (Loop A)
    → layout analysis report (text):
      "2-column, bold problem numbers, indented solutions,
       diagrams right-aligned, 10pt, 1.3 spacing"
    │
    ▼
  Opus → presents design proposal to User:
    "Based on original layout: 2-column with problem boxes. Proceed?"
    │
    ├── User: "Approve" → generate LaTeX template
    ├── User: "Change to 1-column" → Opus adjusts → re-confirm
    └── User: "Custom specs" → user dictates → Opus implements

Flow (Editing):
  User: "Change to 1-column" / "Add problem boxes"
    → Opus: modify LaTeX structure → User confirms
```

### 4.4 Loop D: Layout Verification Loop

```
Implementation: cow/core/layout_verify.py (uses Loop A) + Opus UX
Participants: Gemini (visual check) + Opus (relay/fix) + User (final judge)
Character: Reactive quality check — "Is the compiled output correct?"

Scope:
  - Text/diagram overlap detection
  - Page overflow / content truncation
  - Alignment and spacing correctness
  - Diagram rendering quality
  - Overall visual fidelity

Flow:
  Python: compiled PDF → PNG → Gemini L1+L2 (Loop A)
    → layout report (text only):
      "Problem 2 diagram overlaps solution text by 8pt.
       Bottom 3 lines truncated on page 1.
       Rest OK."
    │
    ▼
  Opus → presents report + PDF path to User
    │
    ├── User: "Approve" → done
    ├── User: "Fix per Gemini" → Opus edits LaTeX → recompile → Loop D again
    ├── User: "Also fix this: ..." → Opus applies both → recompile → Loop D
    └── User: "Gemini is wrong, this is fine" → override → done
```

### 4.5 Loop E: Content Edit Loop (Pipeline 2 only)

```
Implementation: Opus orchestration pattern (Claude Code)
Participants: Opus 4.6 + User
Character: Natural language content editing with logical verification
Prerequisite: Pipeline 1 (Reconstruction) completed

Flow:
  User: "Change vertex from (3,-7) to (4,-5)"
    │
    ▼
  Opus: edit .tex content (Claude Code Edit tool)
    - Direct modification
    - Cascade impact analysis (coefficient changes, solution recalculation, answer update)
    │
    ▼
  Loop B: logical verification + user approval
    │
    ├── Approved → compile → Loop D (layout verification)
    └── Rejected → Opus re-edits → Loop B again
```

### 4.6 Loop F: Design Edit Loop (Pipeline 2 only)

```
Implementation: Opus orchestration + cow/core/layout_*.py
Participants: User + Opus + Gemini
Character: Layout/design modification with visual verification
Prerequisite: Pipeline 1 (Reconstruction) completed

Flow:
  User: "Wrap problems in boxes" / "Change to 1-column"
    │
    ▼
  Opus: modify LaTeX design structure (Edit tool)
    │
    ▼
  compile → Loop D (layout verification)
    │
    ├── Approved → done
    └── Rejected → Opus re-edits → recompile → Loop D
```

---

## 5. Pipeline 1: Reconstruction (Required)

### 5.1 Flow

```
STEP 0: Preprocessing
  Input: PDF file (user-provided)
  Process: PDF → PNG at 600 DPI (local, pdf2image)
  Output: High-resolution PNG(s)
  Cost: $0

STEP 1: Interactive Configuration
  Opus presents page overview (via Gemini L1 quick scan)
  Per-problem module selection via AskUserQuestion:
    - OCR source: Gemini / Mathpix / both
    - Diagram processing: crop / skip
    - Model selection: image_model, reasoning_model
    - Quality params: temperature, max_iterations

  Progressive automation:
    Level 1: Full per-problem selection
    Level 2: "Same as last time?" batch approval
    Level 3: Auto-apply learned defaults

STEP 2: Content Extraction (Loop A x N)
  2a: OCR — cow/core/ocr.py
    Loop A (L1+L2) → converged LaTeX text
    (Gemini OCR or Mathpix, per user selection)

  2b: Diagram Detection + Crop — cow/core/diagram.py
    Loop A (L1+L2) → verified bbox JSON
    PIL crop → Loop A (crop verification) → verified diagram PNGs

  2a and 2b run in parallel where possible.

STEP 3: Layout Design (Loop C)
  cow/core/layout_design.py
  Gemini L1+L2 analyzes original page layout → text report
  Opus presents design proposal → user approves/modifies
  Output: confirmed LaTeX template structure

STEP 4: Logical Verification (Loop B)
  Opus 4.6 (L3) — text/LaTeX input ONLY
  Verifies: math correctness, logic chains, LaTeX integrity, completeness
  Reports to user → user final approval

STEP 5: LaTeX Composition
  Opus 4.6 — logical structural task
  Assembles: approved OCR text + design template + diagram file references
  Output: complete .tex file

STEP 6: Compile
  cow/core/compile.py
  XeLaTeX + kotex → PDF
  On compile error: error log → Opus → .tex fix → retry

STEP 7: Layout Verification (Loop D)
  cow/core/layout_verify.py
  PDF → PNG → Gemini L1+L2 → text report
  Opus presents report + PDF path → user final approval
  If rejected: Opus fixes → STEP 6 → STEP 7

COMPLETE → user chooses: finish OR enter Pipeline 2
```

### 5.2 Step Dependencies

```
STEP 0 ──→ STEP 1 ──→ STEP 2a ──→ STEP 4 ──→ STEP 5 ──→ STEP 6 ──→ STEP 7
                   └──→ STEP 2b ──┘
                   └──→ STEP 3 ───────────────┘

2a, 2b, 3 can run in parallel after STEP 1.
STEP 4 requires 2a and 2b output.
STEP 5 requires 3 and 4 output.
```

---

## 6. Pipeline 2: Editing (Optional)

### 6.1 Entry Condition

Pipeline 1 must be complete. Input: .tex file + diagram PNGs from Pipeline 1.

### 6.2 Flow

```
User edit request
  │
  ▼
Opus: classify edit type
  │
  ├── Content edit → Loop E
  │   (math changes, problem restructuring, solution edits)
  │
  ├── Design edit → Loop F
  │   (boxes, columns, diagram sizing, typography)
  │
  └── Combined → Loop E then Loop F (sequential)
  │
  ▼
Final compile → Loop D (layout verification) → user approval
  │
  ├── Done → save
  └── More edits → re-enter Pipeline 2
```

---

## 7. Python SDK Module Design

### 7.1 Directory Structure

```
cow/
├── core/
│   ├── __init__.py
│   ├── gemini_loop.py        # Loop A: L1+L2 building block
│   ├── ocr.py                # OCR extraction (uses Loop A)
│   ├── diagram.py            # Diagram detection + crop (uses Loop A)
│   ├── layout_design.py      # Loop C: layout analysis (uses Loop A)
│   ├── layout_verify.py      # Loop D: layout verification (uses Loop A)
│   └── compile.py            # XeLaTeX compilation
│
├── config/
│   ├── __init__.py
│   ├── models.py             # Model configuration + fail-stop validation
│   └── profiles.py           # User presets for progressive automation
│
├── cli.py                    # CLI wrapper for Claude Code integration
├── requirements.txt          # google-genai, Pillow, requests, pdf2image
│
├── docs/                     # KEEP from v1
├── images/                   # KEEP from v1
├── sample.pdf                # KEEP
└── sample2.pdf               # KEEP
```

### 7.2 Module Specifications

#### 7.2.1 gemini_loop.py — Loop A

```python
class GeminiQualityLoop:
    """
    Dual-model quality convergence loop.
    L1 (image model) generates, L2 (reasoning model) validates.
    Repeats until convergence or max_iterations.

    All visual tasks use this as their foundation.
    Returns TEXT/JSON only — never returns images.
    """

    def __init__(self,
                 image_model: str = "gemini-3-pro-image-preview",
                 reasoning_model: str = "gemini-3-pro-preview",
                 api_key: str = None):
        # Fail-stop: verify model availability on init
        # If model returns 404 → raise ModelUnavailableError (no fallback)

    def run(self,
            image_path: str,
            task_prompt: str,
            validation_prompt: str,
            temperature: float = 0.1,
            max_iterations: int = 3,
            confidence_threshold: float = 0.9) -> LoopResult:
        """
        Returns: LoopResult(
            result: str/dict,       # converged output
            iterations: int,        # how many loops ran
            confidence: float,      # final confidence
            l1_history: list,       # L1 outputs per iteration
            l2_feedback: list,      # L2 feedback per iteration
        )
        """
```

#### 7.2.2 ocr.py

```python
def extract_gemini(image_path: str, loop_params: dict) -> OcrResult:
    """Gemini OCR via Loop A. Returns LaTeX text."""

def extract_mathpix(image_path: str, app_id: str, app_key: str) -> OcrResult:
    """Mathpix v3/text OCR. Returns LaTeX text.
    Note: Do NOT use include_line_data + include_word_data together (ISS-1).
    """
```

#### 7.2.3 diagram.py

```python
def detect_diagrams(image_path: str, loop_params: dict) -> list[BboxResult]:
    """Detect diagram regions via Loop A. Returns bbox list.
    Note: Gemini returns ~1000-unit width scale. Apply scale factor (ISS-4).
    """

def crop_diagrams(image_path: str, bboxes: list[BboxResult], padding: int = 15) -> list[str]:
    """PIL crop using scaled bbox coordinates. Returns list of cropped PNG paths."""

def verify_crops(crop_paths: list[str], loop_params: dict) -> list[CropVerifyResult]:
    """Verify crop quality via Loop A. Returns pass/fail + correction suggestions."""
```

#### 7.2.4 layout_design.py

```python
def analyze_layout(image_path: str, loop_params: dict) -> LayoutDesignReport:
    """Analyze original page layout via Loop A.
    Returns text report: column config, box styles, diagram placement,
    typography settings, etc.
    """
```

#### 7.2.5 layout_verify.py

```python
def verify_layout(pdf_path: str, loop_params: dict) -> LayoutVerifyReport:
    """Verify compiled PDF layout via Loop A.
    Converts PDF → PNG internally, sends to Gemini.
    Returns text report: overlaps, truncation, alignment issues,
    or PASS if layout is correct.
    """
```

#### 7.2.6 compile.py

```python
def compile_latex(tex_path: str, output_dir: str = None) -> CompileResult:
    """XeLaTeX + kotex compilation.
    Runs xelatex with Korean font support (Noto CJK KR).
    Returns: CompileResult(pdf_path, success, error_log)
    """
```

#### 7.2.7 config/models.py

```python
class ModelConfig:
    """Model configuration with fail-stop validation.
    On init: pings model endpoint to verify availability.
    Raises ModelUnavailableError if model not found (AD-9).
    """

    image_model: str = "gemini-3-pro-image-preview"
    reasoning_model: str = "gemini-3-pro-preview"

    def validate(self) -> None:
        """Verify all models are available. Fail-stop on any 404."""
```

#### 7.2.8 config/profiles.py

```python
class UserProfile:
    """User presets for progressive automation.
    Stores per-problem-type defaults that evolve over time.

    Level 1: No defaults — full interactive selection
    Level 2: Type-based defaults — user approves batch
    Level 3: Auto-apply — user reviews final output only
    """

    def get_defaults(self, problem_type: str) -> dict:
        """Return stored defaults for a problem type."""

    def save_selection(self, problem_type: str, selection: dict) -> None:
        """Record user selection for future default inference."""
```

### 7.3 CLI Wrapper — Claude Code Integration

```python
# cow/cli.py
# Opus (Claude Code) calls this via Bash tool.
# Returns JSON on stdout. Errors on stderr. Exit codes: 0=ok, 1=fail-stop, 2=error.

Commands:

  python cow/cli.py validate-models
    → Checks all model IDs are available. Fail-stop if any missing.

  python cow/cli.py ocr \
      --image <path> \
      --method gemini|mathpix \
      --image-model <model-id> \
      --reasoning-model <model-id> \
      --temperature <float> \
      --max-iterations <int>
    → Returns: {"text": "...", "confidence": 0.95, "iterations": 2}

  python cow/cli.py diagram detect \
      --image <path> \
      --image-model <model-id> \
      --reasoning-model <model-id>
    → Returns: {"diagrams": [{"id": 1, "bbox": {...}, "desc": "..."}]}

  python cow/cli.py diagram crop \
      --image <path> \
      --bboxes <json-path> \
      --padding <int>
    → Returns: {"crops": ["diagram_1.png", "diagram_2.png"]}

  python cow/cli.py diagram verify \
      --crops <path1> <path2> ...
    → Returns: {"results": [{"path": "...", "pass": true, "issues": []}]}

  python cow/cli.py layout analyze \
      --image <path>
    → Returns: {"report": "2-column, bold numbers, ...", "confidence": 0.92}

  python cow/cli.py layout verify \
      --pdf <path>
    → Returns: {"pass": false, "issues": ["overlap at problem 2", ...]}

  python cow/cli.py compile \
      --tex <path> \
      --output-dir <path>
    → Returns: {"pdf_path": "...", "success": true}

  python cow/cli.py preprocess \
      --pdf <path> \
      --dpi 600
    → Returns: {"pages": [{"path": "page_1.png", "width": 4960, "height": 7010}]}
```

---

## 8. Interactive UX — Progressive Automation

### 8.1 Levels

```
Level 1 (Manual) — Initial usage
  Per-problem AskUserQuestion:
    - OCR source selection
    - Diagram processing toggle
    - Model/parameter selection
    - Design approval
    - Verification approval

Level 2 (Semi-auto) — After patterns emerge
  Opus: "3 problems detected. Applying previous defaults:
    Text-only → [Gemini OCR + L3]
    With diagram → [Gemini OCR + crop + L3]
    Proceed with these settings?"
  User: approve batch OR modify individual

Level 3 (Full auto) — After trust is established
  Opus: runs full pipeline autonomously
  User: reviews final PDF only
  Triggered by: user says "자동으로 해줘" or similar
```

### 8.2 Level Transitions

Transitions are user-driven via natural language:
- "자동으로 해줘" → Level 3
- "하나씩 확인할게" → Level 1
- "기본값으로 하되 다이어그램만 확인" → Level 2 with selective override

Stored in: `cow/config/profiles.py`

---

## 9. Architecture Decisions Summary

| # | Decision | Rationale |
|---|----------|-----------|
| AD-1 | Single Pipeline (no A/B comparison) | This design IS the pipeline |
| AD-2 | Hybrid Diagram (image crop + includegraphics) | TikZ too complex for automation |
| AD-3 | 600 DPI preprocessing | Max quality, negligible cost impact |
| AD-4 | Direct API usage (Gemini + Mathpix keys outside MCP) | User authorized |
| AD-5 | Gemini bbox protocol (scale correction) | Gemini returns ~1000-unit width |
| AD-6 | MCP vision tools insufficient | Use Gemini direct API instead |
| AD-7 | Operational lessons (Gemini-first) | Never manual pixel estimation |
| AD-8 | Model Role Separation | Opus=logic, Gemini=vision, absolute |
| AD-9 | No Fallback — Fail-Stop | Silent degradation forbidden |
| AD-10 | Framework Discipline | ASCII visualization + user approval gate |
| AD-11 | Triple-Layer Verification | L1 image + L2 reasoning + L3 Opus |
| AD-12 | Gemini 3.0 Only | No 2.5 models, all image models 3.0 |
| AD-13 | Progressive Automation | Level 1→2→3, user-driven transitions |
| AD-14 | Python SDK + CLI Wrapper | Core Python, Claude Code via Bash |
| AD-15 | Claude Max X20 cost model | Opus=free, minimize Gemini calls |
| AD-16 | L3 = Opus+User loop | User final approval required |
| AD-17 | Two-Pipeline architecture | Reconstruction (required) + Editing (optional) |
| AD-18 | Loop-based modular design | 6 composable loops (A-F) |
| AD-19 | Layout Design/Verification split | Proactive design vs reactive verification |
| AD-20 | Full codebase rebuild | Delete cow-cli/ and cow-mcp/ entirely |

---

## 10. Known Issues (from v1.0 experience)

| ID | Issue | Mitigation |
|----|-------|------------|
| ISS-1 | Mathpix opts_conflict (line_data + word_data) | Never use both simultaneously |
| ISS-2 | Gemini OCR hallucination (\quad repetition) | Loop A L2 cross-validation catches this |
| ISS-3 | Gemini API hang (no response) | CLI timeout + retry logic |
| ISS-4 | Gemini bbox ~1000-unit scale | Always apply SCALE = actual_width/1000 |
| ISS-5 | MCP vision tools insufficient for bbox | Use Gemini direct API (AD-6) |
| ISS-6 | gemini-3-pro-image-preview availability | validate-models check at pipeline start (AD-9) |

---

## 11. Cost Model

```
Claude Max X20 subscription:
  Opus 4.6 (L3 + composition + editing + UX) = FREE (included)
  → Maximize Opus usage for verification and editing

Variable costs (per page):
  Gemini L1+L2 calls:
    OCR: ~2-6 calls (1-3 iterations × 2 models)
    Diagram detect: ~2-6 calls
    Diagram crop verify: ~2-6 calls per diagram
    Layout design: ~2-6 calls
    Layout verify: ~2-6 calls
    Total estimate: 10-30 Gemini calls per page

  Mathpix (optional): 1 call per page

  XeLaTeX: $0 (local)
  pdf2image: $0 (local)

Strategy: Opus handles as much as possible (free).
Gemini calls bounded by max_iterations parameter.
```

---

## 12. Dependencies

```
# cow/requirements.txt
google-genai>=1.0.0      # Gemini API SDK
Pillow>=10.0.0           # Image cropping
requests>=2.31.0         # Mathpix API calls
pdf2image>=1.17.0        # PDF → PNG conversion
```

System dependencies:
- `poppler-utils` (for pdf2image)
- `texlive-xetex`, `texlive-lang-korean` (for XeLaTeX + kotex)
- `fonts-noto-cjk` (Noto Sans CJK KR)

---

## 13. Implementation Priority

```
Phase 1: Core infrastructure
  - gemini_loop.py (Loop A — foundation for everything)
  - config/models.py (fail-stop validation)
  - cli.py (basic CLI framework)

Phase 2: Extraction modules
  - ocr.py (Gemini + Mathpix)
  - diagram.py (detect + crop + verify)

Phase 3: Layout modules
  - layout_design.py (Loop C)
  - layout_verify.py (Loop D)
  - compile.py (XeLaTeX)

Phase 4: Pipeline 1 integration test
  - End-to-end: PDF → OCR → design → verify → compose → compile → layout check

Phase 5: Pipeline 2 (Editing)
  - Loop E (content edit) + Loop F (design edit) orchestration patterns

Phase 6: Progressive automation
  - config/profiles.py
  - Level 1→2→3 transition logic
```
