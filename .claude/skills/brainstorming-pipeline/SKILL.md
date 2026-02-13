---
name: brainstorming-pipeline
description: Use when starting a new feature or task that needs Agent Teams pipeline orchestration through Phase 0-3 (PT Check, Discovery, Research, Architecture). Requires Agent Teams mode enabled and CLAUDE.md v5.0+.
argument-hint: "[feature description or topic]"
---

# Brainstorming Pipeline

Agent Teams-native Phase 0-3 orchestrator. Transforms a feature idea into a researched, validated architecture through structured team collaboration with understanding verification.

**Announce at start:** "I'm using brainstorming-pipeline to orchestrate Phase 0-3 for this feature."

**Core flow:** PT Check (Lead) → Discovery (Lead) → Deep Research (research-coordinator or direct researcher) → Architecture (architect or architecture-coordinator) → Clean Termination

## When to Use

```
Have a feature idea or task?
├── Working in Agent Teams mode? ─── no ──→ Use /brainstorming (solo)
├── yes
├── Need research + architecture? ── no ──→ Skip to /writing-plans directly
├── yes
└── Use /brainstorming-pipeline
```

**vs. brainstorming (solo):** This skill spawns actual teammates for research and architecture.
Solo brainstorming does everything inline as Lead. Use this when quality justifies the overhead.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Phase 1 Recon.

**Project Structure:**
!`ls -la /home/palantir/ 2>/dev/null | head -30`

**Recent Changes:**
!`cd /home/palantir && git log --oneline -15 2>/dev/null`

**Existing Plans:**
!`ls /home/palantir/docs/plans/ 2>/dev/null`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Active Branches:**
!`cd /home/palantir && git branch 2>/dev/null | head -10`

**Feature Request:** $ARGUMENTS

---

## A) Phase 0: PERMANENT Task Check

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
to B)     │     │
          ▼     ▼
        /permanent-tasks    Continue to B)
        creates PT-v1       without PT
        → then B)
```

If a PERMANENT Task exists, read it via TaskGet. Its content (user intent, codebase impact map,
architecture decisions, phase status, constraints) provides authoritative cross-phase context.
Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to B) Core Workflow.

If a PERMANENT Task exists but `$ARGUMENTS` describes a different feature than the PT's
User Intent, ask the user to clarify which feature to work on before proceeding.

---

## B) Phase 1-3: Core Workflow

### Phase 1: Discovery (Lead Only)

Lead-only phase. No teammates spawned.

#### 1.1 Structured Recon

Synthesize the Dynamic Context above with targeted investigation:

**Layer A — Codebase:** Project structure, config files, dependencies relevant to the feature.
**Layer B — Domain:** Prior designs in `docs/plans/`, MEMORY.md entries, infrastructure state.
**Layer C — Constraints:** Conflicts with existing systems, available teammate types, user's `$ARGUMENTS`.

No files are created in this step.

#### 1.2 Freeform Q&A with Category Awareness

Engage the user in natural conversation to understand the feature. One question at a time.
Multiple choice via `AskUserQuestion` preferred, open-ended when appropriate.

**Question count is not fixed.** Follow the conversation until sufficient understanding is reached.

Internally track which categories have been explored:

| Category | What to Understand |
|----------|-------------------|
| PURPOSE | What are we building and why? |
| SCOPE | Where are the boundaries? |
| CONSTRAINTS | Invariants, limitations, non-negotiables? |
| APPROACH | Which method or strategy? (triggers 1.3) |
| RISK | What failure scenarios exist? |
| INTEGRATION | How does this connect to existing systems? |

Categories may be covered in any order. Not all need explicit questions — natural conversation
coverage counts. Gently steer toward uncovered categories when the flow allows it.

**Feasibility Check** — After the user explains PURPOSE, validate before deep-diving:

```
PURPOSE answered
     │
