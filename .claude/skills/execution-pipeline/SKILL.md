---
name: execution-pipeline
description: Use after agent-teams-write-plan (or plan-validation) to execute an implementation plan (Phase 6). Spawns adaptive implementers with DIA v3.0 enforcement, two-stage review, and Gate 6 evaluation. Requires Agent Teams mode and CLAUDE.md v3.0+.
argument-hint: "[session-id or path to implementation plan]"
---

# Execution Pipeline

Phase 6 (Implementation) orchestrator. Transforms an implementation plan into working code through DIA-verified implementer teammates with integrated two-stage review.

**Announce at start:** "I'm using execution-pipeline to orchestrate Phase 6 (Implementation) for this feature."

**Core flow:** Input Discovery → Team Setup → Adaptive Spawn + DIA → Task Execution + Review → Gate 6 → Clean Termination

## When to Use

```
Have an implementation plan from agent-teams-write-plan?
├── Working in Agent Teams mode? ─── no ──→ Use /executing-plans (solo)
├── yes
├── GC-v4 with Phase 4 COMPLETE? ── no ──→ Run /agent-teams-write-plan first
├── yes
├── Plan validated (Phase 5)?
│   ├── yes ──→ Use /execution-pipeline
│   └── no ──→ Recommended: run plan-validation first, or proceed at own risk
└── Use /execution-pipeline
```

**vs. executing-plans (solo):** This skill spawns persistent implementer teammates with DIA verification, adaptive parallelism, and two-stage review. Solo executing-plans runs everything in a single agent sequentially. Use this when the plan has 2+ tasks or requires file ownership isolation.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Implementation Plans:**
!`ls docs/plans/*-implementation.md 2>/dev/null; ls docs/plans/*-plan.md 2>/dev/null`

**Previous Pipeline Output:**
!`ls -d .agent/teams/*/global-context.md 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "---"; echo "Dir: $dir"; head -8 "$f"; echo ""; done`

**Git Status:**
!`cd /home/palantir && git diff --name-only 2>/dev/null | head -20`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Feature Input:** $ARGUMENTS

---

## Phase 6.1: Input Discovery + Validation

LDAP intensity: NONE (Lead-only step). No teammates spawned.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find agent-teams-write-plan output:

1. Look for `.agent/teams/*/global-context.md` files with `Phase 4: COMPLETE` or `Phase 5: COMPLETE`
2. If `$ARGUMENTS` provides a session-id or path, use that directly
3. If multiple candidates found, present options via `AskUserQuestion`
4. If single candidate, confirm with user: "Found implementation plan output at {path}. Use this?"
5. If no candidates, inform user: "No implementation plan found. Run /agent-teams-write-plan first."

### Validation

After identifying the source, verify:

| # | Check | On Failure |
|---|-------|------------|
| V-1 | `global-context.md` exists with Phase 4 or 5 COMPLETE | Abort: "GC-v4 not found or Phase 4 not complete" |
| V-2 | Implementation plan file exists in `docs/plans/` | Abort: "Implementation plan not found" |
| V-3 | Plan contains §3 (File Ownership) and §4 (TaskCreate Definitions) | Abort: "Plan missing required sections: {list}" |
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

## Phase 6.3: Adaptive Spawn + DIA

DIA: TIER 1 + LDAP HIGH (2Q). Protocol execution follows CLAUDE.md [PERMANENT] §7.

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
- Semantic Integrity Check

Set up dependencies via addBlockedBy/addBlocks.

### Implementer Spawn + DIA

For each implementer:

```
Task tool:
  subagent_type: "implementer"
  team_name: "{feature-name}-execution"
  name: "implementer-{N}"
  mode: "plan"
```

#### [DIRECTIVE] Construction

The directive must include these context layers:

1. **GC-v4 full embedding** — the entire global-context.md (CIP protocol)
2. **Task-context.md** — assignment, file ownership, task list, plan §5 specs for assigned tasks
3. **Review instructions** — two-stage review protocol, fix loop rules, reviewer prompt templates
4. **Implementation plan path** — for implementer to Read directly

Task-context must instruct implementer to:
- Read the implementation plan before starting (especially §5 for their tasks)
- Execute tasks in topological order within their component
- Run self-review after each task using implementer.md checklist
- Dispatch spec-reviewer then code-reviewer subagents (two-stage, ordered)
- Include reviewer raw output in L2-summary.md
- Write L1/L2/L3 after each task completion (Pre-Compact Obligation)
- Report [STATUS] COMPLETE per task with structured report
- Report [STATUS] BLOCKED immediately if cross-boundary issue found

#### DIA Flow

1. Implementer confirms context receipt: `[STATUS] Phase 6 | CONTEXT_RECEIVED | GC-v4`
2. Implementer submits Impact Analysis (TIER 1: 6 sections, 10 RC)
3. Lead verifies RC checklist (10 items)
4. Lead issues LDAP challenge (HIGH: 2 questions)
   - Categories: RIPPLE_TRACE, FAILURE_MODE, DEPENDENCY_RISK, INTERCONNECTION_MAP
5. Implementer defends with specific evidence
6. Lead verifies or rejects (max 3 attempts)
7. On [IMPACT_VERIFIED]: implementer submits [PLAN], Lead approves → execution begins

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
             └── 3x FAIL → [STATUS] BLOCKED
