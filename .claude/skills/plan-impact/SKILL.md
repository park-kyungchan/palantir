---
name: plan-impact
description: |
  [P3·Plan·ImpactSequencing] Sequences execution order by propagation containment into checkpoint-bounded waves.

  WHEN: After research-coordinator complete. Wave 3 parallel with plan-static/behavioral/relational.
  DOMAIN: plan (skill 4 of 4). Wave 3 parallel execution.
  INPUT_FROM: research-coordinator (audit-impact L3 propagation paths via $ARGUMENTS).
  OUTPUT_TO: plan-verify-impact (execution sequence with checkpoints for verification).

  METHODOLOGY: (1) Read audit-impact L3 propagation paths and blast radius, (2) Group tasks into parallel waves (max 4 per wave) by propagation independence, (3) Set checkpoint boundaries between high-risk waves, (4) Define containment strategy per path (isolation/ordered/blast-limit/rollback), (5) Output execution sequence with parallel efficiency metric.
  OUTPUT_FORMAT: L1 YAML execution sequence with wave groups and checkpoints, L2 sequencing rationale with containment strategy.
user-invocable: false
disable-model-invocation: false
---

# Plan — Impact Sequencing

## Execution Model
- **TRIVIAL**: Lead-direct. Linear sequence with 1-2 groups. No propagation risk.
- **STANDARD**: Spawn analyst. Systematic grouping and checkpoint placement across 3-8 tasks.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep propagation analysis across 9+ tasks with multi-wave containment boundaries.

## Phase-Aware Execution
- **Standalone / P0-P1**: Spawn agent with `run_in_background`. Lead reads TaskOutput directly.
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers result via SendMessage micro-signal per conventions.md protocol.
- **Delivery**: Agent writes to `/tmp/pipeline/p3-plan-impact.md`, sends micro-signal: `{STATUS}|groups:{N}|checkpoints:{N}|ref:/tmp/pipeline/p3-plan-impact.md`

## Methodology

### 1. Read Audit-Impact L3 (Propagation Paths)
Load the audit-impact L3 file path provided via `$ARGUMENTS`. This file contains:
- Change propagation paths (which files are affected when file X changes)
- Impact classification: DIRECT (1-hop import/reference) vs TRANSITIVE (2+ hops)
- Propagation risk scores per path (likelihood of cascading failure)
- Blast radius estimates per change point

Validate the input exists and contains propagation data. If absent, route to Failure Handling (Missing Audit Input).

### 2. Define Parallel Execution Groups (Max 4 Per Wave)
Group tasks into parallel execution waves based on propagation containment:

**Grouping principles:**
- Tasks whose changes do NOT propagate to each other can run in parallel
- Tasks whose changes DO propagate must be sequenced (producer before consumer)
- Maximum 4 tasks per parallel wave (teammate capacity constraint)
- Minimize total wave count (optimize for speed while respecting safety)

**Group formation algorithm:**
1. Identify tasks with zero incoming propagation (root changes) -- these form Wave 1
2. For remaining tasks, identify those whose ALL propagation sources are in completed waves
3. Group eligible tasks into the next wave (max 4 per wave)
4. Repeat until all tasks assigned to a wave

**Propagation-safe parallelism check:**
| Condition | Parallel Safe? | Reason |
|-----------|---------------|--------|
| No propagation path between tasks | Yes | Independent changes |
| DIRECT propagation, same direction | No | Must sequence producer -> consumer |
| TRANSITIVE propagation only | Conditional | Safe if intermediate is stable |
| Bidirectional propagation | No | Must merge into same wave or sequence |

### 3. Set Checkpoint Boundaries Between Waves
Insert verification checkpoints between waves to contain propagation failures:

**Checkpoint placement rules:**
- ALWAYS insert checkpoint after a wave containing high-risk propagation sources
- ALWAYS insert checkpoint before a wave that depends on multiple prior waves
- OPTIONAL checkpoint between low-risk sequential waves (speed vs safety tradeoff)

**Checkpoint protocol:**
```
Checkpoint CP-{N} (after Wave {M}):
  Verify: All Wave {M} changes are stable (no test failures, no unexpected side effects)
  Gate: Propagation targets of Wave {M} changes are unaffected OR expected
  On pass: Release Wave {M+1}
  On fail: Rollback Wave {M}, assess propagation damage
  Timeout: 5 minutes
```

**Checkpoint density by tier:**
| Tier | Checkpoint Frequency | Rationale |
|------|---------------------|-----------|
| TRIVIAL | After final wave only | Low propagation risk |
| STANDARD | After waves with DIRECT propagation | Moderate containment |
| COMPLEX | After every wave with high-risk sources | Maximum containment |

### 4. Plan Propagation Containment Strategy
For each identified propagation path, define containment:

