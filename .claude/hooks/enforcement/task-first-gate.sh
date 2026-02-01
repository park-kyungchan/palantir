#!/bin/bash
#=============================================================================
# Task First Gate
# Version: 1.0.0
#
# Purpose: Enforce TaskCreate before complex source code modifications
# Trigger: PreToolUse (Edit|Write)
#
# Logic:
#   1. If file path is source code (.py, .ts, .js, .sh, etc.)
#   2. AND has_recent_task_create() is false
#   3. THEN DENY with TaskCreate instruction
#
# Exceptions:
#   - Files within .claude/ directory
#   - Files within .agent/ directory
#   - Test files (test_, _test.py, .test.ts, etc.)
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Helper Functions
#=============================================================================

# Check if file is source code
# Returns: 0 if source code, 1 if not
is_source_code() {
    local file_path="$1"
    local basename
    basename=$(basename "$file_path")

    # Source code extensions
    local extensions=(
        ".py"
        ".ts"
        ".tsx"
        ".js"
        ".jsx"
        ".sh"
        ".bash"
        ".go"
        ".rs"
        ".java"
        ".kt"
        ".scala"
        ".rb"
        ".php"
        ".c"
        ".cpp"
        ".h"
        ".hpp"
    )

    for ext in "${extensions[@]}"; do
        if [[ "$basename" == *"$ext" ]]; then
            return 0
        fi
    done

    return 1
}

# Check if file is a test file
# Returns: 0 if test file, 1 if not
is_test_file() {
    local file_path="$1"
    local basename
    basename=$(basename "$file_path")

    # Test file patterns
    local patterns=(
        "test_"
        "_test."
        ".test."
        ".spec."
        "_spec."
        "Test."
        "Tests."
        "__tests__"
    )

    for pattern in "${patterns[@]}"; do
        if [[ "$basename" == *"$pattern"* ]] || [[ "$file_path" == *"$pattern"* ]]; then
            return 0
        fi
    done

    # Test directories
    if [[ "$file_path" == *"/tests/"* ]] || [[ "$file_path" == *"/test/"* ]]; then
        return 0
    fi

    return 1
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

    # Check if file is source code
    if ! is_source_code "$file_path"; then
        # Not source code - allow
        output_allow
        exit 0
    fi

    # Exception: Test files are allowed without TaskCreate
    if is_test_file "$file_path"; then
        output_allow
        exit 0
    fi

    # Check if TaskCreate was called recently
    if has_recent_task_create; then
        # Task exists - allow
        output_allow
        exit 0
    fi

    # DENY: TaskCreate required
    local reason="TaskCreate Required"
    local guidance="소스 코드 수정 전 TaskCreate로 작업을 등록해야 합니다. File: ${file_path}. Use TaskCreate tool first."

    log_enforcement "task-first-gate" "deny" "$reason" "$tool_name"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
