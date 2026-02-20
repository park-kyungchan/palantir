#!/usr/bin/env bash
# PreToolUse:Grep hook — CE Pattern 3: Pattern Optimization
# Purpose: Inject CE tips when Grep parameters may cause large result sets.
#          Checks for: content mode without head_limit, and root/empty path searches.
# Exit: Always 0 (advisory only, never blocks)

set -uo pipefail

INPUT=$(cat)

# Graceful fallback if jq missing
if ! command -v jq &>/dev/null; then
  exit 0
fi

# Extract tool_input fields — exit 0 on any parse error
OUTPUT_MODE=$(echo "$INPUT" | jq -r '.tool_input.output_mode // empty' 2>/dev/null) || exit 0
HEAD_LIMIT=$(echo "$INPUT" | jq -r '.tool_input.head_limit // empty' 2>/dev/null) || exit 0
SEARCH_PATH=$(echo "$INPUT" | jq -r '.tool_input.path // empty' 2>/dev/null) || exit 0

TIPS=()

# Check 1: content mode without head_limit
if [[ "$OUTPUT_MODE" == "content" ]]; then
  if [[ -z "$HEAD_LIMIT" || "$HEAD_LIMIT" == "0" || "$HEAD_LIMIT" == "null" ]]; then
    TIPS+=("CE Tip: Grep output_mode:\"content\" without head_limit may return large results and consume significant context tokens. Add head_limit (e.g., 20-50) to cap output.")
  fi
fi

# Check 2: root or empty path search
if [[ -z "$SEARCH_PATH" || "$SEARCH_PATH" == "/" || "$SEARCH_PATH" == "." ]]; then
  TIPS+=("CE Tip: Grep without a specific path searches the entire working directory. Specify a path (e.g., \"src/\", \"*.ts\") to narrow scope and reduce token consumption.")
fi

# Only output if we have tips
if [[ ${#TIPS[@]} -eq 0 ]]; then
  exit 0
fi

# Combine tips
COMBINED_TIPS=""
for tip in "${TIPS[@]}"; do
  if [[ -n "$COMBINED_TIPS" ]]; then
    COMBINED_TIPS="${COMBINED_TIPS} | ${tip}"
  else
    COMBINED_TIPS="$tip"
  fi
done

jq -n --arg ctx "$COMBINED_TIPS" '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": $ctx
  }
}'

exit 0
