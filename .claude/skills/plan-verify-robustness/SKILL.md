---
name: plan-verify-robustness
description: |
  [P5·PlanVerify·Robustness] Edge case and failure mode challenger. Tests implementation plan against edge cases, failure scenarios, security implications, and resource constraints to ensure robustness under adverse conditions.

  WHEN: plan domain complete. Implementation plan ready for robustness challenge. Can run parallel with correctness and completeness.
  DOMAIN: plan-verify (skill 3 of 3). Parallel-capable: correctness ∥ completeness ∥ robustness.
  INPUT_FROM: plan-strategy (complete plan), design-risk (risk assessment for focused challenge).
  OUTPUT_TO: orchestration-decompose (if PASS) or plan domain (if FAIL, for revision).

  METHODOLOGY: (1) Read plan and risk assessment, (2) Generate edge case scenarios per task, (3) Simulate failure modes (what if task X fails?), (4) Check security implications of implementation approach, (5) Verify resource constraints (4-teammate limit, file count limits).
  CLOSED_LOOP: Challenge → Find weaknesses → Report → Plan revision → Re-challenge (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML robustness verdict with edge case list, L2 markdown challenge report, L3 detailed failure scenario analysis.
user-invocable: true
disable-model-invocation: false
---

# Plan Verify — Robustness

## Output

### L1
```yaml
domain: plan-verify
skill: robustness
status: PASS|FAIL
edge_cases: 0
failure_modes: 0
weaknesses: 0
```

### L2
- Edge case scenarios per task
- Failure mode analysis
- Security and resource constraint review
