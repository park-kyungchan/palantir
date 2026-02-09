# Claude Code CLI Features — Raw Research Data

## Sources
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/settings
- https://github.com/anthropics/claude-code/releases
- https://claudelog.com/claude-code-changelog/

## 1. Skill System (Complete Reference)

### File Format
- YAML frontmatter + Markdown content
- Entrypoint: `SKILL.md`
- Supporting files in skill directory

### ALL Frontmatter Fields
| Field | Required | Description |
|-------|----------|-------------|
| name | No | Display name, becomes /slash-command. Lowercase, hyphens, max 64 chars |
| description | Recommended | What skill does, when to use. Claude uses for auto-invocation |
| argument-hint | No | Hint during autocomplete, e.g. [issue-number] |
| disable-model-invocation | No | true = only user can invoke via /name. Default: false |
| user-invocable | No | false = hide from / menu, only Claude invokes. Default: true |
| allowed-tools | No | Tools available without asking when skill active |
| model | No | Model override when skill active |
| context | No | "fork" = run in forked subagent context |
| agent | No | Subagent type for context:fork. Default: general-purpose |
| hooks | No | Lifecycle hooks scoped to skill |

### String Substitutions
| Variable | Description |
|----------|-------------|
| $ARGUMENTS | All arguments passed to skill |
| $ARGUMENTS[N] | Specific argument by 0-based index |
| $N | Shorthand for $ARGUMENTS[N] |
| ${CLAUDE_SESSION_ID} | Current session ID |

### Dynamic Context Injection
- `!`command`` syntax runs shell commands BEFORE content sent to Claude
- Output replaces placeholder — preprocessing, not Claude execution
- Use for live data injection (git status, PR info, etc.)

### Skill Locations (priority order)
1. Enterprise (managed settings)
2. Personal (~/.claude/skills/)
3. Project (.claude/skills/)
4. Plugin (plugin/skills/)

### Forked Context
- `context: fork` runs in isolated subagent
- Skill content becomes subagent prompt
- No access to conversation history
- `agent` field selects execution environment

### Key Patterns
- Reference content: conventions, patterns, style guides (runs inline)
- Task content: step-by-step workflows (often with disable-model-invocation)
- Skills from --add-dir directories supported with hot reload
- Budget: 2% of context window for descriptions, fallback 16K chars
- Override budget: SLASH_COMMAND_TOOL_CHAR_BUDGET env var
- "ultrathink" keyword enables extended thinking in skills

## 2. Hook System (Complete Reference)

### ALL Hook Events (14 total)
| Event | When | Can Block? | Matcher |
|-------|------|------------|---------|
| SessionStart | Session begins/resumes | No | startup, resume, clear, compact |
| UserPromptSubmit | User submits prompt | Yes | (no matcher) |
| PreToolUse | Before tool call | Yes | Tool name (Bash, Edit, etc.) |
| PermissionRequest | Permission dialog shown | Yes | Tool name |
| PostToolUse | After tool succeeds | No (feedback) | Tool name |
| PostToolUseFailure | After tool fails | No (feedback) | Tool name |
| Notification | Notification sent | No | permission_prompt, idle_prompt, auth_success, elicitation_dialog |
| SubagentStart | Subagent spawned | No (inject context) | Agent type name |
| SubagentStop | Subagent finishes | Yes | Agent type name |
| Stop | Main agent finishes | Yes | (no matcher) |
| TeammateIdle | Teammate about to idle | Yes (exit 2 only) | (no matcher) |
| TaskCompleted | Task marked complete | Yes (exit 2 only) | (no matcher) |
| PreCompact | Before compaction | No | manual, auto |
| SessionEnd | Session terminates | No | clear, logout, prompt_input_exit, etc. |

### Hook Handler Types (3)
1. **command** (type: "command"): Shell command, JSON stdin, exit codes + JSON stdout
2. **prompt** (type: "prompt"): LLM single-turn evaluation, returns {ok: bool, reason: string}
3. **agent** (type: "agent"): Subagent with tools (Read, Grep, Glob), up to 50 turns

