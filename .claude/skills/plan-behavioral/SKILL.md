---
name: plan-behavioral
description: >-
  Prescribes test and rollback strategy per predicted behavior
  change. Defines test cases P0-P3 and rollback triggers.
  Parallel with plan-static, plan-relational, and plan-impact.
  Use after research-coordinator complete. Reads from
  research-coordinator audit-behavioral L3 behavior predictions
  via $ARGUMENTS. Produces test and rollback inventory, and
  per-change test cases with rollback procedures for
  plan-verify-behavioral.
user-invocable: false
disable-model-invocation: false
allowed-tools: "Read Glob Grep Write"
metadata:
  category: plan
  tags: [test-strategy, rollback-planning, behavior-coverage]
  version: 2.0.0
---

# Plan — Behavioral Strategy

## Execution Model
- **TRIVIAL**: Lead-direct. 1-2 behavior changes with obvious test cases. Simple pass/fail rollback.
- **STANDARD**: Spawn analyst. Systematic test case generation across 3-8 predicted behavior changes.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep behavior chain analysis with cascading rollback design across 9+ changes.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Decision Points

### Risk Level Escalation
When predicted behavior changes show concentrated risk.
- **High-risk pipeline**: If > 3 P0 behavior changes predicted. Flag to Lead, recommend staged execution.
- **Moderate-risk**: If 1-3 P0 changes OR > 5 P1 changes. Standard rollback planning with checkpoints.
- **Low-risk**: If 0 P0 and ≤ 2 P1 changes. Lightweight strategy, minimal checkpoints.

### Rollback Strategy Selection
When choosing between rollback approaches for P0/P1 changes.
- **Atomic revert**: If changes within task are tightly coupled (shared state). Always for P0 risks.
- **Selective revert**: If changes are isolated within task (no shared state). P1 risks with clear boundaries.
- **Forward fix**: If change is additive and partial success is acceptable. P2-P3 only.

## Methodology

### 1. Read Audit-Behavioral L3 (Behavior Predictions)
Load the audit-behavioral L3 file path provided via `$ARGUMENTS`. This file contains:
- Predicted behavior changes per modified file/function
- Side effect analysis (what breaks when X changes)
- Behavior dependency chains (change A triggers behavior change B)

Validate the input exists and contains behavior predictions. If absent, route to Failure Handling (Missing Audit Input).

### 2. Define Test Cases Per Predicted Behavior Change
For each predicted behavior change from the audit:
- **Test subject**: Which function/module/endpoint behavior changes
- **Pre-condition**: Current behavior (IS state from audit)
- **Post-condition**: Expected new behavior (SHOULD state)
- **Test type**: Unit / integration / end-to-end (based on scope)
- **Verification method**: Assertion, output comparison, manual check

Test case granularity rules:
- One test case per discrete behavior change (not per file)
- If a single file change produces multiple behavior changes, create separate test cases
- Group related test cases into test suites aligned with task boundaries from plan-static

Priority classification:
| Priority | Criteria | Action if Fails |
|----------|----------|----------------|
| P0 (Critical) | Core business logic change | Block pipeline, immediate rollback |
| P1 (High) | Integration behavior change | Pause dependent tasks, assess |
| P2 (Normal) | Additive behavior (new feature) | Continue, fix in next iteration |
| P3 (Low) | Cosmetic/logging behavior change | Note and continue |

### 3. Design Rollback Triggers for Each Risk
For each behavior change with risk (P0 and P1 priority):
- **Trigger condition**: What observable failure activates rollback
- **Detection method**: How the failure is detected (test failure, runtime error, metric threshold)
- **Blast radius**: Which other components are affected if this change fails
- **Rollback scope**: Minimal set of changes to revert

Rollback strategy types:
- **Atomic revert**: Revert all files in the task. Simple but coarse.
- **Selective revert**: Revert only the failing change within a task. Fine-grained but requires isolated changes.
- **Forward fix**: Do not revert; instead apply a corrective change. Best for additive changes that partially succeed.

Selection heuristic:
- P0 risks: Always atomic revert (safety over efficiency)
- P1 risks: Selective revert if changes are isolated, atomic if coupled
- P2-P3 risks: Forward fix preferred (non-blocking)

### 4. Map Checkpoints to Task Dependency Chain
Align rollback checkpoints with the task structure from plan-static:
- Insert checkpoint AFTER each task that contains a P0 or P1 behavior change
- Checkpoint verifies: all test cases for that task pass before dependents proceed
- If a task has no P0/P1 changes, no checkpoint needed (flow-through)

Checkpoint protocol:
```
Checkpoint C-{N} (after Task T-{M}):
  Gate: All P0/P1 test cases for T-{M} pass
  On pass: Release dependent tasks
  On fail: Trigger rollback for T-{M}, pause dependents
  Timeout: 5 minutes (treat as fail if exceeded)
```

