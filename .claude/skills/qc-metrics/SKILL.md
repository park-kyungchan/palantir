---
name: qc-metrics
description: |
  [D2·PipelineB·QCMetrics] AggregateProductionQuality from qc-report batch data. Per-worker accuracy, batch trends, error distribution, SLA compliance. Terminal D2 Pipeline B analytics.

  WHEN: After qc-report persists production QC reports. User-invocable for dashboard, trends, or worker review.
  DOMAIN: production eval (D2 Pipeline B). Terminal. No downstream consumers. Analogous to progress-track (Pipeline A).
  INPUT_FROM: qc-report (batch QC reports: batch_id, items[], summary, worker_stats), user invocation (batch|trend|worker:id).
  OUTPUT_TO: PM/PL (metrics dashboard, SLA reports), reference-build (dominant error patterns for targeted refresh).

  METHODOLOGY: (1) Read QC reports, scope by $ARGUMENTS, (2) Aggregate totals/pass-fail/hitl/fidelity/error distribution, (3) Per-worker: accuracy, volume, dominant errors, (4) Trend analysis (>=3 batches): fidelity+error trends, SLA, (5) Dashboard output with status, flags, trends, recommendations.
user-invocable: true
disable-model-invocation: false
argument-hint: "[batch|trend|worker:id]"
---

# QC Metrics -- Production Quality Dashboard (Pipeline B Terminal)

## Execution Model
- **Batch summary**: After a batch QC run, aggregate all QC reports for that batch. Default mode when no arguments provided (processes latest batch).
- **Trend analysis**: Historical analysis across multiple batches. Requires >=3 batches of history for meaningful trends.
- **Worker view**: Per-worker performance deep-dive. Accuracy rate, item volume, dominant error types, comparison to team average.
- **Pipeline B ONLY** (AD-1): qc-metrics processes production mode data exclusively. Drill mode data routes through Pipeline A (progress-track). If upstream data has `mode: "drill"`, reject with error.
- This is the PM/PL analytics dashboard. Output must support decision-making: actionable flags, thresholds, and recommendations -- not raw numbers.

## Decision Points

### Report Type Selection (from $ARGUMENTS)
```
IF $ARGUMENTS contains "batch":
  -> Current batch aggregate metrics
  -> Reads latest batch file from crowd_works/data/qc-reports/
  -> Outputs summary with pass/fail/hitl distribution, error categories, worker stats

ELIF $ARGUMENTS contains "trend":
  -> Multi-batch trend analysis
  -> Reads ALL batch files from crowd_works/data/qc-reports/
  -> Requires >= 3 batches (reject with "insufficient data" if < 3)
  -> Outputs fidelity trend, error category trends, worker performance trends, SLA

ELIF $ARGUMENTS starts with "worker:":
  -> Extract worker_id from "worker:{id}" format
  -> Single worker performance deep-dive across all batches
  -> Reads ALL batch files, filters worker_stats for target worker
  -> Outputs accuracy rate, volume, error patterns, peer comparison

ELSE (no arguments or empty):
  -> Default: Latest batch summary (same as "batch")
```

### Quality Thresholds (REQ-QM-01)

| Metric | GOOD | NEEDS_ATTENTION | CRITICAL |
|--------|------|-----------------|----------|
| Batch avg_fidelity | >= 85% | 70-84% | < 70% |
| Worker accuracy | >= 90% | 75-89% | < 75% |
| SLA compliance | >= 95% items within SLA | 85-94% | < 85% |

Threshold interpretation:
- GOOD: No action needed. Green status indicator.
- NEEDS_ATTENTION: PM review recommended. Yellow status indicator. Include specific areas for improvement.
- CRITICAL: Immediate PM action required. Red status indicator. Include root cause analysis and remediation recommendations.

### Trend Analysis Window (REQ-QM-03)
When report_type == "trend":
```
Short-term:  Last 3 batches  -> Detect immediate quality drops
Medium-term: Last 10 batches -> Identify sustained patterns
Long-term:   All available   -> Establish baselines

Trend classification per metric (requires >= 3 data points):
  improving:  Last 3 values strictly increasing
  stable:     Last 3 values within +/- 3% variance
  declining:  Last 3 values strictly decreasing
  critical:   Declining AND latest value in CRITICAL threshold
```
- Short-term trends drive immediate alerts (declining -> flag)
- Medium-term trends drive process recommendations (sustained decline -> escalate)
- Long-term trends provide baseline context (team average over time)

