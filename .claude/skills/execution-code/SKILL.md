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
  plan-interface contracts verbatim. Exclude ADR rationale and
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
Lead determines tier based on orchestration-verify output:
- **TRIVIAL indicators**: Single task in matrix, 1-2 files assigned, no inter-file dependencies, simple change type (rename, config update, string change)
- **STANDARD indicators**: 2-3 tasks in matrix, 3-6 files across 1-2 modules, some interface dependencies between tasks, moderate change type (new function, API endpoint, component)
- **COMPLEX indicators**: 4+ tasks in matrix, 7+ files across 3+ modules, circular or deep dependency chains, architectural change type (new module, refactor, migration)

### Spawn vs Lead-Direct Decision
- **Lead-direct** (no spawn): Only for TRIVIAL tier when Lead already has the exact code change in context (e.g., from a previous implementer's completion summary). Requires: file path known, change < 20 lines, no test required.
- **Spawn implementer** (default): All other cases. Even simple changes benefit from implementer's Bash access for testing.
- **Never Lead-direct**: Changes requiring `npm test`, `pytest`, compilation, or any build step — Lead has no Bash.

### Input Validation Before Proceeding
Before spawning implementers, verify:
1. orchestration-verify L1 shows `status: PASS` — never execute from FAIL orchestration
2. Task-teammate matrix has complete file assignments (no empty `files[]` arrays)
3. Interface contracts exist for all cross-task dependencies
4. No file appears in multiple task assignments (ownership conflict)

If any validation fails: route back to orchestration-verify with specific failure reason.

### Parallel vs Sequential Spawning
- **Parallel** (default for STANDARD/COMPLEX): When implementer task groups have no shared files and no producer-consumer dependency
- **Sequential**: When Task B depends on Task A's output file (e.g., Task A creates a module, Task B imports from it). Sequence determined by plan-interface dependency order.
- **Mixed**: In COMPLEX tier, spawn independent groups in parallel, then sequential groups after dependencies complete.

## Methodology

### 1. Read Validated Assignments
Load orchestration-verify PASS report and task-teammate matrix.
Extract file assignments, dependency order, and interface contracts per implementer.

### 2. Spawn Implementers
For each task group in the matrix:
- Create Task with `subagent_type: implementer`

Construct each delegation prompt with:
- **Context (D11 — cognitive focus first)**:
  - INCLUDE: Exact task row from orchestration-verify matrix (task_id, description, assigned files). Interface contracts verbatim from plan-interface: function signatures, data types, return values, error types. PT subject and acceptance criteria.
  - EXCLUDE: Other implementers' task details. ADR rationale (pass WHAT decisions, not WHY). Full pipeline state beyond this task group. Rejected design alternatives.
  - Budget: Context field ≤ 30% of implementer effective context.
- **Task**: List exact file paths to create/modify. For each file, specify: what function/class/method to implement, what behavior it should exhibit, what tests to satisfy. Reference existing patterns: "Follow the pattern in `<existing_file>:<line_range>` for consistency."
- **Constraints**: Scope limited to non-.claude/ application source files only. Do NOT modify .claude/ files, test fixtures, or unrelated modules. If a dependency file needs changes, report it — do not modify files outside your assignment.
- **Expected Output**: Report completion as L1 YAML with `files_changed` (array of paths), `status` (complete|failed), and `blockers` (array, empty if none). Provide L2 markdown summarizing what was implemented, key decisions made, and any deviations from the plan.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

#### Tier-Specific DPS Variations

**TRIVIAL DPS Additions:**
- Context: Include full file content (small files, fits in context). No need for line range references.
- Task: Specify exact diff: "Change line X from `old` to `new`". Include expected test command: "Run `npm test -- --grep 'test name'` to verify."
- Constraints: Single file only. If change requires touching a second file, escalate to STANDARD.
- maxTurns: 15 (small scope, quick completion expected)

**STANDARD DPS Additions:**
- Context: Include file headers and relevant functions (not full files). Reference line ranges: "See `src/auth.ts:45-80` for the existing pattern."
- Task: Describe behavior change, not exact diff. Let implementer decide implementation approach within interface contracts.
- Constraints: Scope limited to assigned files only. Report (don't fix) issues in unassigned files.
- maxTurns: 25 (moderate scope)

**COMPLEX DPS Additions:**
- Context: Include architecture summary from design-architecture L2. Include interface contracts from plan-interface for ALL cross-boundary interactions. Include dependency order from plan-strategy.
- Task: Describe component-level goals. Reference test suites: "All tests in `tests/auth/` must pass after changes."
- Constraints: Own files only. Use interface contracts as boundaries — do not reach into other implementers' file assignments.
- maxTurns: 30 (full scope, may need exploration)

### 3. Monitor Progress
During implementation:
- Receive implementer completion summary via SendMessage
- Track files_changed count against expected
- If implementer reports blocker: assess and provide guidance

#### Monitoring Heuristics
- **Healthy progress**: Implementer reports files_changed incrementally, no blockers
- **Stalled**: No L1 update after maxTurns/2 — read L2 for status, consider guidance message
- **Blocked on dependency**: Implementer reports blocker referencing another implementer's file — hold this implementer, accelerate the dependency
- **Scope creep detected**: Implementer modifying files outside assignment — send correction via new spawn, reference constraint in original DPS
- **Test failures**: Implementer reports test failures — check if test expectations match design-interface contracts; if contract mismatch, escalate to plan revision rather than forcing implementer to work around incorrect contract

### 4. Handle Failures
If an implementer fails or produces incorrect output:
- Read their L2 for error details
- Provide corrected instructions via new spawn
- Max 3 retry iterations per implementer

### 5. Consolidate Results
After all implementers complete:
- Collect L1 YAML from each implementer
- Build unified file change manifest
- Report to execution-review for validation

**SRC Integration**: After consolidation, Lead should route to execution-impact for dependency analysis before proceeding to execution-review. SubagentStop hook will inject SRC IMPACT ALERT into Lead's context when implementers finish.

### Iteration Tracking (D15)
- Lead manages `metadata.iterations.execution_code: N` in PT before each invocation
- Iteration 1-2: strict mode (FAIL → return to execution-review for re-assessment)
- Iteration 3+: auto-PASS with documented gaps; escalate to L4 if critical findings remain
- Max iterations: 2

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error, implementer spawn timeout | L0 Retry | Re-invoke same implementer with same DPS |
| Implementer output incomplete or off-scope | L1 Nudge | SendMessage with corrected constraints or scope |
| Implementer exhausted turns or context polluted | L2 Respawn | Kill → fresh implementer with refined DPS |
| File ownership conflict or dependency broken between task groups | L3 Restructure | Reassign files, reorder task graph, split tasks |
| All implementers failed after L2, architectural issue suspected | L4 Escalate | AskUserQuestion with situation summary + options |

- **Retries exhausted (3 per implementer)**: Set task `status: failed`, include `blockers` array with error details and last attempt output
- **Partial completion**: Set skill `status: partial`, include completed tasks in manifest alongside failed ones
- **Routing**: Route to execution-review with FAIL status -- review assesses if partial results are usable
- **Pipeline impact**: Non-blocking. Pipeline continues with partial results; review decides if rework needed

## Anti-Patterns

### DO NOT: Spawn Without Interface Contracts
Never spawn an implementer for a task that has cross-file dependencies without providing interface contracts from plan-interface. The implementer will guess at interfaces, creating integration bugs that are expensive to fix in execution-review.

### DO NOT: Overlap File Ownership
Never assign the same file to multiple implementers. This creates merge conflicts that neither implementer can resolve. If a file needs changes from multiple tasks, assign it to one implementer and provide the combined requirements.

### DO NOT: Retry Infinitely
Max 3 retry iterations per implementer. After 3 failures on the same task, the issue is likely architectural (wrong approach, missing dependency, incorrect interface). Route to execution-review for assessment rather than spawning a 4th implementer.

### DO NOT: Mix Code and Infra
Never assign .claude/ files to a code implementer. Code implementers have Bash but lack the INFRA context. Route .claude/ changes to execution-infra exclusively.

### DO NOT: Skip SRC Integration
After consolidation, always check for SubagentStop hook's SRC IMPACT ALERT. Skipping execution-impact means cascade-worthy changes slip through undetected.

### DO NOT: Use `run_in_background: true` for Dependent Tasks
Background implementers can't receive mid-task guidance. Use background only for independent tasks where no mid-execution course correction is expected.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestrate-coordinator | Unified execution plan with code task assignments | L1 YAML: `tasks[].{task_id, implementer, files[], dependencies[]}` |
| plan-interface | Interface contracts for cross-task boundaries | L2 markdown: function signatures, data types, error contracts |
| plan-strategy | Execution sequence and parallel groups | L2 markdown: dependency graph, parallel opportunities |
| design-architecture | Component structure (for COMPLEX DPS context) | L2 markdown: module boundaries, data flow |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-impact | File change manifest | Always (even if partial). SRC hook auto-triggers. |
| execution-review | Implementation artifacts + L1/L2 per implementer | After all implementers complete (or max retries hit) |
| verify domain | Completed implementation artifacts | After execution-review PASS |
| orchestration-verify | Error report | If assignment is invalid (missing files, ownership conflict) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| All implementers failed | execution-review (FAIL) | Failed task details, error logs, last attempt output |
| Partial completion | execution-review (PASS with warnings) | Completed + failed task separation |
| Assignment invalid | orchestration-verify | Specific validation failure reason |
| Interface contract mismatch | plan-interface | Mismatched contract details from implementer report |

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
