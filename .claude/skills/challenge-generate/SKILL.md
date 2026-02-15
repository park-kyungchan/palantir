---
name: challenge-generate
description: |
  [D1·Drill·Challenge] Generates difficulty-scaled rendering challenges with intentional traps for JSONL/LaTeX drill training.

  WHEN: Drill loop start. After reference-build or progress-track recommendation.
  DOMAIN: drill (skill 1 of 5). Entry: challenge -> user -> jsonl-validate ∥ latex-parse -> render-evaluate -> golden-correct.
  INPUT_FROM: reference-build (command pool), progress-track (difficulty + weak areas).
  OUTPUT_TO: jsonl-validate (target spec), latex-parse (expected constructs), render-evaluate (target rendering), golden-correct (golden answer).

  METHODOLOGY: (1) Select topic+difficulty from pool or recommendation, (2) Design target with ≥2 nested structures, (3) Embed ≥3 traps matching weak areas, (4) Write target description + math preview, (5) Generate hidden golden answer.
  OUTPUT_FORMAT: L1 YAML challenge spec, L2 target rendering with hidden trap annotations.
user-invocable: true
disable-model-invocation: false
argument-hint: "[topic] [difficulty:1-5]"
---

# Drill — Challenge Generate

## Execution Model
- **Level 1-2 (Beginner)**: Single math expression with 1-2 traps. No environments.
- **Level 3 (Intermediate)**: Multi-line math with `aligned`/`cases`. 2-3 traps including text mixing.
- **Level 4 (Advanced)**: Nested environments (matrix inside limit, set with conditions). 3-4 traps.
- **Level 5 (Hell)**: Full passage mixing Korean text + complex math + logical quantifiers + nested environments. 4-5 traps across all categories.

## Decision Points

### Topic Selection Strategy
```
IF progress-track provides weak_areas:
  -> 70% challenges from weak areas, 30% from mastered areas (retention)
ELIF user specifies topic:
  -> Use specified topic, select appropriate difficulty
ELSE (first session):
  -> Start with Level 2, balanced across core topics
  -> Topics: calculus > linear_algebra > set_theory > logic (frequency order)
```

### Difficulty Scaling
| Level | Structure | Traps | Text/Math Mix | Environment |
|-------|-----------|-------|---------------|-------------|
| 1 | Single expression | 1 escape | Math only | None |
| 2 | 2-3 expressions | 1 escape + 1 syntax | Minimal text | None |
| 3 | Multi-line block | 2 escape + 1 semantics | Text paragraphs | `aligned` or `cases` |
| 4 | Nested structures | 2 escape + 2 syntax/semantics | Definition-style | Nested environments |
| 5 | Full passage | 2 escape + 2 syntax + 1 semantics | Full Korean passage | Multiple nested |

### Trap Type Selection
Traps are categorized and intentionally embedded:

| Trap Category | Examples | Level Introduced |
|---------------|----------|-----------------|
| **ESCAPE** | `\"` in text, `\\\\` for align breaks, `\n` vs `\\n` | Level 1 |
| **GROUPING** | `{}^13C` vs `{}^{13}C`, missing braces in `\frac` | Level 2 |
| **OPERATOR** | `sin x` (italic) vs `\sin x` (upright) | Level 2 |
| **SIZING** | Missing `\left`/`\right`, `\{` without escape | Level 3 |
| **TEXT** | `\text{ if }` spacing, nested `$` inside text | Level 3 |
| **ENVIRONMENT** | `\\\\` row breaks, `&` alignment, `\begin`/`\end` match | Level 4 |
| **SEMANTIC** | Missing `\,` before `dx`, `\middle|` for set builder | Level 4 |
| **COMPOSITE** | Multiple categories in single expression | Level 5 |

### Challenge Output Format
The challenge is presented as a "Target Rendering" — a description of what the final rendered output should look like, NOT the LaTeX code. The trainee must produce the JSONL string that would render to match.

```
Example (Level 3):

**Target Rendering:**
A piecewise function definition where f(x) equals:
- x² + 1  when x > 0
- 0        when x = 0
- -x + 1   when x < 0

With the text "Define f: ℝ → ℝ as follows:" before the math block.
The curly brace should auto-size to the cases.
```

## Methodology

### 1. Select Topic and Difficulty
Read from progress-track or user argument. Map to available command pool from reference-build.

### 2. Design Target Rendering
Create a mathematically meaningful expression/passage that:
- Uses ≥2 different LaTeX construct categories (fracs, environments, operators, text)
- Has natural text-math interleaving (Korean 설명 + LaTeX 수식)
- Requires at least one JSONL escape challenge

### 3. Embed Intentional Traps
Select trap types based on difficulty level and trainee weak areas.
Each trap must be:
- **Plausible**: A real mistake someone would make
- **Detectable**: Has a clear right/wrong answer
- **Educational**: Teaches a specific rule when corrected

### 4. Write Target Description
Present in natural language what the rendered output should look like.
Include:
- Visual description of math layout
- Specific formatting requirements (auto-sizing, alignment, spacing)
- Any text content that must appear verbatim
- DO NOT show LaTeX code — that's the trainee's job

### 5. Generate Hidden Golden Answer
Create the perfect JSONL string that matches the target.
Store internally for render-evaluate and golden-correct to use.
NEVER reveal to trainee until evaluation phase.

## Failure Handling

### Trainee Repeatedly Fails Same Trap Type
- **Cause**: Difficulty too high for current skill level
- **Action**: Reduce difficulty by 1 level, increase trap frequency for that category
- **Route**: progress-track (flag persistent weakness)

### Topic Exhaustion
- **Cause**: All standard challenges for a topic used
- **Action**: Generate novel combinations by mixing 2+ topics
- **Route**: Self (composite challenge generation)

## Anti-Patterns

### DO NOT: Show LaTeX Code in Challenge
The challenge is a RENDERING DESCRIPTION, not code. Showing code defeats the purpose of the drill.

### DO NOT: Make Traps Ambiguous
Every trap must have exactly one correct resolution. If a construct could be validly written multiple ways, specify which style is required.

### DO NOT: Generate Mathematically Incorrect Content
All expressions must be mathematically valid. The challenge tests LaTeX/JSONL skills, not math knowledge.

### DO NOT: Exceed 5 Traps Per Challenge
More than 5 traps creates confusion. Quality over quantity — each trap should be learnable.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| reference-build | Command pool, escape rules | YAML command inventory |
| progress-track | Difficulty recommendation, weak areas | YAML progress report |
| User | Topic preference, difficulty override | Natural language or `[topic] [level]` |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| jsonl-validate | Challenge spec (expected structure) | Always (drill chain) |
| latex-parse | Expected constructs list | Always (drill chain) |
| render-evaluate | Target rendering + golden answer (hidden) | Always (drill chain) |
| golden-correct | Golden answer (hidden) | Always (drill chain) |

## Quality Gate
- Challenge has ≥2 nested construct categories
- Trap count matches difficulty level (±1)
- Golden answer passes `JSON.parse()` validation
- Golden answer LaTeX renders correctly in KaTeX
- Mathematical content is accurate
- Korean text is grammatically correct

## Output

### L1
```yaml
domain: drill
skill: challenge-generate
status: ready_for_input
difficulty: 3
topic: "aligned_equations_with_logic"
trap_types: [ESCAPE_backslash, TEXT_spacing, SIZING_left_right]
trap_count: 3
construct_categories: [aligned, text, quantifiers]
```

### L2
- Target rendering description (visible to trainee)
- Trap annotations (hidden, for evaluator use only)
- Golden answer JSONL string (hidden)
- Expected difficulty assessment
