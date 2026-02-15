---
name: plan-verify-coordinator
description: |
  [P4·PlanVerify·Coordinator] Consolidates 4 dimension verdicts with cross-dimension consistency checks into tiered output.

  WHEN: After all 4 pv-* skills complete. Wave 4.5. Terminal.
  DOMAIN: plan-verify (skill 5 of 5). Terminal. Receives from 4 parallel verifiers.
  INPUT_FROM: pv-static (coverage verdict), pv-behavioral (test coverage verdict), pv-relational (integrity verdict), pv-impact (containment verdict).
  OUTPUT_TO: orchestrate-static/behavioral/relational/impact (all PASS: L3 per-dimension), plan domain (any FAIL: route back). Lead reads L1 index + L2 summary.

  METHODOLOGY: (1) Read 4 dimension verdicts+metrics, (2) Cross-check: dep<->seq, contract<->boundary, rollback<->checkpoint, traceability, (3) L1 index.md (verdict+routing), (4) L2 summary.md (cross-dim findings), (5) L3 per-dim files with annotations.
  OUTPUT_FORMAT: Tiered /tmp/pipeline/p4-coordinator/. L1 index, L2 summary, L3 verify-{dim}.
user-invocable: false
disable-model-invocation: false
---

# Plan Verify — Coordinator

## Execution Model
- **STANDARD**: Spawn analyst (maxTurns:25). Merge 4 verdicts, perform cross-dimension checks, produce tiered output.
- **COMPLEX**: Spawn analyst (maxTurns:35). Deep cross-dimension analysis with consistency matrix and comprehensive L3 production.

Note: P4 validates PLANS (pre-execution). This coordinator merges dimension-specific verdicts and checks for cross-dimension inconsistencies that individual verifiers cannot detect. It does NOT re-verify dimensions or override individual verdicts.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes tiered output to `/tmp/pipeline/p4-coordinator/`, sends micro-signal: `PASS|dimensions:4|cross_issues:{N}|ref:/tmp/pipeline/p4-coordinator/index.md`.

## Methodology

### 1. Read All 4 Dimension Verdicts
Load each verifier's output:
- **plan-verify-static**: Coverage verdict, orphan count, missing edge count
- **plan-verify-behavioral**: Test coverage, weighted coverage, rollback coverage
- **plan-verify-relational**: Contract count, asymmetric count, missing count
- **plan-verify-impact**: Path count, unmitigated count, late checkpoint count

For each dimension, extract:
- Verdict (PASS/CONDITIONAL_PASS/FAIL)
- Key metrics (counts, percentages)
- Findings list with severity classifications
- Evidence references

If any dimension is PARTIAL (analyst exhausted), note the coverage percentage and treat unverified portions as risk.

### 2. Cross-Dimension Consistency Checks
Individual verifiers check their own dimension. The coordinator checks BETWEEN dimensions for inconsistencies that no single verifier can detect.

#### 2a. Dependency-Sequence Consistency (Static x Impact)
Cross-check plan-verify-static's dependency edges against plan-verify-impact's execution sequence:
- Every dependency edge (A depends on B) should be respected by the execution sequence (B executes before A)
- If static finds an orphan file and impact shows a propagation path through that file, the orphan is more severe than static alone detects

| Static Finding | Impact Finding | Cross-Check Result |
|---------------|----------------|-------------------|
| Orphan file X | Path through X | ESCALATE: orphan on propagation path |
| Missing edge A->B | Checkpoint between A and B | MITIGATED: checkpoint covers missing edge |
| Coverage gap in module M | No paths through M | ACCEPTABLE: isolated module |

#### 2b. Contract-Boundary Consistency (Relational x Static)
Cross-check plan-verify-relational's contracts against plan-verify-static's dependency graph:
- Every cross-boundary dependency edge should have a corresponding contract
- A contract without a corresponding dependency edge is suspicious (orphan contract)
- Asymmetric contracts should align with edge direction in the dependency graph

| Relational Finding | Static Finding | Cross-Check Result |
|-------------------|----------------|-------------------|
| Missing contract for A->B | A->B is cross-boundary edge | ESCALATE: boundary without contract |
| Orphan contract for C->D | No C->D edge in graph | CONFIRM: phantom contract |
| Asymmetric A->B (no B->A contract) | B->A edge exists | ESCALATE: reverse dependency uncontracted |

#### 2c. Rollback-Checkpoint Consistency (Behavioral x Impact)
Cross-check plan-verify-behavioral's rollback triggers against plan-verify-impact's checkpoints:
- Every rollback trigger should have a corresponding checkpoint that can invoke it
- Checkpoints without rollback capability for their detected failures are detection-only
- HIGH-risk behavior changes should have both a test AND a containment checkpoint

| Behavioral Finding | Impact Finding | Cross-Check Result |
|-------------------|----------------|-------------------|
| Rollback trigger for auth | Checkpoint after auth phase | ALIGNED: trigger has checkpoint |
| Rollback trigger for cache | No checkpoint near cache phase | GAP: trigger without checkpoint |
| HIGH-risk untested change | Contained by checkpoint | PARTIAL: contained but untested |

#### 2d. Requirement Traceability (All Dimensions)
Verify that the combined plan verification covers all original requirements:
- Static coverage ensures files are assigned
- Behavioral coverage ensures changes are tested
- Relational coverage ensures interfaces are specified
- Impact coverage ensures changes are contained

