#!/usr/bin/env bash
set -euo pipefail

# File Lock Acquire — atomic mkdir-based file locking
# RSIL-080: Deterministic file ownership enforcement
#
# Usage: file-lock-acquire.sh <file-path> [agent-name]
# - file-path: absolute path to the file to lock
# - agent-name: optional, defaults to CLAUDE_AGENT_NAME or "unknown"
#
# Output: JSON { "lock_acquired": true/false, "lock_dir": "...", "reason": "..." }
# Exit 0 on success (lock acquired or already owned)
# Exit 1 on failure (lock held by another agent, timeout)

FILE_PATH="${1:-}"
AGENT_NAME="${2:-${CLAUDE_AGENT_NAME:-${TEAMMATE_NAME:-unknown}}}"
LOCK_BASE="/tmp/claude-locks"
TIMEOUT=30
LEASE_SECONDS=300  # 5 minute lease

if [[ -z "$FILE_PATH" ]]; then
  echo '{"lock_acquired": false, "reason": "No file path provided"}' >&2
  exit 1
fi

# Normalize path: resolve to absolute
if [[ "$FILE_PATH" != /* ]]; then
  FILE_PATH="$(cd "$(dirname "$FILE_PATH")" 2>/dev/null && pwd)/$(basename "$FILE_PATH")"
fi

# Hash the normalized path for directory name safety
if command -v md5sum &>/dev/null; then
  LOCK_HASH=$(echo -n "$FILE_PATH" | md5sum | cut -d' ' -f1)
elif command -v md5 &>/dev/null; then
  LOCK_HASH=$(echo -n "$FILE_PATH" | md5 -q)
else
  # Fallback: simple hash via cksum
  LOCK_HASH=$(echo -n "$FILE_PATH" | cksum | cut -d' ' -f1)
fi

LOCK_DIR="${LOCK_BASE}/${LOCK_HASH}"
METADATA_FILE="${LOCK_DIR}/metadata.json"

# Ensure base directory exists
mkdir -p "$LOCK_BASE" 2>/dev/null || true

# --- Attempt lock acquisition with timeout ---
START_TIME=$(date +%s)

while true; do
  ELAPSED=$(( $(date +%s) - START_TIME ))
  if [[ $ELAPSED -ge $TIMEOUT ]]; then
    echo "{\"lock_acquired\": false, \"reason\": \"Timeout after ${TIMEOUT}s\", \"file\": \"${FILE_PATH}\"}"
    exit 1
  fi

  # Atomic mkdir — only one process succeeds
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    # Lock acquired — write metadata
    NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%s)
    EXPIRY=$(date -u -v+${LEASE_SECONDS}S +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "$(( $(date +%s) + LEASE_SECONDS ))")
    cat > "$METADATA_FILE" <<METAEOF
{
  "agent": "${AGENT_NAME}",
  "file": "${FILE_PATH}",
  "pid": $$,
  "acquired_at": "${NOW}",
  "expires_at": "${EXPIRY}"
}
METAEOF
    echo "{\"lock_acquired\": true, \"lock_dir\": \"${LOCK_DIR}\", \"agent\": \"${AGENT_NAME}\"}"
    exit 0
  fi

  # Lock exists — check metadata
  if [[ -f "$METADATA_FILE" ]]; then
    if command -v jq &>/dev/null; then
      LOCK_AGENT=$(jq -r '.agent // "unknown"' "$METADATA_FILE" 2>/dev/null || echo "unknown")
      LOCK_TIME=$(jq -r '.acquired_at // ""' "$METADATA_FILE" 2>/dev/null || echo "")
    else
      LOCK_AGENT=$(grep -oP '"agent"\s*:\s*"\K[^"]+' "$METADATA_FILE" 2>/dev/null || echo "unknown")
      LOCK_TIME=$(grep -oP '"acquired_at"\s*:\s*"\K[^"]+' "$METADATA_FILE" 2>/dev/null || echo "")
    fi

    # Same agent — refresh lease and allow
    if [[ "$LOCK_AGENT" == "$AGENT_NAME" ]]; then
      NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%s)
      EXPIRY=$(date -u -v+${LEASE_SECONDS}S +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "$(( $(date +%s) + LEASE_SECONDS ))")
      cat > "$METADATA_FILE" <<METAEOF
{
  "agent": "${AGENT_NAME}",
  "file": "${FILE_PATH}",
  "pid": $$,
  "acquired_at": "${NOW}",
  "expires_at": "${EXPIRY}"
}
METAEOF
      echo "{\"lock_acquired\": true, \"lock_dir\": \"${LOCK_DIR}\", \"agent\": \"${AGENT_NAME}\", \"refreshed\": true}"
      exit 0
    fi

    # Different agent — check lease expiry
    if [[ -n "$LOCK_TIME" ]]; then
      # Try to parse timestamp for expiry check
      LOCK_EPOCH=0
      if command -v date &>/dev/null; then
        LOCK_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LOCK_TIME" +%s 2>/dev/null || echo "0")
      fi
      NOW_EPOCH=$(date +%s)

      if [[ $LOCK_EPOCH -gt 0 ]] && [[ $(( NOW_EPOCH - LOCK_EPOCH )) -ge $LEASE_SECONDS ]]; then
        # Lease expired — force acquire
        rm -rf "$LOCK_DIR" 2>/dev/null || true
        continue  # Retry mkdir
      fi
    fi
  else
    # Lock dir exists but no metadata — stale lock, clean up
    rm -rf "$LOCK_DIR" 2>/dev/null || true
    continue  # Retry mkdir
  fi

  # Lock held by another agent, not expired — wait and retry
  sleep 1
done