### Common Fields (all types)
| Field | Required | Description |
|-------|----------|-------------|
| type | Yes | "command", "prompt", or "agent" |
| timeout | No | Seconds. Default: 600 (command), 30 (prompt), 60 (agent) |
| statusMessage | No | Custom spinner message |
| once | No | true = run once per session (skills only) |

### Command-Specific Fields
| Field | Required | Description |
|-------|----------|-------------|
| command | Yes | Shell command to execute |
| async | No | true = background, non-blocking |

### Prompt/Agent-Specific Fields
| Field | Required | Description |
|-------|----------|-------------|
| prompt | Yes | Prompt text. $ARGUMENTS placeholder for hook input JSON |
| model | No | Model for evaluation. Defaults to fast model |

### Exit Codes
- **Exit 0**: Success, parse stdout for JSON
- **Exit 2**: Blocking error, stderr fed to Claude
- **Other**: Non-blocking error, stderr in verbose mode

### JSON Output Fields
| Field | Default | Description |
|-------|---------|-------------|
| continue | true | false = stop Claude entirely |
| stopReason | none | Message when continue=false |
| suppressOutput | false | Hide stdout from verbose |
| systemMessage | none | Warning to user |

### PreToolUse Decision Control (hookSpecificOutput)
- permissionDecision: "allow", "deny", "ask"
- permissionDecisionReason: string
- updatedInput: modify tool input
- additionalContext: string

### PermissionRequest Decision Control
- decision.behavior: "allow" or "deny"
- decision.updatedInput: modify input (allow only)
- decision.updatedPermissions: apply rules (allow only)
- decision.message: denial reason (deny only)
- decision.interrupt: stop Claude (deny only)

### Hook Locations
1. ~/.claude/settings.json (all projects)
2. .claude/settings.json (single project, shared)
3. .claude/settings.local.json (single project, local)
4. Managed policy settings (org-wide)
5. Plugin hooks/hooks.json
6. Skill/Agent frontmatter (component lifecycle)

### Environment Variables Available
- $CLAUDE_PROJECT_DIR: project root
- ${CLAUDE_PLUGIN_ROOT}: plugin root
- $CLAUDE_CODE_REMOTE: "true" in remote web environments
- $CLAUDE_ENV_FILE: file for persisting env vars (SessionStart only)

### Async Hooks
- `async: true` on command hooks only
- Run in background, non-blocking
- Cannot control decisions
- Output delivered on next turn
- Prompt/agent hooks cannot be async

### MCP Tool Matching
- Pattern: mcp__<server>__<tool>
- Regex: mcp__memory__.* for all memory server tools
- PostToolUse has updatedMCPToolOutput for MCP tools

### New in 2.1.x
- TeammateIdle hook event
- TaskCompleted hook event
- prompt-based hooks (type: "prompt")
- agent-based hooks (type: "agent")
- Hooks in skill/agent frontmatter
- once field for one-shot hooks

## 3. Agent/Subagent System (Complete Reference)

### Built-in Agents
| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| Explore | Haiku | Read-only | Fast codebase search |
| Plan | Inherit | Read-only | Plan mode research |
| general-purpose | Inherit | All | Complex multi-step |
| Bash | Inherit | Bash | Terminal commands |
| statusline-setup | Sonnet | Limited | /statusline config |
| Claude Code Guide | Haiku | Limited | Feature questions |

### Custom Agent Frontmatter
| Field | Required | Description |
|-------|----------|-------------|
| name | Yes | Unique ID, lowercase + hyphens |
| description | Yes | When Claude should delegate |
| tools | No | Allowlist. Inherits all if omitted |
| disallowedTools | No | Denylist, removed from inherited |
| model | No | sonnet, opus, haiku, inherit (default) |
| permissionMode | No | default, acceptEdits, delegate, dontAsk, bypassPermissions, plan |
| maxTurns | No | Max agentic turns |
| skills | No | Preloaded skill content |
| mcpServers | No | MCP servers for this agent |
| hooks | No | Lifecycle hooks |
| memory | No | user, project, or local |

