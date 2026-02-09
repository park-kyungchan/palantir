# L2 Summary — Task A: /rsil-global SKILL.md

## Overview

Created `.claude/skills/rsil-global/SKILL.md` (452 lines) — the auto-invoked INFRA
Meta-Cognition health assessment skill. This is the lightweight counterpart to
/rsil-review: where rsil-review performs deep targeted analysis (~561L, 2 agent spawns),
rsil-global performs broad surface-level health checks (~452L, agents only at Tier 3).

## Implementation Decisions

### D1: G-0 Mixed Case Handling (Lead Q1 — I-2 MEDIUM)

The plan specifies "fallback to Type A" when classification is uncertain. For the
specific edge case of mixed signals (pipeline artifacts + direct .claude/ edits in
the same session), I added an explicit "Mixed signals" paragraph in G-0 Classification
Rules that:

1. Names the mixed case explicitly (not just generic "uncertain" fallback)
2. Explains WHY Type A subsumes it (most comprehensive reading scope)
3. Notes the .claude/ edits as "additional context for G-1 lens application"

This is a VL-2 section, so adding 3 lines of clarification is within scope. The
behavior matches the plan exactly — Type A fallback — but the skill is now
self-documenting about this known edge case.

### D2: Section Ordering

Chose: phases first (G-0→G-4), then Shared Foundation as reference appendix. This
differs from rsil-review (which puts Static Layers before phases) but matches the
plan's A1-A15 ordering and makes sense because:
- rsil-review's R-0 CONSTRUCTS directives from Static Layers (needs them before phases)
- rsil-global's G-1 APPLIES lenses during reading (references them, doesn't construct from them)

### D3: Never Section

Added 9 "Never" items (plan specified principles only). Modeled after rsil-review's
"Never" section pattern. Items are specific to rsil-global's constraints:
- No file modification without approval
- No auto-chaining
- No hooks (AD-15)
- No agent spawns at Tier 1/2
- No application code assessment

### D4: Line Budget Allocation

| Section | Lines | % |
|---------|-------|---|
| Frontmatter + Intro (A1-A2) | 17 | 4% |
| When to Use + Dynamic Context (A3-A4) | 44 | 10% |
| Phase 0 (A5) | 27 | 6% |
| G-0 Classification (A6) | 42 | 9% |
| G-1 Tiered Reading (A7) | 98 | 22% |
| G-2 Discovery (A8) | 27 | 6% |
| G-3 Classification (A9) | 53 | 12% |
| G-4 Record (A10) | 49 | 11% |
| Error Handling (A11) | 12 | 3% |
| Shared Foundation (A12-A14) | 43 | 10% |
| Principles + Never (A15) | 24 | 5% |
| Separators | 16 | 3% |
| **Total** | **452** | **100%** |

G-1 (VL-3) is correctly the largest section at 22%, reflecting its role as the
creative centerpiece.

## Verification Results

- **Line count:** 452 (within 400-500 target)
- **15/15 spec sections:** All present with correct VL levels
- **Shared Foundation verbatim:** 3/3 PASS (Lenses table, AD-15, Boundary Test)
- **Intentional Lenses intro diff:** Confirmed ("G-1/observation window" vs "R-0/$ARGUMENTS")
- **Skill auto-registered:** Confirmed in Claude Code skill listing after file creation

## Artifacts

- Created: `.claude/skills/rsil-global/SKILL.md` (452L)
- L3 full detail: The created skill file itself serves as L3
