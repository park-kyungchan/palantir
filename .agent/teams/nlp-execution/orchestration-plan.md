---
feature: opus46-nlp-conversion (execution)
current_phase: 6
gc_version: GC-v4
source_sessions:
  - opus46-nlp-conversion (Phase 1-3)
  - nlp-validation (Phase 5)
---

# Orchestration Plan — Phase 6 Execution

## Source Artifacts
- L3-v2 design: `.agent/teams/opus46-nlp-conversion/phase-3/architect-2/L3-full/architecture-design-v2.md`
- GC-v4: `.agent/teams/nlp-execution/global-context.md`
- Upstream PT design: `docs/plans/2026-02-08-permanent-tasks-design.md`
- Phase 5 challenge report: `.agent/teams/nlp-validation/phase-5/devils-advocate-1/L3-full/challenge-report.md`

## Phase 5 Conditions (must be applied)
- C-2.2: Restore 4 lost behaviors in CLAUDE.md v6.0 (~4 lines)
  1. Max 3 iterations per phase (add to §2)
  2. DIA pipeline-level mandate (add to §2 or §3)
  3. Spawn count guidance (add to §6)
  4. Gate S-2 6000-line threshold (add to §6 "Before Spawning")

## Execution Plan
- Tasks: 11 (T3 excluded)
- Implementers: 2 persistent
- Rounds: 6
- Max concurrent: 2

## Round Schedule
| Round | impl-1 | impl-2 | Dependencies |
|-------|--------|--------|--------------|
| R1 | T1 (CREATE SKILL.md) | T2 (CLAUDE.md + C-2.2) | None |
| R2 | T4 (common-protocol) | T8 (hook) | T2 complete |
| R3 | T11 (3 agent .md) | T12 (3 agent .md) | T2+T4 complete |
| R4 | T5 (brainstorm skill) | T6 (write-plan skill) | T1+T4 complete |
| R5 | T7 (exec-plan skill) | T9 (MEMORY.md) | T1+T4 complete |
| R6 | T10 (ARCHIVE.md) | (idle) | T9 complete |

## Teammates
- implementer-1: SHUTDOWN (completed T1, T4, T11, T5, T7)
- implementer-2: SHUTDOWN (completed T2, T8, T12, T6, T9)

## Progress
- R1: COMPLETE (T1 SKILL.md ✓, T2 CLAUDE.md v6.0 ✓, C-2.2 4/4 ✓)
- R2: COMPLETE (T4 common-protocol v2.0 ✓, T8 hook GC→PT ✓)
- R3: COMPLETE (T11 3 agents ✓, T12 3 agents ✓ — all 6 agent .md NLP v2.0)
- R4: COMPLETE (T5 brainstorm Phase 0 ✓, T6 write-plan Phase 0 ✓)
- R5: COMPLETE (T7 exec-plan Phase 0 ✓, T9 MEMORY.md v6.0 ✓)
- R6: COMPLETE (T10 ARCHIVE.md — handled in Clean Termination)

## Gate 6: APPROVED (2026-02-08)
- 10/10 tasks PASS (G6-1~G6-5)
- Cross-task interface consistency: PASS (G6-6)
- No unresolved critical issues: PASS (G6-7)
- Protocol markers in modified files: 0
- Total lines: 2,409 across 13 files
