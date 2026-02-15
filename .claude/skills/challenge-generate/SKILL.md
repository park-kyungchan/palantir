---
name: challenge-generate
description: |
  Generates adaptive challenge: 4 types (OCR-correction/pure-escape/domain-switch/composite), 80/20 weak-area trap allocation, adaptive difficulty. Pipeline A entry point.

  Use when: Drill loop start or user-invocable [topic] [difficulty:1-5].
  WHEN: After reference-build (IC-01) or progress-track (IC-03). Drill loop entry.
  CONSUMES: IC-01 command_pool (commands[], escape_rules[], ocr_confusions[], trap_catalog[]), IC-03 recommendation (next_difficulty, focus_rules[], weak_patterns[]).
  PRODUCES: IC-04 challenge_spec → jsonl-validate, IC-05 expected_constructs → latex-parse, IC-06 golden_answer (hidden) → render-evaluate.
user-invocable: true
disable-model-invocation: false
argument-hint: "[topic] [difficulty:1-5]"
---

# Drill -- Challenge Generate (Pipeline A Entry)

## Execution Model
- **Level 1-2 (Beginner)**: Single math expression, 1-2 traps, no environments. Types: pure-escape or OCR-correction only.
- **Level 3 (Intermediate)**: Multi-line math with `aligned`/`cases`, 2-3 traps including text mixing. All single-type challenges.
- **Level 4 (Advanced)**: Nested environments (matrix inside limit, set with conditions), 3-4 traps. Domain-switch introduced.
- **Level 5 (Hell)**: Full passage mixing Korean text + complex math + quantifiers + nested environments, 4-5 traps. Composite challenges.

## Decision Points

### Challenge Type Selection (REQ-CG-05)

Four types selected via IC-03 `weak_patterns` and difficulty:

- **pure-escape** (default, L1-5): When `weak_patterns` has ESCAPE category with pass_rate < 0.5. Focus R1-R5 escape rules, 80%+ ESCAPE traps.
- **OCR-correction** (L2-5): When TEXT category has consecutive_failures >= 2. Focus ocr_confusions[] from IC-01.
- **domain-switch** (L4-5): When domain_performance shows domain with pass_rate < 0.5 AND difficulty >= 4. Cross-domain commands from 2+ IC-01 domains.
- **composite** (L5 only): When difficulty == 5 AND overall_mastery >= 0.7. All trap categories, minimum 1 per category.

Fallback: pure-escape (ESCAPE is foundational, most common early weakness).

### Adaptive Difficulty Parameters (REQ-CG-01)

IC-03 field mappings: `next_difficulty` (1-5) -> trap count + complexity; `difficulty_delta` (-1/0/+1) -> direction (CLAMP to +/-1, never jump >1); `focus_rules` (R1-R5) -> dedicated traps; `focus_commands` -> IC-01 filter; `weak_patterns[].category` -> top N weakest get 80% allocation; `focus_weight` (0.0-1.0) -> split ratio (default 0.7; >=0.6 maps to 80/20); `domain_performance[]` -> weakest domain prioritized; `suggested_trap_types` -> merge with category priority; `suggested_topic` -> use if provided; `mode` -> must be "drill".

**Defaults** (IC-03 absent): difficulty=2, focus_weight=0.5, type=pure-escape, balanced allocation, first available IC-01 domain.

### Difficulty Scaling

| Level | Structure | Traps | Text/Math | Environment | Types |
|-------|-----------|-------|-----------|-------------|-------|
| 1 | Single expr | 1 | Math only | None | pure-escape |
| 2 | 2-3 exprs | 2 | Minimal text | None | pure-escape, OCR |
| 3 | Multi-line | 3 | Text paragraphs | aligned/cases | pure-escape, OCR |
| 4 | Nested | 4 | Definition-style | Nested envs | All single-type |
| 5 | Full passage | 5 | Full Korean | Multiple nested | All incl. composite |

**Trap count validation**: IC-04 `trap_list.length` must equal `difficulty +/- 1`.

### Trap Allocation Strategy (REQ-CG-04)

