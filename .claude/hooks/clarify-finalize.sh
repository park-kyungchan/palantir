#!/usr/bin/env bash
# clarify-finalize.sh - Stop Hook for /clarify Skill
#
# Triggers: Stop event when /clarify skill completes
# Purpose:
#   1. Finalize YAML log with status update
#   2. Record downstream_skills if routing occurred
#   3. Compute context_hash for integrity verification
#
# Input (JSON stdin):
#   - hook_event_name: "Stop"
#   - agent_id: skill agent ID
#   - agent_transcript_path: path to transcript
#
# Output (JSON stdout):
#   - continue: true (always continue)
#   - hookSpecificOutput: finalization summary

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
CLARIFY_LOG_DIR=".agent/clarify"
LOG_FILE=".agent/logs/clarify-finalize.log"

# ============================================================================
# LOGGING
# ============================================================================
log() {
    local level="$1"
    local msg="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[${timestamp}] [${level}] ${msg}" >> "$LOG_FILE"
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"

    # Read hook input
    local input
    input=$(cat)

    log "INFO" "Stop hook triggered"
    log "DEBUG" "Input: ${input}"

    # Extract hook event info
    local hook_event
    hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

    if [[ "$hook_event" != "Stop" ]]; then
        log "WARN" "Unexpected event: ${hook_event}"
        echo '{"continue": true}'
        return 0
    fi

    # Find the most recent in-progress clarify log
    local latest_log
    latest_log=$(find "$CLARIFY_LOG_DIR" -name "*.yaml" -type f 2>/dev/null | \
        xargs -I {} sh -c 'grep -l "status: \"in_progress\"" "{}" 2>/dev/null || true' | \
        head -1)

    if [[ -z "$latest_log" ]]; then
        log "INFO" "No in-progress clarify log found"
        echo '{"continue": true}'
        return 0
    fi

    log "INFO" "Processing log: ${latest_log}"

    # Check if yq is available
    if ! command -v yq &> /dev/null; then
        log "WARN" "yq not found, skipping finalization"
        echo '{"continue": true}'
        return 0
    fi

    # Get current status
    local current_status
    current_status=$(yq '.metadata.status' "$latest_log")

    # Only finalize if still in_progress
    if [[ "$current_status" == "\"in_progress\"" ]]; then
        # Check if final approval was given
        local final_approved
        final_approved=$(yq '.metadata.final_approved' "$latest_log")

        if [[ "$final_approved" == "true" ]]; then
            # Already marked as approved by main loop, just ensure status
            yq -i '.metadata.status = "completed"' "$latest_log"
            log "INFO" "Log already approved, confirmed completion"
        else
            # Mark as incomplete (user may have cancelled or timed out)
            yq -i '.metadata.status = "incomplete"' "$latest_log"
            log "INFO" "Log marked as incomplete (no final approval)"
        fi

        # Update timestamp
        yq -i ".metadata.updated_at = \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"" "$latest_log"

        # Compute final context hash if not already set
        local existing_hash
        existing_hash=$(yq '.pipeline.context_hash' "$latest_log")

        if [[ "$existing_hash" == "null" ]]; then
            local hash
            hash=$(yq '.original_request, .rounds' "$latest_log" | sha256sum | cut -d' ' -f1)
            yq -i ".pipeline.context_hash = \"${hash}\"" "$latest_log"
            log "INFO" "Context hash computed: ${hash:0:16}..."
        fi
    fi

    # Return success
    local output
    output=$(cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "clarify-finalize",
        "log_path": "${latest_log}",
        "status": "$(yq '.metadata.status' "$latest_log" | tr -d '"')"
    }
}
EOF
)

    log "INFO" "Finalization complete"
    echo "$output"
}

# Run main
main "$@"
