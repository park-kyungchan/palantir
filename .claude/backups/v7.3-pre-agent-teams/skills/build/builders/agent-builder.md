---
name: agent-builder
description: |
  Interactive Agent definition builder.
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

# Agent Builder

> **Purpose:** YAML 형식의 Agent 정의 파일 생성
> **Caller:** /build agent, SKILL.md orchestrator
> **Output:** `.claude/agents/{name}.md`

---

## Agent Definition Schema (V2.1.19)

```yaml
# .claude/agents/{name}.md
---
name: {agent-name}
description: |
  {agent-description}
model: {haiku|sonnet|opus}
tools:
  - {tool-1}
  - {tool-2}
permissionMode: {default|acceptEdits|dontAsk|plan}
skills:
  - {skill-1}
  - {skill-2}
custom_instructions: |
  {custom-instructions}
---
```

---

## Round 1: Agent Identity

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Agent 이름을 지정해주세요 (영문, kebab-case 권장)",
        "header": "Name",
        "options": [
            {
                "label": "직접 입력",
                "description": "예: code-reviewer, test-runner, doc-generator"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-agent-name"}
)
# User selects "Other" and types name
```

### Naming Convention

| Pattern | Example | Use Case |
|---------|---------|----------|
| `{action}-{target}` | `code-reviewer` | 특정 작업 수행 |
| `{domain}-agent` | `frontend-agent` | 도메인 전문 |
| `{workflow}-{role}` | `ci-validator` | 워크플로우 역할 |

---

## Round 2: Description

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Agent의 역할과 목적을 설명해주세요",
        "header": "Description",
        "options": [
            {
                "label": "직접 입력",
                "description": "1-3문장으로 Agent가 하는 일 설명"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-agent-description"}
)
```

### Description Guidelines

- **첫 문장:** Agent가 하는 주요 작업
- **두 번째 문장:** 언제/어디서 사용하는지
- **세 번째 문장:** (선택) 특별한 동작이나 제약

```yaml
# Good example
description: |
  코드 리뷰를 수행하고 개선 제안을 제공합니다.
  PR 생성 전이나 코드 품질 검사 시 사용합니다.
  보안 취약점과 성능 이슈에 중점을 둡니다.
```

---

## Round 3: Model Selection

> **Delegate to:** `parameters/model-selection.md`

### Delegation Flow

```python
# Call shared module
model_result = delegate_to("parameters/model-selection.md", {
    "component_type": "agent",
    "current_selection": None
})

# Receive result
model = model_result["model"]  # e.g., "sonnet"
```

### Agent-Specific Model Guide

| Agent Type | Recommended Model | Reason |
|------------|-------------------|--------|
| 코드 분석 | sonnet | 균형 잡힌 분석 |
| 간단한 검증 | haiku | 빠른 응답 |
| 복잡한 설계 | opus | 깊은 추론 |
| 범용 | sonnet | 기본 선택 |

---

## Round 4: Tool Configuration

> **Delegate to:** `parameters/tool-config.md`

### Delegation Flow

```python
# Call shared module
tool_result = delegate_to("parameters/tool-config.md", {
    "component_type": "agent"
})

# Receive result
tools = tool_result["allowed_tools"]  # e.g., ["Read", "Glob", "Grep"]
```

### Agent Tools vs Skill allowed-tools

| Context | Parameter | Description |
|---------|-----------|-------------|
| Agent | `tools` | Agent가 사용할 도구 목록 |
| Skill | `allowed-tools` | Skill 내에서 허용된 도구 |

---

## Round 5: Permission Mode

> **Delegate to:** `parameters/permission-mode.md`

### Delegation Flow

```python
# Call shared module
permission_result = delegate_to("parameters/permission-mode.md", {
    "component_type": "agent",
    "use_case": inferred_use_case
})

# Receive result
permission_mode = permission_result["permissionMode"]  # e.g., "default"
```

---

## Round 6: Skills Injection

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Agent에 주입할 스킬을 선택하세요 (복수 선택 가능)",
        "header": "Skills",
        "options": [
            {
                "label": "없음 (Recommended)",
                "description": "기본 동작만 사용"
            },
            {
                "label": "기존 스킬 선택",
                "description": ".claude/skills/ 에서 선택"
            },
            {
                "label": "직접 입력",
                "description": "스킬 이름 직접 입력"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-agent-skills"}
)
```

### Skill Discovery

```python
if mode == "기존 스킬 선택":
    # Discover available skills
    available_skills = Glob(".claude/skills/*/SKILL.md")

    # Parse skill names
    skill_names = [parse_skill_name(path) for path in available_skills]

    # Present for selection
    # Use multiSelect to allow multiple skills
```

---

## Round 7: Custom Instructions

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Agent에 추가할 커스텀 지시사항이 있나요?",
        "header": "Instructions",
        "options": [
            {
                "label": "없음 (Recommended)",
                "description": "기본 지시사항만 사용"
            },
            {
                "label": "추가하기",
                "description": "특별한 규칙이나 지시사항 입력"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-agent-instructions"}
)
```

### Custom Instructions Examples

```yaml
# Example 1: Code style enforcement
custom_instructions: |
  항상 ESLint 규칙을 준수하세요.
  함수는 20줄 이내로 유지하세요.

# Example 2: Documentation requirement
custom_instructions: |
  모든 public 함수에 JSDoc 주석을 추가하세요.
  README.md를 항상 최신 상태로 유지하세요.
```

---

## Output Generation

### Final Agent File

```yaml
# .claude/agents/{name}.md
---
name: {agent_name}
description: |
  {description}
model: {model}
tools:
  - {tool_1}
  - {tool_2}
permissionMode: {permission_mode}
skills:
  - {skill_1}
  - {skill_2}
custom_instructions: |
  {custom_instructions}
---

# {Agent Name}

> Auto-generated by /build agent

## Usage

```bash
claude --agent {agent_name}
```

## Capabilities

{capability_summary}

## Example Commands

```bash
# Basic usage
claude --agent {agent_name} "Analyze this code"

# With specific file
claude --agent {agent_name} "Review src/main.ts"
```
```

### File Writing

```python
# Generate agent file
output_path = f".claude/agents/{agent_name}.md"

# Write content
Write(
    file_path=output_path,
    content=generate_agent_content(collected_data)
)

# Success message
print(f"✅ Agent created: {output_path}")
print(f"   Usage: claude --agent {agent_name}")
```

---

## State Collection Summary

```yaml
# Collected state at end of builder
agent_state:
  name: "{agent_name}"
  description: "{description}"
  model: "{model}"                    # From model-selection.md
  tools: [...]                        # From tool-config.md
  permission_mode: "{permission}"     # From permission-mode.md
  skills: [...]                       # From Round 6
  custom_instructions: "{text}"       # From Round 7
```

---

## Validation

### Required Fields

| Field | Required | Default |
|-------|----------|---------|
| `name` | ✓ | - |
| `description` | ✓ | - |
| `model` | ✗ | inherit |
| `tools` | ✗ | all |
| `permissionMode` | ✗ | default |
| `skills` | ✗ | [] |
| `custom_instructions` | ✗ | null |

### Name Validation

```python
def validate_agent_name(name):
    # Kebab-case check
    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name):
        return False, "kebab-case 형식을 사용하세요 (예: my-agent)"

    # Reserved names check
    reserved = ["default", "system", "claude", "anthropic"]
    if name in reserved:
        return False, f"'{name}'은 예약어입니다"

    # Existing check
    if file_exists(f".claude/agents/{name}.md"):
        return False, f"Agent '{name}'이(가) 이미 존재합니다. 덮어쓰시겠습니까?"

    return True, None
```

---

## Integration

### Called By

| Caller | When |
|--------|------|
| `/build agent` | 사용자 직접 호출 |
| `/build "concept"` | Concept 분석 후 Agent 타입 결정 시 |

### Delegates To

| Module | Purpose |
|--------|---------|
| `model-selection.md` | 모델 선택 |
| `tool-config.md` | 도구 설정 |
| `permission-mode.md` | 권한 모드 |

---

## Version History

| Version | Change |
|---------|--------|
| V2.0+ | Basic agent definition |
| V2.1+ | `skills` injection support |
| V2.1.16+ | `permissionMode` in frontmatter |
