#!/bin/bash
# ODA Governance Pre-Tool Hook
# Validates operations against blocked patterns before execution

set -e

# Read input from stdin (JSON format)
INPUT=$(cat)

# Extract tool name and parameters
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // empty')

# Define blocked patterns
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
    COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty')

    for pattern in "${BLOCKED_PATTERNS[@]}"; do
        if echo "$COMMAND" | grep -q "$pattern"; then
            echo '{"decision": "deny", "reason": "Blocked pattern detected: '"$pattern"'"}' >&2
            exit 2  # Deny
        fi
    done
fi

# Check for sensitive file access
if [ "$TOOL_NAME" = "Read" ] || [ "$TOOL_NAME" = "Edit" ] || [ "$TOOL_NAME" = "Write" ]; then
    FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.file_path // empty')

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
            echo '{"decision": "deny", "reason": "Access to sensitive file blocked: '"$FILE_PATH"'"}' >&2
            exit 2  # Deny
        fi
    done
fi

# Allow operation
echo '{"decision": "allow"}'
exit 0
