#!/bin/bash
# =============================================================================
# mcp-sequential-logger.sh - Log Sequential Thinking Usage
# =============================================================================
# Matcher: mcp__sequential-thinking__sequentialthinking
# Purpose: Track and audit sequential thinking tool usage
# =============================================================================

set +e

# Read input
INPUT=$(cat)

# Extract details
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty' 2>/dev/null)
THOUGHT_NUM=$(echo "$INPUT" | jq -r '.tool_input.thoughtNumber // "?"' 2>/dev/null)
TOTAL_THOUGHTS=$(echo "$INPUT" | jq -r '.tool_input.totalThoughts // "?"' 2>/dev/null)

# Ensure log directory exists
mkdir -p "${HOME}/.agent/logs" 2>/dev/null

# Log usage
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat <<EOF >> "${HOME}/.agent/logs/sequential_thinking.log"
[$TIMESTAMP] EVENT: $HOOK_EVENT | TOOL: $TOOL_NAME | THOUGHT: $THOUGHT_NUM/$TOTAL_THOUGHTS
EOF

# Allow and continue
cat <<'RESPONSE'
{
  "hookSpecificOutput": {
    "permissionDecision": "allow"
  }
}
RESPONSE

exit 0
