#!/bin/bash
#=============================================================================
# Output Preservation Gate - Ensure task outputs are saved before completion
# Version: 1.1.0
#
# Purpose: Warn when completing a task without saving outputs
# Trigger: PreToolUse (TaskUpdate)
#
# Logic:
#   1. Check if tool is TaskUpdate
#   2. Check if status is being set to "completed"
#   3. Get current workload slug
#   4. Check if outputs directory exists
#   5. Check if outputs directory has content
#   6. If no outputs or empty, ASK for confirmation
#
# Exceptions:
#   - Non-TaskUpdate tools
#   - Status changes other than "completed"
#   - No active workload (allow completion freely)
#   - Outputs directory has files (allow completion)
#
# Changes in 1.1.0:
#   - Added set -euo pipefail
#   - Added trap for cleanup on error
#   - Standardized JSON field names
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

    # Only check when status is being set to "completed"
    if [[ "$new_status" != "completed" ]]; then
        output_allow
        exit 0
    fi

    # Get current workload slug
    local slug
    slug=$(get_workload_slug)

    if [[ -z "$slug" ]]; then
        # No active workload, allow completion
        output_allow
        exit 0
    fi

    # Check if outputs directory exists and has content
    local outputs_dir="${WORKSPACE_ROOT}/.agent/prompts/${slug}/outputs"

    if [[ ! -d "$outputs_dir" ]]; then
        # No outputs directory - ask for confirmation
        log_enforcement "output-preservation-gate" "ask" "No outputs directory for workload $slug" "TaskUpdate"
        output_ask \
            "Output Warning: No outputs directory found at ${outputs_dir}. Consider saving task results before marking complete. Continue anyway?"
        exit 0
    fi

    # Check if directory has any content
    local output_count
    output_count=$(find "$outputs_dir" -type f 2>/dev/null | wc -l)

    if [[ "$output_count" -eq 0 ]]; then
        log_enforcement "output-preservation-gate" "ask" "Empty outputs directory for workload $slug" "TaskUpdate"
        output_ask \
            "Output Warning: The outputs directory is empty. Consider saving task #$task_id results before marking complete. Continue anyway?"
        exit 0
    fi

    # Outputs exist, allow completion
    output_allow
}

# Execute main
main

exit 0
