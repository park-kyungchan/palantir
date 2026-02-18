---
name: plan-verify-coordinator
description: >-
  Consolidates four dimension verdicts with cross-dimension
  consistency checks. Terminal plan-verify skill that
  cross-checks dependency-sequence, contract-boundary, and
  rollback-checkpoint alignment. Use after all four plan-verify
  dimension skills complete (plan-verify-static,
  plan-verify-behavioral, plan-verify-relational,
  plan-verify-impact). Reads from plan-verify-static coverage
  verdict, plan-verify-behavioral test coverage verdict,
  plan-verify-relational integrity verdict, and
  plan-verify-impact containment verdict. Produces L1 index and
  L2 summary for Lead, L3 per-dimension files for orchestrate
  skills. On FAIL (cross-dimension inconsistency), Lead applies
  D12 escalation. DPS needs all four plan-verify dimension
  verdicts. Exclude individual plan dimension detail.
user-invocable: false
disable-model-invocation: false
---

# Plan Verify — Coordinator

## Execution Model
- **TRIVIAL**: Lead-direct. Merge 4 dimension verdicts inline. Skip cross-checks if all PASS with zero findings. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:25). Merge 4 verdicts, perform cross-dimension checks, produce tiered output.
- **COMPLEX**: Spawn analyst (maxTurns:35). Deep cross-dimension analysis with consistency matrix and comprehensive L3 production.

Note: P4 validates PLANS (pre-execution). This coordinator merges dimension-specific verdicts and checks for cross-dimension inconsistencies that individual verifiers cannot detect. It does NOT re-verify dimensions or override individual verdicts.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via Four-Channel Protocol.
- **Ch2**: Agent writes tiered output to `tasks/{team}/p4-coordinator-*.md`.
- **Ch3** micro-signal to Lead: `PASS|dimensions:4|cross_issues:{N}|ref:tasks/{team}/p4-coordinator-index.md`.
- **Ch4** P2P: not sent at this stage — Lead uses Deferred Spawn to route orchestrate-* skills with $ARGUMENTS pointing to L3 files.

