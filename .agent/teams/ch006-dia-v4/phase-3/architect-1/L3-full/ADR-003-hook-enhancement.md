# ADR-003: Hook Enhancement

**Status:** PROPOSED | **Date:** 2026-02-07 | **Author:** architect-1

---

## 1. Context

DIA v3.0의 enforcement는 전적으로 Lead의 LLM 판단에 의존합니다 (CIP, DIAVP, LDAP).
Teammate가 L1/L2를 작성하지 않고 idle에 빠지거나, 산출물 없이 task를 완료 표시하면
Lead가 Gate 시점에서야 발견합니다. 자동화된 quality gate가 없어 enforcement gap이 존재합니다.

Claude Code v2.1.32에서 TeammateIdle과 TaskCompleted hook events가 추가되었으며,
exit code 2로 각각 idle 전환과 task 완료를 차단할 수 있습니다.

## 2. Decision

**3개 hook을 추가/강화합니다:**
1. on-subagent-start.sh: GC version additionalContext 주입 (기존 강화)
2. on-teammate-idle.sh: L1/L2 존재 + 최소 크기 검증 (신규)
3. on-task-completed.sh: 산출물 존재 검증 (신규)

**포지셔닝:** Hook = Layer 4 "Speed Bump" (구문 검증, LLM 비의존)

## 3. Alternatives Considered

### Alternative A: Lead-Only Gate Enforcement (Hook 없음)
- Lead가 Gate 시점에 L1/L2 존재 및 내용 검증
- **장점:** 단순, 의미적 검증 가능 (LLM 판단)
- **단점:** Gate까지 enforcement 없음, 중간에 artifact 누락 감지 불가
- **기각 사유:** 사후 검증만으로는 proactive enforcement 불가

### Alternative B: Full Hook Enforcement (강력한 검증)
- Hook에서 YAML 구조 검증, 내용 길이, 키 존재 등 심층 검증
- **장점:** 자동화 수준 높음
- **단점:** Hook timeout (10초), 복잡한 스크립트 유지보수, 의미 검증 여전히 불가
- **기각 사유:** 과도한 복잡성 대비 증분 가치 낮음

### Alternative C: Speed Bump Hooks (채택)
- 파일 존재 + 최소 크기만 검증 (구문 수준)
- **장점:** 단순, 빠름 (<1초), 정직한 실수 잡음, LLM 독립
- **단점:** 의도적 우회 가능 (minimal valid file)
- **채택 사유:** Layer 1-3 (LLM 기반)과 상호 보완, 자동화 방어선 추가

## 4. 4-Layer Enforcement Architecture (DIA v4.0)

```
Layer 1: CIP (Context Injection)     → 전달 보장    → Lead LLM 의존
Layer 2: DIAVP (Impact Verification) → 이해 검증    → Lead LLM 의존
Layer 3: LDAP (Adversarial Challenge) → 체계적 사고  → Lead LLM 의존
Layer 4: Hooks (Automated Gates)      → 산출물 존재  → 자동화, LLM 비의존
```

**Layer 4의 고유 가치:**
- Lead compact/실수/건너뛰기 시에도 기계적으로 실행
- 정직한 실수(L1 작성 잊음)에 대한 즉각 피드백
- 의도적 우회는 Layer 2-3에서 감지 (Lead가 Gate에서 내용 검토)

## 5. Hook Specifications

### 5.1 on-subagent-start.sh (Enhanced)

**목적:** Spawn 시 현재 GC version을 additionalContext로 주입

**Input JSON (official schema):**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "string",
  "hook_event_name": "SubagentStart",
  "agent_id": "string",
  "agent_type": "string"
}
```

**주의:** `team_name`, `agent_name` 필드는 공식 스키마에 없음.
현재 hook의 `.agent_name`, `.tool_input.subagent_type`, `.tool_input.team_name` 참조는
비공식이므로 jq fallback (`//`)으로 보호해야 함.

**Enhanced Logic:**
1. 기존 로깅 유지
2. 활성 팀 디렉토리에서 global-context.md의 version 추출
3. additionalContext로 GC version 주입

**Team Directory Discovery:**
- `.claude/teams/` 디렉토리에서 가장 최근 수정된 config.json의 팀 확인
- 한 세션에 하나의 팀만 존재 (ISS-004) → 단일 결과 보장
- fallback: 팀 찾지 못하면 additionalContext 없이 exit 0 (기존 동작)

