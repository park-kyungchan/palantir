#!/bin/bash
# Hook: SessionStart(compact) — Auto-compact recovery notification
# Recovery: Lead must re-inject context to all active teammates
# Output: JSON with additionalContext for Claude to consume

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — re-injection required" >> "$LOG_DIR/compact-events.log"

# Output structured JSON for Claude to consume
if command -v jq &>/dev/null; then
  jq -n '{
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": "Your session was compacted. As Lead: 1) Read orchestration-plan.md 2) Read task list (including PERMANENT Task) 3) Send fresh context to each active teammate with the latest PT version 4) Teammates should read their L1/L2/L3 files to restore progress."
    }
  }'
else
  # Fallback: plain JSON without jq
  echo '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Your session was compacted. As Lead: 1) Read orchestration-plan.md 2) Read task list (including PERMANENT Task) 3) Send fresh context to each active teammate with the latest PT version 4) Teammates should read their L1/L2/L3 files to restore progress."}}'
fi

exit 0
