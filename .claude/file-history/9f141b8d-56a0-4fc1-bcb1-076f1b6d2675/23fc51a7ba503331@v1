#!/bin/bash
# PostToolUse Hook for Task tool - Agent ID capture and L1 logging
# Version: 2.3.0 (Progressive Disclosure)
#
# Purpose:
#   - Capture Agent ID for resume support
#   - Log L1 summary with priority for later reference
#   - Validate Progressive Disclosure compliance

set -euo pipefail

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')

# Only process Task tool results
if [[ "$TOOL_NAME" != "Task" ]]; then
    echo '{}'
    exit 0
fi

# Extract result info
AGENT_ID=$(echo "$INPUT" | jq -r '.tool_result.agent_id // ""')
OUTPUT=$(echo "$INPUT" | jq -r '.tool_result.output // ""')
SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // "unknown"')

# Extract L1 fields from output (if present)
TASK_ID=$(echo "$OUTPUT" | grep -oP 'taskId:\s*\K\w+' 2>/dev/null || echo "unknown")
PRIORITY=$(echo "$OUTPUT" | grep -oP 'priority:\s*\K\w+' 2>/dev/null || echo "UNKNOWN")
STATUS=$(echo "$OUTPUT" | grep -oP 'status:\s*\K\w+' 2>/dev/null || echo "unknown")
FINDINGS_COUNT=$(echo "$OUTPUT" | grep -oP 'findingsCount:\s*\K\d+' 2>/dev/null || echo "0")
CRITICAL_COUNT=$(echo "$OUTPUT" | grep -oP 'criticalCount:\s*\K\d+' 2>/dev/null || echo "0")
L2_PATH=$(echo "$OUTPUT" | grep -oP 'l2Path:\s*\K[^\s]+' 2>/dev/null || echo "")
REQUIRES_L2=$(echo "$OUTPUT" | grep -oP 'requiresL2Read:\s*\K\w+' 2>/dev/null || echo "false")

# Log to file
LOG_FILE=".agent/logs/task_execution.log"
mkdir -p "$(dirname "$LOG_FILE")"

cat >> "$LOG_FILE" <<EOF
---
timestamp: $(date -Iseconds)
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
        GUIDANCE="⚠️ CRITICAL priority detected. MUST read recommendedRead sections in L2."
        ;;
    "HIGH")
        GUIDANCE="📋 HIGH priority. SHOULD read recommendedRead sections."
        ;;
    "MEDIUM")
        GUIDANCE="ℹ️ MEDIUM priority. MAY read L2 on demand."
        ;;
    "LOW")
        GUIDANCE="✅ LOW priority. L1 is sufficient."
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
