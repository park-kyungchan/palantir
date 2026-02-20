---
name: validate-semantic
description: >-
  Validates contextual correctness and quality of artifacts
  via phase-parameterized DPS. P4: cross-checks test coverage
  against behavior predictions with risk-weighted scoring.
  P7: assesses artifact quality across specificity,
  concreteness, completeness, and utilization dimensions.
  Verdict: PASS (P4 weighted ≥90% + rollback ≥90%; P7 avg
  score >75), FAIL (P4 HIGH untested or <75%; P7 avg <75
  or CRITICAL scores). Parallel with other validate-* axis
  skills. Use after plan domain complete (P4) or
  execution-review PASS (P7). Reads from plan-behavioral +
  audit-behavioral L3 (P4) or verify-ready artifacts (P7).
  Produces semantic verdict for validate-coordinator.
  On FAIL, routes to plan-behavioral (P4) or execution-infra
  (P7). DPS needs PHASE_CONTEXT + upstream outputs. Exclude
  other axis results.
user-invocable: true
disable-model-invocation: true
---

# Validate — Semantic

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check that each predicted change has a test entry (P4) or spot-check 1-3 files against rubric (P7). No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of tests vs predictions (P4) or full quality scoring audit of 4-15 files (P7).
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep risk-weighted coverage + rollback analysis (P4) or 2-analyst quality split — WHEN/METHODOLOGY vs OUTPUT/utilization (P7).

Note: P4 validates PLANS (pre-execution). P7 validates IMPLEMENTATION artifacts (post-execution). Phase context is set by DPS PHASE_CONTEXT block.

## Phase Context

| Phase | Artifacts In | Focus | Pass Threshold | Fail Route | Output File |
|-------|-------------|-------|----------------|------------|-------------|
| P4 | plan-behavioral test strategy + audit-behavioral L3 predictions | Test coverage vs behavior predictions; risk-weighted scoring (HIGH=3, MEDIUM=2, LOW=1) | Weighted ≥90% + rollback ≥90% | plan-behavioral | `{work_dir}/p4-validate-semantic.md` |
| P7 | verify-ready artifacts post execution-review PASS | Quality scoring: WHEN specificity 30%, METHODOLOGY concreteness 30%, OUTPUT completeness 20%, utilization 20% | avg score >75, no CRITICAL (<50) | execution-infra | `{work_dir}/p7-validate-semantic.md` |

## Phase-Aware Execution
- **Spawn**: Spawn analyst (`run_in_background:true`, `context:fork`). Agent writes output to phase-specific file per Phase Context table.
- **Delivery**: Micro-signal: `{VERDICT}|phase:{P4|P7}|ref:tasks/{work_dir}/{phase}-validate-semantic.md`.
- See `.claude/resources/phase-aware-execution.md` for full phase protocol.

## Decision Points

### P4 — Coverage Thresholds
- **Weighted ≥90% AND rollback ≥90%**: PASS. Route to validate-coordinator.
- **Weighted 75–89% with untested items LOW-risk only**: CONDITIONAL_PASS. Route with risk annotation.
- **Weighted <75% or any HIGH-risk untested**: FAIL. Route to plan-behavioral with gap evidence.
- **Hard rule**: Any HIGH-risk change with neither test NOR rollback trigger → always FAIL regardless of aggregate score.

### P7 — Scoring Thresholds
- **avg score >75 with no CRITICAL items**: PASS. Route to validate-coordinator.
- **avg score <75 or any skill WHEN <50 (CRITICAL)**: FAIL (blocking). Route bottom-5 to execution-infra.
- **Individual scores 51–70 (HIGH)**: Warnings accumulate. Three or more HIGH warnings trigger blocking FAIL.
- **Cross-cutting/homeostasis skills**: Apply domain-adjusted baseline — WHEN scores start at 50 for broad triggers.

### P7 — Scoring Rubric (condensed)
| Dimension | Weight | PASS (≥75) | FAIL (<50) |
|-----------|--------|-----------|-----------|
| WHEN Specificity | 30% | Named phase + concrete upstream trigger | Missing or vague "when needed" |
| METHODOLOGY Concreteness | 30% | Numbered steps + tool/agent names | Generic actions or unnumbered |
| OUTPUT Completeness | 20% | L1 YAML + L2 markdown templates | No output template defined |
| Utilization | 20% | >80% of 1024 chars | <60% |

→ Full scoring rubric table with per-score breakpoints: `resources/methodology.md`

### Scale → Spawn Parameters
- **<10 predictions (P4) / <15 files (P7)**: STANDARD analyst (maxTurns:20).
- **10–30 predictions / 16+ files**: COMPLEX analyst (maxTurns:30). Prioritize HIGH-risk predictions or recently modified files.
- **>30 predictions**: COMPLEX (maxTurns:30). Cover all HIGH-risk first, sample MEDIUM/LOW. Flag PARTIAL if <100% verified.

## Methodology

### P4 Steps
1. **Test Inventory** — Build list of all tests and rollback triggers from plan-behavioral output.
2. **Prediction Inventory** — Extract behavior predictions with risk ratings from audit-behavioral L3.
3. **Cross-Reference** — Map each prediction to covering test(s). Verify assertion type and scope match. Score: weighted coverage = Σ(risk_weight × covered) / Σ(risk_weight × total).
4. **Rollback Verification** — For each HIGH-risk change: verify rollback trigger is specific (not "rollback if something fails"). Flag generic triggers as PARTIAL.
5. **Report** — Weighted coverage %, rollback coverage %, untested HIGH-risk list, verdict vs threshold.

