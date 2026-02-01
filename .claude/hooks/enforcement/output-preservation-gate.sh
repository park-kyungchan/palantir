#!/bin/bash
#=============================================================================
# output-preservation-gate.sh - Ensure task outputs are saved before completion
# Version: 1.0.0
#
# Trigger: PreToolUse (TaskUpdate)
# Purpose: Warn when completing a task without saving outputs
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

# Only check when status is being set to "completed"
if [[ "$NEW_STATUS" != "completed" ]]; then
    output_allow
    exit 0
fi

# Get current workload slug
SLUG=$(get_workload_slug)

if [[ -z "$SLUG" ]]; then
    # No active workload, allow completion
    output_allow
    exit 0
fi

# Check if outputs directory exists and has content
OUTPUTS_DIR="${WORKSPACE_ROOT}/.agent/prompts/${SLUG}/outputs"

if [[ ! -d "$OUTPUTS_DIR" ]]; then
    # No outputs directory - ask for confirmation
    log_enforcement "output-preservation-gate" "ask" "No outputs directory for workload $SLUG" "TaskUpdate"
    output_ask \
        "Output Warning: No outputs directory found at ${OUTPUTS_DIR}. Consider saving task results before marking complete. Continue anyway?"
    exit 0
fi

# Check if directory has any content
OUTPUT_COUNT=$(find "$OUTPUTS_DIR" -type f 2>/dev/null | wc -l)

if [[ "$OUTPUT_COUNT" -eq 0 ]]; then
    log_enforcement "output-preservation-gate" "ask" "Empty outputs directory for workload $SLUG" "TaskUpdate"
    output_ask \
        "Output Warning: The outputs directory is empty. Consider saving task #$TASK_ID results before marking complete. Continue anyway?"
    exit 0
fi

# Outputs exist, allow completion
output_allow
exit 0
