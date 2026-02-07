---
name: agent-teams-write-plan
description: Use after brainstorming-pipeline to produce a detailed implementation plan (Phase 4). Takes GC-v3 + architecture artifacts as input, spawns an architect to create a 10-section CH-001-format plan. Requires Agent Teams mode and CLAUDE.md v3.0+.
argument-hint: "[brainstorming-session-id or path]"
---

# Agent Teams Write Plan

Phase 4 (Detailed Design) orchestrator. Transforms brainstorming-pipeline architecture output into a concrete implementation plan through a DIA-verified architect teammate.

**Announce at start:** "I'm using agent-teams-write-plan to orchestrate Phase 4 (Detailed Design) for this feature."

**Core flow:** Input Discovery → Team Setup → Architect Spawn + DIA → Plan Generation → Gate 4 → Clean Termination

## When to Use

```
Have architecture output from brainstorming-pipeline?
├── Working in Agent Teams mode? ─── no ──→ Use /writing-plans (solo)
├── yes
├── GC-v3 with Phase 3 COMPLETE? ── no ──→ Run /brainstorming-pipeline first
├── yes
└── Use /agent-teams-write-plan
```

**vs. writing-plans (solo):** This skill spawns an architect teammate with full DIA verification (TIER 2 + LDAP MAXIMUM). Solo writing-plans has the Lead write the plan directly with no verification. Use this when the feature complexity justifies the overhead.

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

## Phase 4.1: Input Discovery + Validation

LDAP intensity: NONE (Lead-only step). No teammates spawned yet.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find brainstorming-pipeline output:

1. Look for `.agent/teams/*/global-context.md` files with `Phase 3: COMPLETE`
2. If `$ARGUMENTS` provides a session-id or path, use that directly
3. If multiple candidates found, present options via `AskUserQuestion`
4. If single candidate, confirm with user: "Found brainstorming output at {path}. Use this?"
5. If no candidates, inform user: "No brainstorming-pipeline output found. Run /brainstorming-pipeline first."

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

## Phase 4.3: Architect Spawn + DIA

DIA: TIER 2 + LDAP MAXIMUM (3Q + alternative). Protocol execution follows CLAUDE.md [PERMANENT] §7.

Use `sequential-thinking` for all Lead decisions in this phase.

### Spawn

```
Task tool:
  subagent_type: "architect"
  team_name: "{feature-name}-write-plan"
  name: "architect-1"
  mode: "plan"
```

### [DIRECTIVE] Construction

The directive must include these 4 context layers:

1. **GC-v3 full embedding** — the entire global-context.md (CIP protocol)
2. **Phase 3 Architect L2-summary.md** — embedded inline in task-context for architecture narrative
3. **Architecture Design path** — `{source}/phase-3/architect-1/L3-full/architecture-design.md` for architect to Read
4. **CH-001 Exemplar path** — `docs/plans/2026-02-07-ch001-ldap-implementation.md` for format reference

Task-context must instruct architect to:
- Read architecture-design.md and CH-001 exemplar before starting
- Follow the 10-section template (§1-§10)
- Use Read-First-Write-Second workflow for §5
- Tag all §5 specs with Verification Level
- Include AC-0 in every §4 task
- Include V6 Code Plausibility in §7
- Dual-save plan to docs/plans/ and L3-full/
- Use sequential-thinking for all design decisions

### DIA Flow

1. Architect confirms context receipt
2. Architect submits Impact Analysis (TIER 2: 4 sections, 7 RC)
3. Lead verifies RC checklist
4. Lead issues LDAP challenge (MAXIMUM: 3Q + ALTERNATIVE_DEMAND)
   - Q1-Q3: Context-specific questions from 7 LDAP categories
   - +ALT: "Propose one alternative plan decomposition and defend current"
5. Architect defends with specific evidence
6. Lead verifies or rejects (max 3 attempts)

All agents use `sequential-thinking` throughout.

---

## Phase 4.4: Plan Generation

After [IMPACT_VERIFIED], architect produces the implementation plan.

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

Architect reports `[STATUS] Phase 4 | COMPLETE` via SendMessage.

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
2. Write phase-4/gate-record.yaml
3. Proceed to Clean Termination

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

**Implementation Plan:** docs/plans/{filename}
**Artifacts:** .agent/teams/{session-id}/

**Next:** Phase 5 (Plan Validation) — validates the implementation plan.
Input: GC-v4 + plan document.
```

### Shutdown

1. Shutdown architect-1: `SendMessage type: "shutdown_request"`
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`

---

## Cross-Cutting

### Sequential Thinking
All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, design, and verification.

### Error Handling
| Situation | Response |
|-----------|----------|
| No brainstorming output | Inform user, suggest /brainstorming-pipeline |
| GC-v3 incomplete | Abort with missing section list |
| Spawn failure | Retry once, abort with notification |
| DIA 3x rejection | Abort architect, re-spawn |
| Gate 4 3x iteration | Abort, present partial results |
| Context compact | CLAUDE.md §8 recovery |
| User cancellation | Graceful shutdown, preserve artifacts |

### Compact Recovery
- Lead: orchestration-plan → task list → gate records → L1 → re-inject
- Architect: receive injection → read L1/L2/L3 → re-submit Impact Analysis

## Key Principles

- DRY, YAGNI, TDD — preserved from writing-plans
- Exact file paths always — even more critical with multiple implementers
- Complete code in plan — with Verification Level tags for confidence signaling
- AC-0 mandatory — every task starts with plan-vs-reality verification
- V6 Code Plausibility — compensates for architect's inability to run code
- Sequential thinking always — structured reasoning at every decision point
- DIA delegated — CLAUDE.md [PERMANENT] owns protocol, skill owns orchestration
- Clean termination — no auto-chaining to Phase 5
- Dual-save — docs/plans/ (permanent) + .agent/teams/ (session)

## Never

- Skip DIA verification for the architect
- Auto-chain to Phase 5 after termination
- Proceed past Gate 4 without all criteria met
- Let the architect write to Task API
- Skip input validation (GC-v3 must exist with Phase 3 COMPLETE)
- Omit AC-0 from any TaskCreate definition
- Omit V6 from the validation checklist
- Write §5 specs without reading target files first
