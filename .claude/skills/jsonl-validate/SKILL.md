---
name: jsonl-validate
description: |
  Validates JSONL structural integrity in dual mode: drill (vs challenge_spec, educational feedback) or production QC (vs preprocessed_input, PASS/FAIL binary). 3-tier severity (FATAL/WARN/INFO), char-level positioning, R1-R5 escape compliance. Parallel with latex-parse.

  WHEN: After trainee submits JSONL (drill) or worker/OCR output arrives (production). Mode from $ARGUMENTS or upstream.
  CONSUMES: challenge-generate (IC-04 challenge_spec, drill), image-preprocess (IC-13 preprocessed_input, production), User input (raw JSONL).
  PRODUCES: IC-07 validation_result → render-evaluate, drill errors → golden-correct, production verdict → qc-report. HITL queue when confidence < 0.8 (production).
user-invocable: true
disable-model-invocation: true
---

# D1 Shared Validation Core — JSONL Validate (Dual-Mode)

## Execution Model
- **All tiers**: Lead-direct. JSONL validation is deterministic; no agent spawning needed.
- **Dual-mode**: Mode determined per-invocation by $ARGUMENTS or upstream skill identity.
  - Drill mode: upstream = challenge-generate, educational feedback, no partial recovery.
  - Production QC mode: upstream = image-preprocess, binary verdict, partial recovery attempted.
- Always runs parallel with latex-parse (independent structural vs semantic concerns).

## Decision Points

### Mode Selection
```
IF $ARGUMENTS contains "mode:drill" OR upstream = challenge-generate:
  -> DRILL MODE
     - Load challenge_spec (IC-04) for trap-aware validation
     - Severity response: educational (explain which rule, why it matters)
     - Partial recovery: NOT attempted (trainee must learn from failure)
     - HITL flag: NOT applicable
     - Downstream: render-evaluate (drill) -> golden-correct -> progress-track

ELIF $ARGUMENTS contains "mode:qc" OR upstream = image-preprocess:
  -> PRODUCTION QC MODE
     - Load preprocessed_input (IC-13) for backslash depth + artifact context
     - Severity response: binary PASS/FAIL for submission acceptance
     - Partial recovery: ATTEMPTED when parse fails (production throughput)
     - HITL flag: REQUIRED when confidence < 0.8
     - Downstream: render-evaluate (qc) -> qc-report -> qc-metrics

ELSE:
  -> ABORT: mode parameter required. Cannot validate without mode context.
```

### Parse Success vs Failure (Both Modes)
```
IF JSON.parse(input) succeeds:
  -> Extract "text" field value
  -> Proceed to escape rule compliance (R1-R5)
  -> Record char positions for all escape instances
ELIF JSON.parse(input) fails:
  -> Locate failure point (char_start, char_end)
  -> Classify error type (FATAL)
  -> IF production mode: attempt partial recovery (REQ-JV-07)
  -> IF drill mode: DO NOT recover (learning value in seeing raw failure)
  -> Route raw input to render-evaluate for crash simulation
```

### Partial Recovery Decision (Production Only)
```
IF mode == production AND json_parseable == false:
  -> Attempt text extraction from malformed JSON:
     1. Regex: extract value between "text"\s*:\s*" and final "
     2. Heuristic: find longest quoted string in input
     3. Fallback: strip JSON wrapper chars, treat remainder as text
  -> Set confidence based on method (regex: 0.7, heuristic: 0.5, fallback: 0.3)
  -> IF confidence < 0.8: set hitl_required = true (REQ-JV-08)
```

### Backslash Depth Validation (REQ-JV-04)
```
IF mode == production AND preprocessed_input.backslash_depth exists:
  -> Compare current_depth vs target_depth from IC-13
  -> IF needs_escaping == true:
     Apply depth_map transformations before R1-R5 compliance check
     Log normalization suggestions per-command
  -> IF depth mismatch detected post-normalization:
     Severity: FATAL (structural integrity compromised)
```

