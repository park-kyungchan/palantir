#!/usr/bin/env bash
set -euo pipefail

# Stop hook — detects rationalization cop-outs and prevents premature stopping (RSIL-009)
# Input: JSON on stdin with stop context
# Output: exit 2 + stderr to PREVENT stopping (force continuation)
# Exit: 0 (allow stop) or 2 (block stop, continue working)
# Guard: stop_hook_active prevents infinite loops (RSIL-007)

INPUT=$(cat)

# Guard: second-pass detection — if stop_hook_active is true, always allow stop
if echo "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true'; then
  exit 0
fi

# Extract response/content text from available fields
if command -v jq &>/dev/null; then
  RESPONSE=$(echo "$INPUT" | jq -r '
    (.tool_input.response // .response // .content // .message // "") |
    ascii_downcase
  ' 2>/dev/null || echo "")
else
  RESPONSE=$(echo "$INPUT" | tr '[:upper:]' '[:lower:]')
fi

# Empty response — nothing to check
[[ -z "$RESPONSE" ]] && exit 0

# Rationalization cop-out phrases (high-confidence only to minimize false positives)
PHRASES=(
  "pre-existing issue"
  "pre-existing bug"
  "out of scope"
  "beyond the scope"
  "beyond scope"
  "follow-up task"
  "future work"
  "separate issue"
  "cannot be fixed"
  "not feasible"
  "this is expected behavior"
  "this is too complex"
  "let me skip"
  "i'll do this later"
  "i will do this later"
  "skip this for now"
  "defer this to"
  "revisit later"
  "punt this"
  "i'll move on"
  "let's move on to something else"
  "unable to complete this"
)

for phrase in "${PHRASES[@]}"; do
  if echo "$RESPONSE" | grep -qF "$phrase"; then
    echo "BLOCKED STOP: Rationalization detected — \"$phrase\". Continue working on the original task instead of dismissing it." >&2
    exit 2
  fi
done

exit 0
