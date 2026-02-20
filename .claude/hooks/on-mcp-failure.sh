#!/usr/bin/env bash
# MCP Tool Failure Handler
# Event: PostToolUseFailure (mcp__tavily|mcp__context7)
# Scope: agent (researcher only)
# Purpose: When research-critical MCP tools fail, inject STOP directive
#          to prevent wasteful WebSearch/WebFetch fallback attempts.
# Output: additionalContext with STOP instruction

set -euo pipefail

INPUT=$(cat)

if command -v jq &>/dev/null; then
    TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
else
    TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)
    SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
fi

[[ -z "$TOOL_NAME" ]] && exit 0

# Only trigger for research-critical MCP tools (tavily, context7)
# sequential-thinking failure is non-critical — warn but don't stop
case "$TOOL_NAME" in
    mcp__tavily__*|mcp__context7__*)
        # Critical: inject STOP directive
        cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "⚠️ CRITICAL MCP FAILURE: Research MCP tool is unavailable. You MUST stop all research work immediately. Do NOT attempt WebSearch or WebFetch as fallback — these waste tokens without MCP-quality results. Write FAIL status to your output file: FAIL|reason:mcp-unavailable|tool:{failed_tool}|action:retry-later. Lead will detect failure via output file micro-signal."
  }
}
EOF
        # Log the failure
        echo "$(date -Iseconds) MCP_CRITICAL_FAIL ${TOOL_NAME} session=${SESSION_ID}" \
            >> "/tmp/mcp-failures.log" 2>/dev/null || true
        ;;
    mcp__sequential-thinking__*)
        # Non-critical: warn but allow continuation
        cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUseFailure",
    "additionalContext": "⚠️ sequential-thinking MCP unavailable. Continue work without it — use internal reasoning instead. This is non-critical."
  }
}
EOF
        ;;
    *)
        # Other MCP tools — generic warning
        exit 0
        ;;
esac

exit 0
