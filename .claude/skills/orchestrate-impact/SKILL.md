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
user-invocable: false
disable-model-invocation: false
---

# Orchestrate — Impact (WHEN)

## Execution Model
- **TRIVIAL**: Skip (orchestration simplified for trivial tiers).
- **STANDARD**: Spawn 1 analyst. Systematic wave grouping with dependency awareness.
- **COMPLEX**: Spawn 1 analyst with maxTurns:25. Deep DAG analysis with load balancing and critical path optimization.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Decision Points

### Wave Priority Selection
When more than 4 tasks are eligible for the same wave:
- **Critical path tasks present** (longest dependency chain): Prioritize critical path tasks first. Fill remaining slots by fan-out descending.
- **No critical path contention**: Sort by fan-out (most dependents first), then complexity descending.
- **Tie** (equal priority scores): Use task ID order for deterministic scheduling.

### Single-Task Wave Treatment
When a wave contains only 1 task:
- **If wave N-1 has < 4 tasks AND dependency allows merge**: Merge task into wave N-1. Reduces total wave count.
- **If dependency prevents merge** (task depends on all N-1 outputs): Accept single-task wave. Flag as scheduling bottleneck in L2.
- **If task is final wave** (integration/aggregation): Always acceptable. Solo final waves are normal.

### Load Balance Threshold
When wave file count exceeds targets:
- **Total files > 12 per wave**: Split highest-file-count task to next wave (if dependencies allow). Agent context pressure risk.
- **Total files <= 12**: Accept current distribution. No rebalancing needed.
- **Single task has > 6 files**: Flag as agent complexity warning regardless of wave total.

## Methodology

### 1. Read Verified Plan
Load plan-verify-coordinator L3 output via `$ARGUMENTS` path. Extract:
- Task list with IDs, descriptions, complexity estimates
- Dependency graph (directed edges: A must complete before B)
- File assignments per task (for load estimation)
- Phase structure (if pre-defined in plan)

For STANDARD/COMPLEX tiers, construct the delegation prompt for the analyst with:
- **Context (D11 priority: cognitive focus > token efficiency)**:
  INCLUDE:
    - Verified plan L3 content (task list, dependency graph, complexity estimates)
    - Platform constraint: max 4 teammates per wave (CC Agent Teams hard limit)
    - Wave scheduling principles: dependency-respecting, load-balanced, minimize total waves
  EXCLUDE:
    - Other orchestrate dimension outputs (static, behavioral, relational)
    - Historical rationale from plan-verify phases
    - Full pipeline state beyond this task's scope
  Budget: Context field ≤ 30% of teammate effective context
- **Task**: "Build execution DAG from task dependencies. Group tasks into waves: each wave has max 4 parallel tasks, all dependencies satisfied by prior waves. Balance load across waves (avoid 1-task waves where possible). Compute critical path. Output wave capacity schedule."
- **Constraints**: Read-only analysis. No modifications. Hard limit: max 4 parallel tasks per wave. Soft goal: minimize total wave count. Never violate dependency ordering.
- **Expected Output**: L1 YAML wave schedule. L2 wave visualization with load metrics and critical path.
- **Delivery**: Write full result to `tasks/{team}/p5-orch-impact.md`. Send micro-signal to Lead via SendMessage: `PASS|waves:{N}|max_parallel:{N}|ref:tasks/{team}/p5-orch-impact.md`.

#### Step 1 Tier-Specific DPS Variations
**TRIVIAL**: Skip — Lead assigns sequential execution (1-2 tasks, no wave scheduling needed).
**STANDARD**: Single DPS to analyst. maxTurns:15. Simple wave grouping without critical path analysis. Omit load balance optimization.
**COMPLEX**: Full DPS as above. maxTurns:25. Deep DAG analysis with load balancing, critical path optimization, and parallel efficiency metrics.

### 2. Build Execution DAG
Construct directed acyclic graph from task dependencies:

#### DAG Construction Steps
1. Create node for each task (ID, description, complexity, file count)
2. Add directed edges for each dependency (A -> B means A must complete before B)
3. Verify acyclicity (topological sort must succeed)
4. Compute in-degree for each node (number of predecessors)
5. Identify root nodes (in-degree = 0, can start immediately)

