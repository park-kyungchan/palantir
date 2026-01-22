#!/bin/bash
# PreToolUse Hook for Task tool - L1/L2 Format Injection
# Version: 2.3.0 (Progressive Disclosure)
#
# Purpose:
#   - Inject L1/L2 format instructions into Task subagent prompts
#   - Add run_in_background=true for parallel execution
#   - Add model="opus" for complex analysis
#   - Skip injection for conversational agents (prompt-assistant)

set -euo pipefail

# Read input from stdin
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')

# Only process Task tool
if [[ "$TOOL_NAME" != "Task" ]]; then
    echo '{}'
    exit 0
fi

# Extract current tool input
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // "{}"')
SUBAGENT_TYPE=$(echo "$TOOL_INPUT" | jq -r '.subagent_type // ""')

# Conversational agents: skip L1/L2 format injection
SKIP_AGENTS=("prompt-assistant" "onboarding-guide" "statusline-setup")
for skip in "${SKIP_AGENTS[@]}"; do
    if [[ "$SUBAGENT_TYPE" == "$skip" ]]; then
        # Allow without L1/L2 format injection
        cat <<RESPONSE
{
  "hookSpecificOutput": {
    "permissionDecision": "allow"
  }
}
RESPONSE
        exit 0
    fi
done

# L1/L2 Format Prompt (V2.3.0 with Progressive Disclosure)
L1L2_PROMPT='## L1/L2 Output Format V2.3.0 (MANDATORY - Progressive Disclosure)

Your output MUST follow this structure:

### L1 Section (Return to Main Agent - MAX 500 TOKENS)
```yaml
taskId: {auto-generate unique 8-char id}
agentType: {Explore|Plan|general-purpose}
summary: |
  1-2 sentence summary (max 200 chars)
status: success | partial | failed

# Progressive Disclosure Fields (REQUIRED)
priority: CRITICAL | HIGH | MEDIUM | LOW
recommendedRead:
  - anchor: "#anchor-name"
    reason: "Brief explanation why this should be read"

findingsCount: {number}
criticalCount: {number}

l2Index:
  - anchor: "#section-name"
    tokens: {estimated tokens for this section}
    priority: CRITICAL | HIGH | MEDIUM | LOW
    description: "what this section contains"

l2Path: .agent/outputs/{agentType}/{taskId}.md
requiresL2Read: true | false
nextActionHint: "suggested next step"
```

### L2 Section (Write to File)
Write detailed output to: .agent/outputs/{agentType}/{taskId}.md
Use markdown anchors (## Section {#anchor}) matching l2Index.
Include estimated token count per section in header comment.

### Priority Guidelines
- CRITICAL: criticalCount > 0 OR blocking issues found
- HIGH: status == partial OR major issues requiring attention
- MEDIUM: status == success with notable findings (findingsCount > 5)
- LOW: status == success with minimal findings

CONSTRAINT: L1 MUST NOT EXCEED 500 TOKENS. Be concise.'

# Build updated input with injections
UPDATED_INPUT=$(echo "$TOOL_INPUT" | jq \
    --arg l1l2 "$L1L2_PROMPT" \
    '. + {
        run_in_background: true,
        model: "opus"
    }')

# Output with additionalContext for L1/L2 prompt
cat <<RESPONSE
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "updatedInput": $UPDATED_INPUT,
    "additionalContext": $(echo "$L1L2_PROMPT" | jq -Rs .)
  }
}
RESPONSE
