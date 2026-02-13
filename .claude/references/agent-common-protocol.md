# Shared Protocol for All Teammates

This covers procedures common to all teammate agent types (43 agents across 13 categories). Role-specific guidance is in each agent's own .md file.

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

**Exception — Fork-context agents:** If your agent .md frontmatter does NOT include
TaskCreate/TaskUpdate in `disallowedTools`, you have explicit Task API write access.
This applies only to Lead-delegated fork agents (pt-manager, delivery-agent,
rsil-agent). You are an extension of Lead's intent — use Task API only for the
specific PT operations defined in your skill's instructions.

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

### L1 Canonical Format (Mandatory Keys)

All L1-index.yaml files MUST include these top-level keys:

```yaml
agent: {your-role-id}           # e.g., "static-verifier"
phase: P{N}                      # e.g., "P2b"
status: complete | in_progress | blocked
timestamp: {ISO 8601}

# Domain-specific keys below (per your agent .md specification)
# ...

# Recommended footer
evidence_count: {N}
pt_goal_links:
  - "R-1 (Requirement Name)"
  - "AD-3 (Decision Name)"
```

**4 mandatory keys:** `agent`, `phase`, `status`, `timestamp`
**2 recommended keys:** `evidence_count`, `pt_goal_links`
Domain-specific keys: per your agent .md (e.g., `findings:`, `tasks:`, `workers:`)

### L2 Canonical Section Order

All L2-summary.md files MUST follow this section order:

1. `## Summary` — 1-3 sentence executive summary (ALWAYS FIRST)
2. `## {Domain-Specific Sections}` — Findings, decisions, reviews, etc. (per your role)
3. `## PT Goal Linkage` — Connecting work to requirements/decisions (recommended)
4. `## Evidence Sources` — Key references, MCP findings, verification data (ALWAYS present)
5. `## Downstream Handoff` — Coordinators ONLY, ALWAYS LAST (see D-011 protocol)

**Rules:** Summary first. Evidence Sources second-to-last. Downstream Handoff last
(coordinators only). Domain sections in between.

### L3 Format

No standardization. L3 is raw work product. Directory structure at your discretion.
Only requirement: L3 lives in `L3-full/` subdirectory.

### Downstream Handoff (Coordinators Only)

If you are a coordinator, your L2 MUST end with a `## Downstream Handoff` section
containing these 6 categories (populate all, even if empty):

```markdown
## Downstream Handoff
### Decisions Made (forward-binding)
### Risks Identified (must-track)
### Interface Contracts (must-satisfy)
### Constraints (must-enforce)
### Open Questions (requires resolution)
### Artifacts Produced
```

Lead reads this section to construct the next phase's directive. The next-phase agent
reads your L2 directly for detailed context. Reference-based, not paraphrase-based.

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

### Per-Agent Memory
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

### Category Memory (Shared)
Your category has a shared memory file at `.claude/agent-memory/{category}/MEMORY.md`
(e.g., `research/MEMORY.md`, `verification/MEMORY.md`). This captures cross-role patterns
within your category.

**Rules:**
- **Read it** at the start of your work for category-level context
- **Only coordinators write** to category memory (single-writer pattern to avoid conflicts)
- If you are a worker: report noteworthy patterns to your coordinator for inclusion
- If you are a coordinator: update category memory at the end of each coordination cycle
- Keep under 100 lines. Use Read-Merge-Write pattern.

---

## Error Handling

### Tier 1: Self-Recoverable
Errors you can handle without external help. Log in your L2 output and continue.
- File not found → Create from template or skip with warning
- Tool parse error → Use fallback or retry once
- MCP server timeout → Proceed without that tool's data, note in L2

### Tier 2: Escalation-Required
Errors requiring external help. Save your work immediately, then escalate.
1. Write current L1/L2/L3 files (your recovery checkpoint)
2. SendMessage to coordinator (or Lead if no coordinator):
   - What failed: exact error description
   - What you tried: Tier 1 recovery attempt (if any)
   - What you need: specific ask (re-assign, more context, intervention)
   - Current status: what work is saved and what is lost
3. Wait for response. Do NOT continue working on the failed task.
4. If no response in 5 minutes: SendMessage to Lead directly.

### Tier 3: Pipeline-Affecting
Errors that stop the pipeline. Typically handled by coordinators and Lead.
If you detect a Tier 3 error as a worker:
1. Save all work immediately
2. Escalate to coordinator with URGENT flag in SendMessage
3. The coordinator/Lead will determine: retry, skip, or abort

**Tier mapping:** File not found = Tier 1. Context pressure = Tier 2. Gate failure = Tier 3.
Worker unresponsive = Tier 2 (coordinator handles). Coordinator unresponsive = Tier 3 (Lead handles).
