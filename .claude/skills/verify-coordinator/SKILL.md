---
name: verify-coordinator
description: >-
  Consolidates four verify dimension verdicts with cross-dimension
  consistency checks into a unified delivery verdict. Terminal P7
  skill that merges parallel verify results (verify-structural-content,
  verify-consistency, verify-quality, verify-cc-feasibility) into a
  single PASS/FAIL routing decision. Use after all four verify skills
  complete. Reads from structural-content scores, consistency findings,
  quality scores, and CC-feasibility verdicts. Produces L1 index and
  L2 summary for Lead, L3 per-dimension files for downstream reference.
  On PASS routes to delivery-pipeline (P8). On FAIL routes findings to
  execution skills per dimension (DPS-parameterized; default:
  execution-infra for structural/consistency issues, execution-review
  for quality issues, Lead for cc-feasibility FAIL which blocks
  delivery). On FAIL, includes specific error locations and owning
  execution skill. DPS needs all four verify dimension outputs.
  Exclude raw execution artifacts and individual file-level annotation
  detail.
user-invocable: true
disable-model-invocation: true
---

# Verify — Coordinator (Cross-Dimension Consolidation)

## Execution Model
- **TRIVIAL**: Lead-direct. ≤2 dimensions, ≤5 findings each. Inline merge with no agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns: 25). Systematic merge of all 4 dimension verdicts, cross-dimension checks, tiered output.
- **COMPLEX**: Spawn analyst (maxTurns: 35). Deep cross-dimension analysis with compound pattern detection and comprehensive L3 production.

Note: P7 validates EXECUTION OUTPUT (post-execution). This coordinator merges dimension verdicts and detects cross-dimension inconsistencies invisible to individual verifiers. It does NOT re-verify dimensions or override individual verdicts.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via Four-Channel Protocol.
- **Ch2**: Agent writes tiered output to `tasks/{team}/p7-coordinator-*.md`.
- **Ch3** micro-signal to Lead: `PASS|dims:4|issues:{N}|ref:tasks/{team}/p7-coordinator-index.md`.
- **Ch4** P2P: not sent at this stage — Lead uses ch3 signal to route delivery-pipeline or execution domain.

