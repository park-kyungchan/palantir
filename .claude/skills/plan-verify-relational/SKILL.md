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
user-invocable: false
disable-model-invocation: false
---

# Plan Verify — Relational Integrity

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check that each relationship edge has a contract entry. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of interface contracts against relationship graph edges.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep bidirectional consistency check with asymmetry detection across all module boundaries.

Note: P4 validates PLANS (pre-execution). This skill verifies that interface contracts fully and symmetrically cover the relationship graph. It does NOT verify contract implementation correctness.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `tasks/{team}/p4-pv-relational.md`, sends micro-signal: `PASS|contracts:{N}|asymmetric:{N}|ref:tasks/{team}/p4-pv-relational.md`.

## Decision Points

### Integrity Threshold Interpretation
Gap severity determines verdict routing.
- **Zero HIGH-severity gaps AND total gaps <= 2**: PASS. Route to plan-verify-coordinator.
- **Only MEDIUM-severity gaps AND total <= 5**: CONDITIONAL_PASS. Route with risk annotation.
- **Any HIGH-severity gap OR total > 5**: FAIL. Route to plan-relational for fix.
- **Default**: If > 50% relationships lack contracts (plan-audit misalignment), always FAIL regardless of severity.

### Relationship Graph Scale
Graph size determines spawn parameters.
- **< 15 edges**: STANDARD analyst (maxTurns:20). Full edge-by-edge consistency check.
- **15-40 edges**: COMPLEX analyst (maxTurns:30). Prioritize cross-boundary and bidirectional edges first.
- **> 40 edges**: COMPLEX analyst (maxTurns:30). Full cross-boundary check, sample intra-module. Flag PARTIAL if < 100% verified.

## Methodology

### Analyst Delegation DPS
- **Context (D11 priority: cognitive focus > token efficiency)**:
  - INCLUDE: plan-relational L1 interface contracts (contracts[], producer, consumer, data_type, direction); research-coordinator audit-relational L3 relationship graph (edges[], source, target, type, bidirectional flag); file paths within this agent's ownership boundary
  - EXCLUDE: other verify dimension results (static/behavioral/impact); historical rationale for plan-relational decisions; full pipeline state beyond P3-P4; rejected contract alternatives
  - Budget: Context field ≤ 30% of teammate effective context
- **Task**: "Cross-reference contract inventory against relationship inventory. Verify bidirectional consistency for each edge. Identify asymmetric contracts (one-direction only), missing contracts (no coverage), and orphan contracts (no matching relationship). Classify gaps by severity."
- **Constraints**: Analyst agent (Read-only, no Bash). maxTurns:20 (STANDARD) or 30 (COMPLEX). Verify only listed relationship edges.
- **Expected Output**: L1 YAML: contract_count, relationship_count, asymmetric_count, missing_count, orphan_count, verdict, findings[]. L2: consistency matrix with gap analysis.
- **Delivery**: SendMessage to Lead: `PASS|contracts:{N}|asymmetric:{N}|ref:tasks/{team}/p4-pv-relational.md`

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. Verify each relationship edge has a contract entry inline. No bidirectional check needed.
**STANDARD**: Single analyst, maxTurns:20. Full consistency matrix with gap classification.
**COMPLEX**: Single analyst, maxTurns:30. Full matrix + bidirectional asymmetry analysis across all module boundaries.

### 1. Read Plan-Relational Interface Contracts
Load plan-relational output to extract:
- Interface contracts: each contract with producer, consumer, data type, and format
- Contract direction: which side defines the contract, which side consumes
- Boundary specifications: module boundaries where contracts apply

Build a **contract inventory**: every contract as a directed edge (producer -> consumer) with data type.

### 2. Read Audit-Relational L3 Relationship Graph
Load audit-relational L3 output from research-coordinator:
- Relationship graph: nodes (files/components) and edges (cross-file references)
- Bidirectional chains: pairs where A references B AND B references A
- Relationship types: import, callback, event, config, shared-type

Build a **relationship inventory**: every relationship as a directed edge with type.

### 3. Cross-Reference Bidirectional Consistency
For each relationship edge in the audit graph, check:
- Does a contract exist for this relationship?
- If the relationship is bidirectional (A<->B), do contracts exist in BOTH directions?
- Does the contract data type match the relationship type?

Build a consistency matrix:

| Relationship Edge | Direction | Contract Exists? | Data Type Match? | Status |
|------------------|-----------|-----------------|-----------------|--------|
| auth -> db | A->B | Yes (auth reads db) | Yes (query interface) | COVERED |
| db -> auth | B->A | No | -- | ASYMMETRIC |
| api -> cache | A->B | Yes (api invalidates) | Yes (cache key type) | COVERED |
| cache -> api | B->A | Yes (cache returns) | Yes (response type) | COVERED |
| config -> logger | A->B | No | -- | MISSING |

**COVERED**: Contract exists and data type matches.
**ASYMMETRIC**: Bidirectional relationship but contract only covers one direction.
**MISSING**: Relationship exists but no contract at all.

### 4. Identify Asymmetric and Missing Contracts
Two categories of integrity gaps:

**Asymmetric contracts**: Bidirectional relationships where only one direction has a contract.
- Risk: The uncovered direction may have implicit assumptions that break during implementation.
- Severity: HIGH if the uncovered direction involves data mutation, MEDIUM if read-only.

**Missing contracts**: Relationships in the audit graph with no contract at all.
- Risk: No interface specification means the implementer defines the contract ad-hoc.
- Severity: HIGH if the relationship crosses module boundaries, MEDIUM if within a module.

**Orphan contracts**: Contracts that do not correspond to any relationship in the audit graph.
- Risk: Contract specifies an interface for a relationship that does not exist (phantom contract).
- Severity: MEDIUM (indicates plan-audit misalignment, not necessarily a plan defect).

For each gap, record:
- Relationship edge (source -> target)
- Gap type (ASYMMETRIC, MISSING, ORPHAN)
- Evidence: specific relationship from audit-relational L3
- Severity classification with rationale

### 5. Report Integrity Verdict
Produce final verdict with evidence:

**PASS criteria**:
- All bidirectional relationships have contracts in both directions
- All cross-boundary relationships have contracts
- Zero HIGH-severity gaps

**Conditional PASS criteria**:
- Asymmetric gaps exist but only for read-only directions (MEDIUM severity)
- Missing contracts exist but only for intra-module relationships (MEDIUM severity)
- Total gap count <= 2

**FAIL criteria**:
- Any HIGH-severity asymmetric contract (mutation direction uncovered), OR
- Any HIGH-severity missing contract (cross-boundary relationship without interface), OR
- Total gap count > 5 (systematic contract coverage failure)

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-verify-relational: N` in PT before each invocation
- Iteration 1: strict mode (FAIL → return to plan-relational with gap evidence)
- Iteration 2: relaxed mode (proceed with risk flags, document gaps in phase_signals)
- Max iterations: 2

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Audit-relational L3 missing, tool error, or timeout | L0 Retry | Re-invoke same agent, same DPS |
| Consistency matrix incomplete or relationships unverified | L1 Nudge | SendMessage with refined context |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh agent with refined DPS |
| Relationship graph stale or plan-audit scope diverged | L3 Restructure | Modify task graph, reassign files |
| Strategic contract model conflict, 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

### Audit-Relational L3 Not Available
- **Cause**: research-coordinator did not produce audit-relational L3 output.
- **Action**: FAIL with `reason: missing_upstream`. Cannot verify integrity without relationship graph.
- **Route**: Lead for re-routing to research-coordinator.

### Plan-Relational Output Incomplete
- **Cause**: plan-relational produced partial contracts (missing producer/consumer or data types).
- **Action**: FAIL with `reason: incomplete_plan`. Report which contracts lack required fields.
- **Route**: plan-relational for completion.

### No Relationships in Audit Graph
- **Cause**: audit-relational found zero cross-file relationships (fully decoupled components).
- **Action**: PASS with `contracts: 0`, `asymmetric: 0`. No relational verification needed.
- **Route**: plan-verify-coordinator with trivial confirmation.

### Relationship Graph and Contract Set Diverge Significantly
- **Cause**: >50% of relationships have no contracts, or >50% of contracts are orphans.
- **Action**: FAIL with `reason: plan_audit_misalignment`. The plan and audit describe different system structures.
- **Route**: Lead for investigation. May indicate stale audit data or plan based on outdated architecture.

### Analyst Exhausted Turns
- **Cause**: Large relationship graph exceeds analyst budget.
- **Action**: Report partial integrity check with percentage verified. Set `status: PARTIAL`.
- **Route**: plan-verify-coordinator with partial flag and unverified relationship list.

## Anti-Patterns

### DO NOT: Verify Contract Implementation
P4 verifies PLANS, not code. Check that contracts exist for relationships. Do not assess whether contracts are implementable, performant, or correctly typed beyond matching the audit relationship type.

### DO NOT: Assume Unidirectional Relationships
Many relationships that appear one-way in import structure are bidirectional at runtime (callbacks, events, shared state). Trust the audit-relational L3 classification of direction.

### DO NOT: Ignore Orphan Contracts
A contract without a corresponding audit relationship may indicate plan-audit misalignment. Report orphan contracts even though they are lower severity than missing contracts.

### DO NOT: Treat All Asymmetries Equally
An asymmetric contract on a read-only direction is less severe than one on a mutation direction. Classify severity based on the uncovered direction's data flow characteristics.

### DO NOT: Create or Modify Contracts
If integrity gaps exist, REPORT them with evidence. Do not propose new contracts or modify existing ones. Contract revision is the plan domain's responsibility.

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
signal_format: "{STATUS}|contracts:{N}|asymmetric:{N}|ref:tasks/{team}/p4-pv-relational.md"
```

### L2
- Consistency matrix: relationship edge vs contract mapping
- Asymmetric contract analysis with direction and mutation details
- Missing contract list with module boundary classification
- Orphan contract list with plan-audit alignment notes
- Coverage statistics: covered/asymmetric/missing/orphan counts
- Verdict justification with severity threshold comparisons
