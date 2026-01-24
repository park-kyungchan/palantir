#!/bin/bash
# =============================================================================
# Claude Code PreToolUse Hook - L1/L2 Format Injection
# =============================================================================
# Injects L1/L2 format instructions into Task subagent prompts.
# Adds run_in_background=true and model="opus" for complex analysis.
# Skips injection for conversational agents.
#
# Matcher: Task
# Exit Codes:
#   0 - Allow (with JSON output)
# =============================================================================

# Don't exit on error - handle failures gracefully
set +e

#=============================================================================
# JSON Helper
#=============================================================================

HAS_JQ=false
if command -v jq &> /dev/null; then
    HAS_JQ=true
fi

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
# Main Logic
#=============================================================================

# Read input from stdin
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(json_get '.tool_name' "$INPUT")

# Only process Task tool
if [[ "$TOOL_NAME" != "Task" ]]; then
    echo '{}'
    exit 0
fi

# Extract current tool input and subagent type
# Note: Get subagent_type directly from nested path to avoid double-parsing
TOOL_INPUT=$(json_get '.tool_input' "$INPUT")
SUBAGENT_TYPE=$(json_get '.tool_input.subagent_type' "$INPUT")

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

#=============================================================================
# Build Updated Input
#=============================================================================

build_updated_input() {
    local tool_input="$1"

    if $HAS_JQ; then
        echo "$tool_input" | jq '. + {
            run_in_background: true,
            model: "opus"
        }' 2>/dev/null
    else
        # Use stdin to avoid shell escaping issues with JSON content
        echo "$tool_input" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    data['run_in_background'] = True
    data['model'] = 'opus'
    print(json.dumps(data))
except:
    print('{}')
" 2>/dev/null || echo '{}'
    fi
}

escape_json_string() {
    local str="$1"

    if $HAS_JQ; then
        echo "$str" | jq -Rs . 2>/dev/null
    else
        # Use stdin to avoid shell escaping issues
        echo "$str" | python3 -c "
import json, sys
print(json.dumps(sys.stdin.read()))
" 2>/dev/null || echo '""'
    fi
}

UPDATED_INPUT=$(build_updated_input "$TOOL_INPUT")
ESCAPED_L1L2=$(escape_json_string "$L1L2_PROMPT")

# Output with additionalContext for L1/L2 prompt
cat <<RESPONSE
{
  "hookSpecificOutput": {
    "permissionDecision": "allow",
    "updatedInput": $UPDATED_INPUT,
    "additionalContext": $ESCAPED_L1L2
  }
}
RESPONSE
