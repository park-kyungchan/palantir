---
version: GC-v6
created: 2026-02-09
feature: rsil-system
complexity: COMPLEX
---

# Global Context — RSIL System (Global + Narrow Refinement)

## Scope

**Goal:** INFRA Meta-Cognition 자가개선 시스템 구축 — /rsil-global (NEW) + /rsil-review (REFINE)

**In Scope:**
1. /rsil-global (NEW, ~400-500L) — Lead auto-invoked, Three-Tier Observation Window, ~2000 token budget
2. /rsil-review REFINEMENT (561L → ~551L) — 5 deltas: ultrathink, wc-l, agent memory, principles merge, output simplify
3. Shared Foundation — 8 Lenses + AD-15 + Boundary Test (~85L embedded copy per skill)
4. CLAUDE.md Integration — 5-line NL discipline after §2 Phase Pipeline table
5. Agent Memory — ~/.claude/agent-memory/rsil/MEMORY.md (4-section schema with seed data)
6. Tracker Migration — unified tracker with G-{N}/P-R{N} namespacing

**Out of Scope:**
- Hook additions (AD-15: 8→3)
- Layer 2 (Ontology Framework)
- Application code review
- Existing 7 pipeline skill modifications
- Cross-session trend analysis (Layer 2 gap)

**Success Criteria:**
- /rsil-global skill auto-invocable via Lead NL discipline
- Three-Tier Reading prevents context explosion (~2000 token budget)
- /rsil-review 5 deltas applied (-10L net)
- Clear role separation between skills
- AD-15 (3 hooks) maintained
- Agent memory enables cross-session learning

**Estimated Complexity:** COMPLEX

## Component Map

| ID | Component | Files | Status |
|----|-----------|-------|--------|
| C-1 | /rsil-global Complete Flow (G-0→G-4) | .claude/skills/rsil-global/SKILL.md (NEW) | Design complete |
| C-2 | /rsil-review Refinement (5 deltas) | .claude/skills/rsil-review/SKILL.md (MODIFY) | Design complete |
| C-3 | Shared Foundation | Embedded in C-1 and C-2 (~85L each) | Design complete |
| C-4 | CLAUDE.md Integration | .claude/CLAUDE.md (MODIFY) | Design complete |
| C-5 | Agent Memory Schema | ~/.claude/agent-memory/rsil/MEMORY.md (NEW) | Design complete |
| C-6 | Tracker Migration | docs/plans/2026-02-08-narrow-rsil-tracker.md (MODIFY) | Design complete |

## Interface Contracts

| Interface | From | To | Contract |
|-----------|------|----|----------|
| Shared Foundation | C-3 | C-1, C-2 | 8 Lenses + AD-15 + Boundary Test = identical text (~85L) |
| Agent Memory R/W | C-5 | C-1, C-2 | Read: dynamic context head -50; Write: R-4/G-4 Read-Merge-Write |
| Tracker Namespacing | C-6 | C-1, C-2 | G-{N} (global) vs P-R{N} (narrow), cross_refs/promoted_to/decomposed_to |
| NL Discipline | C-4 | C-1 | CLAUDE.md §2 instruction triggers Lead to invoke /rsil-global |
| Cross-Reference | C-1 | C-2 | Global finding decomposed_to narrow; narrow promoted_to global (≥3 reviews) |

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED 2026-02-09)
- Phase 2: COMPLETE (Gate 2 APPROVED 2026-02-09)
- Phase 3: COMPLETE (Gate 3 APPROVED 2026-02-09)
- Phase 4: COMPLETE (Gate 4 APPROVED 2026-02-09)
- Phase 5: COMPLETE (Gate 5 APPROVED 2026-02-09, Verdict: CONDITIONAL_PASS)
- Phase 6: COMPLETE (Gate 6 APPROVED 2026-02-09)

## Constraints
- AD-15: 8→3 hooks inviolable (no new hooks)
- Layer 1 boundary only (Opus 4.6 + Agent Teams + CC CLI)
- NL discipline for auto-invocation (no hook-based triggers)
- Findings-only output (user approves before application)
- INFRA scope only (not application code)
- Context budget: ~2000 tokens for /rsil-global observation window

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | /rsil-global = Lead NL auto-invoke | AD-15 compatible, no hook needed | P1 |
| D-2 | Three-Tier + parallel agent discovery | Context efficiency + INFRA boundary discovery | P1 |
| D-3 | Immediate Cat B application (propose, not auto-apply) | User present, approval fast | P1 |
| D-4 | Shared Foundation architecture | Both skills share Lenses/AD-15 but independent | P1 |
| D-5 | /rsil-review also refined | Feasibility research improvements applicable | P1 |
| AD-6 | Findings-only output (no auto-apply) | Safety > speed for INFRA changes | P3 |
| AD-7 | Three-Tier per work type (adaptive A/B/C) | Uniform strategy wastes tokens on nonexistent artifacts | P3 |
| AD-8 | BREAK escalation via AskUserQuestion | User present in auto-invoke context | P3 |
| AD-9 | Tracker section isolation + ID namespacing | G-{N} vs P-R{N}; sequential consistency | P3 |
| AD-10 | Shared Foundation = embedded copy | 85L stable; no external dependency | P3 |
| AD-11 | Single shared agent memory | Patterns universal; separation fragments learning | P3 |

## Implementation Plan Reference
- Plan: docs/plans/2026-02-09-rsil-system.md (1231L, 10 sections)
- Tasks: 4 (A: rsil-global, B: rsil-review+CLAUDE.md, C: agent-memory+tracker, D: integration)
- Implementers: 2, zero file overlap
- Specs: 26 (A1-A15, B1-B7, C1-C4) with VL tags
- Plan decisions: PD-1 verbatim Foundation, PD-2 head-50, PD-3 interface by construction, PD-4 VL-3 scoping

## File Ownership Map
- implementer-1: .claude/skills/rsil-global/SKILL.md (NEW, ~400-500L)
- implementer-2: .claude/skills/rsil-review/SKILL.md (MODIFY), .claude/CLAUDE.md (MODIFY), ~/.claude/agent-memory/rsil/MEMORY.md (NEW), docs/plans/2026-02-08-narrow-rsil-tracker.md (MODIFY)

## Phase 6 Implementation Results
- Tasks: 4/4 complete (A, B, C, D)
- Implementers: 2 parallel, zero file overlap maintained
- Files created: .claude/skills/rsil-global/SKILL.md (452L), ~/.claude/agent-memory/rsil/MEMORY.md (53L)
- Files modified: .claude/skills/rsil-review/SKILL.md (549L), .claude/CLAUDE.md (178L), tracker (283L)
- Integration: 7/7 cross-file checks PASS (automated diff for Shared Foundation)
- Session: .agent/teams/rsil-execution/

## Phase 5 Validation Results
- Verdict: CONDITIONAL_PASS (0 CRITICAL, 1 HIGH, 6 MEDIUM, 7 LOW)
- HIGH: I-1 Shared Foundation transcription risk (mitigation: automated diff in Task D)
- Conditions accepted: automated diff for Foundation, git diff in Type A Tier 1, seed data "estimated" label
- Challenge report: .agent/teams/rsil-validation/phase-5/devils-advocate-1/L3-full/challenge-report.md (592L)
- All 7 challenge targets + 5 assumptions validated
- Session: .agent/teams/rsil-validation/
