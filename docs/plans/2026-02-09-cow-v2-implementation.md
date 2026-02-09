# COW Pipeline v2.0 — Implementation Plan

> **For Lead:** This plan is designed for Agent Teams native execution.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.
> User mandate: Lead self-approves all gates autonomously.

**Goal:** Replace the entire COW v1.0 codebase (cow-cli/, cow-mcp/, 6 MCP servers) with a Python SDK + CLI
wrapper implementing Triple-Layer Verification architecture (L1: Gemini image, L2: Gemini reasoning, L3: Opus logic).

**Architecture:** Python SDK in `cow/core/` and `cow/config/`, CLI wrapper at `cow/cli.py`.
Opus calls CLI via Bash tool, receives JSON on stdout. Gemini API called directly within Python SDK.
All models are Gemini 3.0 series — fail-stop on unavailability (AD-9).

**Design Source:** `docs/plans/2026-02-09-cow-v2-design.md` (approved, 779 lines, 20 ADs)

**Pipeline:** Phase 4 → 5 → 6 → 7-8 → 9 (full product pipeline)

---

## 1. Orchestration Overview (Lead Instructions)

### Pipeline Structure

```
Phase 4: Detailed Design    — Architect produces this plan (COMPLETE)
Phase 5: Plan Validation    — Devils-advocate challenges assumptions
Phase 6: Implementation     — 4 implementers execute file specs
Phase 7-8: Testing          — 1-2 testers validate + 1 integrator merges
Phase 9: Delivery           — Lead commits and cleans up
```

### Teammate Allocation

| Role | Count | Agent Type | File Ownership | Phase |
|------|-------|-----------|----------------|-------|
| Implementer 1 | 1 | `implementer` | Foundation: gemini_loop.py, config/ (4 files) | 6 |
| Implementer 2 | 1 | `implementer` | Extraction: ocr.py, diagram.py (2 files) | 6 |
| Implementer 3 | 1 | `implementer` | Layout+Compile: layout_design.py, layout_verify.py, compile.py (3 files) | 6 |
| Implementer 4 | 1 | `implementer` | CLI+Config+Cleanup: cli.py, profiles.py, requirements.txt, legacy deletion (4+ files) | 6 |
| Tester 1 | 1 | `tester` | Unit + integration tests | 7 |
| Integrator 1 | 1 | `integrator` | Cross-boundary merge + MCP cleanup | 8 |

### Execution Sequence

```
Lead:   TeamCreate("cow-v2-execution")
Lead:   TaskCreate × 6 (Tasks A-F — see §4)
Lead:   Spawn Implementer 1 (foundation)
Lead:   Send directive with PT + §5.1-§5.4 specs
        ┌─────────────────────────────────────────────────┐
        │ Imp-1: Understanding verification               │
        │ Imp-1: Execute Task A (foundation files)        │
        │ Imp-1: Write L1/L2/L3 → report complete        │
        └─────────────────────────────────────────────────┘
Lead:   Verify Imp-1 artifacts exist. Spawn Imp-2 + Imp-3 IN PARALLEL.
Lead:   Send directives: Imp-2 gets §5.5-§5.6, Imp-3 gets §5.7-§5.9
        ┌─────────────────────────────────────────────────┐
        │ Imp-2: Execute Task B (ocr.py, diagram.py)      │
        │ Imp-3: Execute Task C (layout + compile)        │
        │ (PARALLEL — zero file overlap)                   │
        └─────────────────────────────────────────────────┘
Lead:   Verify Imp-2+3 artifacts. Spawn Imp-4.
Lead:   Send directive: Imp-4 gets §5.10-§5.12 + cleanup list
        ┌─────────────────────────────────────────────────┐
        │ Imp-4: Execute Task D (cli.py, profiles.py, req)│
        │ Imp-4: Execute Task E (legacy deletion)         │
        └─────────────────────────────────────────────────┘
Lead:   Gate 6 review → Spawn Tester 1
        ┌─────────────────────────────────────────────────┐
        │ Tester: Execute Task F (validation checklist)   │
        └─────────────────────────────────────────────────┘
Lead:   Gate 7 → Spawn Integrator (MCP cleanup + .claude.json)
Lead:   Gate 8 → Phase 9 Delivery
```

### Autonomous Execution Note
Per user mandate, Lead self-approves all gates. No user confirmation needed for phase transitions
within this pipeline. User involvement resumes at Phase 9 delivery (commit approval).

---

## 2. global-context.md Template

> Lead: Create this as `.agent/teams/{session-id}/global-context.md` at TeamCreate time.

```yaml
---
version: GC-v4
project: COW Pipeline v2.0
pipeline: Full Product (Phase 4 → 5 → 6 → 7-8 → 9)
current_phase: 6
---
```

```markdown
# Global Context — COW Pipeline v2.0

## Project Summary
Complete rebuild of the COW (Convert OCR Worksheet) pipeline. Deletes all v1.0 code
(cow-cli/, cow-mcp/, 6 MCP servers, ~93 Python files) and replaces with a Python SDK + CLI
wrapper (~12 files) implementing Triple-Layer Verification: Gemini L1 (image) + L2 (reasoning)
+ Opus L3 (logic verification, LaTeX composition, interactive UX).

## Design Reference
- Approved design: `docs/plans/2026-02-09-cow-v2-design.md` (779 lines)
- Implementation plan: `docs/plans/2026-02-09-cow-v2-implementation.md` (this plan)

## Key Architecture Decisions (abbreviated — full list in design §9)
- AD-8: Model Role Separation — Opus=logic only, Gemini=vision only, absolute boundary
- AD-9: Fail-Stop — NO fallback models. Pipeline halts on model unavailability.
- AD-11: Triple-Layer Verification — L1 image + L2 reasoning + L3 Opus
- AD-12: Gemini 3.0 Only — No 2.5 models permitted
- AD-14: Python SDK + CLI Wrapper — core Python, Claude Code integrates via Bash
- AD-15: Claude Max X20 — Opus=free, minimize Gemini API calls
- AD-20: Full codebase rebuild — delete cow-cli/ and cow-mcp/ entirely

## Component Map
```
cow/
├── core/
│   ├── __init__.py           → Imp-1 (exports public API)
│   ├── gemini_loop.py        → Imp-1 (Loop A: L1+L2 foundation)
│   ├── ocr.py                → Imp-2 (OCR extraction)
│   ├── diagram.py            → Imp-2 (diagram detect+crop+verify)
│   ├── layout_design.py      → Imp-3 (Loop C: layout analysis)
│   ├── layout_verify.py      → Imp-3 (Loop D: layout verification)
│   └── compile.py            → Imp-3 (XeLaTeX compilation)
├── config/
│   ├── __init__.py           → Imp-1 (exports config API)
│   ├── models.py             → Imp-1 (model config + fail-stop)
│   └── profiles.py           → Imp-4 (user presets)
├── cli.py                    → Imp-4 (CLI wrapper)
└── requirements.txt          → Imp-4 (4 packages)
```

## Interface Contracts
- GeminiQualityLoop.run() → LoopResult (used by ocr, diagram, layout_design, layout_verify)
- ModelConfig.validate() → raises ModelUnavailableError (called at pipeline start)
- CLI commands → JSON stdout, exit codes: 0=ok, 1=fail-stop, 2=error
- API keys: GEMINI_API_KEY, MATHPIX_APP_ID, MATHPIX_APP_KEY via os.environ

## Known Issues (from v1.0)
| ID | Issue | Mitigation |
|----|-------|------------|
| ISS-1 | Mathpix opts_conflict | Never use line_data + word_data together |
| ISS-2 | Gemini OCR hallucination | Loop A L2 cross-validation |
| ISS-3 | Gemini API hang | CLI timeout + retry |
| ISS-4 | Gemini bbox ~1000-unit scale | Apply SCALE = actual_width/1000 |
| ISS-5 | MCP vision insufficient | Direct Gemini API (AD-6) |
| ISS-6 | Model availability | validate-models at pipeline start (AD-9) |

## Active Teammates
(Lead updates this as teammates are spawned)

## Phase Status
- Phase 4 (Detailed Design): COMPLETE
- Phase 5 (Plan Validation): PENDING
- Phase 6 (Implementation): PENDING
- Phase 7-8 (Testing): PENDING
- Phase 9 (Delivery): PENDING
```

---

## 3. File Ownership Map

### Implementer 1 — Foundation (4 files)

| File | Operation | Est. Lines |
|------|-----------|-----------|
| `cow/core/__init__.py` | CREATE | ~15 |
| `cow/core/gemini_loop.py` | CREATE | ~150 |
| `cow/config/__init__.py` | CREATE | ~10 |
| `cow/config/models.py` | CREATE | ~50 |

**Dependency:** None (first to execute). All other implementers depend on Imp-1's output.

### Implementer 2 — Extraction (2 files)

| File | Operation | Est. Lines |
|------|-----------|-----------|
| `cow/core/ocr.py` | CREATE | ~100 |
| `cow/core/diagram.py` | CREATE | ~120 |

**Dependency:** Imp-1 must complete first (imports GeminiQualityLoop, LoopResult, ModelConfig).

### Implementer 3 — Layout + Compile (3 files)

| File | Operation | Est. Lines |
|------|-----------|-----------|
| `cow/core/layout_design.py` | CREATE | ~80 |
| `cow/core/layout_verify.py` | CREATE | ~80 |
| `cow/core/compile.py` | CREATE | ~60 |

**Dependency:** Imp-1 must complete first (imports GeminiQualityLoop, LoopResult).

### Implementer 4 — CLI + Config + Cleanup (4+ files)

| File | Operation | Est. Lines |
|------|-----------|-----------|
| `cow/cli.py` | CREATE | ~200 |
| `cow/config/profiles.py` | CREATE | ~60 |
| `cow/requirements.txt` | REPLACE | ~5 |
| `cow/cow-cli/` | DELETE | -3000+ |
| `cow/cow-mcp/` | DELETE | -3000+ |
| `cow/*.png`, `cow/*.pdf` (test artifacts) | DELETE | — |
| `cow/PIPELINE-REFERENCE.md` | DELETE | — |
| `cow/outputs/` | DELETE | — |

**Dependency:** Imp-1, Imp-2, Imp-3 must all complete first (CLI imports all modules).

### Non-Overlap Verification

```
Imp-1: cow/core/__init__.py, cow/core/gemini_loop.py, cow/config/__init__.py, cow/config/models.py
Imp-2: cow/core/ocr.py, cow/core/diagram.py
Imp-3: cow/core/layout_design.py, cow/core/layout_verify.py, cow/core/compile.py
Imp-4: cow/cli.py, cow/config/profiles.py, cow/requirements.txt

Zero overlap confirmed. Cleanup (deletion) assigned to Imp-4 or Integrator.
```

### Dependency Graph

