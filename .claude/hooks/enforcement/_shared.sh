#!/bin/bash
#=============================================================================
# Enforcement Hooks - Shared Library
# Version: 2.1.0
#
# Common function library sourced by all enforcement Gates
#
# Usage in Gate scripts:
#   source "$(dirname "$0")/_shared.sh"
#
# Sections:
#   1. Configuration - Paths and setting constants
#   2. JSON Helper Functions - JSON parsing utilities
#   3. Output Functions - Gate response generation (JSON)
#   4. State Check Functions - Workload/session state verification
#   5. Logging Functions - Log recording and management
#   6. Utility Functions - General purpose utilities
#
# Changes in 2.1.0:
#   - Added error handling to all functions
#   - Removed duplicate logic (integrated escape_json function)
#   - Improved logging consistency (unified timestamp format)
#   - Performance optimization (removed unnecessary subshells)
#   - Enhanced per-function documentation
#=============================================================================

set -euo pipefail

#=============================================================================
# 1. Configuration
#=============================================================================
export WORKSPACE_ROOT="${CLAUDE_WORKSPACE_ROOT:-/home/palantir}"
export AGENT_TMP_DIR="${WORKSPACE_ROOT}/.agent/tmp"
export AGENT_LOGS_DIR="${WORKSPACE_ROOT}/.agent/logs/enforcement"
export TRACKING_DIR="${WORKSPACE_ROOT}/.claude/hooks/tracking"

# Tracking files
readonly READ_TRACKING_FILE="${AGENT_TMP_DIR}/recent_reads.log"
readonly TASK_TRACKING_FILE="${AGENT_TMP_DIR}/recent_tasks.log"
readonly SESSION_STATE_FILE="${AGENT_TMP_DIR}/current_session.json"
readonly ACTIVE_WORKLOAD_FILE="${WORKSPACE_ROOT}/.agent/prompts/_active_workload.yaml"

# Settings
readonly MAX_TRACKING_ENTRIES=100
readonly TASK_CREATE_TIMEOUT_SECONDS=300  # 5 minutes

# Export for Gate scripts
export READ_TRACKING_FILE TASK_TRACKING_FILE SESSION_STATE_FILE ACTIVE_WORKLOAD_FILE
export MAX_TRACKING_ENTRIES TASK_CREATE_TIMEOUT_SECONDS

# Ensure directories exist (fail silently)
mkdir -p "$AGENT_TMP_DIR" "$AGENT_LOGS_DIR" 2>/dev/null || true

#=============================================================================
# 2. JSON Helper Functions
#=============================================================================

# Check for jq availability (cached for performance)
_HAS_JQ=""
_check_jq() {
    if [[ -z "$_HAS_JQ" ]]; then
        if command -v jq &>/dev/null; then
            _HAS_JQ="true"
        else
            _HAS_JQ="false"
        fi
    fi
    [[ "$_HAS_JQ" == "true" ]]
}

