---
version: 1
team: infra-e2e-optimization
created: 2026-02-08
---

# Orchestration Plan — INFRA E2E Optimization

## Pipeline Status

```
Phase 6 (Implementation) ████████░░░░ IN_PROGRESS
Phase 6.V (Verification)  ░░░░░░░░░░░░ PENDING
Phase 9 (Delivery)         ░░░░░░░░░░░░ PENDING
```

## Workstream Progress

```
WS-1 Safety Fixes         [░░░░░] 0/5 tasks
  #1 settings.json deny    ░ PENDING
  #2 blocking hooks jq     ░ PENDING
  #3 tool-failure.sh       ░ PENDING
  #4 pre-compact stdin     ░ PENDING
  #5 non-blocking hooks jq ░ PENDING

WS-2 Structural Opt       [░░░░░] 0/3 tasks
  #6 common-protocol.md    ░ PENDING
  #7 CLAUDE.md reduction   ░ PENDING (blocked by #6)
  #8 agent .md optimization░ PENDING (blocked by #6)

Verification               [░░░░░] 0/1 task
  #9 cross-reference check ░ PENDING (blocked by #1-#8)
```

## Teammate Status

| Teammate | Role | Workstream | GC Version | Status |
|----------|------|-----------|-----------|--------|
| implementer-ws1 | implementer | WS-1 | GC-v1 | SPAWNED — awaiting Impact Analysis |
| implementer-ws2 | implementer | WS-2 | GC-v1 | SPAWNED — awaiting Impact Analysis |

## Dependency Graph

```
#1 (settings.json) ──────────────────────────────┐
#2 (blocking hooks) ─────────────────────────────│
#3 (tool-failure.sh) ────────────────────────────│
#4 (pre-compact.sh) ─────────────────────────────├──→ #9 (Verification) → Gate 6 → Delivery
#5 (non-blocking hooks) ─────────────────────────│
#6 (common-protocol.md) → #7 (CLAUDE.md) ────────│
                         → #8 (agent .md) ────────┘
```

## Spawn Plan

**Implementers:** 2 (parallel, independent workstreams)
**Strategy:** Parallel — no file overlap between WS-1 and WS-2

| Implementer | Tasks | Files | Context Load |
|-------------|-------|-------|-------------|
| implementer-ws1 | #1, #2, #3, #4, #5 | settings.json + 7 hooks | ~400 lines |
| implementer-ws2 | #6, #7, #8 | agent-common-protocol.md + CLAUDE.md + 6 agents | ~1400 lines |

---

## [PERMANENT] Lead Guidelines — Real-Time User Requirements

This section is Lead's **always-on reference** for Teammates Management and overall orchestration.
Updated dynamically as user provides real-time input. Not a task — a living guideline.

### User Requirements (Captured Real-Time)
1. **Task API Mandatory:** Use TaskCreate/TaskUpdate for comprehensive tracking
2. **CLAUDE.md Compliance:** Lead follows Team Constitution strictly
3. **Dependency-Aware Orchestration:** Split work freely, but always respect dependency chains
4. **Real-Time-Dynamic-Impact-Awareness (RTDIA):** User monitors progress in real-time.
   Lead must provide ASCII status updates, update orchestration-plan.md proactively,
   and report state changes immediately.
5. **[PERMANENT] = Lead's Guideline:** Not a final task — an always-on reference document
   for Teammates Management and overall work coordination.

### Teammates Management Guidelines
- Spawn teammates only after Pre-Spawn Checklist (Gate S-1/S-2/S-3)
- Embed full GC-v{N} + task-context in every directive (CIP)
- Verify impact analysis before allowing work (DIAVP)
- Monitor via tmux visual (0 tokens) + TaskList (periodic)
- On silence >30 min: query teammate status
- On CONTEXT_PRESSURE: shutdown → re-spawn with L1/L2
- Update orchestration-plan.md ASCII visualization on every state change
- Report to user in Korean, all artifacts in English
