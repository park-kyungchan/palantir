# Agent Teams — Known Bugs & Workarounds

## BUG-001: permissionMode: plan blocks MCP tools (2026-02-07)

### Problem
- `permissionMode: plan`으로 설정된 teammate (researcher, architect)가 MCP tool 호출 시 "Waiting for team lead approval" 상태로 stuck
- 영향받는 도구: `mcp__tavily__tavily_search`, `mcp__context7__*` 등 모든 MCP tools
- 증상: teammate가 permission_request를 Lead inbox에 보내지만, Lead에게는 plan_approval_response(request_id 필요)만 있고 permission_response 메커니즘이 없음
- teammate는 이 상태에서 shutdown_request에도 응답 불가 (tool 호출이 blocking 상태)

### Root Cause
- `permissionMode: plan`은 read-only exploration 모드로 설계됨
- MCP tools는 외부 네트워크 호출이므로 plan mode에서 "non-read-only"로 분류되어 permission 필요
- Agent Teams에서 Lead가 teammate의 tool permission을 승인하는 공식 메커니즘이 없음

### Workaround
- **researcher/architect 스폰 시 `mode: "default"` 사용** (agent .md의 `permissionMode: plan` 무시)
- 안전성: disallowedTools (Edit, Write, Bash 등)가 이미 코드 수정을 차단하므로 default mode에서도 안전
- Task tool spawn parameter `mode`가 agent .md frontmatter `permissionMode`를 override함

### Permanent Fix Candidates
1. agent .md의 `permissionMode`를 `plan` → `default`로 변경 (researcher, architect)
2. settings.json에 MCP tools에 대한 global allow rule 추가
3. Claude Code에서 plan mode + MCP 호환성 개선 대기 (upstream fix)

### Affected Agents
- researcher.md: `permissionMode: plan` → 스폰 시 `mode: "default"` 사용
- architect.md: `permissionMode: plan` → 스폰 시 `mode: "default"` 사용
- 나머지 agents: `permissionMode: acceptEdits` 또는 `default` → 영향 없음

### Prevention Rule [PERMANENT]
**모든 teammate 스폰 시 MCP tools 사용이 필요하면 `mode: "default"` 지정.**
`permissionMode: plan` agent도 disallowedTools로 이미 mutation이 차단되므로 default mode가 안전함.

## BUG-003: $CLAUDE_SESSION_ID not available in hook contexts (2026-02-10)

### Problem
- PostToolUse hook에서 어떤 agent가 tool call을 했는지 식별 불가
- `$CLAUDE_SESSION_ID` 환경변수가 Claude Code hook context에서 존재하지 않음
- GitHub issue #17188 OPEN — Claude Code 팀 인지, 미해결

### Root Cause
- Claude Code hooks는 child process로 실행되지만, agent의 session ID를 환경변수로 전달하지 않음
- stdin JSON의 `session_id`는 parent session의 SID (Lead의 SID)
- 따라서 모든 hook event가 동일한 SID로 기록됨

### Workaround (AD-29)
- SubagentStart hook에서 stdin `session_id`를 agent name과 매핑하여 `session-registry.json`에 저장
- PostToolUse hook에서 session-registry.json을 조회하여 agent name 해석
- **한계:** parent SID만 사용하므로 정확한 child agent 식별이 아닌 best-effort mapping
- 미해석 SID는 "lead"로 fallback

### Impact
- events.jsonl의 agent attribution이 100% 정확하지 않음
- RTD Index (Lead-maintained)는 이 한계에 영향받지 않음 (Lead가 직접 작성)
- Dashboard UI 구현 시 이 한계를 고려해야 함

### Fix Condition
- Claude Code가 `$CLAUDE_SESSION_ID`를 hook 환경변수로 제공하면 해결
- `on-subagent-start.sh`에서 child의 실제 SID를 사용하도록 업데이트
- `on-rtd-post-tool.sh`에서 정확한 agent 매핑 가능

### Discovered During
- RTD System (INFRA v7.0) Phase 5 — devils-advocate-1 발견, AD-29로 문서화

## BUG-004: No cross-agent compaction notification (2026-02-11)

### Problem
- Teammate가 auto-compact되면 Lead에게 자동 알림이 전달되지 않음
- Teammate는 summarized context로 계속 작업할 수 있어 품질 저하 위험
- Lead는 teammate의 compact 발생을 알 수 없음 (tmux 모니터링 외 방법 없음)

### Root Cause
- PreCompact hook은 해당 teammate 프로세스 내부에서 shell command로 실행
- Hook에서 SendMessage (Claude Code tool)를 직접 호출할 수 없음
- Claude Code에 cross-agent event system이 존재하지 않음
- Agent isolation 설계로 인해 한 agent의 lifecycle event가 다른 agent에게 전파되지 않음

### Current Defense Layers
| Layer | Mechanism | Gap |
|-------|-----------|-----|
| PreCompact hook | teammate state를 파일로 저장 | Lead에게 알림 없음 |
| SessionStart hook | compact 후 recovery context 제공 | 이미 summarized 상태 |
| H-3 (incremental L1) | 매 task 후 L1 기록 | compact 전 마지막 미저장 작업 유실 가능 |
| agent-common-protocol | compact 후 Lead에게 메시지 | teammate가 자발적으로 해야 함 |

### Workaround
- **User tmux 모니터링** — 현재 가장 빠른 감지 수단
- **H-3 mitigation** — incremental L1로 유실 최소화
- **agent-common-protocol §If You Lose Context** — teammate가 compact 인지 시 Lead에게 보고

### Possible Layer 1 Improvement
- PreCompact hook에서 파일 기반 알림: `echo "COMPACTED $(date)" >> .agent/teams/compact-alerts.log`
- Lead가 주기적으로 폴링 (자동이 아닌 수동 체크)
- 한계: 진정한 자동 알림이 아닌 polling 방식

### Layer 2 Required For
- Structured cross-agent event bus (compaction event → Lead notification)
- Real-time agent lifecycle monitoring dashboard
- Automatic re-spawn on compaction detection

### Classification
- Severity: HIGH (summarized context로 작업 시 품질 저하 직결)
- Layer: 1 partial / 2 full solution
- Discovered: Lead Architecture Redesign Phase 6 execution (2026-02-11)

## RESOLVED in CC 2.1.45 (2026-02-18)

### Agent Teams Bedrock/Vertex/Foundry Failure (#23561)
- **Problem**: tmux-spawned teammates failed on Bedrock, Vertex, and Foundry because API provider environment variables were not propagated to tmux processes
- **Fix**: CC now propagates API provider environment variables to tmux-spawned processes
- **Version**: CC 2.1.45

### Task Tool (Backgrounded Agents) Crash (#22087)
- **Problem**: Backgrounded agents crashed with `ReferenceError` on completion
- **Fix**: Completion handler properly handles reference resolution
- **Version**: CC 2.1.45

### Sandbox macOS Temp File Error (#21654)
- **Problem**: "operation not permitted" errors when writing temporary files on macOS
- **Fix**: Uses correct per-user temp directory
- **Version**: CC 2.1.45
