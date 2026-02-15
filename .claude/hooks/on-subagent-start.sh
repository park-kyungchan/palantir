#!/usr/bin/env bash
# Hook: SubagentStart — Logging + PT context injection

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "no-team"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/tmp/claude-hooks"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# Context injection via additionalContext — PT-based
if [ "$TEAM_NAME" != "no-team" ] && [ -n "$TEAM_NAME" ]; then
  jq -n --arg team "$TEAM_NAME" '{
    "hookSpecificOutput": {
      "hookEventName": "SubagentStart",
      "additionalContext": ("Active team: " + $team + ". Context is managed via PERMANENT Task. Use TaskGet on task with subject containing [PERMANENT] for full project context.")
    }
  }'
  exit 0
fi

exit 0
