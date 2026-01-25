---
name: clarify
description: |
  PE 기법을 적용하여 사용자 요청을 반복적으로 개선.
  Semantic Integrity를 유지하는 YAML 로그 생성.
  스킬 파이프라인의 진입점으로 설계됨.
user-invocable: true
disable-model-invocation: true
context: fork
model: sonnet
version: "2.2.0"
argument-hint: "<request> | --resume <slug>"
allowed-tools:
  - Read
  - Grep
  - Glob
  - AskUserQuestion
  - Task
  - WebSearch
hooks:
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/clarify-validate.sh"
      timeout: 10000
    - type: command
      command: "/home/palantir/.claude/hooks/clarify-finalize.sh"
      timeout: 150000
---

# /clarify - Prompt Engineering Loop (V2.1.0)

> **Role:** 사용자 요청 명확화 + PE 기법 적용
> **Core Principle:** YAML Machine-Readable 로그 → Semantic Integrity 유지
> **Access Pattern:** P1 (User-Only) - 사용자 명시적 호출만 허용
> **Compatible:** V2.1.19 Skill Frontmatter Spec

---

## 1. Execution Protocol

### 1.1 Argument Parsing

```bash
# $ARGUMENTS 파싱
if [[ "$ARGUMENTS" == --resume* ]]; then
    RESUME_MODE=true
    SLUG="${ARGUMENTS#--resume }"
    # Workload-scoped path (V2.2.0)
    LOG_PATH=".agent/prompts/${SLUG}/clarify.yaml"
else
    RESUME_MODE=false
    USER_INPUT="$ARGUMENTS"
fi
```

### 1.2 Initialize (New Session)

```bash
# Source helper functions
source /home/palantir/.claude/skills/clarify/helpers.sh

# Generate unique session
SLUG=$(yaml_generate_slug "$USER_INPUT")
# Workload-scoped path (V2.2.0)
WORKLOAD_DIR=".agent/prompts/${SLUG}"
LOG_PATH="${WORKLOAD_DIR}/clarify.yaml"

# Create workload directory and YAML log
mkdir -p "${WORKLOAD_DIR}"
yaml_init_log "$LOG_PATH" "$USER_INPUT"
```

### 1.3 Resume (Existing Session)

```bash
if [[ "$RESUME_MODE" == "true" ]]; then
    # Load existing session
    if [[ ! -f "$LOG_PATH" ]]; then
        echo "❌ Session not found: $SLUG"
        exit 1
    fi

    # Extract last state
    ROUND_NUM=$(yaml_get_field "$LOG_PATH" ".metadata.rounds")
    CURRENT_INPUT=$(yaml_get_field "$LOG_PATH" ".rounds[-1].improved_prompt")
fi
```

---

## 2. YAML Log Schema

### 2.1 Full Schema

```yaml
# .agent/prompts/{slug}/clarify.yaml (Workload-scoped V2.2.0)
metadata:
  id: "{slug}"
  version: "2.0.0"
  created_at: "2026-01-24T18:13:32Z"
  updated_at: "2026-01-24T18:15:00Z"
  status: "in_progress"  # in_progress | completed | cancelled
  rounds: 0
  final_approved: false

original_request: |
  {원본 사용자 요청}

rounds:
  - round: 1
    timestamp: "2026-01-24T18:13:35Z"
    input: "{현재 라운드 입력}"
    pe_technique:
      name: "Chain of Thought"
      reason: "분석 작업에 단계별 사고가 적합"
    improved_prompt: |
      {개선된 프롬프트}
    user_response: "승인"  # 승인 | 수정요청 | 기법변경 | 취소
    user_feedback: null

final_output:
  approved_prompt: |
    {최종 승인된 프롬프트}
  pe_techniques_applied:
    - "Chain of Thought"
    - "Structured Output"

# Pipeline Integration Fields
pipeline:
  downstream_skills: []    # 이후 호출된 스킬 추적
  task_references: []      # 연결된 Task ID
  context_hash: null       # SHA256 무결성 해시
  decision_trace:          # 주요 결정 기록
    - round: 1
      decision: "CoT 적용"
      reason: "분석 작업"
```

### 2.2 Schema Sections

| Section | Purpose | When Updated |
|---------|---------|--------------|
| `metadata` | 세션 메타데이터 | 매 라운드 |
| `original_request` | 원본 요청 보존 | 초기화 시 |
| `rounds` | 라운드별 상호작용 | 매 라운드 |
| `final_output` | 최종 승인 결과 | 승인 시 |
| `pipeline` | 스킬 파이프라인 통합 | Stop hook |

---

## 3. Main Loop

