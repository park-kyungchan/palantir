---
name: progress-track
description: |
  [D2·Eval·Progress] Terminal Pipeline A evaluator + feedback loop. Aggregates multi-drill results, identifies weak patterns, calculates 4-level mastery, persists to progress.yaml, generates IC-03 recommendation.

  WHEN: After golden-correct (IC-11). Terminal D2. User-invocable: report/reset.
  DOMAIN: eval (1/1). Terminal + loop: progress-track->IC-03->challenge-generate. Pipeline A only.
  INPUT_FROM: IC-10 trap_results (score, category_breakdown, render_status), IC-11 correction_report (corrections[], severity, rule_violated, badge).
  OUTPUT_TO: IC-03 recommendation (next_difficulty, difficulty_delta+/-1, focus_rules R1-R5, weak_patterns[], focus_weight, domain_performance[]).
  PERSISTENCE: crowd_works/data/progress.yaml. Cross-cutting C: Optimization Loop.

  METHODOLOGY: (1) Load IC-10+IC-11+progress.yaml, (2) Merge category_breakdown+corrections, (3) Domain-separated+per-category mastery, (4) Pattern ID: failures+errors+trend, (5) IC-03: delta+/-1, focus, persist.
user-invocable: true
disable-model-invocation: false
argument-hint: "[report|reset]"
---

# Eval -- Progress Track (Pipeline A Terminal)

## Execution Model
- **After drill**: Auto-triggered when golden-correct completes. Record IC-10 + IC-11 results, update cumulative stats, generate IC-03 recommendation for next challenge-generate cycle.
- **On demand**: User invokes with "report" for full progress dashboard. Reads progress.yaml, generates cumulative analysis without recording new drill.
- **Reset**: User invokes with "reset" to clear progress.yaml and start fresh. Confirmation prompt before destructive action.
- **Pipeline A only** (AD-1): progress-track processes drill mode data exclusively. Production mode data routes through Pipeline B (qc-report). If mode != "drill" in upstream data, reject with error.

## Decision Points

### Mastery Level Classification
4-level system matching IC-03 contract (overall_level enum):

| Mastery Level | Pass Rate | Description | Difficulty Action |
|---------------|-----------|-------------|-------------------|
| **Novice** | 0-40% | Frequent errors, needs focused drill | difficulty_delta: -1 (floor: Level 1) |
| **Developing** | 41-70% | Improving but inconsistent | difficulty_delta: 0 (maintain) |
| **Proficient** | 71-90% | Mostly correct, occasional slips | difficulty_delta: +1 (ceiling: Level 5) |
| **Master** | 91-100% | Consistent accuracy | difficulty_delta: +1, composite challenges |

Applied per-category (7 categories) and per-domain independently. Overall mastery = weighted average across categories (weighted by attempt count).

### Difficulty Adjustment Rules
```
INPUT: category mastery levels, consecutive pass/fail counts, overall mastery
OUTPUT: difficulty_delta (-1, 0, or +1 ONLY -- no jumps >1)

IF any category has consecutive_failures >= 3 AND mastery == Novice:
  -> difficulty_delta: -1 (floor: Level 1)
  -> focus_weight: 0.8 (increase focus on weak area)
  -> Rationale: "Persistent weakness requires lower difficulty for foundation building"

ELIF overall mastery >= Proficient AND consecutive_passes >= 3 across all categories:
  -> difficulty_delta: +1 (ceiling: Level 5)
  -> focus_weight: 0.5 (balance weak and mastered areas)
  -> Rationale: "Consistent proficiency supports difficulty increase"

ELIF overall mastery == Master AND all 7 categories == Master:
  -> difficulty_delta: +1 to Level 5
  -> Recommend composite challenges (multiple categories combined)
  -> Rationale: "Full mastery -- graduation track"

ELIF any category regressed (dropped 2+ mastery levels since last drill):
  -> difficulty_delta: -1
  -> Flag regression in IC-03 weak_patterns[].trend = "critical"
  -> HITL trigger: mastery drop >= 2 levels (Cross-cutting theme D)
  -> Rationale: "Regression detected -- stabilize before advancing"

ELSE:
  -> difficulty_delta: 0
  -> focus_weight: 0.7 (default -- 70% traps from weak areas)
```

