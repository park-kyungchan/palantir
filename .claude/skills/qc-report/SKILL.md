---
name: qc-report
description: |
  [D1·PipelineB·QCReport] ProduceQCVerdict: production pass/fail report with HITL routing, batch aggregation, auto-fix suggestions. Pipeline B terminal.

  WHEN: After render-evaluate completes in production mode (IC-12 qc_rendering available). Pipeline B terminal skill.
  DOMAIN: production QC (D1 terminal). Pipeline B ONLY. PM/PL-facing output.
  INPUT_FROM: IC-12 qc_rendering (render-evaluate: fidelity_score, fidelity_breakdown, error_taxonomy, element_verdicts, hitl_required, source_comparison).
  OUTPUT_TO: qc-metrics (QC report data for aggregation at crowd_works/data/qc-reports/), PM/PL (HITL review items).

  METHODOLOGY: (1) Receive IC-12 qc_rendering, (2) Determine verdict (PASS/CONDITIONAL_PASS/FAIL/HITL_REQUIRED), (3) Filter auto-fix suggestions (confidence>95%), (4) Generate QC report with CrowdWorks format, (5) Persist + batch summary.
  OUTPUT_FORMAT: L1 YAML verdict+fidelity+error_count, L2 full QC report with error details+fix suggestions+HITL items.
user-invocable: true
disable-model-invocation: false
argument-hint: "[file-or-directory]"
---

# Production QC Report -- Pipeline B Terminal

## Execution Model
- **Single-file QC**: One production JSONL file. Receive IC-12, determine verdict, generate report.
- **Batch QC**: Directory of JSONL files. Iterate per-file, generate individual reports + batch summary.
- **All tiers**: Lead-direct. QC reporting is deterministic analysis given IC-12 input.
- Pipeline B ONLY (AD-1). This skill never operates in drill mode.
- PM/PL-facing terminal skill. All output must be actionable, human-readable, and in CrowdWorks submission format.

## Decision Points

### 1. Pass/Fail Verdict Determination

```
IF render_status == CRASH:
  -> FAIL (automatic)
  -> hitl_priority: urgent
  -> Suggest JSON structure fixes from error_taxonomy

ELIF fidelity_score >= 0.85 AND no FATAL errors AND no unresolved HITL:
  IF has WARN-level auto-fixable issues:
    -> CONDITIONAL_PASS
    -> Include auto-fix suggestions, no PM review needed
  ELSE:
    -> PASS
    -> Ready for delivery

ELIF fidelity_score >= 0.70 AND fidelity_score < 0.85:
  -> HITL_REQUIRED
  -> hitl_priority: based on score distance from threshold
  -> PM must review and approve/reject/rework

ELIF fidelity_score < 0.70 OR any FATAL error:
  -> FAIL
  -> hitl_priority: urgent if FATAL, normal otherwise
  -> Detailed error report for rework

ELIF confidence < 0.80 (regardless of score):
  -> HITL_REQUIRED
  -> Evaluation uncertain, needs human judgment
```

### 2. Auto-Fix Decision (REQ-QR-07)

From IC-12 error_taxonomy, filter for auto-fixable items:
```
ELIGIBLE for auto-fix:
  - auto_fixable == true
  - auto_fix_confidence > 0.95
  - category in [ESCAPE, GROUPING] (well-defined mechanical rules)

NEVER auto-fix:
  - SEMANTIC errors (meaning changes require human judgment)
  - ENVIRONMENT structure changes (document-level restructuring)
  - Content additions (missing elements cannot be auto-generated)
  - Any item with auto_fix_confidence <= 0.95
```

Auto-fix suggestions are SUGGESTIONS only -- they do not modify the source file. PM/PL decides whether to apply.

### 3. Batch Processing Strategy (REQ-QR-02)

```
IF input is single file:
  -> Generate one QC report
  -> Persist to crowd_works/data/qc-reports/{date}_{file_id}.yaml

IF input is directory:
  -> Process each JSONL file independently (each gets its own IC-12)
  -> Generate per-file QC report
  -> Aggregate batch summary:
     batch_id, total, pass_count, conditional_pass_count,
     fail_count, hitl_count, avg_fidelity, systemic_issues[]
  -> Persist to crowd_works/data/qc-reports/{batch-date}.yaml

IF batch fail_rate > 50%:
  -> Flag batch for systemic issue review
  -> Identify common error categories across failed files
  -> Recommend batch-level corrective action
```

