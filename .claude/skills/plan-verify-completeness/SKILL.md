---
name: plan-verify-completeness
description: |
  [P5·PlanVerify·Completeness] Gap detection and missing element identifier. Checks implementation plan covers all requirements, all architecture components have corresponding tasks, and no scenarios are left unaddressed.

  WHEN: plan domain complete. Implementation plan ready for completeness challenge. Can run parallel with correctness and robustness.
  DOMAIN: plan-verify (skill 2 of 3). Parallel-capable: correctness ∥ completeness ∥ robustness.
  INPUT_FROM: plan-strategy (complete plan), pre-design-validate (original requirements for coverage check).
  OUTPUT_TO: orchestration-decompose (if PASS) or plan domain (if FAIL, for revision).

  METHODOLOGY: (1) Read plan and original requirements, (2) Build requirement-to-task traceability matrix, (3) Identify requirements without corresponding tasks, (4) Check all architecture components have implementation tasks, (5) Identify untested scenarios and missing error handling.
  CLOSED_LOOP: Verify → Find gaps → Report → Plan revision → Re-verify (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML traceability matrix with coverage percentage, L2 markdown gap report, L3 detailed requirement-task mapping.
user-invocable: true
disable-model-invocation: false
---

# Plan Verify — Completeness

## Output

### L1
```yaml
domain: plan-verify
skill: completeness
status: PASS|FAIL
coverage_pct: 0
gaps: 0
traceability:
  - requirement: ""
    task: ""
    status: covered|uncovered
```

### L2
- Requirement-to-task traceability matrix
- Uncovered requirements and scenarios
- Coverage percentage analysis
