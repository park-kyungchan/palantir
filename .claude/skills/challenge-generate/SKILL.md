---
name: challenge-generate
description: |
  [D1·Drill·Challenge] GenerateAdaptiveChallenge: 4 types (OCR-correction/pure-escape/domain-switch/composite), 80/20 weak-area trap allocation, adaptive difficulty. Pipeline A entry.

  WHEN: Drill loop start. After reference-build (IC-01) or progress-track (IC-03). User-invocable [topic] [difficulty:1-5].
  DOMAIN: drill (1/5). Entry: challenge -> user -> jsonl-validate || latex-parse -> render-evaluate -> golden-correct.
  INPUT_FROM: IC-01 command_pool (commands[], escape_rules[], ocr_confusions[], trap_catalog[]), IC-03 recommendation (next_difficulty, focus_rules[], weak_patterns[]).
  OUTPUT_TO: IC-04 challenge_spec (trap_list, escape_rules_tested), IC-05 expected_constructs (constructs[], parse_depth), IC-06 golden_answer (jsonl_string, trap_annotations, hidden).

  METHODOLOGY: (1) Load IC-01+IC-03 or defaults, (2) Select type from weak_patterns, (3) Allocate traps 80/20, (4) Domain-adaptive template, (5) Hidden golden answer per IC-06.
  OUTPUT_FORMAT: L1 YAML challenge_spec + contracts_produced, L2 target rendering + hidden annotations.
user-invocable: true
disable-model-invocation: false
argument-hint: "[topic] [difficulty:1-5]"
---

# Drill -- Challenge Generate (Pipeline A Entry)

## Execution Model
- **Level 1-2 (Beginner)**: Single math expression with 1-2 traps. No environments. Challenge types: pure-escape or OCR-correction only.
- **Level 3 (Intermediate)**: Multi-line math with `aligned`/`cases`. 2-3 traps including text mixing. All single-type challenges available.
- **Level 4 (Advanced)**: Nested environments (matrix inside limit, set with conditions). 3-4 traps. Domain-switch challenges introduced.
- **Level 5 (Hell)**: Full passage mixing Korean text + complex math + logical quantifiers + nested environments. 4-5 traps across all categories. Composite challenges (all categories combined).

## Decision Points

### Challenge Type Selection (REQ-CG-05)

Four challenge types, selected based on IC-03 `weak_patterns` and difficulty level:

```
IF IC-03.weak_patterns contains category == "ESCAPE" with pass_rate < 0.5:
  -> pure-escape challenge
     Focus: R1-R5 escape rules from IC-01.escape_rules[]
     Trap allocation: 80%+ traps are ESCAPE category
     Levels: 1-5 (available at all levels)

ELIF IC-03.weak_patterns contains category == "TEXT" with consecutive_failures >= 2:
  -> OCR-correction challenge
     Focus: ocr_confusions[] from IC-01 command_pool
     Content: Present OCR-degraded text for JSONL construction
     Traps: OCR confusion patterns as trap sources
     Levels: 2-5 (requires text content)

ELIF IC-03.domain_performance shows domain with pass_rate < 0.5 AND difficulty >= 4:
  -> domain-switch challenge
     Focus: Cross-domain commands (e.g., calculus + linear algebra)
     Content: Problem requiring commands from 2+ IC-01 domains
     Traps: Domain-specific conventions that conflict across domains
     Levels: 4-5 (requires multi-domain familiarity)

ELIF difficulty == 5 AND IC-03.overall_mastery >= 0.7:
  -> composite challenge
     Focus: All trap categories in single complex passage
     Content: Full Korean passage + nested math + multiple environments
     Traps: Minimum 1 per category (ESCAPE + GROUPING + OPERATOR + TEXT + SEMANTIC)
     Levels: 5 only

ELSE:
  -> pure-escape challenge (default)
     Rationale: ESCAPE is foundational; most common early weakness
```

### Adaptive Difficulty Parameters (REQ-CG-01)

Maps IC-03 recommendation fields to challenge generation parameters:

