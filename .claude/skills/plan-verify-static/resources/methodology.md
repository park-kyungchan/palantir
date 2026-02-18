# Plan Verify Static — Methodology Reference

> Loaded on-demand by the analyst agent. Contains DPS specification, verification steps, coverage matrix format, and evidence template.

## Analyst Delegation DPS

### Context (D11 priority: cognitive focus > token efficiency)

**INCLUDE:**
- plan-static L1 task breakdown (task IDs, file assignments, depends_on[])
- research-coordinator audit-static L3 dependency graph (DAG nodes, edges, hotspot metrics)
- File paths within this agent's ownership boundary

**EXCLUDE:**
- Other verify dimension results (behavioral/relational/impact)
- Historical rationale for plan-static decisions
- Full pipeline state beyond P3-P4
- Rejected task decomposition alternatives

**Budget:** Context field ≤ 30% of teammate effective context

### Task

"Cross-reference plan file set against dependency file set. Identify orphan files (unassigned), missing dependency edges (unsequenced), and partial coverage. Compute coverage percentage and classify all gaps by severity."

### Constraints

- Agent: analyst (Read-only, no Bash)
- maxTurns: 20 (STANDARD), 30 (COMPLEX)
- Verify only nodes listed in the dependency graph

### Expected Output

L1 YAML: `coverage_percent`, `orphan_count`, `missing_edge_count`, `verdict`, `findings[]`
L2: Coverage matrix with file:line evidence

### Delivery

SendMessage to Lead: `PASS|coverage:{pct}|orphans:{N}|ref:tasks/{team}/p4-pv-static.md`

## Tier-Specific DPS Variations

| Tier | Mode | maxTurns | Matrix | Notes |
|------|------|----------|--------|-------|
| TRIVIAL | Lead-direct | n/a | Not required | Count plan files vs dependency files inline; if all present, PASS |
| STANDARD | Single analyst | 20 | Full coverage matrix with all orphans listed with fan-in | No edge analysis required |
| COMPLEX | Single analyst | 30 | Full coverage matrix + edge coverage analysis across all module boundaries | Prioritize HIGH fan-in nodes |

## Verification Steps

### Step 1: Read Plan-Static Task Breakdown

Load plan-static output to extract the complete task list:
- Task IDs with file assignments (which files each task owns)
- Dependency chains between tasks (blocks/independent relationships)
- File ownership map: every assigned file and its owning task

Build an inventory of all files referenced by the plan. This is the **plan file set**.

### Step 2: Read Audit-Static L3 Dependency Graph

Load audit-static L3 output from research-coordinator:
- Dependency DAG: nodes (files) and edges (import/reference relationships)
- Hotspot nodes with fan-in/fan-out metrics
- Edge types and weights

Build an inventory of all files in the dependency graph. This is the **dependency file set**.

### Step 3: Cross-Reference Coverage

For each file in the dependency file set, check:
- Is it present in the plan file set? (assigned to at least one task)
- If present, does the owning task also cover files it directly depends on?
- If present, are dependency edges between files respected by task ordering?

**Coverage Matrix Format:**

| Dependency File | In Plan? | Owning Task | Dependencies Covered? | Status |
|----------------|----------|-------------|----------------------|--------|
| src/auth.ts | Yes | T1 | Yes (imports in T1 scope) | COVERED |
| src/db.ts | Yes | T2 | Partial (1 of 3 deps) | PARTIAL |
| src/util.ts | No | -- | -- | ORPHAN |

Coverage percentage = (COVERED + PARTIAL files) / (total dependency files) × 100

### Step 4: Identify Orphans and Missing Edges

**Orphan files:** Files in the dependency graph not assigned to any task.
- Structural gaps: the plan misses files that the codebase depends on.
- Severity: HIGH if fan-in > 2 (multiple files depend on it), LOW otherwise.

**Missing dependency edges:** Task A owns file X, Task B owns file Y, X depends on Y, but no task dependency A→B or B→A exists in the plan.
- Ordering gaps: the plan does not sequence tasks according to structural dependencies.
- Severity: HIGH if direct import, MEDIUM if config reference.

**Evidence Template (per gap):**

```
file: {path(s) involved}
edge: {source} -> {target}
evidence: {file:line reference from audit-static L3}
severity: HIGH|MEDIUM|LOW
```

### Step 5: Report Coverage Verdict

**PASS:** Coverage ≥ 95% AND zero HIGH-severity orphan files AND zero HIGH-severity missing edges.

**Conditional PASS:** Coverage ≥ 85% with all gaps LOW/MEDIUM severity AND orphan files have fan-in ≤ 1.

**FAIL:** Coverage < 85%, OR any HIGH-severity orphan file (hub file missing from plan), OR any HIGH-severity missing edge (direct import not reflected in task ordering).

**Borderline (84–86%):** Include explicit evidence justifying the call.

**Graph scale → verification mode:**
- < 20 nodes: full node-by-node check
- 20–50 nodes: prioritize HIGH fan-in nodes first
- > 50 nodes: sample-based with full HIGH-node coverage; set `status: PARTIAL` if < 100% verified
