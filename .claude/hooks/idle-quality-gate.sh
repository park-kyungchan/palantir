#!/usr/bin/env bash
# DEPRECATED: TeammateIdle event removed in INFRA v14 (single-session architecture)
set -euo pipefail

# TeammateIdle hook — blocks idle when teammate has unfinished tasks (RSIL-011)
# Input: JSON on stdin with teammate_name, team_name
# Output: exit 2 + stderr to BLOCK idle (force more work)
# Exit: 0 (allow idle) or 2 (block idle)
# Guard: max 3 retries per teammate prevents infinite loops (RSIL-007)

INPUT=$(cat)

# Extract fields
if command -v jq &>/dev/null; then
  TEAMMATE=$(echo "$INPUT" | jq -r '.teammate_name // "unknown"')
  TEAM=$(echo "$INPUT" | jq -r '.team_name // "unknown"')
else
  TEAMMATE=$(echo "$INPUT" | grep -oP '"teammate_name"\s*:\s*"\K[^"]+' || echo "unknown")
  TEAM=$(echo "$INPUT" | grep -oP '"team_name"\s*:\s*"\K[^"]+' || echo "unknown")
fi

# Unknown teammate — allow idle
[[ "$TEAMMATE" == "unknown" ]] && exit 0

# Guard: retry counter prevents infinite loops
RETRY_FILE="/tmp/idle-retries-${TEAMMATE}.count"
RETRY_COUNT=0
if [[ -f "$RETRY_FILE" ]]; then
  RETRY_COUNT=$(cat "$RETRY_FILE" 2>/dev/null || echo "0")
  # Ensure numeric
  RETRY_COUNT=$((RETRY_COUNT + 0)) 2>/dev/null || RETRY_COUNT=0
fi

if [[ $RETRY_COUNT -ge 3 ]]; then
  # Max retries reached — reset and allow idle to prevent deadlock
  rm -f "$RETRY_FILE" 2>/dev/null || true
  exit 0
fi

# Check task directory for in_progress tasks owned by this teammate
TASK_DIR="$HOME/.claude/tasks/${TEAM}"
if [[ ! -d "$TASK_DIR" ]]; then
  exit 0  # No task directory — allow idle
fi

# Scan task files for in_progress status owned by teammate
HAS_ACTIVE=false
ACTIVE_TASK=""

for task_file in "$TASK_DIR"/*.json; do
  [[ -f "$task_file" ]] || continue

  if command -v jq &>/dev/null; then
    STATUS=$(jq -r '.status // ""' "$task_file" 2>/dev/null || echo "")
    OWNER=$(jq -r '.owner // ""' "$task_file" 2>/dev/null || echo "")
    SUBJECT=$(jq -r '.subject // ""' "$task_file" 2>/dev/null || echo "")
  else
    STATUS=$(grep -oP '"status"\s*:\s*"\K[^"]+' "$task_file" 2>/dev/null || echo "")
    OWNER=$(grep -oP '"owner"\s*:\s*"\K[^"]+' "$task_file" 2>/dev/null || echo "")
    SUBJECT=$(grep -oP '"subject"\s*:\s*"\K[^"]+' "$task_file" 2>/dev/null || echo "")
  fi

  if [[ "$STATUS" == "in_progress" && "$OWNER" == "$TEAMMATE" ]]; then
    HAS_ACTIVE=true
    ACTIVE_TASK="$SUBJECT"
    break
  fi
done

if [[ "$HAS_ACTIVE" == true ]]; then
  # Increment retry counter
  echo "$((RETRY_COUNT + 1))" > "$RETRY_FILE" 2>/dev/null || true
  echo "Task still in progress: \"${ACTIVE_TASK}\". Continue working on the task before going idle." >&2
  exit 2
fi

# No active tasks — legitimate idle, reset counter
rm -f "$RETRY_FILE" 2>/dev/null || true
exit 0
