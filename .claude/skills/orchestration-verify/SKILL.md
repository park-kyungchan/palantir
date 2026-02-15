---
name: orchestration-verify
description: |
  [P6·Orchestration·Verify] Orchestration decision validator. Checks assignments for correctness (right agent for right task), dependency acyclicity, and 4-teammate capacity enforcement before execution.

  WHEN: After orchestration-assign produces task-teammate matrix. Assignments exist but validity unconfirmed.
  DOMAIN: orchestration (skill 3 of 3). Terminal skill in orchestration domain.
  INPUT_FROM: orchestration-assign (task-teammate matrix with rationale).
  OUTPUT_TO: execution domain (validated assignments, PASS) or orchestration-assign (FAIL, re-assign).

  METHODOLOGY: (1) Read task-teammate matrix, (2) Verify each agent type matches task requirements via WHEN conditions, (3) Topological sort on dependency graph to detect cycles, (4) Confirm teammate count <=4 per domain, (5) Check no file ownership conflicts (non-overlapping).
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

For COMPLEX tier, construct the delegation prompt for the analyst with:
- **Context**: Paste orchestration-assign L1 (task-teammate matrix with assignments). Include Agent profile reference: analyst=B(Read,Glob,Grep,Write), researcher=C(+WebSearch,WebFetch,context7,tavily), implementer=D(+Edit,Bash), infra-implementer=E(+Edit,Write for .claude/).
- **Task**: "For each assignment: verify agent WHEN condition matches task type, verify agent has required tools for the task. Check dependency acyclicity (approximate reasoning for small graphs, systematic for large). Confirm <=4 teammate instances per execution phase. Verify non-overlapping file ownership."
- **Constraints**: Read-only. No modifications. For topological sort: use systematic reasoning, not algorithmic execution. Acknowledge this is approximate for large graphs.
- **Expected Output**: L1 YAML with checks (agent_match, acyclicity, capacity, ownership) each PASS/FAIL. L2 verification details.

### 3. Check Dependency Acyclicity
Run topological sort on dependency graph:
- If sort succeeds -> acyclic (PASS)
- If sort fails -> cycle detected (FAIL, report cycle)

**Note**: For TRIVIAL/STANDARD (Lead-direct), Lead performs approximate cycle detection via reasoning — suitable for small dependency graphs (≤8 tasks). For COMPLEX tier, the spawned analyst performs systematic cycle detection using exhaustive path tracing.

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
