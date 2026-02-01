#!/bin/bash
#=============================================================================
# task-tracker.sh - Track TaskCreate and TaskUpdate invocations
# Version: 2.0.0
#
# Trigger: PostToolUse (TaskCreate|TaskUpdate)
# Purpose: Log task operations for workflow tracking and verification
#
# Log Path: .agent/tmp/recent_tasks.log (via _shared.sh)
# Format: ISO8601_TIMESTAMP|TOOL_NAME|taskId:ID|status:STATUS|subject:SUBJECT
#
# Changes in 2.0.0:
#   - Added comprehensive header documentation
#   - Improved error handling with set -euo pipefail
#   - Standardized log format documentation
#=============================================================================

set -euo pipefail

# Source shared library (from parent enforcement directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../enforcement/_shared.sh"

# Read stdin JSON (handle empty input gracefully)
INPUT=$(cat 2>/dev/null || echo '{}')

# Extract tool name
TOOL_NAME=$(json_get '.toolName' "$INPUT")

# Only process TaskCreate and TaskUpdate
if [[ "$TOOL_NAME" != "TaskCreate" ]] && [[ "$TOOL_NAME" != "TaskUpdate" ]]; then
    output_passthrough
    exit 0
fi

# Extract common fields
TASK_ID=$(json_get '.toolInput.taskId' "$INPUT")
STATUS=$(json_get '.toolInput.status' "$INPUT")
SUBJECT=$(json_get '.toolInput.subject' "$INPUT")

# For TaskCreate, the ID might come from the result, but we may not have it in PreToolUse
# So we log what we have

# Build details string
DETAILS="$TOOL_NAME"

if [[ -n "$TASK_ID" ]]; then
    DETAILS="${DETAILS}|taskId:${TASK_ID}"
fi

if [[ -n "$STATUS" ]]; then
    DETAILS="${DETAILS}|status:${STATUS}"
fi

if [[ -n "$SUBJECT" ]]; then
    # Truncate subject if too long
    SUBJECT_SHORT="${SUBJECT:0:50}"
    DETAILS="${DETAILS}|subject:${SUBJECT_SHORT}"
fi

# Log the task event
log_tracking "task" "$DETAILS"

# Pass through (no blocking in PostToolUse)
output_passthrough
exit 0
