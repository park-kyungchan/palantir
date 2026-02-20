---
name: plan-verify-relational
description: >-
  Validates contract integrity against relationship graph for
  asymmetric or missing contracts. Verdict: PASS (zero HIGH
  gaps), FAIL (HIGH asymmetric or >5 gaps). Parallel with
  plan-verify-static, plan-verify-behavioral, and
  plan-verify-impact. Use after plan-relational complete. Reads
  from plan-relational interface contracts and
  research-coordinator audit-relational L3 relationship graph.
  Produces integrity verdict and consistency matrix with gap
  analysis for plan-verify-coordinator.
  On FAIL, routes back to plan-relational with verified gap
  evidence. DPS needs plan-relational output and
  research-coordinator audit-relational L3. Exclude other verify
  dimension results.
user-invocable: true
disable-model-invocation: true
---

# Plan Verify — Relational Integrity

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check that each relationship edge has a contract entry. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of interface contracts against relationship graph edges.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep bidirectional consistency check with asymmetry detection across all module boundaries.

Note: P4 validates PLANS (pre-execution). This skill verifies that interface contracts fully and
symmetrically cover the relationship graph. It does NOT verify contract implementation correctness.

## Phase-Aware Execution
- **Spawn**: Spawn agent (`run_in_background:true`, `context:fork`). Agent writes output to file.
- **Delivery**: Agent writes result to `tasks/{work_dir}/p4-pv-relational.md`, micro-signal: `PASS|contracts:{N}|asymmetric:{N}|ref:tasks/{work_dir}/p4-pv-relational.md`.

> Ref: `.claude/resources/phase-aware-execution.md` — Phase-Aware agent spawn protocol

## Decision Points

### Integrity Threshold Interpretation
Gap severity determines verdict routing.
- **Zero HIGH-severity gaps AND total gaps <= 2**: PASS. Route to plan-verify-coordinator.
- **Only MEDIUM-severity gaps AND total <= 5**: CONDITIONAL_PASS. Route with risk annotation.
- **Any HIGH-severity gap OR total > 5**: FAIL. Route to plan-relational for fix.
- **Default**: If > 50% relationships lack contracts (plan-audit misalignment), always FAIL.

**Asymmetric definition**: Bidirectional relationship where only one direction has a contract.
Severity: HIGH if uncovered direction involves data mutation; MEDIUM if read-only.

### Relationship Graph Scale
Graph size determines spawn parameters.
- **< 15 edges**: STANDARD analyst (maxTurns:20). Full edge-by-edge consistency check.
- **15-40 edges**: COMPLEX analyst (maxTurns:30). Prioritize cross-boundary and bidirectional edges first.
- **> 40 edges**: COMPLEX analyst (maxTurns:30). Full cross-boundary check, sample intra-module. Flag PARTIAL if < 100% verified.

## Methodology

Five-step verification process: (1) Read plan-relational contracts and build contract inventory.
(2) Read audit-relational L3 and build relationship inventory. (3) Cross-reference each edge for
bidirectional consistency — build consistency matrix. (4) Identify and classify asymmetric,
missing, and orphan gaps by severity. (5) Report integrity verdict with evidence.

**Gap classification**:
- **ASYMMETRIC**: Bidirectional relationship with contract covering only one direction.
- **MISSING**: Relationship with no contract. HIGH if cross-boundary, MEDIUM if intra-module.
- **ORPHAN**: Contract with no matching relationship. MEDIUM severity (plan-audit misalignment).

> Ref: `resources/methodology.md` — analyst DPS, consistency matrix format, gap evidence template, and full step detail
> Ref: `.claude/resources/dps-construction-guide.md` — DPS v5 template fields

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-verify-relational: N` in PT before each invocation.
- Iteration 1: strict mode (FAIL routes back to plan-relational with gap evidence).
- Iteration 2: relaxed mode (proceed with risk flags, document gaps in phase_signals).
- Max iterations: 2.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Audit-relational L3 missing, tool error, or timeout | L0 Retry | Re-invoke same agent, same DPS |
| Consistency matrix incomplete or relationships unverified | L1 Nudge | Respawn with refined DPS targeting refined context |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS |
| Relationship graph stale or plan-audit scope diverged | L3 Restructure | Modify task graph, reassign files |
| Strategic contract model conflict, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

**Edge cases**: (1) Audit-relational L3 unavailable → FAIL `reason: missing_upstream`, route Lead.
(2) Incomplete plan-relational contracts → FAIL `reason: incomplete_plan`, route plan-relational.
(3) Zero relationships in audit graph → PASS `contracts:0, asymmetric:0`, route coordinator.
(4) >50% divergence between plan and audit → FAIL `reason: plan_audit_misalignment`, route Lead.

> Ref: `.claude/resources/failure-escalation-ladder.md` — L0-L4 escalation levels

## Anti-Patterns

- **DO NOT verify contract implementation**: P4 verifies plans, not code. Check existence, not implementability.
- **DO NOT assume unidirectional relationships**: Many apparent one-way imports are bidirectional at runtime. Trust audit-relational L3 classification.
- **DO NOT ignore orphan contracts**: Report all orphans even though they are lower severity than missing contracts.
- **DO NOT treat all asymmetries equally**: Mutation-direction asymmetry is HIGH; read-only asymmetry is MEDIUM.
- **DO NOT create or modify contracts**: Report gaps with evidence. Contract revision is the plan domain's responsibility.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-relational | Interface contracts with producer/consumer/type | L1 YAML: contracts[] with producer, consumer, data_type, direction |
| research-coordinator | Audit-relational L3 relationship graph | L3: edges[] with source, target, type, bidirectional flag |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-coordinator | Integrity verdict with evidence | Always (Wave 4 -> Wave 4.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit-relational L3 | Lead | Which upstream missing |
| Incomplete plan-relational | plan-relational | Contracts lacking required fields |
| Plan-audit misalignment | Lead | Divergence statistics and evidence |
| Analyst exhausted | plan-verify-coordinator | Partial check + unverified relationships |

## Quality Gate
- Every relationship edge in the audit graph checked for contract existence
- Bidirectional relationships verified for contracts in both directions
- All gaps classified by type (ASYMMETRIC/MISSING/ORPHAN) and severity (HIGH/MEDIUM)
- Orphan contracts identified and reported
- Every finding has evidence citing specific relationship edges and contract IDs
- Verdict (PASS/FAIL) with explicit gap counts and severity thresholds

## Output

### L1
```yaml
domain: plan-verify
skill: plan-verify-relational
contract_count: 0
relationship_count: 0
asymmetric_count: 0
missing_count: 0
orphan_count: 0
verdict: PASS|CONDITIONAL_PASS|FAIL
findings:
  - type: asymmetric|missing|orphan
    edge: ""
    severity: HIGH|MEDIUM
    evidence: ""
pt_signal: "metadata.phase_signals.p4_verify_relational"
signal_format: "{STATUS}|contracts:{N}|asymmetric:{N}|ref:tasks/{work_dir}/p4-pv-relational.md"
```

### L2
- Consistency matrix: relationship edge vs contract mapping
- Asymmetric contract analysis with direction and mutation details
- Missing contract list with module boundary classification
- Orphan contract list with plan-audit alignment notes
- Coverage statistics: covered/asymmetric/missing/orphan counts
- Verdict justification with severity threshold comparisons

> Ref: `.claude/resources/output-micro-signal-format.md` — Channel 2-3 signal formats
