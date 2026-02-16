# Runtime, Tools & Security

> Verified: 2026-02-16 via claude-code-guide, cross-referenced with code.claude.com

---

## 1. Runtime Core — The Agentic Loop

Claude Code's central execution model is an iterative tool-calling loop:

```
User Prompt → Claude Reasoning → Tool Selection → Tool Execution → Result Observation → Reasoning → ... → Stop
```

When launched in a directory, Claude Code gains access to:
- **Project files**: Working directory and subdirectories, plus elsewhere with permission
- **Terminal**: Any command the user could run — build tools, git, package managers, scripts
- **Git state**: Current branch, uncommitted changes, recent commit history
- **CLAUDE.md**: All levels merged into system prompt

Hooks can intercept every stage. The loop is autonomous and multi-turn — Claude decides tools, observes results, and continues until task completion (or Stop hook overrides).

### Session Independence

Each session starts with a fresh context window. No conversation history from previous sessions. Cross-session persistence only through:
- CLAUDE.md files (persistent instructions)
- Auto memory (built-in memory feature)
- Filesystem artifacts (files written to disk)

---

## 2. Built-in Tools

| Tool | Function | Permission Pattern Example |
|------|----------|---------------------------|
| **Bash** | Execute shell commands | `Bash(npm run *)`, `Bash(git commit *)` |
| **Read** | Read file contents | gitignore-style path patterns |
| **Write** | Create new files | gitignore-style path patterns |
| **Edit** | Partial file modification | Shares Read/Edit rules |
| **MultiEdit** | Multiple edits in one operation | Shares Read/Edit rules |
| **NotebookEdit** | Edit Jupyter notebook cells | Shares Read/Edit rules |
| **Glob** | File path search/discovery | Read rules apply |
| **Grep** | Text content search | Read rules apply |
| **WebFetch** | Retrieve web page content | `WebFetch(domain:github.com)` |
| **WebSearch** | Search the web | — |
| **Task** | Spawn subagents | — |
| **Skill** | Invoke skills | — |
| **AskUserQuestion** | Prompt user for input | — |
| **ExitPlanMode** | Signal plan completion | — |
| **TaskCreate/Update/Get/List** | Task management (todo) | — |
| **TeammateTool** | Agent Teams coordination | spawn, sendMessage, broadcast, etc. |
| **ListMcpResources/ReadMcpResource** | MCP resource access | — |
| **mcp__*__*** | MCP server tools | `mcp__servername__actionname` |

---

## 3. Permission System

### Evaluation Order

```
deny → ask → allow (first matching rule wins)
```

Deny rules have highest precedence. Cannot be overridden by lower-priority allow/ask rules.

### Permission Pattern Syntax — 4 Path Types

| Pattern | Meaning | Example |
|---------|---------|---------|
| `//path` | **Absolute** filesystem path | `Read(//Users/alice/secrets/**)` |
| `~/path` | **Home** directory relative | `Read(~/Documents/*.pdf)` |
| `/path` | Relative to **settings file** location | `Edit(/src/**/*.ts)` |
| `path` or `./path` | Relative to **current directory** | `Read(*.env)` |

### Bash Pattern Wildcards

- `Bash(npm run *)` — matches `npm run test`, `npm run build`
- `Bash(ls *)` — word boundary: matches `ls -la` but NOT `lsof`
- `Bash(ls*)` — no boundary: matches both `ls -la` and `lsof`
- Shell operator awareness: `Bash(safe-cmd *)` will NOT match `safe-cmd && malicious-cmd`
- `*` matches single level; `**` matches recursively (Read/Edit paths)

### Permission Scopes (Settings Precedence)

| Priority | Scope | Location | Shared? |
|----------|-------|----------|---------|
| 1 (highest) | Managed | OS system path (IT deployed) | Organization |
| 2 | CLI args | `--model`, `--agent`, etc. | Session only |
| 3 | Local | `.claude/settings.local.json` | No (gitignored) |
| 4 | Project | `.claude/settings.json` | Yes (git) |
| 5 (lowest) | User | `~/.claude/settings.json` | No |

### Managed Settings Paths

- macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
- Linux/WSL: `/etc/claude-code/managed-settings.json`

---

## 4. Sandboxing — Defense-in-Depth

### 4 Security Layers

| Layer | Mechanism | Enforcement |
|-------|-----------|-------------|
| 1. Permission rules | deny → ask → allow | Claude Code logic (pre-execution) |
| 2. Filesystem isolation | Read/write only in cwd + subdirs | OS-level sandbox |
| 3. Network isolation | Proxy-based domain restriction | All scripts/subprocesses inherit |
| 4. OS enforcement | Seatbelt (macOS) / bubblewrap (Linux/WSL2) | Kernel-level |

### Key Constraints

- Cannot modify files outside cwd without explicit permission
- Cannot access non-approved network domains via Bash
- Child processes inherit ALL sandbox restrictions
- WSL1: sandboxing NOT supported (WSL2 required)
- Hooks run with full user permissions (NO sandbox for hooks)

### Defense-in-Depth Principle

Permission rules and sandboxing are independent layers:
- Permission rules stop Claude from **attempting** to access restricted resources
- Sandbox prevents Bash commands from **reaching** resources even if prompt injection bypasses Claude's decision-making
- Effective protection requires BOTH filesystem and network isolation
