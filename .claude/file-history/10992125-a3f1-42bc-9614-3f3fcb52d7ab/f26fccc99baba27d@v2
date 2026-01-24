# Claude Code Task System Integration Report

> **Report ID:** PALANTIR-20260124-TASK-INTEGRATION
> **Generated:** 2026-01-24
> **Task List ID:** `palantir-20260124`
> **Target Audience:** Main Agent Orchestrator
> **Purpose:** Agents/Skills/Hooks 개선을 위한 Native Task System 통합 전략

---

## Executive Summary

현재 Palantir 프로젝트는 **파일 기반 조율 시스템** (`.agent/prompts/`, `_progress.yaml`)과 **Progressive Disclosure (L1/L2/L3)** 패턴을 사용하고 있습니다. Claude Code v2.1.16+에서 도입된 **Native Task System**은 의존성 추적, 상태 관리, 크로스 세션 지속성을 제공하여 현재 시스템을 크게 개선할 수 있습니다.

### 핵심 권장사항

| 영역 | 현재 | 개선 후 |
|------|------|---------|
| 태스크 의존성 | `_progress.yaml` 수동 관리 | `blockedBy`/`blocks` 자동 추적 |
| 상태 추적 | 파일 이동 (pending→completed) | `status` 필드 자동 업데이트 |
| 크로스 터미널 | 파일 폴링 | `CLAUDE_CODE_TASK_LIST_ID` 공유 |
| L1/L2/L3 캐싱 | `~/.claude/cache/l1l2/` | Task `metadata` 필드 활용 |

---

## 1. 현재 아키텍처 분석

### 1.1 파일 기반 조율 시스템 (현재)

```
.agent/
├── prompts/
│   ├── pending/          # 대기 중인 태스크
│   ├── active/           # 실행 중 (수동 이동)
│   └── completed/        # 완료된 태스크 (감사 추적)
├── outputs/
│   └── {agentType}/{taskId}.md  # L3 상세 출력
└── logs/
    ├── task_execution.log
    ├── prompt_lifecycle.log
    └── agent_ids.log
```

**문제점:**
1. **수동 상태 관리**: 파일을 디렉토리 간 이동해야 상태 변경
2. **의존성 추적 없음**: `_progress.yaml`에서 수동으로 `blockedBy` 관리
3. **경쟁 조건**: 멀티 터미널에서 동시 파일 접근 시 충돌 가능
4. **복잡한 훅 체인**: `pd-task-interceptor.sh` → `pd-task-processor.sh` 필요

### 1.2 현재 에이전트/스킬/훅 인벤토리

**에이전트 (4개):**
| Agent | Model | Context | Purpose |
|-------|-------|---------|---------|
| `onboarding-guide` | haiku | standard | 사용자 온보딩 |
| `pd-readonly-analyzer` | haiku | fork | 읽기 전용 분석 |
| `pd-skill-loader` | sonnet | standard | 스킬 사전 로딩 |
| `clarify-agent` | opus | fork | 요구사항 명확화 (deprecated) |

**스킬 (19개):**
- **오케스트레이션**: `orchestrate`, `assign`, `worker`, `workers`, `collect`
- **계획**: `plan-draft`, `plan-l1l2l3`, `explore-l1l2l3`
- **실행**: `build`, `build-research`, `commit-push-pr`, `docx-automation`
- **유틸리티**: `clarify`, `pd-analyzer`, `pd-injector`

**훅 (5개):**
- **세션**: `session-start.sh`, `session-end.sh`
- **태스크 파이프라인**: `pd-task-interceptor.sh`, `pd-task-processor.sh`, `pd-context-injector.sh`

---

## 2. Native Task System 장점 분석

### 2.1 핵심 기능 비교

| 기능 | 파일 기반 | Native Task System |
|------|-----------|-------------------|
| **의존성 그래프** | ❌ 수동 YAML | ✅ `blockedBy`/`blocks` 자동 |
| **상태 워크플로우** | ❌ 디렉토리 이동 | ✅ `pending→in_progress→completed` |
| **소유권** | ❌ 없음 | ✅ `owner` 필드 |
| **메타데이터** | ❌ 별도 파일 | ✅ `metadata` 필드 |
| **크로스 세션** | ⚠️ 파일 기반 | ✅ `CLAUDE_CODE_TASK_LIST_ID` |
| **CLI 접근** | ❌ 없음 | ✅ `/tasks` 명령 |
| **경쟁 조건** | ⚠️ 파일 잠금 필요 | ✅ 원자적 업데이트 |

