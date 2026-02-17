#!/usr/bin/env bash
set -euo pipefail

# TaskCompleted hook — quality gate + logging for pipeline tracking
# Input: JSON on stdin with task_id, task_subject, task_description, teammate_name, team_name
# Exit 2: blocks completion if quality checks fail (max 3 retries per task)
# Exit 0: allows completion
# RSIL-010: Upgraded from logging-only to quality gate

INPUT=$(cat)

# Extract fields using jq with grep fallback
if command -v jq &>/dev/null; then
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
  TASK_ID=$(echo "$INPUT" | jq -r '.task_id // "unknown"')
  TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject // "unknown"')
  TASK_DESC=$(echo "$INPUT" | jq -r '.task_description // ""')
  TEAMMATE=$(echo "$INPUT" | jq -r '.teammate_name // "unknown"')
  TEAM=$(echo "$INPUT" | jq -r '.team_name // "unknown"')
else
  SESSION_ID=$(echo "$INPUT" | grep -oE '"session_id"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*:[[:space:]]*"//;s/"$//' || echo "unknown")
  TASK_ID=$(echo "$INPUT" | grep -oE '"task_id"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*:[[:space:]]*"//;s/"$//' || echo "unknown")
  TASK_SUBJECT=$(echo "$INPUT" | grep -oE '"task_subject"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*:[[:space:]]*"//;s/"$//' || echo "unknown")
  TASK_DESC=$(echo "$INPUT" | grep -oE '"task_description"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*:[[:space:]]*"//;s/"$//' || echo "")
  TEAMMATE=$(echo "$INPUT" | grep -oE '"teammate_name"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*:[[:space:]]*"//;s/"$//' || echo "unknown")
  TEAM=$(echo "$INPUT" | grep -oE '"team_name"[[:space:]]*:[[:space:]]*"[^"]+"' | sed 's/.*:[[:space:]]*"//;s/"$//' || echo "unknown")
fi

LOGFILE="/tmp/task-completions-${SESSION_ID}.log"
RETRY_FILE="/tmp/task-gate-retries-${TASK_ID}"

# --- Retry guard: max 3 exit-2 retries to prevent deadlock ---
RETRY_COUNT=0
if [[ -f "$RETRY_FILE" ]]; then
  RETRY_COUNT=$(cat "$RETRY_FILE" 2>/dev/null || echo "0")
fi

if [[ "$RETRY_COUNT" -ge 3 ]]; then
  echo "[$(date '+%H:%M:%S')] GATE PASS (max retries) task=${TASK_ID} subject=\"${TASK_SUBJECT}\" by=${TEAMMATE}" >> "$LOGFILE"
  rm -f "$RETRY_FILE"
  exit 0
fi

# --- Lock Cleanup: release file locks held by completing agent (RSIL-080) ---
if [[ -n "$TEAMMATE" && "$TEAMMATE" != "unknown" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  LOCK_RESULT=$("${SCRIPT_DIR}/file-lock-release.sh" --agent "$TEAMMATE" 2>/dev/null || echo '{"released_count": 0}')
  LOCK_COUNT=$(echo "$LOCK_RESULT" | grep -oE '"released_count"[[:space:]]*:[[:space:]]*[0-9]+' 2>/dev/null | grep -oE '[0-9]+' || echo "0")
  if [[ "$LOCK_COUNT" -gt 0 ]]; then
    echo "[$(date '+%H:%M:%S')] LOCK CLEANUP task=${TASK_ID} agent=${TEAMMATE} released=${LOCK_COUNT}" >> "$LOGFILE"
  fi
fi

# --- Quality Gate Checks ---

# Check 1: PT completion — verify pipeline artifacts exist
if echo "$TASK_SUBJECT" | grep -q "\[PERMANENT\]"; then
  if [[ ! -d "/tmp/pipeline" ]] || [[ -z "$(ls -A /tmp/pipeline/ 2>/dev/null)" ]]; then
    echo $((RETRY_COUNT + 1)) > "$RETRY_FILE"
    echo "[$(date '+%H:%M:%S')] GATE BLOCK task=${TASK_ID} reason=\"PT completion: /tmp/pipeline/ missing or empty\"" >> "$LOGFILE"
    echo "PT completion blocked: /tmp/pipeline/ directory is missing or empty. Ensure pipeline artifacts exist before completing PT." >&2
    exit 2
  fi
fi

# Check 2: File-producing task — verify expected output exists
EXPECTED_OUTPUT=""
if [[ -n "$TASK_DESC" ]]; then
  # Detect output path from description patterns: "write to /path", "output to /path", "produce /path"
  EXPECTED_OUTPUT=$(echo "$TASK_DESC" | grep -oE '(write to|output to|produce)[[:space:]]+[`"'"'"']?/[^[:space:]`"'"'"']+' | head -1 | sed 's/.*[[:space:]]//' || true)
fi

if [[ -n "$EXPECTED_OUTPUT" ]]; then
  if [[ ! -f "$EXPECTED_OUTPUT" ]] || [[ ! -s "$EXPECTED_OUTPUT" ]]; then
    echo $((RETRY_COUNT + 1)) > "$RETRY_FILE"
    echo "[$(date '+%H:%M:%S')] GATE BLOCK task=${TASK_ID} reason=\"Expected output not found: ${EXPECTED_OUTPUT}\"" >> "$LOGFILE"
    echo "Expected output file not found or empty: ${EXPECTED_OUTPUT}. Complete the output before marking task done." >&2
    exit 2
  fi
fi

# --- All checks passed — allow completion ---
rm -f "$RETRY_FILE"

# Append completion record (preserved from original)
echo "[$(date '+%H:%M:%S')] COMPLETED task=${TASK_ID} subject=\"${TASK_SUBJECT}\" by=${TEAMMATE} team=${TEAM}" >> "$LOGFILE"

# Pipeline state: record task completion event (preserved from original)
STATE_FILE="/tmp/claude-pipeline-state.json"
if command -v jq &>/dev/null && [[ -f "$STATE_FILE" ]]; then
  local_tmp=$(mktemp)
  jq --arg tid "$TASK_ID" --arg subj "$TASK_SUBJECT" --arg by "$TEAMMATE" --arg at "$(date -u +%H:%M:%S)" \
    '.tasks_completed += [{"task_id": $tid, "subject": $subj, "by": $by, "at": $at}]' "$STATE_FILE" > "$local_tmp" && mv "$local_tmp" "$STATE_FILE"
fi

exit 0