| IC-03 Field | Challenge Parameter | Mapping |
|-------------|-------------------|---------|
| `next_difficulty` (1-5) | Trap count, structure complexity | See Difficulty Scaling table |
| `difficulty_delta` (-1, 0, +1) | Difficulty direction | CLAMP to +/-1; never jump >1 level |
| `focus_rules` (R1-R5 IDs) | Escape rule emphasis | Selected rules get dedicated traps |
| `focus_commands` | Command pool filter | Filter IC-01 commands to focus set |
| `weak_patterns[].category` | Trap category priority | Top N weakest get 80% allocation |
| `focus_weight` (0.0-1.0) | Weak/retention split | Default 0.7; maps to 80/20 at >= 0.6 |
| `domain_performance[]` | Domain selection | Weakest recommended domain prioritized |
| `suggested_trap_types` | Trap type hints | Merge with category priority |
| `suggested_topic` | Topic selection | Use if provided; else derive from weak areas |
| `mode` | Pipeline context | Must be "drill" for Pipeline A |

**Default Parameters** (when IC-03 recommendation absent):
```yaml
difficulty: 2
focus_weight: 0.5
challenge_type: pure-escape
trap_allocation: balanced (no 80/20 skew)
domain: first available in IC-01 command_pool
```

### Difficulty Scaling

| Level | Structure | Trap Count | Text/Math Mix | Environment | Challenge Types |
|-------|-----------|------------|---------------|-------------|-----------------|
| 1 | Single expression | 1 | Math only | None | pure-escape |
| 2 | 2-3 expressions | 2 | Minimal text | None | pure-escape, OCR-correction |
| 3 | Multi-line block | 3 | Text paragraphs | `aligned` or `cases` | pure-escape, OCR-correction |
| 4 | Nested structures | 4 | Definition-style | Nested environments | All single-type |
| 5 | Full passage | 5 | Full Korean passage | Multiple nested | All including composite |

**Trap count validation**: IC-04 `trap_list.length` must equal `difficulty +/- 1`.

### Trap Allocation Strategy (REQ-CG-04)

When IC-03 recommendation is present with `weak_patterns[]`:

```
Step 1: Rank categories by weakness (lowest pass_rate first)
Step 2: Select top N weak categories where N = min(3, categories with pass_rate < 0.7)
Step 3: Allocate 80% of trap_count to top N weak categories
         - Distribute proportionally to inverse pass_rate
         - e.g., TEXT at 30% and SIZING at 45% -> TEXT gets more traps
Step 4: Allocate remaining 20% to mastered categories (retention)
         - Select from categories with pass_rate > 0.8
         - Ensures skills don't regress

IF IC-03 focus_weight < 0.6:
  -> Use 60/40 split instead of 80/20 (less aggressive focusing)
IF IC-03 focus_weight >= 0.8:
  -> Use 90/10 split (very aggressive focusing for persistent weakness)
```

**Without IC-03**: Balance traps across all categories introduced at current level.

### Topic Selection Strategy

```
IF IC-03.suggested_topic is present:
  -> Use suggested_topic, verify commands exist in IC-01 pool
ELIF IC-03.domain_performance identifies recommended domain:
  -> Select topic from recommended domain
ELIF user specifies topic via $ARGUMENTS:
  -> Use specified topic, select appropriate difficulty
ELSE (first session, no IC-03):
  -> Start with Level 2, balanced across core topics
  -> Topics: calculus > linear_algebra > set_theory > logic (frequency order)
```

### Challenge Output Format

The challenge is presented as a "Target Rendering" -- a description of what the final rendered output should look like, NOT the LaTeX code. The trainee must produce the JSONL string that would render to match.

```
Example (Level 3, pure-escape type):

**Target Rendering:**
A piecewise function definition where f(x) equals:
- x squared + 1  when x > 0
- 0              when x = 0
- -x + 1         when x < 0

With the text "함수 f: R -> R을 다음과 같이 정의하자:" before the math block.
The curly brace should auto-size to the cases.
```

