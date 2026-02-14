#!/usr/bin/env bash
# SRC Stage 2: Impact summary injector
# Event: SubagentStop (matcher: implementer)
# Purpose: Read accumulated changes, grep reverse refs, inject to Lead
# Output: additionalContext JSON (max 500 chars)

set -euo pipefail

INPUT=$(cat)

# Extract session_id
if command -v jq &>/dev/null; then
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
else
    SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
fi

[[ -z "$SESSION_ID" ]] && exit 0

LOGFILE="/tmp/src-changes-${SESSION_ID}.log"

# No change log = no changes detected
if [[ ! -f "$LOGFILE" || ! -s "$LOGFILE" ]]; then
    echo '{"hookSpecificOutput":{"hookEventName":"SubagentStop","additionalContext":"SRC: No file changes detected by implementer."}}'
    exit 0
fi

# Read and deduplicate changed files
CHANGED_FILES=$(cut -f3 "$LOGFILE" 2>/dev/null | sort -u)
CHANGED_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')

[[ "$CHANGED_COUNT" -eq 0 ]] && {
    echo '{"hookSpecificOutput":{"hookEventName":"SubagentStop","additionalContext":"SRC: No file changes detected by implementer."}}'
    exit 0
}

# Build changed files summary (compact basenames)
CHANGED_SUMMARY=""
while IFS= read -r f; do
    BASENAME=$(basename "$f")
    if [[ -z "$CHANGED_SUMMARY" ]]; then
        CHANGED_SUMMARY="$BASENAME"
    else
        CHANGED_SUMMARY="${CHANGED_SUMMARY}, ${BASENAME}"
    fi
done <<< "$CHANGED_FILES"

# Grep for reverse references (fixed string, recursive, files only)
# Exclude: .git, node_modules, /tmp, *.log, the changed files themselves
DEPENDENTS=""
DEP_COUNT=0
while IFS= read -r changed; do
    BASENAME=$(basename "$changed")
    # Search for references to this file's basename
    REFS=$(timeout 10 grep -Frl "$BASENAME" /home/palantir/.claude/ \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=agent-memory \
        --exclude='*.log' \
        2>/dev/null | grep -v "$changed" | head -10) || true

    while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        REF_BASE=$(basename "$ref")
        if [[ -z "$DEPENDENTS" ]]; then
            DEPENDENTS="${REF_BASE} (refs ${BASENAME})"
        else
            DEPENDENTS="${DEPENDENTS}, ${REF_BASE} (refs ${BASENAME})"
        fi
        DEP_COUNT=$((DEP_COUNT + 1))
    done <<< "$REFS"
done <<< "$CHANGED_FILES"

# Build output message (max 500 chars)
if [[ "$DEP_COUNT" -eq 0 ]]; then
    MSG="SRC: ${CHANGED_COUNT} files changed. 0 dependents detected. Changed: ${CHANGED_SUMMARY}."
else
    MSG="SRC IMPACT ALERT: ${CHANGED_COUNT} files changed, ${DEP_COUNT} potential dependents. Changed: ${CHANGED_SUMMARY}. Dependents: ${DEPENDENTS}."
fi

# Truncate to 500 chars
if [[ ${#MSG} -gt 500 ]]; then
    MSG="${MSG:0:470}... Run /execution-impact for full list."
fi

# Escape for JSON
MSG=$(echo "$MSG" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\n/\\n/g')

echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SubagentStop\",\"additionalContext\":\"${MSG}\"}}"
exit 0
