---
name: orchestrate-coordinator
description: >-
  Unifies task-agent assignments, checkpoints, DPS contracts, and
  wave schedule into per-task spawn instructions with
  cross-validation. Terminal orchestration skill that merges four
  dimension outputs into unified execution plan. Use after all
  four orchestrate dimension skills complete (orchestrate-static,
  orchestrate-behavioral, orchestrate-relational,
  orchestrate-impact). Reads from orchestrate-static task-agent
  matrix, orchestrate-behavioral checkpoint schedule,
  orchestrate-relational DPS specs, and orchestrate-impact wave
  schedule. Produces L1 index and L2 summary for Lead, L3
  execution-plan for execution-code and execution-infra. Enforces DPS v5 with MCP_DIRECTIVES and COMM_PROTOCOL. All spawns model:sonnet. Plan-first gate for COMPLEX tier. On FAIL (execution plan inconsistency), Lead applies D12 escalation. DPS needs all four orchestrate dimension outputs. Exclude plan-verify raw data.
user-invocable: true
disable-model-invocation: true
---

# Orchestrate — Coordinator

## Execution Model
- **TRIVIAL**: Skip — Lead produces inline execution plan (1-2 tasks, no cross-validation needed).
- **STANDARD**: Spawn 1 analyst (maxTurns:20). Merge and cross-validate 4 dimension outputs (Check A + D only).
- **COMPLEX**: Spawn 1 analyst (maxTurns:35). Full cross-validation (all 4 checks), conflict resolution, optimization.

## Phase-Aware Execution

P5 — Team mode only. $ARGUMENTS receives 4 dimension file paths from Lead.
- **Communication**: Four-Channel Protocol — Ch2 disk file + Ch3 micro-signal to Lead + Ch4 P2P to downstream.
- **P2P Self-Coordination**: Read dimension outputs directly from `tasks/{team}/` via $ARGUMENTS paths.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

