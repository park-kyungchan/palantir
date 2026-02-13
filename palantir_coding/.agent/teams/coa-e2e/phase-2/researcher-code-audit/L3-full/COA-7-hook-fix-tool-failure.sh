#!/bin/bash
# on-tool-failure.sh — Log tool execution failures for debugging
# Event: PostToolUseFailure
#
# Official PostToolUseFailure schema fields:
#   tool_name, error, tool_input, hook_event_name, session_id, cwd
# NOT available: agent_name (no agent context in tool failure events)

LOG_DIR="/home/palantir/.agent/teams"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Parse stdin JSON
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null)
ERROR=$(echo "$INPUT" | jq -r '.error // "no error details"' 2>/dev/null)

# Find active team directory from tool_input (if team-related tool) or most recent
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // empty' 2>/dev/null)
if [ -n "$TEAM_NAME" ]; then
  LATEST_TEAM="$LOG_DIR/$TEAM_NAME"
else
  LATEST_TEAM=$(ls -td "$LOG_DIR"/*/ 2>/dev/null | head -1)
fi
if [ -z "$LATEST_TEAM" ] || [ ! -d "$LATEST_TEAM" ]; then
  mkdir -p "$LOG_DIR"
  echo "[$TIMESTAMP] TOOL_FAILURE | tool=$TOOL_NAME | error=$ERROR" >> "$LOG_DIR/tool-failures.log"
  exit 0
fi

# Log the failure
echo "[$TIMESTAMP] TOOL_FAILURE | tool=$TOOL_NAME | error=$ERROR" >> "$LATEST_TEAM/tool-failures.log"
exit 0
