#!/bin/bash
#=============================================================================
# PermissionRequest Audit Hook
# Version: 1.0.0
#
# Purpose: Audit permission requests and log for compliance tracking
# Trigger: PermissionRequest (when a permission dialog appears)
#
# Input (stdin JSON):
#   - session_id, cwd, hook_event_name
#   - tool_name: tool requesting permission
#   - tool_input: tool input parameters
#   - permission_suggestions: array of always-allow options
#
# Output:
#   - .agent/logs/permission_audit.log (audit trail)
#   - Logging only, does not auto-approve/deny (user decides)
#
# Changes in v1.0.0:
#   - Initial implementation
#   - Audit logging for all permission requests
#   - No auto-approval (safety first)
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
readonly HOOK_NAME="permission-request-handler"
readonly HOOK_VERSION="1.0.0"
readonly WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-/home/palantir}"
readonly LOG_DIR="${WORKSPACE_ROOT}/.agent/logs"
readonly LOG_FILE="${LOG_DIR}/permission_audit.log"

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
    local tool_name session_id
    tool_name=$(json_extract '.tool_name' "$input")
    session_id=$(json_extract '.session_id' "$input")

    # Extract a summary of tool_input (first 100 chars)
    local tool_input_summary
    if $HAS_JQ; then
        tool_input_summary=$(echo "$input" | jq -c '.tool_input // {}' 2>/dev/null | head -c 100 || echo "{}")
    else
        tool_input_summary=$(echo "$input" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(json.dumps(data.get('tool_input', {}))[:100])
except:
    print('{}')
" 2>/dev/null || echo "{}")
    fi

    # Timestamp
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Log the permission request
    echo "[${timestamp}] PERM_REQ ${tool_name:-unknown}: ${tool_input_summary} (session: ${session_id:-unknown})" >> "$LOG_FILE" 2>/dev/null || true

    # Output empty JSON - let user decide (no auto-approve/deny)
    echo '{}'
}

main
exit 0