├── Produces a concrete codebase deliverable?
│     ├── NO → "This sounds strategic. What would change in the codebase?"
│     └── YES ↓
├── Overlaps with completed work? (check git log, MEMORY.md)
│     ├── YES → "This overlaps with {X}. Extending it or new?"
│     └── NO ↓
├── Scope estimable? (can you name affected modules/files?)
│     ├── NO → "Too open-ended. What's the specific deliverable?"
│     └── YES ↓
└── FEASIBLE → continue Q&A for remaining categories
```

On failure: user refines (loop to failed criterion) or pivots (restart from PURPOSE).
User can override: "I want to proceed anyway" — log override in checkpoint.

#### 1.2.5 Phase 1 Checkpoint

After feasibility check passes (or user overrides) AND at least 2 Q&A categories are
covered, create a lightweight checkpoint to protect against auto-compact:

**`.agent/teams/{session-id}/phase-1/qa-checkpoint.md`:**

```markdown
# Phase 1 Q&A Checkpoint — {feature}

## Feasibility
{PASS | OVERRIDE with rationale}

## Categories Covered
{List which of PURPOSE/SCOPE/CONSTRAINTS/APPROACH/RISK/INTEGRATION are resolved}

## Key Decisions So Far
{Decisions locked in from conversation — approach not yet selected}

## Scope Direction (Draft)
{Early boundary draft — what's in, what's obviously out}
```

On recovery: read qa-checkpoint.md, resume Q&A from last covered category.

#### 1.3 Approach Exploration

When the conversation reaches strategy decisions, present a structured comparison:

```markdown
| Criterion         | Option A: {name}  | Option B: {name}  | Option C: {name} |
|-------------------|--------------------|--------------------|-------------------|
| Complexity        | LOW / MED / HIGH   |                    |                   |
| Risk              | LOW / MED / HIGH   |                    |                   |
| Phase 2 Research  | {scope desc}       |                    |                   |
| Phase 3 Arch      | {expected effort}  |                    |                   |
| File Count (est)  | ~N files           |                    |                   |
| Recommendation    | *                  |                    |                   |
```

Always 2-3 options. Lead with the recommended option and explain why.
After user selection, Q&A may continue for remaining categories.

#### 1.4 Scope Crystallization

When you judge sufficient understanding, propose a Scope Statement for user approval:

```markdown
## Scope Statement

**Goal:** {one sentence}
**In Scope:**
- {item}

**Out of Scope:**
- {item}

**Approach:** {selected option summary}
**Success Criteria:**
- {measurable outcome}

**Pipeline Tier:** TRIVIAL | STANDARD | COMPLEX
**Tier Rationale:**
- File count: ~N
- Module count: ~N
- Cross-boundary impact: YES/NO

**Phase 2 Research Needs:**
- {topic}

