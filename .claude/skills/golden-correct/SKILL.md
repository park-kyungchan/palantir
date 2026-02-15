---
name: golden-correct
description: |
  [D1·Drill·Correction] Generates IC-11 correction_report with 7-category taxonomy, 3-stage verification badge, and per-correction confidence scoring. Terminal skill in Pipeline A drill cycle.

  WHEN: After render-evaluate completes (IC-09 rendering_diff available). Terminal skill in D1 drill cycle.
  DOMAIN: drill (skill 5 of 5). Terminal: golden-correct -> progress-track (D2). Pipeline A ONLY (drill mode).
  INPUT_FROM: IC-09 rendering_diff (render-evaluate: render_status, score, element_verdicts, trap_results, crash_report), IC-06 golden_answer (challenge-generate: element_list, trap_annotations, rendered_description), jsonl-validate (JSONL errors), latex-parse (LaTeX errors).
  OUTPUT_TO: IC-11 correction_report (progress-track: corrections[] FATAL-first, verification badge, golden_jsonl, summary by_category/by_severity/correction_density/learning_value).

  METHODOLOGY: (1) Retrieve IC-06 golden_answer + 3-stage verify, (2) Align trainee vs golden via IC-09 element_verdicts, (3) Generate corrections with category/severity/rule/backslash_depth/confidence, (4) Assemble golden_jsonl with COR-001..COR-N markers, (5) Produce IC-11 with VERIFIED_3STAGE badge + summary.
  OUTPUT_FORMAT: L1 YAML with verification_badge + hitl_count + contracts_produced, L2 correction table + IC-11 example.
user-invocable: false
disable-model-invocation: false
---

# Drill -- Golden Correct (Pipeline A Terminal)

## Execution Model
- **All levels**: Lead-direct. Correction generation is deterministic given upstream analysis.
- **Pipeline A ONLY**: This skill operates exclusively in drill mode. Production QC uses a separate pipeline.
- This is the "teaching moment" -- every correction must be educational, not just mechanical.
- Terminal skill in the drill cycle. Output (IC-11 correction_report) feeds progress-track for learning analytics.

## Decision Points

### Correction Presentation Strategy
```
IF IC-09.render_status == CRASH (JSON parse failure):
  -> Minimal correction: fix JSON structure only (COR-001 = JSON fix)
  -> Then show full golden answer
  -> All corrections severity: FATAL
  -> Lesson: "JSON validity is prerequisite -- fix structure before content"

ELIF IC-09.score.total_numeric < 0.5:
  -> Show corrections grouped by severity (FATAL -> FAIL -> WARN -> INFO)
  -> Highlight the 3 most impactful corrections
  -> Full golden answer at end

ELIF IC-09.score.total_numeric >= 0.5:
  -> Show segment-by-segment diff
  -> Each correction as a "micro-lesson"
  -> Golden answer at end as confirmation
```

### Diff Alignment Strategy
```
IF trainee submission structurally similar to golden:
  -> Character-level diff (precise alignment)
  -> Position mapping: char_start/char_end in JSONL string
ELIF trainee submission restructured differently:
  -> Segment-level diff (match by mathematical content, not position)
  -> Use IC-09.element_verdicts to identify element-level matches
ELIF trainee submission fundamentally different approach:
  -> Side-by-side comparison (trainee approach vs golden approach)
  -> Check alternative_valid flag
```

### Alternative Valid Solutions
```
IF trainee approach different but produces identical rendering:
  -> Set alternative_valid: true in IC-11
  -> Show both approaches with style preference note
  -> Corrections still generated for "preferred form" education
ELIF trainee approach different and produces different rendering:
  -> Set alternative_valid: false
  -> Show why golden approach is correct via visual_impact field
```