### 4. HITL Routing (REQ-QR-04)

Priority assignment based on severity and score:
```
urgent:
  - Any FATAL error in error_taxonomy
  - render_status == CRASH
  - fidelity_score < 0.50

normal:
  - fidelity_score 0.50-0.70 (clear fail, needs rework)
  - fidelity_score 0.70-0.85 (threshold zone, needs review)

low:
  - confidence < 0.80 but fidelity_score >= 0.85
  - Minor ambiguities requiring confirmation
```

HITL items enter "검수 대기" (review pending) state. PM can:
- **Approve**: Override to PASS (with PM approval stamp)
- **Reject**: Confirm FAIL, route to rework
- **Request Re-work**: Send back with specific correction instructions

### 5. CrowdWorks Submission Format (REQ-QR-05)

Report structure optimized for PM/PL consumption:
- Korean status labels: 합격(PASS), 조건부 합격(CONDITIONAL_PASS), 불합격(FAIL), 검수 대기(HITL_REQUIRED)
- Include: file_id, worker_id (if available from metadata), verdict, error_count, fix_suggestions
- Error descriptions translated to human-readable form (no raw JSONL technical details)
- Actionable next steps per verdict

## Methodology

### 1. Receive IC-12 qc_rendering

Load IC-12 from render-evaluate (production mode):
```yaml
required_fields:
  file_id: string              # Production file identifier
  mode: "production"           # Must be "production" -- reject drill mode
  render_status: FULL|PARTIAL|CRASH
  fidelity_score: float        # 0.0-1.0
  fidelity_breakdown:
    structural: float
    textual: float
    formatting: float
    completeness: float
  element_verdicts: array
  error_taxonomy: array
  hitl_required: boolean
  confidence: float

optional_fields:
  batch_id: string
  source_comparison: object    # OCR pipeline only
  hitl_reason: string
  hitl_priority: string
```

**Validation**: If `mode != "production"`, ABORT. qc-report is Pipeline B only.
**Validation**: If IC-12 is missing entirely, ABORT (cannot generate QC without evaluation).

### 2. Determine Verdict

Apply the decision tree from Decision Points section 1.

Record verdict with full audit trail:
```yaml
verdict:
  result: PASS|CONDITIONAL_PASS|FAIL|HITL_REQUIRED
  fidelity_score: 0.87
  threshold_applied: 0.85
  fatal_errors: 0
  determining_factor: "fidelity_score >= 0.85, no FATAL errors"
  confidence: 0.92
```

Cross-validate: If IC-12 `hitl_required: true` but local verdict is PASS, escalate to HITL_REQUIRED (upstream HITL flag takes precedence).

### 3. Process Auto-Fix Suggestions (REQ-QR-07)

Filter IC-12 error_taxonomy for auto-fixable items:
```yaml
auto_fixes: []
for each error in error_taxonomy:
  if error.auto_fixable == true
     AND error.auto_fix_confidence > 0.95
     AND error.category in [ESCAPE, GROUPING]:
    -> Include in auto_fixes[]
    -> Record: error_id, category, description, auto_fix_suggestion, confidence
  elif error.auto_fixable == true
     AND (error.auto_fix_confidence <= 0.95 OR error.category in [SEMANTIC, ENVIRONMENT]):
    -> Exclude from auto_fixes[]
    -> Record in excluded_fixes[] with reason
```

Count auto-fixable vs manual-fix items for summary statistics.

### 4. Generate QC Report

Assemble the report in CrowdWorks submission format:

**Header** (Korean labels for PM consumption):
```
파일 ID: {file_id}
배치 ID: {batch_id or "단건"}
작업자 ID: {worker_id or "N/A"}
검수 일시: {evaluated_at}
판정: {Korean verdict label}
```

**Fidelity Summary**:
```
종합 충실도: {fidelity_score * 100}%
  구조 정확도: {structural * 100}%
  텍스트 정확도: {textual * 100}%
  서식 정확도: {formatting * 100}%
  완전성: {completeness * 100}%
```

**Error Details** (from error_taxonomy, sorted by severity FATAL-first):
For each error:
- Human-readable description (no raw JSONL/LaTeX code)
- Category (7-category: ESCAPE/GROUPING/OPERATOR/SIZING/TEXT/ENVIRONMENT/SEMANTIC)
- Severity (FATAL/FAIL/WARN/INFO)
- Auto-fix available? If yes, include suggestion text.

