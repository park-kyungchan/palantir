---
name: plan-verify-static
description: |
  Verifies task coverage against dependency DAG for orphan files and missing edges. Cross-references plan file set against dependency file set. Verdict: PASS (≥95% coverage, zero HIGH orphans), FAIL (<85% or HIGH gaps).

  WHEN: After plan-static complete. Parallel with plan-verify-behavioral/relational/impact.
  CONSUMES: plan-static (task breakdown with file assignments), research-coordinator (audit-static L3 dependency graph).
  PRODUCES: L1 YAML coverage verdict with metrics, L2 coverage matrix with orphan/gap evidence → plan-verify-coordinator.
user-invocable: false
disable-model-invocation: false
---

# Plan Verify — Static Coverage

## Execution Model
- **TRIVIAL**: Lead-direct. Inline count of plan files vs dependency files. If all present, PASS. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of task files against dependency graph nodes.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep node-by-node verification with edge coverage analysis across all modules.

Note: P4 validates PLANS (pre-execution). This skill verifies that the task decomposition structurally covers the dependency landscape. It does NOT verify implementation correctness.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p4-pv-static.md`, sends micro-signal: `PASS|coverage:{pct}|orphans:{N}|ref:/tmp/pipeline/p4-pv-static.md`.

## Decision Points

### Coverage Threshold Interpretation
Coverage percentage determines verdict routing.
- **>= 95% with zero HIGH orphans**: PASS. Route to plan-verify-coordinator.
- **85-94% with only LOW/MEDIUM gaps**: CONDITIONAL_PASS. Route with risk annotation.
- **< 85% or any HIGH orphan/edge**: FAIL. Route failing dimension to plan-static for fix.
- **Default**: If threshold is borderline (84-86%), include explicit evidence justifying the call.

### Dependency Graph Scale
Graph size determines spawn parameters.
- **< 20 nodes**: STANDARD analyst (maxTurns:20). Full node-by-node check feasible.
- **20-50 nodes**: COMPLEX analyst (maxTurns:30). Prioritize HIGH fan-in nodes first.
- **> 50 nodes**: COMPLEX analyst (maxTurns:30). Sample-based verification with full HIGH-node coverage. Flag PARTIAL if < 100% verified.

## Methodology

### Analyst Delegation DPS
- **Context**: Paste plan-static L1 task breakdown (task IDs, file assignments, depends_on[]). Paste research-coordinator audit-static L3 dependency graph (DAG nodes, edges, hotspot metrics).
- **Task**: "Cross-reference plan file set against dependency file set. Identify orphan files (unassigned), missing dependency edges (unsequenced), and partial coverage. Compute coverage percentage and classify all gaps by severity."
- **Constraints**: Analyst agent (Read-only, no Bash). maxTurns:20 (STANDARD) or 30 (COMPLEX). Verify only listed dependency graph nodes.
- **Expected Output**: L1 YAML: coverage_percent, orphan_count, missing_edge_count, verdict, findings[]. L2: coverage matrix with file:line evidence.
- **Delivery**: SendMessage to Lead: `PASS|coverage:{pct}|orphans:{N}|ref:/tmp/pipeline/p4-pv-static.md`

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. Count plan files vs dependency files inline. If all dependency files present, PASS. No matrix needed.
**STANDARD**: Single analyst, maxTurns:20. Full coverage matrix. All orphans listed with fan-in.
**COMPLEX**: Single analyst, maxTurns:30. Full coverage matrix + edge coverage analysis across all module boundaries.

### 1. Read Plan-Static Task Breakdown
Load plan-static output to extract the complete task list:
- Task IDs with file assignments (which files each task owns)
- Dependency chains between tasks (blocks/independent relationships)
- File ownership map: every assigned file and its owning task

Build an inventory of all files referenced by the plan. This is the **plan file set**.

### 2. Read Audit-Static L3 Dependency Graph
Load audit-static L3 output from research-coordinator:
- Dependency DAG: nodes (files) and edges (import/reference relationships)
- Hotspot nodes with fan-in/fan-out metrics
- Edge types and weights

Build an inventory of all files in the dependency graph. This is the **dependency file set**.

### 3. Cross-Reference Coverage
For each file in the dependency file set, check:
- Is it present in the plan file set? (assigned to at least one task)
- If present, does the owning task also cover files it directly depends on?
- If present, are dependency edges between files respected by task ordering?

Build a coverage matrix:

| Dependency File | In Plan? | Owning Task | Dependencies Covered? | Status |
|----------------|----------|-------------|----------------------|--------|
| src/auth.ts | Yes | T1 | Yes (imports in T1 scope) | COVERED |
| src/db.ts | Yes | T2 | Partial (1 of 3 deps) | PARTIAL |
| src/util.ts | No | -- | -- | ORPHAN |

Coverage percentage = (COVERED + PARTIAL files) / (total dependency files) * 100.

### 4. Identify Orphans and Missing Edges
Two categories of gaps:

**Orphan files**: Files in the dependency graph not assigned to any task.
- These are structural gaps: the plan misses files that the codebase depends on.
- Severity: HIGH if the orphan has fan-in > 2 (multiple files depend on it), LOW otherwise.

**Missing dependency edges**: Cases where task A owns file X, task B owns file Y, X depends on Y, but there is no task dependency A->B or B->A in the plan.
- These are ordering gaps: the plan does not sequence tasks according to structural dependencies.
- Severity: HIGH if the edge represents a direct import, MEDIUM if it is a config reference.

For each gap, record:
- File path(s) involved
- Dependency edge (source -> target)
- Evidence: file:line reference from audit-static L3
- Severity classification

### 5. Report Coverage Verdict
Produce final verdict with evidence:

**PASS criteria**:
- Coverage >= 95% (virtually all dependency-graph files covered by tasks)
- Zero HIGH-severity orphan files
- Zero HIGH-severity missing dependency edges

**Conditional PASS criteria**:
- Coverage >= 85% with all gaps being LOW/MEDIUM severity
- Orphan files exist but have fan-in <= 1 (peripheral files)

**FAIL criteria**:
- Coverage < 85%, OR
- Any HIGH-severity orphan file (hub file missing from plan), OR
- Any HIGH-severity missing edge (direct import not reflected in task ordering)

## Failure Handling

### Audit-Static L3 Not Available
- **Cause**: research-coordinator did not produce audit-static L3 output.
- **Action**: FAIL with `reason: missing_upstream`. Cannot verify coverage without dependency graph.
- **Route**: Lead for re-routing to research-coordinator.

### Plan-Static Output Incomplete
- **Cause**: plan-static produced partial task breakdown (missing file assignments).
- **Action**: FAIL with `reason: incomplete_plan`. Report which tasks lack file assignments.
- **Route**: plan-static for completion.

### Dependency Graph is Empty
- **Cause**: audit-static found zero dependencies (possible for single-file projects).
- **Action**: PASS with `coverage: 100`, `orphans: 0`. No structural verification needed.
- **Route**: plan-verify-coordinator with trivial coverage confirmation.

### Analyst Exhausted Turns
- **Cause**: Large dependency graph exceeds analyst budget.
- **Action**: Report partial coverage with percentage of graph verified. Set `status: PARTIAL`.
- **Route**: plan-verify-coordinator with partial flag and unverified node list.

## Anti-Patterns

### DO NOT: Verify Implementation Correctness
P4 verifies PLANS, not code. Check that the plan structurally covers the dependency graph. Do not assess whether the planned changes will correctly implement anything.

### DO NOT: Add Files to the Plan
If orphan files are found, REPORT them. Do not propose task modifications or new tasks. Fixing the plan is the plan domain's responsibility.

### DO NOT: Ignore Low-Fan-In Orphans
Even peripheral orphan files should be reported. They may indicate scope drift or intentional exclusion. Report all orphans, classify by severity, let the coordinator decide.

### DO NOT: Treat Config References as Hard Dependencies
Config file references (JSON path lookups, env var reads) are softer than import dependencies. Classify them as MEDIUM severity, not HIGH.

### DO NOT: Double-Count Partial Coverage
A file that is PARTIAL (some deps covered, some not) counts once toward coverage. Do not count it as both covered and uncovered.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-static | Task breakdown with file assignments | L1 YAML: tasks[] with id, files[], depends_on[]. L2: task descriptions |
| research-coordinator | Audit-static L3 dependency graph | L3: DAG with nodes, edges, hotspots, edge types |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-coordinator | Coverage verdict with evidence | Always (Wave 4 -> Wave 4.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit-static L3 | Lead | Which upstream missing |
| Incomplete plan-static | plan-static | Tasks lacking file assignments |
| Analyst exhausted | plan-verify-coordinator | Partial coverage + unverified nodes |

## Quality Gate
- Every file in the dependency graph checked against the plan file set
- Coverage percentage calculated with clear numerator/denominator
- All orphan files listed with fan-in counts and severity classification
- All missing dependency edges listed with edge type and severity
- Every finding has file:line evidence from audit-static L3
- Verdict (PASS/FAIL) with explicit threshold comparison

## Output

### L1
```yaml
domain: plan-verify
skill: plan-verify-static
coverage_percent: 0
orphan_count: 0
missing_edge_count: 0
verdict: PASS|CONDITIONAL_PASS|FAIL
dependency_files_total: 0
plan_files_total: 0
findings:
  - type: orphan|missing_edge
    file: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
```

### L2
- Coverage matrix: dependency file vs plan task mapping
- Orphan file list with fan-in/fan-out and severity
- Missing dependency edge list with edge type and severity
- Coverage percentage calculation with thresholds
- Verdict justification with evidence citations
