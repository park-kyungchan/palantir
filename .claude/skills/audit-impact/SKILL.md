---
name: audit-impact
description: >-
  Traces change propagation paths classifying as DIRECT (1-hop)
  or TRANSITIVE (2-3 hops). Classifies impact severity per path
  with file:line evidence. Parallel with audit-static,
  audit-behavioral, and audit-relational. Use after
  research-codebase and research-external complete. Reads from
  research-codebase file inventory, research-external constraints,
  and design-risk risk matrix. Produces impact summary and
  propagation analysis for research-coordinator, and Shift-Left
  predicted paths for execution-impact. On FAIL (risk assessment
  incomplete or severity miscategorization), Lead applies L0 retry
  with narrower scope; 2+ failures escalate to L2. DPS needs
  research-codebase file
  inventory and dependency patterns, research-external propagation
  constraints, and design-risk risk matrix. Exclude relational
  integrity data, behavioral predictions, and pre-design history.
user-invocable: true
disable-model-invocation: true
---

# Audit — Impact (Change Propagation Analysis)

## Execution Model

- **TRIVIAL**: Lead-direct. Inline trace of 1-2 file change impacts. No agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns: 25). Trace DIRECT + 2-hop TRANSITIVE propagation paths.
- **COMPLEX**: Spawn 2 analysts (maxTurns: 25 each). Analyst-1 traces DIRECT; Analyst-2 traces TRANSITIVE using Analyst-1's edge list. Sequential.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

**Delivery**: Subagent writes to `{work_dir}/p2-audit-impact.md`, sends micro-signal:
`PASS|direct:{N}|transitive:{N}|ref:{work_dir}/p2-audit-impact.md`

## Decision Points

### Propagation Depth Strategy

Based on design change scope and dependency density:
- **Isolated (≤3 change points, ≤2 direct dependents each)**: DIRECT only. Skip transitive. maxTurns: 20.
- **Moderate (4–8 change points)**: DIRECT + TRANSITIVE up to 2 hops. maxTurns: 25.
- **Broad (>8 change points or hub-touching)**: Full 3-hop TRANSITIVE. Spawn 2 analysts. maxTurns: 25 each.
- **Default**: DIRECT + 2-hop TRANSITIVE (STANDARD tier).

### Risk Matrix Availability

- **design-risk available**: Use risk matrix for severity calibration and change point identification.
- **design-risk missing (TRIVIAL/STANDARD)**: Fall back to design-architecture component scope. Note reduced confidence.

> Propagation depth tables, depth-first traversal steps: read `resources/methodology.md`

## Methodology

### 1. Ingest Wave 1 Findings and Risk Matrix
Read research-codebase L1/L2 (file inventory, dependency patterns, component interactions). Read research-external L2 (breaking change rules, cascading patterns). Read design-risk L1/L2 (risk matrix, change scope boundaries — optional for STANDARD).

### 2. Trace Change Propagation Paths
From each design change point, trace DIRECT (1-hop) and TRANSITIVE (2-3 hop) paths. Record `file:line` evidence at every hop. Cap transitive at 3 hops; flag deeper chains as "potential deep impact" without tracing.

> Full traversal algorithm, hop chain examples: read `resources/methodology.md`

### 3. Classify Impact Severity
Per path: CRITICAL (breaks interface, no backward compat) / HIGH (requires rework, 3+ callers) / MEDIUM (minor updates, compat exists) / LOW (self-contained). Escalators: +1 level if path crosses module boundary, no test coverage, or multiple design decisions converge.

> Full severity table and escalator rules: read `resources/methodology.md`

### 4. Assess Maintenance and Scalability Risk
For each affected module: rate coupling increase, new single points of failure, blast radius growth. For each architecture decision: rate scalability at 2x/5x codebase growth. Rate each as HIGH/MEDIUM/LOW with justification.

> Full assessment rubric: read `resources/methodology.md`

