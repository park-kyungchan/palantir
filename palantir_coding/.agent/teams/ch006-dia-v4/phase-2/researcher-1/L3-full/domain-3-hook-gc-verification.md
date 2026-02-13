# Domain 3: Hook GC Verification — Deep Research

## 1. SubagentStart Hook — Official Documentation Analysis

**Source:** https://code.claude.com/docs/en/hooks (fetched 2026-02-07)

### Input JSON Schema

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

**주의:** `team_name`, `agent_name` 필드는 공식 스키마에 **없음**.
현재 on-subagent-start.sh가 사용하는 `.agent_name`과 `.tool_input.subagent_type`은
공식 스키마와 불일치. `agent_type` 필드만 공식.

### Matcher
- agent_type 필드로 필터링
- 사용 가능 값: `Bash`, `Explore`, `Plan`, 또는 custom agent names (`researcher`, `implementer` 등)

### Exit Code Behavior

| Exit Code | 효과 |
|-----------|------|
| 0 | 성공 — stdout JSON 파싱 |
| 2 | **Non-blocking** — stderr가 **user에게만** 표시. Spawn 진행됨. |
| Other | Non-blocking error — stderr가 verbose mode에서만 표시 |

**핵심 결론:** SubagentStart는 spawn을 **차단할 수 없음**.
`exit 2`로 차단을 시도해도 subagent는 정상적으로 생성됨.

### Output JSON (additionalContext)

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "string — subagent의 context에 주입됨"
  }
}
```

**이것이 GC 검증의 유일한 메커니즘:**
- Hook이 GC version을 파일에서 읽어 additionalContext로 주입
- Subagent가 시작 시 이 context를 수신
- Subagent의 injected GC version과 비교 가능

## 2. 현재 Hook 분석

### on-subagent-start.sh (현재)
```bash
#!/bin/bash
INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"')
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"')
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "no-team"')
# ... logging only, exit 0
```

**문제점:**
1. `.tool_input.subagent_type`, `.agent_name`, `.tool_input.team_name` — 공식 스키마에 없는 필드
2. jq fallback (`//`) 으로 보완하고 있으나, 실제 동작 미검증
3. 로깅만 수행 — GC version 검증/주입 없음

### on-subagent-stop.sh (현재)
- 동일 패턴 — 로깅만 수행
- SubagentStop은 `decision: "block"`으로 **차단 가능** (stop 방지)

## 3. 새로운 Hook Events 발견

### TeammateIdle (현재 미구현)

**공식 문서:**
- 실행 시점: Agent team teammate가 idle 상태로 전환되기 직전
- Input: `teammate_name`, `team_name` (common fields에 추가)
- Matcher: 미지원 (항상 실행)
- **Exit code 2: idle 차단 가능** — stderr가 teammate에게 feedback으로 전달
- Teammate는 feedback을 받고 **계속 작업**

**DIA 활용 방안:**
```bash
#!/bin/bash
# on-teammate-idle.sh
INPUT=$(cat)
TEAMMATE_NAME=$(echo "$INPUT" | jq -r '.teammate_name')
TEAM_NAME=$(echo "$INPUT" | jq -r '.team_name')

# Check if L1/L2 files exist
TEAM_DIR="/home/palantir/.agent/teams/$TEAM_NAME"
L1_FILE=$(find "$TEAM_DIR" -path "*/$TEAMMATE_NAME/L1-index.yaml" 2>/dev/null)

if [ -z "$L1_FILE" ]; then
  echo "L1/L2 files not found. Write L1-index.yaml and L2-summary.md before going idle." >&2
  exit 2  # Blocks idle — teammate continues
fi

exit 0
```

### TaskCompleted (현재 미구현)

**공식 문서:**
- 실행 시점: Task가 completed로 표시되기 직전
- Input: `task_id`, `task_subject`, `task_description`, `teammate_name`, `team_name`
- Matcher: 미지원 (항상 실행)
- **Exit code 2: 완료 차단 가능** — stderr가 model에게 feedback으로 전달
- Task는 completed로 표시되지 않음

**DIA 활용 방안:**
```bash
#!/bin/bash
# on-task-completed.sh
INPUT=$(cat)
TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject')
TEAMMATE_NAME=$(echo "$INPUT" | jq -r '.teammate_name // empty')
TEAM_NAME=$(echo "$INPUT" | jq -r '.team_name // empty')

# Only enforce for team tasks
if [ -z "$TEAM_NAME" ]; then
  exit 0
fi

# Check if teammate has L1/L2 output
if [ -n "$TEAMMATE_NAME" ]; then
  TEAM_DIR="/home/palantir/.agent/teams/$TEAM_NAME"
  L1_FILE=$(find "$TEAM_DIR" -path "*/$TEAMMATE_NAME/L1-index.yaml" 2>/dev/null)

  if [ -z "$L1_FILE" ]; then
    echo "Cannot complete task '$TASK_SUBJECT': L1-index.yaml not found for $TEAMMATE_NAME. Write output files first." >&2
    exit 2
  fi
fi

exit 0
```

