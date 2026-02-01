#!/bin/bash
#=============================================================================
# Enforcement Hooks - Shared Library
# Version: 2.0.0
#
# 모든 enforcement Gate가 source하는 공통 함수 라이브러리
#
# Usage in Gate scripts:
#   source "$(dirname "$0")/_shared.sh"
#=============================================================================

#=============================================================================
# Configuration
#=============================================================================
export WORKSPACE_ROOT="${CLAUDE_WORKSPACE_ROOT:-/home/palantir}"
export AGENT_TMP_DIR="${WORKSPACE_ROOT}/.agent/tmp"
export AGENT_LOGS_DIR="${WORKSPACE_ROOT}/.agent/logs/enforcement"
export TRACKING_DIR="${WORKSPACE_ROOT}/.claude/hooks/tracking"

# Tracking files
export READ_TRACKING_FILE="${AGENT_TMP_DIR}/recent_reads.log"
export TASK_TRACKING_FILE="${AGENT_TMP_DIR}/recent_tasks.log"
export SESSION_STATE_FILE="${AGENT_TMP_DIR}/current_session.json"
export ACTIVE_WORKLOAD_FILE="${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml"

# Settings
export MAX_TRACKING_ENTRIES=100
export TASK_CREATE_TIMEOUT_SECONDS=300  # 5 minutes

# Ensure directories exist
mkdir -p "$AGENT_TMP_DIR" "$AGENT_LOGS_DIR" 2>/dev/null

#=============================================================================
# JSON Helper Functions
#=============================================================================
HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

# Parse JSON field
# Usage: json_get '.field.path' "$json_string"
json_get() {
    local field="$1"
    local json="$2"
    if $HAS_JQ; then
        echo "$json" | jq -r "$field // empty" 2>/dev/null || echo ""
    else
        echo "$json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    keys = '$field'.lstrip('.').split('.')
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, '')
        else:
            val = ''
            break
    print(val if val else '')
except:
    print('')
" 2>/dev/null || echo ""
    fi
}

#=============================================================================
# Output Functions (JSON Response)
#=============================================================================

# Allow tool execution
# Usage: output_allow
output_allow() {
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
EOF
}

# Deny tool execution (HARD BLOCK)
# Usage: output_deny "reason" "guidance"
output_deny() {
    local reason="$1"
    local guidance="${2:-}"

    # Escape special characters for JSON
    reason=$(echo "$reason" | sed 's/"/\\"/g' | tr '\n' ' ')
    guidance=$(echo "$guidance" | sed 's/"/\\"/g' | tr '\n' ' ')

    if [[ -n "$guidance" ]]; then
        cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$reason",
    "additionalContext": "$guidance"
  }
}
EOF
    else
        cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$reason"
  }
}
EOF
    fi
}

# Ask for user permission
# Usage: output_ask "reason"
output_ask() {
    local reason="$1"
    reason=$(echo "$reason" | sed 's/"/\\"/g' | tr '\n' ' ')

    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "$reason"
  }
}
EOF
}

# PostToolUse output (guidance only, no blocking)
# Usage: output_post_guidance "context"
output_post_guidance() {
    local context="$1"
    context=$(echo "$context" | sed 's/"/\\"/g' | tr '\n' ' ')

    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "$context"
  }
}
EOF
}

# Empty output (pass through)
output_passthrough() {
    echo '{}'
}

#=============================================================================
# State Check Functions
#=============================================================================

# Check if active workload exists
# Returns: 0 if exists, 1 if not
has_active_workload() {
    [[ -f "$ACTIVE_WORKLOAD_FILE" ]]
}

