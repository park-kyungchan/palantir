#!/usr/bin/env bash
set -euo pipefail

# input-modifier.sh — PreToolUse hook for deterministic input modification
# RSIL-001: Converts advisory CLAUDE.md rules into hook-based enforcement
#
# Handles three concerns:
#   1. File Lock Enforcement (Edit/Write) — synergy with RSIL-080 lock structure
#   2. Git Commit Co-Author Enforcement (Bash) — via updatedInput
#   3. Path Safety Enforcement (Edit/Write) — blocks system directory writes
#
# Input: JSON on stdin with tool_name, tool_input
# Output: JSON to stdout with updatedInput (modifications), or exit 2 to block
# Exit: 0 (allow/pass-through), 2 (block with stderr feedback)

INPUT=$(cat)

# Extract tool name from stdin JSON
if command -v jq &>/dev/null; then
  TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || echo "")
else
  TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
fi

[[ -z "$TOOL_NAME" ]] && exit 0

# --- Configuration ---
AGENT_NAME="${CLAUDE_AGENT_NAME:-${TEAMMATE_NAME:-unknown}}"
LOCK_BASE="/tmp/claude-locks"
LEASE_SECONDS=300  # 5 minute lease (matches file-lock-acquire.sh)
CO_AUTHOR="Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# ============================================================================
# Helper: Write lock metadata (single line JSON for atomicity)
# ============================================================================
write_lock_metadata() {
  local meta_file="$1"
  local norm_path="$2"
  local now expiry
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%s)
  expiry=$(date -u -v+${LEASE_SECONDS}S +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "$(( $(date +%s) + LEASE_SECONDS ))")
  printf '{"agent":"%s","file":"%s","pid":%d,"acquired_at":"%s","expires_at":"%s"}\n' \
    "$AGENT_NAME" "$norm_path" $$ "$now" "$expiry" > "$meta_file"
}

# ============================================================================
# Helper: Hash a file path for lock directory name
# ============================================================================
hash_path() {
  local path="$1"
  if command -v md5 &>/dev/null; then
    echo -n "$path" | md5 -q
  elif command -v md5sum &>/dev/null; then
    echo -n "$path" | md5sum | cut -d' ' -f1
  else
    echo -n "$path" | cksum | cut -d' ' -f1
  fi
}

# ============================================================================
# Helper: Check if lock lease has expired
# Returns 0 if expired, 1 if still valid
# ============================================================================
is_lease_expired() {
  local lock_time="$1"
  local lock_epoch=0 now_epoch
  now_epoch=$(date +%s)

  # macOS date parsing
  lock_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$lock_time" +%s 2>/dev/null || echo "0")

  if [[ "$lock_epoch" -gt 0 ]] && [[ $(( now_epoch - lock_epoch )) -ge $LEASE_SECONDS ]]; then
    return 0  # expired
  fi
  return 1  # still valid
}

