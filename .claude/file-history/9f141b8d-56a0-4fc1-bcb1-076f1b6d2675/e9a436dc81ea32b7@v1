#!/bin/bash
# =============================================================================
# Claude Code Governance Pre-Tool Hook
# =============================================================================
# Validates operations against blocked patterns before execution.
# Blocks dangerous commands and sensitive file access.
#
# Exit Codes:
#   0 - Allow (with JSON output)
#   2 - Deny (with JSON output)
# =============================================================================

# Don't exit on error - handle failures gracefully
set +e

#=============================================================================
# JSON Helper
#=============================================================================

HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

# Extract JSON field
# Usage: json_get field json_string
json_get() {
    local field="$1"
    local json="$2"

    if $HAS_JQ; then
        echo "$json" | jq -r "$field // empty" 2>/dev/null || echo ""
    else
        echo "$json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    keys = '$field'.lstrip('.').split('.')
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, '')
        else:
            val = ''
    print(val if val else '')
except:
    print('')
" 2>/dev/null || echo ""
    fi
}

# Output deny decision
output_deny() {
    local reason="$1"
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$reason"
  }
}
EOF
}

# Output allow decision
output_allow() {
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
EOF
}

#=============================================================================
# Main Logic
#=============================================================================

# Read input from stdin (JSON format)
INPUT=$(cat)

# Extract tool name and parameters
TOOL_NAME=$(json_get '.tool_name' "$INPUT")
TOOL_INPUT=$(json_get '.tool_input' "$INPUT")

# If we couldn't parse, allow (fail open for parsing errors only)
if [ -z "$TOOL_NAME" ]; then
    output_allow
    exit 0
fi

# Define blocked patterns for Bash commands
BLOCKED_PATTERNS=(
    "rm -rf"
    "sudo rm"
    "chmod 777"
    "DROP TABLE"
    "DROP DATABASE"
    "TRUNCATE TABLE"
)

# Check for blocked patterns in Bash commands
if [ "$TOOL_NAME" = "Bash" ]; then
    COMMAND=$(json_get '.command' "$TOOL_INPUT")

    for pattern in "${BLOCKED_PATTERNS[@]}"; do
        if echo "$COMMAND" | grep -q "$pattern"; then
            output_deny "Blocked pattern detected: $pattern"
            exit 2  # Deny
        fi
    done
fi

# Check for sensitive file access
if [ "$TOOL_NAME" = "Read" ] || [ "$TOOL_NAME" = "Edit" ] || [ "$TOOL_NAME" = "Write" ]; then
    FILE_PATH=$(json_get '.file_path' "$TOOL_INPUT")

    # Block access to sensitive files
    SENSITIVE_PATTERNS=(
        ".env"
        "credentials"
        "secrets"
        ".ssh/id_"
        "private_key"
    )

    for pattern in "${SENSITIVE_PATTERNS[@]}"; do
        if echo "$FILE_PATH" | grep -qi "$pattern"; then
            output_deny "Access to sensitive file blocked: $FILE_PATH"
            exit 2  # Deny
        fi
    done
fi

# Allow operation
output_allow
exit 0