### Backslash Depth Tracking (REQ-GC-03)
Every ESCAPE-category correction must include backslash depth annotation:
```
Depth 0: LaTeX source level (image -> LaTeX)
  - Raw LaTeX: \frac{x}{2}
  - Backslash count: 1 per command

Depth 1: String level (LaTeX -> string)
  - String literal: \\frac{x}{2}
  - Backslash count: 2 per command

Depth 2: JSONL level (string -> JSONL)
  - Inside JSONL: \\frac{x}{2} (JSON string escaping)
  - Backslash count: 2 per command (JSON parser reduces \\\\ -> \\)

Depth 4: JSONL-in-JSON level (JSONL -> outer JSON wrapper)
  - Nested escaping: \\\\frac{x}{2}
  - Backslash count: 4 per command
```

Corrections report which depth the error occurs at and what the correct form is at that depth.

### Confidence Scoring (REQ-GC-07)
Per-correction confidence based on evidence source:
```
confidence >= 0.95: Exact match with IC-06.trap_annotations[]
  -> trap_id mapped, correct_form confirmed, scoring_weight applied
  -> hitl_required: false

confidence 0.70-0.94: Pattern match without annotation
  -> Rule violation detected (R1-R5 or SEM-*), form correction clear
  -> No matching trap_annotation but correction is high-confidence
  -> hitl_required: false

confidence < 0.70: Heuristic correction
  -> Ambiguous error, multiple possible corrections
  -> OR correction changes mathematical meaning
  -> hitl_required: true (route for PM review)
```

### 3-Stage Verification (REQ-GC-04)
Applied to golden_jsonl BEFORE producing IC-11:
```
Stage 1: JSON Validity
  -> JSON.parse(golden_jsonl) succeeds
  -> Extracts text field without error
  -> FAIL: golden_jsonl is not valid JSON

Stage 2: LaTeX Syntax Check
  -> All LaTeX commands are well-formed
  -> All environments have matching \begin/\end
  -> All braces balanced, no orphaned delimiters
  -> FAIL: LaTeX syntax error detected

Stage 3: Render Match
  -> Rendered output matches IC-06.rendered_description
  -> All IC-06.element_list elements present and correct
  -> FAIL: rendered output differs from target

Badge Assignment:
  ALL 3 PASS -> badge: VERIFIED_3STAGE
  1-2 PASS   -> badge: VERIFIED_PARTIAL (report which stages failed)
  0 PASS      -> badge: UNVERIFIED (golden answer needs repair)
```

## Methodology

### 1. Retrieve Golden Answer + Verify
Load IC-06 golden_answer from challenge-generate:
- `jsonl_string`: the correct JSONL
- `json_parsed.text`: extracted text content
- `element_list[]`: element-level descriptions with critical flags
- `trap_annotations[]`: intentional traps with correct_form, incorrect_alternatives, scoring_weight

**Defensive verification**: Apply 3-stage verification to IC-06 golden_answer FIRST.
- If golden answer fails Stage 1 or 2: attempt self-correction, flag to challenge-generate (see Failure Handling).
- If golden answer passes all 3 stages: proceed to alignment.
- Record verification result for inclusion in IC-11.verification.

### 2. Align Trainee vs Golden (Element-Level Diff)
Use IC-09 element_verdicts to identify mismatches:

```yaml
# For each element in IC-09.element_verdicts:
element_verdicts:
  - element_id: "E1"
    match: PASS           # -> No correction needed
  - element_id: "E2"
    match: FAIL
    severity: FATAL
    target_description: "fraction x-squared over 2"
    actual_description: "garbled output, backslash-f visible"
    visual_impact: "entire fraction unreadable"
    # -> Generate correction(s) for this element
  - element_id: "E3"
    match: WARN
    severity: WARN
    target_description: "auto-sized parentheses around expression"
    actual_description: "fixed-size parentheses, slightly too small"
    visual_impact: "minor aesthetic issue"
    # -> Generate INFO/WARN correction
```

Cross-reference each FAIL/WARN element with:
- IC-06.trap_annotations[] (for confidence scoring: trap match = 0.95+)
- Upstream JSONL errors from jsonl-validate (for position_in_jsonl)
- Upstream LaTeX errors from latex-parse (for rule_violated mapping)

