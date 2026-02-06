#!/usr/bin/env bash
# hook-health-check.sh - Verify all registered hooks have valid scripts
# Part of INFRA-UPDATE V2.1.33 Diagnostics Suite
set -euo pipefail

SETTINGS_FILE="/home/palantir/.claude/settings.json"
PASS=0
FAIL=0
WARN=0
ERRORS=()

echo "================================================"
echo "  Hook Health Check - Claude Code V2.1.33"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"
echo ""

# Check settings.json exists
if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo "FATAL: settings.json not found at $SETTINGS_FILE"
    exit 1
fi

# Validate JSON syntax
if ! python3 -m json.tool "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo "FATAL: settings.json is not valid JSON"
    exit 1
fi
echo "[OK] settings.json is valid JSON"
((PASS++))

# All 12 V2.1.33 hook events
EXPECTED_EVENTS=(
    "SessionStart"
    "UserPromptSubmit"
    "PreToolUse"
    "PermissionRequest"
    "PostToolUse"
    "PostToolUseFailure"
    "Notification"
    "SubagentStart"
    "SubagentStop"
    "Stop"
    "PreCompact"
    "SessionEnd"
)

echo ""
echo "--- Hook Event Registration ---"

for event in "${EXPECTED_EVENTS[@]}"; do
    if python3 -c "
import json, sys
with open('$SETTINGS_FILE') as f:
    s = json.load(f)
hooks = s.get('hooks', {})
if '$event' in hooks:
    sys.exit(0)
else:
    sys.exit(1)
" 2>/dev/null; then
        echo "[OK] $event: registered"
        ((PASS++))
    else
        echo "[FAIL] $event: NOT registered"
        ERRORS+=("Event '$event' not registered in settings.json")
        ((FAIL++))
    fi
done

echo ""
echo "--- Script File Checks ---"

# Extract all command hooks and check their scripts exist + executable
python3 -c "
import json, os

with open('$SETTINGS_FILE') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})
results = []

for event, entries in hooks.items():
    if not isinstance(entries, list):
        continue
    for entry in entries:
        hook_list = entry.get('hooks', [])
        for hook in hook_list:
            if hook.get('type') == 'command':
                cmd = hook.get('command', '')
                # Extract the script path (first word of command)
                parts = cmd.split()
                if parts:
                    script = parts[0]
                    # Skip 'source' keyword
                    if script == 'source' and len(parts) > 1:
                        script = parts[1]
                    # Only check absolute paths
                    if script.startswith('/'):
                        exists = os.path.isfile(script)
                        executable = os.access(script, os.X_OK) if exists else False
                        results.append((event, script, exists, executable))

for event, script, exists, executable in results:
    if not exists:
        print(f'FAIL|{event}|{script}|Script not found')
    elif not executable:
        print(f'WARN|{event}|{script}|Script not executable')
    else:
        print(f'OK|{event}|{script}|Healthy')
" 2>/dev/null | while IFS='|' read -r status event script detail; do
    case "$status" in
        OK)
            echo "[OK] $event: $script - $detail"
            ((PASS++)) 2>/dev/null || true
            ;;
        WARN)
            echo "[WARN] $event: $script - $detail"
            ((WARN++)) 2>/dev/null || true
            ;;
        FAIL)
            echo "[FAIL] $event: $script - $detail"
            ((FAIL++)) 2>/dev/null || true
            ;;
    esac
done

echo ""
echo "--- Prompt Hook Checks ---"

python3 -c "
import json

with open('$SETTINGS_FILE') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})
count = 0
for event, entries in hooks.items():
    if not isinstance(entries, list):
        continue
    for entry in entries:
        hook_list = entry.get('hooks', [])
        for hook in hook_list:
            if hook.get('type') == 'prompt':
                prompt = hook.get('prompt', '')[:80]
                timeout = hook.get('timeout', 'default')
                print(f'OK|{event}|prompt hook|timeout={timeout}s, prompt=\"{prompt}...\"')
                count += 1

if count == 0:
    print('INFO|N/A|No prompt hooks configured|')
" 2>/dev/null | while IFS='|' read -r status event detail extra; do
    echo "[$status] $event: $detail $extra"
done

echo ""
echo "--- Async Hook Checks ---"

python3 -c "
import json

with open('$SETTINGS_FILE') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})
count = 0
for event, entries in hooks.items():
    if not isinstance(entries, list):
        continue
    for entry in entries:
        hook_list = entry.get('hooks', [])
        for hook in hook_list:
            if hook.get('async', False):
                cmd = hook.get('command', '')[:60]
                timeout = hook.get('timeout', 'default')
                print(f'OK|{event}|async hook|timeout={timeout}s, cmd=\"{cmd}\"')
                count += 1

if count == 0:
    print('INFO|N/A|No async hooks configured|')
" 2>/dev/null | while IFS='|' read -r status event detail extra; do
    echo "[$status] $event: $detail $extra"
done

echo ""
echo "================================================"
echo "  Results: PASS=$PASS  FAIL=$FAIL  WARN=$WARN"
echo "================================================"

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo ""
    echo "Errors:"
    for err in "${ERRORS[@]}"; do
        echo "  - $err"
    done
fi

exit $FAIL
