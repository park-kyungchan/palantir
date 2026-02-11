---
name: agent-teams-execution-plan
description: "Phase 0 (PT Check) + Phase 6 (Implementation) — executes implementation plan from agent-teams-write-plan. Spawns adaptive implementers with understanding verification, two-stage review, and Gate 6 evaluation. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[session-id or path to implementation plan]"
---

# Execution Pipeline

Phase 6 (Implementation) orchestrator. Transforms an implementation plan into working code through verified implementer teammates with integrated two-stage review.

**Announce at start:** "I'm using agent-teams-execution-plan to orchestrate Phase 6 (Implementation) for this feature."

**Core flow:** PT Check (Lead) → Input Discovery → Team Setup → Coordinator Setup + Adaptive Spawn + Verification → Coordinator-Mediated Execution + Review → Gate 6 → Clean Termination

## When to Use

```
Have an implementation plan from agent-teams-write-plan?
├── Working in Agent Teams mode? ─── no ──→ Use /executing-plans (solo)
├── yes
├── GC-v4 with Phase 4 COMPLETE? ── no ──→ Run /agent-teams-write-plan first
├── yes
├── Plan validated (Phase 5)?
│   ├── yes ──→ Use /agent-teams-execution-plan
│   └── no ──→ Recommended: run plan-validation first, or proceed at own risk
└── Use /agent-teams-execution-plan
```

**vs. executing-plans (solo):** This skill spawns persistent implementer teammates with understanding verification, adaptive parallelism, and two-stage review. Solo executing-plans runs everything in a single agent sequentially. Use agent-teams-execution-plan when the plan has 2+ tasks or requires file ownership isolation.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Implementation Plans:**
!`ls /home/palantir/docs/plans/*-implementation.md /home/palantir/docs/plans/*-plan.md 2>/dev/null || true`

**Previous Pipeline Output:**
!`ls -d /home/palantir/.agent/teams/*/global-context.md 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "---"; echo "Dir: $dir"; head -8 "$f"; echo ""; done`

**Git Status:**
!`cd /home/palantir && git diff --name-only 2>/dev/null | head -20`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Feature Input:** $ARGUMENTS

---

## Phase 0: PERMANENT Task Check

Lightweight step (~500 tokens). No teammates spawned, no verification required.

Call `TaskList` and search for a task with `[PERMANENT]` in its subject.

```
TaskList result
     │
┌────┴────┐
found      not found
│           │
▼           ▼
TaskGet →   AskUser: "No PERMANENT Task found.
read PT     Create one for this feature?"
│           │
▼         ┌─┴─┐
Continue  Yes   No
to 6.1    │     │
          ▼     ▼
        /permanent-tasks    Continue to 6.1
        creates PT-v1       without PT
        → then 6.1
```

If a PERMANENT Task exists, its content (user intent, codebase impact map, prior decisions)
provides additional context for Phase 6 execution. Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to Phase 6.1.

If a PERMANENT Task exists but `$ARGUMENTS` describes a different feature than the PT's
User Intent, ask the user to clarify which feature to work on before proceeding.

---

## Phase 6.1: Input Discovery + Validation

No teammates spawned. Lead-only step.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find agent-teams-write-plan output:

1. Look for `.agent/teams/*/global-context.md` files with `Phase 4: COMPLETE` or `Phase 5: COMPLETE`
2. If `$ARGUMENTS` provides a session-id or path, use that directly
3. If multiple candidates found, present options via `AskUserQuestion`
4. If single candidate, confirm with user: "Found implementation plan output at {path}. Use this?"
5. If no candidates, inform user: "No implementation plan found. Run /agent-teams-write-plan first."

If a PERMANENT Task was loaded in Phase 0, use its Codebase Impact Map and user intent
to inform validation and provide additional context to implementers.

### Validation

After identifying the source, verify:

| # | Check | On Failure |
|---|-------|------------|
| V-1 | `global-context.md` exists with Phase 4 or 5 COMPLETE | Abort: "GC-v4 not found or Phase 4 not complete" |
| V-2 | Implementation plan file exists in `docs/plans/` | Abort: "Implementation plan not found" |
| V-3 | Plan contains File Ownership Assignment and TaskCreate Definitions (§3/§4 in 10-section template or equivalent) | Abort: "Plan missing required sections: {list}" |
| V-4 | Plan contains §5 (Change Specifications) | Abort: "Plan missing §5 Change Specifications" |

On all checks PASS → proceed to 6.2.

---

## Phase 6.2: Team Setup

