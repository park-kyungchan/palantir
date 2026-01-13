#!/bin/bash
# =============================================================================
# ODA Session End Hook
# =============================================================================
# Finalizes evidence collection and syncs todos to ODA Tasks.
# Includes Boris Cherny Pattern 12: Final health evaluation.
#
# Exit Codes:
#   0 - Session finalized successfully
# =============================================================================

# Don't exit on error - gracefully handle failures
set +e

# Configuration
WORKSPACE_ROOT="${ORION_WORKSPACE_ROOT:-/home/palantir}"
AGENT_TMP_DIR="$WORKSPACE_ROOT/park-kyungchan/palantir/.agent/tmp"
SESSION_STATE_DIR="$AGENT_TMP_DIR/sessions"
ARCHIVE_DIR="$AGENT_TMP_DIR/archive"

SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
SESSION_FILE="$SESSION_STATE_DIR/session_${SESSION_ID}.json"
EVIDENCE_FILE="$AGENT_TMP_DIR/evidence_${SESSION_ID}.jsonl"
AUDIT_LOG_FILE="$AGENT_TMP_DIR/audit_session_${SESSION_ID}.jsonl"

# Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR" 2>/dev/null

# Read current session state
if [ -f "$SESSION_FILE" ]; then
    SESSION_STATE=$(cat "$SESSION_FILE")
else
    SESSION_STATE='{"session_id":"'$SESSION_ID'","status":"unknown"}'
fi

# Finalize evidence collection
if [ -f "$EVIDENCE_FILE" ]; then
    # Count evidence entries
    EVIDENCE_COUNT=$(wc -l < "$EVIDENCE_FILE" 2>/dev/null || echo "0")

    # Add session end marker
    echo '{"type":"session_end","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","session_id":"'$SESSION_ID'","evidence_count":'$EVIDENCE_COUNT'}' >> "$EVIDENCE_FILE"
fi

# =============================================================================
# Boris Cherny Pattern 12: Final Health Evaluation
# =============================================================================
# Run health check and log final session health status
HEALTH_REPORT=""
HEALTH_STATUS="unknown"

# Try to run Python health evaluation
if command -v python3 &> /dev/null; then
    HEALTH_REPORT=$(python3 -c "
import sys
sys.path.insert(0, '$WORKSPACE_ROOT/park-kyungchan/palantir')

try:
    import asyncio
    from scripts.claude.session_health import get_health_monitor
    import json

    async def final_check():
        monitor = get_health_monitor()
        report = await monitor.evaluate()
        return json.dumps(report.to_dict())

    print(asyncio.run(final_check()))
except Exception as e:
    print('{\"error\":\"' + str(e).replace('\"', '\\\\\"') + '\"}')" 2>/dev/null)

    # Extract status from report
    if command -v jq &> /dev/null && [ -n "$HEALTH_REPORT" ]; then
        HEALTH_STATUS=$(echo "$HEALTH_REPORT" | jq -r '.metrics.status // "unknown"' 2>/dev/null || echo "unknown")
        OVERALL_HEALTH=$(echo "$HEALTH_REPORT" | jq -r '.metrics.overall_health // 0' 2>/dev/null || echo "0")
        SHOULD_TERMINATE=$(echo "$HEALTH_REPORT" | jq -r '.should_terminate // false' 2>/dev/null || echo "false")
    fi
fi

# Log health status to evidence
if [ -f "$EVIDENCE_FILE" ] && [ -n "$HEALTH_REPORT" ]; then
    echo '{"type":"final_health_check","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","session_id":"'$SESSION_ID'","status":"'$HEALTH_STATUS'","overall_health":'${OVERALL_HEALTH:-0}',"should_have_terminated":'${SHOULD_TERMINATE:-false}'}' >> "$EVIDENCE_FILE"
fi

# Save full health report
HEALTH_FILE="$AGENT_TMP_DIR/health_final_${SESSION_ID}.json"
if [ -n "$HEALTH_REPORT" ]; then
    echo "$HEALTH_REPORT" > "$HEALTH_FILE"
fi

# Extract incomplete todos for ODA Task sync
if [ -f "$SESSION_FILE" ]; then
    if command -v jq &> /dev/null; then
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
        # Write incomplete todos to sync file for ODA Task creation
        SYNC_FILE="$AGENT_TMP_DIR/pending_tasks_${SESSION_ID}.json"
        TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

        if command -v jq &> /dev/null; then
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

        echo '{"type":"todos_synced","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","pending_count":'$PENDING_COUNT'}' >> "$EVIDENCE_FILE"
    fi
fi

# Update session state to completed
END_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if command -v jq &> /dev/null; then
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

# Log session end to main audit
echo '{"type":"session_end","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","session_id":"'$SESSION_ID'","status":"completed"}' >> "$AUDIT_LOG_FILE"

# Output completion status with health info
echo '{"status":"finalized","session_id":"'$SESSION_ID'","archived":true,"health_status":"'$HEALTH_STATUS'","overall_health":'${OVERALL_HEALTH:-0}'}'

exit 0
