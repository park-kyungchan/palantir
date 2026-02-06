---
name: task-params
description: |
  Shared parameter module for Task tool delegation parameters.
  Used by: Task subagent configuration, Agent orchestration
context: fork
model: haiku
version: "1.0.0"
allowed-tools:
  - AskUserQuestion
---

# Task Parameters Module

> **Purpose:** Task 도구로 서브에이전트 위임 시 실행 파라미터 설정
> **Caller:** agent-builder, orchestration flows, delegation patterns

---

## Parameters Covered

| Parameter | Type | Default | Version | Description |
|-----------|------|---------|---------|-------------|
| `run_in_background` | boolean | false | V2.1.16+ | 백그라운드 실행 여부 |
| `resume` | string | null | V2.1+ | 재개할 에이전트 ID |
| `max_turns` | number | unlimited | V2.1+ | 최대 턴 수 제한 |
| `allowed_tools` | array | all | V2.1+ | 허용할 도구 목록 |

---

## Round 1: Background Execution

### Input Context
```yaml
task_type: "{long-running|quick|exploratory}"  # Caller provides
parallelization: "{sequential|parallel}"       # Workflow context
current_selection: null                         # Or previous value for resume
```

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "Task를 백그라운드에서 실행할까요?",
        "header": "Background",
        "options": [
            {
                "label": "No (Recommended)",
                "description": "결과를 즉시 받음. 대부분의 작업에 적합"
            },
            {
                "label": "Yes",
                "description": "백그라운드 실행. 긴 작업이나 병렬 처리에 유용"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-task-background"}
)
```

### Background Execution Details

| run_in_background | Behavior | Use Case |
|-------------------|----------|----------|
| false | 동기 실행, 결과 즉시 반환 | 짧은 작업, 순차 의존성 |
| true | 비동기 실행, TaskOutput으로 결과 조회 | 병렬 탐색, 긴 빌드 |

### Output File Pattern (V2.1.16+)
```yaml
# run_in_background=true 시 반환값
{
  "task_id": "abc123",
  "output_file": "/tmp/claude-task-abc123.out",
  "status": "running"
}
```

---

## Round 2: Resume Configuration

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "이전 에이전트를 재개(resume)할까요?",
        "header": "Resume",
        "options": [
            {
                "label": "No, new agent (Recommended)",
                "description": "새 에이전트로 시작"
            },
            {
                "label": "Yes, resume existing",
                "description": "이전 컨텍스트를 유지하며 재개"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-task-resume"}
)
```

### Resume Behavior

| resume | Behavior | When to Use |
|--------|----------|-------------|
| null | 새 에이전트 생성 | 일반적인 사용 |
| agent_id | 해당 ID의 에이전트 재개 | 중단된 작업 계속, 후속 질문 |

### Resume Example
```python
# 첫 번째 호출
result = Task(
    prompt="Analyze the codebase",
    subagent_type="Explore"
)
# result.agent_id = "xyz789"

# 후속 호출 (재개)
result = Task(
    prompt="Now focus on the auth module",
    subagent_type="Explore",
    resume="xyz789"  # 이전 컨텍스트 유지
)
```

---

## Round 3: Maximum Turns

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "에이전트의 최대 턴 수를 제한할까요?",
        "header": "Max Turns",
        "options": [
            {
                "label": "Unlimited (Recommended)",
                "description": "작업이 완료될 때까지 실행"
            },
            {
                "label": "10 turns",
                "description": "빠른 탐색에 적합"
            },
            {
                "label": "25 turns",
                "description": "중간 규모 작업에 적합"
            },
            {
                "label": "Custom",
                "description": "사용자 정의 턴 수"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-task-maxturns"}
)
```

### Turn Limit Guidelines

| max_turns | Use Case | Risk |
|-----------|----------|------|
| unlimited | 완전한 작업 수행 | 비용 증가 가능 |
| 5-10 | 빠른 탐색, 간단한 질문 | 불완전할 수 있음 |
| 15-25 | 코드 분석, 중간 작업 | 적절한 균형 |
| 50+ | 복잡한 구현 | 주의 필요 |

---

## Round 4: Tool Restrictions

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "서브에이전트가 사용할 도구를 제한할까요?",
        "header": "Tools",
        "options": [
            {
                "label": "All tools (Recommended)",
                "description": "모든 도구 사용 가능"
            },
            {
                "label": "Read-only",
                "description": "Read, Glob, Grep만 허용 (분석용)"
            },
            {
                "label": "No Bash",
                "description": "Bash 제외한 모든 도구"
            },
            {
                "label": "Custom list",
                "description": "사용자 정의 도구 목록"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-task-tools"}
)
```

### Preset Tool Lists

| Preset | Tools Included | Use Case |
|--------|----------------|----------|
| All | (모든 도구) | 일반 작업 |
| Read-only | Read, Glob, Grep, WebFetch | 분석, 탐색 |
| No Bash | Read, Write, Edit, Glob, Grep | 안전한 파일 작업 |
| File-ops | Read, Write, Edit, Glob, Grep | 파일 중심 작업 |
| Research | Read, Glob, Grep, WebFetch, WebSearch | 정보 수집 |

### Custom Tool List Input
```python
if selection == "Custom list":
    # User provides tool names
    # Example: ["Read", "Glob", "Grep", "Edit"]
```

---

## Output Format

### Return to Caller

```yaml
task_config:
  run_in_background: false
  resume: null
  max_turns: null  # unlimited
  allowed_tools: null  # all tools
  selection_summary: "동기 실행, 새 에이전트, 제한 없음"
```

### Task Tool Call Fragment

```python
Task(
    prompt="...",
    subagent_type="Explore",
    run_in_background=False,
    # resume=None,  # omit if new agent
    # max_turns=25,  # omit if unlimited
    # allowed_tools=["Read", "Glob", "Grep"]  # omit if all
)
```

---

## Common Patterns

### Pattern 1: Quick Exploration
```yaml
run_in_background: false
max_turns: 10
allowed_tools: ["Read", "Glob", "Grep"]
use_case: "빠른 코드베이스 탐색"
```

### Pattern 2: Parallel Research
```yaml
run_in_background: true
max_turns: 25
allowed_tools: ["Read", "Glob", "Grep", "WebFetch"]
use_case: "여러 소스 동시 조사"
```

### Pattern 3: Safe Implementation
```yaml
run_in_background: false
max_turns: 50
allowed_tools: ["Read", "Write", "Edit", "Glob", "Grep"]
use_case: "Bash 없이 파일 수정"
```

### Pattern 4: Resume Workflow
```yaml
run_in_background: false
resume: "{previous_agent_id}"
max_turns: 10
use_case: "이전 분석 이어서 진행"
```

---

## Subagent Type Recommendations

| subagent_type | Recommended Config |
|---------------|--------------------|
| Explore | max_turns: 15-25, read-only tools |
| Plan | max_turns: 20-30, no Bash |
| general-purpose | unlimited, all tools |
| Bash | unlimited, Bash only |

---

## Version History

| Version | Change |
|---------|--------|
| V2.1+ | `resume`, `max_turns`, `allowed_tools` 도입 |
| V2.1.16+ | `run_in_background` 추가, TaskOutput 도구 |

---

## Related Modules

| Module | Relationship |
|--------|--------------|
| `tool-config.md` | 상세 도구 설정 (allowed/disallowed 패턴) |
| `model-selection.md` | Task의 model 파라미터와 연계 |
| `agent-builder.md` | Agent 내에서 Task 위임 설정 |