### Domain-Separated Tracking (REQ-PT-04)
Map IC-10 `challenge_metadata.topic` to domains:
```
Domain mapping (topic -> domain):
  calculus, integration, differentiation, limits -> "calculus"
  linear_algebra, matrices, vectors, eigenvalues -> "linear_algebra"
  set_theory, logic, quantifiers, proofs         -> "set_theory"
  statistics, probability, distributions          -> "statistics"
  (unmapped topics)                               -> "general"
```

Per-domain tracking stored in `progress.yaml.cumulative_stats.by_domain{}`:
- domain pass_rate = total passes / total attempts across all drills in that domain
- domain mastery = classify pass_rate using 4-level thresholds
- IC-03 `domain_performance[]` populated from this data
- `recommended` field in domain_performance: true if domain mastery < Developing

### Pattern Identification (REQ-PT-02)
A **pattern** is a recurring error identified across multiple drills:
```
Pattern definition:
  - Same rule_violated (from IC-11 corrections[].rule_violated)
  - Same category (from IC-11 corrections[].category)
  - Appears in >= 3 separate drills

Pattern output (maps to IC-03 weak_patterns[].specific_errors[]):
  - "Missing \\, before dx (R1, SEMANTIC) -- 5 occurrences across 4 drills"
  - "Unescaped backslash in \\frac (R1, ESCAPE) -- 3 occurrences across 3 drills"

Pattern tracking in progress.yaml:
  error_patterns:
    - rule: "R1"
      category: "ESCAPE"
      description: "backslash double-escape in \\frac"
      drill_ids: [3, 5, 7]
      occurrence_count: 5
      last_seen: "2026-02-15"
```

### Trend Calculation
Trend classification for each category, based on last 3+ drills:
```
improving:  last 3 pass_rates strictly increasing (e.g., 40% -> 55% -> 70%)
stable:     last 3 pass_rates within +/-5% variance (e.g., 65% -> 68% -> 63%)
declining:  last 3 pass_rates strictly decreasing (e.g., 80% -> 65% -> 50%)
critical:   consecutive_failures >= 3 AND current pass_rate < 40%
```
- Trend requires minimum 3 data points. With < 3 drills, trend = "insufficient_data".
- Trend feeds IC-03 `weak_patterns[].trend` field.
- "critical" trend triggers HITL review suggestion (Cross-cutting theme D).

### Progress Report Triggers
```
IF user invokes with "report":
  -> Generate full progress dashboard (L2 format)
  -> No new drill data recorded

ELIF drill_count % 5 == 0:
  -> Auto-generate mini progress summary alongside normal IC-03 output

ELIF any mastery level changes (up or down):
  -> Report the level change in IC-03 difficulty_rationale

ELIF regression detected (mastery drops 2+ levels):
  -> Full alert with HITL trigger recommendation
```

## Methodology

### 1. Load Inputs and State
Read IC-10 (trap_results from render-evaluate) + IC-11 (correction_report from golden-correct). Load `crowd_works/data/progress.yaml` for cumulative state.

**IC-10 key fields consumed**:
- `challenge_id`, `mode` (must be "drill"), `evaluated_at`
- `results` (map of trap_type -> PASS/FAIL)
- `score.total` ("N/M"), `score.total_numeric` (0.0-1.0), `score.by_category` (4 scoring categories)
- `render_status` (FULL/PARTIAL/CRASH)
- `challenge_metadata.difficulty`, `challenge_metadata.topic`, `challenge_metadata.trap_count`, `challenge_metadata.trap_types[]`
- `category_breakdown[]` (per-category: category, tested, result, instance_count, pass_count, fail_count)

**IC-11 key fields consumed**:
- `challenge_id`, `mode` (must match IC-10)
- `corrections[]` (each: correction_id, category, severity, rule_violated, description, confidence, hitl_required)
- `verification.badge` (VERIFIED_3STAGE / VERIFIED_PARTIAL / UNVERIFIED)
- `summary.total_corrections`, `summary.by_category{}`, `summary.by_severity{}`, `summary.correction_density`, `summary.estimated_learning_value`

**Validation checks**:
- IC-10 `mode` == "drill" (reject production data)
- IC-10 `render_status` == CRASH -> override: record ALL traps as FAIL regardless of individual results
- IC-11 `verification.badge` != VERIFIED_3STAGE -> log verification gap (still record results)
- IC-10 and IC-11 `challenge_id` must match (mismatch = error)
- Empty IC-11 corrections[] = perfect score (0 corrections is valid)

### 2. Record Drill Result
Merge IC-10 category_breakdown + IC-11 corrections into a single drill record:

