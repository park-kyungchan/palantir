# Orchestrate-Static: Methodology Reference

> Loaded on-demand by orchestrate-static agents needing detail beyond SKILL.md L2 summaries.

## Tool-Profile Matrix

| Profile | ID | Tools | Assignable? |
|---------|----|-------|-------------|
| analyst | B | Read, Glob, Grep, Write | Yes |
| researcher | C | +WebSearch, WebFetch, context7, tavily | Yes |
| implementer | D | +Edit, Bash | Yes — source files only |
| infra-implementer | E | +Edit, Write (.claude/ files) | Yes — .claude/ files only |
| delivery-agent | F | fork-only | No — reserved for P8 |
| pt-manager | G | fork-only | No — reserved for PT ops |

**Boundary rule**: `.claude/` files → infra-implementer (E). Source files → implementer (D). Crossing this boundary causes execution failures.

## DPS Template for Task-Agent Assignment

When constructing the DPS for the analyst in Step 1:

**Context field (D11: cognitive focus > token efficiency)**

```
INCLUDE:
  - Verified plan L3 content: task list, dependency graph, file assignments
  - Agent profile reference (condensed from Tool-Profile Matrix above)
  - .claude/ boundary rule

EXCLUDE:
  - Other orchestrate dimension outputs (behavioral, relational, impact)
  - Historical rationale from plan-verify phases
  - Full pipeline state beyond this task's scope

Budget: Context field ≤ 30% of teammate effective context
```

**Task field**: "For each task: identify tool requirements, match to best agent profile, verify no capability gaps. Handle multi-capability tasks by splitting. Produce task-agent assignment matrix."

**Constraints field**: Read-only analysis. No file modifications. Use Agent L1 PROFILE tags for matching. Flag ambiguous matches.

**Delivery field**: Four-Channel output per D17:
- Ch2: Write full result to `tasks/{team}/p5-orch-static.md`
- Ch3: Micro-signal to Lead: `PASS|tasks:{N}|agents:{N}|ref:tasks/{team}/p5-orch-static.md`
- Ch4: P2P to orchestrate-coordinator (if spawned): `READY|path:tasks/{team}/p5-orch-static.md|fields:task_agent_matrix,tool_requirements`

## Assignment Matrix Format

The analyst produces a matrix per task. Each row documents:

| Task ID | Description | Required Tools | Agent Type | Confidence |
|---------|-------------|----------------|------------|------------|
| T1 | Implement API handler | Edit, Bash | implementer | HIGH |
| T2 | Update agent config | Edit, Write (.claude/) | infra-implementer | HIGH |
| T3-a | Read + analyze spec | Read, Glob | analyst | HIGH |
| T3-b | Fetch external docs | WebSearch, WebFetch | researcher | HIGH |

**Split notation**: When T3 is split into T3-a/T3-b, both rows carry `parent_task: T3` and a dependency edge `T3-b blocked_by: T3-a` if applicable.

**Confidence levels**:
- HIGH: Exactly 1 matching profile, all tools covered, clear .claude/ vs source boundary
- MEDIUM: Multiple profiles eligible — selected by priority rule, OR task description ambiguous
- LOW: Required split, OR agent has >2 unused capabilities (over-provisioned)

## Parallelism-Optimized Splitting

Beyond tool-boundary splits, consider splitting for scheduling efficiency:

| Split Trigger | Condition | Action |
|---------------|-----------|--------|
| File count split | Task has >6 files AND files are logically groupable | Split into 2+ sub-tasks of ~3 files each |
| Complexity split | Task estimated HIGH complexity AND has 2+ independent sub-modules | Split by sub-module boundary |
| Dependency chain split | Task is bottleneck in serial chain (from orchestrate-impact feedback) | Split to enable parallel execution of sub-parts |

**DO split when all three conditions hold**:
1. Sub-tasks are independently executable (no inter-dependency within the split)
2. Each sub-task maps to the SAME agent type (otherwise use multi-capability split)
3. Split produces net parallelism gain (saves >= 1 wave)

**DO NOT split when**:
- Task has <4 files (too small to benefit)
- Files are tightly coupled (shared state, circular imports)
- Split would create more coordination overhead than parallelism savings

## Failure Sub-Cases

### Verified Plan Data Missing
- **Cause**: `$ARGUMENTS` path is empty or plan-verify-coordinator L3 file not found
- **Signal**: `FAIL|reason:plan-L3-missing|ref:tasks/{team}/p5-orch-static.md`
- **Route**: Back to plan-verify-coordinator for re-export

### Unassignable Task (No Agent Match)
- **Cause**: Task requires capabilities spanning 2+ agent profiles with no clean split boundary
- **Action**: Attempt split first. If logically unsplittable (shared state, atomic transaction), flag as architectural blocker.
- **Route**: Report to orchestrate-coordinator for escalation with task details + capability gap

### Ambiguous Agent Match
- **Cause**: Task description matches 2+ agent profiles equally (e.g., "update config file" — .claude/ or source?)
- **Action**: Apply decision tree priority order. Document alternative choice in L2. Set confidence MEDIUM.
- **Route**: Continue — confidence MEDIUM is acceptable, will be reviewed at orchestrate-coordinator.
