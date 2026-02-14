---
name: orchestration-verify
description: |
  [P6a·Orchestration·Verify] Orchestration decision validator. Checks teammate-task assignments for correctness (right agent for right task), dependency chain acyclicity, and 4-teammate capacity limit enforcement before execution.

  WHEN: After orchestration-assign produces task-teammate matrix. Assignments exist but validity unconfirmed.
  DOMAIN: orchestration (skill 3 of 3). Terminal skill in orchestration domain.
  INPUT_FROM: orchestration-assign (task-teammate matrix with rationale).
  OUTPUT_TO: execution domain (validated assignments, PASS) or orchestration-assign (FAIL, re-assign needed).

  METHODOLOGY: (1) Read task-teammate matrix, (2) Verify each agent type matches task requirements (check WHEN conditions), (3) Run topological sort on dependency graph to detect cycles, (4) Confirm teammate count ≤ 4 per domain, (5) Check no file ownership conflicts (non-overlapping).
  CLOSED_LOOP: Verify → Find issues → Report to orchestration-assign → Re-assign → Re-verify (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML validation verdict per check, L2 ASCII validated dependency graph with PASS/FAIL markers.
user-invocable: true
disable-model-invocation: false
---

# Orchestration — Verify

## Output

### L1
```yaml
domain: orchestration
skill: verify
status: PASS|FAIL
checks:
  agent_match: PASS|FAIL
  acyclicity: PASS|FAIL
  teammate_limit: PASS|FAIL
  file_ownership: PASS|FAIL
```

### L2
- Per-check verdict with evidence
- Cycle detection results
- ASCII validated dependency graph
