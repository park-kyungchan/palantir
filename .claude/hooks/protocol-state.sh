#!/bin/bash
# ODA Protocol State Hook
# Tracks 3-Stage Protocol stages (A/B/C) and validates transitions

# Don't exit on error - gracefully handle failures
set +e

# Configuration
AGENT_TMP_DIR="/home/palantir/park-kyungchan/palantir/.agent/tmp"
SESSION_STATE_DIR="$AGENT_TMP_DIR/sessions"

SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
SESSION_FILE="$SESSION_STATE_DIR/session_${SESSION_ID}.json"
PROTOCOL_LOG="$AGENT_TMP_DIR/protocol_${SESSION_ID}.jsonl"

# Valid protocol stages and transitions
# IDLE -> A (SCAN)
# A -> B (TRACE)
# B -> C (VERIFY)
# C -> IDLE (complete) or C -> EXECUTE (execution)
# Any -> IDLE (reset)

# Read input from stdin (JSON with requested stage change)
INPUT=$(cat 2>/dev/null || echo '{}')

# Helper: Extract JSON field using jq or python
json_get() {
    local json="$1"
    local field="$2"
    local default="$3"

    if command -v jq &> /dev/null; then
        echo "$json" | jq -r ".$field // \"$default\"" 2>/dev/null || echo "$default"
    else
        python3 -c "
import json, sys
try:
    data = json.loads('''$json''')
    print(data.get('$field', '$default'))
except:
    print('$default')
" 2>/dev/null || echo "$default"
    fi
}

# Helper: Create JSON object
json_create() {
    if command -v jq &> /dev/null; then
        jq -n "$@"
    else
        # Fallback to python for complex JSON creation
        python3 -c "
import json, sys
# Parse arguments and create JSON
args = sys.argv[1:]
data = {}
i = 0
while i < len(args):
    if args[i] == '--arg':
        data[args[i+1]] = args[i+2]
        i += 3
    elif args[i] == '--argjson':
        data[args[i+1]] = json.loads(args[i+2])
        i += 3
    else:
        i += 1
print(json.dumps(data))
" "$@" 2>/dev/null || echo '{}'
    fi
}

REQUESTED_STAGE=$(json_get "$INPUT" "stage" "")
ACTION=$(json_get "$INPUT" "action" "check")  # check, transition, reset

# Ensure session directory exists
mkdir -p "$SESSION_STATE_DIR"

# Get current state
if [ -f "$SESSION_FILE" ]; then
    CURRENT_STATE=$(cat "$SESSION_FILE")
    CURRENT_STAGE=$(json_get "$CURRENT_STATE" "protocol_stage" "IDLE")
else
    CURRENT_STATE='{"session_id":"'$SESSION_ID'","protocol_stage":"IDLE"}'
    CURRENT_STAGE="IDLE"
fi

# Function to validate stage transition
validate_transition() {
    local from="$1"
    local to="$2"

    case "$from:$to" in
        "IDLE:A"|"IDLE:SCAN")
            echo "valid"
            ;;
        "A:B"|"SCAN:TRACE")
            echo "valid"
            ;;
        "B:C"|"TRACE:VERIFY")
            echo "valid"
            ;;
        "C:IDLE"|"VERIFY:IDLE"|"C:EXECUTE"|"VERIFY:EXECUTE")
            echo "valid"
            ;;
        *":IDLE"|*":RESET")
            # Reset is always allowed (abort)
            echo "valid"
            ;;
        "$from:$from")
            # Same stage is allowed (no-op)
            echo "valid"
            ;;
        *)
            echo "invalid"
            ;;
    esac
}

# Normalize stage names
normalize_stage() {
    local stage="$1"
    case "$stage" in
        "A"|"SCAN"|"scan")
            echo "A"
            ;;
        "B"|"TRACE"|"trace")
            echo "B"
            ;;
        "C"|"VERIFY"|"verify")
            echo "C"
            ;;
        "EXECUTE"|"execute")
            echo "EXECUTE"
            ;;
        "IDLE"|"idle"|"RESET"|"reset"|"")
            echo "IDLE"
            ;;
        *)
            echo "$stage"
            ;;
    esac
}

NORMALIZED_CURRENT=$(normalize_stage "$CURRENT_STAGE")
NORMALIZED_REQUESTED=$(normalize_stage "$REQUESTED_STAGE")

