---
name: hook-config
description: |
  Shared parameter module for hook configuration.
  Used by: Hook builder, Skill hooks, Agent hooks
context: fork
model: haiku
version: "1.0.0"
allowed-tools:
  - AskUserQuestion
---

# Hook Configuration Parameter Module

> **Purpose:** Hook 실행 방식과 동작 조건 설정
> **Caller:** hook-builder, skill-builder (hooks section), agent-builder (hooks section)

---

## Parameters Covered

| Parameter | Type | Values | Version | Dependency |
|-----------|------|--------|---------|------------|
| `type` | enum | command, prompt | V2.1+ | - |
| `matcher` | string | regex pattern | V2.1+ | - |
| `once` | boolean | true, false | V2.1.16+ | - |
| `timeout` | number | milliseconds | V2.1+ | type=command |
| `command` | string | shell command | V2.1+ | type=command |
| `prompt` | string | AI prompt | V2.1+ | type=prompt |

---

## Round 1: Hook Type Selection

### Input Context
```yaml
component_type: "{hook|skill-hook|agent-hook}"  # Caller provides
hook_event: "{PreToolUse|PostToolUse|...}"      # Already selected
current_selection: null                          # Or previous value for resume
```

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Hook 실행 방식을 선택하세요",
        "header": "Type",
        "options": [
            {
                "label": "command (Recommended)",
                "description": "셸 명령어 실행. stdout/stderr을 Claude에 전달"
            },
            {
                "label": "prompt",
                "description": "AI에게 직접 프롬프트 주입. Stop/SubagentStop 이벤트 전용"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-hook-type"}
)
```

### Type Comparison

| Type | Use Case | Output Handling |
|------|----------|-----------------|
| command | 외부 스크립트, 검증, 로깅 | stdout→Claude, exit code 체크 |
| prompt | 직접 지시 주입 | Stop/SubagentStop에서만 사용 가능 |

---

## Round 2: Matcher Pattern

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Hook 트리거 조건(matcher)을 어떻게 설정할까요?",
        "header": "Matcher",
        "options": [
            {
                "label": "Exact match",
                "description": "정확한 도구 이름 매칭 (예: Bash, Read)"
            },
            {
                "label": "OR pattern",
                "description": "여러 도구 중 하나 (예: Bash|Read|Write)"
            },
            {
                "label": "Wildcard",
                "description": "패턴 매칭 (예: mcp__*, Bash(*git*))"
            },
            {
                "label": "Custom regex",
                "description": "사용자 정의 정규식"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-hook-matcher"}
)
```

### Matcher Pattern Examples

| Pattern Type | Example | Description |
|--------------|---------|-------------|
| Exact | `Bash` | Bash 도구만 매칭 |
| OR | `Bash\|Read\|Write` | 세 도구 중 하나 매칭 |
| Prefix wildcard | `mcp__*` | MCP 서버 도구 전체 매칭 |
| Command filter | `Bash(*git*)` | git 명령만 매칭 |
| Glob | `*.py` | Python 파일만 (Read/Edit용) |
| Domain | `https?://api\\..*` | API 호출만 (WebFetch용) |

### Follow-up for Custom Regex

```python
if selection == "Custom regex":
    # Direct text input for custom pattern
    print("Enter custom regex pattern:")
```

---

## Round 3: Once Flag (V2.1.16+)

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Hook을 세션당 한 번만 실행할까요?",
        "header": "Once",
        "options": [
            {
                "label": "No (Recommended)",
                "description": "매칭될 때마다 실행"
            },
            {
                "label": "Yes",
                "description": "세션당 처음 한 번만 실행 (초기화용)"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-hook-once"}
)
```

### Once Flag Use Cases

| once | Use Case | Example |
|------|----------|---------|
| false | 반복 검증, 로깅 | 매 Bash 명령 검사 |
| true | 세션 초기화, 환경 설정 | 첫 도구 사용 시 알림 |

---

## Round 4: Timeout (Conditional)

> **Condition:** type=command 일 때만 표시

### Q&A Flow

```python
if hook_type == "command":
    response = AskUserQuestion(
        questions=[{
            "question": "명령어 실행 제한 시간을 설정하세요 (ms)",
            "header": "Timeout",
            "options": [
                {
                    "label": "60000ms (Recommended)",
                    "description": "기본값: 1분. 대부분의 스크립트에 적합"
                },
                {
                    "label": "10000ms",
                    "description": "빠른 검증용: 10초"
                },
                {
                    "label": "300000ms",
                    "description": "긴 작업용: 5분"
                },
                {
                    "label": "Custom",
                    "description": "사용자 정의 시간 (ms)"
                }
            ],
            "multiSelect": False
        }],
        metadata={"source": "build-hook-timeout"}
    )
```

---

## Round 5: Command/Prompt Content (Conditional)

### For type=command

```python
if hook_type == "command":
    # User provides shell command
    print("Enter command to execute:")
    # Example: ".claude/hooks/validate-imports.sh $CC_TOOL_INPUT"
```

### For type=prompt

```python
if hook_type == "prompt":
    # User provides prompt text
    print("Enter prompt to inject:")
    # Note: Only works with Stop, SubagentStop events
```

### Environment Variables Available

| Variable | Description | Available In |
|----------|-------------|--------------|
| `$CC_HOOK_EVENT` | 이벤트 타입 | All hooks |
| `$CC_TOOL_NAME` | 도구 이름 | PreToolUse, PostToolUse |
| `$CC_TOOL_INPUT` | 도구 입력 (JSON) | PreToolUse, PostToolUse |
| `$CC_TOOL_OUTPUT` | 도구 출력 (JSON) | PostToolUse only |
| `$CC_WORKING_DIRECTORY` | 현재 작업 디렉토리 | All hooks |

---

## Output Format

### Return to Caller

```yaml
hook_config:
  type: "command"
  matcher: "Bash|Read|Write"
  once: false
  timeout: 60000
  command: ".claude/hooks/validate.sh"
  # OR
  prompt: null  # Only if type=prompt
```

### JSON Output Fragment (for settings.json)

```json
{
  "type": "command",
  "matcher": "Bash|Read|Write",
  "once": false,
  "timeout": 60000,
  "command": ".claude/hooks/validate.sh"
}
```

---

## Hook Type Decision Tree

```
Hook 설정 시작
    │
    ├── 외부 스크립트 필요? ──Yes──► type: command
    │   │                           │
    │   │                           ├── timeout 설정 (기본: 60000)
    │   │                           └── command 경로 지정
    │   │
    │   No
    │   │
    └── AI 지시 주입? ──Yes──► type: prompt
        │                       │
        │                       └── Stop/SubagentStop 이벤트만!
        │
        No ──► type: command (기본)
```

---

## Version History

| Version | Change |
|---------|--------|
| V2.1+ | `type`, `matcher`, `timeout`, `command`, `prompt` 도입 |
| V2.1.16+ | `once` 파라미터 추가 (세션당 한 번 실행) |

---

## Related Modules

| Module | Relationship |
|--------|--------------|
| `hook-builder.md` | Hook 전체 생성 (event selection 포함) |
| `permission-mode.md` | Hook 권한 설정 연계 가능 |
