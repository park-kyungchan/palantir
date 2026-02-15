---
name: pre-design-validate
description: |
  [P0·PreDesign·Validate] Requirement completeness checker. Validates requirements cover all dimensions: functional scope, non-functional constraints, acceptance criteria, error handling, and integration points.

  WHEN: After pre-design-brainstorm completes. Requirements document exists but completeness unverified.
  DOMAIN: pre-design (skill 2 of 3). Sequential: brainstorm -> validate -> feasibility.
  INPUT_FROM: pre-design-brainstorm (structured requirements document).
  OUTPUT_TO: pre-design-feasibility (validated requirements) or pre-design-brainstorm (if gaps found).

  METHODOLOGY: (1) Read requirements from brainstorm output, (2) Check against completeness matrix (scope, constraints, criteria, errors, integration), (3) Identify gaps and missing dimensions, (4) If gaps: report to Lead for re-brainstorm, (5) If complete: pass to feasibility. Max 3 iterations.
  OUTPUT_FORMAT: L1 YAML completeness matrix with PASS/FAIL per dimension, L2 markdown gap analysis with missing items.
user-invocable: true
disable-model-invocation: false
---

# Pre-Design — Validate

## Execution Model
- **TRIVIAL**: Lead-direct. Quick completeness check against 5-dimension matrix.
- **STANDARD**: Launch analyst (run_in_background). Systematic dimension-by-dimension validation.
- **COMPLEX**: Launch 2 background agents (run_in_background). Split: functional (scope+criteria) vs non-functional (constraints+errors+integration).

## Methodology

### 1. Read Brainstorm Output
Load requirement document from pre-design-brainstorm output.
Identify which dimensions were covered during brainstorm.

### 2. Check Completeness Matrix

| Dimension | Check | PASS Condition |
|-----------|-------|---------------|
| Scope | Feature boundaries defined | ≥1 inclusion AND ≥1 exclusion statement |
| Constraints | Limits identified | Technical OR resource limits stated |
| Criteria | Success measurable | ≥1 testable acceptance criterion |
| Error Handling | Failure modes considered | ≥1 error scenario with recovery |
| Integration | Touchpoints mapped | All external dependencies listed |

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: Paste the full requirements document from pre-design-brainstorm L1/L2 output. Include the 5-dimension completeness matrix with PASS conditions from Step 2. If re-validation, include previous L1 showing which dimensions failed.
- **Task**: "Evaluate each requirement against the 5-dimension completeness matrix. For each dimension: extract evidence from requirements, compare against PASS condition, report PASS or FAIL with evidence. For FAIL dimensions: actionable gap description with suggested clarifying questions."
- **Constraints**: Read-only analysis. No file modifications. Use sequential-thinking for nuanced gap reasoning. Do not invent requirements.
- **Expected Output**: L1 YAML completeness matrix with status per dimension and gaps count. L2 markdown per-dimension evidence and gap descriptions.

### 3. Identify Gaps
For each FAIL dimension:
- State what's missing
- Explain why it matters
- Suggest specific questions to resolve

### 4. Report or Iterate
- If all PASS → forward to pre-design-feasibility
- If any FAIL → report gaps to Lead for re-brainstorm
- Max 3 iterations before proceeding with documented gaps

## Quality Gate
- Completeness matrix has explicit PASS/FAIL per dimension
- Every FAIL has actionable gap description
- No dimension left unchecked

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
