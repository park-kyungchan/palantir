---
name: plan-strategy
description: |
  [P4·Plan·Strategy] Implementation sequencing and risk mitigation strategist. Defines implementation order, parallel work opportunities, rollback strategy, and risk mitigation approach for execution phase.

  WHEN: After plan-decomposition and plan-interface complete. Tasks and interfaces defined but execution strategy undefined.
  DOMAIN: plan (skill 3 of 3). Terminal skill in plan domain. Runs after decomposition and interface.
  INPUT_FROM: plan-decomposition (task list), plan-interface (dependency ordering), design-risk (risk assessment).
  OUTPUT_TO: orchestration-decompose (execution strategy for orchestration), plan-verify domain (complete plan for validation).

  METHODOLOGY: (1) Read task list, dependency order, and risk assessment, (2) Identify parallelizable task groups, (3) Define implementation sequence respecting dependencies, (4) Create rollback strategy for each phase, (5) Define risk mitigation checkpoints.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML execution sequence with parallel groups, L2 markdown strategy document with ordering rationale, L3 detailed rollback procedures.
user-invocable: true
disable-model-invocation: false
---

# Plan — Strategy

## Output

### L1
```yaml
domain: plan
skill: strategy
parallel_groups: 0
sequential_phases: 0
rollback_points: 0
```

### L2
- Execution sequence with parallel groups
- Risk mitigation checkpoints
- Rollback strategy per phase