```
         Imp-1 (foundation)
        /       \
    Imp-2    Imp-3    ← PARALLEL (zero overlap, same dependency)
        \       /
         Imp-4 (cli + cleanup)
           |
        Tester
           |
       Integrator (MCP cleanup)
```

---

## 4. Task Definitions

### Task A: Create Foundation Modules (Implementer 1)

```
subject: "Create cow/core/gemini_loop.py and cow/config/models.py foundation"

description: |
  ## Objective
  Build the foundational GeminiQualityLoop (Loop A) and ModelConfig modules that all
  other cow/core/ modules depend on. This is the critical path — no other implementer
  can begin until Task A is complete.

  ## Files to Create
  1. cow/core/__init__.py — public API exports (see §5.1)
  2. cow/core/gemini_loop.py — Loop A dual-model quality loop (see §5.2)
  3. cow/config/__init__.py — config exports (see §5.3)
  4. cow/config/models.py — model config + fail-stop validation (see §5.4)

  ## Acceptance Criteria
  AC-0: Read §5.1-§5.4, verify against design file §7.2.1 and §7.2.7, report any
        discrepancies before proceeding.
  AC-1: GeminiQualityLoop.__init__() validates model availability via google-genai SDK.
  AC-2: GeminiQualityLoop.run() returns LoopResult dataclass with all 5 fields.
  AC-3: ModelConfig.validate() raises ModelUnavailableError on 404 (AD-9 fail-stop).
  AC-4: All imports use `from google import genai` (google-genai SDK, NOT google-generativeai).
  AC-5: LoopResult and ModelUnavailableError are importable from cow.core and cow.config.
  AC-6: No async code — all functions are synchronous (Opus calls via Bash, no event loop).

  ## Dependency Chain
  blockedBy: []
  blocks: [Task B, Task C, Task D]

activeForm: "Creating foundation modules (gemini_loop + config)"
```

### Task B: Create Extraction Modules (Implementer 2)

```
subject: "Create cow/core/ocr.py and cow/core/diagram.py extraction modules"

description: |
  ## Objective
  Build OCR extraction (Gemini + Mathpix) and diagram detection/cropping modules
  that use GeminiQualityLoop from Task A.

  ## Files to Create
  1. cow/core/ocr.py — Gemini and Mathpix OCR (see §5.5)
  2. cow/core/diagram.py — diagram detect + crop + verify (see §5.6)

  ## Acceptance Criteria
  AC-0: Read §5.5-§5.6, verify against design file §7.2.2-§7.2.3, report discrepancies.
  AC-0b: Read cow/core/gemini_loop.py (Imp-1 output). Verify LoopResult fields and
         GeminiQualityLoop.run() signature match §6.1 FROZEN CONTRACT. Report deviations
         to Lead before proceeding.
  AC-1: extract_gemini() creates GeminiQualityLoop and calls run() with OCR-specific prompts.
  AC-2: extract_mathpix() uses requests (sync) to call Mathpix v3/text. No async.
  AC-3: extract_mathpix() never uses include_line_data + include_word_data together (ISS-1).
  AC-4: detect_diagrams() applies SCALE = actual_width / 1000 to Gemini bbox (ISS-4).
  AC-5: crop_diagrams() uses PIL to crop with padding. Returns list of saved PNG paths.
  AC-6: verify_crops() uses GeminiQualityLoop to verify each crop.
  AC-7: All functions return typed result dataclasses (OcrResult, BboxResult, CropVerifyResult).

  ## Dependency Chain
  blockedBy: [Task A]
  blocks: [Task D]

activeForm: "Creating extraction modules (ocr + diagram)"
```

### Task C: Create Layout and Compile Modules (Implementer 3)

```
subject: "Create cow/core/layout_design.py, layout_verify.py, and compile.py"

description: |
  ## Objective
  Build layout analysis (Loop C), layout verification (Loop D), and XeLaTeX compilation
  modules that use GeminiQualityLoop from Task A.

  ## Files to Create
  1. cow/core/layout_design.py — Loop C layout analysis (see §5.7)
  2. cow/core/layout_verify.py — Loop D layout verification (see §5.8)
  3. cow/core/compile.py — XeLaTeX compilation (see §5.9)

  ## Acceptance Criteria
  AC-0: Read §5.7-§5.9, verify against design file §7.2.4-§7.2.6, report discrepancies.
  AC-0b: Read cow/core/gemini_loop.py (Imp-1 output). Verify LoopResult fields and
         GeminiQualityLoop.run() signature match §6.1 FROZEN CONTRACT. Report deviations
         to Lead before proceeding.
  AC-1: analyze_layout() creates GeminiQualityLoop and returns LayoutDesignReport (text).
  AC-2: verify_layout() converts PDF→PNG internally (pdf2image), sends to Loop A.
  AC-3: compile_latex() runs `xelatex -interaction=nonstopmode -halt-on-error`.
  AC-4: compile.py does NOT include Mathpix converter fallback (removed per AD-9).
  AC-5: compile_latex() returns CompileResult with pdf_path, success, error_log.
  AC-6: All modules are synchronous (subprocess.run for xelatex, not asyncio).

  ## Dependency Chain
  blockedBy: [Task A]
  blocks: [Task D]

activeForm: "Creating layout and compile modules"
```

### Task D: Create CLI Wrapper, Profiles, and Requirements (Implementer 4)

```
subject: "Create cow/cli.py, cow/config/profiles.py, and cow/requirements.txt"

description: |
  ## Objective
  Build the CLI wrapper that Opus calls via Bash, the user profiles module for progressive
  automation, and the new requirements.txt with minimal dependencies.

  ## Files to Create
  1. cow/cli.py — CLI wrapper with all subcommands (see §5.10)
  2. cow/config/profiles.py — user presets + progressive automation (see §5.11)
  3. cow/requirements.txt — 4 packages only (see §5.12)

  ## Acceptance Criteria
  AC-0: Read §5.10-§5.12, verify against design file §7.3 and §7.2.8, report discrepancies.
  AC-1: CLI uses argparse with subcommands: validate-models, ocr, diagram (detect/crop/verify),
        layout (analyze/verify), compile, preprocess.
  AC-2: All CLI commands output JSON to stdout. Errors go to stderr.
  AC-3: Exit codes: 0=success, 1=fail-stop (ModelUnavailableError), 2=runtime error.
  AC-4: UserProfile stores per-problem-type defaults in JSON file.
  AC-5: requirements.txt contains exactly: google-genai>=1.0.0, Pillow>=10.0.0,
        requests>=2.31.0, pdf2image>=1.17.0.
  AC-6: `python cow/cli.py --help` shows all subcommands.

  ## Dependency Chain
  blockedBy: [Task A, Task B, Task C]
  blocks: [Task E]

activeForm: "Creating CLI wrapper and configuration"
```

### Task E: Delete Legacy Code (Implementer 4 or Integrator)

```
subject: "Delete cow-cli/, cow-mcp/, and test artifacts"

description: |
  ## Objective
  Remove all v1.0 code per AD-20. This is a destructive operation requiring careful
  enumeration of what to delete vs. what to preserve.

  ## Files to DELETE
  - cow/cow-cli/ (entire directory — ~60 Python files)
  - cow/cow-mcp/ (entire directory — 33 Python files, .venv, etc.)
  - cow/*.png (test artifact images: 9.png, sample_p1.png, sample2_p1.png)
  - cow/*.pdf (test artifacts: 9_gemini_only.pdf, 9_mathpix_gemini.pdf,
    sample2.pdf — WAIT: sample2.pdf is in PRESERVE list, see below)
  - cow/sample_scenario_a_gemini_only.pdf
  - cow/sample_scenario_b_mathpix_gemini.pdf
  - cow/PIPELINE-REFERENCE.md
  - cow/outputs/ (if exists)

  ## Files to PRESERVE
  - cow/docs/ (reference documentation)
  - cow/images/ (source test images)
  - cow/sample.pdf (test input)
  - cow/sample2.pdf (test input)
  - cow/.gitignore (update, don't delete)

  ## MCP Cleanup (Integrator scope)
  Remove these entries from `.claude.json` mcpServers section:
  - cow-ingest, cow-ocr, cow-vision, cow-review, cow-export, cow-storage
  API keys remain accessible via environment variables.

  ## Acceptance Criteria
  AC-0: List all files to be deleted, verify each against the PRESERVE list above.
  AC-1: cow/cow-cli/ directory is completely removed.
  AC-2: cow/cow-mcp/ directory is completely removed (including .venv/).
  AC-3: Test artifact files (*.png, specific *.pdf) are removed from cow/ root.
  AC-4: cow/docs/, cow/images/, cow/sample.pdf, cow/sample2.pdf are untouched.
  AC-5: cow/.gitignore is preserved (updated if needed for new structure).
  AC-6: Before deleting any legacy directories, verify API keys are accessible:
        python -c "import os; assert os.environ.get('GEMINI_API_KEY'), 'GEMINI_API_KEY missing'"
        python -c "import os; assert os.environ.get('MATHPIX_APP_ID'), 'MATHPIX_APP_ID missing'"

  ## Dependency Chain
  blockedBy: [Task D]
  blocks: [Task F]

activeForm: "Deleting legacy v1.0 code"
```

### Task F: Validation and Testing (Tester)

```
subject: "Validate COW v2.0 modules against checklist (§7)"

description: |
  ## Objective
  Run the validation checklist from §7 against the implemented modules.

  ## Validation Steps
  See §7 for the complete checklist (V1-V8).

  ## Acceptance Criteria
  AC-0: Read §7, verify each validation item is executable.
  AC-1: V1 (Import validation) — all 8 modules importable without error.
  AC-2: V2 (CLI --help) — all subcommands listed correctly.
  AC-3: V3 (Unit tests) — at least smoke tests per module.
  AC-4: V4 (CLI smoke test) — preprocess command runs with sample2.pdf.
  AC-5: V7 (Fail-stop) — ModelUnavailableError raised with invalid model ID.
  AC-6: Test report written to L1/L2/L3 files.

  ## Dependency Chain
  blockedBy: [Task E]
  blocks: []

activeForm: "Validating COW v2.0 modules"
```

---

## 5. Per-File Specifications

### 5.1 cow/core/__init__.py

**VL-1** (Verified — matches design §7.1 directory structure)

```python
# cow/core/__init__.py
"""COW Pipeline v2.0 — Core modules for Triple-Layer Verification."""

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult
from cow.core.ocr import extract_gemini, extract_mathpix, OcrResult
from cow.core.diagram import (
    detect_diagrams, crop_diagrams, verify_crops,
    BboxResult, CropVerifyResult,
)
from cow.core.layout_design import analyze_layout, LayoutDesignReport
from cow.core.layout_verify import verify_layout, LayoutVerifyReport
from cow.core.compile import compile_latex, CompileResult

__all__ = [
    "GeminiQualityLoop", "LoopResult",
    "extract_gemini", "extract_mathpix", "OcrResult",
    "detect_diagrams", "crop_diagrams", "verify_crops",
    "BboxResult", "CropVerifyResult",
    "analyze_layout", "LayoutDesignReport",
    "verify_layout", "LayoutVerifyReport",
    "compile_latex", "CompileResult",
]
```

