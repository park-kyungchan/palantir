#!/bin/bash
# Hook: PostToolUse(TaskUpdate) — Task state change logging + JSON output
# Fires after TaskUpdate is called (task completion, status changes)

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

TASK_ID=$(echo "$INPUT" | jq -r '.tool_input.taskId // "unknown"' 2>/dev/null)
STATUS=$(echo "$INPUT" | jq -r '.tool_input.status // "unchanged"' 2>/dev/null)
SUBJECT=$(echo "$INPUT" | jq -r '.tool_input.subject // empty' 2>/dev/null)
OWNER=$(echo "$INPUT" | jq -r '.tool_input.owner // empty' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] TASK_UPDATE | id=$TASK_ID | status=$STATUS | owner=${OWNER:-unset}" >> "$LOG_DIR/task-lifecycle.log"

# Output structured JSON for machine parsing
if command -v jq &>/dev/null; then
  jq -n --arg id "$TASK_ID" --arg status "$STATUS" --arg subject "$SUBJECT" --arg owner "$OWNER" '{
    "hookSpecificOutput": {
      "hookEventName": "TaskUpdate",
      "taskId": $id,
      "status": $status,
      "subject": (if $subject != "" then $subject else null end),
      "owner": (if $owner != "" then $owner else null end)
    }
  }'
fi

exit 0
