---
name: ask
description: |
  Prompt Assistant를 호출하여 요구사항을 명확화하고 최적의 기능을 추천받습니다.
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ TOOLS: WebSearch added for fallback if prompt-assistant unavailable      ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
allowed-tools: Read, Grep, Glob, AskUserQuestion, Task, WebSearch
---

# /ask Command

$ARGUMENTS

프롬프트 어시스턴트를 호출하여:
1. 요구사항 분석
2. 명확화 질문 (필요시)
3. 적합한 Claude Code 기능 추천
4. 사용자 승인 후 실행

---

## Orchestration Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐  │
│  │  Main Agent │ ──► │ prompt-assistant │ ──► │ Synthesized     │  │
│  │ (Conductor) │     │  (Forked Agent)  │     │   Results       │  │
│  └─────────────┘     └──────────────────┘     └─────────────────┘  │
│         │                     │                       │             │
│         │                     ▼                       │             │
│         │           ┌──────────────────┐              │             │
│         │           │ • Analyze Intent │              │             │
│         │           │ • Clarify Needs  │              │             │
│         │           │ • Recommend Tool │              │             │
│         │           └──────────────────┘              │             │
│         │                                             │             │
│         └─────────────────────────────────────────────┘             │
│                                                                     │
│  FALLBACK: If subagent unavailable → WebSearch for techniques       │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Principles:**
- **Main Agent only orchestrates** - does not perform analysis directly
- **Delegates to prompt-assistant** (forked context with isolated memory)
- **Returns synthesized results** to user in standardized format
- **WebSearch fallback** for prompt engineering techniques when needed

---

## Delegation Template

```python
Task(
    subagent_type="prompt-assistant",
    prompt="""
    ## Context
    User needs help clarifying their requirements.
    Operating under ODA governance.
    
    ## User Input
    {user_input}
    
    ## Task
    1. Analyze user intent and assess clarity
    2. If unclear, generate Socratic questions
    3. Search for relevant prompting techniques if needed
    4. Recommend appropriate skill/tool after clarification
    
    ## Required Output
    - clarity_score: 0.0-1.0
    - questions_generated: [...] (if clarity < 0.7)
    - recommended_skill: skill name or "continue_clarification"
    - technique_applied: prompting technique used (if any)
    """,
    description="Clarify user requirements and recommend action",
    context="fork"
)
```

---

## 사용법

```
/ask 이 코드를 개선하고 싶어
/ask 버그가 있는 것 같은데 찾아줘
/ask 새로운 기능을 추가하고 싶어
/ask 도와줘
```

---

## Prompt Assistant가 제공하는 것

### 1. 요청 분석
- 사용자 의도 파악
- 작업 범위 식별
- 필요한 도구 결정

### 2. 명확화 질문 (Socratic Questioning)
- 모호한 부분 명확화
- 구체적인 요구사항 도출
- 예상 결과 확인

### 3. 기능 추천
- 상황에 맞는 Native Capabilities 제안
- Skills, Agents, Hooks 활용 방안
- 단계별 실행 계획

### 4. 최종 확인
- 이해한 내용 요약
- 실행 계획 제시
- 사용자 승인 요청

---

## Execution Flow

```
1. User invokes: /ask <요청>
2. Main Agent: Parse $ARGUMENTS
3. Main Agent: Delegate to prompt-assistant subagent
4. Subagent: Analyze, clarify, recommend
5. Main Agent: Synthesize results
6. Main Agent: Present to user with AskUserQuestion if needed
7. User confirms → Execute recommended action
```

---

## Error Handling

| 상황 | 처리 방법 |
|------|----------|
| prompt-assistant 로드 실패 | WebSearch로 prompting 기법 검색 후 직접 처리 |
| 사용자 응답 없음 | 기본 추천 제공 (Explore → Plan 순) |
| 복합 요청 | TodoWrite로 작업 분해 후 순차 처리 |
