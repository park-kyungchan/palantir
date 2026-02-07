# INFRA-UPDATE V2.1.31 Design Document

> **Date:** 2026-02-05
> **Status:** Approved
> **Workload:** infra-update-20260205

---

## 1. Executive Summary

Claude Code V2.1.31 인프라 전면 업그레이드를 위한 설계 문서입니다.

**목표:**
- Subagent 추적 문제 해결 (SubagentStop hook 미등록)
- Hook 실행 진단 및 안정화
- V2.1.31 신규 기능 적용
- CLAUDE.md V7.7 업데이트

**접근 방식:** Priority-based (Critical → High → Medium → Cleanup → Verify)

---

## 2. Gap Analysis Summary

### 2.1 Critical Gaps

| Gap ID | Component | Issue |
|--------|-----------|-------|
| GAP-001 | SubagentStop | Hook not registered in settings.json |
| GAP-002 | hookify | Plugin installed but not enabled |
| GAP-003 | Hook Diagnostics | No diagnostic tools |
| GAP-004 | Stop hook | Empty array `[]` |

### 2.2 High Priority Gaps

| Gap ID | Component | Issue |
|--------|-----------|-------|
| GAP-005 | PreCompact | Not configured |
| GAP-006 | PostToolUseFailure | Not configured |
| GAP-007 | Skill context:fork | Not applied |
| GAP-008 | Agent hooks | Not in frontmatter |

### 2.3 Medium Priority Gaps

| Gap ID | Component | Issue |
|--------|-----------|-------|
| GAP-009 | sandbox | Not configured |
| GAP-010 | plansDirectory | Not set |
| GAP-011 | alwaysThinkingEnabled | Not set |
| GAP-012 | PermissionRequest | Not configured |

---

## 3. ORCHESTRATION PLAN

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  INFRA-UPDATE V2.1.31 - MASTER ORCHESTRATION PLAN                            │
│  Role: Main Agent (= Sub-Orchestrator)                                       │
│  Pattern: Verify → Orchestrate → Verify → Loop                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [PERMANENT] #1 ─────────────────────────────────── [in_progress]           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─── PHASE 1: Critical (병렬 실행 가능) ───────────────────────────────┐   │
│  │  #2 SubagentStop  #3 Hook Diag  #4 Stop/Pre  #5 hookify              │   │
│  │  [pending]        [pending]     [pending]    [pending]               │   │
│  └──────────────────────────┬───────────────────────────────────────────┘   │
│                             │                                                │
│                             ▼ (ALL completed)                                │
│  ┌─── PHASE 2: High ────────────────────────────────────────────────────┐   │
│  │  #6 PreCompact  #7 PostFailure  #8 context:fork  #9 Agent hooks      │   │
│  │  blockedBy:[2,3,4,5]                                                 │   │
│  └──────────────────────────┬───────────────────────────────────────────┘   │
│                             │                                                │
│                             ▼ (ALL completed)                                │
│  ┌─── PHASE 3: Medium ──────────────────────────────────────────────────┐   │
│  │  #10 sandbox  #11 plans  #12 thinking  #13 Permission                │   │
│  │  blockedBy:[6,7,8,9]                                                 │   │
│  └──────────────────────────┬───────────────────────────────────────────┘   │
│                             │                                                │
│                             ▼ (ALL completed)                                │
│  ┌─── PHASE 4: Cleanup ─────────────────────────────────────────────────┐   │
│  │  #14 미사용정리  #15 CLAUDE.md V7.7  #16 스키마검증                  │   │
│  │  blockedBy:[10,11,12,13]                                             │   │
│  └──────────────────────────┬───────────────────────────────────────────┘   │
│                             │                                                │
│                             ▼ (ALL completed)                                │
│  ┌─── PHASE 5: Verification ────────────────────────────────────────────┐   │
│  │  #17 Hook 테스트  #18 Subagent 검증  #19 통합 테스트                 │   │
│  │  blockedBy:[14,15,16] → #19 blockedBy:[17,18]                        │   │
│  └──────────────────────────┬───────────────────────────────────────────┘   │
│                             │                                                │
│                             ▼ (Phase 5 ALL completed)                        │
│  [PERMANENT] #1 ──────────────────────────────────► [completed]             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Task Definitions

### Phase 1: Critical (Parallel)

| Task | Subject | Key Actions | blockedBy |
|------|---------|-------------|-----------|
| #2 | SubagentStop hook 연결 | settings.json에 SubagentStop 섹션 추가 | [] |
| #3 | Hook 진단 스크립트 | diagnostics/ 디렉토리 및 3개 스크립트 | [] |
| #4 | Stop/PreCompact hook | Stop 섹션 구성, pre-compact-save.sh | [] |
| #5 | hookify 활성화 | enabledPlugins에 hookify 추가 | [] |

### Phase 2: High

