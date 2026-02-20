---
name: plan-impact
description: >-
  Sequences execution order by propagation containment into
  checkpoint-bounded waves. Groups tasks by propagation
  independence. Parallel with plan-static, plan-behavioral, and
  plan-relational. Use after research-coordinator complete. Reads
  from research-coordinator audit-impact L3 propagation paths via
  $ARGUMENTS. Produces execution sequence with wave groups and
  checkpoints, and sequencing rationale for plan-verify-impact.
  On FAIL (HIGH uncontained propagation), routes back to
  plan-impact with additional path data. DPS needs
  research-coordinator audit-impact L3 propagation paths. Exclude
  static, behavioral, and relational dimension data.
user-invocable: true
disable-model-invocation: true
---

# Plan — Impact Sequencing

## Execution Model
- **TRIVIAL**: Lead-direct. Linear sequence with 1-2 groups. No propagation risk.
- **STANDARD**: Spawn analyst. Systematic grouping and checkpoint placement across 3-8 tasks.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep propagation analysis across 9+ tasks with multi-wave containment boundaries.

## Phase-Aware Execution

This skill runs in Two-Channel protocol only. Single-session subagent execution:
- **Subagent writes** output file to `tasks/{work_dir}/p3-plan-impact.md`
- **Ch3 micro-signal** to Lead with PASS/FAIL status
- **Task tracking**: Subagent calls TaskUpdate on completion. File ownership: only modify assigned files.

## Decision Points

### Wave Grouping Strategy
When tasks exceed single-wave capacity or have complex propagation.
- **Single wave**: If all tasks are propagation-independent (0 cross-task paths). Group all (max 4) in Wave 1.
- **Multi-wave sequential**: If linear propagation chain exists. Sequence producer before consumer, 1-2 tasks per wave.
- **Multi-wave parallel**: If independent clusters exist. Maximize parallel grouping (max 4 per wave), minimize total waves.

### Checkpoint Density
When deciding checkpoint frequency between waves.
- **Minimal (TRIVIAL)**: After final wave only. Low propagation risk justifies speed.
- **Moderate (STANDARD)**: After waves containing DIRECT propagation sources. Balance speed and safety.
- **Maximum (COMPLEX)**: After every wave with high-risk sources (DIRECT to 3+ targets or TRANSITIVE). Safety over speed.

## Methodology

### 1. Read Audit-Impact L3 (Propagation Paths)
Load the audit-impact L3 file path from `$ARGUMENTS`. Validate input contains propagation paths, DIRECT/TRANSITIVE classification, risk scores, and blast radius estimates. If absent, route to Failure Handling (Missing Audit Input).
See: `resources/methodology.md §Depth Calculation Steps` for blast radius scoring.

### 2. Define Parallel Execution Groups (Max 4 Per Wave)
Group tasks into parallel execution waves based on propagation containment. Tasks with zero incoming propagation form Wave 1; subsequent waves contain tasks whose all sources are in completed waves.

**Propagation-safe parallelism check:**
| Condition | Parallel Safe? | Reason |
|-----------|----------------|--------|
| No propagation path between tasks | Yes | Independent changes |
| DIRECT propagation, same direction | No | Must sequence producer -> consumer |
| TRANSITIVE propagation only | Conditional | Safe if intermediate is stable |
| Bidirectional propagation | No | Must merge into same wave or sequence |

See: `resources/methodology.md §Wave Construction Format` for group formation algorithm and wave output format.

### 3. Set Checkpoint Boundaries Between Waves
Insert verification checkpoints between waves to contain propagation failures.

**Checkpoint placement rules:**
- ALWAYS insert checkpoint after a wave containing high-risk propagation sources
- ALWAYS insert checkpoint before a wave that depends on multiple prior waves
- OPTIONAL checkpoint between low-risk sequential waves (speed vs safety tradeoff)

See: `resources/methodology.md §Checkpoint Schedule Format` for gate condition protocol.

