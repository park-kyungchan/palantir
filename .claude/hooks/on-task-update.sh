#!/bin/bash
# Hook: PostToolUse(TaskUpdate) — Task 상태 변경 시 로깅
# Fires after TaskUpdate is called (task completion, status changes)

INPUT=$(cat)

TASK_ID=$(echo "$INPUT" | jq -r '.tool_input.taskId // "unknown"' 2>/dev/null)
STATUS=$(echo "$INPUT" | jq -r '.tool_input.status // "unchanged"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] TASK_UPDATE | id=$TASK_ID | status=$STATUS" >> "$LOG_DIR/task-lifecycle.log"

exit 0