With IC-03 `weak_patterns[]`: (1) Rank categories by weakness (lowest pass_rate first), (2) Select top N weak categories (N = min(3, categories with pass_rate < 0.7)), (3) Allocate 80% to weak categories proportional to inverse pass_rate, (4) Allocate 20% to mastered categories (pass_rate > 0.8) for retention. Split overrides: focus_weight < 0.6 -> 60/40; focus_weight >= 0.8 -> 90/10. Without IC-03: balance across all categories at current level.

### Topic Selection

Priority order: (1) IC-03.suggested_topic if present and commands exist in IC-01, (2) IC-03.domain_performance recommended domain, (3) User-specified topic via $ARGUMENTS, (4) Default: Level 2, balanced across calculus > linear_algebra > set_theory > logic.

### Challenge Output Format

Challenges are presented as "Target Rendering" -- a visual description of what the rendered output should look like, NOT LaTeX code. The trainee must produce JSONL that renders to match. Example (L3 pure-escape): describe a piecewise function with Korean intro text and auto-sizing requirements. Example (L4 OCR-correction): describe OCR-degraded text needing accurate JSONL representation with known confusion patterns.

### Per-Trap Rule Mapping (REQ-CG-02)

Each IC-04 `trap_list[]` entry includes: `trap_id` (refs IC-01 trap_catalog), `category`, `target_rule`, `description`, `severity_if_failed`. Category severity defaults: ESCAPE -> FATAL, GROUPING -> FAIL, ENVIRONMENT -> FAIL, COMPOSITE -> FAIL, OPERATOR/SIZING/TEXT -> WARN, SEMANTIC -> INFO/WARN. Difficulty contribution: 1-2 per ESCAPE/TEXT trap, 1 per GROUPING/OPERATOR/SIZING trap, 2 per ENVIRONMENT trap, 2-3 per COMPOSITE trap.

## Methodology

### 1. Load Input: IC-01 Command Pool + IC-03 Recommendation

**IC-01** (from reference-build): Read `crowd_works/data/reference-cache/{domain}.yaml`. Extract: `commands[]` (T1-T3), `escape_rules[]` (R1-R5), `ocr_confusions[]`, `trap_catalog[]`. Merge command pools if multiple domains.

**IC-03** (from progress-track): Extract: `next_difficulty`, `difficulty_delta`, `focus_rules[]`, `weak_patterns[]`, `focus_weight`, `domain_performance[]`, `suggested_trap_types[]`, `suggested_topic`, `mode`. Validate: mode must be "drill" (reject "production"). CLAMP difficulty_delta to [-1, +1].

**Fallback** (IC-03 absent): difficulty=2, focus_weight=0.5, no weak_patterns, balanced distribution. Log: "No IC-03 recommendation available; using defaults."

### 2. Select Challenge Type Based on Weak Patterns

Apply Challenge Type Selection decision tree (see Decision Points). Record selection rationale as YAML: `type`, `rationale`, `trigger` (IC-03 field), `weak_categories`. For OCR-correction: filter IC-01 ocr_confusions[] to match weak_patterns. For domain-switch: identify 2 domains with cross-domain weakness. For composite: ensure 1+ trap from each of 3+ categories.

### 3. Allocate Traps per Weak-Area Strategy (REQ-CG-04)

Apply Trap Allocation Strategy (see Decision Points). For each slot: (1) Select trap from IC-01 trap_catalog matching target category, (2) Assign target_rule from IC-01 escape_rules where applicable, (3) Set severity_if_failed per Per-Trap Rule Mapping, (4) Calculate total difficulty_contribution approximating difficulty level.

Build IC-04 `trap_list[]` with fields: `trap_id` (e.g., "ESCAPE_R1_001"), `category`, `target_rule`, `description`, `severity_if_failed`. Verify: weak-area traps >= 80% when focus_weight >= 0.6.

### 4. Design Target Rendering with Domain-Adaptive Template (REQ-CG-03)

**Template by domain**: Calculus (limit/integral: `\lim`, `\int`, `\frac{d}{dx}`), Linear Algebra (matrix/vector: `\begin{pmatrix}`, `\vec{}`, `\det`), Set Theory (set builder: `\{`, `\mid`, `\in`, `\forall`), Logic (quantifier/proof: `\forall`, `\exists`, `\implies`), Physics (force/motion: `\vec{F}`, units), Chemistry (chemical eqs: `\ce{}`).