```
Example (Level 4, OCR-correction type):

**Target Rendering:**
The following text was extracted via OCR and needs accurate JSONL representation:
"적분 integral from 0 to infinity of e to the power of negative x squared dx equals
 square root of pi over 2"

Note: The OCR may have confused 'theta' with '9', and 'integral sign' may appear
as a broken character. Your JSONL must use correct LaTeX commands.
```

### Per-Trap Rule Mapping (REQ-CG-02)

Each trap in `trap_list` maps to specific IC-01 rules with difficulty contribution:

| Trap Category | Target Rules (IC-01) | Difficulty Contribution | Severity if Failed |
|---------------|---------------------|------------------------|-------------------|
| ESCAPE | R1 (backslash), R2 (quote), R3 (newline) | 1-2 per trap | FATAL |
| GROUPING | Brace scope rules from trap_catalog | 1 per trap | FAIL |
| OPERATOR | Operator command rules from trap_catalog | 1 per trap | WARN |
| SIZING | Delimiter sizing rules from trap_catalog | 1 per trap | WARN |
| TEXT | Text-mode rules from trap_catalog | 1-2 per trap | WARN |
| ENVIRONMENT | Environment rules from trap_catalog | 2 per trap | FAIL |
| SEMANTIC | Domain semantic rules from trap_catalog | 1 per trap | INFO/WARN |
| COMPOSITE | Multiple rules combined | 2-3 per trap | FAIL |

Each IC-04 `trap_list[]` entry includes: `trap_id` (refs IC-01 `trap_catalog`), `category`, `target_rule`, `description`, `severity_if_failed`.

## Methodology

### 1. Load Input: IC-01 Command Pool + IC-03 Recommendation

**IC-01 command_pool** (from reference-build):
- Read `crowd_works/data/reference-cache/{domain}.yaml` for domain scope
- Extract: `commands[]` (tiered T1-T3), `escape_rules[]` (R1-R5), `ocr_confusions[]`, `trap_catalog[]`
- If multiple domains requested: merge command pools, note cross-domain overlaps

**IC-03 recommendation** (from progress-track):
- Read most recent recommendation output
- Extract: `next_difficulty`, `difficulty_delta`, `focus_rules[]`, `weak_patterns[]`, `focus_weight`, `domain_performance[]`, `suggested_trap_types[]`, `suggested_topic`, `mode`
- Validate: `mode` must be "drill" (Pipeline A). If "production": reject and report error.
- Validate: `difficulty_delta` is within [-1, +1]. If outside range: CLAMP to nearest boundary.

**Fallback** (IC-03 absent or first session):
- Set `difficulty = 2`, `focus_weight = 0.5`, no weak_patterns
- Select from IC-01 command pool with balanced trap distribution
- Log: "No IC-03 recommendation available; using defaults"

### 2. Select Challenge Type Based on Weak Patterns

Apply the Challenge Type Selection decision tree (see Decision Points).

Record selection rationale:
```yaml
challenge_type_selection:
  type: "pure-escape"|"OCR-correction"|"domain-switch"|"composite"
  rationale: string  # Why this type was chosen
  trigger: string    # Which IC-03 field triggered the selection
  weak_categories: [string]  # Categories driving the selection
```

For **OCR-correction** type: filter IC-01 `ocr_confusions[]` to match weak_patterns. Select confusions that the trainee has historically struggled with.

For **domain-switch** type: identify 2 domains from IC-01 where the trainee has cross-domain weakness (e.g., confusing `\vec{F}` physics notation with `\vec{v}` math notation).

For **composite** type: ensure at least 1 trap from each of 3+ categories. Plan trap distribution before content design.

### 3. Allocate Traps per Weak-Area Strategy (REQ-CG-04)

Apply the Trap Allocation Strategy (see Decision Points).

For each allocated trap slot:
1. Select a specific trap from IC-01 `trap_catalog[]` matching the target category
2. Assign `target_rule` from IC-01 `escape_rules[]` where applicable (R1-R5)
3. Set `severity_if_failed` per the Per-Trap Rule Mapping table
4. Calculate total `difficulty_contribution` -- must approximate `difficulty` level

