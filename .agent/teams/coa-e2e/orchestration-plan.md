---
feature: coa-e2e-integration
current_phase: 2
gc_version: GC-v1
---

# Orchestration Plan — COA E2E Integration

## Gate History
- Phase 1: APPROVED (2026-02-08) — 7 GAPs identified, Option B approach, Scope Statement confirmed

## Active Teammates
| Name | Type | Mode | Status | Domain | GC Version |
|------|------|------|--------|--------|------------|
| researcher-protocol | researcher | default | EXECUTING (DIA VERIFIED) | COA-1~5 | GC-v1 |
| researcher-code-audit | researcher | default | EXECUTING (DIA VERIFIED) | COA-6~7 | GC-v1 |

## Terminated Teammates
(none)

## Phase 2 Plan
- Research domains: 2 (parallel, independent)
  - researcher-protocol: COA-1~5 (protocol design)
  - researcher-code-audit: COA-6~7 (code audit + hook fixes)
- Strategy: Parallel spawn, independent execution, L3 completeness mandated

## Spawn Rules
- All teammates: mode: "default" (BUG-001 workaround)
- Max 3 teammates at any time
- Pre-Spawn Checklist: Gate S-1/S-2/S-3 mandatory
- L3-full/ completeness mandated (D-3)

## File Ownership Map
### Workstream A: Protocol Research (researcher-protocol)
- Read-only: CLAUDE.md, task-api-guideline.md, all agent .md, all skill SKILL.md
- Output: .agent/teams/coa-e2e/phase-2/researcher-protocol/L1,L2,L3

### Workstream B: Code Audit (researcher-code-audit)
- Read-only: all hook scripts, CLAUDE.md, settings.json, audit doc, MEMORY.md, bugs.md
- Output: .agent/teams/coa-e2e/phase-2/researcher-code-audit/L1,L2,L3

## Key Decisions
| # | Decision | GC Version |
|---|----------|------------|
| D-1 | Option B: Parallel Domain Split | GC-v1 |
| D-2 | Lead Meta-Cognition Obligation (MEMORY + seq-thinking) | GC-v1 |
| D-3 | L3 completeness mandate for researchers | GC-v1 |

## Iteration Budget
- Max 3 iterations per teammate per task
- On exceeded: ABORT teammate, re-spawn with enhanced context
