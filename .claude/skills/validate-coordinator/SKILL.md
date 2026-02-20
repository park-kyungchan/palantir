---
name: validate-coordinator
description: >-
  Consolidates six axis verdicts with cross-axis consistency
  checks into unified phase verdict. Terminal validate skill
  that merges parallel validate-* results into a single
  PASS/FAIL routing decision. Phase-parameterized: P4 routes
  PASS to orchestration domain, FAIL back to plan-*; P7
  routes PASS to delivery-pipeline, FAIL back to execution-*.
  Use after all six validate-* axis skills complete. Reads
  from validate-syntactic, validate-semantic,
  validate-behavioral, validate-consumer,
  validate-relational, and validate-impact verdicts.
  Produces L1 index and L2 summary for Lead, L3 per-axis
  files for downstream reference. On FAIL, includes specific
  error locations and owning skill per phase. DPS needs all
  six axis outputs + optional LEAD_OVERRIDES. Exclude raw
  execution artifacts and individual file-level detail.
user-invocable: true
disable-model-invocation: true
---

# Validate — Coordinator (6-Axis Synthesis)

## Execution Model
- **TRIVIAL**: Lead-direct. ≤3 axes with simple PASS. Inline merge, skip cross-checks. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:25). Systematic 6-axis merge + all 4 cross-axis checks. Tiered output.
- **COMPLEX**: Spawn analyst (maxTurns:35). Deep cross-axis analysis with compound pattern detection and comprehensive L3 production.

## Phase Context

| Aspect | P4 (Plan Verify) | P7 (Verify) |
|--------|-----------------|-------------|
| Input | Six validate-* verdicts from plan verification | Six validate-* verdicts from execution verification |
| PASS routing | Orchestration domain (P5) | delivery-pipeline (P8) |
| FAIL routing | Specific plan-* skill owning finding | execution-infra / execution-review / Lead |
| delivery_blocker | N/A | true if behavioral FAIL or HIGH cross-axis issue |
| Output prefix | `p4-vc-` | `p7-vc-` |

Note: This coordinator merges axis verdicts and checks BETWEEN axes for inconsistencies invisible to individual validators. It does NOT re-verify axes or override individual axis verdicts.

## Phase-Aware Execution
> See `.claude/resources/phase-aware-execution.md` for team routing rules.
- **Spawn**: `run_in_background:true`, `context:fork`. Delivers via Two-Channel Protocol.
- **Ch2**: `tasks/{work_dir}/{PHASE}-vc-index.md`, `{PHASE}-vc-summary.md`, and per-axis L3 files.
- **Ch3** micro-signal: `{VERDICT}|phase:{PHASE}|axes:6|issues:{N}|ref:tasks/{work_dir}/{PHASE}-vc-index.md`
- Lead uses Deferred Spawn to route downstream skills with `$ARGUMENTS` pointing to L3 files.

## Methodology

### Coordinator Synthesis Steps

1. **Collect axis outputs**: Read all 6 validate-* axis L1 YAML files from `tasks/{work_dir}/{PHASE}-validate-*.md`. If any axis is missing, mark as PARTIAL.
2. **Extract verdicts**: Parse `verdict:` field from each axis output. Build 6-axis verdict vector.
3. **Compute overall verdict**: Apply Overall Verdict Computation rules (see Decision Points). Any FAIL → overall FAIL. All PASS → overall PASS. Mixed → CONDITIONAL_PASS.
4. **Run cross-axis consistency checks**: Execute the 4 cross-axis checks (Syntactic↔Semantic, Behavioral↔Relational, Consumer↔Impact, Traceability). Each check produces severity (HIGH/MEDIUM/LOW).
5. **Check for Lead overrides**: If LEAD_OVERRIDES present in DPS, apply D-Decision rules to upgrade/downgrade individual axis verdicts.
6. **Determine routing**: Based on phase (P4/P7), route per Sends To tables. FAIL → owning failure route. PASS → next domain.
7. **Generate outputs**: Write L1 index (overall + per-axis), L2 summary (cross-axis narrative), L3 per-axis files (axis findings + cross-axis annotations).

