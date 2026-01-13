# Boris Cherny Workflow Implementation Guide

> **Based on:** Claude Code v2.1.6 Thread-Centric Agent Infrastructure
> **Source:** Boris Cherny's actual development workflow patterns

## Quick Start

```bash
# 1. Install mprocs
cargo install mprocs

# 2. Setup isolated workspaces
chmod +x ~/.claude/boris-workflow/setup-workspaces.sh
~/.claude/boris-workflow/setup-workspaces.sh git@github.com:your/repo.git ~/workspace

# 3. Start parallel sessions
mprocs --config ~/.claude/boris-workflow/mprocs.yaml
```

## Core Patterns Implemented

### 1. Parallel Session Management (Pattern 1-3)

Boris runs 5+ Claude Code terminals simultaneously:
- **Session 1**: Main development
- **Session 2**: Feature branches
- **Session 3**: Bug fixes
- **Session 4**: Code review
- **Session 5**: Experiments

Each session uses a separate git worktree for complete isolation.

### 2. Keyboard Shortcuts (Pattern 4-5)

| Shortcut | Action | Mode |
|----------|--------|------|
| `Shift+Tab×2` | Enter Plan Mode | Planning |
| `Shift+Tab` | Toggle Auto-accept | Execution |
| `Esc+Esc` | Rewind changes | Recovery |
| `1-5` (in mprocs) | Switch session | Navigation |

### 3. Core Commands (Pattern 6-7)

**Most Used: /commit-push-pr**
```bash
# Already configured in: .claude/commands/commit-push-pr.md
# Usage: Type "/commit-push-pr" in Claude Code
```

### 4. Auto-Formatting (Pattern 10)

PostToolUse hooks automatically format code after edits:
- Python: `black`
- JS/TS: `prettier`

Enable in `.claude/hooks/.format-config.json`:
```json
{
  "auto_format_enabled": true,
  "log_formatting_operations": true
}
```

### 5. Session Health Monitoring (Pattern 12)

Automatic loop detection and dead-end warnings:
- Detects repetitive tool patterns
- Warns before sessions go off-track
- Logs to `.agent/tmp/session_health.jsonl`

### 6. System Notifications (Pattern 11)

Desktop notifications when parallel sessions complete:
- Linux: `notify-send`
- macOS: `osascript`
- Windows: PowerShell toast

## Directory Structure

```
~/.claude/boris-workflow/
├── mprocs.yaml              # Multi-session orchestrator config
├── setup-workspaces.sh      # Workspace initialization script
└── README.md                # This guide

~/workspace/                  # Isolated workspaces
├── repo-main/               # Main development
├── repo-feature/            # Feature branches
├── repo-bugfix/             # Hotfixes
├── repo-review/             # Code review
└── repo-sandbox/            # Experiments
```

## Best Practices (from Boris)

1. **"No long-running prompts"** - Keep prompts under 200 words
2. **"Slash commands are king"** - Use /commands for repetitive workflows
3. **"Plan mode for complex tasks"** - Always plan before implementing
4. **"Kill stuck sessions early"** - Don't try to fix confused context
5. **"Sandbox mode always"** - Never use `--dangerously-skip-permissions`

## Troubleshooting

### Sessions not starting?
```bash
# Check mprocs installation
which mprocs

# Verify worktrees exist
ls -la ~/workspace/
```

### No desktop notifications?
```bash
# Linux: Install notify-send
sudo apt install libnotify-bin

# Test manually
notify-send "Test" "Hello from Boris Workflow"
```

### Auto-format not working?
```bash
# Check formatters are installed
which black prettier

# Enable in config
cat ~/.claude/hooks/.format-config.json
# Should show: "auto_format_enabled": true
```

## References

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [mprocs GitHub](https://github.com/pvolok/mprocs)
- [Git Worktrees](https://git-scm.com/docs/git-worktree)
