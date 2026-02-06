#!/usr/bin/env bash
# hook-timing-test.sh - Measure execution time for each hook script
# Part of INFRA-UPDATE V2.1.33 Diagnostics Suite
set -euo pipefail

SETTINGS_FILE="/home/palantir/.claude/settings.json"
THRESHOLD_MS=5000  # Default threshold: 5 seconds
SLOW_HOOKS=()

if [[ "${1:-}" == "--threshold" && -n "${2:-}" ]]; then
    THRESHOLD_MS="$2"
fi

echo "================================================"
echo "  Hook Timing Test - Claude Code V2.1.33"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Threshold: ${THRESHOLD_MS}ms"
echo "================================================"
echo ""

# Sample input payloads for each event type
declare -A SAMPLE_INPUTS
SAMPLE_INPUTS=(
    ["SessionStart"]='{"session_id":"test-session","cwd":"/home/palantir"}'
    ["UserPromptSubmit"]='{"prompt":"test prompt"}'
    ["PreToolUse"]='{"tool_name":"Read","tool_input":{"file_path":"/dev/null"}}'
    ["PermissionRequest"]='{"tool_name":"Bash","tool_input":{"command":"echo test"}}'
    ["PostToolUse"]='{"tool_name":"Read","tool_input":{"file_path":"/dev/null"},"tool_output":"test"}'
    ["PostToolUseFailure"]='{"tool_name":"Bash","tool_input":{"command":"false"},"error":"test error"}'
    ["Notification"]='{"message":"test","title":"test","notification_type":"info"}'
    ["SubagentStart"]='{"agent_id":"test-agent","agent_type":"explore"}'
    ["SubagentStop"]='{"agent_id":"test-agent","agent_type":"explore"}'
    ["PreCompact"]='{"trigger":"manual"}'
    ["SessionEnd"]='{"session_id":"test-session"}'
)

# Extract hooks from settings.json
python3 -c "
import json

with open('$SETTINGS_FILE') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})
for event, entries in hooks.items():
    if not isinstance(entries, list):
        continue
    for entry in entries:
        hook_list = entry.get('hooks', [])
        for hook in hook_list:
            if hook.get('type') == 'command':
                cmd = hook.get('command', '')
                timeout = hook.get('timeout', 10)
                is_async = hook.get('async', False)
                matcher = entry.get('matcher', 'all')
                print(f'{event}|{cmd}|{timeout}|{is_async}|{matcher}')
" 2>/dev/null | while IFS='|' read -r event cmd timeout is_async matcher; do
    # Skip async hooks (they run in background)
    if [[ "$is_async" == "True" ]]; then
        echo "[SKIP] $event ($matcher): async hook - $cmd"
        continue
    fi

    # Extract script path
    script="$cmd"
    parts=($cmd)
    if [[ "${parts[0]}" == "source" && ${#parts[@]} -gt 1 ]]; then
        script="${parts[1]}"
    fi

    # Check if script exists
    if [[ "$script" == /* && ! -f "$script" ]]; then
        echo "[SKIP] $event ($matcher): script not found - $script"
        continue
    fi

    # Get sample input for event
    sample_input="${SAMPLE_INPUTS[$event]:-'{}'}"

    # Time the execution
    start_ns=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")

    # Run with timeout (max 10s for safety)
    timeout_sec=$(( (timeout + 999) / 1000 ))
    if [[ $timeout_sec -gt 10 ]]; then
        timeout_sec=10
    fi

    # Execute hook with sample input
    result=$(echo "$sample_input" | timeout "${timeout_sec}s" bash -c "$cmd" 2>/dev/null) || true

    end_ns=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time()*1e9))")

    # Calculate duration in ms
    duration_ms=$(( (end_ns - start_ns) / 1000000 ))

    # Determine status
    if [[ $duration_ms -gt $THRESHOLD_MS ]]; then
        status="SLOW"
        SLOW_HOOKS+=("$event:$cmd:${duration_ms}ms")
    elif [[ $duration_ms -gt $(( THRESHOLD_MS / 2 )) ]]; then
        status="WARN"
    else
        status="OK"
    fi

    printf "[%-4s] %-20s (%s): %dms (timeout: %ds)\n" "$status" "$event" "$matcher" "$duration_ms" "$timeout"

    # Validate output is valid JSON (if any)
    if [[ -n "$result" ]]; then
        if echo "$result" | python3 -m json.tool > /dev/null 2>&1; then
            echo "       Output: valid JSON (${#result} chars)"
        else
            echo "       Output: non-JSON (${#result} chars)"
        fi
    fi
done

echo ""
echo "================================================"

if [[ ${#SLOW_HOOKS[@]} -gt 0 ]]; then
    echo "  SLOW HOOKS (>${THRESHOLD_MS}ms):"
    for hook in "${SLOW_HOOKS[@]}"; do
        echo "    - $hook"
    done
else
    echo "  All hooks within threshold (${THRESHOLD_MS}ms)"
fi

echo "================================================"
