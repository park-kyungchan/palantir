---
name: execution-code
description: >-
  Spawns implementers for non-.claude/ source files via DPS
  delegation prompts. Monitors completion via SendMessage,
  handles failures with max 3 retries. Parallel with
  execution-infra. Use after orchestrate-coordinator complete
  with PASS and code tasks assigned in unified plan. Reads from
  orchestrate-coordinator unified execution plan L3 with code
  task assignments and DPS prompts. Produces file change manifest
  with per-implementer status and implementation summary for
  execution-impact and execution-review. All spawns model:sonnet.
  Atomic commit per task with pre-commit backpressure. P2P
  SendMessage for producer→consumer handoffs. On FAIL, routes to
  execution-review with partial manifest and retry count. DPS
  needs orchestrate-coordinator task_id/files/dependencies +
  plan-relational contracts verbatim. Exclude ADR rationale and
  rejected alternatives.
user-invocable: true
disable-model-invocation: true
---

# Execution — Code

## Execution Model
- **TRIVIAL**: Single implementer spawn for 1-2 file changes.
- **STANDARD**: Spawn 1-2 implementers. Each owns non-overlapping files.
- **COMPLEX**: Spawn 3-4 implementers. Parallel implementation with dependency awareness.

## Decision Points

### Tier Classification for Code Execution
Lead determines tier based on orchestrate-coordinator output:
- **TRIVIAL**: Single task in matrix, 1-2 files, no inter-file deps, simple change type
- **STANDARD**: 2-3 tasks, 3-6 files across 1-2 modules, some interface deps, moderate change type
- **COMPLEX**: 4+ tasks, 7+ files across 3+ modules, deep dependency chains, architectural change type

### Spawn vs Lead-Direct Decision
- **Lead-direct** (no spawn): TRIVIAL only — exact change already in context, file path known, < 20 lines, no test required.
- **Spawn implementer** (default): All other cases. Changes requiring `npm test`, `pytest`, compilation, or any build step always spawn.
- **Never Lead-direct**: Anything requiring Bash — Lead has no Bash.

### Input Validation Before Proceeding
Before spawning, verify:
1. orchestrate-coordinator L1 shows `status: PASS`
2. Task-teammate matrix has complete file assignments (no empty `files[]`)
3. Interface contracts exist for all cross-task dependencies
4. No file appears in multiple task assignments

If any fails: route back to orchestrate-coordinator with specific failure reason.

### Parallel vs Sequential Spawning
- **Parallel** (default STANDARD/COMPLEX): No shared files and no producer-consumer dependency.
- **Sequential**: Task B depends on Task A's output file. Determined by plan-relational dependency order.
- **Mixed** (COMPLEX): Spawn independent groups in parallel; sequential groups after dependencies complete.

## Methodology

### 1. Read Validated Assignments
Load orchestrate-coordinator PASS report and task-teammate matrix.
Extract file assignments, dependency order, and interface contracts per implementer.

### 2. Spawn Implementers
For each task group in the matrix, create Task with `subagent_type: implementer`.

