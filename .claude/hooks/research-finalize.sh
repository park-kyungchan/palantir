#!/usr/bin/env bash
#=============================================================================
# research-finalize.sh - Stop Hook for /research Skill
# Version: 2.1.0
#
# Trigger: Stop event when /research skill completes
# Purpose:
#   1. Validate research output exists
#   2. Log completion timestamp
#   3. Suggest /planning as next step with research-slug
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
#   - Primary: .agent/prompts/{slug}/research.md
#   - Fallback: .agent/research/{slug}.md (V6 compatibility)
#
# Log Path: .agent/logs/research-finalize.log
# Timestamp Format: ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
#
# Dependencies: jq, yq (optional), stat
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
RESEARCH_OUTPUT_DIR=".agent/research"
LOG_FILE=".agent/logs/research-finalize.log"

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
    # V7.1: Check workload-scoped paths first, then V6 fallback
    local latest_research=""

    # Strategy 1: V7.1 workload-scoped paths
    if [[ -d "$PROMPTS_DIR" ]]; then
        latest_research=$(find "$PROMPTS_DIR" -name "research.md" -type f 2>/dev/null | \
            xargs -I {} stat --printf="%Y %n\n" {} 2>/dev/null | \
            sort -rn | head -1 | cut -d' ' -f2-)
    fi

    # Strategy 2: V6 fallback
    if [[ -z "$latest_research" ]] && [[ -d "$RESEARCH_OUTPUT_DIR" ]]; then
        latest_research=$(find "$RESEARCH_OUTPUT_DIR" -name "*.md" -type f 2>/dev/null | \
            xargs -I {} stat --printf="%Y %n\n" {} 2>/dev/null | \
            sort -rn | head -1 | cut -d' ' -f2-)
    fi

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

    # Extract research slug from path
    # V7.1: .agent/prompts/{slug}/research.md -> extract {slug}
    # V6: .agent/research/{slug}.md -> extract {slug}
    local research_slug
    if [[ "$latest_research" == *"/prompts/"* ]]; then
        # V7.1 path: extract slug from directory name
        research_slug=$(echo "$latest_research" | sed -n 's|.*/prompts/\([^/]*\)/research\.md|\1|p')
    else
        # V6 path: extract slug from filename
        research_slug=$(basename "$latest_research" .md)
    fi

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

    # Determine status based on line count
    local status="success"
    if [[ "$line_count" -lt 10 ]]; then
        status="partial"
    fi

    # Return success with handoff
    local output
    output=$(cat << EOF
{
    "continue": true,
    "hookSpecificOutput": {
        "action": "research-finalize",
        "status": "${status}",
        "researchPath": "${latest_research}",
        "researchSlug": "${research_slug}",
        "lineCount": ${line_count},
        "handoff": {
            "skill": "research",
            "workload_slug": "${research_slug}",
            "status": "${status}",
            "next_action": {
                "skill": "/planning",
                "arguments": "--research-slug ${research_slug}",
                "required": true,
                "reason": "Research complete, ready for planning"
            }
        },
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