### 2.2 Task API 상세

```python
# 태스크 생성
TaskCreate(
    subject="구현할 기능 제목",           # 필수: 명령형
    description="상세 요구사항...",       # 필수: 완료 조건 포함
    activeForm="기능 구현 중",            # 권장: 스피너 표시용
    metadata={                            # 선택: 커스텀 데이터
        "phase": "1",
        "terminal": "B",
        "l1_cache_key": "abc123",
        "priority": "HIGH"
    }
)

# 의존성 설정
TaskUpdate(
    taskId="2",
    addBlockedBy=["1"],     # 태스크 1 완료 후 시작 가능
    addBlocks=["3", "4"]    # 태스크 2가 3, 4를 블록
)

# 상태 변경
TaskUpdate(taskId="1", status="in_progress")
TaskUpdate(taskId="1", status="completed")

# 전체 목록 조회
TaskList()  # blockedBy 정보 포함

# 상세 조회
TaskGet(taskId="1")  # description, blocks, blockedBy 전체
```

---

## 3. 통합 전략

### 3.1 Phase 1: 하이브리드 모드 (권장 시작점)

**파일 기반 유지 + Native Task 보조 사용**

```
┌─────────────────────────────────────────────────────────┐
│ ORCHESTRATOR (Terminal A)                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ TaskCreate() for each worker task                   │ │
│ │ TaskUpdate(addBlockedBy=[...]) for dependencies     │ │
│ │ TaskList() for status dashboard                     │ │
│ └─────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Terminal B  │ │ Terminal C  │ │ Terminal D  │
│  (Worker)   │ │  (Worker)   │ │  (Worker)   │
│             │ │             │ │             │
│ TaskUpdate  │ │ TaskUpdate  │ │ TaskUpdate  │
│ (in_progress│ │ (in_progress│ │ (in_progress│
│ →completed) │ │ →completed) │ │ →completed) │
└─────────────┘ └─────────────┘ └─────────────┘

.agent/prompts/ → L1/L2/L3 출력 저장 (유지)
Native Task   → 상태/의존성 추적 (신규)
```

**장점:**
- 기존 L1/L2/L3 파이프라인 유지
- 점진적 마이그레이션 가능
- 두 시스템의 장점 결합

### 3.2 Phase 2: 완전 통합 모드

**Native Task System 중심 + 파일은 출력만**

```yaml
# 태스크 메타데이터에 L1 정보 저장
metadata:
  l1Summary: "taskId: abc123\npriority: HIGH..."
  l2Path: ".agent/outputs/Explore/abc123.md"
  cacheKey: "md5hash"
  terminal: "B"
  phase: "1"
```

---

## 4. 구체적 개선 영역

### 4.1 `/orchestrate` 스킬 개선

**현재:**
```yaml
# _progress.yaml 수동 관리
terminals:
  terminal-b:
    status: assigned
    blockedBy: []
```

**개선 후:**
```python
# /orchestrate 스킬 내부
TaskCreate(
    subject="Gap Analysis - Orchestration Skills",
    description="분석할 스킬: /orchestrate, /assign...",
    activeForm="Gap 분석 수행 중",
    metadata={"terminal": "B", "phase": "1"}
)

TaskCreate(
    subject="Workflow Completeness Analysis",
    description="워크플로우 완전성 분석...",
    activeForm="완전성 분석 수행 중",
    metadata={"terminal": "C", "phase": "1"}
)

# 의존성 설정
TaskCreate(
    subject="Result Synthesis",
    description="B, C 결과 종합...",
    activeForm="결과 종합 중",
    metadata={"terminal": "A", "phase": "2"}
)
TaskUpdate(taskId="3", addBlockedBy=["1", "2"])
```

### 4.2 `/worker` 스킬 개선

**현재 (파일 기반):**
```bash
# worker start b
# → .agent/prompts/pending/worker-b-*.yaml 생성
```

**개선 후 (Task + 파일):**
```python
# /worker start b
task = TaskCreate(
    subject="Worker B Task",
    description=prompt_content,
    activeForm="Worker B 실행 중",
    metadata={
        "terminal": "B",
        "promptFile": ".agent/prompts/pending/worker-b-xxx.yaml",
        "startTime": "2026-01-24T12:00:00Z"
    }
)

# /worker done b
TaskUpdate(
    taskId=task.id,
    status="completed",
    metadata={
        "endTime": "2026-01-24T12:30:00Z",
        "l1Summary": "분석 결과 요약..."
    }
)
```

### 4.3 `/workers` 스킬 개선