> Phase-aware routing details: read `.claude/resources/phase-aware-execution.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Decision Points

### Overall Verdict Computation
Combined dimension results determine routing.
- **All 4 PASS (or CONDITIONAL_PASS) AND cross-check issues = 0**: PASS. Route to delivery-pipeline.
- **All 4 PASS AND cross-check issues exist (MEDIUM severity)**: CONDITIONAL_PASS. Route to delivery-pipeline with annotations.
- **Any dimension FAIL OR cross-check HIGH severity**: FAIL. Route to specific execution skill per finding.
- **cc-feasibility FAIL**: Always FAIL regardless of other dimensions. Route to Lead (blocks delivery).

### Partial Dimension Handling
- **1 dimension missing**: Partial output (3 dimensions). Set `status: PARTIAL`. Route to Lead.
- **2+ dimensions missing**: FAIL with `reason: insufficient_data`. Cannot perform meaningful cross-checks.
- **Coverage < 70% any dimension**: Route that dimension for re-verification with focused scope.

### Lead D-Decision Overrides
When Lead provides conditional override decisions in the DPS, coordinator applies them BEFORE computing the overall verdict.

**Override syntax in DPS**:
```
LEAD_OVERRIDES:
- If [dimension] FAIL with reason [condition]: evaluate if [alternative] → if yes, treat as CONDITIONAL_PASS
```

**Override application protocol**:
1. Read the failing dimension's output file
2. Verify the override condition matches the actual failure mode (do NOT apply blindly)
3. If match: reclassify as CONDITIONAL_PASS with documented override rationale in L2
4. If no match: FAIL stands — report to Lead that override condition did not apply

**Override precedence**: Lead D-decisions > coordinator internal verdict computation. Coordinator must verify applicability — never blindly apply overrides.

### Cross-Dimension Consistency Checks
Individual verifiers check their own dimension. This coordinator checks BETWEEN dimensions:
- **Structure-Quality** (structural-content × quality): Files with low structure scores should also have quality issues. If a file fails structural checks but passes quality (or vice versa), flag misalignment — may indicate incomplete verification coverage.
- **Consistency-Feasibility** (consistency × cc-feasibility): Cross-file reference inconsistencies that also involve CC-feasibility gaps compound the risk. Flag compound patterns as delivery blockers.
- **Content-Feasibility** (structural-content × cc-feasibility): Incomplete L2 bodies combined with infeasible patterns detected by cc-feasibility = delivery blocker. Cannot ship files with both structural gaps and CC runtime incompatibilities.
- **Traceability** (all 4): Any failure covered by fewer than 2 dimensions needs re-verification. Single-dimension-only findings with HIGH severity trigger re-routing to the owning verifier.

> Full cross-check matrices and examples: read `resources/methodology.md`

## Tiered Output Architecture

| Tier | File | Consumer | When Read |
|------|------|----------|-----------|
| L1 | `tasks/{team}/p7-coordinator-index.md` | Lead | Always (routing decisions) |
| L2 | `tasks/{team}/p7-coordinator-summary.md` | Lead | When routing needs detail |
| L3 | `tasks/{team}/p7-coordinator-structural.md` | execution-infra | Via $ARGUMENTS, Lead never reads |
| L3 | `tasks/{team}/p7-coordinator-consistency.md` | execution-infra | Via $ARGUMENTS, Lead never reads |
| L3 | `tasks/{team}/p7-coordinator-quality.md` | execution-review | Via $ARGUMENTS, Lead never reads |
| L3 | `tasks/{team}/p7-coordinator-feasibility.md` | Lead (direct, blocks delivery) | On cc-feasibility FAIL only |

## Failure Handling

| Failure Type | Action | Route |
|-------------|--------|-------|
| 1 dimension missing | Partial output (3 dims), `status: PARTIAL` | Lead for re-routing |
| 2+ dimensions missing | FAIL `reason: insufficient_data` | Lead |
| cc-feasibility FAIL | Overall → FAIL, `delivery_blocker: true` | Lead (blocks P8) |
| Cross-check HIGH severity | Overall → FAIL | Specific execution skill owning finding |
| Cross-check MEDIUM severity | Overall → CONDITIONAL_PASS | Route with annotations |
| All dimensions FAIL | FAIL, prioritize cc-feasibility first | execution-infra, execution-review (ordered) |
| Conflicting dimension assumptions | FAIL — internally inconsistent verify output | Lead for arbitration |

> D12 escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns
- **DO NOT override individual verifier verdicts internally** — coordinator cannot override verdicts based on its own analysis. Cross-dimension issues create NEW findings; they do not change existing verdicts. EXCEPTION: Lead D-Decision overrides (provided explicitly in DPS LEAD_OVERRIDES block) may reclassify a FAIL to CONDITIONAL_PASS — but only after coordinator verifies the override condition matches the actual failure mode.
- **DO NOT perform dimension-specific analysis** — check BETWEEN dimensions only; re-checking file structure or quality belongs to the individual verifiers.
- **DO NOT skip cross-checks when all dimensions PASS** — cross-dimension inconsistencies can exist even when all pass; always perform all 4 checks.
- **DO NOT route all failures to a single execution skill** — structural/consistency failures go to execution-infra, quality failures to execution-review, feasibility failures to Lead.
- **DO NOT bloat L1 index** — L1 must stay ≤30 lines for Lead context budget. Move detail to L2 or L3.
- **DO NOT treat partial input as complete** — if a verifier sent PARTIAL status, reflect this accurately in all output.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| verify-structural-content | Structure scores, YAML/naming findings | L1 YAML: structure_score, content_score, verdict. L2: per-file breakdown |
| verify-consistency | Cross-file consistency findings | L1 YAML: inconsistency_count, broken_refs, verdict. L2: consistency matrix |
| verify-quality | Quality scores, anti-pattern findings | L1 YAML: quality_score, anti_patterns, completeness_pct, verdict. L2: quality matrix |
| verify-cc-feasibility | CC-native feasibility verdict | L1 YAML: feasibility_verdict, blocking_claims, verified_claims. L2: claim analysis |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| delivery-pipeline | L1 index + L2 summary | All dimensions PASS or CONDITIONAL_PASS |
| execution-infra | L3 structural + consistency findings | verify-structural-content FAIL or verify-consistency FAIL |
| execution-review | L3 quality findings | verify-quality FAIL or quality cross-check issue |
| Lead | L3 feasibility findings (direct) | verify-cc-feasibility FAIL (delivery blocker) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing dimension verdicts (1) | Lead | Which verifier missing, partial output with 3 dimensions |
| Missing dimension verdicts (2+) | Lead | Which verifiers missing, FAIL reason |
| cc-feasibility FAIL | Lead | Blocking claims list, delivery_blocker flag |
| Cross-check HIGH severity | Specific execution skill | Cross-dimension finding with escalated severity, file locations |
| All dimensions FAIL | execution-infra + execution-review (prioritized) | Comprehensive failure report with fix priority order |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- All 4 dimension verdicts read and summarized
- All 4 cross-dimension checks performed (structure-quality, consistency-feasibility, content-feasibility, traceability)
- Cross-dimension findings classified by severity with evidence
- Tiered output produced: L1 index.md, L2 summary.md, L3 per-dimension files (4 files)
- Every L3 file includes cross-dimension annotations relevant to that dimension
- Overall verdict = AND of all 4 dimensions plus cross-check severity
- `delivery_blocker: true` set if cc-feasibility FAIL or any HIGH cross-check issue
- Routing decision explicit: PASS → delivery-pipeline, FAIL → execution-infra/execution-review/Lead per finding
- No new verification performed (consolidation only)

## Output

### L1
```yaml
domain: verify
skill: verify-coordinator
overall_verdict: PASS|CONDITIONAL_PASS|FAIL
dimensions:
  structural_content: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  consistency: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  quality: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  cc_feasibility: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
cross_check_issues: 0
delivery_blocker: false
routing: delivery-pipeline|execution-infra|execution-review|Lead
output_ref: tasks/{team}/p7-coordinator-index.md
pt_signal: "metadata.phase_signals.p7_verify"
signal_format: "PASS|dims:4|issues:{N}|ref:tasks/{team}/p7-coordinator-index.md"
```

### L2
- Per-dimension verdict summary with key metrics
- Cross-dimension consistency matrix (4 cross-checks)
- Compound pattern highlights (top 3 by severity)
- Routing decision with rationale per finding
- delivery_blocker flag explanation if set

### L3
Files in `tasks/{team}/p7-coordinator-*.md`:
- `p7-coordinator-structural.md`: Structural-content findings + cross-dimension annotations (for execution-infra)
- `p7-coordinator-consistency.md`: Consistency findings + cross-dimension annotations (for execution-infra)
- `p7-coordinator-quality.md`: Quality findings + cross-dimension annotations (for execution-review)
- `p7-coordinator-feasibility.md`: CC-feasibility findings + blocking claim list (for Lead)

> Detailed methodology (DPS template, tier DPS variations, cross-check matrices, output steps, failure sub-cases): read `resources/methodology.md`
