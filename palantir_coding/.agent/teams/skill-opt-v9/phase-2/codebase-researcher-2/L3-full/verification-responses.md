# Verification Responses — Domain 3

## VQ-1: Task API in Fork — Priority-1 Finding

### Binary Verdict: FEASIBLE (Confidence: 85%)

### Evidence Chain

**E1: CLAUDE.md §10 line 364** — "Only Lead creates and updates tasks **(enforced by disallowedTools restrictions)**"
- The enforcement mechanism is explicitly named: agent .md `disallowedTools`
- This is NOT a CC platform constraint. It's an NL + frontmatter convention.

**E2: All 43 agent .md files** — Every single one has:
```yaml
disallowedTools:
  - TaskCreate
  - TaskUpdate
```
Confirmed via Grep across `.claude/agents/*.md`. Zero exceptions.

**E3: settings.json permissions.allow** — Includes both `TaskCreate` and `TaskUpdate`:
```json
"allow": ["TaskUpdate", "TaskCreate", ...]
```
These are session-level permitted tools. No platform restriction.

**E4: sub-agents.md CC documentation** — "If `tools` field is omitted, inherits all tools from the main thread"
- Default is FULL tool inheritance. Restrictions are opt-in via `tools:` or `disallowedTools:`
- A new agent .md without these restrictions gets everything, including Task API write tools.

**E5: Frontmatter mechanics** — Agent .md `tools:` defines allowed tools, `disallowedTools:` defines blocked tools.
If we create pt-manager.md with:
```yaml
tools: [TaskCreate, TaskUpdate, TaskList, TaskGet, ...]
disallowedTools: []
```
The agent has full Task API access. No platform override blocks this.

### What Could Invalidate This

1. **Fork sandbox isolation:** If `context: fork` independently restricts tools beyond agent .md. No documentation suggests this, and the pr-check example doesn't mention tool restrictions specific to fork mode.

