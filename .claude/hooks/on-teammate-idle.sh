#!/bin/bash
# Hook: TeammateIdle — Layer 4 Speed Bump
# Validates L1/L2 output files exist before allowing teammate to go idle.
# Exit 2 blocks idle and sends stderr as feedback to teammate.

INPUT=$(cat)

TEAMMATE_NAME=$(echo "$INPUT" | jq -r '.teammate_name // empty' 2>/dev/null)
TEAM_NAME=$(echo "$INPUT" | jq -r '.team_name // empty' 2>/dev/null)

# Skip validation for non-team sessions
if [ -z "$TEAM_NAME" ]; then
  exit 0
fi

TEAM_DIR="/home/palantir/.agent/teams/$TEAM_NAME"

# Skip if team directory doesn't exist yet (early setup)
if [ ! -d "$TEAM_DIR" ]; then
  exit 0
fi

# Search for L1 and L2 files under team directory for this teammate
L1_FILE=$(find "$TEAM_DIR" -path "*/$TEAMMATE_NAME/L1-index.yaml" -type f 2>/dev/null | head -1)
L2_FILE=$(find "$TEAM_DIR" -path "*/$TEAMMATE_NAME/L2-summary.md" -type f 2>/dev/null | head -1)

MISSING=""

if [ -z "$L1_FILE" ] || [ ! -s "$L1_FILE" ] || [ "$(wc -c < "$L1_FILE" 2>/dev/null)" -lt 50 ]; then
  MISSING="L1-index.yaml (>=50 bytes)"
fi

if [ -z "$L2_FILE" ] || [ ! -s "$L2_FILE" ] || [ "$(wc -c < "$L2_FILE" 2>/dev/null)" -lt 100 ]; then
  if [ -n "$MISSING" ]; then
    MISSING="$MISSING, L2-summary.md (>=100 bytes)"
  else
    MISSING="L2-summary.md (>=100 bytes)"
  fi
fi

if [ -n "$MISSING" ]; then
  echo "Missing output files for $TEAMMATE_NAME: $MISSING. Write L1-index.yaml and L2-summary.md under .agent/teams/$TEAM_NAME/ before going idle." >&2
  exit 2
fi

exit 0
