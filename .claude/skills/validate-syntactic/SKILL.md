---
name: validate-syntactic
description: >-
  Validates structural well-formedness of artifacts via
  phase-parameterized DPS. P4: task coverage against dependency
  DAG — orphan files and missing edges. P7: file structure,
  metadata fields, naming conventions, section completeness.
  Verdict: PASS (P4 ≥95% zero HIGH orphans; P7 all files
  structurally sound), FAIL (P4 <85% or HIGH gaps; P7 YAML
  parse failures or missing required fields). Parallel with
  validate-semantic, validate-behavioral, validate-consumer,
  validate-relational, validate-impact. Use after plan domain
  complete (P4) or execution-review PASS (P7). Reads from
  plan-static + audit-static L3 (P4) or execution artifacts
  (P7). Produces structural verdict for validate-coordinator.
  On FAIL, routes to plan-static (P4) or execution-infra (P7).
  DPS needs PHASE_CONTEXT block + upstream outputs. Exclude
  other axis results.
user-invocable: true
disable-model-invocation: true
---

# Validate — Syntactic

## Execution Model
- **TRIVIAL**: Lead-direct. Inline count of plan files vs dependency files (P4) or spot-check 1-3 files (P7). No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of task files against DAG (P4) or structural+content audit of 4-15 files (P7).
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep node-by-node DAG verification (P4) or full structural audit of 16+ files (P7).

Note: P4 validates PLANS (pre-execution). P7 validates IMPLEMENTATION artifacts (post-execution). Phase context is set by DPS PHASE_CONTEXT block.

## Phase Context

| Phase | Artifacts In | Focus | Pass Threshold | Fail Route | Output File |
|-------|-------------|-------|----------------|------------|-------------|
| P4 | plan-static task breakdown + audit-static L3 DAG | Task coverage of dependency graph; orphan files and missing edges | ≥95% + zero HIGH orphans | plan-static | `{work_dir}/p4-validate-syntactic.md` |
| P7 | execution artifacts post execution-review PASS | YAML validity, required fields, naming conventions, section completeness | Both structure+content ≥50, avg util >80% | execution-infra | `{work_dir}/p7-validate-syntactic.md` |

## Phase-Aware Execution
- **Spawn**: Spawn analyst (`run_in_background:true`, `context:fork`). Agent writes output to phase-specific file per Phase Context table.
- **Delivery**: Micro-signal: `{VERDICT}|phase:{P4|P7}|ref:tasks/{work_dir}/{phase}-validate-syntactic.md`.
- See `.claude/resources/phase-aware-execution.md` for full phase protocol.

## Decision Points

### P4 — Coverage Thresholds
- **≥95% + zero HIGH orphans**: PASS. Route to validate-coordinator.
- **85–94% + only LOW/MEDIUM gaps**: CONDITIONAL_PASS. Route with risk annotation.
- **<85% or any HIGH orphan/edge**: FAIL. Route to plan-static with gap evidence.
- **Orphan definition**: A dependency graph node not assigned to any task. HIGH if fan-in > 2; LOW otherwise. Config references = MEDIUM max.

### P7 — Scoring Thresholds
- **Both structure + content scores ≥50 AND avg utilization >80%**: PASS. Route to validate-coordinator.
- **Either score <50 or YAML parse failure**: FAIL (blocking). Route to execution-infra with file:line evidence.
- **Utilization 70–80% with all 5 orchestration keys present**: WARN (non-blocking).

### Scale → Spawn Parameters
- **<20 nodes (P4) / <15 files (P7)**: STANDARD analyst (maxTurns:20). Full node-by-node or file-by-file check.
- **20–50 nodes / 16+ files**: COMPLEX analyst (maxTurns:30). Prioritize HIGH fan-in nodes or most-referenced files first.
- **>50 nodes**: COMPLEX (maxTurns:30). Sample-based with full HIGH-node coverage. Flag PARTIAL if <100% verified.

## Methodology

### P4 Steps
1. **Task Inventory** — Build list of all tasks and their assigned files from plan-static output.
2. **Dep Inventory** — Extract all nodes and edges from audit-static L3 dependency DAG.
3. **Cross-Reference** — Map each dependency node to covering task(s). Flag unmapped nodes as orphan candidates.
4. **Classify Orphans** — Score by fan-in: HIGH if fan-in > 2, MEDIUM if fan-in = 2, LOW if fan-in ≤ 1. Config references = MEDIUM max.
5. **Report** — Coverage %, orphan count by severity, missing edge list, verdict vs threshold comparison.