#### DAG Validation
| Check | Expected | Failure Action |
|-------|----------|---------------|
| Acyclicity | Topological sort succeeds | Report cycle, route to plan-verify-coordinator |
| Connectedness | All tasks reachable from roots | Orphan tasks flagged, added to earliest possible wave |
| No self-loops | No task depends on itself | Remove self-loop, flag in L2 |

### 3. Group Tasks Into Waves
Apply wave assignment algorithm:

#### Wave Assignment Algorithm
```
wave = 0
remaining = all_tasks
while remaining is not empty:
    wave += 1
    eligible = tasks in remaining where all dependencies are in completed waves
    if len(eligible) > 4:
        select top 4 by priority (critical path first, then complexity desc)
        assign selected to this wave
    else:
        assign all eligible to this wave
    move assigned tasks to completed
```

#### Priority Rules for Wave Assignment
When more than 4 tasks are eligible for the same wave:
1. **Critical path tasks first**: Tasks on the longest dependency chain get priority
2. **High fan-out tasks**: Tasks with many dependents get priority (unblocks more work)
3. **High complexity tasks**: Longer tasks start earlier to avoid bottleneck
4. **Tie-breaker**: Task ID order (deterministic)

#### Wave Structure
| Wave | Tasks (max 4) | Dependencies Satisfied | Load Estimate |
|------|--------------|----------------------|---------------|
| W1 | [T1, T2, T3] | None (root tasks) | 3 agents, ~8 files |
| W2 | [T4, T5] | T1, T2 (from W1) | 2 agents, ~5 files |
| W3 | [T6] | T4, T5 (from W2) | 1 agent, ~3 files |

### 4. Balance Wave Load
Optimize wave assignments for efficiency:

#### Load Balancing Rules
- **Avoid single-task waves**: If wave N has 1 task and wave N-1 has <4 tasks, consider merging (only if dependencies allow)
- **Balance file counts**: No wave should have >12 files total across all tasks (agent context pressure)
- **Balance complexity**: Avoid putting all high-complexity tasks in one wave
- **Minimize total waves**: Fewer waves = less coordination overhead

#### Load Metrics Per Wave
| Metric | Target | Warning Threshold |
|--------|--------|-------------------|
| Task count | 2-4 | 1 (under-utilized) |
| Total files | 4-10 | >12 (context pressure) |
| Max task complexity | MEDIUM | HIGH (bottleneck risk) |
| Agent type diversity | 1-2 types | 4 types (coordination overhead) |
| Estimated token cost | wave_count × avg_agents × ~200k | > 1M tokens total |

#### Pipeline Cost Estimation
After wave scheduling, compute estimated total pipeline cost:
```
Cost estimate:
  Waves: {N}
  Avg agents per wave: {N}
  Est. tokens per agent: ~200k (Sonnet session)
  Total estimated: {waves × avg_agents × 200k} tokens
  Lead overhead: ~200k tokens
  Grand total: {sum} tokens
```
Include in L2 output. Flag if grand total exceeds 1.5M tokens (3-agent-team equivalent).

#### Critical Path Analysis
Compute the longest path through the DAG:
1. For each task, calculate earliest start time (max of predecessor completion times)
2. For each task, calculate latest start time (total schedule minus remaining path)
3. Slack = latest start - earliest start
4. Critical path = tasks with slack = 0
5. Report critical path length (number of waves on critical path)

### 4.5. Dependency Chain Depth Analysis
Analyze serial dependency chains for scheduling bottlenecks:

#### Chain Depth Metrics
| Metric | Formula | Warning Threshold |
|--------|---------|-------------------|
| Max chain depth | Longest path in DAG (node count) | > total_waves / 2 |
| Serialization ratio | max_chain_depth / total_tasks | > 0.5 (most tasks serialized) |
| Parallelism efficiency | total_tasks / (wave_count × avg_tasks_per_wave) | < 0.6 |

