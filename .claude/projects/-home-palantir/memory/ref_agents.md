# Agent System — Fields, Spawning & Subagents

> Verified: 2026-02-17 (initial) · 2026-02-19 (Task tool spawn + official fields re-verified via claude-code-guide)

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

> Source: official Anthropic docs (https://docs.anthropic.com/en/docs/claude-code/sub-agents), re-verified 2026-02-19.

**Native fields (officially documented):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | **yes** | — | Agent identifier. Matched by `subagent_type` in Task tool call. Use lowercase + hyphens. |
| `description` | string | **yes** | — | Routing intelligence — when to delegate to this agent. Auto-loaded in Task tool definition (L1 profile). |
| `tools` | list | no | all | Tool allowlist. If specified, agent gets ONLY these tools. If omitted, inherits ALL tools from parent. |
| `disallowedTools` | list | no | none | Tool denylist. Removed from inherited or specified list. If both `tools` + `disallowedTools` specified, `tools` wins. |
| `model` | enum | no | inherit | Values: `sonnet`, `opus`, `haiku`, `inherit`. `inherit` = same model as parent session. |
| `permissionMode` | enum | no | default | See table below. NOTE: `delegate` mode is AT-only (deprecated). Always use `default`. |
| `maxTurns` | number | no | unlimited | Max agentic loop iterations before agent stops. |
| `skills` | list | no | none | FULL L1+L2 content injected at startup for listed skills. Subagents do NOT inherit project skills automatically — must list explicitly if needed. |
| `mcpServers` | object | no | none | MCP servers for this agent. Each entry: server name (referencing pre-configured) or inline definition. |
| `hooks` | object | no | none | Agent-scoped lifecycle hooks. Augments (does not override) global hooks. |
| `memory` | enum | no | (omit) | Values: `user`, `project`, `local`. Omit field entirely to disable memory. |
| `color` | string | no | none | **Not in official frontmatter spec table. Observed in official examples only.** UI color hint. Functionally supported but treat as unofficial. |

### Tools Field — Advanced Syntax

- Simple list: `tools: Read, Glob, Grep, Bash`
- `Task(agent_type)` restricts which subagents can be spawned: `Task(worker, researcher)`
- `Task` without parentheses: allow spawning any subagent type
- Omitting `Task` entirely: agent cannot spawn subagents

**VERIFIED 2026-02-19 (subagent spawn test)**:
- A subagent that has `Task` in its `tools` CAN call `Task({subagent_type: "analyst"})` to spawn a custom `.claude/agents/analyst.md` as a nested subagent.
- The spawned agent loads its `.md` frontmatter correctly — tools, model, body all applied as defined.
- Built-in `general-purpose` has all tools including `Task` → can act as mid-tier orchestrator spawning custom agents.
- **Spawn capability matrix (verified)**:

| Agent | Has Task tool | Can spawn subagents |
|-------|--------------|---------------------|
| `general-purpose` (built-in) | ✅ (all tools) | ✅ |
| `analyst` (custom) | ❌ (explicit CANNOT) | ❌ |
| `implementer` (custom) | ❌ (explicit CANNOT) | ❌ |
| `researcher` (custom) | ❌ (explicit CANNOT) | ❌ |
| `infra-implementer` (custom) | ❌ (explicit CANNOT) | ❌ |

To enable a custom agent to spawn subagents: add `Task` or `Task(allowed_type)` to its `tools` field.
- MCP tools: `mcp__servername__toolname`
- When `memory` is enabled: Read, Write, Edit are auto-added to tools regardless of tools field
- **IMPORTANT**: When `memory` is enabled, Read, Write, Edit are auto-added to tools regardless of explicit `tools` field. This means agent tool isolation is partially broken for memory-enabled agents — they always have file manipulation capability.

### permissionMode Values

| Value | Behavior |
|-------|----------|
| default | Normal permission flow (inherits project settings) — **use this** |
| acceptEdits | Auto-accept file edits, still ask for Bash |
| dontAsk | Auto-deny permission prompts (explicitly allowed tools still work) |
| delegate | Coordination-only mode — Agent Teams only, deprecated in v14 |
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

## 4. Subagent Properties (v14)

In v14 single-session architecture, all spawned agents are subagents. Agent Teams (Teammates) are removed.

| Property | Value |
|----------|-------|
| **Context** | Independent (isolated from Lead conversation) |
| **Lifetime** | Terminates when task completes |
| **Communication** | Writes output files; Lead reads micro-signals |
| **Concurrency** | Up to 7 simultaneous (`run_in_background:true`) |
| **Result delivery** | Up to 30,000 chars injected; excess written to disk with file path reference |
| **Context inheritance** | No parent conversation; receives CLAUDE.md + task prompt |
| **Cost** | ~200K tokens per subagent solo; 3 subagents ≈ 440K total |
| **Spawn params** | `run_in_background:true`, `context:fork`, `model:sonnet` (always) |

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

## 5. Our Usage Pattern (v14 — 2026-02-20)

> 7 agents total: `analyst`, `researcher`, `coordinator`, `implementer`, `infra-implementer`, `delivery-agent`, `pt-manager`.
> All run as subagents (`run_in_background:true`, `context:fork`, `model:sonnet`).
>
> **Design principles:**
> - All agents are subagents — no Teammate/AT distinction
> - `skills` field: only for agents that need explicit skill injection (pt-manager, delivery-agent)
> - Coordinator: `Task(analyst, researcher)` for Sub-Orchestrator pattern
> - Researcher: MCP-only enforcement via dual hooks (WebSearch/WebFetch blocked)
> - Body minimized: Core Rules only; Completion Protocol in CLAUDE.md

| Field | Agents using it | Notes |
|-------|----------------|-------|
| `name` + `description` + `tools` + `maxTurns` + `color` | All 7 | Base fields present in every agent |
| `skills` | **2/7** (pt-manager, delivery-agent) | Subagents need explicit skill injection |
| `memory: project` | 5 (analyst, researcher, coordinator, implementer, infra-implementer) | Auto-adds Read/Write/Edit to tools |
| `model: haiku` | 2 (pt-manager, delivery-agent) | Others inherit (sonnet from Lead) |
| `hooks` | **4/7** | implementer + infra-impl: PostToolUse/Failure (file-change). researcher: PreToolUse (WebSearch block) + PostToolUseFailure (MCP stop). |
| `Task` in tools | **1/7** (coordinator) | `Task(analyst, researcher)` — Sub-Orchestrator pattern. |
| `permissionMode` | 0 | Not used; always spawn with `mode: "default"` |
| `mcpServers` | 0 | Not used; MCP configured at project level in `.claude.json` |
| `disallowedTools` | 0 | Not used; explicit `tools` allowlist preferred |

### Agent Taxonomy (v14)

| Agent | Role | Task tool | skills | hooks |
|-------|------|-----------|--------|-------|
| `analyst` | Dimension analysis worker | ❌ | ❌ | ❌ |
| `researcher` | MCP-powered research worker | ❌ | ❌ | ✅ MCP enforce |
| `coordinator` | Sub-Orchestrator / synthesis | ✅ `Task(analyst, researcher)` | ❌ | ❌ |
| `implementer` | Source code implementation | ❌ | ❌ | ✅ file-change |
| `infra-implementer` | .claude/ file implementation | ❌ | ❌ | ✅ file-change |
| `pt-manager` | Task lifecycle (fork) | Task API (create/update) | ✅ | ❌ |
| `delivery-agent` | Terminal delivery (fork) | Task API (update only) | ✅ | ❌ |

### Researcher MCP Enforcement (v2)

| Hook | Event | Matcher | Action |
|------|-------|---------|--------|
| `block-web-fallback.sh` | PreToolUse | WebSearch\|WebFetch | exit 2 → BLOCK tool call, stderr feedback |
| `on-mcp-failure.sh` | PostToolUseFailure | mcp__* | additionalContext → STOP directive (tavily/context7 = critical, sequential-thinking = non-critical) |

**Key behavioral notes:**
- `Stop` hooks in agent frontmatter auto-convert to `SubagentStop` events (confirmed)
- Agent-scoped hooks AUGMENT global hooks (both fire for same event). Cleaned up when agent finishes.
- `memory` enabled → Read, Write, Edit auto-added to tools (bypasses explicit `tools` field — partial isolation break)
- **Coordinator Sub-Orchestrator**: spawns analyst/researcher as nested subagents. Subagent result ≤30K chars injected into coordinator's context.

---

## 6. Agent Communication Protocol (v14)

All agents use the Two-Channel Handoff Protocol defined in CLAUDE.md [D17]. Agent .md body contains role-specific Core Rules only.

### CC Native Coordination (v14)

Only 2 coordination mechanisms used:
1. **Task JSON files** (Task API: TaskCreate/TaskUpdate/TaskGet) — state: pending → in_progress → completed
2. **Work Directory files** — subagents write output; Lead reads micro-signals (Ch3) then Ch2 files on ENFORCE

No inbox. No SendMessage. No P2P messaging. Everything is file I/O.

### Completion Protocol

| Aspect | All Subagents (v14) |
|--------|---------------------|
| Result delivery | Write to Work Directory path specified in DPS |
| Large outputs | Full output in disk file; micro-signal contains file path |
| Failure reporting | FAIL micro-signal + error details in output file |
| Completion signal | Lead receives auto-notification (run_in_background) |