## Decision Points

### Overall Verdict Computation
- **All 6 PASS (or CONDITIONAL_PASS) + cross-axis issues = 0**: PASS. Route per phase.
- **All 6 PASS + cross-axis issues exist (MEDIUM severity)**: CONDITIONAL_PASS with annotations.
- **Any axis FAIL OR cross-axis HIGH severity**: FAIL. Route to owning skill per finding.
- **P7 behavioral axis FAIL**: Always FAIL + `delivery_blocker: true` regardless of other axes.

### Partial Axis Handling
- **1 axis missing**: Partial output (5 axes), `status: PARTIAL`. Route to Lead.
- **2+ axes missing**: FAIL `reason: insufficient_data`. Cannot perform meaningful cross-checks.
- **Coverage < 70% any axis**: Route that axis for re-verification with focused scope.

### Lead D-Decision Overrides
DPS may include `LEAD_OVERRIDES` block. Protocol: (1) Read the failing axis output file. (2) Verify override condition matches actual failure mode — do NOT apply blindly. (3) Match → reclassify as CONDITIONAL_PASS with documented rationale in L2. (4) No match → FAIL stands; report to Lead that override condition did not apply.

### Cross-Axis Consistency Checks
Individual validators check their own axis. This coordinator checks BETWEEN axes:
1. **Syntactic-Semantic**: P4: orphan files on predicted behavioral paths? P7: structure scores vs quality scores misalignment?
2. **Behavioral-Relational**: P4: behavioral predictions cover cross-boundary interactions? P7: CC feasibility gaps align with reference consistency issues?
3. **Consumer-Impact**: P4: consumer contract fields cover full propagation scope? P7: output contracts match scope drift?
4. **Traceability**: Both phases: any finding covered by fewer than 3 axes → flag as under-verified.

Cross-axis issues create NEW findings; they do NOT change existing axis verdicts.

> Full cross-axis matrices, examples, and DPS templates: `resources/methodology.md`

## Failure Handling

| Failure Type | Action | Route |
|-------------|--------|-------|
| 1 axis missing | Partial output (5 axes), `status: PARTIAL` | Lead for re-routing |
| 2+ axes missing | FAIL `reason: insufficient_data` | Lead |
| P7 behavioral FAIL | Overall FAIL, `delivery_blocker: true` | Lead (blocks P8) |
| Cross-axis HIGH severity | Overall FAIL | Owning skill per finding |
| Cross-axis MEDIUM severity | CONDITIONAL_PASS | Route with annotations |
| All axes FAIL | FAIL, prioritize behavioral/syntactic first | Plan domain (P4) or execution domain (P7) |
| Conflicting axis assumptions | FAIL — internally inconsistent | Lead for arbitration |

