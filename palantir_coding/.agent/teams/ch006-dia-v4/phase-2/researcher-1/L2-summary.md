# L2 Summary — DIA v4.0 Research (Phase 2)

**Researcher:** researcher-1 | **GC Version:** GC-v1 | **Date:** 2026-02-07

---

## Executive Summary

DIA v3.0 → v4.0 업그레이드를 위한 3개 도메인 심층 조사를 완료했습니다.
핵심 발견: SubagentStart hook은 spawn을 차단할 수 없지만 `additionalContext` 주입이 가능하며,
Edit tool의 `old_string` 기반 교체는 section-per-role Team Memory에 안전합니다.

---

## Domain 1: Team Memory (TEAM-MEMORY.md)

### 메커니즘 설계

**위치:** `.agent/teams/{session-id}/TEAM-MEMORY.md`

**Section-per-role 방식:**
- 파일을 역할별 섹션으로 분할 (## Lead, ## researcher-1, ## implementer-1 등)
- 각 teammate는 자신의 섹션만 Edit tool로 수정
- Lead는 전체 파일을 읽고 Gate 시점에 큐레이션 (stale 정보 정리)

**동시 쓰기 안전성 분석:**

| Tool | 메커니즘 | 동시 쓰기 안전성 | 이유 |
|------|----------|-----------------|------|
| Edit | old_string→new_string 교체 | 안전 (섹션 분리 시) | 다른 섹션의 old_string을 건드리지 않음 |
| Write | 전체 파일 덮어쓰기 | 위험 | 마지막 Write만 보존, 이전 데이터 소실 |

**결론:** Edit tool + section-per-role이 유일한 안전 패턴.
Write tool 사용을 **금지**해야 함 (최초 생성 시만 허용).

### L1/L2/L3와의 구분

| 구분 | Team Memory | L1/L2/L3 |
|------|------------|----------|
| 목적 | 실시간 knowledge sharing | Task output handoff |
| 수명 | 세션 내 (Gate 시점에 정리) | 세션 간 지속 가능 |
| 소유 | Section-per-role (공유 파일) | Teammate 전용 디렉토리 |
| 업데이트 | 작업 중 지속적 | 체크포인트 시점 |
| 내용 | 발견, 패턴, 결정, 경고 | 구조화된 산출물 |

### `memory: user` vs TEAM-MEMORY

| 구분 | memory: user | TEAM-MEMORY |
|------|-------------|-------------|
| 범위 | 개인 (agent type별) | 팀 (세션 내) |
| 지속성 | 세션 간 영구 | 세션 내 한정 |
| 위치 | ~/.claude/agent-memory/{type}/ | .agent/teams/{session}/TEAM-MEMORY.md |
| 내용 | 범용 학습/패턴 | 현재 프로젝트 specific |

### Lead 큐레이션 시점
1. **Phase Gate 통과 시:** stale 정보 정리, completed task 관련 정보 정리
2. **GC 버전 업 시:** TEAM-MEMORY에 GC delta 요약 추가
3. **Teammate 교체 시:** 이전 teammate 섹션 보존 (후임이 참조)

---

## Domain 2: Context Delta Protocol

### 기존 GC 파일 크기 측정

| Session | 파일 | 줄 수 | 추정 토큰 |
|---------|------|-------|-----------|
| ch001-ldap | global-context.md | 50줄 | ~1,000 |
| agent-teams-write-plan | global-context.md | 190줄 | ~3,800 |
| execution-pipeline | global-context.md | 177줄 | ~3,500 |
| **중앙값** | — | **~130줄** | **~2,600** |

### Delta 프로토콜 설계

**현재 (v3.0):** [CONTEXT-UPDATE]에 full GC 재전송 또는 간략 설명
**제안 (v4.0):** Delta 전용 포맷

```
[CONTEXT-UPDATE] GC-v{N} → GC-v{N+1}
Delta:
- ADDED: {section.field}: {value}
- CHANGED: {section.field}: {old} → {new}
- REMOVED: {section.field}
```

**Full Fallback 조건:**
1. Version gap > 1 (e.g., teammate가 GC-v3인데 GC-v5 발행)
2. Teammate compact recovery (CONTEXT_LOST 상태)
3. 최초 spawn (IP-001)
4. Delta가 GC의 50% 이상 변경 시

**Token 절감 추정:**
- Full injection: ~2,600 tokens (중앙값)
- Typical delta (1-2 섹션 변경): ~200-500 tokens
- 절감율: 70-90% per update

### Implementation 포인트
- Lead가 GC 파일 수정 후 old_version과 비교하여 delta 계산
- Delta는 [CONTEXT-UPDATE] SendMessage에 inline 포함 (별도 파일 불필요)
- Teammate는 [ACK-UPDATE]에 delta 적용 결과 확인 포함
- orchestration-plan.md에 teammate별 GC 수신 버전 추적 (기존과 동일)

---

## Domain 3: Hook GC Verification

### SubagentStart Hook — 핵심 발견

**공식 문서 확인 결과 (https://code.claude.com/docs/en/hooks):**

| 속성 | 값 |
|------|-----|
| Input JSON | session_id, transcript_path, cwd, permission_mode, hook_event_name, agent_id, agent_type |
| Matcher | agent_type (custom agent names 지원: researcher, implementer 등) |
| Exit code 2 | **차단 불가** — stderr가 user에게만 표시됨 |
| additionalContext | **지원** — stdout JSON으로 subagent context에 주입 |

**핵심:** SubagentStart는 spawn을 **차단할 수 없습니다**. Exit code 2는 non-blocking입니다.
그러나 `additionalContext`로 GC version 정보를 주입하여 context awareness를 강화할 수 있습니다.

### SubagentStart Hook 강화 방안

현재 hook은 단순 로깅만 수행 (exit 0). 개선 방안:

```bash
#!/bin/bash
# on-subagent-start.sh (enhanced)
INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // "unknown"')
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // "unknown"')

# 1. Logging (기존)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE" >> "$LOG_DIR/teammate-lifecycle.log"

# 2. GC version injection (신규)
GC_DIR="/home/palantir/.agent/teams"
LATEST_GC=$(find "$GC_DIR" -name "global-context.md" -newer "$GC_DIR/teammate-lifecycle.log" 2>/dev/null | head -1)
if [ -n "$LATEST_GC" ]; then
  GC_VERSION=$(grep -m1 '^version:' "$LATEST_GC" | awk '{print $2}')
  jq -n --arg ver "$GC_VERSION" '{
    "hookSpecificOutput": {
      "hookEventName": "SubagentStart",
      "additionalContext": ("Current GC version: " + $ver + ". Verify your injected context matches this version.")
    }
  }'
else
  exit 0
fi
```

**한계:** team session-id를 hook이 알 수 없음 (input에 team_name 없음).
→ 파일 시스템 scan 필요 또는 환경변수 설정 필요.

### 새로운 Hook Events 발견

공식 문서에서 현재 settings.json에 미반영된 2개 hook 발견:

| Hook | 설명 | 차단 가능? | DIA 활용 |
|------|------|-----------|----------|
| **TeammateIdle** | Teammate idle 전 실행 | **Yes (exit 2)** | 품질 게이트 — L1/L2 작성 전 idle 차단 |
| **TaskCompleted** | Task 완료 표시 전 실행 | **Yes (exit 2)** | 완료 품질 검증 — L1/L2 존재 확인 |

**TeammateIdle input:** `teammate_name`, `team_name` (matcher 미지원, 항상 실행)
**TaskCompleted input:** `task_id`, `task_subject`, `task_description`, `teammate_name`, `team_name`

### Hook 강화 권장사항

1. **SubagentStart:** additionalContext로 GC version 주입 (차단은 불가)
2. **TeammateIdle (신규):** L1/L2 파일 존재 여부 검증, 미작성 시 exit 2로 차단
3. **TaskCompleted (신규):** task 완료 전 산출물 검증, 미충족 시 exit 2로 차단
4. **기존 hooks:** on-pre-compact.sh, on-session-compact.sh, on-task-update.sh는 변경 불필요

---

## MCP Tools Usage Report

| Tool | Usage | Purpose |
|------|-------|---------|
| tavily (WebSearch) | 5회 | hooks schema, exit code 2, agent teams, Edit concurrency, additionalContext |
| WebFetch | 3회 | hooks reference (공식), agent teams docs (공식), gist schemas |

---

## Recommendations for Implementation

1. **TEAM-MEMORY.md:** CLAUDE.md에 §N 추가, agent .md에 Edit-only section rule 추가
2. **Context Delta:** CLAUDE.md §4 Communication Protocol에 delta 포맷 추가, §6에 fallback 조건
3. **Hook Enhancement:** SubagentStart additionalContext + TeammateIdle + TaskCompleted 추가
4. **task-api-guideline.md:** §13 Team Memory Protocol, §14 Context Delta 추가
