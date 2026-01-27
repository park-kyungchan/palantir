#!/usr/bin/env bash
# planning-subagent-stop.sh - SubagentStop Hook for /planning Skill
#
# Triggers: SubagentStop event when parallel Plan agents complete
# Purpose:
#   1. Collect L1 output from completed Plan subagent
#   2. Track component-level plan completion
#   3. Prepare for plan document merge
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
LOG_FILE=".agent/logs/planning-subagent-stop.log"
AGGREGATION_DIR=".agent/tmp/planning-aggregation"

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

    log "INFO" "SubagentStop hook triggered for planning"

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

    log "INFO" "Processing Plan subagent: ${agent_id}"

    # Extract tool_result if available (L1 output from subagent)
    local tool_result
    tool_result=$(echo "$input" | jq -r '.tool_result // empty')

    if [[ -n "$tool_result" ]]; then
        # Save L1 output to aggregation directory
        local output_file="${AGGREGATION_DIR}/${agent_id}.json"
        echo "$tool_result" > "$output_file"
        log "INFO" "Saved Plan subagent output to: ${output_file}"
    fi

    # Count completed subagents
    local completed_count
    completed_count=$(find "$AGGREGATION_DIR" -name "*.json" -type f 2>/dev/null | wc -l)

    log "INFO" "Plan subagent collection complete. Total collected: ${completed_count}"

    # Return success
    cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "planning-subagent-collect",
        "agent_id": "${agent_id}",
        "status": "collected",
        "total_collected": ${completed_count}
    }
}
EOF
}

# Run main
main "$@"