**Implementation Notes:**
- Imp-1 creates this file with ONLY the imports they own (gemini_loop, config).
  Imp-2/3/4 imports are added by the integrator after all modules exist.
- Initial version from Imp-1 should only export GeminiQualityLoop + LoopResult.

---

### 5.2 cow/core/gemini_loop.py — Loop A Foundation

**VL-2** (Inferred — based on design §7.2.1 + google-genai SDK docs)

**Purpose:** Dual-model quality convergence loop. L1 (image model) generates, L2 (reasoning model)
cross-validates. Repeats until convergence or max_iterations. Returns TEXT/JSON only.

**Estimated Lines:** ~150

```python
# cow/core/gemini_loop.py
"""Loop A: Dual-model Gemini quality convergence loop (L1+L2).

L1 (gemini-3-pro-image-preview) generates results from images.
L2 (gemini-3-pro-preview) cross-validates and provides feedback.
Repeats until confidence >= threshold or max_iterations reached.

Returns TEXT/JSON only — never returns images.
This is the foundation for all visual tasks: OCR, diagram, layout.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger("cow.core.gemini_loop")


class ModelUnavailableError(Exception):
    """Raised when a specified Gemini model is unavailable (AD-9 fail-stop)."""
    def __init__(self, model_id: str, detail: str = ""):
        self.model_id = model_id
        self.detail = detail
        super().__init__(f"Model unavailable: {model_id}. {detail}")


@dataclass
class LoopResult:
    """Result from a GeminiQualityLoop run.

    Attributes:
        result: Converged output (text or parsed dict).
        iterations: Number of L1+L2 cycles executed.
        confidence: Final confidence score from L2 (0.0-1.0).
        l1_history: L1 output per iteration (for debugging).
        l2_feedback: L2 feedback per iteration (for debugging).
        converged: Whether the loop reached the confidence threshold.
    """
    result: str | dict = ""
    iterations: int = 0
    confidence: float = 0.0
    l1_history: list = field(default_factory=list)
    l2_feedback: list = field(default_factory=list)
    converged: bool = False


class GeminiQualityLoop:
    """Dual-model quality convergence loop (Loop A).

    Used by: ocr.py, diagram.py, layout_design.py, layout_verify.py
    """

    def __init__(
        self,
        image_model: str = "gemini-3-pro-image-preview",
        reasoning_model: str = "gemini-3-pro-preview",
        api_key: str | None = None,
    ):
        """Initialize with model IDs and API key.

        Args:
            image_model: Gemini model ID for L1 (image analysis).
            reasoning_model: Gemini model ID for L2 (reasoning/validation).
            api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.

        Raises:
            ModelUnavailableError: If api_key is missing (AD-9 fail-stop).
        """
        self._image_model = image_model
        self._reasoning_model = reasoning_model
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

        if not self._api_key:
            raise ModelUnavailableError(
                image_model,
                "GEMINI_API_KEY not set. Set via environment variable."
            )

        self._client = genai.Client(api_key=self._api_key)

    def run(
        self,
        image_path: str,
        task_prompt: str,
        validation_prompt: str,
        temperature: float = 0.1,
        max_iterations: int = 3,
        confidence_threshold: float = 0.9,
    ) -> LoopResult:
        """Execute the L1+L2 convergence loop.

        Args:
            image_path: Path to input image (PNG).
            task_prompt: Prompt for L1 (what to extract/analyze).
            validation_prompt: Prompt for L2 (how to validate L1 output).
            temperature: Generation temperature for L1.
            max_iterations: Maximum L1→L2 cycles.
            confidence_threshold: L2 confidence required for convergence.

        Returns:
            LoopResult with converged result, iteration count, confidence.

        Raises:
            ModelUnavailableError: If model returns 404/not found.
            FileNotFoundError: If image_path does not exist.
        """
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Load image via PIL (proven pattern from v1.0 gemini.py)
        from PIL import Image as PILImage
        image = PILImage.open(img_path)

        l1_history = []
        l2_feedback_history = []
        feedback = ""

        # AD-9 fail-stop signals: 404, quota, deprecated, permission denied
        FAIL_STOP_SIGNALS = ["404", "not found", "quota", "deprecated",
                             "permission denied", "resource exhausted"]

        for iteration in range(1, max_iterations + 1):
            # --- L1: Image model generates result ---
            l1_prompt = task_prompt
            if feedback:
                l1_prompt += f"\n\nPrevious feedback to address:\n{feedback}"

            try:
                l1_response = self._client.models.generate_content(
                    model=self._image_model,
                    contents=[image, l1_prompt],
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                    ),
                )
                l1_result = l1_response.text
            except Exception as e:
                error_str = str(e).lower()
                if any(signal in error_str for signal in FAIL_STOP_SIGNALS):
                    raise ModelUnavailableError(self._image_model, str(e))
                raise

            l1_history.append(l1_result)

            # --- L2: Reasoning model validates ---
            l2_prompt = (
                f"{validation_prompt}\n\n"
                f"L1 output to validate:\n{l1_result}\n\n"
                "Respond with JSON: "
                '{"confidence": <float 0-1>, "pass": <bool>, "feedback": "<str>"}'
            )

            try:
                l2_response = self._client.models.generate_content(
                    model=self._reasoning_model,
                    contents=[image, l2_prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.0,  # L2 is deterministic validator
                    ),
                )
                l2_text = l2_response.text
            except Exception as e:
                error_str = str(e).lower()
                if any(signal in error_str for signal in FAIL_STOP_SIGNALS):
                    raise ModelUnavailableError(self._reasoning_model, str(e))
                raise

            # Parse L2 response
            l2_data = self._parse_l2_response(l2_text)
            l2_feedback_history.append(l2_data)

            confidence = l2_data.get("confidence", 0.0)
            passed = l2_data.get("pass", False)
            feedback = l2_data.get("feedback", "")

            if passed and confidence >= confidence_threshold:
                return LoopResult(
                    result=l1_result,
                    iterations=iteration,
                    confidence=confidence,
                    l1_history=l1_history,
                    l2_feedback=l2_feedback_history,
                    converged=True,
                )

        # Max iterations reached without convergence
        return LoopResult(
            result=l1_history[-1] if l1_history else "",
            iterations=max_iterations,
            confidence=l2_feedback_history[-1].get("confidence", 0.0) if l2_feedback_history else 0.0,
            l1_history=l1_history,
            l2_feedback=l2_feedback_history,
            converged=False,
        )

    @staticmethod
    def _parse_l2_response(text: str) -> dict:
        """Parse L2 JSON response. Tolerant of markdown code fences."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Remove markdown code fences
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: treat as low-confidence pass
            return {"confidence": 0.5, "pass": False, "feedback": text}
```

**Key Implementation Notes:**
1. **Synchronous API calls** — Opus calls this via `python cow/cli.py` (Bash). No event loop.
   Uses `self._client.models.generate_content()` (sync), NOT `self._client.aio.models`.
2. **PIL Image in contents** — Pass `PIL.Image.open()` directly as content element (proven by
   v1.0 gemini.py:142 which uses `contents=[image, prompt]`). No `files.upload()` needed.
3. **AD-9 fail-stop (expanded)** — FAIL_STOP_SIGNALS covers 404, quota, deprecated, permission
   denied, resource exhausted. All trigger ModelUnavailableError, never silently degrade.
4. **L2 is deterministic** — temperature=0.0 for the reasoning model.
5. **ISS-3 mitigation** — CLI-level timeout handles Gemini API hangs; this module focuses
   on the convergence logic.

**V6 Code Plausibility Notes:**
- VP-1: `genai.Client(api_key=...)` — **LOW risk.** v1.0 gemini.py:118 uses exactly this.
- VP-2: ~~ELIMINATED~~ — PIL Image in contents proven by v1.0 (no files.upload needed).
- VP-3: Sync `client.models.generate_content()` — **LOW risk.** v1.0 uses async counterpart
  `client.aio.models.generate_content()`. Sync API is the standard counterpart.
- VP-4: L2 response parsing assumes JSON format. Gemini may not always produce valid JSON
  even with explicit instructions. The `_parse_l2_response` fallback handles this.

---

### 5.3 cow/config/__init__.py

**VL-1** (Verified — simple exports)

```python
# cow/config/__init__.py
"""COW Pipeline v2.0 — Configuration and model management."""

from cow.config.models import ModelConfig, ModelUnavailableError

__all__ = ["ModelConfig", "ModelUnavailableError"]
```

**Implementation Notes:**
- Imp-1 creates with models.py exports only. profiles.py export added by Imp-4 or integrator.
- ModelUnavailableError is defined in gemini_loop.py but re-exported from config for convenience.
  Actually, it should be defined in config/models.py and imported by gemini_loop.py.
  **Decision: Define ModelUnavailableError in config/models.py (canonical location).
  gemini_loop.py imports it from cow.config.models.**

---

### 5.4 cow/config/models.py — Model Configuration + Fail-Stop

**VL-2** (Inferred — based on design §7.2.7 + google-genai SDK)

**Purpose:** Model configuration with fail-stop validation (AD-9). Pings model endpoints
on init to verify availability.

**Estimated Lines:** ~50

```python
# cow/config/models.py
"""Model configuration with fail-stop validation (AD-9).

On validate(): pings Gemini model endpoints to verify availability.
Raises ModelUnavailableError if any model returns 404.
No fallback — pipeline halts immediately.
"""

import logging
import os
from dataclasses import dataclass

from google import genai

logger = logging.getLogger("cow.config.models")


class ModelUnavailableError(Exception):
    """Raised when a required model is unavailable (AD-9 fail-stop).

    Attributes:
        model_id: The model identifier that failed.
        detail: Error details from the API.
    """
    def __init__(self, model_id: str, detail: str = ""):
        self.model_id = model_id
        self.detail = detail
        super().__init__(f"Model unavailable: {model_id}. {detail}")


@dataclass
class ModelConfig:
    """Model configuration for COW Pipeline v2.0.

    Defaults to Gemini 3.0 series (AD-12).
    All models are fail-stop — no fallback (AD-9).
    """

    image_model: str = "gemini-3-pro-image-preview"
    reasoning_model: str = "gemini-3-pro-preview"
    api_key: str = ""

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY", "")

    def validate(self) -> None:
        """Verify all models are available. Fail-stop on any 404.

        Sends a minimal request to each model to verify it exists and
        is accessible with the current API key.

        Raises:
            ModelUnavailableError: If any model is not accessible.
        """
        if not self.api_key:
            raise ModelUnavailableError(
                self.image_model,
                "GEMINI_API_KEY not set."
            )

        client = genai.Client(api_key=self.api_key)

        for model_id in [self.image_model, self.reasoning_model]:
            try:
                # Attempt to get model info to verify it exists
                client.models.get(model=model_id)
                logger.info(f"Model verified: {model_id}")
            except Exception as e:
                raise ModelUnavailableError(model_id, str(e))
```

