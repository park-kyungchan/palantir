---
name: agent-teams-execution-plan
description: "Phase 0 (PT Check) + Phase 6 (Implementation) — executes implementation plan from agent-teams-write-plan. Spawns adaptive implementers with understanding verification, two-stage review, and Gate 6 evaluation. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[session-id or path to implementation plan]"
---

# Execution Pipeline

Phase 6 (Implementation) orchestrator. Transforms an implementation plan into working code through verified implementer teammates with integrated two-stage review.

**Announce at start:** "I'm using agent-teams-execution-plan to orchestrate Phase 6 (Implementation) for this feature."

**Core flow:** PT Check (Lead) → Input Discovery → Team Setup → Adaptive Spawn + Verification → Task Execution + Review → Gate 6 → Clean Termination

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

## Phase 6.3: Adaptive Spawn + Verification

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
**Strategy:** {parallel / sequential / mixed}

| Implementer | Tasks | Files |
|-------------|-------|-------|
| implementer-1 | Task 1, 2, 5 | src/auth/*, config/auth.yaml |
| implementer-2 | Task 3, 4 | src/api/*, tests/api/* |
```

### TaskCreate

For each task from plan §4, create via TaskCreate with comprehensive description per task-api-guideline.md §3. Include:
- Objective, Context in Global Pipeline, Detailed Requirements
- Interface Contracts, File Ownership (exact paths)
- Dependency Chain (blockedBy/blocks from plan §4)
- Acceptance Criteria (from plan §4, always including AC-0: plan verification)

Set up dependencies via addBlockedBy/addBlocks.

### Implementer Spawn + Verification

For each implementer:

```
Task tool:
  subagent_type: "implementer"
  team_name: "{feature-name}-execution"
  name: "implementer-{N}"
  mode: "default"
```

#### [DIRECTIVE] Construction

The directive must include these context layers:

1. **PERMANENT Task ID** — `PT-ID: {task_id} | PT-v{N}` so implementer can call TaskGet for full context
2. **GC-v4 full embedding** — the entire global-context.md (session-level artifacts)
3. **Task-context.md** — assignment, file ownership, task list, plan §5 specs for assigned tasks
4. **Review instructions** — two-stage review protocol, fix loop rules, reviewer prompt templates
5. **Implementation plan path** — for implementer to Read directly

Task-context must instruct implementer to:
- Read the PERMANENT Task via TaskGet for full project context (user intent, impact map)
- Read the implementation plan before starting (especially §5 for their tasks)
- Execute tasks in topological order within their component
- Run self-review after each task (completeness, quality, YAGNI, testing per §6.4 flow)
- Dispatch spec-reviewer then code-reviewer subagents (two-stage, ordered)
- Include reviewer raw output in L2-summary.md
- Write L1/L2/L3 after each task completion (Pre-Compact Obligation)
- Report completion per task with structured report
- Report immediately if cross-boundary issue found

#### Understanding Verification

1. Implementer reads PERMANENT Task via TaskGet and confirms context receipt
2. Implementer explains their understanding of the task to Lead
3. Lead asks 1-3 probing questions grounded in the Codebase Impact Map,
   covering interconnections, failure modes, and dependency risks
4. Implementer defends with specific evidence
5. Lead verifies or rejects (max 3 attempts)
6. Once understanding is verified: implementer shares their plan, Lead approves → execution begins

All agents use `sequential-thinking` throughout.

---

## Phase 6.4: Task Execution + Review

Implementers work within their assigned components. Lead monitors and coordinates.

### Implementer Execution Flow (per task)

```
1. Read plan §5 spec for current task
2. Implement changes within file ownership boundary
3. Run self-tests (Bash: relevant test commands)
4. Self-review (completeness, quality, YAGNI, testing)
5. Dispatch spec-reviewer subagent (Stage 1)
   ├── PASS → proceed to Stage 2
   └── FAIL → fix → re-dispatch (max 3)
             └── 3x FAIL → BLOCKED
6. Dispatch code-reviewer subagent (Stage 2)
   ├── PASS → proceed to completion
   └── FAIL → fix → re-dispatch (max 3)
             └── 3x FAIL → BLOCKED
7. Write/update L1/L2/L3 (include reviewer raw output in L2)
8. Report Task {N} complete: {summary}
9. Proceed to next task in topological order (if any)
```

### Spec-Reviewer Subagent Prompt

Implementer dispatches via Task tool (general-purpose):

```
You are reviewing whether an implementation matches its specification.

## Specification
{plan §5 Change Specification for this task}

## Implementer Report
{self-review report}

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

### Code-Reviewer Subagent Prompt

Implementer dispatches via Task tool (superpowers:code-reviewer):

```
Review the implementation for code quality, architecture, and production readiness.

WHAT_WAS_IMPLEMENTED: {implementer's self-review report}
PLAN_OR_REQUIREMENTS: {plan §5 spec for this task}
BASE_SHA: {commit before implementation}
HEAD_SHA: {current HEAD}
DESCRIPTION: {task summary}

Additional context: This is part of {feature-name}. See global-context for project-level constraints.
```

Prerequisite: Spec review (Stage 1) must PASS before dispatching code review.

### Implementer Completion Report Format

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

## Spec Compliance Review (Stage 1)
- Result: PASS
- Reviewer raw output: {include full output with file:line references}
- Issues found and resolved: {count}
- Fix iterations: {N}/3

## Code Quality Review (Stage 2)
- Result: PASS
- Reviewer raw output: {include full output}
- Critical issues resolved: {count}
- Important issues resolved: {count}

## Self-Review Findings
- {any issues found and fixed}

## Evidence Sources
- Sequential thinking: {key decision points analyzed}
- Files read: {count} via Read/Glob/Grep
- Reviewer evidence: included in Stage 1-2 sections above

## Artifacts
- L1: .agent/teams/{session-id}/phase-6/implementer-{N}/L1-index.yaml
- L2: .agent/teams/{session-id}/phase-6/implementer-{N}/L2-summary.md
- L3: .agent/teams/{session-id}/phase-6/implementer-{N}/L3-full/
```

---

## Phase 6.5: Monitoring + Issue Resolution

### Monitoring Cadence

| Method | Cost | Frequency | When |
|--------|------|-----------|------|
| tmux visual | 0 tokens | Continuous | Always (primary) |
| TaskList | ~500 tokens | Every 15 min | Periodic check |
| Read L1 | ~2K tokens | On demand | When blocker reported |
| SendMessage query | ~200 tokens | On silence | >30 min no update |

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

For each implementer's completion report:

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
- **Two-stage review always** — spec compliance before code quality, within implementer scope
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
