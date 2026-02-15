---
name: render-evaluate
description: |
  [D1·Shared·RenderEval] Dual-mode merge point: evaluates rendering fidelity across 6 execution paths (3 render states x 2 modes).

  WHEN: After jsonl-validate AND latex-parse complete. Merge point in D1 shared validation core.
  DOMAIN: drill/production shared (skill 4 of 5). Merge: jsonl-validate + latex-parse -> render-evaluate -> mode-specific terminals.
  INPUT_FROM: IC-06 golden_answer (challenge-generate, drill only), IC-07 validation_result (jsonl-validate), IC-08 parse_result (latex-parse).
  OUTPUT_TO: Drill: IC-09 rendering_diff (golden-correct) + IC-10 trap_results (progress-track). Production: IC-12 qc_rendering (qc-report).

  METHODOLOGY: (1) Mode select + merge IC-07+IC-08, (2) Render status (CRASH/PARTIAL/FULL), (3) Element compare (drill: vs IC-06, prod: vs source), (4) Score (drill: N/M + traps, prod: fidelity 0-1), (5) Route per mode.
  OUTPUT_FORMAT: L1 YAML dual-template (drill N/M+traps OR prod fidelity+errors), L2 visual rendering simulation.
user-invocable: false
disable-model-invocation: false
---

# Render Evaluate -- Dual-Mode Merge Point

## Execution Model
- **All tiers**: Lead-direct. Rendering simulation is descriptive analysis, not code execution.
- **Dual-mode**: Operates in drill mode (vs golden answer) or production mode (vs source image/document).
- Merges outputs from two parallel upstream skills (jsonl-validate + latex-parse) plus mode-specific reference data.
- This is the "compiler output" phase -- shows what the submission actually produces, then scores it.

### 6-Path Execution Matrix

| Render Status | Drill Mode | Production Mode |
|--------------|------------|-----------------|
| CRASH | Educational: explain JSON failure, describe what WOULD render if fixed (REQ-RE-04 secondary eval) | Reject + attempt auto-fix suggestion, flag for HITL review |
| PARTIAL | N/M element score, highlight failing elements, map to trap pass/fail | Fidelity score (0.0-1.0), error taxonomy with auto-fix suggestions |
| FULL | Full score, all trap results mapped, confirm correct rendering | Full fidelity approval, ready for delivery |

## Decision Points

### Mode Selection
Determined from upstream `mode` field (present in IC-07 and IC-08):
- `mode: "drill"` -- Compare against golden answer (IC-06). Output to golden-correct (IC-09) + progress-track (IC-10).
- `mode: "production"` -- Compare against source image/document. Output to qc-report (IC-12).
- If IC-07.mode and IC-08.mode disagree: treat as mode-mismatch error (see Failure Handling).

### Render Status Determination
Derived from upstream results, NOT independently assessed:
```
IF IC-07.json_parseable == false:
  -> CRASH: JSON parse failed, nothing renders
  -> Score: 0/N elements (drill) or fidelity: 0.0 (production)
  -> Trigger secondary evaluation (REQ-RE-04): simulate what WOULD render if JSON were fixed

ELIF IC-07.json_parseable == true AND IC-08.summary.status == "FAIL":
  -> PARTIAL: JSON OK but LaTeX has FAIL-severity findings
  -> Score partial elements, flag failing ones

ELIF IC-07.json_parseable == true AND IC-08.summary.status in ["PASS", "WARN"]:
  -> FULL: Everything renders (WARN = cosmetic issues only)
  -> Full element comparison
```

### HITL Threshold (Production Mode Only)
- `fidelity_score < 0.85` -- flag `hitl_required: true`, priority based on distance from threshold
- Any FATAL-severity error in error_taxonomy -- flag `hitl_required: true` regardless of score
- Not applicable in drill mode (drill is a learning exercise, not a quality gate)

