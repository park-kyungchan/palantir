---
name: plan-relational
description: >-
  Defines per-task interface contracts bidirectionally across task
  boundaries. Verifies producer-consumer consistency. Parallel
  with plan-static, plan-behavioral, and plan-impact. Use after
  research-coordinator complete. Reads from research-coordinator
  audit-relational L3 relationship graph via $ARGUMENTS and
  design-interface API contracts. Produces contract registry with
  gap counts and per-task contracts for plan-verify-relational.
user-invocable: false
disable-model-invocation: false
---

# Plan — Relational Contracts

## Execution Model
- **TRIVIAL**: Lead-direct. 1-2 task boundaries with simple file-level contracts. No formal schema needed.
- **STANDARD**: Spawn analyst. Systematic contract specification across 3-8 task boundaries with type definitions.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep cross-module contract analysis across 9+ boundaries with bidirectional verification.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Decision Points

### Contract Formality Level
When deciding contract specification depth per task boundary.
- **Path-only**: If TRIVIAL tier (≤ 2 files). Simple file-level references sufficient.
- **Typed**: If STANDARD tier (3-8 files). Include type definitions and required fields.
- **Full schema**: If COMPLEX tier (9+ files). Complete interface with validation rules and edge cases.

### Design-Interface Gap Handling
When audit relationships have no matching design-interface contract.
- **Design available**: Cross-reference and refine. Use design contract as authority, audit as ground truth.
- **Design missing**: Define minimal contract from audit relationship alone. Flag as `unverified: true`.
- **Design contradicts audit**: Flag inconsistency. Route to design-interface for reconciliation.

## Methodology

### 1. Read Audit-Relational L3 and Design-Interface Contracts
Load two inputs:
- **Audit-relational L3** (via `$ARGUMENTS`): Contains relationship graph between files (imports, exports, shared types, event flows, data passing patterns)
- **Design-interface contracts** (from P1): API-level contracts defined during design phase

Cross-reference audit relationships against design contracts:
- Relationships WITH matching design contracts: refine and formalize at task level
- Relationships WITHOUT design contracts: flag as design gaps, define minimal contracts
- Design contracts WITHOUT matching relationships: flag as potentially stale or speculative

Validate both inputs exist. If audit-relational L3 is absent, route to Failure Handling.

### 2. Define Per-Task INPUT/OUTPUT Contracts
For each task boundary identified in the relationship graph, define:

**Producer contract (OUTPUT):**
- What the task produces (file, data structure, export, event)
- Exact format specification (types, fields, schema)
- Location (file path, export name, event channel)
- Guarantees (non-null fields, valid ranges, completeness)

**Consumer contract (INPUT):**
- What the task expects to receive
- Required fields and their types
- Optional fields with defaults
- Error handling when contract is violated

Contract formality levels (match to tier):
| Tier | Formality | Example |
|------|-----------|---------|
| TRIVIAL | Path-only | "Task A creates `src/auth.ts`, Task B imports from it" |
| STANDARD | Typed | "Task A exports `UserModel {id: string, name: string}`, Task B requires `UserModel.id`" |
| COMPLEX | Full schema | Complete interface with validation rules, edge cases, versioning |

### 3. Verify Bidirectional Consistency
For every contract, verify that producer and consumer agree:
- **Type match**: Producer output type matches consumer expected input type
- **Field coverage**: Consumer required fields are all present in producer output
- **Naming consistency**: Both sides use the same identifier names (no aliasing mismatches)
- **Timing**: Producer completes before consumer needs the data (dependency ordering)

Consistency check matrix:
| Check | Pass Condition | Fail Action |
|-------|---------------|-------------|
| Type match | Producer type assignable to consumer type | Flag as incompatible contract |
| Field coverage | All consumer required fields in producer output | Flag missing fields |
| Naming | Same identifiers on both sides | Flag naming mismatch |
| Timing | Producer task precedes consumer in dependency chain | Flag ordering violation |

Record all failures. A single bidirectional inconsistency is a blocking finding.

### 4. Specify Data Formats and Validation Rules
For each contract, define validation rules that execution agents can use:
- **Structural validation**: JSON schema, TypeScript interface, or equivalent
- **Semantic validation**: Business rules (e.g., "user.email must be valid format")
- **Boundary validation**: Min/max values, string length limits, array size bounds
- **Error contract**: What happens when validation fails (throw, default, log)

Validation rule template:
```
Contract: {producer_task} -> {consumer_task}
Validation:
  structural: {type/schema definition}
  semantic: {business rule list}
  boundary: {min/max/length constraints}
  on_violation: throw|default:{value}|log_and_continue
```