Build the IC-04 `trap_list[]`:
```yaml
trap_list:
  - trap_id: "ESCAPE_R1_001"        # refs IC-01 trap_catalog
    category: ESCAPE
    target_rule: "R1"               # refs IC-01 escape_rules
    description: "Backslash double-escape in \\frac command"
    severity_if_failed: FATAL
  - trap_id: "TEXT_SPACING_003"
    category: TEXT
    target_rule: null
    description: "Missing spaces in \\text{ if } command"
    severity_if_failed: WARN
```

**Verification**: Count traps by source (weak vs retention). Weak-area traps must be >= 80% when IC-03 focus_weight >= 0.6.

### 4. Design Target Rendering with Domain-Adaptive Template (REQ-CG-03)

Templates adapt to the domain(s) selected from IC-01:

**Template Selection by Domain**:
| Domain | Template Pattern | Key Constructs |
|--------|-----------------|----------------|
| Calculus | Limit/integral expressions | `\lim`, `\int`, `\frac{d}{dx}` |
| Linear Algebra | Matrix/vector equations | `\begin{pmatrix}`, `\vec{}`, `\det` |
| Set Theory | Set builder notation | `\{`, `\mid`, `\in`, `\forall` |
| Logic | Quantifier/proof structure | `\forall`, `\exists`, `\implies` |
| Physics | Force/motion equations | `\vec{F}`, `\ddot{x}`, units |
| Chemistry | Chemical equations | `\ce{}`, reaction arrows |

**Template Construction Rules**:
1. Select constructs from IC-01 `commands[]` matching chosen domain(s)
2. Prioritize Tier 1 (daily) commands at Levels 1-2; mix Tier 2-3 at Levels 3-5
3. Ensure each trap has a natural placement in the content (not forced)
4. Include Korean text integration at Level 3+ (domain-appropriate context)
5. For domain-switch: create a problem naturally spanning 2 domains

**Target Rendering Description** (visible to trainee):
- Describe what the rendered output should look like visually
- Specify formatting requirements (auto-sizing, alignment, spacing)
- Include verbatim text content where applicable
- For OCR-correction type: describe the OCR-degraded source
- NEVER show LaTeX code -- that is the trainee's job

**Build IC-05 expected_constructs** alongside the template:
```yaml
expected_constructs:
  challenge_id: "DRILL-016"
  mode: drill
  difficulty: 3
  constructs:
    - construct_type: "fraction"
      expected_count: 2
      nesting_depth: 1
      specific_commands: ["\\frac"]
    - construct_type: "environment"
      expected_count: 1
      nesting_depth: 1
      specific_commands: ["\\begin{cases}", "\\end{cases}"]
  domain_rules:
    - rule_id: "R1"
      description: "Backslash double-escape"
      severity: FATAL
      active: true
  parse_depth: "standard"  # basic(L1-2), standard(L3), full(L4-5)
```

### 5. Generate Hidden Golden Answer (IC-06)

Create the perfect JSONL string that renders to match the target description.

**IC-06 golden_answer schema** (full compliance required):
```yaml
golden_answer:
  challenge_id: "DRILL-016"
  mode: drill
  difficulty: 3
  jsonl_string: '{"text": "함수 $f(x) = \\\\frac{x^{2}}{2}$..."}'
  json_parsed:
    text: "함수 $f(x) = \\frac{x^{2}}{2}$..."
  rendered_description: "A fraction x-squared over 2 with Korean intro text"
  element_list:
    - element_id: "E1"
      type: "text"
      description: "Korean intro: 함수 f(x)를 다음과 같이 정의하자."
      critical: false
    - element_id: "E2"
      type: "math_inline"
      description: "Fraction with x-squared numerator"
      critical: true
  trap_annotations:
    - trap_id: "ESCAPE_R1_001"
      location_in_jsonl:
        char_start: 28
        char_end: 34
      correct_form: "\\\\frac"
      incorrect_alternatives: ["\\frac", "frac"]
      scoring_weight: 0.3
    - trap_id: "TEXT_SPACING_003"
      location_in_jsonl:
        char_start: 15
        char_end: 22
      correct_form: "\\\\text{ if }"
      incorrect_alternatives: ["\\\\text{if}", "\\\\text{ if}"]
      scoring_weight: 0.2
  visibility: "hidden"
```

