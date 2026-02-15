#!/usr/bin/env bash
# OPT-16: PostToolUseFailure logger — tracks failed Edit/Write operations
# Event: PostToolUseFailure (Edit|Write)
# Purpose: Log failed file operations to session-scoped failure log
# Output: None (async, non-blocking)

set -euo pipefail

# Read JSON from stdin
INPUT=$(cat)

# Extract fields (jq preferred, grep fallback)
if command -v jq &>/dev/null; then
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
    TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // "unknown"')
    FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // "unknown"')
else
    SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
    TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)
    FILE_PATH=$(echo "$INPUT" | grep -o '"file_path":"[^"]*"' | cut -d'"' -f4)
    SESSION_ID="${SESSION_ID:-unknown}"
    TOOL_NAME="${TOOL_NAME:-unknown}"
    FILE_PATH="${FILE_PATH:-unknown}"
fi

# Validate required fields
[[ -z "$SESSION_ID" ]] && SESSION_ID="unknown"

# Append to session-scoped failure log
LOGFILE="/tmp/src-failures-${SESSION_ID}.log"
echo "[$(date +%H:%M:%S)] ${TOOL_NAME}_FAIL: ${FILE_PATH}" >> "$LOGFILE" 2>/dev/null || true

exit 0
