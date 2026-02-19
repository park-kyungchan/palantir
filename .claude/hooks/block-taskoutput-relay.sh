#!/usr/bin/env bash
# PreToolUse:TaskOutput hook — blocks Data Relay Tax (RSIL insight)
# Blocks TaskOutput(block:true) in Lead context to prevent full subagent
# output from flooding Lead's context window.
# Allows TaskOutput(block:false) for lightweight status checks.
# Exit: 0 (allow) or 0 + permissionDecision:"deny" (block with additionalContext)

set -euo pipefail

INPUT=$(cat)

# Extract fields from stdin JSON
if command -v jq &>/dev/null; then
  BLOCK_VALUE=$(echo "$INPUT" | jq -r '.tool_input.block // true')
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
else
  # Fallback: assume block=true (default) if we can't parse
  BLOCK_VALUE="true"
  SESSION_ID=""
fi

# Allow non-blocking status checks (block:false)
if [[ "$BLOCK_VALUE" == "false" ]]; then
  exit 0
fi

# Session_id guard (BUG-007): only enforce in Lead context
# In teammate/subagent contexts, TaskOutput may be legitimate
TEAM_CONFIG=$(find ~/.claude/teams/ -name "config.json" -print -quit 2>/dev/null)
if [[ -n "$TEAM_CONFIG" ]]; then
  LEAD_SESSION=$(jq -r '.leadSessionId // empty' "$TEAM_CONFIG" 2>/dev/null)
  if [[ -n "$LEAD_SESSION" && -n "$SESSION_ID" && "$SESSION_ID" != "$LEAD_SESSION" ]]; then
    exit 0  # Non-lead session — allow
  fi
fi

# Log the blocked attempt
echo "$(date -Iseconds) BLOCKED TaskOutput(block:true) session=${SESSION_ID}" \
  >> "/tmp/taskoutput-relay-blocked.log" 2>/dev/null || true

# Exit 0 + permissionDecision:"deny" — blocks tool call AND injects
# additionalContext into Lead's next turn for reinforced guidance.
# (exit 2 only feeds stderr; exit 0 parses stdout JSON for both fields)
cat <<'HOOK_JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "additionalContext": "DATA RELAY TAX BLOCKED: TaskOutput(block:true) denied. Lead MUST NOT read full subagent/teammate output into its context window. Alternatives: (1) TaskOutput(block:false) for status checks only, (2) Read the output_file path returned by Task(run_in_background:true) and pass it downstream via $ARGUMENTS — let the consuming agent read the file directly, (3) In team mode rely on Ch3 micro-signals via SendMessage. The anti-pattern costs ~10k tokens per relay for zero orchestration value."
  }
}
HOOK_JSON
exit 0
