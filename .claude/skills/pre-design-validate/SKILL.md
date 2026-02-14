---
name: pre-design-validate
description: |
  [P0-1·PreDesign·Validate] Requirement completeness checker. Validates gathered requirements cover all dimensions: functional scope, non-functional constraints, acceptance criteria, error handling, and integration points.

  WHEN: After pre-design-brainstorm completes. Requirements document exists but completeness unverified.
  DOMAIN: pre-design (skill 2 of 3). Sequential: brainstorm → validate → feasibility.
  INPUT_FROM: pre-design-brainstorm (structured requirements document).
  OUTPUT_TO: pre-design-feasibility (validated requirements) or pre-design-brainstorm (if gaps found, re-brainstorm).

  METHODOLOGY: (1) Read requirements from brainstorm output, (2) Check against completeness matrix (scope, constraints, criteria, errors, integration), (3) Identify gaps and missing dimensions, (4) If gaps: report to Lead for re-brainstorm, (5) If complete: pass to feasibility.
  CLOSED_LOOP: Validate → Find gaps → Re-brainstorm → Re-validate (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML completeness matrix with PASS/FAIL per dimension, L2 markdown gap analysis with missing items.
user-invocable: true
disable-model-invocation: false
---

# Pre-Design — Validate

## Output

### L1
```yaml
domain: pre-design
skill: validate
status: PASS|FAIL
completeness:
  scope: PASS|FAIL
  constraints: PASS|FAIL
  criteria: PASS|FAIL
  error_handling: PASS|FAIL
  integration: PASS|FAIL
gaps: 0
```

### L2
- Completeness matrix with per-dimension evidence
- Gap analysis for FAIL dimensions
- Iteration count and resolution status
