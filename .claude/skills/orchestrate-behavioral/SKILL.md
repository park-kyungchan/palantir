---
name: orchestrate-behavioral
description: >-
  Plans gate, monitor, and aggregate checkpoints at wave
  boundaries with pass/fail criteria. Assigns checkpoint types
  and failure escalation paths. Parallel with orchestrate-static,
  orchestrate-relational, and orchestrate-impact. Use after
  plan-verify-coordinator complete with all PASS. Reads from
  plan-verify-coordinator verified plan L3 via $ARGUMENTS.
  Produces checkpoint schedule with type counts and rationale
  per checkpoint for orchestrate-coordinator. On FAIL, Lead
  applies D12 escalation. DPS needs plan-verify-coordinator
  verified plan L3. Exclude other orchestrate dimension outputs.
user-invocable: true
disable-model-invocation: true
---

# Orchestrate — Behavioral (WHERE)

## Execution Model
- **TRIVIAL**: Skip — Lead places 1 implicit gate checkpoint at P6→P7 boundary.
- **STANDARD**: Spawn 1 analyst (maxTurns:15). Domain boundaries only (P5→P6, P6→P7). Omit priority scoring.
- **COMPLEX**: Spawn 1 analyst (maxTurns:25). Deep checkpoint analysis with priority scoring and failure propagation awareness across all wave boundaries.

## Phase-Aware Execution

Two-Channel protocol only. See `.claude/resources/phase-aware-execution.md` for coordination protocol.
Two-Channel output: Ch2 (disk file) + Ch3 (micro-signal → Lead) See `.claude/resources/output-micro-signal-format.md`.

## Decision Points

### Checkpoint Type Selection
When placing a checkpoint at a transition point:
- **Wave boundary with downstream blockers** (fan-out >= 2): Use **gate** checkpoint. Blocks until all tasks PASS.
- **Wave boundary with independent downstream**: Use **aggregate** checkpoint. Requires N-of-M tasks PASS.
- **Non-boundary transition** (mid-wave handoff): Use **monitor** checkpoint. Logs only, does not block.
- **Domain boundary** (P5→P6, P6→P7): Always **gate** checkpoint regardless of other factors.

### Checkpoint Density Control
When checkpoint count exceeds 2 per wave boundary:
- **Priority scores differ >= 3**: Keep highest-priority only at that boundary. Merge others into monitor.
- **Priority scores within 2**: Consolidate into single aggregate checkpoint covering both criteria.
- **Maximum**: 1 gate + 1 monitor per wave boundary. Consolidate further if exceeded.

### Failure Escalation Depth
When defining fail_action per checkpoint:
- **Gate FAIL**: Retry failed task (max 2 retries), then route to Lead for re-planning.
- **Monitor FAIL**: Log warning + continue. Flag in L2 for post-execution review.
- **Aggregate partial FAIL** (< N-of-M): Retry failed subset (max 1 retry), then escalate.

## Methodology

See `resources/methodology.md` for: DPS template details, tier-specific DPS variations, transition categories table, priority scoring formula, checkpoint criteria fields, and wave-checkpoint matrix example.

### 1. Read Verified Plan
Load plan-verify-coordinator L3 output via `$ARGUMENTS` path. Extract: task list with wave assignments, dependency graph, file change manifest, risk assessment findings.

Construct analyst DPS per `.claude/resources/dps-construction-guide.md`:
- **Context**: Include verified plan L3 (task list, wave structure, dependency graph) + pipeline constraints (max 4 parallel per wave, max 3 phase iterations). Exclude other orchestrate dimension outputs and historical plan-verify rationale.
- **Task**: Identify WHERE verification checkpoints should be placed. For each: define pass/fail criteria, map to wave boundary, specify data to check.
- **Constraints**: Read-only. Every checkpoint must have measurable criteria. Map each to a specific wave boundary.
- **Delivery**: Two-Channel. Ch2: `tasks/{work_dir}/p5-orch-behavioral.md`. Ch3: `PASS|checkpoints:{N}|ref:tasks/{work_dir}/p5-orch-behavioral.md`.

### 2. Identify Critical Transition Points
Scan the execution flow for wave boundaries, producer-consumer handoffs, domain boundaries, critical path junctions, and risk mitigation points. Score each transition for priority (blast radius + recoverability + frequency). Mandatory if total >= 10.

