#!/bin/bash
#=============================================================================
# Task Lifecycle Gate
# Version: 1.1.0
#
# Purpose: Enforce proper Task status lifecycle and context awareness
# Trigger: PreToolUse (TaskUpdate)
#
# Logic:
#   1. If TaskUpdate changes status
#   2. Validate proper lifecycle: pending → in_progress → completed
#   3. Block invalid transitions (e.g., pending → completed directly)
#   4. Inject context reminder for "holistic context awareness"
#
# Lifecycle Rules:
#   - pending → in_progress: ALLOWED
#   - in_progress → completed: ALLOWED
#   - in_progress → pending: ALLOWED (rollback)
#   - pending → completed: DENIED (must go through in_progress)
#   - completed → in_progress: DENIED (use new task)
#   - completed → pending: DENIED (use new task)
#
# Changes in 1.1.0:
#   - CRITICAL FIX: get_task_status() now checks .claude/todos/ and .claude/tasks/ first
#   - Synchronizes with Native Task API by reading actual task JSON files
#   - Fallback to local tracking file if task file not found
#
# Context Awareness:
#   Ensures Main Agent and Subagents always understand "What am I doing in the overall workflow?"
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Configuration
#=============================================================================
readonly TASK_STATE_FILE="${AGENT_TMP_DIR}/task_states.json"

#=============================================================================
# Helper Functions
#=============================================================================

# Get current task status from tracking (V1.1.0: Check .claude/todos/ first)
get_task_status() {
    local task_id="$1"

    # V1.1.0: First check actual task files in .claude/todos/ or .claude/tasks/
    local task_file="" dir file file_task_id
    for dir in "${WORKSPACE_ROOT}/.claude/tasks/"* "${WORKSPACE_ROOT}/.claude/todos/"*; do
        if [[ -d "$dir" ]]; then
            for file in "$dir"/*.json; do
                if [[ -f "$file" ]]; then
                    file_task_id=$(json_get '.id' "$(cat "$file" 2>/dev/null)" 2>/dev/null)
                    if [[ "$file_task_id" == "$task_id" ]]; then
                        task_file="$file"
                        break 2
                    fi
                fi
            done
        elif [[ -f "$dir" ]]; then
            file_task_id=$(json_get '.id' "$(cat "$dir" 2>/dev/null)" 2>/dev/null)
            if [[ "$file_task_id" == "$task_id" ]]; then
                task_file="$dir"
                break
            fi
        fi
    done

    # If task file found, use its status
    if [[ -n "$task_file" ]] && [[ -f "$task_file" ]]; then
        local file_status
        file_status=$(json_get '.status' "$(cat "$task_file" 2>/dev/null)" 2>/dev/null)
        if [[ -n "$file_status" ]] && [[ "$file_status" != "null" ]]; then
            echo "$file_status"
            return 0
        fi
    fi

    # Fallback to local tracking file
    [[ -f "$TASK_STATE_FILE" ]] || { echo "pending"; return 0; }

    local status
    status=$(json_get ".\"${task_id}\"" "$(cat "$TASK_STATE_FILE" 2>/dev/null)" 2>/dev/null)
    echo "${status:-pending}"
}

# Update task status in tracking
update_task_status() {
    local task_id="$1"
    local new_status="$2"

    mkdir -p "$(dirname "$TASK_STATE_FILE")" 2>/dev/null || true

    # Simple append-based tracking (will have duplicates but last wins)
    echo "{\"${task_id}\": \"${new_status}\"}" >> "$TASK_STATE_FILE" 2>/dev/null || true
}

# Validate status transition
is_valid_transition() {
    local current="$1"
    local new="$2"

    case "${current}:${new}" in
        # Valid transitions
        pending:in_progress) return 0 ;;
        in_progress:completed) return 0 ;;
        in_progress:pending) return 0 ;;  # Rollback allowed
        # Same status (no change)
        pending:pending) return 0 ;;
        in_progress:in_progress) return 0 ;;
        completed:completed) return 0 ;;
        # Invalid transitions
        pending:completed) return 1 ;;  # Must go through in_progress
        completed:*) return 1 ;;  # Completed tasks cannot be changed
        *) return 0 ;;  # Allow unknown for flexibility
    esac
}

# Generate context reminder
get_context_reminder() {
    local task_id="$1"
    local new_status="$2"

    local workload_info=""
    if has_active_workload; then
        local slug skill
        slug=$(get_workload_slug)
        skill=$(get_workload_skill)
        workload_info="Active Workload: ${slug}, Current Skill: ${skill:-unknown}"
    fi

    cat << EOF
[Holistic Context Awareness]
Task #${task_id} → ${new_status}
${workload_info}

IMPORTANT: Always be aware of this Task's role in the overall workflow.
- Are you utilizing results from previous Tasks?
- What impact does this have on downstream Tasks?
- Is the dependency chain (blockedBy) correctly configured?
EOF
}

#=============================================================================
# Main Logic
#=============================================================================

main() {
    # Read JSON from stdin
    local input
    input=$(cat)

    # Parse tool name
    local tool_name
    tool_name=$(json_get '.tool_name' "$input")

    # Only check for TaskUpdate
    if [[ "$tool_name" != "TaskUpdate" ]]; then
        output_allow
        exit 0
    fi

    # Parse task ID and new status
    local task_id new_status
    task_id=$(json_get '.tool_input.taskId' "$input")
    new_status=$(json_get '.tool_input.status' "$input")

    # No status change - allow
    if [[ -z "$new_status" ]]; then
        output_allow
        exit 0
    fi

    # Get current status
    local current_status
    current_status=$(get_task_status "$task_id")

    # Validate transition
    if ! is_valid_transition "$current_status" "$new_status"; then
        local reason="Invalid Task Status Transition"
        local guidance="Invalid status transition: ${current_status} → ${new_status}. Task must follow: pending → in_progress → completed. Cannot skip in_progress phase."

        log_enforcement "task-lifecycle-gate" "deny" "$reason" "TaskUpdate:$task_id ($current_status→$new_status)"
        output_deny "$reason" "$guidance"
        exit 0
    fi

    # Update tracking
    update_task_status "$task_id" "$new_status"

    # Generate context reminder
    local context_reminder
    context_reminder=$(get_context_reminder "$task_id" "$new_status")
    context_reminder=$(_escape_json "$context_reminder")

    log_enforcement "task-lifecycle-gate" "allow" "Valid transition" "TaskUpdate:$task_id ($current_status→$new_status)"

    # Allow with context reminder
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "$context_reminder"
  }
}
EOF
}

# Execute main
main

exit 0
