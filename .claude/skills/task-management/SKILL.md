---
name: task-management
description: >-
  Manages PT and work task lifecycle via Task API. Heavy ops
  spawn pt-manager agent, light ops Lead-direct. Exactly 1 PT
  per pipeline. Use at any phase: pipeline start for PT creation,
  plan ready for batch tasks, execution for status updates, commit
  done for PT completion. Reads from PERMANENT task tier, phase,
  requirements, and architecture decisions for all pipeline
  operations. Produces PT lifecycle events and work task batches
  consumed by all pipeline skills. ASCII status visualization on
  demand. Subagents self-select via TaskList loop. Cross-session
  sharing via CLAUDE_CODE_TASK_LIST_ID env.
  On FAIL (Task API error or duplicate PT), Lead retries L0 with
  same DPS. On persistent failure (3+ L0 retries), Lead L4
  escalation with pipeline state summary.
  DPS needs PERMANENT task ID, current phase, and operation type.
  Exclude completed task details and cross-phase rationale.
user-invocable: true
disable-model-invocation: false
argument-hint: "[action] [args]"
---

# Task Management

## Execution Model

- **TRIVIAL**: Lead-direct. Single TaskUpdate for PT status change. No agent spawn.
- **STANDARD**: Lead-direct or pt-manager for batch operations. maxTurns: 15.
- **COMPLEX**: pt-manager spawn for full PT lifecycle + batch task creation. maxTurns: 25.
**Operation routing**:
- **Heavy ops** → spawn `pt-manager` (`subagent_type: pt-manager`). Full Task API (TaskCreate + TaskUpdate).
- **Light ops** → Lead executes directly. Single TaskUpdate for status/metadata changes.

## Phase-Aware Execution

This skill runs in any pipeline mode. Coordination:
- **Communication**: Two-channel protocol — Ch2 (disk file) + Ch3 (micro-signal to Lead). Lead receives micro-signal only, not full data.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel subagents.