### Error Distribution Analysis (REQ-QM-04)
Aggregate error categories across batch items:
```yaml
error_heatmap:
  # category x severity matrix
  rows: [ESCAPE, GROUPING, OPERATOR, SIZING, TEXT, ENVIRONMENT, SEMANTIC]
  columns: [CRITICAL, MAJOR, MINOR]
  cells: int[][]  # Count of errors per (category, severity) pair

dominant_errors:
  - category: TEXT
    percentage: 42%  # > 40% threshold
    action: "Route to reference-build for targeted reference refresh"
  - category: ESCAPE
    percentage: 28%
    action: "Monitor -- approaching threshold"
```
- Heatmap data enables PM to visualize error concentration patterns
- Dominant error (> 40% of total errors) triggers recommendation to reference-build for targeted training material refresh
- Identify emerging error categories (new in last 3 batches vs historical baseline)

### SLA Compliance (REQ-QM-05)
```
SLA Definition:
  - Items processed within SLA window (configured per project)
  - Default SLA window: items processed within 24 hours of assignment

SLA Calculation:
  total_items = sum of all items across batch
  on_time_items = items where (processed_at - assigned_at) <= SLA_window
  sla_compliance = on_time_items / total_items

  COMPLIANT:     >= 95%
  AT_RISK:       85-94%
  NON_COMPLIANT: < 85%
```

## Methodology

### 1. Read QC Report Data
Read QC batch reports from `crowd_works/data/qc-reports/`. Select scope based on $ARGUMENTS:

**File discovery**:
- Glob pattern: `crowd_works/data/qc-reports/batch-*.yaml`
- Sort by date (extracted from filename `batch-{date}.yaml`)
- For "batch" mode: read latest file only
- For "trend" mode: read all files
- For "worker:{id}" mode: read all files (filter in Step 3)

**Per-file validation**:
- YAML parse check (skip corrupted files with warning)
- Required fields: batch_id, processed_at, items[], summary, worker_stats
- Missing required field -> skip file, log warning, continue

**Persistence schema consumed** (from qc-report output):
```yaml
batch-{date}.yaml:
  batch_id: string
  processed_at: string       # ISO 8601
  items:
    - file_id: string
      verdict: PASS|FAIL
      fidelity_score: float  # 0.0-1.0
      errors: []             # Per-item error list with category and severity
      hitl_status: string    # flagged|cleared|pending
  summary:
    total: int
    pass: int
    fail: int
    hitl_flagged: int
    avg_fidelity: float
  worker_stats:
    {worker_id}:
      accuracy: float        # 0.0-1.0
      items_processed: int
```

### 2. Aggregate Batch Metrics (REQ-QM-01)
For each batch in scope, compute aggregate metrics:

```yaml
batch_aggregate:
  batch_id: string
  date: string
  total_items: int           # summary.total
  pass_count: int            # summary.pass
  fail_count: int            # summary.fail
  hitl_flagged: int          # summary.hitl_flagged
  pass_rate: float           # pass_count / total_items
  fail_rate: float           # fail_count / total_items
  hitl_rate: float           # hitl_flagged / total_items
  avg_fidelity: float        # summary.avg_fidelity
  quality_status: enum       # GOOD / NEEDS_ATTENTION / CRITICAL (from thresholds)
  error_distribution:        # Aggregate from items[].errors[]
    by_category: {}          # Category -> count
    by_severity: {}          # Severity -> count
    heatmap: {}              # Category x severity matrix (REQ-QM-04)
  sla_compliance: float      # Calculated per SLA rules (REQ-QM-05)
  sla_status: enum           # COMPLIANT / AT_RISK / NON_COMPLIANT
```

**Cross-batch aggregation** (for trend mode):
- Compute rolling averages for avg_fidelity, pass_rate, sla_compliance
- Identify batch-over-batch deltas for trend classification
- Flag batches where quality dropped by > 10% from previous batch

### 3. Per-Worker Statistics (REQ-QM-02)
For each worker appearing in worker_stats across batches:

