---
name: latex-parse
description: |
  [D1·Drill·LaTeXParse] Parses and validates LaTeX syntax within extracted JSONL text. Checks grouping scope, operator commands, auto-sizing delimiters, text-mode spacing, environment matching, semantic conventions (dx spacing, set builder notation). Parallel with jsonl-validate.

  WHEN: After trainee submits JSONL string. Parallel with jsonl-validate. Second in D1 drill cycle.
  DOMAIN: drill (skill 3 of 5). Parallel: jsonl-validate ∥ latex-parse -> render-evaluate.
  INPUT_FROM: jsonl-validate (extracted text), challenge-generate (expected constructs), reference-build (command allowlist).
  OUTPUT_TO: render-evaluate (syntax verdicts per construct), golden-correct (LaTeX error list).

  METHODOLOGY: (1) Tokenize into segments (text, inline/display math, environments), (2) Check grouping/scope rules, (3) Validate operator commands vs italic text, (4) Check delimiter sizing (\left/\right), (5) Verify environment matching and semantics.
  OUTPUT_FORMAT: L1 YAML syntax verdict per category, L2 parsing analysis with segment-level evidence.
user-invocable: false
disable-model-invocation: false
---

# Drill — LaTeX Parse

## Execution Model
- **All levels**: Lead-direct. LaTeX parsing is rule-based analysis.
- Operates on the text content AFTER JSONL unescaping (receives from jsonl-validate).
- Parallel with jsonl-validate — each validates its own layer.

## Decision Points

### Input Source
```
IF jsonl-validate PASS:
  -> Use extracted text content (post-JSON-unescape)
ELIF jsonl-validate FAIL (parse error):
  -> Attempt best-effort LaTeX analysis on raw input
  -> Flag all findings as "tentative" (JSONL layer broken)
  -> Still useful for trainee learning
```

### Severity Classification
| Category | Verdict | Description |
|----------|---------|-------------|
| ❌ FAIL | Critical | Renders incorrectly or not at all |
| ⚠️ WARN | Style violation | Renders but violates conventions |
| ✅ PASS | Correct | Matches expected syntax and style |

### Parse Depth by Challenge Level
- **Level 1-2**: Check commands and basic grouping only
- **Level 3**: Add environment matching and text-mode checks
- **Level 4-5**: Full analysis including semantic conventions and nested structure validation

## Methodology

### 1. Tokenize Content into Segments
Split the text content into analyzable segments:

| Segment Type | Delimiter | Example |
|-------------|-----------|---------|
| Plain text | Outside `$...$` | "함수 f를 다음과 같이 정의하자." |
| Inline math | `$...$` | `$f(x) = x^2$` |
| Display math | `$$...$$` | `$$\int_0^1 f(x)\,dx$$` |
| Environment | `\begin{}...\end{}` | `\begin{aligned}...\end{aligned}` |

Track nesting depth. Flag unclosed delimiters.

### 2. Check Grouping/Scope Rules
For every `^` (superscript) and `_` (subscript):
```
Rule: Multi-token arguments MUST be grouped in braces
  x^2      → PASS (single token)
  x^{13}   → PASS (grouped)
  x^13     → FAIL (13 = two tokens, only 1 captured)
  e^{-x^2} → PASS (nested grouping)
  e^-x^2   → FAIL (ambiguous scope)
```

For `\frac`, `\sqrt`, `\binom` and similar 2-argument commands:
```
Rule: Both arguments must be brace-grouped
  \frac{a}{b}   → PASS
  \frac{a}b     → FAIL (second arg not grouped)
  \frac ab      → FAIL (neither arg grouped)
  \sqrt{x}      → PASS
  \sqrt[3]{x}   → PASS (optional arg in brackets)
```

### 3. Validate Operator Commands
Check that mathematical operators use proper LaTeX commands:

| Check | Wrong (italic) | Right (upright) | Rule |
|-------|----------------|-----------------|------|
| Trig | `sin x` | `\sin x` | Standard operators |
| Log | `ln x` | `\ln x` | Standard operators |
| Limits | `lim` | `\lim` | Standard operators |
| Det | `det A` | `\det A` | Standard operators |
| Min/Max | `min` | `\min` | Standard operators |
| Mod | `mod` | `\mod` or `\bmod` | Standard operators |
| Text | `if` | `\text{ if }` | Non-math words |

