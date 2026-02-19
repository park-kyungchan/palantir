# Orchestrate Coordinator — Detailed Methodology

> On-demand reference. Contains dimension input table, tier DPS variations, unified task record
> format, merge conflict resolution table, cross-validation check tables (A-D), scheduling
> efficiency checks, RESTRUCTURE_HINT format, and L3 execution-plan YAML spec.
> Load only when SKILL.md inline guidance is insufficient.

---

## Dimension Input Table

| Dimension | Skill | Output File | Key Data |
|-----------|-------|-------------|----------|
| WHO | orchestrate-static | `tasks/{team}/p5-orch-static.md` | Task-agent assignment matrix |
| WHERE | orchestrate-behavioral | `tasks/{team}/p5-orch-behavioral.md` | Checkpoint schedule |
| HOW | orchestrate-relational | `tasks/{team}/p5-orch-relational.md` | DPS handoff specs |
| WHEN | orchestrate-impact | `tasks/{team}/p5-orch-impact.md` | Wave capacity schedule |

---

## Tier-Specific DPS Variations

**TRIVIAL**: Skip — Lead produces inline execution plan (1-2 tasks, no cross-validation needed).

**STANDARD**: Single DPS to analyst. maxTurns:20. Simplified cross-validation (Check A + D only). Produce L1+L2+L3.

**COMPLEX**: Full DPS. maxTurns:35. All 4 checks, conflict resolution, optimization recommendations.

DPS Context field (D11 principle — cognitive focus first):
- INCLUDE: All 4 dimension output paths, tiered output structure (L1/L2/L3), max 4 teammates/wave constraint
- EXCLUDE: plan-verify raw data, historical design rationale, full pipeline state
- Budget: Context field ≤ 30% of teammate effective context

---

## Unified Task Record Format

For each task, create a merged record combining all 4 dimensions:

```yaml
task:
  id: T1
  description: "..."
  # WHO (from static)
  agent_type: implementer
  tools_required: [Edit, Bash]
  # WHEN (from impact)
  wave: 1
  dependencies: []
  # HOW (from relational)
  inputs:
    - dps_id: DPS-01
      from_task: T0
      path: tasks/{team}/p6-input-schema.md
      format: yaml
  outputs:
    - dps_id: DPS-02
      to_task: T3
      path: tasks/{team}/p6-auth-module.md
      format: markdown
  # WHERE (from behavioral)
  checkpoint: CP-02
  checkpoint_type: gate
  checkpoint_criteria: "Test suite passes, module exports verified"
```

---

## Merge Conflict Resolution Table

| Conflict Type | Resolution Rule | Priority |
|---------------|----------------|----------|
| Task in static but not in impact | Add to earliest eligible wave | Impact adjusts |
| Task in impact but not in static | Flag as unassigned, route back to static | Static must fix |
| Handoff references non-existent task | Flag as dangling DPS, route back to relational | Relational must fix |
| Checkpoint at non-wave boundary | Remap to nearest wave boundary | Behavioral adjusts |
| Agent type cannot run in assigned wave | Swap wave or agent type | Impact + Static negotiate |

---

## Cross-Validation Check Tables

### Check A: Agent-Wave Fit

| Wave | Agent Types | Instance Count | Tools Available | Tasks Covered | Status |
|------|------------|---------------|-----------------|---------------|--------|
| W1 | impl x2, analyst x1 | 3 | Edit,Bash,Read,Glob | T1,T2,T3 | PASS |

Validate: agent has required tools for all wave tasks, no agent exceeds instance limit, total agents ≤ 4.

### Check B: Handoff-Sequence Order

| DPS ID | Producer (Wave) | Consumer (Wave) | Order Valid | Status |
|--------|----------------|-----------------|-------------|--------|
| DPS-01 | T1 (W1) | T3 (W2) | W1 < W2 | PASS |
| DPS-02 | T4 (W2) | T2 (W1) | W2 > W1 | FAIL |

Validate: producer wave < consumer wave (strict), no circular chains.

### Check C: Checkpoint-Wave Alignment

Gate checkpoints at wave completion boundaries. Aggregate checkpoints cover all wave tasks. Monitor checkpoints at meaningful transitions.

### Check D: Task Coverage Completeness

Every task appears exactly once. No duplicates. No orphaned tasks (missing agent, wave, or handoff).

---

## Scheduling Efficiency Checks (Step 3.5)

| Check | Condition | Action |
|-------|-----------|--------|
| Long serial chain | max_chain_depth > wave_count / 2 | Generate RESTRUCTURE_HINT |
| Single-task waves | > 1 wave with only 1 task (non-final) | Suggest task splitting |
| Low parallelism | avg tasks/wave < 2 for total > 6 tasks | Flag underutilization |
| Cost overrun | wave_count × 3 agents × ~200k > budget | Flag with consolidation options |

### RESTRUCTURE_HINT Format

```yaml
restructure_hints:
  - type: chain_bottleneck
    chain: [T2, T5, T8]
    bottleneck_task: T5
    suggestion: "Split T5 into T5a (files 1-3) + T5b (files 4-6)"
    expected_improvement: "Reduces wave count by 1, saves ~200k tokens"
  - type: underutilization
    wave: W3
    task_count: 1
    suggestion: "Split T8 into T8a + T8b to fill W3 capacity"
```

Lead reads RESTRUCTURE_HINTs from L2. HIGH-priority hint routes: (1) back to plan-static for re-decomposition, (2) to orchestrate-static for smart splits, or (3) accept with documented inefficiency.

---

## L3 Execution Plan Format

```yaml
waves:
  - id: W1
    parallel_count: 3
    checkpoint: CP-01
    tasks:
      - id: T1
        agent_type: implementer
        spawn_prompt: |
          Context: {D11 cognitive-focus filtered}
          Task: {what to implement}
          Constraints: {file ownership, interfaces}
          Expected Output: {deliverables}
          Delivery: Write to tasks/{team}/p6-T1-output.md
          COMM_PROTOCOL:
            NOTIFY: [{consumer_teammate_names}]
            SIGNAL_FORMAT: "READY|path:tasks/{team}/p6-T1-output.md|fields:{fields}"
            AWAIT: [{producer_teammate_names if sequential}]
        inputs: [{dps_id, path, format}]
        outputs: [{dps_id, path, format}]
        files: [file1.ts, file2.ts]
```

Required per task: agent type, complete DPS prompt, COMM_PROTOCOL (NOTIFY/SIGNAL_FORMAT/AWAIT), input/output DPS refs, file ownership, checkpoint criteria.
