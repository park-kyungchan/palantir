---
name: render-evaluate
description: |
  [D1·Drill·RenderEval] Simulates rendering of trainee's JSONL/LaTeX submission and compares against target. Visual diff of correct vs incorrect elements, crash scenarios for FATAL errors.

  WHEN: After jsonl-validate AND latex-parse complete. Fourth in D1 drill cycle.
  DOMAIN: drill (skill 4 of 5). Sequential: jsonl-validate ∥ latex-parse -> render-evaluate -> golden-correct.
  INPUT_FROM: jsonl-validate (parse result + escape verdicts), latex-parse (syntax verdicts), challenge-generate (target rendering + golden answer).
  OUTPUT_TO: golden-correct (rendering diff), progress-track (per-trap pass/fail).

  METHODOLOGY: (1) Merge jsonl-validate and latex-parse results, (2) Simulate rendering path (parse → LaTeX → KaTeX), (3) Describe visual output per segment, (4) Compare against target, (5) Produce rendering diff with pass/fail per element.
  OUTPUT_FORMAT: L1 YAML rendering score + verdicts, L2 rendering simulation with visual descriptions.
user-invocable: false
disable-model-invocation: false
---

# Drill — Render Evaluate

## Execution Model
- **All levels**: Lead-direct. Rendering simulation is descriptive analysis.
- Merges outputs from two parallel upstream skills.
- This is the "compiler output" phase — shows what the trainee's code actually produces.

## Decision Points

### Rendering Path Determination
```
IF jsonl-validate.status == FAIL (JSON parse error):
  -> CRASH SIMULATION: Describe what happens when parser encounters the error
  -> "Your JSON fails at character N. Nothing renders. The entire string is rejected."
  -> Skip LaTeX rendering (no content to render)
  -> Score: 0/N elements

ELIF jsonl-validate.status == PASS AND latex-parse.status == FAIL:
  -> PARTIAL RENDER: JSON parses but LaTeX has errors
  -> Describe which parts render and which break
  -> "The fraction renders correctly, but the missing \right causes all subsequent math to display as raw text."

ELIF both PASS:
  -> FULL RENDER: Describe complete visual output
  -> Compare element-by-element against target
```

### Comparison Granularity
| Element Type | Comparison Method | Tolerance |
|-------------|-------------------|-----------|
| Math expressions | Exact structural match | None — must be identical |
| Text content | Exact string match | Whitespace normalization allowed |
| Spacing (`\,`, `\;`) | Presence check | Missing = WARN, wrong type = WARN |
| Auto-sizing | Correct usage check | Missing = FAIL (visual impact) |
| Alignment (`&`) | Column alignment match | Off by one `&` = FAIL |
| Row breaks (`\\`) | Row count match | Missing row = FAIL |

### Visual Description Style
Describe rendering as if narrating to a blind person:
- "The fraction appears with a horizontal line, numerator x² above, denominator 2x below"
- "The curly brace stretches from the first case to the last, spanning all three lines"
- "The text 'if' appears in upright roman font, separated from the math by thin spaces"

Do NOT use LaTeX code in rendering descriptions. Use visual language only.

## Methodology

### 1. Merge Upstream Results
Combine jsonl-validate L1 and latex-parse L1 into unified analysis:

```yaml
merged:
  json_valid: true|false
  escape_issues: [list from jsonl-validate]
  syntax_issues: [list from latex-parse]
  total_issues: N
  severity_max: FATAL|FAIL|WARN|PASS
```

### 2. Simulate Rendering Path
Walk through the rendering pipeline:

**Stage A: JSON → String**
- If FATAL escape error: describe how parser fails
- If PASS: describe extracted string content

**Stage B: String → LaTeX Tokens**
- If operator error: describe italic text instead of upright command
- If grouping error: describe wrong superscript/subscript capture

**Stage C: LaTeX → Visual Layout**
- If environment error: describe broken alignment or missing rows
- If sizing error: describe too-small parentheses around tall content
- If semantic error: describe missing thin space, wrong set notation

### 3. Describe Visual Output Per Segment
For each tokenized segment from latex-parse:

```
Segment: "정의: $f(x) = \\frac{x^2}{2}$"
Rendering: The text "정의:" appears in normal font, followed by inline math
           where f(x) equals a fraction with x-squared above a horizontal
           line and 2 below. The fraction is standard inline size.
Verdict: ✅ PASS — matches target rendering
```

### 4. Compare Against Target
Element-by-element comparison with target rendering from challenge-generate:

| Element | Target | Actual | Match |
|---------|--------|--------|-------|
| Text prefix | "정의:" | "정의:" | ✅ |
| Function def | f(x) = fraction | f(x) = fraction | ✅ |
| Auto-sizing | Tall parens around cases | Small parens (no \left) | ❌ |
| Row breaks | 3 rows in cases | 2 rows (missing \\\\) | ❌ |
| Text spacing | "if" with spaces | "if" cramped | ⚠️ |

### 5. Produce Rendering Score
Calculate overall and per-element scores:

```yaml
score:
  total: 7/10  # elements matching
  by_category:
    structure: 3/3
    escaping: 2/2
    formatting: 1/3
    semantics: 1/2
  trap_results:
    ESCAPE_backslash: PASS
    TEXT_spacing: FAIL
    SIZING_left_right: FAIL
```

## Failure Handling

### Conflicting Upstream Results
- **Cause**: jsonl-validate says PASS but latex-parse found issues that suggest escape problems
- **Action**: Re-examine the boundary. Flag as "cross-layer issue" and explain both interpretations.
- **Route**: golden-correct (with cross-layer annotation)

### Target Rendering Ambiguous
- **Cause**: Multiple valid LaTeX representations match the target rendering
- **Action**: If trainee's version renders identically, accept as PASS even if different from golden answer
- **Route**: golden-correct (note alternative valid approach)

## Anti-Patterns

### DO NOT: Just Say "Wrong"
Every rendering mismatch must be described visually. "Your integral sign appears but the dx is crammed against x² with no space, making it look like dx is part of the expression rather than the differential."

### DO NOT: Show Golden Answer Here
This skill describes what the trainee's code produces. The correction comes from golden-correct. Separation of concerns.

### DO NOT: Award Partial Credit for FATAL Errors
If JSON doesn't parse, the score is 0 regardless of how good the LaTeX might have been. This teaches the trainee that JSONL validity is a prerequisite.

### DO NOT: Skip Visual Description for PASS Segments
Even correct segments should be described. This reinforces correct mental models and helps the trainee verify their understanding.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| jsonl-validate | Parse result, escape verdicts | YAML L1 |
| latex-parse | Syntax verdicts per construct | YAML L1 |
| challenge-generate | Target rendering, golden answer | Challenge spec (hidden) |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| golden-correct | Rendering diff, per-element verdicts | Always |
| progress-track | Trap results (pass/fail per trap type) | Always |

## Quality Gate
- Every segment has a visual rendering description
- FATAL errors produce crash simulation narrative
- Element-by-element comparison against target
- Score is quantified (N/M elements)
- Trap results mapped to challenge-generate trap types
- No LaTeX code in visual descriptions (pure visual language)

## Output

### L1
```yaml
domain: drill
skill: render-evaluate
status: PASS|PARTIAL|CRASH
score_total: "7/10"
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
```

### L2
- Rendering simulation narrative (visual descriptions)
- Element-by-element comparison table
- Crash simulation (if applicable)
- Per-trap verdict summary
