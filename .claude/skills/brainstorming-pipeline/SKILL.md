---
name: brainstorming-pipeline
description: Use when starting a new feature or task that needs Agent Teams pipeline orchestration through Phase 0-3 (PT Check, Discovery, Research, Architecture). Requires Agent Teams mode enabled and CLAUDE.md v5.0+.
argument-hint: "[feature description or topic]"
---

# Brainstorming Pipeline

Agent Teams-native Phase 0-3 orchestrator. Transforms a feature idea into a researched, validated architecture through structured team collaboration with understanding verification.

**Announce at start:** "I'm using brainstorming-pipeline to orchestrate Phase 0-3 for this feature."

**Core flow:** PT Check (Lead) → Discovery (Lead) → Deep Research (researcher) → Architecture (architect) → Clean Termination

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
!`cd /home/palantir && git branch 2>/dev/null`

**Feature Request:** $ARGUMENTS

---

## Phase 0: PERMANENT Task Check

Lightweight step (~500 tokens). No teammates spawned, no verification required.

Call `TaskList` and search for tasks with `[PERMANENT]` in their subject.

```
TaskList result
     │
┌────┼────────┐
none  1        2+
│     │        │
▼     ▼        ▼
Ask   Validate Match $ARGUMENTS against
User  match    each PT's User Intent
│     │        │
▼     │     ┌──┴──┐
Create│     match  no match
PT    │     │      │
│     ▼     ▼      ▼
│   Continue  Continue  AskUser:
│   to 1.1    to 1.1    "Multiple PTs found.
▼                       Which is for this session?"
/permanent-tasks
creates PT-v1
→ then 1.1
```

**PT validation:** When a [PERMANENT] task is found, compare its User Intent section
against `$ARGUMENTS`. If they describe the same feature, use it. If they clearly describe
a different feature (e.g., PT says "COW Pipeline" but $ARGUMENTS says "Ontology Framework"),
ask the user whether to use the existing PT or create a new one.

If a PERMANENT Task exists and matches, its content (user intent, codebase impact map, prior decisions)
provides additional context for Phase 1 discovery. Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to Phase 1.1.

---

## Phase 1: Discovery (Lead Only)

Lead-only phase. No teammates spawned.

Use `sequential-thinking` before every analysis step, judgment, and decision in this phase.

### 1.1 Structured Recon

Synthesize the Dynamic Context above with targeted investigation:

**Layer A — Codebase:** Project structure, config files, dependencies relevant to the feature.
**Layer B — Domain:** Prior designs in `docs/plans/`, MEMORY.md entries, infrastructure state.
**Layer C — Constraints:** Conflicts with existing systems, available teammate types, user's `$ARGUMENTS`.

Use `sequential-thinking` to synthesize Recon into an internal assessment before starting Q&A.
No files are created in this step.

### 1.2 Freeform Q&A with Category Awareness

Engage the user in natural conversation to understand the feature. One question at a time.
Multiple choice via `AskUserQuestion` preferred, open-ended when appropriate.

**Question count is not fixed.** Follow the conversation until sufficient understanding is reached.

Internally track which categories have been explored:

| Category | What to Understand |
|----------|--------------------|
| PURPOSE | What are we building and why? |
| SCOPE | Where are the boundaries? |
| CONSTRAINTS | Invariants, limitations, non-negotiables? |
| APPROACH | Which method or strategy? (triggers 1.3) |
| RISK | What failure scenarios exist? |
| INTEGRATION | How does this connect to existing systems? |

Categories may be covered in any order. Not all need explicit questions — natural conversation
coverage counts. Gently steer toward uncovered categories when the flow allows it.

Use `sequential-thinking` after each user response to analyze the answer and determine
the next question or whether to proceed to Scope Crystallization.

### 1.3 Approach Exploration

When the conversation reaches strategy decisions, present a structured comparison:

```markdown
| Criterion         | Option A: {name}  | Option B: {name}  | Option C: {name} |
|-------------------|--------------------|--------------------|--------------------|
| Complexity        | LOW / MED / HIGH   |                    |                    |
| Risk              | LOW / MED / HIGH   |                    |                    |
| Phase 2 Research  | {scope desc}       |                    |                    |
| Phase 3 Arch      | {expected effort}  |                    |                    |
| File Count (est)  | ~N files           |                    |                    |
| Recommendation    | *                  |                    |                    |
```

Always 2-3 options. Lead with the recommended option and explain why.
Use `sequential-thinking` to formulate the trade-off analysis before presenting.
After user selection, Q&A may continue for remaining categories.

### 1.3.5 Phase 1 Checkpoint

After Approach Exploration (1.3), create a lightweight checkpoint to protect against
auto-compact during extended Q&A:

**`.agent/teams/{session-id}/phase-1/qa-checkpoint.md`:**

```markdown
# Phase 1 Q&A Checkpoint — {feature}

## Categories Covered
{List which of PURPOSE/SCOPE/CONSTRAINTS/APPROACH/RISK/INTEGRATION are resolved}

## Approach Selected
{The comparison result from 1.3 and user's choice}

## Key Decisions So Far
{Decisions locked in from conversation}

## Scope Direction (Draft)
{Early boundary draft before formal Scope Statement}
```

This file enables recovery if compact occurs before Gate 1 creates formal artifacts.
On recovery, read qa-checkpoint.md and resume Q&A from the last covered category.

### 1.4 Scope Crystallization

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

**Estimated Complexity:** SIMPLE / MEDIUM / COMPLEX
**Phase 2 Research Needs:**
- {topic}

**Phase 3 Architecture Needs:**
- {decision}
```

Use `sequential-thinking` to synthesize all Q&A into the Scope Statement.

- User rejects → return to Q&A. No iteration limit on Phase 1 dialogue.
- User approves → proceed to Gate 1.

### 1.5 Gate 1

Evaluate before proceeding:

| # | Criterion |
|---|-----------|
| G1-1 | Scope Statement approved by user |
| G1-2 | Complexity classification confirmed |
| G1-3 | Phase 2 research scope defined |
| G1-4 | Phase 3 entry conditions clear |
| G1-5 | No unresolved critical ambiguities |

**On APPROVE** — create these files:

**`.agent/teams/{session-id}/global-context.md` (GC-v1):**

```markdown
---
version: GC-v1
created: {YYYY-MM-DD}
feature: {feature-name}
complexity: {SIMPLE|MEDIUM|COMPLEX}
---

# Global Context — {Feature Name}

## Scope
{Full Scope Statement from 1.4}

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: PENDING
- Phase 3: PENDING

## Constraints
{From Q&A}

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | {approach} | {reason} | P1 |
```

**`.agent/teams/{session-id}/orchestration-plan.md`:**

```markdown
---
feature: {feature-name}
current_phase: 2
gc_version: GC-v1
---

# Orchestration Plan

## Gate History
- Phase 1: APPROVED ({date})

## Active Teammates
(none yet — Phase 2 will spawn researchers)

## Phase 2 Plan
- Research domains: {from Scope Statement}
- Researcher count: {1-3}
- Strategy: {parallel or sequential}
```

**`.agent/teams/{session-id}/phase-1/gate-record.yaml`:**

```yaml
phase: 1
result: APPROVED
date: {YYYY-MM-DD}
criteria:
  G1-1: PASS
  G1-2: PASS
  G1-3: PASS
  G1-4: PASS
  G1-5: PASS