**Key Implementation Notes:**
1. **ModelUnavailableError is canonical here** — gemini_loop.py imports it from this module.
2. **Validation = model ping** — `client.models.get(model=model_id)` verifies the model
   exists and is accessible. This is lightweight (no generation).
3. **Dataclass, not Pydantic** — minimal dependencies (design §12 lists only 4 packages,
   none of which is pydantic).

**V6 Code Plausibility Notes:**
- VP-5: `client.models.get(model=model_id)` — verify this API exists in google-genai SDK.
  May need `client.models.list()` and filter, or a different method.
- VP-6: Model ID format "gemini-3-pro-image-preview" — verify this is the correct format
  for the google-genai SDK (not "models/gemini-3-pro-image-preview").

---

### 5.5 cow/core/ocr.py — OCR Extraction

**VL-2** (Inferred — based on design §7.2.2 + v1.0 client.py patterns)

**Purpose:** OCR extraction via Gemini Loop A or Mathpix v3/text API. Returns LaTeX text.

**Estimated Lines:** ~100

```python
# cow/core/ocr.py
"""OCR extraction: Gemini (via Loop A) and Mathpix (v3/text API).

Two extraction methods — user selects per-problem:
- extract_gemini(): Uses GeminiQualityLoop for L1+L2 verified OCR.
- extract_mathpix(): Direct Mathpix v3/text API call (sync, requests).

ISS-1: Never use include_line_data + include_word_data together (Mathpix opts_conflict).
ISS-2: Gemini OCR hallucination mitigated by Loop A L2 cross-validation.
"""

import base64
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import requests

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult
from cow.config.models import ModelUnavailableError

logger = logging.getLogger("cow.core.ocr")


@dataclass
class OcrResult:
    """OCR extraction result.

    Attributes:
        text: Extracted LaTeX/text content.
        confidence: Overall confidence (0.0-1.0).
        method: "gemini" or "mathpix".
        iterations: Number of Loop A iterations (gemini only).
        raw_response: Raw API response for debugging.
    """
    text: str = ""
    confidence: float = 0.0
    method: str = ""
    iterations: int = 0
    raw_response: dict = field(default_factory=dict)


def extract_gemini(
    image_path: str,
    loop_params: dict | None = None,
) -> OcrResult:
    """Gemini OCR via Loop A (L1+L2 verified).

    Args:
        image_path: Path to image file (PNG).
        loop_params: Optional dict with keys: image_model, reasoning_model,
                     api_key, temperature, max_iterations, confidence_threshold.

    Returns:
        OcrResult with LaTeX text and confidence.
    """
    params = loop_params or {}

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Extract ALL text content from this image as LaTeX.\n"
        "Include mathematical expressions with proper LaTeX notation.\n"
        "Preserve the document structure: headings, problem numbers, solutions.\n"
        "Use $...$ for inline math and $$...$$ or \\[...\\] for display math.\n"
        "Return ONLY the LaTeX content, no commentary."
    )

    validation_prompt = (
        "Validate this OCR extraction against the original image.\n"
        "Check for:\n"
        "1. Missing text or equations\n"
        "2. Incorrect LaTeX notation\n"
        "3. Hallucinated content (\\quad repetition, ISS-2)\n"
        "4. Structural accuracy (problem numbers, section ordering)\n"
        "Score confidence 0-1 based on extraction quality."
    )

    result: LoopResult = loop.run(
        image_path=image_path,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    return OcrResult(
        text=result.result if isinstance(result.result, str) else json.dumps(result.result),
        confidence=result.confidence,
        method="gemini",
        iterations=result.iterations,
    )


def extract_mathpix(
    image_path: str,
    app_id: str | None = None,
    app_key: str | None = None,
) -> OcrResult:
    """Mathpix v3/text OCR (sync, requests).

    ISS-1: Never uses include_line_data + include_word_data together.

    Args:
        image_path: Path to image file.
        app_id: Mathpix app ID. Falls back to MATHPIX_APP_ID env var.
        app_key: Mathpix app key. Falls back to MATHPIX_APP_KEY env var.

    Returns:
        OcrResult with LaTeX text and confidence.

    Raises:
        ValueError: If Mathpix credentials are missing.
        requests.HTTPError: If API returns error status.
    """
    app_id = app_id or os.environ.get("MATHPIX_APP_ID", "")
    app_key = app_key or os.environ.get("MATHPIX_APP_KEY", "")

    if not app_id or not app_key:
        raise ValueError("Mathpix credentials not set. Set MATHPIX_APP_ID and MATHPIX_APP_KEY.")

    img_path = Path(image_path)
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image_bytes = img_path.read_bytes()
    src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"

    # ISS-1: Use include_line_data ONLY (no include_word_data)
    payload = {
        "src": src,
        "formats": ["text", "latex_styled"],
        "include_line_data": True,
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True,
    }

    headers = {
        "app_id": app_id,
        "app_key": app_key,
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.mathpix.com/v3/text",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    text = data.get("text", "") or data.get("latex_styled", "")
    confidence = data.get("confidence", 0.0) or data.get("confidence_rate", 0.0)

    return OcrResult(
        text=text,
        confidence=float(confidence),
        method="mathpix",
        iterations=1,
        raw_response=data,
    )
```

**Key Implementation Notes:**
1. **Sync requests** — No async. Mathpix call uses `requests.post()`.
2. **ISS-1 strict** — Only `include_line_data: True`, never `include_word_data`.
3. **ISS-2 mitigation** — Gemini OCR hallucination caught by L2 validation_prompt check.
4. **loop_params dict** — flexible parameter passing; CLI parses args and builds this dict.

---

### 5.6 cow/core/diagram.py — Diagram Detection + Crop + Verify

**VL-2** (Inferred — based on design §7.2.3 + ISS-4 scale correction)

**Purpose:** Detect diagram regions via Loop A, crop with PIL, verify crops via Loop A.

**Estimated Lines:** ~120

```python
# cow/core/diagram.py
"""Diagram detection, cropping, and verification.

- detect_diagrams(): Loop A detects diagram bounding boxes in the image.
- crop_diagrams(): PIL crops regions with padding.
- verify_crops(): Loop A verifies each crop is correctly extracted.

ISS-4: Gemini returns bbox in ~1000-unit width scale. Apply SCALE = actual_width / 1000.
ISS-5: MCP vision tools insufficient — uses direct Gemini API (AD-6).
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult

logger = logging.getLogger("cow.core.diagram")


@dataclass
class BboxResult:
    """Bounding box detection result.

    Attributes:
        id: Diagram identifier (e.g., "diagram_1").
        x, y, width, height: Pixel coordinates (after scale correction).
        description: Brief description of the diagram content.
        confidence: Detection confidence (0.0-1.0).
    """
    id: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    description: str = ""
    confidence: float = 0.0


@dataclass
class CropVerifyResult:
    """Crop verification result.

    Attributes:
        path: Path to the cropped PNG file.
        passed: Whether the crop passed verification.
        issues: List of issues found (empty if passed).
        confidence: Verification confidence (0.0-1.0).
    """
    path: str = ""
    passed: bool = False
    issues: list = field(default_factory=list)
    confidence: float = 0.0


def detect_diagrams(
    image_path: str,
    loop_params: dict | None = None,
) -> list[BboxResult]:
    """Detect diagram regions via Loop A.

    ISS-4: Applies scale correction — Gemini bbox uses ~1000-unit width.

    Args:
        image_path: Path to image file (PNG).
        loop_params: Optional GeminiQualityLoop parameters.

    Returns:
        List of BboxResult with pixel-coordinate bounding boxes.
    """
    params = loop_params or {}

    # Get actual image dimensions for scale correction (ISS-4)
    img = Image.open(image_path)
    actual_width, actual_height = img.size
    scale_x = actual_width / 1000.0  # ISS-4: Gemini uses ~1000-unit width
    scale_y = actual_height / 1000.0

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Detect ALL diagrams, figures, charts, and graphs in this image.\n"
        "For each diagram, return a JSON array:\n"
        '[{"id": "diagram_1", "bbox": {"x": N, "y": N, "w": N, "h": N}, '
        '"desc": "brief description"}]\n'
        "Coordinates should be in your native scale (approximately 1000-unit width).\n"
        "Include ALL visual elements that are not pure text."
    )

    validation_prompt = (
        "Validate diagram detection results against the original image.\n"
        "Check for:\n"
        "1. Missing diagrams (false negatives)\n"
        "2. Non-diagram regions detected (false positives)\n"
        "3. Bounding box accuracy (tight fit, no excessive padding)\n"
        "Score confidence 0-1."
    )

    result: LoopResult = loop.run(
        image_path=image_path,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    # Parse result into BboxResult list with scale correction
    diagrams = []
    raw = result.result
    if isinstance(raw, str):
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                cleaned = "\n".join(lines).strip()
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "diagrams" in parsed:
                parsed = parsed["diagrams"]
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse diagram detection result: {raw[:200]}")
            return []
    elif isinstance(raw, list):
        parsed = raw
    else:
        return []

    for item in parsed:
        bbox = item.get("bbox", {})
        diagrams.append(BboxResult(
            id=item.get("id", f"diagram_{len(diagrams)+1}"),
            x=int(bbox.get("x", 0) * scale_x),  # ISS-4 scale correction
            y=int(bbox.get("y", 0) * scale_y),
            width=int(bbox.get("w", 0) * scale_x),
            height=int(bbox.get("h", 0) * scale_y),
            description=item.get("desc", ""),
            confidence=result.confidence,
        ))

    return diagrams


def crop_diagrams(
    image_path: str,
    bboxes: list[BboxResult],
    output_dir: str | None = None,
    padding: int = 15,
) -> list[str]:
    """Crop diagram regions from image using PIL.

    Args:
        image_path: Path to source image.
        bboxes: List of BboxResult with pixel coordinates.
        output_dir: Directory for cropped PNGs. Defaults to image's directory.
        padding: Extra pixels around each crop.

    Returns:
        List of paths to cropped PNG files.
    """
    img = Image.open(image_path)
    img_width, img_height = img.size

    if output_dir is None:
        output_dir = str(Path(image_path).parent)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    crop_paths = []
    for bbox in bboxes:
        # Apply padding with clamping
        x1 = max(0, bbox.x - padding)
        y1 = max(0, bbox.y - padding)
        x2 = min(img_width, bbox.x + bbox.width + padding)
        y2 = min(img_height, bbox.y + bbox.height + padding)

        cropped = img.crop((x1, y1, x2, y2))
        crop_path = str(Path(output_dir) / f"{bbox.id}.png")
        cropped.save(crop_path)
        crop_paths.append(crop_path)
        logger.info(f"Cropped {bbox.id}: ({x1},{y1})-({x2},{y2}) → {crop_path}")

    return crop_paths


def verify_crops(
    crop_paths: list[str],
    loop_params: dict | None = None,
) -> list[CropVerifyResult]:
    """Verify crop quality via Loop A.

    Args:
        crop_paths: List of cropped PNG file paths.
        loop_params: Optional GeminiQualityLoop parameters.

    Returns:
        List of CropVerifyResult (one per crop).
    """
    params = loop_params or {}
    results = []

    for crop_path in crop_paths:
        loop = GeminiQualityLoop(
            image_model=params.get("image_model", "gemini-3-pro-image-preview"),
            reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
            api_key=params.get("api_key"),
        )

        task_prompt = (
            "Analyze this cropped diagram image.\n"
            "Is this a complete, well-cropped diagram?\n"
            "Return JSON: {\"complete\": true/false, \"issues\": [\"...\"]}"
        )

        validation_prompt = (
            "Validate the crop quality assessment.\n"
            "Check: Is the diagram fully captured? Any truncation? "
            "Any excess non-diagram content included?\n"
            "Score confidence 0-1."
        )

        result: LoopResult = loop.run(
            image_path=crop_path,
            task_prompt=task_prompt,
            validation_prompt=validation_prompt,
            temperature=0.1,
            max_iterations=2,  # Quick verification — fewer iterations
            confidence_threshold=0.8,
        )

        # Parse verification result
        issues = []
        passed = True
        if isinstance(result.result, str):
            try:
                parsed = json.loads(result.result.strip().strip("`"))
                passed = parsed.get("complete", True)
                issues = parsed.get("issues", [])
            except json.JSONDecodeError:
                passed = result.converged

        results.append(CropVerifyResult(
            path=crop_path,
            passed=passed,
            issues=issues,
            confidence=result.confidence,
        ))

    return results