### 3. Generate IC-11 Corrections
For each diff, produce a structured correction entry:

```yaml
correction:
  correction_id: "COR-001"        # Systematic numbering
  category: ESCAPE                 # 7-category: ESCAPE/GROUPING/OPERATOR/SIZING/TEXT/ENVIRONMENT/SEMANTIC
  severity: FATAL                  # 4-level: FATAL/FAIL/WARN/INFO
  rule_violated: "R1"             # R1-R5 for JSONL rules, SEM-* for semantic rules
  description: "Backslash not double-escaped in JSONL context"
  trainee_form: "\\frac"          # What trainee wrote (as it appears in their JSONL)
  golden_form: "\\\\frac"         # Correct form (as it should appear in JSONL)
  visual_impact: "JSON parser interprets \\f as form-feed character, entire fraction disappears"
  position_in_jsonl:
    char_start: 42
    char_end: 47
  backslash_depth: 2              # REQ-GC-03: 0=LaTeX, 1=string, 2=JSONL, 4=nested
  confidence: 0.97                # REQ-GC-07: 0.95+ = trap match, 0.7-0.94 = pattern, <0.7 = heuristic
  hitl_required: false            # true if confidence < 0.7
  trap_id: "ESCAPE_backslash"    # null if no matching trap_annotation
```

**Educational micro-lesson** per correction (for L2 output):
```
[COR-001] Category: ESCAPE | Severity: FATAL | Rule: R1 (Backslash Double-Escape)
  Depth: 2 (JSONL level)
  Trainee: \frac  (1 backslash -- LaTeX level, not JSONL level)
  Golden:  \\frac (2 backslashes -- correct for JSONL context)
  Rule: In JSONL, every LaTeX backslash must be double-escaped.
        \frac -> JSON parser sees \ as escape char -> interprets \f as form-feed
        \\frac -> JSON parser sees \\ as literal \ -> passes \frac to LaTeX
  Visual Impact: Without double-escape, JSON parser may fail entirely,
                 or produce garbled output where \f becomes form-feed.
  Confidence: 0.97 (exact trap match: ESCAPE_backslash)
```

Each correction MUST include all 4 educational elements:
1. **What**: Exact characters that differ (trainee_form vs golden_form)
2. **Why**: Rule violated (R1-R5, SEM-*) + backslash depth context
3. **Impact**: Visual effect of the error (visual_impact field)
4. **Fix**: Correct form with depth-aware explanation

### 4. Assemble Golden JSONL + Systematic Numbering
Build the complete corrected JSONL string with correction markers:

```json
{"text": "functions $f(x) = \\frac{x^{2}}{2}$ where $x > 0$,\n$$\\int_0^x f(t)\\,dt = \\frac{x^{3}}{6}$$"}
```

Annotated version with correction markers (L2 only, not in golden_jsonl):
```
{"text": "functions $f(x) = [COR-001]\\frac{x^[COR-002]{2}}{2}$ where..."}
                              ^^^^^^^           ^^^^^^^^^
                           escape fix         grouping fix
```

Systematic numbering rules:
- COR-001 through COR-N, ordered by severity (FATAL first, INFO last)
- Within same severity: ordered by position_in_jsonl.char_start (left to right)
- correction_id in IC-11 matches the annotation markers

### 5. Produce IC-11 Correction Report
Assemble the complete IC-11 correction_report:

**Verification section**: Record 3-stage results from Step 1.
```yaml
verification:
  json_valid: true         # Stage 1 result
  latex_valid: true        # Stage 2 result
  render_matches: true     # Stage 3 result
  all_rules_satisfied: true  # All R1-R5 + SEM-* rules pass
  badge: VERIFIED_3STAGE   # Only if all 4 checks pass
```

**Summary section**: Aggregate statistics for progress-track.
```yaml
summary:
  total_corrections: 5
  by_category:
    ESCAPE: 2
    GROUPING: 1
    OPERATOR: 0
    SIZING: 1
    TEXT: 0
    ENVIRONMENT: 0
    SEMANTIC: 1
  by_severity:
    FATAL: 1
    FAIL: 2
    WARN: 1
    INFO: 1
  correction_density: 0.05    # corrections per character in JSONL
  estimated_learning_value: high  # high (>=3 FATAL/FAIL), medium (1-2), low (0)
```

