---
name: latex-parse
description: |
  Dual-mode LaTeX validation. Drill: FAIL/WARN/PASS against expected_constructs. Production QC: CRITICAL/MAJOR/MINOR against command_allowlist + OCR artifact detection. Parallel with jsonl-validate.

  WHEN: After JSONL submit (drill) or OCR/worker LaTeX extracted (production). Parallel with jsonl-validate.
  CONSUMES: jsonl-validate (extracted text), challenge-generate (IC-05 expected_constructs), reference-build (IC-02 command_allowlist), image-preprocess (flagged_artifacts).
  PRODUCES: IC-08 parse_result (mode-tagged) → render-evaluate, drill errors → golden-correct, production findings → qc-report.
user-invocable: true
disable-model-invocation: true
---

# Shared Validation Core — LaTeX Parse (Dual-Mode)

## Execution Model
- **All tiers**: Lead-direct. LaTeX parsing is deterministic rule-based analysis.
- Operates on text content AFTER JSONL unescaping (receives from jsonl-validate).
- Parallel with jsonl-validate — each validates its own layer independently.
- **Mode** determined at invocation: `$ARGUMENTS` context or upstream skill origin.
  - **Drill mode**: Trainee-submitted LaTeX. Educational severity (FAIL/WARN/PASS). Parse depth varies by difficulty.
  - **Production QC mode**: Worker or OCR-derived LaTeX. Production severity (CRITICAL/MAJOR/MINOR). Always full parse depth.

## Decision Points

### Mode Selection
```
IF $ARGUMENTS contains mode="drill" OR upstream is challenge-generate:
  -> Drill mode. Load expected_constructs (IC-05). Educational severity.
ELIF $ARGUMENTS contains mode="production" OR upstream is image-preprocess:
  -> Production QC mode. Load command_allowlist (IC-02). Production severity.
ELSE:
  -> ERROR: Mode undetermined. Halt and report mode-propagation-error.
```

### Tentative Mode Trigger
```
DRILL:
  IF jsonl-validate status == FAIL:
    -> Set tentative=true, confidence cap at 0.6
    -> Best-effort parse on raw input, all findings marked tentative
    -> Still useful for trainee learning

PRODUCTION:
  IF ocr_confidence < 0.7 (from image-preprocess):
    -> Set tentative=true, confidence cap at 0.5
    -> Cross-reference ALL findings with ocr_confusions list
    -> Set hitl_required=true with reason "low OCR confidence"
  IF jsonl-validate status == FAIL:
    -> Set tentative=true, confidence cap at 0.4
    -> Both structural and content layers unreliable
```

### Parse Depth Selection
```
DRILL (from IC-05 parse_depth or difficulty):
  difficulty 1-2 -> "basic":  commands + grouping only
  difficulty 3   -> "standard": + environments + text-mode checks
  difficulty 4-5 -> "full":  + semantics + nesting + domain rules

PRODUCTION:
  Always "full" — all categories checked, no depth shortcut.
```

### OCR Artifact Detection Threshold
```
PRODUCTION ONLY:
  Load ocr_confusions from reference-build (IC-02 domain):
    e.g., "l" <-> "1", "O" <-> "0", "\ell" <-> "l"
  Load flagged_artifacts from image-preprocess (if available):
    e.g., broken ligatures, partial symbols, noise patterns

  FOR each finding:
    IF finding matches known ocr_confusion pattern:
      -> Reclassify as OCR_ARTIFACT (not author error)
      -> Set severity to MAJOR (not CRITICAL)
      -> Add ocr_confusion_ref to finding
    IF confidence < 0.8 AND finding is ambiguous:
      -> Set hitl_required=true
      -> Add hitl_reason: "ambiguous OCR artifact vs author error"
```

### Severity Classification

**Drill Mode** (educational):
| Verdict | Description | Example |
|---------|-------------|---------|
| FAIL | Renders incorrectly or not at all | Unclosed `\left(` |
| WARN | Renders but violates conventions | `sin x` instead of `\sin x` |
| PASS | Matches expected syntax and style | Correct grouping and commands |

**Production QC Mode** (production):
| Severity | Description | Example |
|----------|-------------|---------|
| CRITICAL | Content loss or corruption | Missing environment `\end{}` |
| MAJOR | Significant rendering error | Wrong operator, OCR artifact |
| MINOR | Style deviation, no content loss | Missing `\,` before `dx` |

### HITL Flag Decision (REQ-LP-07)
```
Set hitl_required=true when ANY of:
  - confidence < 0.7 (tentative parse unreliable)
  - OCR artifact ambiguity (cannot distinguish OCR vs author error)
  - Domain semantic rule produces conflicting signals
  - Nesting depth >= 4 with unresolved grouping
Include hitl_reason string explaining the trigger.
```

## Methodology

