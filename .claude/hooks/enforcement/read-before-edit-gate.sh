#!/bin/bash
#=============================================================================
# Read Before Edit Gate
# Version: 1.0.0
#
# Purpose: Enforce reading a file before editing it
# Trigger: PreToolUse (Edit|Write)
#
# Logic:
#   1. If Edit/Write tool is called for a source code file
#   2. AND that file hasn't been Read in recent session
#   3. THEN DENY with instruction to read first
#
# Exceptions:
#   - Files within .claude/ directory (config files)
#   - Files within .agent/ directory (outputs)
#   - New files being created (Write only, file doesn't exist)
#   - Simple files: .md, .txt, .json, .yaml, .yml
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Configuration
#=============================================================================
readonly SOURCE_CODE_PATTERNS='\.py$|\.js$|\.ts$|\.tsx$|\.jsx$|\.go$|\.rs$|\.java$|\.c$|\.cpp$|\.h$|\.hpp$|\.sh$|\.rb$|\.php$'

#=============================================================================
# Helper Functions
#=============================================================================

# Check if file has been read in this session
has_read_file() {
    local file_path="$1"
    [[ -f "$READ_TRACKING_FILE" ]] || return 1
    grep -qF "$file_path" "$READ_TRACKING_FILE" 2>/dev/null
}

# Check if file is source code (needs read-before-edit)
is_source_code() {
    local file_path="$1"
    echo "$file_path" | grep -qE "$SOURCE_CODE_PATTERNS"
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

    # Only check for Edit, Write tools
    case "$tool_name" in
        Edit|Write)
            ;;
        *)
            output_allow
            exit 0
            ;;
    esac

    # Empty path - allow (will fail naturally)
    [[ -z "$file_path" ]] && { output_allow; exit 0; }

    # Exception: .claude/ and .agent/ directories
    if is_excluded_file "$file_path"; then
        output_allow
        exit 0
    fi

    # Exception: Not source code (simple config files)
    if ! is_source_code "$file_path"; then
        output_allow
        exit 0
    fi

    # Exception: Write to new file (doesn't exist yet)
    if [[ "$tool_name" == "Write" ]] && [[ ! -f "$file_path" ]]; then
        output_allow
        exit 0
    fi

    # Check if file has been read
    if has_read_file "$file_path"; then
        output_allow
        exit 0
    fi

    # DENY: Must read file first
    local reason="Read Before Edit Required"
    local guidance="You must read the source file before modifying it. Run: Read ${file_path}"

    log_enforcement "read-before-edit-gate" "deny" "$reason" "$tool_name:$file_path"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
