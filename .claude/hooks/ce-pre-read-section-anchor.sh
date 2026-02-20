#!/usr/bin/env bash
# PreToolUse:Read hook — CE Pattern 1: Auto Section Anchoring
# Purpose: For large .md files (>100 lines), inject a section map as additionalContext
#          so the agent can reference specific sections instead of reading the whole file.
# Exit: Always 0 (advisory only, never blocks)

set -uo pipefail

INPUT=$(cat)

# Graceful fallback if jq missing
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract file_path from tool_input — exit 0 on any parse error
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null) || exit 0

# Only process .md files
if [[ -z "$FILE_PATH" || "$FILE_PATH" != *.md ]]; then
  exit 0
fi

# Only process files that exist
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

# Count lines — fast path for small files
LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null || echo 0)
if [[ "$LINE_COUNT" -le 100 ]]; then
  exit 0
fi

# Extract headings with line numbers
HEADINGS=$(grep -n '^#' "$FILE_PATH" 2>/dev/null || true)

if [[ -z "$HEADINGS" ]]; then
  exit 0
fi

# Build section map message
SECTION_MAP="Section map for ${FILE_PATH} (${LINE_COUNT} lines):\n${HEADINGS}\n\nCE Tip: Use offset+limit parameters to read only the relevant section rather than the entire file."

# Output additionalContext via JSON
jq -n --arg ctx "$SECTION_MAP" '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": $ctx
  }
}'

exit 0
