#!/bin/bash
#=============================================================================
# Sequential Thinking Gate
# Version: 1.0.0
#
# Purpose: Enforce sequential-thinking MCP tool for complex operations
# Trigger: PreToolUse (TaskCreate) - Task decomposition is critical
#
# Logic:
#   1. If TaskCreate is called (task decomposition)
#   2. AND metadata indicates complex task (5+ steps, dependencies)
#   3. AND sequential-thinking hasn't been used recently
#   4. THEN WARN (not block) with instruction
#
# Rationale:
#   - Task decomposition with Parallel Agents Delegation is critical workflow
#   - Dependency chains require careful reasoning
#   - Sequential thinking helps avoid missed dependencies
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Configuration
#=============================================================================
readonly SEQ_THINKING_TRACKING_FILE="${AGENT_TMP_DIR}/sequential_thinking.log"
readonly SEQ_THINKING_TIMEOUT_SECONDS=600  # 10 minutes

#=============================================================================
# Helper Functions
#=============================================================================

# Check if sequential-thinking was used recently
has_recent_sequential_thinking() {
    [[ -f "$SEQ_THINKING_TRACKING_FILE" ]] || return 1

    local last_use
    last_use=$(tail -1 "$SEQ_THINKING_TRACKING_FILE" 2>/dev/null | cut -d'|' -f1)
    [[ -n "$last_use" ]] || return 1

    local current_time last_epoch
    current_time=$(date +%s)
    last_epoch=$(date -d "$last_use" +%s 2>/dev/null) || return 1

    local diff=$((current_time - last_epoch))
    [[ $diff -le $SEQ_THINKING_TIMEOUT_SECONDS ]]
}

# Check if task description indicates complexity
is_complex_task() {
    local description="$1"
    local subject="$2"

    # Keywords indicating complexity
    if echo "$description $subject" | grep -qiE 'decompos|phase|parallel|depend|orchestrat|architect|refactor|migrat|integrat'; then
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

    # Parse tool name
    local tool_name
    tool_name=$(json_get '.tool_name' "$input")

    # Only check for TaskCreate (task decomposition)
    if [[ "$tool_name" != "TaskCreate" ]]; then
        output_allow
        exit 0
    fi

    # Parse task details
    local subject description
    subject=$(json_get '.tool_input.subject' "$input")
    description=$(json_get '.tool_input.description' "$input")

    # Check if this is a complex task
    if ! is_complex_task "$description" "$subject"; then
        output_allow
        exit 0
    fi

    # Check if sequential-thinking was used recently
    if has_recent_sequential_thinking; then
        output_allow
        exit 0
    fi

    # WARN: Sequential thinking recommended (not blocking)
    local guidance="Complex Task decomposition detected. Use mcp__sequential-thinking__sequentialthinking tool is recommended. Prevents missing dependencies in Parallel Agents Delegation workflow."

    log_enforcement "sequential-thinking-gate" "warn" "Complex task without sequential thinking" "$tool_name:$subject"

    # Output guidance but allow
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "$guidance"
  }
}
EOF
}

# Execute main
main

exit 0
