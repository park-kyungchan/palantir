#!/bin/bash
# =============================================================================
# mcp-sequential-enforcer.sh - Enforce Sequential Thinking for All Tasks
# =============================================================================
# Matcher: Task|Edit|Write (tools that benefit from systematic thinking)
# Purpose: Inject sequential thinking requirement before complex operations
#
# This hook adds context reminding the agent to use sequential thinking
# before performing complex tasks.
# =============================================================================

set +e

# Read input
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)

# Tools that require sequential thinking
THINKING_REQUIRED_TOOLS=(
    "Task"
    "Edit"
    "Write"
)

# Check if current tool requires thinking
REQUIRES_THINKING=false
for tool in "${THINKING_REQUIRED_TOOLS[@]}"; do
    if [[ "$TOOL_NAME" == "$tool" ]]; then
        REQUIRES_THINKING=true
        break
    fi
done

if [[ "$REQUIRES_THINKING" == "true" ]]; then
    # Log the enforcement
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] SEQUENTIAL_THINKING_ENFORCED: $TOOL_NAME" \
        >> "${HOME}/.agent/logs/mcp_enforcement.log" 2>/dev/null || true

    # Inject sequential thinking reminder
    cat <<'RESPONSE'
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "additionalContext": "REMINDER: Use mcp__sequential-thinking__sequentialthinking tool BEFORE this operation to ensure systematic reasoning and error prevention."
  }
}
RESPONSE
    exit 0
fi

# Allow without modification for other tools
echo '{}'
exit 0