**HITL Section** (only if hitl_required):
- Priority level with Korean label
- Reason for human review
- Specific items requiring PM decision
- Recommended action

**Source Comparison** (REQ-QR-03, if source_comparison available):
- Source type (image/latex_draft/ocr_output)
- Comparison method used
- Discrepancies list with location, expected vs actual, severity

### 5. Persist + Batch Summary

**Single file persistence**:
```
crowd_works/data/qc-reports/{YYYY-MM-DD}_{file_id}.yaml
```

**Batch persistence**:
```
crowd_works/data/qc-reports/{batch_id}_{YYYY-MM-DD}.yaml
```

Contents: Full structured QC report (YAML format) including:
- verdict, fidelity_score, fidelity_breakdown
- error_taxonomy (full, with auto-fix annotations)
- hitl_routing (if applicable)
- source_comparison (if applicable)
- metadata (evaluated_at, batch_id, skill version)

**Batch summary** (appended to batch file):
```yaml
batch_summary:
  batch_id: string
  total_files: int
  pass_count: int
  conditional_pass_count: int
  fail_count: int
  hitl_count: int
  avg_fidelity: float
  min_fidelity: float
  max_fidelity: float
  common_errors:
    - category: ESCAPE
      count: 12
      description: "Backslash escaping issues"
    - category: GROUPING
      count: 5
      description: "Missing braces in expressions"
  systemic_flag: boolean       # true if fail_rate > 50%
  systemic_analysis: string    # Common root cause if systemic_flag
```

## Failure Handling

### IC-12 Missing
- **Cause**: render-evaluate did not produce IC-12, or mode was not production
- **Action**: ABORT. Cannot generate QC report without evaluation data.
- **Route**: Error signal to Lead. No report persisted.

### render_status == CRASH
- **Cause**: JSON parse failure in production file
- **Action**: Automatic FAIL verdict. Set hitl_priority: urgent. Include crash_reason from IC-12. Suggest JSON structure fixes if error_taxonomy contains auto-fixable items.
- **Route**: QC report persisted with FAIL verdict. HITL routing triggered.

### All Errors FATAL
- **Cause**: Every error in error_taxonomy has severity FATAL
- **Action**: FAIL verdict. Set hitl_priority: urgent. Flag for immediate PM review.
- **Route**: QC report persisted. Urgent HITL routing.

### Batch >50% FAIL Rate
- **Cause**: Systemic issue across batch (worker error pattern, broken pipeline step)
- **Action**: Set systemic_flag: true in batch summary. Identify common error categories. Recommend batch-level corrective action (re-training, pipeline fix, data source review).
- **Route**: Batch summary flagged. PM alerted to systemic issue.

### Persistence Failure
- **Cause**: Cannot write to crowd_works/data/qc-reports/
- **Action**: Generate full report to stdout (L1 + L2 output). Warn that report was not persisted. Include all data needed for manual persistence.
- **Route**: Report delivered via L1/L2 output. Manual save required.

### Mode Mismatch
- **Cause**: IC-12 contains mode: "drill" instead of "production"
- **Action**: ABORT. qc-report is Pipeline B only (AD-1). Drill mode uses golden-correct.
- **Route**: Error signal to Lead with mode mismatch detail.

### Fidelity Score Missing
- **Cause**: IC-12 has render_status but fidelity_score is null/missing
- **Action**: If render_status == CRASH: proceed with FAIL verdict (fidelity implied 0.0). Otherwise: set verdict to HITL_REQUIRED with reason "fidelity score unavailable".
- **Route**: QC report persisted with degraded confidence.

## Anti-Patterns

### DO NOT: Auto-Approve Below Fidelity Threshold
Items with fidelity_score < 0.85 MUST NOT receive PASS verdict regardless of other factors. The threshold is a hard gate, not a guideline.

### DO NOT: Mix Drill and Production Mode
qc-report is Pipeline B only (AD-1). If mode == "drill", ABORT. Drill mode evaluation uses golden-correct as terminal skill. Cross-routing breaks schema assumptions.

### DO NOT: Auto-Fix SEMANTIC Errors
SEMANTIC errors change mathematical meaning. Even with high auto_fix_confidence, semantic corrections require human judgment. Only ESCAPE and GROUPING categories are eligible for auto-fix.

