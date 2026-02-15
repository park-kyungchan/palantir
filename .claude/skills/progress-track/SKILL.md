---
name: progress-track
description: |
  [D2·Eval·Progress] Learning analytics tracker for math data construction training. Aggregates per-drill results, identifies persistent weak areas, recommends difficulty adjustments, generates progress reports with mastery scores.

  WHEN: After golden-correct completes drill cycle. Terminal evaluator. Also invocable for progress report.
  DOMAIN: eval (skill 1 of 1). Terminal + feedback loop to challenge-generate.
  INPUT_FROM: golden-correct (correction count + categories), render-evaluate (trap results + score).
  OUTPUT_TO: challenge-generate (difficulty recommendation + weak areas for next drill).

  METHODOLOGY: (1) Record drill result (score, corrections, trap pass/fail), (2) Update cumulative stats per category, (3) Identify persistent weak areas (≥3 consecutive failures), (4) Calculate mastery score per domain/category, (5) Recommend next difficulty and focus areas.
  OUTPUT_FORMAT: L1 YAML cumulative stats + mastery scores, L2 progress dashboard with trend analysis.
user-invocable: true
disable-model-invocation: false
argument-hint: "[report|reset]"
---

# Eval — Progress Track

## Execution Model
- **After drill**: Auto-triggered. Record results, update stats, recommend next challenge.
- **On demand**: User invokes for progress report. Generate cumulative dashboard.
- **Reset**: User invokes with "reset" to clear history and start fresh.

## Decision Points

### Mastery Level Classification
Based on cumulative pass rate per category:

| Mastery Level | Pass Rate | Description | Action |
|---------------|-----------|-------------|--------|
| **Novice** | 0-40% | Frequent errors, needs drill | Stay at current difficulty |
| **Developing** | 41-70% | Improving but inconsistent | Maintain difficulty, focus drills |
| **Proficient** | 71-90% | Mostly correct, occasional slips | Increase difficulty by 1 |
| **Master** | 91-100% | Consistent accuracy | Move to next category or composite |

### Difficulty Adjustment Rules
```
IF category mastery == Novice AND consecutive_failures >= 3:
  -> REDUCE difficulty by 1 (floor: Level 1)
  -> Focus next 3 challenges on this category exclusively

ELIF category mastery == Proficient AND consecutive_passes >= 3:
  -> INCREASE difficulty by 1 (ceiling: Level 5)
  -> Mix categories in next challenge

ELIF category mastery == Master AND all categories Master:
  -> COMPOSITE challenges (multiple categories combined)
  -> Level 5 Hell-mode drills

ELSE:
  -> MAINTAIN current difficulty
  -> Weight weak categories at 70% in challenge selection
```

### Weak Area Detection
A category is "persistently weak" when:
- ≥3 consecutive FAIL results in that category
- OR overall pass rate drops below 40% after 5+ attempts
- OR same specific error pattern repeats 3+ times

### Progress Report Triggers
```
IF user invokes with "report":
  -> Generate full dashboard
ELIF drill_count % 5 == 0:
  -> Auto-generate mini progress summary
ELIF mastery level changes:
  -> Report the level change
```

## Methodology

### 1. Record Drill Result
After each drill cycle, capture:

```yaml
drill_result:
  drill_id: N
  timestamp: "YYYY-MM-DD HH:MM"
  challenge:
    topic: "aligned_equations"
    difficulty: 3
    trap_types: [ESCAPE_backslash, TEXT_spacing, SIZING_left_right]
  score: "7/10"
  corrections: 3
  correction_categories: {ESCAPE: 1, SIZING: 1, TEXT: 1}
  trap_results:
    ESCAPE_backslash: PASS
    TEXT_spacing: FAIL
    SIZING_left_right: FAIL
  render_status: PARTIAL
```

### 2. Update Cumulative Statistics
Maintain running statistics per category:

```yaml
cumulative:
  total_drills: 15
  total_score: "98/150"  # 65.3%
  by_category:
    ESCAPE:
      attempts: 12
      passes: 10
      pass_rate: 83.3%
      mastery: Proficient
      consecutive_passes: 3
    GROUPING:
      attempts: 8
      passes: 7
      pass_rate: 87.5%
      mastery: Proficient
      consecutive_passes: 2
    TEXT:
      attempts: 6
      passes: 2
      pass_rate: 33.3%
      mastery: Novice
      consecutive_failures: 3  # ALERT: persistent weakness
    SIZING:
      attempts: 9
      passes: 4
      pass_rate: 44.4%
      mastery: Developing
      consecutive_failures: 1
```

