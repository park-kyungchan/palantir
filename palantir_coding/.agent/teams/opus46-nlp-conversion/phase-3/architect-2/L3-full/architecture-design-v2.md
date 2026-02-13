# Architecture Design v2 — Opus 4.6 Native NLP Conversion + PERMANENT Task Integration

**Architect:** architect-2 | **Phase:** 3 (Revision) | **GC:** v4 | **Date:** 2026-02-08
**Upstream:** architect-1 L3 (NLP conversion) + permanent-tasks-design.md (GC→PT)

---

## Table of Contents
1. [Design Philosophy](#1-design-philosophy)
2. [Architecture Decisions](#2-architecture-decisions)
3. [Deliverable 1: CLAUDE.md v6.0](#3-deliverable-1-claudemd-v60)
4. [Deliverable 2: agent-common-protocol.md v2.0](#4-deliverable-2-agent-common-protocolmd-v20)
5. [Deliverable 3: Agent .md Template Design](#5-deliverable-3-agent-md-template-design)
6. [Deliverable 4: DIA v6.0 Specification](#6-deliverable-4-dia-v60-specification)
7. [Deduplication Plan](#7-deduplication-plan)
8. [Implementation Task Breakdown](#8-implementation-task-breakdown)
9. [Risk Assessment](#9-risk-assessment)

---

## 1. Design Philosophy

### Core Principle
Convert from "prevent failure by over-enforcement" to "enable success by clear criteria + trust + spot-check."

### Three Design Axioms (from original L3 — preserved)

**Axiom 1: Say it once, say it well.**
Every behavioral requirement appears in exactly one location. Other files reference, never repeat.
The "single source of truth" for each concept is the file closest to where it's acted upon:
- Lead behavior → CLAUDE.md
- Shared teammate behavior → agent-common-protocol.md
- Role-specific behavior → individual agent .md

**Axiom 2: Role prompting over rule enforcement.**
Opus 4.6 performs 3-5x better with well-defined roles than rule-based framing.
Instead of "TIER 1: 6 sections, 10 RC items, max 3 attempts", write:
"You're an implementation specialist. Before starting, explain what you'll change and why,
so Lead can verify you understand the task."

**Axiom 3: Natural language compresses without losing meaning.**
Protocol markers like `[IMPACT-ANALYSIS]` add cognitive overhead without proven benefit for Opus 4.6.
The same meaning is conveyed by "explain your understanding of the task" —
and the model is more likely to comply with natural instructions than bracket syntax.

### New Axiom (v2)

**Axiom 4: Self-serve context over embedded delivery.**
Teammates pull context via TaskGet rather than receiving it embedded in directives.
This reduces directive size (BUG-002 mitigation), ensures teammates always read the latest
version, and enables lightweight self-recovery after context loss.

### What Changes vs. What Stays

**Changes (from v5.1 → v6.0, including PT integration):**
- 27 protocol markers → natural language alternatives
- 66 ALL CAPS enforcement phrases → measured language
- 4-tier DIAVP → role-appropriate open-ended questions
- 5-level LDAP → 2-level (Standard/Deep), grounded in Impact Map
- global-context.md → PERMANENT Task (Task API entity)
- CIP embedding → TaskGet self-serve
- Rigid templates → natural expectations
- ~25 duplicate lines → single-source with references
- Recovery: Lead re-injection → teammate self-recovery via TaskGet

**Stays (unchanged):**
- YAML frontmatter in all agent files (tools, permissions, model)
- Phase pipeline structure (9 phases, same roles)
- L1/L2/L3 output format definitions
- File ownership rules
- Safety rules
- disallowedTools enforcement (mechanical, correct)
- Hook scripts (deferred to Ontology layer — except on-subagent-start.sh PT injection)
- Output directory structure (minus global-context.md file)

---

## 2. Architecture Decisions

### AD-1: Deduplication Strategy — "State in authoritative location, reference elsewhere" (preserved)

**Decision:** Each behavioral concept has exactly one authoritative location.

| Concept | Authoritative Location | References From |
|---------|----------------------|-----------------|
| Impact verification before work | CLAUDE.md §3 (Teammates paragraph) | — |
| Context injection via PT | CLAUDE.md §6 (How Lead Works) | — |
| Task API read-only | agent-common-protocol.md | CLAUDE.md §3 mentions "see common protocol" |
| Compact recovery via TaskGet | agent-common-protocol.md | CLAUDE.md §9 says "see common protocol" |
| Team Memory procedures | agent-common-protocol.md | CLAUDE.md §6 mentions location only |
| Challenge protocol (Impact Map grounded) | CLAUDE.md §6 (How Lead Verifies) | Agent .md files describe per-role expectations |
| L1/L2/L3 format | CLAUDE.md §6 (one line) | — |
| PERMANENT Task lifecycle | CLAUDE.md §6 (Coordination Infrastructure) | `/permanent-tasks` skill handles mechanics |

**Rationale:** Researcher finding F-002 identified ~25 duplicate lines (12%). By deduplicating, we reduce
CLAUDE.md's [PERMANENT] section from 40 to ~18 lines — most content simply referenced from §3/§6.

### AD-2: [PERMANENT] Section Transformation (preserved, enhanced)

**Decision:** Replace the numbered-duties [PERMANENT] section with a concise "Integrity Principles" section.

**Current:** 40 lines, 19 protocol markers, 9 Lead duties + 7 Teammate duties + 6 cross-references.
**New:** ~20 lines. Key behaviors stated naturally. No protocol markers. PT lifecycle added.

**Rationale:** The current [PERMANENT] section duplicates §3, §6, and §9 content. After deduplication,
what remains are principles rather than procedures. Two new principles added: Lead creates/maintains
PERMANENT Task, and Lead archives PT at work end.

### AD-3: Communication Protocol Simplification (preserved, PT-adapted)

**Decision:** Replace 13-row communication table with 3 flow-direction groups.

**Current:** 13 labeled message types including "Re-education" and "Adversarial Challenge."
**New:** Three groups describing natural flows:
1. Lead → Teammate: assignments with PT Task ID, context, feedback, challenges, approvals
2. Teammate → Lead: understanding checks, status, plans, question responses
3. Lead → All: phase transitions

**Adaptation for PT:** Directives include PT Task ID instead of full GC content.
Context updates reference PT-v{N} and direct teammates to TaskGet.

### AD-4: MCP Tools Simplification (preserved unchanged)

**Decision:** Replace 9-row phase × tool matrix with 3 natural bullets.

### AD-5: DIA v6.0 — Open Questions Replace Checklists (preserved, Impact Map enhanced)

**Decision:** Replace DIAVP tiers (RC-01~10) and LDAP intensity matrix with role-appropriate questions.

**Enhancement:** Lead generates probing questions from the PERMANENT Task's Codebase Impact Map —
an authoritative reference for module dependencies and ripple paths. This grounds challenges
in documented relationships rather than guesswork.

Detailed specification in [Deliverable 4](#6-deliverable-4-dia-v60-specification).

### AD-6: Agent Template Standardization (preserved unchanged)

**Decision:** All 6 agent files follow a consistent structure (after YAML frontmatter):
1. Role (who you are and why)
2. Before Starting Work (what to tell Lead)
3. If Lead Asks Probing Questions (how to respond)
4. How to Work (execution guidance)
5. Output Format
6. Constraints (boundaries)

### AD-7: GC → PERMANENT Task as Context Delivery Mechanism (NEW)

**Decision:** Replace global-context.md with a PERMANENT Task — a Task API entity (Task #1)
that serves as Single Source of Truth for the pipeline.

| Aspect | GC (v5.1) | PERMANENT Task (v6.0) |
|--------|-----------|----------------------|
| Storage | `.md` file in session directory | Task API (JSON on disk) |
| Delivery | Lead embeds full content in Directive | Teammate reads via TaskGet (self-serve) |
| Update | Lead edits file | Lead does Read-Merge-Write (TaskUpdate) |
| User requirements | Not supported | `/permanent-tasks` skill for real-time reflection |
| Persistence | Dies with TeamDelete | L2 archive + MEMORY.md + ARCHIVE.md |
| Ripple analysis | Weak (no reference data) | Core purpose (Codebase Impact Map) |
| Directive size | Large (full GC embedded) | Small (PT Task ID only) — reduces BUG-002 risk |
| Versioning | GC-v{N} in YAML frontmatter | PT-v{N} in description header |

**Rationale:** Three fundamental GC limitations addressed:
1. Pipeline-scoped lifespan → PT archived beyond TeamDelete
2. No user requirement reflection → `/permanent-tasks` skill
3. No authoritative codebase relationship data → Codebase Impact Map

**Impact on CLAUDE.md:** §3 (Lead maintains PT), §4 (Directive includes PT ID), §6 (Assigning Work,
Verifying Understanding, Monitoring Progress, Coordination Infrastructure), §9 (Recovery via TaskGet),
§10 (Lead creates/maintains/archives PT).

### AD-8: Impact Map Integration into DIA v6.0 (NEW)

**Decision:** LDAP probing questions are grounded in the PERMANENT Task's Codebase Impact Map.

**Before:** Lead generates challenges from judgment/intuition. Teammates defend with best-effort reasoning.
Both sides lack authoritative reference data for module dependencies and ripple paths.

**After:** Lead references documented Impact Map data when asking probing questions.
Teammates reference the same Impact Map when defending their understanding.
Both sides operate on shared, authoritative relationship data.

**Impact on files:**
- CLAUDE.md §6 "Verifying Understanding": Questions reference Impact Map
- CLAUDE.md §6 "Monitoring Progress": Lead uses Impact Map for deviation detection
- Agent .md "Before Starting Work": Reference Impact Map for interconnection awareness
- Agent .md "If Lead Asks Probing Questions": Defend with Impact Map data

### AD-9: Recovery via TaskGet Self-Service (NEW)

**Decision:** After context loss, teammates can begin self-recovery by calling TaskGet(PT ID)
before Lead re-injection arrives.

**Before:** Teammate reports CONTEXT_LOST → waits (blocked) → Lead re-injects full context.
**After:** Teammate reports context loss → calls TaskGet for PT → reads own L1/L2/L3 → confirms understanding.

**Rationale:** TaskGet is already in every teammate's tool list. Self-serve recovery reduces
Lead bottleneck and speeds recovery. Teammate still confirms understanding with Lead before resuming.

---

## 3. Deliverable 1: CLAUDE.md v6.0

### Structure Overview

| Section | Title | Lines | Change from v5.1 |
|---------|-------|-------|-------------------|
| §0 | Language Policy | 4 | Minor trim |
| §1 | Team Identity | 5 | Minor trim |
| §2 | Phase Pipeline | 12 | Remove enforcement lines |
| §3 | Roles | 12 | Natural rewrite, PT references |
| §4 | Communication | 8 | Table → groups, PT-adapted |
| §5 | File Ownership | 4 | Minor trim |
| §6 | How Lead Operates | 38 | Consolidated, PT integration |
| §7 | Tools | 6 | Matrix → bullets |
| §8 | Safety | 5 | Keep |
| §9 | Recovery | 8 | Simplified, TaskGet self-recovery |
| §10 | Integrity Principles | 20 | Replaces [PERMANENT], PT lifecycle |
| | **Total** | **~136** | **-34%** |

### Complete Rewritten Text

```markdown
# Agent Teams — Team Constitution v6.0

> Opus 4.6 native · Natural language DIA · PERMANENT Task context · All instances: claude-opus-4-6

## 0. Language Policy

- **User-facing conversation:** Korean only
- **All technical artifacts:** English — tasks, L1/L2/L3, gate records, designs, agent .md, MEMORY.md, messages

## 1. Team Identity

- **Workspace:** `/home/palantir`
- **Agent Teams:** Enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, tmux split pane)
- **Lead:** Pipeline Controller — spawns teammates, manages gates, never modifies code directly
- **Teammates:** Dynamic per phase (6 agent types, see pipeline below)

## 2. Phase Pipeline

| # | Phase | Zone | Teammate | Effort |
|---|-------|------|----------|--------|
| 1 | Discovery | PRE-EXEC | Lead only | max |
| 2 | Deep Research | PRE-EXEC | researcher (1-3) | max |
| 3 | Architecture | PRE-EXEC | architect (1) | max |
| 4 | Detailed Design | PRE-EXEC | architect (1) | high |
| 5 | Plan Validation | PRE-EXEC | devils-advocate (1) | max |
| 6 | Implementation | EXEC | implementer (1-4) | high |
| 7 | Testing | EXEC | tester (1-2) | high |
| 8 | Integration | EXEC | integrator (1) | high |
| 9 | Delivery | POST-EXEC | Lead only | medium |

Pre-Execution (Phases 1-5) receives 70-80% of effort. Lead approves each phase transition.

## 3. Roles

### Lead (Pipeline Controller)
Spawns and assigns teammates, approves phase gates, maintains orchestration-plan.md and
the PERMANENT Task (versioned PT-v{N}) — the single source of truth for user intent,
codebase impact map, architecture decisions, and pipeline state. Only Lead creates and
updates tasks. Runs the verification engine described in §6. Use `/permanent-tasks` to
reflect mid-work requirement changes.

### Teammates
Follow `.claude/references/agent-common-protocol.md` for shared procedures.
Before starting work, read the PERMANENT Task via TaskGet and explain your understanding to Lead.
Before making code changes (implementer/integrator), share your plan and wait for approval.
Tasks are read-only for you — use TaskList and TaskGet only.

## 4. Communication

Communication flows in three directions:

**Lead → Teammate:** Task assignments with PERMANENT Task ID and task-specific context,
feedback and corrections, probing questions to verify understanding (grounded in the
Codebase Impact Map), approvals or rejections, context updates when PT version changes.

**Teammate → Lead:** Understanding of assigned task (referencing Impact Map), status updates,
implementation plans (before code changes), responses to probing questions, blocking issues.

**Lead → All:** Phase transition announcements.

## 5. File Ownership

- Each implementer owns a non-overlapping file set assigned by Lead.
- No concurrent edits to the same file.
- Only the integrator can cross ownership boundaries.
- Read access is unrestricted.

## 6. How Lead Operates

### Before Spawning
Evaluate three concerns: Is the requirement clear enough? (If not, ask the user.)
Is the scope manageable? (If >4 files, split into multiple tasks.) After a failure,
is the new approach different? (Same approach = same failure.)

### Assigning Work
Include the PERMANENT Task ID (PT-v{N}) and task-specific context in every assignment.
Teammates read the full PERMANENT Task content via TaskGet — no need to embed it in the
directive. When the PERMANENT Task changes, send context updates to affected teammates
with the new version number — they'll call TaskGet for the latest content.

### Verifying Understanding
After a teammate explains their understanding, ask 1-3 open-ended questions appropriate
to their role to test depth of comprehension. Ground your questions in the PERMANENT Task's
Codebase Impact Map — reference documented module dependencies and ripple paths rather
than relying on intuition alone. Focus on interconnection awareness, failure reasoning,
and interface impact. For architecture phases (3/4), also ask for alternative approaches.
If understanding remains insufficient after 3 attempts, re-spawn with clearer context.
Understanding must be verified before approving any implementation plan.

### Monitoring Progress
Read teammate L1/L2/L3 files and compare against the Phase 4 design. Use the Codebase
Impact Map to trace whether changes in one area have unintended effects on dependent modules.
Log cosmetic deviations, re-inject context for interface changes, re-plan for architectural
changes. No gate approval while any teammate has stale context.

### Phase Gates
Before approving a phase transition: Do all output artifacts exist? Does quality meet
the next phase's entry conditions? Are there unresolved critical issues? Are L1/L2/L3 generated?

### Status Visualization
When updating orchestration-plan.md, output ASCII status visualization including phase
pipeline, workstream progress, teammate status, and key metrics.

### Coordination Infrastructure
- **PERMANENT Task:** Task #1 with subject "[PERMANENT] {feature}". Versioned PT-v{N}
  (monotonically increasing). Contains: User Intent, Codebase Impact Map, Architecture
  Decisions, Phase Status, Constraints. Lead tracks each teammate's confirmed PT version
  in orchestration-plan.md.
- **L1/L2/L3:** L1 = index (YAML, ≤50 lines). L2 = summary (MD, ≤200 lines). L3 = full detail (directory).
- **Team Memory:** `.agent/teams/{session-id}/TEAM-MEMORY.md`, section-per-role structure.
- **Output directory:**
  ```
  .agent/teams/{session-id}/
  ├── orchestration-plan.md, TEAM-MEMORY.md
  └── phase-{N}/ → gate-record.yaml, {role}-{id}/ → L1, L2, L3-full/, task-context.md
  ```

## 7. Tools

Use sequential-thinking for all non-trivial analysis and decisions.
Use tavily and context7 for external documentation during research-heavy phases (2-4, 6).
Use github tools as needed for repository operations.
Tool availability per agent is defined in each agent's YAML frontmatter.

## 8. Safety

**Blocked commands:** `rm -rf`, `sudo rm`, `chmod 777`, `DROP TABLE`, `DELETE FROM`
**Protected files:** `.env*`, `*credentials*`, `.ssh/id_*`, `**/secrets/**`
**Git safety:** Never force push main. Never skip hooks. No secrets in commits.

## 9. Recovery

If your session is continued from a previous conversation:
- **Lead:** Read orchestration-plan.md, task list (including PERMANENT Task), latest gate
  record, and teammate L1 indexes. Send fresh context to each active teammate.
- **Teammates:** See agent-common-protocol.md for recovery procedure. You can call TaskGet
  on the PERMANENT Task for immediate self-recovery — it contains the full project context.
  Core rule: never proceed with summarized or remembered information alone.

If a teammate reports they're running low on context: read their L1/L2/L3, shut them down,
and re-spawn with their saved progress.

## 10. Integrity Principles

These principles guide all team interactions and are not overridden by convenience.

**Lead responsibilities:**
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions).
- Create the PERMANENT Task at pipeline start. Maintain it via Read-Merge-Write — always
  a refined current state, never an append-only log. Archive to MEMORY.md + ARCHIVE.md at work end.
- Always include the PT Task ID when assigning work. Verify understanding before approving plans.
- Challenge teammates with probing questions grounded in the Codebase Impact Map — test
  systemic awareness, not surface recall. Scale depth with phase criticality.
- Maintain Team Memory: create at session start, relay findings from read-only agents, curate at gates.
- Hooks verify L1/L2 file existence automatically.

**Teammate responsibilities:**
- Read the PERMANENT Task via TaskGet and confirm you understood the context. Explain in your own words.
- Answer probing questions with specific evidence — reference the Impact Map's module
  dependencies, interface contracts, and propagation chains.
- Read Team Memory before starting. Update your section with discoveries (if you have Edit access)
  or report to Lead for relay (if you don't).
- Save work to L1/L2/L3 files proactively. Report if running low on context.
- Your work persists through files and messages, not through memory.

**See also:** agent-common-protocol.md (shared procedures), agent .md files (role-specific guidance),
hook scripts in `.claude/hooks/` (automated enforcement), `/permanent-tasks` skill (mid-work updates).
```

### Line Count Analysis

Counted section by section:
- Header + §0: 6 lines
- §1: 5 lines
- §2: 14 lines
- §3: 13 lines (+2 from v1: PT description in Lead, TaskGet in Teammates)
- §4: 10 lines (unchanged structure, PT-adapted content)
- §5: 5 lines
- §6: 38 lines (+5 from v1: PT in Assigning Work, Impact Map in Verifying/Monitoring, PT in Coordination)
- §7: 5 lines
- §8: 4 lines
- §9: 9 lines (+1: TaskGet self-recovery mention)
- §10: 22 lines (+4: PT lifecycle in Lead, Impact Map in Teammate)
- **Total: ~136 lines** (vs. 207 current = 34% reduction, vs. 132 original L3 = +4 lines for PT)

### Semantic Preservation Checklist

| Behavioral Requirement | v5.1 Location | v6.0-PT Location | Preserved? |
|----------------------|---------------|------------------|------------|
| Korean for user, English for artifacts | §0 | §0 | Yes |
| Lead never modifies code | §1 | §1 | Yes |
| 9-phase pipeline with roles | §2 | §2 | Yes |
| Shift-left 70-80% effort | §2 line 32 | §2 last line | Yes |
| Lead approves gate transitions | §2 line 33 | §2 last line | Yes |
| Lead maintains shared context | §3 (GC) | §3 (PERMANENT Task) | Yes (upgraded) |
| Teammates explain understanding first | §3 + [PERMANENT] | §3 Teammates paragraph | Yes |
| Teammates read context via TaskGet | NEW | §3 Teammates paragraph | NEW |
| Implementer/integrator plan approval | §3 + [PERMANENT] | §3 Teammates paragraph | Yes |
| Task API read-only for teammates | §3 + [PERMANENT] | §3 + agent-common-protocol | Yes |
| 13 communication types | §4 table | §4 three groups (PT-adapted) | Yes |
| Directive includes PT ID | NEW | §4 Lead→Teammate | NEW |
| File ownership rules | §5 | §5 | Yes (identical) |
| Pre-spawn checklist (S-1/S-2/S-3) | §6 | §6 "Before Spawning" | Yes |
| Context injection via PT | §6 + [PERMANENT] | §6 "Assigning Work" | Yes (upgraded) |
| Impact verification with Impact Map | §6 + [PERMANENT] | §6 "Verifying Understanding" | Yes (upgraded) |
| Deviation monitoring via Impact Map | §6 | §6 "Monitoring Progress" | Yes (upgraded) |
| Gate checklist | §6 | §6 "Phase Gates" | Yes |
| ASCII status visualization | §6 | §6 "Status Visualization" | Yes |
| PT versioning (was GC versioning) | §6 | §6 "Coordination Infrastructure" | Yes (upgraded) |
| L1/L2/L3 format | §6 | §6 "Coordination Infrastructure" | Yes |
| Team Memory | §6 + [PERMANENT] | §6 "Coordination Infrastructure" | Yes |
| Output directory (no GC file) | §6 | §6 "Coordination Infrastructure" | Yes (adapted) |
| MCP tool usage | §7 matrix | §7 bullets | Yes |
| Safety rules | §8 | §8 | Yes (identical) |
| Compact recovery + TaskGet | §9 + [PERMANENT] | §9 + agent-common-protocol | Yes (upgraded) |
| Context pressure handling | §9 | §9 last paragraph | Yes |
| Task API sovereignty | [PERMANENT] | §10 Lead first bullet | Yes |
| PT lifecycle (create/maintain/archive) | NEW | §10 Lead second bullet | NEW |
| LDAP grounded in Impact Map | NEW | §6 "Verifying Understanding" + §10 | NEW |
| Hook enforcement | [PERMANENT] | §10 Lead sixth bullet | Yes |
| Challenge response with evidence | [PERMANENT] | §10 Teammate second bullet | Yes (Impact Map) |
| Pre-compact obligation | [PERMANENT] | §10 Teammate fourth bullet | Yes |
| Persistence via files | [PERMANENT] | §10 Teammate fifth bullet | Yes |
| /permanent-tasks skill reference | NEW | §3 Lead + §10 See also | NEW |

**Result: 28/28 original behavioral requirements preserved + 5 new PT-specific behaviors added. Zero semantic loss.**

---

## 4. Deliverable 2: agent-common-protocol.md v2.0

### Complete Rewritten Text

```markdown
# Shared Protocol for All Teammates

This covers procedures common to all 6 agent types. Role-specific guidance is in each agent's own .md file.

---

## When You Receive a Task Assignment

Read the PERMANENT Task via TaskGet using the Task ID provided in your assignment — it contains
the full project context including user intent, codebase impact map, architecture decisions,
and constraints. Also read the task-specific context provided by Lead. Confirm receipt by
messaging Lead with the PT version you read (e.g., "PT-v3 received, understood scope").
Make sure you understand the scope, constraints, and who will consume your output before
doing anything else.

---

## When Context Changes Mid-Work

If Lead sends a context update with a new PT version:
1. Call TaskGet on the PERMANENT Task to read the latest content.
2. Message Lead confirming what changed, what impact it has on your current work,
   and whether you can continue or need to pause.

---

## When You Finish

1. Write L1/L2/L3 files to your assigned output directory.
2. Message Lead with a summary of what you completed.

Role-specific completion details (e.g., devils-advocate verdict) are in your agent file.

---

## Task API

Tasks are read-only for you: use TaskList and TaskGet to check status, find your assignments,
and read the PERMANENT Task for project context. Task creation and updates are Lead-only
(enforced by tool restrictions).

---

## Team Memory

Read TEAM-MEMORY.md before starting work — it has context from prior phases and other teammates.

- If you have the Edit tool (implementer, integrator): write discoveries to your own section.
  Use `## {your-role-id}` as anchor for edits. Never overwrite other sections.
- If you don't have Edit (researcher, architect, tester): message Lead with findings for relay.
- Devils-advocate: read-only access to Team Memory.

---

## Saving Your Work

Write L1/L2/L3 files throughout your work, not just at the end. These files are your only
recovery mechanism — anything unsaved is permanently lost if your session compacts.

If you notice you're running low on context: save all work immediately, then tell Lead.
Lead will shut you down and re-spawn you with your saved progress.

---

## If You Lose Context

If you see "This session is being continued from a previous conversation":
1. Tell Lead immediately — do not continue working from memory alone.
2. Call TaskGet on the PERMANENT Task (find it via TaskList — subject contains "[PERMANENT]")
   to restore the full project context.
3. Read your own L1/L2/L3 files to restore your progress.
4. Reconfirm your understanding of the task before resuming.

Note: You can begin self-recovery with steps 2-3 while waiting for Lead, but always confirm
your understanding with Lead before resuming work.

---

## Agent Memory

Check your persistent memory at `~/.claude/agent-memory/{role}/MEMORY.md` when you start.
Update it with patterns and lessons learned when you finish.
```

### Line Count: ~52 lines of content (vs. 48 in original L3, +4 for PT details)

### Change Summary from Original L3

| Section | Original L3 v2 | This v2 (PT) | Change |
|---------|----------------|--------------|--------|
| Context Receipt | 3 lines, natural, GC ref | 5 lines, natural, TaskGet | PT self-serve added |
| Mid-Execution | 3 lines, natural | 3 lines, natural, TaskGet | TaskGet replaces "read updated GC" |
| Completion | 3 lines | 3 lines | Unchanged |
| Task API | 2 lines | 3 lines | PT reading added to description |
| Team Memory | 5 lines | 5 lines | Unchanged |
| Context Pressure | 4 lines, natural | 4 lines | Unchanged |
| Auto-Compact | 4 lines, natural | 6 lines, TaskGet self-recovery | Self-recovery via TaskGet added |
| Memory | 2 lines | 2 lines | Unchanged |

### Semantic Preservation

| Behavior | Preserved? |
|----------|------------|
| Confirm context receipt with version | Yes (PT-v{N} instead of GC-v{N}) |
| Read PERMANENT Task via TaskGet | NEW |
| Pause and report on mid-work changes | Yes |
| Write L1/L2/L3 at completion | Yes |
| Task API is read-only | Yes |
| Read Team Memory first | Yes |
| Edit own section only (with anchor) | Yes |
| Lead relay for non-Edit agents | Yes |
| Save work proactively (not just at 75%) | Yes |
| Report context pressure to Lead | Yes |
| On compact: tell Lead, don't proceed alone | Yes |
| Self-recovery via TaskGet | NEW |
| Read own L1/L2/L3 to restore progress | Yes |
| Reconfirm understanding after recovery | Yes |
| Check persistent agent memory | Yes |

**13/13 original behaviors preserved + 2 new PT-specific behaviors added.**

---

## 5. Deliverable 3: Agent .md Template Design

### Universal Structure (all 6 agents — preserved from original L3)

After YAML frontmatter (unchanged), every agent file follows this structure:

```
# {Role Name} Agent

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
{1-3 sentences: who you are, what you do, why it matters}

## Before Starting Work
{What to tell Lead — reference Impact Map for interconnections}

## If Lead Asks Probing Questions
{How to respond — defend with Impact Map data and specific evidence}

## How to Work
{Execution guidance — tools, workflow, deliverables}

## Output Format
{L1/L2/L3 descriptions — keep from current}

## Constraints
{Boundaries — keep from current, natural language}
```

**Changes from original L3 template:**
- "Before Starting Work": Adds reference to Codebase Impact Map for interconnection awareness
- "If Lead Asks Probing Questions": Adds reference to Impact Map data for defense
- No structural changes — same 6-section layout

### Reference Template: implementer.md (~70 lines)

```markdown
---
name: implementer
description: |
  Code implementer with full tool access.
  Each instance owns a non-overlapping file set. Plan Approval mandatory.
  Spawned in Phase 6 (Implementation). Max 4 instances.
model: opus
permissionMode: acceptEdits
memory: user
color: green
maxTurns: 100
tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
  - mcp__tavily__search
disallowedTools:
  - TaskCreate
  - TaskUpdate
---

# Implementer Agent

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You are a code implementation specialist. You execute changes within your assigned file
ownership boundary, following the approved design from Phase 4. Your work must be precise,
well-tested, and documented — other teammates and the integrator depend on your output
matching the interface specifications.

## Before Starting Work
Read the PERMANENT Task via TaskGet to understand the full project context, including the
Codebase Impact Map. Message Lead with your understanding of the task. Cover:
- What files you'll change and what changes you'll make
- Which interfaces are affected and how (reference the Impact Map's module dependencies)
- Which teammates' work could be impacted by your changes (trace the Impact Map's ripple paths)
- What risks you see and how you'd handle them

Then share your implementation plan — which files, what changes, risk level, interface impacts.
Wait for Lead's approval before making any changes.

## If Lead Asks Probing Questions
Defend your understanding with specifics: name the modules, trace the propagation paths
documented in the Impact Map, quantify the blast radius of potential mistakes.
Implementation phases receive thorough scrutiny because code changes are harder to reverse
than design changes.

## How to Work
- Use sequential-thinking for implementation decisions and self-review
- Use context7 to verify library APIs before writing code; use tavily for unfamiliar APIs
- Only modify files within your assigned ownership set
- Run self-tests after implementation
- Write discoveries to your TEAM-MEMORY.md section
- Write L1/L2/L3 files to your assigned directory

## Output Format
- **L1-index.yaml:** Modified files with change descriptions
- **L2-summary.md:** Implementation narrative with decisions
- **L3-full/:** Code diffs, self-test results, implementation notes

## Sub-Orchestrator Mode
You can spawn subagents via Task tool for independent sub-work (nesting limit: 1 level).
All sub-work must stay within your file ownership boundary.

## Constraints
- File ownership is strict — only touch your assigned files
- No code changes without Lead's approval on your plan
- Self-test before marking complete
- Team Memory: edit your own section only (use `## {your-role-id}` as anchor)
- If you need files outside your boundary, tell Lead you're blocked and specify which files
```

**Line count: ~70 lines** (vs. 68 in original L3, +2 for Impact Map references)

### Per-Agent Design Specifications

#### researcher.md (~50 lines)

```markdown
{YAML frontmatter unchanged — 27 lines}

# Researcher Agent

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You are a deep research specialist. You explore codebases and external documentation thoroughly,
producing structured reports that downstream architects and designers will build upon.

## Before Starting Work
Read the PERMANENT Task via TaskGet to understand the full project context. Message Lead
with your understanding of the task. Cover:
- What you're researching and why it matters
- What's in scope vs. out of scope
- Who will use your output and what format they need
- What parts of the Codebase Impact Map (if populated) are relevant to your research

## If Lead Asks Probing Questions
Respond with specific evidence — name your downstream consumers, justify your scope boundaries,
and defend your assumptions with concrete references.

## How to Work
- Break research into parallel sub-tasks when possible
- Use sequential-thinking for analysis, tavily for current docs, context7 for library references
- Cross-reference findings before concluding
- Report key findings to Lead for Team Memory relay
- Write L1/L2/L3 files to your assigned directory

## Output Format
- **L1-index.yaml:** Research findings with one-line summaries
- **L2-summary.md:** Narrative synthesis with key decisions
- **L3-full/:** Complete research reports, API docs, pattern inventories

## Constraints
- You can spawn subagents via Task tool for parallel research (nesting limit: 1 level)
```

#### architect.md (~57 lines)

```markdown
{YAML frontmatter unchanged — 28 lines}

# Architect Agent

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You are an architecture specialist. You synthesize research findings into architecture decisions,
produce risk matrices, and create detailed designs with file and module boundaries. Your designs
directly determine how implementers will decompose and execute work.

## Before Starting Work
Read the PERMANENT Task via TaskGet to understand the full project context, including the
Codebase Impact Map. Message Lead with your understanding of the task. Cover:
- What you're designing and why it matters to the project
- What upstream research and decisions inform your work
- What interfaces you must define and what constraints bind you
- Who consumes your design and what they expect from it
- How your design interacts with the Impact Map's documented dependencies

## If Lead Asks Probing Questions
Architecture receives the deepest scrutiny — design flaws here multiply downstream.
Defend with specific component names, interface contracts, propagation chains from the
Impact Map, and blast radius. If asked for alternatives, propose at least one concrete
alternative with its own impact analysis.

## How to Work
- Use sequential-thinking for every design decision and risk assessment
- Use tavily to verify design patterns and framework best practices
- Use context7 for library constraints and API compatibility
- Produce Architecture Decision Records (ADRs) for every significant choice
- Report key decisions to Lead for Team Memory relay
- Write L1/L2/L3 files to your assigned directory

## Output Format
- **L1-index.yaml:** ADRs, risk entries, design artifacts
- **L2-summary.md:** Architecture narrative with decision rationale
- **L3-full/:** Complete ADRs, risk matrix, component diagrams, interface specs

### Phase 3 (Architecture) Deliverables
ADRs with alternatives analysis, risk matrix, component diagram, rejection rationale

### Phase 4 (Detailed Design) Deliverables
File/module boundary map, interface specifications, data flow diagrams, implementation task breakdown

## Constraints
- Design documents only — no existing source code modification
- You can write new design documents to your assigned output directory
```

#### devils-advocate.md (~48 lines)

```markdown
{YAML frontmatter unchanged — 25 lines}

# Devil's Advocate Agent

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You are a critical design reviewer. You find flaws, edge cases, missing requirements, and
potential failures in architecture and detailed design. You're exempt from the understanding
check — your critical analysis itself demonstrates comprehension.

## How to Work
- Read the PERMANENT Task via TaskGet for project context and Codebase Impact Map
- Use sequential-thinking for each challenge analysis and severity assessment
- Use tavily to find real-world failure cases and anti-pattern evidence
- Use context7 to verify design claims against library documentation
- Challenge every assumption with evidence-based reasoning
- Assign severity ratings and propose specific mitigations
- Write L1/L2/L3 files to your assigned directory

## Challenge Categories
1. **Correctness:** Does the design solve the stated problem?
2. **Completeness:** Missing requirements or edge cases?
3. **Consistency:** Do different parts contradict?
4. **Feasibility:** Can this be implemented within constraints?
5. **Robustness:** What happens when things go wrong?
6. **Interface Contracts:** Are all interfaces explicit and compatible?

## Severity Ratings
- **CRITICAL:** Must fix before proceeding. Blocks gate.
- **HIGH:** Should fix. May block if multiple accumulate.
- **MEDIUM:** Recommended fix.
- **LOW:** Document for future consideration.

## Final Verdict
- **PASS:** No critical or high issues.
- **CONDITIONAL_PASS:** High issues exist but have accepted mitigations.
- **FAIL:** Critical issues exist. Must return to earlier phase.

## Output Format
- **L1-index.yaml:** Challenges with severity ratings
- **L2-summary.md:** Challenge narrative with verdicts and mitigations
- **L3-full/:** Detailed challenge analysis per design component

## Constraints
- Completely read-only — no file mutations
- Critique only — propose mitigations but do not modify the design
- Always reference specific design sections as evidence
```

**Note:** Minimal changes from original L3. Added "Read the PERMANENT Task via TaskGet" to
How to Work section. Already the most natural-language file.

#### tester.md (~60 lines)

```markdown
{YAML frontmatter unchanged — 27 lines}

# Tester Agent

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You are a testing specialist. You verify implementation against design specifications by writing
and executing tests. Your coverage analysis and failure reports determine whether the implementation
is ready for integration.

## Before Starting Work
Read the PERMANENT Task via TaskGet to understand the full project context. Message Lead
with your understanding of the task. Cover:
- What you're testing and how it connects to the design spec
- Which Phase 6 implementation files you're verifying
- What interfaces and acceptance criteria you'll test against
- How the Codebase Impact Map's ripple paths inform your test priorities
- If tests fail, who is affected and what happens next

## If Lead Asks Probing Questions
Defend your test strategy with specifics: name the critical test cases, explain what you
chose not to test and why, and describe how you'd catch the most impactful failure.
Reference the Impact Map to justify your test coverage priorities.

## How to Work
- Use sequential-thinking for test design decisions and failure analysis
- Use context7 to verify testing framework APIs and assertion patterns
- Read the design spec (Phase 4) and implementation outputs (Phase 6)
- Write tests verifying each acceptance criterion
- Execute tests and capture results
- Analyze failures and report root causes
- Report key findings to Lead for Team Memory relay
- Write L1/L2/L3 files to your assigned directory

## Test Design Principles
1. Test behavior, not implementation details
2. Clear test names: `test_{what}_{when}_{expected}`
3. Cover happy path, edge cases, and error conditions
4. Verify interface contracts from Phase 4 design

## Output Format
- **L1-index.yaml:** Test files, pass/fail counts, coverage summary
- **L2-summary.md:** Test narrative with failure analysis
- **L3-full/:** Test files, execution logs, coverage reports

## Constraints
- You can create new test files and run test commands
- Cannot modify existing source code
- If fixes are needed, message Lead with failure details
```

#### integrator.md (~70 lines)

```markdown
{YAML frontmatter unchanged — 28 lines}

# Integrator Agent

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You are the integration specialist — the only agent that can touch files across ownership boundaries.
You resolve conflicts between implementer outputs, perform final merges, and verify system-level
coherence. Your work is the last gate before delivery.

## Before Starting Work
Read the PERMANENT Task via TaskGet to understand the full project context, including the
Codebase Impact Map. Message Lead with your understanding of the task. Cover:
- What implementer outputs you're merging and what test results inform your work
- Which files need cross-boundary changes and what conflicts exist
- Which interfaces must be preserved — reference the Impact Map's interface boundaries
- Your resolution strategy for each identified conflict, with ripple path awareness

Then share your integration plan — conflicts found, resolution strategy per conflict,
affected files, integration test plan, risk level. Wait for approval before proceeding.

## If Lead Asks Probing Questions
Defend your understanding with specifics: name the modules, trace the merge conflict chains
through the Impact Map's dependency graph, quantify the blast radius. Integration affects
the entire codebase — scrutiny matches the scope.

## How to Work
- Use sequential-thinking for conflict analysis and resolution decisions
- Use context7 to verify library compatibility when resolving conflicts
- Read all implementer L1/L2/L3 from Phase 6 and tester results from Phase 7
- Identify and resolve conflicts with documented rationale
- Run integration tests
- Write discoveries to your TEAM-MEMORY.md section
- Write L1/L2/L3 files to your assigned directory

## Conflict Resolution Principles
1. Preserve both implementers' intent when possible
2. Irreconcilable conflict → escalate to Lead
3. Document every resolution decision
4. Verify resolved code against Phase 4 interface specs
5. Run integration tests after each batch of resolutions

## Output Format
- **L1-index.yaml:** Conflicts resolved, integration test results
- **L2-summary.md:** Integration narrative with conflict resolution rationale
- **L3-full/:** Conflict resolution log, merged diffs, integration test logs

## Constraints
- No merge operations without Lead's approval on your plan
- You are the only agent that can cross file ownership boundaries
- Team Memory: edit your own section only (use `## {your-role-id}` as anchor)
- If conflicts can't be resolved, tell Lead with details of the irreconcilable conflict
```

### Line Count Summary

| File | Current (v5.1) | Original L3 (v1) | This L3 (v2, PT) | Reduction from v5.1 |
|------|----------------|-------------------|-------------------|---------------------|
| CLAUDE.md | 207 | 132 | 136 | -34% |
| agent-common-protocol.md | 79 | 48 | 52 | -34% |
| researcher.md | 79 | 48 | 50 | -37% |
| architect.md | 89 | 55 | 57 | -36% |
| devils-advocate.md | 73 | 48 | 48 | -34% |
| implementer.md | 114 | 68 | 70 | -39% |
| tester.md | 90 | 58 | 60 | -33% |
| integrator.md | 116 | 68 | 70 | -40% |
| **Total** | **847** | **525** | **543** | **-36%** |

**Note:** v2 is +18 lines over original L3 (525→543) due to PT/Impact Map integration.
This is a net cost of ~2 lines per file for significant capability gains:
- Self-serve context via TaskGet
- Impact Map grounded verification
- Codebase relationship data for all agents
- Lightweight self-recovery

---

## 6. Deliverable 4: DIA v6.0 Specification

### Current System (DIA v5.0) — same as original L3

```
DIAVP: 4 tiers × variable sections × variable RC items (RC-01~RC-10)
LDAP: 5 intensity levels × 7 named categories × phase matrix
Protocol: [IMPACT-ANALYSIS] → [VERIFICATION-QA] → [CHALLENGE] → [CHALLENGE-RESPONSE]
```

### New System (DIA v6.0 with Impact Map)

```
Verification: Role-appropriate open-ended questions (1-3 per role)
Probing: 2 levels (Standard / Deep) with Impact Map-grounded questioning
Protocol: Natural conversation — teammate explains, Lead questions from Impact Map, teammate defends
```

### Verification Model

#### How It Works

1. **Teammate reads PERMANENT Task and explains understanding** — in their own words,
   covering what Lead's "Before Starting Work" section asks for (role-specific expectations
   in agent .md files). Teammate references the Codebase Impact Map for interconnections.

2. **Lead asks probing questions grounded in Impact Map** — 1-3 questions appropriate to
   the teammate's role, referencing documented module dependencies and ripple paths:

   | Role | Questions | Focus Areas |
   |------|-----------|-------------|
   | Researcher | 1 | Scope awareness, constraint understanding |
   | Architect | 2-3 | Interconnection (Impact Map), failure modes, alternatives |
   | Implementer | 2-3 | Interface impact (Impact Map), rollback plans, cross-team risk |
   | Integrator | 2-3 | Merge conflicts, interface preservation (Impact Map), system coherence |
   | Tester | 1-2 | Test prioritization (Impact Map ripple paths), coverage gaps |
   | Devils-advocate | 0 (exempt) | Critical analysis demonstrates understanding |

3. **Teammate defends with evidence from Impact Map** — specific component names, documented
   interface references, propagation chains from the Impact Map, concrete examples.
   Surface-level answers don't pass.

4. **Lead judges** — does the teammate genuinely understand the task's interconnections
   and failure modes? The Impact Map provides an objective baseline for evaluation — not
   just Lead judgment alone, but Lead judgment informed by documented relationships.

#### Example Questions by Role (Impact Map Enhanced)

**Researcher:**
> "The Impact Map shows module A depends on module B. How does this dependency affect your research scope?"

Tests: scope awareness, constraint understanding, Impact Map awareness.

**Architect:**
> "Walk me through how a change in [component X] would propagate — the Impact Map shows
> three downstream consumers. Which propagation path has the highest risk?"
> "What's the most likely failure mode, and how does your architecture handle it?"

Tests: interconnection awareness grounded in documented data, failure reasoning.

**Implementer / Integrator:**
> "The Impact Map shows your files share an interface with {teammate}'s files at {contract point}.
> What happens if your changes don't match the interface spec?"
> "What's your rollback plan if [specific risk from Impact Map risk hotspots] materializes?"

Tests: interface awareness grounded in Impact Map, risk thinking, verification planning.

**Tester:**
> "The Impact Map identifies {area} as a risk hotspot. What's the one test case that,
> if it fails, means the entire feature is broken?"
> "What would you NOT test, and why — given the ripple paths documented in the Impact Map?"

Tests: prioritization informed by documented risk, scope judgment.

#### Pass/Fail Criteria (preserved from original L3)

**Pass:** Teammate demonstrates genuine understanding of interconnections (referencing Impact
Map data), can trace propagation chains, identifies realistic failure modes, and shows
awareness of how their work affects others.

**Fail:** Surface-level rephrasing of the assignment without demonstrating understanding of
interconnections or failure modes. Can't reference specific components or interfaces from
the Impact Map. Gives generic answers that could apply to any task.

**Max attempts:** 3 for critical roles (architect, implementer, integrator). 2 for researcher.
After max attempts: re-spawn with clearer, more focused context.

### Probing Levels (preserved from original L3)

| Level | When | What |
|-------|------|------|
| Standard | Phases 2, 6, 7, 8 | 1-2 probing questions based on task context + Impact Map |
| Deep | Phases 3, 4 (architecture/design) | 2-3 probing questions + request for alternative approach |
| None | Phases 1, 5, 9 | Lead-only or exempt (devils-advocate) |

**No named categories.** Lead generates questions from the Impact Map and task context.
The goal is to test understanding grounded in documented relationships, not to check off
category boxes.

### How This Maps to Files

| Content | Location |
|---------|----------|
| Verification process (how Lead questions from Impact Map) | CLAUDE.md §6 "Verifying Understanding" |
| Probing depth by phase | CLAUDE.md §6 "Verifying Understanding" + §10 Lead fourth bullet |
| What teammates should explain (with Impact Map) | Each agent .md "Before Starting Work" section |
| How teammates should defend (with Impact Map data) | Each agent .md "If Lead Asks Probing Questions" section |
| Max attempts and failure escalation | CLAUDE.md §6 "Verifying Understanding" |
| Pass/fail judgment criteria (Impact Map baseline) | CLAUDE.md §10 (implicit in language) |

### Migration from DIA v5.0

| v5.0 Concept | v6.0 Replacement | Where |
|-------------|-----------------|-------|
| TIER 0/1/2/3 | Role-appropriate question counts | CLAUDE.md §6 + agent .md |
| RC-01~RC-10 | Removed — replaced by Impact Map-grounded questions | — |
| 7 LDAP categories | Removed — Impact Map-grounded organic questioning | — |
| 5 LDAP intensity levels | 2 levels (Standard/Deep) | CLAUDE.md §6 |
| [IMPACT-ANALYSIS] marker | "explain your understanding" | agent .md §Before Starting |
| [CHALLENGE] marker | "probing questions from Impact Map" | CLAUDE.md §6 + §10 |
| [CHALLENGE-RESPONSE] marker | "defend with Impact Map evidence" | agent .md §If Lead Asks |
| [IMPACT_VERIFIED] marker | Lead's approval message | natural flow |
| [IMPACT_REJECTED] marker | "understanding insufficient" | natural flow |
| Gate A → Gate B | "understanding verified before plan approval" | CLAUDE.md §10 |
| No reference data for challenges | Codebase Impact Map in PERMANENT Task | CLAUDE.md §6 |

---

## 7. Deduplication Plan

### Concepts Currently Stated Multiple Times

| # | Concept | Current Locations | Authoritative v6.0 Location | Action for Other Locations |
|---|---------|-------------------|---------------------------|----------------------------|
| 1 | Impact verification | §3, §6 DIA #4, [PERM] Lead#3, [PERM] Team#2 | §6 "Verifying Understanding" + §3 one line | Remove from §10 (implied by §6) |
| 2 | Context injection (now PT) | §4 row 1, §6 DIA #2, [PERM] Lead#2 | §6 "Assigning Work" | Remove from §10 |
| 3 | Task API read-only | §3, [PERM] Lead#1, [PERM] Team#3 | §3 Teammates + agent-common-protocol | §10 mentions enforcement mechanism only |
| 4 | Compact recovery (now TaskGet) | §9, [PERM] Team#5-6 | §9 + agent-common-protocol | Remove from §10 |
| 5 | Team Memory | §6, [PERM] Lead#8, [PERM] Team#4a | §6 "Coordination Infrastructure" + agent-common-protocol | §10 one line |
| 6 | Challenge protocol (now Impact Map) | §4, [PERM] Lead#7, [PERM] Team#2a | §6 "Verifying Understanding" + agent .md files | §10 one principle line |

**Lines saved by deduplication: ~22 lines** (from CLAUDE.md alone — same as original L3)

### GC → PT Reference Deduplication

All instances of the following are replaced:
- `global-context.md` → `PERMANENT Task`
- `GC-v{N}` → `PT-v{N}`
- `global context` (lowercase) → `PERMANENT Task` or `project context` depending on context
- Output directory listing removes `global-context.md` entry

---

## 8. Implementation Task Breakdown

### Recommended Task Decomposition for Phase 6

Aligned with permanent-tasks-design.md Section 8 (10-task split, max 2 concurrent).

| Task | File | Action | Dependencies | Round |
|------|------|--------|-------------|-------|
| T1 | `.claude/skills/permanent-tasks/SKILL.md` | CREATE | None | R1 |
| T2 | `.claude/CLAUDE.md` | MODIFY | None | R1 |
| T3 | `.claude/references/task-api-guideline.md` | MODIFY | T2 | — (excluded, separate terminal) |
| T4 | `.claude/references/agent-common-protocol.md` | MODIFY | T2 | R2 |
| T5 | `.claude/skills/brainstorming-pipeline/SKILL.md` | MODIFY | T1, T4 | R3 |
| T6 | `.claude/skills/agent-teams-write-plan/SKILL.md` | MODIFY | T1, T4 | R3 |
| T7 | `.claude/skills/agent-teams-execution-plan/SKILL.md` | MODIFY | T1, T4 | R4 |
| T8 | `.claude/hooks/on-subagent-start.sh` | MODIFY | T2 | R4 |
| T9 | `.claude/projects/-home-palantir/memory/MEMORY.md` | MODIFY | None | R5 |
| T10 | `.claude/projects/-home-palantir/memory/ARCHIVE.md` | CREATE | T9 | R5 |

**Note:** T3 (task-api-guideline.md) is excluded from this pipeline — it's being modified
concurrently in another terminal. The 10-task list from permanent-tasks-design is preserved
but T3 is marked as excluded.

### Additional Tasks: Agent .md Files (from original L3)

| Task | Files | Action | Dependencies | Round |
|------|-------|--------|-------------|-------|
| T11 | researcher.md, architect.md, devils-advocate.md | MODIFY | T2, T4 | R2 |
| T12 | implementer.md, tester.md, integrator.md | MODIFY | T2, T4 | R2 |

**Note:** Agent .md files were in the original L3's T3/T4 but not in permanent-tasks-design
Section 8 (which said "6x agent .md: TaskGet already in tools. No disallowedTools change needed").
However, the NLP conversion does change these files significantly (new template structure,
natural language rewrite, Impact Map references). These must be included as implementation tasks.

### Execution Order (max 2 concurrent teammates)

```
Round 1: T1 (SKILL.md CREATE) + T2 (CLAUDE.md MODIFY)       ← parallel, independent
Round 2: T4 (common-protocol) + T11 (3 agent .md)            ← parallel, both depend on T2
         OR T4 (common-protocol) + T12 (3 agent .md)
Round 3: T5 (brainstorm skill) + T6 (write-plan skill)       ← parallel, depend on T1+T4
Round 4: T7 (exec-plan skill) + T8 (hook)                    ← parallel
Round 5: T9 (MEMORY) + T10 (ARCHIVE)                         ← parallel, independent
Round 6: T12 (remaining 3 agent .md) if not done in R2       ← depends on T2, T4
```

**Total: 12 tasks across 5-6 rounds.** Strict max 2 concurrent teammates.

### Dependency Graph

```
T1 ─────────────────────────┐
                             ├──→ T5, T6, T7
T2 ──→ T4 ──→ T11, T12 ────┘
  │          ├──→ T5, T6, T7
  │          └──→ T8 (also depends on T2 directly)
  └──→ T8
T9 ──→ T10
```

### Critical Path: T2 → T4 → T5/T6/T7

CLAUDE.md defines the protocol terms that agent-common-protocol references, which in turn
defines the context receipt pattern that skills must follow. T1 (SKILL.md) is independent
and can start immediately in parallel with T2.

---

## 9. Risk Assessment

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R-1 | Semantic loss during NLP conversion | Medium | Critical | Preservation checklist verified 28/28 + 5 new behaviors |
| R-2 | Implementers deviate from design text | Low | High | Full rewritten text provided — minimal interpretation needed |
| R-3 | DIA v6.0 too permissive (passes weak understanding) | Medium | Medium | Impact Map provides objective baseline; max attempts preserved |
| R-4 | Agent files inconsistent after parallel implementation | Low | Medium | Template pattern + Phase 8 integrator verification |
| R-5 | Line targets exceeded | Low | Low | Targets are approximate; semantic quality > line count |
| R-6 | PT description size exceeds Task API limits | Medium | Medium | If limited: split Impact Map to file, PT holds path reference (from permanent-tasks design F-2) |
| R-7 | TaskGet not available during context loss | Low | High | TaskGet is in every agent's tool list; TaskList + subject search as backup |
| R-8 | Impact Map empty in early phases | Medium | Low | Early phases (1-2) may not have Impact Map yet; Lead uses judgment until populated |
| R-9 | Cross-session PT access scope mismatch | Medium | Medium | Use CLAUDE_CODE_TASK_LIST_ID env var for shared scope (from permanent-tasks design F-4) |

### R-8 Detail: Impact Map Availability by Phase

The Impact Map is populated progressively:
- **Phase 1 (Discovery):** Lead creates initial PT with User Intent + Constraints. Impact Map may be empty.
- **Phase 2 (Research):** Researcher findings inform initial Impact Map entries.
- **Phase 3 (Architecture):** Architect produces comprehensive Impact Map as part of design.
- **Phase 4+ (Design/Implementation):** Impact Map is mature and authoritative.

LDAP questions in Phases 2-3 use Lead judgment + partial Impact Map. By Phase 4+, Impact Map
is the primary reference. This progressive enrichment is acceptable — the map grows with understanding.

---

## Appendix A: Full Line Count Projection

| File | Current (v5.1) | Original L3 (v1) | This L3 (v2, PT) | Δ from v5.1 |
|------|----------------|-------------------|-------------------|-------------|
| CLAUDE.md | 207 | 132 | 136 | -34% |
| agent-common-protocol.md | 79 | 48 | 52 | -34% |
| researcher.md | 79 | 48 | 50 | -37% |
| architect.md | 89 | 55 | 57 | -36% |
| devils-advocate.md | 73 | 48 | 48 | -34% |
| implementer.md | 114 | 68 | 70 | -39% |
| tester.md | 90 | 58 | 60 | -33% |
| integrator.md | 116 | 68 | 70 | -40% |
| **Total** | **847** | **525** | **543** | **-36%** |

Original L3 target was 525 (38% reduction). v2 design: 543 (36% reduction).
Net cost of +18 lines for PERMANENT Task + Impact Map integration across 8 files.

---

## Appendix B: Change Delta from Original L3 (architect-1)

This appendix documents every change made from the original L3 to this v2.

### CLAUDE.md Changes (132 → 136 lines)

| Section | Original L3 Text | v2 Text | Reason |
|---------|-----------------|---------|--------|
| Header subtitle | "Natural language DIA" | "Natural language DIA · PERMANENT Task context" | PT identity |
| §0 artifacts list | "GC, tasks, L1/L2/L3, ..." | "tasks, L1/L2/L3, ..." | GC no longer exists |
| §3 Lead paragraph | "maintains orchestration-plan.md and global-context.md (versioned GC-v{N})" | "maintains orchestration-plan.md and the PERMANENT Task (versioned PT-v{N})" + description + /permanent-tasks reference | PT replaces GC |
| §3 Teammates | "explain your understanding" | "read the PERMANENT Task via TaskGet and explain your understanding" | Self-serve context |
| §4 Lead→Teammate | "Task assignments with context" | "Task assignments with PERMANENT Task ID and task-specific context" | PT ID in directives |
| §4 Lead→Teammate | "context updates when scope changes" | "context updates when PT version changes" | PT versioning |
| §4 Teammate→Lead | "Understanding of assigned task" | "Understanding of assigned task (referencing Impact Map)" | Impact Map awareness |
| §6 "Assigning Work" | "Include global context (GC-v{N})" (3 lines) | "Include the PERMANENT Task ID (PT-v{N})" + TaskGet explanation (4 lines) | CIP → TaskGet |
| §6 "Verifying Understanding" | "Focus on interconnection awareness" | "Ground your questions in the PERMANENT Task's Codebase Impact Map" + 2 additional lines | Impact Map grounded |
| §6 "Monitoring Progress" | 3 lines | 4 lines with Impact Map reference | Impact Map for deviation detection |
| §6 "Coordination Infrastructure" | GC versioning, output dir with global-context.md | PT versioning description, output dir without global-context.md | Full PT migration |
| §9 Lead recovery | "Read orchestration-plan.md, task list" | "Read orchestration-plan.md, task list (including PERMANENT Task)" | PT in recovery |
| §9 Teammate recovery | "See agent-common-protocol.md" | + "You can call TaskGet on the PERMANENT Task for immediate self-recovery" | Self-recovery |
| §10 Lead 2nd bullet | Not present | "Create the PERMANENT Task at pipeline start. Maintain via Read-Merge-Write. Archive at work end." | PT lifecycle |
| §10 Lead 4th bullet | "Challenge teammates with probing questions that test systemic awareness" | + "grounded in the Codebase Impact Map" | Impact Map grounded |
| §10 Teammate 1st bullet | "Confirm you received and understood the context" | "Read the PERMANENT Task via TaskGet and confirm" | TaskGet context |
| §10 Teammate 2nd bullet | "component names, interface references, propagation chains" | "reference the Impact Map's module dependencies, interface contracts, and propagation chains" | Impact Map evidence |
| §10 See also | ends with "(automated enforcement)" | + ", `/permanent-tasks` skill (mid-work updates)" | Skill reference |

### agent-common-protocol.md Changes (48 → 52 lines)

| Section | Change | Reason |
|---------|--------|--------|
| Context Receipt | "Read the global context and task context" → "Read the PERMANENT Task via TaskGet using the Task ID" + PT version confirmation | TaskGet self-serve |
| Mid-Work Update | "Read the updated global context" → "Call TaskGet on the PERMANENT Task to read the latest content" | TaskGet |
| Task API | Added: "and read the PERMANENT Task for project context" | PT reading is now core Task API use |
| Context Loss | "Wait for Lead to send fresh context" → "Call TaskGet on PERMANENT Task" + TaskList discovery + note about self-recovery | Self-recovery via TaskGet |

### Agent .md Changes (all 6 files, +2 lines average)

| Section | Change | Applies To |
|---------|--------|-----------|
| Before Starting Work | Added "Read the PERMANENT Task via TaskGet" + Impact Map references | researcher, architect, implementer, tester, integrator |
| If Lead Asks Probing Questions | Added Impact Map reference for defense | architect, implementer, integrator, tester |
| How to Work (devils-advocate) | Added "Read the PERMANENT Task via TaskGet" | devils-advocate only |
| No structural changes | Template remains 6-section | All 6 |

### DIA v6.0 Changes

| Aspect | Original L3 | v2 | Reason |
|--------|-------------|-----|--------|
| Question generation | "Lead generates questions organically based on specific task context" | "Lead generates questions from the Impact Map and task context" | Impact Map grounded |
| Evidence requirement | "specific component names, interface references, propagation chains" | "documented interface references, propagation chains from the Impact Map" | Authoritative data |
| Pass criteria | "genuine understanding of interconnections" | "genuine understanding of interconnections (referencing Impact Map data)" | Objective baseline |
| Example questions | Generic "walk me through propagation" | Impact Map specific: "Impact Map shows three downstream consumers" | Concrete grounding |

### Implementation Task Breakdown Changes

| Original L3 | v2 |
|-------------|-----|
| 4 tasks (T1-T4) | 12 tasks (T1-T12) |
| T1: CLAUDE.md | T1: SKILL.md CREATE, T2: CLAUDE.md, T4: common-protocol, T5-T7: skills, T8: hook, T9-T10: memory, T11-T12: agents |
| 2-4 implementers | Max 2 concurrent, 5-6 rounds |
| T1∥T2 → T3∥T4 | T1∥T2 → T4∥T11 → T5∥T6 → T7∥T8 → T9∥T10 → T12 |

### New Risks Added

- R-6: PT description size limit
- R-7: TaskGet availability during context loss
- R-8: Impact Map empty in early phases
- R-9: Cross-session PT access scope mismatch
