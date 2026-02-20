---
name: validate-impact
description: >-
  Validates propagation risk of artifacts via
  phase-parameterized DPS. P4: confirms checkpoint
  containment against propagation chains — all HIGH paths
  must have intercepting checkpoints before terminal nodes.
  P7: checks execution scope vs original impact estimate —
  did implementation change more files or modules than
  planned? Verdict: PASS (P4 all HIGH contained; P7 scope
  within estimate), FAIL (P4 HIGH unmitigated or late
  checkpoint; P7 scope exceeds estimate significantly).
  Parallel with other validate-* axis skills. Use after
  plan domain complete (P4) or execution-review PASS (P7).
  Reads from plan-impact + audit-impact L3 (P4) or
  execution diff + original impact estimate (P7). Produces
  impact verdict for validate-coordinator. On FAIL, routes
  to plan-impact (P4) or execution-infra (P7). DPS needs
  PHASE_CONTEXT + upstream outputs. Exclude other axis
  results.
user-invocable: true
disable-model-invocation: true
---

# Validate — Impact

## Execution Model
- **TRIVIAL**: Lead-direct. P4: each path has intercepting checkpoint (no criteria validation). P7: count file delta inline.
- **STANDARD**: Spawn analyst (maxTurns:20). P4: full containment matrix with position + criteria validation. P7: systematic scope comparison.
- **COMPLEX**: Spawn analyst (maxTurns:30). P4: cascade simulation + circular path detection. P7: module-level scope analysis with drift pattern report.

## Phase Context

| Aspect | P4 (Plan Verify) | P7 (Verify) |
|--------|-----------------|-------------|
| Artifacts | plan-impact execution sequence + audit-impact L3 propagation paths | execution diff (git) + plan-impact output (original estimate) |
| Focus | Checkpoint containment — HIGH paths intercepted before terminal node | Scope analysis — actual changed files vs planned impact estimate |
| Gap Types | UNMITIGATED, LATE, INSUFFICIENT, CIRCULAR | SCOPE_CREEP (>20% more files), SCOPE_DRIFT (unplanned files) |
| PASS Threshold | All HIGH contained, zero UNMITIGATED | Scope ≤20% variance, no unplanned HIGH-impact files |
| On FAIL | Route to plan-impact | Route to execution-infra |
| Output File | `tasks/{work_dir}/p4-vi-impact.md` | `tasks/{work_dir}/p7-vi-impact.md` |

## Phase-Aware Execution
> See `.claude/resources/phase-aware-execution.md` for team routing rules.
- **Spawn**: `run_in_background:true`, `context:fork`. Agent writes to `tasks/{work_dir}/{PHASE}-vi-impact.md`.
- **Micro-signal P4**: `{VERDICT}|phase:P4|paths:{N}|unmitigated:{N}|ref:tasks/{work_dir}/p4-vi-impact.md`
- **Micro-signal P7**: `{VERDICT}|phase:P7|files_changed:{N}|drift:{N}|ref:tasks/{work_dir}/p7-vi-impact.md`

## Decision Points

### P4 — Containment Threshold
- **All HIGH CONTAINED + zero UNMITIGATED**: PASS.
- **All HIGH CONTAINED + UNMITIGATED are LOW-only (count ≤ 3)**: CONDITIONAL_PASS with risk annotation.
- **Any HIGH path UNMITIGATED or LATE**: FAIL → plan-impact.
- **> 50% paths lack containment**: Always FAIL (systematic checkpoint gap).
- **Propagation scale**: < 10 paths → STANDARD (maxTurns:20); 10–25 → COMPLEX (maxTurns:30); > 25 → sample MEDIUM/LOW, flag PARTIAL.

### P7 — Scope Analysis
- **Files changed ≤ 120% of estimate AND all changed files in original scope**: PASS.
- **Files changed 121–150% OR ≤ 3 unplanned non-HIGH-impact files**: CONDITIONAL_PASS with delta annotation.
- **Files changed > 150% of estimate OR any unplanned HIGH-impact file changed**: FAIL → execution-infra.
- **Zero propagation paths estimated**: PASS `scope_delta:0`.

## Methodology
> DPS template, containment matrix format, scope delta format, gap classification rubric: `resources/methodology.md`

### P4 Steps
1. **Read plan-impact sequence** — extract phases, checkpoints, rollback boundaries. Build checkpoint inventory.
2. **Read audit-impact L3 paths** — extract propagation paths, severity, depth, origin nodes. Build propagation inventory.
3. **Verify containment** — for each path: intercepting checkpoint exists, appears before terminal node, criteria match propagation type.
4. **Classify gaps** — UNMITIGATED / LATE / INSUFFICIENT / CIRCULAR. Circular paths require dual checkpoints and are always HIGH severity.
5. **Report verdict** — PASS/CONDITIONAL_PASS/FAIL with counts, severity breakdown, and gap evidence.

