---
name: orchestrate-static
description: |
  [P4·Orchestrate·Static] Assigns task-agent pairs by matching tool requirements to agent profiles. Splits multi-capability tasks into single-profile sub-tasks. Parallel with 3 other orchestrate skills.

  WHEN: After plan-verify-coordinator complete (all PASS). Parallel with orchestrate-behavioral/relational/impact.
  DOMAIN: orchestrate (skill 1 of 5).
  INPUT_FROM: plan-verify-coordinator (verified plan L3 via $ARGUMENTS).
  OUTPUT_TO: orchestrate-coordinator (task-agent matrix with splits count, rationale per assignment).

  METHODOLOGY: (1) Profile-match tasks to agents (B/C/D/E), (2) Identify multi-capability tasks, (3) Split into single-profile sub-tasks, (4) Verify no agent overload, (5) Document assignment rationale.
  OUTPUT_FORMAT: L1 YAML (task-agent matrix with splits count), L2 rationale per assignment.
user-invocable: false
disable-model-invocation: false
---

# Orchestrate — Static (WHO)

## Execution Model
- **TRIVIAL**: Skip (orchestration simplified for trivial tiers).
- **STANDARD**: Spawn 1 analyst. Systematic agent-task matching using Agent L1 profiles.
- **COMPLEX**: Spawn 1 analyst with maxTurns:25. Deep capability analysis with multi-capability task splitting.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Decision Points

### Agent Profile Selection
When task tool requirements match multiple agent profiles:
- **Single exact match** (1 profile has all required tools): Assign directly. Confidence: HIGH.
- **Multiple matches** (2+ profiles satisfy requirements): Prefer MORE CAPABLE profile (D > C > B). Confidence: MEDIUM.
- **No single match** (task needs tools from 2+ profiles): Split into sub-tasks. If unsplittable (< 2 logical units), escalate to orchestrate-coordinator as architectural blocker.

### Task Split Threshold
When task spans `.claude/` and source files simultaneously:
- **If >= 2 independent file groups**: Split into infra-implementer (E) + implementer (D) sub-tasks with dependency edge.
- **If files are tightly coupled** (< 2 separable units): Flag as architectural blocker — single agent cannot safely cross the boundary.

### Confidence Classification
- **HIGH**: Exactly 1 matching profile, all tools covered, clear .claude/ vs source boundary.
- **MEDIUM**: Multiple profiles could work, selected by priority rule, OR task description ambiguous.
- **LOW**: Required split, OR agent has > 2 unused capabilities (over-provisioned).

## Methodology

### 1. Read Verified Plan
Load plan-verify-coordinator L3 output via `$ARGUMENTS` path. Extract:
- Task list with IDs, descriptions, file assignments
- Dependency graph between tasks
- Complexity estimates per task

For STANDARD/COMPLEX tiers, construct the delegation prompt for the analyst with:
- **Context**: Paste verified plan L3 content. Include Agent profile reference: analyst=B(Read,Glob,Grep,Write), researcher=C(+WebSearch,WebFetch,context7,tavily), implementer=D(+Edit,Bash), infra-implementer=E(+Edit,Write for .claude/). Include delivery-agent=F and pt-manager=G as fork-only (not assignable).
- **Task**: "For each task: identify tool requirements, match to best agent profile, verify no capability gaps. Handle multi-capability tasks by splitting. Produce task-agent assignment matrix."
- **Constraints**: Read-only analysis. No modifications. Use Agent L1 PROFILE tags for matching. Flag ambiguous matches.
- **Expected Output**: L1 YAML task-agent matrix. L2 rationale per assignment with capability evidence.
- **Delivery**: Write full result to `/tmp/pipeline/p5-orch-static.md`. Send micro-signal to Lead via SendMessage: `PASS|tasks:{N}|agents:{N}|ref:/tmp/pipeline/p5-orch-static.md`.

#### Step 1 Tier-Specific DPS Variations
**TRIVIAL**: Skip — Lead assigns agent inline from task description (typically 1 implementer or 1 infra-implementer).
**STANDARD**: Single DPS to analyst. maxTurns:15. Simplified matching without multi-capability splitting. Omit confidence scoring.
**COMPLEX**: Full DPS as above. maxTurns:25. Deep capability analysis with multi-capability task splitting and per-assignment confidence.

