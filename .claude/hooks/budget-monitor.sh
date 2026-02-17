#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook — monitors tool invocation counts per session (RSIL-057)
# Input: JSON on stdin with tool_name, tool_input, session_id
# Output: Logs to /tmp/budget-monitor.log
# Exit: Always 0 (monitoring only, never blocks)

INPUT=$(cat)

# Extract fields
if command -v jq &>/dev/null; then
  TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"')
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
else
  TOOL_NAME=$(echo "$INPUT" | grep -oP '"tool_name"\s*:\s*"\K[^"]+' || echo "unknown")
  SESSION_ID=$(echo "$INPUT" | grep -oP '"session_id"\s*:\s*"\K[^"]+' || echo "unknown")
fi

LOGFILE="/tmp/budget-monitor.log"

# Append invocation record (atomic for lines < PIPE_BUF)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] session=${SESSION_ID} tool=${TOOL_NAME}" >> "$LOGFILE" 2>/dev/null || true

exit 0
