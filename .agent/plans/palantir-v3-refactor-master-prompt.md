# Palantir V3 Refactor: Agents/Skills/Hooks 통합 개선 연구 프롬프트

> **Version:** 1.0.0
> **Created:** 2026-01-23
> **Task List ID:** `palantir-v3-refactor`
> **Status:** Research Phase

---

## Executive Summary

세션 간 Task 공유(`CLAUDE_CODE_TASK_LIST_ID`)를 핵심 인프라로 활용하여 기존 Agents/Skills/Hooks 시스템을 대규모로 개선합니다. Pre-Compact 훅의 비효율성을 제거하고, Task 기반 영속성 + 의존성 그래프로 대체합니다.

---

## 1. 현재 상태 분석 (AS-IS)

### 1.1 구성 요소 현황

| 카테고리 | 개수 | 핵심 파일 |
|---------|-----|---------|
| Agents | 4 | onboarding-guide, clarify-agent, pd-readonly-analyzer, pd-skill-loader |
| Skills | 4 | commit-push-pr, plan-draft, clarify, build |
| Hooks | 11 | session-*, governance-check, auto-backup, pd-*, pre-compact, session-health |

### 1.2 발견된 문제점

#### P1: Pre-Compact 훅의 비효율성
```
현재 동작:
  PreCompact 이벤트 → 모든 상태를 파일로 덤프

문제:
  - 70% Context 도달 시 실행 → 이미 늦음
  - 덤프된 상태가 다음 세션에서 자동 복구 안 됨
  - Compact 후 컨텍스트에 다시 주입 필요 (수동)
```

#### P2: Hook 중복
```
중복 쌍:
  - pd-inject.sh ↔ pd-pretooluse.sh (동일 역할)
  - post-task-output.sh ↔ pd-posttooluse.sh (동일 역할)

영향:
  - 유지보수 혼란
  - 실행 순서 불명확
```

#### P3: 세션 간 상태 단절
```
현재:
  Session A: Tasks 생성 → 메모리에만 존재
  Session B: 이전 Tasks 모름 → 처음부터 재설명

원하는 상태:
  Session A: Tasks 생성 → ~/.claude/tasks/에 저장
  Session B: 자동 로드 → 이어서 작업
```

#### P4: Agent-Skill-Hook 연결 불명확
```
현재:
  clarify-agent ← 어떤 훅이 적용되는지 명시 없음
  /build skill ← 생성된 컴포넌트가 어떤 훅에 등록되는지 불명확

원하는 상태:
  각 Agent/Skill에 적용되는 Hook 목록이 명시적으로 선언
```

---

## 2. 개선 목표 (TO-BE)

### 2.1 핵심 원칙

```yaml
Principle 1: Task-Centric State
  - 모든 상태는 Task로 표현
  - Task는 파일 시스템에 영속
  - 세션 간 자동 공유

Principle 2: Hook Consolidation
  - 중복 훅 통합
  - 명확한 책임 분리
  - 단일 진실 공급원 (Single Source of Truth)

Principle 3: Explicit Integration
  - Agent ↔ Skill ↔ Hook 관계 명시
  - 의존성 그래프 시각화
  - 자동 등록 메커니즘
```

### 2.2 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    TASK LIST (영속 저장소)                   │
│                ~/.claude/tasks/{TASK_LIST_ID}/              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ Task 1  │──│ Task 2  │──│ Task 3  │──│ Task 4  │       │
│  │ ✅      │  │ 🔄      │  │ ⏳      │  │ ⏳      │       │
│  │ owner:A │  │ owner:B │  │ blocked │  │ blocked │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
└─────────────────────────────────────────────────────────────┘
        │               │
        ▼               ▼
