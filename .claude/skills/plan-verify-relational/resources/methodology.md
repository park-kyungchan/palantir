# Plan Verify Relational — Methodology Reference

Detailed execution reference for the analyst spawned by `plan-verify-relational`.
SKILL.md holds routing intelligence; this file holds execution detail.

---

## Analyst Delegation DPS

### Context (D11 priority: cognitive focus > token efficiency)

**INCLUDE**:
- plan-relational L1 interface contracts (contracts[], producer, consumer, data_type, direction)
- research-coordinator audit-relational L3 relationship graph (edges[], source, target, type, bidirectional flag)
- File paths within this agent's ownership boundary

**EXCLUDE**:
- Other verify dimension results (static/behavioral/impact)
- Historical rationale for plan-relational decisions
- Full pipeline state beyond P3-P4
- Rejected contract alternatives

**Budget**: Context field ≤ 30% of teammate effective context

### Task
Cross-reference contract inventory against relationship inventory. Verify bidirectional consistency
for each edge. Identify asymmetric contracts (one-direction only), missing contracts (no coverage),
and orphan contracts (no matching relationship). Classify gaps by severity.

### Constraints
- Analyst agent (Read-only, no Bash)
- maxTurns: 20 (STANDARD) or 30 (COMPLEX)
- Verify only listed relationship edges

### Expected Output
L1 YAML: contract_count, relationship_count, asymmetric_count, missing_count, orphan_count,
verdict, findings[]. L2: consistency matrix with gap analysis.

### Delivery
Write result to `tasks/{team}/p4-pv-relational.md`.
SendMessage to Lead: `PASS|contracts:{N}|asymmetric:{N}|ref:tasks/{team}/p4-pv-relational.md`

---

## Tier-Specific DPS Variations

**TRIVIAL**: Lead-direct. Verify each relationship edge has a contract entry inline. No
bidirectional check needed.

**STANDARD**: Single analyst, maxTurns:20. Full consistency matrix with gap classification.

**COMPLEX**: Single analyst, maxTurns:30. Full matrix + bidirectional asymmetry analysis across
all module boundaries.

---

## Step 1. Read Plan-Relational Interface Contracts

Load plan-relational output to extract:
- Interface contracts: each contract with producer, consumer, data type, and format
- Contract direction: which side defines the contract, which side consumes
- Boundary specifications: module boundaries where contracts apply

Build a **contract inventory**: every contract as a directed edge (producer -> consumer) with
data type.

---

## Step 2. Read Audit-Relational L3 Relationship Graph

Load audit-relational L3 output from research-coordinator:
- Relationship graph: nodes (files/components) and edges (cross-file references)
- Bidirectional chains: pairs where A references B AND B references A
- Relationship types: import, callback, event, config, shared-type

Build a **relationship inventory**: every relationship as a directed edge with type.

---

## Step 3. Cross-Reference Bidirectional Consistency

For each relationship edge in the audit graph, check:
- Does a contract exist for this relationship?
- If the relationship is bidirectional (A<->B), do contracts exist in BOTH directions?
- Does the contract data type match the relationship type?

Build a **consistency matrix**:

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

---

## Step 4. Identify Asymmetric and Missing Contracts

**Asymmetric contracts**: Bidirectional relationships where only one direction has a contract.
- Risk: The uncovered direction may have implicit assumptions that break during implementation.
- Severity: HIGH if the uncovered direction involves data mutation, MEDIUM if read-only.

**Missing contracts**: Relationships in the audit graph with no contract at all.
- Risk: No interface specification means the implementer defines the contract ad-hoc.
- Severity: HIGH if the relationship crosses module boundaries, MEDIUM if within a module.

**Orphan contracts**: Contracts that do not correspond to any relationship in the audit graph.
- Risk: Contract specifies an interface for a relationship that does not exist (phantom contract).
- Severity: MEDIUM (indicates plan-audit misalignment, not necessarily a plan defect).

**Gap evidence template** — record for each gap:
- Relationship edge (source -> target)
- Gap type (ASYMMETRIC, MISSING, ORPHAN)
- Evidence: specific relationship from audit-relational L3
- Severity classification with rationale

---

## Step 5. Report Integrity Verdict

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
