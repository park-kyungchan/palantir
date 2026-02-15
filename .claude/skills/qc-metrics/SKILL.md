---
name: qc-metrics
description: |
  Aggregates production quality from qc-report batch data. Per-worker accuracy, batch trends, error distribution, SLA compliance. Terminal Pipeline B analytics — no downstream consumers.

  Use when: Dashboard, trends, or worker review needed from production QC data.
  WHEN: After qc-report persists production QC reports. User-invocable for dashboard/trends/worker review.
  CONSUMES: qc-report (batch QC reports: batch_id, items[], summary, worker_stats), user invocation ($ARGUMENTS scope).
  PRODUCES: L1 YAML metrics dashboard, L2 per-worker accuracy + trend analysis → PM/PL (SLA reports), reference-build (dominant error patterns).
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
- **"batch"** (or empty/default): Current batch aggregate. Reads latest `batch-*.yaml` from `crowd_works/data/qc-reports/`. Outputs pass/fail/hitl distribution, error categories, worker stats.
- **"trend"**: Multi-batch trend analysis. Reads ALL batch files. Requires >= 3 batches (reject with "insufficient data" if < 3). Outputs fidelity/error/worker/SLA trends.
- **"worker:{id}"**: Per-worker deep-dive across all batches. Outputs accuracy, volume, error patterns, peer comparison.

### Quality Thresholds (REQ-QM-01)

| Metric | GOOD | NEEDS_ATTENTION | CRITICAL |
|--------|------|-----------------|----------|
| Batch avg_fidelity | >= 85% | 70-84% | < 70% |
| Worker accuracy | >= 90% | 75-89% | < 75% |
| SLA compliance | >= 95% | 85-94% | < 85% |

GOOD = no action (green). NEEDS_ATTENTION = PM review (yellow), include improvement areas. CRITICAL = immediate PM action (red), include root cause + remediation.

### Trend Analysis Window (REQ-QM-03)
When report_type == "trend", analyze three windows: short-term (last 3 batches, immediate drops), medium-term (last 10, sustained patterns), long-term (all, baselines). Trend classification (requires >= 3 data points): **improving** (strictly increasing), **stable** (+/- 3% variance), **declining** (strictly decreasing), **critical** (declining AND in CRITICAL threshold). Short-term drives alerts, medium-term drives process recommendations, long-term provides baseline context.

### Error Distribution Analysis (REQ-QM-04)
Build error heatmap: 7 categories (ESCAPE/GROUPING/OPERATOR/SIZING/TEXT/ENVIRONMENT/SEMANTIC) x 3 severities (CRITICAL/MAJOR/MINOR) with cell counts. Dominant error (> 40% of total) triggers recommendation to reference-build for targeted refresh. Track emerging error categories (new in last 3 batches vs historical baseline).

### SLA Compliance (REQ-QM-05)
Default SLA: items processed within 24 hours of assignment. `sla_compliance = on_time_items / total_items`. Thresholds: COMPLIANT >= 95%, AT_RISK 85-94%, NON_COMPLIANT < 85%.

## Methodology

### 1. Read QC Report Data
Glob `crowd_works/data/qc-reports/batch-*.yaml`, sorted by date. Scope: "batch" reads latest only; "trend" and "worker:{id}" read all. Validate each file: YAML parse check, require batch_id/processed_at/items[]/summary/worker_stats. Skip corrupted/incomplete files with warning.

**Schema consumed** (from qc-report): `batch-{date}.yaml` containing batch_id, processed_at (ISO 8601), items[] (file_id, verdict PASS|FAIL, fidelity_score 0.0-1.0, errors[] with category/severity, hitl_status), summary (total, pass, fail, hitl_flagged, avg_fidelity), worker_stats ({worker_id}: accuracy float, items_processed int).

### 2. Aggregate Batch Metrics (REQ-QM-01)
Per batch compute: batch_id, date, total_items, pass/fail/hitl counts and rates, avg_fidelity, quality_status (from thresholds), error_distribution (by_category, by_severity, heatmap per REQ-QM-04), sla_compliance and sla_status.

**Cross-batch** (trend mode): rolling averages for avg_fidelity/pass_rate/sla_compliance, batch-over-batch deltas for trend classification, flag batches with >10% quality drop.