**현재:**
```bash
# _progress.yaml 읽어서 상태 표시
```

**개선 후:**
```python
# /workers
tasks = TaskList()

for task in tasks:
    terminal = task.metadata.get("terminal")
    status = task.status
    blockedBy = task.blockedBy

    # 시각화 출력
    print(f"Terminal {terminal}: {status}")
    if blockedBy:
        print(f"  Blocked by: {blockedBy}")
```

### 4.4 훅 시스템 간소화

**현재 (5개 훅):**
```
session-start.sh
  ↓
pd-task-interceptor.sh (PreToolUse)
  ↓
[Task 실행]
  ↓
pd-task-processor.sh (PostToolUse)
  ↓
session-end.sh
```

**개선 후 (3개 훅으로 축소):**
```
session-start.sh (유지)
  - 세션 레지스트리 생성
  - CLAUDE_CODE_TASK_LIST_ID 설정

pd-task-unified.sh (통합)
  - PreToolUse: L1/L2/L3 포맷 주입만
  - PostToolUse: TaskUpdate(metadata={l1Summary: ...})

session-end.sh (유지)
  - 미완료 태스크 저장: TaskList() → pending_tasks.json
```

**제거 가능:**
- `pd-context-injector.sh` → `pd-task-unified.sh`에 통합
- 파일 이동 로직 (pending→completed) → Native Task `status` 사용

### 4.5 L1/L2/L3 캐싱 개선

**현재:**
```
~/.claude/cache/l1l2/{hash}.json
```

**개선 후:**
```python
# 캐시 히트 시 태스크 생성 건너뛰기
existing = TaskList()
for task in existing:
    if task.metadata.get("cacheKey") == input_hash:
        # 캐시 히트 - 기존 L1 반환
        return task.metadata.get("l1Summary")

# 캐시 미스 - 새 태스크 생성
TaskCreate(
    subject="Explore Codebase",
    description=prompt,
    metadata={"cacheKey": input_hash}
)

# 완료 후 L1 저장
TaskUpdate(
    taskId=task.id,
    status="completed",
    metadata={"l1Summary": l1_output}
)
```

---

## 5. 구현 계획

### 5.1 태스크 의존성 그래프

```
┌───────────────────────────────────────────────────────────────┐
│ PHASE 1: Foundation (Day 1)                                   │
├───────────────────────────────────────────────────────────────┤
│ Task 1.1: session-start.sh 업데이트                           │
│   - CLAUDE_CODE_TASK_LIST_ID 환경 변수 설정                   │
│   - 기존 태스크 복원 로직 추가                                │
│   blockedBy: []                                               │
│                                                               │
│ Task 1.2: /workers 스킬 개선                                  │
│   - TaskList() 기반 대시보드 구현                             │
│   - 파일 기반 폴백 유지                                       │
│   blockedBy: [1.1]                                            │
│                                                               │
│ Task 1.3: /worker 스킬 개선                                   │
│   - TaskCreate/TaskUpdate 통합                                │
│   - metadata에 터미널, 파일 경로 저장                         │
│   blockedBy: [1.1]                                            │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│ PHASE 2: Orchestration (Day 2)                                │
├───────────────────────────────────────────────────────────────┤
│ Task 2.1: /orchestrate 스킬 개선                              │
│   - 태스크 의존성 그래프 자동 생성                            │
│   - blockedBy 관계 설정                                       │
│   blockedBy: [1.2, 1.3]                                       │
│                                                               │
│ Task 2.2: /assign 스킬 개선                                   │
│   - TaskCreate + owner 필드 활용                              │
│   - 터미널별 태스크 할당                                      │
│   blockedBy: [1.3]                                            │
│                                                               │
│ Task 2.3: /collect 스킬 개선                                  │
│   - TaskList(status="completed") 필터링                       │
│   - metadata.l1Summary 수집                                   │
│   blockedBy: [2.1]                                            │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│ PHASE 3: Hook Simplification (Day 3)                          │
├───────────────────────────────────────────────────────────────┤
│ Task 3.1: pd-task-unified.sh 생성                             │
│   - interceptor + processor 통합                              │
│   - L1/L2/L3 포맷 주입 유지                                   │
│   blockedBy: [2.1, 2.2, 2.3]                                  │
│                                                               │
│ Task 3.2: 레거시 훅 정리                                      │
│   - pd-task-interceptor.sh → deprecated                       │
│   - pd-task-processor.sh → deprecated                         │
│   blockedBy: [3.1]                                            │
│                                                               │
│ Task 3.3: session-end.sh 업데이트                             │
│   - TaskList() 기반 미완료 태스크 저장                        │
│   - 파일 기반 로직 제거                                       │
│   blockedBy: [3.1]                                            │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│ PHASE 4: L1/L2/L3 Cache Integration (Day 4)                   │
├───────────────────────────────────────────────────────────────┤
│ Task 4.1: 캐시 전략 통합                                      │
│   - metadata.cacheKey 기반 중복 방지                          │
│   - 파일 캐시 → Task metadata 마이그레이션                    │
│   blockedBy: [3.2, 3.3]                                       │
│                                                               │
│ Task 4.2: 캐시 히트 최적화                                    │
│   - TaskList() 쿼리 최적화                                    │
│   - TTL 기반 만료 로직                                        │
│   blockedBy: [4.1]                                            │
└───────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│ PHASE 5: Testing & Validation (Day 5)                         │
├───────────────────────────────────────────────────────────────┤
│ Task 5.1: 멀티 터미널 통합 테스트                             │
│   - 3개 터미널 동시 실행 테스트                               │
│   - 의존성 해결 검증                                          │
│   blockedBy: [4.2]                                            │
│                                                               │
│ Task 5.2: 문서화                                              │
│   - CLAUDE.md 업데이트                                        │
│   - 마이그레이션 가이드 작성                                  │
│   blockedBy: [5.1]                                            │
└───────────────────────────────────────────────────────────────┘
```

