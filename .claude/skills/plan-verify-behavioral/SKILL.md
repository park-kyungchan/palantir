---
name: plan-verify-behavioral
description: >-
  Cross-checks test coverage against behavior predictions with
  risk-weighted scoring. Verdict: PASS (weighted ≥90%, rollback
  ≥90%), FAIL (HIGH untested or <75%). Parallel with
  plan-verify-static, plan-verify-relational, and
  plan-verify-impact. Use after plan-behavioral complete. Reads
  from plan-behavioral test/rollback strategy and
  research-coordinator audit-behavioral L3 behavior predictions.
  Produces test coverage verdict with weighted metrics and
  coverage matrices for plan-verify-coordinator.
  On FAIL, routes back to plan-behavioral with verified gap
  evidence. DPS needs plan-behavioral output and
  research-coordinator audit-behavioral L3. Exclude other verify
  dimension results.
user-invocable: true
disable-model-invocation: true
---

# Plan Verify — Behavioral Coverage

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check that each predicted change has a test entry. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of test cases against predicted behavior changes.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep verification of test adequacy per predicted change plus rollback trigger completeness analysis.

Note: P4 validates PLANS (pre-execution). This skill verifies that the test strategy adequately covers predicted behavior changes. It does NOT verify test implementation or execution results.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `tasks/{team}/p4-pv-behavioral.md`, sends micro-signal: `PASS|tested:{N}/{N}|rollbacks:{N}|ref:tasks/{team}/p4-pv-behavioral.md`.

→ See `.claude/resources/phase-aware-execution.md` for team spawn pattern detail.

## Decision Points

### Coverage Threshold Interpretation
Weighted test coverage determines verdict routing.
- **Weighted ≥ 90% AND rollback ≥ 90%**: PASS. Route to plan-verify-coordinator.
- **Weighted 75–89% with untested items LOW-risk only**: CONDITIONAL_PASS. Route with risk annotation.
- **Weighted < 75% or any HIGH-risk untested**: FAIL. Route to plan-behavioral for fix.
- **Default**: If any HIGH-risk change has neither test NOR rollback, always FAIL regardless of aggregate coverage.

### Prediction Set Scale
Prediction count determines spawn parameters.
- **< 10 predictions**: STANDARD analyst (maxTurns:20). Full prediction-by-prediction check.
- **10–30 predictions**: COMPLEX analyst (maxTurns:30). Prioritize HIGH-risk predictions first, then MEDIUM.
- **> 30 predictions**: COMPLEX analyst (maxTurns:30). Cover all HIGH-risk first, sample MEDIUM/LOW. Flag PARTIAL if < 100% verified.

## Methodology

Risk weights: **HIGH=3, MEDIUM=2, LOW=1**

Steps: (1) Build test inventory from plan-behavioral. (2) Build prediction inventory from audit-behavioral L3. (3) Cross-reference test coverage with assertion-type and scope matching. (4) Verify rollback trigger completeness for all HIGH-risk changes. (5) Report verdict with threshold comparison.

→ See `resources/methodology.md` for full analyst delegation DPS (INCLUDE/EXCLUDE lists, tier DPS), coverage matrix examples, rollback matrix examples, per-behavior scoring rubric, and edge case handling.

→ See `.claude/resources/dps-construction-guide.md` for DPS v5 template (WARNING/OBJECTIVE/CONTEXT/PLAN/MCP_DIRECTIVES/COMM_PROTOCOL/CRITERIA/OUTPUT/CONSTRAINTS).

## Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-verify-behavioral: N` in PT before each invocation.
- Iteration 1: strict mode — FAIL returns to plan-behavioral with gap evidence.
- Iteration 2: relaxed mode — proceed with risk flags, document gaps in phase_signals.
- Max iterations: 2. On exceed: proceed with documented gaps.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Audit-behavioral L3 missing, tool error, or timeout | L0 Retry | Re-invoke same agent, same DPS |
| Test coverage matrix incomplete or predictions unverified | L1 Nudge | SendMessage with refined context |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS |
| Prediction set scope changed or behavioral model stale | L3 Restructure | Modify task graph, reassign files |
| Strategic test coverage ambiguity, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

→ See `.claude/resources/failure-escalation-ladder.md` for full L0–L4 escalation protocol.

## Anti-Patterns

### DO NOT: Verify Test Implementation
P4 verifies PLANS, not code. Check that the test strategy covers predictions. Do not assess test code quality, assertion correctness, or framework usage.

### DO NOT: Accept Generic Rollback Triggers
"Rollback if something goes wrong" is not a specific trigger. Each HIGH-risk change needs a trigger condition describing what failure looks like for THAT specific change.

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
| plan-behavioral | Test strategy with rollback triggers | L1 YAML: tests[] with target, assertion, scope; rollbacks[] with trigger, action |
| research-coordinator | Audit-behavioral L3 behavior predictions | L3: predictions[] with change_type, affected_component, risk, confidence |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-coordinator | Test coverage verdict with evidence | Always (Wave 4 → Wave 4.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit-behavioral L3 | Lead | Which upstream missing |
| Incomplete plan-behavioral | plan-behavioral | Missing sections identified |
| Analyst exhausted | plan-verify-coordinator | Partial coverage + unverified predictions |

→ See `.claude/resources/transitions-template.md` for standard transition format.

## Quality Gate
- Every predicted behavior change checked against the test inventory
- Test coverage calculated with both raw and weighted (risk-proportional) metrics
- All untested HIGH-risk changes explicitly flagged with evidence
- Rollback trigger completeness verified for all HIGH-risk changes
- Every finding has evidence citing specific prediction IDs and test case IDs
- Verdict (PASS/FAIL) with explicit threshold comparison for both test and rollback coverage

→ See `.claude/resources/quality-gate-checklist.md` for standard quality gate protocol.

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
pt_signal: "metadata.phase_signals.p4_verify_behavioral"
signal_format: "{STATUS}|tested:{N}/{N}|rollbacks:{N}|ref:tasks/{team}/p4-pv-behavioral.md"
```

### L2
- Test coverage matrix: predicted change vs test case mapping
- Weighted coverage calculation with risk weights (HIGH=3, MEDIUM=2, LOW=1)
- Rollback coverage matrix for HIGH-risk changes
- Untested change list with risk levels and evidence
- Scope mismatch analysis (unit test on integration behavior)
- Verdict justification with threshold comparisons

→ See `.claude/resources/output-micro-signal-format.md` for micro-signal format spec.
