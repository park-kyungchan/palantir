---
name: agent-teams-write-plan
description: Use after brainstorming-pipeline to produce a detailed implementation plan (Phase 4). Takes architecture output and PERMANENT Task as input, spawns an architect to create a 10-section plan. Requires Agent Teams mode and CLAUDE.md v6.0+.
argument-hint: "[brainstorming-session-id or path]"
---

# Agent Teams Write Plan

Phase 4 (Detailed Design) orchestrator. Transforms brainstorming-pipeline architecture output into a concrete implementation plan through a verified architect teammate.

**Announce at start:** "I'm using agent-teams-write-plan to orchestrate Phase 4 (Detailed Design) for this feature."

**Core flow:** PT Check (Lead) → Input Discovery → Team Setup → Architect Spawn + Verification → Plan Generation → Gate 4 → Clean Termination

## When to Use

```
Have architecture output from brainstorming-pipeline?
├── Working in Agent Teams mode? ─── no ──→ Use /writing-plans (solo)
├── yes
├── GC-v3 with Phase 3 COMPLETE? ── no ──→ Run /brainstorming-pipeline first
├── yes
└── Use /agent-teams-write-plan
```

**vs. writing-plans (solo):** This skill spawns an architect teammate with full understanding verification. Solo writing-plans has the Lead write the plan directly with no verification. Use this when the feature complexity justifies the overhead.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Previous Pipeline Output:**
!`ls -d /home/palantir/.agent/teams/*/global-context.md 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "---"; echo "Dir: $dir"; head -8 "$f"; echo ""; done`

**Existing Plans:**
!`ls /home/palantir/docs/plans/ 2>/dev/null`

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
to 4.1    │     │
          ▼     ▼
        /permanent-tasks    Continue to 4.1
        creates PT-v1       without PT
        → then 4.1