### 5. Output Test/Rollback Strategy
Produce the complete behavioral strategy:
- Test case inventory with priority classifications
- Rollback trigger definitions per risk
- Checkpoint placement mapped to task chain
- Coverage metrics: behavior changes covered / total predicted

**DPS -- Analyst Spawn Template (COMPLEX):**
- **Context**: Paste audit-behavioral L3 content (behavior predictions, side effects, dependency chains). Include pipeline tier, total predicted changes count, and task list from plan-static if available.
- **Task**: "For each predicted behavior change: define test case (subject, pre/post condition, type, priority P0-P3). For P0/P1 changes: define rollback trigger (condition, detection, blast radius, scope). Map checkpoints to task chain. Calculate coverage metrics."
- **Constraints**: analyst agent. Read-only (Glob/Grep/Read only). No file modifications. maxTurns: 20. Focus on prescriptive strategy, not test implementation.
- **Expected Output**: L1 YAML with test_count, rollback_count, checkpoint_count, coverage_percent, tests[] and rollbacks[]. L2 per-change test cases and rollback procedures.
- **Delivery**: Write full result to `/tmp/pipeline/p3-plan-behavioral.md`. Send micro-signal to Lead: `PASS|tests:{N}|rollbacks:{N}|ref:/tmp/pipeline/p3-plan-behavioral.md`.

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. 1-2 obvious behavior changes. Inline test specification, skip rollback if no P0/P1 changes.
**STANDARD**: Spawn analyst (maxTurns: 15). Systematic test cases for 3-8 changes. Rollback for P0/P1 only. Skip checkpoint mapping if ≤ 3 tasks.
**COMPLEX**: Full DPS above. Deep chain analysis, cascading rollback design, full checkpoint mapping across 9+ changes.

## Failure Handling
| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Missing audit-behavioral L3 input | CRITICAL | research-coordinator | Yes | Cannot define tests without behavior predictions. Request re-run. |
| No behavior changes predicted (empty audit) | LOW | Complete normally | No | Empty strategy is valid for static-only changes. `test_count: 0`. |
| Behavior chain too deep to analyze (>10 levels) | MEDIUM | Self (truncate) | No | Analyze top 10 levels, document truncation. `status: partial`. |
| Cannot determine rollback scope for coupled changes | HIGH | plan-static | No | Request task boundary clarification. Use atomic revert as fallback. |

## Anti-Patterns

### DO NOT: Invent Behavior Changes Not in Audit
This skill is prescriptive based on audit findings. If the audit did not predict a behavior change, do not speculate about it. Missing predictions are an upstream gap in audit-behavioral.

### DO NOT: Write Test Implementation Code
Define WHAT to test and HOW to verify, not the actual test code. Test implementation belongs in the execution phase. This skill produces test specifications, not test scripts.

### DO NOT: Skip Rollback Planning for P0/P1 Changes
Every P0 and P1 behavior change must have a defined rollback trigger. Proceeding without rollback for critical changes creates unrecoverable pipeline failures.

### DO NOT: Place Checkpoints After Every Task
Only tasks containing P0 or P1 behavior changes need checkpoints. Over-checkpointing adds synchronization overhead without proportional safety benefit.

### DO NOT: Assume All Behavior Changes Are Independent
Behavior dependency chains from the audit mean that rolling back change A may also require rolling back change B. Always check the chain before defining rollback scope.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-coordinator | audit-behavioral L3 file path | `$ARGUMENTS`: file path to L3 with behavior predictions |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-behavioral | Test/rollback strategy | Always (PASS or partial) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit input | research-coordinator | Which L3 file is missing |
| Coupled changes need task clarity | plan-static | Task boundaries needed for rollback scoping |

## Quality Gate
- Every predicted behavior change has at least one test case
- All P0/P1 changes have defined rollback triggers
- Checkpoints aligned with task boundaries
- No orphaned rollbacks (every rollback references a valid trigger)
- Coverage metric calculated: (changes with tests / total predicted changes) * 100

## Output

### L1
```yaml
domain: plan
skill: behavioral
status: complete|partial
test_count: 0
rollback_count: 0
checkpoint_count: 0
coverage_percent: 0
tests:
  - id: ""
    behavior_change: ""
    priority: P0|P1|P2|P3
    type: unit|integration|e2e
rollbacks:
  - id: ""
    trigger: ""
    scope: atomic|selective|forward-fix
    blast_radius: []
```

### L2
- Per-change test case specifications with pre/post conditions
- Rollback trigger definitions with detection methods
- Checkpoint placement map aligned to task chain
- Coverage metrics and gap analysis
