# Model Configuration, MCP & Plugins

> Verified: 2026-02-16 via claude-code-guide, cross-referenced with code.claude.com

---

## 1. Model Selection

| Model | Strengths | Cost | Use Case |
|-------|-----------|------|----------|
| Opus 4.6 | Highest capability, deep reasoning | Highest | Complex architecture, multi-file changes |
| Sonnet 4.5 | Good balance of capability and speed | Medium | General development, most tasks |
| Haiku 4.5 | Fast, cost-efficient | Lowest | Simple tasks, hook evaluation |

### CLAUDE_CODE_EFFORT_LEVEL

- Claude Code values: `low`, `medium`, `high` (default). API also supports `max`
- At `high`: almost always thinks
- At `low`/`medium`: may skip thinking for simpler problems
- Set via: `/model` effort slider, env var, or `effortLevel` in settings.json

### Model Aliases

| Alias | Behavior |
|-------|----------|
| `default` | Account-dependent (Max/Pro = Opus 4.6, API = Sonnet 4.5) |
| `sonnet` | Latest Sonnet (currently 4.5) |
| `opus` | Latest Opus (currently 4.6) |
| `haiku` | Fast, efficient Haiku |
| `sonnet[1m]` | Sonnet with 1M context (API only) |
| `opusplan` | Opus for plan mode, Sonnet for execution (hybrid) |

### Prompt Caching

- Auto-enabled by default
- `DISABLE_PROMPT_CACHING=1` — disable all
- `DISABLE_PROMPT_CACHING_{HAIKU|SONNET|OPUS}=1` — per-model

---

## 2. Cost

### Benchmarks (Official)

- Average daily: ~$6/developer (API pay-as-you-go)
- 90% of users: below $12/day
- Team average: ~$100-200/developer/month (Sonnet 4.5)
- Check usage: `/cost` (API) or `/stats` (Max/Pro)

### Top 10 Optimization Strategies

1. **Model selection**: Sonnet for 80% of tasks, Opus for complex only, Haiku for agents
2. **Effort level**: `medium` for routine phases (fewer thinking tokens)
3. **Clear between tasks**: `/clear` to avoid stale context
4. **Reduce MCP overhead**: disable unused servers, prefer CLI tools
5. **CLAUDE.md lean**: under ~500 lines, move details to skills
6. **Delegate verbose ops**: subagents for tests/logs (summary returns)
7. **Agent Teams cost**: ~7x tokens in plan mode. Use Sonnet, keep teams small
8. **Skill L1 budget**: ≤1024 chars, `disable-model-invocation: true` for user-only
9. **Specific prompts**: "add validation to auth.ts" not "improve the codebase"
10. **Thinking tokens**: billed as output (3x input rate). Lower effort or `MAX_THINKING_TOKENS=8000`

---

## 3. MCP (Model Context Protocol)

### Configuration Scopes

| Scope | Location | Shared? |
|-------|----------|---------|
| Project | `.mcp.json` (project root) | Yes (git-tracked) |
| User/Local | `~/.claude.json` | No (cross-project) |
| Managed | OS system dir `managed-mcp.json` | Organization |

Env var expansion: `${VAR}`, `${VAR:-default}` in command, args, env, url, headers.

### Server Types

| Type | Transport | Status | Use Case |
|------|-----------|--------|----------|
| **http** | Streamable-HTTP | **Recommended** | Remote/cloud servers |
| stdio | stdin/stdout | Standard | Local CLI tools |
| sse | Server-Sent Events | **Deprecated** | Legacy (use http) |

### .mcp.json Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@package/server"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

### MCP Tool Naming

- Format: `mcp__servername__toolname` (double underscores)
- Permission wildcard: `mcp__servername__*` or `mcp__servername`
- MCP prompts as commands: `/mcp__server__promptname [args]`

### mcpServers in Agent Frontmatter

```yaml
mcpServers:
  - slack
  custom-db:
    command: "./db-server"
    args: ["--config", "config.json"]
```

Subagents inherit MCP servers unless explicitly configured.

### Tool Search

- `ENABLE_TOOL_SEARCH`: `auto` (default), `auto:N`, `true`, `false`
- Activates when MCP definitions exceed threshold
- Deferred tools via MCPSearch tool
- **Haiku does NOT support tool search**

### MCP Resources

- Type `@` in prompt to list resources
- Format: `@server:protocol://resource/path`
- `ListMcpResources` / `ReadMcpResource` tools for programmatic access

### MCP Security

- Same permission rules as built-in tools
- Background subagents: MCP tools NOT available
- `permissionMode: plan` blocks MCP tools (BUG-001)

---

## 4. Plugin System

### Overview

Plugins bundle skills, agents, hooks, MCP servers, and commands for distribution.
- Browse: `/plugin` (UI with Discover/Installed/Marketplaces/Errors tabs)
- Official marketplace: `claude-plugins-official` (auto-available)

### Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        ← Manifest (required)
├── commands/              ← Skills as Markdown
├── skills/                ← Agent Skills with SKILL.md
├── agents/                ← Custom agent definitions
├── hooks/
│   └── hooks.json         ← Plugin-scoped hooks
├── .mcp.json              ← MCP server configs
└── .lsp.json              ← LSP server configs
```

### Installation Scopes

| Scope | Effect | Shared? |
|-------|--------|---------|
| User | All your projects | No |
| Project | All collaborators | Yes |
| Local | You only, this project | No |

### Namespacing

- Plugin skills: `/plugin-name:skill-name` (namespaced)
- Standalone skills: `/skill-name` (short names)

### Plugin Lifecycle

- Loaded at Claude Code startup
- Skills/agents appear immediately after installation
- MCP servers auto-start when plugin enabled
- Changes require restart
