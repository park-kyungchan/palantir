---
name: jsonl-validate
description: |
  [D1·Drill·JSONLValidate] Validates JSONL structural integrity. Checks JSON parseability, escape correctness (R1-R5: backslash, quote, newline, row-break, brace), string boundary. Parallel with latex-parse.

  WHEN: After trainee submits JSONL string. Parallel with latex-parse. Second in D1 drill cycle.
  DOMAIN: drill (skill 2 of 5). Parallel: jsonl-validate ∥ latex-parse -> render-evaluate.
  INPUT_FROM: challenge-generate (expected structure), User input (raw JSONL string).
  OUTPUT_TO: render-evaluate (structural verdict + parsed content), golden-correct (error list).

  METHODOLOGY: (1) Attempt JSON.parse on raw input, (2) If fail: locate exact failure point (char position), (3) If pass: extract text field, (4) Check escape rule compliance (5 core rules), (5) Produce segment-by-segment verdict table.
  OUTPUT_FORMAT: L1 YAML parse result + escape verdicts, L2 analysis table with char-level evidence.
user-invocable: false
disable-model-invocation: false
---

# Drill — JSONL Validate

## Execution Model
- **All levels**: Lead-direct. JSONL validation is deterministic and doesn't require agent spawning.
- Character-by-character analysis simulating a JSON parser.
- Always runs parallel with latex-parse (independent concerns).

## Decision Points

### Parse Success vs Failure
```
IF JSON.parse(input) succeeds:
  -> Extract "text" field value
  -> Proceed to escape rule compliance check
  -> Pass extracted content to latex-parse (if not already running)
ELIF JSON.parse(input) fails:
  -> Locate failure point (character position)
  -> Classify error type (FATAL category)
  -> DO NOT proceed to escape compliance (structure broken)
  -> Still pass raw input to render-evaluate for "crash simulation"
```

### Escape Rule Severity Classification
| Rule | Violation | Severity | Recoverable |
|------|-----------|----------|-------------|
| R1: Backslash double-escape | `\frac` instead of `\\frac` | FATAL | No — parser sees escape sequence |
| R2: Quote escape | `"text"` instead of `\"text\"` | FATAL | No — breaks string boundary |
| R3: Newline handling | Literal newline in string | FATAL | No — JSONL is single-line |
| R4: Align row break | `\\` instead of `\\\\` | RENDER | Yes — parses but renders wrong |
| R5: Brace layer | `\{` instead of `\\{` inside JSON | DEPENDS | FATAL if parser confused, else RENDER |

## Methodology

### 1. Attempt JSON Parse
Simulate `JSON.parse()` on the raw input string.
Report: `{parseable: true/false, error_position: N, error_reason: "..."}`.

### 2. Locate Failure Point (if parse fails)
Walk the string character by character:
- Track state: `OUTSIDE_STRING`, `INSIDE_STRING`, `ESCAPE_SEQUENCE`
- Mark exact character where state machine fails
- Report the 10 characters before and after the failure point for context

### 3. Extract Text Field (if parse succeeds)
After successful parse:
- Verify top-level object has `"text"` key
- Extract the raw string value (post-JSON-unescape)
- This is the "LaTeX+text content" that will be rendered

### 4. Check Escape Rule Compliance
For each of the 5 core escape rules, scan the input string (pre-parse form):

**R1: Backslash Double-Escape**
```
Pattern: Look for single backslash followed by LaTeX command
\frac → FAIL (should be \\frac)
\\frac → PASS
\\\\ → PASS (escaped backslash = literal \\)
```

**R2: Quote Escape**
```
Pattern: Look for unescaped " inside the text value
"definition" → FAIL (breaks JSON)
\"definition\" → PASS
```

**R3: Newline Handling**
```
Pattern: Check for literal line breaks inside the JSON string
Actual newline character → FAIL (JSONL = one line)
\n (two chars) → PASS (JSON newline escape)
\\n (three chars) → PASS (literal \n in LaTeX)
```

