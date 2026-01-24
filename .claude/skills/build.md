# /build Skill - Interactive Component Builder

> **Version:** 1.0.0 | **Context:** standard | **Model:** sonnet
> **user-invocable:** true | **argument-hint:** [agent|skill|hook] [--resume name]

---

## Purpose

Interactive builder for creating Agents, Skills, and Hooks through progressive Q&A rounds.
Each round collects specific field values, validates input, and builds the final component.

---

## Initialization

Parse `$ARGUMENTS` to determine:
1. Component type: `agent`, `skill`, `hook`, or none (prompt selection)
2. Resume flag: `--resume <draft_name>` to continue incomplete build

```python
args = "$ARGUMENTS".split()
component_type = None
resume_name = None

if "--resume" in args:
    resume_idx = args.index("--resume")
    if len(args) > resume_idx + 1:
        resume_name = args[resume_idx + 1]
elif args and args[0] in ["agent", "skill", "hook"]:
    component_type = args[0]
```

---

## Phase 1: Type Selection

If `component_type` is None and `resume_name` is None:

```
AskUserQuestion(
  questions=[{
    "question": "어떤 컴포넌트를 생성하시겠습니까?",
    "header": "Type",
    "options": [
      {"label": "Agent (Recommended)", "description": "Specialized subagent with ODA governance"},
      {"label": "Skill", "description": "Reusable /command workflow"},
      {"label": "Hook", "description": "Event-driven script"}
    ],
    "multiSelect": false
  }]
)
```

---

## Phase 2: Q&A Execution

### Agent Builder (15 Rounds)