```python
APPROVED = False
ROUND_NUM = 1

while not APPROVED:
    # Step 1: PE 기법 선택 (내장 레퍼런스 참조)
    technique = select_pe_technique(current_input)

    # Step 2: 프롬프트 개선
    improved = apply_pe_technique(current_input, technique)

    # Step 3: YAML 로그 기록 (응답 전)
    yaml_append_round(
        log_path=LOG_PATH,
        round_num=ROUND_NUM,
        input=current_input,
        technique=technique,
        improved=improved,
        response="pending"
    )

    # Step 4: 사용자에게 제시
    present_round_result(ROUND_NUM, current_input, technique, improved)

    # Step 5: AskUserQuestion (enhanced)
    response = AskUserQuestion(
        questions=[{
            "question": "개선된 프롬프트를 확인해주세요. 어떻게 하시겠습니까?",
            "header": f"Round {ROUND_NUM}",
            "options": [
                {"label": "승인 (Recommended)", "description": "이 프롬프트로 진행"},
                {"label": "수정 요청", "description": "피드백을 입력하고 다시 시도"},
                {"label": "다른 기법 시도", "description": "다른 PE 기법으로 개선"}
            ],
            "multiSelect": False
        }],
        metadata={"source": f"clarify-round-{ROUND_NUM}"}
    )

    # Step 6: 응답 처리
    if response == "승인":
        APPROVED = True
        yaml_finalize(LOG_PATH, improved)
        yaml_update_round(LOG_PATH, ROUND_NUM, "user_response", "승인")
    elif response == "수정 요청":
        feedback = get_user_feedback()
        current_input = feedback
        yaml_update_round(LOG_PATH, ROUND_NUM, "user_response", "수정요청")
        yaml_update_round(LOG_PATH, ROUND_NUM, "user_feedback", feedback)
        ROUND_NUM += 1
    elif response == "다른 기법 시도":
        yaml_update_round(LOG_PATH, ROUND_NUM, "user_response", "기법변경")
        ROUND_NUM += 1
    else:
        yaml_cancel(LOG_PATH, "User cancelled")
        break
```

---

## 4. PE Technique Reference (Built-in)

### 4.1 Basic Techniques

| Technique | Use Case | Prompt Pattern |
|-----------|----------|----------------|
| **Chain of Thought (CoT)** | 분석, 디버깅, 복잡한 추론 | "단계별로 생각해보세요..." |
| **Few-Shot** | 코드 생성, 형식 지정 | "다음 예시를 참고하세요:\n예시1: ...\n예시2: ..." |
| **Role Prompting** | 전문가 관점, 특정 페르소나 | "당신은 [역할]입니다..." |
| **Structured Output** | 복잡한 출력 표준화 | "다음 형식으로 출력하세요:\n```yaml\n...\n```" |

### 4.2 Extended Techniques

| Technique | Use Case | Note |
|-----------|----------|------|
| **Task Decomposition** | 대규모 작업 분해 | `/orchestrate`에 더 적합 |
| **Constraint Setting** | 범위 제한, 제약 조건 | "다음 제약 조건을 지켜주세요: ..." |
| **Self-Consistency** | 신뢰성 향상 | 다중 샘플링 + 투표 |
| **Tree of Thoughts** | 복잡한 문제 해결 | 분기 탐색, 역추적 |

### 4.3 Technique Selection Logic

```python
def select_pe_technique(input_text):
    """입력 분석 → 적절한 PE 기법 선택"""

    # Intent classification
    if contains_analysis_keywords(input_text):
        return "Chain of Thought"
    elif contains_code_keywords(input_text):
        return "Few-Shot + Structured Output"
    elif contains_creative_keywords(input_text):
        return "Role Prompting"
    elif contains_complex_task_keywords(input_text):
        return "Task Decomposition"
    else:
        return "Structured Output"  # Default
```

---

## 5. User Interaction Format

### 5.1 Round Presentation

```markdown
## Round {n} 결과

### 입력
{input}

### 분석
이 요청은 **{intent}**를 원하는 것으로 보입니다.

### 적용한 PE 기법
**{technique_name}**
{technique_description}

### 개선된 프롬프트

```
{improved_prompt}
```

### 개선 포인트
- {point_1}
- {point_2}
```

### 5.2 AskUserQuestion Configuration

```yaml
# Enhanced AskUserQuestion
questions:
  - question: "개선된 프롬프트를 확인해주세요. 어떻게 하시겠습니까?"
    header: "Round N"
    options:
      - label: "승인 (Recommended)"
        description: "이 프롬프트로 진행"
      - label: "수정 요청"
        description: "피드백을 입력하고 다시 시도"
      - label: "다른 기법 시도"
        description: "다른 PE 기법으로 개선"
    multiSelect: false
metadata:
  source: "clarify-round-N"  # 추적용
```

---

## 6. Exit Conditions

### 6.1 Normal Exit (Success)

- User selects "승인"
- YAML status: `completed`
- Stop hooks trigger:
  1. `clarify-validate.sh` - Gate 1: Requirement Feasibility Validation
  2. `clarify-finalize.sh` - Finalization and pipeline integration

### 6.2 Abnormal Exit

