---
name: plan-verify-static
description: >-
  Verifies task coverage against dependency DAG for orphan files
  and missing edges. Verdict: PASS (≥95%, zero HIGH orphans),
  FAIL (<85% or HIGH gaps). Parallel with plan-verify-behavioral,
  plan-verify-relational, and plan-verify-impact. Use after
  plan-static complete. Reads from plan-static task breakdown
  with file assignments and research-coordinator audit-static L3
  dependency graph. Produces coverage verdict with metrics and
  coverage matrix with evidence for plan-verify-coordinator.
  On FAIL, routes back to plan-static with verified gap evidence.
  DPS needs plan-static output and research-coordinator
  audit-static L3. Exclude other verify dimension results.
user-invocable: true
disable-model-invocation: true
---

# Plan Verify — Static Coverage

## Execution Model
- **TRIVIAL**: Lead-direct. Inline count of plan files vs dependency files. If all present, PASS. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of task files against dependency graph nodes.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep node-by-node verification with edge coverage analysis across all modules.

Note: P4 validates PLANS (pre-execution). This skill verifies that the task decomposition structurally covers the dependency landscape. It does NOT verify implementation correctness.

## Phase-Aware Execution
- **Spawn**: Spawn agent (`run_in_background:true`, `context:fork`). Agent writes output to file.
- **Delivery**: Agent writes result to `tasks/{work_dir}/p4-pv-static.md`, micro-signal: `PASS|coverage:{pct}|orphans:{N}|ref:tasks/{work_dir}/p4-pv-static.md`.
- See `.claude/resources/phase-aware-execution.md` for full phase protocol.

## Decision Points

### Coverage Threshold Interpretation
Coverage percentage determines verdict routing.
- **≥ 95% with zero HIGH orphans**: PASS. Route to plan-verify-coordinator.
- **85–94% with only LOW/MEDIUM gaps**: CONDITIONAL_PASS. Route with risk annotation.
- **< 85% or any HIGH orphan/edge**: FAIL. Route failing dimension to plan-static for fix.
- **Borderline (84–86%)**: Include explicit evidence justifying the call.

**Orphan file definition**: A file in the dependency graph not assigned to any task. Severity HIGH if fan-in > 2; LOW otherwise.

### Dependency Graph Scale
Graph size determines spawn parameters.
- **< 20 nodes**: STANDARD analyst (maxTurns:20). Full node-by-node check feasible.
- **20–50 nodes**: COMPLEX analyst (maxTurns:30). Prioritize HIGH fan-in nodes first.
- **> 50 nodes**: COMPLEX analyst (maxTurns:30). Sample-based verification with full HIGH-node coverage. Flag PARTIAL if < 100% verified.

## Methodology
Full analyst DPS specification, per-step verification procedure (5 steps), coverage matrix format, and evidence template:
→ [resources/methodology.md](resources/methodology.md)

**Shared resources** (load on demand):
- `.claude/resources/phase-aware-execution.md`
- `.claude/resources/failure-escalation-ladder.md`
- `.claude/resources/dps-construction-guide.md`
- `.claude/resources/output-micro-signal-format.md`

## Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-verify-static: N` in PT before each invocation.
- Iteration 1: strict mode (FAIL → return to plan-static with gap evidence).
- Iteration 2: relaxed mode (proceed with risk flags, document gaps in phase_signals).
- Max iterations: 2.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Audit-static L3 missing, tool error, or timeout | L0 Retry | Re-invoke same agent, same DPS |
| Analyst output incomplete or coverage matrix partial | L1 Nudge | Respawn with refined DPS targeting refined context |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS |
| Audit-static data stale or plan-static scope changed | L3 Restructure | Modify task graph, reassign files |
| Strategic gap in dependency model, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

See `.claude/resources/failure-escalation-ladder.md` for D12 decision rules and output format.

**Special cases:**
- **Audit-static L3 missing**: FAIL with `reason: missing_upstream`. Route to Lead for re-routing to research-coordinator.
- **Dependency graph empty**: PASS with `coverage: 100, orphans: 0`. Single-file project, no structural verification needed.
- **Analyst exhausted turns**: Report partial coverage with percentage verified. Set `status: PARTIAL`. Route to plan-verify-coordinator with unverified node list.

## Anti-Patterns

### DO NOT: Verify Implementation Correctness
P4 verifies PLANS, not code. Check that the plan structurally covers the dependency graph. Do not assess whether the planned changes will correctly implement anything.

### DO NOT: Add Files to the Plan
If orphan files are found, REPORT them. Do not propose task modifications or new tasks. Fixing the plan is the plan domain's responsibility.

### DO NOT: Ignore Low-Fan-In Orphans
Even peripheral orphan files should be reported. They may indicate scope drift or intentional exclusion. Report all orphans, classify by severity, let the coordinator decide.

### DO NOT: Treat Config References as Hard Dependencies
Config file references (JSON path lookups, env var reads) are softer than import dependencies. Classify them as MEDIUM severity, not HIGH.

### DO NOT: Double-Count Partial Coverage
A file that is PARTIAL (some deps covered, some not) counts once toward coverage. Do not count it as both covered and uncovered.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-static | Task breakdown with file assignments | L1 YAML: tasks[] with id, files[], depends_on[]. L2: task descriptions |
| research-coordinator | Audit-static L3 dependency graph | L3: DAG with nodes, edges, hotspots, edge types |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-coordinator | Coverage verdict with evidence | Always (Wave 4 → Wave 4.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit-static L3 | Lead | Which upstream missing |
| Incomplete plan-static | plan-static | Tasks lacking file assignments |
| Analyst exhausted | plan-verify-coordinator | Partial coverage + unverified nodes |

## Quality Gate
- Every file in the dependency graph checked against the plan file set
- Coverage percentage calculated with clear numerator/denominator
- All orphan files listed with fan-in counts and severity classification
- All missing dependency edges listed with edge type and severity
- Every finding has file:line evidence from audit-static L3
- Verdict (PASS/FAIL) with explicit threshold comparison

## Output

### L1
```yaml
domain: plan-verify
skill: plan-verify-static
coverage_percent: 0
orphan_count: 0
missing_edge_count: 0
verdict: PASS|CONDITIONAL_PASS|FAIL
dependency_files_total: 0
plan_files_total: 0
findings:
  - type: orphan|missing_edge
    file: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
pt_signal: "metadata.phase_signals.p4_verify_static"
signal_format: "{STATUS}|coverage:{pct}|orphans:{N}|ref:tasks/{work_dir}/p4-pv-static.md"
```

### L2
- Coverage matrix: dependency file vs plan task mapping
- Orphan file list with fan-in/fan-out and severity
- Missing dependency edge list with edge type and severity
- Coverage percentage calculation with thresholds
- Verdict justification with evidence citations