**Phase 3 Architecture Needs:**
- {decision}
```

If tier = TRIVIAL: skip Phases 2-3. Create lightweight scope statement,
route to `/agent-teams-execution-plan`.

- User rejects → return to Q&A. No iteration limit on Phase 1 dialogue.
- User approves → proceed to Gate 1.

#### 1.5 Gate 1

Evaluate per `gate-evaluation-standard.md` §6. Key criteria: Scope approved,
tier determined with rationale, research scope defined, Phase 3 entry clear,
no critical ambiguities.

**Gate Audit:** Optional for all tiers (see `gate-evaluation-standard.md` §6).

**On APPROVE** — create artifacts in this sequence:

**Step 1: Create PERMANENT Task**

Invoke `/permanent-tasks` with conversation context (Scope Statement + approach + tier).
Creates PT-v1 with full 5-section template. Note the PT task ID for Step 2.
Control returns to Lead automatically after skill completion.

**Step 2: Create GC-v1 (scratch)**

`.agent/teams/{session-id}/global-context.md`:

```yaml
---
version: GC-v1
pt_version: PT-v1
created: {YYYY-MM-DD}
feature: {feature-name}
tier: TRIVIAL | STANDARD | COMPLEX
---
```

Body: **## Scope** (verbatim from 1.4) · **## Phase Pipeline Status** (P1 COMPLETE,
P2/P3 PENDING) · **## Constraints** (from Q&A) · **## Decisions Log** (table:
#/Decision/Rationale/Phase)

> Note: GC is session-scoped scratch only. Cross-phase state is in PT. GC holds
> scope snapshot, pipeline status, and constraint/decision drafts for session recovery.

**Step 3: Create orchestration-plan.md**

`.agent/teams/{session-id}/orchestration-plan.md`:

```yaml
---
feature: {feature-name}
current_phase: 2
gc_version: GC-v1
pt_version: PT-v1
---
```

Body: **## Gate History** (P1 APPROVED + date) · **## Active Teammates** (none yet) ·
**## Phase 2 Plan** (research domains, count, strategy)

**Step 4: Create gate-record.yaml**

`.agent/teams/{session-id}/phase-1/gate-record.yaml` per `gate-evaluation-standard.md`
format. Include phase: 1, result: APPROVED, date, and pass/fail for each G1 criterion.

---

### Phase 2: Deep Research

Researcher teammates execute research. Lead verifies understanding before approving work.
Protocol execution follows CLAUDE.md §6 and §10.

#### 2.1 Research Scope Determination

Read PT §Phase 2 Research Needs (from /permanent-tasks) and determine:

| Domains | Researchers | Strategy |
|---------|-------------|----------|
| 1 | 1 | Single assignment |
| 2-3 independent | 2-3 | Parallel spawn |
| Dependent domains | 1 | Sequential or combined |

**Routing decision (CLAUDE.md §6 Agent Selection and Routing):**
- 1 researcher → Lead-direct (spawn and manage directly)
- 2+ researchers → spawn `research-coordinator` to manage them

#### 2.2 Team Setup

```
TeamCreate → team_name: "{feature-name}"
Update orchestration-plan.md with Phase 2 details
```

#### 2.3 Research Team Spawn + Verification

**Coordinator route (2+ researchers):**

1. Spawn research-coordinator:
   ```
   Task tool:
     subagent_type: "research-coordinator"
     team_name: "{feature-name}"
     name: "research-coord"
     mode: "default"
   ```
   Directive includes: research scope, PT-ID for TaskGet, Impact Map excerpt, worker types needed

2. Pre-spawn researchers (same team, choose agent type by research domain):
   - Local codebase analysis → `subagent_type: "codebase-researcher"`
   - External docs/web research → `subagent_type: "external-researcher"`
   - Inventory/gap analysis → `subagent_type: "auditor"`

3. Lead informs coordinator of worker names and research question assignments

4. Lead verifies coordinator understanding (1-3 probing questions, CLAUDE.md §6)

5. Coordinator verifies researchers' understanding (AD-11 delegation)

6. Coordinator distributes research questions and monitors progress

**Lead-direct route (1 researcher):**

Spawn researcher directly:

```
Task tool:
  subagent_type: "codebase-researcher" or "external-researcher"
  team_name: "{feature-name}"
  name: "researcher-1"
  mode: "default"

[DIRECTIVE] Phase 2: {research topic}
Files: {investigation targets}
PT-ID: {PERMANENT Task ID} | PT-v{N}
task-context.md: {research scope, deliverables, exclusions}
```

**Verification flow (Lead-direct, CLAUDE.md §6 "Verifying Understanding"):**
1. Researcher reads PERMANENT Task via TaskGet and confirms context receipt
2. Researcher explains their understanding of the task to Lead
3. Lead asks 1 probing question grounded in the Codebase Impact Map
4. Researcher defends with specific evidence
5. Lead verifies or rejects (max 3 attempts)

#### 2.4 Research Execution

Researchers work with: Read, Glob, Grep, WebSearch, WebFetch, context7, sequential-thinking.

**Coordinator route:** research-coordinator monitors progress and consolidates findings.
**Lead-direct route:** Lead monitors researcher progress directly.

**Output artifacts per researcher:**

```
.agent/teams/{session-id}/phase-2/researcher-{N}/
├── L1-index.yaml    (YAML, ≤50 lines — findings, gaps, recommendations)
├── L2-summary.md    (Markdown, ≤200 lines — narrative, analysis, evidence)
└── L3-full/         (raw data, code snippets, external docs)
```

#### 2.5 Gate 2

| # | Criterion |
|---|-----------|
| G2-1 | All researcher L1/L2 artifacts exist (or coordinator consolidated L1/L2) |
| G2-2 | All research needs from PT covered |
| G2-3 | Sufficient information for Phase 3 |
| G2-4 | No unresolved critical unknowns |
| G2-5 | L1/L2 quality meets standard |

**Gate Audit:** Optional for STANDARD/COMPLEX (see `gate-evaluation-standard.md` §6).

**On APPROVE:**
1. Update PERMANENT Task (PT-v{N} → PT-v{N+1}) via `/permanent-tasks`:
   - Add research findings to §Codebase Impact Map
   - Add discovered constraints to §Constraints
   - Update §phase_status.P2 = COMPLETE with l2_path
2. Update GC scratch: Phase Pipeline Status (session-scoped only)
3. Shutdown research-coordinator (if used) and researchers
4. Write `phase-2/gate-record.yaml`
5. Update orchestration-plan.md

**On ITERATE (max 3):** Re-direct researcher or spawn new one with gap instructions.

---

### Phase 3: Architecture

Architect teammate designs the system. Architecture receives the deepest scrutiny —
design flaws here multiply downstream.
Protocol execution follows CLAUDE.md §6 and §10.

#### 3.1 Architect Spawn

**Tier-based routing (D-001/D-005):**

**STANDARD tier (Lead-direct):**
```
Task tool:
  subagent_type: "architect"
  team_name: "{feature-name}"
  name: "architect-1"
  mode: "default"

