# Hooks System

## Hook Events We Use

- **PreToolUse**: Validate/block tool calls before execution (e.g., anti-rm-rf, anti-push-main)
- **PostToolUse**: Run checks after tool execution (e.g., on-file-change formatting)
- **Notification**: Triggered on agent notifications
- **Stop**: Final verification when session ends
- **SubagentStop**: When a spawned subagent completes

## Configuration

- Hook scripts: `.claude/hooks/`
- Permissions allow-list: `permissions.allow` in `~/.claude/settings.json`
- Never use `--dangerously-skip-permissions` flag

## Active Guards

- `anti-rm-rf.sh` — blocks destructive rm commands
- `anti-push-main.sh` — blocks force-push to main
- `block-web-fallback.sh` — blocks WebSearch/WebFetch MCP fallback
- `on-mcp-failure.sh` — pauses on MCP server failure
- Session ID guard required in command hooks (BUG-007: global hooks fire in ALL contexts)
