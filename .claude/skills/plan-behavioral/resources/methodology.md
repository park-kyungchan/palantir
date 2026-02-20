# Plan-Behavioral: Extended Methodology Reference

## Priority Classification Table

| Priority | Criteria | Action if Fails |
|----------|----------|----------------|
| P0 (Critical) | Core business logic change | Block pipeline, immediate rollback |
| P1 (High) | Integration behavior change | Pause dependent tasks, assess |
| P2 (Normal) | Additive behavior (new feature) | Continue, fix in next iteration |
| P3 (Low) | Cosmetic/logging behavior change | Note and continue |

**HIGH behavior definition**: Any predicted behavior change classified P0 or P1.
**Untested-HIGH FAIL condition**: If any P0 or P1 behavior change has no test case, the quality gate fails and routes back to plan-behavioral.

## Per-Behavior Test Case Format

For each predicted behavior change, define one test case:

```
Test case fields:
  id:               T-{N} (unique identifier)
  behavior_change:  Which function/endpoint behavior changes
  pre_condition:    Current behavior (IS state from audit)
  post_condition:   Expected new behavior (SHOULD state)
  type:             unit | integration | e2e
  priority:         P0 | P1 | P2 | P3
  verification:     assertion | output-comparison | manual-check
```

Granularity rules:
- One test case per discrete behavior change (not per file)
- Single file producing multiple behavior changes → create separate test cases
- Group related test cases into suites aligned with task boundaries from plan-static

## Rollback Strategy Types

| Strategy | When to Use | Risk Level |
|----------|-------------|------------|
| Atomic revert | Tightly coupled changes (shared state) | Always P0 |
| Selective revert | Isolated changes within task (no shared state) | P1 with clear boundaries |
| Forward fix | Additive change, partial success acceptable | P2-P3 only |

## Checkpoint Protocol Format

```
Checkpoint C-{N} (after Task T-{M}):
  Gate: All P0/P1 test cases for T-{M} pass
  On pass: Release dependent tasks
  On fail: Trigger rollback for T-{M}, pause dependents
  Timeout: 5 minutes (treat as fail if exceeded)
```

Placement rule: Insert checkpoint AFTER each task containing a P0 or P1 behavior change.
If a task has no P0/P1 changes, no checkpoint needed (flow-through).

## DPS Templates

### COMPLEX — Full Analyst Spawn Template

```
Context (D11 priority: cognitive focus > token efficiency):
  INCLUDE:
    - research-coordinator audit-behavioral L3 from tasks/{work_dir}/p2-coordinator-audit-behavioral.md
    - Pipeline tier and iteration count from PT
    - Task list from plan-static if available (for checkpoint alignment)
  EXCLUDE:
    - Other plan dimension outputs (unless direct dependency for checkpoint mapping)
    - Full research evidence detail (use L3 summaries only)
    - Pre-design and design conversation history
  Budget: Context field ≤ 30% of subagent effective context

Task: For each predicted behavior change: define test case (subject, pre/post condition,
      type, priority P0-P3). For P0/P1 changes: define rollback trigger (condition,
      detection, blast radius, scope). Map checkpoints to task chain.
      Calculate coverage metrics.

Constraints: analyst agent. Read-only (Glob/Grep/Read only). No file modifications.
             maxTurns: 20. Focus on prescriptive strategy, not test implementation.

Expected Output: L1 YAML with test_count, rollback_count, checkpoint_count,
                 coverage_percent, tests[] and rollbacks[].
                 L2 per-change test cases and rollback procedures.

Delivery (Two-Channel):
  Ch2: Write full result to tasks/{work_dir}/p3-plan-behavioral.md
  Ch3: Micro-signal to Lead: PASS|tests:{N}|rollbacks:{N}|ref:tasks/{work_dir}/p3-plan-behavioral.md
  Ch4: P2P to plan-verify-behavioral (Deferred Spawn — Lead spawns after all 4 plan dimensions complete)
```

### STANDARD — Simplified Analyst Spawn

Spawn analyst (maxTurns: 15). Systematic test cases for 3-8 changes. Rollback for P0/P1 only.
Skip checkpoint mapping if ≤ 3 tasks.

### TRIVIAL — Lead-Direct

1-2 obvious behavior changes. Inline test specification. Skip rollback if no P0/P1 changes.