### 4. Plan Propagation Containment Strategy
For each identified propagation path, define containment:
- **Isolation**: Change is self-contained. No propagation path exits the task.
- **Ordered propagation**: Change propagates in a controlled, sequenced manner. Consumer wave starts after producer checkpoint passes.
- **Blast radius limiting**: Change has wide propagation but impact is bounded. Define boundary explicitly.
- **Rollback trigger**: Define observable failure indicating uncontained propagation. Link to plan-behavioral rollback strategy.

**Containment classification per propagation path:**
| Path Type | Containment | Action |
|-----------|-------------|--------|
| No propagation | Isolation | No containment needed |
| DIRECT, single target | Ordered | Sequence waves, checkpoint between |
| DIRECT, multiple targets | Blast radius | Define boundary, checkpoint after |
| TRANSITIVE, 2+ hops | Blast radius + rollback | Checkpoint + defined rollback trigger |
| Circular propagation | Merge + isolate | Merge tasks into same wave, isolate wave |

### 5. Output Execution Sequence with Checkpoints
Produce wave assignments, checkpoint placements, containment strategy per propagation path, and parallel efficiency metric (1 - parallel_time/sequential_time).

See: `resources/methodology.md §DPS Templates` for TRIVIAL/STANDARD/COMPLEX analyst spawn templates.

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-impact: N` in PT before each invocation
- Iteration 1: strict mode (FAIL → return to research-coordinator with propagation path gaps)
- Iteration 2: relaxed mode (proceed with documented coverage gaps, flag in phase_signals)
- Max iterations: 2

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error or timeout during wave grouping | L0 Retry | Re-invoke same agent, same DPS |
| Wave assignment incomplete or propagation containment off-direction | L1 Nudge | Respawn with refined DPS targeting refined propagation scope constraints |
| Agent stuck on topological sort or context exhausted | L2 Respawn | Kill agent → fresh analyst with refined DPS |
| Wave structure broken or task count exceeds capacity requiring restructure | L3 Restructure | Modify wave plan, redefine containment boundaries |
| Strategic ambiguity on checkpoint density or 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Missing audit-impact L3 input | CRITICAL | research-coordinator | Yes | Cannot sequence without propagation data. Request re-run. |
| All tasks have bidirectional propagation | HIGH | plan-static | No | Request task boundary restructuring. Fallback: fully sequential execution. |
| Propagation paths exceed analysis capacity | MEDIUM | Self (truncate) | No | Analyze DIRECT paths only, defer TRANSITIVE. `status: partial`. |
| No propagation paths found (all isolated) | LOW | Complete normally | No | All tasks in one parallel wave. `wave_count: 1`. |

## Anti-Patterns

### DO NOT: Sequence Without Propagation Evidence
Execution order must be justified by propagation paths from audit-impact, not by intuition or file naming.

### DO NOT: Exceed 4 Tasks Per Wave
The subagent capacity constraint is absolute. Split into multiple sequential waves even if propagation-safe in parallel.

### DO NOT: Skip Checkpoints Between High-Risk Waves
Every wave containing a high-risk source (DIRECT to 3+ targets, or any TRANSITIVE path) must be followed by a checkpoint.

### DO NOT: Merge Propagation Containment with Rollback Strategy
Containment defines BOUNDARIES. Rollback defines RESPONSE. Containment is this skill; rollback is plan-behavioral.

### DO NOT: Optimize for Speed Over Safety on COMPLEX Tiers
Containment coverage takes priority over parallel efficiency for COMPLEX pipelines.

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
pt_signal: "metadata.phase_signals.p3_plan_impact"
signal_format: "{STATUS}|groups:{N}|checkpoints:{N}|ref:tasks/{work_dir}/p3-plan-impact.md"
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

## Resources
- `resources/methodology.md` — Depth calculation steps, wave construction format, checkpoint schedule format, DPS templates
- `.claude/resources/phase-aware-execution.md` — Team mode, Two-Channel Protocol, task tracking
- `.claude/resources/failure-escalation-ladder.md` — L0–L4 escalation definitions and triggers
- `.claude/resources/dps-construction-guide.md` — DPS v5 template, D11 context distribution
- `.claude/resources/output-micro-signal-format.md` — Ch2–Ch3 signal formats and examples
