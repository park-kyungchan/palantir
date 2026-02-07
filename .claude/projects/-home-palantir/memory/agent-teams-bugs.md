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