#### Bottleneck Detection
For each serial chain of depth >= 3:
1. **Identify the chain**: List task sequence T_a → T_b → T_c → ...
2. **Measure fan-in/fan-out**: Does the chain bottleneck wider parallel work?
3. **Assess splittability**: Can any task in the chain be split to increase parallelism?
4. **Recommend**: If serialization ratio > 0.5, include RESTRUCTURE_HINT in L2 output with:
   - Which chain(s) are bottlenecks
   - Which task(s) could be split (by file count, by logical sub-module)
   - Expected wave reduction from the split

#### Chain Analysis Output
Include in L2:
```
Serial Chains:
  Chain 1: T2 → T5 → T8 (depth: 3, files: 12)
    Bottleneck: T5 (6 files, HIGH complexity)
    Splittable: Yes — T5a (files 1-3) + T5b (files 4-6), saves 1 wave
  Chain 2: T1 → T3 (depth: 2, files: 5)
    Bottleneck: None (short chain, acceptable)
```

### 5. Output Wave Capacity Schedule
Produce complete schedule with:
- Ordered waves with task assignments
- Per-wave load metrics (task count, file count, agent types)
- Critical path identification
- Total execution timeline (wave count)
- Summary: total waves, max parallel, load balance score

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Plan L3 path empty or file missing (transient) | L0 Retry | Re-invoke after plan-verify-coordinator re-exports |
| Wave schedule incomplete or dependency order ambiguous | L1 Nudge | SendMessage with refined capacity constraints |
| Agent stuck, context polluted, turns exhausted | L2 Respawn | Kill → fresh analyst with refined DPS |
| Cycle in DAG unresolvable without plan restructure | L3 Restructure | Route to plan-verify-coordinator for dependency redesign |
| 3+ L2 failures or DAG unschedulable within wave limits | L4 Escalate | AskUserQuestion with situation + options |

### Verified Plan Data Missing
- **Cause**: $ARGUMENTS path is empty or L3 file not found
- **Action**: Report FAIL. Signal: `FAIL|reason:plan-L3-missing|ref:tasks/{team}/p5-orch-impact.md`
- **Route**: Back to plan-verify-coordinator for re-export

### Cycle Detected in DAG
- **Cause**: Circular dependency between tasks
- **Action**: Report FAIL with cycle path. Signal: `FAIL|reason:cycle-detected|ref:tasks/{team}/p5-orch-impact.md`
- **Route**: Back to plan-verify-coordinator for dependency restructuring

### Capacity Overflow (>4 Tasks All Eligible)
- **Cause**: Many independent tasks at same dependency level
- **Action**: Apply priority rules to select top 4. Defer remaining to next wave. Report in L2.
- **Note**: This is normal behavior, not an error. The algorithm handles it.

### Single-Task Wave Unavoidable
- **Cause**: Critical path bottleneck (one task depends on all previous, all subsequent depend on it)
- **Action**: Accept the single-task wave. Flag as scheduling bottleneck in L2. Recommend reviewing task decomposition.

## Anti-Patterns

### DO NOT: Violate the 4-Teammate Limit
The CC Agent Teams platform limit is 4 concurrent teammates. Scheduling 5+ parallel tasks in one wave will cause execution failure. This is a hard constraint.

### DO NOT: Ignore Dependencies for Load Balancing
Moving a task to an earlier wave for load balance when its dependency is in that same wave or a later wave will cause execution failure. Dependencies always take priority over balance.

### DO NOT: Create Unnecessary Sequential Waves
If tasks are independent, they should be in the same wave (up to capacity). Splitting independent tasks across waves wastes execution time.

### DO NOT: Ignore Critical Path
The critical path determines minimum execution time. Scheduling non-critical tasks before critical-path tasks wastes capacity and extends total time.

### DO NOT: Schedule Without Complexity Awareness
A wave with 4 high-complexity tasks will take longer than a wave with 4 low-complexity tasks. Consider complexity when balancing across waves.

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
signal_format: "PASS|waves:{N}|max_parallel:{N}|ref:tasks/{team}/p5-orch-impact.md"
```

### L2
- Wave schedule visualization (ASCII timeline)
- Critical path analysis
- Load balance metrics per wave
- DAG visualization with wave coloring
- Scheduling decisions rationale