## 4. SubagentStart Hook 강화 설계

### 목표
GC version을 additionalContext로 주입하여 teammate의 context awareness 강화.

### 구현 과제
1. **team session-id 식별:** SubagentStart input에 team_name 없음
   - 대안 A: 환경변수 `CLAUDE_CODE_TASK_LIST_ID` 사용 → team name
   - 대안 B: 최근 수정된 `.agent/teams/*/global-context.md` scan
   - 대안 C: `.claude/teams/*/config.json` 에서 활성 팀 탐색
   - **권장:** 대안 C (config.json이 가장 신뢰성 높음)

2. **GC version 추출:**
   ```bash
   GC_VERSION=$(grep -m1 '^version:' "$GC_FILE" | awk '{print $2}')
   ```

3. **additionalContext 주입:**
   ```json
   {
     "hookSpecificOutput": {
       "hookEventName": "SubagentStart",
       "additionalContext": "[DIA-HOOK] Active team: {team}. Current GC: {version}. Verify your injected context version matches."
     }
   }
   ```

### 한계
- **Spawn 차단 불가:** Stale context의 teammate가 생성되어도 hook으로 막을 수 없음
- **Context 비교 불가:** Hook이 Lead의 directive 내용을 알 수 없음
- **실효성:** additionalContext는 "알림" 수준. 실제 enforcement는 DIA protocol (Impact Analysis)에 의존

### 결론
SubagentStart hook 강화는 "nice to have" 수준.
실제 GC consistency enforcement는:
1. Lead의 CIP (Context Injection Protocol) — directive에 full/delta GC 포함
2. Teammate의 DIAVP (Impact Analysis) — version 확인 echo-back
3. Lead의 Gate — stale context 감지 시 gate block

## 5. Hook Infrastructure Summary

### Current (v3.0)
| Hook | Event | Action |
|------|-------|--------|
| on-subagent-start.sh | SubagentStart | Logging only |
| on-subagent-stop.sh | SubagentStop | Logging only |
| on-task-update.sh | PostToolUse(TaskUpdate) | Logging only |
| on-pre-compact.sh | PreCompact | Task snapshot |
| on-session-compact.sh | SessionStart(compact) | DIA recovery message |

### Proposed (v4.0)
| Hook | Event | Action | New? |
|------|-------|--------|------|
| on-subagent-start.sh | SubagentStart | Logging + GC version additionalContext | Enhanced |
| on-subagent-stop.sh | SubagentStop | Logging (unchanged) | — |
| on-task-update.sh | PostToolUse(TaskUpdate) | Logging (unchanged) | — |
| on-pre-compact.sh | PreCompact | Task snapshot (unchanged) | — |
| on-session-compact.sh | SessionStart(compact) | DIA recovery (unchanged) | — |
| on-teammate-idle.sh | TeammateIdle | L1/L2 existence check, exit 2 차단 | **NEW** |
| on-task-completed.sh | TaskCompleted | Output verification, exit 2 차단 | **NEW** |

### settings.json 변경
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

## 6. Exit Code 2 Behavior Summary (All Hooks)

공식 문서에서 확인한 전체 hook의 exit code 2 동작:

| Hook Event | Can Block? | Exit 2 Effect |
|-----------|-----------|---------------|
| PreToolUse | Yes | Tool call 차단 |
| PermissionRequest | Yes | Permission 거부 |
| UserPromptSubmit | Yes | Prompt 차단 |
| Stop | Yes | Stop 방지 (계속 대화) |
| SubagentStop | Yes | Subagent stop 방지 |
| **TeammateIdle** | **Yes** | **Idle 방지 (계속 작업)** |
| **TaskCompleted** | **Yes** | **완료 방지 (feedback 전달)** |
| PostToolUse | No | stderr를 Claude에게 표시 |
| PostToolUseFailure | No | stderr를 Claude에게 표시 |
| Notification | No | stderr를 user에게만 표시 |
| **SubagentStart** | **No** | **stderr를 user에게만 표시** |
| SessionStart | No | stderr를 user에게만 표시 |
| SessionEnd | No | stderr를 user에게만 표시 |
| PreCompact | No | stderr를 user에게만 표시 |
