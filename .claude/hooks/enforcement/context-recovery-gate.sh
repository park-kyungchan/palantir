#!/bin/bash
#=============================================================================
# Context Recovery Gate
# Version: 1.0.0
#
# Purpose: Enforce reading _active_workload.yaml after Compact recovery
# Trigger: PreToolUse (Edit|Write|Task)
#
# Logic:
#   1. If _active_workload.yaml exists
#   2. AND recent_reads.log doesn't contain _active_workload.yaml
#   3. THEN DENY with context recovery instruction
#
# Exceptions:
#   - Files within .claude/ directory
#   - Files within .agent/ directory
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

    # Parse tool name and file path
    local tool_name
    local file_path
    tool_name=$(json_get '.tool_name' "$input")
    file_path=$(json_get '.tool_input.file_path' "$input")

    # Only check for Edit, Write, Task tools
    case "$tool_name" in
        Edit|Write|Task|TaskCreate|TaskUpdate)
            ;;
        *)
            # Not applicable - allow
            output_allow
            exit 0
            ;;
    esac

    # Exception: .claude/ and .agent/ directories are always allowed
    if [[ "$file_path" == *".claude/"* ]] || [[ "$file_path" == *".agent/"* ]]; then
        output_allow
        exit 0
    fi

    # Check if active workload exists
    if ! has_active_workload; then
        # No active workload - allow
        output_allow
        exit 0
    fi

    # Check if _active_workload.yaml has been read in this session
    if has_read_active_workload; then
        # Already read - allow
        output_allow
        exit 0
    fi

    # DENY: Context recovery required
    local reason="Context Recovery Required"
    local guidance="Post-Compact Recovery: _active_workload.yaml를 먼저 읽어야 합니다. Run: Read .agent/prompts/_active_workload.yaml"

    log_enforcement "context-recovery-gate" "deny" "$reason" "$tool_name"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
