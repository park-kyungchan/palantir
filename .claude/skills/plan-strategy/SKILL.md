---
name: plan-strategy
description: |
  [P3·Plan·Strategy] Implementation sequencing and risk mitigation strategist. Defines execution order, parallel work opportunities, rollback strategy, and risk mitigation approach for execution phase.

  WHEN: After plan-decomposition and plan-interface complete. Tasks and interfaces defined but execution strategy undefined.
  DOMAIN: plan (skill 3 of 3). Terminal skill. Runs after decomposition and interface.
  INPUT_FROM: plan-decomposition (task list), plan-interface (dependency ordering), design-risk (risk assessment), research-audit (external constraints).
  OUTPUT_TO: orchestration-decompose (execution strategy), plan-verify domain (complete plan for validation).

  METHODOLOGY: (1) Read task list, dependency order, and risk assessment, (2) Identify parallelizable task groups, (3) Define implementation sequence respecting dependencies, (4) Create rollback strategy per phase, (5) Define risk mitigation checkpoints.
  OUTPUT_FORMAT: L1 YAML execution sequence with parallel groups, L2 strategy with ordering rationale.
user-invocable: true
disable-model-invocation: false
---

# Plan — Strategy

## Execution Model
- **TRIVIAL**: Lead-direct. Simple sequential execution plan.
- **STANDARD**: Spawn analyst. Detailed strategy with parallelization and rollback.
- **COMPLEX**: Spawn 2-4 analysts. Divide: sequencing, risk mitigation, rollback.

## Decision Points

### Tier Assessment for Strategy Complexity
- **TRIVIAL**: 1-3 tasks, linear dependency chain, no parallelization opportunity. Lead creates simple sequential strategy directly.
- **STANDARD**: 4-8 tasks, some parallel opportunities, 1-2 risk checkpoints needed. Spawn 1 analyst for systematic strategy.
- **COMPLEX**: 9+ tasks, multiple parallel groups, multi-phase execution, 3+ risk checkpoints. Spawn 2-4 analysts divided by concern: sequencing, risk mitigation, rollback planning.

### Strategy Optimization Priority
What to optimize for depends on pipeline context:
- **Speed** (default): Maximize parallelism, minimize sequential phases. Best when no high-RPN risks and ample teammate capacity.
- **Safety** (when high-risk): Insert checkpoints after every risky phase, prefer sequential over parallel to limit blast radius. Best when design-risk identified critical failure modes.
- **Resource efficiency** (when capacity-constrained): Minimize total teammate instances across all phases. Best when other pipeline runs compete for resources.

Lead selects optimization priority based on:
1. design-risk L1: If any risk has RPN > 8 → Safety priority
2. If teammate capacity is limited (already 2+ active pipelines) → Resource efficiency
3. Otherwise → Speed priority

### Parallel Group Identification Rules
Tasks can be grouped for parallel execution when ALL conditions are met:
- No dependency edge between them (neither blocks the other)
- No file ownership conflict (different file assignments)
- Same execution context (both need same type of environment/setup)
- Combined teammate count ≤ 4 per phase