> Phase-aware routing details: read `.claude/resources/phase-aware-execution.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Decision Points

### Overall Verdict Computation
Combined dimension results determine routing.
- **All 4 PASS (or CONDITIONAL_PASS) AND cross-check issues = 0**: PASS. Route to orchestration domain.
- **All 4 PASS AND cross-check issues exist (MEDIUM severity)**: CONDITIONAL_PASS. Route with annotations.
- **Any dimension FAIL OR cross-check HIGH severity**: FAIL. Route to specific plan-X skill per finding.
- **Default — 2+ dimensions FAIL**: Prioritize static first (foundation for others).

### Partial Dimension Handling
- **1 dimension missing**: Produce partial output (3 dimensions). Set `status: PARTIAL`. Route to Lead.
- **2+ dimensions missing**: FAIL with `reason: insufficient_data`. Cannot perform meaningful cross-checks.
- **Coverage ≥ 70% per dimension**: Proceed with risk annotation on unverified portions.
- **Coverage < 70% any dimension**: Route that dimension for re-verification with focused scope.

### Cross-Dimension Consistency Rules
Individual verifiers check their own dimension. This coordinator checks BETWEEN dimensions:
- **Dependency-Sequence** (Static × Impact): orphan files on propagation paths escalate severity; checkpoints mitigate missing edges.
- **Contract-Boundary** (Relational × Static): every cross-boundary dependency edge must have a contract; orphan contracts are flagged.
- **Rollback-Checkpoint** (Behavioral × Impact): every rollback trigger must have a corresponding checkpoint; HIGH-risk untested changes require both a test AND a containment checkpoint.
- **Requirement Traceability** (All 4): any requirement covered by fewer than 3 dimensions is flagged as under-verified.

> Full cross-check matrices and examples: read `resources/methodology.md`

## Failure Handling

| Failure Type | Action | Route |
|-------------|--------|-------|
| 1 dimension missing | Partial output (3 dims), `status: PARTIAL` | Lead for re-routing |
| 2+ dimensions missing | FAIL `reason: insufficient_data` | Lead |
| Cross-check HIGH severity | Overall → FAIL | Specific plan-X skill owning finding |
| Cross-check MEDIUM severity | Overall → CONDITIONAL_PASS | Route with annotations |
| All dimensions FAIL | FAIL, prioritize static first | plan domain (ordered fix list) |
| Conflicting plan assumptions | FAIL — internally inconsistent plan | Lead for arbitration |

> D12 escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns
- **DO NOT override individual verifier verdicts** — cross-dimension issues create NEW findings; they do not change existing verdicts.
- **DO NOT perform dimension-specific analysis** — check BETWEEN dimensions only; re-checking orphans or test coverage belongs to the individual verifiers.
- **DO NOT skip cross-checks when all dimensions PASS** — cross-dimension inconsistencies can exist even when all pass; always perform all 4 checks.
- **DO NOT route all failures to a single plan skill** — each failure maps to its owning plan-X skill; distribute accordingly.
- **DO NOT produce L3 without cross-dimension annotations** — raw verifier output forwarded without annotations provides no coordinator value.
- **DO NOT treat partial input as complete** — if a verifier sent PARTIAL status, reflect this in all output.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-verify-static | Coverage verdict | L1 YAML: coverage_percent, orphan_count, verdict. L2: coverage matrix |
| plan-verify-behavioral | Test coverage verdict | L1 YAML: test_coverage, weighted_coverage, rollback_coverage, verdict. L2: test matrix |
| plan-verify-relational | Integrity verdict | L1 YAML: contract_count, asymmetric_count, missing_count, verdict. L2: consistency matrix |
| plan-verify-impact | Containment verdict | L1 YAML: total_paths, unmitigated_count, verdict. L2: containment matrix |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration domain | L3 per-dimension verified plan data | All dimensions PASS or CONDITIONAL_PASS |
| plan-static | Static coverage failure feedback | plan-verify-static FAIL or static cross-check issue |
| plan-behavioral | Behavioral coverage failure feedback | plan-verify-behavioral FAIL or behavioral cross-check issue |
| plan-relational | Relational integrity failure feedback | plan-verify-relational FAIL or relational cross-check issue |
| plan-impact | Containment failure feedback | plan-verify-impact FAIL or impact cross-check issue |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing dimension verdicts (1) | Lead | Which verifier missing, partial output with 3 dimensions |
| Missing dimension verdicts (2+) | Lead | Which verifiers missing, FAIL reason |
| Cross-check HIGH severity | Specific plan-X skill | Cross-dimension finding with escalated severity |
| All dimensions FAIL | plan domain (prioritized) | Comprehensive failure report with fix priority order |
| Conflicting plan assumptions | Lead | Conflict details between plan skills |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- All 4 dimension verdicts read and summarized
- All 4 cross-dimension checks performed (dep-sequence, contract-boundary, rollback-checkpoint, traceability)
- Cross-dimension findings classified by severity with evidence
- Tiered output produced: L1 index.md, L2 summary.md, L3 per-dimension files
- Every L3 file includes cross-dimension annotations
- Overall verdict computed as AND of dimensions plus cross-check results
- Routing decision explicit: PASS target or FAIL target per finding

## Output

### L1
```yaml
domain: plan-verify
skill: plan-verify-coordinator
overall_verdict: PASS|CONDITIONAL_PASS|FAIL
dimensions:
  static: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  behavioral: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  relational: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
  impact: PASS|CONDITIONAL_PASS|FAIL|PARTIAL
cross_check_issues: 0
escalated_findings: 0
routing: orchestration|plan-static|plan-behavioral|plan-relational|plan-impact
output_ref: tasks/{team}/p4-coordinator-index.md
```

### L2
- Per-dimension verdict summary with key metrics
- Cross-dimension consistency matrix (4 cross-checks)
- Escalated findings from cross-dimension analysis
- Routing decision with rationale

### L3
Files in `tasks/{team}/p4-coordinator-*.md`:
- `p4-coordinator-index.md`: Overall verdict, dimension summary, routing decision
- `p4-coordinator-summary.md`: Cross-dimension analysis narrative
- `p4-coordinator-verify-static.md`: Static findings + cross-dimension annotations
- `p4-coordinator-verify-behavioral.md`: Behavioral findings + cross-dimension annotations
- `p4-coordinator-verify-relational.md`: Relational findings + cross-dimension annotations
- `p4-coordinator-verify-impact.md`: Impact findings + cross-dimension annotations

> Detailed methodology (DPS template, tier DPS variations, cross-check matrices, output steps, failure sub-cases): read `resources/methodology.md`