### Task(agent_type) Tool Restriction (NEW)
- `tools: Task(worker, researcher), Read, Bash`
- Allowlist: only specified agent types can be spawned
- Only effective for agents running as main thread (--agent)
- Subagents cannot spawn other subagents

### Agent Memory Scopes (NEW)
| Scope | Location | Use Case |
|-------|----------|----------|
| user | ~/.claude/agent-memory/<name>/ | Cross-project learnings |
| project | .claude/agent-memory/<name>/ | Project-specific, shareable |
| local | .claude/agent-memory-local/<name>/ | Project-specific, private |

- MEMORY.md: first 200 lines auto-loaded into system prompt
- Read/Write/Edit tools auto-enabled when memory is set

### Agent Scope Priority
1. --agents CLI flag (session only, highest)
2. .claude/agents/ (project)
3. ~/.claude/agents/ (user)
4. Plugin agents/ (lowest)

### Permission Modes for Agents
| Mode | Behavior |
|------|----------|
| default | Standard permission checking |
| acceptEdits | Auto-accept file edits |
| dontAsk | Auto-deny prompts (allowed tools work) |
| delegate | Coordination-only (team management tools) |
| bypassPermissions | Skip all checks |
| plan | Read-only exploration |

### delegate Mode (NEW for Agent Teams)
- Restricts lead to coordination tools only
- Prevents lead from implementing directly
- Toggle with Shift+Tab
- Forces pure orchestration

## 4. Agent Teams (Complete Reference)

### Enable
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in env or settings.json

### Architecture
- Team lead: main session, creates team, coordinates
- Teammates: separate Claude Code instances
- Task list: shared across team
- Mailbox: messaging system

### Team Config Files
- Team config: ~/.claude/teams/{team-name}/config.json
- Task list: ~/.claude/tasks/{team-name}/
- Members array: name, agentId, agentType

### Communication
- **message**: DM to specific teammate (by name)
- **broadcast**: All teammates (expensive, use sparingly)
- **shutdown_request/response**: Graceful shutdown protocol
- **plan_approval_request/response**: Plan mode handshake

### Task System
- TaskCreate: subject, description, activeForm, metadata
- TaskUpdate: status, owner, blocks/blockedBy, description changes
- TaskList: summary of all tasks
- TaskGet: full task details
- States: pending → in_progress → completed (or deleted)
- Dependencies: blocks/blockedBy with auto-unblocking
- File locking prevents race conditions

### Display Modes
- in-process: all in main terminal (default)
- tmux/iTerm2: split panes
- teammateMode setting or --teammate-mode flag

### Key Features
- Shift+Up/Down: cycle teammates (in-process)
- Shift+Tab: toggle delegate mode
- Ctrl+T: toggle task list
- Ctrl+B: background running task
- Automatic idle notifications
- Plan approval workflow

### Limitations
- No session resumption for in-process teammates
- One team per session
- No nested teams
- Lead is fixed
- Permissions set at spawn (can change after)

## 5. Settings System (Complete Reference)

### Hierarchy (highest to lowest)
1. Managed settings (system-wide, cannot override)
2. CLI arguments
3. Local project (.claude/settings.local.json)
4. Project (.claude/settings.json)
5. User (~/.claude/settings.json)

### Key Settings Categories

#### Permissions
- permissions.allow: []
- permissions.deny: []
- permissions.ask: []
- permissions.defaultMode: "acceptEdits" | "plan" | "dontAsk" | "bypassPermissions"
- permissions.additionalDirectories: []
- permissions.disableBypassPermissionsMode: "disable"

#### Model & Output
- model: string (override default)
- language: string (response language)
- outputStyle: string (adjust system prompt style)
- alwaysThinkingEnabled: boolean

#### UI/UX
- showTurnDuration: boolean
- spinnerVerbs: {mode, verbs}
- spinnerTipsEnabled: boolean
- terminalProgressBarEnabled: boolean
- prefersReducedMotion: boolean

