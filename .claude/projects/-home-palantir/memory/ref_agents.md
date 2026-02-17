# Agent System — Fields, Spawning & Subagents

> Verified: 2026-02-17 via claude-code-guide team investigation

---

## 1. Agent Definition

**Claude Agent SDK**: `@anthropic-ai/claude-agent-sdk` (TS), `claude-agent-sdk` (Python)

### Agent Scope Priority (highest to lowest)

1. `--agents` CLI flag (session only)
2. `.claude/agents/` (project)
3. `~/.claude/agents/` (user)
4. Plugin's `agents/` (lowest)

Each agent is a Markdown file with YAML frontmatter:

```yaml
---
name: code-reviewer
description: Reviews code for quality, security, and best practices
model: opus
tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff *)
disallowedTools:
  - Write
  - Edit
---
You are a code reviewer. Never modify files, only analyze and report.
```

---

## 2. Frontmatter Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | yes | none | Agent identifier for subagent_type matching |
| description | string | yes | none | L1 profile. Loaded in Task tool definition |
| tools | list | no | all | Tool allowlist (explicit = ONLY these) |
| disallowedTools | list | no | none | Tool denylist. If both specified, tools wins |
| model | enum | no | inherit | Values: sonnet, opus, haiku |
| permissionMode | enum | no | default | See table below |
| maxTurns | number | no | unlimited | One turn = one agentic loop iteration |
| skills | list | no | none | FULL L1+L2 content preloaded at startup |
| mcpServers | list | no | none | MCP server access config |
| hooks | object | no | none | Agent-scoped hooks |
| memory | enum | no | none | Values: user, project, local |
| color | string | no | none | UI color coding |

### Tools Field — Advanced Syntax

- Simple list: `tools: Read, Glob, Grep, Bash`
- `Task(agent_type)` restricts which subagents can be spawned: `Task(worker, researcher)`
- `Task` without parentheses: allow spawning any subagent type
- Omitting `Task` entirely: agent cannot spawn subagents
- MCP tools: `mcp__servername__toolname`
- When `memory` is enabled: Read, Write, Edit are auto-added to tools regardless of tools field
- **IMPORTANT**: When `memory` is enabled, Read, Write, Edit are auto-added to tools regardless of explicit `tools` field. This means agent tool isolation is partially broken for memory-enabled agents — they always have file manipulation capability.

### permissionMode Values

| Value | Behavior |
|-------|----------|
| default | Normal permission flow (inherits project settings) |
| acceptEdits | Auto-accept file edits, still ask for Bash |
| dontAsk | Auto-deny permission prompts (explicitly allowed tools still work) |
| delegate | Coordination-only mode (agent teams only) |
| bypassPermissions | Skip all permission checks (dangerous) |
| plan | Read-only + plan-only. WARNING: blocks MCP tools (BUG-001) |

**Inheritance rule**: If parent uses `bypassPermissions`, it takes precedence and cannot be overridden by child agent.

### Agent Memory Configuration

| Value | Location | Scope | Auto-Load |
|-------|----------|-------|-----------|
| user | `~/.claude/agent-memory/{agent-name}/` | All projects | First 200 lines MEMORY.md |
| project | `.claude/agent-memory/{agent-name}/` | Current project | First 200 lines |
| local | `.claude/agent-memory-local/{agent-name}/` | Current project (gitignored) | First 200 lines |

Lines 201+ silently truncated.

