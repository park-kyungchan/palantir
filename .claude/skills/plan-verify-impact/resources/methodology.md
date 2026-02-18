# Plan Verify Impact — Methodology Reference

> Skill-local resource for plan-verify-impact. Contains analyst DPS template, containment matrix format, and gap classification rubric. Read when SKILL.md directs here.

## Analyst DPS Template

### Context (D11 Priority: Cognitive Focus > Token Efficiency)

```
INCLUDE:
  - plan-impact L1 execution sequence: phases[], checkpoints[], rollback_boundaries[]
  - research-coordinator audit-impact L3 propagation paths: paths[], origin, chain[], severity, depth
  - File paths within this agent's ownership boundary

EXCLUDE:
  - Other verify dimension results (static/behavioral/relational)
  - Historical rationale for plan-impact decisions
  - Full pipeline state beyond P3–P4
  - Rejected sequencing alternatives

Budget: Context field ≤ 30% of teammate effective context
```

### Task

Map each propagation path to intercepting checkpoints. Verify checkpoint position (before terminal node) and criteria match (tests for specific propagation type). Classify gaps as UNMITIGATED, LATE, or INSUFFICIENT. Flag circular paths requiring dual checkpoints.

### Constraints

- Agent type: analyst (Read-only, no Bash)
- maxTurns: 20 (STANDARD) or 30 (COMPLEX)
- Scope: verify only the listed propagation paths — no scope expansion

### Expected Output

L1 YAML: `total_paths`, `contained_count`, `unmitigated_count`, `late_checkpoint_count`, `verdict`, `findings[]`
L2 Markdown: containment matrix with path evidence

### Delivery

SendMessage to Lead: `PASS|paths:{N}|unmitigated:{N}|ref:tasks/{team}/p4-pv-impact.md`

### Tier-Specific DPS Variations

| Tier | Mode | maxTurns | Scope |
|------|------|----------|-------|
| TRIVIAL | Lead-direct inline | — | Each path has intercepting checkpoint; no criteria validation |
| STANDARD | Single analyst | 20 | Full containment matrix with position and criteria validation |
| COMPLEX | Single analyst | 30 | Full matrix + cascade simulation + circular path detection |

> See `.claude/resources/dps-construction-guide.md` for full DPS v5 field structure.

---

## Containment Matrix Format

For each propagation path, build this matrix:

| Propagation Path | Severity | Depth | Intercepting Checkpoint | Position Valid? | Criteria Match? | Status |
|-----------------|----------|-------|------------------------|----------------|----------------|--------|
| auth.ts → session.ts → api.ts | HIGH | 2 | CP-1 (after auth phase) | Yes | Yes (auth test) | CONTAINED |
| config.json → *.ts (broadcast) | HIGH | 1 | CP-2 (after config phase) | Yes | Partial (3/5 consumers) | PARTIAL |
| util.ts → db.ts → cache.ts | MEDIUM | 2 | — | — | — | UNMITIGATED |

**Status Definitions:**
- **CONTAINED**: Checkpoint exists, positioned before terminal node, criteria match propagation type.
- **PARTIAL**: Checkpoint exists and is positioned correctly, but criteria do not fully cover the propagation scope.
- **UNMITIGATED**: No checkpoint intercepts this propagation path.

---

## Gap Classification Rubric

Three categories of containment gaps. For each gap, record: path (origin → intermediate → terminal), gap type, severity, evidence (path + checkpoint references).

### UNMITIGATED
Propagation path with no intercepting checkpoint.
- **Risk**: Changes propagate unchecked through the dependency chain during execution.
- **Severity**: Inherits path severity (HIGH/MEDIUM/LOW from audit-impact L3).

### LATE
Checkpoint appears AFTER the propagation path has reached its terminal node.
- **Risk**: By the time the checkpoint runs, propagation damage is already done.
- **Severity**: HIGH if path severity is HIGH; MEDIUM otherwise.
- **Record**: Recommended checkpoint position (which phase it should move to).

### INSUFFICIENT
Checkpoint intercepts the path but does not test for the specific propagation type.
- **Risk**: Checkpoint passes even when propagation has occurred unchecked.
- **Severity**: MEDIUM (checkpoint exists but is ineffective for this path).

### Circular Propagation (special case)
A propagation path forms a cycle (A → B → C → A).
- **Severity**: Always HIGH.
- **Requirement**: TWO checkpoints minimum — one at entry point, one at re-entry point.
- **Verdict impact**: FAIL if no checkpoint covers both entry and re-entry.
