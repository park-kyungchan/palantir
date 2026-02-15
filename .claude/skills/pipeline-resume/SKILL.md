---
name: pipeline-resume
description: |
  [X-Cut·Resume·Recovery] Reconstructs pipeline state from Task API after session interruption.

  Use when: User says /pipeline-resume. Session continuation with incomplete pipeline. PT exists with metadata.current_phase set.

  WHEN: Session continuation after interruption. Previous pipeline active but incomplete. User invokes or Lead detects incomplete state.
  DOMAIN: Cross-cutting (session recovery). Independent of pipeline sequence.

  METHODOLOGY: (1) TaskList to find all tasks including [PERMANENT], (2) TaskGet PT for project context, tier, and current_phase, (3) Categorize work tasks: completed/in-progress/pending/failed, (4) Determine resume point (first non-completed phase), (5) Validate git branch state matches PT expectations, (6) Re-spawn agents with PT context + task descriptions.
  OUTPUT_FORMAT: L1 YAML resume state (phases, task counts), L2 recovery report with resume rationale.
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
Use Task API to reconstruct state:
- `TaskList` to see all tasks (including PERMANENT Task)
- Identify PT by `[PERMANENT]` prefix in subject
- Note task statuses: completed, in_progress, pending

### 2. Read PERMANENT Task Context
`TaskGet` on the PERMANENT Task:
- Extract `current_phase` from metadata
- Read project description for pipeline context
- Identify key decisions and architecture choices

### 3. Analyze Task Status
Categorize all work tasks:
- **Completed**: phases that finished successfully
- **In-progress**: phases interrupted mid-execution
- **Pending**: phases not yet started
- Determine resume point = first non-completed phase

#### Tier-Specific Recovery

**TRIVIAL Recovery** (P0->P6->P8):
Only 1-2 work tasks expected. Check if the single execution task completed:
- Completed -> route directly to delivery-pipeline (P8).
- Failed or in-progress -> restart from P6 (execution). Minimal state reconstruction: just PT metadata and the single task description.
- No work tasks exist -> pipeline stalled at P0. Restart from the beginning.

**STANDARD Recovery** (P0->P1->P2->P3->P6->P7->P8):
Multiple tasks across 3-4 phases. Build a phase completion matrix:

| Phase | Tasks | Completed | Failed | Pending |
|-------|-------|-----------|--------|---------|
| P0    | n     | ...       | ...    | ...     |
| P1    | n     | ...       | ...    | ...     |
| ...   | ...   | ...       | ...    | ...     |

Map each phase status from task metadata. Resume from the earliest incomplete phase. If a phase has mixed statuses (some completed, some failed), treat the entire phase as incomplete and restart all tasks in that phase.

