# Skill Access Control Matrix

> **Version:** 1.0.0 | **Date:** 2026-01-24
> **Purpose:** 18개 스킬의 접근 제어 패턴 정의

---

## 1. 접근 제어 패턴 정의

### 4가지 패턴

| Pattern | user-invocable | disable-model-invocation | 사용 사례 |
|---------|---------------|-------------------------|----------|
| **P1: User-Only** | `true` | `true` | 민감한 작업, 워크플로우 트리거 |
| **P2: Model-Only** | `false` | `false` | 내부 헬퍼, 자동화 분석 |
| **P3: Hybrid (기본)** | `true` | `false` | 일반 개발 도구 |
| **P4: Disabled** | `false` | `true` | 실험적, 레거시 |

---

## 2. 스킬별 분류

### Pattern 1: User-Only (7개)

민감한 작업으로 사용자 명시적 호출만 허용:

| 스킬 | 이유 | Subagent |
|------|------|----------|
| `commit-push-pr` | Git 작업, 원격 푸시 | - |
| `orchestrate` | 멀티터미널 조율 | `context: fork` |
| `worker-start` | 터미널별 수동 실행 | - |
| `worker-task` | 작업 파일 기반 | - |
| `worker-done` | 완료 보고 | - |
| `assign` | 오케스트레이터 내부 명령 | - |
| `collect` | 결과 수집 | `context: fork` |

### Pattern 2: Model-Only (2개)

내부 유틸리티로 모델만 자동 호출:

| 스킬 | 이유 | Subagent |
|------|------|----------|
| `build-research` | /build의 Phase 0 헬퍼 | `context: fork` |
| `pd-analyzer` | L1/L2/L3 분석기 | `agent: Explore` |

### Pattern 3: Hybrid - 완전 개방 (8개)

일반 개발 도구로 사용자/모델 모두 호출 가능:

| 스킬 | 용도 | Subagent |
|------|------|----------|
| `build` | 컴포넌트 빌더 | - |
| `clarify` | 요청 명확화 | `context: fork` |
| `explore-l1l2l3` | 코드베이스 탐색 | `agent: Explore` |
| `plan-l1l2l3` | 구현 계획 | `agent: Plan` |
| `plan-draft` | 드래프트 생성 | - |
| `workers` | 워커 상태 확인 | - |
| `pd-injector` | 동적 컨텍스트 주입 | - |
| `docx-automation` | DOCX 문서 생성 | `agent: general-purpose` |

### Pattern 4: Disabled (1개)

실험적 또는 레거시:

| 스킬 | 이유 | Subagent |
|------|------|----------|
| `pd-forked-task` | 데모 스킬 | `context: fork` |

---

## 3. Subagent 활용 현황

### agent: explore (독립 탐색)

```yaml
# 빈 컨텍스트에서 시작, 결과만 반환
agent: Explore
```

- `pd-analyzer`
- `explore-l1l2l3`

### agent: Plan (계획 수립)

```yaml
# 빈 컨텍스트에서 계획 생성
agent: Plan
```

- `plan-l1l2l3`

### context: fork (병렬 작업)

```yaml
# 현재 컨텍스트 복사본에서 작업
context: fork
```

- `clarify`
- `build-research`
- `orchestrate`
- `collect`
- `pd-forked-task`

---

## 4. 3-Tier Context Architecture

```
[Main Context]
└─ 핵심 개발 작업
    ├─ /build, /commit-push-pr
    └─ 사용자 직접 상호작용

[Agent Context - Explore/Plan]
└─ 탐색 및 연구 작업
    ├─ /explore-l1l2l3
    └─ /plan-l1l2l3

[Forked Context]
└─ 파생 작업
    ├─ /clarify (PE 적용)
    ├─ /orchestrate (멀티터미널)
    └─ /build-research (내부 리서치)
```

---

## 5. 적용 완료 현황

### ✅ 완료된 변경

| 스킬 | 이전 | 현재 | 상태 |
|------|------|------|------|
| `commit-push-pr` | P3 | P1 | ✅ 완료 |
| `orchestrate` | P3 | P1 | ✅ 완료 |
| `pd-analyzer` | P3 | P2 | ✅ 완료 |
| `pd-forked-task` | P3 | P4 | ✅ 완료 |
| `build-research` | - | P2 | ✅ 확인됨 |
| `worker-*`, `assign`, `collect` | - | P1 | ✅ 확인됨 |
| 나머지 8개 | - | P3 | ✅ 확인됨 |

---

## 6. 에이전트 현황

### 활성 에이전트 (3개)

| 에이전트 | 패턴 | 용도 |
|----------|------|------|
| `onboarding-guide` | Reference | 신규 사용자 가이드 |
| `pd-readonly-analyzer` | A1: Tool Restrictions | 읽기 전용 분석 데모 |
| `pd-skill-loader` | A2: Skill Injection | 스킬 사전 로드 데모 |

### 비활성화/삭제된 에이전트

| 에이전트 | 상태 | 이유 |
|----------|------|------|
| `clarify-agent` | ❌ 삭제됨 | `/clarify` 스킬과 중복 |

---

## 7. /build 스킬 Q&A 라운드

### 강화된 Socratic Q&A (2026-01-24)

| Builder | Rounds | 주요 내용 |
|---------|--------|-----------|
| **Agent Builder** | 15 | Core Identity, Tool Config, Context, Model, Integration |
| **Skill Builder** | 12 | Identity, Access Control, Execution, Tools, Features |
| **Hook Builder** | 14 | Identity, Event, Trigger, I/O, Advanced |

각 라운드에 추가된 정보:
- 필드별 상세 설명
- 옵션 컨텍스트
- 레퍼런스 테이블
- 접근 제어 매트릭스 (P1/P2/P3/P4)

---

*Last Updated: 2026-01-24 09:15 KST*
*Version: 1.1.0*