**R4: Align Row Break**
```
Pattern: Inside aligned/cases/matrix environments
\\ → might work in JSON but renders as single \
\\\\ → PASS (\\\\  in JSON = \\ in LaTeX = row break)
```

**R5: Brace Escape Layer**
```
Pattern: LaTeX curly braces in JSON context
\{ in JSON → might be interpreted as escape sequence
\\{ in JSON → literal \{ in LaTeX → displays {
\\left\\{ → proper auto-sizing brace
```

### 5. Produce Verdict Table
Generate segment-by-segment analysis:

| Segment | Input | Verdict | Rule | Detail |
|---------|-------|---------|------|--------|
| JSON structure | `{"text":"..."}` | ✅ PASS | - | Valid JSON object |
| Backslash:1 | `\\frac{1}{2}` | ✅ PASS | R1 | Properly double-escaped |
| Quote:1 | `\"definition\"` | ✅ PASS | R2 | Properly escaped |
| Newline:1 | `\n` | ⚠️ CHECK | R3 | Intentional line break? |

## Failure Handling

### Malformed Input (Not Even Close to JSON)
- **Cause**: Trainee submits raw LaTeX without JSON wrapper
- **Action**: Report FATAL with hint: "Input must be a JSON object: `{\"text\": \"...\"}`"
- **Route**: golden-correct (show correct wrapper structure)

### Multiple Errors Cascade
- **Cause**: First error makes subsequent analysis unreliable
- **Action**: Report first FATAL error, note "subsequent analysis may be affected"
- **Route**: render-evaluate (with partial analysis flag)

### Ambiguous Escape (R5 edge case)
- **Cause**: Brace context unclear without full LaTeX parse
- **Action**: Flag as ⚠️ CHECK, defer to latex-parse for definitive verdict
- **Route**: latex-parse result overrides if conflict

## Anti-Patterns

### DO NOT: Accept Input That "Looks Close"
JSONL validation is binary: it parses or it doesn't. No partial credit at the JSON layer.

### DO NOT: Fix Errors Silently
Every error must be explicitly reported with char-level evidence. The trainee must see exactly where the failure occurs.

### DO NOT: Validate LaTeX Syntax Here
This skill checks JSONL structure only. LaTeX validity is latex-parse's responsibility. The boundary is clear: jsonl-validate handles everything outside the rendered content; latex-parse handles everything inside.

### DO NOT: Skip R4/R5 When Parse Succeeds
A string can parse as valid JSON but still have incorrect escape patterns that produce wrong LaTeX. Compliance check happens even on successful parse.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| challenge-generate | Expected structure spec | YAML challenge spec |
| User | Raw JSONL string | Single-line text input |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| render-evaluate | Parse result + extracted text content | Always |
| golden-correct | Error list with positions | Always |
| latex-parse | Extracted text content (if parse succeeded) | On PASS |

### Failure Routes
| Failure | Route | Data |
|---------|-------|------|
| Parse failure | render-evaluate (crash sim) | Error position + reason |
| All PASS | render-evaluate (content) | Clean extracted text |

## Quality Gate
- Every escape rule (R1-R5) explicitly checked and reported
- FATAL errors include exact character position
- Verdict table covers all escape instances in input
- No false positives (valid escaping marked as error)

## Output

### L1
```yaml
domain: drill
skill: jsonl-validate
status: PASS|FAIL
json_parseable: true|false
error_position: null|N
escape_verdicts:
  R1_backslash: PASS|FAIL|N/A
  R2_quotes: PASS|FAIL|N/A
  R3_newlines: PASS|FAIL|N/A
  R4_row_breaks: PASS|FAIL|N/A
  R5_braces: PASS|FAIL|N/A
fatal_count: 0
warning_count: 0
```

### L2
- JSON parse result (success/failure with position)
- Escape rule compliance table (per-instance verdicts)
- Character-level error evidence
- Extracted text content (for downstream skills)
