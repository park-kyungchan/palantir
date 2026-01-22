---
name: clarify
description: |
  Prompt Engineering 루프를 통해 사용자 요청을 명확화합니다.
  claude-code-guide를 활용하여 PE 기법을 적용하고,
  승인 시까지 개선된 프롬프트를 반복 제안합니다.
allowed-tools: Read, Grep, Glob, AskUserQuestion, Task, WebSearch, TodoWrite
argument-hint: <요청 또는 프롬프트>
---

# /clarify Command

$ARGUMENTS

## Purpose

사용자 요청을 **Prompt Engineering 기법**을 적용하여 개선하고,
**승인될 때까지** 반복적으로 개선안을 제시합니다.

---

## Core Loop

```
┌────────────────────────────────────────────────────────────────┐
│                    CLARIFY LOOP                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   User Input                                                   │
│        │                                                       │
│        ▼                                                       │
│   ┌─────────────────────────────────────┐                      │
│   │ 1. claude-code-guide 호출            │                      │
│   │    → Input 분석                      │                      │
│   │    → PE 기법 검색 및 적용            │                      │
│   │    → 개선된 프롬프트 생성            │                      │
│   └─────────────────────────────────────┘                      │
│        │                                                       │
│        ▼                                                       │
│   ┌─────────────────────────────────────┐                      │
│   │ 2. 사용자에게 제시                   │                      │
│   │    "이렇게 개선해봤어요:"            │                      │
│   │    [개선된 프롬프트]                 │                      │
│   │                                     │                      │
│   │    선택: 승인 / 수정요청 / 다시시도   │                      │
│   └─────────────────────────────────────┘                      │
│        │                                                       │
│        ├── 승인 ──────────► EXIT (최종 프롬프트 확정)           │
│        │                                                       │
│        └── 수정요청/다시 ──► LOOP (새 Input으로 반복)           │
│                                                                │
│   [모든 과정 .agent/plans/clarify_{slug}.md에 로그]            │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Delegation

Main Agent는 clarify-agent를 호출합니다:

```python
Task(
    subagent_type="prompt-assistant",  # clarify-agent alias
    prompt="""
    ## User Input
    {user_input}

    ## Task
    Clarify Loop를 실행하세요:
    1. Input 분석
    2. claude-code-guide로 PE 기법 검색
    3. 개선된 프롬프트 생성
    4. 사용자에게 제시 (AskUserQuestion)
    5. 승인될 때까지 반복

    ## Output
    - 로그 파일: .agent/plans/clarify_{slug}.md
    - 최종 프롬프트 (승인 시)
    """,
    description="Clarify loop execution",
    context="fork"
)
```

---

## Usage Examples

```bash
# 모호한 요청 명확화
/clarify 이거 좀 고쳐줘

# 복잡한 기능 요청 명확화
/clarify 사용자 인증 기능 추가하고 싶어

# 프롬프트 개선 요청
/clarify 이 프롬프트 더 좋게 만들어줘: "코드 분석해줘"
```

---

## Output Format

### 매 라운드 출력

```markdown
## Round {n}

### 입력
{user_input}

### 분석
- 의도: {intent}
- 모호한 부분: {ambiguities}

### PE 기법 적용
- 적용 기법: {technique_name}
- 이유: {reason}

### 개선된 프롬프트
```
{improved_prompt}
```

### 선택
- [ ] 승인 (이대로 진행)
- [ ] 수정 요청 (피드백 제공)
- [ ] 다시 시도 (다른 기법으로)
```

### 최종 출력

```markdown
## /clarify 완료 ✅

### 로그 저장 완료
`.agent/plans/clarify_{slug}.md`

### 최종 프롬프트
```
{final_prompt}
```

### 적용된 PE 기법
1. {technique_1}: {explanation}
2. {technique_2}: {explanation}

### 다음 단계
승인된 프롬프트로 작업을 진행합니다.
```

---

## Log File Schema

```markdown
# Clarify Log: {slug}

> **Created:** {datetime}
> **Status:** {in_progress|completed}
> **Rounds:** {count}

---

## INDEX

### 원본 요청
{original_input}

### 최종 프롬프트
{final_prompt}

### 적용 기법 요약
- {technique_1}
- {technique_2}

---

## DETAIL: Round Logs {#rounds}

### Round 1
- Input: ...
- PE Lookup: ...
- Output: ...
- User Response: ...

### Round 2
...
```
