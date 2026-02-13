# context:fork Mechanism — Deep Analysis

## 1. Fork Mechanism Behavior

### How context:fork Works (Evidence-Based)

**Source:** skills-reference.md (claude-code-setup plugin), design doc §9.1

The `context: fork` frontmatter field causes a skill to execute in an **isolated subagent**
instead of the invoking agent's context window. The `agent:` field specifies which agent
type the fork runs as.

**Frontmatter syntax:**
```yaml
---
name: my-skill
context: fork
agent: Explore  # agent type for the fork
---
```

**Known example (pr-check):**
```yaml
---
name: pr-check
description: Review PR against project checklist
disable-model-invocation: true
context: fork
---
## PR Context
- Diff: !`gh pr diff`
- Description: !`gh pr view`
Review against [checklist.md](checklist.md).
```

### Context Inheritance Model

**Dynamic Context (`!command`):**
- Per design doc §9.1: "Preprocessed BEFORE Claude sees skill — shell commands replaced with output"
- Dynamic Context is resolved on the **invoking agent's** machine before fork starts
- The fork agent sees rendered output, not !commands
- This means fork agents DO receive Dynamic Context data

**Conversation history:**
- Fork agents do NOT inherit the invoking agent's conversation history
- They start with a clean context window containing only:
  1. The agent .md body (system instructions)
  2. The rendered skill content (with Dynamic Context resolved)
  3. $ARGUMENTS (if provided)
- Evidence: pr-check example works standalone without conversation context

**$ARGUMENTS:**
- Per §9.1: "$0/$1 = indexed args, $ARGUMENTS = full string"
- "Preprocessed before Claude — not variable references but literal substitutions"
- $ARGUMENTS is substituted BEFORE fork, so fork agent sees the literal value

### Fork Return Model

**UNKNOWN — Limited documentation.** Based on standard subagent behavior:
- The Task tool returns the agent's final output as a message to the invoking agent
- The invoking agent receives a summary or full output from the fork
- The fork's context is discarded after completion
- No persistent state from fork to invoker except the returned message

## 2. Agent Type Resolution in Fork

### `agent:` Field Semantics

**Evidence from pr-check:** Uses `agent: Explore` — a built-in agent type.

**Key question:** Can `agent:` reference a custom `.claude/agents/{name}.md` agent?

**Analysis from design doc §9.2:**
The Task tool's `subagent_type` parameter references custom agent .md files:
```
subagent_type: "implementer" → .claude/agents/implementer.md loaded as system instructions
```

The `agent:` field in skill frontmatter appears to work the same way — it specifies the
agent type that the fork runs as. If a custom agent file exists at `.claude/agents/{name}.md`,
it should be loaded as the fork agent's system instructions.

**Confidence: 70%** — The pr-check example only shows a built-in type (`Explore`). Custom
agent resolution is inferred from Task tool behavior but not explicitly documented for
skill frontmatter.

### Agent .md Frontmatter in Fork Context

If the `agent:` field resolves to a custom agent .md, the fork agent would get:
- `tools:` — allowed tool list
- `disallowedTools:` — blocked tools
- `permissionMode:` — permission mode
- `model:` — model selection
- `memory:` — memory scope
- Body content as system instructions

**Critical for D-10:** If we create `pt-manager.md` with `tools: [TaskCreate, TaskUpdate, ...]`,
the fork agent SHOULD have Task API write access — overriding the "Lead-only" restriction
because the restriction is enforced via `disallowedTools` in agent .md, not at the CC platform level.

## 3. Task API Access in Fork

### Current Restriction Mechanism

CLAUDE.md §10: "Only Lead creates and updates tasks (enforced by disallowedTools restrictions)."
agent-common-protocol.md: "Tasks are read-only for you: use TaskList and TaskGet."

**How it's enforced:**
Every existing agent .md has:
```yaml
disallowedTools:
  - TaskCreate
  - TaskUpdate
```

This means the restriction is **NL + agent frontmatter**, not a CC platform constraint.
The Task API tools (TaskCreate, TaskUpdate) are standard CC tools available to any agent
that doesn't explicitly block them.

### Fork Agent Task API Access

If we create a new agent .md (e.g., `pt-manager.md`) WITHOUT TaskCreate/TaskUpdate in
disallowedTools, and WITH them in the tools list:

```yaml
---
name: pt-manager
tools:
  - TaskList
  - TaskGet
  - TaskCreate
  - TaskUpdate
  - mcp__sequential-thinking__sequentialthinking
  - Read
  - Glob
  - Grep
  - AskUserQuestion
disallowedTools: []
---
```

The fork agent SHOULD have full Task API access.

**Risk: Task scope in fork.** When a skill runs in fork context, which task list does the
fork agent see? Options:
1. The **main session's** task list (where PT lives) — needed for permanent-tasks
2. A **team's** task list (if team_name specified) — not applicable
3. A **new empty** task list — would break permanent-tasks entirely

Based on standard CC behavior, the fork likely shares the main session's task list since
it's running in the same workspace. But this needs verification.

## 4. Per-Skill Feasibility Assessment

### 4.1 permanent-tasks (279L) — MEDIUM-HIGH RISK

**Lead-context dependencies:**
- **Conversation history:** HIGH — "Extract from the full conversation + $ARGUMENTS" (Step 2A)
- **Task API:** Full CRUD — TaskList, TaskCreate, TaskGet, TaskUpdate
- **User interaction:** AskUserQuestion (feature clarification)
- **MCP tools:** sequential-thinking
- **Dynamic Context:** git log, existing plans, CLAUDE.md version
- **Skill invocation from within:** None

