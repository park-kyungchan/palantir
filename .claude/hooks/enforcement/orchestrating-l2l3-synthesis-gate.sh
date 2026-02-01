#!/bin/bash
#=============================================================================
# Orchestrating L2/L3 Synthesis Gate
# Version: 1.0.0
#
# Purpose: Enforce L2→L3 progressive synthesis BEFORE orchestration
# Trigger: PreToolUse (TaskCreate) - When creating orchestration tasks
#
# =============================================================================
# WHY THIS IS CRITICAL (Design Rationale)
# =============================================================================
#
# Main Agent MUST perform only the Orchestrator-Role.
#
# Problem: Orchestrating based only on L1 summaries causes:
#   1. Task allocation without holistic context → inter-task inconsistency
#   2. Missing details → incorrect dependency chain configuration
#   3. Quality degradation and rework cycles
#
# Solution: Enforce L2→L3 Progressive Synthesis
#   1. Read ALL L2 outputs → Horizontal Analysis (cross-agent synthesis)
#   2. Read ALL L3 outputs → Vertical Analysis (deep insights)
#   3. Achieve holistic context → Then proceed with sub-task orchestration
#
# Without this enforcement:
#   - "Missing the forest for the trees" situation occurs
#   - Cannot understand how Task A's results impact Task B
#   - Dependency chain errors → Parallel execution failures
#
# =============================================================================
# Logic:
#   1. If TaskCreate is called (orchestration action)
#   2. AND active workload has agent outputs (L2/L3 files)
#   3. AND those L2/L3 files haven't been read
#   4. THEN DENY with synthesis instruction
#
# Exceptions:
#   - [PERMANENT] Context Check task itself
#   - No active workload
#   - No agent outputs exist yet (first orchestration)
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Configuration
#=============================================================================
readonly L2L3_PATTERNS=(
    'l2_detailed'
    'l3_synthesis'
    '_l2.md'
    '_l3.md'
    'L2_'
    'L3_'
)

#=============================================================================
# Helper Functions
#=============================================================================

# Check if there are L2/L3 output files in current workload
get_unread_l2l3_files() {
    local slug="$1"
    local unread_files=""
    local workload_dir="${WORKSPACE_ROOT}/.agent/prompts/${slug}"

    [[ -d "$workload_dir" ]] || return 0

    # Find L2/L3 files in workload directory
    local l2l3_files
    l2l3_files=$(find "$workload_dir" -type f \( -name "*l2*" -o -name "*l3*" -o -name "*L2*" -o -name "*L3*" \) 2>/dev/null | head -20)

    [[ -z "$l2l3_files" ]] && return 0

    # Check which files haven't been read
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        if ! grep -qF "$file" "$READ_TRACKING_FILE" 2>/dev/null; then
            unread_files="${unread_files}${file}\n"
        fi
    done <<< "$l2l3_files"

    echo -e "$unread_files" | grep -v '^$' | head -5
}

# Check if task is a PERMANENT context check
is_permanent_task() {
    local subject="$1"
    echo "$subject" | grep -qiE '\[PERMANENT\]|Context.*Check|context.*recovery'
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

    # Only check for TaskCreate
    if [[ "$tool_name" != "TaskCreate" ]]; then
        output_allow
        exit 0
    fi

    # Parse task details
    local subject description
    subject=$(json_get '.tool_input.subject' "$input")
    description=$(json_get '.tool_input.description' "$input")

    # Exception: [PERMANENT] tasks are always allowed
    if is_permanent_task "$subject"; then
        output_allow
        exit 0
    fi

    # Check if active workload exists
    if ! has_active_workload; then
        output_allow
        exit 0
    fi

    # Get workload slug
    local slug
    slug=$(get_workload_slug)

    [[ -z "$slug" ]] && { output_allow; exit 0; }

    # Get unread L2/L3 files
    local unread_files
    unread_files=$(get_unread_l2l3_files "$slug")

    # If no L2/L3 files or all read - allow
    if [[ -z "$unread_files" ]]; then
        output_allow
        exit 0
    fi

    # DENY: Must read L2/L3 before orchestrating
    local reason="L2/L3 Synthesis Required Before Orchestrating"
    local file_list
    file_list=$(echo "$unread_files" | tr '\n' ', ' | sed 's/,$//')

    local guidance="Main Agent MUST read ALL L2/L3 outputs before performing Orchestrator-Role.

[WHY]
Correct orchestration of sub-tasks is only possible after achieving holistic context awareness.
L1 summaries alone cannot accurately capture inter-task dependencies, details, and impact scope.

[WHAT TO DO]
1. Read ALL L2 outputs (Horizontal Analysis - cross-agent synthesis)
2. Read ALL L3 outputs (Vertical Analysis - deep insights acquisition)
3. Proceed with TaskCreate only after holistic context is achieved

[UNREAD FILES]
${file_list}"

    log_enforcement "orchestrating-l2l3-synthesis-gate" "deny" "$reason" "TaskCreate:$subject"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
