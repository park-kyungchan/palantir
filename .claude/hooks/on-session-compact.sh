#!/bin/bash
# Hook: SessionStart(compact) — RTD-centric auto-compact recovery
# Provides precise recovery context when RTD data is available,
# falls back to generic recovery when it isn't (C-6).

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — recovery active" \
  >> "$LOG_DIR/compact-events.log"

# Attempt RTD-enhanced recovery
RTD_CONTEXT=""
PROJECT_FILE="/home/palantir/.agent/observability/.current-project"

if [ -f "$PROJECT_FILE" ] && command -v jq &>/dev/null; then
  RTD_SLUG=$(head -1 "$PROJECT_FILE" 2>/dev/null)
  OBS_DIR="/home/palantir/.agent/observability/$RTD_SLUG"
  RTD_INDEX="$OBS_DIR/rtd-index.md"

  if [ -f "$RTD_INDEX" ]; then
    # Extract key state from rtd-index.md
    PHASE=$(grep -oP '^current_phase: \K.*' "$RTD_INDEX" 2>/dev/null | tail -1)
    LAST_DP=$(grep -oP '### DP-\d+' "$RTD_INDEX" 2>/dev/null | tail -1)
    RECENT=$(grep -E '^### DP-' "$RTD_INDEX" 2>/dev/null | tail -3 | tr '\n' ' ')

    RTD_CONTEXT="RTD Recovery — Project: $RTD_SLUG | Phase: ${PHASE:-?} | Last: ${LAST_DP:-?}. Recent: $RECENT"
  fi
fi

# Build recovery message
if [ -n "$RTD_CONTEXT" ]; then
  MSG="Your session was compacted. $RTD_CONTEXT. Steps: 1) Read .agent/observability/$RTD_SLUG/rtd-index.md for decision history 2) Read orchestration-plan.md for teammate status 3) TaskGet PERMANENT Task for project context 4) Send context to active teammates with latest PT version."
else
  # Graceful degradation: no RTD data → current generic recovery (v6.2 identical)
  MSG="Your session was compacted. As Lead: 1) Read orchestration-plan.md 2) Read task list (including PERMANENT Task) 3) Send fresh context to each active teammate with the latest PT version 4) Teammates should read their L1/L2/L3 files to restore progress."
fi

# Output JSON
if command -v jq &>/dev/null; then
  jq -n --arg msg "$MSG" '{
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": $msg
    }
  }'
else
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$MSG\"}}"
fi

exit 0