### P7 Steps
1. **Read original estimate** — load plan-impact output: planned file list, module boundaries, HIGH-impact node list.
2. **Read execution diff** — enumerate all files changed in P6 execution (git diff).
3. **Compare scope** — compute delta percentage; identify unplanned changes and their impact tier.
4. **Report verdict** — PASS/CONDITIONAL_PASS/FAIL with delta table (planned vs actual, unplanned file list with impact tier).

## Iteration Tracking (D15)
Lead manages `metadata.iterations.validate-impact: N`. Iteration 1: strict (FAIL returns upstream). Iteration 2: relaxed (proceed with flags). Max: 2.

## Failure Handling
> Escalation level definitions: `.claude/resources/failure-escalation-ladder.md`

| Failure Type | Level | Action |
|---|---|---|
| Upstream input missing (audit-impact L3 / plan-impact / git diff) | L0 Retry | Re-invoke; persist FAIL `reason: missing_upstream` |
| Containment matrix incomplete or paths unverified | L1 Nudge | Respawn with refined DPS targeting missing paths |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS |
| Propagation graph stale (P4) / git diff unavailable (P7) | L3 Restructure | Route to Lead for upstream re-run |
| Unresolvable gap or 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

**Special cases:** Zero propagation paths (P4) → PASS `paths:0`. Partial analyst output → `status:PARTIAL` to validate-coordinator.

## Anti-Patterns
- **DO NOT re-run execution or simulate propagation (P4)** — verify plan containment claims, not predicted outcomes.
- **DO NOT accept position-only validation (P4)** — checkpoint criteria must test for the specific propagation type.
- **DO NOT treat rollback boundaries as checkpoints** — rollback = recovery after propagation, not containment.
- **DO NOT expand scope (P7)** — compare planned vs actual only; do not re-audit propagation paths.
- **DO NOT propose fixes** — report gaps with evidence. plan-impact / execution-infra own remediation.

## Transitions
> Standard transition protocol: `.claude/resources/transitions-template.md`

### Receives From
| Source | Data Expected | Phase |
|--------|--------------|-------|
| plan-impact | Execution sequence: phases[], checkpoints[], rollback_boundaries[] | P4 |
| research-coordinator | audit-impact L3: paths[], origin, chain[], severity, depth | P4 |
| plan-impact (estimate) | Planned file list + module scope + HIGH-impact node list | P7 |
| execution diff | Actual changed file list from P6 (git diff) | P7 |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| validate-coordinator | Impact verdict with evidence | Always |
| plan-impact | Gap classification with path and checkpoint evidence | P4 FAIL |
| execution-infra | Scope delta table + unplanned change list | P7 FAIL |
| Lead | Which upstream missing | Missing upstream input |

## Quality Gate
> Standard quality gate protocol: `.claude/resources/quality-gate-checklist.md`

- **P4**: Every propagation path checked for containment; checkpoint position + criteria validated; all gaps classified (UNMITIGATED/LATE/INSUFFICIENT/CIRCULAR); circular paths detected.
- **P7**: Original estimate loaded; delta computed as percentage; all unplanned files enumerated with impact tier.
- Every finding cites specific path/file + checkpoint/estimate reference.
- Verdict (PASS/CONDITIONAL_PASS/FAIL) with explicit counts and threshold comparisons.

## Output

### L1
```yaml
domain: validate
skill: validate-impact
phase: P4|P7
# P4 fields:
total_paths: 0
contained_count: 0
unmitigated_count: 0
late_checkpoint_count: 0
# P7 fields:
files_estimated: 0
files_changed: 0
scope_delta_pct: 0
unplanned_high_impact: 0
# Common:
verdict: PASS|CONDITIONAL_PASS|FAIL
findings:
  - type: unmitigated|late|insufficient|circular|scope_creep|scope_drift
    path_or_file: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
pt_signal: "metadata.phase_signals.{phase}_validate_impact"
signal_format: "{VERDICT}|phase:{PHASE}|ref:tasks/{work_dir}/{PHASE}-vi-impact.md"
```

### L2
> See `.claude/resources/output-micro-signal-format.md` for micro-signal rules.
- **P4**: Containment matrix, gap analysis with severity, coverage statistics, verdict justification
- **P7**: Scope delta table (planned vs actual), unplanned change list with impact tier, verdict justification