### P7 Steps
1. **Inventory** — Glob target artifacts; compare counts against DPS-declared totals.
2. **Structural Checks** — Per-file: YAML heuristic parseability, required fields present, naming conventions, directory compliance.
3. **Content Checks** — Per-file: description utilization %, orchestration keys (WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY), body section headings.
4. **Combined Scoring** — Structure score (0-100) + content score (0-100). Calculate avg utilization across all files.
5. **Report** — Per-file scores with PASS/FAIL/WARN; overall verdict; FAIL routes execution-infra with file:line evidence.

→ Full DPS templates, coverage matrix format, structural check algorithms: `resources/methodology.md`

**Shared resources** (load on demand):
- `.claude/resources/phase-aware-execution.md`
- `.claude/resources/failure-escalation-ladder.md`
- `.claude/resources/dps-construction-guide.md`
- `.claude/resources/output-micro-signal-format.md`

## Iteration Tracking (D15)
- Lead manages `metadata.iterations.validate-syntactic: N` in PT before each invocation.
- **P4**: Iteration 1 strict (FAIL → return to plan-static with gap evidence). Iteration 2 relaxed (proceed with risk flags). Max 2.
- **P7**: 1 iteration. FAIL routes directly to execution-infra — no plan to iterate against.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Upstream missing (audit-static L3 or execution artifacts) | L0 Retry | Re-invoke same agent, same DPS; report missing upstream to Lead |
| Output incomplete or coverage matrix partial | L1 Nudge | Respawn with refined DPS targeting remaining scope |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS, reduced scope |
| Data stale or plan-static scope changed mid-pipeline | L3 Restructure | Modify task graph or re-run upstream phase |
| Strategic gap, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

**Special cases**: Dependency graph empty (P4) → PASS `coverage:100, orphans:0`. Analyst PARTIAL → report partial coverage with unverified node list, status: PARTIAL.

See `.claude/resources/failure-escalation-ladder.md` for D12 decision rules.

## Anti-Patterns

- **DO NOT verify implementation correctness (P4)** — Check structural coverage of the plan, not whether planned changes will work.
- **DO NOT add files to the plan** — If orphans found, REPORT them. Plan domain (plan-static) is responsible for fixing.
- **DO NOT treat config references as hard dependencies (P4)** — Config lookups are MEDIUM severity max, not HIGH.
- **DO NOT attempt programmatic YAML parsing (P7)** — Analysts have no YAML parser tool. Use heuristic checks only.
- **DO NOT penalize short but complete descriptions (P7)** — 750 chars with all 5 orchestration keys beats 1000 chars missing WHEN.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|---|---|---|
| plan-static (P4) | Task breakdown with file assignments | L1 YAML: tasks[] with id, files[], depends_on[] |
| research-coordinator (P4) | Audit-static L3 dependency graph | L3: DAG with nodes, edges, hotspots, edge types |
| execution-review (P7) | PASS verdict + implementation artifact paths | L1 YAML: status:PASS, changed file paths list |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| validate-coordinator | Structural verdict with coverage/score evidence | Always (parallel axis result for N→1 synthesis) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|---|---|---|
| Orphan files or coverage <85% (P4) | plan-static | Gap evidence: orphan list, fan-in counts, missing edges |
| YAML/structural/field failures (P7) | execution-infra | file path, error type, line location, suggested fix |
| Missing upstream data | Lead | Which upstream phase output is missing |

## Quality Gate
- P4: Every dependency graph node checked; coverage % calculated with clear numerator/denominator; all orphans listed with fan-in + severity
- P7: Every file inventoried vs DPS-declared counts; per-file structure + content scores with PASS/FAIL/WARN
- All findings have file:line evidence from upstream L3 data (P4) or Glob/Read inspection (P7)
- Verdict with explicit threshold comparison and phase clearly stated
- FAIL output includes routing target, data type, and remediation hint

## Output

### L1
```yaml
domain: validate
skill: validate-syntactic
phase: P4|P7
verdict: PASS|CONDITIONAL_PASS|FAIL
pt_signal: "metadata.phase_signals.{phase}_validate_syntactic"
# P4 fields
coverage_percent: 0
orphan_count: 0
missing_edge_count: 0
dependency_files_total: 0
plan_files_total: 0
# P7 fields
total_files: 0
structure_pass: 0
content_pass: 0
avg_utilization_pct: 0
# shared
findings:
  - type: orphan|missing_edge|yaml_fail|missing_field|naming_violation
    file: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
signal_format: "{VERDICT}|phase:{PHASE}|ref:tasks/{work_dir}/{phase}-validate-syntactic.md"
```

### L2
- P4: Coverage matrix (dependency node vs task mapping), orphan list with fan-in/severity, missing edge list, verdict justification with threshold comparison
- P7: Per-file structure + content scores, utilization rankings, structural issues with file:line evidence, overall verdict with routing recommendation
