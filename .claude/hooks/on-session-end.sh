#!/usr/bin/env bash
# OPT-08: SessionEnd cleanup — remove session-scoped temp files
# Event: SessionEnd (clear, logout, prompt_input_exit, other)
# Purpose: Clean up SRC change logs and stale hook temp files
# Output: None (silent, no additionalContext)

set -euo pipefail

# Read session_id from stdin JSON
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)

# Clean up SRC change logs
rm -f /tmp/src-changes-*.log 2>/dev/null
rm -f /tmp/src-changes-*.log.processed 2>/dev/null
rm -f /tmp/src-failures-*.log 2>/dev/null

# Clean up any stale hook temp files
rm -rf /tmp/claude-hooks/ 2>/dev/null

exit 0
