---
name: model-selection
description: |
  Shared parameter module for model selection.
  Used by: Agent, Skill, Task builders
context: fork
model: haiku
version: "1.0.0"
allowed-tools:
  - AskUserQuestion
---

# Model Selection Parameter Module

> **Purpose:** 컴포넌트에서 사용할 AI 모델 선택
> **Caller:** agent-builder, skill-builder, task delegation

---

## Parameters Covered

| Parameter | Type | Values | Version | Used By |
|-----------|------|--------|---------|---------|
| `model` | enum | haiku, sonnet, opus, inherit | V2.0+ | Skill, Agent, Task |
| `fallback-model` | enum | haiku, sonnet, opus | V2.1+ | Print mode only |

---

## Round 1: Model Selection

### Input Context
```yaml
component_type: "{agent|skill|task}"  # Caller provides
current_selection: null               # Or previous value for resume
```

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "어떤 모델을 사용할까요?",
        "header": "Model",
        "options": [
            {
                "label": "sonnet (Recommended)",
                "description": "균형 잡힌 성능과 속도. 대부분의 작업에 적합"
            },
            {
                "label": "haiku",
                "description": "빠른 응답, 간단한 작업에 최적. 비용 효율적"
            },
            {
                "label": "opus",
                "description": "최고 품질, 복잡한 추론에 적합. 느리지만 정확"
            },
            {
                "label": "inherit",
                "description": "부모 컨텍스트의 모델을 상속"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-model-selection"}
)
```

### Selection Guide

| Use Case | Recommended Model | Reason |
|----------|-------------------|--------|
| 파라미터 수집 | haiku | 단순 Q&A, 빠른 응답 |
| 코드 생성 | sonnet | 균형 잡힌 품질 |
| 복잡한 분석 | opus | 깊은 추론 필요 |
| 빌더 내부 | sonnet | 적절한 품질/속도 |
| 오케스트레이터 | opus | 전체 흐름 관리 |

---

## Round 2: Fallback Model (Conditional)

> **Condition:** Print mode 또는 복잡한 출력이 예상될 때만

### Q&A Flow (Optional)

```python
if component_type == "skill" and has_complex_output:
    response = AskUserQuestion(
        questions=[{
            "question": "출력이 길어질 경우 대체 모델을 지정할까요?",
            "header": "Fallback",
            "options": [
                {
                    "label": "지정 안함 (Recommended)",
                    "description": "기본 모델만 사용"
                },
                {
                    "label": "haiku",
                    "description": "긴 출력 시 haiku로 전환"
                }
            ],
            "multiSelect": False
        }],
        metadata={"source": "build-model-fallback"}
    )
```

---

## Output Format

### Return to Caller

```yaml
model_config:
  model: "sonnet"           # Selected model
  fallback_model: null      # Optional fallback
  selection_reason: "균형 잡힌 성능과 속도"
```

### YAML Frontmatter Fragment

```yaml
# For Skill/Agent output
model: sonnet
```

---

## Model Comparison Reference

| Model | Speed | Quality | Cost | Best For |
|-------|-------|---------|------|----------|
| haiku | ⚡⚡⚡ | ★★☆ | $ | Simple Q&A, validation |
| sonnet | ⚡⚡ | ★★★ | $$ | Code generation, analysis |
| opus | ⚡ | ★★★★ | $$$$ | Complex reasoning, planning |

---

## Version History

| Version | Change |
|---------|--------|
| V2.0+ | `model` parameter introduced |
| V2.1+ | `fallback-model` for print mode |
| V2.1.16+ | Model inheritance from parent context |
