#!/bin/bash
# on-tool-failure.sh — Log tool execution failures for debugging
# Event: PostToolUseFailure

LOG_DIR="/home/palantir/.agent/teams"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Parse stdin JSON
INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  mkdir -p "$LOG_DIR" 2>/dev/null
  echo "[$TIMESTAMP] TOOL_FAILURE | raw_input_length=${#INPUT}" >> "$LOG_DIR/tool-failures.log" 2>/dev/null
  exit 0
fi

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"' 2>/dev/null)
ERROR=$(echo "$INPUT" | jq -r '.error // "no error details"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // "unknown"' 2>/dev/null)

# Find active team directory from input or most recent
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // empty' 2>/dev/null)
if [ -n "$TEAM_NAME" ]; then
  LATEST_TEAM="$LOG_DIR/$TEAM_NAME"
else
  LATEST_TEAM=$(ls -td "$LOG_DIR"/*/ 2>/dev/null | head -1)
fi
if [ -z "$LATEST_TEAM" ] || [ ! -d "$LATEST_TEAM" ]; then
  exit 0
fi

# Log the failure
echo "[$TIMESTAMP] TOOL_FAILURE | agent=$AGENT_NAME | tool=$TOOL_NAME | error=$ERROR" >> "$LATEST_TEAM/tool-failures.log"
exit 0
