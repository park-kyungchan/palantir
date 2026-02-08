#!/bin/bash
# Hook: SubagentStart — Logging + context injection (PT-first, GC legacy fallback)
# Cannot block spawn (exit 2 is non-blocking for SubagentStart).
# Injects PERMANENT Task guidance or legacy GC version as additionalContext.

INPUT=$(cat)

if ! command -v jq &>/dev/null; then
  exit 0
fi

AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"' 2>/dev/null)
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "no-team"' 2>/dev/null)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# Context injection via additionalContext
# Strategy: check team-specific global-context.md (legacy) → PT message → cross-team fallback

if [ "$TEAM_NAME" != "no-team" ] && [ -n "$TEAM_NAME" ]; then
  GC_FILE="$LOG_DIR/$TEAM_NAME/global-context.md"

  # Legacy path: team has global-context.md → inject GC version
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

  # PT path: team has no global-context.md → inject PERMANENT Task guidance
  jq -n --arg team "$TEAM_NAME" '{
    "hookSpecificOutput": {
      "hookEventName": "SubagentStart",
      "additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Context is managed via PERMANENT Task. Use TaskGet on task with subject containing [PERMANENT] for full project context.")
    }
  }'
  exit 0
fi

# No team specified: fallback to most recent global-context.md across all teams
LATEST_GC=$(ls -td "$LOG_DIR"/*/global-context.md 2>/dev/null | head -1)
if [ -n "$LATEST_GC" ] && [ -f "$LATEST_GC" ]; then
  GC_VERSION=$(grep -m1 '^version:' "$LATEST_GC" 2>/dev/null | awk '{print $2}')
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
