---
feature: opus46-nlp-conversion (validation)
current_phase: COMPLETE
gc_version: GC-v4
source_session: opus46-nlp-conversion
---

# Orchestration Plan — Phase 5 Validation

## Source Pipeline
- brainstorming-pipeline output at `.agent/teams/opus46-nlp-conversion/`
- Phase 1-3 all APPROVED, Phase 3-rev APPROVED
- L3-v2 serves as combined Phase 3+4 output (complete rewritten text + 12-task breakdown)

## Validation Target
- Primary: `.agent/teams/opus46-nlp-conversion/phase-3/architect-2/L3-full/architecture-design-v2.md`
- Context: `.agent/teams/opus46-nlp-conversion/global-context.md` (GC-v4)
- Upstream: `docs/plans/2026-02-08-permanent-tasks-design.md`

## Teammates
- devils-advocate-1: SHUTDOWN (Phase 5 complete, verdict: CONDITIONAL_PASS)

## Phase 5 Status
- 5.1 Input Discovery: COMPLETE
- 5.2 Team Setup: COMPLETE
- 5.3 DA Spawn: COMPLETE
- 5.4 Challenge Execution: COMPLETE (21 challenges, 6/6 categories)
- 5.5 Gate 5: APPROVED (CONDITIONAL_PASS accepted)

## Gate 5 Condition
- C-2.2: Restore 4 lost v5.1 behaviors (~4 lines) during Phase 6 T2 (CLAUDE.md)

## Deliverables
```
.agent/teams/nlp-validation/
├── orchestration-plan.md (this file)
├── global-context.md (GC-v4 copy)
├── TEAM-MEMORY.md
└── phase-5/
    ├── gate-record.yaml
    └── devils-advocate-1/
        ├── L1-index.yaml
        ├── L2-summary.md
        └── L3-full/challenge-report.md
```
