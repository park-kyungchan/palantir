#!/usr/bin/env bash
# Hook: SubagentStart — Logging + PT context injection

set -euo pipefail

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/tmp/claude-hooks"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE" >> "$LOG_DIR/subagent-lifecycle.log"

# Pipeline state: record agent spawn event
STATE_FILE="/tmp/claude-pipeline-state.json"
if [[ ! -f "$STATE_FILE" ]]; then
  echo '{"session_id":"'$SESSION_ID'","started_at":"'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'","agents_spawned":[],"tasks_completed":[],"src_impacts":[]}' > "$STATE_FILE"
fi
# Append agent spawn event using jq
if command -v jq &>/dev/null && [[ -f "$STATE_FILE" ]]; then
  local_tmp=$(mktemp)
  jq --arg type "$AGENT_TYPE" --arg name "$AGENT_NAME" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    '.agents_spawned += [{"type": $type, "name": $name, "spawned_at": $at}]' "$STATE_FILE" > "$local_tmp" && mv "$local_tmp" "$STATE_FILE"
fi

exit 0
