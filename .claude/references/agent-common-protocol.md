# Shared Protocol for All Teammates

This covers procedures common to all teammate agent types (22 agents across 10 categories). Role-specific guidance is in each agent's own .md file.

> **Coordinator routing:** If your work is assigned through a coordinator, "message Lead"
> in the sections below means "message your coordinator." For emergencies or coordinator
> failure, message Lead directly. See "Working with Coordinators" section for details.

---

## When You Receive a Task Assignment

Your task assignment from Lead includes these context layers:
1. **PERMANENT Task content** — user intent, codebase impact map, architecture decisions,
   and constraints (embedded directly in your directive by Lead)
2. **Global Context (GC)** — session-level artifacts and phase status
3. **Task-specific context** — your assignment details, file ownership, plan specs

Lead may also provide a PT Task ID. In a team context, TaskList/TaskGet only shows your
team's tasks — the PERMANENT Task may live in the main list. If TaskGet fails, rely on the
embedded content in your directive instead. Confirm receipt by messaging Lead with your
understanding of the scope.
Make sure you understand the scope, constraints, and who will consume your output before
doing anything else.

---

## When Context Changes Mid-Work

If Lead sends a context update with a new PT version:
1. Call TaskGet on the PERMANENT Task to read the latest content.
   If TaskGet fails (PT not in your team's task list), ask Lead for the updated content via SendMessage.
2. Message Lead confirming what changed, what impact it has on your current work,
   and whether you can continue or need to pause.

---

## When You Finish

1. If you have Write: write L1/L2/L3 files to your assigned output directory.
   If you don't have Write: send your full output to Lead via SendMessage.
2. Include an Evidence Sources section in L2-summary.md listing key references,
   MCP tool findings, and verification data that support your conclusions.
3. Message Lead with a summary of what you completed.

Role-specific completion details (e.g., devils-advocate verdict) are in your agent file.

---

## Working with Coordinators

Some categories use coordinators to manage workflow. If your work is assigned through
a coordinator (not Lead directly):

- **Your coordinator is your primary contact.** Report progress, issues, and
  completion to the coordinator, not to Lead.
- **Lead may still contact you directly** for cross-cutting operations (PT updates,
  emergency intervention, gate spot-checks).
- **If coordinator becomes unresponsive:** Message Lead directly. Lead will manage
  you in fallback mode (Mode 3).
- **Understanding verification:** Your coordinator verifies your understanding using
  Impact Map context. Answer their probing questions with the same rigor as you
  would for Lead.
- **Review agents:** If you receive a review request from execution-coordinator,
  respond to execution-coordinator with your review results.
- **How to know if you have a coordinator:** Your spawn directive will state
  "Your coordinator is: {name}" if you were assigned through one. If no coordinator
  is mentioned, you are Lead-direct.

---

## Task API

Tasks are read-only for you: use TaskList and TaskGet to check status, find your assignments,
and read the PERMANENT Task for project context. Task creation and updates are Lead-only
(enforced by tool restrictions).

---

## Team Memory

Read TEAM-MEMORY.md before starting work — it has context from prior phases and other teammates.

- If you have the Edit tool (implementer, infra-implementer, integrator): write discoveries to your own section.
  Use `## {your-role-id}` as anchor for edits. Never overwrite other sections.
- If you don't have Edit: message Lead with findings for relay.
- If you don't have Write: communicate results via SendMessage to Lead. Your output
  will be captured in Lead's L2 or the consuming agent's report.

---

## Saving Your Work

Write L1/L2/L3 files throughout your work, not just at the end. These files are your only
recovery mechanism — anything unsaved is permanently lost if your session compacts.
The PostToolUse hook automatically captures all tool calls to events.jsonl — no manual
event logging needed.

If you notice you're running low on context: save all work immediately, then tell Lead.
Lead will shut you down and re-spawn you with your saved progress.

### L1/L2 Project Goal Linkage (Optional)

When working on a project with RTD active, include goal references in your deliverables:

- **L1 YAML:** Add `pt_goal_link:` field to findings or task entries, referencing
  the requirement (R-{N}) or architecture decision (AD-{M}) your work addresses.
  ```yaml
  findings:
    - id: F-1
      summary: "Hooks fire for all sessions"
      pt_goal_link: "R-5 (Agent Teams Shared)"
  ```

- **L2 MD:** Add a `## PT Goal Linkage` section at the end connecting your work
  to the project's requirements and architecture decisions.

This is backward-compatible — omitting these fields does not break any process.
Lead uses them for traceability.

---

## Edge Cases

- **TEAM-MEMORY.md doesn't exist:** You may be the first teammate in this session.
  Skip the read and note this to Lead. Your section will be created when you write to it.
- **Output directory doesn't exist:** Create it before writing L1/L2/L3 files.
  Standard path: `.agent/teams/{session-id}/phase-{N}/{your-role-id}/`
- **Multiple [PERMANENT] tasks found:** Use the first one (lowest task ID).
  Warn Lead about duplicates via SendMessage.

---

## If You Lose Context

If you see "This session is being continued from a previous conversation":
1. Tell Lead immediately — do not continue working from memory alone.
2. Try TaskGet on the PERMANENT Task (find it via TaskList — subject contains "[PERMANENT]").
   If not found in your team's task list, read your own L1/L2/L3 files instead for context.
3. Read your own L1/L2/L3 files to restore your progress.
4. Reconfirm your understanding of the task before resuming.

Note: You can begin self-recovery with steps 2-3 while waiting for Lead, but always confirm
your understanding with Lead before resuming work.

---

## Agent Memory

Check your persistent memory at `~/.claude/agent-memory/{role}/MEMORY.md` when you start.
Update it when you finish — use Read-Merge-Write (read current, merge new findings, write back).

What to save:
- Patterns confirmed across multiple tasks (not one-off observations)
- Key file paths and conventions for your role
- Solutions to recurring problems
- Lessons learned from review feedback

What NOT to save:
- Session-specific context (current task details, temporary state)
- Anything that duplicates protocol or agent .md instructions