#### Sandbox
- sandbox.enabled: boolean
- sandbox.autoAllowBashIfSandboxed: boolean
- sandbox.excludedCommands: []
- sandbox.network.allowedDomains: []
- sandbox.network.allowUnixSockets: []

#### Environment
- env: {} key-value environment variables

#### MCP
- enableAllProjectMcpServers: boolean
- enabledMcpjsonServers: []
- disabledMcpjsonServers: []

#### Plugins
- enabledPlugins: {}
- extraKnownMarketplaces: {}
- strictKnownMarketplaces: [] (managed only)

#### Session & Attribution
- cleanupPeriodDays: number
- attribution.commit: string
- attribution.pr: string

#### File Management
- respectGitignore: boolean
- plansDirectory: string
- fileSuggestion: {type, command}

### Permission Rule Syntax
- `Tool` — all uses of tool
- `Tool(specifier)` — specific uses
- `Bash(npm run *)` — glob matching
- `Read(./.env)` — specific files
- `Edit(./src/**)` — directory patterns
- `WebFetch(domain:example.com)` — domain filtering
- `MCP(tools:github/*)` — MCP tool patterns
- `Task(agent-name)` — specific subagent control

## 6. MCP Integration

### Configuration
- .mcp.json at project root
- Per-server configuration
- Can reference in agent frontmatter via mcpServers field

### Agent-Level MCP
- `mcpServers` in agent frontmatter
- Reference by name (already-configured) or inline definition
- Not available in background subagents

## 7. Recent Features (v2.0 → v2.1.37)

### v2.1.0 (Major Release)
- Shift+Enter for newlines (zero setup)
- Hooks in agent/skill frontmatter
- Skills: forked context, hot reload, custom agent support, invoke with /
- Agents no longer stop when tool use denied
- Language configuration (model response language)
- Wildcard tool permissions: Bash(*-h*)
- /teleport session to claude.ai/code

### v2.1.33
- TeammateIdle and TaskCompleted hook events
- Memory frontmatter for agents (user, project, local)
- Task(agent_type) restriction syntax
- Fixed tmux agent teammate sessions
- Prompt and agent hook types from plugins

### v2.1.37 (approximate)
- Stability fixes
- Performance improvements
- Various bug fixes

## 8. Undocumented / Lesser-Known Features

### Dynamic Effort for Subagents
- Can set effort: "low" for simple subagent tasks to save tokens
- Not widely documented but effective for cost optimization

### SLASH_COMMAND_TOOL_CHAR_BUDGET
- Override skill description budget
- Useful when many skills compete for context space

### once Field in Hook Handlers
- Run a hook only once per session (skills only)
- Good for one-time setup or initialization

### CLAUDE_AUTOCOMPACT_PCT_OVERRIDE
- Override auto-compaction threshold (default ~95%)
- Set lower (e.g. 50) for earlier compaction

### CLAUDE_CODE_DISABLE_BACKGROUND_TASKS
- Disable all background task functionality

### CLAUDE_CODE_SHELL_PREFIX
- Command wrapper for logging all shell commands

### fileSuggestion Setting
- Custom @ file autocomplete via shell command
- Script receives JSON query, outputs file paths

### statusLine Setting
- Custom status line via shell command
- Shows dynamic info in the UI

### Sandbox Network Configuration
- allowedDomains with wildcards
- allowUnixSockets for specific sockets
- HTTP/SOCKS proxy port configuration

### --agents CLI Flag
- Pass agent definitions as JSON (session-only)
- No file creation needed
- Great for quick testing/automation

### Agent Stop Hook Conversion
- Stop hooks in agent frontmatter auto-convert to SubagentStop
- Scoped to component lifecycle

### Prompt Hooks for Quality Gates
- type: "prompt" uses LLM to evaluate conditions
- Cheaper/faster than agent hooks
- Good for simple yes/no decisions

### Agent Hooks for Complex Verification
- type: "agent" spawns subagent with tools
- Up to 50 turns of investigation
- Good for test verification, code review gates

### CLAUDE_ENV_FILE (SessionStart Only)
- Persist environment variables for all subsequent Bash commands
- Write export statements to file
- Capture diff of env changes