**Learning value estimation**:
- `high`: 3+ corrections at FATAL or FAIL severity (significant teaching opportunity)
- `medium`: 1-2 corrections at FATAL or FAIL (targeted improvement)
- `low`: 0 FATAL/FAIL corrections (only WARN/INFO -- polish only)

## Failure Handling

### IC-09 render_status == CRASH
- **Cause**: JSON parse failure in trainee submission, nothing renders
- **Action**: Generate minimal correction set: JSON structure fix only. All corrections severity FATAL. Set golden_jsonl to the correct form. Verification badge still applies to the golden answer (not trainee).
- **Route**: IC-11 to progress-track with high learning value flag
- **Educational framing**: "JSON validity is a prerequisite. Fix structure before content."

### Golden Answer Fails 3-Stage Verification
- **Cause**: IC-06 golden_answer has an error (challenge-generate produced imperfect answer)
- **Action**: Attempt self-correction of golden_jsonl. If self-correction succeeds: use corrected version, set `badge: VERIFIED_3STAGE`, flag original error to challenge-generate. If self-correction fails: set `badge: UNVERIFIED`, include raw golden_jsonl with warning.
- **Route**: challenge-generate (flag for quality improvement), IC-11 still produced with UNVERIFIED badge

### Confidence < 0.7 on Any Correction
- **Cause**: Heuristic correction with ambiguous evidence
- **Action**: Set `hitl_required: true` on that correction. Include both possible corrections if ambiguous. Add note explaining the ambiguity.
- **Route**: IC-11 to progress-track. PM review triggered for hitl_required corrections.

### Trainee Solution Better Than Golden
- **Cause**: Trainee found a valid alternative approach producing identical rendering
- **Action**: Set `alternative_valid: true`. Acknowledge the approach. Generate corrections only for genuine errors (not style differences). If trainee approach is strictly superior, flag to challenge-generate.
- **Route**: progress-track (bonus recognition for superior solution)

### Too Many Corrections (>10)
- **Cause**: Severely broken submission with widespread errors
- **Action**: Generate all corrections (no cap on IC-11.corrections[]), but in L2 presentation group by category and highlight top 5 with "N more similar corrections" summary.
- **Route**: progress-track (flag multiple weak areas, suggest difficulty reduction)

### Missing Upstream Data
- **Cause**: IC-09 or IC-06 unavailable
- **Action**: If IC-09 missing: cannot perform element-level alignment. Fall back to direct comparison of trainee JSONL vs IC-06.jsonl_string. If IC-06 missing: ABORT (cannot generate corrections without golden answer).
- **Route**: Error signal to Lead if IC-06 missing. Degraded IC-11 if IC-09 missing.

## Anti-Patterns

### DO NOT: Just Show the Answer
The golden answer alone has no teaching value. Every correction must explain WHY through the 4-element format (what/why/impact/fix). IC-11 corrections without description or visual_impact are incomplete.

### DO NOT: Use Diff Without Explanation
A character-level diff (`-\frac` / `+\\frac`) is insufficient. The trainee needs to understand the rule violated, the backslash depth context, and the visual impact -- not just the mechanical change.

### DO NOT: Present Corrections in Random Order
Corrections in IC-11 MUST be ordered by severity (FATAL first, INFO last). Within same severity, order by position in JSONL string. The systematic numbering COR-001..COR-N reflects this order.

### DO NOT: Skip 3-Stage Verification
Always verify the golden_jsonl through all 3 stages before setting the badge. A VERIFIED_3STAGE badge on an invalid golden answer is a critical trust violation. When in doubt, use VERIFIED_PARTIAL.

### DO NOT: Criticize the Trainee
Frame corrections as "the parser expects X" not "you made a mistake with X." The persona is a compiler providing diagnostic output, not a judge issuing verdicts.

