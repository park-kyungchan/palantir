---
name: pipeline-resume
description: >-
  Reconstructs pipeline state from Task API after session
  interruption. Categorizes work tasks, determines resume point,
  and re-spawns agents with PT context. Use when session continues
  after interruption and PT exists with metadata.current_phase
  set. Reads from PERMANENT task phase_signals and tasks/{team}/
  output files, plus git branch state. Produces resume context
  for the interrupted skill with phase-by-phase recovery report
  and resume rationale for Lead. Restores DPS v5 context including
  MCP directives and P2P COMM_PROTOCOL state.
  On FAIL (corrupted PT or missing phase artifacts), Lead L4
  escalation with recovery options presented to user.
  DPS needs PT current_phase, tier, phase_signals, and git branch.
  Exclude completed task details and inter-phase output content.
user-invocable: true
disable-model-invocation: false
argument-hint: "[resume-from-phase]"
---

# Pipeline — Resume

## Execution Model
- **TRIVIAL**: Lead-direct. Simple resume from clear interruption point. maxTurns: N/A (Lead inline).
- **STANDARD**: Lead-direct with analyst spawn for state reconstruction. maxTurns: 15.
- **COMPLEX**: Lead-direct with 2 parallel analysts for multi-domain recovery. maxTurns: 20 each.

## Methodology

### 1. Discover Pipeline State
- `TaskList` to see all tasks (including PERMANENT Task)
- Identify PT by `[PERMANENT]` prefix in subject
- Note task statuses: completed, in_progress, pending

### 2. Read PERMANENT Task Context
`TaskGet` on the PERMANENT Task:
- Extract `current_phase` from metadata
- Read project description for pipeline context
- Identify key decisions and architecture choices

### 3. Analyze Task Status
Categorize all work tasks: completed / in-progress / pending. Determine resume point = first non-completed phase.

> Tier-specific recovery procedures (TRIVIAL/STANDARD/COMPLEX phase matrices, COMPLEX dependency graph): read `resources/methodology.md §1`.

### 4. Reconstruct Agent Context
For each in-progress task: read task description for agent assignment, check for partial L1/L2 output, determine if task can continue or needs restart. Default: restart (agent context is lost on interruption).

### 5. Resume Pipeline
- Update PT metadata with resume information
- Re-spawn agents for in-progress tasks with full context (PT + task description + any partial output)
- Resume pipeline flow from the interrupted phase

## Decision Points

### Resume Granularity
- **Phase-level resume**: Resume from beginning of interrupted phase. Default — use when in-progress tasks have no recoverable partial output.
- **Task-level resume**: Resume specific tasks within a phase, preserving completed tasks. Use only when task metadata clearly shows which tasks completed and wrote output to files or PT metadata.

### In-Progress Task Recovery vs Restart
- **Restart task**: No file-persisted partial output. Re-spawn agent with full context from PT + task description. Default and most reliable approach.
- **Continue task**: Task wrote partial results to file or Task metadata before interruption. Provide partial output to re-spawned agent as additional context.

### User-Specified Resume Point Override
- **Accept override**: User provides `[resume-from-phase]` argument that differs from auto-detected point. Trust user intent — they may want to re-run a completed phase.
- **Flag conflict**: User-specified phase is earlier than detected resume point. Accept but warn about potential duplicate work.

### Compaction Detection
Indicators: context shows compaction summary, task details are absent from memory. Action:
1. Do NOT trust recalled task details, phase outcomes, or agent outputs from memory.
2. Perform full TaskList + TaskGet reconstruction as if fresh session.
3. Any "remembered" architecture decisions must be validated against PT metadata or file contents.

> For DPS template, state reconstruction depth, branch validation, and multi-session recovery: read `resources/methodology.md §2-5`.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Task API tool error during state reconstruction | L0 Retry | Re-invoke analyst with same DPS |
| Incomplete reconstruction output or off-direction | L1 Nudge | SendMessage with targeted reconstruction context |
| Analyst exhausted turns or contradictions unresolvable | L2 Respawn | Kill → fresh analyst with deep reconstruction DPS |
| Corrupted PT or missing phase artifacts | L4 Escalate | AskUserQuestion with recovery options |