### HITL Threshold Decision (REQ-JV-08)
```
IF mode == production:
  -> Calculate overall confidence from:
     - Parse confidence (1.0 if parseable, recovery confidence if partial)
     - Escape compliance confidence (pass_count / total_instances)
     - Source confidence (from IC-13 preprocessed_input.confidence)
  -> IF overall confidence < 0.8:
     Set hitl_required = true
     Set hitl_reason with specific low-confidence dimensions
```

### Escape Rule Severity (3-Tier: REQ-JV-02)
| Rule | Violation | Severity | Recoverable |
|------|-----------|----------|-------------|
| R1: Backslash double-escape | `\frac` instead of `\\frac` | FATAL | No -- parser sees escape sequence |
| R2: Quote escape | Unescaped `"` inside text value | FATAL | No -- breaks string boundary |
| R3: Newline (enhanced) | Literal newline in string | FATAL | No -- JSONL is single-line |
| R3+: `\\n` vs `\\\\n` | Wrong escape depth for newline | WARN | Yes -- parses but semantics wrong |
| R3+: double `\\n\\n` | Consecutive newline pattern | INFO | Yes -- check intentionality |
| R4: Align row break | `\\` instead of `\\\\` | WARN | Yes -- parses but renders wrong |
| R5: Brace layer | `\{` ambiguous in JSON context | FATAL/WARN | FATAL if parser confused, else WARN |

## Methodology

### 1. Mode Selection and Input Loading
Determine execution mode and load mode-specific input.

**Drill mode**: Read challenge_spec (IC-04 schema). Extract `expected_structure`, `trap_list`, `escape_rules_tested`. The trap_list maps to specific R1-R5 rules with `severity_if_failed` for educational feedback.

**Production QC mode**: Read preprocessed_input (IC-13 schema). Extract `latex_content`, `backslash_depth`, `flagged_artifacts`, `quality_score`. If `backslash_depth.needs_escaping`, apply depth_map normalization before validation.

**Both modes**: Record `mode` field for propagation through validation_result (IC-07).

### 2. JSON Parse with Char-Level Positioning (REQ-JV-03)
Simulate `JSON.parse()` on raw input. For every finding, record `char_start` and `char_end`.

**On parse success**: Extract `"text"` field value. Verify top-level object has expected keys (from IC-04 `top_level_keys` in drill mode, or standard `["text"]` in production mode).

**On parse failure**: Walk string character-by-character tracking state machine (`OUTSIDE_STRING`, `INSIDE_STRING`, `ESCAPE_SEQUENCE`). Record exact failure point with 10-char context window before and after. Classify error_type per IC-07 enum: `unterminated_string`, `unexpected_token`, `invalid_escape`, `missing_key`, `missing_value`, `trailing_comma`, `missing_wrapper`.

**Production partial recovery** (REQ-JV-07): If parse fails and mode is production, attempt recovery using the 3-method cascade from Decision Points. Set `partial_recovery.recovered`, `recovered_text`, `confidence`, `recovery_method` in output.

### 3. Backslash Depth Tracking (REQ-JV-04)
For each LaTeX command in the input, compute current escape depth.

**Depth levels**: 0 = raw LaTeX (`\frac`), 1 = LaTeX in string (`\\frac`), 2 = JSONL (`\\\\frac`).

**Production mode with IC-13 depth_map**: Compare each command's actual depth against `target_escaping`. Log mismatches with normalization suggestions: `{command, current_depth, target_depth, suggestion}`.

**Drill mode**: Infer expected depth from context (JSONL target = depth 2). Flag any command not at depth 2 as escape violation under the relevant R1-R5 rule.

### 4. R1-R5 Escape Rule Compliance with R3 Enhancement (REQ-JV-05, REQ-JV-06)
Scan input string (pre-parse form) for each rule. Record per-instance: `{position, char_start, char_end, input_fragment, expected, verdict, severity}`.

**R1-R2, R4-R5**: Standard escape checks (see Severity table above).

**R3 Enhanced Newline Analysis** (REQ-JV-06):
- `\n` (2 chars in source) = JSON newline escape -> PASS (intentional line break in rendered output)
- `\\n` (3 chars in source) = literal backslash-n in LaTeX -> check: is this intended? WARN if inside math mode (where `\n` has no meaning)
- `\\\\n` (4 chars in source) = escaped backslash + n -> likely depth error, WARN
- Literal newline (0x0A in source) = FATAL (breaks JSONL single-line rule)
- Double `\n\n` pattern = INFO (consecutive newlines, verify paragraph break intentionality)
- Double `\\n\\n` = WARN (consecutive literal `\n` in LaTeX, unusual)