```yaml
worker_profile:
  worker_id: string          # Anonymized ID (never expose real names)
  batches_active: int        # Number of batches this worker participated in
  total_items_processed: int # Sum across all batches
  overall_accuracy: float    # Weighted average accuracy across batches
  accuracy_status: enum      # HIGH (>= 90%) / NORMAL (75-89%) / FLAGGED (< 75%)
  accuracy_trend: enum       # improving / stable / declining / critical
  dominant_errors: []        # Top 3 error categories for this worker
  comparison_to_team:
    accuracy_delta: float    # Worker accuracy - team average accuracy
    volume_percentile: int   # Percentile rank by items_processed
  flag_reason: string|null   # Reason for FLAGGED status (null if not flagged)
```

**Worker trend** (requires >= 3 batches participation):
- Track accuracy per batch, calculate trend using same classification as batch trends
- Flag workers with declining accuracy trend even if current accuracy is NORMAL
- HITL principle: never auto-flag workers for action -- PM decides (flag_reason is advisory)

**Privacy**: Use anonymized worker IDs in all reports. Never expose worker names in shared dashboards. Worker-specific deep-dive (via `worker:{id}` argument) still uses anonymized IDs.

### 4. Trend Analysis + SLA Compliance (REQ-QM-03, REQ-QM-05)
Generate trend analysis when sufficient history exists (>= 3 batches):

**Fidelity trend**:
```yaml
fidelity_trend:
  short_term:
    window: 3                # Last 3 batches
    values: [0.87, 0.85, 0.83]
    direction: declining     # Strictly decreasing
    alert: true              # Declining fidelity triggers alert
  medium_term:
    window: 10               # Last 10 batches (or all if < 10)
    baseline: 0.86           # Average fidelity over window
    direction: stable
  long_term:
    all_batches: int
    baseline: 0.84           # All-time average
    direction: improving
```

**Error category trends** (per category):
- Track category error count as percentage of total errors per batch
- Identify categories with increasing share (emerging problems)
- Identify categories with decreasing share (resolved problems)

**Worker performance trends**:
- Team average accuracy per batch
- Variance in worker accuracy (high variance = inconsistent team quality)
- New worker onboarding curve (first 3 batches performance vs team baseline)

**SLA compliance trend**:
- Per-batch SLA compliance percentage
- Trend classification (improving/stable/declining/critical)
- Project against SLA target (95%) with trajectory indicator

### 5. Output Dashboard with Actionable Insights
Assemble structured dashboard for PM/PL consumption:

**Quality status summary**:
- Overall quality rating (GOOD / NEEDS_ATTENTION / CRITICAL) based on latest batch
- Change indicator vs previous batch (improved / unchanged / degraded)
- Key metric highlights: avg_fidelity, pass_rate, sla_compliance

**Worker flags** (REQ-QM-02):
- List workers with accuracy_status == FLAGGED
- List workers with declining accuracy_trend
- PM action items: "Review worker W-003 (accuracy 72%, declining trend, dominant errors: TEXT 45%)"

**Trend indicators**:
- Per-metric trend arrows: UP (improving), FLAT (stable), DOWN (declining)
- Alert flags for any CRITICAL threshold breaches
- Batch-over-batch comparison for key metrics

**SLA status** (REQ-QM-05):
- Current compliance percentage
- Trend direction
- At-risk items identification

**Recommendations**:
- Data-driven recommendations based on findings
- Error pattern recommendations: "TEXT errors dominate at 42% -- trigger reference-build refresh for text handling rules"
- Worker recommendations: "Worker W-003 accuracy declining -- recommend additional training or review"
- Process recommendations: "SLA compliance declining -- investigate batch assignment workflow"

**Persistence** (REQ-QM-06):
Write aggregated metrics summary back to `crowd_works/data/qc-reports/metrics-summary.yaml`:
```yaml
last_updated: string         # ISO 8601
report_type: string          # batch|trend|worker
batches_analyzed: int
latest_batch:
  batch_id: string
  quality_status: enum
  avg_fidelity: float
  pass_rate: float
  sla_compliance: float
team_overview:
  active_workers: int
  flagged_workers: int
  team_avg_accuracy: float
trend_summary:
  fidelity_direction: enum
  error_trend: string        # Brief description
  sla_direction: enum
```

