---
skill_name: clarify
description: PE 기법을 적용하여 사용자 요청을 반복적으로 개선
user_invocable: true
context: fork
model: sonnet
version: "1.0.0"
---

# /clarify - Prompt Engineering Loop

> **Role:** 사용자 요청 명확화 + PE 기법 적용
> **Core Principle:** 승인 없이 진행 안 함 → 매 라운드 PE 적용 → 로그 기록

---

## 1. Execution Protocol

### 1.1 Initialize

```python
# 1. 로그 파일 생성
slug = generate_slug(user_input)
log_path = f".agent/plans/clarify_{slug}.md"

# 2. 초기 로그 작성
write_log_header(log_path, user_input)

# 3. Round 카운터 시작
round_num = 1
```

### 1.2 Main Loop

```python
while not approved:
    # Step 1: claude-code-guide로 PE 기법 검색
    pe_result = Task(
        subagent_type="claude-code-guide",
        prompt=f"""
        ## Input
        {current_input}

        ## Task
        이 Input에 적용할 수 있는 Prompt Engineering 기법을 찾아주세요.

        ## Return Format
        - technique_name: 기법 이름
        - description: 설명 (1-2문장)
        - application: 이 Input에 어떻게 적용할지
        - improved_prompt: 개선된 프롬프트 예시
        """,
        description="PE technique lookup"
    )

    # Step 2: 개선된 프롬프트 생성
    improved = apply_pe_technique(current_input, pe_result)

    # Step 3: 로그 기록
    append_round_log(log_path, round_num, current_input, pe_result, improved)

    # Step 4: 사용자에게 제시
    response = AskUserQuestion(
        questions=[{
            "question": f"개선된 프롬프트입니다:\n\n```\n{improved}\n```\n\n어떻게 하시겠습니까?",
            "header": f"Round {round_num}",
            "options": [
                {"label": "승인", "description": "이대로 진행합니다"},
                {"label": "수정 요청", "description": "피드백을 제공합니다"},
                {"label": "다른 기법으로", "description": "다른 PE 기법을 시도합니다"}
            ],
            "multiSelect": False
        }]
    )

    # Step 5: 분기
    if response == "승인":
        approved = True
        finalize_log(log_path, improved)
    else:
        current_input = get_new_input(response)
        round_num += 1
```

---

## 2. PE Technique Lookup

### 2.1 claude-code-guide 호출 템플릿

```python
Task(
    subagent_type="claude-code-guide",
    prompt="""
    ## Context
    사용자가 다음 요청을 개선하려 합니다:
    "{user_input}"

    ## Task
    1. 이 요청의 의도 파악
    2. 적용 가능한 PE 기법 검색
    3. 개선된 프롬프트 제안

    ## PE Techniques to Consider
    - Chain of Thought (CoT): 단계별 사고 유도
    - Few-Shot: 예시 제공
    - Role Prompting: 역할 부여
    - Structured Output: 출력 형식 지정
    - Constraint Setting: 제약 조건 명시

    ## Return Format (JSON)
    {
        "intent": "파악된 의도",
        "technique": "적용 기법",
        "reason": "선택 이유",
        "improved_prompt": "개선된 프롬프트"
    }
    """,
    description="PE technique search"
)
```

### 2.2 검색 키워드 매핑

| 요청 유형 | 추천 PE 기법 |
|-----------|-------------|
| 분석/설명 요청 | Chain of Thought |
| 코드 작성 | Few-Shot + Structured Output |
| 문제 해결 | Step-by-Step + Constraint |
| 창의적 작업 | Role Prompting |
| 복잡한 작업 | Task Decomposition |

---

## 3. Log File Management

### 3.1 Log Schema

```markdown
# Clarify Log: {slug}

> **Created:** {datetime}
> **Status:** {in_progress|completed|cancelled}
> **Rounds:** {count}
> **Final Approved:** {yes|no}

---

## INDEX

### 원본 요청
{original_input}

### 최종 프롬프트
{final_prompt or "N/A"}

### 적용 기법
1. {technique_1}
2. {technique_2}

### 라운드 요약
| Round | Input (요약) | 기법 | 결과 |
|-------|-------------|------|------|
| 1 | ... | CoT | 수정요청 |
| 2 | ... | Few-Shot | 승인 |

---

## DETAIL: Round Logs {#rounds}

### Round 1
**Input:**
{input}

**PE Lookup Result:**
- Technique: {technique}
- Reason: {reason}

**Improved Prompt:**
```
{improved}
```

**User Response:** {승인|수정요청|다른기법}
**Feedback:** {user_feedback if any}

---

### Round 2
...
```

### 3.2 Log Operations

```python
def write_log_header(path, original_input):
    """로그 파일 헤더 생성"""

def append_round_log(path, round_num, input, pe_result, improved):
    """라운드 로그 추가"""

def finalize_log(path, final_prompt):
    """최종 승인 후 로그 완료 처리"""

def cancel_log(path, reason):
    """취소 시 로그 마무리"""
```

---

## 4. User Interaction

### 4.1 라운드별 출력 형식

```markdown
## Round {n} 결과

### 입력
{input}

### 분석
이 요청은 **{intent}**를 원하는 것으로 보입니다.

### 적용한 PE 기법
**{technique_name}**
{description}

### 개선된 프롬프트

```
{improved_prompt}
```

### 개선 포인트
- {point_1}
- {point_2}
```

### 4.2 AskUserQuestion 옵션

```python
AskUserQuestion(
    questions=[{
        "question": "개선된 프롬프트를 확인해주세요. 어떻게 하시겠습니까?",
        "header": f"Round {n}",
        "options": [
            {"label": "승인 (Recommended)", "description": "이 프롬프트로 진행"},
            {"label": "수정 요청", "description": "피드백을 입력하고 다시 시도"},
            {"label": "다른 기법 시도", "description": "다른 PE 기법으로 개선"}
        ],
        "multiSelect": False
    }]
)
```

---

## 5. Exit Conditions

### 5.1 정상 종료

- 사용자가 "승인" 선택
- 로그 상태: `completed`

### 5.2 비정상 종료

- 사용자가 "취소" 입력
- 5라운드 초과 (MAX_ROUNDS = 5)
- 로그 상태: `cancelled`

---

## 6. Integration

### 6.1 다른 스킬로 라우팅

승인된 프롬프트 기반으로:

```python
if approved:
    # 의도에 따라 라우팅
    if intent == "분석":
        suggest_skill = "Explore Agent"
    elif intent == "수정":
        suggest_skill = "/plan"
    elif intent == "검사":
        suggest_skill = "/audit"

    AskUserQuestion(
        questions=[{
            "question": f"승인된 프롬프트로 {suggest_skill}를 실행할까요?",
            "header": "Next Step",
            "options": [
                {"label": f"예, {suggest_skill} 실행", "description": "바로 진행"},
                {"label": "아니요, 프롬프트만 저장", "description": "나중에 사용"}
            ]
        }]
    )
```

### 6.2 로그 재사용

```bash
# 이전 로그 확인
ls .agent/plans/clarify_*.md

# 특정 로그 참조
/clarify --resume {slug}
```

---

## 7. Error Handling

| 상황 | 처리 |
|------|------|
| claude-code-guide 실패 | WebSearch 폴백 |
| 로그 저장 실패 | 메모리에 유지 + 경고 |
| 사용자 무응답 | 3회 후 자동 저장 |