┌───────────────┐ ┌───────────────┐
│ Session A     │ │ Session B     │
│ (Orchestrator)│ │ (Worker)      │
│               │ │               │
│ ┌───────────┐ │ │ ┌───────────┐ │
│ │ Agent 1   │ │ │ │ Agent 2   │ │
│ │ + Skills  │ │ │ │ + Skills  │ │
│ │ + Hooks   │ │ │ │ + Hooks   │ │
│ └───────────┘ │ │ └───────────┘ │
└───────────────┘ └───────────────┘
        │               │
        └───────┬───────┘
                ▼
        ┌─────────────┐
        │ Broadcast   │ ← Task 변경 시 모든 세션에 알림
        └─────────────┘
```

---

## 3. 개선 작업 정의

### Phase 1: Hook 통합 및 정리

#### Task 1.1: 중복 Hook 통합
```yaml
작업:
  - pd-inject.sh와 pd-pretooluse.sh 통합 → pd-task-interceptor.sh
  - post-task-output.sh와 pd-posttooluse.sh 통합 → pd-task-processor.sh

결과물:
  .claude/hooks/task-pipeline/
  ├── pd-task-interceptor.sh   # PreToolUse (Task)
  └── pd-task-processor.sh     # PostToolUse (Task)

검증:
  - 기존 기능 100% 유지
  - 중복 코드 0%
```

#### Task 1.2: Pre-Compact 훅 제거
```yaml
작업:
  - pre-compact.sh 기능을 Task 기반으로 대체
  - SessionStart 훅에서 이전 Task 상태 자동 로드
  - SessionEnd 훅에서 Task 상태 자동 저장

결과물:
  - pre-compact.sh 삭제
  - session-start.sh 개선 (Task 로드 로직 추가)
  - session-end.sh 개선 (Task 저장 로직 추가)

검증:
  - Compact 후에도 Task 상태 유지
  - 세션 재시작 후 Task 자동 복구
```

#### Task 1.3: Hook 파이프라인 최적화
```yaml
현재:
  PreToolUse (Task):
    1. governance-check.sh (불필요 - Task는 위험하지 않음)
    2. pd-inject.sh

개선:
  PreToolUse (Task):
    1. pd-task-interceptor.sh (통합된 훅만)

  PreToolUse (Bash|Edit|Write):
    1. governance-check.sh
    2. auto-backup.sh (Edit|Write만)
```

---

### Phase 2: Task 기반 상태 관리

#### Task 2.1: Task 상태 스키마 정의
```yaml
Task Schema V2:
  id: string (8-char)
  subject: string
  description: string
  status: pending | in_progress | completed | blocked

  # 새로운 필드
  owner: string (session_id | agent_name)
  blockedBy: Task[]
  blocks: Task[]
  metadata:
    createdAt: timestamp
    updatedAt: timestamp
    completedAt: timestamp
    source: skill | agent | user
    priority: CRITICAL | HIGH | MEDIUM | LOW

  # L1/L2 연동
  l1Summary: string (≤500 tokens)
  l2Path: string (.agent/outputs/...)
```

#### Task 2.2: Session-Task 자동 연동
```yaml
SessionStart Hook 개선:
  1. CLAUDE_CODE_TASK_LIST_ID 확인
  2. ~/.claude/tasks/{ID}/ 로드
  3. 미완료 Task 목록 컨텍스트에 주입
  4. "이전 세션에서 N개의 Task가 남아있습니다" 알림

SessionEnd Hook 개선:
  1. 현재 Task 상태 저장
  2. 미완료 Task에 owner 제거 (다른 세션이 가져갈 수 있도록)
  3. 감사 로그 기록
```

#### Task 2.3: Task Broadcast 활용
```yaml
구현:
  - Task 변경 시 파일 시스템에 즉시 저장
  - 다른 세션은 주기적으로 (또는 이벤트로) 변경 감지
  - 변경된 Task 목록 알림

활용 시나리오:
  Session A: TaskUpdate(task_1, status=completed)
  → ~/.claude/tasks/palantir-v3-refactor/task_1.json 업데이트
  → Session B: "Task 1이 완료되었습니다. Task 2 시작 가능"
