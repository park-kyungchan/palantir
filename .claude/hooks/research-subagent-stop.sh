#!/usr/bin/env bash
# research-subagent-stop.sh - SubagentStop Hook for /research Skill
#
# Triggers: SubagentStop event when parallel Explore agents complete
# Purpose:
#   1. Collect L1 output from completed subagent
#   2. Aggregate results for final research report
#   3. Track parallel agent completion count
#
# Input (JSON stdin):
#   - hook_event_name: "SubagentStop"
#   - agent_id: subagent ID
#   - session_id: parent session
#   - tool_result: subagent output
#
# Output (JSON stdout):
#   - continue: true (always continue)
#   - hookSpecificOutput: collection status

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
LOG_FILE=".agent/logs/research-subagent-stop.log"
AGGREGATION_DIR=".agent/tmp/research-aggregation"

# ============================================================================
# LOGGING
# ============================================================================
log() {
    local level="$1"
    local msg="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[${timestamp}] [${level}] ${msg}" >> "$LOG_FILE"
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$AGGREGATION_DIR"

    # Read hook input
    local input
    input=$(cat)

    log "INFO" "SubagentStop hook triggered for research"

    # Extract agent info
    local agent_id
    agent_id=$(echo "$input" | jq -r '.agent_id // "unknown"')

    local hook_event
    hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

    if [[ "$hook_event" != "SubagentStop" ]]; then
        log "WARN" "Unexpected event: ${hook_event}"
        echo '{"continue": true}'
        return 0
    fi

    log "INFO" "Processing subagent: ${agent_id}"

    # Extract tool_result if available (L1 output from subagent)
    local tool_result
    tool_result=$(echo "$input" | jq -r '.tool_result // empty')

    if [[ -n "$tool_result" ]]; then
        # Save L1 output to aggregation directory
        local output_file="${AGGREGATION_DIR}/${agent_id}.json"
        echo "$tool_result" > "$output_file"
        log "INFO" "Saved subagent output to: ${output_file}"
    fi

    # Count completed subagents
    local completed_count
    completed_count=$(find "$AGGREGATION_DIR" -name "*.json" -type f 2>/dev/null | wc -l)

    log "INFO" "Subagent collection complete. Total collected: ${completed_count}"

    # Return success
    cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "research-subagent-collect",
        "agent_id": "${agent_id}",
        "status": "collected",
        "total_collected": ${completed_count}
    }
}
EOF
}

# Run main
main "$@"