### 3. Per-Worker Statistics (REQ-QM-02)
Per worker build profile: worker_id (anonymized), batches_active, total_items_processed, overall_accuracy (weighted avg), accuracy_status (HIGH >=90% / NORMAL 75-89% / FLAGGED <75%), accuracy_trend, top 3 dominant_errors, comparison_to_team (accuracy_delta, volume_percentile), flag_reason (advisory only).

Worker trend (requires >=3 batches): track per-batch accuracy, classify trend. Flag declining workers even if current accuracy is NORMAL. HITL principle: flags are advisory -- PM decides all personnel actions. Privacy: anonymized IDs only in all reports.

### 4. Trend Analysis + SLA Compliance (REQ-QM-03, REQ-QM-05)
Requires >=3 batches. Per metric (fidelity, error categories, worker accuracy, SLA), compute three windows: short-term (last 3, with alert on decline), medium-term (last 10, baseline + direction), long-term (all, all-time baseline).

**Error category trends**: track per-category share of total errors per batch; flag increasing (emerging) and decreasing (resolved) categories. **Worker trends**: team avg accuracy, variance (high = inconsistent quality), new worker onboarding curve (first 3 batches vs baseline). **SLA trend**: per-batch compliance %, trend classification, trajectory vs 95% target.

### 5. Output Dashboard with Actionable Insights
Assemble structured dashboard for PM/PL:

- **Quality status**: Overall rating (GOOD/NEEDS_ATTENTION/CRITICAL) from latest batch, change indicator vs previous (improved/unchanged/degraded), key metrics (avg_fidelity, pass_rate, sla_compliance).
- **Worker flags** (REQ-QM-02): List FLAGGED and declining-trend workers with PM action items citing specific data (e.g., "Review W-003: accuracy 72%, declining, TEXT errors 45%").
- **Trend indicators**: Per-metric arrows (UP/FLAT/DOWN), CRITICAL threshold breach alerts, batch-over-batch comparisons.
- **SLA status** (REQ-QM-05): Current compliance %, trend direction, at-risk items.
- **Recommendations**: Evidence-based, categorized by error patterns (reference-build refresh triggers), worker performance (training recommendations), and process (SLA workflow fixes).

**Persistence** (REQ-QM-06): Write `crowd_works/data/qc-reports/metrics-summary.yaml` with: last_updated, report_type, batches_analyzed, latest_batch (batch_id, quality_status, avg_fidelity, pass_rate, sla_compliance), team_overview (active_workers, flagged_workers, team_avg_accuracy), trend_summary (fidelity_direction, error_trend, sla_direction).

## Failure Handling

| Failure | Cause | Action | Route |
|---------|-------|--------|-------|
| No QC reports | Empty directory or no `batch-*.yaml` | Report "no data", suggest `/qc-report` first | L1 `status: no_data` |
| Corrupted file | YAML parse fail, missing fields | Skip with warning, process remaining | Normal (degraded), L1 `skipped_files: N` |
| Insufficient history | <3 batches for trend mode | Fallback to batch summary, no extrapolation | L1 `report_type: batch_fallback` |
| Worker not found | No matching worker_id in any batch | Report unknown ID, list available IDs | L1 `status: worker_not_found` |
| Directory missing | `crowd_works/data/qc-reports/` absent | Create directory + initial metrics-summary.yaml | L1 `status: initialized` |
| Drill-mode data | QC reports contain drill markers | Skip drill data; reject if ALL drill-mode (route to progress-track) | Error or degraded |

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
Full metrics dashboard containing:
- **Quality Overview**: Pass/fail/hitl counts with rates and batch-over-batch change indicators (e.g., "Pass: 460/500 92.0% [+1.2%]")
- **Error Category Heatmap**: 7-category x 3-severity matrix with cell counts, totals, and share percentages. Flag dominant categories with [!]
- **Worker Performance Table**: Per-worker rows with accuracy, volume, status (HIGH/NORMAL/FLAGGED), trend, dominant errors. Team average row at bottom.
- **Trend Indicators**: Per-metric (fidelity, pass rate, SLA, flagged workers) value series with direction classification [stable/improving/declining]
- **SLA Compliance Summary**: Current status with trend and at-risk items
- **Recommendations**: Categorized action items ([WORKER]/[ERRORS]/[SLA]) with specific data citations and recommended actions
