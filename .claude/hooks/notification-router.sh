#!/bin/bash
#=============================================================================
# Notification Router Hook
# Version: 1.0.0
#
# Purpose: Route and log notifications by type
# Trigger: Notification (when Claude Code sends a notification)
#
# Input (stdin JSON):
#   - session_id, cwd, hook_event_name
#   - message: notification message
#   - title: notification title (optional)
#   - notification_type: permission_prompt|idle_prompt|auth_success|elicitation_dialog
#
# Output:
#   - .agent/logs/notifications.log (all notifications)
#   - Notification hooks cannot block
#
# Changes in v1.0.0:
#   - Initial implementation
#   - Type-based routing and logging
#=============================================================================

set -euo pipefail

#=============================================================================
# Fail-Open Error Handler
#=============================================================================
_fail_open() {
    echo '{}'
    exit 0
}
trap '_fail_open' ERR

#=============================================================================
# Configuration
#=============================================================================
readonly HOOK_NAME="notification-router"
readonly HOOK_VERSION="1.0.0"
readonly WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-/home/palantir}"
readonly LOG_DIR="${WORKSPACE_ROOT}/.agent/logs"
readonly LOG_FILE="${LOG_DIR}/notifications.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR" 2>/dev/null || true

#=============================================================================
# JSON Helpers
#=============================================================================
HAS_JQ=false
if command -v jq &>/dev/null; then
    HAS_JQ=true
fi

json_extract() {
    local field="$1"
    local input="$2"
    if $HAS_JQ; then
        echo "$input" | jq -r "$field // empty" 2>/dev/null || echo ""
    else
        echo "$input" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    keys = '$field'.strip('.').split('.')
    val = data
    for k in keys:
        val = val.get(k, '')
        if val == '': break
    print(val if val else '')
except:
    print('')
" 2>/dev/null || echo ""
    fi
}

#=============================================================================
# Main Logic
#=============================================================================
main() {
    # Read JSON from stdin
    local input
    input=$(cat 2>/dev/null || echo '{}')

    # Parse fields
    local notification_type message title session_id
    notification_type=$(json_extract '.notification_type' "$input")
    message=$(json_extract '.message' "$input")
    title=$(json_extract '.title' "$input")
    session_id=$(json_extract '.session_id' "$input")

    # Timestamp
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Truncate message for log (max 150 chars)
    local message_short="${message:0:150}"

    # Log notification
    echo "[${timestamp}] NOTIFY [${notification_type:-unknown}]: ${title:+${title} - }${message_short} (session: ${session_id:-unknown})" >> "$LOG_FILE" 2>/dev/null || true

    # Output empty JSON (Notification cannot block)
    echo '{}'
}

main
exit 0
