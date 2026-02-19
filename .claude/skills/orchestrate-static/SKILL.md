---
name: orchestrate-static
description: >-
  Assigns task-agent pairs by matching tool requirements to agent
  profiles. Splits multi-capability tasks into single-profile
  sub-tasks. Parallel with orchestrate-behavioral,
  orchestrate-relational, and orchestrate-impact. Use after
  plan-verify-coordinator complete with all PASS. Reads from
  plan-verify-coordinator verified plan L3 via $ARGUMENTS.
  Produces task-agent matrix with splits count and assignment
  rationale for orchestrate-coordinator. Model:sonnet for all spawns. MCP tasks require general-purpose subagent_type. Teammates when P2P coordination needed.
  On FAIL, Lead applies D12 escalation. DPS needs plan-verify-coordinator verified plan L3. Exclude other orchestrate dimension outputs.
user-invocable: false
disable-model-invocation: false
---

# Orchestrate — Static (WHO)

## Execution Model
- **TRIVIAL**: Skip — Lead assigns agent inline from task description.
- **STANDARD**: Spawn 1 analyst (maxTurns:15). Systematic agent-task matching using Agent L1 profiles. Omit confidence scoring.
- **COMPLEX**: Spawn 1 analyst (maxTurns:25). Deep capability analysis with multi-capability task splitting and per-assignment confidence.

## Phase-Aware Execution

Runs in P2+ Team mode only. See `.claude/resources/phase-aware-execution.md` for team mode routing and compaction recovery.

- **Communication**: Four-Channel Protocol (Ch2 disk + Ch3 micro-signal to Lead + Ch4 P2P to consumers).
- **Input**: Read plan-verify-coordinator L3 output directly from `$ARGUMENTS` path.
- **File ownership**: Only modify `tasks/{team}/p5-orch-static.md`. No overlapping edits with parallel agents.

## Decision Points

### Agent Profile Selection
When task tool requirements match multiple agent profiles:
- **Single exact match** (1 profile has all required tools): Assign directly. Confidence: HIGH.
- **Multiple matches** (2+ profiles satisfy requirements): Prefer MORE CAPABLE profile (D > C > B). Confidence: MEDIUM.
- **No single match** (task needs tools from 2+ profiles): Split into sub-tasks. If unsplittable (<2 logical units), escalate to orchestrate-coordinator as architectural blocker.

### Task Split Threshold
When task spans `.claude/` and source files simultaneously:
- **If >=2 independent file groups**: Split into infra-implementer (E) + implementer (D) sub-tasks with dependency edge.
- **If tightly coupled** (<2 separable units): Flag as architectural blocker.

### Confidence Classification
- **HIGH**: Exactly 1 matching profile, all tools covered, clear .claude/ vs source boundary.
- **MEDIUM**: Multiple profiles eligible (selected by priority), OR task description ambiguous.
- **LOW**: Required split, OR agent has >2 unused capabilities (over-provisioned).

## Methodology

### 1. Read Verified Plan
Load plan-verify-coordinator L3 output via `$ARGUMENTS` path. Extract task list with IDs, descriptions, file assignments, dependency graph, and complexity estimates.

Construct DPS for analyst using D11 context filtering. See `resources/methodology.md §DPS Template` for full INCLUDE/EXCLUDE blocks and delivery format.

### 2. Extract Tool Requirements Per Task
For each task, identify required capabilities and apply the decision tree:

1. **Modifies `.claude/` files?** → infra-implementer (E)
2. **Requires shell commands?** (build, test, deploy) → implementer (D)
3. **Requires web access?** (fetch docs, search APIs) → researcher (C)
4. **Read + analyze + write only?** → analyst (B)
5. **Ambiguous?** → Prefer MORE CAPABLE profile (D > C > B > E for general tasks)

### 3. Match Tasks to Agent Profiles
Build assignment matrix: task ID, required tools, agent type, confidence level, file list. For multi-capability tasks, split into sub-tasks each matching a single profile. Add dependency edges between sub-tasks. See `resources/methodology.md §Assignment Matrix Format` for table format and split notation.

For parallelism-optimized splitting beyond tool boundaries, see `resources/methodology.md §Parallelism Splitting`.

### 4. Verify No Capability Mismatches
Cross-check every assignment:
- Agent has ALL tools the task requires (not just some)
- No `.claude/` file assigned to implementer
- No source file assigned to infra-implementer
- No test-requiring task assigned to analyst (no Bash)
- No web-requiring task assigned to non-researcher

### 5. Output Task-Agent Assignment Matrix
Produce matrix with: task ID, agent type, required tools, file list, split tasks with parent task reference, confidence per assignment, summary counts (tasks per agent type, total unique agents needed).

## Failure Handling

See `.claude/resources/failure-escalation-ladder.md` for D12 escalation levels (L0–L4).

| Failure Type | Level | Action |
|---|---|---|
| Plan L3 path empty or file missing | L0 Retry | Re-invoke after plan-verify-coordinator re-exports |
| Assignment incomplete or capability gap ambiguous | L1 Nudge | SendMessage with refined capability criteria |
| Agent stuck, context polluted, turns exhausted | L2 Respawn | Kill → fresh analyst with refined DPS |
| Unassignable task that cannot be split | L3 Restructure | Route to orchestrate-coordinator as architectural blocker |
| 3+ L2 failures or scope beyond defined agent profiles | L4 Escalate | AskUserQuestion with situation + options |

For failure sub-case detail (plan missing, unassignable, ambiguous match), see `resources/methodology.md §Failure Sub-Cases`.

## Anti-Patterns

### DO NOT: Read Agent Definition Files
Agent L1 PROFILE tags are already in the analyst's context (auto-loaded). Do NOT Glob/Read `.claude/agents/` — this wastes turns.

### DO NOT: Assign delivery-agent or pt-manager
These are fork agents for specific skills only. Never assign for general tasks.

### DO NOT: Ignore the .claude/ Boundary
Files in `.claude/` MUST go to infra-implementer. Source files MUST go to implementer. Mixing causes execution failures.

### DO NOT: Leave Multi-Capability Tasks Unsplit
A task needing Bash AND WebSearch cannot be assigned to any single agent. Always split.

## Transitions

See `.claude/resources/transitions-template.md` for standard transition format.

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

See `.claude/resources/quality-gate-checklist.md` for standard gates.

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
pt_signal: "metadata.phase_signals.p5_orchestrate_static"
signal_format: "PASS|tasks:{N}|agents:{N}|splits:{N}|ref:tasks/{team}/p5-orch-static.md"
```

### L2
- Task-agent assignment rationale per task (see `resources/methodology.md §Assignment Matrix Format`)
- Decision tree application evidence
- Multi-capability task split documentation
- Agent type distribution summary
