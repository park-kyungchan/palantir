#!/bin/bash
# =============================================================================
# pd-context-injector.sh - PreToolUse Hook for Context Injection
# =============================================================================
# Injects project-specific context before tool execution.
# Matcher: Edit, Write, Task
# =============================================================================

set +e
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

case "$TOOL_NAME" in
    "Edit"|"Write")
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "Code Style: Follow existing patterns. Preserve L1/L2/L3 output compatibility. No new dependencies without approval."
  }
}
EOF
        ;;
    "Task")
        SUBAGENT_TYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // empty')
        case "$SUBAGENT_TYPE" in
            "Explore"|"Plan"|"general-purpose")
                SESSION_ID=$(cat ~/.agent/tmp/current_session.json 2>/dev/null | jq -r '.sessionId // "unknown"')
                cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "Output Format: L1/L2/L3 Progressive Disclosure required. Write L2/L3 to .agent/outputs/{agentType}/. Session: $SESSION_ID"
  }
}
EOF
                ;;
        esac
        ;;
esac

exit 0
