#!/usr/bin/env bash
# PostToolUse:Grep hook — CE Pattern 2: Result Explosion Prevention
# Purpose: Warn when Grep returns >50 matches to prevent context bloat.
#          PostToolUse cannot block — advisory only.
# Exit: Always 0

set -uo pipefail

INPUT=$(cat)

# Graceful fallback if jq missing
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract tool_response from stdin — exit 0 on any parse error
TOOL_RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null) || exit 0

if [[ -z "$TOOL_RESPONSE" ]]; then
  exit 0
fi

# Count lines in the tool response output
# tool_response is a string; count newlines as proxy for result lines
RESPONSE_TEXT=$(echo "$INPUT" | jq -r '.tool_response | if type == "string" then . elif type == "object" then (.content // .output // (. | tostring)) else (. | tostring) end' 2>/dev/null || true)

if [[ -z "$RESPONSE_TEXT" ]]; then
  exit 0
fi

LINE_COUNT=$(echo "$RESPONSE_TEXT" | wc -l 2>/dev/null || echo 0)

if [[ "$LINE_COUNT" -le 50 ]]; then
  exit 0
fi

# Inject warning
PATTERN=$(echo "$INPUT" | jq -r '.tool_input.pattern // "unknown"' 2>/dev/null || echo "unknown")

jq -n --argjson count "$LINE_COUNT" --arg pattern "$PATTERN" '{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": ("CE Warning: Grep returned " + ($count | tostring) + " lines for pattern \"" + $pattern + "\". Large grep results consume significant context window tokens. Recommendations: (1) Add head_limit parameter (e.g., head_limit: 20) to cap results, (2) Use output_mode: \"files_with_matches\" to get file paths only, (3) Narrow the pattern or add a path filter, (4) Use output_mode: \"count\" to check scale before reading content.")
  }
}'

exit 0