```yaml
drill_record:
  drill_id: int          # Auto-increment from progress.yaml.drill_history.length + 1
  challenge_id: string   # From IC-10/IC-11
  timestamp: string      # IC-10.evaluated_at (ISO 8601)
  difficulty: int        # IC-10.challenge_metadata.difficulty
  topic: string          # IC-10.challenge_metadata.topic
  domain: string         # Mapped from topic (see Domain-Separated Tracking)
  score_total: string    # IC-10.score.total ("7/10")
  score_numeric: float   # IC-10.score.total_numeric (0.7)
  render_status: string  # IC-10.render_status
  trap_results: {}       # IC-10.results (per-trap PASS/FAIL)
  category_breakdown:    # IC-10.category_breakdown (7 categories)
    ESCAPE: {tested: true, pass: 2, fail: 1}
    GROUPING: {tested: true, pass: 1, fail: 0}
    # ... all 7 categories
  corrections:           # From IC-11
    total: int           # IC-11.summary.total_corrections
    by_category: {}      # IC-11.summary.by_category
    by_severity: {}      # IC-11.summary.by_severity
    rules_violated: []   # Extracted from IC-11.corrections[].rule_violated (unique)
    patterns: []         # Extracted from IC-11.corrections[].description (for pattern tracking)
  verification_badge: string  # IC-11.verification.badge
  learning_value: string      # IC-11.summary.estimated_learning_value
```

Append to `progress.yaml.drill_history[]`.

### 3. Update Cumulative Statistics
Update domain-separated tracking (REQ-PT-04) and per-category mastery:

**Per-category update** (7 categories: ESCAPE, GROUPING, OPERATOR, SIZING, TEXT, ENVIRONMENT, SEMANTIC):
```yaml
cumulative_stats.by_category.{CATEGORY}:
  total_attempts: int       # += category_breakdown[cat].instance_count (if tested)
  total_passes: int         # += category_breakdown[cat].pass_count
  total_fails: int          # += category_breakdown[cat].fail_count
  pass_rate: float          # total_passes / total_attempts
  mastery: enum             # Classify pass_rate: Novice/Developing/Proficient/Master
  previous_mastery: enum    # For regression detection
  consecutive_passes: int   # Reset to 0 on any FAIL, increment on PASS
  consecutive_failures: int # Reset to 0 on any PASS, increment on FAIL
  last_result: enum         # PASS or FAIL (from this drill)
```

**Per-domain update** (mapped from topic):
```yaml
cumulative_stats.by_domain.{domain}:
  total_drills: int
  total_score_numeric: float  # Sum of score_numeric across drills in this domain
  pass_rate: float            # Average score_numeric
  mastery: enum               # Classify pass_rate
  topics_seen: []             # Unique topics encountered
```

**Overall update**:
```yaml
cumulative_stats.overall:
  total_drills: int
  total_score: string         # "N/M" cumulative
  overall_pass_rate: float    # Weighted average of category pass_rates (by attempt count)
  overall_mastery: enum       # Classify overall_pass_rate
  overall_level: enum         # Same as overall_mastery (IC-03 field name)
```

### 4. Identify Weak Patterns
Scan drill_history for recurring error patterns (REQ-PT-02):

**Step 4a -- Category-level weakness**:
- Which categories have mastery == Novice? -> Add to IC-03 focus_rules
- Which categories have consecutive_failures >= 3? -> Flag as critical weakness
- Which categories regressed from previous mastery level? -> Flag regression

**Step 4b -- Error-level patterns**:
- Group IC-11 corrections by (rule_violated, category) across all drills
- If same (rule, category) appears in >= 3 drills: create named pattern
- Extract description string for IC-03 weak_patterns[].specific_errors[]

**Step 4c -- Trend classification**:
- For each category with >= 3 data points: calculate trend (improving/stable/declining/critical)
- For each domain with >= 3 data points: calculate domain trend

**Step 4d -- Build IC-03 weak_patterns[]**:
```yaml
weak_patterns:
  - category: "TEXT"
    pass_rate: 0.33
    mastery: "Novice"
    consecutive_failures: 3
    specific_errors:
      - "Missing spaces in \\text{ if } command (R3, TEXT) -- 4 occurrences"
      - "Nested $ inside \\text{} (R3, TEXT) -- 3 occurrences"
    trend: "critical"
  - category: "SIZING"
    pass_rate: 0.44
    mastery: "Developing"
    consecutive_failures: 1
    specific_errors:
      - "Missing \\left/\\right for auto-sizing (R4, SIZING) -- 2 occurrences"
    trend: "declining"
```

