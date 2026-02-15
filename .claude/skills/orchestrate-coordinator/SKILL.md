---
name: orchestrate-coordinator
description: |
  [P5·Orchestration·Coordinator] Unifies WHO+WHERE+HOW+WHEN into per-task spawn instructions with cross-validation.

  WHEN: After all 4 orchestrate-* skills complete. Wave 5.5 terminal.
  DOMAIN: orchestration (skill 5 of 5). Terminal. Produces unified plan for P6.
  INPUT_FROM: orchestrate-static (WHO: task-agent matrix), orchestrate-behavioral (WHERE: checkpoints), orchestrate-relational (HOW: DPS specs), orchestrate-impact (WHEN: wave schedule).
  OUTPUT_TO: execution-code + execution-infra (L3 unified execution plan). Lead reads L1 index + L2 summary.

  METHODOLOGY: (1) Read 4 dimension outputs from p5-orch-*.md, (2) Merge per-task: agent, wave, DPS, checkpoint, (3) Cross-validate: agent-wave fit, handoff order, checkpoint alignment, coverage, (4) L1 index + L2 summary for Lead, (5) L3 execution-plan with spawn DPS per wave.
  OUTPUT_FORMAT: Tiered: L1 index.md, L2 summary.md, L3 execution-plan.md at /tmp/pipeline/p5-coordinator/.
user-invocable: false
disable-model-invocation: false
---

# Orchestrate — Coordinator

## Execution Model
- **TRIVIAL**: Skip (orchestration simplified for trivial tiers).
- **STANDARD**: Spawn 1 analyst. Systematic merge and cross-validation of 4 dimension outputs.
- **COMPLEX**: Spawn 1 analyst with maxTurns:35. Deep cross-validation with conflict resolution and optimization.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn analyst with `team_name` parameter. Agent delivers result via SendMessage micro-signal per conventions.md protocol.
- **Delivery**: Write tiered output to `/tmp/pipeline/p5-coordinator/`. Send micro-signal to Lead via SendMessage: `PASS|tasks:{N}|waves:{N}|handoffs:{N}|ref:/tmp/pipeline/p5-coordinator/index.md`.

## Decision Points

