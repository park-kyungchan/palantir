---
name: golden-correct
description: |
  Generates IC-11 correction_report with 7-category taxonomy, 3-stage verification badge, and per-correction confidence scoring. Terminal Pipeline A drill skill.

  WHEN: After render-evaluate completes (IC-09 rendering_diff available). Pipeline A only.
  CONSUMES: IC-09 rendering_diff (render-evaluate), IC-06 golden_answer (challenge-generate), jsonl-validate (JSONL errors), latex-parse (LaTeX errors).
  PRODUCES: IC-11 correction_report (corrections[] FATAL-first, verification badge, golden_jsonl, summary) → progress-track.
user-invocable: false
disable-model-invocation: false
---

# Drill -- Golden Correct (Pipeline A Terminal)

## Execution Model
- **All levels**: Lead-direct. Correction generation is deterministic given upstream analysis.
- **Pipeline A ONLY**: Drill mode exclusively. Production QC uses a separate pipeline.
- This is the "teaching moment" -- every correction must be educational, not just mechanical.
- Terminal skill: IC-11 correction_report feeds progress-track for learning analytics.

## Decision Points

### Correction Presentation Strategy

- **CRASH** (IC-09.render_status == CRASH): Minimal correction -- fix JSON structure only (COR-001 = JSON fix), then full golden answer. All FATAL. Lesson: "JSON validity is prerequisite."
- **Low score** (total_numeric < 0.5): Corrections grouped by severity (FATAL -> INFO), highlight top 3 most impactful, full golden at end.
- **Passing** (total_numeric >= 0.5): Segment-by-segment diff, each correction as micro-lesson, golden at end as confirmation.

### Diff Alignment Strategy

- **Structurally similar**: Character-level diff with char_start/char_end positions in JSONL string.
- **Restructured differently**: Segment-level diff matching by mathematical content via IC-09.element_verdicts.
- **Fundamentally different**: Side-by-side comparison; check alternative_valid flag.

### Alternative Valid Solutions

If trainee approach differs but produces identical rendering: set `alternative_valid: true`, show both approaches with style preference, still generate corrections for preferred form. If different rendering: set `alternative_valid: false`, explain why golden is correct via visual_impact.

### Backslash Depth Tracking (REQ-GC-03)

Every ESCAPE-category correction includes depth annotation: Depth 0 = LaTeX source (1 backslash per command: `\frac`), Depth 1 = string level (2 backslashes: `\\frac`), Depth 2 = JSONL level (2 backslashes, JSON parser reduces `\\\\` -> `\\`), Depth 4 = JSONL-in-JSON (4 backslashes: `\\\\frac`). Corrections report which depth the error occurs at and correct form at that depth.

### Confidence Scoring (REQ-GC-07)

- **>= 0.95**: Exact match with IC-06.trap_annotations[]. trap_id mapped, correct_form confirmed, scoring_weight applied. hitl_required: false.
- **0.70-0.94**: Pattern match without annotation. Rule violation detected (R1-R5 or SEM-*), high-confidence correction. hitl_required: false.
- **< 0.70**: Heuristic correction. Ambiguous error or changes mathematical meaning. hitl_required: true (route for PM review).

### 3-Stage Verification (REQ-GC-04)

Applied to golden_jsonl BEFORE producing IC-11. Stage 1 (JSON): JSON.parse succeeds, text field extracted. Stage 2 (LaTeX): All commands well-formed, environments matched, braces balanced. Stage 3 (Render): Output matches IC-06.rendered_description, all elements present. Badge: ALL 3 PASS -> VERIFIED_3STAGE; 1-2 PASS -> VERIFIED_PARTIAL (report failures); 0 PASS -> UNVERIFIED (needs repair).

## Methodology

### 1. Retrieve Golden Answer + Verify

Load IC-06 golden_answer: `jsonl_string`, `json_parsed.text`, `element_list[]` (with critical flags), `trap_annotations[]` (correct_form, incorrect_alternatives, scoring_weight). Apply 3-stage verification FIRST. If golden fails Stage 1/2: attempt self-correction, flag to challenge-generate. If passes all 3: proceed. Record verification result for IC-11.

### 2. Align Trainee vs Golden (Element-Level Diff)

Use IC-09 element_verdicts to identify mismatches. For each element: PASS -> no correction; FAIL -> generate correction(s) with severity; WARN -> generate INFO/WARN correction. Cross-reference each FAIL/WARN with: IC-06.trap_annotations (confidence 0.95+), upstream JSONL errors from jsonl-validate (position_in_jsonl), upstream LaTeX errors from latex-parse (rule_violated mapping).

