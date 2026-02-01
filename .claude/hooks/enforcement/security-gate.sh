#!/bin/bash
#=============================================================================
# security-gate.sh - Block dangerous shell commands
# Version: 1.0.0
#
# Trigger: PreToolUse (Bash)
# Purpose: Prevent execution of dangerous/destructive commands
#=============================================================================

source "$(dirname "$0")/_shared.sh"

# Read stdin JSON
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(json_get '.toolName' "$INPUT")

# Only process Bash commands
if [[ "$TOOL_NAME" != "Bash" ]]; then
    output_allow
    exit 0
fi

# Extract command
COMMAND=$(json_get '.toolInput.command' "$INPUT")

if [[ -z "$COMMAND" ]]; then
    output_allow
    exit 0
fi

# Dangerous patterns to block
# Each pattern is checked against the command
declare -A DANGEROUS_PATTERNS=(
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
COMMAND_LOWER=$(echo "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Check each dangerous pattern
for pattern in "${!DANGEROUS_PATTERNS[@]}"; do
    pattern_lower=$(echo "$pattern" | tr '[:upper:]' '[:lower:]')

    if [[ "$COMMAND_LOWER" == *"$pattern_lower"* ]]; then
        REASON="${DANGEROUS_PATTERNS[$pattern]}"
        log_enforcement "security-gate" "deny" "$REASON: $pattern" "Bash"
        output_deny \
            "Security Block: Dangerous command pattern detected - $REASON" \
            "The command '$pattern' has been blocked for security reasons. This action could cause system damage or data loss."
        exit 0
    fi
done

# Additional regex-based checks
# Check for rm -rf with dangerous paths
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r)\s+/($|[^a-zA-Z])'; then
    log_enforcement "security-gate" "deny" "Recursive force delete on root" "Bash"
    output_deny \
        "Security Block: Recursive force deletion on root or system paths detected" \
        "This command pattern could delete critical system files. Please specify a safer target path."
    exit 0
fi

# Check for chmod with dangerous permissions on sensitive paths
if echo "$COMMAND" | grep -qE 'chmod\s+(777|a\+rwx)\s+/'; then
    log_enforcement "security-gate" "deny" "Insecure permissions on system path" "Bash"
    output_deny \
        "Security Block: Setting insecure permissions (777) on system paths" \
        "World-writable permissions on system paths are a security vulnerability."
    exit 0
fi

# Check for direct writes to block devices
if echo "$COMMAND" | grep -qE '>\s*/dev/(sd|hd|nvme|vd)[a-z]'; then
    log_enforcement "security-gate" "deny" "Direct write to block device" "Bash"
    output_deny \
        "Security Block: Direct write to block device detected" \
        "Writing directly to disk devices can cause irreversible data loss."
    exit 0
fi

# No dangerous patterns found
output_allow
exit 0