# Helper: Get allowed transitions for a stage
get_allowed_transitions() {
    local stage="$1"
    case "$stage" in
        "IDLE") echo '["A"]' ;;
        "A") echo '["B", "IDLE"]' ;;
        "B") echo '["C", "IDLE"]' ;;
        "C") echo '["EXECUTE", "IDLE"]' ;;
        *) echo '["IDLE"]' ;;
    esac
}

case "$ACTION" in
    "check")
        # Just report current state
        TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        ALLOWED=$(get_allowed_transitions "$NORMALIZED_CURRENT")
        if command -v jq &> /dev/null; then
            jq -n \
                --arg session_id "$SESSION_ID" \
                --arg current_stage "$NORMALIZED_CURRENT" \
                --arg timestamp "$TIMESTAMP" \
                --argjson allowed "$ALLOWED" \
                '{
                    status: "ok",
                    session_id: $session_id,
                    current_stage: $current_stage,
                    timestamp: $timestamp,
                    allowed_transitions: $allowed
                }'
        else
            python3 -c "
import json
print(json.dumps({
    'status': 'ok',
    'session_id': '$SESSION_ID',
    'current_stage': '$NORMALIZED_CURRENT',
    'timestamp': '$TIMESTAMP',
    'allowed_transitions': json.loads('$ALLOWED')
}))
" 2>/dev/null || echo '{"status":"ok","session_id":"'$SESSION_ID'","current_stage":"'$NORMALIZED_CURRENT'"}'
        fi
        ;;

    "transition")
        if [ -z "$REQUESTED_STAGE" ]; then
            echo '{"status":"error","message":"No stage specified for transition"}'
            exit 1
        fi

        VALIDATION=$(validate_transition "$NORMALIZED_CURRENT" "$NORMALIZED_REQUESTED")
        TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

        if [ "$VALIDATION" = "valid" ]; then
            # Update session state
            if command -v jq &> /dev/null; then
                UPDATED_STATE=$(echo "$CURRENT_STATE" | jq \
                    --arg new_stage "$NORMALIZED_REQUESTED" \
                    --arg timestamp "$TIMESTAMP" \
                    '. + {
                        protocol_stage: $new_stage,
                        last_stage_change: $timestamp,
                        stage_history: (.stage_history // []) + [{stage: $new_stage, timestamp: $timestamp}]
                    }'
                )
            else
                UPDATED_STATE=$(python3 -c "
import json
try:
    data = json.loads('''$CURRENT_STATE''')
    data['protocol_stage'] = '$NORMALIZED_REQUESTED'
    data['last_stage_change'] = '$TIMESTAMP'
    history = data.get('stage_history', [])
    history.append({'stage': '$NORMALIZED_REQUESTED', 'timestamp': '$TIMESTAMP'})
    data['stage_history'] = history
    print(json.dumps(data))
except Exception as e:
    print('{\"protocol_stage\":\"$NORMALIZED_REQUESTED\",\"last_stage_change\":\"$TIMESTAMP\"}')" 2>/dev/null)
            fi
            echo "$UPDATED_STATE" > "$SESSION_FILE"

            # Log transition
            echo '{"type":"stage_transition","timestamp":"'$TIMESTAMP'","from":"'$NORMALIZED_CURRENT'","to":"'$NORMALIZED_REQUESTED'","session_id":"'$SESSION_ID'"}' >> "$PROTOCOL_LOG"

            if command -v jq &> /dev/null; then
                jq -n \
                    --arg session_id "$SESSION_ID" \
                    --arg from_stage "$NORMALIZED_CURRENT" \
                    --arg to_stage "$NORMALIZED_REQUESTED" \
                    --arg timestamp "$TIMESTAMP" \
                    '{
                        status: "ok",
                        session_id: $session_id,
                        transition: {from: $from_stage, to: $to_stage},
                        current_stage: $to_stage,
                        timestamp: $timestamp
                    }'
            else
                python3 -c "
