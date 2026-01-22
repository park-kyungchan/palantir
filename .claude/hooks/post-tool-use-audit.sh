#!/bin/bash
# PostToolUse Audit Hook
# Logs completed tool execution to ODA audit trail
#
# Environment variables used:
#   TOOL_INPUT_TOOL_NAME - Name of the tool that was invoked
#   TOOL_EXIT_CODE - Exit code of the tool execution
#   TOOL_OUTPUT - Output from the tool (optional, may be truncated)
#
# Exit codes:
#   0 - Always succeeds (audit logging should not block)

set -euo pipefail

TOOL_NAME="${TOOL_INPUT_TOOL_NAME:-unknown}"
EXIT_CODE="${TOOL_EXIT_CODE:-0}"
TIMESTAMP=$(date -Iseconds)

# Ensure log directory exists
mkdir -p .agent/logs

# Determine status based on exit code
if [[ "$EXIT_CODE" == "0" ]]; then
  STATUS="success"
else
  STATUS="failed"
fi

# Log tool execution
echo "$TIMESTAMP | POST_TOOL | $TOOL_NAME | exit:$EXIT_CODE | status:$STATUS" >> .agent/logs/oda_audit.log

# Track tool execution statistics
STATS_FILE=".agent/logs/tool_stats.log"
if [[ -f "$STATS_FILE" ]]; then
  # Increment counter for this tool
  CURRENT_COUNT=$(grep -c "^$TOOL_NAME|" "$STATS_FILE" 2>/dev/null || echo "0")
  echo "$TOOL_NAME|$TIMESTAMP|$STATUS" >> "$STATS_FILE"
else
  echo "$TOOL_NAME|$TIMESTAMP|$STATUS" >> "$STATS_FILE"
fi

exit 0