```
TeamCreate:
  team_name: "{feature-name}-execution"
```

Create orchestration-plan.md and copy GC-v4 to new session directory.

Read the implementation plan fully:
- §1 (Orchestration Overview): understand scope and task count
- §3 (File Ownership Assignment): extract file sets per task
- §4 (TaskCreate Definitions): extract all tasks with dependencies
- §5 (Change Specifications): understand what each task implements

---

## Phase 6.3: Adaptive Spawn + Coordinator Setup + Verification

Protocol execution follows CLAUDE.md §6 and §10.

Use `sequential-thinking` for all Lead decisions in this phase.

### Adaptive Spawn Algorithm

Determine implementer count from plan structure:

```
1. Extract all tasks from plan §4 with blockedBy/blocks
2. Build dependency graph (directed)
3. Compute connected components (treat as undirected for grouping)
4. Merge file ownership sets per component from §3
5. Verify inter-component file sets are non-overlapping
   If overlap → merge components → recompute
6. implementer_count = min(connected_components, 4)
7. Assign each implementer one component
8. Within each component, determine topological execution order
```

Present spawn plan to user:
```markdown
## Spawn Plan

**Tasks:** {total} tasks in {component_count} independent groups
**Implementers:** {count}
**Coordinator:** execution-coordinator (manages implementation-review lifecycle)
**Strategy:** {parallel / sequential / mixed}

| Implementer | Tasks | Files |
|-------------|-------|-------|
| implementer-1 | Task 1, 2, 5 | src/auth/*, config/auth.yaml |
| implementer-2 | Task 3, 4 | src/api/*, tests/api/* |

**Reviewers:** spec-reviewer, code-reviewer (dispatched by execution-coordinator)
```

### TaskCreate

For each task from plan §4, create via TaskCreate with comprehensive description per task-api-guideline.md §3. Include:
- Objective, Context in Global Pipeline, Detailed Requirements
- Interface Contracts, File Ownership (exact paths)
- Dependency Chain (blockedBy/blocks from plan §4)
- Acceptance Criteria (from plan §4, always including AC-0: plan verification)

Set up dependencies via addBlockedBy/addBlocks.

### Execution Coordinator Spawn

```
Task tool:
  subagent_type: "execution-coordinator"
  team_name: "{feature-name}-execution"
  name: "exec-coord"
  mode: "default"
```

#### [DIRECTIVE] for Execution Coordinator

The directive must include these context layers:

1. **PERMANENT Task ID** — `PT-ID: {task_id} | PT-v{N}` for TaskGet
2. **Implementation plan** — full §1-§10 path for coordinator to Read
3. **Task list with file ownership** — per component grouping from adaptive spawn
4. **Review prompt templates** — spec-reviewer and code-reviewer prompts (see §6.4 Templates)
5. **Impact Map excerpt** — for worker understanding verification (AD-11)
6. **Verification criteria** — what to check in worker understanding
7. **Fix loop rules** — max 3 per review stage, escalate to Lead on exhaustion
8. **Worker names** — sent via follow-up message after worker pre-spawn (Step below)

### Worker Pre-Spawn

After execution-coordinator confirms ready, pre-spawn all workers in parallel:

```
# Implementers (per adaptive spawn algorithm)
Task(subagent_type="implementer", name="implementer-{N}",
     mode="default", team_name="{feature}-execution")

# Reviewers (includes D-005 contract-reviewer and regression-reviewer)
Task(subagent_type="spec-reviewer", name="spec-rev",
     mode="default", team_name="{feature}-execution")
Task(subagent_type="code-reviewer", name="code-rev",
     mode="default", team_name="{feature}-execution")
Task(subagent_type="contract-reviewer", name="contract-rev",
     mode="default", team_name="{feature}-execution")   # COMPLEX only
Task(subagent_type="regression-reviewer", name="regression-rev",
     mode="default", team_name="{feature}-execution")   # COMPLEX only

# Execution Monitor (D-014 — COMPLEX tier only, Lead-direct)
Task(subagent_type="execution-monitor", name="exec-monitor",
     mode="default", team_name="{feature}-execution")
```

For COMPLEX tier, Lead writes phase-context.md (D-012) with Impact Map excerpt,
interface contracts, and constraints before spawning implementers.

Worker directives include:
- "Your coordinator is: exec-coord. Report progress and completion to your coordinator."
- PT-ID for TaskGet
- Implementation plan path for direct reading
- File ownership assignment (implementers only)