#### Rounds 1-3: Core Identity
```
AskUserQuestion(
  questions=[
    {
      "question": "Agent 이름을 입력하세요 (예: security-validator)",
      "header": "Name",
      "options": [
        {"label": "직접 입력", "description": "lowercase, hyphens, max 64 chars"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `name` (text validation: `^[a-z][a-z0-9-]{0,63}$`)

```
AskUserQuestion(
  questions=[
    {
      "question": "Agent 설명을 입력하세요",
      "header": "Description",
      "options": [
        {"label": "직접 입력", "description": "Claude 자동 호출 트리거에 사용. 'proactively' 포함 시 자동 활성화"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `description`

```
AskUserQuestion(
  questions=[
    {
      "question": "Claude 자동 호출을 비활성화하시겠습니까?",
      "header": "Auto-invoke",
      "options": [
        {"label": "No (Recommended)", "description": "Claude가 적절할 때 자동 호출"},
        {"label": "Yes", "description": "수동 호출만 허용"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `disable-model-invocation` (boolean)

#### Rounds 4-6: Tool Configuration
```
AskUserQuestion(
  questions=[
    {
      "question": "허용할 도구를 선택하세요",
      "header": "Tools",
      "options": [
        {"label": "Read-only (Recommended)", "description": "Read, Grep, Glob"},
        {"label": "Standard", "description": "Read, Grep, Glob, Bash, Edit, Write"},
        {"label": "Full", "description": "All tools including Task, WebSearch"},
        {"label": "Custom", "description": "직접 선택"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ If "Custom" selected, show multiSelect for individual tools

#### Rounds 7-9: ODA Context
```
AskUserQuestion(
  questions=[
    {
      "question": "ODA 역할을 선택하세요",
      "header": "ODA Role",
      "options": [
        {"label": "validator", "description": "입력/출력 검증"},
        {"label": "executor", "description": "액션 실행"},
        {"label": "gate", "description": "접근 제어"},
        {"label": "controller", "description": "워크플로우 제어"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `oda_context.role`

```
AskUserQuestion(
  questions=[
    {
      "question": "접근 가능한 스테이지를 선택하세요",
      "header": "Stages",
      "options": [
        {"label": "A (SCAN)", "description": "파일 탐색, 구조 분석"},
        {"label": "B (TRACE)", "description": "임포트 검증, 시그니처 확인"},
        {"label": "C (VERIFY)", "description": "품질 검사, 테스트 실행"}
      ],
      "multiSelect": true
    }
  ]
)
```

→ Collect: `oda_context.stage_access`

#### Rounds 10-12: Execution Context
```
AskUserQuestion(
  questions=[
    {
      "question": "사용할 모델을 선택하세요",
      "header": "Model",
      "options": [
        {"label": "haiku (Recommended)", "description": "빠른 응답, 간단한 작업"},
        {"label": "sonnet", "description": "균형잡힌 성능"},
        {"label": "opus", "description": "최대 품질, 복잡한 작업"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `model`

#### Rounds 13-15: Integration
```
AskUserQuestion(
  questions=[
    {
      "question": "연동할 Hook 이벤트를 선택하세요",
      "header": "Hooks",
      "options": [
        {"label": "None", "description": "Hook 연동 없음"},
        {"label": "PreToolUse", "description": "도구 실행 전 검증"},
        {"label": "PostToolUse", "description": "도구 실행 후 로깅"},
        {"label": "SubagentStop", "description": "서브에이전트 종료 제어"}
      ],
      "multiSelect": true
    }
  ]
)
```

---

### Skill Builder (12 Rounds)

#### Rounds 1-3: Identity
- name, description, user-invocable

#### Rounds 4-6: Execution
- context (standard/fork), agent type (if fork), model

#### Rounds 7-9: Tools
- allowed-tools, argument-hint, hooks

#### Rounds 10-12: Features
- content-type, dynamic-commands (!`cmd`), ultrathink

---

### Hook Builder (14 Rounds)

#### Rounds 1-3: Identity
- name, event-type, language (Bash/Python)

#### Rounds 4-6: Trigger
- matcher pattern, timeout, type (command/prompt)

#### Rounds 7-10: Input/Output (PreToolUse)
- permissionDecision, updatedInput, additionalContext, input fields

#### Rounds 11-14: Advanced
- output fields, blocking capability, env vars, log path

---

## Phase 3: Draft Generation

After all rounds, generate draft file:

```markdown
# Build Draft: {type} - {name}

## INDEX
- Type: {Agent | Skill | Hook}
- Name: {collected_name}
- Status: READY_FOR_GENERATION
- Rounds Completed: {N}/{total}

## Collected Fields
| Field | Value | Round |
|-------|-------|-------|
{field_table}

## Generated Preview
```{yaml_or_code}
{template_with_values}
```

## Target Path
{output_path}

## Test Command
{test_command}
```

Save to: `.agent/plans/create_drafts/{type}_{name}.md`

---

## Phase 4: Confirmation & Generation

```
AskUserQuestion(
  questions=[{
    "question": "생성된 미리보기를 확인하셨나요? 파일을 생성하시겠습니까?",
    "header": "Confirm",
    "options": [
      {"label": "Yes, generate", "description": "파일 생성 진행"},
      {"label": "Edit fields", "description": "Q&A 다시 진행"},
      {"label": "Save draft only", "description": "드래프트만 저장"}
    ],
    "multiSelect": false
  }]
)
```

On "Yes, generate":
1. Write file to target path
2. Update settings.json if Hook (add to hooks array)
3. Show success message with test command

---

## Templates Reference

### Agent Template
```yaml
---
name: {name}
description: {description}
tools: {tools}
oda_context:
  role: {role}
  stage_access: {stages}
  evidence_required: {bool}
  governance_mode: {mode}
model: {model}
context: {context}
---

# {Name} Agent

## Purpose
{description}

## Behavior
{behavior_rules}
```

### Skill Template
```yaml
---
skill_name: {name}
description: {description}
user_invocable: {bool}
allowed_tools: {tools}
context: {context}
model: {model}
---

# /{name} Command

## Purpose
{description}

## Execution Flow
1. {step}
```

### Hook Template (Bash)
```bash
#!/bin/bash
# {name} - {event_type}
# Trigger: {event_type} on {matcher}

set -euo pipefail
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')

# Logic
{logic}

echo '{"hookSpecificOutput":{"permissionDecision":"{decision}"}}'
```

### Hook Template (Python)
```python
#!/usr/bin/env python3
"""
{name} - {event_type}
Trigger: {event_type} on {matcher}
"""
import sys, json

def main():
    data = json.load(sys.stdin)
    # Logic
    {logic}
    print(json.dumps({"hookSpecificOutput": {"permissionDecision": "{decision}"}}))

if __name__ == "__main__":
    main()
```

---

## Error Handling

| Error | Action |
|-------|--------|
| Invalid name format | Re-prompt with validation hint |
| Draft not found (resume) | List available drafts |
| File already exists | Ask overwrite confirmation |
| Settings.json parse error | Manual hook registration hint |

---

## State Persistence

Draft auto-saves after each round:
- Location: `.agent/plans/create_drafts/{type}_{name}.md`
- Format: Markdown with YAML frontmatter
- Resume: `/build --resume {type}_{name}`

---

## Integration Points

| System | Integration |
|--------|-------------|
| /plan | Draft handoff for complex builds |
| settings.json | Hook auto-registration |
| ODA Registry | Agent registration (future) |
| Template System | Base templates for all types |
