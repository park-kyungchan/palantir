---
name: permanent-tasks
description: "Reflect conversation context and user requirements into the PERMANENT
  Task. Creates if none exists, updates via Read-Merge-Write if one exists. Use
  mid-work when requirements change or evolve."
argument-hint: "[requirement description or context]"
---

# Permanent Tasks

Reflect user requirements and conversation context into a PERMANENT Task — the Single Source of Truth that replaces `global-context.md` for all pipeline execution. The PERMANENT Task is a Task API entity (Task #1) that persists across the pipeline lifecycle.

**Announce at start:** "I'm using permanent-tasks to reflect requirements into the PERMANENT Task."

**Core flow:** TaskList Search → CREATE (new) or READ-MERGE-WRITE (existing) → Output Summary

## When to Use

```
Need to capture or update project requirements?
├── Starting a new feature/project? ──→ /permanent-tasks "description"
├── Requirements changed mid-work? ──→ /permanent-tasks "what changed"
├── User gave new constraints? ──→ /permanent-tasks "new constraints"
└── Pipeline skill Phase 0 detected no PT? ──→ /permanent-tasks (auto-invoked)
```

This skill is used standalone or auto-invoked from Phase 0 of pipeline skills (brainstorming-pipeline, agent-teams-write-plan, agent-teams-execution-plan).

## Dynamic Context

The following is auto-injected when this skill loads.

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Recent Changes:**
!`cd /home/palantir && git log --oneline -10 2>/dev/null`

**Existing Plans:**
!`ls /home/palantir/docs/plans/ 2>/dev/null`

**User Input:** $ARGUMENTS

---

## Step 1: PERMANENT Task Discovery

Use `sequential-thinking` to analyze $ARGUMENTS and conversation context before searching.

Call `TaskList` and scan all tasks for a subject containing `[PERMANENT]`.

```
TaskList result
     │
┌────┴────┐
not found  found
│           │
▼           ▼
Step 2A    Step 2B
(CREATE)   (READ-MERGE-WRITE)
```

---

## Step 2A: Create New PERMANENT Task

When no `[PERMANENT]` task exists. Use `sequential-thinking` to extract from the full conversation + $ARGUMENTS:

1. **User Intent** — what the user wants to achieve
2. **Codebase Impact Map draft** — module dependencies, ripple paths (best effort from available context)
3. **Constraints** — technical constraints, project rules

Then create:

```
TaskCreate:
  subject: "[PERMANENT] {feature/project name}"
  description: (see PT Description Template below)
  activeForm: "Managing PERMANENT Task"
```

After creation, output a summary to the user (see Step 3).

---

## Step 2B: Update Existing PERMANENT Task (Read-Merge-Write)

When a `[PERMANENT]` task already exists.

### 2B.1 Read Current State

```
TaskGet(task_id) → read current PT description
```

Extract the current PT version number from `## [PERMANENT] — PT-v{N}`.

### 2B.2 Consolidate

Use `sequential-thinking` to merge new requirements ($ARGUMENTS + conversation) with existing content:

**Consolidation Rules:**
1. **Deduplicate** — same intent expressed differently → merge into one
2. **Resolve contradictions** — old requirement vs new requirement → keep latest intent
3. **Elevate abstraction** — 3+ specific requests sharing a principle → consolidate into the principle
4. **Result**: Always a refined current state. Never an append-only log.

Assess each section:
- **User Intent**: merge new requirements with existing
- **Codebase Impact Map**: add new dependency/ripple paths discovered; update existing
- **Architecture Decisions**: add new decisions, update changed ones
- **Phase Status**: update if phase transitions occurred
- **Constraints**: add new, remove obsolete

### 2B.3 Bump Version and Update

```
TaskUpdate:
  task_id: {PT task ID}
  description: (consolidated content with PT-v{N+1})
```

### 2B.4 Teammate Notification Decision

Use `sequential-thinking` to assess impact:

```
PT-v{N} → PT-v{N+1} change
     │
     ▼
Impact analysis on active teammates
     │
┌────┴────┐
CRITICAL   LOW
│           │
▼           ▼
Immediate   Next task only
SendMessage  (update description,
to affected  no notification)
teammates
[CONTEXT-UPDATE]
+ Task ID
```

- **CRITICAL**: Impact Map ripple paths include files owned by currently active teammates → immediate `SendMessage` with `[CONTEXT-UPDATE] PT-v{old} → PT-v{new} | Delta: {summary} | TaskGet for full content`
- **LOW**: Change affects areas unrelated to current in-progress work → no notification needed

---

## Step 3: Output Summary

Present to user after CREATE or UPDATE:

### After CREATE (Step 2A)
```markdown
## PERMANENT Task Created

**Subject:** [PERMANENT] {name}
**Version:** PT-v1
**Task ID:** {id}

**Sections initialized:**
- User Intent: {brief}
- Codebase Impact Map: {brief}
- Architecture Decisions: (pending)
- Phase Status: (pending)
- Constraints: {brief}

This task is now the Single Source of Truth for pipeline execution.
Pipeline skills will read it via TaskGet in Phase 0.
```

### After UPDATE (Step 2B)
```markdown
## PERMANENT Task Updated

**Version:** PT-v{N} → PT-v{N+1}
**Task ID:** {id}

**Changes:**
- {section}: {what changed}

**Teammate Notification:** {CRITICAL: notified {names} / LOW: no notification needed}
```

---

## PT Description Template

This is the exact structure for the PERMANENT Task description. All sections are mandatory. Section headers must match exactly — they are the interface contract for Phase 0 blocks and teammate TaskGet parsing.

```markdown
## [PERMANENT] — PT-v{N}

### User Intent
What the user wants to achieve. Refined current state only — no version history.
Consolidated on every update: deduplication, contradiction resolution,
abstraction elevation. Always a clean, coherent document.

### Codebase Impact Map
The authoritative reference for module/file dependencies and ripple paths.
Lead uses this for LDAP challenge generation.
Teammates use this for Impact Analysis.

- Module Dependencies: A → B → C (directional)
- Ripple Paths: Change X → affects {Y, Z}
- Interface Boundaries: contract points between modules
- Risk Hotspots: high ripple-risk areas

### Architecture Decisions
Confirmed design decisions with rationale. Refined state, not log.

### Phase Status
Pipeline progress. Phase-by-phase COMPLETE/IN_PROGRESS/PENDING.

### Constraints
Technical constraints, project rules, safety rules.
```

---

## Error Handling

| Situation | Response |
|-----------|----------|
| TaskList returns empty | Treat as "not found" → Step 2A |
| TaskGet fails for found ID | Report error to user, suggest manual check |
| $ARGUMENTS empty | Extract requirements from conversation context only |
| Description too large | Split Impact Map to file; PT holds path reference only |
| Multiple [PERMANENT] tasks found | Use the first one; warn user about duplicates |

---

## Key Principles

- **Single Source of Truth** — one PERMANENT Task per project, not per pipeline
- **Refined state always** — consolidation produces a clean document, never an append log
- **Interface contract** — section headers and search pattern are shared with Phase 0 blocks
- **Sequential thinking always** — structured reasoning for every extraction and consolidation
- **Lightweight** — this skill runs in ~500-1000 tokens for reads, more for consolidation
- **No pipeline orchestration** — this skill manages the PT only, not teammates or phases

## Never

- Create multiple [PERMANENT] tasks for the same project
- Append without consolidating — always deduplicate, resolve, elevate
- Change the section header names (interface contract with Phase 0 blocks)
- Change the subject search pattern `[PERMANENT]` (interface contract)
- Skip sequential-thinking for consolidation decisions
- Notify teammates for LOW-impact changes