After all workers spawned, inform coordinator:
```
SendMessage to exec-coord:
  "Workers spawned: implementer-1, implementer-2, spec-rev, code-rev.
   Task assignments: {per component grouping}.
   Begin worker verification and task execution."
```

### Understanding Verification (Delegated — AD-11)

```
Level 1: Lead verifies execution-coordinator
  - Full Impact Map context
  - 1-3 probing questions covering cross-category awareness
  - Coordinator explains implementation plan understanding

Level 2: Execution-coordinator verifies implementers
  - Category-scoped Impact Map excerpt (from Lead's directive)
  - 1-2 questions per implementer on intra-category concerns
  - Coordinator approves implementer plans before execution
  - Coordinator reports verification status to Lead
```

Once all verification passes: coordinator signals execution start.

All agents use `sequential-thinking` throughout.

---

## Phase 6.4: Task Execution + Review (Coordinator-Mediated)

Execution-coordinator manages the full implementation-review lifecycle.
Lead receives consolidated reports only.

### Implementer Execution Flow (per task, managed by coordinator)

```
1. Coordinator assigns task to implementer with plan §5 spec
2. Implementer reads plan §5 spec for current task
3. Implementer implements changes within file ownership boundary
4. Implementer runs self-tests (Bash: relevant test commands)
5. Implementer self-reviews (completeness, quality, YAGNI, testing)
6. Implementer reports to coordinator for review dispatch
   Coordinator dispatches spec-reviewer (Stage 1):
   ├── PASS → coordinator dispatches code-reviewer (Stage 2)
   └── FAIL → coordinator relays fix to implementer (max 3)
             └── 3x FAIL → coordinator escalates to Lead: BLOCKED
   Code-reviewer (Stage 2):
   ├── PASS → task complete
   └── FAIL → coordinator relays fix to implementer (max 3)
             └── 3x FAIL → coordinator escalates to Lead: BLOCKED
7. Coordinator updates task status, sends consolidated report to Lead
8. Coordinator assigns next task to implementer (if any)
```

### Review Prompt Templates

These templates are embedded in the execution-coordinator's directive by Lead.
The coordinator constructs actual review prompts by filling template variables
with task-specific content.

**Spec-Reviewer Template:**

```
You are reviewing whether an implementation matches its specification.

## Specification
{plan §5 Change Specification for this task}

## Implementer Report
{self-review report from implementer}

## Files to Inspect
{files within implementer's ownership}

## Verification Principle
Do Not Trust the Report. Verify by reading actual code.

## Verification Axes
1. Missing requirements: spec items not implemented
2. Extra/unneeded work: features not in spec
3. Misunderstandings: wrong interpretation of spec

Report format:
- Result: PASS / FAIL
- For EACH spec requirement: file:line reference showing the implementation
- If FAIL: specific issues with file:line references and explanation
- Summary: what was checked and what was found

Evidence is mandatory for both PASS and FAIL. A PASS without file:line
references for each requirement is incomplete and should be treated as FAIL.
```

**Code-Reviewer Template:**

```
Review the implementation for code quality, architecture, and production readiness.

WHAT_WAS_IMPLEMENTED: {implementer's self-review report}
PLAN_OR_REQUIREMENTS: {plan §5 spec for this task}
BASE_SHA: {commit before implementation}
HEAD_SHA: {current HEAD}
DESCRIPTION: {task summary}

Additional context: This is part of {feature-name}. See global-context for project-level constraints.
```

Prerequisite: Spec review (Stage 1) must PASS before coordinator dispatches code review.

### Consolidated Reporting (Coordinator → Lead)

After each task completion, coordinator sends to Lead:

```
Task {N}: {PASS/FAIL}
  - Spec review: {PASS/FAIL} ({iterations} iteration(s))
  - Quality review: {PASS/FAIL} ({iterations} iteration(s))
  - Files: {list of files changed}
  - Issues: {resolved count}, {outstanding count}
  Proceeding to Task {N+1}. / All tasks complete.
```

### Implementer Completion Report (to Coordinator)

```
Task {N} implementation complete: {summary}

## Implementation Summary
- Files created: {list}
- Files modified: {list}
- Tests: {count} added/modified, all passing

## Self-Test Results
{test command executed}
{captured stdout/stderr}
Exit code: 0 (PASS) or non-zero (FAIL)

## Self-Review Findings
- {any issues found and fixed}

## Evidence Sources
- Sequential thinking: {key decision points analyzed}
- Files read: {count} via Read/Glob/Grep

## Artifacts
- L1: .agent/teams/{session-id}/phase-6/implementer-{N}/L1-index.yaml
- L2: .agent/teams/{session-id}/phase-6/implementer-{N}/L2-summary.md
- L3: .agent/teams/{session-id}/phase-6/implementer-{N}/L3-full/
```

