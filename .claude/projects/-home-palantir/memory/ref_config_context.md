# Configuration, Context & Session

> Verified: 2026-02-17 via claude-code-guide team investigation

---

## 1. Configuration System — 5-Layer Settings

### Precedence Order (Highest to Lowest)

| Priority | Scope | Location | Affects | Shared? |
|----------|-------|----------|---------|---------|
| 1 | **Managed** | `managed-settings.json` (system dir) | All users on machine | IT deployed |
| 2 | **CLI args** | `--model`, `--agent`, etc. | Current session only | N/A |
| 3 | **Local** | `.claude/settings.local.json` (project) | Current project, you only | No (gitignored) |
| 4 | **Project** | `.claude/settings.json` (project) | All collaborators | Yes (git) |
| 5 | **User** | `~/.claude/settings.json` | All your projects | No |

More specific scopes take precedence. If the same key has conflicting values, higher-priority scope wins.

### Environment Variables

Shell-level env vars take precedence over `env` object in settings.json. Pre-existing shell variables are not overwritten.

### Key settings.json Sections

```jsonc
{
  "model": "opus",
  "permissions": {
    "allow": ["Bash(npm run *)"],
    "deny": ["Read(./.env)", "Read(./.env.*)"],
    "ask": ["Bash(git push *)"]
  },
  "defaultMode": "default",
  "hooks": { /* ... */ },
  "env": {
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "80"
  }
}
```

### Additional Settings Keys

```jsonc
{
  "otelHeadersHelper": "...",        // OpenTelemetry header config
  "statusLine": true,                // Show status line in UI
  "fileSuggestion": true,            // Suggest files to read
  "respectGitignore": true,          // Honor .gitignore in file operations
  "outputStyle": "...",              // Output formatting style
  "disableAllHooks": false,          // Kill switch for all hooks
  "allowManagedHooksOnly": false,    // Only run managed (IT-deployed) hooks
  "enableAllProjectMcpServers": false // Auto-enable all project MCP servers
}
```

### Complete Settings Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `$schema` | string | — | JSON schema URL |
| `alwaysThinkingEnabled` | boolean | `false` | Force extended thinking for all sessions |
| `apiKeyHelper` | string | — | Shell script for auth token generation |
| `attribution` | object | — | Git commit/PR attribution customization |
| `autoUpdatesChannel` | string | `"latest"` | Release channel: `"stable"` or `"latest"` |
| `availableModels` | array | — | Restrict selectable models |
| `cleanupPeriodDays` | number | `30` | Session cleanup period |
| `companyAnnouncements` | array | — | Startup announcement strings |
| `disableAllHooks` | boolean | `false` | Kill switch for all hooks |
| `enableAllProjectMcpServers` | boolean | `false` | Auto-approve project MCP servers |
| `enabledMcpjsonServers` | array | — | MCP server allowlist |
| `disabledMcpjsonServers` | array | — | MCP server denylist |
| `enabledPlugins` | object | — | `{"name@marketplace": boolean}` |
| `fileSuggestion` | object | — | Custom `@` autocomplete script |
| `forceLoginMethod` | string | — | `"claudeai"` or `"console"` |
| `language` | string | — | Response language preference |
| `model` | string | — | Override default model |
| `outputStyle` | string | — | Output formatting style |
| `permissions` | object | — | Permission rules (allow/deny/ask) |
| `plansDirectory` | string | `~/.claude/plans` | Plan file storage |
| `prefersReducedMotion` | boolean | `false` | Reduce UI animations |
| `promptSuggestionEnabled` | boolean | `true` | Ghost-text followup suggestions |
| `respectGitignore` | boolean | `true` | Honor .gitignore in file operations |
| `sandbox` | object | — | Advanced sandboxing config |
| `showTurnDuration` | boolean | `true` | Show turn duration messages |
| `skipDangerousModePermissionPrompt` | boolean | `false` | Suppress bypass warning |
| `spinnerTipsEnabled` | boolean | `true` | Show tips in spinner |
| `spinnerVerbs` | object | — | Customize spinner verbs |
| `statusLine` | object | — | Custom status line script |
| `teammateMode` | string | `"auto"` | Agent team display: auto/in-process/tmux |
| `terminalProgressBarEnabled` | boolean | `true` | Terminal progress bar |

**Managed-only fields** (only in `managed-settings.json`):

