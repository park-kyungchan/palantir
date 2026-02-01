#!/bin/bash
#=============================================================================
# read-tracker.sh - Track Read tool invocations
# Version: 2.0.0
#
# Trigger: PostToolUse (Read)
# Purpose: Log file reads for context tracking and verification
#
# Log Path: .agent/tmp/recent_reads.log (via _shared.sh)
# Format: ISO8601_TIMESTAMP|FILE_PATH
#
# Changes in 2.0.0:
#   - Added comprehensive header documentation
#   - Improved error handling with set -euo pipefail
#   - Standardized field extraction order
#=============================================================================

set -euo pipefail

# Source shared library (from parent enforcement directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../enforcement/_shared.sh"

# Read stdin JSON (handle empty input gracefully)
INPUT=$(cat 2>/dev/null || echo '{}')

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