### 3. Generate IC-11 Corrections

Per correction, produce: `correction_id` (COR-001..N), `category` (7-category: ESCAPE/GROUPING/OPERATOR/SIZING/TEXT/ENVIRONMENT/SEMANTIC), `severity` (FATAL/FAIL/WARN/INFO), `rule_violated` (R1-R5 or SEM-*), `description`, `trainee_form`, `golden_form`, `visual_impact`, `position_in_jsonl` ({char_start, char_end}), `backslash_depth` (0/1/2/4), `confidence` (0.0-1.0), `hitl_required` (true if < 0.7), `trap_id` (null if no match).

Each correction MUST include 4 educational elements: (1) **What**: exact characters differing, (2) **Why**: rule violated + depth context, (3) **Impact**: visual effect, (4) **Fix**: correct form with depth-aware explanation.

### 4. Assemble Golden JSONL + Systematic Numbering

Build complete corrected JSONL string. Annotated version (L2 only) uses COR-001..N markers at correction locations. Ordering: by severity (FATAL first, INFO last); within same severity, by char_start position (left to right). correction_id matches annotation markers.

### 5. Produce IC-11 Correction Report

**Verification section**: `json_valid`, `latex_valid`, `render_matches`, `all_rules_satisfied`, `badge` (VERIFIED_3STAGE only if all 4 pass; VERIFIED_PARTIAL if 1-3; UNVERIFIED if 0).

**Summary section**: `total_corrections`, `by_category` (7 categories), `by_severity` (4 levels), `correction_density` (corrections per JSONL char), `estimated_learning_value` (high: 3+ FATAL/FAIL, medium: 1-2, low: 0 FATAL/FAIL).

## Failure Handling

| Failure | Cause | Action | Route |
|---------|-------|--------|-------|
| CRASH render | JSON parse failure | Minimal correction set (JSON fix only, all FATAL). Verification badge applies to golden, not trainee. | IC-11 with high learning value |
| Golden fails verification | IC-06 has error | Self-correct golden_jsonl; if success: VERIFIED_3STAGE + flag original error; if fail: UNVERIFIED badge with warning. | challenge-generate (flag) + IC-11 produced |
| Confidence < 0.7 | Ambiguous evidence | Set hitl_required: true, include both possible corrections with ambiguity note. | IC-11 to progress-track, PM review triggered |
| Trainee solution better | Valid alternative approach | Set alternative_valid: true, acknowledge, correct genuine errors only. Flag superior approach. | progress-track (bonus recognition) |
| >10 corrections | Severely broken submission | Generate all corrections (no cap), but L2 groups by category with top 5 highlighted + "N more" summary. | progress-track (suggest difficulty reduction) |
| IC-09 missing | Upstream unavailable | Fall back to direct JSONL comparison vs IC-06.jsonl_string (degraded alignment). | Degraded IC-11 |
| IC-06 missing | No golden answer | ABORT -- cannot generate corrections without golden answer. | Error signal to Lead |
| Mode != drill | Wrong pipeline | ABORT -- Pipeline A only. | Error signal to Lead |

## Anti-Patterns

### DO NOT: Just Show the Answer
The golden answer alone has no teaching value. Every correction must explain WHY through the 4-element format (what/why/impact/fix). Corrections without description or visual_impact are incomplete.

### DO NOT: Use Diff Without Explanation
A character-level diff (`-\frac` / `+\\frac`) is insufficient. Trainee needs rule violated, backslash depth context, and visual impact -- not just mechanical change.

### DO NOT: Present Corrections in Random Order
IC-11 corrections MUST be ordered by severity (FATAL first, INFO last), then by position. Systematic numbering COR-001..COR-N reflects this order.

### DO NOT: Skip 3-Stage Verification
Always verify golden_jsonl through all 3 stages before setting badge. VERIFIED_3STAGE on invalid golden is a critical trust violation.

### DO NOT: Criticize the Trainee
Frame as "the parser expects X" not "you made a mistake with X." Persona is a compiler providing diagnostics, not a judge.

### DO NOT: Set hitl_required Without Checking Confidence
confidence < 0.7 -> hitl_required: true. confidence >= 0.7 -> hitl_required: false. Mechanical rule, not judgment.

### DO NOT: Operate in Production Mode
Pipeline A only (AD-1). If mode != "drill", ABORT. Production uses qc-report as terminal skill.

## Transitions