**Verification before output**:
1. `jsonl_string` passes `JSON.parse()` -- valid JSON
2. `json_parsed.text` contains valid LaTeX -- no syntax errors
3. Every `trap_annotations[].trap_id` exists in `trap_list[]` (IC-04)
4. `char_start`/`char_end` positions are accurate within `jsonl_string`
5. `scoring_weight` values sum to <= 1.0
6. `visibility` is always "hidden" -- NEVER expose to trainee

**Security**: The golden answer is stored internally and passed ONLY to render-evaluate (IC-06) and golden-correct. The trainee sees only the Target Rendering description.

## Failure Handling

### IC-01 Command Pool Missing
- **Cause**: reference-build has not been run, or reference-cache/{domain}.yaml does not exist
- **Action**: FALLBACK to built-in minimal command set (20 core commands: `\frac`, `\int`, `\sum`, `\lim`, `\sqrt`, `\sin`, `\cos`, `\log`, `\text`, `\begin`/`\end` for `aligned`/`cases`/`pmatrix`, `\left`/`\right`, `\vec`, `\cdot`, `\infty`, `\partial`). Generate challenge using built-in set. Log warning: "Using fallback command set; run /reference-build for full pool."
- **Route**: Normal output with `fallback_mode: true` flag. Downstream skills operate normally.

### IC-03 Recommendation Has Invalid Difficulty Delta
- **Cause**: `difficulty_delta` exceeds +/-1 range (e.g., +2 or -3)
- **Action**: CLAMP to nearest valid value (+1 or -1). Log: "difficulty_delta clamped from {original} to {clamped}"
- **Route**: Normal challenge generation with clamped difficulty. Report clamp in L1 output.

### IC-03 Mode is "production"
- **Cause**: Incorrect routing -- production mode recommendation sent to drill skill
- **Action**: REJECT recommendation. Report error: "challenge-generate is Pipeline A (drill) only. Received mode: production."
- **Route**: Use default parameters (difficulty 2, no weak-area focus). Signal Lead for routing correction.

### Topic Not in IC-01 Command Pool
- **Cause**: User or IC-03 requests topic not covered by any reference-cache domain
- **Action**: Map to nearest available domain. Log: "Requested topic '{topic}' not in pool; using nearest domain '{domain}'"
- **Route**: Normal generation with substituted domain.

### Trainee Repeatedly Fails Same Trap Type
- **Cause**: Difficulty too high for current skill level (pattern visible across multiple drills)
- **Action**: This skill does not track history directly. Rely on IC-03 recommendation from progress-track, which will adjust difficulty_delta to -1 and increase focus_weight.
- **Route**: progress-track handles the feedback loop. challenge-generate responds to IC-03 signals.

### Topic Exhaustion
- **Cause**: All standard challenges for a topic have been generated in recent drills
- **Action**: Generate novel combinations by mixing 2+ topics (domain-switch challenge type) or varying trap allocation within the same topic.
- **Route**: Self (composite or domain-switch challenge generation)

### Trap Catalog Too Small for Allocation
- **Cause**: IC-01 trap_catalog has fewer traps than needed for difficulty level in target category
- **Action**: Fill remaining trap slots from next-priority category. Log: "Insufficient {category} traps in IC-01; supplemented with {fallback_category}"
- **Route**: Normal output with adjusted allocation. Note in L1 output.

## Anti-Patterns

### DO NOT: Show LaTeX Code in Challenge
The challenge is a RENDERING DESCRIPTION, not code. Showing LaTeX code defeats the purpose of the drill. The trainee must translate visual intent into JSONL.

### DO NOT: Make Traps Ambiguous
Every trap must have exactly one correct resolution per IC-01 escape_rules and trap_catalog. If a construct could be validly written multiple ways, specify which style is required in the target description.

### DO NOT: Generate Mathematically Incorrect Content
All expressions must be mathematically valid. The challenge tests LaTeX/JSONL skills, not math knowledge.

