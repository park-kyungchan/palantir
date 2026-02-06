#!/bin/bash
#=============================================================================
# PreCompact Context Save Hook
# Version: 1.0.0
#
# Purpose: Save active workload context before context compaction
# Trigger: PreCompact (before context compaction, manual or auto)
#
# Input (stdin JSON):
#   - session_id, cwd, hook_event_name
#   - trigger: "manual" | "auto"
#   - custom_instructions: string (manual compact only)
#
# Output:
#   - .agent/tmp/pre_compact_snapshot.json (context snapshot)
#   - .agent/logs/compact_events.log (event log)
#   - PreCompact cannot block compaction
#
# Changes in v1.0.0:
#   - Initial implementation
#   - Active workload snapshot capture
#   - Recent reads preservation
#   - TaskList state snapshot
#=============================================================================

set -euo pipefail

#=============================================================================
# Fail-Open Error Handler
#=============================================================================
_fail_open() {
    echo '{}'
    exit 0
}
trap '_fail_open' ERR

#=============================================================================
# Configuration
#=============================================================================
readonly HOOK_NAME="pre-compact-save"
readonly HOOK_VERSION="1.0.0"
readonly WORKSPACE_ROOT="${CLAUDE_PROJECT_DIR:-/home/palantir}"
readonly AGENT_TMP="${WORKSPACE_ROOT}/.agent/tmp"
readonly AGENT_LOGS="${WORKSPACE_ROOT}/.agent/logs"
readonly SNAPSHOT_FILE="${AGENT_TMP}/pre_compact_snapshot.json"
readonly COMPACT_LOG="${AGENT_LOGS}/compact_events.log"
readonly WORKLOAD_FILE="${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml"
readonly READS_LOG="${AGENT_TMP}/recent_reads.log"

# Ensure directories exist
mkdir -p "$AGENT_TMP" "$AGENT_LOGS" 2>/dev/null || true

#=============================================================================
# JSON Helpers
#=============================================================================
HAS_JQ=false
if command -v jq &>/dev/null; then
    HAS_JQ=true
fi

json_extract() {
    local field="$1"
    local input="$2"
    if $HAS_JQ; then
        echo "$input" | jq -r "$field // empty" 2>/dev/null || echo ""
    else
        echo "$input" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    keys = '$field'.strip('.').split('.')
    val = data
    for k in keys:
        val = val.get(k, '')
        if val == '': break
    print(val if val else '')
except:
    print('')
" 2>/dev/null || echo ""
    fi
}

#=============================================================================
# Context Capture Functions
#=============================================================================

# Get active workload slug from _active_workload.yaml
get_workload_slug() {
    if [[ -f "$WORKLOAD_FILE" ]]; then
        grep -E '^slug:' "$WORKLOAD_FILE" 2>/dev/null | sed 's/slug: *//' | tr -d '"' || echo ""
    else
        echo ""
    fi
}

# Get active workload skill
get_workload_skill() {
    if [[ -f "$WORKLOAD_FILE" ]]; then
        grep -E '^current_skill:' "$WORKLOAD_FILE" 2>/dev/null | sed 's/current_skill: *//' | tr -d '"' || echo ""
    else
        echo ""
    fi
}

# Get recent reads (last 10)
get_recent_reads() {
    if [[ -f "$READS_LOG" ]]; then
        tail -10 "$READS_LOG" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

#=============================================================================
# Main Logic
#=============================================================================
main() {
    # Read JSON from stdin
    local input
    input=$(cat 2>/dev/null || echo '{}')

    # Parse fields
    local trigger session_id custom_instructions
    trigger=$(json_extract '.trigger' "$input")
    session_id=$(json_extract '.session_id' "$input")
    custom_instructions=$(json_extract '.custom_instructions' "$input")

    # Timestamp
    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Capture context
    local slug skill recent_reads
    slug=$(get_workload_slug)
    skill=$(get_workload_skill)
    recent_reads=$(get_recent_reads)

    # Log compact event
    echo "[${timestamp}] PreCompact: trigger=${trigger:-unknown}, session=${session_id:-unknown}, slug=${slug:-none}, skill=${skill:-none}" >> "$COMPACT_LOG" 2>/dev/null || true

    # Create snapshot
    if $HAS_JQ; then
        jq -n \
            --arg timestamp "$timestamp" \
            --arg trigger "${trigger:-unknown}" \
            --arg session_id "${session_id:-unknown}" \
            --arg slug "${slug:-}" \
            --arg skill "${skill:-}" \
            --arg recent_reads "${recent_reads:-}" \
            --arg custom_instructions "${custom_instructions:-}" \
            '{
                snapshot_version: "1.0.0",
                timestamp: $timestamp,
                trigger: $trigger,
                session_id: $session_id,
                active_workload: {
                    slug: $slug,
                    current_skill: $skill
                },
                recent_reads: ($recent_reads | split("\n") | map(select(. != ""))),
                custom_instructions: $custom_instructions
            }' > "$SNAPSHOT_FILE" 2>/dev/null
    else
        python3 -c "
import json
reads = '''${recent_reads}'''.strip().split('\n')
reads = [r for r in reads if r]
print(json.dumps({
    'snapshot_version': '1.0.0',
    'timestamp': '${timestamp}',
    'trigger': '${trigger:-unknown}',
    'session_id': '${session_id:-unknown}',
    'active_workload': {
        'slug': '${slug:-}',
        'current_skill': '${skill:-}'
    },
    'recent_reads': reads,
    'custom_instructions': '${custom_instructions:-}'
}, indent=2))
" > "$SNAPSHOT_FILE" 2>/dev/null
    fi

    # Output empty JSON (PreCompact cannot block)
    echo '{}'
}

main
exit 0
