#!/bin/bash
# ODA Audit Logger Post-Tool Hook
# Logs all tool operations for audit trail
# Enhanced: Tracks Read/Grep/Glob tool calls for evidence collection

# Don't exit on error - gracefully handle failures
set +e

# Configuration
AUDIT_LOG_DIR="/home/palantir/park-kyungchan/palantir/.agent/tmp"
AUDIT_LOG_FILE="$AUDIT_LOG_DIR/audit_$(date +%Y%m%d).jsonl"
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)}"
EVIDENCE_FILE="$AUDIT_LOG_DIR/evidence_${SESSION_ID}.jsonl"
SESSION_STATE_DIR="$AUDIT_LOG_DIR/sessions"
SESSION_FILE="$SESSION_STATE_DIR/session_${SESSION_ID}.json"

# Ensure directories exist
mkdir -p "$AUDIT_LOG_DIR" 2>/dev/null
mkdir -p "$SESSION_STATE_DIR" 2>/dev/null

# Read input from stdin (JSON format)
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

# Helper: Extract JSON object field
json_get_obj() {
    local json="$1"
    local field="$2"
    local default="$3"

    if command -v jq &> /dev/null; then
        echo "$json" | jq ".$field // $default" 2>/dev/null || echo "$default"
    else
        python3 -c "
import json, sys
try:
    data = json.loads('''$json''')
    result = data.get('$field', json.loads('$default'))
    print(json.dumps(result))
except:
    print('$default')
" 2>/dev/null || echo "$default"
    fi
}

# Validate JSON input
if command -v jq &> /dev/null; then
    if ! echo "$INPUT" | jq . >/dev/null 2>&1; then
        INPUT='{"tool_name":"unknown","tool_input":{}}'
    fi
else
    python3 -c "import json; json.loads('''$INPUT''')" 2>/dev/null || INPUT='{"tool_name":"unknown","tool_input":{}}'
fi

# Extract tool information
TOOL_NAME=$(json_get "$INPUT" "tool_name" "unknown")
TOOL_INPUT=$(json_get_obj "$INPUT" "tool_input" "{}")
TOOL_RESULT=$(json_get_obj "$INPUT" "tool_result" "{}")

# Create audit log entry
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
PWD_DIR=$(pwd)
if command -v jq &> /dev/null; then
    AUDIT_ENTRY=$(jq -n \
        --arg timestamp "$TIMESTAMP" \
        --arg session_id "$SESSION_ID" \
        --arg tool_name "$TOOL_NAME" \
        --argjson tool_input "$TOOL_INPUT" \
        --arg user "${USER:-unknown}" \
        --arg pwd "$PWD_DIR" \
        '{
            timestamp: $timestamp,
            session_id: $session_id,
            tool_name: $tool_name,
            tool_input: $tool_input,
            user: $user,
            working_directory: $pwd
        }'
    )
