# Team Memory — INFRA E2E Optimization

## Lead
- [Decision] Two parallel implementers: WS-1 (hooks/settings) and WS-2 (structural optimization)
- [Decision] Task #6 (common-protocol.md) blocks #7 and #8 (CLAUDE.md + agents need reference file)
- [Finding] settings.json deny rules use colon syntax — confirmed STILL BROKEN as of session start
- [Finding] on-pre-compact.sh already has jq check but missing INPUT=$(cat)
- [Finding] on-subagent-stop.sh already has conditional jq check but no early guard

## implementer-ws1
- [Finding] on-session-compact.sh has same missing INPUT=$(cat) issue as on-pre-compact.sh — outside WS-1 ownership scope but should be tracked
- [Finding] TeammateIdle/TaskCompleted events are team-scoped only — jq exit 2 guard has zero blast radius on non-team operations
- [Pattern] INPUT=$(cat) serves as Unix pipe drainage hygiene — side effect (drain) is purpose, not stored value

## implementer-ws2
- [Pattern] CLAUDE.md content split: BEHAVIORAL RULES (stay in CLAUDE.md) vs PROCEDURAL DETAIL (move to agent-common-protocol.md)
- [Decision] "Every removed line must have a surviving authoritative source" — safety invariant for structural reduction
- [Finding] 5 reduction targets identified: §4 format strings, "Why This Exists" paragraph, version header, §9 teammate recovery, §3 pre-compact detail
- [Finding] 9 sole-source sections identified as untouchable: §2 Pipeline, §5 Ownership, §6 Pre-Spawn, §6 DIA Engine, §7 MCP, §8 Safety, [PERMANENT] Lead/Teammate/Cross-Refs