### No PERMANENT Task Found
- **Cause**: PT creation skipped, failed, or PT was completed/deleted.
- **Action**: Report `status: no_pt_found`. Route to task-management to create a new PT from available context (git log, working directory state, user description).

### Task Status Contradictions
- **Cause**: Tasks claim same phase but show conflicting statuses, or dependency chain is broken.
- **Action**: Trust most conservative status. If any task in a phase shows failed, treat phase as incomplete. Report contradictions in L2 output.

### All Tasks Show Completed But Pipeline Not Delivered
- **Cause**: Session interrupted between last phase completion and delivery invocation.
- **Action**: Set resume point to P8 (delivery). All preceding work is done — route to delivery-pipeline.

> Verbose sub-cases (PT Metadata Missing, Branch Mismatch, Stale Work Tasks, PT Phase Ahead): read `resources/methodology.md §6`.

## Anti-Patterns

### DO NOT: Resume Without Reading PT First
Always reconstruct state from Task API before taking any action. Memory, git history, or file timestamps alone miss critical pipeline context (tier, decisions, dependencies).

### DO NOT: Assume Agent Context Survives Session Interruption
Agent context is lost on interruption. Every re-spawned agent must receive full context via its delegation prompt. Never instruct an agent to "continue where you left off" without providing complete context.

### DO NOT: Skip Failed Tasks and Resume Later Phases
If a task in P3 failed, do not skip to P5. Pipeline phases have dependencies — later phases depend on earlier outputs. Resume from the failed phase.

### DO NOT: Trust Lead's Memory Over Task API
After compaction, Lead may have inaccurate memories. Task API (TaskList, TaskGet) provides ground truth. If Lead "remembers" P3 completed but TaskGet shows in-progress, trust the Task API.

> Secondary anti-patterns (auto-resume without awareness, duplicate task creation, parallel→sequential serialization): read `resources/methodology.md §8`.

## Phase-Aware Execution
Runs in P2+ Team mode only:
- **Communication**: Four-Channel Protocol — Ch2 (disk file) + Ch3 (micro-signal to Lead) + Ch4 (P2P to downstream consumers).
- **Task tracking**: Update task status via TaskUpdate after completion.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (User invocation) | Resume request with optional phase override | `$ARGUMENTS` text: phase name or empty |
| (Session start) | Lead detects incomplete pipeline state | Implicit: TaskList shows non-completed PT |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (Resumed phase skill) | PT context + task assignments | Resume point determines which phase skill to invoke |
| delivery-pipeline | All tasks completed, delivery pending | All work tasks completed but PT not DELIVERED |
| task-management | PT update with resume metadata | Always (update PT current_phase to resume point) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| No PT found | task-management | Request to create PT from available context |
| Unresolvable state contradictions | (User) | Contradiction report for manual resolution |
| Phase dependency broken | (Earliest failed phase skill) | Failed task details for re-execution |

> Full State Reconstruction Checklist (12-item ordered checklist for every resume): read `resources/methodology.md §7`.

## Quality Gate
- PERMANENT Task found and context extracted
- All task statuses accurately determined
- Resume point identified with clear rationale
- Git branch state validated (see `resources/methodology.md §4` for branch checks)
- No task status contradictions (or contradictions explicitly resolved)
- Agents re-spawned with sufficient context to continue
- User informed of resume strategy before execution begins

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Output

### L1
```yaml
domain: cross-cutting
skill: pipeline-resume
last_completed_phase: ""
resume_phase: ""
total_tasks: 0
completed_tasks: 0
in_progress_tasks: 0
pending_tasks: 0
pt_signal: "metadata.phase_signals.cross-cutting"
signal_format: "{STATUS}|resume:{phase}|tasks:{completed}/{total}|ref:tasks/{team}/pipeline-resume.md"
```

### L2
- Task-based recovery summary
- Pipeline state reconstruction from PT metadata
- Resume point with rationale