### 2. Extract Tool Requirements Per Task
For each task, identify required capabilities:
- **File modification**: Which files? `.claude/` files need infra-implementer (E), source files need implementer (D).
- **Shell execution**: Tasks needing `npm test`, `pytest`, build commands require Bash (implementer D only).
- **Web access**: External doc lookup, API validation require WebSearch/WebFetch (researcher C only).
- **Read-only analysis**: Review, audit, planning tasks need Read+Glob+Grep (analyst B sufficient).

#### Agent Selection Decision Tree
For each task, check requirements in priority order:
1. **Modifies `.claude/` files?** -> infra-implementer (E)
2. **Requires shell commands?** (build, test, deploy) -> implementer (D)
3. **Requires web access?** (fetch docs, search APIs) -> researcher (C)
4. **Read + analyze + write only?** -> analyst (B)
5. **Ambiguous?** -> Prefer MORE CAPABLE profile (D > C > B > E for general tasks)

### 3. Match Tasks to Agent Profiles
Build assignment matrix:

| Task ID | Description | Required Tools | Agent Type | Confidence |
|---------|-------------|---------------|------------|------------|
| T1 | ... | Edit, Bash | implementer | HIGH |
| T2 | ... | Edit, Write (.claude/) | infra-implementer | HIGH |

#### Multi-Capability Task Handling
When a task needs capabilities from multiple agent profiles:
- **Split the task**: Create sub-tasks, each matching a single agent profile
- **Add dependency edge**: Consumer sub-task depends on producer sub-task
- **Document the split**: Include original task ID and split rationale
- **Never assign multi-capability tasks to a single agent**

### 4. Verify No Capability Mismatches
Cross-check every assignment:
- Agent has ALL tools the task requires (not just some)
- No `.claude/` file assigned to implementer
- No source file assigned to infra-implementer
- No test-requiring task assigned to analyst (no Bash)
- No web-requiring task assigned to non-researcher

### 5. Output Task-Agent Assignment Matrix
Produce matrix with:
- Task ID, agent type, required tools, file list
- Split tasks noted with parent task reference
- Confidence level per assignment (HIGH/MEDIUM/LOW)
- Summary counts: tasks per agent type, total unique agents needed

## Failure Handling

### Verified Plan Data Missing
- **Cause**: $ARGUMENTS path is empty or L3 file not found
- **Action**: Report FAIL. Signal: `FAIL|reason:plan-L3-missing|ref:/tmp/pipeline/p5-orch-static.md`
- **Route**: Back to plan-verify-coordinator for re-export

### Unassignable Task (No Agent Match)
- **Cause**: Task requires capabilities not in any single agent profile
- **Action**: Split into sub-tasks. If unsplittable, flag as architectural blocker.
- **Route**: If blocker, report to orchestrate-coordinator for escalation

### Ambiguous Agent Match
- **Cause**: Task could match 2+ agent types equally
- **Action**: Apply decision tree priority. Document alternative in L2. Set confidence MEDIUM.

## Anti-Patterns

### DO NOT: Read Agent Definition Files
Agent L1 PROFILE tags are already in the analyst's context (auto-loaded). Do NOT Glob/Read `.claude/agents/` -- this wastes turns.

### DO NOT: Assign delivery-agent or pt-manager
These are fork agents for specific skills only. Never assign for general tasks.

### DO NOT: Ignore the .claude/ Boundary
Files in `.claude/` MUST go to infra-implementer. Source files MUST go to implementer. Mixing causes execution failures.

### DO NOT: Leave Multi-Capability Tasks Unsplit
A task needing Bash AND WebSearch cannot be assigned to any single agent. Always split.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-verify-coordinator | Verified plan L3 | File path via $ARGUMENTS: task list, dependencies, files |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestrate-coordinator | Task-agent assignment matrix | Always (WHO dimension output) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Plan L3 missing | plan-verify-coordinator | Missing file path |
| Unassignable task (unsplittable) | orchestrate-coordinator | Task details + capability gap |
| All tasks assigned | orchestrate-coordinator | Complete matrix (normal flow) |

## Quality Gate
- Every task assigned to exactly 1 agent type
- Agent has ALL required tools for each assigned task
- No `.claude/` file assigned to implementer
- No source file assigned to infra-implementer
- Multi-capability tasks split with dependency edges
- Confidence documented per assignment

## Output

### L1
```yaml
domain: orchestration
skill: static
dimension: WHO
task_count: 0
agent_types_used: 0
splits: 0
assignments:
  - task_id: ""
    agent_type: ""
    tools_required: []
    files: []
    confidence: HIGH|MEDIUM|LOW
```

### L2
- Task-agent assignment rationale per task
- Decision tree application evidence
- Multi-capability task split documentation
- Agent type distribution summary