| Task | Subject | Key Actions | blockedBy |
|------|---------|-------------|-----------|
| #6 | PreCompact 구현 | Auto-Compact 전 컨텍스트 저장 | [2,3,4,5] |
| #7 | PostToolUseFailure | Tool 실패 시 에러 핸들링 | [2,3,4,5] |
| #8 | context:fork | clarify, planning, synthesis에 적용 | [2,3,4,5] |
| #9 | Agent hooks | 각 agent frontmatter에 hooks 추가 | [2,3,4,5] |

### Phase 3: Medium

| Task | Subject | Key Actions | blockedBy |
|------|---------|-------------|-----------|
| #10 | sandbox 설정 | sandbox.enabled, allowedDomains | [6,7,8,9] |
| #11 | plansDirectory | `.agent/plans` 경로 설정 | [6,7,8,9] |
| #12 | alwaysThinkingEnabled | Opus 4.5 thinking 활성화 | [6,7,8,9] |
| #13 | PermissionRequest | 선택적 auto-approve 로직 | [6,7,8,9] |

### Phase 4: Cleanup

| Task | Subject | Key Actions | blockedBy |
|------|---------|-------------|-----------|
| #14 | 미사용 파일 정리 | orphaned hooks, deprecated 파일 | [10,11,12,13] |
| #15 | CLAUDE.md V7.7 | 새 기능 반영, hook 목록 업데이트 | [10,11,12,13] |
| #16 | settings.json 검증 | JSON schema validation | [10,11,12,13] |

### Phase 5: Verification

| Task | Subject | Key Actions | blockedBy |
|------|---------|-------------|-----------|
| #17 | Hook 실행 테스트 | 모든 hook 트리거 확인 | [14,15,16] |
| #18 | Subagent Lifecycle | SubagentStart/Stop 로그 확인 | [14,15,16] |
| #19 | 통합 테스트 | E2E 테스트, 최종 보고서 | [17,18] |

---

## 5. Dependency Chain (DAG)

```
[PERMANENT #1] ─────────────────────────────────────────────────────┐
        │                                                           │
        ▼                                                           │
   #2, #3, #4, #5 (병렬) ─────────────────────────────┐           │
        │                                              │           │
        ▼                                              │           │
   #6, #7, #8, #9 ─┬─ blockedBy: [2,3,4,5]           │           │
                   │                                   │           │
        ▼                                              │           │
   #10, #11, #12, #13 ─┬─ blockedBy: [6,7,8,9]       │ in_progress
                       │                               │           │
        ▼                                              │           │
   #14, #15, #16 ─┬─ blockedBy: [10,11,12,13]        │           │
                  │                                    │           │
        ▼                                              │           │
   #17, #18 ─┬─ blockedBy: [14,15,16]                │           │
             │                                         │           │
        ▼                                              │           │
   #19 ─── blockedBy: [17,18]                         │           │
        │                                              │           │
        ▼                                              │           │
   [PERMANENT #1] → completed ◄────────────────────────┘───────────┘
```

---

## 6. Implementation Notes

### 6.1 Enforcement Hooks 제거됨

전면 재설계를 위해 다음 hooks가 settings.json에서 제거됨:
- context-recovery-gate.sh
- l2l3-access-gate.sh
- workload-path-gate.sh
- orchestrating-l2l3-synthesis-gate.sh
- 기타 enforcement hooks

남은 hooks:
- auto-backup.sh (Edit|Write)
- sensitive-files-gate.sh (Read, Edit|Write)
- clarify-qa-logger.sh (AskUserQuestion)
- read-tracker.sh (Read)

### 6.2 SubagentStop Hook Template

```bash
#!/usr/bin/env bash
# subagent-stop.sh - Log subagent completion

LOG_FILE="${HOME}/.agent/logs/subagent_lifecycle.log"
TIMESTAMP=$(date +"%Y-%m-%dT%H:%M:%S")

echo "[${TIMESTAMP}] SubagentStop: ${CLAUDE_SUBAGENT_TYPE:-unknown}" >> "$LOG_FILE"

echo '{"status": "logged"}'
```

---

## 7. Success Criteria

- [ ] Phase 1-5 모든 Task completed
- [ ] SubagentStart/Stop 쌍 검증 통과
- [ ] Hook 진단 스크립트 작동 확인
- [ ] CLAUDE.md V7.7 업데이트 완료
- [ ] settings.json 스키마 검증 통과

---

## 8. Files Reference

| File | Purpose |
|------|---------|
| `/home/palantir/.claude/settings.json` | Main configuration |
| `/home/palantir/.claude/CLAUDE.md` | V7.6 → V7.7 |
| `/home/palantir/.agent/prompts/infra-update-20260205/` | Workload outputs |
| `/home/palantir/.claude/references/task-api-guideline.md` | V3.1.0 |

---

> **Approved:** 2026-02-05
> **Next Step:** Phase 1 병렬 실행
