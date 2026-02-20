# Validate Impact — Methodology Reference

> Skill-local resource for validate-impact. Contains analyst DPS templates, containment matrix format, scope delta format, and gap classification rubric. Read when SKILL.md directs here.

## Analyst DPS Template

### P4 — Containment Analysis

```
PHASE_CONTEXT: P4

INCLUDE:
  - plan-impact L1 execution sequence: phases[], checkpoints[], rollback_boundaries[]
  - research-coordinator audit-impact L3 propagation paths: paths[], origin, chain[], severity, depth
  - File paths within ownership boundary

EXCLUDE:
  - Other validate-* axis results (syntactic/semantic/behavioral/consumer/relational)
  - Historical rationale for plan-impact decisions
  - Full pipeline state beyond P3–P4
  - Rejected sequencing alternatives

Budget: Context field ≤ 30% of subagent effective context
```

**Task**: Map each propagation path to intercepting checkpoints. Verify checkpoint position (before terminal node) and criteria match (tests for specific propagation type). Classify gaps as UNMITIGATED, LATE, INSUFFICIENT, or CIRCULAR. Flag circular paths requiring dual checkpoints.

### P7 — Scope Analysis

```
PHASE_CONTEXT: P7

INCLUDE:
  - plan-impact output: planned file list, module scope, HIGH-impact node list
  - git diff output: all files changed during P6 execution

EXCLUDE:
  - Propagation path details (P4 artifact — not P7 scope)
  - Checkpoint analysis (P4 only)
  - Other validate-* axis results

Budget: Context field ≤ 20% of subagent effective context
```

**Task**: Compare planned file scope against execution diff. Compute delta percentage. Enumerate unplanned changes with their impact tier. Classify SCOPE_CREEP (quantity variance) and SCOPE_DRIFT (unplanned files). Report verdict with full delta table.

### Tier-Specific DPS Variations

| Tier | Mode | maxTurns | P4 Scope | P7 Scope |
|------|------|----------|----------|----------|
| TRIVIAL | Lead-direct inline | — | Each path has checkpoint; skip criteria validation | Count files in diff vs estimate |
| STANDARD | Single analyst | 20 | Full containment matrix with position + criteria validation | Systematic file-by-file comparison |
| COMPLEX | Single analyst | 30 | Full matrix + cascade simulation + circular path detection | Module-level analysis + drift pattern identification |

> See `.claude/resources/dps-construction-guide.md` for full DPS v5 field structure.

---

## Containment Matrix Format (P4)

| Propagation Path | Severity | Depth | Intercepting Checkpoint | Position Valid? | Criteria Match? | Status |
|-----------------|----------|-------|------------------------|----------------|----------------|--------|
| auth.ts → session.ts → api.ts | HIGH | 2 | CP-1 (after auth phase) | Yes | Yes | CONTAINED |
| config.json → *.ts (broadcast) | HIGH | 1 | CP-2 (after config phase) | Yes | Partial | PARTIAL |
| util.ts → db.ts → cache.ts | MEDIUM | 2 | — | — | — | UNMITIGATED |

**Status Definitions**:
- **CONTAINED**: Checkpoint exists, positioned before terminal node, criteria match propagation type.
- **PARTIAL**: Checkpoint correctly positioned but criteria do not fully cover propagation scope.
- **UNMITIGATED**: No checkpoint intercepts this path.

---

## Scope Delta Format (P7)

| File | Planned? | Changed? | Impact Tier | Classification |
|------|----------|----------|-------------|----------------|
| src/auth.ts | Yes | Yes | HIGH | In-scope |
| src/utils/helper.ts | No | Yes | MEDIUM | SCOPE_DRIFT |
| src/api/router.ts | Yes | No | HIGH | Uncovered planned |

**Summary Row**: Total planned: {N} | Total changed: {N} | Delta: {pct}% | Unplanned HIGH-impact: {N}

---

## Gap Classification Rubric (P4)

### UNMITIGATED
No intercepting checkpoint on the propagation path.
- Risk: Changes propagate unchecked through the dependency chain.
- Severity: Inherits path severity from audit-impact L3.

### LATE
Checkpoint appears AFTER the path terminal node.
- Risk: Propagation damage already done when checkpoint runs.
- Severity: HIGH if path is HIGH; MEDIUM otherwise.
- Record recommended checkpoint position (which phase to move to).

### INSUFFICIENT
Checkpoint intercepts the path but does not test for the specific propagation type.
- Risk: Checkpoint passes even when propagation has occurred unchecked.
- Severity: MEDIUM (checkpoint exists but ineffective for this path type).

### CIRCULAR (special case)
Propagation path forms a cycle (A → B → C → A).
- Severity: Always HIGH.
- Requirement: TWO checkpoints — one at entry, one at re-entry.
- Verdict impact: FAIL if no checkpoint covers both entry and re-entry points.
