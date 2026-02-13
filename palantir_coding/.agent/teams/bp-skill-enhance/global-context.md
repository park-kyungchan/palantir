---
version: GC-v3
created: 2026-02-12
feature: brainstorming-pipeline-quality-enhancement
complexity: STANDARD
---

# Global Context — brainstorming-pipeline P0/P1 Flow Redesign

## Scope

**Goal:** Redesign brainstorming-pipeline P0/P1 flow to fix 8 identified issues, reducing SKILL.md from 672L to ~578L.
**In Scope:**
- Phase 0 simplification (PT existence check only)
- Feasibility Check gate in Q&A (after PURPOSE)
- Checkpoint relocation (1.3.5 → 1.2.5)
- Scope + Tier unification at 1.4
- PT creation at Gate 1 via /permanent-tasks
- Sequential-thinking consolidation (9 inline → 1 cross-cutting)
- Dynamic Context git branch capping
- RTD Decision Points reduction (7 → 3)

**Out of Scope:**
- Phase 2/3 logic changes (only sequential-thinking inline removal)
- Clean Termination section changes
- GC structure changes (downstream compatibility)
- /permanent-tasks skill modifications

**Approach:** Structural flow redesign with 8 Architecture Decisions (AD-1 through AD-8)
**Success Criteria:**
- All 8 issues (H1-H3, M1, L1-L3) resolved
- Line count ≤ 578L (from 672L)
- Downstream skill compatibility preserved

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: COMPLETE (Gate 2 APPROVED)
- Phase 3: COMPLETE (Gate 3 APPROVED)

## Research Findings

### D1: GC Downstream Dependencies
GC serves 3 roles across 5 downstream skills: (1) Phase completion gating, (2) Session/artifact discovery, (3) Rich context carrier. PT can substitute for roles 1+2 but NOT role 3. write-plan embeds full GC-v3 (line 166). GC structure must persist.

### D2: PT Creation Interface
/permanent-tasks is standalone — takes $ARGUMENTS + conversation context, produces 5-section PT template. No Phase-0-specific dependency. Can be invoked at Gate 1 without modification. All downstream skills handle "PT found" gracefully.

### D3: Hook GC References
Hook reads only version: frontmatter field (line 55). PT fallback already exists (lines 67-74). Zero downstream parsers for the injected "Current GC: GC-v{N}" string. No modification needed.

## Codebase Constraints
- write-plan skill embeds FULL GC-v3 in architect directive (line 166) — GC context carrier role must persist
- Hook injected version string is purely informational — no agent/skill parses it
- M2 (GC-PT overlap) downgraded to LOW — GC is valid mechanism, not redundancy

## Architecture Summary

8 Architecture Decisions redesigning P0/P1 flow:

| AD | Decision | Impact |
|----|----------|--------|
| AD-1 | P0 → PT existence check only | -37L |
| AD-2 | Feasibility Check (3-criteria soft gate after PURPOSE) | +15L |
| AD-3 | Checkpoint moved to 1.2.5 | -5L (net with deletion of 1.3.5) |
| AD-4 | Scope + Tier unified at 1.4 | +3L |
| AD-5 | Gate 1 PT creation sequence | +10L |
| AD-6 | Sequential-thinking consolidation (9→1) | -21L |
| AD-7 | Dynamic Context git branch cap (head -10) | -3L |
| AD-8 | RTD DPs reduced (7→3) | -8L |

Line budget: 672L → ~578L (net -94L)

## Architecture Decisions
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| AD-1 | P0 becomes PT existence check only | PT creation at P0 wastes cycles when user pivots topics | P1 |
| AD-2 | Feasibility Check after PURPOSE | 2 invalid topics before a real one in live session | P1 |
| AD-3 | Checkpoint moved to 1.2.5 | Q&A context lost on compact when checkpoint at 1.3.5 | P1 |
| AD-4 | Scope + Tier unified at 1.4 | Tier at P0 is premature — scope unknown | P1 |
| AD-5 | PT creation at Gate 1 | Full context available; richer initial PT | P1 |
| AD-6 | Sequential-thinking consolidated | 9 scattered reminders → 1 cross-cutting instruction | P3 |
| AD-7 | Git branch output capped | 35+ branches waste tokens | P3 |
| AD-8 | RTD DPs reduced 7→3 | Only gate transitions are meaningful DPs | P3 |

## Constraints
- Phase 2/3 logic unchanged (only sequential-thinking inline removal)
- Clean Termination section unchanged
- GC structure must persist for downstream compatibility
- /permanent-tasks invocation at Gate 1 uses existing interface

## Phase 4 Entry Requirements
- Implement all 8 ADs in brainstorming-pipeline/SKILL.md
- Preserve Phase 2/3 logic (only remove inline sequential-thinking reminders)
- Maintain GC-v1 creation structure at Gate 1 (add PT creation before it)
- Target ~578L final line count
- Verify downstream compatibility (GC structure, /permanent-tasks interface)
