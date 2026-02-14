---
name: execution-infra
description: |
  [P7·Execution·Infra] Infrastructure file implementation executor. Spawns infra-implementer agents to modify .claude/ directory files (agent .md, skill SKILL.md, references, settings). Handles .claude/ infrastructure changes exclusively.

  WHEN: orchestration domain assigns infra-related tasks. Infrastructure changes needed alongside or independent of code changes.
  DOMAIN: execution (skill 2 of 3). Parallel-capable: code ∥ infra → review.
  INPUT_FROM: orchestration-verify (validated infra task assignments).
  OUTPUT_TO: execution-review (infra changes for review), verify domain (completed infra for verification).

  METHODOLOGY: (1) Read validated infra assignments, (2) Spawn infra-implementer agents per assignment, (3) Each infra-implementer: read target → apply changes → write output, (4) Monitor progress via L1/L2, (5) Consolidate infra change results.
  CONSTRAINT: Infra-implementers have Write but no Bash. Cannot delete files or run shell commands.
  TIER_BEHAVIOR: TRIVIAL=single infra-implementer, STANDARD/COMPLEX=1-2 infra-implementers.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML infra change manifest, L2 markdown change summary, L3 per-file change details.
user-invocable: true
disable-model-invocation: false
confirm: true
---

# Execution — Infra

## Output

### L1
```yaml
domain: execution
skill: infra
status: complete|in-progress|failed
files_changed: 0
implementers: 0
```

### L2
- Infra change manifest per implementer
- Configuration change summary
- Schema validation results