### DO NOT: Exceed 5 Traps Per Challenge
Maximum trap count is `difficulty + 1` (capped at 5 for Level 5). Quality over quantity -- each trap should be learnable.

### DO NOT: Ignore IC-03 Recommendation When Present
If progress-track provides a recommendation, it MUST influence challenge generation. Generating challenges without responding to the feedback loop breaks the Continuous Optimization Loop (Cross-Cutting Theme C).

### DO NOT: Use Commands Not in IC-01 Pool
All LaTeX commands in the golden answer must exist in IC-01 `commands[]` for the selected domain(s). Using commands outside the pool creates untestable constructs -- downstream latex-parse has no allowlist entry for them.

### DO NOT: Reveal Golden Answer Metadata to Trainee
`trap_annotations`, `scoring_weight`, `incorrect_alternatives` are evaluator-only data (IC-06 `visibility: "hidden"`). The trainee sees only the Target Rendering description.

### DO NOT: Generate Drill-Mode Challenges for Production Pipeline
challenge-generate is Pipeline A (drill) ONLY. IC-03 `mode` must be "drill". Production QC (Pipeline B) starts at image-preprocess, not here.

## Transitions

### Receives From (Interface Contracts)

| Source Skill | IC | Data Expected | Key Fields |
|-------------|-----|---------------|------------|
| reference-build | IC-01 | Command pool + escape rules + OCR patterns + trap catalog | `command_pool.{domains[].commands[], domains[].escape_rules[], domains[].ocr_confusions[], domains[].trap_catalog[], tier_distribution}` |
| progress-track | IC-03 | Adaptive difficulty recommendation | `recommendation.{drill_count, overall_mastery, overall_level, next_difficulty, difficulty_delta, focus_rules[], focus_commands[], weak_patterns[].{category, pass_rate, mastery, consecutive_failures, specific_errors[], trend}, focus_weight, domain_performance[].{domain, pass_rate, mastery, recommended}, suggested_trap_types[], suggested_topic, mode}` |
| User | -- | Topic preference, difficulty override | Natural language or `[topic] [difficulty:1-5]` via argument-hint |

**Error handling for IC-03**: Missing recommendation -> DEFAULT difficulty=2, focus_weight=0.5, no weak_patterns. See Failure Handling for invalid fields.

### Sends To (Interface Contracts)

| Target Skill | IC | Data Produced | Key Fields | Trigger |
|-------------|-----|---------------|------------|---------|
| jsonl-validate | IC-04 | Challenge specification | `challenge_spec.{challenge_id, mode, difficulty, topic, expected_structure.{top_level_keys, contains_math, contains_environments[], contains_korean_text}, trap_list[].{trap_id, category, target_rule, description, severity_if_failed}, escape_rules_tested[]}` | Always (drill chain start) |
| latex-parse | IC-05 | Expected constructs | `expected_constructs.{challenge_id, mode, difficulty, constructs[].{construct_type, expected_count, nesting_depth, specific_commands[]}, domain_rules[].{rule_id, description, severity, active}, parse_depth}` | Always (drill chain start) |
| render-evaluate | IC-06 | Golden answer (hidden) | `golden_answer.{challenge_id, mode, difficulty, jsonl_string, json_parsed.{text}, rendered_description, element_list[].{element_id, type, description, critical}, trap_annotations[].{trap_id, location_in_jsonl.{char_start, char_end}, correct_form, incorrect_alternatives[], scoring_weight}, visibility:"hidden"}` | Always (drill chain start) |

### Failure Routes

| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| IC-01 missing | Self (fallback mode) | Built-in minimal command set |
| IC-03 mode mismatch | Lead (error) | Mode rejection signal |
| IC-03 invalid delta | Self (clamped) | Clamped difficulty_delta |
| Topic not in pool | Self (substituted domain) | Nearest domain mapping |

## Quality Gate