2. **Task list scope in fork:** If fork agent sees an ISOLATED task list (not main session's), it can call TaskCreate/TaskUpdate but they operate on a different list. This wouldn't prevent Task API access but would prevent finding/modifying the PERMANENT Task.

### Practical Test Design

```yaml
# .claude/skills/test-fork-task-api/SKILL.md
---
name: test-fork-task-api
context: fork
agent: pt-manager
---
Execute these steps and report results:
1. Call TaskList — report all tasks you see (subjects and IDs)
2. Call TaskCreate with subject "[TEST-FORK] API Access Test" and description "Testing fork Task API"
3. Report: did TaskCreate succeed? What task ID was assigned?
4. Call TaskList again — is the new task visible?
```

Combined with creating `.claude/agents/pt-manager.md` (without TaskCreate/TaskUpdate in disallowedTools). Run `/test-fork-task-api` from Lead's context and observe:
- **Success scenario:** Fork agent creates task visible in main session → D-10 VALIDATED
- **Partial success:** Fork creates task but in isolated scope → D-10 needs workaround
- **Failure:** Fork can't call TaskCreate despite agent .md allowing it → D-10 INVALIDATED

### Cascade Impact If INFEASIBLE

If Task API is NOT accessible in fork:
- **D-10 invalidated** — no "Lead-delegated fork agent" exception possible
- **D-11 partially invalidated:**
  - pt-manager becomes INFEASIBLE (needs TaskCreate)
  - delivery-agent degraded (needs TaskUpdate — could use file-based workaround)
  - rsil-agent slightly degraded (needs TaskUpdate for PT update in R-4)
- **permanent-tasks CANNOT fork** — must remain in Lead's context
- **delivery-pipeline partially degradable** — could fork without TaskUpdate, but Op-1 (mark DELIVERED) would need file-based signaling back to Lead
- **rsil-review R-4 degraded** — PT update skipped, written to file instead for Lead to apply

## VQ-2: Fork Difficulty Ranking (Easiest to Hardest)

### Analysis Framework

For each skill, I assess the **most critical Lead-context dependency** — the single thing that would break most severely if the skill ran in fork context.

### Rank 1 (Easiest): rsil-global — CRITICAL DEP: "Just-completed work" observation

**Most critical Lead-context dependency:** Knowledge of what work just completed.

**Why it's LOW risk in fork:** This dependency is fully served by Dynamic Context:
- `!ls -dt .agent/teams/*/ | head -3` — session directories
- `!ls .agent/teams/*/phase-*/gate-record*.yaml | wc -l` — gate count
- `!git diff --name-only HEAD~1 | head -20` — recent file changes
- `!cat ~/.claude/agent-memory/rsil/MEMORY.md | head -50` — prior assessment memory

The fork agent receives ALL of this pre-rendered. It does NOT need Lead's conversation to know what happened — the filesystem IS the record.

**User interaction:** Minimal — only AskUserQuestion for BREAK items (rare). Standard tool, works in fork.

**Task API:** Read-only (TaskList + TaskGet). No restriction conflict.

**Agent spawning:** Only at Tier 3 (rare, <10% of runs). Most runs complete at Tier 1 with zero findings.

**AskUserQuestion count:** 1 (BREAK items, rare)
**sequential-thinking usage:** Every tier transition (standard tool, available in fork)

### Rank 2: rsil-review — CRITICAL DEP: Target file analysis + agent orchestration

**Most critical Lead-context dependency:** R-0 Lead Synthesis (parsing $ARGUMENTS → research questions → agent directives) and R-1 agent spawning.

**Why it's MEDIUM risk in fork:** The skill's core value IS synthesis — transforming universal lenses into target-specific research questions. In Lead's context, this benefits from Lead's accumulated understanding of the INFRA. In fork context, the agent starts fresh, but $ARGUMENTS carries the target specification and Dynamic Context provides:
- All agent .md names, hook files, skill names, CLAUDE.md version, git diff, protocol line count, target file content, RSIL memory
- This is surprisingly comprehensive. R-0 synthesis primarily reads files, not conversation.

**Agent spawning from fork:** R-1 spawns claude-code-guide + codebase-researcher in parallel via Task tool. This is the main risk — can a fork agent use the Task tool? If so, the fork becomes a sub-orchestrator.

**Task API:** Needs TaskUpdate for R-4 (PT update with RSIL results). Not for core operation.

**User interaction:** AskUserQuestion (R-0 if $ARGUMENTS unclear, R-2 for approval). 2-3 user touch points.

**AskUserQuestion count:** 2-3
**sequential-thinking usage:** Every phase (R-0, R-2, R-4)

### Rank 3: permanent-tasks — CRITICAL DEP: Conversation history for requirement extraction

**Most critical Lead-context dependency:** Step 2A explicitly says "extract from the **full conversation** + $ARGUMENTS" — the conversation IS the input.

**Why it's MEDIUM-HIGH risk in fork:** Two usage patterns with different risk profiles:

**Pattern A — Auto-invoked from Phase 0 (LOW risk):**
Pipeline skills invoke `/permanent-tasks` when no PT exists. The calling context already has structured information (user's initial request is the $ARGUMENTS). Fork works fine here because $ARGUMENTS carries everything.

**Pattern B — Standalone manual invocation (HIGH risk):**
User says something like "let's also add caching to the API" mid-conversation. Lead invokes `/permanent-tasks "add caching"`. In Lead's context, the skill can see the full conversation (what API, what caching strategy was discussed, prior decisions). In fork context, it only sees `$ARGUMENTS = "add caching"` — losing all conversational nuance.

**Mitigation for Pattern B:** Lead must serialize conversation context into $ARGUMENTS before invoking the fork. This shifts work from the fork back to Lead (who must summarize context), partially defeating the context isolation benefit.

**Task API:** Full CRUD — TaskList, TaskCreate, TaskGet, TaskUpdate. This is the D-10 linchpin.

**User interaction:** Implicit (no explicit AskUserQuestion in the skill body — it just outputs to user). However, Step 2A.69 says "ask the user to clarify" which implies AskUserQuestion capability.

**AskUserQuestion count:** 0-1 (clarification only)
**sequential-thinking usage:** Every extraction and consolidation

### Rank 4 (Hardest): delivery-pipeline — CRITICAL DEP: Multi-step user confirmation loop

**Most critical Lead-context dependency:** The 5+ USER CONFIRMATION REQUIRED gates create a sustained interactive dialogue between the executing agent and the user.

**Why it's HIGH risk in fork:**

**Interaction complexity analysis (from SKILL.md evidence):**
1. **Phase 0:** AskUser if no PT found (line 72-73)
2. **Op-2:** USER CONFIRMATION for MEMORY.md write (line 179)
3. **Op-4:** USER CONFIRMATION for commit — with modification loop (line 228-235)
4. **Op-4 rejection:** User choice to keep or revert MEMORY.md (line 239-241)
5. **Op-5:** USER CONFIRMATION for PR creation (line 253)
6. **Op-6:** USER CONFIRMATION for cleanup plan (line 286)

That's potentially 6 user interaction points in a single skill execution. Each one is a back-and-forth:
- Agent presents options → User responds → Agent acts on response → Agent may re-present

In Lead's context, Lead naturally handles these interactions as part of the conversation flow. In fork context, the fork agent must manage the entire dialogue chain independently.

**This SHOULD work if AskUserQuestion works in fork** — each interaction is self-contained (present → wait → respond). The user sees fork agent's questions directly. But:
- The user might be confused about WHO is asking (Lead vs fork agent)
- If the fork compacts during a long multi-step delivery, recovery is harder (no Lead oversight)
- Op-4's modification loop (user can adjust commit, re-present) requires state tracking within fork

**Nested skill invocation:** delivery-pipeline can invoke /permanent-tasks (line 87-88). If both are forked, this creates a fork-within-fork chain. Undocumented behavior.

**Git operations:** Bash for `git status`, `git diff`, `git add`, `git commit`, `gh pr create`. Fork agent shares filesystem, so git operations work. But git operations are irreversible — running them in a fork without Lead oversight increases risk.

**AskUserQuestion count:** 5-6 (high)
**sequential-thinking usage:** All phases (discovery, consolidation, commit generation, cleanup)

### Summary: Fork Difficulty Ranking

| Rank | Skill | Fork Difficulty | Critical Dependency | AskUser Count | Task API Need |
|------|-------|----------------|---------------------|---------------|---------------|
| 1 (Easiest) | rsil-global | LOW | Dynamic Context (filesystem-based) | 0-1 | Read-only |
| 2 | rsil-review | MEDIUM | Agent spawning + target analysis | 2-3 | Update |
| 3 | permanent-tasks | MEDIUM-HIGH | Conversation history (Pattern B) | 0-1 | Full CRUD |
| 4 (Hardest) | delivery-pipeline | HIGH | 5-6 user confirmation gates | 5-6 | Update |

## VQ-3: `agent:` Field — Custom vs Built-in Resolution

### Current Evidence

**For built-in types:** pr-check example uses `agent: Explore`. This is a built-in agent type recognized by the Task tool system.

**For custom types via Task tool:** Design doc §9.2 confirms:
```
subagent_type: "implementer" → .claude/agents/implementer.md loaded as system instructions
```

**The key question:** Does `agent:` in skill frontmatter resolve the same way as `subagent_type:` in Task tool?

### Analysis

The CC system has a unified agent resolution model:
1. Built-in types: `Explore`, `Plan`, `Bash`, `general-purpose`, `claude-code-guide` (etc.)
2. Custom types: any `.claude/agents/{name}.md` file creates a custom agent type

The `subagent_type` parameter in the Task tool resolves BOTH — if the name matches a built-in, it uses the built-in; if it matches a custom agent .md file, it loads that file's body as system instructions and applies its frontmatter configuration.

**Hypothesis (confidence: 70%):** The `agent:` field in skill frontmatter uses the same resolution mechanism. If we set `agent: "rsil-agent"` and `.claude/agents/rsil-agent.md` exists, the fork should load that agent file.

**Evidence gap:** No example shows `context: fork` + `agent: "{custom-name}"`. The pr-check example uses a built-in. This 30% uncertainty is the single biggest architectural risk for D-11.

**If custom resolution fails:** The entire fork-agent architecture needs redesign:
- Cannot create pt-manager.md, delivery-agent.md, rsil-agent.md as custom agents
- Would need to use built-in agent types (like `general-purpose`) with the skill body providing all instructions
- Tool restrictions would need to come from skill `allowed-tools` frontmatter instead
- This is WORSE but still POSSIBLE — the skill content itself can instruct the agent, and `allowed-tools` can restrict dangerous tools

**Fallback architecture if custom agent resolution fails:**
```yaml
---
name: permanent-tasks
context: fork
agent: general-purpose  # built-in type
allowed-tools: TaskList, TaskGet, TaskCreate, TaskUpdate, Read, Glob, Grep, AskUserQuestion
---
# (full skill instructions including agent identity/constraints)
```

This loses the separation between persistent agent identity (agent .md) and task-specific instructions (skill .md), but functionally works.
