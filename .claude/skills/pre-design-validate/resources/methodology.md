# Pre-Design Validate — Detailed Methodology

> On-demand reference. Contains completeness scoring guide, gap report template, and iteration examples.

## Completeness Matrix Scoring Guide

**Scope**: PASS if ≥1 inclusion AND ≥1 exclusion statement. FAIL if only vague scope or missing exclusions. Edge: single-file TRIVIAL may have implicit exclusion.

**Constraints**: PASS if ≥1 technical OR resource limit stated. FAIL if no limits (every project has constraints). Common missing: context window, file count, time.

**Criteria**: PASS if ≥1 testable acceptance criterion. FAIL if only subjective ("make it better"). Test: Can analyst verify without asking user?

**Error Handling**: PASS if ≥1 error scenario with recovery. FAIL if no failure modes. TRIVIAL relaxation: "if fails, report error" is sufficient.

**Integration**: PASS if all external dependencies listed. FAIL if task mentions external components without listing them. "Integration: none" is valid PASS.

## Gap Report Template
```
Dimension: {name}
Status: FAIL
Missing: {what specific info is missing}
Impact: {what happens if we proceed without this}
Suggested Question: {what to ask user}
Priority: critical | recommended | nice-to-have
```

## Gap Priority Classification
| Priority | Definition | Action |
|----------|-----------|--------|
| Critical | Prevents any design | Must return to brainstorm |
| Recommended | May cause design issues | Return if within iteration budget |
| Nice-to-have | Supplementary | Document and proceed |

## DPS for Analysts
- **Context**: Full requirements doc from brainstorm L1/L2. 5-dimension matrix with PASS conditions. If re-validation: previous L1 showing failed dimensions.
- **Task**: "Evaluate each requirement against 5-dimension matrix. Per dimension: extract evidence, compare against PASS condition, report PASS/FAIL with evidence. For FAIL: actionable gap + suggested question."
- **Constraints**: Read-only. Sequential-thinking for nuanced reasoning. No invented requirements.
- **Delivery**: Lead reads directly (P0-P1).
- **STANDARD**: 1 analyst, maxTurns: 15.
- **COMPLEX**: 2 analysts: functional (scope+criteria) vs non-functional (constraints+errors+integration). maxTurns: 15 each.

## Iteration Example
| Iter | Checked | PASS | FAIL | Action |
|------|---------|------|------|--------|
| 1 | 5 | 3 | 2 (constraints, integration) | Return to brainstorm |
| 2 | 5 | 4 | 1 (integration) | Return or proceed? |
| 3 | 5 | 4 | 1 | Proceed with documented gap |

## Failure Protocols
**Missing brainstorm output**: Cannot validate. Route to Lead → re-invoke brainstorm.
**All 5 FAIL**: Return to brainstorm with ALL gaps. Lead uses deep exploration.
**Circular requirements**: Flag contradiction. Route to brainstorm for user priority resolution.
**Analyst disagrees with Lead**: Trust analyst (fresh perspective). Include both assessments.
**Analyst exhausted**: Partial validation. Report checked dimensions, flag unchecked as SKIP.