# Parse JSON field
#
# @param $1 field - JSON path (e.g., '.field.path')
# @param $2 json - JSON string to parse
# @returns Field value or empty string on error
#
# Example:
#   value=$(json_get '.tool_name' "$input")
json_get() {
    local field="${1:-}"
    local json="${2:-}"

    if [[ -z "$field" ]] || [[ -z "$json" ]]; then
        echo ""
        return 0
    fi

    if _check_jq; then
        echo "$json" | jq -r "$field // empty" 2>/dev/null || echo ""
    else
        # Fallback to Python
        echo "$json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    keys = '${field}'.lstrip('.').split('.')
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

# Escape string for JSON embedding
#
# @param $1 str - String to escape
# @returns Escaped string safe for JSON
#
# Handles: double quotes, backslashes, newlines, tabs, carriage returns
_escape_json() {
    local str="${1:-}"
    # Escape backslashes first, then quotes, then control characters
    str="${str//\\/\\\\}"
    str="${str//\"/\\\"}"
    str="${str//$'\n'/ }"
    str="${str//$'\t'/ }"
    str="${str//$'\r'/}"
    echo "$str"
}

#=============================================================================
# 3. Output Functions (JSON Response)
#
# All Output functions generate JSON to stdout.
# Must be called before exit in Gate scripts.
#=============================================================================

# Allow tool execution
#
# @returns JSON with permissionDecision: "allow"
#
# Example:
#   output_allow
#   exit 0
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
#
# @param $1 reason - Denial reason (required)
# @param $2 guidance - Additional guidance for user (optional)
# @returns JSON with permissionDecision: "deny"
#
# Example:
#   output_deny "Context Recovery Required" "Read _active_workload.yaml first"
output_deny() {
    local reason="${1:-Denied}"
    local guidance="${2:-}"

    # Escape for JSON
    reason=$(_escape_json "$reason")
    guidance=$(_escape_json "$guidance")

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
#
# @param $1 reason - Reason for asking (required)
# @returns JSON with permissionDecision: "ask"
#
# Example:
#   output_ask "This operation may be destructive. Continue?"
output_ask() {
    local reason="${1:-Permission required}"
    reason=$(_escape_json "$reason")

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
#
# @param $1 context - Additional context to provide
# @returns JSON for PostToolUse event
#
# Example:
#   output_post_guidance "File read successfully. Consider checking dependencies."
output_post_guidance() {
    local context="${1:-}"
    context=$(_escape_json "$context")

    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "$context"
  }
}
EOF
}

# Empty output (pass through without action)
#
# @returns Empty JSON object
output_passthrough() {
    echo '{}'
}

#=============================================================================
# 4. State Check Functions
#
# Functions to verify workload and session state
# All functions return 0 (true) or 1 (false)
#=============================================================================

# Check if active workload exists
#
# @returns 0 if _active_workload.yaml exists, 1 otherwise
has_active_workload() {
    [[ -f "$ACTIVE_WORKLOAD_FILE" ]]
}

# Get active workload slug
#
# @returns Slug string or empty string if not found
#
# Example:
#   slug=$(get_workload_slug)
#   [[ -n "$slug" ]] && echo "Active: $slug"
get_workload_slug() {
    [[ -f "$ACTIVE_WORKLOAD_FILE" ]] || { echo ""; return 0; }

    # Try both quoted and unquoted formats
    grep -oP 'slug:\s*"\K[^"]+|slug:\s*\K[^\s]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null | head -1 || echo ""
}

# Get active workload skill
#
# @returns Current skill name or empty string
get_workload_skill() {
    [[ -f "$ACTIVE_WORKLOAD_FILE" ]] || { echo ""; return 0; }

    grep -oP 'current_skill:\s*"\K[^"]+|current_skill:\s*\K[^\s]+' "$ACTIVE_WORKLOAD_FILE" 2>/dev/null | head -1 || echo ""
}

# Check if _active_workload.yaml has been read in this session
#
# @returns 0 if read, 1 if not
has_read_active_workload() {
    [[ -f "$READ_TRACKING_FILE" ]] || return 1
    grep -q "_active_workload.yaml" "$READ_TRACKING_FILE" 2>/dev/null
}

# Check if L2/L3 files have been read for current workload
#
# @returns 0 if L2/L3 files found in read log, 1 if not
#
# Checks patterns: l2_, l3_, _l2, _l3, L2, L3, l2_detailed, l3_synthesis
has_read_l2l3() {
    [[ -f "$READ_TRACKING_FILE" ]] || return 1

    # Single grep with alternation for better performance
    if grep -qE '(l2_detailed|l3_synthesis|[Ll]2_|[Ll]3_|_[Ll]2|_[Ll]3)' "$READ_TRACKING_FILE" 2>/dev/null; then
        return 0
    fi

    # Also check if workload directory was read
    local slug
    slug=$(get_workload_slug)
    if [[ -n "$slug" ]]; then
        grep -q ".agent/prompts/${slug}" "$READ_TRACKING_FILE" 2>/dev/null && return 0
    fi

    return 1
}

# Check if TaskCreate was called recently (within TASK_CREATE_TIMEOUT_SECONDS)
#
# @returns 0 if recent TaskCreate found, 1 otherwise
has_recent_task_create() {
    [[ -f "$TASK_TRACKING_FILE" ]] || return 1

    # Find most recent TaskCreate entry
    local last_create
    last_create=$(grep "TaskCreate" "$TASK_TRACKING_FILE" 2>/dev/null | tail -1 | cut -d'|' -f1)
    [[ -n "$last_create" ]] || return 1

    # Parse timestamp and compare
    local current_time last_epoch
    current_time=$(date +%s)
    last_epoch=$(date -d "$last_create" +%s 2>/dev/null) || return 1

    local diff=$((current_time - last_epoch))
    [[ $diff -le $TASK_CREATE_TIMEOUT_SECONDS ]]
}

# Check if a file path is in exclusion list (simple/config files)
#
# @param $1 file_path - Path to check
# @returns 0 if excluded (simple file), 1 if not (needs gate checks)
#
# Excludes: README, LICENSE, .md, .txt, .json, .yaml, .yml, .gitignore
# Also excludes: .claude/, .agent/ directories
is_excluded_file() {
    local file_path="${1:-}"
    [[ -z "$file_path" ]] && return 1

    # Quick path-based exclusions first (most common cases)
    case "$file_path" in
        *".claude/"*|*".agent/"*)
            return 0
            ;;
    esac

    # Check file basename for excluded patterns
    local basename
    basename="${file_path##*/}"

    case "$basename" in
        README*|LICENSE*|CHANGELOG*|*.md|*.txt|*.json|*.yaml|*.yml|.gitignore)
            return 0
            ;;
    esac

    return 1
}