# ============================================================================
# EDIT / WRITE — Path Safety + File Lock Enforcement
# ============================================================================
handle_edit_write() {
  # Extract file path
  local file_path
  if command -v jq &>/dev/null; then
    file_path=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
  else
    file_path=$(echo "$INPUT" | grep -o '"file_path":"[^"]*"' 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
  fi

  [[ -z "$file_path" ]] && exit 0

  # --- PATH SAFETY ENFORCEMENT ---
  # Block writes to system directories (absolute paths only)
  case "$file_path" in
    /etc/*|/usr/*|/var/*|/bin/*|/sbin/*|/lib/*|/System/*)
      echo "BLOCKED: Write to system directory '${file_path}' is not allowed. Only project files can be modified." >&2
      exit 2 ;;
    /dev/*|/proc/*|/sys/*)
      echo "BLOCKED: Write to virtual filesystem '${file_path}' is not allowed." >&2
      exit 2 ;;
    /Library/*)
      echo "BLOCKED: Write to system Library '${file_path}' is not allowed." >&2
      exit 2 ;;
  esac

  # --- FILE LOCK ENFORCEMENT ---
  # Normalize path to absolute
  local norm_path="$file_path"
  if [[ "$norm_path" != /* ]]; then
    norm_path="$(pwd)/${norm_path}"
  fi

  local lock_hash lock_dir metadata_file
  lock_hash=$(hash_path "$norm_path")
  lock_dir="${LOCK_BASE}/${lock_hash}"
  metadata_file="${lock_dir}/metadata.json"

  # Ensure lock base directory exists
  mkdir -p "$LOCK_BASE" 2>/dev/null || true

  # Attempt atomic lock acquisition via mkdir
  if mkdir "$lock_dir" 2>/dev/null; then
    # Lock acquired successfully — write metadata
    write_lock_metadata "$metadata_file" "$norm_path"
    exit 0
  fi

  # Lock directory exists — check ownership
  if [[ -f "$metadata_file" ]]; then
    local lock_agent lock_time
    if command -v jq &>/dev/null; then
      lock_agent=$(jq -r '.agent // "unknown"' "$metadata_file" 2>/dev/null || echo "unknown")
      lock_time=$(jq -r '.acquired_at // ""' "$metadata_file" 2>/dev/null || echo "")
    else
      lock_agent=$(grep -o '"agent":"[^"]*"' "$metadata_file" 2>/dev/null | head -1 | cut -d'"' -f4 || echo "unknown")
      lock_time=$(grep -o '"acquired_at":"[^"]*"' "$metadata_file" 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
    fi

    # Same agent — refresh lease, allow through
    if [[ "$lock_agent" == "$AGENT_NAME" ]]; then
      write_lock_metadata "$metadata_file" "$norm_path"
      exit 0
    fi

    # Different agent — check lease expiry
    if [[ -n "$lock_time" ]] && is_lease_expired "$lock_time"; then
      # Lease expired — force re-acquire
      rm -rf "$lock_dir" 2>/dev/null || true
      if mkdir "$lock_dir" 2>/dev/null; then
        write_lock_metadata "$metadata_file" "$norm_path"
        exit 0
      fi
    fi

    # Lock held by different agent, lease still valid — BLOCK
    echo "BLOCKED: File '$(basename "$norm_path")' locked by '${lock_agent}'. Wait for lock release or lease expiry (5 min)." >&2
    exit 2
  else
    # Lock directory exists but no metadata — stale lock, clean up and acquire
    rm -rf "$lock_dir" 2>/dev/null || true
    if mkdir "$lock_dir" 2>/dev/null; then
      write_lock_metadata "$metadata_file" "$norm_path"
    fi
    exit 0
  fi
}

# ============================================================================
# BASH — Git Commit Co-Author Enforcement
# ============================================================================
handle_bash() {
  # Extract command
  local command
  if command -v jq &>/dev/null; then
    command=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")
  else
    command=$(echo "$INPUT" | grep -o '"command":"[^"]*"' 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
  fi

  [[ -z "$command" ]] && exit 0

  # Only process git commit commands
  echo "$command" | grep -q 'git commit' || exit 0

  # Skip amend/fixup/squash — don't modify these
  echo "$command" | grep -qE '\-\-(amend|fixup|squash)' && exit 0

  # Check if Co-Authored-By is already present (case-insensitive)
  echo "$command" | grep -qi 'Co-Authored-By' && exit 0

  # Co-Author missing — inject via updatedInput using --trailer flag
  # --trailer appends to the commit message body regardless of -m format
  local modified_cmd
  modified_cmd=$(echo "$command" | sed "s/git commit/git commit --trailer \"${CO_AUTHOR}\"/")

  # Output updatedInput JSON to stdout
  if command -v jq &>/dev/null; then
    jq -n --arg cmd "$modified_cmd" '{
      "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": { "command": $cmd },
        "additionalContext": "Auto-injected Co-Authored-By trailer via input-modifier hook (RSIL-001)"
      }
    }'
  else
    # Manual JSON construction with basic escaping
    local escaped_cmd
    escaped_cmd=$(printf '%s' "$modified_cmd" | sed 's/\\/\\\\/g; s/"/\\"/g')
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","updatedInput":{"command":"%s"},"additionalContext":"Auto-injected Co-Authored-By trailer via input-modifier hook (RSIL-001)"}}\n' "$escaped_cmd"
  fi
  exit 0
}

# ============================================================================
# Main dispatch
# ============================================================================
case "$TOOL_NAME" in
  "Edit"|"Write")
    handle_edit_write
    ;;
  "Bash")
    handle_bash
    ;;
esac

# Default: allow without modification
exit 0
