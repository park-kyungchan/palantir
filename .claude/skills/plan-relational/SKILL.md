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
  On FAIL (HIGH asymmetric gaps), routes back to plan-relational
  with integrity evidence. DPS needs research-coordinator
  audit-relational L3 relationships and design-interface
  contracts. Exclude static, behavioral, and impact data.
user-invocable: false
disable-model-invocation: false
---

# Plan — Relational Contracts

## Execution Model
- **TRIVIAL**: Lead-direct. 1-2 task boundaries with simple file-level contracts. No formal schema needed.
- **STANDARD**: Spawn analyst. Systematic contract specification across 3-8 task boundaries with type definitions.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep cross-module contract analysis across 9+ boundaries with bidirectional verification.

## Phase-Aware Execution

Runs in P2+ Team mode. See `.claude/resources/phase-aware-execution.md` for full protocol.
- **Communication**: Four-Channel Protocol — Ch2 (disk file) + Ch3 (micro-signal to Lead) + Ch4 (P2P to consumers).
- **Task tracking**: Update task status via TaskUpdate after completion.
- **P2P Self-Coordination**: Read upstream outputs from `tasks/{team}/` via $ARGUMENTS. Send P2P signals to downstream consumers.
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

See `resources/methodology.md` for full gap classification rubric.

## Methodology

### 1. Read Audit-Relational L3 and Design-Interface Contracts
Load two inputs via `$ARGUMENTS`:
- **Audit-relational L3**: Relationship graph (imports, exports, shared types, event flows, data passing)
- **Design-interface contracts** (from P1): API-level contracts defined during design phase

Cross-reference: relationships WITH matching contracts → refine; WITHOUT → flag design gap; contracts WITHOUT relationships → flag stale.
Validate both inputs exist. If audit-relational L3 is absent, route to Failure Handling.

### 2. Define Per-Task INPUT/OUTPUT Contracts
For each task boundary in the relationship graph, define producer OUTPUT contract and consumer INPUT contract.
Contract formality matches tier (path-only / typed / full schema).
See `resources/methodology.md` for contract specification format, tier formality table, and producer-consumer pairing algorithm.

### 3. Verify Bidirectional Consistency
For every contract, verify producer and consumer agree:
- **Type match**: Producer output type assignable to consumer input type
- **Field coverage**: All consumer required fields present in producer output
- **Naming consistency**: Same identifier names on both sides (no aliasing mismatches)
- **Timing**: Producer task precedes consumer in dependency chain

Consistency check matrix:
| Check | Pass Condition | Fail Action |
|-------|---------------|-------------|
| Type match | Producer type assignable to consumer type | Flag as incompatible contract |
| Field coverage | All consumer required fields in producer output | Flag missing fields |
| Naming | Same identifiers on both sides | Flag naming mismatch |
| Timing | Producer task precedes consumer | Flag ordering violation |

Record all failures. A single bidirectional inconsistency is a blocking finding.
**FAIL condition**: Any HIGH asymmetric gap (producer defines output with no consumer claim, or consumer requires field not in any producer) triggers FAIL routing back to plan-relational with integrity evidence.

### 4. Specify Data Formats and Validation Rules
For each contract, define structural, semantic, boundary, and error-contract validation rules.
See `resources/methodology.md` for the validation rule template.

### 5. Output Interface Contract Specification
Produce the complete contract registry: all per-task INPUT/OUTPUT contracts, bidirectional consistency results, validation rules, gap analysis, and coverage metric.
**Gap thresholds**: gap_count 0 = PASS; 1-5 = partial; >5 = FAIL (route to research-coordinator).
DPS template (COMPLEX analyst spawn, tier variations, D17 Four-Channel delivery): see `resources/methodology.md`.
See `.claude/resources/dps-construction-guide.md` for DPS v5 field order.
See `.claude/resources/output-micro-signal-format.md` for Ch3/Ch4 signal formats.

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.plan-relational: N` in PT before each invocation
- Iteration 1: strict mode (FAIL → return to research-coordinator with relationship graph gaps)
- Iteration 2: relaxed mode (proceed with documented coverage gaps, flag in phase_signals)
- Max iterations: 2

## Failure Handling

See `.claude/resources/failure-escalation-ladder.md` for L0–L4 level definitions.

| Failure Type | Level | Action |
|---|---|---|
| Tool error or timeout during contract generation | L0 Retry | Re-invoke same agent, same DPS |
| Contract output incomplete or missing bidirectional coverage | L1 Nudge | SendMessage with refined relationship scope constraints |
| Agent stuck on schema analysis or context exhausted | L2 Respawn | Kill agent → fresh analyst with refined DPS |
| Contract boundaries conflict with task structure | L3 Restructure | Modify contract scope, request design-interface clarification |
| Strategic ambiguity on contract formality or 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Missing audit-relational L3 input | CRITICAL | research-coordinator | Yes | Cannot define contracts without relationship graph. Request re-run. |
| Missing design-interface contracts | MEDIUM | Complete with gaps | No | Define minimal contracts from audit alone. Flag as unverified. |
| Bidirectional inconsistency found | HIGH | Self (re-analyze) | No | Document inconsistency. If design-sourced: route to design-interface. |
| No relationships in audit (isolated files) | LOW | Complete normally | No | No contracts needed. `contract_count: 0`. |

## Anti-Patterns

### DO NOT: Define Contracts Without Audit Evidence
Every contract must trace back to a relationship in the audit-relational L3. Speculative contracts create false dependencies.

### DO NOT: Ignore Design-Interface Contracts
Design-interface contracts are the architectural intent. Audit relationships are the codebase reality. Both must be reconciled.

### DO NOT: Create One-Directional Contracts
Every contract must define BOTH producer output AND consumer input. A contract without consumer input spec is incomplete and unverifiable.

### DO NOT: Over-Specify Internal Task Contracts
For files within the same task (same agent context), formal contracts are unnecessary. Only specify at cross-task boundaries.

### DO NOT: Skip Validation Rules
Contracts without validation rules are aspirational, not enforceable. Every contract needs at least structural validation.

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
pt_signal: "metadata.phase_signals.p3_plan_relational"
signal_format: "{STATUS}|contracts:{N}|gaps:{N}|ref:tasks/{team}/p3-plan-relational.md"
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
