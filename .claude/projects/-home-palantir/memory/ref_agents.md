# Agent System — Fields, Spawning & Subagents

> Verified: 2026-02-16 via claude-code-guide, cross-referenced with code.claude.com

---

## 1. Agent Definition

```
~/.claude/agents/       ← Global agents
.claude/agents/         ← Project agents
```

Each agent is a Markdown file with YAML frontmatter:

```yaml
---
name: code-reviewer
description: Reviews code for quality, security, and best practices
model: opus
allowed-tools:
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

### permissionMode Values

| Value | Behavior |
|-------|----------|
| default | Normal permission flow (inherits project settings) |
| acceptEdits | Auto-accept file edits, still ask for Bash |
| dontAsk | Auto-deny permission prompts (explicitly allowed tools still work) |
| delegate | Coordination-only mode (agent teams only) |
| bypassPermissions | Skip all permission checks (dangerous) |
| plan | Read-only + plan-only. WARNING: blocks MCP tools (BUG-001) |

### Agent Memory Configuration

| Value | Location | Scope | Auto-Load |
|-------|----------|-------|-----------|
| user | `~/.claude/agent-memory/{agent-name}/` | All projects | First 200 lines MEMORY.md |
| project | `.claude/agent-memory/{agent-name}/` | Current project | First 200 lines |
| local | `.claude/agent-memory-local/{agent-name}/` | Current project (gitignored) | First 200 lines |

Lines 201+ silently truncated.

---

## 3. Agent Spawning Flow

1. Lead calls Task tool with `subagent_type` parameter
2. Agent lookup: project (.claude/agents/) > user (~/.claude/agents/) > plugin > built-in
3. Agent receives: agent .md body (system prompt) + CLAUDE.md chain + task prompt
4. Agent does NOT receive: parent conversation history, parent skill context
5. If `skills` field: FULL skill content (L1+L2) preloaded at startup
6. If `memory` field: MEMORY.md first 200 lines auto-loaded
7. SubagentStart hook fires after spawn
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

| Type | Purpose | Tool Access |
|------|---------|-------------|
| **Explore** | Read-only codebase navigation | Read, Glob, Grep only |
| **Plan** | Structured planning | Read, Glob, Grep only |
| **General-purpose** | Full multi-step tasks | All tools |

### Subagent Output Handling

Background subagent outputs truncated to 30,000 characters. Full output written to disk with file path reference.

---

## 5. Our Usage Pattern

- All 6 agents: name, description, tools (explicit allowlist), maxTurns
- 4 agents: memory: project (analyst, researcher, implementer, infra-implementer)
- 2 agents: model: haiku (pt-manager, delivery-agent)
- 2 agents: hooks (implementer, infra-implementer: PostToolUse + PostToolUseFailure)
- 0 agents: permissionMode, skills, mcpServers, disallowedTools
