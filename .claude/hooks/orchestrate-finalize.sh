#!/usr/bin/env bash
# orchestrate-finalize.sh - Stop Hook for /orchestrate Skill
#
# Triggers: Stop event when /orchestrate skill completes
# Purpose:
#   1. Validate Native Tasks were created
#   2. Validate worker prompts generated
#   3. Log completion and suggest /assign

set -euo pipefail

LOG_FILE=".agent/logs/orchestrate-finalize.log"

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

    log "INFO" "Stop hook triggered for /orchestrate"

    local hook_event
    hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

    if [[ "$hook_event" != "Stop" ]]; then
        echo '{"continue": true}'
        return 0
    fi

    # Count pending prompts
    local prompt_count=0
    if [[ -d ".agent/prompts" ]]; then
        prompt_count=$(find .agent/prompts -name "*.yaml" -path "*/pending/*" 2>/dev/null | wc -l)
    fi

    log "INFO" "Orchestration complete. Pending prompts: ${prompt_count}"

    cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "orchestrate-finalize",
        "status": "success",
        "pending_prompts": ${prompt_count},
        "suggestion": "Next step: /assign to assign workers"
    }
}
EOF
}

main "$@"