# Check if output is summary-only (truncated/abbreviated)
#
# @param $1 output - Output content to check
# @returns 0 if summary-only, 1 if complete
#
# Detects: empty, very short (<50 chars), contains truncation indicators
is_summary_only() {
    local output="${1:-}"

    # Empty or very short
    [[ -z "$output" ]] && return 0
    [[ ${#output} -lt 50 ]] && return 0

    # Check for summary indicators (case-insensitive)
    local lower_output="${output,,}"
    case "$lower_output" in
        *"summary only"*|*"truncated"*|*"abbreviated"*|*"continued from"*)
            return 0
            ;;
    esac

    # Very short output check
    local line_count
    line_count=$(printf '%s' "$output" | wc -l)
    [[ ${#output} -lt 500 ]] && [[ $line_count -lt 20 ]] && return 0

    return 1
}

#=============================================================================
# 5. Logging Functions
#
# All log format: ISO8601_TIMESTAMP|COMPONENT|LEVEL|MESSAGE
#=============================================================================

# Generate ISO8601 timestamp (UTC)
_timestamp() {
    date -u +%Y-%m-%dT%H:%M:%SZ
}

# Log enforcement decision
#
# @param $1 hook_name - Name of the gate/hook (required)
# @param $2 decision - allow/deny/ask (required)
# @param $3 reason - Decision reason (optional)
# @param $4 tool_name - Tool being controlled (optional)
#
# Example:
#   log_enforcement "context-recovery-gate" "deny" "Context recovery required" "Edit"
log_enforcement() {
    local hook_name="${1:-unknown}"
    local decision="${2:-unknown}"
    local reason="${3:-}"
    local tool_name="${4:-}"

    local log_file="${AGENT_LOGS_DIR}/enforcement.log"
    local timestamp
    timestamp=$(_timestamp)

    # Ensure log directory exists
    [[ -d "${AGENT_LOGS_DIR}" ]] || mkdir -p "${AGENT_LOGS_DIR}" 2>/dev/null || true

    echo "${timestamp}|${hook_name}|${decision}|${tool_name}|${reason}" >> "$log_file" 2>/dev/null || true
}

# Log tracking event (read or task)
#
# @param $1 event_type - "read" or "task"
# @param $2 details - Event details
#
# Example:
#   log_tracking "read" "/path/to/file.py"
#   log_tracking "task" "TaskCreate|task-123"
log_tracking() {
    local event_type="${1:-}"
    local details="${2:-}"

    [[ -z "$event_type" ]] && return 0

    local timestamp
    timestamp=$(_timestamp)

    case "$event_type" in
        read)
            echo "${timestamp}|${details}" >> "$READ_TRACKING_FILE" 2>/dev/null || true
            _rotate_tracking_file "$READ_TRACKING_FILE"
            ;;
        task)
            echo "${timestamp}|${details}" >> "$TASK_TRACKING_FILE" 2>/dev/null || true
            _rotate_tracking_file "$TASK_TRACKING_FILE"
            ;;
    esac
}

# Rotate tracking file if too large (internal function)
#
# @param $1 file - File to rotate
_rotate_tracking_file() {
    local file="${1:-}"
    [[ -f "$file" ]] || return 0

    local line_count
    line_count=$(wc -l < "$file" 2>/dev/null) || return 0

    if [[ $line_count -gt $MAX_TRACKING_ENTRIES ]]; then
        tail -n "$MAX_TRACKING_ENTRIES" "$file" > "${file}.tmp" 2>/dev/null && \
            mv "${file}.tmp" "$file" 2>/dev/null || true
    fi
}

# Public alias for rotate (backward compatibility)
rotate_tracking_file() {
    _rotate_tracking_file "$@"
}

#=============================================================================
# 6. Utility Functions
#=============================================================================

# Clean session tracking files (call at session start)
#
# Removes read and task tracking files to start fresh session
clean_session_tracking() {
    rm -f "$READ_TRACKING_FILE" "$TASK_TRACKING_FILE" 2>/dev/null || true
    mkdir -p "$AGENT_TMP_DIR" 2>/dev/null || true
}

# Get current session ID from session state file
#
# @returns Session ID or "unknown" if not found
get_session_id() {
    if [[ -f "$SESSION_STATE_FILE" ]]; then
        local content
        content=$(cat "$SESSION_STATE_FILE" 2>/dev/null) || { echo "unknown"; return 0; }
        json_get '.sessionId' "$content"
    else
        echo "unknown"
    fi
}

# Check if string matches any pattern in array
#
# @param $1 string - String to check
# @param $@ patterns - Remaining args are patterns to match
# @returns 0 if any pattern matches, 1 otherwise
#
# Example:
#   matches_any "$path" "*.py" "*.ts" "*.js" && echo "Source file"
matches_any() {
    local string="${1:-}"
    shift

    for pattern in "$@"; do
        [[ "$string" == $pattern ]] && return 0
    done
    return 1
}