import json
print(json.dumps({
    'status': 'ok',
    'session_id': '$SESSION_ID',
    'transition': {'from': '$NORMALIZED_CURRENT', 'to': '$NORMALIZED_REQUESTED'},
    'current_stage': '$NORMALIZED_REQUESTED',
    'timestamp': '$TIMESTAMP'
}))
" 2>/dev/null || echo '{"status":"ok","current_stage":"'$NORMALIZED_REQUESTED'"}'
            fi
        else
            # Block invalid transition
            echo '{"type":"blocked_transition","timestamp":"'$TIMESTAMP'","from":"'$NORMALIZED_CURRENT'","attempted":"'$NORMALIZED_REQUESTED'","session_id":"'$SESSION_ID'","reason":"invalid_stage_skip"}' >> "$PROTOCOL_LOG"
            ALLOWED=$(get_allowed_transitions "$NORMALIZED_CURRENT")

            if command -v jq &> /dev/null; then
                jq -n \
                    --arg session_id "$SESSION_ID" \
                    --arg from_stage "$NORMALIZED_CURRENT" \
                    --arg attempted_stage "$NORMALIZED_REQUESTED" \
                    --argjson allowed "$ALLOWED" \
                    '{
                        status: "blocked",
                        session_id: $session_id,
                        current_stage: $from_stage,
                        attempted_stage: $attempted_stage,
                        reason: "Invalid stage transition. Protocol requires sequential stages: IDLE -> A (SCAN) -> B (TRACE) -> C (VERIFY) -> EXECUTE/IDLE",
                        allowed_transitions: $allowed
                    }'
            else
                python3 -c "
import json
print(json.dumps({
    'status': 'blocked',
    'session_id': '$SESSION_ID',
    'current_stage': '$NORMALIZED_CURRENT',
    'attempted_stage': '$NORMALIZED_REQUESTED',
    'reason': 'Invalid stage transition. Protocol requires sequential stages: IDLE -> A (SCAN) -> B (TRACE) -> C (VERIFY) -> EXECUTE/IDLE',
    'allowed_transitions': json.loads('$ALLOWED')
}))
" 2>/dev/null || echo '{"status":"blocked","current_stage":"'$NORMALIZED_CURRENT'","attempted_stage":"'$NORMALIZED_REQUESTED'"}'
            fi
            exit 1
        fi
        ;;

    "reset")
        # Force reset to IDLE
        TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        if command -v jq &> /dev/null; then
            UPDATED_STATE=$(echo "$CURRENT_STATE" | jq \
                --arg timestamp "$TIMESTAMP" \
                '. + {
                    protocol_stage: "IDLE",
                    last_stage_change: $timestamp,
                    stage_history: (.stage_history // []) + [{stage: "IDLE", timestamp: $timestamp, reason: "reset"}]
                }'
            )
        else
            UPDATED_STATE=$(python3 -c "
import json
try:
    data = json.loads('''$CURRENT_STATE''')
    data['protocol_stage'] = 'IDLE'
    data['last_stage_change'] = '$TIMESTAMP'
    history = data.get('stage_history', [])
    history.append({'stage': 'IDLE', 'timestamp': '$TIMESTAMP', 'reason': 'reset'})
    data['stage_history'] = history
    print(json.dumps(data))
except:
    print('{\"protocol_stage\":\"IDLE\",\"last_stage_change\":\"$TIMESTAMP\"}')" 2>/dev/null)
        fi
        echo "$UPDATED_STATE" > "$SESSION_FILE"

        echo '{"type":"protocol_reset","timestamp":"'$TIMESTAMP'","from":"'$NORMALIZED_CURRENT'","session_id":"'$SESSION_ID'"}' >> "$PROTOCOL_LOG"

        if command -v jq &> /dev/null; then
            jq -n \
                --arg session_id "$SESSION_ID" \
                --arg previous_stage "$NORMALIZED_CURRENT" \
                --arg timestamp "$TIMESTAMP" \
                '{
                    status: "ok",
                    session_id: $session_id,
                    action: "reset",
                    previous_stage: $previous_stage,
                    current_stage: "IDLE",
                    timestamp: $timestamp
                }'
        else
            python3 -c "
import json
print(json.dumps({
    'status': 'ok',
    'session_id': '$SESSION_ID',
    'action': 'reset',
    'previous_stage': '$NORMALIZED_CURRENT',
    'current_stage': 'IDLE',
    'timestamp': '$TIMESTAMP'
}))
" 2>/dev/null || echo '{"status":"ok","action":"reset","current_stage":"IDLE"}'
        fi
        ;;

    *)
        echo '{"status":"error","message":"Unknown action: '$ACTION'. Valid actions: check, transition, reset"}'
        exit 1
        ;;
esac

exit 0