**COMPLEX Recovery** (P0->P8, all phases):
Many tasks across all phases. Full state reconstruction required:
1. Build complete dependency graph from Task API (task references, metadata.phase fields).
2. Check for broken dependency chains: a dependent task shows completed but its blocker shows failed. This indicates stale or corrupted state.
3. Resolve contradictions before resuming: trust the most conservative interpretation (if blocker failed, dependent's "completed" status is suspect -- flag for re-verification).
4. For multi-domain phases (e.g., P5 with parallel code + infra tasks), verify all parallel branches before advancing.

### 4. Reconstruct Agent Context
For each in-progress task:
- Read task description for agent assignment
- Check if agents produced partial L1/L2 output
- Determine if task can continue or needs restart

**Recovery Limitation**: In-progress tasks at interruption typically need full restart, not continuation. Partial output is only recoverable if written to files or Task metadata before interruption. For completed tasks, L1/L2 may be in Lead's compacted context or PT metadata.

### 5. Resume Pipeline
Execute recovery:
- Update PT metadata with resume information
- Re-spawn agents for in-progress tasks with full context
- Provide each agent: PT context + task description + any partial output
- Resume pipeline flow from the interrupted phase

## Decision Points

### State Reconstruction Analyst DPS
- **Context**: TaskList output (all tasks with statuses), PT metadata (current_phase, tier, phase_signals), git branch name and status.
- **Task**: "Reconstruct pipeline state: categorize all work tasks by phase and status, identify contradictions, determine resume point, validate git branch matches PT expectations."
- **Constraints**: analyst agent (read-only, no Bash). maxTurns: 15 (STANDARD), 20 (COMPLEX). Do not modify any tasks or files.
- **Expected Output**: L1 YAML with `resume_phase`, `completed_tasks`, `failed_tasks`, `contradictions`. L2 recovery report with phase-by-phase status matrix.
- **Delivery**: SendMessage to Lead: `PASS|resume:{phase}|tasks:{completed}/{total}|ref:/tmp/pipeline/pipeline-resume.md`

#### Analyst Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. No analyst spawn — just TaskList + TaskGet inline.
**STANDARD**: 1 analyst for state reconstruction. maxTurns: 15.
**COMPLEX**: 2 parallel analysts (task state + git state). maxTurns: 20 each.

### Resume Granularity
- **Phase-level resume**: Resume from the beginning of the interrupted phase. Simpler, more reliable. Use when in-progress tasks have no recoverable partial output (typical case after session interruption).
- **Task-level resume**: Resume specific tasks within a phase, preserving completed tasks from the same phase. Use only when task metadata clearly shows which tasks completed and which were interrupted, and completed tasks wrote their output to files or PT metadata.

### In-Progress Task Recovery vs Restart
- **Restart task**: In-progress task has no file-persisted partial output. Agent context is lost on session interruption. Re-spawn agent with full context from PT + task description. This is the default and most reliable approach.
- **Continue task**: In-progress task wrote partial results to a file or Task metadata before interruption. Provide partial output to re-spawned agent as additional context to avoid duplicate work. Only viable when partial output is clearly identifiable.

### State Reconstruction Depth
- **Shallow reconstruction**: Only read PT metadata (current_phase, tier) and task statuses. Sufficient for TRIVIAL/STANDARD tiers where pipeline state is straightforward.
- **Deep reconstruction**: Read PT metadata + all task descriptions + any referenced files. Necessary for COMPLEX tiers with multi-domain dependencies where understanding the full pipeline state requires examining intermediate outputs.

### User-Specified Resume Point Override
- **Accept override**: User provides `[resume-from-phase]` argument that differs from the auto-detected resume point. Trust user intent -- they may want to re-run a completed phase (e.g., re-execute P6 after manual code changes).
- **Flag conflict**: User-specified phase is earlier than detected resume point, meaning completed work would be re-done. Accept the override but warn the user about potential duplicate work in the resume report.

### Compaction Detection
Session was compacted (common scenario for long pipelines). Indicators:
- Lead's context is shorter than expected (system-reminder about compaction present)
- Previous conversation details are summarized rather than verbatim
- Task API still has accurate state -- compaction does not affect Task API data

Action: Rely on Task API as ground truth, not Lead's memory. PT metadata is more reliable than Lead's compacted context. When compaction is detected:
1. Do NOT trust any recalled task details, phase outcomes, or agent outputs from memory.
2. Perform full TaskList + TaskGet reconstruction as if this is a fresh session.
3. Any "remembered" architecture decisions must be validated against PT metadata or file contents.

### Branch State Validation
Before resuming, validate git state matches pipeline expectations:

| Check | Command | Expected |
|-------|---------|----------|
| Current branch | `git branch --show-current` | Same as PT's branch |
| Uncommitted changes | `git status` | Clean or only pipeline-generated changes |
| Branch divergence | `git log origin/main..HEAD` | Expected commits from previous phases |

If branch state does not match PT expectations:
- **Different branch**: Warn user, ask whether to continue on current branch or switch to PT's expected branch. Update PT metadata if user confirms a different branch.
- **Unexpected uncommitted changes**: These may be manual edits made between sessions. Flag for user review before resuming. Manual edits could invalidate completed phase outputs.
- **Missing expected commits**: Previous phase commits may have been lost (force push, reset). Treat affected phases as incomplete regardless of task status.

### Multi-Session Recovery
Pipeline may have been interrupted multiple times. Check PT metadata for `resume_count`:
- **0 or missing**: First resume. Standard recovery -- follow methodology as written.
- **1-2**: Second or third resume. Verify previous resume was successful by checking whether tasks marked completed since last resume actually have file-level evidence of completion (output files exist, commits present). If previous resume failed silently, the task status may be stale.
- **3+**: Pipeline is experiencing repeated interruptions. This signals a systemic issue. Recommend one of:
  - Simplify: drop tier from COMPLEX to STANDARD (fewer phases, less state to track).
  - Diagnose: identify the underlying interruption cause (resource limits, compaction pressure, user availability).
  - Checkpoint: commit partial work more frequently to reduce per-resume reconstruction cost.

## Failure Handling

### No PERMANENT Task Found
- **Cause**: Pipeline was never properly initialized (PT creation skipped or failed), or PT was accidentally completed/deleted.
- **Action**: Report `status: no_pt_found`. Route to task-management to create a new PT with whatever context is available (git log, working directory state, user description). Cannot resume without a PT.

### PT Metadata Missing current_phase
- **Cause**: PT was created but never updated with phase progression (e.g., pipeline crashed during P0 before first phase update).
- **Action**: Infer current phase from task statuses. If no work tasks exist, assume P0. If work tasks exist, derive phase from their `metadata.phase` fields. Update PT with inferred phase before resuming.

### Task Status Contradictions
- **Cause**: Multiple tasks claim the same phase but show conflicting statuses (e.g., one completed, one failed for the same phase). Or task dependency chain is broken (dependent task shows completed but blocker shows failed).
- **Action**: Trust the most conservative status. If any task in a phase shows failed, treat the phase as incomplete. Report contradictions in L2 output for user awareness.

### All Tasks Show Completed But Pipeline Not Delivered
- **Cause**: Pipeline completed execution but delivery-pipeline was never invoked (session interrupted between last phase completion and delivery).
- **Action**: Set resume point to P8 (delivery). All preceding work is done -- simply route to delivery-pipeline with consolidated outputs.

### Branch Mismatch
- **Cause**: Current git branch differs from what PT expects. User may have switched branches between sessions, or compaction lost branch context. PT metadata records the pipeline's working branch.
- **Action**: Display both branches to user (current vs expected). If user confirms current branch is correct, update PT metadata to reflect it. If user wants the original branch, instruct them to switch (`git checkout <branch>`) and re-invoke resume. Do not silently proceed on the wrong branch -- file state divergence causes cascading failures.

### Stale Work Tasks
- **Cause**: Work tasks exist and show "completed", but their assigned files have been modified outside the pipeline (manual edits, other tools, or a different pipeline run). Indicator: file modification time is newer than task completion time, or file content hash differs from what was reviewed.
- **Action**: Flag stale tasks as needing re-verification. Route affected phases through the verify domain before resuming downstream phases. Specifically:
  1. Identify which tasks reference modified files.
  2. Mark those tasks as "stale" in the resume report (not failed, not completed).
  3. Route to appropriate verify-* skills for the affected files before proceeding.
  4. If verify passes, continue. If verify fails, route back to execution for that phase.

### PT Phase Ahead of Actual Progress
- **Cause**: PT `metadata.current_phase` shows P5 but only P0-P2 tasks exist. PT was updated optimistically (phase was set before work completed), or intermediate tasks were deleted or lost.
- **Action**: Trust task evidence over PT metadata. Reset `current_phase` to match the actual highest completed phase based on task statuses. Report the discrepancy in L2 output. If no tasks exist at all but PT shows an advanced phase, treat as a corrupted PT -- reconstruct from git history and file state.

## Anti-Patterns

### DO NOT: Resume Without Reading PT First
Always reconstruct state from the Task API before taking any action. Attempting to resume based on memory, git history, or file timestamps alone misses critical pipeline context (tier, decisions, dependencies).

### DO NOT: Assume Agent Context Survives Session Interruption
Agent context (conversation history, working memory) is lost on session interruption. Every re-spawned agent must receive full context via its delegation prompt. Never instruct an agent to "continue where you left off" without providing the complete context.

### DO NOT: Skip Failed Tasks and Resume Later Phases
If a task in phase P3 failed, do not skip to P5. Pipeline phases have dependencies -- later phases depend on earlier phase outputs. Resume from the failed phase, not around it.

### DO NOT: Auto-Resume Without User Awareness
Always present the reconstructed pipeline state and proposed resume point to the user before taking action. The user may have made manual changes between sessions that affect the resume strategy.

### DO NOT: Re-Create Completed Work Tasks
When resuming, do not create duplicate tasks for work that was already completed. Check task statuses first and only create/restart tasks that are in-progress or pending.

### DO NOT: Trust Lead's Memory Over Task API
After compaction, Lead may have inaccurate or incomplete memories of previous work. Task API (TaskList, TaskGet) provides the ground truth for pipeline state. Always reconstruct state from tasks, not from contextual memory. If Lead "remembers" that P3 completed but TaskGet shows the P3 task as in-progress, trust the Task API. Memory-based shortcuts lead to skipped phases or duplicate work.

### DO NOT: Resume Parallel Tasks Sequentially
If the interrupted phase had parallel tasks (e.g., code and infra in P5, or multiple parallel research tasks in P2), resume them in parallel. Do not accidentally serialize by spawning them one at a time. Check the original orchestration-assign output (stored in PT metadata or task descriptions) for the parallelism strategy. Serializing previously-parallel work wastes time and may introduce ordering dependencies that did not exist in the original plan.

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

## State Reconstruction Checklist

Reference checklist Lead follows for every resume invocation. Execute in order:

```
Resume Checklist:
[ ] TaskList -- retrieve all tasks in the session
[ ] Find [PERMANENT] task by subject prefix
[ ] TaskGet PT -- extract current_phase, tier, branch, references
[ ] Categorize work tasks: completed / in_progress / pending / failed
[ ] Check git branch matches PT expectations
[ ] Check git status for uncommitted changes
[ ] Detect compaction (check if session context was summarized)
[ ] Identify resume point: first non-completed phase
[ ] Check for task status contradictions and resolve
[ ] Build resume context for agents: PT + task descriptions + any partial output
[ ] Present reconstructed state to user before acting
[ ] Update PT metadata: resume_count++, current_phase = resume point
```

If any checklist item fails, route to the corresponding Failure Handling scenario above. Do not skip items -- the order matters because later items depend on earlier ones (e.g., contradiction resolution requires completed task categorization).

## Quality Gate
- PERMANENT Task found and context extracted
- All task statuses accurately determined
- Resume point identified with clear rationale
- Git branch state validated
- No task status contradictions (or contradictions explicitly resolved)
- Agents re-spawned with sufficient context to continue
- User informed of resume strategy before execution begins

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
```

### L2
- Task-based recovery summary
- Pipeline state reconstruction from PT metadata
- Resume point with rationale