### Receives From
| Source Skill | IC | Data Expected | Key Fields |
|-------------|-----|---------------|------------|
| render-evaluate | IC-09 | rendering_diff | render_status, score.total/total_numeric/by_category, element_verdicts[].{element_id, match, severity, visual_impact}, trap_results, crash_report |
| challenge-generate | IC-06 | golden_answer (hidden) | jsonl_string, json_parsed.text, element_list[], trap_annotations[].{trap_id, correct_form, incorrect_alternatives, scoring_weight}, rendered_description |
| jsonl-validate | -- | JSONL errors | Error positions, escape rule violations (R1-R5) |
| latex-parse | -- | LaTeX errors | Syntax errors, construct mismatches |

### Sends To
| Target Skill | IC | Data Produced | Trigger Condition |
|-------------|-----|---------------|-------------------|
| progress-track | IC-11 | correction_report: corrections[], verification, golden_jsonl, summary | Always (drill cycle terminal) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Golden answer invalid | challenge-generate (error) | Failed verification stage details |
| IC-06 missing | ABORT to Lead | Dependency error signal |
| IC-09 missing | Continue (degraded) | Direct diff without element alignment |
| Mode != drill | ABORT to Lead | Mode mismatch error |

## Quality Gate

- IC-11 validates against schema; corrections ordered FATAL -> FAIL -> WARN -> INFO
- Systematic numbering COR-001..N with no gaps
- 3-stage badge correctly assigned (VERIFIED_3STAGE requires all 4 checks pass)
- All corrections have confidence scores (0.0-1.0); hitl_required correctly set per threshold
- Every correction has 4 educational elements: what + why (rule) + impact + fix
- 7-category taxonomy consistent; 4-severity ordering enforced
- golden_jsonl is complete valid JSONL string (not fragment)
- alternative_valid correctly assessed; learning_value consistent with severity counts

## Output

### L1
```yaml
domain: drill
skill: golden-correct
status: complete
correction_count: 5
categories: {ESCAPE: 2, GROUPING: 1, OPERATOR: 0, SIZING: 1, TEXT: 0, ENVIRONMENT: 0, SEMANTIC: 1}
severity: {FATAL: 1, FAIL: 2, WARN: 1, INFO: 1}
verification_badge: VERIFIED_3STAGE
hitl_count: 0
alternative_valid: false
estimated_learning_value: high
contracts_produced: [IC-11]
```

### L2

Segment-by-segment correction table with educational micro-lessons (what/why/impact/fix), backslash depth annotations on ESCAPE corrections, confidence scores with evidence source, complete verified golden JSONL, annotated golden with COR markers, 3-stage verification report, summary statistics (by_category, by_severity, correction_density).

### IC-11 Example
```yaml
correction_report:
  challenge_id: "CH-042"
  mode: drill
  corrections:
    - correction_id: "COR-001"
      category: ESCAPE
      severity: FATAL
      rule_violated: "R1"
      description: "Backslash not double-escaped for \\frac in JSONL context"
      trainee_form: "\\frac"
      golden_form: "\\\\frac"
      visual_impact: "JSON parser interprets \\f as form-feed, fraction disappears"
      position_in_jsonl: {char_start: 42, char_end: 47}
      backslash_depth: 2
      confidence: 0.97
      hitl_required: false
      trap_id: "ESCAPE_backslash"
    - correction_id: "COR-002"
      category: GROUPING
      severity: FAIL
      rule_violated: "R3"
      description: "Missing braces around multi-character superscript"
      trainee_form: "x^2"
      golden_form: "x^{2}"
      visual_impact: "Only first character superscripted in complex expressions"
      position_in_jsonl: {char_start: 58, char_end: 61}
      backslash_depth: 0
      confidence: 0.95
      hitl_required: false
      trap_id: "GROUPING_superscript"
  verification:
    json_valid: true
    latex_valid: true
    render_matches: true
    all_rules_satisfied: true
    badge: VERIFIED_3STAGE
  golden_jsonl: '{"text": "functions $f(x) = \\\\frac{x^{2}}{2}$..."}'
  alternative_valid: false
  summary:
    total_corrections: 2
    by_category: {ESCAPE: 1, GROUPING: 1, OPERATOR: 0, SIZING: 0, TEXT: 0, ENVIRONMENT: 0, SEMANTIC: 0}
    by_severity: {FATAL: 1, FAIL: 1, WARN: 0, INFO: 0}
    correction_density: 0.025
    estimated_learning_value: high
```
