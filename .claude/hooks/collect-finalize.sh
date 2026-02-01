#!/usr/bin/env bash
# collect-finalize.sh - Stop Hook for /collect Skill
#
# Triggers: Stop event when /collect skill completes
# Purpose:
#   1. Validate collection report generated
#   2. Log aggregation summary
#   3. Suggest /synthesis as next step

set -euo pipefail

LOG_FILE=".agent/logs/collect-finalize.log"

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

    log "INFO" "Stop hook triggered for /collect"

    local hook_event
    hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

    if [[ "$hook_event" != "Stop" ]]; then
        echo '{"continue": true}'
        return 0
    fi

    # Check for collection report
    local report_exists="false"
    if [[ -f ".agent/outputs/collection_report.md" ]]; then
        report_exists="true"
    fi

    log "INFO" "Collection complete. Report exists: ${report_exists}"

    cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "collect-finalize",
        "status": "success",
        "report_exists": ${report_exists},
        "suggestion": "Next step: /synthesis for quality validation"
    }
}
EOF
}

main "$@"
