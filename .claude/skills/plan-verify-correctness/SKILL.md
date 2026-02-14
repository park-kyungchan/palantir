---
name: plan-verify-correctness
description: |
  [P5·PlanVerify·Correctness] Logical correctness and specification compliance validator. Checks implementation plan correctly implements approved architecture, respects all constraints, and has no logical contradictions.

  WHEN: plan domain complete (all 3 skills done). Implementation plan ready for validation challenge.
  DOMAIN: plan-verify (skill 1 of 3). Parallel-capable: correctness ∥ completeness ∥ robustness.
  INPUT_FROM: plan-strategy (complete implementation plan), design-architecture (architecture to verify against).
  OUTPUT_TO: orchestration-decompose (if all plan-verify PASS) or plan domain (if FAIL, for revision).

  METHODOLOGY: (1) Read implementation plan and architecture spec, (2) Check each task implements correct architecture component, (3) Verify dependency chains match interface contracts, (4) Check for logical contradictions between tasks, (5) Verify constraint compliance (file limits, teammate limits).
  CLOSED_LOOP: Verify → Find issues → Report → Plan revision → Re-verify (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML correctness verdict per task, L2 markdown analysis with evidence, L3 detailed contradiction traces.
user-invocable: true
disable-model-invocation: false
---

# Plan Verify — Correctness

## Execution Model
- **TRIVIAL**: Lead-direct. Quick correctness scan.
- **STANDARD**: Spawn analyst. Systematic specification compliance check.
- **COMPLEX**: Spawn 2-4 analysts. Divide by architecture module.

## Methodology

### 1. Load Plan and Architecture
Read plan-strategy (complete implementation plan) and design-architecture (approved architecture).

### 2. Task-Architecture Mapping
For each implementation task, verify:
- Maps to exactly 1 architecture component
- Implements the correct responsibility (not a different component's job)
- Uses the correct interface contracts

### 3. Dependency Chain Verification
Compare plan dependency chains against interface contracts:
- Producer tasks produce what consumer tasks expect
- No missing intermediate tasks
- No dependency on non-existent task output

### 4. Contradiction Detection
Search for logical contradictions:
- Task A modifies file X, Task B also modifies file X (ownership conflict)
- Task A assumes data format Y, Task B produces format Z (type mismatch)
- Task A requires capability C, assigned agent lacks tool C (agent mismatch)

### 5. Constraint Compliance
Verify plan respects all constraints:
- Max 4 teammates per phase
- File ownership non-overlapping
- Tier classification matches actual task count

## Quality Gate
- Every task maps to correct architecture component
- Zero ownership conflicts
- Zero type mismatches between producer-consumer pairs
- All constraints satisfied

## Output

### L1
```yaml
domain: plan-verify
skill: correctness
status: PASS|FAIL
tasks_checked: 0
contradictions: 0
constraint_violations: 0
findings:
  - task: ""
    check: mapping|dependency|contradiction|constraint
    status: PASS|FAIL
    detail: ""
```

### L2
- Task-architecture mapping verification
- Contradiction report with evidence
- Constraint compliance matrix