| Key | Type | Description |
|-----|------|-------------|
| `allowManagedHooksOnly` | boolean | Block user/project/plugin hooks |
| `allowManagedPermissionRulesOnly` | boolean | Only managed permission rules |
| `allowedMcpServers` | array | MCP server allowlist |
| `deniedMcpServers` | array | MCP server denylist |
| `disableBypassPermissionsMode` | string | `"disable"` prevents bypass mode |
| `strictKnownMarketplaces` | array | Plugin marketplace allowlist |

### Functional Separation

- **settings.json**: Controls "what Claude CAN do" — permissions, model, env vars, hooks
- **CLAUDE.md**: Controls "what Claude SHOULD KNOW" — conventions, architecture, project rules

---

## 2. CLAUDE.md — Knowledge Injection Layer

### Loading Order

```
~/.claude/CLAUDE.md            ← Global (all projects)
./CLAUDE.md                    ← Project root
./CLAUDE.local.md              ← Project local (gitignored)
./src/CLAUDE.md                ← Subdirectory (on-demand when working in that dir)
```

Full chain: managed policy → user → project → local → subdirectory (on-demand).

### Critical Behavior

- Injected into system prompt on **every single API request** — permanently consumes context tokens
- Survives compaction (re-injected automatically)
- `--add-dir` requires `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`
- Max recommended: keep total under 2000 tokens for efficiency
- Progressive disclosure: keep CLAUDE.md lean, move details to reference files
- Progressive disclosure equation: CLAUDE.md (always loaded) + Skills (on-demand) + Supporting files (on-demand from skills)

### @import Syntax

CLAUDE.md files can import additional files:
- Syntax: `@path/to/file` on its own line
- Relative paths resolve relative to the containing file (not CWD)
- Absolute paths and home directory (`@~/.claude/...`) supported
- Recursive imports supported (max depth 5)
- Imports inside code spans/blocks are NOT evaluated
- First-time external imports show approval dialog (one-time per project)

### Official Best Practices

| Include in CLAUDE.md | Exclude from CLAUDE.md |
|---------------------|----------------------|
| Bash commands Claude can't guess | Anything Claude can figure out by reading code |
| Code style rules differing from defaults | Standard language conventions Claude already knows |
| Testing instructions, preferred test runners | Detailed API documentation (link instead) |
| Repository etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to project | Long explanations or tutorials |
| Developer environment quirks (required env vars) | File-by-file descriptions of the codebase |
| Common gotchas or non-obvious behaviors | Self-evident practices like "write clean code" |

Pruning test: "Would removing this cause Claude to make mistakes?" If not, cut it.

### Rules Directory (.claude/rules/)

- Supplements CLAUDE.md (does NOT replace it)
- All `.md` files auto-discovered recursively
- Loading order: User-level (`~/.claude/rules/`) then Project-level (`./.claude/rules/`)
- Project rules have higher priority than user rules
- Same priority as `.claude/CLAUDE.md`
- Frontmatter field: `paths` (array of glob patterns for conditional loading)
- Example: `paths: ["src/api/**/*.ts"]` only loads when working with those files
- Brace expansion supported: `src/**/*.{ts,tsx}`
- Symlinks supported (circular links handled gracefully)
- Rules without `paths` frontmatter are loaded globally (unconditionally)
- Survives compaction (re-injected automatically)
- **Known Bug**: User-level rules (`~/.claude/rules/`) ignore `paths` field — always load globally
- **Known Bug**: Project rules with `paths` may sometimes load globally regardless

### System Reminders

Claude Code injects `<system-reminder>` tags into user messages at runtime containing CLAUDE.md content and internal state.

---

## 3. Context Window Management

### The 200K Constraint

The 200,000-token context window (Claude Max) is shared between input and output.

```
System Prompt (internal, unpublished)
  + CLAUDE.md (all levels merged — ALWAYS present)
  + MCP tool definitions (connected servers — ALWAYS present unless deferred)
  + Skill L1 descriptions (loaded at session start)
  + Conversation history (all user + assistant turns)
  + Tool use inputs and results
  = Total context usage
```

1M beta available for API users only (tier 4+, requires `anthropic-beta: context-1m-2025-08-07` header, pricing 2x input / 1.5x output). Claude Max operates at 200K.

### Context Awareness Tags

