---
feature: skl006-delivery-pipeline
current_phase: "6 — Implementation"
gc_version: GC-v4
skill: /agent-teams-execution-plan
---

# Orchestration Plan — Phase 6

## Gate History
- Phase 1: APPROVED (2026-02-08) — in skl006-delivery/
- Phase 2: APPROVED (2026-02-08) — in skl006-delivery/
- Phase 3: APPROVED (2026-02-08) — in skl006-delivery/
- Phase 4: APPROVED (2026-02-08) — in skl006-write-plan/
- Phase 5: APPROVED (2026-02-08) — in skl006-validation/ (CONDITIONAL_PASS)

## Active Teammates
| Name | Role | Status | PT Version | Current Task |
|------|------|--------|------------|--------------|
| impl-A | implementer | WORKING | PT-v5 (embedded) | T-1: SKILL.md creation |
| impl-B | implementer | WORKING | PT-v5 (embedded) | T-2: Hook reduction 8→3 |

## Understanding Verification
- impl-A: PASSED (2 probing Qs — multi-session discovery fallback, post-rejection recovery)
- impl-B: PASSED (2 probing Qs — JSON edit strategy, H-2 path resolution)

## Phase 6 Objectives
1. impl-A: Create delivery-pipeline SKILL.md (T-1)
2. impl-B: Hook reduction 8→3 (T-2), Hook NLP (T-3+H-2), NL-MIGRATE (T-4+H-1), MEMORY templates (T-5)
3. Lead: Cross-workstream validation (T-6)

## Key Inputs
- PT: Task #3 (PT-v5)
- GC-v4: .agent/teams/skl006-delivery/global-context.md
- Implementation Plan: docs/plans/2026-02-08-skl006-delivery-pipeline.md
- Phase 5 Mitigations: H-1 (CLAUDE.md 160/172), H-2 (on-pre-compact.sh WARNING)

## Dependency Graph
T-1 ─────────────────────────→ T-6
T-2 → T-4 ──────────────────→ T-6
T-3 ─────────────────────────→ T-6
T-5 ─────────────────────────→ T-6
