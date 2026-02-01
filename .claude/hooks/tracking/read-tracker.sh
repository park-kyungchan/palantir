#!/bin/bash
#=============================================================================
# read-tracker.sh - Track Read tool invocations
# Version: 1.0.0
#
# Trigger: PostToolUse (Read)
# Purpose: Log file reads for context tracking and verification
#=============================================================================

# Source shared library (from parent enforcement directory)
source "$(dirname "$0")/../enforcement/_shared.sh"

# Read stdin JSON
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(json_get '.toolName' "$INPUT")

# Only process Read commands
if [[ "$TOOL_NAME" != "Read" ]]; then
    output_passthrough
    exit 0
fi

# Extract file path from tool input
FILE_PATH=$(json_get '.toolInput.file_path' "$INPUT")

if [[ -z "$FILE_PATH" ]]; then
    # Try alternative field names
    FILE_PATH=$(json_get '.toolInput.filePath' "$INPUT")
fi

if [[ -z "$FILE_PATH" ]]; then
    FILE_PATH=$(json_get '.toolInput.path' "$INPUT")
fi

# Log the read event if we have a file path
if [[ -n "$FILE_PATH" ]]; then
    log_tracking "read" "$FILE_PATH"
fi

# Pass through (no blocking in PostToolUse)
output_passthrough
exit 0
