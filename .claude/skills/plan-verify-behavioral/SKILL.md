---
name: plan-verify-behavioral
description: |
  [P3·PlanVerify·Behavioral] Cross-checks test coverage against behavior predictions with risk-weighted scoring. Verdict: PASS (weighted ≥90%, rollback ≥90%), FAIL (HIGH untested or <75%). Parallel with 3 other verify skills.

  WHEN: After plan-behavioral complete. Parallel with plan-verify-static/relational/impact.
  DOMAIN: plan-verify (skill 2 of 5).
  INPUT_FROM: plan-behavioral (test/rollback strategy), research-coordinator (audit-behavioral L3 behavior predictions).
  OUTPUT_TO: plan-verify-coordinator (test coverage verdict with weighted metrics, coverage matrices).

  METHODOLOGY: (1) Map test cases to behavior predictions, (2) Apply risk weights, (3) Calculate weighted coverage %, (4) Verify rollback coverage, (5) Flag HIGH-risk untested behaviors.
  OUTPUT_FORMAT: L1 YAML (test coverage verdict with weighted metrics), L2 test/rollback coverage matrices.
user-invocable: false
disable-model-invocation: false
---

# Plan Verify — Behavioral Coverage

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check that each predicted change has a test entry. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of test cases against predicted behavior changes.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep verification of test adequacy per predicted change plus rollback trigger completeness analysis.

