#!/bin/bash
# Hook: SubagentStop — Teammate 종료 시 검증
# Fires when any teammate/subagent finishes
# Input: JSON on stdin with session info

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)

# Log teammate termination for Lead awareness
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_STOP | name=$AGENT_NAME | type=$AGENT_TYPE" >> "$LOG_DIR/teammate-lifecycle.log"

# Exit 0 = allow (don't block)
exit 0
