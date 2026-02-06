#!/bin/bash
#=============================================================================
# Async Test Runner Hook (Template)
# Version: 1.0.0
#
# Purpose: Run tests in background after file changes
# Trigger: PostToolUse (Write|Edit) with async: true
#
# Input (stdin JSON):
#   - tool_name, tool_input (file_path, content, etc.)
#   - tool_response (success result)
#
# Output:
#   - systemMessage with test results (delivered on next turn)
#   - async: true means Claude does not wait for completion
#
# Changes in v1.0.0:
#   - Initial implementation
#   - Python and JS/TS test detection
#   - Async execution template
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
readonly HOOK_NAME="async-test-runner"
readonly HOOK_VERSION="1.0.0"
readonly WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-/home/palantir}"

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

    # Extract file path
    local file_path
    file_path=$(json_extract '.tool_input.file_path' "$input")

    # Only run tests for source files
    case "$file_path" in
        *.py)
            # Python: try pytest
            if command -v pytest &>/dev/null; then
                local result
                result=$(cd "$WORKSPACE_ROOT" && pytest --tb=short -q 2>&1 | tail -5) || true
                local exit_code=$?
                if [[ $exit_code -eq 0 ]]; then
                    echo "{\"systemMessage\": \"Tests passed after editing ${file_path}\"}"
                else
                    echo "{\"systemMessage\": \"Tests failed after editing ${file_path}: ${result:0:200}\"}"
                fi
            else
                echo '{}'
            fi
            ;;
        *.ts|*.js|*.tsx|*.jsx)
            # JavaScript/TypeScript: try npm test
            if [[ -f "${WORKSPACE_ROOT}/package.json" ]] && command -v npm &>/dev/null; then
                local result
                result=$(cd "$WORKSPACE_ROOT" && npm test 2>&1 | tail -5) || true
                local exit_code=$?
                if [[ $exit_code -eq 0 ]]; then
                    echo "{\"systemMessage\": \"Tests passed after editing ${file_path}\"}"
                else
                    echo "{\"systemMessage\": \"Tests failed after editing ${file_path}: ${result:0:200}\"}"
                fi
            else
                echo '{}'
            fi
            ;;
        *)
            # Not a testable source file
            echo '{}'
            ;;
    esac
}

main
exit 0
