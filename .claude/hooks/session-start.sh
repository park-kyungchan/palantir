#!/bin/bash
# ODA Session Start Hook
# Initializes evidence tracker and loads previous session state

# Don't exit on error - gracefully handle failures
set +e

# Configuration
AGENT_TMP_DIR="/home/palantir/park-kyungchan/palantir/.agent/tmp"
SESSION_STATE_DIR="$AGENT_TMP_DIR/sessions"
AUDIT_LOG_DIR="$AGENT_TMP_DIR"

# Generate session ID if not provided
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
SESSION_FILE="$SESSION_STATE_DIR/session_${SESSION_ID}.json"
EVIDENCE_FILE="$AGENT_TMP_DIR/evidence_${SESSION_ID}.jsonl"
AUDIT_LOG_FILE="$AUDIT_LOG_DIR/audit_session_${SESSION_ID}.jsonl"

# Ensure directories exist
mkdir -p "$SESSION_STATE_DIR" 2>/dev/null
mkdir -p "$AUDIT_LOG_DIR" 2>/dev/null

# Helper function: Use jq if available, fallback to python
json_tool() {
    if command -v jq &> /dev/null; then
        jq "$@"
    else
        python3 -c "
import sys, json
data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
expr = '''$1'''
# Basic jq-like operations
if expr.startswith('-r'):
    expr = expr[3:].strip()
if expr.startswith('.'):
    keys = expr[1:].split(' // ')[0].split('.')
    result = data
    for k in keys:
        if k and isinstance(result, dict):
            result = result.get(k, '')
    print(result if result else (expr.split(' // ')[1].strip('\"') if '//' in '''$1''' else ''))
else:
    print(json.dumps(data))
" 2>/dev/null || echo ""
    fi
}

# Initialize evidence tracker file
if [ ! -f "$EVIDENCE_FILE" ]; then
    echo '{"type":"session_start","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","session_id":"'$SESSION_ID'"}' > "$EVIDENCE_FILE"
fi

# Load previous session state if exists
PREVIOUS_SESSION=""
LATEST_SESSION=$(ls -t "$SESSION_STATE_DIR"/session_*.json 2>/dev/null | head -n 1 || true)

if [ -n "$LATEST_SESSION" ] && [ -f "$LATEST_SESSION" ]; then
    if command -v jq &> /dev/null; then
        PREVIOUS_STATE=$(cat "$LATEST_SESSION" 2>/dev/null || echo '{}')
        PREVIOUS_SESSION=$(echo "$PREVIOUS_STATE" | jq -r '.session_id // "none"' 2>/dev/null || echo "none")
        INCOMPLETE_TODOS=$(echo "$PREVIOUS_STATE" | jq '.todos // [] | map(select(.status != "completed"))' 2>/dev/null || echo '[]')
    else
        PREVIOUS_SESSION=$(python3 -c "
import json
try:
    with open('$LATEST_SESSION') as f:
        data = json.load(f)
    print(data.get('session_id', 'none'))
except:
    print('none')
" 2>/dev/null || echo "none")
        INCOMPLETE_TODOS=$(python3 -c "
import json
try:
    with open('$LATEST_SESSION') as f:
        data = json.load(f)
    todos = [t for t in data.get('todos', []) if t.get('status') != 'completed']
    print(json.dumps(todos))
except:
    print('[]')
" 2>/dev/null || echo '[]')
    fi

    if [ "$INCOMPLETE_TODOS" != "[]" ] && [ "$INCOMPLETE_TODOS" != "" ]; then
        echo '{"type":"restored_todos","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","previous_session":"'$PREVIOUS_SESSION'","todos":'$INCOMPLETE_TODOS'}' >> "$EVIDENCE_FILE"
    fi
fi

# Initialize new session state
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if command -v jq &> /dev/null; then
    SESSION_STATE=$(jq -n \
        --arg session_id "$SESSION_ID" \
        --arg start_time "$TIMESTAMP" \
        --arg previous_session "$PREVIOUS_SESSION" \
        --arg evidence_file "$EVIDENCE_FILE" \
        --arg audit_log "$AUDIT_LOG_FILE" \
        '{
            session_id: $session_id,
            start_time: $start_time,
            previous_session: $previous_session,
            evidence_file: $evidence_file,
            audit_log: $audit_log,
            protocol_stage: "IDLE",
            todos: [],
            files_viewed: [],
            status: "active"
        }'
    )
else
    SESSION_STATE=$(python3 -c "
import json
print(json.dumps({
    'session_id': '$SESSION_ID',
    'start_time': '$TIMESTAMP',
    'previous_session': '$PREVIOUS_SESSION',
    'evidence_file': '$EVIDENCE_FILE',
    'audit_log': '$AUDIT_LOG_FILE',
    'protocol_stage': 'IDLE',
    'todos': [],
    'files_viewed': [],
    'status': 'active'
}))
" 2>/dev/null)
fi

echo "$SESSION_STATE" > "$SESSION_FILE"

# Set up audit log for session
echo '{"type":"session_start","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","session_id":"'$SESSION_ID'","previous_session":"'$PREVIOUS_SESSION'"}' >> "$AUDIT_LOG_FILE"

# Export session ID for child processes
export CLAUDE_SESSION_ID="$SESSION_ID"
export ODA_EVIDENCE_FILE="$EVIDENCE_FILE"

# Output session info (for Claude to consume)
echo '{"status":"initialized","session_id":"'$SESSION_ID'","evidence_file":"'$EVIDENCE_FILE'"}'

exit 0