**Known Bug (#24044)**: MEMORY.md is injected **twice** per API call — once via auto-memory loader, once via claudeMd/project-instructions loader. Doubles MEMORY.md token cost. Mitigation: keep MEMORY.md as lean as possible (well under 200 lines).

---

## 3. Agent Spawning Flow

1. Lead calls Task tool with `subagent_type` parameter
2. Agent lookup: CLI (--agents flag) > project (.claude/agents/) > user (~/.claude/agents/) > plugin > built-in
3. Agent receives: agent .md body (system prompt) + CLAUDE.md chain + task prompt
4. Agent does NOT receive: parent conversation history, parent skill context
5. If `skills` field: FULL skill content (L1+L2) preloaded at startup
   - Skills in agent: agent controls system prompt, skill content loaded as reference
   - This is INVERSE of context:fork in skills (skill controls task, agent provides execution env)
   - Subagents do NOT inherit skills from parent — must be listed explicitly
6. If `memory` field: MEMORY.md first 200 lines auto-loaded
7. SubagentStart hook fires after spawn
- Agent-scoped hooks **augment** (not override) global hooks. Both fire for the same event.
- Agent hooks are scoped to the component's lifecycle — cleaned up when agent finishes.
- `Stop` hooks in agent frontmatter auto-convert to `SubagentStop` events (confirmed).
8. Agent runs independently until maxTurns or task completion

---

## 4. Subagent vs Agent Teams Teammate

| Property | Subagent | Agent Teams Teammate |
|----------|----------|---------------------|
| **Context** | Independent (separate from main) | Independent (own window) |
| **Lifetime** | Terminates when task completes | Persists; can go idle; explicit shutdown |
| **Communication** | Returns summary to parent | Inbox messaging + shared task list |
| **Concurrency** | Up to 7 simultaneous | No hard limit (cost is practical limit) |
| **Result delivery** | Up to 30,000 chars injected; excess to disk | SendMessage text; no injection |
| **Context inheritance** | No parent conversation | No lead conversation |
| **Shared context** | CLAUDE.md, MCP servers, skills | CLAUDE.md, MCP servers, skills |
| **Cost** | Lower (results summarized) | Higher (full Claude instance each) |
| **Best for** | Focused tasks, result-only | Complex work needing discussion |

### Built-in Subagent Types

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **Explore** | Haiku | Read-only | File discovery |
| **Plan** | Inherit | Read-only | Codebase research |
| **General-purpose** | Inherit | All | Complex tasks |
| **Bash** | Inherit | Bash | Terminal commands |

### Subagent Output Handling

Background subagent outputs truncated to 30,000 characters. Full output written to disk with file path reference.

### Subagent Transcript Persistence

- Transcripts stored at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`
- Survive main conversation compaction
- Persist within session (can resume after Claude Code restart)
- Cleaned up based on `cleanupPeriodDays` setting (default: 30 days)
- Resume: "Continue that code review" — Claude resumes with full conversation history
- Auto-compaction events: `compact_boundary` with `preTokens` count
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` — override auto-compaction threshold percentage

---

## 5. Our Usage Pattern

- All 6 agents: name, description, tools (explicit allowlist), maxTurns
- 4 agents: memory: project (analyst, researcher, implementer, infra-implementer)
  - When memory enabled: Read, Write, Edit auto-added to tools (regardless of explicit tools field)
- 2 agents: model: haiku (pt-manager, delivery-agent)
- 2 agents: hooks (implementer, infra-implementer: PostToolUse + PostToolUseFailure)
- Note: `Stop` hooks in agent frontmatter auto-convert to `SubagentStop` events (confirmed)
- Note: Agent-scoped hooks AUGMENT global hooks (both fire). Hooks cleaned up when agent finishes.
- 0 agents: permissionMode, skills, mcpServers, disallowedTools

---

## 6. Agent Communication Protocol (Custom Convention)

Our agents use a dual-mode completion protocol embedded in each agent body. This is NOT CC native — it's our custom convention on top of CC's file-based coordination.

### CC Native Ground Truth

Only 2 coordination channels exist:
1. **Task JSON files** (`~/.claude/tasks/{team-name}/N.json`) — state: pending → in_progress → completed
2. **Inbox JSON** (`~/.claude/teams/{team-name}/inboxes/{agent-id}.json`) — SendMessage writes entries

No shared memory. No sockets/pipes/IPC. Everything is file I/O. "Automatic message delivery" = inbox check on each API turn, not OS push.

### Our Dual-Mode Protocol

| Aspect | Local Mode (P0-P1) | Team Mode (P2+) |
|--------|-------------------|-----------------|
| Detection | SendMessage NOT available | SendMessage available |
| Result delivery | Write to disk path from DPS | TaskUpdate + SendMessage to Lead |
| Large outputs | Full output in disk file | Disk file + path reference in SendMessage |
| Failure reporting | Error in disk output | FAIL status via SendMessage |
| Completion signal | Parent reads via TaskOutput | Idle notification auto-sent to Lead |

### Agent Categories

- **Dual-mode** (4 agents): analyst, researcher, implementer, infra-implementer — can run in both Local and Team mode
- **Team-only** (2 agents): delivery-agent, pt-manager — always run in P2+ Team mode
