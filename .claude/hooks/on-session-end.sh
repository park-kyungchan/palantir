#!/usr/bin/env bash
# OPT-08: SessionEnd cleanup — remove session-scoped temp files
# Event: SessionEnd (clear, logout, prompt_input_exit, other)
# Purpose: Clean up SRC change logs and stale hook temp files
# Output: None (silent, no additionalContext)

set -euo pipefail

# Read session_id from stdin JSON
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)

# Archive pipeline state to dashboard sessions
STATE_FILE="/tmp/claude-pipeline-state.json"
SESSIONS_DIR="$HOME/.claude/dashboard/sessions"
if [[ -f "$STATE_FILE" ]]; then
  mkdir -p "$SESSIONS_DIR"
  SESSION_DATE=$(date -u +%Y%m%d-%H%M%S)
  ARCHIVE_NAME="session-${SESSION_ID:-unknown}-${SESSION_DATE}.json"
  cp "$STATE_FILE" "$SESSIONS_DIR/$ARCHIVE_NAME"
  rm -f "$STATE_FILE"
fi

# Clean up SRC change logs
rm -f /tmp/src-changes-*.log 2>/dev/null
rm -f /tmp/src-changes-*.log.processed 2>/dev/null
rm -f /tmp/src-failures-*.log 2>/dev/null
rm -f /tmp/src-impact-*.md 2>/dev/null

# Clean up any stale hook temp files
rm -rf /tmp/claude-hooks/ 2>/dev/null
rm -f /tmp/claude-pipeline-state.json 2>/dev/null

exit 0