**Construction rules**: (1) Select constructs from IC-01 commands[] for chosen domain, (2) Prioritize T1 at L1-2, mix T2-T3 at L3-5, (3) Ensure natural trap placement, (4) Korean text at L3+, (5) Domain-switch: span 2 domains naturally.

**Target Rendering** (visible): Describe visual output, formatting, verbatim text. For OCR-correction: describe degraded source. NEVER show LaTeX code.

**Build IC-05 expected_constructs**: `challenge_id`, `mode`, `difficulty`, `constructs[]` (construct_type, expected_count, nesting_depth, specific_commands[]), `domain_rules[]` (rule_id, description, severity, active), `parse_depth` (basic L1-2, standard L3, full L4-5).

### 5. Generate Hidden Golden Answer (IC-06)

Create perfect JSONL string matching target description. IC-06 schema fields: `challenge_id`, `mode`, `difficulty`, `jsonl_string`, `json_parsed.text`, `rendered_description`, `element_list[]` (element_id, type, description, critical), `trap_annotations[]` (trap_id, location_in_jsonl.{char_start, char_end}, correct_form, incorrect_alternatives[], scoring_weight), `visibility: "hidden"`.

**Verification**: (1) jsonl_string passes JSON.parse(), (2) json_parsed.text has valid LaTeX, (3) Every trap_annotations[].trap_id exists in trap_list[], (4) char_start/char_end positions accurate, (5) scoring_weight sum <= 1.0, (6) visibility always "hidden".

**Security**: Golden answer stored internally, passed ONLY to render-evaluate (IC-06) and golden-correct. Trainee sees only Target Rendering.

## Failure Handling

| Failure | Cause | Action | Route |
|---------|-------|--------|-------|
| IC-01 missing | reference-build not run | FALLBACK to built-in 20 core commands (`\frac`, `\int`, `\sum`, `\lim`, `\sqrt`, `\sin`, `\cos`, `\log`, `\text`, aligned/cases/pmatrix envs, `\left`/`\right`, `\vec`, `\cdot`, `\infty`, `\partial`). Log warning. | Normal with `fallback_mode: true` |
| Invalid difficulty_delta | delta exceeds +/-1 | CLAMP to nearest valid value. Log clamp. | Normal with clamped value |
| IC-03 mode=production | Wrong pipeline routing | REJECT. Error: "challenge-generate is Pipeline A only." | Default params + Lead error signal |
| Topic not in pool | Topic not in reference-cache | Map to nearest available domain. Log substitution. | Normal with substituted domain |
| Repeated trap failures | Difficulty too high | Rely on IC-03 from progress-track (adjusts delta to -1, increases focus_weight). | progress-track handles feedback loop |
| Topic exhaustion | All standard challenges used | Generate novel combos via domain-switch or varied allocation. | Self (composite/domain-switch) |
| Trap catalog too small | Fewer traps than needed | Fill remaining slots from next-priority category. Log supplement. | Normal with adjusted allocation |

## Anti-Patterns

### DO NOT: Show LaTeX Code in Challenge
The challenge is a RENDERING DESCRIPTION, not code. Showing LaTeX defeats the drill purpose -- trainee must translate visual intent into JSONL.

### DO NOT: Make Traps Ambiguous
Every trap must have exactly one correct resolution per IC-01 rules. If multiple valid forms exist, specify required style in target description.

### DO NOT: Generate Mathematically Incorrect Content
All expressions must be mathematically valid. The challenge tests LaTeX/JSONL skills, not math knowledge.

### DO NOT: Exceed 5 Traps Per Challenge
Maximum trap count is `difficulty + 1` (capped at 5 for Level 5). Quality over quantity.

### DO NOT: Ignore IC-03 Recommendation When Present
If progress-track provides a recommendation, it MUST influence generation. Ignoring it breaks the Continuous Optimization Loop.

### DO NOT: Use Commands Not in IC-01 Pool
All LaTeX commands must exist in IC-01 commands[] for selected domain(s). Commands outside the pool create untestable constructs.

