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

## Output

### L1
```yaml
domain: plan-verify
skill: correctness
status: PASS|FAIL
tasks_verified: 0
contradictions: 0
constraint_violations: 0
```

### L2
- Per-task correctness verdict with evidence
- Contradiction traces (if any)
- Constraint compliance summary
