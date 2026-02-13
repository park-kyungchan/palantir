---
version: GC-v2
created: 2026-02-07
feature: ch006-dia-v4
complexity: MEDIUM
---

# Global Context — CH-006: DIA v3.0 → v4.0 Upgrade

## Scope

**Goal:** DIA v3.0 → v4.0 업그레이드: Team Memory(실시간 공유), Context Delta, Hook GC Verification

**In Scope:**
- TEAM-MEMORY.md 메커니즘 설계 및 CLAUDE.md/agent .md 반영 (실시간 읽기/쓰기, Lead 큐레이션)
- Context Delta 프로토콜 ([CONTEXT-UPDATE]에 delta 포맷 추가)
- SubagentStart hook 강화 (GC-v{N} consistency check)
- task-api-guideline.md v3.0 → v4.0 업데이트
- CLAUDE.md v3.1 → v4.0 업데이트
- 6개 agent .md 파일 업데이트 (Team Memory 참조 추가)

**Out of Scope:**
- plan-validation 스킬 (Phase 5) — DIA v4.0 완료 후 별도 진행
- 코드베이스 변경 (인프라 파일만 대상)
- 스킬 SKILL.md 수정 (기존 3개 스킬은 변경하지 않음)

**Approach:** CH-006 직접 구현 (Lead 단독, brainstorming 후 직접 구현)

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: COMPLETE (Gate 2 APPROVED)
- Phase 3: IN_PROGRESS

## Constraints
- 기존 DIA v3.0 프로토콜과 하위 호환 유지
- Teammate의 disallowedTools 변경하지 않음
- 스킬 파일 (SKILL.md) 이번에 수정하지 않음
- Team Memory의 실시간 공유는 파일 기반 (MCP 등 추가 인프라 불필요)

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | 전체 3개 개선 포인트 포함 | 사용자 요청: DIA 기초 강화 우선 | P1 |
| D-2 | Team Memory: 실시간 팀 상태 공유 | 사용자: "실시간 공유가 중요" | P1 |
| D-3 | CH-006 직접 구현 | 인프라 수정에 파이프라인 오버헤드 불필요 | P1 |
| D-4 | Team Memory: Edit + section-per-role | Write 전체 덮어쓰기 위험, Edit의 old_string 교체는 원자적 | P2 |
| D-5 | Context Delta: inline ADDED/CHANGED/REMOVED | 별도 파일 불필요, 70-90% 토큰 절감 | P2 |
| D-6 | SubagentStart: additionalContext GC 주입 | 차단 불가 (exit 2 non-blocking), 알림만 가능 | P2 |
| D-7 | TeammateIdle + TaskCompleted hooks 추가 | exit 2 차단 가능, DIA 품질 게이트 활용 | P2 |

## Phase 2 Research Findings Summary
### D1: Team Memory (TEAM-MEMORY.md)
- 위치: `.agent/teams/{session-id}/TEAM-MEMORY.md`
- Section-per-role: `## Lead`, `## researcher-1` 등. 각자 자기 섹션만 Edit.
- Write tool 사용 금지 (최초 생성 시만 허용) — 전체 덮어쓰기로 다른 섹션 소실 위험
- Lead 큐레이션: Gate 시점에 stale 정보 정리

### D2: Context Delta Protocol
- 기존 GC 파일 크기: 50~190줄 (중앙값 ~130줄, ~2,600 tokens)
- Delta 포맷: `ADDED: {section.field}: {value}` / `CHANGED: {old} → {new}` / `REMOVED: {field}`
- Full fallback: version gap >1, compact recovery, 최초 spawn, >50% 변경 시
- Token 절감: 70-90% per update

### D3: Hook Enhancement
- SubagentStart: spawn 차단 불가 (exit 2 = non-blocking). additionalContext로 GC version 주입만 가능.
- TeammateIdle (신규): exit 2로 idle 차단 가능. L1/L2 미작성 시 차단.
- TaskCompleted (신규): exit 2로 완료 차단 가능. 산출물 미충족 시 차단.
- 현재 on-subagent-start.sh: 비공식 스키마 필드 사용 (`.agent_name`, `.tool_input.*`)

## Architecture Needs (Phase 3)
1. TEAM-MEMORY.md 파일 구조 및 접근 규칙 상세 설계
2. Context Delta 프로토콜 포맷 및 CLAUDE.md 반영 설계
3. Hook 스크립트 로직 (TeammateIdle, TaskCompleted, SubagentStart 강화)
4. CLAUDE.md / agent .md / task-api-guideline.md 변경 범위 매핑
5. v3.1 → v4.0 마이그레이션 전략