### P7 Steps
1. **WHEN Specificity** — Read WHEN clause per artifact. Score 0-100: concrete upstream skill + trigger event (100) → vague "when needed" (0).
2. **METHODOLOGY Concreteness** — Check steps are numbered. Each step must name a concrete tool or action. Score 0-100.
3. **OUTPUT Completeness** — Verify L1 YAML has `domain`, `skill`, `status` fields. Verify L2 markdown description present. Score 0-100.
4. **Utilization** — Calculate char count / 1024. Target >80%. Score 0-100.
5. **Quality Rankings** — Combined score = (WHEN × 0.30) + (METHODOLOGY × 0.30) + (OUTPUT × 0.20) + (utilization × 0.20). Rank all artifacts. Identify bottom-5 for improvement paths.

→ Full analyst DPS templates, scoring examples, bottom-5 report format: `resources/methodology.md`

**Shared resources** (load on demand):
- `.claude/resources/phase-aware-execution.md`
- `.claude/resources/failure-escalation-ladder.md`
- `.claude/resources/dps-construction-guide.md`
- `.claude/resources/output-micro-signal-format.md`

## Iteration Tracking (D15)
- Lead manages `metadata.iterations.validate-semantic: N` in PT before each invocation.
- **P4**: Iteration 1 strict (FAIL → return to plan-behavioral). Iteration 2 relaxed (proceed with risk flags). Max 2.
- **P7**: 1 iteration. FAIL routes directly to execution-infra with bottom-5 improvement instructions.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Upstream missing (audit-behavioral L3 or verify-ready artifacts) | L0 Retry | Re-invoke same agent, same DPS; report missing upstream to Lead |
| Coverage matrix incomplete or predictions unverified | L1 Nudge | Respawn with refined DPS targeting remaining scope + scoring rubric reminder |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS, reduced file/prediction batch |
| Prediction set scope changed or behavioral model stale (P4) | L3 Restructure | Modify task graph, re-run audit-behavioral upstream |
| Strategic test coverage ambiguity or rubric unclear, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

**Special cases**: Analyst PARTIAL (P4) → report partial coverage + unverified prediction list, status: PARTIAL. Routing failure investigation mode (P7) → weight WHEN specificity at 50%, produce disambiguation recommendations.

See `.claude/resources/failure-escalation-ladder.md` for D12 decision rules.

## Anti-Patterns

- **DO NOT verify test implementation (P4)** — Check that test strategy covers predictions. Do not assess test code quality, assertion correctness, or framework usage.
- **DO NOT accept generic rollback triggers (P4)** — "Rollback if something goes wrong" is not specific. HIGH-risk changes need a condition describing what failure looks like for that change.
- **DO NOT treat scope mismatches as full coverage (P4)** — A unit test for an integration-level behavior change is PARTIAL, not covered.
- **DO NOT score based on L2 body quality (P7)** — Score only L1 description/frontmatter. L2 body quality is validate-syntactic's domain.
- **DO NOT auto-fix low scores (P7)** — Quality check is read-only. Produce improvement instructions only; fixes route through execution-infra.
- **DO NOT over-weight utilization (P7)** — A concise specific description outperforms padded vague content. Utilization weighted at 20% only.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|---|---|---|
| plan-behavioral (P4) | Test strategy with rollback triggers | L1 YAML: tests[] with target, assertion, scope; rollbacks[] with trigger, action |
| research-coordinator (P4) | Audit-behavioral L3 behavior predictions | L3: predictions[] with change_type, affected_component, risk, confidence |
| execution-review (P7) | PASS verdict + verify-ready artifact paths | L1 YAML: status:PASS, artifact paths list |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| validate-coordinator | Semantic verdict with coverage/quality evidence | Always (parallel axis result for N→1 synthesis) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|---|---|---|
| Untested HIGH-risk or coverage <75% (P4) | plan-behavioral | Untested prediction list + risk weights + gap evidence |
| avg score <75 or CRITICAL WHEN score (P7) | execution-infra | Bottom-5 skills with scores, per-dimension breakdown, fix instructions |
| Missing upstream data | Lead | Which upstream phase output is missing |

## Quality Gate
- P4: Every predicted behavior change checked against test inventory; weighted + rollback coverage calculated; all untested HIGH-risk changes flagged with evidence
- P7: Every artifact scored across all 4 dimensions; bottom-5 identified with specific improvement paths; rubric applied consistently with documented weights (30/30/20/20)
- All findings cite specific prediction IDs + test case IDs (P4) or file path + current score + target (P7)
- Verdict with explicit threshold comparison and phase clearly stated

## Output

### L1
```yaml
domain: validate
skill: validate-semantic
phase: P4|P7
verdict: PASS|CONDITIONAL_PASS|FAIL
pt_signal: "metadata.phase_signals.{phase}_validate_semantic"
# P4 fields
test_coverage_percent: 0
weighted_coverage_percent: 0
rollback_coverage_percent: 0
tested_count: 0
total_predictions: 0
# P7 fields
total_files: 0
avg_score: 0
bottom_5: []
# shared
findings:
  - type: untested_change|scope_mismatch|missing_rollback|low_when|missing_methodology|missing_output
    file: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
signal_format: "{VERDICT}|phase:{PHASE}|ref:tasks/{work_dir}/{phase}-validate-semantic.md"
```

### L2
- P4: Test coverage matrix (prediction vs test mapping), weighted coverage calculation with risk weights, rollback coverage matrix for HIGH-risk changes, untested change list with risk levels and evidence
- P7: Quality score per file (0-100) with per-dimension breakdown, WHEN disambiguation test results, bottom-5 priority improvement list with specific fix instructions
