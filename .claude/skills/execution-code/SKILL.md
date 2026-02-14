---
name: execution-code
description: |
  [P7·Execution·Code] Source code implementation executor. Spawns implementer agents to write application source code (Python, TypeScript, etc.) based on validated task-teammate assignments. Handles all non-.claude/ file changes.

  WHEN: orchestration domain complete (all 3 PASS). Validated assignments ready for code implementation. Domain entry point for execution.
  DOMAIN: execution (skill 1 of 3). Parallel-capable: code ∥ infra → review.
  INPUT_FROM: orchestration-verify (validated task-teammate matrix with PASS status).
  OUTPUT_TO: execution-review (implementation artifacts for review), verify domain (completed code for verification).

  METHODOLOGY: (1) Read validated assignments, (2) Spawn implementer agents per task-teammate matrix, (3) Each implementer: TaskGet PT → explain understanding → write code → report, (4) Monitor progress via L1/L2 reads, (5) Consolidate implementation results.
  TIER_BEHAVIOR: TRIVIAL=single implementer, STANDARD=1-2 implementers, COMPLEX=execution-coordinator+3.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML file change manifest, L2 markdown implementation summary, L3 per-file change details.
user-invocable: true
disable-model-invocation: true
confirm: true
---

# Execution — Code

## Output

### L1
```yaml
domain: execution
skill: code
status: complete|in-progress|failed
files_changed: 0
implementers: 0
tasks:
  - task_id: ""
    implementer: ""
    files: []
    status: complete|in-progress|failed
```

### L2
- Implementation summary per implementer
- File change manifest
- Issues encountered and resolutions
