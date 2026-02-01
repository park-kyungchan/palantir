#!/bin/bash
#=============================================================================
# Pipeline Order Gate
# Version: 1.0.0
#
# Purpose: Warn when E2E Pipeline order is violated
# Trigger: PreToolUse (Skill) - When skill invocation detected
#
# Expected Order:
#   /clarify → /research → /planning → /orchestrate → /assign → /worker → /collect → /synthesis
#
# Logic:
#   1. Track skill execution in session
#   2. If skill is called out of order
#   3. WARN (not block) with pipeline guidance
#
# Note: Warning only - allows flexibility for urgent situations
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Configuration
#=============================================================================
readonly SKILL_TRACKING_FILE="${AGENT_TMP_DIR}/skill_pipeline.log"

# Pipeline order (lower = earlier)
declare -A SKILL_ORDER=(
    ["clarify"]=1
    ["research"]=2
    ["planning"]=3
    ["orchestrate"]=4
    ["assign"]=5
    ["worker"]=6
    ["collect"]=7
    ["synthesis"]=8
)

# Prerequisites for each skill
declare -A SKILL_PREREQS=(
    ["research"]="clarify"
    ["planning"]="research"
    ["orchestrate"]="planning"
    ["assign"]="orchestrate"
    ["worker"]="assign"
    ["collect"]="worker"
    ["synthesis"]="collect"
)

#=============================================================================
# Helper Functions
#=============================================================================

# Check if prerequisite skill was executed
has_executed_prereq() {
    local prereq="$1"
    [[ -f "$SKILL_TRACKING_FILE" ]] || return 1
    grep -q "^${prereq}|" "$SKILL_TRACKING_FILE" 2>/dev/null
}

# Record skill execution
record_skill_execution() {
    local skill="$1"
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    echo "${skill}|${timestamp}" >> "$SKILL_TRACKING_FILE" 2>/dev/null || true
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

    # Only check for Skill tool
    if [[ "$tool_name" != "Skill" ]]; then
        output_allow
        exit 0
    fi

    # Parse skill name
    local skill_name
    skill_name=$(json_get '.tool_input.skill' "$input")
    skill_name="${skill_name#/}"  # Remove leading slash if present

    # Check if this is a pipeline skill
    if [[ -z "${SKILL_ORDER[$skill_name]:-}" ]]; then
        # Not a pipeline skill - allow
        output_allow
        exit 0
    fi

    # Check prerequisite
    local prereq="${SKILL_PREREQS[$skill_name]:-}"
    if [[ -n "$prereq" ]] && ! has_executed_prereq "$prereq"; then
        # Prerequisite not met - WARN only
        local guidance="E2E Pipeline order warning: /${prereq} should be executed before /${skill_name}. Order: /clarify → /research → /planning → /orchestrate → /assign → /worker → /collect → /synthesis"

        log_enforcement "pipeline-order-gate" "warn" "Missing prereq: $prereq" "Skill:$skill_name"

        # Record execution despite warning
        record_skill_execution "$skill_name"

        cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "additionalContext": "$guidance"
  }
}
EOF
        exit 0
    fi

    # Record skill execution
    record_skill_execution "$skill_name"

    output_allow
}

# Execute main
main

exit 0