### Merge Conflict Resolution Strategy
When dimension outputs disagree on task attributes:
- **Task in WHO but not WHEN** (static has it, impact doesn't): Add to earliest eligible wave. Impact adjusts.
- **Task in WHEN but not WHO** (impact has it, static doesn't): Flag as unassigned. Route back to orchestrate-static.
- **Handoff references non-existent task**: Flag as dangling DPS. Route back to orchestrate-relational.
- **Checkpoint at non-wave boundary**: Remap to nearest wave boundary. Behavioral adjusts.

### Cross-Validation Failure Severity
When a cross-validation check fails:
- **Check A FAIL (agent-wave fit)**: BLOCKING. Cannot produce L3. Route to orchestrate-static + orchestrate-impact for resolution.
- **Check B FAIL (handoff order)**: BLOCKING. Cannot produce L3. Route to orchestrate-relational + orchestrate-impact for resolution.
- **Check C WARN (checkpoint alignment)**: NON-BLOCKING. Remap checkpoint, document in L2. Produce L3 with warning.
- **Check D FAIL (task coverage)**: BLOCKING. Cannot produce L3. Identify missing dimension and route back.

### L3 Output Completeness
When producing L3 execution plan:
- **All 4 checks PASS**: Produce full L3 with spawn DPS per task. Normal flow.
- **Any BLOCKING check FAIL**: Do NOT produce L3. Report failure details in L1/L2 only.
- **Only WARN checks (no FAIL)**: Produce L3 with warnings flagged. Include remediation notes in L2.

## Methodology

### 1. Read All 4 Dimension Outputs
Load outputs from all 4 parallel orchestrate-* skills:

| Dimension | Skill | Output File | Key Data |
|-----------|-------|-------------|----------|
| WHO | orchestrate-static | `/tmp/pipeline/p5-orch-static.md` | Task-agent assignment matrix |
| WHERE | orchestrate-behavioral | `/tmp/pipeline/p5-orch-behavioral.md` | Checkpoint schedule |
| HOW | orchestrate-relational | `/tmp/pipeline/p5-orch-relational.md` | DPS handoff specs |
| WHEN | orchestrate-impact | `/tmp/pipeline/p5-orch-impact.md` | Wave capacity schedule |

For STANDARD/COMPLEX tiers, construct the delegation prompt for the analyst with:
- **Context**: Paste all 4 dimension outputs. Include tiered output structure: L1 (index.md = routing metadata), L2 (summary.md = narrative for Lead), L3 (execution-plan.md = full spawn instructions for P6). Include platform constraints: max 4 teammates per wave, SendMessage protocol for agent completion.
- **Task**: "Merge the 4 dimension outputs into a unified execution plan. For each task, consolidate: WHO runs it (agent type from static), WHEN it executes (wave from impact), HOW it gets/sends data (DPS from relational), WHERE it is verified (checkpoint from behavioral). Cross-validate: agent has right tools for its wave tasks, handoff ordering matches wave sequence, checkpoints align with wave boundaries. Produce L1 index, L2 summary, L3 execution plan."
- **Constraints**: Read-only analysis on inputs. Write tiered output to `/tmp/pipeline/p5-coordinator/`. Every task must appear in unified plan. Every cross-validation check must have explicit PASS/FAIL.
- **Expected Output**: Three files in `/tmp/pipeline/p5-coordinator/`: index.md (L1), summary.md (L2), execution-plan.md (L3).
- **Delivery**: Write tiered output to `/tmp/pipeline/p5-coordinator/`. Send micro-signal to Lead via SendMessage: `PASS|tasks:{N}|waves:{N}|handoffs:{N}|ref:/tmp/pipeline/p5-coordinator/index.md`.

#### Step 1 Tier-Specific DPS Variations
**TRIVIAL**: Skip — Lead produces inline execution plan (1-2 tasks, no cross-validation needed).
**STANDARD**: Single DPS to analyst. maxTurns:20. Merge 4 dimensions with simplified cross-validation (Check A + D only). Produce L1+L2+L3.
**COMPLEX**: Full DPS as above. maxTurns:35. Deep cross-validation with all 4 checks, conflict resolution, and optimization recommendations.

### 2. Merge Into Unified Plan
For each task, create a unified record combining all 4 dimensions:

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
      path: /tmp/pipeline/p6-input-schema.md
      format: yaml
  outputs:
    - dps_id: DPS-02
      to_task: T3
      path: /tmp/pipeline/p6-auth-module.md
      format: markdown
  # WHERE (from behavioral)
  checkpoint: CP-02
  checkpoint_type: gate
  checkpoint_criteria: "Test suite passes, module exports verified"
```

#### Merge Conflict Resolution
When dimension outputs disagree:
| Conflict Type | Resolution Rule | Priority |
|---------------|----------------|----------|
| Task in static but not in impact | Add to earliest eligible wave | Impact adjusts |
| Task in impact but not in static | Flag as unassigned, route back to static | Static must fix |
| Handoff references non-existent task | Flag as dangling DPS, route back to relational | Relational must fix |
| Checkpoint at non-wave boundary | Remap to nearest wave boundary | Behavioral adjusts |
| Agent type cannot run in assigned wave | Swap wave assignment or agent type | Impact + Static negotiate |

### 3. Cross-Validate Consistency
Run cross-dimensional validation checks:

#### Check A: Agent-Wave Fit
For each wave, verify assigned agents can handle the tasks:
- Agent type has required tools for all tasks in that wave
- No agent type exceeds instance limit within a wave
- Total agents in wave <= 4

| Wave | Agent Types | Instance Count | Tools Available | Tasks Covered | Status |
|------|------------|---------------|-----------------|---------------|--------|
| W1 | impl x2, analyst x1 | 3 | Edit,Bash,Read,Glob | T1,T2,T3 | PASS |

#### Check B: Handoff-Sequence Order
For each DPS handoff, verify producer wave precedes consumer wave:
- Producer task wave < consumer task wave (strict ordering)
- Handoff path exists before consumer needs it
- No circular handoff chains

| DPS ID | Producer (Wave) | Consumer (Wave) | Order Valid | Status |
|--------|----------------|-----------------|-------------|--------|
| DPS-01 | T1 (W1) | T3 (W2) | W1 < W2 | PASS |
| DPS-02 | T4 (W2) | T2 (W1) | W2 > W1 | FAIL |

#### Check C: Checkpoint-Wave Alignment
For each checkpoint, verify it aligns with a wave boundary:
- Gate checkpoints must be at wave completion boundaries
- Aggregate checkpoints cover all tasks in the target wave
- Monitor checkpoints can be anywhere but should be at meaningful transitions

| Checkpoint | Location | Wave Boundary? | Type Valid | Status |
|-----------|----------|---------------|------------|--------|
| CP-01 | After W1 | Yes (W1->W2) | Gate | PASS |
| CP-02 | Mid-W2 | No | Gate (should be monitor) | WARN |

#### Check D: Task Coverage Completeness
- Every task from the verified plan appears exactly once in the unified plan
- No duplicate task assignments (same task in multiple waves)
- No orphaned tasks (task with no agent, no wave, or no handoff)

### 4. Produce L1 Index + L2 Summary for Lead
Write routing-level output for Lead consumption:

**L1 (index.md)**: Compact YAML with task counts, wave counts, handoff counts, validation status, and file references.

**L2 (summary.md)**: Narrative summary with:
- Unified plan overview (task count, wave count, agent distribution)
- Cross-validation results (all 4 checks: PASS/FAIL/WARN)
- Identified conflicts and resolutions
- Critical path and bottleneck analysis
- Recommendations for P6 execution

### 5. Produce L3 Execution Plan for P6
Write detailed execution plan that P6 skills can consume directly:

**L3 (execution-plan.md)**: Complete spawn instructions per wave:
```yaml
waves:
  - id: W1
    parallel_count: 3
    checkpoint: CP-01
    tasks:
      - id: T1
        agent_type: implementer
        spawn_prompt: |
          Context: {what to include in DPS}
          Task: {what to implement}
          Constraints: {file ownership, interfaces}
          Expected Output: {deliverables}
          Delivery: {SendMessage signal format}
        inputs: [{dps_id, path, format}]
        outputs: [{dps_id, path, format}]
        files: [file1.ts, file2.ts]
```

The L3 file must contain ALL information needed to spawn teammates:
- Agent type per task
- Complete DPS prompt content (context, task, constraints, output, delivery)
- Input DPS references (what to read before starting)
- Output DPS references (what to produce)
- File ownership list
- Checkpoint criteria for wave completion

## Failure Handling

### One or More Dimension Outputs Missing
- **Cause**: A parallel orchestrate-* skill failed or has not completed
- **Action**: Report FAIL. Signal: `FAIL|reason:missing-{dimension}|ref:/tmp/pipeline/p5-coordinator/index.md`
- **Route**: Lead re-invokes the failed dimension skill

### Cross-Validation FAIL (Any Check)
- **Cause**: Inconsistency between dimension outputs
- **Action**: Attempt auto-resolution per merge conflict rules. If unresolvable, report FAIL with specific check and evidence.
- **Route**: Lead re-invokes the relevant dimension skill(s) with correction guidance

### Task Coverage Mismatch
- **Cause**: Unified plan has different task count than verified plan
- **Action**: Report exact discrepancy (missing tasks, extra tasks). FAIL if any task is missing.
- **Route**: Identify which dimension dropped/added the task, route back to that dimension

### Handoff-Sequence Order Violation
- **Cause**: Producer in later wave than consumer
- **Action**: Propose fix: move producer to earlier wave OR move consumer to later wave. Include both options with tradeoffs.
- **Route**: Lead decides, orchestrate-impact re-schedules if needed

## Anti-Patterns

### DO NOT: Produce L3 Without Cross-Validation
The L3 execution plan must be cross-validated before output. Skipping validation pushes errors to P6 execution where they are more expensive to fix.

### DO NOT: Omit Spawn Prompt Content from L3
The L3 must contain COMPLETE DPS prompts for each task. P6 execution skills should not need to reconstruct prompts from multiple sources. The coordinator is the single consolidation point.

### DO NOT: Ignore Merge Conflicts
When dimension outputs disagree, silently picking one side creates hidden inconsistencies. Every conflict must be resolved explicitly and documented in L2.

### DO NOT: Create L3 Without Handoff Paths
Every inter-task data dependency must have a concrete `/tmp/pipeline/` path in the L3. Tasks reading from undefined paths will fail at execution.

### DO NOT: Skip Agent-Wave Validation
A wave with 5 agents will fail. A wave where analyst is assigned a Bash-requiring task will fail. Agent-wave fit is the most critical cross-validation check.

### DO NOT: Produce Partial L3
If any cross-validation check FAILs, do NOT produce an L3 execution plan. A partial L3 misleads P6 into executing with known errors.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestrate-static | Task-agent assignment matrix (WHO) | L1 YAML + L2 rationale at `/tmp/pipeline/p5-orch-static.md` |
| orchestrate-behavioral | Checkpoint schedule (WHERE) | L1 YAML + L2 rationale at `/tmp/pipeline/p5-orch-behavioral.md` |
| orchestrate-relational | DPS handoff specs (HOW) | L1 YAML + L2 chain at `/tmp/pipeline/p5-orch-relational.md` |
| orchestrate-impact | Wave capacity schedule (WHEN) | L1 YAML + L2 timeline at `/tmp/pipeline/p5-orch-impact.md` |

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
| All checks PASS | execution-code / execution-infra | L3 execution plan (normal flow) |

## Quality Gate
- All 4 dimension outputs loaded and parsed
- Every task in unified plan has WHO, WHEN, HOW, WHERE fields populated
- Cross-validation Check A (agent-wave fit): PASS
- Cross-validation Check B (handoff-sequence order): PASS
- Cross-validation Check C (checkpoint-wave alignment): PASS or WARN only
- Cross-validation Check D (task coverage completeness): PASS
- L3 execution plan contains complete spawn instructions for every task
- L3 handoff paths are all concrete `/tmp/pipeline/` paths
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
  l2_summary: /tmp/pipeline/p5-coordinator/summary.md
  l3_execution_plan: /tmp/pipeline/p5-coordinator/execution-plan.md
```

### L2 (summary.md)
- Unified plan overview with counts and distribution
- Cross-validation results with evidence per check
- Conflict resolutions and rationale
- Critical path and execution timeline
- Agent distribution across waves
- Recommendations for P6 execution

### L3 (execution-plan.md)
- Per-wave spawn instructions with complete DPS prompts
- Input/output handoff references per task
- File ownership per task
- Checkpoint criteria per wave boundary
- Agent type and tool requirements per task
