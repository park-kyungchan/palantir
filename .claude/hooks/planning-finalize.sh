#!/usr/bin/env bash
#=============================================================================
# planning-finalize.sh - Stop Hook for /planning Skill
# Version: 2.1.0
#
# Trigger: Stop event when /planning skill completes
# Purpose:
#   1. Validate planning document exists
#   2. Check Plan Agent review status
#   3. Log completion timestamp
#   4. Suggest next step (/orchestrate)
#   5. Append handoff metadata for pipeline continuity
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
#   - Primary: .agent/prompts/{slug}/plan.yaml
#   - Fallback: .agent/plans/{slug}.yaml (V6 compatibility)
#
# Log Path: .agent/logs/planning-finalize.log
# Timestamp Format: ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
#
# Dependencies: jq, yq (required for full functionality), stat
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
PLANS_DIR=".agent/plans"
LOG_FILE=".agent/logs/planning-finalize.log"

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
    mkdir -p "$(dirname "$LOG_FILE")"
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

    log "INFO" "Stop hook triggered for /planning"
    log "DEBUG" "Input: ${input}"

    # Extract hook event info
    local hook_event
    hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

    if [[ "$hook_event" != "Stop" ]]; then
        log "WARN" "Unexpected event: ${hook_event}"
        echo '{"continue": true}'
        return 0
    fi

    # Find the most recent planning document
    # V7.1: Check workload-scoped paths first, then V6 fallback
    local latest_plan=""

    # Strategy 1: V7.1 workload-scoped paths
    if [[ -d "$PROMPTS_DIR" ]]; then
        latest_plan=$(find "$PROMPTS_DIR" -name "plan.yaml" -type f 2>/dev/null | \
            xargs -I {} stat --format="%Y %n" {} 2>/dev/null | \
            sort -rn | head -1 | cut -d' ' -f2-)
    fi

    # Strategy 2: V6 fallback
    if [[ -z "$latest_plan" ]] && [[ -d "$PLANS_DIR" ]]; then
        latest_plan=$(find "$PLANS_DIR" -name "*.yaml" -type f 2>/dev/null | \
            xargs -I {} stat --format="%Y %n" {} 2>/dev/null | \
            sort -rn | head -1 | cut -d' ' -f2-)
    fi

    if [[ -z "$latest_plan" ]]; then
        log "INFO" "No planning document found in ${PLANS_DIR}"
        echo '{"continue": true, "hookSpecificOutput": {"status": "no_document", "suggestion": "Run /planning first"}}'
        return 0
    fi

    log "INFO" "Processing planning document: ${latest_plan}"

    # Check if yq is available
    if ! command -v yq &> /dev/null; then
        log "WARN" "yq not found, performing basic validation only"
        # Basic validation: check file exists and has content
        if [[ -s "$latest_plan" ]]; then
            echo "{\"continue\": true, \"hookSpecificOutput\": {\"status\": \"validated_basic\", \"path\": \"${latest_plan}\", \"suggestion\": \"Next step: /orchestrate\"}}"
        else
            echo '{"continue": true, "hookSpecificOutput": {"status": "empty_document"}}'
        fi
        return 0
    fi

    # Validate planning document schema
    local review_status
    review_status=$(yq '.planAgentReview.status' "$latest_plan" 2>/dev/null | tr -d '"')

    local plan_id
    plan_id=$(yq '.metadata.id' "$latest_plan" 2>/dev/null | tr -d '"')

    local phase_count
    phase_count=$(yq '.phases | length' "$latest_plan" 2>/dev/null || echo "0")

    log "INFO" "Plan ID: ${plan_id}, Review Status: ${review_status}, Phases: ${phase_count}"

    # Determine action based on review status
    local action_message
    local next_step

    case "$review_status" in
        "approved")
            action_message="Plan Agent approved. Ready for orchestration."
            next_step="/orchestrate --plan-slug ${plan_id}"
            # Update document status to 'ready'
            yq -i '.metadata.status = "ready"' "$latest_plan" 2>/dev/null || true
            yq -i ".metadata.finalized_at = \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"" "$latest_plan" 2>/dev/null || true
            log "INFO" "Document finalized with status 'ready'"
            ;;
        "pending")
            action_message="Plan Agent review not yet completed."
            next_step="Continue /planning or run manually"
            log "WARN" "Planning completed but Plan Agent review still pending"
            ;;
        "rejected"|"needs_revision")
            action_message="Plan Agent requested revisions. Review comments."
            next_step="Address comments and re-run /planning"
            log "WARN" "Plan Agent rejected or requested revisions"
            ;;
        *)
            action_message="Unknown review status: ${review_status}"
            next_step="Check planning document manually"
            log "WARN" "Unknown review status: ${review_status}"
            ;;
    esac

    # Extract slug for handoff
    # V7.1: .agent/prompts/{slug}/plan.yaml -> extract {slug}
    # V6: .agent/plans/{slug}.yaml -> use plan_id
    local plan_slug="${plan_id}"
    if [[ "$latest_plan" == *"/prompts/"* ]]; then
        plan_slug=$(echo "$latest_plan" | sed -n 's|.*/prompts/\([^/]*\)/plan\.yaml|\1|p')
    fi

    # Determine handoff status
    local handoff_status="completed"
    local handoff_required="true"
    if [[ "$review_status" != "approved" ]]; then
        handoff_status="partial"
        handoff_required="false"
    fi

    # Build output with handoff
    local output
    output=$(cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "planning-finalize",
        "plan_id": "${plan_id}",
        "plan_slug": "${plan_slug}",
        "plan_path": "${latest_plan}",
        "review_status": "${review_status}",
        "phase_count": ${phase_count},
        "message": "${action_message}",
        "handoff": {
            "skill": "planning",
            "workload_slug": "${plan_slug}",
            "status": "${handoff_status}",
            "next_action": {
                "skill": "/orchestrate",
                "arguments": "--plan-slug ${plan_slug}",
                "required": ${handoff_required},
                "reason": "${action_message}"
            }
        },
        "suggestion": "${next_step}"
    }
}
EOF
)

    log "INFO" "Finalization complete with handoff: ${action_message}"
    echo "$output"
}

# Run main
main "$@"