Tasks CANNOT be parallel when ANY condition applies:
- Producer-consumer relationship (Task B uses Task A's output file)
- Shared resource (both modify same configuration file)
- Integration dependency (both contribute to same integration test)

### Phase Boundary Placement
Where to place phase boundaries (synchronization points):
- **After critical path tasks**: Ensure critical outputs are verified before dependents start
- **After risky tasks**: Insert checkpoint for risk validation
- **At agent type transitions**: When Phase 1 is all analysts and Phase 2 is all implementers
- **At capacity boundaries**: When >4 teammates needed, split into phases

### Rollback Granularity Decision
- **Phase-level rollback** (default): Revert all changes from a single phase. Simple, clean boundaries.
- **Task-level rollback** (when feasible): Revert individual task's changes. Finer control but harder to manage cross-task dependencies.
- **No rollback** (for idempotent operations): If task is idempotent (re-running produces same result), rollback is unnecessary.
- **Heuristic**: Use phase-level for TRIVIAL/STANDARD, task-level for COMPLEX (where partial rollback may save significant rework).

## Methodology

### 1. Read Plan and Risk Assessment
Load plan-decomposition tasks, plan-interface ordering, and design-risk assessment.

### 2. Define Parallel Groups
Identify tasks that can execute simultaneously:
- No dependency edges between them
- No file ownership conflicts

**DPS — Analyst Spawn Template:**
- **Context**: Paste plan-decomposition L1 (tasks with dependencies), plan-interface L1 (ordering), and design-risk L1 (risk matrix with RPN scores). Include pipeline tier (TRIVIAL/STANDARD/COMPLEX).
- **Task**: "Identify parallelizable task groups (no dependency edges, no file conflicts). Build execution sequence table. For each high-RPN risk: insert checkpoint after risky task with verification step. Define rollback strategy per phase."
- **Constraints**: Read-only. No modifications. Focus on sequencing, not teammate assignment.
- **Expected Output**: L1 YAML with phase_count, phases[] (id, tasks, parallel, checkpoint). L2 execution sequence, risk checkpoints, rollback strategies.

#### Parallel Group Visualization
```
Phase 1 (parallel):     [Task-A] ∥ [Task-B] ∥ [Task-C]
                              │           │
Phase 2 (sequential):   [Task-D] ──────→ [Task-E]
                              │
Phase 3 (single):       [Task-F]
```

#### Parallelism Savings Estimation
For each phase, estimate:
- Sequential time: Sum of individual task durations
- Parallel time: Duration of longest task in parallel group
- Savings: Sequential time - Parallel time
- Document in L2 to justify phase structure

Example: Phase 1 with 3 tasks (est. 5min, 8min, 3min each)
- Sequential: 16 min
- Parallel: 8 min (limited by longest task)
- Savings: 8 min (50% reduction)

### 3. Build Execution Sequence

| Phase | Tasks | Agent Type | Parallel? | Depends On |
|-------|-------|-----------|-----------|------------|
| 1 | [task-A, task-B] | analyst | yes | -- |
| 2 | [task-C] | implementer | no | Phase 1 |
| 3 | [task-D, task-E] | infra-impl | yes | Phase 2 |

### 4. Plan Risk Mitigation
For each high-RPN risk from design-risk:
- Insert checkpoint after risky task
- Define verification step before proceeding
- Identify early warning signals

#### Risk Checkpoint Protocol
For each checkpoint inserted after a risky task:
1. **Gate condition**: What must be true before proceeding (e.g., "all tests pass", "API returns 200")
2. **Verification method**: How to check the condition (e.g., "run test suite", "manual curl check")
3. **Failure action**: What to do if gate fails (e.g., "rollback phase", "retry task", "escalate to plan revision")
4. **Timeout**: Maximum wait time before treating as failure (default: 5 minutes per checkpoint)

#### Risk Mitigation Strategies by Type
| Risk Type | Mitigation | Checkpoint |
|-----------|-----------|------------|
| Integration failure | Interface contracts + integration test task | After integration task |
| Performance regression | Benchmark task in execution plan | After performance-critical task |
| Security vulnerability | Security review task (analyst) | After auth/data-handling task |
| External dependency failure | Fallback implementation task | After external API integration |
| Data migration error | Backup task before migration | Before and after migration task |

### 5. Define Rollback Strategy
For each execution phase:
- **Rollback trigger**: What condition triggers rollback
- **Rollback action**: Git revert, file restore, task re-assignment
- **Recovery point**: Where to resume after rollback

#### Rollback Strategy Template
For each execution phase:
```
Phase {N} Rollback:
  Trigger: {condition that activates rollback}
  Scope: {which files/changes are reverted}
  Method: {git revert, file restore, task re-run}
  Recovery point: {which phase to resume from after rollback}
  Dependencies: {which other phases are affected by this rollback}
  Estimated recovery time: {minutes}
```

#### Rollback Dependency Chain
If Phase 3 rolls back and Phase 4 depends on Phase 3's output:
- Phase 4 must also be rolled back or paused
- After Phase 3 re-executes, Phase 4 can resume
- Document these chains to prevent orphaned phases running with stale inputs

### 6. Consolidate Execution Plan
Merge all above into a single execution plan document.
This is the primary input for orchestration-decompose.

## Failure Handling

### Insufficient Input Data
- **Cause**: plan-decomposition or plan-interface didn't complete fully
- **Action**: Proceed with available data, flag gaps. Set `status: partial`.
- **Routing**: plan-verify will catch missing strategy elements

### Unresolvable Dependency Conflict
- **Cause**: Tasks with circular dependencies that plan-interface didn't resolve
- **Action**: Route back to plan-decomposition for task restructuring. Include dependency graph with cycle highlighted.

### Risk Assessment Missing
- **Cause**: design-risk didn't produce risk scores (skipped in TRIVIAL/STANDARD tiers)
- **Action**: Proceed without risk checkpoints. Note in L2: "No risk checkpoints — design-risk was not executed." Pipeline continues normally.

### Capacity Overflow
- **Cause**: Strategy requires >4 teammates per phase and cannot be phased further
- **Action**: Reduce parallelism — merge parallel groups into sequential execution. Accept longer execution time in exchange for capacity compliance.
- **Never exceed**: the 4-teammate limit, even if it means slower execution.

### Analyst Failed to Complete Strategy
- **Cause**: COMPLEX tier analyst ran out of turns
- **Action**: Set `status: partial`. Include completed phases and flag incomplete phases.
- **Routing**: plan-verify can still validate completed portions.

## Anti-Patterns

### DO NOT: Optimize Sequencing Without Dependencies
Execution order must be driven by dependency edges, not intuition. "Do the easy tasks first" is not a valid sequencing rationale — it may leave critical path tasks for last.

### DO NOT: Skip Rollback Planning
Every phase needs a rollback strategy, even if it's "git revert all changes from this phase." Without rollback, execution failures require manual recovery.

### DO NOT: Create Single-Task Phases
Unless the task is a critical checkpoint, avoid phases with a single task — this adds synchronization overhead without benefit. Merge single-task phases with adjacent phases.

### DO NOT: Assume All Tasks Take Equal Time
Task complexity estimates from plan-decomposition should drive phase scheduling. Grouping a COMPLEX task with three TRIVIAL tasks in the same parallel phase means waiting for the COMPLEX task while TRIVIAL tasks finished long ago.

### DO NOT: Specify Teammate Assignments
Strategy defines execution PHASES and ORDERING, not teammate assignments. That's orchestration-decompose/assign's responsibility. Don't prematurely lock in agent types here.

### DO NOT: Insert Checkpoints After Every Task
Only insert checkpoints after high-RPN risk tasks identified by design-risk. Excessive checkpoints slow execution without proportional safety benefit.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-decomposition | Task list with dependencies and complexity | L1 YAML: `tasks[].{id, files[], complexity, depends_on[]}` |
| plan-interface | Implementation ordering and interface contracts | L1 YAML: `implementation_tiers`, `contracts[]` |
| design-risk | Risk assessment with RPN scores | L1 YAML: `risks[].{description, rpn, mitigation}` |
| research-audit | External constraints | L2: technology constraints, version requirements |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration-decompose | Execution strategy (phases, ordering, risk checkpoints) | Always (strategy is orchestration input) |
| plan-verify domain | Complete execution plan for validation | Always (strategy → plan-verify) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Circular dependencies | plan-decomposition | Cycle details |
| Capacity overflow | Self (re-strategize with less parallelism) | Current strategy + constraint |
| Incomplete strategy | plan-verify (degraded) | Partial strategy with gap flags |

## Quality Gate
- Every task appears in exactly 1 execution phase
- Parallel groups respect 4-teammate limit
- High-RPN risks have checkpoints
- Rollback strategy covers every phase

## Output

### L1
```yaml
domain: plan
skill: strategy
phase_count: 0
parallel_groups: 0
risk_checkpoints: 0
phases:
  - id: ""
    tasks: []
    parallel: true|false
    checkpoint: true|false
```

### L2
- Execution sequence with parallel groups
- Risk mitigation checkpoints
- Rollback strategy per phase
