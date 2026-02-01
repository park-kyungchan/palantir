---
name: re-architecture
description: |
  **파이프라인 컴포넌트 분해 및 피드백 도구** - 전체 파이프라인을 컴포넌트별로 분해하여
  각각의 세부사항에 대한 피드백을 제공합니다.

  핵심 기능:
  - 모든 상호작용 과정을 Machine-Readable YAML 형식으로 기록
  - 설계 의도와 이슈 추적을 위한 traceability 스키마
  - 매 프롬프트마다 문서 업데이트 (incremental logging)
  - /research 스킬과 연계하여 skill-driven pipeline 지원

user-invocable: true
disable-model-invocation: false
context: fork
model: opus
argument-hint: "<target-path> | --resume <slug>"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Task
  - Write
  - Edit
  - AskUserQuestion
  - mcp__sequential-thinking__sequentialthinking
hooks:
  Setup:
    - type: command
      command: "/home/palantir/.claude/hooks/re-architecture-setup.sh"
      timeout: 10000
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/re-architecture-finalize.sh"
      timeout: 180000
---

# /re-architecture - Pipeline Component Analysis & Feedback (V1.0.0)

> **Role:** 파이프라인 컴포넌트 분해 + 의사결정 지원 피드백 제공
> **Core Principle:** Machine-Readable YAML 로그 → Traceability 유지
> **Access Pattern:** P1 (User-Only) - 사용자 명시적 호출만 허용
> **Downstream:** `/research` 스킬과 연계

---

## CRITICAL REQUIREMENTS

### Language Requirement
**모든 출력은 한국어로 작성해야 합니다.**
- All prompts, explanations, and interactions MUST be in Korean
- User-facing text MUST be in Korean
- YAML field names can use English but descriptions should be in Korean

### Complete Traceability Logging
**모든 상호작용은 YAML 로그에 기록됩니다.**
- 설계 의도(design_intent) 필수 기록
- 이슈 추적을 위한 structured schema
- Incremental update: 매 라운드마다 문서 업데이트
- Workload-scoped output: `.agent/prompts/{slug}/re-architecture-log.yaml`

### Decision Support
**컴포넌트별 피드백을 통한 의사결정 지원**
- 각 컴포넌트에 대해 findings, recommendations, issues 제공
- 사용자의 명확한 의도와 요구사항 기록
- 판단근거(rationale) 명시

---

## 1. Execution Protocol

### 1.1 Argument Parsing

```bash
# $ARGUMENTS 파싱
if [[ "$ARGUMENTS" == --resume* ]]; then
    RESUME_MODE=true
    SLUG="${ARGUMENTS#--resume }"
    LOG_PATH=".agent/prompts/${SLUG}/re-architecture-log.yaml"
else
    RESUME_MODE=false
    TARGET_PATH="$ARGUMENTS"
fi
```

### 1.2 Initialize (New Session)

```bash
# Source helper functions
source /home/palantir/.claude/skills/shared/slug-generator.sh
source /home/palantir/.claude/skills/shared/workload-tracker.sh

# Generate unique session
SLUG=$(generate_slug "re-arch" "$TARGET_PATH")
WORKLOAD_DIR=".agent/prompts/${SLUG}"
LOG_PATH="${WORKLOAD_DIR}/re-architecture-log.yaml"

# Create workload directory and YAML log
mkdir -p "${WORKLOAD_DIR}"
yaml_init_architecture_log "$LOG_PATH" "$TARGET_PATH"
```

### 1.3 Resume (Existing Session)

```bash
if [[ "$RESUME_MODE" == "true" ]]; then
    if [[ ! -f "$LOG_PATH" ]]; then
        echo "❌ Session not found: $SLUG"
        exit 1
    fi

    # Load existing state
    CURRENT_COMPONENT=$(yaml_get_field "$LOG_PATH" ".state.current_component")
    ROUND_NUM=$(yaml_get_field "$LOG_PATH" ".state.round")
fi
```

---

## 2. YAML Log Schema (Traceability Focus)

### 2.1 Full Schema

