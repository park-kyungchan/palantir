#!/bin/bash
#=============================================================================
# Plan Mode Gate
# Version: 1.0.0
#
# Purpose: Block automatic EnterPlanMode usage
# Trigger: PreToolUse (EnterPlanMode)
#
# Logic:
#   1. If EnterPlanMode tool is called
#   2. DENY with instruction to use /planning skill instead
#
# Rationale:
#   - CLAUDE.md specifies: EnterPlanMode → NEVER use automatically
#   - Only when user explicitly requests "plan mode"
#   - Use /planning skill for structured planning instead
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Main Logic
#=============================================================================

main() {
    # Read JSON from stdin
    local input
    input=$(cat)

    # Parse tool name
    local tool_name
    tool_name=$(json_get '.tool_name' "$input")

    # Only check for EnterPlanMode
    if [[ "$tool_name" != "EnterPlanMode" ]]; then
        output_allow
        exit 0
    fi

    # DENY: Use /planning skill instead
    local reason="EnterPlanMode Blocked"
    local guidance="Automatic EnterPlanMode is disabled. Use the /planning skill instead. Only allowed when user explicitly requests 'plan mode'."

    log_enforcement "plan-mode-gate" "deny" "$reason" "$tool_name"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
