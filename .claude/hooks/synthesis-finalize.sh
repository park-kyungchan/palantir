#!/usr/bin/env bash
# synthesis-finalize.sh - Stop Hook for /synthesis Skill
#
# Triggers: Stop event when /synthesis skill completes
# Purpose:
#   1. Validate synthesis report generated
#   2. Log COMPLETE/ITERATE decision
#   3. Suggest next step based on decision

set -euo pipefail

LOG_FILE=".agent/logs/synthesis-finalize.log"

log() {
    local level="$1"
    local msg="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[${timestamp}] [${level}] ${msg}" >> "$LOG_FILE"
}

main() {
    local input
    input=$(cat)

    log "INFO" "Stop hook triggered for /synthesis"

    local hook_event
    hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

    if [[ "$hook_event" != "Stop" ]]; then
        echo '{"continue": true}'
        return 0
    fi

    # Check for synthesis report
    local report_path=""
    if [[ -f ".agent/outputs/synthesis/synthesis_report.md" ]]; then
        report_path=".agent/outputs/synthesis/synthesis_report.md"
    fi

    log "INFO" "Synthesis complete. Report: ${report_path:-none}"

    local suggestion="Check synthesis report for COMPLETE/ITERATE decision"
    if [[ -n "$report_path" ]]; then
        suggestion="Review ${report_path} then /commit-push-pr or /rsil-plan"
    fi

    cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "synthesis-finalize",
        "status": "success",
        "report_path": "${report_path}",
        "suggestion": "${suggestion}"
    }
}
EOF
}

main "$@"