**Fork feasibility issues:**
1. **CRITICAL: Conversation history loss.** Step 2A says "Extract from the full conversation + $ARGUMENTS."
   Fork agent has NO conversation history. It can only work with $ARGUMENTS and Dynamic Context.
   - **Mitigation:** Require callers to pass all context via $ARGUMENTS. Dynamic Context already
     captures infrastructure state, git log, and plans. But conversation-derived requirements
     (user's verbal instructions, mid-conversation corrections) would be lost.
   - **Alternative:** The `prompt:` parameter when spawning via Task tool CAN include conversation
     context — but that's the Task tool path (Agent Teams), not the skill frontmatter path (fork).

2. **Task API scope:** Fork agent needs to see main session's task list to find/create/update PT.

3. **Other skills invocation:** permanent-tasks doesn't invoke other skills — safe.

**Verdict: FEASIBLE with degradation.** Loss of conversation context is significant.
$ARGUMENTS must carry the full context payload. For Phase 0 auto-invocation scenarios
(where pipeline skills invoke /permanent-tasks), this works fine because the calling skill
already has structured context. For standalone manual invocation by users, the $ARGUMENTS
would need to be comprehensive.

### 4.2 delivery-pipeline (471L) — HIGH RISK

**Lead-context dependencies:**
- **Conversation history:** LOW-MEDIUM (mostly uses Dynamic Context + PT)
- **Task API:** TaskList, TaskGet, TaskUpdate (mark DELIVERED, complete tasks)
- **User interaction:** HEAVY — 5+ USER CONFIRMATION REQUIRED gates (commit, PR, cleanup, MEMORY.md)
- **MCP tools:** sequential-thinking
- **Dynamic Context:** Heavy — gate records, archives, plans, git status, session dirs
- **File system:** Extensive — Read, Write, Glob, Edit (MEMORY.md, ARCHIVE.md, cleanup)
- **Git:** Bash for git status, diff, add, commit; gh pr create
- **Skill invocation:** /permanent-tasks (if PT not found)

**Fork feasibility issues:**
1. **User interaction model.** 5+ user confirmation gates. AskUserQuestion is a standard tool;
   if the fork agent has it, user interactions go through the fork → user → fork loop directly.
   This should work if the fork agent has AskUserQuestion in its tools list.

2. **Git operations.** Fork agent needs Bash for git commands. If the agent .md grants Bash,
   this works. But git operations in a fork are risky — the fork agent can't see
   Lead's approval of commits. The user must confirm directly to the fork agent.

3. **Skill invocation from fork.** delivery-pipeline can invoke /permanent-tasks. Can a fork
   agent invoke a skill? Skills are loaded at session start. A fork agent IS a session, so
   it should have skills available. But would invoking /permanent-tasks from a fork create
   a NESTED fork? This is poorly documented.

4. **Task API Update.** Needs to mark PT as DELIVERED and complete tasks.

5. **File system scope.** Needs to read `.agent/teams/*/` directories and write ARCHIVE.md,
   MEMORY.md. Fork agent shares the same filesystem, so this should work.

**Verdict: FEASIBLE but complex.** The skill is already self-contained (Lead-only, no teammates).
Fork would isolate it from Lead's context window. Main risks: nested skill invocation,
user confirmation loop behavior, git operation safety.

### 4.3 rsil-global (452L) — LOW RISK

**Lead-context dependencies:**
- **Conversation history:** LOW — uses Dynamic Context for most info
- **Task API:** Read-only (TaskList, TaskGet)
- **User interaction:** AskUserQuestion for BREAK items, user approval
- **MCP tools:** sequential-thinking
- **Dynamic Context:** session dirs, gate records, L1 count, git diff, RSIL memory, tracker
- **File system:** Read (gate records, L1, L2), Write (tracker, agent memory)
- **Git:** Bash for git diff
- **Skill invocation:** /permanent-tasks (if PT not found)
- **Agent spawning:** codebase-researcher at Tier 3 (rare)

**Fork feasibility issues:**
1. **Agent spawning from fork.** At Tier 3, rsil-global spawns a codebase-researcher.
   Can a fork agent spawn subagents via Task tool? This is the critical question.
   If the fork agent has the Task tool, it should be able to spawn agents. But the
   spawned agent runs in the fork's context, NOT Lead's context.

2. **Task API is read-only** — no restriction conflicts.

3. **Mostly self-contained.** Low conversation dependency, rich Dynamic Context.

**Verdict: HIGHLY FEASIBLE.** Best fork candidate. Low conversation dependency,
read-only Task API, rich Dynamic Context. Only risk is rare Tier 3 agent spawning.

### 4.4 rsil-review (549L) — MEDIUM RISK

**Lead-context dependencies:**
- **Conversation history:** LOW — $ARGUMENTS is the primary input
- **Task API:** TaskList, TaskGet (read), TaskUpdate (PT update in R-4)
- **User interaction:** AskUserQuestion (R-0 clarification), user approval (R-2)
- **MCP tools:** sequential-thinking
- **Dynamic Context:** Heavy — hooks, settings, agents, skills, CLAUDE.md, git diff, RSIL memory
- **File system:** Read, Edit (apply FIX items), Write (tracker, memory)
- **Git:** None directly
- **Skill invocation:** /permanent-tasks (if PT not found)
- **Agent spawning:** claude-code-guide + codebase-researcher (R-1 parallel)

**Fork feasibility issues:**
1. **Agent spawning from fork.** R-1 spawns TWO agents (claude-code-guide + codebase-researcher)
   in parallel. This is a core part of the skill — the fork agent is a sub-orchestrator.
   If the fork agent has the Task tool, this should work, but it means the fork is managing
   a mini-pipeline within itself.

2. **Task API Update.** R-4 updates PT with RSIL results. Needs TaskUpdate.

3. **Edit tool for R-3.** Applies FIX items to .claude/ files. Fork agent needs Edit access.

4. **Nested /permanent-tasks.** Same concern as delivery-pipeline.

**Verdict: FEASIBLE with Task API modification.** Main challenges are agent spawning
from fork and TaskUpdate access. If both work, rsil-review is a good fork candidate
because its input ($ARGUMENTS) is self-contained.

## 5. Cross-Cutting Concerns

### 5.1 Skill Invocation from Fork (Nested Fork Risk)

All 4 skills can invoke /permanent-tasks. If /permanent-tasks ALSO has `context: fork`,
would this create a nested fork (fork-within-fork)? CC behavior is undocumented for this case.

**Mitigation options:**
- Keep permanent-tasks as a non-fork skill (runs in the calling agent's context)
- Have the fork agent use Task tool + pt-manager subagent_type instead of /permanent-tasks skill

### 5.2 AskUserQuestion in Fork

Fork agents need user interaction. AskUserQuestion is a standard CC tool. If the fork
agent has it, the user should see the question and respond directly. This creates a direct
user↔fork communication channel that bypasses Lead.

**Implication:** During fork execution, Lead is NOT involved in user decisions. The fork
agent handles the full interaction independently. This is actually the INTENDED behavior
for context isolation — Lead doesn't need to process these interactions.

### 5.3 Dynamic Context Timing

Dynamic Context is resolved BEFORE fork starts. This means:
- The fork agent sees a SNAPSHOT of system state at invocation time
- If the fork takes long (delivery-pipeline can take minutes), the snapshot may be stale
- For rsil-global/rsil-review, this is fine (they need current state at assessment start)
- For delivery-pipeline, git status could change during execution

### 5.4 Hooks in Fork

Fork agents run as separate CC instances. Hooks defined in settings.json should fire
for fork agents too (they're session-level, not agent-level). This means:
- SubagentStart fires when the fork spawns subagents
- PostToolUse captures fork agent's tool calls
- PreCompact fires if the fork's context compacts

### 5.5 Memory Access in Fork

If the fork agent .md has `memory: user` or `memory: project`, it should have access
to persistent memory at `~/.claude/agent-memory/{name}/MEMORY.md`. This enables
cross-session learning for fork agents (useful for rsil-agent).

## 6. New Agent .md Files Needed (D-11)

### 6.1 pt-manager (for permanent-tasks fork)

```yaml
---
name: pt-manager
description: Manages the PERMANENT Task — creates, reads, updates via Task API. Fork-context agent for /permanent-tasks skill.
model: opus
permissionMode: default
memory: user
tools:
  - TaskList
  - TaskGet
  - TaskCreate
  - TaskUpdate
  - Read
  - Glob
  - Grep
  - AskUserQuestion
  - mcp__sequential-thinking__sequentialthinking
disallowedTools: []
---
```

**Unique: Full Task API access.** This is the D-10 exception — "Lead-delegated fork agents."

### 6.2 delivery-agent (for delivery-pipeline fork)

```yaml
---
name: delivery-agent
description: Phase 9 delivery agent — consolidates pipeline, creates commits, archives artifacts. Fork-context agent for /delivery-pipeline skill.
model: opus
permissionMode: default
memory: user
tools:
  - TaskList
  - TaskGet
  - TaskUpdate
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - TaskCreate
---
```

**Note:** TaskUpdate needed (mark DELIVERED), TaskCreate NOT needed. Bash for git ops.

### 6.3 rsil-agent (for rsil-global and rsil-review fork)

```yaml
---
name: rsil-agent
description: RSIL quality assessment agent — applies 8 lenses, integration audit, AD-15 filter. Fork-context agent for /rsil-global and /rsil-review skills.
model: opus
permissionMode: default
memory: user
tools:
  - TaskList
  - TaskGet
  - TaskUpdate
  - Task  # For spawning codebase-researcher / claude-code-guide in R-1 and G-2
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - TaskCreate
---
```

**Note:** Shared by both rsil-global and rsil-review. Needs Task tool for agent spawning.
TaskUpdate for PT update (rsil-review R-4). Edit for applying FIX items (rsil-review R-3).

## 7. Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Conversation history loss (permanent-tasks) | HIGH | Require comprehensive $ARGUMENTS; add Dynamic Context for user intent |
| Agent spawning from fork (rsil-review, rsil-global Tier 3) | MEDIUM | Needs verification; if Task tool is available in fork, should work |
| Nested skill invocation (/permanent-tasks from fork) | MEDIUM | Keep permanent-tasks non-fork, or use Task tool + pt-manager instead |
| Task API scope in fork | MEDIUM | Fork likely shares main session task list; needs verification |
| User interaction in fork | LOW | AskUserQuestion bypasses Lead — intended behavior |
| Dynamic Context staleness | LOW | Snapshot at invocation time; acceptable for all skills |
| Custom agent resolution via `agent:` | MEDIUM | Needs verification; only built-in types documented |
| Git operations in fork (delivery-pipeline) | LOW | User confirms directly to fork agent |

## 8. Unknowns Requiring CC Research

1. **Can `agent:` field reference custom `.claude/agents/{name}.md`?** Only built-in type
   (`Explore`) documented in examples.
2. **Can a fork agent spawn subagents via Task tool?** No documentation found.
3. **What task list does a fork agent see?** Main session or isolated?
4. **Can a fork agent invoke other skills?** Would /permanent-tasks from fork create nested fork?
5. **Fork return model:** Does the invoking agent get full output or summary?
6. **Fork agent lifecycle:** Does the fork terminate after skill execution, or persist?