```yaml
# .agent/prompts/{slug}/re-architecture-log.yaml

metadata:
  id: "{slug}"
  version: "1.0.0"
  created_at: "2026-01-26T21:10:00Z"
  updated_at: "2026-01-26T21:15:00Z"
  status: "in_progress"  # in_progress | completed | paused
  target_path: "{분석 대상 경로}"

# 세션 상태 추적
state:
  current_phase: "decomposition"  # decomposition | analysis | feedback | handoff
  current_component: null
  round: 1
  total_components: 0
  analyzed_components: 0

# 사용자 의도 및 요구사항 (CRITICAL for traceability)
user_intent:
  original_request: |
    {사용자 원본 요청}
  clarified_goals: []    # 명확화된 목표들
  constraints: []        # 제약 조건
  priorities: []         # 우선순위

# 컴포넌트 분해 결과
decomposition:
  pipeline_structure: |
    {파이프라인 구조 다이어그램}
  components:
    - id: "comp-001"
      name: "{컴포넌트명}"
      path: "{파일/디렉토리 경로}"
      type: "stage|module|service|utility"
      dependencies:
        upstream: []
        downstream: []
      status: "pending"  # pending | analyzing | completed

# 상호작용 라운드 기록 (Incremental)
rounds:
  - round: 1
    timestamp: "2026-01-26T21:11:00Z"
    phase: "decomposition"
    component_id: null

    # 입력
    input:
      prompt: "{사용자/시스템 입력}"
      context: "{관련 컨텍스트}"

    # 분석 결과
    analysis:
      findings: []           # 발견사항
      recommendations: []    # 권장사항
      issues: []             # 잠재적 이슈
      code_evidence: []      # 코드 근거

    # 출력
    output:
      feedback: |
        {생성된 피드백}
      options_presented:     # 제시된 선택지
        - label: "{선택지}"
          rationale: "{판단근거}"
      user_selection: null   # 사용자 선택

    # 추적성 필드 (CRITICAL)
    traceability:
      design_intent: |
        {이 라운드의 설계 의도}
      decision_rationale: |
        {결정 판단근거}
      related_components: []
      parent_round: null     # 이전 라운드 참조
      issue_refs: []         # 관련 이슈 ID

# 컴포넌트별 피드백 결과
component_feedback:
  "comp-001":
    analyzed_at: "2026-01-26T21:12:00Z"
    summary: "{컴포넌트 요약}"

    findings:
      - id: "find-001"
        type: "pattern|issue|opportunity"
        severity: "info|warning|critical"
        description: "{발견사항 상세}"
        evidence:
          file: "{파일 경로}"
          line: "{라인 번호}"
          snippet: "{코드 스니펫}"

    recommendations:
      - id: "rec-001"
        priority: "high|medium|low"
        description: "{권장사항}"
        rationale: "{판단근거}"
        effort_estimate: "small|medium|large"

    issues:
      - id: "issue-001"
        type: "bug|debt|risk|improvement"
        severity: "critical|high|medium|low"
        description: "{이슈 설명}"
        suggested_action: "{권장 조치}"
        blocking: false

# 핸드오프 정보 (/research 연계)
handoff:
  ready_for_research: false
  research_context:
    summary: "{분석 요약}"
    key_findings: []
    priority_components: []
    recommended_focus: []
  next_action_hint: "/research --clarify-slug {slug}"

# 파이프라인 통합
pipeline:
  downstream_skills: []
  context_hash: null
```

### 2.2 Schema Design Rationale

| Section | Purpose | Traceability Value |
|---------|---------|-------------------|
| `metadata` | 세션 메타데이터 | 시간/버전 추적 |
| `state` | 현재 진행 상태 | 재개 지원 |
| `user_intent` | 사용자 의도/요구사항 | **의사결정 근거** |
| `decomposition` | 컴포넌트 분해 | 구조 파악 |
| `rounds` | 상호작용 기록 | **전체 이력 추적** |
| `component_feedback` | 컴포넌트별 결과 | 상세 분석 |
| `handoff` | /research 연계 | 파이프라인 연결 |

---

## 3. Main Execution Flow

### Phase 1: Decomposition (컴포넌트 분해)

```python
# 3.1 Sequential Thinking으로 구조 분석
mcp__sequential-thinking__sequentialthinking(
    thought="대상 파이프라인 구조 분석 시작",
    thoughtNumber=1,
    totalThoughts=5,
    nextThoughtNeeded=True
)

# 3.2 파이프라인 구조 탐색
structure = Task(
    subagent_type="Explore",
    prompt=f"Analyze pipeline structure at {target_path}. Identify all components, stages, and their dependencies.",
    model="opus"
)

# 3.3 컴포넌트 목록 생성
components = extract_components(structure)

# 3.4 YAML 로그 업데이트
yaml_update_decomposition(LOG_PATH, components)

# 3.5 사용자에게 분해 결과 제시
present_decomposition_result(components)
```

