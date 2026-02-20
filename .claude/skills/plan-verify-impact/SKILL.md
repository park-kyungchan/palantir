---
name: plan-verify-impact
description: >-
  Confirms checkpoint containment against propagation chains.
  Verdict: PASS (all HIGH contained), FAIL (HIGH unmitigated
  or >3 gaps). Parallel with plan-verify-static,
  plan-verify-behavioral, and plan-verify-relational. Use after
  plan-impact complete. Reads from plan-impact execution
  sequence with checkpoints and research-coordinator audit-impact
  L3 propagation paths. Produces containment verdict and
  path-checkpoint mapping with gap classification for
  plan-verify-coordinator.
  On FAIL, routes back to plan-impact with verified gap
  evidence. DPS needs plan-impact output and
  research-coordinator audit-impact L3. Exclude other verify
  dimension results.
user-invocable: true
disable-model-invocation: true
---

# Plan Verify — Impact Containment

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check that each propagation path has an intercepting checkpoint. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of checkpoints against propagation paths.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep path-by-path containment analysis with cascade simulation across all propagation chains.

> P4 validates PLANS (pre-execution). This skill verifies that the execution sequence safely contains predicted change propagation — not execution results or actual impact.

## Phase-Aware Execution
> See `.claude/resources/phase-aware-execution.md` for team routing rules.
- **Spawn**: Spawn agent (`run_in_background:true`, `context:fork`). Agent writes output to file.
- **Delivery**: Write `tasks/{work_dir}/p4-pv-impact.md`. Micro-signal: `PASS|paths:{N}|unmitigated:{N}|ref:tasks/{work_dir}/p4-pv-impact.md`.

## Decision Points

### Containment Threshold
- **All HIGH CONTAINED + zero UNMITIGATED**: PASS → plan-verify-coordinator.
- **All HIGH CONTAINED + UNMITIGATED are LOW-only (count ≤ 3)**: CONDITIONAL_PASS → route with risk annotation.
- **Any HIGH path UNMITIGATED or LATE**: FAIL → plan-impact for fix.
- **> 50% paths lack containment**: Always FAIL (systematic checkpoint gap).

### Propagation Graph Scale
- **< 10 paths**: STANDARD analyst (maxTurns:20). Full path-by-path containment check.
- **10–25 paths**: COMPLEX analyst (maxTurns:30). Prioritize HIGH-severity and deep (depth ≥ 3) paths first.
- **> 25 paths**: COMPLEX analyst (maxTurns:30). Full HIGH check, sample MEDIUM/LOW. Flag PARTIAL if < 100% verified.

## Methodology
> DPS template, containment matrix format, and gap classification rubric: `resources/methodology.md`
> DPS v5 field structure: `.claude/resources/dps-construction-guide.md`

### 1. Read Plan-Impact Execution Sequence
Load plan-impact output and extract: execution phases (ordered task groups), checkpoints (verification gates with pass criteria and containment claims), rollback boundaries.
Build a **checkpoint inventory**: every checkpoint with its position in the sequence and containment scope.

### 2. Read Audit-Impact L3 Propagation Paths
Load research-coordinator audit-impact L3 output and extract: propagation paths (chains of files/components), path severity (HIGH/MEDIUM/LOW), cascade depth, origin nodes.
Build a **propagation inventory**: every path as an ordered chain with severity and depth.

### 3. Verify Checkpoint Containment
For each propagation path: confirm an intercepting checkpoint exists, checkpoint appears BEFORE the terminal node, and checkpoint criteria detect the specific propagation type.
Build a containment matrix (format and status definitions: `resources/methodology.md`).

### 4. Identify Gaps
Classify all uncontained paths as UNMITIGATED, LATE, or INSUFFICIENT.
Detect circular propagation cycles — these require dual checkpoints and are always HIGH severity.
Full gap classification rubric and record format: `resources/methodology.md`.

### 5. Report Containment Verdict

**PASS**: All HIGH-severity paths CONTAINED + zero UNMITIGATED paths + late/insufficient total ≤ 2 (MEDIUM only).

**CONDITIONAL_PASS**: All HIGH-severity paths CONTAINED + UNMITIGATED paths are LOW-severity only + total unmitigated ≤ 3.