# Get active workload slug
# Returns: slug string or empty
get_workload_slug() {
    if [[ ! -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        echo ""
        return
    fi
    grep -oP 'slug:\s*"\K[^"]+|slug:\s*\K[^\s]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null | head -1
}

# Get active workload skill
get_workload_skill() {
    if [[ ! -f "$ACTIVE_WORKLOAD_FILE" ]]; then
        echo ""
        return
    fi
    grep -oP 'current_skill:\s*"\K[^"]+|current_skill:\s*\K[^\s]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null | head -1
}

# Check if _active_workload.yaml has been read in this session
# Returns: 0 if read, 1 if not
has_read_active_workload() {
    if [[ ! -f "$READ_TRACKING_FILE" ]]; then
        return 1
    fi
    grep -q "_active_workload.yaml" "$READ_TRACKING_FILE" 2>/dev/null
}

# Check if L2/L3 files have been read for current workload
# Returns: 0 if read, 1 if not
has_read_l2l3() {
    if [[ ! -f "$READ_TRACKING_FILE" ]]; then
        return 1
    fi

    local slug
    slug=$(get_workload_slug)

    # L2/L3 file patterns
    local patterns=(
        "l2_detailed"
        "l3_synthesis"
        "l2_"
        "l3_"
        "_l2"
        "_l3"
        "L2"
        "L3"
    )

    for pattern in "${patterns[@]}"; do
        if grep -q "$pattern" "$READ_TRACKING_FILE" 2>/dev/null; then
            return 0
        fi
    done

    # Also check if workload directory was read
    if [[ -n "$slug" ]] && grep -q ".agent/prompts/${slug}" "$READ_TRACKING_FILE" 2>/dev/null; then
        return 0
    fi

    return 1
}

# Check if TaskCreate was called recently
# Returns: 0 if yes, 1 if no
has_recent_task_create() {
    if [[ ! -f "$TASK_TRACKING_FILE" ]]; then
        return 1
    fi

    local current_time
    current_time=$(date +%s)

    # Find most recent TaskCreate
    local last_create
    last_create=$(grep "TaskCreate" "$TASK_TRACKING_FILE" 2>/dev/null | tail -1 | cut -d'|' -f1)

    if [[ -z "$last_create" ]]; then
        return 1
    fi

    # Parse timestamp (ISO format to epoch)
    local last_epoch
    last_epoch=$(date -d "$last_create" +%s 2>/dev/null || echo 0)

    local diff=$((current_time - last_epoch))

    if [[ $diff -le $TASK_CREATE_TIMEOUT_SECONDS ]]; then
        return 0
    fi

    return 1
}

# Check if a file path is in exclusion list (simple files)
# Returns: 0 if excluded, 1 if not
is_excluded_file() {
    local file_path="$1"

    local exclusions=(
        "README"
        ".gitignore"
        ".md"
        "LICENSE"
        "CHANGELOG"
        ".txt"
        ".json"
        ".yaml"
        ".yml"
    )

    local basename
    basename=$(basename "$file_path")

    for pattern in "${exclusions[@]}"; do
        if [[ "$basename" == *"$pattern"* ]]; then
            return 0
        fi
    done

    # Exclude .claude/ configuration files
    if [[ "$file_path" == *".claude/"* ]]; then
        return 0
    fi

    # Exclude .agent/ files
    if [[ "$file_path" == *".agent/"* ]]; then
        return 0
    fi

    return 1
}

# Check if output is summary-only (truncated)
# Returns: 0 if summary-only, 1 if complete
is_summary_only() {
    local output="$1"

    # Empty or very short
    if [[ -z "$output" ]] || [[ ${#output} -lt 50 ]]; then
        return 0
    fi

    # Summary indicators
    local indicators=(
        "summary only"
        "truncated"
        "abbreviated"
        "continued from"
    )

    local lower_output
    lower_output=$(echo "$output" | tr '[:upper:]' '[:lower:]')

    for indicator in "${indicators[@]}"; do
        if [[ "$lower_output" == *"$indicator"* ]]; then
            return 0
        fi
    done

    # Very short output (less than 500 chars and less than 20 lines)
    if [[ ${#output} -lt 500 ]] && [[ $(echo "$output" | wc -l) -lt 20 ]]; then
        return 0
    fi

    return 1
}

#=============================================================================
# Logging Functions
#=============================================================================

# Log enforcement decision
# Usage: log_enforcement "hook_name" "decision" "reason" "tool_name"
log_enforcement() {
    local hook_name="$1"
    local decision="$2"
    local reason="${3:-}"
    local tool_name="${4:-}"

    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    local log_file="${AGENT_LOGS_DIR}/enforcement.log"

    echo "${timestamp}|${hook_name}|${decision}|${tool_name}|${reason}" >> "$log_file" 2>/dev/null
}

# Log tracking event
# Usage: log_tracking "event_type" "details"
log_tracking() {
    local event_type="$1"
    local details="$2"

    local timestamp
    timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    case "$event_type" in
        "read")
            echo "${timestamp}|${details}" >> "$READ_TRACKING_FILE"
            ;;
        "task")
            echo "${timestamp}|${details}" >> "$TASK_TRACKING_FILE"
            ;;
    esac

    # Rotate if needed
    rotate_tracking_file "$READ_TRACKING_FILE"
    rotate_tracking_file "$TASK_TRACKING_FILE"
}

# Rotate tracking file if too large
rotate_tracking_file() {
    local file="$1"

    if [[ ! -f "$file" ]]; then
        return
    fi

    local line_count
    line_count=$(wc -l < "$file" 2>/dev/null || echo 0)

    if [[ $line_count -gt $MAX_TRACKING_ENTRIES ]]; then
        tail -n $MAX_TRACKING_ENTRIES "$file" > "${file}.tmp"
        mv "${file}.tmp" "$file"
    fi
}

#=============================================================================
# Utility Functions
#=============================================================================

# Clean session tracking (called at session start)
clean_session_tracking() {
    rm -f "$READ_TRACKING_FILE" "$TASK_TRACKING_FILE" 2>/dev/null
    mkdir -p "$AGENT_TMP_DIR" 2>/dev/null
}

# Get current session ID
get_session_id() {
    if [[ -f "$SESSION_STATE_FILE" ]]; then
        json_get '.sessionId' "$(cat "$SESSION_STATE_FILE")"
    else
        echo "unknown"
    fi
}
