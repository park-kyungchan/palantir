#!/bin/bash
# =============================================================================
# Clarify Q&A Logger Hook (V2.0.0 - YAML Integration)
# =============================================================================
# Purpose: Capture AskUserQuestion exchanges and integrate with YAML log
# Trigger: PostToolUse on AskUserQuestion
# Output: Updates .agent/clarify/{slug}.yaml (rounds section)
#
# V2.0.0 Changes:
# - Migrated from JSONL to YAML integration
# - Updates existing clarify session log directly
# - Maintains backward compatibility with JSONL for non-clarify sessions
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
CLARIFY_LOG_DIR=".agent/clarify"
LEGACY_LOG_DIR=".agent/logs/clarify"
NOTIFY_LOG=".agent/logs/oda_notifications.log"

# =============================================================================
# MAIN
# =============================================================================

# Read hook input from stdin
HOOK_INPUT=$(cat)

# Parse essential fields
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // "unknown"')

# Only process AskUserQuestion
if [[ "$TOOL_NAME" != "AskUserQuestion" ]]; then
    echo '{"continue": true}'
    exit 0
fi

# Extract Q&A data
TOOL_INPUT=$(echo "$HOOK_INPUT" | jq '.tool_input')
TOOL_RESPONSE=$(echo "$HOOK_INPUT" | jq '.tool_response // empty')
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Check if this is a clarify session (has metadata.source starting with "clarify-")
SOURCE=$(echo "$TOOL_INPUT" | jq -r '.metadata.source // ""')

if [[ "$SOURCE" == clarify-* ]]; then
    # ==========================================================================
    # YAML INTEGRATION MODE (for /clarify sessions)
    # ==========================================================================

    # Find the most recent in-progress clarify log
    LATEST_LOG=$(find "$CLARIFY_LOG_DIR" -name "*.yaml" -type f 2>/dev/null | \
        xargs -I {} sh -c 'grep -l "status: \"in_progress\"" "{}" 2>/dev/null || true' | \
        head -1)

    if [[ -n "$LATEST_LOG" ]] && command -v yq &> /dev/null; then
        # Extract answer from response
        ANSWER=$(echo "$TOOL_RESPONSE" | jq -r '.answers["0"] // "unknown"')

        # Determine which round this answer belongs to
        ROUND_NUM=$(yq '.metadata.rounds' "$LATEST_LOG")

        if [[ "$ROUND_NUM" -gt 0 ]]; then
            # Update the user_response field for the current round
            IDX=$((ROUND_NUM - 1))
            yq -i ".rounds[${IDX}].user_response = \"${ANSWER}\"" "$LATEST_LOG"
            yq -i ".metadata.updated_at = \"${TIMESTAMP}\"" "$LATEST_LOG"

            # Log notification
            echo "[${TIMESTAMP}] CLARIFY-QA-YAML: Updated round ${ROUND_NUM} with response '${ANSWER}'" >> "$NOTIFY_LOG"

            # Return success with YAML context
            jq -n \
                --arg log_path "$LATEST_LOG" \
                --arg round "$ROUND_NUM" \
                --arg answer "$ANSWER" \
                '{
                    continue: true,
                    hookSpecificOutput: {
                        hookEventName: "PostToolUse",
                        mode: "yaml_integration",
                        logPath: $log_path,
                        round: ($round | tonumber),
                        userResponse: $answer
                    }
                }'
            exit 0
        fi
    fi
fi

# =============================================================================
# LEGACY JSONL MODE (for non-clarify sessions or fallback)
# =============================================================================

# Create log directory
mkdir -p "$LEGACY_LOG_DIR"

LOG_FILE="${LEGACY_LOG_DIR}/${SESSION_ID}-qa-audit.jsonl"

# Generate unique Q&A ID
QA_ID="qa-$(date +%s%N | sha256sum | head -c 8)"

# Extract questions and answers
QUESTIONS=$(echo "$TOOL_INPUT" | jq -c '.questions // []')
ANSWERS=$(echo "$TOOL_RESPONSE" | jq -c '.answers // {}')

# Determine answer type
if echo "$TOOL_RESPONSE" | jq -e '.answers | to_entries | .[0].value | contains(",")' > /dev/null 2>&1; then
    ANSWER_TYPE="multi-select"
else
    ANSWER_TYPE="selected-option"
fi

# Build audit log entry
AUDIT_ENTRY=$(jq -n \
    --arg id "$QA_ID" \
    --arg ts "$TIMESTAMP" \
    --arg sid "$SESSION_ID" \
    --arg src "$SOURCE" \
    --arg atype "$ANSWER_TYPE" \
    --argjson questions "$QUESTIONS" \
    --argjson answers "$ANSWERS" \
    '{
        id: $id,
        timestamp: $ts,
        sessionId: $sid,
        source: $src,
        event: "clarification_qa",
        questions: $questions,
        answers: $answers,
        answerType: $atype
    }'
)

# Append to audit log
echo "$AUDIT_ENTRY" >> "$LOG_FILE"

# Log notification
echo "[${TIMESTAMP}] CLARIFY-QA-JSONL: Logged Q&A $QA_ID to $LOG_FILE" >> "$NOTIFY_LOG"

# Return success with context
jq -n \
    --arg qa_id "$QA_ID" \
    --arg log_path "$LOG_FILE" \
    '{
        continue: true,
        hookSpecificOutput: {
            hookEventName: "PostToolUse",
            mode: "jsonl_legacy",
            qaId: $qa_id,
            logPath: $log_path,
            additionalContext: "Q&A exchange logged for traceability"
        }
    }'
