#!/bin/bash
#=============================================================================
# blocked-task-gate.sh - Block starting tasks that have unresolved dependencies
# Version: 1.0.0
#
# Trigger: PreToolUse (TaskUpdate)
# Purpose: Prevent starting a task that has blockedBy dependencies
#=============================================================================

source "$(dirname "$0")/_shared.sh"

# Read stdin JSON
INPUT=$(cat)

# Extract tool name and parameters
TOOL_NAME=$(json_get '.toolName' "$INPUT")

# Only process TaskUpdate
if [[ "$TOOL_NAME" != "TaskUpdate" ]]; then
    output_allow
    exit 0
fi

# Extract parameters
TASK_ID=$(json_get '.toolInput.taskId' "$INPUT")
NEW_STATUS=$(json_get '.toolInput.status' "$INPUT")

# Only check when status is being set to "in_progress"
if [[ "$NEW_STATUS" != "in_progress" ]]; then
    output_allow
    exit 0
fi

# Check if task has blockedBy dependencies
# Note: We need to check the task's current state, which requires reading from task storage
# Since we don't have direct access to Task API from shell, we check for task files

# Look for task file in .claude/tasks/ or .claude/todos/
TASK_FILE=""
for dir in "${WORKSPACE_ROOT}/.claude/tasks/"* "${WORKSPACE_ROOT}/.claude/todos/"*; do
    if [[ -d "$dir" ]]; then
        for file in "$dir"/*.json; do
            if [[ -f "$file" ]]; then
                file_task_id=$(json_get '.id' "$(cat "$file")")
                if [[ "$file_task_id" == "$TASK_ID" ]]; then
                    TASK_FILE="$file"
                    break 2
                fi
            fi
        done
    elif [[ -f "$dir" ]]; then
        file_task_id=$(json_get '.id' "$(cat "$dir")")
        if [[ "$file_task_id" == "$TASK_ID" ]]; then
            TASK_FILE="$dir"
            break
        fi
    fi
done

# If we found a task file, check blockedBy
if [[ -n "$TASK_FILE" ]]; then
    TASK_CONTENT=$(cat "$TASK_FILE")
    BLOCKED_BY=$(json_get '.blockedBy' "$TASK_CONTENT")

    # Check if blockedBy is non-empty array
    if [[ -n "$BLOCKED_BY" ]] && [[ "$BLOCKED_BY" != "[]" ]] && [[ "$BLOCKED_BY" != "null" ]]; then
        log_enforcement "blocked-task-gate" "deny" "Task $TASK_ID has unresolved blockedBy: $BLOCKED_BY" "TaskUpdate"
        output_deny \
            "Blocked Task: Task #$TASK_ID cannot be started because it is blocked by other tasks." \
            "The blockedBy list contains: $BLOCKED_BY. Please complete those tasks first before starting this one."
        exit 0
    fi
fi

# Allow if no blocking issues found
output_allow
exit 0