### 5. Generate IC-03 Recommendation
Assemble the IC-03 recommendation output for challenge-generate:

```yaml
recommendation:
  version: "1.0"
  challenge_id: string          # ID of the drill just completed
  drill_count: int              # Total drills completed
  overall_mastery: float        # 0.0-1.0 (overall_pass_rate)
  overall_level: enum           # Novice/Developing/Proficient/Master
  next_difficulty: int          # Current difficulty + difficulty_delta (clamped 1-5)
  difficulty_delta: int         # -1, 0, or +1 ONLY (never jumps >1)
  difficulty_rationale: string  # Human-readable explanation for delta
  focus_rules: []               # R1-R5 rules most commonly violated in weak categories
  focus_commands: []             # Specific LaTeX commands causing errors
  weak_patterns: []             # From Step 4d (full weak_patterns array)
  focus_weight: float           # Default 0.7 (70% traps from weak areas)
  domain_performance: []        # From cumulative_stats.by_domain
    # - domain: "calculus", pass_rate: 0.78, mastery: "Proficient", recommended: false
    # - domain: "set_theory", pass_rate: 0.45, mastery: "Developing", recommended: true
  suggested_trap_types: []      # Trap types to prioritize based on weak patterns
  suggested_topic: string       # Domain with lowest mastery, or user preference
  mode: "drill"                 # Always "drill" for Pipeline A
```

**Persist to progress.yaml** (REQ-PT-06):
Write the complete state (drill_history[], cumulative_stats{}, mastery_levels{}, error_patterns[], last_recommendation{}) to `crowd_works/data/progress.yaml`.

**Validation before output**:
- difficulty_delta is exactly -1, 0, or +1 (enforce constraint)
- next_difficulty is clamped to 1-5 range
- overall_level matches overall_mastery threshold classification
- All weak_patterns entries have valid category enum values (7 categories)
- All focus_rules entries are valid (R1-R5 or SEM-*)

## Failure Handling

### progress.yaml Missing (First Drill or File Deleted)
- **Cause**: First drill ever, or file was accidentally deleted
- **Action**: Initialize empty state. Create progress.yaml with empty drill_history[], zero-initialized cumulative_stats, default mastery_levels (all Novice).
- **Defaults**: difficulty_delta: 0, next_difficulty: 2, focus_weight: 0.7, overall_mastery: 0.0, overall_level: "Novice"
- **Route**: Normal IC-03 output with first-drill defaults

### progress.yaml Corrupted (Parse Failure)
- **Cause**: YAML syntax error, incomplete write, manual editing error
- **Action**: Attempt to rebuild from drill_history[] array if parseable. If drill_history is also corrupted, reset to empty state with warning.
- **Recovery**: Back up corrupted file as `progress.yaml.bak`, write fresh state.
- **Route**: Normal IC-03 output. Log corruption event in L2.

### IC-10 render_status == CRASH
- **Cause**: JSON parse failure in upstream JSONL validation
- **Action**: Override ALL trap results to FAIL regardless of individual IC-10.results values. Record drill with score_numeric: 0.0.
- **Difficulty impact**: difficulty_delta: -1 (crash indicates fundamental issue), unless already at Level 1.
- **Route**: IC-03 with crash-adjusted recommendation. difficulty_rationale: "CRASH render status -- fundamental JSONL issue requires lower difficulty."

### IC-11 verification.badge != VERIFIED_3STAGE
- **Cause**: Golden answer was only partially verified or unverified
- **Action**: Still record results (corrections are informative even without full verification). Log verification gap in drill_record.
- **Confidence adjustment**: If UNVERIFIED, add note to IC-03 difficulty_rationale: "Correction data from unverified golden -- recommendation confidence reduced."
- **Route**: Normal IC-03 output with verification gap logged

### IC-10 and IC-11 challenge_id Mismatch
- **Cause**: Upstream routing error, stale data from different drill cycle
- **Action**: ABORT recording. Do not update progress.yaml. Report mismatch to Lead.
- **Route**: Error signal. No IC-03 output.

### All Categories Master at Level 5
- **Cause**: Trainee has mastered all 7 categories at maximum difficulty
- **Action**: Generate "graduation" report. Recommend transition to Pipeline B (production QC practice) or real data construction.
- **Route**: IC-03 with `difficulty_delta: 0`, `next_difficulty: 5`, `difficulty_rationale: "Full mastery achieved -- recommend production practice or composite challenges."`

