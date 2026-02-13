# Phase 6 Context — Skill Optimization v9.0

## PT Reference
- PT-ID: Task #1 (PT-v2) — use TaskGet to read full context
- Feature: Skill Optimization v9.0 — 22 files, Big Bang atomic change

## Implementation Plan
- Full plan: `docs/plans/2026-02-12-skill-optimization-v9-implementation.md` (630L)
- Per-file specs (L3): `.agent/teams/skill-opt-v9/phase-4/decomposition-planner-1/L3-full/section-5-specs.md` (737L)
- Interface contracts (L3): `.agent/teams/skill-opt-v9/phase-4/interface-planner-1/L3-full/interface-design.md` (541L)

## Phase 5 Mandatory Conditions (ACCEPTED)
1. **CONS-1:** RISK-8 fallback — interface-planner L3 §1.2 is authoritative for exact text
2. **CONS-2:** impl-b — L1 checkpoint after EACH file, split contingency
3. **CONS-3:** infra-c — L1 checkpoint every 2-3 files, monitor first
4. **CONS-4:** §10/protocol — interface-planner L3 §2 authoritative, §10=REPLACE, protocol=APPEND

## Task Assignments
| Task | Owner | Agent Type | Files | Task ID |
|------|-------|-----------|:-----:|:-------:|
| D | infra-d | infra-implementer | 2 | #1 |
| A1 | impl-a1 | implementer | 4 | #2 |
| A2 | impl-a2 | implementer | 3 | #3 |
| B | impl-b | implementer | 5 | #4 |
| C | infra-c | infra-implementer | 8 | #5 |
| V | verifier | integrator | 0→22 | #6 (blocked by #1-5) |

## Review Protocol
- Stage 1: spec-reviewer (spec compliance check)
- Stage 2: code-reviewer (quality + architecture)
- COMPLEX extras: contract-reviewer (C-1~C-6 contracts), regression-reviewer (existing functionality)
- Fix loop: max 3 per stage, escalate to Lead on exhaustion

## Monitoring Priority
1. infra-c (8 files, BUG-002 risk) — check FIRST
2. impl-b (5 files, CONS-2 checkpointing)
3. impl-a1, impl-a2, infra-d (smaller scope)