```

---

### Phase 3: Agent-Skill-Hook 명시적 통합

#### Task 3.1: Agent 정의 스키마 확장
```yaml
# .claude/agents/clarify-agent.md 개선

---
name: clarify-agent
version: 2.0.0

# 명시적 Hook 선언 (NEW)
hooks:
  PreToolUse:
    - pd-task-interceptor.sh (Task 매칭)
  PostToolUse:
    - pd-task-processor.sh (Task 매칭)

# 명시적 Skill 선언 (NEW)
skills:
  provides: [clarify]
  uses: []

# 명시적 Task 통합 (NEW)
taskIntegration:
  autoCreateTask: true
  taskPrefix: "clarify-"
  defaultPriority: HIGH
---
```

#### Task 3.2: Skill 정의 스키마 확장
```yaml
# .claude/commands/build.md 개선

---
name: build
version: 2.0.0

# 명시적 Task 의존성 (NEW)
taskDependencies:
  creates:
    - type: agent | skill | hook | chain
      taskTemplate: "Build {type}: {name}"
  cascades:
    - agent → skill (optional)
    - skill → hook (optional)
    - agent → hook (optional)

# 생성 후 자동 등록 (NEW)
autoRegister:
  hooks: true  # settings.json에 자동 추가
  permissions: true  # 필요한 권한 자동 추가
---
```

#### Task 3.3: 통합 레지스트리 생성
```yaml
# .claude/registry.yaml (NEW)

version: 1.0.0
lastUpdated: 2026-01-23

agents:
  onboarding-guide:
    hooks: []
    skills: []
    taskIntegration: false

  clarify-agent:
    hooks: [pd-task-interceptor, pd-task-processor]
    skills: [clarify]
    taskIntegration: true

  pd-readonly-analyzer:
    hooks: [pd-task-interceptor, pd-task-processor]
    skills: []
    taskIntegration: true

  pd-skill-loader:
    hooks: [pd-task-interceptor, pd-task-processor]
    skills: [pd-analyzer, pd-injector]
    taskIntegration: true

skills:
  commit-push-pr:
    agents: []
    hooks: [governance-check, auto-backup]

  plan-draft:
    agents: []
    hooks: [session-health]

  clarify:
    agents: [clarify-agent]
    hooks: [pd-task-interceptor, pd-task-processor]

  build:
    agents: []
    hooks: []
    cascadeTargets: [agent, skill, hook, chain]

hooks:
  pd-task-interceptor:
    event: PreToolUse
    matcher: Task
    agents: [clarify-agent, pd-readonly-analyzer, pd-skill-loader]

  pd-task-processor:
    event: PostToolUse
    matcher: Task
    agents: [clarify-agent, pd-readonly-analyzer, pd-skill-loader]

  governance-check:
    event: PreToolUse
    matcher: Bash|Edit|Write
    global: true

  auto-backup:
    event: PreToolUse
    matcher: Edit|Write
    global: true

  session-health:
    event: PostToolUse
    matcher: "*"
    global: true
```

---

### Phase 4: Progressive-Disclosure 최적화

#### Task 4.1: L1/L2 캐싱 전략
```yaml
현재:
  매 Task 호출 → L1/L2 새로 생성

개선:
  Task 결과 캐싱:
    - ~/.claude/tasks/{ID}/cache/
    - Task ID + Input Hash로 캐시 키 생성
    - 동일 Task 재실행 시 캐시 반환 (선택적)

구현:
  pd-task-interceptor.sh:
    1. 캐시 확인 (Task ID + Input Hash)
    2. 캐시 hit → 즉시 반환
    3. 캐시 miss → 정상 실행 → 캐시 저장
```

#### Task 4.2: Token Budget 동적 조절
```yaml
현재:
  L1: 고정 500 tokens
  L2 읽기: Priority 기반 수동 결정