### Phase 2: Iterative Component Analysis

```python
for component in components:
    # =========================================================================
    # Step 1: 컴포넌트 심층 분석
    # =========================================================================
    analysis = analyze_component(component)

    # =========================================================================
    # Step 2: YAML 로그 기록 (분석 전)
    # =========================================================================
    yaml_append_round(
        log_path=LOG_PATH,
        round_num=ROUND_NUM,
        phase="analysis",
        component_id=component.id,
        input={"prompt": f"Analyzing {component.name}", "context": component.path},
        traceability={
            "design_intent": f"{component.name} 컴포넌트의 구조와 역할 파악",
            "parent_round": ROUND_NUM - 1 if ROUND_NUM > 1 else None
        }
    )

    # =========================================================================
    # Step 3: 피드백 생성 (findings, recommendations, issues)
    # =========================================================================
    feedback = generate_component_feedback(component, analysis)

    # =========================================================================
    # Step 4: 사용자에게 피드백 제시 + 의사결정 지원
    # =========================================================================
    options = [
        {
            "label": "피드백 승인",
            "description": "이 컴포넌트 분석을 승인하고 다음으로 진행",
            "rationale": f"{len(feedback.findings)}개 발견사항, {len(feedback.recommendations)}개 권장사항 확인됨"
        },
        {
            "label": "추가 분석 요청",
            "description": "특정 영역에 대해 더 깊은 분석 진행",
            "rationale": "현재 분석이 충분하지 않다고 판단될 경우"
        },
        {
            "label": "이슈 등록",
            "description": "발견된 문제를 이슈로 등록",
            "rationale": f"{len(feedback.issues)}개 잠재적 이슈가 감지됨"
        },
        {
            "label": "건너뛰기",
            "description": "이 컴포넌트를 건너뛰고 다음으로",
            "rationale": "우선순위가 낮거나 이미 충분히 파악됨"
        }
    ]

    response = AskUserQuestion(
        questions=[{
            "question": f"{component.name} 컴포넌트 분석 결과입니다. 어떻게 진행하시겠습니까?",
            "header": f"컴포넌트 #{component_index}",
            "options": [{"label": o["label"], "description": f"{o['description']}\n📋 근거: {o['rationale']}"} for o in options],
            "multiSelect": False
        }]
    )

    # =========================================================================
    # Step 5: YAML 로그 업데이트 (응답 후)
    # =========================================================================
    yaml_update_round(LOG_PATH, ROUND_NUM, {
        "analysis": feedback,
        "output": {
            "options_presented": options,
            "user_selection": response
        },
        "traceability": {
            "decision_rationale": f"사용자가 '{response}'를 선택함"
        }
    })

    # =========================================================================
    # Step 6: 컴포넌트 피드백 저장
    # =========================================================================
    yaml_save_component_feedback(LOG_PATH, component.id, feedback)

    ROUND_NUM += 1
```

### Phase 3: Handoff Preparation (/research 연계)

```python
# 3.1 분석 결과 종합
summary = synthesize_all_feedback(LOG_PATH)

# 3.2 핸드오프 컨텍스트 생성
handoff_context = {
    "summary": summary.overview,
    "key_findings": summary.top_findings,
    "priority_components": summary.priority_list,
    "recommended_focus": summary.focus_areas
}

# 3.3 YAML 업데이트
yaml_update_handoff(LOG_PATH, handoff_context)

# 3.4 사용자에게 핸드오프 옵션 제시
AskUserQuestion(
    questions=[{
        "question": "분석이 완료되었습니다. /research로 진행하시겠습니까?",
        "header": "핸드오프",
        "options": [
            {"label": "/research로 진행 (권장)", "description": f"분석 결과를 바탕으로 심층 연구 시작\n📋 근거: {len(summary.key_findings)}개 주요 발견사항이 추가 연구 필요"},
            {"label": "분석 결과만 저장", "description": "나중에 수동으로 /research 호출\n📋 근거: 현재 결과만으로 충분하거나 다른 작업 우선"},
            {"label": "추가 분석 진행", "description": "놓친 컴포넌트 추가 분석\n📋 근거: 일부 영역이 충분히 분석되지 않음"}
        ],
        "multiSelect": False
    }]
)
```

---

## 4. Incremental Document Update Protocol

