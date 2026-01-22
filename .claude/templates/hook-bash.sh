#!/bin/bash
# {HOOK_NAME} - {HOOK_EVENT}
#
# File: .claude/hooks/{PATH}/{NAME}.sh
# Version: 1.0.0
# Trigger: {HOOK_EVENT} on {MATCHER}
#
# Purpose:
#   {HOOK_DESCRIPTION}
#
# Event Types:
#   PreToolUse     - Before tool execution (can modify, block)
#   PostToolUse    - After tool execution (can block)
#   PermissionRequest - Auto-approve/deny permissions
#   UserPromptSubmit  - Pre-process user input
#   SessionStart   - Session initialization
#   SessionEnd     - Session cleanup
#   SubagentStop   - Control subagent termination
#   Stop           - Prevent session end
#   PreCompact     - Before context compaction
#   Setup          - Environment setup
#   Notification   - Log notifications
#
# Native Capabilities (PreToolUse/PostToolUse):
#   updatedInput      - Modify tool parameters
#   additionalContext - Inject context to Claude
#   permissionDecision - allow | deny | ask

set -euo pipefail

# ============================================
# JSON Helper Functions
# ============================================

json_get() {
    local json="$1"
    local path="$2"
    local default="${3:-}"

    if command -v jq &>/dev/null; then
        echo "$json" | jq -r "$path // \"$default\""
    else
        echo "$json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
path = '$path'.strip('.')
result = data
for key in path.split('.'):
    if key and isinstance(result, dict):
        result = result.get(key, '$default')
print(result if result else '$default')
"
    fi
}

json_stringify() {
    local text="$1"
    if command -v jq &>/dev/null; then
        echo "$text" | jq -Rs .
    else
        python3 -c "import json; print(json.dumps('''$text'''))"
    fi
}

json_add_field() {
    local json="$1"
    local field="$2"
    local value="$3"

    if command -v jq &>/dev/null; then
        echo "$json" | jq -c ". + {\"$field\": $value}"
    else
        local py_value="$value"
        [[ "$value" == "true" ]] && py_value="True"
        [[ "$value" == "false" ]] && py_value="False"
        [[ "$value" == "null" ]] && py_value="None"

        echo "$json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
data['$field'] = $py_value
print(json.dumps(data))
"
    fi
}

# ============================================
# Read Input
# ============================================

INPUT=$(cat)

# ============================================
# Extract Common Fields
# ============================================

TOOL_NAME=$(json_get "$INPUT" ".tool_name" "")
SESSION_ID=$(json_get "$INPUT" ".session_id" "")
CWD=$(json_get "$INPUT" ".cwd" "")
PERMISSION_MODE=$(json_get "$INPUT" ".permission_mode" "")

# Extract tool_input as JSON
if command -v jq &>/dev/null; then
    TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}')
else
    TOOL_INPUT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d.get('tool_input',{})))")
fi

# ============================================
# Hook Logic - TODO(human): Implement
# ============================================

# Example: Check if tool matches pattern
# if [[ "$TOOL_NAME" =~ ^(Bash|Edit|Write)$ ]]; then
#     # Perform validation
# fi

# Example: Modify tool input (updatedInput)
# UPDATED_INPUT=$(json_add_field "$TOOL_INPUT" "timeout" "5000")

# Example: Inject context (additionalContext)
# ADDITIONAL_CONTEXT="Additional information for Claude"

# ============================================
# Output Response
# ============================================

# Basic allow response
cat <<RESPONSE
{
  "hookSpecificOutput": {
    "permissionDecision": "allow"
  }
}
RESPONSE

# ============================================
# Alternative Responses
# ============================================

# Deny with reason:
# cat <<RESPONSE
# {
#   "hookSpecificOutput": {
#     "permissionDecision": "deny",
#     "reason": "Operation not allowed"
#   }
# }
# RESPONSE

# With updatedInput (modify tool parameters):
# cat <<RESPONSE
# {
#   "hookSpecificOutput": {
#     "permissionDecision": "allow",
#     "updatedInput": $UPDATED_INPUT
#   }
# }
# RESPONSE

# With additionalContext (inject info to Claude):
# ESCAPED_CONTEXT=$(json_stringify "$ADDITIONAL_CONTEXT")
# cat <<RESPONSE
# {
#   "hookSpecificOutput": {
#     "permissionDecision": "allow",
#     "additionalContext": $ESCAPED_CONTEXT
#   }
# }
# RESPONSE

# Full response with all capabilities:
# cat <<RESPONSE
# {
#   "hookSpecificOutput": {
#     "permissionDecision": "allow",
#     "updatedInput": $UPDATED_INPUT,
#     "additionalContext": $ESCAPED_CONTEXT
#   }
# }
# RESPONSE
