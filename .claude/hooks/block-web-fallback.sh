#!/usr/bin/env bash
# WebSearch/WebFetch Blocker for researcher agent
# Event: PreToolUse (WebSearch|WebFetch)
# Scope: agent (researcher only)
# Purpose: Prevent researcher from using WebSearch/WebFetch as MCP fallback.
#          These native tools produce lower-quality results than tavily/context7
#          and waste tokens when MCP is the intended research pathway.
# Exit: 2 (BLOCK) — always blocks, stderr fed back to agent

set -euo pipefail

INPUT=$(cat)

if command -v jq &>/dev/null; then
    TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
else
    TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4)
    SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
fi

# Log the blocked attempt
echo "$(date -Iseconds) BLOCKED ${TOOL_NAME} session=${SESSION_ID}" \
    >> "/tmp/web-fallback-blocked.log" 2>/dev/null || true

# Exit 2 = BLOCK. stderr is fed back to the agent as feedback.
echo "BLOCKED: ${TOOL_NAME} is disabled for researcher agent. Use MCP tools instead: mcp__tavily__search for web search, mcp__context7__resolve-library-id + mcp__context7__query-docs for library docs. If MCP tools are unavailable, STOP work and report FAIL to Lead." >&2
exit 2
