#!/bin/bash
# =============================================================================
# Orion ODA - Session Health Monitor Hook
# =============================================================================
# Boris Cherny Pattern 12: Session Discard
#
# "If the agent gets stuck in a loop or goes down a wrong path,
# I just kill it and start fresh - cheaper than trying to fix context."
#
# Hook Type: PostToolUse
# Triggers: After every tool call
# Purpose: Track tool usage patterns and detect dead-ends
#
# Environment Variables (from Claude Code):
#   CLAUDE_SESSION_ID - Current session ID
#   CLAUDE_TOOL_NAME - Name of the tool that was called
#   CLAUDE_TOOL_INPUT - JSON input to the tool
#   CLAUDE_TOOL_OUTPUT - JSON output from the tool (truncated)
#
# Exit Codes:
#   0 - Success, continue
#   2 - Block (if health is terminal - NOT recommended, prefer warnings)
# =============================================================================

set -e

# Configuration
WORKSPACE_ROOT="${ORION_WORKSPACE_ROOT:-/home/palantir}"
AGENT_TMP_DIR="$WORKSPACE_ROOT/park-kyungchan/palantir/.agent/tmp"
HEALTH_LOG="$AGENT_TMP_DIR/session_health.jsonl"
TOOL_HISTORY_FILE="$AGENT_TMP_DIR/tool_history_${CLAUDE_SESSION_ID:-unknown}.jsonl"

# Thresholds
HEALTH_CHECK_INTERVAL=10  # Check health every N tool calls
REPETITION_WARNING_THRESHOLD=5  # Warn if same tool+input seen N times

# Ensure directories exist
mkdir -p "$AGENT_TMP_DIR" 2>/dev/null || true

# Parse input
TOOL_NAME="${CLAUDE_TOOL_NAME:-unknown}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-{}}"
TOOL_OUTPUT="${CLAUDE_TOOL_OUTPUT:-{}}"
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Determine success based on output
SUCCESS="true"
if echo "$TOOL_OUTPUT" | grep -qi '"error"' 2>/dev/null; then
    SUCCESS="false"
fi

# Create input hash for repetition detection
if command -v md5sum &> /dev/null; then
    INPUT_HASH=$(echo -n "$TOOL_INPUT" | md5sum | cut -c1-8)
elif command -v md5 &> /dev/null; then
    INPUT_HASH=$(echo -n "$TOOL_INPUT" | md5 | cut -c1-8)
else
    INPUT_HASH="no-hash"
fi

# Log tool call to history
TOOL_RECORD="{\"timestamp\":\"$TIMESTAMP\",\"session_id\":\"$SESSION_ID\",\"tool\":\"$TOOL_NAME\",\"input_hash\":\"$INPUT_HASH\",\"success\":$SUCCESS}"
echo "$TOOL_RECORD" >> "$TOOL_HISTORY_FILE"

# Count tool calls in session
CALL_COUNT=$(wc -l < "$TOOL_HISTORY_FILE" 2>/dev/null || echo "0")

# Quick repetition check
check_repetition() {
    local signature="$TOOL_NAME:$INPUT_HASH"
    local count=0

    if [ -f "$TOOL_HISTORY_FILE" ]; then
        # Count occurrences of this exact tool+input combination
        count=$(grep -c "\"tool\":\"$TOOL_NAME\".*\"input_hash\":\"$INPUT_HASH\"" "$TOOL_HISTORY_FILE" 2>/dev/null || echo "0")
    fi

    echo "$count"
}

# Check for repetitive patterns
REPETITION_COUNT=$(check_repetition)

if [ "$REPETITION_COUNT" -ge "$REPETITION_WARNING_THRESHOLD" ]; then
    # Log warning
    echo "{\"timestamp\":\"$TIMESTAMP\",\"session_id\":\"$SESSION_ID\",\"type\":\"repetition_warning\",\"tool\":\"$TOOL_NAME\",\"count\":$REPETITION_COUNT}" >> "$HEALTH_LOG"

    # Output warning (will be shown to user via hook output)
    echo "{\"warning\":\"Repetitive pattern detected\",\"tool\":\"$TOOL_NAME\",\"occurrences\":$REPETITION_COUNT,\"suggestion\":\"Consider a different approach\"}"
fi

# Periodic full health check
if [ $((CALL_COUNT % HEALTH_CHECK_INTERVAL)) -eq 0 ] && [ "$CALL_COUNT" -gt 0 ]; then
    # Run Python health evaluation in background (non-blocking)
    python3 -c "
import sys
sys.path.insert(0, '$WORKSPACE_ROOT/park-kyungchan/palantir')

try:
    import asyncio
    from scripts.claude.session_health import get_health_monitor

    async def check():
        monitor = get_health_monitor()
        report = await monitor.evaluate()

        import json
        print(json.dumps({
            'health_check': True,
            'status': report.metrics.status,
            'overall_health': round(report.metrics.overall_health, 2),
            'should_terminate': report.should_terminate,
            'termination_reason': report.termination_reason,
            'recommendations': report.recommendations[:2] if len(report.recommendations) > 2 else report.recommendations
        }))

    asyncio.run(check())
except Exception as e:
    print('{\"health_check\":false,\"error\":\"' + str(e).replace('\"', '\\\\\"') + '\"}')
" 2>/dev/null || true
fi

# Simple pattern detection without Python
detect_simple_loop() {
    if [ ! -f "$TOOL_HISTORY_FILE" ]; then
        return
    fi

    # Get last 10 tool names
    local recent_tools=$(tail -10 "$TOOL_HISTORY_FILE" 2>/dev/null | grep -o '"tool":"[^"]*"' | cut -d'"' -f4)

    # Check for A-B-A-B pattern (simple loop)
    local tools_array=($recent_tools)
    local len=${#tools_array[@]}

    if [ "$len" -ge 4 ]; then
        if [ "${tools_array[$len-1]}" = "${tools_array[$len-3]}" ] && \
           [ "${tools_array[$len-2]}" = "${tools_array[$len-4]}" ]; then
            echo "{\"timestamp\":\"$TIMESTAMP\",\"type\":\"loop_detected\",\"pattern\":\"${tools_array[$len-2]}-${tools_array[$len-1]}\"}" >> "$HEALTH_LOG"
            echo "{\"warning\":\"Possible loop detected\",\"pattern\":[\"${tools_array[$len-2]}\",\"${tools_array[$len-1]}\"],\"suggestion\":\"Try breaking the cycle\"}"
        fi
    fi
}

# Run simple loop detection
detect_simple_loop

# Output standard completion (ensures hook doesn't block)
echo "{\"status\":\"recorded\",\"tool\":\"$TOOL_NAME\",\"call_count\":$CALL_COUNT}"

exit 0