Construct each delegation prompt with:
- **Context (D11)**: INCLUDE: task row from coordinator matrix, interface contracts from plan-relational verbatim, PT acceptance criteria. EXCLUDE: other implementers' tasks, ADR rationale, full pipeline state, rejected alternatives. Budget ≤ 30% of implementer context.
- **Task**: List exact file paths. Specify function/class/method to implement, behavior, tests to satisfy. Reference existing patterns by `file:line_range`.
- **Constraints**: Non-.claude/ source files only. Report (don't fix) issues in unassigned files.
- **Expected Output**: L1 YAML: `files_changed[]`, `status`, `blockers[]`. L2 markdown: implementation summary, key decisions, deviations.
- **Delivery (Four-Channel)**: Ch2: `tasks/{team}/p6-{task_id}-output.md`. Ch3 micro-signal to Lead. Ch4 P2P READY signal to COMM_PROTOCOL NOTIFY targets.

> For tier-specific DPS content (TRIVIAL/STANDARD/COMPLEX maxTurns and context rules): read `resources/methodology.md`

### 3. Monitor Progress
- Receive Ch3 micro-signals from implementers (status only, not full data)
- Track `files_changed` count against expected from L3 execution plan
- **Sequential deps**: COMM_PROTOCOL AWAIT/NOTIFY enables self-coordination — Lead does NOT relay data between waves

> For monitoring heuristics (healthy/stalled/blocked/scope-creep/test-failure patterns): read `resources/methodology.md`

### 4. Handle Failures
Read implementer L2 for error details. Provide corrected instructions via new spawn. Max 3 retry iterations per implementer.

### 5. Consolidate Results
Collect L1 YAML from each implementer. Build unified file change manifest. Check SubagentStop hook SRC IMPACT ALERT. Route to execution-impact, then execution-review.

### Iteration Tracking (D15)
- `metadata.iterations.execution_code: N` in PT before each invocation
- Iter 1-2: strict (FAIL → execution-review re-assessment). Iter 3+: auto-PASS with gaps; L4 if critical.
- Max iterations: 2

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error, implementer spawn timeout | L0 Retry | Re-invoke same implementer with same DPS |
| Implementer output incomplete or off-scope | L1 Nudge | SendMessage with corrected constraints or scope |
| Implementer exhausted turns or context polluted | L2 Respawn | Kill → fresh implementer with refined DPS |
| File ownership conflict or dependency broken | L3 Restructure | Reassign files, reorder task graph, split tasks |
| All implementers failed after L2, architectural issue | L4 Escalate | AskUserQuestion with situation summary + options |

- **Retries exhausted**: Set task `status: failed`, include `blockers[]` with error details and last attempt output
- **Partial completion**: Set skill `status: partial`; route to execution-review — review decides if rework needed
- **Pipeline impact**: Non-blocking. Pipeline continues with partial results.

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

### DO NOT: Spawn Without Interface Contracts
Never spawn for cross-file dependency tasks without plan-relational interface contracts. Implementer will guess at interfaces — integration bugs are expensive to fix in execution-review.

### DO NOT: Overlap File Ownership
Never assign the same file to multiple implementers. If a file needs changes from multiple tasks, assign to one implementer with combined requirements.

### DO NOT: Retry Infinitely
Max 3 iterations per implementer. After 3 failures, the issue is likely architectural — route to execution-review, not a 4th implementer.

### DO NOT: Mix Code and Infra
Never assign .claude/ files to a code implementer. Route .claude/ changes to execution-infra exclusively.

### DO NOT: Skip SRC Integration
Always check for SubagentStop hook's SRC IMPACT ALERT after consolidation. Skipping execution-impact lets cascade-worthy changes slip through.

### DO NOT: Background Dependent Tasks
Background implementers can't receive mid-task guidance. Use background only for independent tasks.

## Phase-Aware Execution

P2+ Team mode. Four-Channel Protocol: Ch2 (disk file) + Ch3 (micro-signal to Lead) + Ch4 (P2P to consumers). Sequential deps use COMM_PROTOCOL AWAIT/NOTIFY — Lead is NOT in the data path. No overlapping file edits with parallel agents.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestrate-coordinator | Unified execution plan with code task assignments | L1 YAML: `tasks[].{task_id, implementer, files[], dependencies[]}` |
| plan-relational | Interface contracts for cross-task boundaries | L2 markdown: function signatures, data types, error contracts |
| plan-behavioral | Execution sequence and parallel groups | L2 markdown: dependency graph, parallel opportunities |
| design-architecture | Component structure (COMPLEX DPS context only) | L2 markdown: module boundaries, data flow |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-impact | File change manifest | Always (even if partial). SRC hook auto-triggers. |
| execution-review | Implementation artifacts + L1/L2 per implementer | After all implementers complete (or max retries hit) |
| verify domain | Completed implementation artifacts | After execution-review PASS |
| orchestrate-coordinator | Error report | If assignment is invalid (missing files, ownership conflict) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| All implementers failed | execution-review (FAIL) | Failed task details, error logs, last attempt output |
| Partial completion | execution-review (PASS with warnings) | Completed + failed task separation |
| Assignment invalid | orchestrate-coordinator | Specific validation failure reason |
| Interface contract mismatch | plan-relational | Mismatched contract details from implementer report |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- All assigned files have been modified/created
- Each implementer reports `status: complete`
- No unresolved blockers or errors
- File ownership non-overlapping (no conflicts)

## Output

### L1
```yaml
domain: execution
skill: code
status: complete|in-progress|failed
files_changed: 0
implementers: 0
tasks:
  - task_id: ""
    implementer: ""
    files: []
    status: complete|in-progress|failed
pt_signal: "metadata.phase_signals.p6_code"
signal_format: "{STATUS}|files:{N}|implementers:{N}|ref:tasks/{team}/p6-code.md"
```

### L2
- Implementation summary per implementer
- File change manifest
- Issues encountered and resolutions
