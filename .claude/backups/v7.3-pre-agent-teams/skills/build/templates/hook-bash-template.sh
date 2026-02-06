#!/bin/bash
# ============================================================================
# Hook: {{hook_name}}
# Event: {{event_type}}
# Matcher: {{matcher}}
# Created: {{timestamp}}
# ============================================================================
#
# ENVIRONMENT VARIABLES:
#   $CC_HOOK_EVENT           - Event type (PreToolUse, PostToolUse, etc.)
#   $CC_TOOL_NAME            - Tool name (Bash, Read, Edit, etc.)
#   $CC_TOOL_INPUT           - Tool input as JSON string
#   $CC_TOOL_OUTPUT          - Tool output as JSON (PostToolUse only)
#   $CC_WORKING_DIRECTORY    - Current working directory
#
# EXIT CODES:
#   0 = Allow / Success
#   1 = Block (PreToolUse only)
#   2 = Error
#
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

LOG_FILE="${CC_WORKING_DIRECTORY}/.agent/logs/{{hook_name}}.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

log_info() {
    echo "[INFO] $TIMESTAMP | $*" >> "$LOG_FILE"
}

log_error() {
    echo "[ERROR] $TIMESTAMP | $*" >> "$LOG_FILE"
}

block_with_message() {
    local message="$1"
    echo "❌ Blocked: $message"
    log_error "Blocked: $message"
    exit 1
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

main() {
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"

    # Parse tool input
    local tool_name="${CC_TOOL_NAME:-unknown}"
    local tool_input="${CC_TOOL_INPUT:-{}}"

    # Log hook execution
    log_info "Hook triggered for: $tool_name"

    # TODO(human): Implement your hook logic here
    # Example validation:
    #
    # if [[ "$tool_name" == "Bash" ]]; then
    #     local command=$(echo "$tool_input" | jq -r '.command // ""')
    #     if [[ "$command" =~ rm\ -rf ]]; then
    #         block_with_message "Dangerous command pattern: rm -rf"
    #     fi
    # fi

    # Default: Allow
    exit 0
}

# ============================================================================
# ENTRY POINT
# ============================================================================

main "$@"