> D12 escalation ladder: `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns
- **DO NOT override individual axis verdicts** — cross-axis issues create NEW findings; they do not change existing verdicts. EXCEPTION: Lead LEAD_OVERRIDES block after condition verification.
- **DO NOT re-verify axes** — check BETWEEN axes only; axis-specific analysis belongs to the individual validate-* skills.
- **DO NOT skip cross-checks when all axes PASS** — cross-axis inconsistencies can exist even when all pass.
- **DO NOT route all failures to a single skill** — each finding maps to its owning plan-* (P4) or execution-* (P7) skill.
- **DO NOT bloat L1 index** — L1 must stay ≤30 lines. Move detail to L2 or L3.
- **DO NOT treat partial input as complete** — if an axis sent PARTIAL status, reflect it in all output.

## Transitions
> Standard transition protocol: `.claude/resources/transitions-template.md`

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| validate-syntactic | Syntactic verdict | L1 YAML: verdict, finding counts. L2: per-file breakdown |
| validate-semantic | Semantic verdict | L1 YAML: verdict, prediction coverage. L2: semantic matrix |
| validate-behavioral | Behavioral verdict | L1 YAML: verdict, test coverage, CC-feasibility. L2: test matrix |
| validate-consumer | Consumer verdict | L1 YAML: verdict, contract counts. L2: consumer matrix |
| validate-relational | Relational verdict | L1 YAML: verdict, integrity counts. L2: consistency matrix |
| validate-impact | Impact verdict | L1 YAML: verdict, path/scope counts. L2: containment/delta |

### Sends To (P4)
| Target | Data | Trigger |
|--------|------|---------|
| Orchestration domain | L1 index + L2 summary | All axes PASS or CONDITIONAL_PASS |
| plan-syntactic / plan-semantic | L3 syntactic/semantic findings | validate-syntactic or validate-semantic FAIL |
| plan-behavioral | L3 behavioral findings | validate-behavioral FAIL |
| plan-relational / plan-impact | L3 relational/impact findings | validate-relational or validate-impact FAIL |

### Sends To (P7)
| Target | Data | Trigger |
|--------|------|---------|
| delivery-pipeline | L1 index + L2 summary | All axes PASS or CONDITIONAL_PASS |
| execution-infra | L3 syntactic/relational/impact findings | Structural or scope failures |
| execution-review | L3 semantic/consumer/quality findings | Semantic or consumer failures |
| Lead | L3 behavioral (CC feasibility) findings | Behavioral FAIL (delivery blocker) |

## Quality Gate
> Standard quality gate protocol: `.claude/resources/quality-gate-checklist.md`

- All 6 axis verdicts read and summarized
- All 4 cross-axis checks performed (syntactic-semantic, behavioral-relational, consumer-impact, traceability)
- Cross-axis findings classified by severity with evidence
- Tiered output produced: L1 index, L2 summary, L3 per-axis files (6 files)
- `delivery_blocker: true` set if P7 behavioral FAIL or any HIGH cross-axis issue (P7)
- Overall verdict = AND of 6 axes plus cross-axis severity
- Routing decision explicit: PASS target or FAIL target per finding

## Output

### L1
```yaml
domain: validate
skill: validate-coordinator
phase: P4|P7
overall_verdict: PASS|CONDITIONAL_PASS|FAIL
axes:
  syntactic: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  semantic: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  behavioral: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  consumer: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  relational: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  impact: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
cross_axis_issues: 0
under_verified_findings: 0
delivery_blocker: false
routing: orchestration|delivery-pipeline|plan-*|execution-*|Lead
output_ref: tasks/{work_dir}/{PHASE}-vc-index.md
pt_signal: "metadata.phase_signals.{phase}_validate"
signal_format: "{VERDICT}|phase:{PHASE}|axes:6|issues:{N}|ref:tasks/{work_dir}/{PHASE}-vc-index.md"
```

### L2
- Per-axis verdict summary with key metrics
- Cross-axis consistency matrix (4 checks with severity and evidence)
- Under-verified findings (traceability check results)
- Routing decision with rationale per finding
- `delivery_blocker` flag explanation if set (P7 only)

### L3
Files in `tasks/{work_dir}/{PHASE}-vc-*.md`:
- `{PHASE}-vc-index.md`: Overall verdict, axis summary table, routing decision
- `{PHASE}-vc-summary.md`: Cross-axis analysis narrative + compound patterns
- `{PHASE}-vc-syntactic.md`, `{PHASE}-vc-semantic.md`, `{PHASE}-vc-behavioral.md`
- `{PHASE}-vc-consumer.md`, `{PHASE}-vc-relational.md`, `{PHASE}-vc-impact.md`
- Each L3 file includes axis findings + cross-axis annotations relevant to that axis

> Detailed methodology (DPS template, tier DPS variations, cross-axis matrix format, output steps, failure sub-cases): `resources/methodology.md`