## Failure Handling

### No QC Reports Found
- **Cause**: `crowd_works/data/qc-reports/` is empty or no `batch-*.yaml` files match
- **Action**: Report "no data available" with clear instructions. Suggest running `/qc-report` first to generate production QC reports.
- **Route**: L1 with `status: no_data`, L2 with setup instructions

### Corrupted QC Report File
- **Cause**: YAML parse failure, incomplete write, or missing required fields
- **Action**: Skip the corrupted file with warning. Process remaining valid files. Report skipped files in L2 with file names and error details.
- **Route**: Normal output (degraded if many files corrupted). L1 includes `skipped_files: N`

### Insufficient History for Trend Analysis
- **Cause**: Fewer than 3 batches available when `trend` mode requested
- **Action**: Report available data as batch summary. Note "insufficient data for trend analysis (need >= 3 batches, have N)". Do not extrapolate from insufficient data.
- **Route**: L1 with `report_type: batch_fallback`, L2 with available metrics + explanation

### Worker ID Not Found
- **Cause**: `worker:{id}` requested but no matching worker in any batch
- **Action**: Report "unknown worker ID: {id}". List available worker IDs for reference.
- **Route**: L1 with `status: worker_not_found`, L2 with available worker list

### Persistence Directory Missing
- **Cause**: `crowd_works/data/qc-reports/` does not exist
- **Action**: Create the directory. Write initial empty metrics-summary.yaml. Warn that this appears to be first run.
- **Route**: L1 with `status: initialized`, L2 with initialization confirmation

### Production Mode Validation Failure
- **Cause**: Data in QC reports contains drill-mode markers
- **Action**: Skip drill-mode data. If ALL data is drill-mode, reject with error directing to progress-track (Pipeline A).
- **Route**: Error signal if no production data found. Degraded output if mixed data (production data only processed).

## Anti-Patterns

### DO NOT: Expose Individual Worker Names
Use anonymized worker IDs (W-001, W-002, etc.) in all reports. Shared dashboards must never contain personally identifiable information. Even the `worker:{id}` deep-dive uses anonymized IDs.

### DO NOT: Calculate Trends from <3 Data Points
Trend classification requires minimum 3 batches of data. With fewer, report trend as "insufficient_data". Never extrapolate from 1-2 points -- this produces unreliable conclusions.

### DO NOT: Auto-Flag Workers Without PM Review
Worker flags (accuracy_status: FLAGGED) are advisory indicators. qc-metrics NEVER takes automated action on worker performance. All personnel decisions are HITL (Human-In-The-Loop) -- PM decides.

### DO NOT: Mix Pipeline A and Pipeline B Data
qc-metrics processes production QC data ONLY (Pipeline B). Drill data (mode: "drill") belongs to progress-track (Pipeline A). If drill data appears in qc-reports, skip it with warning.

### DO NOT: Report Raw Numbers Without Context
"42 errors" is meaningless without context. Always include: percentages, comparisons to previous batch, team averages, threshold classifications. Example: "42 errors (8.4% error rate, +2.1% from previous batch, NEEDS_ATTENTION threshold)".

### DO NOT: Recommend Without Evidence
Every recommendation must cite specific data. "Improve worker training" is vague. "Worker W-003 accuracy 72% (declining over 3 batches), dominant errors: TEXT 45% -- recommend TEXT-focused reference refresh" is actionable.

## Transitions

### Receives From
| Source | Data Expected | Key Fields |
|--------|---------------|------------|
| qc-report | Batch QC reports persisted to crowd_works/data/qc-reports/ | batch_id, items[] (file_id, verdict, fidelity_score, errors, hitl_status), summary (total, pass, fail, hitl_flagged, avg_fidelity), worker_stats |
| User | Report type argument | "batch" or "trend" or "worker:{id}" or empty (default: batch) |