### 4. Check Delimiter Sizing
For parentheses, brackets, and braces around tall expressions:

```
Rule: Use \left and \right for auto-sizing when content is taller than one line
  (\frac{a}{b})         → WARN (should auto-size)
  \left(\frac{a}{b}\right) → PASS

Rule: \left must pair with \right (or \right.)
  \left( ... \right)    → PASS
  \left( ...            → FAIL (unpaired)
  \left\{ ... \right\}  → PASS (curly braces)
  \left\{ ... \right.   → PASS (invisible right delimiter)

Rule: Curly braces need escape
  \left{ → FAIL (bare { is grouping, not delimiter)
  \left\{ → PASS (escaped { is delimiter)
```

### 5. Verify Environment Matching and Semantics
For `\begin{env}...\end{env}` blocks:

**Matching**: Every `\begin{X}` has a `\end{X}` with same environment name.

**Alignment**: In `aligned`, `cases`, `matrix`:
- `&` marks alignment points
- `\\` marks row breaks
- Each row should have consistent `&` count

**Semantic conventions**:
- `\,` thin space before `dx` in integrals: `\int f(x)\,dx`
- `\middle|` for set builder: `\{x \middle| x > 0\}`
- `\mathbb{}` for number sets: `\mathbb{R}`, not `R` or `\textbf{R}`

## Failure Handling

### Content Has No Math
- **Cause**: Input is pure text, no `$` delimiters
- **Action**: Report as ⚠️ WARN "No math delimiters found"
- **Route**: render-evaluate (text-only rendering check)

### Deeply Nested Structures
- **Cause**: 4+ nesting levels make analysis complex
- **Action**: Analyze outer 3 levels fully, flag inner levels as "deep nesting — verify manually"
- **Route**: render-evaluate (with partial analysis flag)

### jsonl-validate Returned FAIL
- **Cause**: JSON structure broken, extracted content unreliable
- **Action**: Best-effort parse on raw input, all verdicts marked "tentative"
- **Route**: render-evaluate (tentative verdicts)

## Anti-Patterns

### DO NOT: Validate JSONL Escaping Here
LaTeX-parse operates on the UNESCAPED content (after JSON parsing). `\\frac` in JSON becomes `\frac` in LaTeX — this skill sees `\frac` and validates it as LaTeX. Escape validation is jsonl-validate's job.

### DO NOT: Judge Mathematical Correctness
`\frac{0}{0}` is valid LaTeX syntax. Mathematical accuracy is out of scope for this skill.

### DO NOT: Enforce Personal Style Preferences
Only check rules that affect rendering or violate established conventions. `\frac{1}{2}` and `\tfrac{1}{2}` are both valid choices.

### DO NOT: Skip WARN-Level Findings
Style violations (`\sin` vs `sin`) are critical learning points even if they render "close enough."

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| jsonl-validate | Extracted text content | Raw string (post-JSON-unescape) |
| challenge-generate | Expected construct list | YAML construct categories |
| reference-build | Valid command allowlist | YAML command inventory |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| render-evaluate | Syntax verdicts per construct | Always |
| golden-correct | LaTeX error list with positions | Always |

## Quality Gate
- Every math segment tokenized and analyzed
- Grouping rules checked for all `^`, `_`, `\frac`, `\sqrt`
- Operator commands checked against allowlist
- Delimiter pairs all matched (`\left`/`\right` count equal)
- Environment `\begin`/`\end` pairs all matched
- Zero false positives on valid LaTeX

## Output

### L1
```yaml
domain: drill
skill: latex-parse
status: PASS|FAIL|WARN
segment_count: 0
findings:
  FAIL: 0
  WARN: 0
  PASS: 0
categories_checked: [grouping, operators, delimiters, environments, semantics]
```

### L2
- Segment-by-segment parsing analysis table
- Per-category verdict with evidence (input fragment → expected → actual)
- Environment nesting diagram (for Level 4-5)
- Tentative flag if jsonl-validate failed