**String boundary analysis** (REQ-JV-05): Track quote state transitions. For each `"` in input, classify as: JSON structural (object/key delimiter), escaped content (`\"`), or boundary violation (unescaped within string). Report boundary violations with char positions.

### 5. Produce Mode-Specific Output
Generate validation_result conforming to IC-07 schema.

**Drill mode output**: Educational verdict table with trap mapping.
- Map each finding to challenge_spec.trap_list entries where applicable
- For each FAIL: explain the rule, show the correct form, reference the trap
- Severity uses educational scale: FATAL (must fix), WARN (should fix), INFO (note)
- `hitl_required`: always false in drill mode

**Production QC mode output**: Binary verdict with auto-fix suggestions.
- Overall: PASS (zero FATAL + zero FAIL) or FAIL (any FATAL or FAIL present)
- For each FAIL: provide auto-fix suggestion (corrected fragment)
- Include partial_recovery results if parse failed
- Set `hitl_required` based on confidence threshold (< 0.8)
- Include `file_id` from IC-13 for batch traceability

## Failure Handling

### Parse Failure with Recovery (Production, REQ-JV-07)
- **Cause**: Worker/OCR output is malformed JSON
- **Action**: Attempt 3-method partial recovery cascade. Set recovery confidence.
- **Route**: render-evaluate with `partial_recovery` object. If confidence < 0.8: HITL queue.

### HITL Queue Routing (Production, REQ-JV-08)
- **Cause**: Overall validation confidence below 0.8 threshold
- **Action**: Set `hitl_required: true` with `hitl_reason`. Include all findings.
- **Route**: render-evaluate proceeds with HITL annotation. qc-report flags for human review.

### Backslash Depth Mismatch (REQ-JV-04)
- **Cause**: IC-13 `backslash_depth.current_depth` != expected for JSONL (depth 2)
- **Action**: Apply normalization from depth_map. If normalization fails: FATAL error.
- **Route**: render-evaluate with `backslash_depth_normalized: true/false` flag.

### Mode Propagation Error
- **Cause**: No mode parameter in $ARGUMENTS and upstream skill not identifiable
- **Action**: ABORT validation. Report: "Mode parameter required (drill or production)."
- **Route**: Return to Lead for mode clarification. Do not guess mode.

### Malformed Input (Not JSON at All)
- **Cause**: Raw LaTeX without JSON wrapper (drill: trainee error, production: preprocessing failure)
- **Drill action**: Report FATAL with educational hint about JSON wrapper structure.
- **Production action**: Attempt partial recovery, then HITL if low confidence.
- **Route**: golden-correct (drill) or qc-report with HITL flag (production).

### Multiple Errors Cascade
- **Cause**: First error makes subsequent analysis unreliable
- **Action**: Report first FATAL, continue best-effort for remaining rules with caveat.
- **Route**: render-evaluate with `cascade_warning: true` flag.

## Anti-Patterns

### DO NOT: Attempt Partial Recovery in Drill Mode
Drill mode exists to teach. If the trainee's JSON is broken, they must see the raw failure and learn to fix it. Recovery undermines the pedagogical purpose.

### DO NOT: Skip HITL Flag in Production Mode
Every production validation must compute confidence and set `hitl_required` accordingly. Skipping HITL on low-confidence results risks bad data entering the pipeline.

### DO NOT: Validate Without Mode Parameter
Mode determines severity semantics, recovery behavior, downstream routing, and HITL applicability. Guessing mode produces incorrect output for the pipeline it enters.

### DO NOT: Accept Input That "Looks Close"
JSONL validation is binary at the parse layer: it parses or it doesn't. No partial credit. (Partial recovery in production is a separate post-failure step, not leniency.)

### DO NOT: Fix Errors Silently
Every error must be explicitly reported with char-level evidence (char_start, char_end). In drill mode the trainee must see exact failure locations. In production mode the auto-fix must be traceable.

