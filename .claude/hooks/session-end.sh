#!/bin/bash
#=============================================================================
# session-end.sh - Claude Code Session End Hook
# Version: 2.0.0
#
# Trigger: Session end lifecycle event
# Purpose: Finalize session and save incomplete todos for next session
#
# Exit Codes:
#   0 - Session finalized successfully
#
# Log Paths:
#   - Archive: .agent/tmp/archive/audit_{ID}_{TIMESTAMP}.jsonl
#   - Compact: .agent/compact-state/compact_summary_{TIMESTAMP}.md
#
# Timestamp Format: ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
#
# Changes in 2.0.0:
#   - Standardized header documentation
#   - Consistent timestamp format (ISO 8601)
#   - Improved compact state management
#=============================================================================

# Don't exit on error - gracefully handle failures for session hooks
set +e

#=============================================================================
# Configuration - Environment-based paths (consistent with session-start.sh)
#=============================================================================

get_agent_tmp_dir() {
    if [ -n "$CLAUDE_AGENT_TMP_DIR" ]; then
        echo "$CLAUDE_AGENT_TMP_DIR"
    else
        echo "${HOME}/.agent/tmp"
    fi
}

AGENT_TMP_DIR="$(get_agent_tmp_dir)"
SESSION_STATE_DIR="$AGENT_TMP_DIR/sessions"
ARCHIVE_DIR="$AGENT_TMP_DIR/archive"

SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
SESSION_FILE="$SESSION_STATE_DIR/session_${SESSION_ID}.json"
EVIDENCE_FILE="$AGENT_TMP_DIR/evidence_${SESSION_ID}.jsonl"
AUDIT_LOG_FILE="$AGENT_TMP_DIR/audit_session_${SESSION_ID}.jsonl"

# Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR" 2>/dev/null

#=============================================================================
# JSON Helper (consistent with session-start.sh)
#=============================================================================

HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

#=============================================================================
# Main Logic
#=============================================================================

# Read current session state
if [ -f "$SESSION_FILE" ]; then
    SESSION_STATE=$(cat "$SESSION_FILE")
else
    SESSION_STATE='{"session_id":"'$SESSION_ID'","status":"unknown"}'
fi

# Finalize evidence collection
if [ -f "$EVIDENCE_FILE" ]; then
    EVIDENCE_COUNT=$(wc -l < "$EVIDENCE_FILE" 2>/dev/null || echo "0")
    echo '{"type":"session_end","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","session_id":"'$SESSION_ID'","evidence_count":'$EVIDENCE_COUNT'}' >> "$EVIDENCE_FILE"
fi

# Extract incomplete todos for next session
if [ -f "$SESSION_FILE" ]; then
    if $HAS_JQ; then
        INCOMPLETE_TODOS=$(echo "$SESSION_STATE" | jq '.todos // [] | map(select(.status != "completed"))' 2>/dev/null || echo '[]')
    else
        INCOMPLETE_TODOS=$(python3 -c "
import json, sys
try:
    data = json.loads('''$SESSION_STATE''')
    todos = [t for t in data.get('todos', []) if t.get('status') != 'completed']
    print(json.dumps(todos))
except:
    print('[]')
" 2>/dev/null || echo '[]')
    fi

    if [ "$INCOMPLETE_TODOS" != "[]" ] && [ "$INCOMPLETE_TODOS" != "" ] && [ "$INCOMPLETE_TODOS" != "null" ]; then
        # Save pending tasks for next session restoration
        SYNC_FILE="$AGENT_TMP_DIR/pending_tasks_${SESSION_ID}.json"
        TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

        if $HAS_JQ; then
            jq -n \
                --arg session_id "$SESSION_ID" \
                --arg timestamp "$TIMESTAMP" \
                --argjson todos "$INCOMPLETE_TODOS" \
                '{
                    session_id: $session_id,
                    timestamp: $timestamp,
                    source: "claude_session",
                    pending_tasks: $todos
                }' > "$SYNC_FILE"
            PENDING_COUNT=$(echo "$INCOMPLETE_TODOS" | jq 'length')
        else
            python3 -c "
