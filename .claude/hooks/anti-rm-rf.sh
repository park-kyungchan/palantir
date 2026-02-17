#!/usr/bin/env bash
set -euo pipefail

# PreToolUse:Bash hook — blocks destructive commands (RSIL-009)
# Input: JSON on stdin with tool_name, tool_input.command
# Output: exit 2 + stderr message to BLOCK dangerous commands
# Exit: 0 (safe) or 2 (block)

INPUT=$(cat)

# Extract command from stdin JSON
if command -v jq &>/dev/null; then
  COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')
else
  COMMAND=$(echo "$INPUT" | grep -oP '"command"\s*:\s*"\K[^"]+' || echo "")
fi

# Empty command — nothing to check
[[ -z "$COMMAND" ]] && exit 0

# Normalize: lowercase for matching
CMD_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# --- Destructive rm patterns ---
# Detect rm with recursive+force flags
if echo "$CMD_LOWER" | grep -qE '\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b'; then
  # Extract the target path after rm flags
  TARGET=$(echo "$CMD_LOWER" | sed -E 's/.*\brm\s+(-[a-z]+\s+)*//;s/\s.*//')

  # Block: root, home, current dir, wildcard, system dirs
  case "$TARGET" in
    /|//)
      echo "BLOCKED: rm -rf / — recursive delete of root filesystem" >&2
      exit 2 ;;
    ~|~/)
      echo "BLOCKED: rm -rf ~ — recursive delete of home directory" >&2
      exit 2 ;;
    .|./)
      echo "BLOCKED: rm -rf . — recursive delete of current directory" >&2
      exit 2 ;;
    \*|./\*)
      echo "BLOCKED: rm -rf * — recursive delete of all files" >&2
      exit 2 ;;
    \$home|\$\{home\}|\$home/|\$\{home\}/)
      echo "BLOCKED: rm -rf \$HOME — recursive delete of home directory" >&2
      exit 2 ;;
    /users|/users/|/home|/home/)
      echo "BLOCKED: rm -rf targeting user directories root" >&2
      exit 2 ;;
    /etc|/etc/|/var|/var/|/usr|/usr/|/bin|/bin/|/sbin|/sbin/)
      echo "BLOCKED: rm -rf targeting system directory" >&2
      exit 2 ;;
    /lib|/lib/|/opt|/opt/|/system|/system/)
      echo "BLOCKED: rm -rf targeting system directory" >&2
      exit 2 ;;
  esac
fi

# --- Git destructive patterns ---
if echo "$CMD_LOWER" | grep -qE '\bgit\s+reset\s+--hard\b'; then
  echo "BLOCKED: git reset --hard — discards all local changes irreversibly" >&2
  exit 2
fi

if echo "$CMD_LOWER" | grep -qE '\bgit\s+checkout\s+\.\s*($|[;&|])'; then
  echo "BLOCKED: git checkout . — discards all unstaged changes" >&2
  exit 2
fi

if echo "$CMD_LOWER" | grep -qE '\bgit\s+clean\s+-[a-z]*f'; then
  echo "BLOCKED: git clean -f — force deletes untracked files" >&2
  exit 2
fi

# --- SQL destructive patterns ---
if echo "$CMD_LOWER" | grep -qiE '\b(drop\s+table|drop\s+database)\b'; then
  echo "BLOCKED: SQL DROP statement detected — destructive database operation" >&2
  exit 2
fi

# --- Disk-level destructive patterns ---
if echo "$CMD_LOWER" | grep -qE '>\s*/dev/sd[a-z]'; then
  echo "BLOCKED: Direct write to block device" >&2
  exit 2
fi

if echo "$CMD_LOWER" | grep -qE '\bmkfs\.'; then
  echo "BLOCKED: Filesystem format command detected" >&2
  exit 2
fi

if echo "$CMD_LOWER" | grep -qE '\bdd\s+if='; then
  echo "BLOCKED: dd command detected — potential disk overwrite" >&2
  exit 2
fi

exit 0
