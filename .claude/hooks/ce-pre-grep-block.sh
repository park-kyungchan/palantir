#!/usr/bin/env bash
# CE blocking hook: Grep without path= → exit 2
# Fires on PreToolUse for Grep tool

TOOL_INPUT=$(cat)
TOOL_NAME=$(echo "$TOOL_INPUT" | jq -r '.tool_name // empty' 2>/dev/null)

if [ "$TOOL_NAME" != "Grep" ]; then
  exit 0
fi

PATH_VAL=$(echo "$TOOL_INPUT" | jq -r '.tool_input.path // empty' 2>/dev/null)

if [ -z "$PATH_VAL" ]; then
  echo "CE-BLOCK: Grep without 'path' parameter is prohibited (full-codebase scan = context waste)." >&2
  echo "Correct pattern:" >&2
  echo "  1. Always provide path= to scope the search directory or file" >&2
  echo "  2. Add head_limit= (e.g. head_limit:20) to cap result size" >&2
  echo "  3. Use output_mode='files_with_matches' unless line content is needed" >&2
  echo "Examples:" >&2
  echo "  Grep pattern='myFunc' path='/home/palantir/.claude/skills/'" >&2
  echo "  Grep pattern='TODO' path='/home/palantir/src/' head_limit:20 output_mode='files_with_matches'" >&2
  echo "Never omit path= — it causes ripgrep to scan the entire workspace." >&2
  exit 2
fi

exit 0
