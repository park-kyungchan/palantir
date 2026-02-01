#!/bin/bash
#=============================================================================
# Workload Path Gate
# Version: 1.0.0
#
# Purpose: Enforce output path compliance with workload directory
# Trigger: PreToolUse (Write)
#
# Logic:
#   1. If active workload exists (_active_workload.yaml)
#   2. AND Write is to .agent/ directory
#   3. AND path doesn't match current workload slug
#   4. THEN DENY with correct path guidance
#
# Expected Path Pattern:
#   .agent/prompts/{current-slug}/**
#
# Exceptions:
#   - .agent/tmp/ (temporary files)
#   - .agent/logs/ (log files)
#   - Files outside .agent/ directory
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Helper Functions
#=============================================================================

# Check if path is within .agent/prompts/
is_prompts_path() {
    local path="$1"
    [[ "$path" == *".agent/prompts/"* ]]
}

# Check if path is in exception directories
is_exception_path() {
    local path="$1"
    case "$path" in
        *".agent/tmp/"*|*".agent/logs/"*|*".agent/builds/"*)
            return 0
            ;;
    esac
    return 1
}

# Check if path matches workload slug
matches_workload_slug() {
    local path="$1"
    local slug="$2"
    [[ "$path" == *".agent/prompts/${slug}/"* ]]
}

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

    # Only check for Write tool
    if [[ "$tool_name" != "Write" ]]; then
        output_allow
        exit 0
    fi

    # Empty path - allow (will fail naturally)
    [[ -z "$file_path" ]] && { output_allow; exit 0; }

    # Not writing to .agent/ directory - allow
    if [[ "$file_path" != *".agent/"* ]]; then
        output_allow
        exit 0
    fi

    # Exception directories - allow
    if is_exception_path "$file_path"; then
        output_allow
        exit 0
    fi

    # Not writing to .agent/prompts/ - allow (other .agent dirs)
    if ! is_prompts_path "$file_path"; then
        output_allow
        exit 0
    fi

    # Check if active workload exists
    if ! has_active_workload; then
        # No active workload - allow (first time setup)
        output_allow
        exit 0
    fi

    # Get current workload slug
    local slug
    slug=$(get_workload_slug)

    # Empty slug - allow
    [[ -z "$slug" ]] && { output_allow; exit 0; }

    # Check if path matches workload slug
    if matches_workload_slug "$file_path" "$slug"; then
        output_allow
        exit 0
    fi

    # DENY: Wrong workload path
    local reason="Workload Path Violation"
    local guidance="Output must be written to the active workload directory (${slug}). Correct path: .agent/prompts/${slug}/"

    log_enforcement "workload-path-gate" "deny" "$reason" "Write:$file_path (expected: $slug)"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