### 1. Detect Mode and Load Context
Determine operating mode from invocation context:
- **Drill**: Load `expected_constructs` from challenge-generate (IC-05). Extract `parse_depth`, `constructs[]`, `domain_rules[]`.
- **Production**: Load `command_allowlist` from reference-build (IC-02). Extract `valid_commands[]`, `operators[]`, `environments[]`, `domain_semantics[]`. Load `flagged_artifacts` from image-preprocess if available.
- Validate mode field consistency. If IC-02 `mode` mismatches current mode, override and log warning.

### 2. Tokenize Content into Segments
Split text content into analyzable segments:

| Segment Type | Delimiter | Example |
|-------------|-----------|---------|
| plain_text | Outside `$...$` | "f(x)를 다음과 같이 정의하자." |
| inline_math | `$...$` | `$f(x) = x^2$` |
| display_math | `$$...$$` | `$$\int_0^1 f(x)\,dx$$` |
| environment | `\begin{}...\end{}` | `\begin{aligned}...\end{aligned}` |

Track nesting depth. Flag unclosed delimiters immediately. Assign each segment a `segment_id` (SEG-001, SEG-002, ...) with `start_pos` and `end_pos` for IC-08 output.

### 3. Apply Rule Checks Per Segment
For each segment, apply checks based on parse depth. Each finding records: `finding_id`, `category`, `severity` (mode-appropriate), `position`, `input_fragment`, `expected`, and optional `rule_reference`.

**Grouping/Scope** (all depths):
- Multi-token `^`/`_` arguments must be braced: `x^{13}` not `x^13` (REQ-LP-03)
- `\frac`, `\sqrt`, `\binom` arguments must be brace-grouped
- Vector notation consistency: if `\vec{F}` used, all vectors must use `\vec{}` (REQ-LP-02)

**Operator Commands** (all depths):
- Math operators must use commands: `\sin`, `\ln`, `\lim`, `\det`, `\min`, `\max`, `\mod`
- Non-math text in math mode must use `\text{}` with proper spacing

**Delimiter Sizing** (standard+ depth):
- `\left`/`\right` for auto-sizing around tall expressions
- All `\left` must pair with `\right` (or `\right.`)
- Curly braces need escape: `\left\{` not `\left{`

**Environment Matching** (standard+ depth):
- Every `\begin{X}` has matching `\end{X}`
- Alignment `&` count consistent per row in `aligned`, `cases`, `matrix`
- `\\` row breaks present where expected

**Semantic Conventions** (full depth only):
- `\,` thin space before `dx` in integrals
- `\middle|` for set builder notation
- `\mathbb{}` for number sets
- Domain-specific rules from IC-02 `domain_semantics[]` or IC-05 `domain_rules[]` (REQ-LP-04)

### 4. OCR Artifact Cross-Reference (Production Only)
For production mode, cross-reference findings against OCR artifact sources (REQ-LP-06):
- Match each finding against `ocr_confusions` from reference-build (IC-02)
- Match against `flagged_artifacts` from image-preprocess
- If a finding matches a known OCR confusion pattern:
  - Tag finding with `ocr_artifact: true` and `ocr_confusion_ref`
  - Downgrade severity from CRITICAL to MAJOR (OCR error, not author error)
  - If ambiguous (could be either): set `hitl_required=true`

### 5. Assemble parse_result Output
Build IC-08 compliant `parse_result`:
- Set `tentative` flag based on Decision Points logic (REQ-LP-05)
- Populate `segments[]` with all tokenized segments and their findings
- Calculate `summary`: `total_segments`, `status`, `finding_counts`, `categories_checked`, `worst_severity`
- Set `confidence` (0.0-1.0): reduce for tentative, low OCR confidence, deep nesting
- Set `hitl_required` and `hitl_reason` per HITL decision logic (REQ-LP-07)
- Tag output with `mode` for downstream routing differentiation

## Failure Handling

### Tentative Mode Degradation
- **Cause**: jsonl-validate FAIL (drill) or OCR confidence < threshold (production)
- **Action**: Best-effort parse, all findings marked tentative, confidence capped
- **Route**: render-evaluate (with tentative flag — merges tentative verdicts accordingly)

### OCR Artifact Ambiguity
- **Cause**: Finding matches OCR confusion pattern but could also be author error
- **Action**: Tag as ambiguous, set `hitl_required=true`, include both interpretations in L2
- **Route**: render-evaluate (HITL flag propagates to qc-report for human review)

### Domain Rule Missing
- **Cause**: IC-02 `domain_semantics` empty or IC-05 `domain_rules` all inactive
- **Action**: Skip semantic checks, proceed with structural-only parse. Log warning.
- **Route**: render-evaluate (structural parse only, `categories_checked` excludes "semantics")

### Content Has No Math
- **Cause**: Input is pure text, no `$` delimiters found
- **Action**: Report as WARN (drill) or MINOR (production) "No math delimiters found"
- **Route**: render-evaluate (text-only rendering check)

### Deeply Nested Structures
- **Cause**: 4+ nesting levels
- **Action**: Analyze outer 3 levels fully, flag inner levels as "deep nesting — verify manually"
- **Route**: render-evaluate (with partial analysis flag, `hitl_required=true` if nesting >= 4)