Models (Sonnet 4.5, Haiku 4.5) receive XML budget tags in context:
- `<budget:token_budget>200000</budget:token_budget>` — total budget
- `<system_warning>Token usage: N/200000</system_warning>` — current usage

### Session Start Loading Order

1. System prompt (CC base instructions, internal)
2. CLAUDE.md chain: managed → user → project → local → subdirectory (on-demand)
2.5. `.claude/rules/*.md` — loaded when matching files referenced
3. Project memory: MEMORY.md first 200 lines auto-loaded
4. Skill L1 descriptions aggregated into Skill tool definition
5. Agent L1 descriptions loaded into Task tool definition
6. SessionStart hooks fire, additionalContext injected
7. Conversation begins

### Auto-Compaction (CC Client-Side)

- Triggers: ~95% of context window (configurable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` env var)
- PreCompact hook fires before compaction
- Conversation summarized, old tool outputs cleared
- CLAUDE.md + Skill L1 re-injected automatically
- SessionStart hook fires with `compact` matcher
- ~30-50% capacity recovered
- Compaction buffer: ~33K tokens reserved (not configurable)
- Active teammates NOT notified of parent compaction (BUG-004)
- Customization via CLAUDE.md: "When compacting, always preserve the full list of modified files"
- `/compact <instructions>` for targeted compaction (e.g., `/compact Focus on API changes`)
- `/rewind` + "Summarize from here" — condenses messages from a point forward
- Subagent transcripts survive main conversation compaction (separate files)
- Practical heuristic: after 2 failed corrections, `/clear` and start fresh

### Server-Side Compaction API (Beta)

Beta header: `compact-2026-01-12` (Opus 4.6 only). Alternative to CC client-side compaction for API users.

- Type: `compact_20260112`, trigger default 150K tokens (minimum 50K)
- `pause_after_compaction`: boolean — pauses to let client preserve messages before continuing
- Custom `instructions` parameter replaces default summarization prompt
- Usage tracking: `usage.iterations` array contains compaction + message type entries
- Token budget enforcement: count compactions x trigger threshold

### Context Editing (Beta)

Beta header: `context-management-2025-06-27`. Server-side strategies to trim context:

1. **`clear_tool_uses_20250919`**: Clears old tool results from context
   - `trigger`: token threshold (default 100K)
   - `keep`: number of recent tool uses to preserve (default 3)
   - `clear_at_least`: minimum tool uses to clear per edit
   - `exclude_tools`: array of tool names to never clear
   - `clear_tool_inputs`: also clear tool inputs (not just results)

2. **`clear_thinking_20251015`**: Clears old thinking blocks
   - `keep`: number of recent thinking turns to preserve (default 1)

Response includes `context_management.applied_edits` array with cleared counts.

### Hook Context Injection

- `hookSpecificOutput.additionalContext`: injected as system-level context
- Scope: SINGLE TURN only (not persisted)
- NOT visible to spawned subagents
- Does NOT survive compaction
- Multiple hooks same turn: concatenated in declaration order

### MCP Tool Definition Cost

Every connected MCP server adds tool definitions to context. Tool Search mitigates by loading descriptions up to 10% of context, deferring rest via MCPSearch tool.

### Skill L1 Budget

- Formula: `max(context_window × 2%, 16000)` characters (total for ALL skill descriptions) — confirmed: 2% of context window, fallback 16,000 chars
- Override: `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var
- Skills with `disable-model-invocation: true` excluded from budget
- If exceeded: skills excluded likely FIFO (no priority mechanism)

### Context Budget Environment Variables

| Variable | Default | Range/Values | Description |
|----------|---------|-------------|-------------|
| CLAUDE_CODE_MAX_OUTPUT_TOKENS | 32000 | max 64K (CC cap) | Max output tokens per response |
| CLAUDE_AUTOCOMPACT_PCT_OVERRIDE | ~95% | 1-100 | Compaction trigger threshold |
| CLAUDE_CODE_EFFORT_LEVEL | high | low/medium/high | Opus thinking depth |
| MAX_THINKING_TOKENS | 31999 | 0 to disable | Legacy thinking budget |
| CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS | (default) | number | File read token limit |
| MAX_MCP_OUTPUT_TOKENS | 25000 | number | MCP tool output limit |
| SLASH_COMMAND_TOOL_CHAR_BUDGET | dynamic | number | Skill L1 total char budget |
| ENABLE_TOOL_SEARCH | auto | auto/auto:N/true/false | MCP tool search threshold |
| CLAUDE_CODE_TASK_LIST_ID | (none) | string | Task list ID for task management |
| CLAUDE_CODE_EXIT_AFTER_STOP_DELAY | (none) | ms | Exit after stop with delay |
| CLAUDE_CODE_DISABLE_AUTO_MEMORY | (enabled) | 0/1 | Disable auto memory feature |
| ANTHROPIC_MODEL | — | string | Override model |
| CLAUDE_CODE_SUBAGENT_MODEL | — | string | Model for subagents |
| CLAUDE_CODE_SHELL_PREFIX | — | string | Command prefix for all bash |
| CLAUDE_ENV_FILE | — | string | Shell script for persistent env |
| CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR | — | boolean | Reset to project dir after each command |
| CLAUDE_CODE_DISABLE_BACKGROUND_TASKS | — | 0/1 | Disable background tasks |
| CLAUDE_CODE_ENABLE_TASKS | true | boolean | Enable task tracking |
| CLAUDE_CODE_TEAM_NAME | — | string | Team name for agent teams |
| CLAUDE_CODE_PLAN_MODE_REQUIRED | — | boolean | Auto-set on team teammates |
| MCP_TIMEOUT | — | ms | MCP server startup timeout |
| MCP_TOOL_TIMEOUT | — | ms | MCP tool execution timeout |
| CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC | — | 0/1 | Bundles: disable autoupdater+telemetry+error reporting |

### Critical Constraints

- Context window: 200K tokens (Claude Max)
- Agent `skills` preloads FULL L1+L2 (context expensive)
- Skill description > 1024 chars: excess may be lost in L1 loading
- Only ONE skill active at a time
- `$ARGUMENTS` works in skill body only, NOT in frontmatter
- Agent body: no parent conversation access
- MEMORY.md: 200-line limit, lines 201+ silently truncated

---

## 4. Session & Persistence — Filesystem Map

### Complete Filesystem Map

```
~/.claude/                              ← GLOBAL (User scope)
├── settings.json                       ← User settings (all projects)
├── settings.local.json                 ← User local settings
├── CLAUDE.md                           ← Global instructions
├── agents/                             ← Global subagent definitions
├── skills/                             ← Global skills
├── commands/                           ← Global slash commands
├── teams/{team-name}/                  ← Agent Teams data
│   ├── config.json                     ← Team metadata
│   └── inboxes/*.json                  ← Teammate inboxes
└── tasks/{team-name}/*.json            ← Task data

{project}/.claude/                      ← PROJECT scope
├── settings.json                       ← Team-shared settings (git)
├── settings.local.json                 ← Personal settings (gitignored)
├── agents/                             ← Project agents
├── skills/                             ← Project skills
└── commands/                           ← Project commands

{project}/
├── CLAUDE.md                           ← Project root instructions (git)
├── CLAUDE.local.md                     ← Project local (gitignored)
├── .mcp.json                           ← MCP server config (git)
└── src/CLAUDE.md                       ← Subdirectory instructions
```

### Session Storage

Claude Code saves conversations locally. Each message, tool use, and result stored. Enables: rewinding (`/rewind`), resuming (`--resume`), forking sessions. File snapshots taken before code changes. Sessions tied to current directory.

### Auto Memory System

Three distinct memory mechanisms:
1. **Auto memory** (Claude-written): `~/.claude/projects/<project>/memory/` — Claude auto-saves useful context
2. **CLAUDE.md** (user-written): User instructions, conventions, architecture
3. **Agent memory** (agent-scoped): `{scope}/agent-memory/{agent-name}/` — per-agent persistent knowledge

Auto memory details:
- MEMORY.md entrypoint (first 200 lines auto-loaded)
- Topic files (e.g., `debugging.md`) loaded on-demand
- Project path derived from git repo root (shared across subdirectories)
- Git worktrees get separate memory directories
- `/memory` command opens file selector
- Tell Claude: "remember that we use pnpm" to explicitly save
- **Known Bug (#24044)**: MEMORY.md injected twice per API call — once via auto-memory loader, once via claudeMd loader. Doubles token cost for MEMORY.md content.

### Configuration Backups

Timestamped backups when config files change. Keeps 5 most recent per file.