**Containment strategies:**
- **Isolation**: Change is self-contained. No propagation path exits the task. Safest.
- **Ordered propagation**: Change propagates but in a controlled, sequenced manner. Consumer wave starts after producer checkpoint passes.
- **Blast radius limiting**: Change has wide propagation but impact is bounded. Define the boundary explicitly (which files are "inside" and "outside" blast radius).
- **Rollback trigger**: Define what observable failure indicates uncontained propagation. Link to plan-behavioral rollback strategy for response.

**Containment classification per propagation path:**
| Path Type | Containment | Action |
|-----------|-------------|--------|
| No propagation | Isolation | No containment needed |
| DIRECT, single target | Ordered | Sequence waves, checkpoint between |
| DIRECT, multiple targets | Blast radius | Define boundary, checkpoint after |
| TRANSITIVE, 2+ hops | Blast radius + rollback | Checkpoint + defined rollback trigger |
| Circular propagation | Merge + isolate | Merge tasks into same wave, isolate wave |

### 5. Output Execution Sequence with Checkpoints
Produce the complete execution sequence:
- Wave assignments with task lists and parallel groupings
- Checkpoint placements with gate conditions
- Containment strategy per propagation path
- Metrics: total waves, parallel efficiency, containment coverage

**Parallel efficiency metric:**
- Sequential time: Sum of all task durations across all waves
- Parallel time: Sum of max-task-duration per wave
- Efficiency: 1 - (parallel_time / sequential_time)

**DPS -- Analyst Spawn Template:**
- **Context**: Paste audit-impact L3 content (propagation paths, impact classification, blast radius estimates). Include pipeline tier and task list from plan-static if available.
- **Task**: "Group tasks into parallel execution waves (max 4 per wave) based on propagation containment. Insert checkpoints between waves with gate conditions. Define containment strategy per propagation path. Calculate parallel efficiency metric."
- **Constraints**: Read-only analysis. No file modifications. Focus on sequencing and containment, not teammate assignment.
- **Expected Output**: L1 YAML with wave_count, checkpoint_count, groups[] and checkpoints[]. L2 sequencing rationale with containment strategy.
- **Delivery**: Write full result to `/tmp/pipeline/p3-plan-impact.md`. Send micro-signal to Lead: `PASS|groups:{N}|checkpoints:{N}|ref:/tmp/pipeline/p3-plan-impact.md`.

## Failure Handling
| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Missing audit-impact L3 input | CRITICAL | research-coordinator | Yes | Cannot sequence without propagation data. Request re-run. |
| All tasks have bidirectional propagation | HIGH | plan-static | No | Request task boundary restructuring. Fallback: fully sequential execution. |
| Propagation paths exceed analysis capacity | MEDIUM | Self (truncate) | No | Analyze DIRECT paths only, defer TRANSITIVE. `status: partial`. |
| No propagation paths found (all isolated) | LOW | Complete normally | No | All tasks in one parallel wave. `wave_count: 1`. |

## Anti-Patterns

### DO NOT: Sequence Without Propagation Evidence
Execution order must be justified by propagation paths from audit-impact, not by intuition or file naming. "Do database first" is not valid unless the audit shows propagation from database changes to downstream consumers.

### DO NOT: Exceed 4 Tasks Per Wave
The teammate capacity constraint is absolute. If more than 4 independent tasks exist, split them into multiple sequential waves even if they are propagation-safe in parallel.

### DO NOT: Skip Checkpoints Between High-Risk Waves
Every wave containing a high-risk propagation source (DIRECT to 3+ targets, or any TRANSITIVE path) must be followed by a checkpoint. Skipping checkpoints for speed creates uncontained blast radius.

### DO NOT: Merge Propagation Containment with Rollback Strategy
Containment defines BOUNDARIES (where propagation stops). Rollback defines RESPONSE (what to do when containment fails). These are complementary concerns. Containment is this skill; rollback is plan-behavioral.

### DO NOT: Optimize for Speed Over Safety on COMPLEX Tiers
For COMPLEX pipelines, containment coverage takes priority over parallel efficiency. It is acceptable to have lower efficiency if containment is comprehensive.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-coordinator | audit-impact L3 file path | `$ARGUMENTS`: file path to L3 with propagation paths |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-impact | Execution sequence with checkpoints | Always (PASS or partial) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit input | research-coordinator | Which L3 file is missing |
| All bidirectional propagation | plan-static | Request task boundary restructuring |

## Quality Gate
- Every task assigned to exactly one execution wave
- No wave exceeds 4 tasks
- Propagation paths respected (producer wave before consumer wave)
- High-risk waves followed by checkpoints
- Containment strategy defined for every DIRECT and TRANSITIVE propagation path
- Parallel efficiency metric calculated

## Output

### L1
```yaml
domain: plan
skill: impact
status: complete|partial
wave_count: 0
checkpoint_count: 0
parallel_efficiency: 0.0
groups:
  - wave: 1
    tasks: []
    parallel: true
    propagation_risk: low|medium|high
checkpoints:
  - id: ""
    after_wave: 0
    gate_condition: ""
```

### L2
- Wave assignment table with task groupings
- Checkpoint placement rationale
- Propagation containment strategy per path
- Parallel efficiency analysis