### Secondary Evaluation Trigger (REQ-RE-04)
When render_status == CRASH:
- Use IC-07.partial_recovery.recovered_text (if available) or IC-07.raw_input with manual fix simulation
- Describe what WOULD render if the JSON parse error were corrected
- Helps drill trainees understand the gap between "broken JSON" and "correct rendering"
- In production: informs auto-fix suggestion confidence

### OCR Artifact Assessment (REQ-RE-05)
When IC-08 segments contain findings with `category: "text_mode"` or `category: "semantics"`:
- Check if the finding correlates with known OCR artifacts (misread characters, encoding issues)
- Flag artifacts that affect visual output vs those that are cosmetic
- In production mode: OCR artifacts feed into source_comparison discrepancies

## Methodology

### 1. Mode Selection + Upstream Merge
Combine IC-07 (validation_result) and IC-08 (parse_result) into unified analysis:

```yaml
merged:
  challenge_id: string       # From IC-07 (primary) or IC-08 (fallback)
  mode: "drill"|"production" # Verified consistent across inputs
  json_parseable: boolean    # From IC-07
  overall_severity: enum     # Worst of IC-07.overall_severity and IC-08.summary.worst_severity
  escape_issues: []          # From IC-07.escape_verdicts (FAIL instances only)
  syntax_issues: []          # From IC-08.segments[].findings (FAIL/WARN instances)
  total_issues: int          # Combined count
  tentative: boolean         # From IC-08.tentative (if true, LaTeX findings are best-effort)
```

**Mode-specific reference loading**:
- Drill: Load IC-06 (golden_answer) -- element_list, trap_annotations, rendered_description
- Production: Load source image/document reference for structural comparison

**Merge conflict detection**: If IC-07 says PASS but IC-08 found issues suggesting escape problems (cross-layer), flag as cross_layer_issue and explain both interpretations.

### 2. Render Status Determination
Apply the decision tree from Decision Points above. Record:

```yaml
render_status: CRASH|PARTIAL|FULL
crash_reason: string|null      # Only if CRASH
partial_elements: int|null     # Count of renderable elements if PARTIAL
secondary_eval: boolean        # True if CRASH triggers "what would render" simulation
```

**3-Stage Report (REQ-RE-07)**:
- CRASH: Failure point identification + recovery suggestion + secondary eval
- PARTIAL: Renderable elements described + failing elements flagged + progressive scoring
- FULL: Complete rendering description + full scoring

### 3. Element-Level Comparison
**Drill mode** (vs golden answer IC-06):
For each element in IC-06.element_list:
- Describe what the trainee's submission actually renders for this element
- Compare against IC-06 element description
- Classify: PASS (matches), FAIL (mismatch, critical element), WARN (mismatch, non-critical)
- Map to trap_annotations where applicable

**Production mode** (vs source image/document):
For each structural element detected in submission:
- Describe what renders
- Compare against source document structure
- Classify with fidelity sub-scores (structural, textual, formatting, completeness)
- Check for OCR artifacts that affect rendering (REQ-RE-05)

**Visual description style**: Describe rendering as if narrating to a blind person. Use visual language only -- no LaTeX code in descriptions.
- "The fraction appears with a horizontal line, numerator x-squared above, denominator 2x below"
- "The curly brace stretches from the first case to the last, spanning all three lines"

### 4. Score Calculation
**Drill mode** -- Element score (REQ-RE-03):
```yaml
score:
  total: "N/M"              # Elements matched / total elements from IC-06
  total_numeric: float       # 0.0-1.0
  by_category:
    structure: "N/M"
    escaping: "N/M"
    formatting: "N/M"
    semantics: "N/M"
trap_results:                # Per-trap pass/fail mapped from element verdicts
  TRAP_ID: PASS|FAIL         # References IC-06.trap_annotations[].trap_id
```