**FAIL** (any one condition):
- Any HIGH-severity path UNMITIGATED
- Any HIGH-severity path has LATE checkpoint
- Total unmitigated count > 3 (any severity)
- > 50% of paths lack containment

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-verify-impact: N` in PT before each invocation.
- Iteration 1: strict mode — FAIL returns to plan-impact with gap evidence.
- Iteration 2: relaxed mode — proceed with risk flags, document gaps in phase_signals.
- Max iterations: 2.

## Failure Handling
> Escalation level definitions: `.claude/resources/failure-escalation-ladder.md`

| Failure Type | Level | Action |
|---|---|---|
| Audit-impact L3 missing, tool error, timeout | L0 Retry | Re-invoke same agent, same DPS |
| Containment matrix incomplete or paths unverified | L1 Nudge | Respawn with refined DPS targeting refined context |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS |
| Propagation graph stale or circular path detected | L3 Restructure | Modify task graph, reassign files |
| Unresolvable containment gap, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

**Special cases:**
- **Audit-impact L3 missing**: FAIL `reason: missing_upstream` → Lead re-routes to research-coordinator.
- **Plan-impact checkpoints absent**: FAIL `reason: incomplete_plan` → report phases lacking checkpoints → route to plan-impact.
- **Zero propagation paths**: PASS `paths:0, unmitigated:0` → route to plan-verify-coordinator with trivial confirmation.
- **Analyst exhausted turns**: Report partial analysis with % verified, set `status: PARTIAL` → plan-verify-coordinator with partial flag.

## Anti-Patterns

- **DO NOT verify execution results.** P4 verifies PLANS. Check that checkpoints are positioned and specified — do not simulate execution or predict actual checkpoint effectiveness.
- **DO NOT accept position-only validation.** A checkpoint at the right position is necessary but not sufficient. Verify criteria actually test for the specific propagation type.
- **DO NOT ignore LOW-severity unmitigated paths.** Report all unmitigated paths; accumulated low-severity gaps indicate a weak containment strategy.
- **DO NOT treat rollback boundaries as checkpoints.** Rollback = recovery after propagation. Containment = prevention or detection BEFORE propagation completes.
- **DO NOT propose new checkpoints.** Report gaps with evidence only. Checkpoint creation is plan-impact's responsibility.

## Transitions
> Standard transition protocol: `.claude/resources/transitions-template.md`

### Receives From
| Source | Data Expected |
|--------|--------------|
| plan-impact | L1 YAML: phases[], checkpoints[], rollback_boundaries[]. L2: containment claims per path |
| research-coordinator | L3: paths[] with origin, chain[], severity, depth |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| plan-verify-coordinator | Containment verdict with evidence | Always (Wave 4 → Wave 4.5) |
| plan-impact | Phases lacking checkpoints | Incomplete plan-impact |
| Lead | Which upstream missing | Missing audit-impact L3 |

## Quality Gate
> Standard quality gate protocol: `.claude/resources/quality-gate-checklist.md`

- Every propagation path from audit-impact checked for checkpoint coverage
- Checkpoint position validated (appears BEFORE path terminal node)
- Checkpoint criteria validated (tests for specific propagation type)
- All gaps classified by type (UNMITIGATED/LATE/INSUFFICIENT) and severity
- Circular propagation paths detected and flagged
- Every finding has evidence citing specific paths and checkpoint IDs
- Verdict (PASS/CONDITIONAL_PASS/FAIL) with explicit counts and severity thresholds

## Output

### L1
```yaml
domain: plan-verify
skill: plan-verify-impact
total_paths: 0
contained_count: 0
partial_count: 0
unmitigated_count: 0
late_checkpoint_count: 0
verdict: PASS|CONDITIONAL_PASS|FAIL
findings:
  - type: unmitigated|late|insufficient|circular
    path: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
pt_signal: "metadata.phase_signals.p4_verify_impact"
signal_format: "{STATUS}|paths:{N}|unmitigated:{N}|ref:tasks/{work_dir}/p4-pv-impact.md"
```

### L2
> See `.claude/resources/output-micro-signal-format.md` for micro-signal formatting rules.
- Containment matrix: propagation path vs checkpoint mapping
- Unmitigated path analysis with severity and cascade depth
- Late checkpoint analysis with recommended repositioning
- Insufficient criteria analysis with specificity gaps
- Circular propagation report (if any)
- Coverage statistics: contained/partial/unmitigated counts
- Verdict justification with threshold comparisons
