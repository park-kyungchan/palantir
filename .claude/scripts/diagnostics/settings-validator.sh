#!/usr/bin/env bash
# settings-validator.sh - Validate settings.json structure and completeness
# Part of INFRA-UPDATE V2.1.33 Diagnostics Suite
set -euo pipefail

SETTINGS_FILE="/home/palantir/.claude/settings.json"
PASS=0
FAIL=0
WARN=0

echo "================================================"
echo "  Settings Validator - Claude Code V2.1.33"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================"
echo ""

# 1. JSON Validity
echo "--- JSON Validity ---"
if python3 -m json.tool "$SETTINGS_FILE" > /dev/null 2>&1; then
    echo "[OK] Valid JSON syntax"
    ((PASS++))
else
    echo "[FAIL] Invalid JSON syntax"
    ((FAIL++))
    echo "FATAL: Cannot continue with invalid JSON"
    exit 1
fi

# 2. Schema Reference
echo ""
echo "--- Schema Reference ---"
python3 -c "
import json
with open('$SETTINGS_FILE') as f:
    s = json.load(f)
schema = s.get('\$schema', '')
if 'schemastore.org' in schema or 'claude-code' in schema:
    print('OK|Schema reference present: ' + schema)
else:
    print('WARN|No schema reference found')
" 2>/dev/null | while IFS='|' read -r status detail; do
    echo "[$status] $detail"
done

# 3. Required Top-Level Keys
echo ""
echo "--- Top-Level Configuration ---"
python3 -c "
import json

with open('$SETTINGS_FILE') as f:
    s = json.load(f)

required = ['hooks']
recommended = ['env', 'statusLine', 'language']

for key in required:
    if key in s:
        print(f'OK|Required key \"{key}\" present')
    else:
        print(f'FAIL|Required key \"{key}\" missing')

for key in recommended:
    if key in s:
        print(f'OK|Recommended key \"{key}\" present')
    else:
        print(f'WARN|Recommended key \"{key}\" missing')
" 2>/dev/null | while IFS='|' read -r status detail; do
    echo "[$status] $detail"
    case "$status" in
        OK) ((PASS++)) 2>/dev/null || true ;;
        FAIL) ((FAIL++)) 2>/dev/null || true ;;
        WARN) ((WARN++)) 2>/dev/null || true ;;
    esac
done

# 4. Hook Event Coverage
echo ""
echo "--- Hook Event Coverage (V2.1.33) ---"

python3 << 'PYEOF'
import json

with open("/home/palantir/.claude/settings.json") as f:
    settings = json.load(f)

hooks = settings.get("hooks", {})

# V2.1.33 Complete Event List
all_events = {
    "SessionStart": "CRITICAL",
    "UserPromptSubmit": "HIGH",
    "PreToolUse": "CRITICAL",
    "PermissionRequest": "MEDIUM",
    "PostToolUse": "CRITICAL",
    "PostToolUseFailure": "MEDIUM",
    "Notification": "LOW",
    "SubagentStart": "MEDIUM",
    "SubagentStop": "MEDIUM",
    "Stop": "HIGH",
    "PreCompact": "HIGH",
    "SessionEnd": "CRITICAL",
}

# Experimental events (V2.1.33)
experimental_events = {
    "TeammateIdle": "EXPERIMENTAL",
    "TaskCompleted": "EXPERIMENTAL",
}

registered = 0
total = len(all_events)

for event, priority in all_events.items():
    if event in hooks:
        entries = hooks[event]
        hook_count = sum(len(e.get("hooks", [])) for e in entries if isinstance(e, dict))
        print(f"OK|{event} ({priority}): {hook_count} hook(s) registered")
        registered += 1
    else:
        status = "FAIL" if priority in ("CRITICAL", "HIGH") else "WARN"
        print(f"{status}|{event} ({priority}): NOT registered")

print(f"INFO|Coverage: {registered}/{total} events registered ({registered*100//total}%)")

# Check experimental
for event, priority in experimental_events.items():
    if event in hooks:
        print(f"INFO|{event} ({priority}): registered (experimental)")
    else:
        print(f"INFO|{event} ({priority}): not registered (optional)")