### 3. Identify Persistent Weak Areas
Scan for patterns:
- **Category-level**: Which categories have Novice mastery?
- **Error-level**: Which specific errors repeat? (e.g., "missing `\,` before dx" recurring)
- **Trap-level**: Which trap types consistently fail?

Generate weak area report:
```
PERSISTENT WEAKNESS DETECTED:
  Category: TEXT (text-mode spacing)
  Pass rate: 33.3% (2/6)
  Consecutive failures: 3
  Most common error: Missing spaces in \text{ if } command
  RECOMMENDATION: 3 focused TEXT-only drills at Level 2 before mixing
```

### 4. Calculate Mastery Scores
Per domain and per category:

```
Overall Mastery: 65.3% (Developing)
Domain Mastery:
  - Calculus: 78% (Proficient)
  - Linear Algebra: 52% (Developing)
  - Set Theory: 45% (Developing)

Category Mastery:
  - ESCAPE: 83% (Proficient) ↑
  - GROUPING: 88% (Proficient) ↑
  - OPERATOR: 75% (Proficient) →
  - SIZING: 44% (Developing) ↓
  - TEXT: 33% (Novice) ↓↓ [ALERT]
  - ENVIRONMENT: 60% (Developing) →
  - SEMANTIC: 50% (Developing) →
```

### 5. Recommend Next Challenge
Based on cumulative analysis:

```yaml
recommendation:
  next_difficulty: 2  # reduced from 3 due to TEXT weakness
  focus_categories: [TEXT, SIZING]  # weak areas
  focus_weight: 0.7  # 70% of traps from weak areas
  topic_suggestion: "cases_with_text"  # combines weak areas
  rationale: "TEXT mastery at Novice (33%). 3 consecutive failures. Recommend focused drilling at lower difficulty before advancing."
```

## Failure Handling

### No History Available
- **Cause**: First drill or after reset
- **Action**: Record result, use defaults for recommendations
- **Route**: challenge-generate (default difficulty Level 2)

### All Categories Master
- **Cause**: Trainee has mastered all categories at Level 5
- **Action**: Generate "graduation" report, recommend real data construction practice
- **Route**: User (training complete signal)

### Score Regression After Mastery
- **Cause**: Category drops from Proficient back to Developing
- **Action**: Flag regression, recommend review drill
- **Route**: challenge-generate (focused review at previous mastery level)

## Anti-Patterns

### DO NOT: Track Only Pass/Fail
Category-level granularity is essential. "3 errors" is useless without knowing they were all TEXT errors.

### DO NOT: Recommend Difficulty Jumps >1
Progress should be gradual. Level 2 → Level 4 skips foundational patterns.

### DO NOT: Ignore Regression
A trainee going from 80% → 50% in a category signals a conceptual gap, not randomness. Flag it.

### DO NOT: Report Raw Numbers Only
Trends matter more than snapshots. "TEXT: 33% ↓↓" is more useful than "TEXT: 33%."

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| golden-correct | Correction count, categories, severity | YAML L1 |
| render-evaluate | Trap results, score | YAML L1 |
| User | "report" or "reset" command | Argument |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| challenge-generate | Difficulty recommendation, weak areas, focus weight | Every drill cycle (loop) |
| reference-build | Weak categories for targeted reference refresh | When mastery < Developing |
| User | Progress dashboard | On demand or every 5 drills |

## Quality Gate
- Every drill result recorded with full category breakdown
- Cumulative statistics updated and consistent
- Weak areas identified with evidence (pass rate + consecutive failures)
- Recommendation includes difficulty + focus + rationale
- No stale data (results from >30 days flagged)

## Output

### L1
```yaml
domain: eval
skill: progress-track
status: updated
total_drills: 0
overall_mastery: "0%"
overall_level: Novice
weak_areas: []
recommendation:
  next_difficulty: 2
  focus_categories: []
  focus_weight: 0.7
```

### L2
- Cumulative progress dashboard (category × mastery grid)
- Trend indicators (↑ improving, → stable, ↓ declining, ↓↓ alert)
- Weak area analysis with evidence
- Next challenge recommendation with rationale
- Historical drill result log (last 10)