### 3. Define Checkpoint Criteria
For each checkpoint: assign `checkpoint_id`, `location`, `criteria` (measurable), `data_checked`, `pass_action`, `fail_action`. See `resources/methodology.md` for full field definitions.

#### Checkpoint Types
- **Gate**: Blocks downstream execution until PASS. For wave boundaries.
- **Monitor**: Logs status but does not block. For non-critical transitions.
- **Aggregate**: Requires N-of-M tasks to pass. For parallel wave completion.

### 4. Map Checkpoints to Wave Boundaries
- Every wave boundary: at least 1 gate checkpoint.
- Parallel task completion waves: aggregate checkpoint.
- Domain boundaries (P5→P6, P6→P7): gate checkpoint.
- Non-boundary (mid-wave): monitor type only.

### 5. Output Checkpoint Schedule
Ordered list by execution sequence with: wave mapping per checkpoint, measurable pass/fail criteria, failure escalation path per checkpoint, and summary counts (gate / monitor / aggregate).

## Failure Handling

See `.claude/resources/failure-escalation-ladder.md` for D12 decision rules and failure output format.

| Failure Type | Level | Action |
|---|---|---|
| Plan L3 path empty or file missing (transient) | L0 Retry | Re-invoke after plan-verify-coordinator re-exports |
| Checkpoint incomplete or criteria unmeasurable | L1 Nudge | Respawn with refined DPS targeting refined wave boundary constraints |
| Agent stuck, context polluted, turns exhausted | L2 Respawn | Kill → fresh analyst with refined DPS |
| No wave boundaries in plan (cannot infer) | L3 Restructure | Route to plan-verify-coordinator for plan restructuring |
| 3+ L2 failures or excessive checkpoint conflicts | L4 Escalate | AskUserQuestion with situation + options |

**Verified Plan Data Missing**: Report `FAIL|reason:plan-L3-missing|ref:tasks/{work_dir}/p5-orch-behavioral.md`. Route back to plan-verify-coordinator for re-export.

**No Clear Wave Boundaries**: Infer from dependency graph. Flag as assumption in L2. Continue — orchestrate-coordinator will validate.

**Excessive Checkpoints (>2 per wave boundary)**: Consolidate to 1 gate + 1 monitor per boundary max. Merge redundant criteria.

## Anti-Patterns

- **No measurable criteria**: "Check that everything looks good" is not a checkpoint. Every checkpoint must have specific, verifiable conditions (file exists, test passes, count matches).
- **Mid-task checkpoints**: Checkpoints belong at transitions BETWEEN tasks or waves, not during task execution. Mid-task checkpoints interfere with agent autonomy.
- **All gates**: Gate checkpoints block execution. Overuse creates bottlenecks. Use monitor for non-critical transitions.
- **Missing fail_action**: Every checkpoint needs a defined action for FAIL — specify retry count, fallback, and escalation path.
- **Skip domain boundaries**: The P5→P6 and P6→P7 transitions are high-risk by nature. Always gate at domain boundaries.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-verify-coordinator | Verified plan L3 | File path via $ARGUMENTS: tasks, waves, dependencies |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestrate-coordinator | Checkpoint schedule | Always (WHERE dimension output) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Plan L3 missing | plan-verify-coordinator | Missing file path |
| No wave boundaries | orchestrate-coordinator | Inferred boundaries (flagged) |
| All checkpoints defined | orchestrate-coordinator | Complete schedule (normal flow) |

## Quality Gate
- Every wave boundary has at least 1 checkpoint
- Every checkpoint has measurable pass/fail criteria
- Every checkpoint has a defined failure escalation path
- Domain boundaries (P5→P6, P6→P7) have gate checkpoints
- No mid-task checkpoints
- Checkpoint count is proportional to plan complexity (not excessive)

## Output

### L1
```yaml
domain: orchestration
skill: behavioral
dimension: WHERE
checkpoint_count: 0
gate_count: 0
monitor_count: 0
aggregate_count: 0
checkpoints:
  - id: ""
    location: ""
    type: gate|monitor|aggregate
    criteria: ""
    fail_action: ""
pt_signal: "metadata.phase_signals.p5_orchestrate_behavioral"
signal_format: "PASS|checkpoints:{N}|gates:{N}|ref:tasks/{work_dir}/p5-orch-behavioral.md"
```

### L2
- Checkpoint placement rationale per transition
- Priority scoring evidence
- Wave-checkpoint mapping visualization
- Failure escalation paths