> D17 Note: use 2-channel protocol (Ch2 output file `tasks/{work_dir}/`, Ch3 micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Methodology

### 1. PT Creation
1. TaskList → verify no existing `[PERMANENT]` task
2. If user intent unclear → AskUserQuestion
3. TaskCreate with subject `[PERMANENT] {feature-name}`, description (user intent + constraints + acceptance criteria), and metadata (type, tier, current_phase, commit_status, references, user_directives)
4. Report PT task ID to Lead

> For PT metadata JSON template: read `resources/methodology.md`

### 2. PT Update (Read-Merge-Write)
1. TaskList → find `[PERMANENT]` task
2. TaskGet → read current description + metadata
3. Merge new information into existing — add to `user_directives[]`, `references[]`, or update `current_phase`
4. TaskUpdate with merged result
5. If description exceeds useful density → move details to file, keep index in description

### 2b. PT Phase Checkpoint (Compaction Recovery)
After each phase completion:
1. TaskGet PT → read current metadata
2. Add compact phase signal: `metadata.phase_signals.{phase} = "{STATUS}|{key_signal}"`
3. Update `metadata.current_phase` to next phase
4. TaskUpdate with merged metadata

This enables compaction recovery: Lead calls `TaskGet(PT)` → reads `phase_signals` → knows entire pipeline history.

> For phase_signals JSON example: read `resources/methodology.md`

### 3. Work Task Batch Creation
1. Read plan output files (plan domain L1/L2)
2. For each planned sub-task: TaskCreate with actionable subject + complete metadata (type, phase, domain, skill, agent, files, priority, parent, problem, improvement)
3. Set `addBlockedBy` for dependency chains; `activeForm`: present-tense Korean description
4. Report task count + dependency graph summary to Lead

> For work task metadata JSON template and dependency patterns: read `resources/methodology.md`

### 4. Real-Time Update Protocol
Subagents update their assigned tasks during execution (in_progress → progress → completed/failed).

> For status update event table: read `resources/methodology.md`

### 5. ASCII Visualization (Korean Output)
1. TaskList → get all tasks; TaskGet for each active/blocked task
2. Group by `metadata.phase` and `metadata.domain`
3. Render pipeline overview, domain progress bars, in-progress/completed/pending/PT-refs sections

> For ASCII visualization template and rendering rules: read `resources/methodology.md`

### 6. PT Completion
1. TaskList → verify all work tasks with `parent: {PT-id}` are `completed`
2. If incomplete tasks remain → report blockers
3. TaskUpdate PT: `metadata.commit_status` → `"committed"`
4. TaskUpdate PT: `status` → `"completed"`

## Decision Points

### Heavy vs Light Operation Routing
- **Heavy ops (pt-manager spawn)**: PT creation, PT update with complex merge, batch work task creation, ASCII visualization. Require multiple Task API calls and complex logic.
- **Light ops (Lead-direct)**: Single TaskUpdate for status change or simple metadata field update. No agent spawn overhead.

### PT-Manager Spawn DPS
- **Context**: PT task ID, current pipeline phase, operation type (create/update/batch/visualize), plan domain output paths if batch creation.
- **Constraints**: Tools: Read, Glob, Grep, Write, TaskCreate, TaskUpdate, TaskGet, TaskList, AskUserQuestion. No Edit/Bash.
- **Delivery**: Write to output file + micro-signal to Lead: `PASS|action:{type}|tasks:{N}|ref:tasks/{work_dir}/task-management.md`

**Tier-Specific DPS Variations**:
- **TRIVIAL**: Lead-direct. Single TaskUpdate inline. No pt-manager spawn.
- **STANDARD**: pt-manager spawn for batch creation or complex PT update. maxTurns: 15.
- **COMPLEX**: pt-manager spawn with full lifecycle management + visualization. maxTurns: 25.

> For PT description density management and work task granularity rules: read `resources/methodology.md`

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Task API tool error or timeout | L0 Retry | Re-invoke pt-manager with same DPS |
| Duplicate PT detected or partial metadata | L1 Nudge | Respawn with refined DPS targeting deduplication context |
| pt-manager exhausted turns or stuck | L2 Respawn | Kill → fresh pt-manager with refined DPS |
| Circular dependency or batch scope shift | L3 Restructure | Modify task graph, break cycle, reassign files |
| 3+ L2 failures or PT unrecoverable | L4 Escalate | AskUserQuestion with pipeline state options |

> For failure sub-cases (duplicate PT, circular deps, metadata corruption, stuck tasks, stalled subagent): read `resources/methodology.md`

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

### DO NOT: Overwrite PT Without Reading First
Every PT update must follow Read-Merge-Write. Blind overwrites lose information from other phases.

### DO NOT: Create Work Tasks Without Complete Metadata
Every task needs all fields: type, phase, domain, skill, agent, files, priority, parent. Missing fields break visualization, routing, and dependency tracking.

### DO NOT: Use PT for Ephemeral Communication
PT is the persistent pipeline record, not a messaging system. Do not add temporary status messages or debug notes to PT metadata.

### DO NOT: Create Cyclic Dependencies
Always verify the dependency graph is acyclic before adding `addBlockedBy`. A single cycle deadlocks all tasks in the chain.

### DO NOT: Complete PT Before All Work Tasks Finish
Always verify all `parent: {PT-id}` tasks are completed before marking PT completed.

### DO NOT: Delete Work Directory Before PT Completion
Deleting `~/.claude/tasks/{team-name}/` removes PT task files. **Correct sequence**: PT completed → subagent shutdown → cleanup work directory.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (User invocation) | Task management action request | `$ARGUMENTS` text: action + args (e.g., "create-pt SRC", "visualize") |
| (Any pipeline phase) | Phase completion requiring PT update | Lead routes with phase results for PT metadata merge |
| plan-static | Task breakdown requiring batch creation | L1 YAML: task list with files, dependencies, priorities |
| delivery-pipeline | Pipeline completion requiring PT close | L1 YAML: `commit_hash`, `status: delivered` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (Lead context) | PT task ID and pipeline state | After PT creation or update |
| (Lead context) | ASCII visualization | After visualize action |
| (Lead context) | Dependency graph summary | After batch work task creation |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Duplicate PT detected | (Self - resolve) | Both PT task IDs for deduplication |
| Circular dependency | (Self - break cycle) | Cycle path details |
| PT metadata corruption | (Self - reconstruct) | Current PT state + reconstruction context |

## Quality Gate
- Exactly 1 `[PERMANENT]` task exists (no duplicates)
- PT updates use Read-Merge-Write (never blind overwrite)
- Work tasks have complete metadata (type, phase, domain, skill, agent, files)
- Dependency chains are acyclic (addBlockedBy creates no cycles)
- ASCII visualization matches current TaskList state

## Output

### L1
```yaml
domain: cross-cutting
skill: task-management
action: create-pt|update-pt|batch-create|visualize|complete-pt
pt_id: ""
task_count: 0
pt_signal: "metadata.phase_signals.cross-cutting"
signal_format: "{STATUS}|action:{type}|tasks:{N}|ref:tasks/{work_dir}/task-management.md"
```

### L2
- Action summary with affected task IDs
- ASCII visualization (if visualize action)
- Dependency graph changes (if batch-create)