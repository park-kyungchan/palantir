## Summary

Investigated `context: fork` + `agent:` skill frontmatter mechanism for converting 4 Lead-only skills to isolated subagent execution. Found fork mechanism exists in CC (documented in skills-reference.md with pr-check example), Dynamic Context resolves pre-fork, and tool access is controlled via agent .md frontmatter. All 4 skills are feasible for fork conversion with varying risk levels: rsil-global (LOW), rsil-review (MEDIUM), permanent-tasks (MEDIUM-HIGH), delivery-pipeline (HIGH). Six critical unknowns remain requiring CC research.

## Fork Mechanism Findings

### How context:fork Works
- Skill frontmatter `context: fork` + `agent: "{type}"` runs skill in isolated subagent
- Only documented example: `agent: Explore` (built-in type) in pr-check skill
- Dynamic Context (`!command`) resolves BEFORE fork — fork sees rendered output
- $ARGUMENTS is literal-substituted before fork
- Fork agent does NOT inherit invoking agent's conversation history
- Fork agent starts with: agent .md body + rendered skill content + $ARGUMENTS

### Tool Access in Fork
- Controlled by agent .md `tools:` and `disallowedTools:` frontmatter
- Current "Lead-only Task API" restriction is enforced via `disallowedTools` in every agent .md, NOT at CC platform level
- Creating new agent .md without TaskCreate/TaskUpdate in disallowedTools grants full Task API
- This is the mechanism for D-10 (Lead-delegated fork agent Task API exception)

### Current State in Our Codebase
- Zero `context: fork` skills currently in use
- No agent .md uses `skills:` preload field
- All 43 agents have `disallowedTools: [TaskCreate, TaskUpdate]` (except variations)
- CLAUDE.md §10 and agent-common-protocol.md §Task API both enforce Lead-only Task API via NL

## Per-Skill Feasibility

### rsil-global (452L) — LOW RISK, HIGHLY FEASIBLE
- Low conversation dependency (Dynamic Context provides most info)
- Task API is read-only — no restriction conflicts
- Only risk: rare Tier 3 agent spawning from fork (codebase-researcher)
- Best fork candidate of all 4 skills

### rsil-review (549L) — MEDIUM RISK, FEASIBLE
- $ARGUMENTS is primary input (low conversation dependency)
- Core challenge: R-1 spawns 2 agents (claude-code-guide + codebase-researcher) in parallel
- Fork agent becomes a sub-orchestrator managing mini-pipeline
- Needs TaskUpdate for R-4 (PT update) and Edit for R-3 (apply FIX items)
- Shared `rsil-agent` with rsil-global is viable

### permanent-tasks (279L) — MEDIUM-HIGH RISK, FEASIBLE WITH DEGRADATION
- **CRITICAL:** Step 2A extracts from "full conversation + $ARGUMENTS" — conversation history LOST in fork
- Fork agent can only work with $ARGUMENTS + Dynamic Context
- For Phase 0 auto-invocation (pipeline skills calling /permanent-tasks): works fine (structured context)
- For standalone manual invocation: $ARGUMENTS must carry full context payload
- Needs full Task API (TaskCreate + TaskUpdate) — D-10 exception

### delivery-pipeline (471L) — HIGH RISK, FEASIBLE BUT COMPLEX
- 5+ USER CONFIRMATION REQUIRED gates (user interacts directly with fork agent)
- Heavy file I/O (ARCHIVE.md, MEMORY.md, cleanup)
- Git operations via Bash (commit, PR creation)
- Can invoke /permanent-tasks — nested skill invocation concern
- Already self-contained (no teammates) — good isolation candidate despite complexity

## D-10: CLAUDE.md §10 Modification Design

Current rule: "Only Lead creates and updates tasks (enforced by disallowedTools restrictions)"

Proposed modification:
```
Only Lead creates and updates tasks, except for Lead-delegated fork agents
(pt-manager, delivery-agent) which receive Task API access via their agent .md
frontmatter. Fork agents execute skills that Lead invokes — they are extensions
of Lead's intent, not independent actors.
```

agent-common-protocol.md §Task API also needs matching update:
```
Tasks are read-only for you unless you are a fork-context agent with explicit
Task API access in your agent .md frontmatter.
```

## D-11: Three New Agent .md Files

| Agent | Fork For | Task API | Special Tools |
|-------|----------|----------|---------------|
| pt-manager | permanent-tasks | Full (Create+Update) | AskUserQuestion |
| delivery-agent | delivery-pipeline | Update only | Bash (git), Edit, AskUserQuestion |
| rsil-agent | rsil-global + rsil-review | Update only | Task (agent spawning), Edit, AskUserQuestion |

## Critical Unknowns (Need CC Research)

1. **Custom agent resolution:** Can `agent:` field reference `.claude/agents/{name}.md`? Only built-in types shown in examples.
2. **Agent spawning from fork:** Can fork agent use Task tool to spawn subagents?
3. **Task list scope:** Which task list does fork agent see — main session or isolated?
4. **Nested skill invocation:** Can fork agent invoke other skills? Would /permanent-tasks from fork create nested fork?
5. **Fork return model:** Does invoking agent get full output or summary?
6. **Fork lifecycle:** Does fork terminate after skill execution or persist?

## PT Goal Linkage

- D-9 (4 Lead-only skills → context:fork): All 4 assessed, all feasible with varying risk
- D-10 (CLAUDE.md §10 modification): Enforcement mechanism analyzed, modification path clear
- D-11 (3 new fork-context agent .md): Tool requirements mapped per agent

## Evidence Sources

| Source | Path | What It Provided |
|--------|------|------------------|
| skills-reference.md | .claude/plugins/.../references/skills-reference.md | Fork frontmatter syntax, pr-check example |
| Design doc §9 | docs/plans/2026-02-12-skill-optimization-v9-design.md | CC research findings, D-9/D-10/D-11 decisions |
| permanent-tasks SKILL.md | .claude/skills/permanent-tasks/SKILL.md | Task API usage, conversation dependency |
| delivery-pipeline SKILL.md | .claude/skills/delivery-pipeline/SKILL.md | User interaction pattern, git operations |
| rsil-global SKILL.md | .claude/skills/rsil-global/SKILL.md | Tier 3 agent spawning, read-only Task API |
| rsil-review SKILL.md | .claude/skills/rsil-review/SKILL.md | R-1 parallel agent spawning, Edit operations |
| CLAUDE.md §10 | .claude/CLAUDE.md:359-387 | Lead-only Task API enforcement mechanism |
| agent-common-protocol.md §Task API | .claude/references/agent-common-protocol.md:72-76 | Read-only Task API for teammates |
| 43 agent .md files | .claude/agents/*.md | disallowedTools patterns, no skills: usage |
| sub-agents.md | .claude/plugins/.../references/sub-agents.md | Agent configuration fields, tool inheritance |
| settings.json | .claude/settings.json | Current hook, permission, env config |