```

**Key Implementation Notes:**
1. **ISS-4 scale correction** — Applied in `detect_diagrams()`. Gemini bbox coords multiplied
   by `actual_width / 1000`.
2. **AD-2 hybrid diagram** — Crop as image, include via `\includegraphics` in LaTeX (Opus handles).
3. **Separate GeminiQualityLoop per crop** in verify_crops — each crop is independent.

---

### 5.7 cow/core/layout_design.py — Loop C: Layout Analysis

**VL-2** (Inferred — based on design §7.2.4 + §4.3)

**Purpose:** Analyze original page layout via Loop A. Returns text report for Opus to
present to user and convert to LaTeX template.

**Estimated Lines:** ~80

```python
# cow/core/layout_design.py
"""Loop C: Layout design analysis via Gemini (L1+L2).

Analyzes original page layout and produces a text report describing:
column configuration, box styles, diagram placement, typography, etc.

Opus (L3) receives this text report and presents it to the user
for approval/modification before generating the LaTeX template.
"""

import logging
from dataclasses import dataclass

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult

logger = logging.getLogger("cow.core.layout_design")


@dataclass
class LayoutDesignReport:
    """Layout analysis report from Loop C.

    Attributes:
        report: Text description of the layout design.
        confidence: Analysis confidence (0.0-1.0).
        iterations: Number of Loop A iterations.
        converged: Whether Loop A converged.
    """
    report: str = ""
    confidence: float = 0.0
    iterations: int = 0
    converged: bool = False


