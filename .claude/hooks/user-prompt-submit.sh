#!/bin/bash
#=============================================================================
# UserPromptSubmit Hook
# Version: 1.0.0
#
# Purpose: Inject active workload context when user submits a prompt
# Trigger: UserPromptSubmit (before Claude processes the prompt)
#
# Input (stdin JSON):
#   - session_id, cwd, hook_event_name
#   - prompt: user's submitted prompt text
#
# Output:
#   - additionalContext with active workload info (slug, skill, phase)
#   - Does NOT block prompts
#
# Changes in v1.0.0:
#   - Initial implementation
#   - Active workload context injection
#   - Lightweight (no heavy processing)
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
readonly HOOK_NAME="user-prompt-submit"
readonly HOOK_VERSION="1.0.0"
readonly WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-/home/palantir}"
readonly WORKLOAD_FILE="${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml"

#=============================================================================
# Main Logic
#=============================================================================
main() {
    # Read JSON from stdin
    local input
    input=$(cat 2>/dev/null || echo '{}')

    # Check if active workload exists
    if [[ ! -f "$WORKLOAD_FILE" ]]; then
        echo '{}'
        exit 0
    fi

    # Extract workload info
    local slug skill phase
    slug=$(grep -E '^slug:' "$WORKLOAD_FILE" 2>/dev/null | sed 's/slug: *//' | tr -d '"' || echo "")
    skill=$(grep -E '^current_skill:' "$WORKLOAD_FILE" 2>/dev/null | sed 's/current_skill: *//' | tr -d '"' || echo "")
    phase=$(grep -E '^current_phase:' "$WORKLOAD_FILE" 2>/dev/null | sed 's/current_phase: *//' | tr -d '"' || echo "")

    # If no active workload, pass through
    if [[ -z "$slug" ]]; then
        echo '{}'
        exit 0
    fi

    # Build context string
    local context="[Active Workload] slug: ${slug}"
    if [[ -n "$skill" ]]; then
        context+=", skill: ${skill}"
    fi
    if [[ -n "$phase" ]]; then
        context+=", phase: ${phase}"
    fi
    context+=". Output dir: .agent/prompts/${slug}/"

    # Return additionalContext
    if command -v jq &>/dev/null; then
        jq -n --arg ctx "$context" \
            '{hookSpecificOutput: {hookEventName: "UserPromptSubmit", additionalContext: $ctx}}'
    else
        # Safe JSON escape
        context="${context//\"/\\\"}"
        echo "{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"${context}\"}}"
    fi
}

main
exit 0
