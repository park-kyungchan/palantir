---
name: orchestrate-impact
description: >-
  Schedules execution waves via topological sort with capacity
  balancing at max 4 parallel per wave. Calculates critical path
  and parallel efficiency. Parallel with orchestrate-static,
  orchestrate-behavioral, and orchestrate-relational. Use after
  plan-verify-coordinator complete with all PASS. Reads from
  plan-verify-coordinator verified plan L3 via $ARGUMENTS.
  Produces wave schedule with critical path length and wave
  visualization with DAG for orchestrate-coordinator. On FAIL,
  Lead applies D12 escalation. DPS needs plan-verify-coordinator
  verified plan L3. Exclude other orchestrate dimension outputs.
user-invocable: true
disable-model-invocation: true
---

# Orchestrate — Impact (WHEN)

## Execution Model
- **TRIVIAL**: Skip (orchestration simplified for trivial tiers).
- **STANDARD**: Spawn 1 analyst with maxTurns:15. Simple wave grouping, no critical path analysis.
- **COMPLEX**: Spawn 1 analyst with maxTurns:25. Deep DAG analysis with load balancing and critical path optimization.

## Phase-Aware Execution
Two-Channel protocol only. Two-Channel Protocol: Ch2 (disk file) + Ch3 (micro-signal to Lead)
- Read upstream from `tasks/{work_dir}/` via $ARGUMENTS. Write output to `tasks/{work_dir}/p5-orch-impact.md`.
- Update task status via TaskUpdate. No overlapping edits with parallel agents.

> D17 Note: Two-Channel protocol — Ch2 (file output to tasks/{work_dir}/) + Ch3 (micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Decision Points

### Wave Priority Selection
When >4 tasks are eligible for the same wave:
- **Critical path tasks present**: Prioritize critical path first. Fill remaining slots by fan-out descending.
- **No critical path contention**: Sort by fan-out (most dependents first), then complexity descending.
- **Tie**: Task ID order (deterministic).

### Single-Task Wave Treatment
- **Wave N-1 has < 4 tasks AND dependency allows merge**: Merge into wave N-1. Reduces total wave count.
- **Dependency prevents merge**: Accept single-task wave. Flag as scheduling bottleneck in L2.
- **Final wave** (integration/aggregation): Always acceptable.

### Load Balance Threshold
- **Total files > 12 per wave**: Split highest-file-count task to next wave if dependencies allow.
- **Total files ≤ 12**: Accept current distribution. No rebalancing needed.
- **Single task > 6 files**: Flag as agent complexity warning regardless of wave total.

## Methodology

### 1. Read Verified Plan
Load plan-verify-coordinator L3 via `$ARGUMENTS`. Extract task list, dependency graph, file assignments, phase structure.

Build analyst DPS with D11 context filter:
- **INCLUDE**: Verified plan L3, platform constraint (max 4 parallel/wave), wave scheduling principles
- **EXCLUDE**: Other orchestrate dimension outputs, historical rationale, full pipeline state
- **Budget**: Context field ≤ 30% of subagent effective context
- **Delivery (Ch2+Ch3)**: Write to `tasks/{work_dir}/p5-orch-impact.md`. Ch3: `PASS|waves:{N}|max_parallel:{N}|ref:tasks/{work_dir}/p5-orch-impact.md`. file-based output to orchestrate-coordinator: `READY|path:tasks/{work_dir}/p5-orch-impact.md|fields:wave_schedule,parallel_limits,capacity`

### 2. Build Execution DAG
Construct directed acyclic graph from dependency edges. Verify acyclicity via topological sort. Identify root nodes (in-degree = 0). On cycle detected: FAIL → route to plan-verify-coordinator.

### 3. Group Tasks Into Waves
Topological wave assignment: max 4 tasks/wave, all dependencies in prior waves. Priority order: critical path → fan-out → complexity → task ID. Defer overflow to next wave.

### 4. Balance Wave Load + Critical Path
Merge single-task waves into prior wave if dependencies allow. Enforce no wave >12 files total. Compute critical path (tasks with slack = 0). Estimate total pipeline token cost; flag if >1.5M tokens.

### 5. Output Wave Capacity Schedule
Produce ordered waves with task assignments, per-wave load metrics, critical path, total wave count, and parallelism efficiency score.

> For DAG construction steps, wave assignment algorithm pseudocode, load metrics tables, pipeline cost
> estimation format, and dependency chain depth analysis: read `resources/methodology.md`

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Plan L3 path empty or file missing (transient) | L0 Retry | Re-invoke after plan-verify-coordinator re-exports |
| Wave schedule incomplete or dependency order ambiguous | L1 Nudge | Respawn with refined DPS targeting refined capacity constraints |
| Agent stuck, context polluted, turns exhausted | L2 Respawn | Kill → fresh analyst with refined DPS |
| Cycle in DAG unresolvable without plan restructure | L3 Restructure | Route to plan-verify-coordinator for dependency redesign |
| 3+ L2 failures or DAG unschedulable within wave limits | L4 Escalate | AskUserQuestion with situation + options |

> For failure sub-case details (verbose prose): read `resources/methodology.md`

## Anti-Patterns
- **DO NOT** exceed 4 concurrent tasks per wave — CC Agent Teams hard limit, causes execution failure.
- **DO NOT** move tasks to earlier waves when their dependency is in that or a later wave — dependency ordering is absolute.
- **DO NOT** split independent tasks across waves — independent tasks must share a wave; separate waves waste execution time.
- **DO NOT** ignore critical path — non-critical tasks before critical ones waste capacity and extend total time.
- **DO NOT** schedule without complexity awareness — 4 HIGH-complexity tasks/wave creates a longer bottleneck than 4 LOW.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-verify-coordinator | Verified plan L3 | File path via $ARGUMENTS: tasks, dependencies, complexity |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestrate-coordinator | Wave capacity schedule | Always (WHEN dimension output) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Plan L3 missing | plan-verify-coordinator | Missing file path |
| Cycle detected | plan-verify-coordinator | Cycle path details |
| All waves scheduled | orchestrate-coordinator | Complete schedule (normal flow) |

## Quality Gate
- All tasks assigned to exactly 1 wave
- No wave exceeds 4 parallel tasks
- All dependencies respected (producer wave < consumer wave)
- DAG is acyclic (topological sort succeeds)
- Critical path identified and documented
- No unnecessary sequential waves (independent tasks in parallel)
- Load balance score documented per wave

## Output

### L1
```yaml
domain: orchestration
skill: impact
dimension: WHEN
wave_count: 0
max_parallel: 0
critical_path_length: 0
waves:
  - id: 1
    tasks: []
    task_count: 0
    file_count: 0
    agent_types: []
pt_signal: "metadata.phase_signals.p5_orchestrate_impact"
signal_format: "PASS|waves:{N}|max_parallel:{N}|ref:tasks/{work_dir}/p5-orch-impact.md"
```

### L2
- Wave schedule visualization (ASCII timeline)
- Critical path analysis
- Load balance metrics per wave
- DAG visualization with wave coloring
- Scheduling decisions rationale
