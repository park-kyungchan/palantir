#!/bin/bash
# Hook: SubagentStop — Teammate termination logging + L1/L2 output validation
# Fires when any teammate/subagent finishes
# Input: JSON on stdin with session info

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "unknown"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_STOP | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# Check if the stopped agent left L1/L2 files using direct path construction
TEAM_DIR="$LOG_DIR"
if [ "$TEAM_NAME" != "unknown" ] && [ -n "$TEAM_NAME" ]; then
  TEAM_DIR="$LOG_DIR/$TEAM_NAME"
fi
if [ -n "$AGENT_NAME" ] && [ "$AGENT_NAME" != "unknown" ]; then
  L1_EXISTS=$(ls "$TEAM_DIR"/phase-*/"$AGENT_NAME"/L1-index.yaml 2>/dev/null | head -1)
  L2_EXISTS=$(ls "$TEAM_DIR"/phase-*/"$AGENT_NAME"/L2-summary.md 2>/dev/null | head -1)
  if [ -z "$L1_EXISTS" ] && [ -z "$L2_EXISTS" ]; then
    echo "[$TIMESTAMP] SUBAGENT_STOP | WARNING: $AGENT_NAME stopped without L1/L2 output" >> "$LOG_DIR/teammate-lifecycle.log"
  fi
fi

# Output structured JSON summary
if command -v jq &>/dev/null; then
  HAS_L1="false"
  HAS_L2="false"
  [ -n "$L1_EXISTS" ] && HAS_L1="true"
  [ -n "$L2_EXISTS" ] && HAS_L2="true"
  jq -n --arg name "$AGENT_NAME" --arg type "$AGENT_TYPE" --argjson l1 "$HAS_L1" --argjson l2 "$HAS_L2" '{
    "hookSpecificOutput": {
      "hookEventName": "SubagentStop",
      "agent": $name,
      "agentType": $type,
      "hasL1": $l1,
      "hasL2": $l2
    }
  }'
fi

exit 0
