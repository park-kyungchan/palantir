# [PERMANENT] Task API Guideline — Agent Teams Edition

> **Status:** [PERMANENT] — Must be read by EVERY agent before ANY Task API call.
> **Applies to:** Lead, all Teammates, all Subagents spawned by Teammates.
> **Version:** 1.0 (Agent Teams)

---

## 1. Mandatory Pre-Call Protocol

**BEFORE** calling `TaskCreate`, `TaskUpdate`, `TaskList`, or `TaskGet`:

1. Read this file (`.claude/references/task-api-guideline.md`)
2. Read your own context:
   - **Teammates:** Read `task-context.md` in your output directory
   - **Lead:** Read `orchestration-plan.md`
3. Ensure Task description meets the Comprehensive Requirements below

---

## 2. Comprehensive Task Creation

Every `TaskCreate` call MUST produce a task that is:
- **DETAILED** — No ambiguity in what needs to be done
- **COMPLETE** — All acceptance criteria explicitly listed
- **DEPENDENCY-AWARE** — Full dependency chain documented
- **IMPACT-AWARE** — Downstream impact explicitly stated
- **VERIFIABLE** — Clear success/failure criteria

### Required Fields

**subject:** Imperative action verb + specific target
- Good: "Implement user authentication module"
- Bad: "Work on auth"

**description:** Must include ALL of the following sections:

```
## Objective
[What this task accomplishes — 1-2 sentences]

## Context in Global Pipeline
- Phase: [which phase this belongs to]
- Upstream: [what tasks produced the inputs for this task]
- Downstream: [what tasks depend on this task's output]

## Detailed Requirements
1. [Specific requirement]
2. [Specific requirement]
...

## Interface Contracts
- [What interfaces/APIs this task must satisfy]
- [What data formats this task must produce]

## File Ownership
- [Exact list of files this task may create/modify]

## Dependency Chain
- blockedBy: [list of task IDs, or [] if none]
- blocks: [list of task IDs that wait for this task]

## Acceptance Criteria
1. [Verifiable criterion]
2. [Verifiable criterion]
...

## Semantic Integrity Check
- [PERMANENT] rules this task enforces: [list]
- Downstream impact if output changes: [description]
```

**activeForm:** Present continuous form (e.g., "Implementing user authentication")

---

## 3. Dependency Chain Rules

| Rule | Rationale |
|------|-----------|
| Every task MUST declare `blockedBy` (even if empty `[]`) | Forces conscious consideration of dependencies |
| Every task MUST declare what it `blocks` | Forces awareness of downstream impact |
| Circular dependencies are FORBIDDEN | Prevents deadlocks in distributed execution |
| Cross-Teammate dependencies MUST be reported to Lead | Lead needs this for DIA cross-impact analysis |

---

## 4. Task Lifecycle

```
pending → in_progress → completed
            ↓
         blocked → wait for blockers to complete
```

- **Before starting:** Check `blockedBy` is empty
- **During work:** Update status to `in_progress`
- **On completion:** Update to `completed` + send Status Report to Lead
- **On blocker:** Update with `addBlockedBy` + send Status Report with BLOCKED

---

## 5. [PERMANENT] Semantic Integrity Integration

### Teammate-Level
Before EVERY Task API call:
1. Read `task-context.md` — understand your position in the global pipeline
2. Read this guideline — refresh the comprehensive requirements
3. Include in Task description:
   - Which [PERMANENT] rules this task enforces
   - What downstream impact this task has
   - What interface contracts this task must satisfy
4. Create comprehensive Task with full dependency chains

### Lead-Level (DIA)
Before EVERY Task API call:
1. Read `orchestration-plan.md` — understand current pipeline state
2. Read all active teammates' L1-index.yaml — understand current progress
3. Verify no cross-impact conflicts exist
4. Update task-context.md for affected teammates if deviation detected

---

## 6. Anti-Patterns

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| `TaskCreate({subject: "Do the thing"})` | Full comprehensive description |
| Skipping `blockedBy` declaration | Always declare, even if `[]` |
| Not reading task-context.md first | ALWAYS read before Task API call |
| Creating tasks without acceptance criteria | Every task must be verifiable |
| Ignoring downstream impact | Always state what this task blocks |
| Updating status without Status Report | Always notify Lead on completion |

---

## 7. Sub-Orchestrator Task Patterns

When a Teammate acts as Sub-Orchestrator (spawning subagents):

1. **Parent Task:** Create a parent task for the overall sub-workflow
2. **Child Tasks:** Create child tasks with `blockedBy` pointing to prerequisites
3. **Nesting Limit:** Subagents spawned by Teammate CANNOT spawn further subagents (depth = 1)
4. **Boundary Constraint:** All sub-tasks must stay within the Teammate's assigned file ownership
5. **Reporting:** Report significant sub-orchestration decisions to Lead via Status Report
