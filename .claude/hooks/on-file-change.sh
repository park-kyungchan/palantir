#!/usr/bin/env bash
# SRC Stage 1: Silent file change logger
# Event: PostToolUse (Edit|Write)
# Purpose: Append changed file path to session-scoped change log
# Output: None (silent, no additionalContext)

set -euo pipefail

# Read JSON from stdin
INPUT=$(cat)

# Extract fields via jq
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
SUCCESS=$(echo "$INPUT" | jq -r 'if .tool_response.success == false then "false" else "true" end')

# Validate required fields
[[ -z "$SESSION_ID" || -z "$FILE_PATH" ]] && exit 0

# Only log successful operations
[[ "$SUCCESS" == "false" ]] && exit 0

# Sanitize: remove tabs/newlines from file path
FILE_PATH=$(echo "$FILE_PATH" | tr -d '\t\n\r')

# Append to session-scoped change log (atomic for lines < PIPE_BUF)
LOGFILE="/tmp/src-changes-${SESSION_ID}.log"
echo -e "$(date -Iseconds)\t${TOOL_NAME}\t${FILE_PATH}" >> "$LOGFILE" 2>/dev/null || true

exit 0