[DIRECTIVE] Phase 3: {architecture task}
Files: {scope from P1 + P2 discoveries}
PT-ID: {PERMANENT Task ID} | PT-v{N}
task-context.md: {scope, research L2 summaries, architecture expectations, constraints}
```

**COMPLEX tier (coordinator route):**
```
1. Spawn architecture-coordinator (subagent_type: "architecture-coordinator")
2. Pre-spawn: structure-architect, interface-architect, risk-architect
3. Coordinator verifies workers and distributes architecture tasks
4. Each architect applies their ontological lens (ARE/RELATE/IMPACT)
5. Coordinator consolidates into unified architecture
```
For COMPLEX tier, Lead follows CLAUDE.md §6 Coordinator Management protocol.

#### 3.2 Understanding Verification

1. Architect reads PERMANENT Task via TaskGet and confirms context receipt
2. Architect explains their understanding of the task to Lead
3. Lead asks 3 probing questions grounded in the Codebase Impact Map, covering
   interconnections, failure modes, and dependency risks
4. Lead also asks: "Propose one alternative architecture and defend why yours is superior"
5. Architect defends each with specific evidence
6. Lead evaluates defense quality → verify or reject (max 3 attempts)

#### 3.3 Architecture Design

Architect submits [PLAN] before execution. Lead approves, then architect designs.

**Expected design content:**
- Component overview and hierarchy
- Interface definitions (contracts between components)
- Data flow (input → processing → output)
- Error handling strategy
- Key decisions with rationale and alternatives considered
- Phase 4 input requirements
- Risk register with mitigation

**Output artifacts:**

```
.agent/teams/{session-id}/phase-3/architect-1/
├── L1-index.yaml    (YAML, ≤50 lines — components, interfaces, decisions, risks)
├── L2-summary.md    (Markdown, ≤200 lines — narrative, trade-offs, Phase 4 readiness)
└── L3-full/
    └── architecture-design.md  (full design, no length limit)
```

#### 3.4 Gate 3

| # | Criterion |
|---|-----------|
| G3-1 | Architect L1/L2/L3 artifacts exist |
| G3-2 | Architecture satisfies Phase 1 Scope Statement |
| G3-3 | Phase 2 research findings reflected |
| G3-4 | Component interfaces clearly defined |
| G3-5 | Phase 4 entry requirements specified |
| G3-6 | No unresolved HIGH+ architectural risks |
| G3-7 | Decisions documented with rationale |

#### User Architecture Review

Present architecture summary to user before final gate decision:

```markdown
## Architecture Review

**Feature:** {name}
**Components:** {count} designed
**Key decisions:** {AD-1, AD-2 summaries}
**Top risks:** {3 highest risks from risk matrix}

