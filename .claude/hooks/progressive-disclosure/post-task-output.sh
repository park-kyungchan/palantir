#!/bin/bash
# =============================================================================
# Claude Code PostToolUse Hook - Agent ID Capture and L1 Logging
# =============================================================================
# Captures Agent ID for resume support and logs L1 summary with priority.
# Provides guidance to Main Agent based on priority level.
#
# Matcher: Task
# Exit Codes:
#   0 - Success (with optional JSON output)
# =============================================================================

# Don't exit on error - handle failures gracefully
set +e

#=============================================================================
# Configuration
#=============================================================================

WORKSPACE_ROOT="${CLAUDE_WORKSPACE_ROOT:-$(pwd)}"
LOG_DIR="${WORKSPACE_ROOT}/.agent/logs"
LOG_FILE="${LOG_DIR}/task_execution.log"

#=============================================================================
# JSON Helper
#=============================================================================

HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

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
    print(val if val else '')
except:
    print('')
" 2>/dev/null || echo ""
    fi
}

#=============================================================================
# YAML Field Extractor (grep fallback for -oP compatibility)
#=============================================================================

# Check grep -oP support once (Perl regex)
HAS_GREP_P=false
if echo "test" | grep -oP 'test' &>/dev/null; then
    HAS_GREP_P=true
fi

extract_yaml_field() {
    local field="$1"
    local text="$2"
    local default="${3:-}"

    # Try grep -oP first (Perl regex) - cached check
    if $HAS_GREP_P; then
        result=$(echo "$text" | grep -oP "${field}:\s*\K[^\s]+" 2>/dev/null | head -1)
        if [ -n "$result" ]; then
            echo "$result"
            return
        fi
    fi

    # Fallback: Python extraction (use stdin for safety)
    result=$(echo "$text" | python3 -c "
import sys, re
text = sys.stdin.read()
match = re.search(r'${field}:\s*(\S+)', text)
print(match.group(1) if match else '')
" 2>/dev/null)

    if [ -n "$result" ]; then
        echo "$result"
    else
        echo "$default"
    fi
}

#=============================================================================
# Main Logic
#=============================================================================

INPUT=$(cat)
TOOL_NAME=$(json_get '.tool_name' "$INPUT")

# Only process Task tool results
if [[ "$TOOL_NAME" != "Task" ]]; then
    echo '{}'
    exit 0
fi

# Extract result info
AGENT_ID=$(json_get '.tool_result.agent_id' "$INPUT")
OUTPUT=$(json_get '.tool_result.output' "$INPUT")
SUBAGENT_TYPE=$(json_get '.tool_input.subagent_type' "$INPUT")
[ -z "$SUBAGENT_TYPE" ] && SUBAGENT_TYPE="unknown"

# Extract L1 fields from output (if present)
TASK_ID=$(extract_yaml_field 'taskId' "$OUTPUT" "unknown")
PRIORITY=$(extract_yaml_field 'priority' "$OUTPUT" "UNKNOWN")
STATUS=$(extract_yaml_field 'status' "$OUTPUT" "unknown")
FINDINGS_COUNT=$(extract_yaml_field 'findingsCount' "$OUTPUT" "0")
CRITICAL_COUNT=$(extract_yaml_field 'criticalCount' "$OUTPUT" "0")
L2_PATH=$(extract_yaml_field 'l2Path' "$OUTPUT" "")
REQUIRES_L2=$(extract_yaml_field 'requiresL2Read' "$OUTPUT" "false")

# Create log directory and log entry
mkdir -p "$LOG_DIR" 2>/dev/null

cat >> "$LOG_FILE" <<EOF
---
timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
agent_id: $AGENT_ID
task_id: $TASK_ID
subagent_type: $SUBAGENT_TYPE
priority: $PRIORITY
status: $STATUS
findings_count: $FINDINGS_COUNT
critical_count: $CRITICAL_COUNT
l2_path: $L2_PATH
requires_l2_read: $REQUIRES_L2
---
EOF

# Generate guidance for Main Agent based on priority
GUIDANCE=""
case "$PRIORITY" in
    "CRITICAL")
        GUIDANCE="CRITICAL priority detected. MUST read recommendedRead sections in L2."
        ;;
    "HIGH")
        GUIDANCE="HIGH priority. SHOULD read recommendedRead sections."
        ;;
    "MEDIUM")
        GUIDANCE="MEDIUM priority. MAY read L2 on demand."
        ;;
    "LOW")
        GUIDANCE="LOW priority. L1 is sufficient."
        ;;
esac

# Output guidance if priority is CRITICAL or HIGH
if [[ "$PRIORITY" == "CRITICAL" || "$PRIORITY" == "HIGH" ]]; then
    cat <<RESPONSE
{
  "hookSpecificOutput": {
    "guidance": "$GUIDANCE",
    "l2Path": "$L2_PATH",
    "agentId": "$AGENT_ID"
  }
}
RESPONSE
else
    echo '{}'
fi

exit 0