### 5.2 Native Task로 표현

```python
# Phase 1
t1_1 = TaskCreate(subject="session-start.sh 업데이트",
                  description="CLAUDE_CODE_TASK_LIST_ID 설정, 기존 태스크 복원",
                  activeForm="session-start.sh 업데이트 중")

t1_2 = TaskCreate(subject="/workers 스킬 개선",
                  description="TaskList() 기반 대시보드, 파일 폴백 유지",
                  activeForm="/workers 스킬 개선 중")
TaskUpdate(taskId=t1_2.id, addBlockedBy=[t1_1.id])

t1_3 = TaskCreate(subject="/worker 스킬 개선",
                  description="TaskCreate/Update 통합, metadata 저장",
                  activeForm="/worker 스킬 개선 중")
TaskUpdate(taskId=t1_3.id, addBlockedBy=[t1_1.id])

# Phase 2
t2_1 = TaskCreate(subject="/orchestrate 스킬 개선",
                  description="태스크 의존성 그래프 자동 생성",
                  activeForm="/orchestrate 스킬 개선 중")
TaskUpdate(taskId=t2_1.id, addBlockedBy=[t1_2.id, t1_3.id])

t2_2 = TaskCreate(subject="/assign 스킬 개선",
                  description="TaskCreate + owner 필드 활용",
                  activeForm="/assign 스킬 개선 중")
TaskUpdate(taskId=t2_2.id, addBlockedBy=[t1_3.id])

t2_3 = TaskCreate(subject="/collect 스킬 개선",
                  description="TaskList 필터링, l1Summary 수집",
                  activeForm="/collect 스킬 개선 중")
TaskUpdate(taskId=t2_3.id, addBlockedBy=[t2_1.id])

# Phase 3
t3_1 = TaskCreate(subject="pd-task-unified.sh 생성",
                  description="interceptor + processor 통합",
                  activeForm="훅 통합 중")
TaskUpdate(taskId=t3_1.id, addBlockedBy=[t2_1.id, t2_2.id, t2_3.id])

t3_2 = TaskCreate(subject="레거시 훅 정리",
                  description="deprecated 마킹, 제거",
                  activeForm="레거시 정리 중")
TaskUpdate(taskId=t3_2.id, addBlockedBy=[t3_1.id])

t3_3 = TaskCreate(subject="session-end.sh 업데이트",
                  description="TaskList() 기반 저장",
                  activeForm="session-end.sh 업데이트 중")
TaskUpdate(taskId=t3_3.id, addBlockedBy=[t3_1.id])

# Phase 4
t4_1 = TaskCreate(subject="캐시 전략 통합",
                  description="metadata.cacheKey 마이그레이션",
                  activeForm="캐시 전략 통합 중")
TaskUpdate(taskId=t4_1.id, addBlockedBy=[t3_2.id, t3_3.id])

t4_2 = TaskCreate(subject="캐시 히트 최적화",
                  description="TTL 기반 만료",
                  activeForm="캐시 최적화 중")
TaskUpdate(taskId=t4_2.id, addBlockedBy=[t4_1.id])

# Phase 5
t5_1 = TaskCreate(subject="멀티 터미널 통합 테스트",
                  description="3개 터미널 동시 실행",
                  activeForm="통합 테스트 중")
TaskUpdate(taskId=t5_1.id, addBlockedBy=[t4_2.id])

t5_2 = TaskCreate(subject="문서화",
                  description="CLAUDE.md 업데이트, 마이그레이션 가이드",
                  activeForm="문서화 중")
TaskUpdate(taskId=t5_2.id, addBlockedBy=[t5_1.id])
```

