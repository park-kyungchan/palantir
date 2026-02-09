#!/bin/bash
# Hook: SubagentStart — Logging + GC version additionalContext injection
# Cannot block spawn (exit 2 is non-blocking for SubagentStart).
# Injects current GC version as additionalContext for context awareness.
#
# Official SubagentStart schema fields:
#   agent_id, agent_type, session_id, transcript_path, cwd, hook_event_name
# NOT available: agent_name, tool_input.*, teammate_name, team_name

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // "unknown"' 2>/dev/null)
AGENT_ID=$(echo "$INPUT" | jq -r '.agent_id // "unknown"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | id=$AGENT_ID | type=$AGENT_TYPE" >> "$LOG_DIR/teammate-lifecycle.log"

# GC version injection via additionalContext
# SubagentStart has no team_name field — use filesystem heuristic to find active team
GC_FILE=""
TEAM_LABEL="no-team"

# Find the most recently modified team's global-context.md
LATEST_GC=$(ls -t "$LOG_DIR"/*/global-context.md 2>/dev/null | head -1)
if [ -n "$LATEST_GC" ] && [ -f "$LATEST_GC" ]; then
  GC_FILE="$LATEST_GC"
  TEAM_LABEL=$(basename "$(dirname "$LATEST_GC")")
fi

if [ -f "$GC_FILE" ]; then
  GC_VERSION=$(grep -m1 '^version:' "$GC_FILE" 2>/dev/null | awk '{print $2}')
  if [ -n "$GC_VERSION" ]; then
    jq -n --arg ver "$GC_VERSION" --arg team "$TEAM_LABEL" --arg aid "$AGENT_ID" '{
      "hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Current GC: " + $ver + ". Agent ID: " + $aid + ". Verify your injected context version matches.")
      }
    }'
    exit 0
  fi
fi

exit 0
