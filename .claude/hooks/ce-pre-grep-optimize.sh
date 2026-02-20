#!/usr/bin/env bash
# PreToolUse:Grep hook — CE Pattern 3: Content Mode Guard (BLOCKING)
# Purpose: Block Grep calls with output_mode="content" that lack head_limit.
#          Without head_limit, content mode can return thousands of lines and
#          consume significant context window tokens.
# Exit: 2 (BLOCK) when content mode + no head_limit | 0 (allow) otherwise

set -uo pipefail

INPUT=$(cat)

# Graceful fallback if jq missing
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract tool_input fields — exit 0 on any parse error
OUTPUT_MODE=$(echo "$INPUT" | jq -r '.tool_input.output_mode // empty' 2>/dev/null) || exit 0
HEAD_LIMIT=$(echo "$INPUT" | jq -r '.tool_input.head_limit // empty' 2>/dev/null) || exit 0

# Only block when: output_mode is "content" AND head_limit is absent/zero/null
if [[ "$OUTPUT_MODE" == "content" ]]; then
  if [[ -z "$HEAD_LIMIT" || "$HEAD_LIMIT" == "0" || "$HEAD_LIMIT" == "null" ]]; then
    jq -n '{
      "decision": "block",
      "reason": "CE BLOCK: Grep output_mode:\"content\" requires head_limit to prevent context bloat. Add head_limit (e.g., head_limit: 20) to cap output. Example: {\"pattern\": \"...\", \"output_mode\": \"content\", \"head_limit\": 20}"
    }'
    exit 2
  fi
fi

exit 0