**Production mode** -- Fidelity score (REQ-RE-06):
```yaml
fidelity_score: float        # 0.0-1.0, weighted average of breakdown
fidelity_breakdown:
  structural: float          # 0.0-1.0, math structure accuracy
  textual: float             # 0.0-1.0, text content accuracy
  formatting: float          # 0.0-1.0, spacing/sizing/alignment
  completeness: float        # 0.0-1.0, no missing elements
error_taxonomy: []           # Per-error with auto_fixable flag and confidence
```

### 5. Output Routing
**Drill mode** -- Produce two outputs:
1. IC-09 rendering_diff -> golden-correct: render_status, score, element_verdicts, trap_results, crash_report (if CRASH)
2. IC-10 trap_results -> progress-track: per-trap pass/fail, score, challenge_metadata, category_breakdown

**Production mode** -- Produce one output:
1. IC-12 qc_rendering -> qc-report: render_status, fidelity_score, fidelity_breakdown, element_verdicts, error_taxonomy, source_comparison, hitl_required

## Failure Handling

### Upstream Merge Conflict
- **Cause**: IC-07 and IC-08 disagree on status (e.g., IC-07 PASS but IC-08 found issues suggesting escape problems)
- **Action**: Flag as cross_layer_issue. Use IC-07 as primary for JSON status, IC-08 as primary for LaTeX status. Explain both interpretations in L2.
- **Route**: Normal output with cross_layer_issues[] populated

### Golden Answer Invalid (Drill Mode)
- **Cause**: IC-06 golden_answer fails internal consistency (jsonl_string does not parse, element_list empty)
- **Action**: ABORT evaluation. Report broken golden answer upstream to challenge-generate.
- **Route**: No IC-09/IC-10 output. Error signal to Lead.

### Fidelity Below Threshold (Production Mode)
- **Cause**: fidelity_score < 0.85
- **Action**: Set hitl_required: true, calculate hitl_priority based on score (< 0.5 = urgent, 0.5-0.7 = normal, 0.7-0.85 = low)
- **Route**: IC-12 output with hitl flags set. qc-report handles escalation.

### Mode Mismatch in Chain
- **Cause**: IC-07.mode != IC-08.mode, or mode field missing
- **Action**: Use IC-07.mode as authoritative (jsonl-validate is earlier in chain). Log mismatch. If both missing, check IC-06 presence: if IC-06 exists, assume drill; otherwise assume production.
- **Route**: Normal output with mode_mismatch warning in L2

### Missing Upstream Input
- **Cause**: IC-07 or IC-08 entirely absent
- **Action**: If IC-07 missing: ABORT (cannot determine JSON parseability). If IC-08 missing: proceed with jsonl-validate only, mark all LaTeX verdicts as "unavailable", set confidence lower.
- **Route**: Degraded output with missing_input annotation

## Anti-Patterns

### DO NOT: Compare Against Golden Answer in Production Mode
Production mode compares against the source image/document, not a golden answer. IC-06 is drill-only. Using golden answer in production conflates learning assessment with quality control.

### DO NOT: Skip CRASH Handling
When json_parseable == false, the score is 0 regardless of LaTeX quality. Always produce a crash_report with failure_point and recovery suggestion. Always run secondary evaluation to show what WOULD render.

### DO NOT: Route Drill Output to qc-report
Drill output goes to IC-09 (golden-correct) + IC-10 (progress-track). Production output goes to IC-12 (qc-report). Cross-routing breaks downstream assumptions about data schema and scoring semantics.

### DO NOT: Calculate Fidelity Score in Drill Mode
Drill mode uses N/M element scoring + trap pass/fail mapping. Fidelity score (0.0-1.0 with structural/textual/formatting/completeness breakdown) is production-only. Mixing metrics confuses downstream consumers.

### DO NOT: Show Golden Answer in Rendering Description
This skill describes what the submission actually produces. The correction comes from golden-correct. Separation of concerns: render-evaluate = "what you see", golden-correct = "what you should see".