### 5. Report Propagation Paths and Risk Assessment
Produce propagation path table (origin, hops, terminal, severity, evidence), DIRECT/TRANSITIVE summary counts, risk matrix, maintenance/scalability narratives, and Shift-Left handoff for execution-impact.

> DPS template for impact analysts, Shift-Left prediction format: read `resources/methodology.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error during propagation trace | L0 Retry | Re-invoke same analyst, same scope |
| Incomplete path tracing or off-scope analysis | L1 Nudge | Respawn with refined DPS targeting change point scope |
| Analyst exhausted turns tracing chains | L2 Respawn | Kill → fresh analyst with refined DPS |
| DIRECT-TRANSITIVE handoff broken (COMPLEX) | L3 Restructure | Merge into single analyst or re-partition |
| Strategic ambiguity on hop depth, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

Special cases: no propagation paths found → report `direct: 0, transitive: 0` (valid for isolated additions); design-risk missing → continue with reduced confidence; chains >3 hops → cap and flag.

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
> Failure protocol details: read `resources/methodology.md`

## Anti-Patterns

- **DO NOT trace beyond 3 hops.** Transitive impact beyond 3 hops is speculative. Cap at 3 hops and note potential deep impacts without further tracing.
- **DO NOT recommend mitigations.** Impact audit describes what will be affected and how severely. Mitigation belongs to plan-behavioral. Keep findings descriptive.
- **DO NOT confuse impact with dependency.** audit-static maps structural dependencies (what references what). audit-impact traces change propagation (if X changes, what breaks). Impact analysis is change-triggered.

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|---|---|---|
| research-codebase | File inventory, dependency patterns | L1 YAML: pattern inventory, L2: file:line findings |
| research-external | Change propagation constraints | L2: breaking change rules, cascading patterns |
| design-risk | Risk matrix from P1 | L1 YAML: risk items, L2: risk analysis (optional for STANDARD) |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| research-coordinator | Impact analysis for consolidation | Always (Wave 2 → Wave 2.5) |
| execution-impact | Predicted propagation paths (Shift-Left) | Always (P2 → P6 via $ARGUMENTS in plan) |

### Failure Routes

| Failure Type | Route To | Data Passed |
|---|---|---|
| No propagation paths | research-coordinator | Empty impact set with explanation |
| Analyst exhausted | research-coordinator | Partial paths + coverage percentage |
| Design-risk missing | Continue (degraded) | Reduced confidence flag in output |

> D17 Note: Two-Channel protocol — Ch2 output file in work directory, Ch3 micro-signal to Lead.
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate

- Every propagation path has `file:line` evidence for each hop
- DIRECT vs TRANSITIVE classification applied to all paths
- Severity classification applied with criteria documented
- Maintenance and scalability risk assessed per affected module
- No paths traced beyond 3 hops (cap enforced)
- Shift-Left output structured for execution-impact consumption
- No prescriptive recommendations (descriptive findings only)

## Output

### L1

```yaml
domain: research
skill: audit-impact
direct_count: 0
transitive_count: 0
critical_paths: 0
high_paths: 0
medium_paths: 0
low_paths: 0
maintenance_risk: HIGH|MEDIUM|LOW
scalability_risk: HIGH|MEDIUM|LOW
propagation:
  - origin: ""
    type: DIRECT|TRANSITIVE
    hops: 1
    severity: CRITICAL|HIGH|MEDIUM|LOW
    terminal: ""
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|direct:{N}|transitive:{N}|ref:{work_dir}/p2-audit-impact.md"
```

### L2

- Propagation path table with full hop chains and evidence
- DIRECT impact inventory with severity per path
- TRANSITIVE impact inventory (2-3 hops) with chain evidence
- Risk matrix: per-design-decision severity across all paths
- Maintenance risk narrative per affected module
- Scalability risk narrative per architecture decision
- Shift-Left handoff section: structured data for execution-impact (P6)
