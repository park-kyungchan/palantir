# L2 Summary — execution-pipeline Phase 2 Research

> **Researcher:** researcher-1 | **Date:** 2026-02-07 | **GC:** v1

---

## Executive Summary

3개 도메인 조사 결과, execution-pipeline 스킬은 superpowers의 두 INCOMPATIBLE 스킬에서 **11개 패턴을 보존**하고 **11개 요소를 대체**하는 구조로 설계해야 한다. 핵심 설계 결정은 two-stage review의 통합 위치(implementer 위임 권장)와 adaptive implementer spawn 알고리즘이다.

---

## Domain 1: 원본 스킬 분석 — 핵심 발견

**executing-plans**는 단일 agent 배치 실행 + 인간 체크포인트 모델이다. 3개 task씩 실행 후 인간 리뷰. 단순하지만 병렬성과 DIA가 없다.

**subagent-driven-development**는 task당 ephemeral subagent + two-stage review 모델이다. 핵심 혁신은 (1) 신선한 context per task, (2) spec → quality 순서의 리뷰, (3) fix loop. 그러나 sequential-only이고 DIA 없이 persistent teammate와 호환 불가.

**보존 대상 (11개):** Two-stage review, context curation, "Do Not Trust", ordered review, fix loop, self-review, pre-work Q&A, stop on blocker, critical plan review, fresh context, final whole-project review.

**대체 대상 (11개):** TodoWrite→TaskCreate, human checkpoint→Gate 6, ephemeral→persistent, sequential→adaptive parallel, same-session controller→delegate Lead, finishing chain→clean termination, worktree→shared workspace, no DIA→TIER 1+LDAP, no GC→CIP injection, flat tasks→dependency-aware, no ownership→non-overlapping.

---

## Domain 2: Implementer Agent — 핵심 발견

**도구 세트:** 11개 사용 가능 (Read/Glob/Grep/Edit/Write/Bash + TaskList/TaskGet + sequential-thinking + context7). TaskCreate/TaskUpdate 차단.

**DIA TIER 1:** 6 IAS sections, 10 RC items, LDAP HIGH 2Q. Gate A (Impact) → Gate B (Plan) 순서. 최대 3회 시도.

**Sub-Orchestrator:** implementer가 Task tool로 subagent 생성 가능 (depth=1). 이것이 spec-reviewer와 code-reviewer subagent 디스패치의 메커니즘.

**Adaptive Spawn 알고리즘:** plan §3 (File Ownership) + §4 (TaskCreate) 기반. 파일 중복 없는 독립 task 클러스터 수 = implementer 수 (max 4). DIA 오버헤드 (implementer당 5-22K tokens) 감안 시, ≤5 tasks는 1-2명, 6+ independent tasks는 3-4명 권장.

**File Ownership:** 비중복 할당, concurrent edit 금지, cross-boundary는 integrator만 가능. 위반 시 [STATUS] BLOCKED.

---

## Domain 3: code-reviewer 통합 — 핵심 발견

**통합 방안:** Option B (Implementer 위임) 권장.
- Implementer가 자신의 Sub-Orchestrator 역할로 spec-reviewer와 code-reviewer subagent를 디스패치
- Fix loop이 implementer 내에서 완결 (Lead round-trip 불필요)
- Lead는 Gate 6에서 결과를 cross-verify (per-task + cross-task)

**Reviewer는 ephemeral subagent로 유지 (DIA 비대상).** 근거: read-only 작업 (mutation 없음), task-per-invocation 생명주기, 3중 품질 보장 (Prompt Template + Lead Override + Re-review Loop).

**spec-reviewer 적응:** plan §5 Change Specification을 input으로 사용. 파일 범위를 implementer ownership으로 제한. 핵심 패턴 (distrust, 3-axis verification) 보존.

**code-reviewer 적응:** 기존 code-reviewer.md template 그대로 사용 가능. 유일한 추가: global-context 참조.

**Gate 6 구조:** Per-task (spec + quality + self-test + ownership) → Cross-task (interface consistency + integration + optional final review) → APPROVE/ITERATE/ABORT.

---

## Key Recommendations for Phase 3 Architect

1. **Two-stage review를 implementer의 Sub-Orchestrator 패턴으로 통합** — Lead는 Gate 6에서 결과를 cross-verify
2. **Adaptive spawn 알고리즘을 plan §3/§4 기반으로 설계** — independent cluster 수 = implementer 수
3. **Gate 6을 per-task + cross-task 2단계로 설계** — per-task는 implementer 보고 기반, cross-task는 Lead 직접 평가
4. **Reviewer subagent는 ephemeral 유지** — DIA 비대상, Prompt Template으로 품질 보장
5. **Final whole-project review 패턴 보존** — 모든 implementer 완료 후 전체 구현 리뷰 (optional)
6. **Fix loop 반복 제한 설정** — review stage당 max 3회 (무한 루프 방지)
7. **GC-v4 → GC-v5 delta는 Phase 6 결과 반영** — task 완료 현황, 인터페이스 변경, Gate 6 결과
8. **Clean Termination** — Phase 7로 auto-chain하지 않음, GC-v5 + artifacts 보존

---

## Unresolved Questions for Phase 3

| # | Question | Impact |
|---|----------|--------|
| UQ-1 | Review loop max 반복 수: 3이 적절한가, plan complexity에 따라 가변해야 하는가? | Fix loop 무한 방지 vs 유연성 |
| UQ-2 | Final whole-project review를 필수로 할 것인가, optional로 할 것인가? | Token overhead vs 품질 보장 |
| UQ-3 | Implementer가 review 결과를 조작할 수 있는 위험에 대한 추가 safeguard 필요한가? | Lead의 spot-check 빈도 결정 |
| UQ-4 | 1개 implementer가 여러 task를 순차 처리할 때 context pressure 관리 전략은? | L1/L2/L3 중간 저장 시점 결정 |