### DO NOT: Award Partial Credit for CRASH
If JSON does not parse, the score is 0/N. The secondary evaluation describes what WOULD render but does not contribute to the score. This teaches that JSONL validity is a prerequisite.

## Transitions

### Receives From
| Source Skill | IC | Data Expected | Key Fields |
|-------------|-----|---------------|------------|
| challenge-generate | IC-06 | Golden answer (drill only) | element_list[], trap_annotations[], rendered_description, visibility: hidden |
| jsonl-validate | IC-07 | Validation result | json_parseable, parse_error (if CRASH), extracted_text, escape_verdicts.R1-R5, overall_severity, partial_recovery |
| latex-parse | IC-08 | Parse result | tentative, segments[].findings[], summary.status, summary.worst_severity, confidence |

### Sends To
| Target Skill | IC | Data Produced | Trigger Condition |
|-------------|-----|---------------|-------------------|
| golden-correct | IC-09 | rendering_diff: render_status, score, element_verdicts, trap_results, crash_report | Drill mode (always) |
| progress-track | IC-10 | trap_results: per-trap pass/fail, score, render_status, challenge_metadata, category_breakdown | Drill mode (always) |
| qc-report | IC-12 | qc_rendering: render_status, fidelity_score, fidelity_breakdown, element_verdicts, error_taxonomy, hitl_required | Production mode (always) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Golden answer invalid | challenge-generate (error) | Broken IC-06 details |
| IC-07 missing | ABORT | Dependency error signal |
| IC-08 missing | Continue (degraded) | Partial evaluation, LaTeX verdicts unavailable |
| Mode mismatch | Continue (warning) | mode_mismatch flag in L2 |

## Quality Gate
- Render status consistent with upstream (CRASH iff json_parseable==false, PARTIAL iff LaTeX FAIL, FULL otherwise)
- Every renderable segment has a visual description (no LaTeX code in descriptions)
- Element-by-element comparison completed (drill: vs IC-06 elements, production: vs source)
- Score quantified: drill N/M format, production 0.0-1.0 fidelity
- Trap results mapped to IC-06 trap_annotations (drill mode)
- CRASH produces crash_report + secondary evaluation
- HITL flag set when fidelity_score < 0.85 (production mode)
- Output routed to correct downstream: drill -> IC-09+IC-10, production -> IC-12
- All 7 REQ-RE requirements addressed

## Output

### L1 -- Drill Mode
```yaml
domain: drill
skill: render-evaluate
mode: drill
status: PASS|PARTIAL|CRASH
render_status: FULL|PARTIAL|CRASH
score_total: "7/10"
score_numeric: 0.7
score_by_category:
  structure: "3/3"
  escaping: "2/2"
  formatting: "1/3"
  semantics: "1/2"
trap_results:
  ESCAPE_backslash: PASS
  TEXT_spacing: FAIL
  SIZING_left_right: FAIL
crash: false
secondary_eval: false
```

### L1 -- Production Mode
```yaml
domain: production
skill: render-evaluate
mode: production
status: PASS|PARTIAL|CRASH
render_status: FULL|PARTIAL|CRASH
fidelity_score: 0.85
fidelity_breakdown:
  structural: 0.95
  textual: 0.90
  formatting: 0.75
  completeness: 0.80
error_count: 1
auto_fixable_count: 1
hitl_required: false
confidence: 0.88
```

### L2
- Upstream merge summary (IC-07 + IC-08 combined status)
- Rendering simulation narrative (visual descriptions per segment)
- Element-by-element comparison table (drill: vs golden, production: vs source)
- Crash simulation + secondary evaluation (if CRASH)
- Score breakdown with per-element verdicts
- Per-trap verdict summary (drill) or error taxonomy with auto-fix suggestions (production)
- Cross-layer issues (if upstream merge conflict detected)
- HITL recommendation with priority (production, if applicable)
