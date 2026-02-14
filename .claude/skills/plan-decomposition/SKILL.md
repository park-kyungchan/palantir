---
name: plan-decomposition
description: |
  [P4·Plan·Decomposition] Task breakdown and file assignment specialist. Decomposes approved architecture into implementable tasks with file ownership, dependency chains, and estimated complexity. Domain entry point for planning phase.

  WHEN: research domain complete. Architecture validated against codebase. Ready for implementation planning.
  DOMAIN: plan (skill 1 of 3). Sequential: decomposition → interface → strategy.
  INPUT_FROM: research-audit (consolidated findings), design-architecture (component structure).
  OUTPUT_TO: plan-interface (tasks needing interface specs), plan-strategy (tasks needing sequencing), orchestration-decompose (approved plan for task-teammate assignment).

  METHODOLOGY: (1) Read architecture and research findings, (2) Break components into implementable tasks (max 4 files per task), (3) Assign file ownership per task (non-overlapping), (4) Identify inter-task dependencies, (5) Estimate complexity per task (TRIVIAL/STANDARD/COMPLEX).
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=plan-writer agent, COMPLEX=planning-coordinator+3 workers.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML task list with file assignments and dependencies, L2 markdown task descriptions, L3 detailed file-level breakdown.
user-invocable: true
disable-model-invocation: true
---

# Plan — Decomposition

## Output

### L1
```yaml
domain: plan
skill: decomposition
task_count: 0
total_files: 0
tasks:
  - id: ""
    files: []
    complexity: trivial|standard|complex
    depends_on: []
```

### L2
- Task descriptions with file ownership
- Dependency chain visualization
- Complexity estimates per task
