#!/bin/bash
#=============================================================================
# Blocked Task Gate - Block starting tasks with unresolved dependencies
# Version: 1.1.0
#
# Purpose: Prevent starting a task that has blockedBy dependencies
# Trigger: PreToolUse (TaskUpdate)
#
# Logic:
#   1. Check if tool is TaskUpdate
#   2. Check if status is being set to "in_progress"
#   3. Find task file in .claude/tasks/ or .claude/todos/
#   4. Check if task has non-empty blockedBy array
#   5. If blockedBy exists and is not empty, DENY
#
# Exceptions:
#   - Non-TaskUpdate tools
#   - Status changes other than "in_progress"
#   - Tasks without blockedBy field
#   - Tasks with empty blockedBy array
#
# Changes in 1.1.0:
#   - Added set -euo pipefail
#   - Added trap for cleanup on error
#   - Standardized JSON field names (tool_name, tool_input)
#   - Enhanced documentation
#   - Improved error handling
#=============================================================================

set -euo pipefail

# Error cleanup trap - allow on script errors (fail-open)
trap 'output_allow; exit 0' ERR

# Source shared library
source "$(dirname "$0")/_shared.sh"

#=============================================================================
# Main Logic
#=============================================================================

main() {
    # Read stdin JSON
    local input
    input=$(cat)

    # Extract tool name and parameters
    local tool_name
    tool_name=$(json_get '.tool_name' "$input")

    # Only process TaskUpdate
    if [[ "$tool_name" != "TaskUpdate" ]]; then
        output_allow
        exit 0
    fi

    # Extract parameters
    local task_id new_status
    task_id=$(json_get '.tool_input.taskId' "$input")
    new_status=$(json_get '.tool_input.status' "$input")

    # Only check when status is being set to "in_progress"
    if [[ "$new_status" != "in_progress" ]]; then
        output_allow
        exit 0
    fi

    # Check if task has blockedBy dependencies
    # Note: We need to check the task's current state, which requires reading from task storage
    # Since we don't have direct access to Task API from shell, we check for task files

    # Look for task file in .claude/tasks/ or .claude/todos/
    local task_file="" dir file file_task_id
    for dir in "${WORKSPACE_ROOT}/.claude/tasks/"* "${WORKSPACE_ROOT}/.claude/todos/"*; do
        if [[ -d "$dir" ]]; then
            for file in "$dir"/*.json; do
                if [[ -f "$file" ]]; then
                    file_task_id=$(json_get '.id' "$(cat "$file")")
                    if [[ "$file_task_id" == "$task_id" ]]; then
                        task_file="$file"
                        break 2
                    fi
                fi
            done
        elif [[ -f "$dir" ]]; then
            file_task_id=$(json_get '.id' "$(cat "$dir")")
            if [[ "$file_task_id" == "$task_id" ]]; then
                task_file="$dir"
                break
            fi
        fi
    done

    # If we found a task file, check blockedBy
    if [[ -n "$task_file" ]]; then
        local task_content blocked_by
        task_content=$(cat "$task_file")
        blocked_by=$(json_get '.blockedBy' "$task_content")

        # Check if blockedBy is non-empty array
        if [[ -n "$blocked_by" ]] && [[ "$blocked_by" != "[]" ]] && [[ "$blocked_by" != "null" ]]; then
            log_enforcement "blocked-task-gate" "deny" "Task $task_id has unresolved blockedBy: $blocked_by" "TaskUpdate"
            output_deny \
                "Blocked Task: Task #$task_id cannot be started because it is blocked by other tasks." \
                "The blockedBy list contains: $blocked_by. Please complete those tasks first before starting this one."
            exit 0
        fi
    fi

    # Allow if no blocking issues found
    output_allow
}

# Execute main
main

exit 0
