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
