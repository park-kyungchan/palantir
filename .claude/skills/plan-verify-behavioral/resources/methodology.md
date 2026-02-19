# Plan Verify Behavioral — Analyst Methodology

Detailed execution methodology for the analyst spawned by `plan-verify-behavioral`.
Referenced from SKILL.md to keep L2 body within 200-line budget.

---

## Analyst Delegation DPS

### Context Construction (D11: cognitive focus > token efficiency)

**INCLUDE:**
- plan-behavioral L1 test strategy: `tests[]` with target behavior, assertion type, scope; `rollbacks[]` with trigger condition, action; risk classifications (HIGH/MEDIUM/LOW)
- research-coordinator audit-behavioral L3: `predictions[]` with change_type, affected_component, risk, confidence
- File paths within this agent's ownership boundary

**EXCLUDE:**
- Other verify dimension results (static/relational/impact)
- Historical rationale for plan-behavioral decisions
- Full pipeline state beyond P3-P4
- Rejected test strategy alternatives

**Budget:** DPS Context field ≤ 30% of teammate effective context.

### Task Specification

> "Cross-reference test inventory against prediction inventory. Verify assertion type match, scope match, and rollback trigger completeness for all HIGH-risk changes. Compute weighted coverage using risk weights HIGH=3, MEDIUM=2, LOW=1."

**Constraints:** Analyst agent (Read-only, no Bash). maxTurns:20 (STANDARD) or 30 (COMPLEX). Verify only listed predictions.

**Expected Output:**
- L1 YAML: `test_coverage_percent`, `weighted_coverage_percent`, `rollback_coverage_percent`, `verdict`, `findings[]`
- L2: test/rollback coverage matrices
- Delivery: `SendMessage` to Lead: `PASS|tested:{N}/{N}|rollbacks:{N}|ref:tasks/{team}/p4-pv-behavioral.md`

### Tier-Specific DPS Variations

**TRIVIAL:** Lead-direct. Verify each predicted change has a test entry inline. No rollback check needed.

**STANDARD:** Single analyst, maxTurns:20. Full test + rollback coverage matrices.

**COMPLEX:** Single analyst, maxTurns:30. Full matrices + scope mismatch analysis + over-testing observation.

---

## Step 1 — Read Plan-Behavioral Test Strategy

Load plan-behavioral output to extract:
- Test cases: each test with its target behavior, assertion type, and scope
- Rollback triggers: conditions under which changes should be reverted
- Risk classifications: which behavior changes are tagged HIGH/MEDIUM/LOW risk
- Test coverage claims: what the plan says is tested

Build a **test inventory**: every planned test case with its target behavior ID.

---

## Step 2 — Read Audit-Behavioral L3 Predictions

Load audit-behavioral L3 output from research-coordinator:
- Predicted behavior changes: each change with affected component, change type, and confidence
- Behavior change categories: functional, performance, error handling, integration
- Risk annotations: predicted severity of each behavior change

Build a **prediction inventory**: every predicted behavior change with its ID and risk level.

---

## Step 3 — Cross-Reference Test Coverage

For each predicted behavior change, check:
- Is there at least one test case targeting this change?
- Does the test assertion match the change type (functional test for functional change, etc.)?
- Is the test scope appropriate (unit for isolated changes, integration for cross-component)?

Build a **test coverage matrix:**

| Predicted Change | Risk | Test Case(s) | Assertion Match? | Scope Match? | Status |
|-----------------|------|-------------|-----------------|-------------|--------|
| Auth token refresh | HIGH | T-01, T-02 | Yes | Yes (integration) | TESTED |
| Cache invalidation | HIGH | T-03 | Partial (wrong scope) | No (unit, needs integration) | PARTIAL |
| Log format change | LOW | -- | -- | -- | UNTESTED |

**Formulas:**
- Test coverage = (TESTED changes) / (total predicted changes) × 100
- Weighted coverage = sum(tested_risk_weight) / sum(total_risk_weight) × 100, where HIGH=3, MEDIUM=2, LOW=1

---

## Step 4 — Verify Rollback Trigger Completeness

For each HIGH-risk predicted behavior change:
- Does a rollback trigger exist for this change?
- Is the trigger condition specific (not just "if test fails" but what failure looks like)?
- Is the rollback action defined (revert which files, restore which state)?

Build a **rollback coverage matrix:**

| HIGH-Risk Change | Rollback Trigger? | Trigger Specific? | Action Defined? | Status |
|-----------------|-------------------|-------------------|-----------------|--------|
| Auth token refresh | Yes | Yes (401 response) | Yes (revert auth.ts) | COVERED |
| Cache invalidation | Yes | No (generic "failure") | Partial | GAP |
| Data migration | No | -- | -- | MISSING |

**Formula:** Rollback coverage = (COVERED triggers) / (total HIGH-risk changes) × 100

---

## Step 5 — Report Test Coverage Verdict

**PASS criteria:**
- Weighted test coverage ≥ 90%
- All HIGH-risk changes have at least one matching test
- Rollback coverage ≥ 90% for HIGH-risk changes

**Conditional PASS criteria:**
- Weighted test coverage ≥ 75% with untested items being LOW-risk only
- Rollback coverage ≥ 75% with gaps only on changes that have alternative mitigation

**FAIL criteria:**
- Weighted test coverage < 75%, OR
- Any HIGH-risk change completely untested, OR
- Rollback coverage < 75% for HIGH-risk changes, OR
- Any HIGH-risk change has neither test nor rollback trigger

---

## Edge Cases

### Audit-Behavioral L3 Not Available
- **Cause:** research-coordinator did not produce audit-behavioral L3 output.
- **Action:** FAIL with `reason: missing_upstream`. Cannot verify test coverage without behavior predictions.
- **Route:** Lead for re-routing to research-coordinator.

### Plan-Behavioral Output Incomplete
- **Cause:** plan-behavioral produced partial test strategy (missing test cases or rollback triggers).
- **Action:** FAIL with `reason: incomplete_plan`. Report which sections are missing.
- **Route:** plan-behavioral for completion.

### No Behavior Changes Predicted
- **Cause:** audit-behavioral predicted zero behavior changes (cosmetic-only change).
- **Action:** PASS with `tested: 0/0`, `rollbacks: 0`. No behavioral verification needed.
- **Route:** plan-verify-coordinator with trivial confirmation.

### Test-Prediction Mismatch (Tests Exist for Non-Predicted Changes)
- **Cause:** plan-behavioral includes tests for behaviors not in the prediction set.
- **Action:** Flag as informational finding (not a failure). Extra tests are conservative.
- **Route:** Include in L2 as over-testing observation. Does not affect verdict.

### Analyst Exhausted Turns
- **Cause:** Large prediction set exceeds analyst budget.
- **Action:** Report partial coverage with percentage of predictions verified. Set `status: PARTIAL`.
- **Route:** plan-verify-coordinator with partial flag and unverified prediction list.