- IC-04 `challenge_spec` validates against schema: all REQUIRED fields present
- IC-05 `expected_constructs` validates: constructs[] non-empty, parse_depth set per difficulty
- IC-06 `golden_answer.jsonl_string` passes `JSON.parse()` -- valid JSON
- IC-06 `golden_answer.json_parsed.text` contains syntactically valid LaTeX
- Trap count matches difficulty level +/-1 (IC-04 `trap_list.length`)
- 80% weak-area allocation verified when IC-03 recommendation present with focus_weight >= 0.6
- Every `trap_list[].trap_id` references a valid IC-01 `trap_catalog` entry (or fallback set)
- Every `trap_annotations[].trap_id` exists in `trap_list[]` (cross-reference consistency)
- `char_start`/`char_end` positions in `trap_annotations` are accurate within `jsonl_string`
- Challenge type matches selection criteria from Decision Points
- Mathematical content is accurate (expressions are mathematically valid)
- Korean text is grammatically correct (when present at Level 3+)
- Mode is "drill" in all three output contracts (IC-04, IC-05, IC-06)
- `visibility: "hidden"` set on IC-06 golden_answer
- No LaTeX commands used outside IC-01 command pool (or documented fallback set)

## Output

### L1
```yaml
domain: drill
skill: challenge-generate
status: ready_for_input
challenge_id: "DRILL-016"
challenge_type: "pure-escape"|"OCR-correction"|"domain-switch"|"composite"
mode: drill
difficulty: 3
difficulty_source: "IC-03"|"user"|"default"
topic: "aligned_equations_with_logic"
domain: "calculus"
trap_types: [ESCAPE_backslash, TEXT_spacing, SIZING_left_right]
trap_count: 3
trap_allocation:
  weak_area: 2          # 80% of 3 (rounded)
  retention: 1           # 20% of 3
construct_categories: [aligned, text, quantifiers]
contracts_produced: [IC-04, IC-05, IC-06]
fallback_mode: false
```

### L2

**Target Rendering Description** (visible to trainee):
- Visual description of what the rendered output should look like
- Formatting requirements (auto-sizing, alignment, spacing)
- Verbatim text content where applicable
- For OCR-correction: OCR-degraded source description

**Hidden Evaluator Data** (IC-04 challenge_spec):
```yaml
# Example IC-04 output
challenge_spec:
  challenge_id: "DRILL-016"
  mode: drill
  difficulty: 3
  topic: "piecewise_function"
  expected_structure:
    top_level_keys: ["text"]
    contains_math: true
    contains_environments: ["cases"]
    contains_korean_text: true
  trap_list:
    - trap_id: "ESCAPE_R1_001"
      category: ESCAPE
      target_rule: "R1"
      description: "Backslash double-escape in \\frac"
      severity_if_failed: FATAL
    - trap_id: "TEXT_SPACING_003"
      category: TEXT
      target_rule: null
      description: "Missing spaces in \\text{ if }"
      severity_if_failed: WARN
    - trap_id: "SIZING_DELIM_002"
      category: SIZING
      target_rule: null
      description: "Missing \\left\\{ for cases brace"
      severity_if_failed: WARN
  escape_rules_tested: ["R1", "R3"]
```

**Hidden Evaluator Data** (IC-05 expected_constructs):
```yaml
# Example IC-05 output
expected_constructs:
  challenge_id: "DRILL-016"
  mode: drill
  difficulty: 3
  constructs:
    - construct_type: "fraction"
      expected_count: 1
      nesting_depth: 1
      specific_commands: ["\\frac"]
    - construct_type: "environment"
      expected_count: 1
      nesting_depth: 1
      specific_commands: ["\\begin{cases}", "\\end{cases}"]
    - construct_type: "text_mode"
      expected_count: 3
      nesting_depth: 0
      specific_commands: ["\\text"]
  domain_rules:
    - rule_id: "R1"
      description: "Backslash double-escape"
      severity: FATAL
      active: true
    - rule_id: "R3"
      description: "Newline handling in JSONL"
      severity: FATAL
      active: true
  parse_depth: "standard"
```

**Hidden Evaluator Data** (IC-06 golden_answer):
- Complete JSONL string (verified JSON.parse + valid LaTeX)
- Element list with element_id, type, description, critical flag
- Trap annotations with char-level positions and scoring weights
- `visibility: "hidden"` -- NEVER exposed to trainee