### Score Regression After Mastery
- **Cause**: Category drops from Proficient/Master back to Developing/Novice
- **Action**: Flag regression with trend: "critical". If drop >= 2 levels: trigger HITL review recommendation (Cross-cutting theme D).
- **Route**: IC-03 with difficulty_delta: -1, focused review drill recommendation

## Anti-Patterns

### DO NOT: Track Only Pass/Fail
Category-level granularity is essential. "3 errors" is useless without knowing they were all TEXT errors. Always record per-category breakdown from IC-10 `category_breakdown[]` and per-correction detail from IC-11 `corrections[]`.

### DO NOT: Recommend Difficulty Jumps >1
`difficulty_delta` MUST be exactly -1, 0, or +1. Level 2 to Level 4 skips foundational patterns. This is an IC-03 contract constraint -- violation breaks challenge-generate expectations.

### DO NOT: Ignore Regression
A trainee going from Proficient (80%) to Developing (50%) in a category signals a conceptual gap, not randomness. Always flag regression with trend classification and adjust difficulty downward.

### DO NOT: Report Raw Numbers Only
Trends matter more than snapshots. "TEXT: 33% (critical, declining)" is more useful than "TEXT: 33%". Always include trend indicators and consecutive failure counts.

### DO NOT: Skip Persistence
Every drill result MUST be persisted to `crowd_works/data/progress.yaml` before generating IC-03 output. If persistence fails, log error but still output IC-03 (in-memory state is valid for current cycle).

### DO NOT: Process Production Mode Data
progress-track is Pipeline A only (AD-1). If IC-10 or IC-11 has `mode: "production"`, reject immediately. Production data routes through Pipeline B (qc-report).

### DO NOT: Calculate Trends with < 3 Data Points
Trend classification requires minimum 3 drills of data for that category. With fewer, report trend as "insufficient_data" -- never extrapolate from 1-2 points.

## Transitions

### Receives From
| Source Skill | IC | Data Expected | Key Fields |
|-------------|-----|---------------|------------|
| render-evaluate | IC-10 | trap_results | score (total, total_numeric, by_category), results (trap->PASS/FAIL), render_status, challenge_metadata (difficulty, topic, trap_count, trap_types), category_breakdown[] |
| golden-correct | IC-11 | correction_report | corrections[] (category, severity, rule_violated, description, confidence, hitl_required), verification.badge, summary (total_corrections, by_category, by_severity, correction_density, estimated_learning_value) |
| User | -- | "report" or "reset" command | Argument string |

### Sends To
| Target Skill | IC | Data Produced | Trigger Condition |
|-------------|-----|---------------|-------------------|
| challenge-generate | IC-03 | recommendation | Every drill cycle (feedback loop). Contains: overall_mastery, next_difficulty, difficulty_delta, focus_rules, weak_patterns, focus_weight, domain_performance, suggested_trap_types, suggested_topic |
| reference-build | -- | Weak categories for targeted reference refresh | When any category mastery < Developing AND consecutive_failures >= 3 |
| User | -- | Progress dashboard | On demand ("report"), every 5 drills (mini summary), or on mastery level change |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| challenge_id mismatch | Lead (error) | Mismatch details, no IC-03 output |
| progress.yaml corrupted | Continue (degraded) | Rebuilt or reset state, corruption logged |
| Production mode data | Lead (reject) | Mode validation failure |

## Quality Gate
- IC-03 recommendation validates against full schema (all required fields present)
- `difficulty_delta` is exactly -1, 0, or +1 (never any other value)
- `next_difficulty` clamped to 1-5 range
- Mastery levels consistent with pass_rate thresholds (Novice 0-40%, Developing 41-70%, Proficient 71-90%, Master 91-100%)
- All `weak_patterns[].category` values are valid 7-category enum members
- All `focus_rules[]` values are valid (R1-R5 or SEM-*)
- `progress.yaml` persisted after every drill (REQ-PT-06)
- Trend calculations based on >= 3 data points (no extrapolation)
- Per-domain mastery calculated and included in IC-03 `domain_performance[]`
- CRASH render_status results in all-FAIL recording and difficulty decrease

## Output

