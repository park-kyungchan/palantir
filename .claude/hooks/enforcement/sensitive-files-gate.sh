#!/bin/bash
#=============================================================================
# Sensitive Files Gate
# Version: 1.0.0
#
# Purpose: Enhanced protection for sensitive files (beyond settings.json deny)
# Trigger: PreToolUse (Read|Edit|Write)
#
# Protected Patterns:
#   - .env* (environment files)
#   - *credentials* (credential files)
#   - *secret* (secret files)
#   - .ssh/* (SSH keys)
#   - *.pem, *.key (certificates/keys)
#   - *password* (password files)
#   - *token* (token files, excluding code files)
#   - .npmrc, .pypirc (package manager configs with tokens)
#   - .netrc, .docker/config.json (auth configs)
#
# Logic:
#   1. If Read/Edit/Write targets a sensitive file pattern
#   2. DENY immediately with security warning
#
# Note: This is a defense-in-depth layer on top of settings.json deny rules
#=============================================================================

set -euo pipefail

# Source shared library
SCRIPT_DIR="$(dirname "$0")"
source "${SCRIPT_DIR}/_shared.sh"

#=============================================================================
# Configuration
#=============================================================================

# Sensitive file patterns (case-insensitive matching)
readonly SENSITIVE_PATTERNS=(
    '\.env'
    'credentials'
    'secret'
    '\.ssh/'
    '\.pem$'
    '\.key$'
    'password'
    '\.npmrc$'
    '\.pypirc$'
    '\.netrc$'
    'docker/config\.json$'
    'aws/credentials$'
    'gcloud.*\.json$'
    'service.account.*\.json$'
    'private.*key'
    'api.?key'
    'auth.?token'
)

# Excluded patterns (false positives)
readonly EXCLUDED_PATTERNS=(
    '\.md$'
    '\.txt$'
    'test.*secret'
    'mock.*credential'
    'example.*env'
    'sample.*key'
    '__pycache__'
    'node_modules'
    '\.pyc$'
)

#=============================================================================
# Helper Functions
#=============================================================================

# Check if path matches sensitive patterns
is_sensitive_file() {
    local path="$1"
    local lower_path
    lower_path=$(echo "$path" | tr '[:upper:]' '[:lower:]')

    # Check excluded patterns first
    for pattern in "${EXCLUDED_PATTERNS[@]}"; do
        if echo "$lower_path" | grep -qE "$pattern"; then
            return 1
        fi
    done

    # Check sensitive patterns
    for pattern in "${SENSITIVE_PATTERNS[@]}"; do
        if echo "$lower_path" | grep -qiE "$pattern"; then
            return 0
        fi
    done

    return 1
}

# Get sensitivity type for logging
get_sensitivity_type() {
    local path="$1"
    local lower_path
    lower_path=$(echo "$path" | tr '[:upper:]' '[:lower:]')

    if echo "$lower_path" | grep -qE '\.env'; then
        echo "environment_file"
    elif echo "$lower_path" | grep -qE 'credential'; then
        echo "credentials"
    elif echo "$lower_path" | grep -qE 'secret'; then
        echo "secrets"
    elif echo "$lower_path" | grep -qE '\.ssh/'; then
        echo "ssh_keys"
    elif echo "$lower_path" | grep -qE '\.(pem|key)$'; then
        echo "certificates"
    elif echo "$lower_path" | grep -qE 'password'; then
        echo "passwords"
    elif echo "$lower_path" | grep -qE '(api|auth).?(key|token)'; then
        echo "api_keys"
    else
        echo "sensitive"
    fi
}

#=============================================================================
# Main Logic
#=============================================================================

main() {
    # Read JSON from stdin
    local input
    input=$(cat)

    # Parse tool name and file path
    local tool_name
    local file_path
    tool_name=$(json_get '.tool_name' "$input")
    file_path=$(json_get '.tool_input.file_path' "$input")

    # Only check for Read, Edit, Write tools
    case "$tool_name" in
        Read|Edit|Write)
            ;;
        *)
            output_allow
            exit 0
            ;;
    esac

    # Empty path - allow (will fail naturally)
    [[ -z "$file_path" ]] && { output_allow; exit 0; }

    # Check if file is sensitive
    if ! is_sensitive_file "$file_path"; then
        output_allow
        exit 0
    fi

    # DENY: Sensitive file access
    local sensitivity_type
    sensitivity_type=$(get_sensitivity_type "$file_path")

    local reason="Sensitive File Access Blocked"
    local guidance="Access to sensitive file blocked (${sensitivity_type}). This file may contain sensitive information. Request explicit user confirmation if access is absolutely required."

    log_enforcement "sensitive-files-gate" "deny" "$reason:$sensitivity_type" "$tool_name:$file_path"
    output_deny "$reason" "$guidance"
}

# Execute main
main

exit 0
