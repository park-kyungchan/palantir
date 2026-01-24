#!/bin/bash
# 파일 편집 전 자동 백업
# PreToolUse hook for Edit|Write

set -e

# Read input from stdin
input=$(cat)

# Extract file path from tool input
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Skip if no file path
if [ -z "$file_path" ]; then
    exit 0
fi

# Skip if file doesn't exist (new file)
if [ ! -f "$file_path" ]; then
    exit 0
fi

# Create backup directory
backup_dir="/home/palantir/.claude/backups/$(date +%Y%m%d)"
mkdir -p "$backup_dir"

# Create backup with timestamp
backup_name="$(basename "$file_path").$(date +%H%M%S).bak"
cp "$file_path" "$backup_dir/$backup_name"

# Keep only last 100 backups
find /home/palantir/.claude/backups -type f -name "*.bak" | sort -r | tail -n +101 | xargs rm -f 2>/dev/null || true

exit 0
