#!/bin/bash
# Hook: SubagentStart — Teammate 스폰 시 로깅 + 검증
# Logs teammate spawning for Lead orchestration tracking

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "no-team"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

exit 0