### 5. Output Interface Contract Specification
Produce the complete contract registry:
- All per-task INPUT/OUTPUT contracts
- Bidirectional consistency results
- Validation rules per contract
- Gap analysis: relationships without contracts, contracts without relationships
- Coverage metrics: (relationships with contracts / total relationships) * 100

**DPS -- Analyst Spawn Template (COMPLEX):**
- **Context**: Paste audit-relational L3 content (relationship graph, shared types, data flows). Paste design-interface L1 (API contracts). Include pipeline tier and total relationship count.
- **Task**: "For each relationship in the audit graph: define producer OUTPUT contract and consumer INPUT contract. Verify bidirectional consistency (type, field, naming, timing). Specify validation rules per contract. Flag gaps where audit relationships have no design contract. Calculate coverage metric."
- **Constraints**: analyst agent. Read-only (Glob/Grep/Read only). No file modifications. maxTurns: 20. Cross-reference audit and design artifacts.
- **Expected Output**: L1 YAML with contract_count, gap_count, consistency_score, coverage_percent, contracts[]. L2 per-task contracts with validation rules and gap analysis.
- **Delivery**: Write full result to `/tmp/pipeline/p3-plan-relational.md`. Send micro-signal to Lead: `PASS|contracts:{N}|gaps:{N}|ref:/tmp/pipeline/p3-plan-relational.md`.

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. 1-2 task boundaries. Path-only contracts (file references). No formal validation rules needed.
**STANDARD**: Spawn analyst (maxTurns: 15). Typed contracts for 3-8 boundaries. Type + field consistency checks. Skip edge-case validation.
**COMPLEX**: Full DPS above. Full schema contracts across 9+ boundaries with bidirectional verification and validation rules.

## Failure Handling
| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Missing audit-relational L3 input | CRITICAL | research-coordinator | Yes | Cannot define contracts without relationship graph. Request re-run. |
| Missing design-interface contracts | MEDIUM | Complete with gaps | No | Define minimal contracts from audit relationships alone. Flag as unverified. |
| Bidirectional inconsistency found | HIGH | Self (re-analyze) | No | Document inconsistency. If design-sourced: route to design-interface. If audit-sourced: accept audit as ground truth. |
| No relationships in audit (isolated files) | LOW | Complete normally | No | No contracts needed for isolated files. `contract_count: 0`. |

## Anti-Patterns

### DO NOT: Define Contracts Without Audit Evidence
Every contract must trace back to a relationship in the audit-relational L3. Speculative contracts (based on assumed relationships) create false dependencies and mislead execution agents.

### DO NOT: Ignore Design-Interface Contracts
Design-interface contracts from P1 are the architectural intent. Audit relationships are the codebase reality. Both must be reconciled. Ignoring design contracts produces plans that drift from architecture.

### DO NOT: Create One-Directional Contracts
Every contract must define BOTH producer output AND consumer input. A contract that only specifies "Task A produces X" without specifying "Task B expects X with fields Y, Z" is incomplete and unverifiable.

### DO NOT: Over-Specify Internal Task Contracts
For files within the same task (same agent context), formal contracts are unnecessary overhead. Only specify contracts at cross-task boundaries where different agents handle producer and consumer.

### DO NOT: Skip Validation Rules
Contracts without validation rules are aspirational, not enforceable. Every contract must include at least structural validation (type match) to be useful during execution review.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-coordinator | audit-relational L3 file path | `$ARGUMENTS`: file path to L3 with relationship graph |
| design-interface | API contracts from P1 design | L1 YAML: interfaces[], L2: contract specifications |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-relational | Interface contract specification | Always (PASS or partial) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit input | research-coordinator | Which L3 file is missing |
| Design contract inconsistency | design-interface | Mismatch details between audit and design |

## Quality Gate
- Every audit relationship has a corresponding contract (or documented exclusion)
- All contracts are bidirectional (producer OUTPUT + consumer INPUT defined)
- Bidirectional consistency verified (type, field, naming, timing)
- Validation rules defined for all cross-task contracts
- Coverage metric calculated: (relationships with contracts / total relationships) * 100

## Output

### L1
```yaml
domain: plan
skill: relational
status: complete|partial
contract_count: 0
gap_count: 0
consistency_score: 0
coverage_percent: 0
contracts:
  - producer: ""
    consumer: ""
    data_type: ""
    validated: true|false
    bidirectional: true|false
```

### L2
- Per-task INPUT/OUTPUT contract specifications
- Bidirectional consistency check results
- Validation rules per contract
- Gap analysis (unmatched relationships and contracts)