Note: P4 validates PLANS (pre-execution). This skill verifies that the test strategy adequately covers predicted behavior changes. It does NOT verify test implementation or execution results.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p4-pv-behavioral.md`, sends micro-signal: `PASS|tested:{N}/{N}|rollbacks:{N}|ref:/tmp/pipeline/p4-pv-behavioral.md`.

## Decision Points

### Coverage Threshold Interpretation
Weighted test coverage determines verdict routing.
- **Weighted >= 90% AND rollback >= 90%**: PASS. Route to plan-verify-coordinator.
- **Weighted 75-89% with untested items LOW-risk only**: CONDITIONAL_PASS. Route with risk annotation.
- **Weighted < 75% or any HIGH-risk untested**: FAIL. Route to plan-behavioral for fix.
- **Default**: If any HIGH-risk change has neither test NOR rollback, always FAIL regardless of aggregate coverage.

### Prediction Set Scale
Prediction count determines spawn parameters.
- **< 10 predictions**: STANDARD analyst (maxTurns:20). Full prediction-by-prediction check.
- **10-30 predictions**: COMPLEX analyst (maxTurns:30). Prioritize HIGH-risk predictions first, then MEDIUM.
- **> 30 predictions**: COMPLEX analyst (maxTurns:30). Cover all HIGH-risk first, sample MEDIUM/LOW. Flag PARTIAL if < 100% verified.

## Methodology

### Analyst Delegation DPS
- **Context**: Paste plan-behavioral L1 test strategy (tests[], rollbacks[], risk classifications). Paste research-coordinator audit-behavioral L3 behavior predictions (predictions[], change types, risk levels).
- **Task**: "Cross-reference test inventory against prediction inventory. Verify assertion type match, scope match, and rollback trigger completeness for all HIGH-risk changes. Compute weighted coverage using risk weights HIGH=3, MEDIUM=2, LOW=1."
- **Constraints**: Analyst agent (Read-only, no Bash). maxTurns:20 (STANDARD) or 30 (COMPLEX). Verify only listed predictions.
- **Expected Output**: L1 YAML: test_coverage_percent, weighted_coverage_percent, rollback_coverage_percent, verdict, findings[]. L2: test/rollback coverage matrices.
- **Delivery**: SendMessage to Lead: `PASS|tested:{N}/{N}|rollbacks:{N}|ref:/tmp/pipeline/p4-pv-behavioral.md`

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. Verify each predicted change has a test entry inline. No rollback check needed.
**STANDARD**: Single analyst, maxTurns:20. Full test + rollback coverage matrices.
**COMPLEX**: Single analyst, maxTurns:30. Full matrices + scope mismatch analysis + over-testing observation.

### 1. Read Plan-Behavioral Test Strategy
Load plan-behavioral output to extract:
- Test cases: each test with its target behavior, assertion type, and scope
- Rollback triggers: conditions under which changes should be reverted
- Risk classifications: which behavior changes are tagged HIGH/MEDIUM/LOW risk
- Test coverage claims: what the plan says is tested

Build a **test inventory**: every planned test case with its target behavior ID.

### 2. Read Audit-Behavioral L3 Predictions
Load audit-behavioral L3 output from research-coordinator:
- Predicted behavior changes: each change with affected component, change type, and confidence
- Behavior change categories: functional, performance, error handling, integration
- Risk annotations: predicted severity of each behavior change

Build a **prediction inventory**: every predicted behavior change with its ID and risk level.

### 3. Cross-Reference Test Coverage
For each predicted behavior change, check:
- Is there at least one test case targeting this change?
- Does the test assertion match the change type (functional test for functional change, etc.)?
- Is the test scope appropriate (unit for isolated changes, integration for cross-component)?

Build a test coverage matrix:

| Predicted Change | Risk | Test Case(s) | Assertion Match? | Scope Match? | Status |
|-----------------|------|-------------|-----------------|-------------|--------|
| Auth token refresh | HIGH | T-01, T-02 | Yes | Yes (integration) | TESTED |
| Cache invalidation | HIGH | T-03 | Partial (wrong scope) | No (unit, needs integration) | PARTIAL |
| Log format change | LOW | -- | -- | -- | UNTESTED |

Test coverage = (TESTED changes) / (total predicted changes) * 100.
Weighted coverage = sum(tested_risk_weight) / sum(total_risk_weight) * 100, where HIGH=3, MEDIUM=2, LOW=1.

### 4. Verify Rollback Trigger Completeness
For each HIGH-risk predicted behavior change:
- Does a rollback trigger exist for this change?
- Is the trigger condition specific (not just "if test fails" but what failure looks like)?
- Is the rollback action defined (revert which files, restore which state)?

Build a rollback coverage matrix:

| HIGH-Risk Change | Rollback Trigger? | Trigger Specific? | Action Defined? | Status |
|-----------------|-------------------|-------------------|-----------------|--------|
| Auth token refresh | Yes | Yes (401 response) | Yes (revert auth.ts) | COVERED |
| Cache invalidation | Yes | No (generic "failure") | Partial | GAP |
| Data migration | No | -- | -- | MISSING |

Rollback coverage = (COVERED triggers) / (total HIGH-risk changes) * 100.

### 5. Report Test Coverage Verdict
Produce final verdict with evidence:

**PASS criteria**:
- Weighted test coverage >= 90%
- All HIGH-risk changes have at least one matching test
- Rollback coverage >= 90% for HIGH-risk changes

**Conditional PASS criteria**:
- Weighted test coverage >= 75% with untested items being LOW-risk only
- Rollback coverage >= 75% with gaps only on changes that have alternative mitigation

**FAIL criteria**:
- Weighted test coverage < 75%, OR
- Any HIGH-risk change completely untested, OR
- Rollback coverage < 75% for HIGH-risk changes, OR
- Any HIGH-risk change has neither test nor rollback trigger

## Failure Handling

### Audit-Behavioral L3 Not Available
- **Cause**: research-coordinator did not produce audit-behavioral L3 output.
- **Action**: FAIL with `reason: missing_upstream`. Cannot verify test coverage without behavior predictions.
- **Route**: Lead for re-routing to research-coordinator.

### Plan-Behavioral Output Incomplete
- **Cause**: plan-behavioral produced partial test strategy (missing test cases or rollback triggers).
- **Action**: FAIL with `reason: incomplete_plan`. Report which sections are missing.
- **Route**: plan-behavioral for completion.

### No Behavior Changes Predicted
- **Cause**: audit-behavioral predicted zero behavior changes (cosmetic-only change).
- **Action**: PASS with `tested: 0/0`, `rollbacks: 0`. No behavioral verification needed.
- **Route**: plan-verify-coordinator with trivial confirmation.

### Test-Prediction Mismatch (Tests Exist for Non-Predicted Changes)
- **Cause**: plan-behavioral includes tests for behaviors not in the prediction set.
- **Action**: Flag as informational finding (not a failure). Extra tests are conservative.
- **Route**: Include in L2 as over-testing observation. Does not affect verdict.

### Analyst Exhausted Turns
- **Cause**: Large prediction set exceeds analyst budget.
- **Action**: Report partial coverage with percentage of predictions verified. Set `status: PARTIAL`.
- **Route**: plan-verify-coordinator with partial flag and unverified prediction list.

## Anti-Patterns

### DO NOT: Verify Test Implementation
P4 verifies PLANS, not code. Check that the test strategy covers predictions. Do not assess test code quality, assertion correctness, or framework usage.

### DO NOT: Accept Generic Rollback Triggers
"Rollback if something goes wrong" is not a specific trigger. Each HIGH-risk change needs a trigger condition that describes what failure looks like for THAT specific change.

### DO NOT: Ignore Scope Mismatches
A unit test for an integration-level behavior change is a scope mismatch. Report it as PARTIAL even if a test technically exists.

### DO NOT: Treat All Untested Changes Equally
An untested LOW-risk change (log format) is categorically different from an untested HIGH-risk change (auth mechanism). Use weighted coverage to reflect risk-proportional importance.

### DO NOT: Create or Suggest Test Cases
If coverage gaps exist, REPORT them with evidence. Do not design new tests. Test strategy revision is the plan domain's responsibility.

### DO NOT: Discount Rollback Verification
Rollback completeness is as important as test coverage. A plan with 100% test coverage but 0% rollback coverage is brittle.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-behavioral | Test strategy with rollback triggers | L1 YAML: tests[] with target, assertion, scope. Rollbacks[] with trigger, action |
| research-coordinator | Audit-behavioral L3 behavior predictions | L3: predictions[] with change_type, affected_component, risk, confidence |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-coordinator | Test coverage verdict with evidence | Always (Wave 4 -> Wave 4.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit-behavioral L3 | Lead | Which upstream missing |
| Incomplete plan-behavioral | plan-behavioral | Missing sections identified |
| Analyst exhausted | plan-verify-coordinator | Partial coverage + unverified predictions |

## Quality Gate
- Every predicted behavior change checked against the test inventory
- Test coverage calculated with both raw and weighted (risk-proportional) metrics
- All untested HIGH-risk changes explicitly flagged with evidence
- Rollback trigger completeness verified for all HIGH-risk changes
- Every finding has evidence citing specific prediction IDs and test case IDs
- Verdict (PASS/FAIL) with explicit threshold comparison for both test and rollback coverage

## Output

### L1
```yaml
domain: plan-verify
skill: plan-verify-behavioral
test_coverage_percent: 0
weighted_coverage_percent: 0
rollback_coverage_percent: 0
tested_count: 0
total_predictions: 0
rollback_count: 0
verdict: PASS|CONDITIONAL_PASS|FAIL
findings:
  - type: untested_change|scope_mismatch|missing_rollback|weak_trigger
    prediction_id: ""
    risk: HIGH|MEDIUM|LOW
    evidence: ""
```

### L2
- Test coverage matrix: predicted change vs test case mapping
- Weighted coverage calculation with risk weights
- Rollback coverage matrix for HIGH-risk changes
- Untested change list with risk levels and evidence
- Scope mismatch analysis (unit test on integration behavior)
- Verdict justification with threshold comparisons
