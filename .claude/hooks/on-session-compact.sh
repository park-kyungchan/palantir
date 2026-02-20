#!/usr/bin/env bash
# Hook: SessionStart(compact) — Task API-based auto-compact recovery

set -euo pipefail

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/tmp/claude-hooks"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — recovery active" \
  >> "$LOG_DIR/compact-events.log"

# Recovery message — Task API based
MSG="Your session was compacted. As Lead: 1) TaskList to see all tasks (including PERMANENT Task) 2) TaskGet on [PERMANENT] task for project context and pipeline history 3) Resume pipeline from last completed phase using PT metadata."

# Output JSON
if command -v jq &>/dev/null; then
  jq -n --arg msg "$MSG" '{
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": $msg
    }
  }'
else
  ESCAPED_MSG=$(printf '%s' "$MSG" | sed 's/\\/\\\\/g; s/"/\\"/g')
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$ESCAPED_MSG\"}}"
fi

exit 0
