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

# Log the blocked attempt
echo "$(date -Iseconds) BLOCKED TaskOutput(block:true) session=${SESSION_ID}" \
  >> "/tmp/taskoutput-relay-blocked.log" 2>/dev/null || true

# Stderr message for operator visibility (exit 2 path is not used here,
# but stderr is still surfaced in hook logs)
echo "CE-BLOCK: TaskOutput is prohibited for Lead (Data Relay Tax)." >&2
echo "Correct pattern:" >&2
echo "  1. Spawn with run_in_background:true" >&2
echo "  2. Receive auto-notification on completion" >&2
echo "  3. Read output file via Read tool if details needed" >&2
echo "  Never use TaskOutput — it floods Lead context with subagent data." >&2

# Exit 0 + permissionDecision:"deny" — blocks tool call AND injects
# additionalContext into Lead's next turn for reinforced guidance.
# (exit 2 only feeds stderr; exit 0 parses stdout JSON for both fields)
cat <<'HOOK_JSON'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "additionalContext": "DATA RELAY TAX BLOCKED: TaskOutput(block:true) denied. Lead MUST NOT read full subagent output into its context window. Alternatives: (1) TaskOutput(block:false) for status checks only, (2) Read the output_file path returned by Task(run_in_background:true) and pass it downstream via $ARGUMENTS — let the consuming agent read the file directly. The anti-pattern costs ~10k tokens per relay for zero orchestration value."
  }
}
HOOK_JSON
exit 0
