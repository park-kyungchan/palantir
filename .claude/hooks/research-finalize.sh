#!/usr/bin/env bash
# research-finalize.sh - Stop Hook for /research Skill
#
# Triggers: Stop event when /research skill completes
# Purpose:
#   1. Validate research output exists at .agent/research/
#   2. Log completion timestamp
#   3. Suggest /planning as next step with research-slug
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
RESEARCH_OUTPUT_DIR=".agent/research"
LOG_FILE=".agent/logs/research-finalize.log"

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
    mkdir -p "$RESEARCH_OUTPUT_DIR"

    # Read hook input
    local input
    input=$(cat)

    log "INFO" "Research Stop hook triggered"
    log "DEBUG" "Input: ${input}"

    # Extract hook event info
    local hook_event
    hook_event=$(echo "$input" | jq -r '.hook_event_name // "unknown"')

    if [[ "$hook_event" != "Stop" ]]; then
        log "WARN" "Unexpected event: ${hook_event}"
        echo '{"continue": true}'
        return 0
    fi

    # Find the most recent research output
    local latest_research
    latest_research=$(find "$RESEARCH_OUTPUT_DIR" -name "*.md" -type f 2>/dev/null | \
        xargs -I {} stat --printf="%Y %n\n" {} 2>/dev/null | \
        sort -rn | head -1 | cut -d' ' -f2-)

    if [[ -z "$latest_research" ]]; then
        log "INFO" "No research output found"

        # Return with warning
        local output
        output=$(cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "research-finalize",
        "status": "warning",
        "message": "No research output found at ${RESEARCH_OUTPUT_DIR}",
        "nextStep": null
    }
}
EOF
)
        echo "$output"
        return 0
    fi

    log "INFO" "Found research output: ${latest_research}"

    # Extract research slug from filename
    local research_slug
    research_slug=$(basename "$latest_research" .md)

    log "INFO" "Research slug: ${research_slug}"

    # Validate research output has content
    local line_count
    line_count=$(wc -l < "$latest_research" 2>/dev/null || echo "0")

    if [[ "$line_count" -lt 10 ]]; then
        log "WARN" "Research output appears incomplete (${line_count} lines)"
    fi

    # Log completion timestamp to research file (if yq available)
    if command -v yq &> /dev/null; then
        # If file has YAML frontmatter, could update it here
        log "DEBUG" "yq available for advanced processing"
    fi

    # Generate next step suggestion
    local next_step="/planning --research-slug ${research_slug}"

    log "INFO" "Finalization complete. Next step: ${next_step}"

    # Return success with next step suggestion
    local output
    output=$(cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "research-finalize",
        "status": "success",
        "researchPath": "${latest_research}",
        "researchSlug": "${research_slug}",
        "lineCount": ${line_count},
        "nextStep": "${next_step}",
        "message": "Research complete. Run: ${next_step}"
    }
}
EOF
)

    echo "$output"
}

# Run main
main "$@"
