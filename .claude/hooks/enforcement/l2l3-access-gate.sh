#!/bin/bash
#=============================================================================
# L2/L3 Access Gate
# Version: 1.1.0
#
# Purpose: Enforce reading L2/L3 files before Edit/Write operations
# Trigger: PreToolUse (Edit|Write)
#
# Logic:
#   1. Check if tool is Edit or Write
#   2. Check for exception paths (.claude/, .agent/)
#   3. Check for excluded file types (is_excluded_file)
#   4. If has_active_workload() is true
#   5. AND has_read_l2l3() is false
#   6. THEN DENY with L2/L3 access instruction
#
# Exceptions:
#   - Files within .claude/ directory (configuration files)
#   - Files within .agent/ directory (internal agent files)
#   - Excluded file types: .md, .json, .yaml, .yml, .txt, README, LICENSE
#   - No active workload present
#
# Changes in 1.1.0:
#   - Added trap for cleanup on error
#   - Enhanced exception documentation
#   - Improved error handling
#=============================================================================

set -euo pipefail

# Error cleanup trap - allow on script errors (fail-open)
trap 'output_allow; exit 0' ERR

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

    # Only check for Edit, Write tools
    case "$tool_name" in
        Edit|Write)
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

    # Exception: Excluded file types (.md, .json, .yaml, etc.)
    if is_excluded_file "$file_path"; then
        output_allow
        exit 0
    fi

    # Check if active workload exists
    if ! has_active_workload; then
        # No active workload - allow
        output_allow
        exit 0
    fi

    # Check if L2/L3 files have been read
    if has_read_l2l3; then
        # Already read - allow
        output_allow
        exit 0
    fi

    # DENY: L2/L3 access required
    local slug
    slug=$(get_workload_slug)

    local reason="L2/L3 Access Required"
    local guidance="You must read L2/L3 files before Edit/Write. Slug: ${slug}. Check: .agent/prompts/${slug}/research/ for L2/L3 files."

    log_enforcement "l2l3-access-gate" "deny" "$reason" "$tool_name"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
