---
name: hook-builder
description: |
  Interactive Hook definition builder.
  Creates standalone hook scripts or settings.json configurations.
context: fork
model: sonnet
version: "1.0.0"
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
  - Write
---

# Hook Builder

> **Purpose:** Hook 스크립트 및 설정 생성
> **Caller:** /build hook, SKILL.md orchestrator
> **Output:** `.claude/hooks/{name}.sh` or `.claude/settings.json` update

---

## Hook Configuration Overview (V2.1.19)

### Hook Events

| Event | Trigger | Common Use Cases |
|-------|---------|------------------|
| `PreToolUse` | 도구 실행 전 | 입력 검증, 차단, 로깅 |
| `PostToolUse` | 도구 실행 후 | 결과 처리, 알림 |
| `Notification` | 알림 발생 시 | 외부 알림 연동 |
| `Stop` | 세션 종료 시 | 정리 작업, 상태 저장 |
| `SubagentStop` | 서브에이전트 종료 | 결과 수집 |

### Hook Levels

| Level | Location | Scope |
|-------|----------|-------|
| Global | `settings.json` → `hooks` | 모든 세션 |
| Skill | `SKILL.md` → `hooks:` | 해당 Skill만 |

---

## Round 1: Hook Level

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Hook을 어디에 설정할까요?",
        "header": "Level",
        "options": [
            {
                "label": "Global (settings.json)",
                "description": "모든 세션에서 실행되는 전역 Hook"
            },
            {
                "label": "Skill-level",
                "description": "특정 Skill 내에서만 실행되는 Hook"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-hook-level"}
)
```

### Level Decision Guide

| Scenario | Recommended Level |
|----------|-------------------|
| 보안 검증 (모든 Bash) | Global |
| 특정 Skill 후처리 | Skill-level |
| 로깅/감사 | Global |
| 상태 저장 | Skill-level |

---

## Round 2: Event Selection

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Hook을 트리거할 이벤트를 선택하세요",
        "header": "Event",
        "options": [
            {
                "label": "PreToolUse (Recommended)",
                "description": "도구 실행 전 - 검증, 차단 가능"
            },
            {
                "label": "PostToolUse",
                "description": "도구 실행 후 - 결과 처리"
            },
            {
                "label": "Stop",
                "description": "세션/Skill 종료 시"
            },
            {
                "label": "Notification",
                "description": "알림 발생 시"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-hook-event"}
)
```

### Event Details

| Event | Input Available | Can Block | Typical Actions |
|-------|-----------------|-----------|-----------------|
| PreToolUse | tool_name, tool_input | ✓ | 검증, 필터링 |
| PostToolUse | tool_name, tool_input, tool_output | ✗ | 로깅, 알림 |
| Stop | session_info | ✗ | 정리, 저장 |
| SubagentStop | agent_id, result | ✗ | 결과 수집 |
| Notification | message, level | ✗ | 외부 연동 |

---

## Round 3: Hook Configuration

> **Delegate to:** `parameters/hook-config.md`

### Delegation Flow

```python
# Call shared module
hook_result = delegate_to("parameters/hook-config.md", {
    "hook_event": selected_event,
    "component_type": "hook"
})

# Receive result
hook_type = hook_result["type"]        # "command" or "prompt"
matcher = hook_result["matcher"]        # regex pattern
once = hook_result["once"]              # boolean
timeout = hook_result["timeout"]        # ms
command = hook_result.get("command")    # if type=command
prompt = hook_result.get("prompt")      # if type=prompt
```

---

## Round 4: Script Template (type=command)

### Q&A Flow

```python
if hook_type == "command":
    response = AskUserQuestion(
        questions=[{
            "question": "Hook 스크립트 언어를 선택하세요",
            "header": "Language",
            "options": [
                {
                    "label": "Bash (Recommended)",
                    "description": "가볍고 빠른 쉘 스크립트"
                },
                {
                    "label": "Python",
                    "description": "복잡한 로직 처리에 적합"
                },
                {
                    "label": "Node.js",
                    "description": "JSON 처리에 편리"
                }
            ],
            "multiSelect": False
        }],
        metadata={"source": "build-hook-language"}
    )
```

---

## Round 5: Hook Action

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Hook이 수행할 주요 동작은?",
        "header": "Action",
        "options": [
            {
                "label": "검증 (Validation)",
                "description": "입력 검증 후 차단/허용"
            },
            {
                "label": "로깅 (Logging)",
                "description": "실행 기록 저장"
            },
            {
                "label": "변환 (Transform)",
                "description": "입력/출력 변환"
            },
            {
                "label": "알림 (Notification)",
                "description": "외부 시스템에 알림"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-hook-action"}
)
```

### Action Templates

| Action | Exit Code | Output |
|--------|-----------|--------|
| Validation | 0=허용, 1=차단 | 차단 사유 출력 |
| Logging | 0 (항상) | 없음 |
| Transform | 0 | 변환된 데이터 |
| Notification | 0 | 알림 상태 |

---

## Output Generation

### Bash Script Template

```bash
#!/bin/bash
# Hook: {hook_name}
# Event: {event_type}
# Created: {timestamp}

# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================
# $CC_HOOK_EVENT    - Event type (PreToolUse, PostToolUse, etc.)
# $CC_TOOL_NAME     - Tool name (Bash, Read, etc.)
# $CC_TOOL_INPUT    - Tool input (JSON)
# $CC_TOOL_OUTPUT   - Tool output (JSON, PostToolUse only)
# $CC_WORKING_DIRECTORY - Current working directory

# ============================================================================
# MAIN LOGIC
# ============================================================================

{main_logic_placeholder}

# Exit codes:
# 0 = Allow (or success)
# 1 = Block (for PreToolUse)
# 2 = Error
```

### Python Script Template

```python
#!/usr/bin/env python3
"""
Hook: {hook_name}
Event: {event_type}
Created: {timestamp}
"""

import os
import sys
import json

def main():
    # Environment variables
    event = os.environ.get('CC_HOOK_EVENT', '')
    tool_name = os.environ.get('CC_TOOL_NAME', '')
    tool_input = json.loads(os.environ.get('CC_TOOL_INPUT', '{}'))

    # Main logic
    {main_logic_placeholder}

    # Return code
    return 0  # 0=allow, 1=block, 2=error

if __name__ == '__main__':
    sys.exit(main())
```

---

## Global Hook Settings (settings.json)

### Output Format

```json
{
  "hooks": {
    "{event_type}": [
      {
        "type": "command",
        "matcher": "{regex_pattern}",
        "command": ".claude/hooks/{hook_name}.sh",
        "timeout": {timeout_ms},
        "once": {once_boolean}
      }
    ]
  }
}
```

### Settings Update Logic

```python
# Read existing settings
settings = read_json(".claude/settings.json")

# Ensure hooks section exists
if "hooks" not in settings:
    settings["hooks"] = {}

if event_type not in settings["hooks"]:
    settings["hooks"][event_type] = []

# Add new hook
settings["hooks"][event_type].append({
    "type": hook_type,
    "matcher": matcher,
    "command": f".claude/hooks/{hook_name}.sh",
    "timeout": timeout,
    "once": once
})

# Write back
write_json(".claude/settings.json", settings)
```

---

## Skill-Level Hook (SKILL.md)

### Output Format

```yaml
# In SKILL.md frontmatter
hooks:
  {event_type}:
    - type: command
      command: ".claude/hooks/{hook_name}.sh"
      matcher: "{regex_pattern}"
      timeout: {timeout_ms}
      once: {once_boolean}
```

---

## State Collection Summary

```yaml
# Collected state at end of builder
hook_state:
  name: "{hook_name}"
  level: "global|skill"
  event: "{event_type}"
  type: "{command|prompt}"            # From hook-config.md
  matcher: "{regex}"                  # From hook-config.md
  once: false                         # From hook-config.md
  timeout: 60000                      # From hook-config.md
  language: "{bash|python|node}"
  action: "{validation|logging|...}"
  script_path: ".claude/hooks/{name}.sh"
```

---

## File Writing

```python
# Create hooks directory
import os
os.makedirs(".claude/hooks", exist_ok=True)

# Write hook script
script_path = f".claude/hooks/{hook_name}.sh"
Write(
    file_path=script_path,
    content=generate_hook_script(collected_data)
)

# Make executable
Bash(f"chmod +x {script_path}")

# Update settings if global
if level == "global":
    update_settings_json(hook_state)

# Success message
print(f"✅ Hook created: {script_path}")
print(f"   Event: {event_type}")
print(f"   Matcher: {matcher}")
```

---

## Validation

### Required Fields

| Field | Required | Default |
|-------|----------|---------|
| `event` | ✓ | - |
| `type` | ✓ | command |
| `matcher` | ✓ | `.*` (all) |
| `command/prompt` | ✓ | - |
| `timeout` | ✗ | 60000 |
| `once` | ✗ | false |

### Script Validation

```python
def validate_hook_script(path):
    # Check file exists
    if not file_exists(path):
        return False, f"스크립트 파일이 없습니다: {path}"

    # Check executable
    if not is_executable(path):
        return False, f"실행 권한이 없습니다: chmod +x {path}"

    # Check shebang
    first_line = read_first_line(path)
    if not first_line.startswith("#!"):
        return False, "shebang 줄이 필요합니다 (#!/bin/bash)"

    return True, None
```

---

## Integration

### Called By

| Caller | When |
|--------|------|
| `/build hook` | 사용자 직접 호출 |
| `skill-builder.md` | Skill의 hooks 섹션 설정 시 |

### Delegates To

| Module | Purpose |
|--------|---------|
| `hook-config.md` | Hook 세부 설정 |

---

## Common Patterns

### Pattern 1: Bash Command Validator

```bash
#!/bin/bash
# Block dangerous commands

INPUT=$(echo "$CC_TOOL_INPUT" | jq -r '.command // ""')

if [[ "$INPUT" =~ rm\ -rf|sudo\ rm|chmod\ 777 ]]; then
    echo "❌ Blocked: Dangerous command pattern detected"
    exit 1
fi

exit 0
```

### Pattern 2: Audit Logger

```bash
#!/bin/bash
# Log all tool usage

LOG_FILE=".agent/logs/tool_audit.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "$TIMESTAMP | $CC_TOOL_NAME | $CC_TOOL_INPUT" >> "$LOG_FILE"

exit 0
```

### Pattern 3: MCP Tool Filter

```bash
#!/bin/bash
# Only allow specific MCP servers

if [[ "$CC_TOOL_NAME" =~ ^mcp__ ]]; then
    ALLOWED="mcp__github-mcp-server|mcp__context7"
    if [[ ! "$CC_TOOL_NAME" =~ $ALLOWED ]]; then
        echo "❌ Blocked: Unauthorized MCP server"
        exit 1
    fi
fi

exit 0
```

---

## Version History

| Version | Change |
|---------|--------|
| V2.1+ | Hook system introduced |
| V2.1.16+ | `once` flag added |
| V2.1.19 | Improved environment variables |