개선:
  Context 사용량 기반 동적 조절:
    - 사용량 < 50%: L1 + 모든 L2 읽기 허용
    - 사용량 50-70%: L1 + CRITICAL/HIGH L2만
    - 사용량 > 70%: L1만 (L2는 명시적 요청 시만)

구현:
  pd-task-processor.sh:
    1. 현재 Context 사용량 추정
    2. 사용량에 따른 권장사항 생성
    3. Main Agent에 가이던스 제공
```

---

## 4. 연구 질문 (Research Questions)

### RQ1: Task Broadcast 지연 시간
```
질문: 여러 세션에서 동시 작업 시 Task 상태 동기화 지연이 문제가 되는가?
측정: Session A의 TaskUpdate → Session B의 인지 시간
목표: < 1초
```

### RQ2: Hook 실행 오버헤드
```
질문: 통합된 Hook이 기존보다 빠른가?
측정: PreToolUse + PostToolUse 총 실행 시간
목표: 기존 대비 -30%
```

### RQ3: Task 기반 상태 복구 정확도
```
질문: Pre-Compact 대비 Task 기반 상태 관리가 더 정확한가?
측정: Compact 후 상태 복구율
목표: 100% (이전: ~70%)
```

### RQ4: Registry 자동 업데이트 가능성
```
질문: /build로 생성된 컴포넌트를 registry.yaml에 자동 등록할 수 있는가?
방안: PostToolUse Hook에서 Write 감지 → registry 업데이트
```

---

## 5. 실행 계획

### 5.1 Task 의존성 그래프

```
[Phase 1: Hook 통합]
Task 1.1 (중복 Hook 통합)
    │
    ├──▶ Task 1.2 (Pre-Compact 제거)
    │
    └──▶ Task 1.3 (파이프라인 최적화)

[Phase 2: Task 기반 상태]
Task 2.1 (스키마 정의)
    │
    ├──▶ Task 2.2 (Session-Task 연동)
    │        │
    │        └──▶ Task 2.3 (Broadcast 활용)
    │
    └──▶ (Phase 1 완료 후 시작)

[Phase 3: 명시적 통합]
Task 3.1 (Agent 스키마)
    │
    ├──▶ Task 3.2 (Skill 스키마)
    │
    └──▶ Task 3.3 (Registry 생성)
         │
         └──▶ (Phase 2 완료 후 시작)

[Phase 4: PD 최적화]
Task 4.1 (캐싱 전략) ──▶ Task 4.2 (동적 Token Budget)
    │
    └──▶ (Phase 3 완료 후 시작)
```

### 5.2 예상 소요 시간

| Phase | 예상 시간 | 세션 수 |
|-------|----------|--------|
| Phase 1 | 2-3시간 | 1-2 |
| Phase 2 | 3-4시간 | 2-3 |
| Phase 3 | 2-3시간 | 1-2 |
| Phase 4 | 2-3시간 | 1-2 |
| **Total** | **9-13시간** | **5-9** |

### 5.3 위험 요소

| 위험 | 영향 | 완화 방안 |
|-----|------|---------|
| Hook 통합 시 기능 손실 | HIGH | 통합 전 테스트 케이스 작성 |
| Task 파일 충돌 | MEDIUM | 파일 락 또는 optimistic locking |
| Registry 불일치 | LOW | /build 후 자동 검증 |

---

## 6. 실행 프롬프트

### 6.1 Phase 1 시작 프롬프트

```markdown
## Task: Hook 통합 및 정리 (Phase 1)

### Context
- Task List ID: palantir-v3-refactor
- 분석 완료: .agent/plans/palantir-v3-refactor-master-prompt.md
- 현재 Hook 목록: 11개 (중복 포함)

### 작업 내용

1. **Task 1.1: 중복 Hook 통합**
   - pd-inject.sh + pd-pretooluse.sh → pd-task-interceptor.sh
   - post-task-output.sh + pd-posttooluse.sh → pd-task-processor.sh
   - 기존 기능 100% 유지 검증

