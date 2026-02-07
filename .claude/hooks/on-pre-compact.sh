#!/bin/bash
# Hook: PreCompact — Context compaction 전 상태 보존
# Critical for DIA Enforcement: saves orchestration state before context loss

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] PRE_COMPACT | Saving orchestration state before compaction" >> "$LOG_DIR/compact-events.log"

# Save current task list state snapshot
if command -v jq &>/dev/null; then
  TASK_DIR=$(find /home/palantir/.claude/tasks/ -maxdepth 1 -type d ! -name tasks 2>/dev/null | head -1)
  if [ -n "$TASK_DIR" ]; then
    SNAPSHOT_FILE="$LOG_DIR/pre-compact-tasks-$(date '+%s').json"
    echo "[" > "$SNAPSHOT_FILE"
    first=true
    for f in "$TASK_DIR"/*.json; do
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
fi

exit 0