```

---

## Phase 2: Deep Research

Researcher teammates execute research. Lead verifies understanding before approving work.
Protocol execution follows CLAUDE.md §6 and §10.

Use `sequential-thinking` for all Lead decisions in this phase.

### 2.1 Research Scope Determination

Read GC-v1 "Phase 2 Research Needs" and determine:

| Domains | Researchers | Strategy |
|---------|-------------|----------|
| 1 | 1 | Single assignment |
| 2-3 independent | 2-3 | Parallel spawn |
| Dependent domains | 1 | Sequential or combined |

### 2.2 Team Setup

```
TeamCreate → team_name: "{feature-name}"
Update orchestration-plan.md with Phase 2 details
```

### 2.3 Researcher Spawn + Verification

For each researcher:

```
Task tool:
  subagent_type: "researcher"
  team_name: "{feature-name}"
  name: "researcher-{N}"
  mode: "default"

[DIRECTIVE] Phase 2: {research topic}
Files: {investigation targets}
PT-ID: {PERMANENT Task ID} | PT-v{N}
task-context.md: {research scope, deliverables, exclusions}
```

**Verification flow (CLAUDE.md §6 "Verifying Understanding"):**
1. Researcher reads PERMANENT Task via TaskGet and confirms context receipt
2. Researcher explains their understanding of the task to Lead
3. Lead asks 1 probing question grounded in the Codebase Impact Map
4. Researcher defends with specific evidence
5. Lead verifies or rejects (max 3 attempts)

All agents use `sequential-thinking` throughout.

### 2.4 Research Execution

Researchers work with: Read, Glob, Grep, WebSearch, WebFetch, context7, sequential-thinking.

**Output artifacts per researcher:**

```
.agent/teams/{session-id}/phase-2/researcher-{N}/
├── L1-index.yaml    (YAML, ≤50 lines — findings, gaps, recommendations)
├── L2-summary.md    (Markdown, ≤200 lines — narrative, analysis, evidence)
└── L3-full/         (raw data, code snippets, external docs)
```

### 2.5 Gate 2

| # | Criterion |
|---|-----------|
| G2-1 | All researcher L1/L2 artifacts exist |
| G2-2 | All research needs from GC-v1 covered |
| G2-3 | Sufficient information for Phase 3 |
| G2-4 | No unresolved critical unknowns |
| G2-5 | L1/L2 quality meets standard |

**On APPROVE:**
1. Update global-context.md → GC-v2 with these additions:
   ```markdown
   ## Research Findings
   {Per-domain key findings, gaps, and recommendations from researcher L2s}

   ## Codebase Constraints
   {Technical constraints discovered during research that affect architecture}

   ## Phase 3 Input
   {Architecture focus areas, expected decisions, known risks}
   ```
2. Shutdown researchers
3. Write `phase-2/gate-record.yaml`
4. Update orchestration-plan.md

**On ITERATE (max 3):** Re-direct researcher or spawn new one with gap instructions.

---

## Phase 3: Architecture

Architect teammate designs the system. Architecture receives the deepest scrutiny —
design flaws here multiply downstream.
Protocol execution follows CLAUDE.md §6 and §10.

Use `sequential-thinking` for all Lead decisions in this phase.

### 3.1 Architect Spawn

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

### 3.2 Understanding Verification

1. Architect reads PERMANENT Task via TaskGet and confirms context receipt
2. Architect explains their understanding of the task to Lead
3. Lead asks 3 probing questions grounded in the Codebase Impact Map, covering
   interconnections, failure modes, and dependency risks
4. Lead also asks: "Propose one alternative architecture and defend why yours is superior"
5. Architect defends each with specific evidence
6. Lead evaluates defense quality → verify or reject (max 3 attempts)

All agents use `sequential-thinking` throughout.

### 3.3 Architecture Design

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

### 3.4 Gate 3

| # | Criterion |
|---|-----------|
| G3-1 | Architect L1/L2/L3 artifacts exist |
| G3-2 | Architecture satisfies Phase 1 Scope Statement |
| G3-3 | Phase 2 research findings reflected |
| G3-4 | Component interfaces clearly defined |
| G3-5 | Phase 4 entry requirements specified |
| G3-6 | No unresolved HIGH+ architectural risks |
| G3-7 | Decisions documented with rationale |

**On APPROVE:**
1. Update global-context.md → GC-v3 with these additions:
   ```markdown
   ## Architecture Summary
   {Component overview, hierarchy, key interfaces from architect L2}

   ## Architecture Decisions
   | # | Decision | Rationale | Phase |
   {AD-{N} entries from architect's design}

   ## Phase 4 Entry Requirements
   {Implementation constraints, verification criteria, expected file count}
   ```
2. Write `phase-3/gate-record.yaml`
3. Proceed to Clean Termination

**On ITERATE (max 3):** Specific redesign instructions to architect.

---

## Clean Termination

After Gate 3 APPROVE:

### Output Summary

Present to user:

```markdown
## brainstorming-pipeline Complete (Phase 1-3)

**Feature:** {name}
**Complexity:** {level}

**Artifacts:**
- PERMANENT Task (PT-v{N}) — authoritative project context
- global-context.md (GC-v3) — session artifacts
- orchestration-plan.md
- Phase 2: researcher L1/L2/L3
- Phase 3: architect L1/L2/L3 (architecture-design.md)

**Location:** .agent/teams/{session-id}/

**Next:** Phase 4 (Detailed Design) — use `/agent-teams-write-plan`.
Input: the artifacts above. Update PERMANENT Task with `/permanent-tasks` if scope evolved.
```

### Shutdown Sequence

1. Shutdown architect: `SendMessage type: "shutdown_request"`
   (researchers already shut down after Gate 2)
2. `TeamDelete` — cleans team coordination files
3. Artifacts in `.agent/teams/{session-id}/` are preserved

---

## Cross-Cutting Requirements

### RTD Index

At each Decision Point in this phase, update the RTD index:
1. Update `current-dp.txt` with the new DP number
2. Write an rtd-index.md entry with WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS
3. Update the frontmatter (current_phase, current_dp, updated, total_entries)

Decision Points for this skill:
- DP: Scope crystallization (1.4 approval)
- DP: Approach selection (1.3 user choice)
- DP: Researcher spawn (2.3)
- DP: Gate 1 evaluation
- DP: Gate 2 evaluation
- DP: Architect spawn (3.1)
- DP: Gate 3 evaluation

### Sequential Thinking

All agents (Lead and teammates) use `mcp__sequential-thinking__sequentialthinking` for
analysis, judgment, design, and verification throughout the entire pipeline.

| Agent | When |
|-------|------|
| Lead (P1) | After Recon, after each user response, before Scope Statement, at Gates |
| Lead (P2-3) | Understanding verification, probing questions, Gate evaluation, PT/GC updates |
| Researcher (P2) | Research strategy, findings synthesis, L2 writing |
| Architect (P3) | Component design, trade-off analysis, interface definition |

### Error Handling

| Situation | Response |
|-----------|----------|
| Spawn failure | Retry once, then abort phase with user notification |
| Verification 3x rejection | Abort teammate, re-spawn with enhanced context |
| Gate 3x iteration | Abort phase, present partial results to user |
| Context compact | Follow CLAUDE.md §9 Compact Recovery |
| User cancellation | Graceful shutdown all teammates, preserve artifacts |

### Compact Recovery

Follows CLAUDE.md §9:
- Lead: Read orchestration-plan → task list → gate records → L1 indexes → re-inject
- Teammates: Receive injection → read own L1/L2/L3 → re-submit Impact Analysis

---

## Key Principles

- **One question at a time** — never overwhelm with multiple questions
- **Multiple choice preferred** — easier to answer than open-ended
- **Freeform Q&A** — question count driven by conversation, not formula
- **Category Awareness** — internal guide for Lead, not a constraint on user
- **Sequential thinking always** — structured reasoning at every decision point
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
- Let teammates write to Task API (TaskCreate/TaskUpdate)
- Present the Scope Statement without using sequential-thinking first
- Rush through Q&A — follow the user's pace
