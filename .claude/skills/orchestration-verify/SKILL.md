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

## Execution Model
- **TRIVIAL**: Lead-direct. Quick sanity check.
- **STANDARD**: Lead-direct. Systematic verification of assignments.
- **COMPLEX**: Spawn analyst for independent verification of complex assignment.

## Methodology

### 1. Read Assignment Matrix
Load orchestration-assign output (task-teammate assignments).

### 2. Verify Agent-Task Match
For each assignment, check:
- Agent WHEN condition matches task requirements
- Agent has required tools for the task (Edit for code changes, Bash for testing)
- Agent profile (B/C/D/E) is appropriate for task type

### 3. Check Dependency Acyclicity
Run topological sort on dependency graph:
- If sort succeeds -> acyclic (PASS)
- If sort fails -> cycle detected (FAIL, report cycle)

### 4. Validate Capacity
Per execution phase:
- Teammate count <= 4
- No single agent overloaded (>4 files per instance)
- Context budget feasible (estimate tokens per task)

### 5. Check File Ownership
Verify non-overlapping file ownership:
- No file appears in multiple agent assignments
- All files from plan appear in assignments (nothing dropped)
- .claude/ files assigned to infra-implementer, not implementer

## Quality Gate
- All agent-task matches verified correct
- Dependency graph is acyclic
- Capacity within limits
- File ownership non-overlapping and complete

## Output

### L1
```yaml
domain: orchestration
skill: verify
status: PASS|FAIL
checks:
  agent_match: PASS|FAIL
  acyclicity: PASS|FAIL
  capacity: PASS|FAIL
  ownership: PASS|FAIL
issues: 0
```

### L2
- Verification results per check category
- Issues found with evidence
- Validated dependency graph (ASCII)