---

## 6. 마이그레이션 체크리스트

### 6.1 환경 설정

- [ ] 모든 터미널에서 동일한 `CLAUDE_CODE_TASK_LIST_ID` 사용
- [ ] `session-start.sh`에서 태스크 리스트 ID 주입
- [ ] `/tasks` 명령으로 공유 상태 확인 가능

### 6.2 스킬 업데이트

- [ ] `/worker`: TaskCreate/Update 통합
- [ ] `/workers`: TaskList() 기반 대시보드
- [ ] `/orchestrate`: 의존성 그래프 자동 생성
- [ ] `/assign`: owner 필드 활용
- [ ] `/collect`: completed 태스크 수집

### 6.3 훅 간소화

- [ ] `pd-task-interceptor.sh` + `pd-task-processor.sh` → `pd-task-unified.sh`
- [ ] 파일 이동 로직 제거 (pending→completed)
- [ ] L1 캐시를 Task metadata로 마이그레이션

### 6.4 호환성

- [ ] `CLAUDE_CODE_ENABLE_TASKS=false` 폴백 테스트
- [ ] 파일 기반 시스템 폴백 유지 (선택적)
- [ ] 기존 L1/L2/L3 출력 형식 유지

---

## 7. 예상 효과

### 7.1 정량적 개선

| 지표 | 현재 | 개선 후 | 개선율 |
|------|------|---------|--------|
| 훅 수 | 5개 | 3개 | 40% 감소 |
| 파일 I/O | 높음 | 낮음 | ~60% 감소 |
| 의존성 추적 | 수동 | 자동 | 100% 자동화 |
| 경쟁 조건 위험 | 있음 | 없음 | 제거 |
| 크로스 세션 지속성 | 복잡 | 간단 | 단순화 |

### 7.2 정성적 개선

1. **개발자 경험**: `/tasks` 명령으로 실시간 상태 확인
2. **디버깅 용이**: 의존성 그래프 시각화
3. **유지보수성**: 훅 수 감소로 복잡도 하락
4. **신뢰성**: 원자적 상태 업데이트로 경쟁 조건 제거

---

## 8. 롤백 계획

Native Task System에 문제 발생 시:

```bash
# 환경 변수로 비활성화
export CLAUDE_CODE_ENABLE_TASKS=false

# session-start.sh에서 폴백 로직 활성화
if [ "$CLAUDE_CODE_ENABLE_TASKS" = "false" ]; then
    # 기존 파일 기반 시스템 사용
    use_file_based_coordination
fi
```

---

## 9. 즉시 실행 가능한 명령

### 9.1 현재 태스크 확인

```bash
# 터미널에서 직접 실행
/tasks
```

### 9.2 첫 번째 태스크 생성 (테스트)

Main Agent가 다음을 실행:

```python
TaskCreate(
    subject="Task System 통합 테스트",
    description="Native Task System이 3개 터미널에서 올바르게 공유되는지 테스트",
    activeForm="통합 테스트 중",
    metadata={
        "testId": "palantir-20260124-test-001",
        "terminals": ["A", "B", "C"]
    }
)
```

---

## 10. 결론

Claude Code v2.1.16+의 Native Task System은 현재 Palantir 프로젝트의 파일 기반 조율 시스템을 크게 개선할 수 있습니다. **하이브리드 접근법**으로 시작하여 점진적으로 마이그레이션하는 것을 권장합니다.

### 우선순위 권장사항

1. **즉시**: `CLAUDE_CODE_TASK_LIST_ID` 환경 변수 활용 (이미 설정됨)
2. **Day 1**: `/worker`, `/workers` 스킬에 TaskCreate/TaskList 통합
3. **Day 2-3**: `/orchestrate` 스킬의 의존성 그래프 자동화
4. **Day 4-5**: 훅 간소화 및 캐시 마이그레이션

---

> **Report Generated By:** Explore Agent + Main Agent Collaboration
> **Task List ID:** `palantir-20260124`
> **Next Action:** Main Agent가 Phase 1 태스크 생성 시작
