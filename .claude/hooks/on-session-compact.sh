#!/bin/bash
# Hook: SessionStart(compact) — Task API-based auto-compact recovery

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — recovery active" \
  >> "$LOG_DIR/compact-events.log"

# Recovery message — Task API based
MSG="Your session was compacted. As Lead: 1) TaskList to see all tasks (including PERMANENT Task) 2) TaskGet on [PERMANENT] task for project context 3) Send fresh context to each active teammate with latest PT 4) Teammates should TaskGet their assigned tasks to restore progress."

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