6. Dispatch code-reviewer subagent (Stage 2)
   ├── PASS → proceed to completion
   └── FAIL → fix → re-dispatch (max 3)
             └── 3x FAIL → [STATUS] BLOCKED
7. Write/update L1/L2/L3 (include reviewer raw output in L2)
8. Report [STATUS] Phase 6 | COMPLETE | Task {N}: {summary}
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
- If FAIL: specific issues with file:line references
- Summary: what was checked and what was found
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

### Implementer [STATUS] COMPLETE Report Format

```
[STATUS] Phase 6 | COMPLETE | Task {N}: {summary}

## Implementation Summary
- Files created: {list}
- Files modified: {list}
- Tests: {count} added/modified, all passing

## Spec Compliance Review
- Result: PASS
- Issues found and resolved: {count}
- Fix iterations: {N}/3

## Code Quality Review
- Result: PASS
- Assessment: Ready to merge
- Critical issues resolved: {count}
- Important issues resolved: {count}

## Self-Review Findings
- {any issues found and fixed}

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
| [STATUS] BLOCKED (cross-boundary) | Follow AD-4 Cross-Boundary Escalation Protocol |
| [STATUS] BLOCKED (fix loop exhausted) | Evaluate: revise plan spec / reassign / ABORT |
| [STATUS] CONTEXT_PRESSURE | Shutdown implementer → re-spawn with L1/L2 injection |
| >30 min silence | Send status query to implementer |
| >40 min silence | Escalate: Read L1, check if stuck, consider intervention |
| Implementer deviation from spec | [CONTEXT-UPDATE] with correction → implementer [ACK-UPDATE] |

### Cross-Boundary Issue Escalation

When implementer reports `[STATUS] BLOCKED | Need file outside ownership`:

```
Stage 1: Read the BLOCKED report — understand the issue
Stage 2: Determine root cause:
  Case A (other implementer deviation) → [CONTEXT-UPDATE] to that implementer
  Case B (plan spec error) → bump GC → [CONTEXT-UPDATE] to all affected
Stage 3: Wait for [ACK-UPDATE] from affected implementer(s)
Stage 4: Verify fix → unblock original implementer
```

---

## Phase 6.6: Gate 6

Use `sequential-thinking` for all gate evaluation.

### Per-Task Evaluation

For each implementer's [STATUS] COMPLETE:

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

### GC-v4 → GC-v5 Update

Add to global-context.md:

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
## execution-pipeline Complete (Phase 6)

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

**Artifacts:** .agent/teams/{session-id}/
**Global Context:** GC-v5

**Next:** Phase 7 (Testing) — use the verification-pipeline skill.
Input: GC-v5 + implementer artifacts.
```

### Shutdown Sequence

1. Shutdown all implementers: `SendMessage type: "shutdown_request"` to each
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`

---

## Cross-Cutting Requirements

### Sequential Thinking

All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, and verification.

| Agent | When |
|-------|------|
| Lead | Adaptive spawn calculation, DIA verification, LDAP challenges, Gate 6, issue resolution |
| Implementer | Impact analysis, plan submission, complex implementation decisions, self-review |

### Error Handling

| Situation | Response |
|-----------|----------|
| No implementation plan found | Inform user, suggest /agent-teams-write-plan |
| GC-v4 incomplete | Abort with missing section list |
| Spawn failure | Retry once, abort with notification |
| DIA 3x rejection | Abort implementer, re-spawn with enhanced context |
| Fix loop 3x exhaustion | Implementer reports BLOCKED, Lead evaluates |
| Gate 6 3x iteration | Abort, present partial results to user |
| Cross-boundary issue | Follow escalation protocol (Phase 6.5) |
| Context compact | CLAUDE.md §8 recovery |
| Context pressure | Shutdown implementer, re-spawn with L1/L2 injection |
| User cancellation | Graceful shutdown all implementers, preserve artifacts |

### Compact Recovery

- Lead: orchestration-plan → task list → gate records → L1 indexes → re-inject
- Implementer: receive injection → read L1/L2/L3 → re-submit Impact Analysis

---

## Key Principles

- **Adaptive parallelism** — spawn only as many implementers as independent components require
- **Two-stage review always** — spec compliance before code quality, within implementer scope
- **Fix loop bounded** — max 3 per stage, escalate on exhaustion
- **File ownership strict** — no cross-boundary writes, ever (except integrator)
- **3-Layer Defense** — automated review + self-report + risk-proportional spot-check
- **Pre-Compact Obligation** — write L1/L2/L3 after every task, not only at ~75%
- **DIA delegated** — CLAUDE.md [PERMANENT] owns protocol, skill owns orchestration
- **Clean termination** — no auto-chaining to Phase 7
- **Sequential thinking always** — structured reasoning at every decision point
- **Artifacts preserved** — all outputs survive in `.agent/teams/{session-id}/`

## Never

- Skip DIA verification for any implementer
- Allow concurrent editing of the same file by multiple implementers
- Dispatch code-reviewer before spec-reviewer passes
- Let implementers write to Task API (TaskCreate/TaskUpdate)
- Auto-chain to Phase 7 after termination
- Proceed past Gate 6 without all criteria met
- Trust review reports without L2 raw output evidence
- Fix cross-boundary issues without Lead coordination
- Exceed fix loop max (3) without escalation
- Spawn more than 4 implementers
