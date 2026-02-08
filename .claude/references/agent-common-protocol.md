# Agent Common Protocol

Shared protocol for all teammate agents. Role-specific behavior is defined in each agent's own `.md` file.
This file covers operational procedures common to all 6 agent types.

---

## Phase 0: Context Receipt

1. Receive [DIRECTIVE] + [INJECTION] from Lead.
2. Parse embedded global-context.md (note GC-v{N}).
3. Parse embedded task-context.md.
4. Send to Lead: `[STATUS] Phase {N} | CONTEXT_RECEIVED | GC-v{ver}, TC-v{ver}`

---

## Mid-Execution Updates

On [CONTEXT-UPDATE] from Lead:
1. Parse updated global-context.md.
2. Send: `[ACK-UPDATE] GC-v{ver} received. Items: {applied}/{total}. Impact: {assessment}. Action: {CONTINUE|PAUSE|NEED_CLARIFICATION}`
3. If the update affects your current work, pause and report to Lead.

---

## Completion

1. Write L1/L2/L3 files to your assigned output directory.
2. Send to Lead: `[STATUS] Phase {N} | COMPLETE | {summary}`

Role-specific completion formats (e.g., devils-advocate verdict) are defined in the agent's own file.

---

## Task API Access

Task API is read-only for all teammates: use TaskList and TaskGet only.
TaskCreate and TaskUpdate are Lead-only (enforced via disallowedTools).

---

## Team Memory

Read TEAM-MEMORY.md before starting work for context from prior phases and other teammates.
- Agents with Edit tool (implementer, integrator): write discoveries to your own section using Edit.
  Use `## {your-role-id}` in old_string for uniqueness. Do not use Write after initial creation.
- Agents without Edit tool (researcher, architect, tester): report findings via SendMessage to Lead for relay.
- Devils-advocate: read-only access to Team Memory.

Tags: `[Finding]`, `[Pattern]`, `[Decision]`, `[Warning]`, `[Dependency]`, `[Conflict]`, `[Question]`

---

## Context Pressure & Auto-Compact

### Pre-Compact Obligation
Write intermediate L1/L2/L3 proactively throughout execution — not only at ~75%.
L1/L2/L3 are your only recovery mechanism. Unsaved work is permanently lost on compact.

### Context Pressure (~75% capacity)
1. Immediately write L1/L2/L3 files with all work completed so far.
2. Send `[STATUS] CONTEXT_PRESSURE | L1/L2/L3 written` to Lead.
3. Await Lead termination and replacement with L1/L2 injection.

### Auto-Compact Detection
If you see "This session is being continued from a previous conversation":
1. Send `[STATUS] CONTEXT_LOST` to Lead immediately.
2. Do not proceed with any work using only summarized context.
3. Await [INJECTION] from Lead with full GC + task-context.
4. Read your own L1/L2/L3 files to restore progress.
5. Re-submit [IMPACT-ANALYSIS] to Lead (TIER 0 exempt — await Lead instructions instead).
6. Wait for [IMPACT_VERIFIED] before resuming work.

---

## Memory

Consult your persistent agent memory at `~/.claude/agent-memory/{role}/MEMORY.md` at start.
Update it with patterns, lessons learned, and domain knowledge on completion.