### Sends To
| Target | Data Produced | Trigger Condition |
|--------|---------------|-------------------|
| PM/PL | Metrics dashboard (L1 summary + L2 full dashboard) | Always (primary output) |
| reference-build | Dominant error patterns for targeted reference refresh | When specific error category > 40% of total errors across batch |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| No QC data | User (setup instructions) | Empty state guidance |
| Worker not found | User (error + available IDs) | Available worker list |
| All data is drill-mode | User (redirect to progress-track) | Pipeline mismatch explanation |
| Corrupted files | Continue (degraded) | Skipped file count + warnings |

## Quality Gate
- All metrics calculated from actual QC report data (no synthetic or estimated values)
- Per-worker stats accurately reflect individual performance across all available batches
- Trend analysis uses sufficient data points (>= 3 batches, no extrapolation from fewer)
- SLA compliance calculated against defined thresholds (95% COMPLIANT, 85% AT_RISK)
- Error distribution heatmap aggregates match sum of individual item errors
- Quality status thresholds consistently applied (GOOD/NEEDS_ATTENTION/CRITICAL)
- Worker anonymization enforced (no real names in any output)
- Recommendations are evidence-based with specific data citations
- Persistence (metrics-summary.yaml) updated after every report generation
- Pipeline B data only (drill-mode data rejected)

## Output

### L1
```yaml
domain: production-eval
skill: qc-metrics
status: complete
report_type: batch|trend|worker
batch_count: 1
total_items: 500
avg_fidelity: 0.87
pass_rate: 0.92
fail_rate: 0.06
hitl_rate: 0.02
quality_status: GOOD
sla_compliance: 0.96
sla_status: COMPLIANT
worker_count: 12
flagged_workers: 1
flagged_worker_ids: [W-003]
skipped_files: 0
persistence_path: "crowd_works/data/qc-reports/metrics-summary.yaml"
trend_direction: stable
dominant_error_category: TEXT
dominant_error_percentage: 0.28
```

### L2
Full metrics dashboard with:
- **Quality Overview**: Pass/fail/hitl distribution with batch-over-batch change indicators
```
Quality Status: GOOD (avg fidelity 87%)
  Pass:  460/500 (92.0%)  [+1.2% from previous]
  Fail:   30/500 ( 6.0%)  [-0.8% from previous]
  HITL:   10/500 ( 2.0%)  [-0.4% from previous]
```
- **Error Category Heatmap**: Category x severity matrix with cell counts
```
Error Distribution Heatmap:
              CRITICAL  MAJOR  MINOR  Total  Share
  ESCAPE         2       5      3      10    18%
  GROUPING       0       3      2       5     9%
  OPERATOR       1       2      1       4     7%
  SIZING         0       4      3       7    13%
  TEXT            3       8      5      16    28%  [!]
  ENVIRONMENT    0       2      4       6    11%
  SEMANTIC       1       3      4       8    14%
  ─────────────────────────────────────────────
  Total          7      27     22      56   100%
```
- **Worker Performance Table**: Accuracy, volume, dominant errors per worker
```
Worker Performance (12 active):
  ID      Accuracy  Volume  Status   Trend     Dominant Errors
  W-001   94.2%     52      HIGH     stable    ESCAPE (30%)
  W-002   91.0%     48      HIGH     improving --
  W-003   72.1%     35      FLAGGED  declining TEXT (45%), SIZING (25%)
  ...
  Team Avg: 88.5%   41.7    --       stable    --
```
- **Trend Indicators**: Per-metric direction arrows with alert flags
```
Trend Summary (5 batches):
  Fidelity:   87% -> 85% -> 83% -> 85% -> 87%  [stable]
  Pass Rate:  91% -> 90% -> 89% -> 91% -> 92%  [improving]
  SLA:        97% -> 96% -> 95% -> 96% -> 96%  [stable]
  Flagged:    2   -> 1   -> 2   -> 1   -> 1    [stable]
```
- **SLA Compliance Summary**: Current status with trend and at-risk items
- **Recommendations**: Data-driven action items for PM
```
Recommendations:
  1. [WORKER] Review W-003: accuracy 72.1% (declining), TEXT errors 45%
     -> Recommend TEXT-focused training drill via Pipeline A
  2. [ERRORS] TEXT category at 28% of total errors (approaching 40% threshold)
     -> Monitor next 2 batches; if > 40%, trigger reference-build refresh
  3. [SLA] Compliance stable at 96% (above 95% target)
     -> No action needed
```
