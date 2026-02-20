# Plan Verify Coordinator — Detailed Methodology

## Coordinator Delegation DPS

**Context (D11 priority: cognitive focus > token efficiency)**:
- INCLUDE: all four plan-verify dimension L1 verdicts with YAML metrics and L2 evidence summaries;
  file paths within this agent's ownership boundary
- EXCLUDE: individual plan dimension detail; historical rationale; full pipeline state beyond P4;
  dimension-internal methodology
- Budget: Context field ≤ 30% of subagent effective context

**Task**: "Consolidate 4 dimension verdicts. Perform 4 cross-dimension checks: (a) dependency-sequence,
(b) contract-boundary, (c) rollback-checkpoint, (d) requirement traceability. Produce tiered output:
L1 index.md, L2 summary.md, L3 per-dimension annotated files."

**Constraints**: Analyst agent (Read-only, no Bash). maxTurns:25 (STANDARD) or 35 (COMPLEX).
Do NOT re-evaluate individual dimensions.

**Expected Output**: L1: `tasks/{work_dir}/p4-coordinator-index.md` (verdict, routing).
L2: `tasks/{work_dir}/p4-coordinator-summary.md` (cross-dim findings).
L3: 4 files `tasks/{work_dir}/p4-coordinator-verify-{dim}.md` with cross-dimension annotations.

### Tier-Specific DPS Variations
- **TRIVIAL**: Lead-direct. All 4 PASS with zero findings → merge verdicts inline. Write minimal L1 index only.
- **STANDARD**: Single analyst, maxTurns:25. Full 4 cross-checks + tiered L1/L2/L3 output.
- **COMPLEX**: Single analyst, maxTurns:35. Deep cross-dimension consistency matrix + comprehensive L3 with adjusted severity annotations.

## Step 1 — Read All 4 Dimension Verdicts

Load each verifier's output and extract:
- Verdict (PASS/CONDITIONAL_PASS/FAIL), key metrics, findings list with severity, evidence references

| Dimension | Key Metrics |
|-----------|-------------|
| plan-verify-static | coverage_percent, orphan_count, missing_edge_count |
| plan-verify-behavioral | test_coverage, weighted_coverage, rollback_coverage |
| plan-verify-relational | contract_count, asymmetric_count, missing_count |
| plan-verify-impact | total_paths, unmitigated_count, late_checkpoint_count |

If any dimension is PARTIAL (analyst exhausted): note coverage percentage, treat unverified portions as risk.

## Step 2 — Cross-Dimension Consistency Checks

### 2a. Dependency-Sequence Consistency (Static × Impact)
Cross-check plan-verify-static dependency edges vs. plan-verify-impact execution sequence.

| Static Finding | Impact Finding | Cross-Check Result |
|---------------|----------------|-------------------|
| Orphan file X | Path through X | ESCALATE: orphan on propagation path |
| Missing edge A→B | Checkpoint between A and B | MITIGATED: checkpoint covers missing edge |
| Coverage gap in module M | No paths through M | ACCEPTABLE: isolated module |

### 2b. Contract-Boundary Consistency (Relational × Static)
Cross-check plan-verify-relational contracts vs. plan-verify-static dependency graph.

| Relational Finding | Static Finding | Cross-Check Result |
|-------------------|----------------|-------------------|
| Missing contract for A→B | A→B is cross-boundary edge | ESCALATE: boundary without contract |
| Orphan contract for C→D | No C→D edge in graph | CONFIRM: phantom contract |
| Asymmetric A→B (no B→A) | B→A edge exists | ESCALATE: reverse dependency uncontracted |

### 2c. Rollback-Checkpoint Consistency (Behavioral × Impact)
Cross-check plan-verify-behavioral rollback triggers vs. plan-verify-impact checkpoints.

| Behavioral Finding | Impact Finding | Cross-Check Result |
|-------------------|----------------|-------------------|
| Rollback trigger for auth | Checkpoint after auth phase | ALIGNED: trigger has checkpoint |
| Rollback trigger for cache | No checkpoint near cache phase | GAP: trigger without checkpoint |
| HIGH-risk untested change | Contained by checkpoint | PARTIAL: contained but untested |

### 2d. Requirement Traceability (All Dimensions)
Verify combined plan verification covers all original requirements:
- Static: files assigned. Behavioral: changes tested. Relational: interfaces specified. Impact: changes contained.
- Flag any requirement covered by fewer than 3 of the 4 dimensions as under-verified.

## Steps 3–5 — Output Production

### Step 3 — L1 Index (Lead routing)
Write `tasks/{work_dir}/p4-coordinator-index.md`:
- Overall verdict + per-dimension verdict summary (one line each)
- Cross-dimension issue count + routing decision (PASS → orchestration | FAIL → specific plan-X)

### Step 4 — L2 Summary (Lead quality gate)
Write `tasks/{work_dir}/p4-coordinator-summary.md`:
- Per-dimension metric summary table
- Cross-dimension consistency findings + escalated findings
- Routing recommendation with rationale

### Step 5 — L3 Per-Dimension Files (orchestrate-* input)
Write `tasks/{work_dir}/p4-coordinator-verify-{dim}.md` for each dimension:
- Original verifier findings + cross-dimension annotations (escalations, mitigations)
- Adjusted severity based on cross-checks

## Failure Sub-Cases (Prose)

**1 dimension missing**: Produce partial output with 3 dimensions. `status: PARTIAL`. Route to Lead for re-routing missing verifier.

**2+ dimensions missing**: FAIL with `reason: insufficient_data`. Cannot perform meaningful cross-checks.

**All dimensions PASS, cross-check finds MEDIUM issues**: CONDITIONAL_PASS. Route with annotations.

**All dimensions PASS, cross-check finds HIGH severity**: FAIL. Route to specific plan-X skill that owns the finding.

**All dimensions FAIL**: FAIL with prioritized fix list. Address static first (foundation for other dimensions).

**Conflicting plan assumptions** (e.g., plan-static treats module A as independent; plan-impact shows propagation through A): FAIL. Route to Lead for arbitration.