```

If a PERMANENT Task exists, its content (user intent, codebase impact map, prior decisions)
provides additional context for Phase 4 design. Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to Phase 4.1.

---

## Phase 4.1: Input Discovery + Validation

No teammates spawned yet. Lead-only step.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find brainstorming-pipeline output:

1. Look for `.agent/teams/*/global-context.md` files with `Phase 3: COMPLETE`
2. If `$ARGUMENTS` provides a session-id or path, use that directly
3. If multiple candidates found, present options via `AskUserQuestion`
4. If single candidate, confirm with user: "Found brainstorming output at {path}. Use this?"
5. If no candidates, inform user: "No brainstorming-pipeline output found. Run /brainstorming-pipeline first."

If a PERMANENT Task was loaded in Phase 0, use its Codebase Impact Map and user intent
to inform validation and provide additional context to the architect.

### Validation

After identifying the source directory, verify:

| # | Check | On Failure |
|---|-------|------------|
| V-1 | `global-context.md` exists with `Phase 3: COMPLETE` | Abort: "GC-v3 not found or Phase 3 not complete" |
| V-2 | `phase-3/architect-1/L3-full/architecture-design.md` exists | Abort: "Architecture design not found" |
| V-3 | GC-v3 contains Scope, Component Map, Interface Contracts sections | Abort: "GC-v3 missing required sections: {list}" |

Use `sequential-thinking` to evaluate validation results.

On all checks PASS → proceed to 4.2.

---

## Phase 4.2: Team Setup

```
TeamCreate:
  team_name: "{feature-name}-write-plan"
```

Create orchestration-plan.md and copy GC-v3 to new session directory.

---

## Phase 4.3: Architect Spawn + Verification

Protocol execution follows CLAUDE.md §6 and §10.

Use `sequential-thinking` for all Lead decisions in this phase.

### Spawn

```
Task tool:
  subagent_type: "architect"
  team_name: "{feature-name}-write-plan"
  name: "architect-1"
  mode: "default"
```

### Directive Construction

The directive must include these context layers:

1. **PERMANENT Task ID** — `PT-ID: {task_id} | PT-v{N}` so architect can call TaskGet for full context
2. **GC-v3 full embedding** — the entire global-context.md (session-level artifacts)
3. **Phase 3 Architect L2-summary.md** — embedded inline in task-context for architecture narrative
4. **Architecture Design path** — `{source}/phase-3/architect-1/L3-full/architecture-design.md` for architect to Read
5. **CH-001 Exemplar path** — `docs/plans/2026-02-07-ch001-ldap-implementation.md` for format reference

Task-context must instruct architect to:
- Read the PERMANENT Task via TaskGet for full project context (user intent, impact map)
- Read architecture-design.md and CH-001 exemplar before starting
- Follow the 10-section template (§1-§10)
- Use Read-First-Write-Second workflow for §5
- Tag all §5 specs with Verification Level
- Include AC-0 in every §4 task
- Include V6 Code Plausibility in §7
- Dual-save plan to docs/plans/ and L3-full/
- Use sequential-thinking for all design decisions

### Understanding Verification

1. Architect reads PERMANENT Task via TaskGet and confirms context receipt
2. Architect explains their understanding of the task to Lead
3. Lead asks 3 probing questions grounded in the Codebase Impact Map, covering
   interconnections, failure modes, and dependency risks
4. Lead also asks: "Propose one alternative plan decomposition and defend current"
5. Architect defends each with specific evidence
6. Lead evaluates defense quality → verify or reject (max 3 attempts)

All agents use `sequential-thinking` throughout.

---

## Phase 4.4: Plan Generation

After understanding is verified, architect produces the implementation plan.

Architect works with: Read, Glob, Grep, Write, sequential-thinking.

**Expected output:**

```
docs/plans/YYYY-MM-DD-{feature-name}.md
  → Complete 10-section implementation plan

.agent/teams/{session-id}/phase-4/architect-1/
├── L1-index.yaml    (≤50 lines — tasks, files, decisions, risks)
├── L2-summary.md    (≤200 lines — design narrative, trade-offs)
└── L3-full/
    └── implementation-plan.md  (copy of docs/plans/ file)
```

Architect reports completion via SendMessage.

---

## Phase 4.5: Gate 4

Use `sequential-thinking` for all gate evaluation.

### Criteria

| # | Criterion |
|---|-----------|
| G4-1 | Plan exists in docs/plans/ and L3-full/ |
| G4-2 | Plan follows 10-section template |
| G4-3 | §5 specs reference real files (spot-check via Read) |
| G4-4 | §3 file ownership is non-overlapping |
| G4-5 | §4 tasks all have AC-0 |
| G4-6 | §7 includes V6 Code Plausibility |
| G4-7 | §5 specs have Verification Level tags |
| G4-8 | Plan satisfies GC-v3 Phase 4 Entry Requirements |

### User Review

Present plan summary to user before final approval:

```markdown
## Implementation Plan Ready

**Feature:** {name}
**Plan:** docs/plans/{filename}
**Tasks:** {N} tasks, {M} implementers
**Files:** {create} new, {modify} modified

Shall I proceed with Gate 4 approval?
```

### On APPROVE
1. GC-v3 → GC-v4 (add Implementation Plan Reference, Task Decomposition,
   File Ownership Map, Phase 6 Entry Conditions, Phase 5 Validation Targets,
   Commit Strategy; update Phase Pipeline Status)
2. Update PERMANENT Task (PT-v{N} → PT-v{N+1}) with Implementation Plan Reference,
   Task Decomposition summary, File Ownership Map, and Phase 4 COMPLETE status
3. Write phase-4/gate-record.yaml
4. Proceed to Clean Termination

### On ITERATE (max 3)
- Relay specific revision instructions to architect
- Architect revises and resubmits

---

## Clean Termination

After Gate 4 APPROVE:

### Output Summary

```markdown
## agent-teams-write-plan Complete (Phase 4)

**Feature:** {name}
**Complexity:** {level}

**Artifacts:**
- PERMANENT Task (PT-v{N}) — authoritative project context (updated with plan reference)
- Implementation Plan: docs/plans/{filename}
- Session artifacts: .agent/teams/{session-id}/

**Next:** Phase 5 (Plan Validation) — validates the implementation plan.
Input: GC-v4 + plan document. Update PERMANENT Task with `/permanent-tasks` if scope evolved.
```

### Shutdown

1. Shutdown architect-1: `SendMessage type: "shutdown_request"`
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`

---

## Cross-Cutting

### RTD Index

At each Decision Point in this phase, update the RTD index:
1. Update `current-dp.txt` with the new DP number
2. Write an rtd-index.md entry with WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS
3. Update the frontmatter (current_phase, current_dp, updated, total_entries)

Decision Points for this skill:
- DP: Input validation and plan scope
- DP: Architect spawn
- DP: Plan completion assessment
- DP: Gate 4 evaluation

### Sequential Thinking
All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, design, and verification.

### Error Handling
| Situation | Response |
|-----------|----------|
| No brainstorming output | Inform user, suggest /brainstorming-pipeline |
| GC-v3 incomplete | Abort with missing section list |
| Spawn failure | Retry once, abort with notification |
| Understanding verification 3x rejection | Abort architect, re-spawn |
| Gate 4 3x iteration | Abort, present partial results |
| Context compact | CLAUDE.md §9 recovery |
| User cancellation | Graceful shutdown, preserve artifacts |

### Compact Recovery
- Lead: orchestration-plan → task list → gate records → L1 → re-inject
- Architect: call TaskGet on PERMANENT Task for immediate self-recovery, then read own L1/L2/L3 and re-submit understanding

## Key Principles

- DRY, YAGNI, TDD — preserved from writing-plans
- Exact file paths always — even more critical with multiple implementers
- Complete code in plan — with Verification Level tags for confidence signaling
- AC-0 mandatory — every task starts with plan-vs-reality verification
- V6 Code Plausibility — compensates for architect's inability to run code
- Sequential thinking always — structured reasoning at every decision point
- Protocol delegated — CLAUDE.md owns verification protocol, skill owns orchestration
- Clean termination — no auto-chaining to Phase 5
- Dual-save — docs/plans/ (permanent) + .agent/teams/ (session)

## Never

- Skip understanding verification for the architect
- Skip Phase 0 PERMANENT Task check
- Auto-chain to Phase 5 after termination
- Proceed past Gate 4 without all criteria met
- Let the architect write to Task API
- Skip input validation (GC-v3 must exist with Phase 3 COMPLETE)
- Omit AC-0 from any TaskCreate definition
- Omit V6 from the validation checklist
- Write §5 specs without reading target files first
