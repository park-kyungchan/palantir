#!/usr/bin/env bash
#=============================================================================
# clarify-finalize.sh - Stop Hook for /clarify Skill
# Version: 2.1.0
#
# Trigger: Stop event when /clarify skill completes
# Purpose:
#   1. Finalize YAML log with status update
#   2. Record downstream_skills if routing occurred
#   3. Compute context_hash for integrity verification
#   4. Append handoff metadata for pipeline continuity
#
# Input (JSON stdin):
#   - hook_event_name: "Stop"
#   - agent_id: skill agent ID
#   - agent_transcript_path: path to transcript
#
# Output (JSON stdout):
#   - continue: true (always continue)
#   - hookSpecificOutput: finalization summary with handoff
#
# Path Strategy (V7.1):
#   - Primary: .agent/prompts/{slug}/clarify.yaml
#   - Fallback: .agent/clarify/{slug}.yaml (V6 compatibility)
#
# Log Path: .agent/logs/clarify-finalize.log
# Timestamp Format: ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
#
# Dependencies: jq, yq (optional)
#
# Changes in 2.1.0:
#   - Standardized header with version and log path
#   - Added dependency documentation
#=============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
# V7.1 workload-scoped path (primary)
PROMPTS_DIR=".agent/prompts"
# V6 legacy path (fallback)
CLARIFY_LOG_DIR=".agent/clarify"
LOG_FILE=".agent/logs/clarify-finalize.log"

# Source standalone module for handoff
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_DIR="${SCRIPT_DIR}/../skills/shared"
if [[ -f "${SHARED_DIR}/skill-standalone.sh" ]]; then
    source "${SHARED_DIR}/skill-standalone.sh"
fi

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
    # V7.1: Check workload-scoped paths first, then V6 fallback
    local latest_log=""

    # Strategy 1: V7.1 workload-scoped paths
    if [[ -d "$PROMPTS_DIR" ]]; then
        latest_log=$(find "$PROMPTS_DIR" -name "clarify.yaml" -type f 2>/dev/null | \
            xargs -I {} sh -c 'grep -l "status: \"in_progress\"" "{}" 2>/dev/null || true' | \
            head -1)
    fi

    # Strategy 2: V6 fallback
    if [[ -z "$latest_log" ]] && [[ -d "$CLARIFY_LOG_DIR" ]]; then
        latest_log=$(find "$CLARIFY_LOG_DIR" -name "*.yaml" -type f 2>/dev/null | \
            xargs -I {} sh -c 'grep -l "status: \"in_progress\"" "{}" 2>/dev/null || true' | \
            head -1)
    fi

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

    # Extract slug for handoff
    local slug=""
    slug=$(yq '.metadata.id // ""' "$latest_log" 2>/dev/null | tr -d '"')

    # Generate handoff suggestion
    local next_step=""
    local final_status
    final_status=$(yq '.metadata.status' "$latest_log" 2>/dev/null | tr -d '"')

    if [[ "$final_status" == "completed" ]]; then
        next_step="/research --clarify-slug ${slug}"
        log "INFO" "Handoff ready: ${next_step}"
    fi

    # Return success with handoff
    local output
    output=$(cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "clarify-finalize",
        "log_path": "${latest_log}",
        "status": "${final_status}",
        "slug": "${slug}",
        "handoff": {
            "skill": "clarify",
            "workload_slug": "${slug}",
            "status": "${final_status}",
            "next_action": {
                "skill": "/research",
                "arguments": "--clarify-slug ${slug}",
                "required": true,
                "reason": "Clarify complete, ready for research"
            }
        },
        "nextStep": "${next_step}"
    }
}
EOF
)

    log "INFO" "Finalization complete with handoff"
    echo "$output"
}

# Run main
main "$@"
