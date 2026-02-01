#!/bin/bash
#=============================================================================
# Security Gate - Block dangerous shell commands
# Version: 1.1.0
#
# Purpose: Prevent execution of dangerous/destructive shell commands
# Trigger: PreToolUse (Bash)
#
# Logic:
#   1. Check if tool is Bash
#   2. Extract command from tool input
#   3. Match command against dangerous patterns (associative array)
#   4. Match command against regex patterns for complex detection
#   5. If dangerous pattern found, DENY with security reason
#
# Exceptions:
#   - Non-Bash tools (always allowed)
#   - Empty commands (allowed - will fail naturally)
#
# Dangerous Pattern Categories:
#   - Recursive deletion (rm -rf /)
#   - Privileged operations (sudo rm)
#   - Permission escalation (chmod 777)
#   - Device access (> /dev/sda)
#   - Fork bombs
#   - Remote code execution (curl | bash)
#   - System control (shutdown, reboot)
#
# Changes in 1.1.0:
#   - Added set -euo pipefail
#   - Added trap for cleanup on error
#   - Standardized JSON field names
#   - Enhanced documentation with pattern categories
#   - Improved error handling
#=============================================================================

set -euo pipefail

# Error cleanup trap - allow on script errors (fail-open for safety)
trap 'output_allow; exit 0' ERR

# Source shared library
source "$(dirname "$0")/_shared.sh"

#=============================================================================
# Main Logic
#=============================================================================

main() {
    # Read stdin JSON
    local input
    input=$(cat)

    # Extract tool name
    local tool_name
    tool_name=$(json_get '.tool_name' "$input")

    # Only process Bash commands
    if [[ "$tool_name" != "Bash" ]]; then
        output_allow
        exit 0
    fi

    # Extract command
    local command
    command=$(json_get '.tool_input.command' "$input")

    if [[ -z "$command" ]]; then
        output_allow
        exit 0
    fi

    # Dangerous patterns to block
    # Each pattern is checked against the command
    local -A DANGEROUS_PATTERNS=(
    ["rm -rf /"]="Recursive deletion of root filesystem"
    ["rm -rf /*"]="Recursive deletion of root contents"
    ["rm -fr /"]="Recursive deletion of root filesystem"
    ["sudo rm"]="Privileged deletion command"
    ["chmod 777"]="Insecure permission change (world-writable)"
    ["> /dev/sda"]="Direct write to disk device"
    [">/dev/sda"]="Direct write to disk device"
    ["mkfs."]="Filesystem format command"
    ["dd if="]="Low-level disk operation"
    [":(){:|:&};:"]="Fork bomb"
    [":(){ :|:& };:"]="Fork bomb with spaces"
    ["wget -O- | sh"]="Arbitrary code execution from URL"
    ["curl | sh"]="Arbitrary code execution from URL"
    ["curl | bash"]="Arbitrary code execution from URL"
    ["wget | bash"]="Arbitrary code execution from URL"
    ["> /dev/null 2>&1 &"]="Silent background execution (suspicious)"
    ["rm -rf ~"]="Home directory deletion"
    ["rm -rf $HOME"]="Home directory deletion"
    ["shutdown"]="System shutdown command"
    ["reboot"]="System reboot command"
    ["init 0"]="System halt command"
    ["init 6"]="System reboot command"
    )

    # Convert command to lowercase for case-insensitive matching
    local command_lower
    command_lower=$(echo "$command" | tr '[:upper:]' '[:lower:]')

    # Check each dangerous pattern
    local pattern pattern_lower reason
    for pattern in "${!DANGEROUS_PATTERNS[@]}"; do
        pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')

        if [[ "$command_lower" == *"$pattern_lower"* ]]; then
            reason="${DANGEROUS_PATTERNS[$pattern]}"
            log_enforcement "security-gate" "deny" "$reason: $pattern" "Bash"
            output_deny \
                "Security Block: Dangerous command pattern detected - $reason" \
                "The command '$pattern' has been blocked for security reasons. This action could cause system damage or data loss."
            exit 0
        fi
    done

    # Additional regex-based checks
    # Check for rm -rf with dangerous paths
    if echo "$command" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+/($|[^a-zA-Z])'; then
        log_enforcement "security-gate" "deny" "Recursive force delete on root" "Bash"
        output_deny \
            "Security Block: Recursive force deletion on root or system paths detected" \
            "This command pattern could delete critical system files. Please specify a safer target path."
        exit 0
    fi

    # Check for chmod with dangerous permissions on sensitive paths
    if echo "$command" | grep -qE 'chmod\s+(777|a\+rwx)\s+/'; then
        log_enforcement "security-gate" "deny" "Insecure permissions on system path" "Bash"
        output_deny \
            "Security Block: Setting insecure permissions (777) on system paths" \
            "World-writable permissions on system paths are a security vulnerability."
        exit 0
    fi

    # Check for direct writes to block devices
    if echo "$command" | grep -qE '>\s*/dev/(sd|hd|nvme|vd)[a-z]'; then
        log_enforcement "security-gate" "deny" "Direct write to block device" "Bash"
        output_deny \
            "Security Block: Direct write to block device detected" \
            "Writing directly to disk devices can cause irreversible data loss."
        exit 0
    fi

    # No dangerous patterns found
    output_allow
}

# Execute main
main

exit 0
