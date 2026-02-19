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
  plan-verify-behavioral. On FAIL (untested HIGH behavior),
  routes back to plan-behavioral with additional predictions.
  DPS needs research-coordinator audit-behavioral L3 behavior
  predictions. Exclude static, relational, and impact dimension
  data.
user-invocable: false
disable-model-invocation: false
---

# Plan — Behavioral Strategy

## Execution Model
- **TRIVIAL**: Lead-direct. 1-2 behavior changes with obvious test cases. Simple pass/fail rollback.
- **STANDARD**: Spawn analyst. Systematic test case generation across 3-8 predicted behavior changes.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep behavior chain analysis with cascading rollback design across 9+ changes.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Four-Channel Protocol — Ch2 (disk file) + Ch3 (micro-signal to Lead) + Ch4 (P2P to downstream consumers). Lead receives status only, not full data.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **P2P Self-Coordination**: Read upstream outputs directly from `tasks/{team}/` files via $ARGUMENTS path. Send P2P signals to downstream consumers.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Decision Points

### Risk Level Escalation
When predicted behavior changes show concentrated risk.
- **High-risk pipeline**: > 3 P0 behavior changes predicted → flag to Lead, recommend staged execution.
- **Moderate-risk**: 1-3 P0 OR > 5 P1 changes → standard rollback planning with checkpoints.
- **Low-risk**: 0 P0 and ≤ 2 P1 changes → lightweight strategy, minimal checkpoints.

### Rollback Strategy Selection
When choosing between rollback approaches for P0/P1 changes.
- **Atomic revert**: Tightly coupled changes (shared state). Always for P0 risks.
- **Selective revert**: Isolated changes within task (no shared state). P1 risks with clear boundaries.
- **Forward fix**: Additive, partial success acceptable. P2-P3 only.

## Methodology

### 1. Read Audit-Behavioral L3 (Behavior Predictions)
Load the audit-behavioral L3 file path provided via `$ARGUMENTS`. Validate input contains:
- Predicted behavior changes per modified file/function
- Side effect analysis (what breaks when X changes)
- Behavior dependency chains (change A triggers behavior change B)

If absent, route to Failure Handling (Missing Audit Input).

### 2. Define Test Cases Per Predicted Behavior Change
For each predicted behavior change: define subject, pre-condition (IS state), post-condition (SHOULD state), test type (unit/integration/e2e), and verification method. Full format: `resources/methodology.md` → Per-Behavior Test Case Format.

Priority classification (P0-P3 table): `resources/methodology.md` → Priority Classification Table.
- P0 (Critical): block pipeline on fail; P1 (High): pause dependents; P2-P3: continue.
- **Untested-HIGH FAIL**: any P0/P1 change without a test case → quality gate fails.

One test case per discrete behavior change. Group into suites aligned with plan-static task boundaries.

### 3. Design Rollback Triggers for Each P0/P1 Risk
For each P0/P1 behavior change define:
- **Trigger condition**: observable failure that activates rollback
- **Detection method**: test failure, runtime error, or metric threshold
- **Blast radius**: which other components are affected
- **Rollback scope**: minimal set of changes to revert

Strategy selection heuristic: P0 → atomic revert; P1 → selective if isolated, atomic if coupled; P2-P3 → forward fix. Full strategy type table: `resources/methodology.md` → Rollback Strategy Types.

### 4. Map Checkpoints to Task Dependency Chain
Insert checkpoint after each task containing a P0 or P1 behavior change. Checkpoint verifies all P0/P1 test cases for that task pass before dependents proceed. Full checkpoint format: `resources/methodology.md` → Checkpoint Protocol Format.

If a task has no P0/P1 changes, no checkpoint (flow-through).

### 5. Output Test/Rollback Strategy
Produce complete behavioral strategy: test case inventory, rollback triggers, checkpoint placements, coverage metric (changes with tests / total predicted × 100).

**DPS — Analyst Spawn Template**: `resources/methodology.md` → DPS Templates.

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. 1-2 obvious changes. Inline test spec. Skip rollback if no P0/P1 changes.
**STANDARD**: Spawn analyst (maxTurns: 15). Test cases for 3-8 changes. Rollback for P0/P1 only. Skip checkpoint mapping if ≤ 3 tasks.
**COMPLEX**: Full DPS. Deep chain analysis, cascading rollback, full checkpoint mapping across 9+ changes.

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-behavioral: N` in PT before each invocation
- Iteration 1: strict mode (FAIL → return to research-coordinator with behavior prediction gaps)
- Iteration 2: relaxed mode (proceed with documented coverage gaps, flag in phase_signals)
- Max iterations: 2

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error or timeout during test case generation | L0 Retry | Re-invoke same agent, same DPS |
| Test/rollback strategy incomplete or missing P0/P1 coverage | L1 Nudge | SendMessage with refined behavior prediction scope |
| Agent stuck on chain analysis or context exhausted | L2 Respawn | Kill agent → fresh analyst with refined DPS |
| Task chain structure broken or rollback scoping requires plan-static clarification | L3 Restructure | Modify task graph, request boundary clarification |
| Strategic ambiguity on risk classification or 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Missing audit-behavioral L3 input | CRITICAL | research-coordinator | Yes | Cannot define tests without behavior predictions. Request re-run. |
| No behavior changes predicted (empty audit) | LOW | Complete normally | No | Empty strategy valid for static-only changes. `test_count: 0`. |
| Behavior chain too deep (>10 levels) | MEDIUM | Self (truncate) | No | Analyze top 10 levels, document truncation. `status: partial`. |
| Cannot determine rollback scope for coupled changes | HIGH | plan-static | No | Request task boundary clarification. Use atomic revert as fallback. |

## Anti-Patterns

1. **DO NOT invent behavior changes not in audit** — missing predictions are an upstream gap in audit-behavioral, not scope for speculation.
2. **DO NOT write test implementation code** — define WHAT to test and HOW to verify; actual test code belongs in execution phase.
3. **DO NOT skip rollback planning for P0/P1** — every HIGH change must have a defined rollback trigger or pipeline recovery is unrecoverable.
4. **DO NOT over-checkpoint** — only tasks with P0/P1 changes need checkpoints; over-checkpointing adds synchronization overhead without proportional safety benefit.

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
- Checkpoints aligned with task boundaries from plan-static
- No orphaned rollbacks (every rollback references a valid trigger)
- Coverage metric calculated: (changes with tests / total predicted) × 100

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
pt_signal: "metadata.phase_signals.p3_plan_behavioral"
signal_format: "{STATUS}|tests:{N}|rollbacks:{N}|ref:tasks/{team}/p3-plan-behavioral.md"
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