### DO NOT: Validate LaTeX Syntax Here
This skill checks JSONL structure only. LaTeX validity is latex-parse's responsibility. Boundary: jsonl-validate handles everything outside the rendered content; latex-parse handles everything inside.

### DO NOT: Skip R4/R5 When Parse Succeeds
Valid JSON can still have incorrect escape patterns that produce wrong LaTeX rendering. R1-R5 compliance check runs on every successful parse, every mode.

## Transitions

### Receives From
| Source Skill | Data Expected | Key Fields (IC ref) |
|-------------|---------------|---------------------|
| challenge-generate | Challenge specification | `challenge_spec.{challenge_id, mode, expected_structure, trap_list, escape_rules_tested}` (IC-04) |
| image-preprocess | Preprocessed OCR/worker input | `preprocessed_input.{file_id, mode, latex_content, backslash_depth, flagged_artifacts, confidence}` (IC-13) |
| User (drill) | Raw JSONL string | Single-line text input (direct submission) |

### Sends To
| Target Skill | Data Produced | Key Fields (IC ref) | Trigger |
|-------------|---------------|---------------------|---------|
| render-evaluate | Full validation result | `validation_result.{mode, json_parseable, escape_verdicts, overall_severity, partial_recovery, hitl_required, confidence}` (IC-07) | Always |
| golden-correct | Error list (drill) | Error positions + trap mapping + educational hints | Drill mode, on any FAIL |
| qc-report | Binary verdict (production) | PASS/FAIL + auto-fix suggestions + HITL flag | Production mode |
| latex-parse | Extracted text content | Post-unescape text field value | On successful parse (both modes) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Parse failure (drill) | render-evaluate crash sim + golden-correct | Error position, reason, educational hint |
| Parse failure (production) | render-evaluate + HITL queue | Partial recovery result + confidence |
| Mode missing | Lead (abort) | Error: mode parameter required |
| Depth mismatch | render-evaluate | Normalization result + warnings |

## Quality Gate
- Every R1-R5 rule explicitly checked and reported with per-instance char positions
- Mode field present in output and consistent with input mode
- 3-tier severity (FATAL/WARN/INFO) correctly applied per rule table
- R3 enhanced: `\n` vs `\\n` vs `\\\\n` vs literal newline all distinguished
- Backslash depth tracked and normalization applied when IC-13 provides depth_map
- HITL flag set correctly: always false in drill, threshold-based in production
- Partial recovery attempted only in production mode, never in drill
- validation_result conforms to IC-07 schema (all REQUIRED fields present)
- Confidence computed and within 0.0-1.0 range

## Output

### L1 (IC-07 validation_result schema)
```yaml
domain: drill|production
skill: jsonl-validate
mode: drill|production
status: PASS|FAIL
challenge_id: string          # from IC-04 (drill) or generated (production)
file_id: string|null          # from IC-13 (production only)
json_parseable: true|false
error_position: null|N        # char position of parse failure
overall_severity: FATAL|FAIL|WARN|INFO|PASS
escape_verdicts:
  R1_backslash: PASS|FAIL|N/A
  R2_quotes: PASS|FAIL|N/A
  R3_newlines: PASS|FAIL|N/A
  R4_row_breaks: PASS|FAIL|N/A
  R5_braces: PASS|FAIL|N/A
fatal_count: 0
warning_count: 0
info_count: 0
partial_recovery: null|{recovered: bool, confidence: float}
hitl_required: false|true
confidence: 0.0-1.0
```

### L2 — Drill Mode
- JSON parse result (success/failure with char position + 10-char context)
- Trap mapping table: finding -> challenge_spec.trap_list entry
- Per-instance escape verdict table with educational explanations
- Backslash depth analysis per LaTeX command
- R3 enhanced newline classification table

### L2 — Production QC Mode
- JSON parse result (success/failure with char position + error_type)
- Partial recovery result (if attempted): method, recovered_text, confidence
- Per-instance escape verdict table with auto-fix suggestions
- Backslash depth normalization log (from IC-13 depth_map)
- HITL decision rationale (confidence breakdown by dimension)
- R3 enhanced newline classification table
