# Plan — Relational Contracts: Methodology Reference

> Loaded on-demand from SKILL.md. Contains contract spec formats, DPS templates, and gap classification rubric.

## Contract Specification Format

### Producer Contract (OUTPUT) Fields
- **What**: file, data structure, export, or event the task produces
- **Format**: exact type or schema definition (TypeScript interface, JSON schema, or equivalent)
- **Location**: file path, export name, or event channel
- **Guarantees**: non-null fields, valid ranges, completeness

### Consumer Contract (INPUT) Fields
- **What**: expected receive (file, data structure, export, event)
- **Required**: field names and types the consumer must receive
- **Optional**: fields with default values when absent
- **Error handling**: behavior when contract is violated (throw, default, log)

### Tier Formality Levels

| Tier | Formality | Example |
|------|-----------|---------|
| TRIVIAL | Path-only | "Task A creates `src/auth.ts`, Task B imports from it" |
| STANDARD | Typed | "Task A exports `UserModel {id: string, name: string}`, Task B requires `UserModel.id`" |
| COMPLEX | Full schema | Complete interface with validation rules, edge cases, versioning |

---

## Gap Classification Rubric

When cross-referencing audit relationships against design-interface contracts:

| Relationship State | Action |
|--------------------|--------|
| Relationship WITH matching design contract | Refine and formalize at task level. Design contract is authority; audit is ground truth. |
| Relationship WITHOUT design contract | Define minimal contract from audit alone. Flag as `unverified: true`. |
| Design contract WITHOUT matching relationship | Flag as potentially stale or speculative. Do not create a contract. |
| Design contradicts audit | Flag inconsistency. Route to design-interface for reconciliation. |

---

## Validation Rule Template

For Step 4 (Specify Data Formats and Validation Rules), use this per-contract format:

```
Contract: {producer_task} -> {consumer_task}
Validation:
  structural: {type/schema definition}
  semantic: {business rule list}
  boundary: {min/max/length constraints}
  on_violation: throw|default:{value}|log_and_continue
```

---

## DPS Templates

### COMPLEX: Analyst Spawn Template

**Context** (D11 priority: cognitive focus > token efficiency):
- INCLUDE:
  - research-coordinator audit-relational L3 from `tasks/{work_dir}/p2-coordinator-audit-relational.md`
  - design-interface API contracts (L1 interfaces[] summary only)
  - Pipeline tier and iteration count from PT
- EXCLUDE:
  - Other plan dimension outputs (unless direct dependency)
  - Full research evidence detail (use L3 summaries only)
  - Pre-design and design conversation history
- Budget: Context field ≤ 30% of subagent effective context

**Task**: "For each relationship in the audit graph: define producer OUTPUT contract and consumer INPUT contract. Verify bidirectional consistency (type, field, naming, timing). Specify validation rules per contract. Flag gaps where audit relationships have no design contract. Calculate coverage metric."

**Constraints**: analyst agent. Read-only (Glob/Grep/Read only). No file modifications. maxTurns: 20. Cross-reference audit and design artifacts.

**Expected Output**: L1 YAML with contract_count, gap_count, consistency_score, coverage_percent, contracts[]. L2 per-task contracts with validation rules and gap analysis.

**Delivery (Two-Channel)**:
- Ch2: Write full result to `tasks/{work_dir}/p3-plan-relational.md`
- Ch3 micro-signal to Lead: `PASS|contracts:{N}|gaps:{N}|ref:tasks/{work_dir}/p3-plan-relational.md`
- file-based output to validate-relational subagent (Deferred Spawn — Lead spawns verifier after all 4 plan dimensions complete): signal sent only if verifier is already active

See `.claude/resources/dps-construction-guide.md` for DPS v5 field order and file-based handoff spec spec.
See `.claude/resources/output-micro-signal-format.md` for channel format and micro-signal examples.

### Tier-Specific Variations

**TRIVIAL**: Lead-direct. 1-2 task boundaries. Path-only contracts (file references). No formal validation rules. Output inline.

**STANDARD**: Spawn analyst (maxTurns: 15). Typed contracts for 3-8 boundaries. Type + field consistency checks. Skip edge-case validation.

**COMPLEX**: Full DPS above. Full schema contracts across 9+ boundaries with bidirectional verification and validation rules.

---

## Producer-Consumer Pairing Algorithm

1. Load audit-relational L3 relationship graph (each entry: source_file → target_file, relationship_type)
2. Group relationships by task boundary: if source and target are in different tasks, this is a contract boundary
3. For each boundary pair (Task-A → Task-B):
   - Task-A = producer; Task-B = consumer
   - If the same file pair appears in both directions, both are producers AND consumers
4. Apply gap classification rubric (above) to cross-reference with design-interface contracts
5. Assign contract formality level based on tier (see Tier Formality Levels table)
6. For each COMPLEX-tier contract, apply validation rule template
7. Verify bidirectionality: confirm consumer required fields are all present in producer output fields