### Mode Propagation Error
- **Cause**: Neither $ARGUMENTS nor upstream context provides mode
- **Action**: HALT. Cannot proceed without mode — severity system is mode-dependent.
- **Route**: Report error to Lead. Do not guess mode.

## Anti-Patterns

### DO NOT: Apply Drill Severity in Production Mode
Production uses CRITICAL/MAJOR/MINOR, not FAIL/WARN/PASS. Mixing severity vocabularies corrupts downstream qc-report aggregation and metric tracking.

### DO NOT: Skip Tentative Flag When Upstream FAIL
If jsonl-validate reports FAIL or OCR confidence is below threshold, tentative MUST be set. Omitting it causes render-evaluate to treat unreliable findings as definitive.

### DO NOT: Parse Without Domain Context
Always load IC-02 (production) or IC-05 (drill) domain rules before semantic analysis. Parsing without domain context produces generic findings that miss domain-specific conventions.

### DO NOT: Validate JSONL Escaping Here
latex-parse operates on UNESCAPED content (after JSON parsing). `\\frac` in JSON becomes `\frac` in LaTeX. Escape validation is jsonl-validate's responsibility.

### DO NOT: Judge Mathematical Correctness
`\frac{0}{0}` is valid LaTeX syntax. Mathematical accuracy is out of scope for this skill.

### DO NOT: Enforce Personal Style Preferences
Only check rules that affect rendering or violate established conventions. `\frac{1}{2}` and `\tfrac{1}{2}` are both valid choices unless domain rules specify otherwise.

### DO NOT: Skip WARN/MINOR-Level Findings
Style violations are critical learning points (drill) or fidelity concerns (production). Report all findings regardless of severity.

## Transitions

### Receives From (Interface Contracts)
| Source Skill | Data Expected | Interface | Format |
|-------------|---------------|-----------|--------|
| jsonl-validate | Extracted text content | parallel | Raw string (post-JSON-unescape) |
| challenge-generate | Expected construct list + parse depth + domain rules | IC-05 | YAML `expected_constructs` schema |
| reference-build | Command allowlist + domain semantics + OCR confusions | IC-02 | YAML `command_allowlist` schema |
| image-preprocess | Flagged OCR artifacts | production | YAML `flagged_artifacts` list |

### Sends To
| Target Skill | Data Produced | Interface | Trigger |
|-------------|---------------|-----------|---------|
| render-evaluate | parse_result (segments + findings + summary) | IC-08 | Always (both modes) |
| golden-correct | LaTeX error list with positions | drill | Drill mode only |
| qc-report | Production findings with severity | production | Production mode only |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Mode undetermined | Lead (error) | mode-propagation-error flag |
| Domain rules missing | render-evaluate (degraded) | structural-only parse, semantics excluded |
| Content unparseable | render-evaluate | empty segments, tentative=true, confidence=0.0 |

## Quality Gate
- Every math segment tokenized and assigned segment_id with positions
- Grouping rules checked for all `^`, `_`, `\frac`, `\sqrt` (REQ-LP-03)
- Vector notation consistency verified across all segments (REQ-LP-02)
- Operator commands checked against allowlist (IC-02 or built-in)
- Delimiter pairs all matched (`\left`/`\right` count equal)
- Environment `\begin`/`\end` pairs all matched
- Domain semantic rules applied per IC-02/IC-05 when available (REQ-LP-04)
- Mode-appropriate severity vocabulary used (drill vs production) (REQ-LP-01)
- Tentative flag set when upstream FAIL or OCR confidence low (REQ-LP-05)
- OCR artifacts cross-referenced in production mode (REQ-LP-06)
- HITL flag set for uncertain parses with reason string (REQ-LP-07)
- `summary` counts match actual segment finding counts
- Zero false positives on valid LaTeX

## Output

### L1
```yaml
domain: drill|production
skill: latex-parse
mode: drill|production
status: PASS|FAIL|WARN          # drill
# OR
status: PASS|CRITICAL|MAJOR     # production
tentative: false
confidence: 0.92
hitl_required: false
segment_count: 0
findings:
  FAIL: 0                       # drill severity
  WARN: 0
  PASS: 0
  # OR
  CRITICAL: 0                   # production severity
  MAJOR: 0
  MINOR: 0
categories_checked: [grouping, operators, delimiters, environments, semantics, text_mode]
ocr_artifacts_detected: 0       # production only
```

### L2
- Mode declaration (drill or production) with input source identification
- Segment-by-segment parsing analysis table with segment_id, type, position range
- Per-finding detail: category, severity, input_fragment, expected, rule_reference
- Domain semantic rule application results (which rules checked, which triggered)
- OCR artifact cross-reference results (production: which findings reclassified)
- Vector notation consistency report across segments (REQ-LP-02)
- Environment nesting diagram (for full parse depth)
- Tentative flag explanation if set (upstream cause and confidence impact)
- HITL recommendation with reason if hitl_required=true
- Summary: total segments, finding counts by severity, confidence score
