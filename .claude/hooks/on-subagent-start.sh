#!/bin/bash
# Hook: SubagentStart — Logging + GC version additionalContext injection
# Cannot block spawn (exit 2 is non-blocking for SubagentStart).
# Injects current GC version as additionalContext for context awareness.

INPUT=$(cat)

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "no-team"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# GC version injection via additionalContext
# Find active team's global-context.md
GC_FILE=""
if [ "$TEAM_NAME" != "no-team" ] && [ -n "$TEAM_NAME" ]; then
  GC_FILE="$LOG_DIR/$TEAM_NAME/global-context.md"
fi

# Fallback: scan most recently modified team config
if [ -z "$GC_FILE" ] || [ ! -f "$GC_FILE" ]; then
  LATEST_TEAM=$(find /home/palantir/.claude/teams/ -name "config.json" -type f -printf '%T@ %h\n' 2>/dev/null | sort -rn | head -1 | awk '{print $2}')
  if [ -n "$LATEST_TEAM" ]; then
    TEAM_FROM_CONFIG=$(basename "$LATEST_TEAM")
    GC_FILE="$LOG_DIR/$TEAM_FROM_CONFIG/global-context.md"
  fi
fi

if [ -f "$GC_FILE" ]; then
  GC_VERSION=$(grep -m1 '^version:' "$GC_FILE" 2>/dev/null | awk '{print $2}')
  if [ -n "$GC_VERSION" ]; then
    jq -n --arg ver "$GC_VERSION" --arg team "$TEAM_NAME" '{
      "hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Current GC: " + $ver + ". Verify your injected context version matches.")
      }
    }'
    exit 0
  fi
fi

exit 0
