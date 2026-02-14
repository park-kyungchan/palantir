---
name: plan-interface
description: |
  [P4·Plan·Interface] Interface specification and dependency ordering specialist. Defines precise interface contracts between implementation tasks and determines task completion order based on interface dependencies.

  WHEN: After plan-decomposition produces task breakdown. Tasks exist but inter-task interfaces undefined.
  DOMAIN: plan (skill 2 of 3). Sequential: decomposition → interface → strategy.
  INPUT_FROM: plan-decomposition (task list with file assignments), design-interface (API contracts from design phase).
  OUTPUT_TO: plan-strategy (interface constraints for sequencing), orchestration-assign (interface dependencies for teammate assignment).

  METHODOLOGY: (1) Read task breakdown and design interfaces, (2) For each task boundary: define precise input/output contract, (3) Map design interfaces to task-level interfaces, (4) Determine dependency ordering (which tasks must complete first), (5) Identify integration points requiring cross-task coordination.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML interface registry per task, L2 markdown dependency ordering with rationale, L3 detailed contract specifications.
user-invocable: true
disable-model-invocation: false
---

# Plan — Interface

## Output

### L1
```yaml
domain: plan
skill: interface
interface_count: 0
dependency_edges: 0
integration_points: 0
```

### L2
- Interface registry per task boundary
- Dependency ordering with rationale
- Integration points requiring coordination