> Phase-aware routing: read `.claude/resources/phase-aware-execution.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
> Detailed methodology: read `resources/methodology.md`

## Decision Points

### Merge Conflict Resolution Strategy
When dimension outputs disagree on task attributes:
- **Task in WHO but not WHEN**: Add to earliest eligible wave. Impact adjusts.
- **Task in WHEN but not WHO**: Flag as unassigned. Route back to orchestrate-static.
- **Handoff references non-existent task**: Flag as dangling DPS. Route back to orchestrate-relational.
- **Checkpoint at non-wave boundary**: Remap to nearest wave boundary. Behavioral adjusts.

> Full conflict resolution table: read `resources/methodology.md`

### Cross-Validation Failure Severity
When a cross-validation check fails:

| Check | Failure Severity | Action |
|-------|-----------------|--------|
| A: Agent-wave fit | BLOCKING | Cannot produce L3. Route to orchestrate-static + orchestrate-impact. |
| B: Handoff-sequence order | BLOCKING | Cannot produce L3. Route to orchestrate-relational + orchestrate-impact. |
| C: Checkpoint alignment | NON-BLOCKING (WARN) | Remap checkpoint, document in L2. Produce L3 with warning. |
| D: Task coverage completeness | BLOCKING | Cannot produce L3. Identify missing dimension, route back. |

### L3 Output Completeness
- **All 4 checks PASS**: Produce full L3 with spawn DPS per task.
- **Any BLOCKING check FAIL**: Do NOT produce L3. Report failure details in L1/L2 only.
- **Only WARN checks**: Produce L3 with warnings flagged and remediation notes in L2.

## Methodology

### 1. Read All 4 Dimension Outputs
Load WHO (orchestrate-static), WHERE (orchestrate-behavioral), HOW (orchestrate-relational), WHEN (orchestrate-impact) from $ARGUMENTS paths.
> Dimension input table + tier-specific DPS variations: read `resources/methodology.md`

### 2. Merge Into Unified Plan
For each task, create a unified record combining WHO/WHEN/HOW/WHERE fields. Resolve merge conflicts per Decision Points rules above.
> Unified task record YAML format + conflict resolution table: read `resources/methodology.md`

### 3. Cross-Validate Consistency
Run four checks (A: agent-wave fit, B: handoff-sequence order, C: checkpoint-wave alignment, D: task coverage). Report PASS/FAIL/WARN for each.
> Full check tables with example rows: read `resources/methodology.md`

### 3.5. Scheduling Efficiency Analysis
Detect long serial chains, single-task waves, low parallelism, cost overrun. Generate RESTRUCTURE_HINT in L2 for HIGH-priority inefficiencies. Lead decides: re-decompose, restructure, or accept with documented gaps.
> Efficiency check table + RESTRUCTURE_HINT format: read `resources/methodology.md`

### 4. Produce L1 Index + L2 Summary
Write L1 (compact YAML with counts and validation status) and L2 (narrative with cross-validation results, conflicts, critical path, and recommendations for P6).

### 5. Produce L3 Execution Plan
Write detailed per-wave spawn instructions with complete DPS prompts, COMM_PROTOCOL (NOTIFY/SIGNAL_FORMAT/AWAIT), input/output handoff references, file ownership, and checkpoint criteria.
> L3 YAML format spec: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Dimension output missing (transient) | L0 Retry | Re-invoke after missing dimension skill re-exports |
| Cross-validation incomplete or merge ambiguous | L1 Nudge | SendMessage with refined conflict resolution constraints |
| Agent stuck, context polluted, turns exhausted | L2 Respawn | Kill → fresh analyst with refined DPS |
| Cross-validation FAIL unresolvable without restructure | L3 Restructure | Route to affected dimension skill(s) for redesign |
| 3+ L2 failures or task coverage mismatch unresolvable | L4 Escalate | AskUserQuestion with situation + options |

## Anti-Patterns

### DO NOT: Produce L3 Without Cross-Validation
L3 must be cross-validated before output. Skipping pushes errors to P6 where they cost more to fix.

### DO NOT: Omit Spawn Prompt Content from L3
L3 must contain COMPLETE DPS prompts per task. P6 should not reconstruct prompts from multiple sources.

### DO NOT: Ignore Merge Conflicts
Every conflict must be resolved explicitly and documented in L2. Silent resolution creates hidden inconsistencies.

### DO NOT: Create L3 Without Handoff Paths
Every inter-task dependency must have a concrete `tasks/{team}/` path. Tasks reading from undefined paths fail at execution.

### DO NOT: Skip Agent-Wave Validation
A wave with 5 agents will fail. Agent-wave fit is the most critical cross-validation check.

### DO NOT: Produce Partial L3
If any BLOCKING check fails, do NOT produce an L3. A partial L3 misleads P6 into executing with known errors.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestrate-static | Task-agent assignment matrix (WHO) | L1 YAML + L2 at `tasks/{team}/p5-orch-static.md` |
| orchestrate-behavioral | Checkpoint schedule (WHERE) | L1 YAML + L2 at `tasks/{team}/p5-orch-behavioral.md` |
| orchestrate-relational | DPS handoff specs (HOW) | L1 YAML + L2 chain at `tasks/{team}/p5-orch-relational.md` |
| orchestrate-impact | Wave capacity schedule (WHEN) | L1 YAML + L2 timeline at `tasks/{team}/p5-orch-impact.md` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-code | L3 unified execution plan (code tasks) | Cross-validation PASS, code tasks exist |
| execution-infra | L3 unified execution plan (infra tasks) | Cross-validation PASS, infra tasks exist |
| Lead | L1 index + L2 summary | Always (routing data for Lead) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing dimension output | Lead (re-invoke failed skill) | Which dimension, error details |
| Cross-validation FAIL | Lead (re-invoke relevant dimension) | Check ID, evidence, fix suggestion |
| Task coverage mismatch | Lead (investigate discrepancy) | Missing/extra task list |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- All 4 dimension outputs loaded and parsed
- Every task in unified plan has WHO, WHEN, HOW, WHERE fields populated
- Cross-validation Check A (agent-wave fit): PASS
- Cross-validation Check B (handoff-sequence order): PASS
- Cross-validation Check C (checkpoint-wave alignment): PASS or WARN only
- Cross-validation Check D (task coverage completeness): PASS
- L3 execution plan contains complete spawn instructions for every task
- L3 handoff paths are all concrete `tasks/{team}/` paths
- No wave exceeds 4 parallel tasks

## Output

### L1 (index.md)
```yaml
domain: orchestration
skill: coordinator
status: PASS|FAIL
task_count: 0
wave_count: 0
handoff_count: 0
checkpoint_count: 0
cross_validation:
  agent_wave_fit: PASS|FAIL
  handoff_sequence: PASS|FAIL
  checkpoint_alignment: PASS|FAIL|WARN
  task_coverage: PASS|FAIL
files:
  l2_summary: tasks/{team}/p5-coordinator-summary.md
  l3_execution_plan: tasks/{team}/p5-coordinator-execution-plan.md
```

### L2 (summary.md)
Narrative: unified plan overview, cross-validation results, conflict resolutions, critical path, agent distribution, recommendations for P6.

### L3 (execution-plan.md)
Per-wave spawn instructions with complete DPS prompts, input/output handoff references, file ownership, checkpoint criteria, and agent tool requirements per task.
