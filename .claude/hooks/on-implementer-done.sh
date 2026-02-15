#!/usr/bin/env bash
# SRC Stage 2: Impact summary injector
# Event: SubagentStop (matcher: implementer)
# Purpose: Read accumulated changes, grep reverse refs, inject to Lead
# Output: additionalContext JSON (max 800 chars)

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
if [[ -z "$CHANGED_FILES" ]]; then
    CHANGED_COUNT=0
else
    CHANGED_COUNT=$(echo "$CHANGED_FILES" | wc -l | tr -d ' ')
fi

[[ "$CHANGED_COUNT" -eq 0 ]] && {
    echo '{"hookSpecificOutput":{"hookEventName":"SubagentStop","additionalContext":"SRC: No file changes detected by implementer."}}'
    exit 0
}

# Build changed files summary (last 2 path components for specificity)
CHANGED_SUMMARY=""
while IFS= read -r f; do
    SHORT_NAME=$(echo "$f" | awk -F/ '{if(NF>=2) print $(NF-1)"/"$NF; else print $NF}')
    if [[ -z "$CHANGED_SUMMARY" ]]; then
        CHANGED_SUMMARY="$SHORT_NAME"
    else
        CHANGED_SUMMARY="${CHANGED_SUMMARY}, ${SHORT_NAME}"
    fi
done <<< "$CHANGED_FILES"

# Grep for reverse references (fixed string, recursive, files only)
# Exclude: .git, node_modules, /tmp, *.log, the changed files themselves
DEPENDENTS=""
DEP_COUNT=0
MAX_DEPS=8
while IFS= read -r changed; do
    # Use last 2 path components for specificity (e.g., "execution-code/SKILL.md")
    SEARCH_PATTERN=$(echo "$changed" | awk -F/ '{if(NF>=2) print $(NF-1)"/"$NF; else print $NF}')
    # Search .claude/ scope
    REFS=$(timeout 10 grep -Frl "$SEARCH_PATTERN" "$HOME/.claude/" \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=agent-memory \
        --exclude='*.log' \
        2>/dev/null | grep -v "$changed" | head -10) || true

    # Also search project root for source code dependents (broader scope)
    GIT_ROOT=$(git -C "$HOME" rev-parse --show-toplevel 2>/dev/null || echo "$HOME")
    PROJECT_REFS=$(timeout 10 grep -Frl "$SEARCH_PATTERN" "$GIT_ROOT" \
        --exclude-dir=.git \
        --exclude-dir=node_modules \
        --exclude-dir=.claude \
        --exclude='*.log' \
        --include='*.py' --include='*.ts' --include='*.js' --include='*.md' --include='*.json' --include='*.sh' \
        2>/dev/null | grep -v "$changed" | head -5) || true

    REFS=$(printf '%s\n%s' "$REFS" "$PROJECT_REFS" | sort -u | grep -v '^$')

    while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        [[ "$DEP_COUNT" -ge "$MAX_DEPS" ]] && break
        REF_SHORT=$(echo "$ref" | awk -F/ '{if(NF>=2) print $(NF-1)"/"$NF; else print $NF}')
        if [[ -z "$DEPENDENTS" ]]; then
            DEPENDENTS="${REF_SHORT} (refs ${SEARCH_PATTERN})"
        else
            DEPENDENTS="${DEPENDENTS}, ${REF_SHORT} (refs ${SEARCH_PATTERN})"
        fi
        DEP_COUNT=$((DEP_COUNT + 1))
    done <<< "$REFS"
done <<< "$CHANGED_FILES"

# Append truncation notice if capped
if [[ "$DEP_COUNT" -ge "$MAX_DEPS" ]]; then
    DEPENDENTS="${DEPENDENTS} (truncated)"
fi

# Cleanup processed log file
rm -f "$LOGFILE" 2>/dev/null

# Build output message (max 800 chars)
if [[ "$DEP_COUNT" -eq 0 ]]; then
    MSG="SRC: ${CHANGED_COUNT} files changed. 0 dependents detected. Changed: ${CHANGED_SUMMARY}."
else
    MSG="SRC IMPACT ALERT: ${CHANGED_COUNT} files changed, ${DEP_COUNT} potential dependents. Changed: ${CHANGED_SUMMARY}. Dependents: ${DEPENDENTS}."
fi

# Truncate to 800 chars (safety net — dependent limiting controls typical length)
if [[ ${#MSG} -gt 800 ]]; then
    MSG="${MSG:0:770}... Run /execution-impact for full list."
fi

# Escape for JSON
MSG=$(echo "$MSG" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g; s/\n/\\n/g')

echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SubagentStop\",\"additionalContext\":\"${MSG}\"}}"
exit 0
