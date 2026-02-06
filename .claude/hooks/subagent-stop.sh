#!/bin/bash
#=============================================================================
# Subagent Stop Hook
# Version: 1.0.0
#
# Purpose: Log subagent completion with agent_type, agent_id, duration
# Trigger: SubagentStop (when a subagent finishes)
#
# Input (stdin JSON):
#   - session_id, cwd, hook_event_name
#   - agent_id: unique subagent identifier
#   - agent_type: agent type name (Explore, Plan, Bash, etc.)
#   - agent_transcript_path: path to subagent's transcript
#   - stop_hook_active: boolean
#
# Output:
#   - Log to .agent/logs/subagent_lifecycle.log
#   - No decision returned (logging only)
#
# Changes in v1.0.0:
#   - Initial implementation
#   - Matches subagent-start.sh pattern
#   - Lifecycle logging for duration tracking
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
readonly HOOK_NAME="subagent-stop"
readonly HOOK_VERSION="1.0.0"
readonly WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-/home/palantir}"
readonly LOG_DIR="${WORKSPACE_ROOT}/.agent/logs"
readonly LOG_FILE="${LOG_DIR}/subagent_lifecycle.log"

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
    local agent_id agent_type session_id stop_hook_active transcript_path
    agent_id=$(json_extract '.agent_id' "$input")
    agent_type=$(json_extract '.agent_type' "$input")
    session_id=$(json_extract '.session_id' "$input")
    stop_hook_active=$(json_extract '.stop_hook_active' "$input")
    transcript_path=$(json_extract '.agent_transcript_path' "$input")

    # Timestamp
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Log subagent completion
    echo "[${timestamp}] SubagentStop: ${agent_type:-unknown} (id: ${agent_id:-unknown}, session: ${session_id:-unknown}, stop_hook_active: ${stop_hook_active:-false})" >> "$LOG_FILE" 2>/dev/null || true

    # Output empty JSON (non-blocking, logging only)
    echo '{}'
}

main
exit 0