Does this architecture align with your vision?
[Approve / Request changes / Discuss further]
```

- **Approve** → proceed to Gate Audit (if required) then On APPROVE
- **Request changes** → relay to architect with revision targets (no iteration limit for user-initiated)
- **Discuss further** → freeform Q&A, then re-present summary

**Gate Audit:** Mandatory for COMPLEX (see `gate-evaluation-standard.md` §6).
If audit required: spawn `gate-auditor` with G3 criteria and evidence paths.
Compare verdicts per §6 procedure. On disagreement → escalate to user.

**On APPROVE:**
1. Update PERMANENT Task (PT-v{N} → PT-v{N+1}) via `/permanent-tasks`:
   - Add §Architecture Decisions from architect's design
   - Update §Codebase Impact Map with architecture components
   - Update §phase_status.P3 = COMPLETE with l2_path
2. Update GC scratch: Phase Pipeline Status (session-scoped only)
3. Write `phase-3/gate-record.yaml`
4. Proceed to Clean Termination

**On ITERATE (max 3):** Specific redesign instructions to architect.

---

### Clean Termination

After Gate 3 APPROVE:

#### Output Summary

Present to user:

```markdown
## brainstorming-pipeline Complete (Phase 1-3)

**Feature:** {name}
**Complexity:** {level}

**Artifacts:**
- PERMANENT Task (PT-v{N}) — authoritative project context
- Session artifacts: .agent/teams/{session-id}/
- Phase 2: researcher L1/L2/L3
- Phase 3: architect L1/L2/L3 (architecture-design.md)

**Next:** Phase 4 (Detailed Design) — use `/agent-teams-write-plan`.
```

#### Shutdown Sequence

1. Shutdown architect: `SendMessage type: "shutdown_request"`
   (researchers already shut down after Gate 2)
2. `TeamDelete` — cleans team coordination files
3. Artifacts in `.agent/teams/{session-id}/` are preserved

---

## C) Interface

### Input
- **$ARGUMENTS:** Feature description or topic (seed for User Intent)
- **No predecessor L2:** This is the pipeline start — no prior phase output
- **No prior PT:** This skill creates the PERMANENT Task (via /permanent-tasks at Gate 1)

### Output
- **PT-v1** (created via /permanent-tasks): User Intent, Codebase Impact Map, Architecture Decisions, Phase Status (P1-P3=COMPLETE), Constraints
- **L1/L2/L3:** research-coordinator L1/L2/L3, architecture-coordinator L1/L2/L3 (COMPLEX) or researcher/architect L1/L2/L3 (STANDARD)
- **Gate records:** gate-record.yaml for Gates 1, 2, 3
- **GC scratch:** Phase Pipeline Status, execution metrics, version marker (session-scoped only)

### Next
Invoke `/agent-teams-write-plan "$ARGUMENTS"`.
Write-plan needs:
- PT §phase_status.P3.status == COMPLETE
- PT §phase_status.P3.l2_path → arch-coordinator/L2 §Downstream Handoff (contains Architecture Decisions, Constraints, Interface Contracts, Risks)

---

## D) Cross-Cutting

Follow CLAUDE.md §6 (Agent Selection and Routing), §9 (Compact Recovery), §10 (Integrity Principles) for all protocol decisions.
Follow `coordinator-shared-protocol.md` for coordinator management when COMPLEX tier is active.
Follow `gate-evaluation-standard.md` §6 for gate audit requirements.
All agents use `sequential-thinking` for analysis, judgment, and verification.

### Skill-Specific Error Handling

| Situation | Response |
|-----------|----------|
| Spawn failure | Retry once, then abort phase with user notification |
| Verification 3x rejection | Abort teammate, re-spawn with enhanced context |
| Gate 3x iteration | Abort phase, present partial results to user |

---

## Key Principles

- **One question at a time** — never overwhelm with multiple questions
- **Multiple choice preferred** — easier to answer than open-ended
- **Freeform Q&A** — question count driven by conversation, not formula
- **Category Awareness** — internal guide for Lead, not a constraint on user
- **Feasibility first** — validate topic produces actionable codebase deliverable before deep Q&A
- **Verification delegated** — CLAUDE.md §6/§10 owns protocol, skill owns orchestration
- **Clean termination** — no auto-chaining. User controls next step
- **Artifacts preserved** — all outputs survive in `.agent/teams/{session-id}/`
- **YAGNI** — remove unnecessary features from all designs
- **Explore alternatives** — always present 2-3 approaches before settling

## Never

- Skip understanding verification for any teammate
- Spawn teammates in Phase 1 (Lead only)
- Auto-chain to another skill after termination
- Proceed past a Gate without all criteria met
- Skip the feasibility check (unless user explicitly overrides)
- Let teammates write to Task API (TaskCreate/TaskUpdate)
- Rush through Q&A — follow the user's pace
