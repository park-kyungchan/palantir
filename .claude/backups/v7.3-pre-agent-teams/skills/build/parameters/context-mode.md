---
name: context-mode
description: |
  Shared parameter module for context and agent selection.
  Used by: Skill, Agent builders (fork mode configuration)
context: fork
model: haiku
version: "1.0.0"
allowed-tools:
  - AskUserQuestion
---

# Context Mode Parameter Module

> **Purpose:** 실행 컨텍스트 및 서브에이전트 유형 선택
> **Caller:** skill-builder, agent-builder

---

## Parameters Covered

| Parameter | Type | Values | Version | Dependency |
|-----------|------|--------|---------|------------|
| `context` | enum | standard, fork | V2.0+ | - |
| `agent` | string | Explore, Plan, general-purpose, custom | V2.0+ | context=fork |

---

## Round 1: Context Mode

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "실행 컨텍스트를 선택하세요:",
        "header": "Context",
        "options": [
            {
                "label": "standard (Recommended)",
                "description": "메인 대화 컨텍스트에서 실행. 이전 대화 참조 가능"
            },
            {
                "label": "fork",
                "description": "독립된 서브에이전트로 실행. 격리된 컨텍스트"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-context-mode"}
)
```

### Context Comparison

| Context | Isolation | Memory | Use Case |
|---------|-----------|--------|----------|
| `standard` | 없음 | 공유 | 대화 흐름 유지 필요 시 |
| `fork` | 완전 격리 | 독립 | 독립 작업, 병렬 실행 |

---

## Round 2: Agent Type (Conditional)

> **Condition:** `context: fork` 선택 시에만 표시

### Q&A Flow

```python
if context == "fork":
    response = AskUserQuestion(
        questions=[{
            "question": "서브에이전트 유형을 선택하세요:",
            "header": "Agent",
            "options": [
                {
                    "label": "general-purpose (Recommended)",
                    "description": "범용 에이전트. 모든 도구 사용 가능"
                },
                {
                    "label": "Explore",
                    "description": "코드베이스 탐색 전용. Read, Grep, Glob만 사용"
                },
                {
                    "label": "Plan",
                    "description": "설계/계획 전용. 읽기 도구 + 분석"
                },
                {
                    "label": "custom",
                    "description": "커스텀 에이전트 지정 (이름 입력 필요)"
                }
            ],
            "multiSelect": False
        }],
        metadata={"source": "build-context-agent"}
    )
```

### Built-in Agent Types (V2.1.19)

| Agent | Tools | Purpose |
|-------|-------|---------|
| `Explore` | Read, Grep, Glob | 빠른 코드베이스 탐색 |
| `Plan` | Read, Grep, Glob + 분석 | 설계 및 계획 수립 |
| `general-purpose` | All | 범용 멀티스텝 작업 |
| `custom` | Configurable | 사용자 정의 에이전트 |

---

## Round 3: Custom Agent Name (Conditional)

> **Condition:** `agent: custom` 선택 시에만

### Q&A Flow

```python
if agent == "custom":
    response = AskUserQuestion(
        questions=[{
            "question": "커스텀 에이전트 이름을 입력하세요:",
            "header": "Custom",
            "options": [
                {
                    "label": "직접 입력",
                    "description": ".claude/agents/에 정의된 에이전트 이름"
                }
            ],
            "multiSelect": False
        }],
        metadata={"source": "build-context-custom-agent"}
    )
    # User will select "Other" and type custom name
```

---

## Output Format

### Return to Caller

```yaml
context_config:
  context: "fork"
  agent: "Explore"              # null if context=standard
  custom_agent_name: null       # Only if agent=custom
```

### YAML Frontmatter Fragment

```yaml
# For context: standard
context: standard

# For context: fork with built-in agent
context: fork
# Agent specified in Task tool call, not frontmatter

# For Skill with fork context
context: fork
```

---

## Decision Tree

```
context?
├── standard → Done (no agent needed)
└── fork
    └── agent?
        ├── Explore → Done
        ├── Plan → Done
        ├── general-purpose → Done
        └── custom
            └── custom_agent_name? → Done
```

---

## Integration with Task Tool

When `context: fork` is used, the Task tool call should include:

```python
Task(
    subagent_type=agent_type,  # "Explore", "Plan", "general-purpose", or custom
    prompt="...",
    run_in_background=False,   # See task-params.md
    # ...
)
```

---

## Version History

| Version | Change |
|---------|--------|
| V2.0+ | `context` parameter (standard/fork) |
| V2.0+ | Built-in agent types (Explore, Plan) |
| V2.1+ | `general-purpose` agent added |
| V2.1.16+ | Custom agent support improved |
