---
name: plan-strategy
description: |
  [P4·Plan·Strategy] Implementation sequencing and risk mitigation strategist. Defines execution order, parallel work opportunities, rollback strategy, and risk mitigation approach for execution phase.

  WHEN: After plan-decomposition and plan-interface complete. Tasks and interfaces defined but execution strategy undefined.
  DOMAIN: plan (skill 3 of 3). Terminal skill. Runs after decomposition and interface.
  INPUT_FROM: plan-decomposition (task list), plan-interface (dependency ordering), design-risk (risk assessment).
  OUTPUT_TO: orchestration-decompose (execution strategy), plan-verify domain (complete plan for validation).

  METHODOLOGY: (1) Read task list, dependency order, and risk assessment, (2) Identify parallelizable task groups, (3) Define implementation sequence respecting dependencies, (4) Create rollback strategy per phase, (5) Define risk mitigation checkpoints.
  OUTPUT_FORMAT: L1 YAML execution sequence with parallel groups, L2 markdown strategy with ordering rationale.
user-invocable: true
disable-model-invocation: false
---

# Plan — Strategy

## Execution Model
- **TRIVIAL**: Lead-direct. Simple sequential execution plan.
- **STANDARD**: Spawn analyst. Detailed strategy with parallelization and rollback.
- **COMPLEX**: Spawn 2-4 analysts. Divide: sequencing, risk mitigation, rollback.

## Methodology

### 1. Read Plan and Risk Assessment
Load plan-decomposition tasks, plan-interface ordering, and design-risk assessment.

### 2. Define Parallel Groups
Identify tasks that can execute simultaneously:
- No dependency edges between them
- No file ownership conflicts
- Within 4-teammate limit per group

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

### 5. Define Rollback Strategy
For each execution phase:
- **Rollback trigger**: What condition triggers rollback
- **Rollback action**: Git revert, file restore, task re-assignment
- **Recovery point**: Where to resume after rollback

### 6. Consolidate Execution Plan
Merge all above into a single execution plan document.
This is the primary input for orchestration-decompose.

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
