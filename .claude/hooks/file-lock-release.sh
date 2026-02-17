#!/usr/bin/env bash
set -euo pipefail

# File Lock Release — release mkdir-based file locks
# RSIL-080: Deterministic file ownership enforcement
#
# Usage:
#   file-lock-release.sh <file-path>           Release lock for specific file (validates ownership)
#   file-lock-release.sh --agent <agent-name>   Release ALL locks held by agent (cleanup mode)
#
# Output: JSON { "lock_released": true/false, "reason": "..." }
# Exit 0 on success, Exit 1 on failure

LOCK_BASE="/tmp/claude-locks"
AGENT_NAME="${CLAUDE_AGENT_NAME:-${TEAMMATE_NAME:-unknown}}"

# --- Parse arguments ---
MODE="file"
TARGET=""

if [[ "${1:-}" == "--agent" ]]; then
  MODE="agent"
  TARGET="${2:-}"
  if [[ -z "$TARGET" ]]; then
    echo '{"lock_released": false, "reason": "No agent name provided"}' >&2
    exit 1
  fi
else
  MODE="file"
  TARGET="${1:-}"
  if [[ -z "$TARGET" ]]; then
    echo '{"lock_released": false, "reason": "No file path provided"}' >&2
    exit 1
  fi
fi

# --- Agent cleanup mode: release ALL locks for given agent ---
if [[ "$MODE" == "agent" ]]; then
  if [[ ! -d "$LOCK_BASE" ]]; then
    echo "{\"lock_released\": true, \"released_count\": 0, \"reason\": \"No lock directory exists\"}"
    exit 0
  fi

  RELEASED=0
  for META_FILE in "$LOCK_BASE"/*/metadata.json; do
    [[ -f "$META_FILE" ]] || continue

    LOCK_AGENT=""
    if command -v jq &>/dev/null; then
      LOCK_AGENT=$(jq -r '.agent // ""' "$META_FILE" 2>/dev/null || echo "")
    else
      LOCK_AGENT=$(grep -oP '"agent"\s*:\s*"\K[^"]+' "$META_FILE" 2>/dev/null || echo "")
    fi

    if [[ "$LOCK_AGENT" == "$TARGET" ]]; then
      LOCK_DIR=$(dirname "$META_FILE")
      rm -rf "$LOCK_DIR" 2>/dev/null || true
      RELEASED=$((RELEASED + 1))
    fi
  done

  echo "{\"lock_released\": true, \"released_count\": ${RELEASED}, \"agent\": \"${TARGET}\"}"
  exit 0
fi

# --- File-specific mode: release lock for one file ---
FILE_PATH="$TARGET"

# Normalize path
if [[ "$FILE_PATH" != /* ]]; then
  FILE_PATH="$(cd "$(dirname "$FILE_PATH")" 2>/dev/null && pwd)/$(basename "$FILE_PATH")"
fi

# Hash path
if command -v md5sum &>/dev/null; then
  LOCK_HASH=$(echo -n "$FILE_PATH" | md5sum | cut -d' ' -f1)
elif command -v md5 &>/dev/null; then
  LOCK_HASH=$(echo -n "$FILE_PATH" | md5 -q)
else
  LOCK_HASH=$(echo -n "$FILE_PATH" | cksum | cut -d' ' -f1)
fi

LOCK_DIR="${LOCK_BASE}/${LOCK_HASH}"
METADATA_FILE="${LOCK_DIR}/metadata.json"

# Check lock exists
if [[ ! -d "$LOCK_DIR" ]]; then
  echo "{\"lock_released\": true, \"reason\": \"No lock exists for file\", \"file\": \"${FILE_PATH}\"}"
  exit 0
fi

# Validate ownership before release
if [[ -f "$METADATA_FILE" ]]; then
  LOCK_AGENT=""
  if command -v jq &>/dev/null; then
    LOCK_AGENT=$(jq -r '.agent // ""' "$METADATA_FILE" 2>/dev/null || echo "")
  else
    LOCK_AGENT=$(grep -oP '"agent"\s*:\s*"\K[^"]+' "$METADATA_FILE" 2>/dev/null || echo "")
  fi

  if [[ "$LOCK_AGENT" != "$AGENT_NAME" && "$LOCK_AGENT" != "" ]]; then
    echo "{\"lock_released\": false, \"reason\": \"Lock owned by '${LOCK_AGENT}', not '${AGENT_NAME}'\", \"file\": \"${FILE_PATH}\"}"
    exit 1
  fi
fi

# Release lock
rm -rf "$LOCK_DIR" 2>/dev/null || true
echo "{\"lock_released\": true, \"file\": \"${FILE_PATH}\", \"agent\": \"${AGENT_NAME}\"}"
exit 0