else
    AUDIT_ENTRY=$(python3 -c "
import json
print(json.dumps({
    'timestamp': '$TIMESTAMP',
    'session_id': '$SESSION_ID',
    'tool_name': '$TOOL_NAME',
    'tool_input': json.loads('''$TOOL_INPUT'''),
    'user': '${USER:-unknown}',
    'working_directory': '$PWD_DIR'
}))
" 2>/dev/null || echo '{"timestamp":"'$TIMESTAMP'","tool_name":"'$TOOL_NAME'"}')
fi

# Append to audit log
echo "$AUDIT_ENTRY" >> "$AUDIT_LOG_FILE"

# Evidence collection for Read/Grep/Glob tools
collect_evidence() {
    local tool="$1"
    local input="$2"
    local result="$3"
    local TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    case "$tool" in
        "Read")
            # Extract file path and line numbers from Read tool
            FILE_PATH=$(json_get "$input" "file_path" "")
            OFFSET=$(json_get "$input" "offset" "0")
            LIMIT=$(json_get "$input" "limit" "all")

            if [ -n "$FILE_PATH" ] && [ "$FILE_PATH" != "" ]; then
                if command -v jq &> /dev/null; then
                    EVIDENCE_ENTRY=$(jq -n \
                        --arg timestamp "$TS" \
                        --arg session_id "$SESSION_ID" \
                        --arg type "file_read" \
                        --arg file_path "$FILE_PATH" \
                        --arg offset "$OFFSET" \
                        --arg limit "$LIMIT" \
                        '{
                            timestamp: $timestamp,
                            session_id: $session_id,
                            type: $type,
                            evidence: {
                                file_path: $file_path,
                                offset: ($offset | tonumber),
                                limit: $limit
                            }
                        }'
                    )
                else
                    EVIDENCE_ENTRY=$(python3 -c "
import json
print(json.dumps({
    'timestamp': '$TS',
    'session_id': '$SESSION_ID',
    'type': 'file_read',
    'evidence': {
        'file_path': '$FILE_PATH',
        'offset': int('$OFFSET') if '$OFFSET'.isdigit() else 0,
        'limit': '$LIMIT'
    }
}))
" 2>/dev/null || echo '{"type":"file_read","file_path":"'$FILE_PATH'"}')
                fi
                echo "$EVIDENCE_ENTRY" >> "$EVIDENCE_FILE"

                # Update session state with file viewed
                if [ -f "$SESSION_FILE" ]; then
                    if command -v jq &> /dev/null; then
                        UPDATED_STATE=$(cat "$SESSION_FILE" | jq \
                            --arg file "$FILE_PATH" \
                            '.files_viewed = ((.files_viewed // []) + [$file] | unique)'
                        )
                    else
                        UPDATED_STATE=$(python3 -c "
import json
try:
    with open('$SESSION_FILE') as f:
        data = json.load(f)
    files = data.get('files_viewed', [])
    if '$FILE_PATH' not in files:
        files.append('$FILE_PATH')
    data['files_viewed'] = files
    print(json.dumps(data))
except Exception as e:
    print('{}')" 2>/dev/null)
                    fi
                    [ -n "$UPDATED_STATE" ] && [ "$UPDATED_STATE" != "{}" ] && echo "$UPDATED_STATE" > "$SESSION_FILE"
                fi
            fi
            ;;

        "Grep")
            # Extract pattern, path, and matched results from Grep tool
            PATTERN=$(json_get "$input" "pattern" "")
            SEARCH_PATH=$(json_get "$input" "path" ".")
            GLOB_FILTER=$(json_get "$input" "glob" "")
            OUTPUT_MODE=$(json_get "$input" "output_mode" "files_with_matches")

            if [ -n "$PATTERN" ] && [ "$PATTERN" != "" ]; then
                # Extract matched files from result if available
                MATCHED_FILES=$(json_get_obj "$result" "matched_files" "[]")

                if command -v jq &> /dev/null; then
                    EVIDENCE_ENTRY=$(jq -n \
                        --arg timestamp "$TS" \
                        --arg session_id "$SESSION_ID" \
                        --arg type "grep_search" \
                        --arg pattern "$PATTERN" \
                        --arg path "$SEARCH_PATH" \
                        --arg glob "$GLOB_FILTER" \
                        --arg output_mode "$OUTPUT_MODE" \
                        --argjson matched_files "$MATCHED_FILES" \
                        '{
                            timestamp: $timestamp,
                            session_id: $session_id,
                            type: $type,
                            evidence: {
                                pattern: $pattern,
                                path: $path,
                                glob: $glob,
                                output_mode: $output_mode,
                                matched_files: $matched_files
                            }
                        }'
                    )
                else
                    EVIDENCE_ENTRY=$(python3 -c "
import json
print(json.dumps({
    'timestamp': '$TS',
    'session_id': '$SESSION_ID',
    'type': 'grep_search',
    'evidence': {
        'pattern': '''$PATTERN''',
        'path': '$SEARCH_PATH',
        'glob': '$GLOB_FILTER',
        'output_mode': '$OUTPUT_MODE',
        'matched_files': json.loads('''$MATCHED_FILES''') if '''$MATCHED_FILES''' else []
    }
}))
" 2>/dev/null || echo '{"type":"grep_search","pattern":"'$PATTERN'"}')
                fi
                echo "$EVIDENCE_ENTRY" >> "$EVIDENCE_FILE"
            fi
            ;;

        "Glob")
            # Extract glob pattern and matched files from Glob tool
            PATTERN=$(json_get "$input" "pattern" "")
            SEARCH_PATH=$(json_get "$input" "path" ".")

            if [ -n "$PATTERN" ] && [ "$PATTERN" != "" ]; then
                # Extract matched files from result if available
                MATCHED_FILES=$(json_get_obj "$result" "files" "[]")

                if command -v jq &> /dev/null; then
                    EVIDENCE_ENTRY=$(jq -n \
                        --arg timestamp "$TS" \
                        --arg session_id "$SESSION_ID" \
                        --arg type "glob_search" \
                        --arg pattern "$PATTERN" \
                        --arg path "$SEARCH_PATH" \
                        --argjson matched_files "$MATCHED_FILES" \
                        '{
                            timestamp: $timestamp,
                            session_id: $session_id,
                            type: $type,
                            evidence: {
                                pattern: $pattern,
                                path: $path,
                                matched_files: $matched_files
                            }
                        }'
                    )
                else
                    EVIDENCE_ENTRY=$(python3 -c "
import json
print(json.dumps({
    'timestamp': '$TS',
    'session_id': '$SESSION_ID',
    'type': 'glob_search',
    'evidence': {
        'pattern': '''$PATTERN''',
        'path': '$SEARCH_PATH',
        'matched_files': json.loads('''$MATCHED_FILES''') if '''$MATCHED_FILES''' else []
    }
}))
" 2>/dev/null || echo '{"type":"glob_search","pattern":"'$PATTERN'"}')
                fi
                echo "$EVIDENCE_ENTRY" >> "$EVIDENCE_FILE"
            fi
            ;;
    esac
}

# Call evidence collection for relevant tools
case "$TOOL_NAME" in
    "Read"|"Grep"|"Glob")
        collect_evidence "$TOOL_NAME" "$TOOL_INPUT" "$TOOL_RESULT"
        ;;
esac

# Exit successfully (don't block)
exit 0