### DO NOT: Skip HITL When Confidence < 0.8
Low confidence means the evaluation itself is uncertain. Regardless of fidelity_score, confidence < 0.8 triggers HITL_REQUIRED. This is a safety gate for production quality.

### DO NOT: Expose Raw Technical Details to PM
Error descriptions must be human-readable. Translate JSONL parse errors, LaTeX syntax issues, and escape violations into descriptions a PM/PL can act on. "Backslash escaping error in fraction" not "\\frac parse failure at offset 42".

### DO NOT: Suppress Batch Systemic Flags
When >50% of a batch fails, the problem is likely systemic (worker training gap, broken upstream step, data source issue). Always flag this explicitly -- individual file fixes will not solve systemic problems.

### DO NOT: Override Upstream HITL Flag
If IC-12 sets hitl_required: true, the QC report MUST preserve this. Never downgrade an upstream HITL flag to PASS based on local fidelity score alone.

## Transitions

### Receives From
| Source Skill | IC | Data Expected | Key Fields |
|-------------|-----|---------------|------------|
| render-evaluate | IC-12 | qc_rendering (production mode) | file_id, mode, render_status, fidelity_score, fidelity_breakdown, element_verdicts[], error_taxonomy[], source_comparison, hitl_required, hitl_reason, hitl_priority, confidence |

### Sends To
| Target | Data Produced | Trigger Condition |
|--------|---------------|-------------------|
| qc-metrics | QC report data (persisted YAML) | Always (report persisted to crowd_works/data/qc-reports/) |
| PM/PL | HITL review items | When verdict is HITL_REQUIRED or FAIL with hitl_priority |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| IC-12 missing | ABORT to Lead | Dependency error signal |
| Mode mismatch (drill) | ABORT to Lead | Mode mismatch error |
| Persistence failure | Continue (degraded) | Full report via L1/L2 stdout |
| Batch systemic flag | PM alert | Batch summary with systemic analysis |

## Quality Gate
- Verdict consistent with fidelity_score thresholds (PASS >= 0.85, HITL 0.70-0.85, FAIL < 0.70)
- render_status == CRASH always produces FAIL verdict
- Auto-fix suggestions limited to confidence > 0.95 and ESCAPE/GROUPING categories only
- HITL correctly routed for all threshold and low-confidence items
- Upstream hitl_required flag preserved (never downgraded)
- Error taxonomy uses 7-category system: ESCAPE/GROUPING/OPERATOR/SIZING/TEXT/ENVIRONMENT/SEMANTIC
- Error severity uses 4-level system: FATAL/FAIL/WARN/INFO
- CrowdWorks format: Korean labels, human-readable descriptions, actionable structure
- Report persisted to crowd_works/data/qc-reports/ (or stdout fallback with warning)
- Batch summary includes systemic flag when fail_rate > 50%
- All 7 REQ-QR requirements addressed

## Output

### L1
```yaml
domain: production
skill: qc-report
status: complete
file_id: "PROD-2024-001"
batch_id: "BATCH-20240215"
verdict: PASS|CONDITIONAL_PASS|FAIL|HITL_REQUIRED
fidelity_score: 0.87
error_count: 2
auto_fix_count: 1
hitl_required: false
hitl_priority: null
persisted_to: "crowd_works/data/qc-reports/2024-02-15_PROD-2024-001.yaml"
```

### L1 -- Batch Mode
```yaml
domain: production
skill: qc-report
status: complete
batch_id: "BATCH-20240215"
batch_summary:
  total: 25
  pass: 18
  conditional_pass: 3
  fail: 2
  hitl_required: 2
  avg_fidelity: 0.89
  systemic_flag: false
persisted_to: "crowd_works/data/qc-reports/BATCH-20240215_2024-02-15.yaml"
```

### L2
- **Header**: File/batch identification with Korean status labels
- **Verdict Section**: Pass/fail determination with full audit trail (score, threshold, determining factor)
- **Fidelity Breakdown**: Per-dimension scores (structural, textual, formatting, completeness)
- **Error Details**: Per-error with category, severity, human-readable description, auto-fix status
- **Auto-Fix Suggestions**: Filtered list with confidence scores and suggested corrections
- **HITL Items**: Priority-ranked list of items requiring PM review with recommended actions
- **Source Comparison**: Discrepancy analysis vs source image/document (when available)
- **Batch Summary**: Aggregate statistics, common error patterns, systemic flags (batch mode)
- **Persisted Report Path**: Location of YAML report file for downstream qc-metrics consumption
