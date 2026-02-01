#!/bin/bash
# =============================================================================
# permission-guard.sh - PermissionRequest Hook for Dynamic Validation
# =============================================================================
# Provides dynamic permission validation beyond static allow/deny rules.
# Features:
#   1. Audit logging for all permission requests
#   2. Dynamic risk pattern detection (pipe-to-shell, eval, etc.)
#   3. Context-aware validation
#
# Version: 1.0.0
# Exit Codes:
#   0 - Allow/Deny with JSON output
# =============================================================================

set +e

#=============================================================================
# Configuration
#=============================================================================

LOG_DIR="${HOME}/.agent/logs"
LOG_FILE="${LOG_DIR}/permission_requests.log"
RISK_LOG="${LOG_DIR}/permission_risks.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR" 2>/dev/null

#=============================================================================
# JSON Helper
#=============================================================================

HAS_JQ=false
command -v jq &> /dev/null && HAS_JQ=true

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

#=============================================================================
# Risk Pattern Detection
#=============================================================================

# Dynamic risk patterns (beyond static deny rules)
RISK_PATTERNS=(
    # Pipe-to-shell attacks
    "curl.*\\|.*sh"
    "curl.*\\|.*bash"
    "wget.*\\|.*sh"
    "wget.*\\|.*bash"
    # Eval execution
    "eval\\s"
    "\\$\\(.*\\)"
    # Environment variable exposure
    "env\\s*>"
    "printenv.*>"
    "export.*PASSWORD"
    "export.*SECRET"
    "export.*TOKEN"
    "export.*KEY"
    # History manipulation
    "history.*-c"
    "history.*-w"
    # Network exfiltration patterns
    "nc\\s+-e"
    "netcat.*-e"
    # Dangerous redirections
    ">\\/dev\\/sd"
    ">\\/dev\\/null.*2>&1.*&"
    # Git credential exposure
    "git.*config.*credential"
    "git.*credential-store"
)

check_risk_patterns() {
    local input="$1"
    local input_lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')

    for pattern in "${RISK_PATTERNS[@]}"; do
        if echo "$input_lower" | grep -qiE "$pattern" 2>/dev/null; then
            echo "$pattern"
            return 0
        fi
    done

    return 1
}

#=============================================================================
# Main Logic
#=============================================================================

# Read input from stdin
INPUT=$(cat)

# Extract fields
TOOL_NAME=$(json_get '.tool_name' "$INPUT")
TOOL_INPUT=$(json_get '.tool_input' "$INPUT")

# For Bash tool, extract command
COMMAND=""
if [[ "$TOOL_NAME" == "Bash" ]]; then
    COMMAND=$(json_get '.tool_input.command' "$INPUT")
fi

# Timestamp for logging
TIMESTAMP=$(date -Iseconds)

#=============================================================================
# Audit Logging
#=============================================================================

# Log all permission requests (truncated for readability)
INPUT_PREVIEW="${TOOL_INPUT:0:200}"
[[ ${#TOOL_INPUT} -gt 200 ]] && INPUT_PREVIEW="${INPUT_PREVIEW}..."

echo "${TIMESTAMP} | ${TOOL_NAME} | ${INPUT_PREVIEW}" >> "$LOG_FILE" 2>/dev/null

#=============================================================================
# Dynamic Risk Validation (Bash commands only)
#=============================================================================

if [[ "$TOOL_NAME" == "Bash" && -n "$COMMAND" ]]; then
    # Check for dynamic risk patterns
    MATCHED_PATTERN=$(check_risk_patterns "$COMMAND")

    if [[ -n "$MATCHED_PATTERN" ]]; then
        # Log risk detection
        echo "${TIMESTAMP} | RISK_DETECTED | Pattern: ${MATCHED_PATTERN} | Command: ${COMMAND:0:100}" >> "$RISK_LOG" 2>/dev/null

        # Block with explanation
        cat <<RESPONSE
{
  "hookSpecificOutput": {
    "permissionDecision": "block",
    "reason": "Dynamic risk pattern detected: ${MATCHED_PATTERN}. This command matches a potentially dangerous pattern. Please review and use explicit permission if intentional."
  }
}
RESPONSE
        exit 0
    fi
fi

#=============================================================================
# Default: Allow (delegate to static rules)
#=============================================================================

cat <<RESPONSE
{
  "hookSpecificOutput": {
    "permissionDecision": "allow"
  }
}
RESPONSE