**Output JSON:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "[DIA-HOOK] Active team: {team_name}. Current GC: GC-v{N}. Verify your injected context version matches."
  }
}
```

**Exit Code:** Always 0 (SubagentStart는 exit 2로도 차단 불가)

**한계:** additionalContext는 "알림" 수준. 실제 enforcement는 DIA Layer 1-2 (CIP + DIAVP).

### 5.2 on-teammate-idle.sh (New)

**목적:** Teammate idle 전 L1/L2 산출물 존재 검증

**Input JSON:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "hook_event_name": "TeammateIdle",
  "teammate_name": "string",
  "team_name": "string"
}
```

**Validation Logic:**
1. team_name에서 팀 디렉토리 경로 구성: `.agent/teams/{team_name}/`
2. 팀 디렉토리에서 `{teammate_name}/L1-index.yaml` 검색 (재귀)
3. 파일 존재 + 최소 크기 (50 bytes) 확인
4. L2-summary.md 동일 확인 (100 bytes 최소)

**Exit Codes:**
| Condition | Exit | Effect |
|-----------|------|--------|
| L1 + L2 존재, 최소 크기 충족 | 0 | Idle 허용 |
| L1 또는 L2 미존재 | 2 | Idle 차단, stderr feedback |
| L1 또는 L2 < 최소 크기 | 2 | Idle 차단, stderr feedback |
| team_name 없음 (비팀 세션) | 0 | 비팀은 검증 불필요 |
| 팀 디렉토리 없음 | 0 | 초기 setup 중, 통과 |

**Stderr Feedback (exit 2 시):**
```
L1/L2 output files not found or too small for {teammate_name}.
Write L1-index.yaml (≥50 bytes) and L2-summary.md (≥100 bytes) before going idle.
Your output directory should be under .agent/teams/{team_name}/.
```

**Timeout:** 10초 (filesystem scan 충분)

### 5.3 on-task-completed.sh (New)

**목적:** Task 완료 전 산출물 존재 검증

**Input JSON:**
```json
{
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "hook_event_name": "TaskCompleted",
  "task_id": "string",
  "task_subject": "string",
  "task_description": "string",
  "teammate_name": "string",
  "team_name": "string"
}
```

**Validation Logic:**
1. team_name이 비어있으면 exit 0 (비팀 task)
2. teammate_name이 비어있으면 exit 0 (Lead task — Lead는 L1/L2 의무 없음)
3. 팀 디렉토리에서 `{teammate_name}/L1-index.yaml` 검색
4. 파일 존재 + 최소 크기 (50 bytes) 확인
5. L2-summary.md 동일 확인

**Exit Codes:**
| Condition | Exit | Effect |
|-----------|------|--------|
| 검증 통과 | 0 | Task 완료 허용 |
| L1/L2 미충족 | 2 | 완료 차단, stderr feedback |
| 비팀 또는 Lead task | 0 | 검증 건너뜀 |

**Stderr Feedback (exit 2 시):**
```
Cannot complete task '{task_subject}': L1/L2 output files not found for {teammate_name}.
Write L1-index.yaml and L2-summary.md before marking task as completed.
```

## 6. settings.json Configuration

### New Entries (추가)

```json
{
  "hooks": {
    "TeammateIdle": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-teammate-idle.sh",
            "timeout": 10,
            "statusMessage": "Verifying teammate output before idle"
          }
        ]
      }
    ],
    "TaskCompleted": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-task-completed.sh",
            "timeout": 10,
            "statusMessage": "Verifying task completion criteria"
          }
        ]
      }
    ]
  }
}
```

### Existing Entry (수정) — SubagentStart
현재 hook 명세는 유지하되, 스크립트 내용만 강화.
settings.json의 SubagentStart 항목은 변경 없음.

## 7. Backward Compatibility

### 비팀 세션
- 모든 새 hook은 `team_name` 확인 → 비어있으면 exit 0
- 비팀 세션(Solo mode)에서는 hook이 아무 검증 없이 통과

### 기존 팀 세션
- TEAM-MEMORY.md가 없는 기존 세션: hook은 L1/L2만 검증 (TEAM-MEMORY 무관)
- 기존 5개 hook: 변경 없음 (on-subagent-stop, on-task-update, on-pre-compact, on-session-compact)

## 8. Consequences

### Positive
- LLM 비의존 자동 enforcement 추가 (Lead compact/실수 시에도 동작)
- 정직한 실수(L1/L2 작성 잊음) 즉각 피드백
- SubagentStart GC 주입으로 context awareness 강화

### Negative
- Hook 스크립트 유지보수 부담 (3개 추가)
- 의도적 우회(minimal valid file) 불가능하지 않음
- filesystem scan 의존 (경로 convention 변경 시 hook도 수정 필요)

### Neutral
- Hook은 "Speed Bump" — 주 enforcement는 여전히 Layer 1-3 (CIP, DIAVP, LDAP)
- Hook 실패(timeout, error)는 non-blocking (exit 0 fallback) → 안전 기본값
