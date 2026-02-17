#!/usr/bin/env bash
set -euo pipefail

# PreToolUse:Bash hook — blocks unsafe git push to main/master (RSIL-009)
# Input: JSON on stdin with tool_name, tool_input.command
# Output: exit 2 + stderr message to BLOCK dangerous pushes
# Exit: 0 (safe) or 2 (block)

INPUT=$(cat)

# Extract command from stdin JSON
if command -v jq &>/dev/null; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
else
  COMMAND=$(echo "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]+' || echo "")
fi

# Only check git push commands
echo "$COMMAND" | grep -q 'git push' || exit 0

# Normalize for matching
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Block: force push (--force / -f) to ANY branch
if echo "$CMD_LOWER" | grep -qE '\bgit\s+push\s+.*(\s--force\b|\s-f\b)'; then
  echo "BLOCKED: Force push (--force/-f) is not allowed. Use --force-with-lease for non-protected branches." >&2
  exit 2
fi

# Block: force-with-lease to main/master specifically
if echo "$CMD_LOWER" | grep -qE '\bgit\s+push\s+.*--force-with-lease.*\s(main|master)\b'; then
  echo "BLOCKED: Force push to main/master is not allowed, even with --force-with-lease." >&2
  exit 2
fi

# Block: direct push to main/master (without PR)
if echo "$CMD_LOWER" | grep -qE '\bgit\s+push\s+\S+\s+(main|master)\b'; then
  echo "BLOCKED: Direct push to main/master is not allowed. Create a PR instead." >&2
  exit 2
fi

exit 0
