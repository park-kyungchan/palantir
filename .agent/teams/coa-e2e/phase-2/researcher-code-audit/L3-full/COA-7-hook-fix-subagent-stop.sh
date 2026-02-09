#!/bin/bash
# Hook: SubagentStop — Teammate termination logging + transcript path capture
# Fires when any teammate/subagent finishes.
#
# Official SubagentStop schema fields:
#   agent_id, agent_type, agent_transcript_path, session_id, transcript_path, cwd, hook_event_name
# NOT available: agent_name, tool_input.*, teammate_name, team_name
#
# L1/L2 enforcement is handled by TeammateIdle and TaskCompleted hooks
# (which have teammate_name and team_name). SubagentStop focuses on
# logging agent_id and transcript_path for audit trail.

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // "unknown"' 2>/dev/null)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // "unknown"' 2>/dev/null)
TRANSCRIPT=$(echo "$INPUT" | jq -r '.agent_transcript_path // "none"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_STOP | id=$AGENT_ID | type=$AGENT_TYPE | transcript=$TRANSCRIPT" >> "$LOG_DIR/teammate-lifecycle.log"

# Output structured JSON summary with available fields
if command -v jq &>/dev/null; then
  jq -n --arg aid "$AGENT_ID" --arg type "$AGENT_TYPE" --arg transcript "$TRANSCRIPT" '{
    "hookSpecificOutput": {
      "hookEventName": "SubagentStop",
      "agentId": $aid,
      "agentType": $type,
      "transcriptPath": $transcript
    }
  }'
fi

exit 0
