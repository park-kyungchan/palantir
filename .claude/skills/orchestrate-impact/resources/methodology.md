# Orchestrate Impact — Detailed Methodology

> On-demand reference. Contains DAG construction steps, wave assignment algorithm, load metrics
> tables, pipeline cost estimation, dependency chain analysis, and failure sub-case details.
> Load only when SKILL.md inline guidance is insufficient.

---

## DAG Construction Steps

1. Create node for each task (ID, description, complexity, file count)
2. Add directed edges for each dependency (A → B means A must complete before B)
3. Verify acyclicity (topological sort must succeed)
4. Compute in-degree for each node (number of predecessors)
5. Identify root nodes (in-degree = 0, can start immediately)

### DAG Validation Table

| Check | Expected | Failure Action |
|-------|----------|----------------|
| Acyclicity | Topological sort succeeds | Report cycle path → route to plan-verify-coordinator |
| Connectedness | All tasks reachable from roots | Orphan tasks flagged, added to earliest possible wave |
| No self-loops | No task depends on itself | Remove self-loop, flag in L2 |

---

## Wave Assignment Algorithm

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

### Priority Rules for Wave Assignment

When more than 4 tasks are eligible for the same wave:
1. **Critical path tasks first**: Tasks on the longest dependency chain get priority
2. **High fan-out tasks**: Tasks with many dependents get priority (unblocks more work)
3. **High complexity tasks**: Longer tasks start earlier to avoid bottleneck
4. **Tie-breaker**: Task ID order (deterministic)

### Wave Structure Example

| Wave | Tasks (max 4) | Dependencies Satisfied | Load Estimate |
|------|--------------|------------------------|---------------|
| W1 | [T1, T2, T3] | None (root tasks) | 3 agents, ~8 files |
| W2 | [T4, T5] | T1, T2 (from W1) | 2 agents, ~5 files |
| W3 | [T6] | T4, T5 (from W2) | 1 agent, ~3 files |

---

## Load Balancing Rules

- **Avoid single-task waves**: If wave N has 1 task and wave N-1 has <4 tasks, consider merging (only if dependencies allow)
- **Balance file counts**: No wave should have >12 files total across all tasks (agent context pressure)
- **Balance complexity**: Avoid putting all high-complexity tasks in one wave
- **Minimize total waves**: Fewer waves = less coordination overhead

### Load Metrics Per Wave

| Metric | Target | Warning Threshold |
|--------|--------|-------------------|
| Task count | 2–4 | 1 (under-utilized) |
| Total files | 4–10 | >12 (context pressure) |
| Max task complexity | MEDIUM | HIGH (bottleneck risk) |
| Agent type diversity | 1–2 types | 4 types (coordination overhead) |
| Estimated token cost | wave_count × avg_agents × ~200k | >1M tokens total |

---

## Pipeline Cost Estimation

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

---

## Critical Path Analysis

Compute the longest path through the DAG:
1. For each task, calculate earliest start time (max of predecessor completion times)
2. For each task, calculate latest start time (total schedule minus remaining path)
3. Slack = latest start − earliest start
4. Critical path = tasks with slack = 0
5. Report critical path length (number of waves on critical path)

---

## Dependency Chain Depth Analysis

### Chain Depth Metrics

| Metric | Formula | Warning Threshold |
|--------|---------|-------------------|
| Max chain depth | Longest path in DAG (node count) | > total_waves / 2 |
| Serialization ratio | max_chain_depth / total_tasks | > 0.5 (most tasks serialized) |
| Parallelism efficiency | total_tasks / (wave_count × avg_tasks_per_wave) | < 0.6 |

### Bottleneck Detection

For each serial chain of depth >= 3:
1. **Identify the chain**: List task sequence T_a → T_b → T_c → ...
2. **Measure fan-in/fan-out**: Does the chain bottleneck wider parallel work?
3. **Assess splittability**: Can any task in the chain be split to increase parallelism?
4. **Recommend**: If serialization ratio > 0.5, include RESTRUCTURE_HINT in L2 output with:
   - Which chain(s) are bottlenecks
   - Which task(s) could be split (by file count, by logical sub-module)
   - Expected wave reduction from the split

### Chain Analysis Output Format

Include in L2:

```
Serial Chains:
  Chain 1: T2 → T5 → T8 (depth: 3, files: 12)
    Bottleneck: T5 (6 files, HIGH complexity)
    Splittable: Yes — T5a (files 1-3) + T5b (files 4-6), saves 1 wave
  Chain 2: T1 → T3 (depth: 2, files: 5)
    Bottleneck: None (short chain, acceptable)
```

---

## Failure Sub-Cases (Verbose)

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
