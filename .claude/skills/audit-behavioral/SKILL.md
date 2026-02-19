---
name: audit-behavioral
description: >-
  Predicts runtime behavior changes and regression risks per
  component. Classifies risk as HIGH, MEDIUM, or LOW with
  file:line evidence. Parallel with audit-static,
  audit-relational, and audit-impact. Use after research-codebase
  and research-external complete. Reads from research-codebase
  existing behaviors, research-external known issues and
  workarounds, and design-architecture change scope. Produces
  behavior change summary and prediction report with risk matrix
  for research-coordinator. On FAIL, Lead applies D12 escalation
  ladder. DPS needs research-codebase behavior patterns and
  file:line evidence, research-external known issues, and
  design-architecture change scope. Exclude other audit dimension
  results (static/relational/impact) and pre-design history.
user-invocable: false
disable-model-invocation: false
---

# Audit — Behavioral (Runtime Behavior Prediction)

## Execution Model
- **TRIVIAL**: Lead-direct. Inline assessment of 1-2 behavior-bearing files. No agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns:25). Map design changes to existing behaviors. Predict side effects.
- **COMPLEX**: Spawn 2 analysts scoped by subsystem (maxTurns:25 each). Each predicts behavior changes within assigned component boundaries.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### Component Scope Strategy
Based on design-architecture change scope breadth.
- **≤5 behavior-bearing components**: Single analyst covers all. maxTurns: 20.
- **6-15 components**: Single analyst, prioritize by risk. maxTurns: 25.
- **>15 components**: Spawn 2 analysts scoped by subsystem. maxTurns: 25 each.

### Risk Classification
- **HIGH**: Breaks observable behavior, no fallback, affects multiple downstream components. Block implementation if unmitigated.
- **MEDIUM**: Detectable change, fallback exists or single-component impact. Include regression test in plan.
- **LOW**: Minor change, easily reversible, limited blast radius. Note in plan only.

> Detailed scoring rubrics, pattern taxonomy, regression risk formula: read `resources/methodology.md`

## Methodology

### 1. Ingest Wave 1 Findings
Read research-codebase L1/L2 for existing runtime behaviors, error handling, and state management patterns. Read research-external L2 for known issues and behavioral quirks. Read design-architecture L1/L2 for component modifications and ADRs.

### 2. Identify Behavior-Bearing Components
Tag control flow, state mutation, external interaction, and error handling files. For each: document current behavior (file:line), the design change affecting it, and the overlap zone.

### 3. Predict Side Effects and Regressions
Per component: predict new behaviors (side effects) and at-risk behaviors (regressions). Evidence requirement: current code file:line AND triggering design decision (ADR reference).

### 4. Classify Risk Levels
Apply HIGH/MEDIUM/LOW criteria from Decision Points. Risk factors that increase severity: high fan-in, no test coverage, error-handling paths, multiple interacting design decisions at the same component.

### 5. Report Predictions
Produce per-component behavior change table, side effect inventory, regression risk matrix (HIGH first), cross-component interaction warnings, and summary statistics (total changes, H/M/L distribution).

> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> Detailed scoring rubrics, DPS template, edge case handling: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error during behavior analysis | L0 Retry | Re-invoke same analyst, same scope |
| Incomplete predictions or off-scope analysis | L1 Nudge | SendMessage with refined component scope |
| Analyst exhausted turns, context polluted | L2 Respawn | Kill → fresh analyst with refined DPS |
| Subsystem scope conflict between parallel analysts | L3 Restructure | Modify subsystem boundaries, reassign components |
| Design conflict requiring strategic decision, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

### DO NOT: Prescribe Solutions
Behavioral audit predicts outcomes, not remedies. Statements like "refactor component X to avoid regression" are plan-phase work — report the prediction only.

### DO NOT: Predict Without Evidence
Every prediction must cite current behavior (file:line) AND the design decision creating the change. Speculation without concrete code or ADR grounding is not a valid prediction.

### DO NOT: Conflate Static and Behavioral Analysis
Import chains and file dependencies belong to audit-static. Focus on runtime effects only. Note dependency issues for audit-static cross-reference but do not analyze them here.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-codebase | Existing behaviors, patterns, conventions | L1 YAML: pattern inventory, L2: behavior descriptions with file:line |
| research-external | Known issues, workarounds, behavioral quirks | L2: issue descriptions with source URLs |
| design-architecture | Change scope, component modifications | L1 YAML: components list, L2: ADRs with change details |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-coordinator | Behavior predictions + risk classification | Always (Wave 2 -> Wave 2.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| No behavior-bearing components | research-coordinator | Empty prediction set with explanation |
| Analyst exhausted | research-coordinator | Partial predictions + uncovered component list |
| Design conflict detected | research-coordinator | Conflicting predictions with both ADR references |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every prediction cites current behavior (file:line) AND triggering design decision (ADR)
- Risk classification applied to all predictions with criteria documented
- No prescriptive recommendations (predictions only, not solutions)
- Side effects classified as intended or unintended
- Cross-component interactions identified when multiple predictions share downstream targets
- Summary statistics: total changes, HIGH/MEDIUM/LOW distribution

## Output

### L1
```yaml
domain: research
skill: audit-behavioral
total_changes: 0
risk_high: 0
risk_medium: 0
risk_low: 0
conflicts: 0
predictions:
  - component: ""
    change_type: side_effect|regression
    risk: HIGH|MEDIUM|LOW
    design_decision: ""
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|changes:{N}|risks:{N}|ref:tasks/{team}/p2-audit-behavioral.md"
```

### L2
- Per-component behavior change table (current vs predicted)
- Side effect inventory with intended/unintended classification
- Regression risk matrix sorted by severity
- Cross-component interaction warnings
- Design conflict report (if any)
- Evidence trail: file:line references for all predictions
