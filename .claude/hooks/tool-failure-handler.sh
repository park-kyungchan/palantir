#!/bin/bash
#=============================================================================
# PostToolUseFailure Handler Hook
# Version: 1.0.0
#
# Purpose: Log tool failures with error context for debugging
# Trigger: PostToolUseFailure (after a tool call fails)
#
# Input (stdin JSON):
#   - session_id, cwd, hook_event_name
#   - tool_name: failed tool name
#   - tool_input: tool input parameters
#   - tool_use_id: tool use ID
#   - error: error message string
#   - is_interrupt: boolean (user interruption)
#
# Output:
#   - .agent/logs/tool_failures.log (detailed log)
#   - additionalContext on repeated failures (same tool 3+ in 5 min)
#
# Changes in v1.0.0:
#   - Initial implementation
#   - Repeated failure pattern detection
#   - Context injection for Claude guidance
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
readonly HOOK_NAME="tool-failure-handler"
readonly HOOK_VERSION="1.0.0"
readonly WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-/home/palantir}"
readonly LOG_DIR="${WORKSPACE_ROOT}/.agent/logs"
readonly LOG_FILE="${LOG_DIR}/tool_failures.log"
readonly REPEAT_WINDOW_SECONDS=300  # 5 minutes
readonly REPEAT_THRESHOLD=3

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
# Repeated Failure Detection
#=============================================================================
check_repeated_failures() {
    local tool_name="$1"

    if [[ ! -f "$LOG_FILE" ]]; then
        echo "0"
        return
    fi

    # Count failures for this tool in the last N seconds
    local cutoff_time
    cutoff_time=$(date -u -d "-${REPEAT_WINDOW_SECONDS} seconds" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)

    local count
    count=$(grep -c "FAIL ${tool_name}:" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "$count"
}

#=============================================================================
# Main Logic
#=============================================================================
main() {
    # Read JSON from stdin
    local input
    input=$(cat 2>/dev/null || echo '{}')

    # Parse fields
    local tool_name error is_interrupt session_id tool_use_id
    tool_name=$(json_extract '.tool_name' "$input")
    error=$(json_extract '.error' "$input")
    is_interrupt=$(json_extract '.is_interrupt' "$input")
    session_id=$(json_extract '.session_id' "$input")
    tool_use_id=$(json_extract '.tool_use_id' "$input")

    # Timestamp
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Truncate error for log (max 200 chars)
    local error_short
    error_short="${error:0:200}"

    # Log the failure
    echo "[${timestamp}] FAIL ${tool_name:-unknown}: ${error_short} (interrupt: ${is_interrupt:-false}, id: ${tool_use_id:-unknown})" >> "$LOG_FILE" 2>/dev/null || true

    # Check for repeated failures
    local failure_count
    failure_count=$(check_repeated_failures "${tool_name:-unknown}")

    # If repeated failures detected, provide guidance
    if [[ "$failure_count" -ge "$REPEAT_THRESHOLD" ]]; then
        local context_msg="Tool '${tool_name}' has failed ${failure_count} times recently. Consider: 1) Using an alternative approach, 2) Checking prerequisites, 3) Reading error details carefully before retrying."

        if $HAS_JQ; then
            jq -n \
                --arg ctx "$context_msg" \
                '{
                    hookSpecificOutput: {
                        hookEventName: "PostToolUseFailure",
                        additionalContext: $ctx
                    }
                }'
        else
            echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUseFailure\",\"additionalContext\":\"${context_msg}\"}}"
        fi
    else
        echo '{}'
    fi
}

main
exit 0
