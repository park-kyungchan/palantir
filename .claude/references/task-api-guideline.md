# Task API Guideline — Agent Teams Edition

> **Version:** 6.0 (NLP + INFRA v7.0 consolidation) | Updated: 2026-02-10
> **Ownership:** Only Lead calls TaskCreate/TaskUpdate. Teammates: TaskList/TaskGet only.

---

## 1. Before Using Task API

Read this file before your first Task API call. Lead reads orchestration-plan.md for pipeline
state. For DIA, verification, and team coordination, see CLAUDE.md §3-§6 and agent-common-protocol.md.

---

## 2. Storage, Scoping & Configuration

Tasks are scoped to either a team or a session — cross-scope access is impossible.

| Context | Storage | Accessible By |
|---------|---------|---------------|
| Team | `~/.claude/tasks/{team-name}/` | All team members |
| Solo | `~/.claude/tasks/{sessionId}/` | That session only |

Always use TeamCreate to establish team scope. Solo-scoped tasks become orphaned on context clear.

In team scope, all members can read all tasks via TaskList/TaskGet. Write access (TaskCreate/TaskUpdate) is restricted to Lead by disallowedTools enforcement.

Metadata uses merge semantics: `{"key": "value"}` adds/updates, `{"key": null}` deletes,
omitted keys are preserved.

For cross-session persistence, set `CLAUDE_CODE_TASK_LIST_ID=palantir-dev` before launch.
Priority: env var (highest) → team_name from TeamCreate → session-scoped (lowest).

---

## 3. Creating Tasks

Every TaskCreate call must produce a task that is detailed, complete, dependency-aware,
impact-aware, and verifiable.

**subject:** Imperative verb + specific target (e.g., "Implement user authentication module").

**description:** Include all of these fields:
- **Objective:** 1-2 sentences — what this task accomplishes
- **Context:** Phase number, upstream tasks, downstream consumers
- **Detailed Requirements:** Numbered specific requirements
- **Interface Contracts:** (mandatory) APIs and data formats this task must satisfy
- **File Ownership:** (mandatory) Exact files this task may create/modify
- **Dependency Chain:** blockedBy and blocks task IDs (always declare, even if [])
- **Acceptance Criteria:** Numbered verifiable criteria

**activeForm:** Present continuous (e.g., "Implementing user authentication").

When RTD is active, note the current Decision Point context in the task description
so teammates can link their L1/L2 outputs via pt_goal_link.

---

## 4. Dependencies

| Rule | Rationale |
|------|-----------|
| Always declare `blockedBy` (even if `[]`) | Forces conscious dependency consideration |
| Always declare what task `blocks` | Forces downstream impact awareness |
| No circular dependencies | Prevents deadlocks |
| Cross-teammate deps → report to Lead | Lead needs this for impact analysis |

addBlockedBy and addBlocks auto-sync bidirectionally. Blocker completion does NOT
auto-remove blockedBy — entries persist. Use TaskList (filters completed) for
blocked/unblocked judgment, not TaskGet (shows raw including completed).

Warning: Using TaskGet to check if blocked is a common mistake — always use TaskList.

---

## 5. Lifecycle

```
pending → in_progress → completed (may be auto-cleaned, see §6 ISS-001)
                         deleted (file removed, "Task not found" on future access)
```

Before starting, check blockedBy is resolved (use TaskList, not TaskGet).
On completion, update status and message Lead with a summary.
On blocker, update with addBlockedBy and message Lead.

Save critical information to L1/L2/L3 before marking complete — completed tasks may be auto-deleted.

---

## 6. Known Issues

**ISS-001: Completed Task Auto-Cleanup [HIGH]**
Completed tasks may be auto-deleted from disk. Save critical information to L1/L2/L3
before marking complete.

**ISS-003: Task Orphaning on Context Clear [HIGH]**
Context clear creates new sessionId — previous tasks become invisible.
Always use team scope or set `CLAUDE_CODE_TASK_LIST_ID`.

**ISS-004: Platform Limitations**
`/resume` cannot restore teammates (use L1/L2 handoff), one team per session,
no nested teams, fixed lead (plan at team creation).

**ISS-005: Teammate Auto-Compact Recovery [HIGH]**
Lead's PreCompact hook only protects Lead. Teammates must save L1/L2/L3 proactively.
On ~75% pressure, save immediately and report to Lead.
See CLAUDE.md §9 and agent-common-protocol.md for recovery procedures.

---

## 7. Sub-Orchestration

When a teammate spawns subagents via the Task tool:
- Use Task tool only (TaskCreate is blocked for teammates).
- Nesting depth = 1 (subagents cannot spawn further subagents).
- All sub-work stays within the teammate's assigned file ownership.
- Report sub-orchestration decisions to Lead via SendMessage.
