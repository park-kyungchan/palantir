# Orchestration Plan — RSIL System Phase 6 Implementation

## Pipeline Status

```
P1 Discovery    [████████████] COMPLETE
P2 Research     [████████████] COMPLETE
P3 Architecture [████████████] COMPLETE
P4 Design       [████████████] COMPLETE
P5 Validation   [████████████] COMPLETE (CONDITIONAL_PASS)
P6 Implementation [██░░░░░░░░░░] IN PROGRESS  ← YOU ARE HERE
P7-8 Testing       [ not started ]
P9 Delivery        [ not started ]
```

## Team

| Role | Agent | Status | PT Version | Tasks |
|------|-------|--------|------------|-------|
| Lead | team-lead | active | PT-v4 | D (integration) |
| implementer-1 | — | pending spawn | — | A |
| implementer-2 | — | pending spawn | — | B, C |

## Dependency Graph

```
Task A (rsil-global NEW)  ─────────┐
                                    ├──→ Task D (integration)
Task B (rsil-review MODIFY) ──┐    │
                               ├───┘
Task C (memory+tracker)   ────┘
```

A, B, C: independent (parallel)
D: blockedBy A, B, C (Lead handles)

## Spawn Plan

| Implementer | Tasks | Files | VL |
|-------------|-------|-------|----|
| implementer-1 | A | .claude/skills/rsil-global/SKILL.md (NEW, ~400-500L) | VL-2/3 |
| implementer-2 | B, C | rsil-review (MODIFY), CLAUDE.md (MODIFY), agent-memory (NEW), tracker (MODIFY) | VL-1 |

## Workstream Progress

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| A | implementer-1 | pending | rsil-global SKILL.md NEW |
| B | implementer-2 | pending | rsil-review 5 deltas + CLAUDE.md |
| C | implementer-2 | pending | agent-memory + tracker |
| D | Lead | blocked by A,B,C | integration verification |

## Gate 6 Criteria

| # | Criterion | Status |
|---|-----------|--------|
| G6-1 | Spec review PASS (per task) | pending |
| G6-2 | Quality review PASS (per task) | pending |
| G6-3 | Self-test PASS (per task) | pending |
| G6-4 | File ownership COMPLIANT | pending |
| G6-5 | L1/L2/L3 exist | pending |
| G6-6 | Cross-task interface consistency | pending |
| G6-7 | No unresolved critical issues | pending |

## Phase 5 Conditions (accepted)

1. Add automated diff command to Task D for Foundation verification
2. Consider git diff in Type A Tier 1 readings
3. Label seed data as "manually estimated"