### DO NOT: Reveal Golden Answer Metadata to Trainee
trap_annotations, scoring_weight, incorrect_alternatives are evaluator-only (IC-06 visibility: "hidden").

### DO NOT: Generate Drill-Mode Challenges for Production Pipeline
Pipeline A (drill) ONLY. IC-03 mode must be "drill". Production QC starts at image-preprocess.

## Transitions

### Receives From (Interface Contracts)

| Source Skill | IC | Data Expected | Key Fields |
|-------------|-----|---------------|------------|
| reference-build | IC-01 | Command pool + escape rules + OCR patterns + trap catalog | `command_pool.{domains[].commands[], escape_rules[], ocr_confusions[], trap_catalog[], tier_distribution}` |
| progress-track | IC-03 | Adaptive difficulty recommendation | `recommendation.{next_difficulty, difficulty_delta, focus_rules[], weak_patterns[].{category, pass_rate, consecutive_failures, trend}, focus_weight, domain_performance[], suggested_topic, mode}` |
| User | -- | Topic preference, difficulty override | `[topic] [difficulty:1-5]` via argument-hint |

### Sends To (Interface Contracts)

| Target Skill | IC | Data Produced | Key Fields |
|-------------|-----|---------------|------------|
| jsonl-validate | IC-04 | Challenge spec | `challenge_spec.{challenge_id, mode, difficulty, topic, expected_structure, trap_list[].{trap_id, category, target_rule, description, severity_if_failed}, escape_rules_tested[]}` |
| latex-parse | IC-05 | Expected constructs | `expected_constructs.{challenge_id, mode, difficulty, constructs[].{construct_type, expected_count, nesting_depth, specific_commands[]}, domain_rules[], parse_depth}` |
| render-evaluate | IC-06 | Golden answer (hidden) | `golden_answer.{challenge_id, mode, difficulty, jsonl_string, json_parsed, rendered_description, element_list[], trap_annotations[].{trap_id, location_in_jsonl, correct_form, incorrect_alternatives[], scoring_weight}, visibility:"hidden"}` |

### Failure Routes

| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| IC-01 missing | Self (fallback mode) | Built-in minimal command set |
| IC-03 mode mismatch | Lead (error) | Mode rejection signal |
| IC-03 invalid delta | Self (clamped) | Clamped difficulty_delta |
| Topic not in pool | Self (substituted domain) | Nearest domain mapping |

## Quality Gate

- IC-04 challenge_spec validates: all REQUIRED fields present
- IC-05 expected_constructs: constructs[] non-empty, parse_depth set per difficulty
- IC-06 golden_answer.jsonl_string passes JSON.parse() with valid LaTeX
- Trap count matches difficulty +/-1; 80% weak-area allocation when focus_weight >= 0.6
- Every trap_list[].trap_id references valid IC-01 trap_catalog entry (or fallback set)
- Every trap_annotations[].trap_id exists in trap_list[] (cross-reference consistency)
- char_start/char_end positions accurate in trap_annotations
- Challenge type matches Decision Points selection criteria
- Mathematical content accurate; Korean text grammatically correct (L3+)
- Mode is "drill" in IC-04, IC-05, IC-06; visibility: "hidden" on IC-06
- No LaTeX commands outside IC-01 pool (or documented fallback set)

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
trap_allocation: {weak_area: 2, retention: 1}
construct_categories: [aligned, text, quantifiers]
contracts_produced: [IC-04, IC-05, IC-06]
fallback_mode: false
```

### L2

**Target Rendering Description** (visible to trainee): Visual description of rendered output with formatting requirements and verbatim text. For OCR-correction: OCR-degraded source. NEVER show LaTeX code.

**Hidden Evaluator Data**: IC-04 challenge_spec (challenge_id, mode, difficulty, topic, expected_structure, trap_list[] with severity, escape_rules_tested[]), IC-05 expected_constructs (constructs[] with nesting/commands, domain_rules[] with severity, parse_depth), IC-06 golden_answer (verified JSONL string, element_list, trap_annotations with char positions and scoring weights, visibility: "hidden").