def analyze_layout(
    image_path: str,
    loop_params: dict | None = None,
) -> LayoutDesignReport:
    """Analyze original page layout via Loop A (L1+L2).

    Args:
        image_path: Path to original page image (PNG, 600 DPI).
        loop_params: Optional GeminiQualityLoop parameters.

    Returns:
        LayoutDesignReport with text description of layout.
    """
    params = loop_params or {}

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Analyze the layout and design of this document page.\n"
        "Describe in detail:\n"
        "1. Column configuration (single-column, two-column, minipage)\n"
        "2. Problem/question box styling (framed, tcolorbox, plain, indented)\n"
        "3. Diagram placement strategy (inline, float, margin, right-aligned)\n"
        "4. Font size estimate and line spacing\n"
        "5. Page margins (narrow, normal, wide)\n"
        "6. Header/footer presence and content\n"
        "7. Section/problem numbering style (1., (1), Q1, etc.)\n"
        "8. Any special visual elements (watermarks, logos, borders)\n\n"
        "Return a structured text report, NOT JSON."
    )

    validation_prompt = (
        "Validate this layout analysis against the original image.\n"
        "Check for:\n"
        "1. Accuracy of column count detection\n"
        "2. Correct identification of box/frame styles\n"
        "3. Reasonable font size and spacing estimates\n"
        "4. Completeness — are any major layout features missed?\n"
        "Score confidence 0-1."
    )

    result: LoopResult = loop.run(
        image_path=image_path,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    return LayoutDesignReport(
        report=result.result if isinstance(result.result, str) else str(result.result),
        confidence=result.confidence,
        iterations=result.iterations,
        converged=result.converged,
    )
```

---

### 5.8 cow/core/layout_verify.py — Loop D: Layout Verification

**VL-2** (Inferred — based on design §7.2.5 + §4.4)

**Purpose:** Verify compiled PDF layout via Loop A. Converts PDF→PNG internally, sends to
Gemini for quality check.

**Estimated Lines:** ~80

```python
# cow/core/layout_verify.py
"""Loop D: Layout verification via Gemini (L1+L2).

Converts compiled PDF → PNG, sends to Gemini for visual quality check.
Detects: text/diagram overlap, truncation, alignment issues.

Opus (L3) receives the text report and presents it to the user
for approval, or applies fixes and recompiles.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pdf2image import convert_from_path

from cow.core.gemini_loop import GeminiQualityLoop, LoopResult

logger = logging.getLogger("cow.core.layout_verify")


@dataclass
class LayoutVerifyReport:
    """Layout verification report from Loop D.

    Attributes:
        passed: Whether the layout passed verification.
        issues: List of specific issues found.
        report: Full text report from Gemini.
        confidence: Verification confidence (0.0-1.0).
        page_image: Path to the PNG used for verification.
    """
    passed: bool = False
    issues: list = field(default_factory=list)
    report: str = ""
    confidence: float = 0.0
    page_image: str = ""


def verify_layout(
    pdf_path: str,
    loop_params: dict | None = None,
    page_number: int = 1,
    dpi: int = 300,
) -> LayoutVerifyReport:
    """Verify compiled PDF layout via Loop A (L1+L2).

    Converts the specified page to PNG and sends to Gemini for analysis.

    Args:
        pdf_path: Path to compiled PDF.
        loop_params: Optional GeminiQualityLoop parameters.
        page_number: Page to verify (1-indexed).
        dpi: Resolution for PDF→PNG conversion (300 for verification).

    Returns:
        LayoutVerifyReport with pass/fail, issues, and text report.
    """
    params = loop_params or {}

    # Convert PDF page to PNG
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        return LayoutVerifyReport(
            passed=False,
            issues=[f"PDF not found: {pdf_path}"],
            report=f"PDF not found: {pdf_path}",
        )

    images = convert_from_path(
        str(pdf_file),
        first_page=page_number,
        last_page=page_number,
        dpi=dpi,
    )
    if not images:
        return LayoutVerifyReport(
            passed=False,
            issues=["PDF→PNG conversion produced no images"],
            report="PDF→PNG conversion failed",
        )

    # Save temp PNG for Gemini
    page_png = str(pdf_file.parent / f"_verify_page_{page_number}.png")
    images[0].save(page_png)

    loop = GeminiQualityLoop(
        image_model=params.get("image_model", "gemini-3-pro-image-preview"),
        reasoning_model=params.get("reasoning_model", "gemini-3-pro-preview"),
        api_key=params.get("api_key"),
    )

    task_prompt = (
        "Analyze this compiled PDF page for layout quality.\n"
        "Check for:\n"
        "1. Text/diagram overlap — any elements blocking each other\n"
        "2. Page overflow — content cut off at margins\n"
        "3. Content truncation — missing text at page boundaries\n"
        "4. Alignment issues — misaligned columns, uneven spacing\n"
        "5. Diagram rendering quality — clear, proportional, well-placed\n"
        "6. Overall visual fidelity — clean, professional appearance\n\n"
        "Return a structured text report. Start with PASS or FAIL, "
        "then list specific issues if any."
    )

    validation_prompt = (
        "Validate this layout verification against the PDF page.\n"
        "Check: Are the reported issues real? Are there missed issues?\n"
        "Is the pass/fail determination correct?\n"
        "Score confidence 0-1."
    )

    result: LoopResult = loop.run(
        image_path=page_png,
        task_prompt=task_prompt,
        validation_prompt=validation_prompt,
        temperature=params.get("temperature", 0.1),
        max_iterations=params.get("max_iterations", 3),
        confidence_threshold=params.get("confidence_threshold", 0.9),
    )

    report_text = result.result if isinstance(result.result, str) else str(result.result)
    passed = report_text.strip().upper().startswith("PASS")
    issues = []
    if not passed:
        # Extract issue lines from report
        for line in report_text.split("\n"):
            line = line.strip()
            if line and not line.upper().startswith("FAIL") and not line.upper().startswith("PASS"):
                issues.append(line)

    return LayoutVerifyReport(
        passed=passed,
        issues=issues,
        report=report_text,
        confidence=result.confidence,
        page_image=page_png,
    )
```

**Key Implementation Notes:**
1. **pdf2image dependency** — requires `poppler-utils` system package.
2. **300 DPI for verification** — lower than 600 DPI preprocessing (sufficient for quality check).
3. **Temp PNG cleanup** — `_verify_page_N.png` left in PDF directory. Cleanup is caller's responsibility.

---

### 5.9 cow/core/compile.py — XeLaTeX Compilation

**VL-1** (Verified — adapted from v1.0 compiler.py with simplifications)

**Purpose:** XeLaTeX + kotex compilation. No Mathpix fallback (AD-9).

**Estimated Lines:** ~60

```python
# cow/core/compile.py
"""XeLaTeX compilation with Korean font support (kotex + Noto CJK KR).

Simplified from v1.0 compiler.py:
- Removed Mathpix converter fallback (AD-9 fail-stop)
- Removed async (synchronous subprocess.run)
- Kept multi-pass compilation for cross-references
- Kept auto-fix for common errors (font fallback, missing packages)
"""

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("cow.core.compile")

XELATEX_CMD = "xelatex"
MAX_PASSES = 3
TIMEOUT_SECONDS = 120


@dataclass
class CompileResult:
    """XeLaTeX compilation result.

    Attributes:
        pdf_path: Path to generated PDF (empty on failure).
        success: Whether compilation succeeded.
        error_log: Full compilation log (useful for debugging).
        warnings: List of LaTeX warnings.
    """
    pdf_path: str = ""
    success: bool = False
    error_log: str = ""
    warnings: list = field(default_factory=list)


def compile_latex(
    tex_path: str,
    output_dir: str | None = None,
) -> CompileResult:
    """Compile a .tex file to PDF using XeLaTeX.

    Runs up to 3 passes for cross-reference resolution.
    Attempts auto-fix on first failure (font substitution, missing packages).

    Args:
        tex_path: Path to the .tex file.
        output_dir: Output directory. Defaults to same directory as .tex.

    Returns:
        CompileResult with pdf_path (if success), logs, and warnings.
    """
    tex_file = Path(tex_path)
    if not tex_file.exists():
        return CompileResult(
            error_log=f"File not found: {tex_path}",
            warnings=[f"File not found: {tex_path}"],
        )

    if not shutil.which(XELATEX_CMD):
        return CompileResult(
            error_log="xelatex not found in PATH",
            warnings=["xelatex binary not found — install texlive-xetex"],
        )

    out_dir = Path(output_dir) if output_dir else tex_file.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    full_log_parts = []
    warnings = []

    for pass_num in range(1, MAX_PASSES + 1):
        cmd = [
            XELATEX_CMD,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={out_dir}",
            str(tex_file),
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=str(tex_file.parent),
            )
            log = proc.stdout
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            log = "Compilation timed out"
            returncode = 1

        full_log_parts.append(f"=== Pass {pass_num} ===\n{log}")

        if returncode == 0:
            if "Rerun to get cross-references right" not in log:
                break
        else:
            if pass_num == 1:
                if _auto_fix_errors(log, str(tex_file)):
                    warnings.append("Auto-fix applied, retrying")
                    continue
            break

    full_log = "\n".join(full_log_parts)

    # Extract warnings
    for line in full_log.splitlines():
        if "LaTeX Warning:" in line:
            warnings.append(line.strip())

    pdf_path = out_dir / tex_file.with_suffix(".pdf").name
    if pdf_path.exists():
        return CompileResult(
            pdf_path=str(pdf_path),
            success=True,
            error_log=full_log,
            warnings=warnings,
        )
    else:
        return CompileResult(
            error_log=full_log,
            warnings=warnings + ["Compilation failed — no PDF produced"],
        )


def _auto_fix_errors(log: str, tex_path: str) -> bool:
    """Attempt auto-fix for common compilation errors."""
    tex = Path(tex_path).read_text(encoding="utf-8")
    original = tex

    # Fix: Missing font → fallback to Nanum Myeongjo
    if "not found" in log.lower() and "Noto" in log:
        tex = tex.replace("Noto Serif CJK KR", "Nanum Myeongjo")
        tex = tex.replace("Noto Sans CJK KR", "Nanum Gothic")
        logger.warning("Auto-fix: replaced Noto CJK fonts with Nanum fallback")

    # Fix: Missing pgfplots package
    if "Undefined control sequence" in log and "pgfplotsset" in log:
        if "\\usepackage{pgfplots}" not in tex:
            tex = tex.replace(
                "\\usepackage{tikz}",
                "\\usepackage{tikz}\n\\usepackage{pgfplots}\n\\pgfplotsset{compat=1.18}",
            )
            logger.warning("Auto-fix: added missing pgfplots package")

    if tex != original:
        Path(tex_path).write_text(tex, encoding="utf-8")
        return True
    return False
```

**Key Implementation Notes:**
1. **Synchronous subprocess.run** — not asyncio (v1.0 used asyncio.create_subprocess_exec).
2. **No Mathpix fallback** — per AD-9. Only XeLaTeX compilation.
3. **Auto-fix preserved** — font fallback and missing package detection from v1.0.

---

### 5.10 cow/cli.py — CLI Wrapper

**VL-2** (Inferred — based on design §7.3 + argparse patterns)

**Purpose:** CLI entry point for Opus (Claude Code) to call via Bash tool. Outputs JSON to stdout.

**Estimated Lines:** ~200

```python
# cow/cli.py
"""COW Pipeline v2.0 CLI — Claude Code integration layer.

Opus (Claude Code) calls this via Bash tool:
  python cow/cli.py <command> [options]

All commands output JSON to stdout. Errors go to stderr.
Exit codes: 0 = success, 1 = fail-stop (model unavailable), 2 = runtime error.
"""

import argparse
import json
import sys
import logging
from pathlib import Path

logger = logging.getLogger("cow.cli")


def _output(data: dict, exit_code: int = 0) -> None:
    """Write JSON to stdout and exit."""
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.exit(exit_code)


def _error(message: str, exit_code: int = 2) -> None:
    """Write error to stderr and exit."""
    sys.stderr.write(f"ERROR: {message}\n")
    json.dump({"error": message}, sys.stdout)
    sys.stdout.write("\n")
    sys.exit(exit_code)


def cmd_validate_models(args: argparse.Namespace) -> None:
    """Validate model availability (AD-9 fail-stop check)."""
    from cow.config.models import ModelConfig, ModelUnavailableError

    config = ModelConfig(
        image_model=args.image_model,
        reasoning_model=args.reasoning_model,
    )
    try:
        config.validate()
        _output({"status": "ok", "models": {
            "image": config.image_model,
            "reasoning": config.reasoning_model,
        }})
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)


def cmd_ocr(args: argparse.Namespace) -> None:
    """Run OCR extraction."""
    from cow.config.models import ModelUnavailableError

    try:
        if args.method == "gemini":
            from cow.core.ocr import extract_gemini
            result = extract_gemini(args.image, loop_params={
                "image_model": args.image_model,
                "reasoning_model": args.reasoning_model,
                "temperature": args.temperature,
                "max_iterations": args.max_iterations,
            })
        elif args.method == "mathpix":
            from cow.core.ocr import extract_mathpix
            result = extract_mathpix(args.image)
        else:
            _error(f"Unknown OCR method: {args.method}")
            return

        _output({
            "text": result.text,
            "confidence": result.confidence,
            "method": result.method,
            "iterations": result.iterations,
        })
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_diagram_detect(args: argparse.Namespace) -> None:
    """Detect diagrams in an image."""
    from cow.core.diagram import detect_diagrams
    from cow.config.models import ModelUnavailableError

    try:
        results = detect_diagrams(args.image, loop_params={
            "image_model": args.image_model,
            "reasoning_model": args.reasoning_model,
        })
        _output({"diagrams": [
            {"id": r.id, "bbox": {"x": r.x, "y": r.y, "w": r.width, "h": r.height},
             "desc": r.description, "confidence": r.confidence}
            for r in results
        ]})
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_diagram_crop(args: argparse.Namespace) -> None:
    """Crop diagram regions from an image."""
    from cow.core.diagram import crop_diagrams, BboxResult

    try:
        # Load bboxes from JSON file
        bboxes_data = json.loads(Path(args.bboxes).read_text())
        bboxes = [BboxResult(**b) for b in bboxes_data]
        paths = crop_diagrams(args.image, bboxes, padding=args.padding)
        _output({"crops": paths})
    except Exception as e:
        _error(str(e))


def cmd_diagram_verify(args: argparse.Namespace) -> None:
    """Verify cropped diagram quality."""
    from cow.core.diagram import verify_crops
    from cow.config.models import ModelUnavailableError

    try:
        results = verify_crops(args.crops)
        _output({"results": [
            {"path": r.path, "pass": r.passed, "issues": r.issues,
             "confidence": r.confidence}
            for r in results
        ]})
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_layout_analyze(args: argparse.Namespace) -> None:
    """Analyze page layout."""
    from cow.core.layout_design import analyze_layout
    from cow.config.models import ModelUnavailableError

    try:
        result = analyze_layout(args.image, loop_params={
            "image_model": args.image_model,
            "reasoning_model": args.reasoning_model,
        })
        _output({
            "report": result.report,
            "confidence": result.confidence,
            "iterations": result.iterations,
            "converged": result.converged,
        })
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_layout_verify(args: argparse.Namespace) -> None:
    """Verify compiled PDF layout."""
    from cow.core.layout_verify import verify_layout
    from cow.config.models import ModelUnavailableError

    try:
        result = verify_layout(args.pdf, loop_params={
            "image_model": args.image_model,
            "reasoning_model": args.reasoning_model,
        })
        _output({
            "pass": result.passed,
            "issues": result.issues,
            "report": result.report,
            "confidence": result.confidence,
        })
    except ModelUnavailableError as e:
        _error(f"Model unavailable: {e.model_id}. {e.detail}", exit_code=1)
    except Exception as e:
        _error(str(e))


def cmd_compile(args: argparse.Namespace) -> None:
    """Compile LaTeX to PDF."""
    from cow.core.compile import compile_latex

    result = compile_latex(args.tex, output_dir=args.output_dir)
    _output({
        "pdf_path": result.pdf_path,
        "success": result.success,
        "error_log": result.error_log if not result.success else "",
        "warnings": result.warnings,
    })


def cmd_preprocess(args: argparse.Namespace) -> None:
    """Convert PDF to PNG pages."""
    from pdf2image import convert_from_path

    try:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            _error(f"PDF not found: {args.pdf}")
            return

        images = convert_from_path(str(pdf_path), dpi=args.dpi)
        output_dir = pdf_path.parent
        pages = []
        for i, img in enumerate(images, 1):
            page_path = str(output_dir / f"{pdf_path.stem}_p{i}.png")
            img.save(page_path)
            pages.append({
                "page": i,
                "path": page_path,
                "width": img.width,
                "height": img.height,
            })

        _output({"pages": pages})
    except Exception as e:
        _error(str(e))


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="cow",
        description="COW Pipeline v2.0 — PDF Reconstruction & Editing SDK",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common model arguments
    def add_model_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--image-model", default="gemini-3-pro-image-preview")
        p.add_argument("--reasoning-model", default="gemini-3-pro-preview")

    # validate-models
    p_validate = subparsers.add_parser("validate-models", help="Check model availability")
    add_model_args(p_validate)
    p_validate.set_defaults(func=cmd_validate_models)

    # ocr
    p_ocr = subparsers.add_parser("ocr", help="OCR extraction")
    p_ocr.add_argument("--image", required=True, help="Path to image file")
    p_ocr.add_argument("--method", choices=["gemini", "mathpix"], required=True)
    add_model_args(p_ocr)
    p_ocr.add_argument("--temperature", type=float, default=0.1)
    p_ocr.add_argument("--max-iterations", type=int, default=3)
    p_ocr.set_defaults(func=cmd_ocr)

    # diagram detect
    p_diag = subparsers.add_parser("diagram", help="Diagram operations")
    diag_sub = p_diag.add_subparsers(dest="diagram_cmd", required=True)

    p_detect = diag_sub.add_parser("detect", help="Detect diagrams")
    p_detect.add_argument("--image", required=True)
    add_model_args(p_detect)
    p_detect.set_defaults(func=cmd_diagram_detect)

    p_crop = diag_sub.add_parser("crop", help="Crop diagram regions")
    p_crop.add_argument("--image", required=True)
    p_crop.add_argument("--bboxes", required=True, help="Path to JSON bbox file")
    p_crop.add_argument("--padding", type=int, default=15)
    p_crop.set_defaults(func=cmd_diagram_crop)

    p_verify = diag_sub.add_parser("verify", help="Verify cropped diagrams")
    p_verify.add_argument("--crops", nargs="+", required=True, help="Paths to crop PNGs")
    add_model_args(p_verify)
    p_verify.set_defaults(func=cmd_diagram_verify)

    # layout
    p_layout = subparsers.add_parser("layout", help="Layout operations")
    layout_sub = p_layout.add_subparsers(dest="layout_cmd", required=True)

    p_analyze = layout_sub.add_parser("analyze", help="Analyze page layout")
    p_analyze.add_argument("--image", required=True)
    add_model_args(p_analyze)
    p_analyze.set_defaults(func=cmd_layout_analyze)

    p_lverify = layout_sub.add_parser("verify", help="Verify compiled PDF layout")
    p_lverify.add_argument("--pdf", required=True)
    add_model_args(p_lverify)
    p_lverify.set_defaults(func=cmd_layout_verify)

    # compile
    p_compile = subparsers.add_parser("compile", help="Compile LaTeX to PDF")
    p_compile.add_argument("--tex", required=True, help="Path to .tex file")
    p_compile.add_argument("--output-dir", default=None)
    p_compile.set_defaults(func=cmd_compile)

    # preprocess
    p_preprocess = subparsers.add_parser("preprocess", help="PDF to PNG conversion")
    p_preprocess.add_argument("--pdf", required=True, help="Path to PDF file")
    p_preprocess.add_argument("--dpi", type=int, default=600)
    p_preprocess.set_defaults(func=cmd_preprocess)

    # Parse and execute
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
        stream=sys.stderr,  # Logs to stderr, JSON to stdout
    )
    args.func(args)


if __name__ == "__main__":
    main()
```

**Key Implementation Notes:**
1. **JSON stdout / errors stderr** — clean separation for Opus to parse.
2. **Lazy imports** — each `cmd_*` function imports its module at call time, so
   `python cow/cli.py --help` works without all dependencies installed.
3. **Exit codes** — 0=ok, 1=fail-stop (ModelUnavailableError), 2=runtime error.
4. **argparse subcommands** — matches design §7.3 command list exactly.

---

### 5.11 cow/config/profiles.py — User Presets + Progressive Automation

**VL-2** (Inferred — based on design §7.2.8 + §8)

**Purpose:** Store per-problem-type defaults for progressive automation (Level 1→2→3).

**Estimated Lines:** ~60

```python
# cow/config/profiles.py
"""User presets for progressive automation (AD-13).

Level 1: Full interactive selection (no defaults).
Level 2: Type-based defaults — user approves batch.
Level 3: Auto-apply — user reviews final output only.

Profile data stored as JSON in ~/.cow/profiles.json.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("cow.config.profiles")

DEFAULT_PROFILE_PATH = Path.home() / ".cow" / "profiles.json"


@dataclass
class UserProfile:
    """User profile for progressive automation.

    Attributes:
        path: Path to profile JSON file.
        defaults: Per-problem-type default settings.
        automation_level: Current automation level (1, 2, or 3).
    """
    path: Path = DEFAULT_PROFILE_PATH
    defaults: dict = field(default_factory=dict)
    automation_level: int = 1

    def load(self) -> None:
        """Load profile from disk."""
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.defaults = data.get("defaults", {})
            self.automation_level = data.get("automation_level", 1)

    def save(self) -> None:
        """Save profile to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "defaults": self.defaults,
            "automation_level": self.automation_level,
        }
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_defaults(self, problem_type: str) -> dict:
        """Return stored defaults for a problem type.

        Args:
            problem_type: e.g., "text_only", "with_diagram", "multi_column".

        Returns:
            Dict of default settings, or empty dict if none stored.
        """
        return self.defaults.get(problem_type, {})

    def save_selection(self, problem_type: str, selection: dict) -> None:
        """Record user selection for future default inference.

        Args:
            problem_type: Problem category.
            selection: User's chosen settings (ocr_method, model params, etc.).
        """
        self.defaults[problem_type] = selection
        self.save()
        logger.info(f"Saved defaults for '{problem_type}': {selection}")
```

---

### 5.12 cow/requirements.txt

**VL-1** (Verified — matches design §12 exactly)

```
# COW Pipeline v2.0 Dependencies
google-genai>=1.0.0      # Gemini API SDK (L1+L2)
Pillow>=10.0.0           # Image cropping (diagram.py)
requests>=2.31.0         # Mathpix API calls (ocr.py)
pdf2image>=1.17.0        # PDF → PNG conversion (layout_verify.py, cli.py)
```

**System dependencies** (documented, not in requirements.txt):
- `poppler-utils` — required by pdf2image
- `texlive-xetex` — required for xelatex
- `texlive-lang-korean` — required for kotex
- `fonts-noto-cjk` — Noto Sans/Serif CJK KR fonts

---

## 6. Cross-File Interface Contracts

### 6.0 FROZEN CONTRACTS

The following interfaces are immutable once Implementer 1 delivers. Any deviation
requires Lead approval before downstream implementers proceed.

```
FROZEN: LoopResult dataclass fields
  - result: str | dict       (converged output)
  - iterations: int          (loop count)
  - confidence: float        (0.0-1.0)
  - l1_history: list         (L1 outputs per iteration)
  - l2_feedback: list        (L2 feedback per iteration)
  - converged: bool          (reached threshold?)

FROZEN: GeminiQualityLoop.run() signature
  run(image_path: str, task_prompt: str, validation_prompt: str,
      temperature: float = 0.1, max_iterations: int = 3,
      confidence_threshold: float = 0.9) → LoopResult

FROZEN: ModelUnavailableError(model_id: str, detail: str = "")
  - Defined in cow.config.models
  - Imported by cow.core.gemini_loop
```

### 6.1 GeminiQualityLoop Interface (Foundation)

```
Usage pattern (all consumers):
  from cow.core.gemini_loop import GeminiQualityLoop, LoopResult
  from cow.config.models import ModelUnavailableError

  loop = GeminiQualityLoop(
      image_model="gemini-3-pro-image-preview",
      reasoning_model="gemini-3-pro-preview",
      api_key=os.environ.get("GEMINI_API_KEY"),
  )
  result: LoopResult = loop.run(
      image_path="path/to/image.png",
      task_prompt="...",
      validation_prompt="...",
  )
  # result.result: str (text) or dict (parsed JSON)
  # result.confidence: float 0.0-1.0
  # result.converged: bool

Consumers: ocr.py, diagram.py, layout_design.py, layout_verify.py
```

### 6.2 Data Model Contracts

| Model | Module | Fields |
|-------|--------|--------|
| `LoopResult` | gemini_loop.py | result, iterations, confidence, l1_history, l2_feedback, converged |
| `OcrResult` | ocr.py | text, confidence, method, iterations, raw_response |
| `BboxResult` | diagram.py | id, x, y, width, height, description, confidence |
| `CropVerifyResult` | diagram.py | path, passed, issues, confidence |
| `LayoutDesignReport` | layout_design.py | report, confidence, iterations, converged |
| `LayoutVerifyReport` | layout_verify.py | passed, issues, report, confidence, page_image |
| `CompileResult` | compile.py | pdf_path, success, error_log, warnings |
| `ModelConfig` | models.py | image_model, reasoning_model, api_key |
| `ModelUnavailableError` | models.py | model_id, detail |
| `UserProfile` | profiles.py | path, defaults, automation_level |

### 6.3 CLI JSON Output Contracts

All CLI commands output to stdout in this format:
```json
// Success (exit 0):
{"field1": "value", "field2": 123}

// Fail-stop error (exit 1):
{"error": "Model unavailable: gemini-3-pro-image-preview. 404 Not Found"}

// Runtime error (exit 2):
{"error": "Image not found: /path/to/image.png"}
```

### 6.4 Error Propagation Chain

```
ModelUnavailableError (cow.config.models)
  Triggers: 404, quota exceeded, deprecated, permission denied, resource exhausted
  ↑ raised by: ModelConfig.validate(), GeminiQualityLoop.__init__(), GeminiQualityLoop.run()
  ↑ caught by: cow/cli.py cmd_* functions → exit code 1
  ↑ seen by: Opus (Claude Code) → reports to user with model ID + details
  Note: Mid-loop failures (iteration 2 of 3) propagate immediately — partial results lost.

FileNotFoundError (Python builtin)
  ↑ raised by: GeminiQualityLoop.run(), extract_mathpix(), compile_latex()
  ↑ caught by: cow/cli.py cmd_* functions → exit code 2

requests.HTTPError (requests library)
  ↑ raised by: extract_mathpix() on Mathpix API error
  ↑ caught by: cow/cli.py cmd_ocr() → exit code 2
```

### 6.5 API Key Loading Chain

```
Priority: explicit parameter → os.environ → error

GEMINI_API_KEY:
  GeminiQualityLoop(api_key=X)  →  os.environ["GEMINI_API_KEY"]  →  ModelUnavailableError
  ModelConfig(api_key=X)        →  os.environ["GEMINI_API_KEY"]  →  ModelUnavailableError

MATHPIX_APP_ID / MATHPIX_APP_KEY:
  extract_mathpix(app_id=X)     →  os.environ["MATHPIX_APP_ID"]  →  ValueError
```

---

## 7. Validation Checklist

### V1: Import Validation
```bash
cd /home/palantir
python -c "from cow.config.models import ModelConfig, ModelUnavailableError; print('config OK')"
python -c "from cow.core.gemini_loop import GeminiQualityLoop, LoopResult; print('loop OK')"
python -c "from cow.core.ocr import extract_gemini, extract_mathpix, OcrResult; print('ocr OK')"
python -c "from cow.core.diagram import detect_diagrams, crop_diagrams, verify_crops; print('diagram OK')"
python -c "from cow.core.layout_design import analyze_layout; print('layout_design OK')"
python -c "from cow.core.layout_verify import verify_layout; print('layout_verify OK')"
python -c "from cow.core.compile import compile_latex; print('compile OK')"
python -c "from cow.config.profiles import UserProfile; print('profiles OK')"
```

### V2: CLI --help
```bash
python cow/cli.py --help              # Shows all subcommands
python cow/cli.py ocr --help          # Shows OCR options
python cow/cli.py diagram detect --help
python cow/cli.py layout analyze --help
python cow/cli.py compile --help
python cow/cli.py preprocess --help
python cow/cli.py validate-models --help
```

### V3: Unit Tests (per module)
Tester creates pytest files. Key tests:
- `test_gemini_loop.py`: Mock Gemini API, verify convergence logic
- `test_ocr.py`: Mock both Gemini and Mathpix APIs
- `test_diagram.py`: Mock Gemini + real PIL crop test
- `test_compile.py`: Compile a minimal .tex file
- `test_models.py`: Verify ModelUnavailableError raised on bad model ID

### V4: CLI Smoke Test
```bash
python cow/cli.py preprocess --pdf cow/sample2.pdf --dpi 600
# Expected: JSON with page list, PNG files created
```

### V5: Integration Test (mock pipeline)
```bash
# Step 0: preprocess
python cow/cli.py preprocess --pdf cow/sample2.pdf

# Step 1: OCR (requires GEMINI_API_KEY)
python cow/cli.py ocr --image cow/sample2_p1.png --method gemini

# Step 2: diagram detect
python cow/cli.py diagram detect --image cow/sample2_p1.png

# Step 3: layout analyze
python cow/cli.py layout analyze --image cow/sample2_p1.png

# Step 4-5: Opus handles (logical verification + LaTeX composition)

# Step 6: compile
python cow/cli.py compile --tex cow/output.tex

# Step 7: layout verify
python cow/cli.py layout verify --pdf cow/output.pdf
```

### V6: Code Plausibility (Architect Assessment)

| ID | Module | Concern | Risk | Evidence | Mitigation |
|----|--------|---------|------|----------|------------|
| VP-1 | gemini_loop.py | `genai.Client(api_key=...)` constructor | LOW | v1.0 gemini.py:118 uses exactly this | Proven |
| VP-2 | ~~ELIMINATED~~ | PIL Image in contents | — | v1.0 gemini.py:142 passes PIL Image directly | N/A |
| VP-3 | gemini_loop.py | Sync `client.models.generate_content()` | LOW | v1.0 uses async counterpart; sync is standard | asyncio.run() fallback if needed |
| VP-4 | gemini_loop.py | L2 JSON parsing from Gemini | LOW | — | Fallback parser included |
| VP-5 | models.py | `client.models.get(model=id)` API exists | MEDIUM | No v1.0 evidence | May need list+filter alternative |
| VP-6 | models.py | Model ID format "gemini-3-pro-image-preview" | HIGH | Model may not exist yet | AD-9 fail-stop handles gracefully |
| VP-7 | layout_verify.py | pdf2image `convert_from_path` requires poppler | LOW | Used in v1.0 | System dep documented |

### V7: AD-9 Fail-Stop Validation
```bash
# Set invalid model ID to trigger fail-stop
python cow/cli.py validate-models --image-model "nonexistent-model"
# Expected: exit code 1, JSON error with model ID

python cow/cli.py ocr --image cow/sample2_p1.png --method gemini --image-model "nonexistent"
# Expected: exit code 1, JSON error
```

### V8: ISS-1~6 Mitigation Verification

| ISS | Check |
|-----|-------|
| ISS-1 | Review ocr.py Mathpix payload — no `include_word_data` present |
| ISS-2 | Review ocr.py Gemini validation_prompt — mentions hallucination check |
| ISS-3 | Review cli.py and gemini_loop.py — timeout handling present |
| ISS-4 | Review diagram.py `detect_diagrams()` — scale correction applied |
| ISS-5 | Verify no MCP vision tool usage — direct Gemini API only |
| ISS-6 | Review cli.py `validate-models` — checks model availability |

---

## 8. Risk Registry

| ID | Risk | Impact | Prob. | Mitigation |
|----|------|--------|-------|------------|
| R-1 | `gemini-3-pro-image-preview` model unavailable | Pipeline cannot run (AD-9) | MEDIUM | validate-models check at start; user notified with model ID for manual resolution |
| R-2 | google-genai SDK API surface changes | Code breaks on SDK update | LOW | Pin version in requirements.txt; VP-1/3/5 verified on first run |
| R-3 | pdf2image/poppler interaction on WSL2 | Preprocessing fails | LOW | poppler-utils already installed (used in v1.0); fallback: manual PNG conversion |
| R-4 | XeLaTeX + kotex compilation with Korean | Compile errors with CJK fonts | LOW | Auto-fix font fallback in compile.py; Nanum fonts as backup |
| R-5 | Gemini bbox scale correction accuracy (ISS-4) | Diagram crops misaligned | MEDIUM | L2 cross-validation in detect_diagrams; verify_crops double-checks |
| R-6 | google-genai sync API doesn't exist (VP-3) | Must use async wrapper | MEDIUM | Add `asyncio.run()` in CLI layer if needed; single-line change per cmd_* |
| R-7 | Legacy deletion impacts preserved files | Accidentally deletes test inputs | LOW | Explicit PRESERVE list in Task E; AC-4 verification |
| R-8 | MCP server removal from .claude.json | Breaks other tools | LOW | Only cow-* entries removed; other MCP servers untouched |

---

## 9. Commit Strategy

### Single Commit After All Tasks Complete

```bash
# Stage new files
git add cow/core/__init__.py
git add cow/core/gemini_loop.py
git add cow/core/ocr.py
git add cow/core/diagram.py
git add cow/core/layout_design.py
git add cow/core/layout_verify.py
git add cow/core/compile.py
git add cow/config/__init__.py
git add cow/config/models.py
git add cow/config/profiles.py
git add cow/cli.py
git add cow/requirements.txt

# Stage deletions
git rm -r cow/cow-cli/
git rm -r cow/cow-mcp/
git rm cow/PIPELINE-REFERENCE.md  # if tracked
# Note: *.png and *.pdf test artifacts may be untracked — verify with git status

# Stage .claude.json MCP cleanup (integrator)
git add .claude.json

# Commit
git commit -m "feat(cow): v2.0 rebuild — Python SDK with Triple-Layer Verification

Replace 6 MCP servers + CLI pipeline with Python SDK + CLI wrapper.
- GeminiQualityLoop (Loop A): L1+L2 dual-model convergence
- OCR: Gemini + Mathpix extraction
- Diagram: detect + crop + verify via Loop A
- Layout: design analysis (Loop C) + verification (Loop D)
- Compile: XeLaTeX + kotex (no Mathpix fallback, AD-9)
- CLI: JSON stdout, exit codes 0/1/2
- Config: fail-stop model validation (AD-9), user profiles (AD-13)

Deletes cow-cli/ (~60 files), cow-mcp/ (33 files), 6 MCP registrations.
Architecture: AD-1 through AD-20 implemented.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 10. Phase 6 Entry Conditions

Before spawning implementers, Lead must verify:

### Environment
- [ ] `python --version` returns Python 3.10+ (dataclass field defaults, `str | None` syntax)
- [ ] `pip install google-genai Pillow requests pdf2image` succeeds (or venv exists)
- [ ] `GEMINI_API_KEY` is set in environment (extract from .claude.json cow-vision env)
- [ ] `MATHPIX_APP_ID` and `MATHPIX_APP_KEY` are set (extract from .claude.json cow-ocr env)
- [ ] `poppler-utils` installed (`which pdftoppm` returns a path)
- [ ] `xelatex` installed (`which xelatex` returns a path)

### API Keys (from .claude.json)
The following keys are currently in MCP server env vars and must be available as
shell environment variables for the new SDK:
```
GEMINI_API_KEY=<redacted — see .claude.json cow-vision env>
MATHPIX_APP_ID=<redacted — see .claude.json cow-ocr env>
MATHPIX_APP_KEY=<redacted — see .claude.json cow-ocr env>
```
Lead should verify these are in the shell environment before Phase 6 begins.

### Directory Structure
- [ ] `cow/core/` directory exists (create if not: `mkdir -p cow/core cow/config`)
- [ ] No naming conflicts with existing files

### Design File
- [ ] `docs/plans/2026-02-09-cow-v2-design.md` exists and is readable
- [ ] `docs/plans/2026-02-09-cow-v2-implementation.md` exists (this file)

### Legacy Files (pre-deletion inventory)
- [ ] `cow/cow-cli/` exists (will be deleted in Task E)
- [ ] `cow/cow-mcp/` exists (will be deleted in Task E)
- [ ] `cow/sample.pdf` and `cow/sample2.pdf` exist (PRESERVE)
- [ ] `cow/docs/` and `cow/images/` exist (PRESERVE)

### Phase 5 Gate
- [ ] Phase 5 (Plan Validation) has been completed (or skipped per Lead judgment)

---

## Appendix A: v1.0 Adaptation Scope

| v2.0 Module | v1.0 Source | Adaptation | Scope |
|-------------|------------|------------|-------|
| gemini_loop.py | cow-mcp/vision/gemini.py | New dual-model L1+L2 loop, sync API | HIGH |
| ocr.py (gemini) | — | New (Loop A based) | NEW |
| ocr.py (mathpix) | cow-mcp/ocr/client.py | Simplify: sync requests, no cache/retry | MEDIUM |
| diagram.py | cow-mcp/vision/gemini.py | New Loop A based + ISS-4 scale correction | HIGH |
| layout_design.py | cow-mcp/vision/gemini.py | New Loop A based | HIGH |
| layout_verify.py | — | New (pdf2image + Loop A) | NEW |
| compile.py | cow-mcp/export/compiler.py | Simplify: sync, remove Mathpix fallback | LOW |
| config/models.py | — | New (AD-9 fail-stop validation) | NEW |
| config/profiles.py | — | New (AD-13 progressive automation) | NEW |
| cli.py | — | New (argparse, JSON output) | NEW |

## Appendix B: Phase 5 Targets (for Devils-Advocate)

| # | Assumption | Evidence | Risk if Wrong |
|---|-----------|----------|---------------|
| A-1 | google-genai SDK has sync `models.generate_content()` | VP-3 | Must wrap with asyncio.run(), adds complexity |
| A-2 | `client.files.upload(file=Path)` accepts pathlib.Path | VP-2 | Needs str() cast, trivial fix |
| A-3 | `client.models.get(model=id)` verifies model existence | VP-5 | Need alternative validation method |
| A-4 | Model ID "gemini-3-pro-image-preview" is correct format | VP-6 | Pipeline cannot start (AD-9 catches this) |
| A-5 | 4 implementers with this dependency graph is efficient | §3 dependency graph | Could use 3 (merge Imp-2+3) or 2 (merge Imp-1+2) |
| A-6 | Synchronous code throughout is correct for CLI usage | AD-14 | If Gemini calls are slow, may need progress reporting |
| A-7 | Loop A L2 JSON parsing is reliable enough | VP-4 | May need structured output config for Gemini |