Note: Review output (spec-reviewer, code-reviewer raw responses) is captured by the
coordinator and included in the coordinator's consolidated L2, not the implementer's L2.

---

## Phase 6.5: Monitoring + Issue Resolution

### Monitoring Cadence

| Method | Cost | Frequency | When |
|--------|------|-----------|------|
| tmux visual | 0 tokens | Continuous | Always (primary) |
| TaskList | ~500 tokens | Every 15 min | Periodic check |
| Read L1 | ~2K tokens | On demand | When blocker reported |
| SendMessage query | ~200 tokens | On silence | >30 min no update |
| Read coordinator L2 | ~2K tokens | On demand | When coordinator reports completion |

### Issue Resolution

| Issue | Lead Action |
|-------|------------|
| BLOCKED (cross-boundary) | Follow Cross-Boundary Issue Escalation below |
| BLOCKED (fix loop exhausted) | Evaluate: revise plan spec / reassign / ABORT |
| Context pressure reported | Shutdown implementer → re-spawn with L1/L2 injection |
| >30 min silence | Send status query to implementer |
| >40 min silence | Escalate: Read L1, check if stuck, consider intervention |
| Implementer deviation from spec | Send correction with updated context → implementer acknowledges |

### Cross-Boundary Issue Escalation

When implementer reports `BLOCKED | Need file outside ownership`:

```
Stage 1: Read the BLOCKED report — understand the issue
Stage 2: Determine root cause:
  Case A (other implementer deviation) → send correction to that implementer
  Case B (plan spec error) → update PT + GC → send context update to all affected
Stage 3: Wait for acknowledgement from affected implementer(s)
Stage 4: Verify fix → unblock original implementer
```

---

## Phase 6.6: Gate 6

Use `sequential-thinking` for all gate evaluation.

### Per-Task Evaluation

For each task in the coordinator's consolidated report:

| # | Criterion | Method |
|---|-----------|--------|
| G6-1 | Spec review PASS | Read L2 → reviewer raw output |
| G6-2 | Quality review PASS | Read L2 → reviewer raw output |
| G6-3 | Self-test PASS | Read L2 → test results |
| G6-4 | File ownership COMPLIANT | Verify files ⊆ assigned set |
| G6-5 | L1/L2/L3 exist | Check file existence |

### Spot-Check (Risk-Proportional Sampling)

Per implementer, select the highest-risk task and:
1. Read the actual code changes (use Read/Glob)
2. Compare to plan §5 spec
3. Verify spec-reviewer's assessment independently

### Cross-Task Evaluation

After ALL implementers complete:

| # | Criterion | Method |
|---|-----------|--------|
| G6-6 | Inter-implementer interface consistency | Read interface files, cross-reference |
| G6-7 | No unresolved critical issues | Verify all BLOCKED resolved |

### Conditional Final Review

If 2+ implementers AND (complex interfaces OR concerns found during cross-task):
- Dispatch code-reviewer subagent with full project scope
- Include all implementer outputs as review target

### Gate 6 Result

- **APPROVE:** G6-1~G6-7 all PASS → proceed to GC-v5 + Clean Termination
- **ITERATE (max 3):** Specific fix instructions to affected implementer(s)
- **ABORT:** 3x iteration exceeded or fundamental plan flaw → report to user

### Gate Record

Write `phase-6/gate-record.yaml`:

```yaml
phase: 6
result: APPROVED
date: {YYYY-MM-DD}
per_task:
  - task_id: {N}
    implementer: implementer-{X}
    spec_review: PASS
    quality_review: PASS
    self_test: PASS
    file_ownership: COMPLIANT
cross_task:
  interface_consistency: PASS
  unresolved_issues: NONE
  final_review: PASS / SKIPPED
gate_criteria:
  G6-1: PASS
  G6-2: PASS
  G6-3: PASS
  G6-4: PASS
  G6-5: PASS
  G6-6: PASS
  G6-7: PASS
```

---

## Phase 6.7: Clean Termination

After Gate 6 APPROVE:

### GC-v4 → GC-v5 Update + PT Update

Update PERMANENT Task (PT-v{N} → PT-v{N+1}) with implementation results and Phase 6 COMPLETE status.

Preserve all existing GC-v4 sections, then add to global-context.md:

```markdown
## Phase Pipeline Status
- Phase 6: COMPLETE (Gate 6 APPROVED)

## Implementation Results
- Tasks completed: {N}/{total}
- Files created: {list}
- Files modified: {list}
- Implementers used: {count}

## Interface Changes from Phase 4 Spec
- {deviations, if any}

## Gate 6 Record
- Per-task: {summary}
- Cross-task: {result}

## Phase 7 Entry Conditions
- Test targets: {files/modules}
- Integration points: {interfaces}
- Known risks: {observations}
```

### Output Summary

Present to user:

```markdown
## agent-teams-execution-plan Complete (Phase 6)

**Feature:** {name}
**Implementers:** {count}
**Tasks:** {completed}/{total}

**Code Changes:**
- Created: {count} files
- Modified: {count} files

**Gate 6:** APPROVED
- Spec compliance: ALL PASS
- Code quality: ALL PASS
- Cross-task interfaces: CONSISTENT

**Artifacts:**
- PERMANENT Task (PT-v{N}) — authoritative project context (updated with implementation results)
- Session artifacts: .agent/teams/{session-id}/
- Global Context: GC-v5

**Next:** Phase 7 (Testing) — use the verification-pipeline skill.
Input: GC-v5 + implementer artifacts. Update PERMANENT Task with `/permanent-tasks` if scope evolved.
```

### Shutdown Sequence

1. Shutdown all implementers: `SendMessage type: "shutdown_request"` to each
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`

---

## Cross-Cutting Requirements

### RTD Index

At each Decision Point in this phase, update the RTD index:
1. Update `current-dp.txt` with the new DP number
2. Write an rtd-index.md entry with WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS
3. Update the frontmatter (current_phase, current_dp, updated, total_entries)

Decision Points for this skill:
- DP-1: Input validation and spawn algorithm
- DP-2: Each implementer spawn
- DP-3: Per-task completion assessment
- DP-4: Monitoring interventions
- DP-5: Gate 6 evaluation

### Sequential Thinking

All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, and verification.

| Agent | When |
|-------|------|
| Lead | Adaptive spawn calculation, understanding verification, probing questions, Gate 6, issue resolution |
| Implementer | Impact analysis, plan submission, complex implementation decisions, self-review |

### Error Handling

| Situation | Response |
|-----------|----------|
| No implementation plan found | Inform user, suggest /agent-teams-write-plan |
| GC-v4 incomplete | Abort with missing section list |
| Spawn failure | Retry once, abort with notification |
| Understanding verification 3x rejection | Abort implementer, re-spawn with enhanced context |
| Fix loop 3x exhaustion | Implementer reports BLOCKED, Lead evaluates |
| Gate 6 3x iteration | Abort, present partial results to user |
| Cross-boundary issue | Follow escalation protocol (Phase 6.5) |
| Context compact | CLAUDE.md §9 recovery |
| Context pressure | Shutdown implementer, re-spawn with L1/L2 injection |
| User cancellation | Graceful shutdown all implementers, preserve artifacts |

### Compact Recovery

- Lead: orchestration-plan → task list → gate records → L1 indexes → re-inject
- Implementer: call TaskGet on PERMANENT Task for immediate self-recovery, then read own L1/L2/L3 and re-submit understanding

---

## Key Principles

- **Adaptive parallelism** — spawn only as many implementers as independent components require
- **Two-stage review always** — spec compliance before code quality, coordinator-managed
- **Fix loop bounded** — max 3 per stage, escalate on exhaustion
- **File ownership strict** — no cross-boundary writes, ever (except integrator)
- **3-Layer Defense** — automated review + self-report + risk-proportional spot-check
- **Pre-Compact Obligation** — write L1/L2/L3 after every task, not only at ~75%
- **Protocol delegated** — CLAUDE.md owns verification protocol, skill owns orchestration
- **Clean termination** — no auto-chaining to Phase 7
- **Sequential thinking always** — structured reasoning at every decision point
- **Artifacts preserved** — all outputs survive in `.agent/teams/{session-id}/`

## Never

- Skip understanding verification for any implementer
- Bypass execution-coordinator for review dispatch during Phase 6
- Skip Phase 0 PERMANENT Task check
- Allow concurrent editing of the same file by multiple implementers
- Dispatch code-reviewer before spec-reviewer passes
- Let implementers write to Task API (TaskCreate/TaskUpdate)
- Auto-chain to Phase 7 after termination
- Proceed past Gate 6 without all criteria met
- Trust review reports without L2 raw output evidence
- Fix cross-boundary issues without Lead coordination
- Exceed fix loop max (3) without escalation
- Spawn more than 4 implementers