### DO NOT: Set hitl_required Without Checking Confidence
Every correction with confidence < 0.7 MUST have hitl_required: true. Every correction with confidence >= 0.7 MUST have hitl_required: false. This is a mechanical rule, not a judgment call.

### DO NOT: Operate in Production Mode
This skill is Pipeline A only (AD-1). If mode != "drill", ABORT. Production QC uses a separate pipeline with qc-report as terminal skill.

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
- IC-11 correction_report validates against schema (all required fields present)
- Corrections ordered by severity: FATAL -> FAIL -> WARN -> INFO
- Systematic numbering: COR-001 through COR-N, no gaps
- 3-stage verification badge correctly assigned:
  - VERIFIED_3STAGE only if json_valid AND latex_valid AND render_matches AND all_rules_satisfied
  - VERIFIED_PARTIAL if 1-3 checks pass (with report of failed checks)
  - UNVERIFIED if 0 checks pass
- All corrections have confidence scores (0.0-1.0)
- hitl_required correctly set: true if confidence < 0.7, false otherwise
- Every correction has all 4 educational elements: what + why (rule) + impact + fix
- 7-category taxonomy used consistently: ESCAPE/GROUPING/OPERATOR/SIZING/TEXT/ENVIRONMENT/SEMANTIC
- 4-severity ordering enforced: FATAL/FAIL/WARN/INFO
- golden_jsonl is a complete, valid JSONL string (not a fragment)
- alternative_valid correctly assessed
- summary.estimated_learning_value consistent with by_severity counts

## Output

### L1
```yaml
domain: drill
skill: golden-correct
status: complete
correction_count: 5
categories:
  ESCAPE: 2
  GROUPING: 1
  OPERATOR: 0
  SIZING: 1
  TEXT: 0
  ENVIRONMENT: 0
  SEMANTIC: 1
severity:
  FATAL: 1
  FAIL: 2
  WARN: 1
  INFO: 1
verification_badge: VERIFIED_3STAGE
hitl_count: 0
alternative_valid: false
estimated_learning_value: high
contracts_produced: [IC-11]
```

### L2
- Segment-by-segment correction table with educational micro-lessons (what/why/impact/fix)
- Backslash depth annotations on ESCAPE-category corrections
- Confidence scores per correction with evidence source
- Complete golden JSONL string (copyable, verified)
- Annotated golden JSONL with COR-001..COR-N markers
- 3-stage verification report (Stage 1: JSON, Stage 2: LaTeX, Stage 3: Render)
- Summary statistics: by_category, by_severity, correction_density
- IC-11 correction_report (complete structured output for progress-track)

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
      description: "Backslash not double-escaped for \\frac command in JSONL context"
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
    - correction_id: "COR-003"
      category: SEMANTIC
      severity: WARN
      rule_violated: "SEM-spacing"
      description: "Missing thin space before differential dx"
      trainee_form: "f(t)dt"
      golden_form: "f(t)\\\\,dt"
      visual_impact: "Integral lacks conventional spacing before differential"
      position_in_jsonl: {char_start: 112, char_end: 118}
      backslash_depth: 2
      confidence: 0.82
      hitl_required: false
      trap_id: null
  verification:
    json_valid: true
    latex_valid: true
    render_matches: true
    all_rules_satisfied: true
    badge: VERIFIED_3STAGE
  golden_jsonl: '{"text": "functions $f(x) = \\\\frac{x^{2}}{2}$ where $x > 0$,\\n$$\\\\int_0^x f(t)\\\\,dt = \\\\frac{x^{3}}{6}$$"}'
  alternative_valid: false
  summary:
    total_corrections: 3
    by_category: {ESCAPE: 1, GROUPING: 1, OPERATOR: 0, SIZING: 0, TEXT: 0, ENVIRONMENT: 0, SEMANTIC: 1}
    by_severity: {FATAL: 1, FAIL: 1, WARN: 1, INFO: 0}
    correction_density: 0.025
    estimated_learning_value: high
```
