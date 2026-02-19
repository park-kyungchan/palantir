---
name: research-coordinator
description: >-
  Consolidates four audit dimensions into tiered output with
  cross-dimensional pattern analysis. Aggregates CC-native behavioral
  claims from research dimensions and flags for verification routing.
  Terminal research skill that merges parallel audit results into
  unified intelligence. Use after all four audit skills complete
  (audit-static, audit-behavioral, audit-relational, audit-impact).
  Reads from audit-static dependency graph, audit-behavioral behavior
  predictions, audit-relational relationship graph, and audit-impact
  propagation paths. Produces L1 index and L2 summary for Lead,
  L3 per-dimension files for plan skills, plus CC-native claim
  aggregation for research-cc-verify. On FAIL (dimension output
  missing or inconsistent), Lead applies D12 escalation. DPS needs
  audit-static L3 dependency graph, audit-behavioral L3 predictions,
  audit-relational L3 relationships, audit-impact L3 propagation
  paths. Exclude individual claim evidence detail.
user-invocable: false
disable-model-invocation: false
---

# Research — Coordinator (Cross-Audit Consolidation)

## Execution Model
- **TRIVIAL**: Lead-direct. Inline consolidation of minimal audit outputs (≤2 dimensions, ≤5 findings each). No agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns: 30). Read all 4 audit outputs, cross-reference, produce tiered output.
- **COMPLEX**: Spawn analyst (maxTurns: 35). Larger audit outputs require more turns for cross-referencing. Single analyst maintains cross-dimensional coherence.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Tiered Output Architecture

| Tier | File | Consumer | When Read |
|------|------|----------|-----------|
| L1 | `tasks/{team}/p2-coordinator-index.md` | Lead | Always (routing decisions) |
| L2 | `tasks/{team}/p2-coordinator-summary.md` | Lead | When routing needs detail |
| L3 | `tasks/{team}/p2-coordinator-static.md` | plan-static | Via $ARGUMENTS, Lead never reads |
| L3 | `tasks/{team}/p2-coordinator-behavioral.md` | plan-behavioral | Via $ARGUMENTS, Lead never reads |
| L3 | `tasks/{team}/p2-coordinator-relational.md` | plan-relational | Via $ARGUMENTS, Lead never reads |
| L3 | `tasks/{team}/p2-coordinator-impact.md` | plan-impact, execution-impact | Via $ARGUMENTS, Lead never reads |

## Decision Points

### Consolidation Depth
- **≤2 dimensions, ≤5 findings each**: Lead-direct inline consolidation (TRIVIAL).
- **3-4 dimensions, ≤20 total findings**: Single analyst, standard cross-reference. maxTurns: 30.
- **4 dimensions, >20 total findings**: Single analyst, extended cross-reference. maxTurns: 35.

### Partial Dimension Handling
- **1-2 dimensions missing**: Proceed with available data. Mark gaps in L1 index.
- **3-4 dimensions missing**: FAIL. Insufficient data for meaningful consolidation. Route to Lead.

## Methodology

### 1. Read All Audit Outputs
Read 4 audit output files from `tasks/{team}/`: `p2-audit-static.md`, `p2-audit-behavioral.md`, `p2-audit-relational.md`, `p2-audit-impact.md`. Extract key metrics (counts, risk levels), primary findings (top by severity), and coverage status. Missing or partial outputs are gaps — do not block; consolidate what is available.

### 2. Cross-Reference Dimensions
Discover compound patterns spanning multiple dimensions:
- **Dependency + Behavior**: Hotspot files (audit-static) with HIGH behavioral risk (audit-behavioral) → critical nodes.
- **Relationship + Impact**: Broken relationships (audit-relational) on high-severity propagation paths (audit-impact) → integrity risks.
- **Static + Relational Consistency**: High fan-in files (audit-static) missing from relationship declarations (audit-relational) → undeclared dependencies.
- **Behavioral + Impact Compound**: Predicted regressions (audit-behavioral) on TRANSITIVE paths (audit-impact) → cascading regression risks.

> Cross-dimensional pattern discovery heuristics and conflict resolution algorithm: read `resources/methodology.md`

### 2.5. Aggregate CC-Native Claims
Collect all `[CC-CLAIM]` tagged items from research-codebase and research-external outputs. Deduplicate, categorize by type (FILESYSTEM, PERSISTENCE, STRUCTURE, CONFIG, BEHAVIORAL), and priority-rank (PERSISTENCE highest). Include in L2 with routing recommendation for research-cc-verify.

> Claim deduplication protocol and priority ranking detail: read `resources/methodology.md`

### 3–5. Produce Tiered Output (L1, L2, L3)
Produce 6 files: L1 compact YAML index (≤30 lines), L2 executive summary (≤200 lines), and 4 L3 per-dimension files. L1 drives Lead routing. L2 supplements routing decisions. L3 files carry complete per-dimension data plus compound patterns for plan-phase skills.

> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> L3 format templates, deduplication protocol, DPS template, deferred spawn pattern: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Single dimension output missing or delayed | L0 Retry | Re-invoke missing dimension audit skill |
| Cross-dimension inconsistency detected | L1 Nudge | SendMessage to affected dimension analyst with specific conflict |
| Analyst exhausted turns during consolidation | L2 Respawn | Kill → fresh analyst with all 4 dimension outputs |
| Dimension output structurally incompatible | L3 Restructure | Modify L3 format contract, re-run affected dimension |
| 2+ dimensions persistently failing, 3+ L2 failures | L4 Escalate | AskUserQuestion with dimension status summary |

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

### DO NOT: Filter Out Low-Severity Findings in L3
L3 files must contain complete dimension data. Low-severity findings in one dimension may become high-severity when combined with another dimension in plan-phase analysis.

### DO NOT: Add New Research in Coordinator
Coordinator consolidates existing audit findings only. Gaps discovered during consolidation are noted as gap recommendations in L2 — do not perform new Grep/Glob/Read to fill them.

### DO NOT: Bloat L1 Index
L1 must stay compact for Lead context budget. Any detail beyond summary metrics and routing recommendation belongs in L2 or L3. If L1 exceeds 30 YAML lines, it is too large.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| audit-static | Dependency graph, hotspots, cycles | L2 markdown at `tasks/{team}/p2-audit-static.md` |
| audit-behavioral | Behavior predictions, risk classification | L2 markdown at `tasks/{team}/p2-audit-behavioral.md` |
| audit-relational | Relationship graph, integrity issues | L2 markdown at `tasks/{team}/p2-audit-relational.md` |
| audit-impact | Propagation paths, risk assessment | L2 markdown at `tasks/{team}/p2-audit-impact.md` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| Lead | L1 index.md + L2 summary.md | Always (terminal P2 skill) |
| plan-static | L3 `tasks/{team}/p2-coordinator-static.md` | Via $ARGUMENTS (Lead passes path) |
| plan-behavioral | L3 `tasks/{team}/p2-coordinator-behavioral.md` | Via $ARGUMENTS (Lead passes path) |
| plan-relational | L3 `tasks/{team}/p2-coordinator-relational.md` | Via $ARGUMENTS (Lead passes path) |
| plan-impact | L3 `tasks/{team}/p2-coordinator-impact.md` | Via $ARGUMENTS (Lead passes path) |
| execution-impact | L3 `tasks/{team}/p2-coordinator-impact.md` (Shift-Left data) | Via $ARGUMENTS in plan phase |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| 3-4 audits missing | Lead | Missing audit list, expected locations |
| Cross-dimensional contradiction | Lead | Both findings with dimension sources |
| Output directory error | Lead | Filesystem error details |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- All available audit dimensions ingested and represented in output
- Compound patterns documented with evidence from both contributing dimensions
- L1 index compact (<30 lines YAML) with routing recommendation
- L2 summary under 200 lines with executive overview and routing guidance
- L3 files contain complete per-dimension data plus relevant compound patterns
- Missing dimensions explicitly noted in L1 and L2
- No new research performed (consolidation only)
- CC-native behavioral claims aggregated and flagged for research-cc-verify
- All 6 output files written to `tasks/{team}/p2-coordinator-{file}.md`

## Output

### L1 (index.md)
```yaml
domain: research
skill: coordinator
status: PASS|PARTIAL|FAIL
dimensions_received: 4
dimensions_complete: 0
compound_patterns: 0
overall_risk: HIGH|MEDIUM|LOW
critical_findings: 0
audit_summary:
  static:
    status: PASS|PARTIAL|MISSING
    hotspots: 0
    cycles: 0
  behavioral:
    status: PASS|PARTIAL|MISSING
    high_risks: 0
    conflicts: 0
  relational:
    status: PASS|PARTIAL|MISSING
    broken: 0
    integrity_pct: 100
  impact:
    status: PASS|PARTIAL|MISSING
    critical_paths: 0
    maintenance_risk: LOW
routing_recommendation: ""
cc_native_claims: 0
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|dims:4|claims:{N}|ref:tasks/{team}/p2-coordinator-index.md"
```

### L2 (summary.md)
- Executive summary (3-5 sentences)
- Compound pattern highlights (top 3)
- Risk distribution across all dimensions
- Gap report for missing/partial dimensions
- Routing guidance for plan-phase skills
- CC-native claims aggregated from research dimensions (for research-cc-verify routing)

### L3 (4 per-dimension files)
- Complete audit data per dimension
- Relevant compound patterns cross-referenced
- Constraint recommendations for consuming plan-phase skill
- Shift-Left handoff data (audit-impact.md only)