PYEOF

# 5. Hook Structure Validation
echo ""
echo "--- Hook Structure Validation ---"

python3 << 'PYEOF'
import json

with open("/home/palantir/.claude/settings.json") as f:
    settings = json.load(f)

hooks = settings.get("hooks", {})
issues = []

for event, entries in hooks.items():
    if not isinstance(entries, list):
        print(f"FAIL|{event}: value must be an array, got {type(entries).__name__}")
        continue

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            print(f"FAIL|{event}[{i}]: entry must be an object")
            continue

        hook_list = entry.get("hooks", [])
        if not isinstance(hook_list, list):
            print(f"FAIL|{event}[{i}]: 'hooks' must be an array")
            continue

        matcher = entry.get("matcher", None)
        if matcher:
            print(f"OK|{event}[{i}]: matcher=\"{matcher}\", {len(hook_list)} hook(s)")
        else:
            print(f"OK|{event}[{i}]: no matcher (all tools), {len(hook_list)} hook(s)")

        for j, hook in enumerate(hook_list):
            hook_type = hook.get("type", "command")

            if hook_type == "command":
                if "command" not in hook:
                    print(f"FAIL|{event}[{i}].hooks[{j}]: missing 'command' field")
                else:
                    cmd = hook["command"][:50]
                    timeout = hook.get("timeout", "default")
                    is_async = hook.get("async", False)
                    status_msg = hook.get("statusMessage", None)
                    extras = []
                    if is_async:
                        extras.append("async")
                    if status_msg:
                        extras.append(f"statusMsg=\"{status_msg[:30]}\"")
                    extra_str = f" [{', '.join(extras)}]" if extras else ""
                    print(f"OK|  hook[{j}]: type=command, timeout={timeout}{extra_str}")

            elif hook_type == "prompt":
                if "prompt" not in hook:
                    print(f"FAIL|{event}[{i}].hooks[{j}]: missing 'prompt' field")
                else:
                    prompt = hook["prompt"][:50]
                    timeout = hook.get("timeout", "default")
                    print(f"OK|  hook[{j}]: type=prompt, timeout={timeout}")

            else:
                print(f"WARN|  hook[{j}]: unknown type '{hook_type}'")
PYEOF

# 6. Environment Variables
echo ""
echo "--- Environment Variables ---"

python3 -c "
import json

with open('$SETTINGS_FILE') as f:
    s = json.load(f)

env = s.get('env', {})
if not env:
    print('WARN|No environment variables configured')
else:
    for key, val in env.items():
        # Mask potential secrets
        display_val = val if len(val) < 50 and 'KEY' not in key.upper() and 'SECRET' not in key.upper() else val[:20] + '...'
        print(f'OK|{key}={display_val}')
" 2>/dev/null | while IFS='|' read -r status detail; do
    echo "[$status] $detail"
done

# 7. StatusLine Check
echo ""
echo "--- StatusLine ---"

python3 -c "
import json, os

with open('$SETTINGS_FILE') as f:
    s = json.load(f)

sl = s.get('statusLine', None)
if sl is None:
    print('WARN|No statusLine configured')
elif isinstance(sl, dict):
    sl_type = sl.get('type', 'unknown')
    sl_cmd = sl.get('command', '')
    if sl_type == 'command' and sl_cmd:
        # Extract script path
        parts = sl_cmd.split()
        script = parts[-1] if parts else ''
        if script.startswith('/') and os.path.isfile(script):
            print(f'OK|type={sl_type}, script exists: {script}')
        elif script.startswith('/'):
            print(f'WARN|type={sl_type}, script not found: {script}')
        else:
            print(f'OK|type={sl_type}, command: {sl_cmd[:60]}')
    else:
        print(f'OK|type={sl_type}')
else:
    print(f'WARN|statusLine has unexpected type: {type(sl).__name__}')
" 2>/dev/null | while IFS='|' read -r status detail; do
    echo "[$status] $detail"
done

echo ""
echo "================================================"
echo "  Validation Complete"
echo "================================================"