If any requirement is covered by fewer than 3 of the 4 dimensions, flag as under-verified.

### 3. Produce L1 Index for Lead
Write `/tmp/pipeline/p4-coordinator/index.md` with:
- Overall verdict: AND of all 4 dimensions (CONDITIONAL_PASS counts as PASS)
- Per-dimension verdict summary (one line each)
- Cross-dimension issue count
- Routing decision: PASS -> orchestration domain, FAIL -> specific plan-X skills

### 4. Produce L2 Summary for Lead
Write `/tmp/pipeline/p4-coordinator/summary.md` with:
- Per-dimension metric summary table
- Cross-dimension consistency findings
- Escalated findings (cross-dimension issues that increase severity)
- Routing recommendation with rationale

### 5. Produce L3 Per-Dimension Files for Downstream
Write individual files to `/tmp/pipeline/p4-coordinator/`:
- `verify-static.md`: Static coverage details with orphan list
- `verify-behavioral.md`: Test coverage details with untested change list
- `verify-relational.md`: Contract integrity details with gap list
- `verify-impact.md`: Containment details with unmitigated path list

Each L3 file includes:
- Original verifier findings
- Cross-dimension annotations (escalations, mitigations)
- Adjusted severity based on cross-checks

## Failure Handling

### One or More Dimension Verdicts Missing
- **Cause**: A verifier did not complete (agent failure, exhaustion).
- **Action**: If 1 dimension missing, produce partial coordinator output with 3 dimensions. Set `status: PARTIAL`. If 2+ dimensions missing, FAIL with `reason: insufficient_data`.
- **Route**: Lead for re-routing missing verifiers.

### All Dimensions PASS But Cross-Checks Find Issues
- **Cause**: Individual dimensions pass their thresholds but cross-dimension analysis reveals inconsistencies.
- **Action**: Set overall to CONDITIONAL_PASS if cross-issues are MEDIUM severity. Set overall to FAIL if any cross-issue is HIGH severity.
- **Route**: If FAIL, route to the specific plan skill that owns the finding (plan-static for dependency issues, plan-behavioral for test issues, etc.).

### All Dimensions FAIL
- **Cause**: Systematic plan quality failure across all dimensions.
- **Action**: FAIL with comprehensive feedback. Prioritize findings: address structural (static) first, then behavioral, relational, impact.
- **Route**: plan domain with prioritized fix list. Recommend addressing static coverage first (foundation for other dimensions).

### Partial Dimension Verdicts
- **Cause**: One or more verifiers reported PARTIAL (analyst exhausted).
- **Action**: Accept partial verdicts but note coverage gaps in L2. Unverified portions count as risk, not failure.
- **Route**: If partial coverage > 70% per dimension, proceed with risk annotation. If < 70%, route for re-verification with focused scope.

### Cross-Check Reveals Conflicting Plan Assumptions
- **Cause**: plan-static assumes module A is independent, but plan-impact shows propagation paths through A.
- **Action**: Escalate to FAIL. The plan has internally conflicting assumptions.
- **Route**: Lead for arbitration between conflicting plan skills.

## Anti-Patterns

### DO NOT: Override Individual Verifier Verdicts
The coordinator consolidates and cross-checks. It does not re-evaluate individual dimensions. If plan-verify-static says PASS, the coordinator cannot change it to FAIL based on its own re-analysis. Cross-dimension issues create NEW findings, they do not override existing verdicts.

### DO NOT: Perform Dimension-Specific Analysis
Each dimension has its own verifier. The coordinator checks BETWEEN dimensions only. Do not re-check orphan files (that is plan-verify-static's job) or re-check test coverage (that is plan-verify-behavioral's job).

### DO NOT: Skip Cross-Checks When All Dimensions PASS
Cross-dimension inconsistencies can exist even when all individual dimensions pass. The coordinator's primary value is cross-dimension analysis. Always perform all 4 cross-checks.

### DO NOT: Route All Failures to a Single Plan Skill
Each failure maps to a specific plan-X skill. Route static issues to plan-static, behavioral to plan-behavioral, etc. Sending all failures to one skill overloads it.

### DO NOT: Produce L3 Without Cross-Dimension Annotations
Raw verifier output forwarded without cross-check annotations provides no coordinator value. Every L3 file must include cross-dimension context.

### DO NOT: Accept Partial Input as Complete
If a verifier sent PARTIAL status, the coordinator must reflect this in its output. Do not treat 70% verified as fully verified.

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
output_dir: /tmp/pipeline/p4-coordinator/
```

### L2
- Per-dimension verdict summary with key metrics
- Cross-dimension consistency matrix (4 cross-checks)
- Escalated findings from cross-dimension analysis
- Routing decision with rationale

### L3
Files in `/tmp/pipeline/p4-coordinator/`:
- `index.md`: Overall verdict, dimension summary, routing decision
- `summary.md`: Cross-dimension analysis narrative
- `verify-static.md`: Static findings + cross-dimension annotations
- `verify-behavioral.md`: Behavioral findings + cross-dimension annotations
- `verify-relational.md`: Relational findings + cross-dimension annotations
- `verify-impact.md`: Impact findings + cross-dimension annotations
