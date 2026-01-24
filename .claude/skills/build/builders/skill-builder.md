---
name: skill-builder
description: |
  Interactive Skill definition builder.
  Delegates to shared parameter modules for common configurations.
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

# Skill Builder

> **Purpose:** YAML frontmatter 기반 Skill 정의 파일 생성
> **Caller:** /build skill, SKILL.md orchestrator
> **Output:** `.claude/skills/{name}/SKILL.md`

---

## Skill Definition Schema (V2.1.19)

```yaml
# .claude/skills/{name}/SKILL.md
---
name: {skill-name}
description: |
  {skill-description}
user-invocable: {true|false}
disable-model-invocation: {true|false}
context: {standard|fork}
model: {haiku|sonnet|opus}
argument-hint: "{hint-text}"
allowed-tools:
  - {tool-1}
  - {tool-2}
hooks:
  {Event}:
    - type: {command|prompt}
      command: "{command}"
      matcher: "{regex}"
version: "{semver}"
---

# Skill Content
...
```

---

## Round 1: Skill Identity

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Skill 이름을 지정해주세요 (영문, kebab-case)",
        "header": "Name",
        "options": [
            {
                "label": "직접 입력",
                "description": "예: code-review, test-runner, doc-gen"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-skill-name"}
)
```

### Naming Convention

| Pattern | Example | Use Case |
|---------|---------|----------|
| `{action}` | `build`, `clarify` | 단일 동작 |
| `{action}-{target}` | `code-review` | 특정 대상 동작 |
| `{domain}-{action}` | `git-commit` | 도메인 특화 |

---

## Round 2: Description

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Skill의 역할과 목적을 설명해주세요",
        "header": "Description",
        "options": [
            {
                "label": "직접 입력",
                "description": "1-3문장으로 Skill이 하는 일 설명"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-skill-description"}
)
```

---

## Round 3: Invocation Mode

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Skill 호출 방식을 설정하세요",
        "header": "Invocation",
        "options": [
            {
                "label": "사용자 호출 전용 (Recommended)",
                "description": "user-invocable=true, disable-model-invocation=true"
            },
            {
                "label": "자동 + 수동 호출",
                "description": "user-invocable=true, disable-model-invocation=false"
            },
            {
                "label": "자동 호출 전용",
                "description": "user-invocable=false (내부용)"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-skill-invocation"}
)
```

### Invocation Mode Mapping

| Mode | user-invocable | disable-model-invocation |
|------|----------------|--------------------------|
| 사용자 전용 | true | true |
| 자동 + 수동 | true | false |
| 자동 전용 | false | false |

### Access Pattern Reference (P1-P4)

| Pattern | Access Level | Example |
|---------|--------------|---------|
| P1 | User-only | /clarify, /commit |
| P2 | User+System | /build |
| P3 | Internal | helpers, validators |
| P4 | Ephemeral | one-time scripts |

---

## Round 4: Context Mode

> **Delegate to:** `parameters/context-mode.md`

### Delegation Flow

```python
# Call shared module
context_result = delegate_to("parameters/context-mode.md", {
    "component_type": "skill"
})

# Receive result
context = context_result["context"]  # "standard" or "fork"
agent = context_result.get("agent")  # Only if fork
```

---

## Round 5: Model Selection

> **Delegate to:** `parameters/model-selection.md`

### Delegation Flow

```python
# Call shared module
model_result = delegate_to("parameters/model-selection.md", {
    "component_type": "skill",
    "current_selection": None
})

# Receive result
model = model_result["model"]  # e.g., "sonnet"
```

---

## Round 6: Tool Configuration

> **Delegate to:** `parameters/tool-config.md`

### Delegation Flow

```python
# Call shared module
tool_result = delegate_to("parameters/tool-config.md", {
    "component_type": "skill"
})

# Receive result
if tool_result["mode"] == "allowlist":
    allowed_tools = tool_result["allowed_tools"]
elif tool_result["mode"] == "denylist":
    disallowed_tools = tool_result["disallowed_tools"]
```

---

## Round 7: Argument Hint

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Skill 호출 시 인자 힌트를 설정할까요?",
        "header": "Args",
        "options": [
            {
                "label": "없음 (Recommended)",
                "description": "인자 없이 호출"
            },
            {
                "label": "설정하기",
                "description": "인자 형식 힌트 입력"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-skill-argument-hint"}
)
```

### Argument Hint Examples

```yaml
# Simple argument
argument-hint: "<file-path>"

# Multiple arguments
argument-hint: "<action> [options]"

# With flags
argument-hint: "<target> | --resume <id>"

# Indexed arguments ($0, $1 - V2.1.19)
# /skill start main → $0="start", $1="main"
argument-hint: "<command> <target>"
```

---

## Round 8: Hooks Configuration

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Skill에 Hook을 추가할까요?",
        "header": "Hooks",
        "options": [
            {
                "label": "없음 (Recommended)",
                "description": "Hook 없이 실행"
            },
            {
                "label": "추가하기",
                "description": "Hook 이벤트 선택"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-skill-hooks"}
)
```

### Hook Event Selection (If Adding)

```python
if add_hooks:
    response = AskUserQuestion(
        questions=[{
            "question": "Hook을 트리거할 이벤트를 선택하세요",
            "header": "Event",
            "options": [
                {"label": "Stop", "description": "Skill 종료 시"},
                {"label": "PreToolUse", "description": "도구 사용 전"},
                {"label": "PostToolUse", "description": "도구 사용 후"}
            ],
            "multiSelect": True
        }],
        metadata={"source": "build-skill-hook-event"}
    )

    # For each event, delegate to hook-config.md
    for event in selected_events:
        hook_result = delegate_to("parameters/hook-config.md", {
            "hook_event": event
        })
```

---

## Round 9: Version

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Skill 버전을 지정하세요",
        "header": "Version",
        "options": [
            {
                "label": "1.0.0 (Recommended)",
                "description": "첫 번째 안정 버전"
            },
            {
                "label": "0.1.0",
                "description": "초기 개발 버전"
            },
            {
                "label": "직접 입력",
                "description": "SemVer 형식 (X.Y.Z)"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-skill-version"}
)
```

---

## Output Generation

### Directory Structure

```
.claude/skills/{skill-name}/
├── SKILL.md          # Main skill file
└── helpers.sh        # Optional helper scripts
```

### Final Skill File

```yaml
# .claude/skills/{name}/SKILL.md
---
name: {skill_name}
description: |
  {description}
user-invocable: {user_invocable}
disable-model-invocation: {disable_model}
context: {context}
model: {model}
argument-hint: "{argument_hint}"
allowed-tools:
  - {tool_1}
  - {tool_2}
hooks:
  {Event}:
    - type: {hook_type}
      command: "{hook_command}"
version: "{version}"
---

# /{skill_name} - {Title}

> **Role:** {role_description}
> **Access Pattern:** {P1|P2|P3|P4}

---

## Usage

```bash
/{skill_name} {argument_hint_example}
```

## Main Logic

{main_logic_placeholder}

---

## Version History

| Version | Change |
|---------|--------|
| {version} | Initial release |
```

### File Writing

```python
# Create directory
import os
os.makedirs(f".claude/skills/{skill_name}", exist_ok=True)

# Write skill file
Write(
    file_path=f".claude/skills/{skill_name}/SKILL.md",
    content=generate_skill_content(collected_data)
)

# Success message
print(f"✅ Skill created: .claude/skills/{skill_name}/SKILL.md")
print(f"   Usage: /{skill_name}")
```

---

## State Collection Summary

```yaml
# Collected state at end of builder
skill_state:
  name: "{skill_name}"
  description: "{description}"
  user_invocable: true
  disable_model_invocation: true
  context: "{context}"                # From context-mode.md
  model: "{model}"                    # From model-selection.md
  allowed_tools: [...]                # From tool-config.md
  argument_hint: "{hint}"
  hooks: {...}                        # From hook-config.md
  version: "{version}"
```

---

## Validation

### Required Fields

| Field | Required | Default |
|-------|----------|---------|
| `name` | ✓ | - |
| `description` | ✓ | - |
| `user-invocable` | ✗ | true |
| `disable-model-invocation` | ✗ | false |
| `context` | ✗ | standard |
| `model` | ✗ | inherit |
| `allowed-tools` | ✗ | all |
| `argument-hint` | ✗ | null |
| `hooks` | ✗ | {} |
| `version` | ✗ | "1.0.0" |

### Name Validation

```python
def validate_skill_name(name):
    # Kebab-case check
    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name):
        return False, "kebab-case 형식을 사용하세요 (예: my-skill)"

    # Reserved names check
    reserved = ["help", "clear", "compact", "memory", "config"]
    if name in reserved:
        return False, f"'{name}'은 예약된 명령어입니다"

    # Existing check
    if dir_exists(f".claude/skills/{name}"):
        return False, f"Skill '{name}'이(가) 이미 존재합니다. 덮어쓰시겠습니까?"

    return True, None
```

---

## Integration

### Called By

| Caller | When |
|--------|------|
| `/build skill` | 사용자 직접 호출 |
| `/build "concept"` | Concept 분석 후 Skill 타입 결정 시 |

### Delegates To

| Module | Purpose |
|--------|---------|
| `context-mode.md` | 컨텍스트 설정 |
| `model-selection.md` | 모델 선택 |
| `tool-config.md` | 도구 설정 |
| `hook-config.md` | Hook 설정 |

---

## Version History

| Version | Change |
|---------|--------|
| V2.0+ | Basic skill definition |
| V2.1+ | `hooks` section support |
| V2.1.16+ | `once` hook flag |
| V2.1.19+ | `$0`, `$1` indexed arguments |
