#!/usr/bin/env bash
set -euo pipefail

# TaskCompleted hook — logs task completion events for pipeline tracking
# Input: JSON on stdin with task_id, task_subject, task_description, teammate_name, team_name
# Output: Logs to /tmp/task-completions-{session_id}.log
# Exit: Always 0 (non-blocking, logging only)

INPUT=$(cat)

# Extract fields using jq with grep fallback
if command -v jq &>/dev/null; then
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
  TASK_ID=$(echo "$INPUT" | jq -r '.task_id // "unknown"')
  TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject // "unknown"')
  TEAMMATE=$(echo "$INPUT" | jq -r '.teammate_name // "unknown"')
  TEAM=$(echo "$INPUT" | jq -r '.team_name // "unknown"')
else
  SESSION_ID=$(echo "$INPUT" | grep -oP '"session_id"\s*:\s*"\K[^"]+' || echo "unknown")
  TASK_ID=$(echo "$INPUT" | grep -oP '"task_id"\s*:\s*"\K[^"]+' || echo "unknown")
  TASK_SUBJECT=$(echo "$INPUT" | grep -oP '"task_subject"\s*:\s*"\K[^"]+' || echo "unknown")
  TEAMMATE=$(echo "$INPUT" | grep -oP '"teammate_name"\s*:\s*"\K[^"]+' || echo "unknown")
  TEAM=$(echo "$INPUT" | grep -oP '"team_name"\s*:\s*"\K[^"]+' || echo "unknown")
fi

LOGFILE="/tmp/task-completions-${SESSION_ID}.log"

# Append completion record
echo "[$(date '+%H:%M:%S')] COMPLETED task=${TASK_ID} subject=\"${TASK_SUBJECT}\" by=${TEAMMATE} team=${TEAM}" >> "$LOGFILE"

exit 0
