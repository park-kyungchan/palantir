# Orchestration Infrastructure 개선 종합 계획

> **Version:** 1.0 | **Date:** 2026-01-24
> **Principle:** "단순하지만 완벽하게"

---

## 1. Executive Summary

V2.1.0~V2.1.19 CHANGELOG 분석 및 현재 스킬/훅 현황 종합 결과,
다음 4개 Phase로 Orchestration 인프라를 개선합니다.

---

## 2. Phase 1: 즉시 적용 (Critical)

### 2.1 인자 문법 업그레이드 (V2.1.19)

**대상 스킬:** 인자를 받는 모든 스킬

```yaml
# 변경 전
prompt: "Execute $ARGUMENTS.0 on $ARGUMENTS.1"

# 변경 후
prompt: "Execute $0 on $1"
```

### 2.2 Frontmatter 표준화

| 필드 | 표준 형식 |
|------|-----------|
| name | lowercase-hyphen |
| user-invocable | 하이픈 (언더스코어 아님) |
| allowed-tools | YAML 리스트 |
| version | "1.x.x" |

### 2.3 자동 승인 최적화

추가 권한/훅 없는 스킬은 V2.1.19에서 자동 승인됨.
불필요한 `disable-model-invocation: true` 검토.

---

## 3. Phase 2: 스킬 통합 (High)

### 3.1 /orchestrate + /assign 통합

**현재 문제:**
- 역할 중복
- Description 불명확으로 자동 매칭 실패

**해결안 A: /assign을 /orchestrate에 통합**
```yaml
name: orchestrate
description: |
  Multi-terminal task orchestration with automatic work distribution.
  Creates task files, assigns to workers (B/C/D), tracks progress.
  Supports parallel execution with dependency management.
  Use for complex multi-step workflows requiring coordination.
```

**해결안 B: /assign을 내부 헬퍼로 전환**
```yaml
name: assign
user-invocable: false
disable-model-invocation: true
```

### 3.2 Worker 스킬 통합

**현재:** /worker-start, /worker-task, /worker-done (3개)

**통합안:** /worker (1개)

```yaml
name: worker
description: |
  Multi-terminal worker management with lifecycle control.
  Subcommands: start <terminal>, task <terminal>, done <terminal>
  Terminal: B, C, or D

# 사용 예시:
# /worker start b
# /worker done c
```

### 3.3 PD-* 스킬 삭제 검토

| 스킬 | 상태 | 조치 |
|------|------|------|
| pd-injector | Hook으로 대체됨 | 삭제 후보 |
| pd-analyzer | Hook으로 대체됨 | 삭제 후보 |
| pd-forked-task | context: fork로 대체 | 삭제 후보 |

---

## 4. Phase 3: V2.1.16 Task System 적용

### 4.1 현재 방식 vs 신규 방식

**현재:**
```yaml
# _progress.yaml 수동 관리
terminals:
  terminal-b:
    status: "assigned"
    taskId: "orch-gap-b1"
```

**V2.1.16 방식:**
```python
# Native Task System
TaskCreate(
  subject="Orchestration Gap Analysis",
  description="Analyze /orchestrate and /assign skills",
  activeForm="Analyzing orchestration gaps"
)

TaskUpdate(
  taskId="1",
  status="in_progress",
  addBlockedBy=["0"]  # 의존성
)
```

### 4.2 Migration 계획

1. _progress.yaml → TaskCreate로 마이그레이션
2. blockedBy/blocks로 의존성 표현
3. /todos 또는 TaskList로 상태 확인

---

## 5. Phase 4: 워크플로우 완전성

### 5.1 누락 단계 보완

| 누락 단계 | 해결 방안 |
|-----------|-----------|
| **Synthesis** | /collect 확장 또는 신규 /synthesize |
| **Approval Gate** | ExitPlanMode 활용 |
| **Loop Control** | SessionEnd Hook 또는 신규 스킬 |

### 5.2 Synthesis 스킬 신규 제안

```yaml
name: synthesize
description: |
  Synthesize collected results from multiple workers into unified analysis.
  Aggregates findings, identifies patterns, generates actionable summary.
  Use after /collect to prepare for planning phase.
user-invocable: true
context: fork
model: opus
```

---

## 6. Description 상세화 가이드

### 6.1 좋은 Description 예시

```yaml
# BAD: 너무 짧음
description: "Run orchestration"

# GOOD: 상세하고 구체적
description: |
  Multi-terminal task orchestration for parallel workflows.
  Creates task files in .agent/prompts/pending/ for workers.
  Assigns work to Terminal B, C, or D based on task type.
  Tracks progress via _progress.yaml with real-time updates.
  Supports investigation, implementation, and verification phases.
  Use when coordinating complex multi-step tasks across terminals.
```

### 6.2 키워드 포함 권장

- **What:** 무엇을 하는가
- **When:** 언제 사용하는가
- **How:** 어떻게 동작하는가
- **Output:** 결과물은 무엇인가

---

## 7. 검증 체크리스트

### Phase 1 완료 확인
- [ ] 모든 스킬 $0/$1 문법 적용
- [ ] Frontmatter 하이픈 표준화
- [ ] YAML allowed-tools 형식

### Phase 2 완료 확인
- [ ] /orchestrate + /assign 통합/역할 명확화
- [ ] /worker-* 통합
- [ ] pd-* 스킬 삭제

### Phase 3 완료 확인
- [ ] _progress.yaml → TaskCreate 마이그레이션
- [ ] blockedBy/blocks 의존성 테스트

### Phase 4 완료 확인
- [ ] Synthesis 단계 구현
- [ ] 전체 루프 E2E 테스트

---

## 8. 참조 문서

- CHANGELOG.md: V2.1.0~V2.1.19 전체 릴리스
- .agent/outputs/claude-code-guide/task-params-v2119.md: Task 파라미터 상세
- .claude/hooks/task-pipeline/: L1/L2/L3 Hook 구현

---

> **Next Action:** 사용자 승인 후 Phase 1부터 순차 실행