### 4.1 Update Strategy

```python
def yaml_append_round(log_path, round_num, **kwargs):
    """
    매 라운드마다 YAML 문서에 새 엔트리 추가
    - 기존 내용 보존
    - 새 라운드 append
    - metadata.updated_at 갱신
    """
    current = Read(log_path)

    # 새 라운드 엔트리 생성
    new_round = {
        "round": round_num,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }

    # rounds 배열에 추가
    current["rounds"].append(new_round)

    # metadata 갱신
    current["metadata"]["updated_at"] = datetime.now().isoformat()
    current["state"]["round"] = round_num

    # 파일 업데이트
    Write(log_path, yaml_dump(current))
```

### 4.2 Partial Update (성능 최적화)

```python
def yaml_update_round(log_path, round_num, updates):
    """
    특정 라운드의 필드만 업데이트
    - 전체 파일 재작성 대신 타겟 업데이트
    """
    # Edit 도구 사용으로 부분 업데이트
    for key, value in updates.items():
        Edit(
            file_path=log_path,
            old_string=f"round: {round_num}\n",
            new_string=f"round: {round_num}\n    {key}: {yaml_inline(value)}\n"
        )
```

---

## 5. Output Format

### 5.1 Round Presentation

```markdown
## 라운드 {n}: {component_name} 분석

### 컴포넌트 정보
- **경로:** {path}
- **유형:** {type}
- **의존성:** {dependencies}

### 발견사항 (Findings)
| ID | 유형 | 심각도 | 설명 |
|----|------|--------|------|
| find-001 | pattern | info | {description} |

### 권장사항 (Recommendations)
| ID | 우선순위 | 설명 | 판단근거 |
|----|----------|------|----------|
| rec-001 | high | {description} | {rationale} |

### 이슈 (Issues)
| ID | 유형 | 심각도 | 설명 | 권장 조치 |
|----|------|--------|------|----------|
| issue-001 | debt | medium | {description} | {action} |

### 설계 의도 (Design Intent)
{design_intent_explanation}
```

### 5.2 L1 Return Summary

```yaml
taskId: re-arch-{slug}
status: success
summary: "{n}개 컴포넌트 분석 완료, {findings}개 발견사항, {issues}개 이슈"

logPath: .agent/prompts/{slug}/re-architecture-log.yaml
handoffReady: true
nextActionHint: "/research --clarify-slug {slug}"
```

---

## 6. Integration Points

### 6.1 Pipeline Position

```
/re-architecture  ◄── THIS SKILL (Entry Point)
    │
    │ re-architecture-log.yaml
    ▼
/research                    심층 연구 (선택적)
    │
    ▼
/planning                    구현 계획 수립
```

### 6.2 /research Handoff Contract

| Field | Type | Description |
|-------|------|-------------|
| `handoff.summary` | string | 분석 요약 |
| `handoff.key_findings` | array | 주요 발견사항 |
| `handoff.priority_components` | array | 우선 분석 컴포넌트 |
| `handoff.recommended_focus` | array | 권장 연구 영역 |

---

## 7. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| Target path not found | File/dir not exists | Prompt for correct path |
| YAML write failure | I/O error | Memory fallback + warning |
| Component analysis timeout | >5min | Save partial, allow resume |
| User session timeout | No response | Auto-save, resume later |

---

## 8. Testing Checklist

- [ ] `/re-architecture <path>` 기본 실행
- [ ] `/re-architecture --resume {slug}` 재개 테스트
- [ ] YAML 로그 스키마 검증
- [ ] Incremental update 동작 확인
- [ ] 컴포넌트 분해 정확성
- [ ] 피드백 생성 품질
- [ ] /research 핸드오프 연계
- [ ] traceability 필드 기록 확인
- [ ] 한국어 출력 검증
- [ ] Stop hook 트리거 확인

---

## 9. Parameter Module Compatibility (V2.1.0)

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `opus` for comprehensive analysis |
| `context-mode.md` | ✅ | `fork` for isolated execution |
| `tool-config.md` | ✅ | Read, Grep, Glob, Task, Write, Edit, AskUserQuestion, MCP |
| `hook-config.md` | ✅ | Stop hook, 180000ms timeout |
| `permission-mode.md` | N/A | Skill-specific |
| `task-params.md` | ✅ | Explore delegation for structure analysis |

### Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Initial /re-architecture skill implementation |

---

*Created by /build skill | 2026-01-26*