import json
todos = json.loads('''$INCOMPLETE_TODOS''')
print(json.dumps({
    'session_id': '$SESSION_ID',
    'timestamp': '$TIMESTAMP',
    'source': 'claude_session',
    'pending_tasks': todos
}))
" > "$SYNC_FILE" 2>/dev/null
            PENDING_COUNT=$(python3 -c "import json; print(len(json.loads('''$INCOMPLETE_TODOS''')))" 2>/dev/null || echo "0")
        fi

        echo '{"type":"todos_saved","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","pending_count":'$PENDING_COUNT'}' >> "$EVIDENCE_FILE"
    fi
fi

# Update session state to completed
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if $HAS_JQ; then
    UPDATED_STATE=$(echo "$SESSION_STATE" | jq \
        --arg end_time "$END_TIME" \
        '. + {end_time: $end_time, status: "completed"}'
    )
else
    UPDATED_STATE=$(python3 -c "
import json
try:
    data = json.loads('''$SESSION_STATE''')
    data['end_time'] = '$END_TIME'
    data['status'] = 'completed'
    print(json.dumps(data))
except:
    print('{\"session_id\":\"$SESSION_ID\",\"status\":\"completed\",\"end_time\":\"$END_TIME\"}')" 2>/dev/null)
fi
echo "$UPDATED_STATE" > "$SESSION_FILE"

# Archive session audit log
if [ -f "$AUDIT_LOG_FILE" ]; then
    ARCHIVE_NAME="audit_${SESSION_ID}_$(date +%Y%m%d_%H%M%S).jsonl"
    cp "$AUDIT_LOG_FILE" "$ARCHIVE_DIR/$ARCHIVE_NAME" 2>/dev/null

    # Compress if larger than 1MB
    FILE_SIZE=$(stat -c%s "$ARCHIVE_DIR/$ARCHIVE_NAME" 2>/dev/null || echo "0")
    if [ "$FILE_SIZE" -gt 1048576 ]; then
        gzip "$ARCHIVE_DIR/$ARCHIVE_NAME" 2>/dev/null || true
    fi
fi

#=============================================================================
# Compact State Management (Migrated from pre-compact.sh)
# Task-based state is now managed by Claude Code's native Task system
# This section creates a lightweight summary for session continuity
#=============================================================================

COMPACT_STATE_DIR="${HOME}/.agent/compact-state"
mkdir -p "$COMPACT_STATE_DIR" 2>/dev/null

# Create compact summary for quick resume (replaces pre-compact functionality)
COMPACT_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
COMPACT_SUMMARY_FILE="$COMPACT_STATE_DIR/compact_summary_${COMPACT_TIMESTAMP}.md"

cat > "$COMPACT_SUMMARY_FILE" << COMPACT_EOF
# Session End Summary
> Session ID: ${SESSION_ID}
> Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
> Status: Session ended normally

## Quick Resume Instructions
1. Claude Code Task system automatically persists tasks to ~/.claude/tasks/
2. Use TaskList to see pending tasks from previous sessions
3. Reference .claude/CLAUDE.md for governance rules

## Session Metrics
- Evidence entries: ${EVIDENCE_COUNT:-0}
- Pending tasks saved: ${PENDING_COUNT:-0}
COMPACT_EOF

# Cleanup old compact summaries (keep last 5)
ls -t "$COMPACT_STATE_DIR"/compact_summary_*.md 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true

# Log session end
echo '{"type":"session_end","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","session_id":"'$SESSION_ID'","status":"completed"}' >> "$AUDIT_LOG_FILE"

# Output completion status
echo '{"status":"finalized","session_id":"'$SESSION_ID'","archived":true}'

exit 0