### L1
```yaml
domain: eval
skill: progress-track
status: updated
persistence_path: "crowd_works/data/progress.yaml"
contracts_produced: [IC-03]
total_drills: 15
overall_mastery: 0.653
overall_level: Developing
category_mastery:
  ESCAPE: {pass_rate: 0.83, mastery: Proficient, trend: improving}
  GROUPING: {pass_rate: 0.88, mastery: Proficient, trend: stable}
  OPERATOR: {pass_rate: 0.75, mastery: Proficient, trend: stable}
  SIZING: {pass_rate: 0.44, mastery: Developing, trend: declining}
  TEXT: {pass_rate: 0.33, mastery: Novice, trend: critical}
  ENVIRONMENT: {pass_rate: 0.60, mastery: Developing, trend: stable}
  SEMANTIC: {pass_rate: 0.50, mastery: Developing, trend: stable}
domain_mastery:
  calculus: {pass_rate: 0.78, mastery: Proficient}
  linear_algebra: {pass_rate: 0.52, mastery: Developing}
  set_theory: {pass_rate: 0.45, mastery: Developing}
weak_areas: [TEXT, SIZING]
recommendation:
  next_difficulty: 2
  difficulty_delta: -1
  focus_rules: [R1, R3, R4]
  focus_weight: 0.7
```

### L2
Full progress dashboard with:
- Cumulative progress dashboard (category x mastery grid with trend arrows)
```
Category Mastery Dashboard (15 drills):
  ESCAPE:      [=========>  ] 83% Proficient  (improving)
  GROUPING:    [=========>  ] 88% Proficient  (stable)
  OPERATOR:    [=======>    ] 75% Proficient  (stable)
  SIZING:      [====>       ] 44% Developing  (declining)
  TEXT:         [===>        ] 33% Novice      (critical) [ALERT]
  ENVIRONMENT: [======>     ] 60% Developing  (stable)
  SEMANTIC:    [=====>      ] 50% Developing  (stable)
```
- Domain performance breakdown with recommendation flags
- Trend analysis per category and per domain (improving/stable/declining/critical)
- Weak area analysis with specific recurring error patterns and rule references
- IC-03 recommendation summary (next_difficulty, difficulty_delta, focus_rules, rationale)
- Regression alerts with HITL trigger recommendations when applicable
- Historical drill result log (last 10 drills with scores and key findings)

### progress.yaml Schema (REQ-PT-06)
```yaml
# crowd_works/data/progress.yaml
version: "1.0"
last_updated: "2026-02-15T14:30:00Z"
drill_history:
  - drill_id: 1
    challenge_id: "CH-001"
    timestamp: "2026-02-15T10:00:00Z"
    difficulty: 2
    topic: "fractions_basic"
    domain: "calculus"
    score_total: "7/10"
    score_numeric: 0.7
    render_status: "FULL"
    category_breakdown:
      ESCAPE: {tested: true, pass: 2, fail: 1}
      GROUPING: {tested: true, pass: 1, fail: 0}
      TEXT: {tested: true, pass: 0, fail: 2}
    corrections:
      total: 3
      by_severity: {FAIL: 2, WARN: 1}
      rules_violated: [R1, R3]
    verification_badge: "VERIFIED_3STAGE"
cumulative_stats:
  overall:
    total_drills: 15
    overall_pass_rate: 0.653
    overall_mastery: "Developing"
  by_category:
    ESCAPE: {total_attempts: 12, total_passes: 10, pass_rate: 0.833, mastery: "Proficient", consecutive_passes: 3, consecutive_failures: 0}
    TEXT: {total_attempts: 6, total_passes: 2, pass_rate: 0.333, mastery: "Novice", consecutive_passes: 0, consecutive_failures: 3}
  by_domain:
    calculus: {total_drills: 8, pass_rate: 0.78, mastery: "Proficient", topics_seen: ["fractions_basic", "integration", "limits"]}
    set_theory: {total_drills: 4, pass_rate: 0.45, mastery: "Developing", topics_seen: ["set_builder", "quantifiers"]}
error_patterns:
  - rule: "R1"
    category: "ESCAPE"
    description: "backslash double-escape in \\frac"
    drill_ids: [3, 5, 7]
    occurrence_count: 5
    last_seen: "2026-02-15"
  - rule: "R3"
    category: "TEXT"
    description: "missing spaces in \\text{ if } command"
    drill_ids: [4, 6, 8, 10]
    occurrence_count: 7
    last_seen: "2026-02-15"
last_recommendation:
  challenge_id: "CH-015"
  next_difficulty: 2
  difficulty_delta: -1
  focus_rules: [R1, R3, R4]
  focus_weight: 0.7
```
