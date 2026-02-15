#!/usr/bin/env bash
# Hook: PreCompact — Context compaction state preservation
# Saves orchestration state before context loss for recovery

set -euo pipefail

INPUT=$(cat)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/tmp/claude-hooks"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] PRE_COMPACT | Saving orchestration state before compaction" >> "$LOG_DIR/compact-events.log"

# Save current task list state snapshot
if ! command -v jq &>/dev/null; then
  echo "[$TIMESTAMP] PRE_COMPACT | WARNING: jq not available, skipping task snapshot" >> "$LOG_DIR/compact-events.log"
  exit 0
fi

# Use CLAUDE_CODE_TASK_LIST_ID if available, otherwise find most recent
if [ -n "${CLAUDE_CODE_TASK_LIST_ID:-}" ]; then
  TASK_DIR="/home/palantir/.claude/tasks/$CLAUDE_CODE_TASK_LIST_ID/"
else
  TASK_DIR=""
  for d in /home/palantir/.claude/tasks/*/; do
    [ -d "$d" ] && TASK_DIR="$d" && break
  done
fi
if [ -n "$TASK_DIR" ]; then
  SNAPSHOT_FILE="$LOG_DIR/pre-compact-tasks-$(date '+%s').json"
  echo "[" > "$SNAPSHOT_FILE"
  first=true
  for f in "$TASK_DIR"*.json; do
    [ -f "$f" ] || continue
    if [ "$first" = true ]; then
      first=false
    else
      echo "," >> "$SNAPSHOT_FILE"
    fi
    cat "$f" >> "$SNAPSHOT_FILE"
  done
  echo "]" >> "$SNAPSHOT_FILE"
  echo "[$TIMESTAMP] PRE_COMPACT | Task snapshot saved: $SNAPSHOT_FILE" >> "$LOG_DIR/compact-events.log"
fi

exit 0
