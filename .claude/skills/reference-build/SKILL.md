---
name: reference-build
description: |
  [D0·Foundation·Reference] LaTeX/JSONL command reference builder. Generates tiered command tables (Tier1: daily, Tier2: frequent, Tier3: rare) with syntax, common errors, JSONL escape patterns.

  WHEN: First session start or reference refresh request. No prerequisites. Foundation skill.
  DOMAIN: foundation (skill 1 of 1). Independent. Feeds challenge-generate (command pool), latex-parse (command allowlist), golden-correct (rule reference).
  INPUT_FROM: User request (topic scope), progress-track (weak areas for targeted reference).
  OUTPUT_TO: challenge-generate (command pool), latex-parse (command allowlist), golden-correct (canonical syntax).

  METHODOLOGY: (1) Identify math domain scope (calculus, linear algebra, set theory, logic), (2) Build tiered command table: LaTeX + meaning + JSONL-escaped form + common errors, (3) Generate escape rule quick-reference, (4) Create trap catalog (confused patterns), (5) Output as YAML + markdown.
  OUTPUT_FORMAT: L1 YAML command inventory by tier, L2 reference with examples and error patterns.
user-invocable: true
disable-model-invocation: false
argument-hint: "[math-domain]"
---

# Foundation — Reference Build

## Execution Model
- **BASIC**: Single-domain reference (e.g., calculus only). Lead-direct generation.
- **STANDARD**: Multi-domain reference (2-3 domains). Structured table generation.
- **COMPREHENSIVE**: Full-scope reference (all 7 domains). Includes cross-domain patterns.

## Decision Points

### Domain Scope Selection
User specifies or Lead infers from progress-track data:

| Domain | Key Commands | Trap Density |
|--------|-------------|--------------|
| Functions/Limits | `\lim`, `\to`, `\infty`, `\epsilon` | Medium |
| Differentiation | `\frac{d}{dx}`, `\partial`, `\nabla` | High (nested fracs) |
| Integration | `\int`, `\iint`, `\oint`, `\,dx` | High (dx spacing, bounds) |
| Sequences/Series | `\sum`, `\prod`, `\cdots`, `\binom` | Medium |
| Probability/Stats | `\mathbb{P}`, `\sigma`, `\mu`, `\bar{x}` | Low |
| Geometry/Vectors | `\vec`, `\overrightarrow`, `\angle`, `\perp` | Medium |
| Matrices/Linear | `\begin{pmatrix}`, `\det`, `\text{tr}` | Very High (environments) |

### Tier Classification
- **Tier 1 (Daily)**: Commands appearing in >70% of 수리논술 problems. Must be memorized.
- **Tier 2 (Frequent)**: Commands appearing in 30-70%. Should recognize and write correctly.
- **Tier 3 (Rare)**: Commands appearing in <30%. Should recognize; lookup acceptable.

### When to Rebuild vs Incremental Update
```
IF first session OR no existing reference:
  -> Full build (all tiers, all requested domains)
ELIF progress-track reports new weak areas:
  -> Incremental: add weak-area commands to existing reference
ELIF user requests specific domain:
  -> Targeted: build single-domain reference
```

## Methodology

### 1. Identify Math Domain Scope
Parse user request or progress-track output for domain keywords.
Default to full scope if unspecified and first session.

### 2. Build Tiered Command Table
For each command in scope:

```yaml
- command: "\\frac{a}{b}"
  tier: 1
  domain: "calculus"
  meaning: "분수 a/b"
  jsonl_escaped: "\\\\frac{a}{b}"
  common_errors:
    - pattern: "\\frac{a}b"
      issue: "Missing second braces group"
      fix: "\\frac{a}{b}"
    - pattern: "\\frac a b"
      issue: "No braces at all"
      fix: "\\frac{a}{b}"
  render_note: "Renders as vertical fraction"
```

### 3. Generate Escape Rule Quick-Reference
Core JSONL-in-LaTeX escape rules:

| LaTeX Original | JSONL Escaped | Trap |
|---------------|---------------|------|
| `\frac` | `\\frac` | Single `\` breaks JSON parser |
| `\\` (newline in align) | `\\\\` | Double-escape for row break |
| `"text"` | `\"text\"` | Unescaped quotes break JSON |
| `\n` (literal) | `\\n` | Conflicts with JSON newline |
| `\{` | `\\{` or `\\left\\{` | Brace escaping layers |

### 4. Create Trap Catalog
Organized by error severity:
- **FATAL**: Breaks JSON parsing entirely (unescaped quotes, unescaped backslash)
- **RENDER**: Compiles but displays incorrectly (missing `\left`/`\right`, wrong grouping)
- **STYLE**: Technically correct but violates standards (`\sin` as italic text, missing `\,` before dx)

### 5. Output Reference Document
Combine into structured output with both machine-readable (YAML) and human-readable (markdown) formats.

## Failure Handling

### Domain Not Recognized
- **Cause**: User specifies unknown math domain
- **Action**: List available domains via AskUserQuestion, let user choose
- **Route**: Self (re-run with valid domain)

### Reference Too Large
- **Cause**: Full-scope reference exceeds practical size
- **Action**: Split into per-domain reference files
- **Route**: Output multiple L2 documents, one per domain

## Anti-Patterns

### DO NOT: Include Commands Not Used in 수리논술
Korean 수리논술 uses a specific subset of LaTeX. Don't include chemistry (`\ce`), tikz diagrams, or advanced typography commands.

### DO NOT: Show Only Correct Forms
The trap catalog IS the reference's primary value. Every command entry MUST include common error patterns.

### DO NOT: Separate LaTeX and JSONL References
Always show both forms together. The trainee must internalize the mapping.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| User request | Domain scope | Natural language or domain keyword |
| progress-track | Weak areas | YAML with error_categories and frequencies |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| challenge-generate | Command pool | Always (reference feeds challenges) |
| latex-parse | Valid command allowlist | Always (parser needs known-good commands) |
| golden-correct | Canonical syntax | Always (corrector needs reference forms) |

## Quality Gate
- Every command has: LaTeX form + JSONL-escaped form + ≥1 error pattern
- Escape rule table covers all 5 core rules
- Trap catalog has ≥3 FATAL, ≥5 RENDER, ≥3 STYLE examples
- All examples validated: JSONL string is parseable by `JSON.parse()`

## Output

### L1
```yaml
domain: foundation
skill: reference-build
status: complete
scope: [calculus, linear_algebra]  # domains covered
command_count: 0
tier_distribution:
  tier1: 0
  tier2: 0
  tier3: 0
trap_count: 0
```

### L2
- Tiered command reference table (YAML + markdown)
- JSONL escape quick-reference card
- Trap catalog by severity (FATAL/RENDER/STYLE)
- Domain-specific gotchas