| Condition | YAML Status | Recovery |
|-----------|-------------|----------|
| User cancels | `cancelled` | `/clarify --resume {slug}` |
| Error | `error` | Check logs, retry |
| Session timeout | `timeout` | Resume possible |

---

## 7. Post-Approval Routing

```python
if approved:
    # 의도에 따라 다음 스킬 제안
    intent = analyze_intent(final_prompt)

    suggestions = {
        "분석": "Explore Agent",
        "계획": "/plan",
        "수정": "/build",
        "검사": "/audit",
        "조율": "/orchestrate"
    }

    suggested = suggestions.get(intent, "직접 실행")

    AskUserQuestion(
        questions=[{
            "question": f"승인된 프롬프트로 {suggested}을(를) 실행할까요?",
            "header": "Next Step",
            "options": [
                {"label": f"예, {suggested} 실행 (Recommended)",
                 "description": "바로 진행"},
                {"label": "아니요, 프롬프트만 저장",
                 "description": "나중에 사용"}
            ],
            "multiSelect": False
        }],
        metadata={"source": "clarify-routing"}
    )
```

---

## 8. Integration Points

### 8.1 Skill Pipeline

```
/clarify (진입점)
    │
    ▼ [YAML 로그 생성]
/orchestrate or /plan
    │
    ▼ [downstream_skills 추적]
/build or Worker
    │
    ▼ [task_references 연결]
/commit-push-pr
```

### 8.2 Log Reuse

```bash
# 이전 세션 목록 (Workload-scoped)
ls .agent/prompts/*/clarify.yaml

# 특정 세션 재개
/clarify --resume {slug}

# 로그 검색
grep -l "Chain of Thought" .agent/prompts/*/clarify.yaml
```

### 8.3 Task Delegation Pattern (V2.1.16+)

> **Reference:** `/build/parameters/task-params.md`

PE 기법 검색 시 Task 도구 사용:

```python
# Background research delegation (optional)
Task(
    subagent_type="Explore",
    prompt="Search for PE technique examples in codebase",
    run_in_background=True,  # 비동기 실행
    max_turns=10             # 빠른 탐색
)
```

### 8.4 Model Inheritance (V2.1.16+)

> **Reference:** `/build/parameters/model-selection.md`

| Option | Behavior |
|--------|----------|
| `sonnet` (current) | 균형 잡힌 품질/속도 |
| `inherit` | 부모 컨텍스트 모델 사용 (CLI에서 지정 시) |
| `haiku` | 빠른 응답 (간단한 요청 시) |

---

## 9. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| YAML write failure | File I/O error | Memory fallback + warning |
| Invalid PE technique | Selection failure | Default to Structured Output |
| User timeout | No response | Auto-save, resume later |
| Hook failure | Stop hook error | Manual finalization |

---

## 10. Shift-Left Validation (Gate 1)

### 10.1 Purpose

Gate 1 validates requirement feasibility **before** proceeding to `/research`:
- Detects potentially missing files early
- Identifies vague requirements needing clarification
- Catches destructive operations before execution

### 10.2 Hook Integration

```yaml
hooks:
  Stop:
    - clarify-validate.sh  # Gate 1: Requirement Feasibility
    - clarify-finalize.sh  # Pipeline integration
```

### 10.3 Validation Results

| Result | Behavior | User Action |
|--------|----------|-------------|
| `passed` | ✅ Continue to next phase | None required |
| `passed_with_warnings` | ⚠️ Display warnings, allow proceed | Review warnings |
| `failed` | ❌ Block progression, request clarification | Address errors, re-run `/clarify` |

---

## 11. Testing Checklist

- [ ] `/clarify "테스트 요청"` 기본 실행
- [ ] `/clarify --resume {slug}` 재개 테스트
- [ ] YAML 로그 스키마 검증
- [ ] AskUserQuestion metadata.source 확인
- [ ] Stop hook 트리거 확인
- [ ] Gate 1 validation 실행 확인
- [ ] Warning/Error 표시 확인
- [ ] 다중 라운드 진행 테스트
- [ ] Pipeline downstream_skills 추적 테스트

---

## 11. Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `sonnet` 설정, `inherit` 지원 문서화 |
| `context-mode.md` | ✅ | `fork` 사용, Task 위임 패턴 명시 |
| `tool-config.md` | ✅ | V2.1.0: `TodoWrite` 제거, Task API 사용 |
| `hook-config.md` | ✅ | Stop hook, 150000ms timeout |
| `permission-mode.md` | N/A | Skill에는 해당 없음 (Agent 전용) |
| `task-params.md` | ✅ | 8.3절 Task Delegation Pattern 참조 |

### Version History

| Version | Change |
|---------|--------|
| 2.0.0 | YAML 로깅, Stop hook, PE 내장 라이브러리 |
| 2.1.0 | `TodoWrite` 제거, Task API 표준화, 파라미터 모듈 호환성 |
| 2.2.0 | Workload-scoped 출력 경로 (V7.1 호환) |
