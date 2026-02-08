#!/bin/bash
# Hook: PreCompact — Context compaction state preservation
# Saves orchestration state before context loss for recovery

INPUT=$(cat)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
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
  TASK_DIR=$(ls -td /home/palantir/.claude/tasks/*/ 2>/dev/null | head -1)
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

# H-2 Mitigation: Non-blocking WARNING for missing L1/L2 files
# Scans agent output directories to warn about unsaved work before compaction
if [ -n "${CLAUDE_CODE_TASK_LIST_ID:-}" ]; then
  TEAM_DIR="$LOG_DIR/$CLAUDE_CODE_TASK_LIST_ID"
else
  TEAM_DIR=$(ls -td "$LOG_DIR"/*/ 2>/dev/null | head -1)
fi
if [ -n "$TEAM_DIR" ] && [ -d "$TEAM_DIR" ]; then
  MISSING_AGENTS=""
  for agent_dir in "$TEAM_DIR"/phase-*/*/; do
    [ -d "$agent_dir" ] || continue
    agent_name=$(basename "$agent_dir")
    has_l1=$(ls "$agent_dir"/L1-index.yaml 2>/dev/null)
    has_l2=$(ls "$agent_dir"/L2-summary.md 2>/dev/null)
    if [ -z "$has_l1" ] || [ -z "$has_l2" ]; then
      MISSING_AGENTS="$MISSING_AGENTS $agent_name"
    fi
  done
  if [ -n "$MISSING_AGENTS" ]; then
    echo "[$TIMESTAMP] PRE_COMPACT | WARNING: Agents missing L1/L2 before compaction:$MISSING_AGENTS" >> "$LOG_DIR/compact-events.log"
  fi
fi

exit 0