2. **Task 1.2: Pre-Compact 훅 제거**
   - pre-compact.sh 기능을 session-start.sh/session-end.sh로 이전
   - Task 기반 상태 저장/로드 구현

3. **Task 1.3: Hook 파이프라인 최적화**
   - settings.json hooks 섹션 정리
   - 불필요한 Hook 매칭 제거

### 제약 조건
- 기존 기능 100% 유지
- 하위 호환성 보장
- 테스트 후 이전 파일 삭제

### 출력 형식
각 Task 완료 시 TaskUpdate로 상태 변경
L1/L2 형식으로 결과 보고
```

### 6.2 전체 리팩토링 시작 프롬프트

```markdown
## Master Prompt: Palantir V3 Refactor

### Context
세션 간 Task 공유를 활용한 대규모 Agents/Skills/Hooks 통합 개선 프로젝트입니다.

### 시작 조건
```bash
CLAUDE_CODE_TASK_LIST_ID=palantir-v3-refactor claude
```

### 핵심 원칙
1. **Task-Centric State**: 모든 상태는 Task로 표현, 파일 시스템에 영속
2. **Hook Consolidation**: 중복 제거, 단일 진실 공급원
3. **Explicit Integration**: Agent ↔ Skill ↔ Hook 관계 명시

### 실행 순서
1. Task List 로드 확인
2. Phase 1 (Hook 통합) 시작
3. 각 Task 완료 시 TaskUpdate
4. Phase 완료 시 다음 Phase로 진행

### 참조 문서
- 마스터 플랜: .agent/plans/palantir-v3-refactor-master-prompt.md
- 분석 결과: .agent/outputs/Explore/a1b2c3d4.md (또는 최신 분석)

### 예상 결과
- Hook 수: 11개 → 7개
- 중복 코드: 30% → 0%
- 상태 복구율: 70% → 100%
- Context 효율성: +20%
```

---

## 7. 검증 체크리스트

### Phase 1 완료 조건
- [ ] pd-task-interceptor.sh 생성 및 테스트
- [ ] pd-task-processor.sh 생성 및 테스트
- [ ] pre-compact.sh 기능 이전 완료
- [ ] settings.json hooks 섹션 업데이트
- [ ] 기존 Hook 파일 백업 후 삭제

### Phase 2 완료 조건
- [ ] Task Schema V2 정의
- [ ] session-start.sh Task 로드 구현
- [ ] session-end.sh Task 저장 구현
- [ ] Broadcast 테스트 (2개 세션)

### Phase 3 완료 조건
- [ ] Agent 정의 스키마 확장
- [ ] Skill 정의 스키마 확장
- [ ] registry.yaml 생성
- [ ] /build 후 자동 등록 테스트

### Phase 4 완료 조건
- [ ] L1/L2 캐싱 구현
- [ ] 동적 Token Budget 구현
- [ ] 성능 벤치마크 완료

---

## Appendix: 관련 파일 목록

### 수정 대상
```
.claude/hooks/
├── session-start.sh (개선)
├── session-end.sh (개선)
├── governance-check.sh (유지)
├── auto-backup.sh (유지)
├── session-health.sh (유지)
├── welcome.sh (유지)
├── pre-compact.sh (삭제 예정)
└── progressive-disclosure/
    ├── pd-inject.sh (통합 후 삭제)
    ├── post-task-output.sh (통합 후 삭제)
    ├── pd-pretooluse.sh (통합 후 삭제)
    └── pd-posttooluse.sh (통합 후 삭제)

.claude/hooks/task-pipeline/ (NEW)
├── pd-task-interceptor.sh
└── pd-task-processor.sh
```

### 신규 생성
```
.claude/registry.yaml
.claude/schemas/task-v2.schema.json
```

### 설정 파일
```
settings.json (hooks 섹션 업데이트)
.claude.json (변경 없음)
CLAUDE.md (Progressive-Disclosure 섹션 업데이트)
```
