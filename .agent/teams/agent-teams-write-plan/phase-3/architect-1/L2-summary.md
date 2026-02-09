# L2 Summary — agent-teams-write-plan Architecture

> Phase 3 | architect-1 | 2026-02-07

## Overview

`agent-teams-write-plan` is a Phase 4 (Detailed Design) custom skill that bridges brainstorming-pipeline (Phase 1-3) output to a concrete implementation plan. It spawns a DIA-verified architect teammate to produce a 10-section plan following the CH-001 format.

## Architecture Narrative

### Input → Processing → Output

**Input:** brainstorming-pipeline artifacts — GC-v3 (with Phase 3 COMPLETE), architecture-design.md, researcher L2 summaries. Discovered via hybrid auto-discovery (Dynamic Context Injection scan + $ARGUMENTS) with user confirmation.

**Processing:** Lead orchestrates a single architect teammate through:
1. Input validation (3 checks: GC-v3 exists, architecture exists, required sections present)
2. Team setup (TeamCreate, copy GC-v3, orchestration-plan)
3. DIA verification (TIER 2 + LDAP MAXIMUM: 3Q + alternative demand)
4. Plan generation (architect reads codebase + produces 10-section plan)
5. Gate 4 evaluation (8 criteria including Q2 compensating mechanisms)
6. GC-v3 → GC-v4 update (6 new sections, 2 updated, rest preserved)

**Output:** Implementation plan dual-saved to `docs/plans/` + `.agent/teams/` L1/L2/L3, plus GC-v4.

### Key Trade-offs

**1. Architect vs Lead as plan author (AD-1)**
Chose architect for: DIA verification, Delegate Mode compliance, context separation, CLAUDE.md §2 alignment. Trade-off: ~15K tokens DIA overhead. Justified by Shift-Left principle (70-80% pre-execution investment).

**2. 10-section template from single precedent (AD-2)**
CH-001 is sample size 1. Mitigated by designing all sections as parametric (variable content with fixed structure). The template accommodates single-implementer (CH-001 style) and multi-implementer scenarios.

**3. Verification Level tags (AD-3) + AC-0 (AD-4) + V6 (AD-5)**
These three mechanisms compensate for architect's inability to run code (no Bash/Edit tools):
- Verification Level: Signals confidence per code block (READ_VERIFIED > PATTERN_BASED > DESIGN_ONLY)
- AC-0: Every task starts with implementer verifying plan vs reality
- V6: Validation checklist includes code plausibility checks

**4. 4-layer task-context (AD-7)**
Solves Phase 3→4 architect discontinuity: GC-v3 (compressed decisions) + L2-summary (narrative inline) + L3 path (reference for Read) + CH-001 (format exemplar). CIP guarantees delivery, DIAVP verifies understanding, LDAP verifies systemic reasoning.

### Writing-Plans Principle Preservation

All 6 core principles from the original writing-plans skill are preserved with Agent Teams adaptations:

| Principle | Solo Form | Agent Teams Form |
|-----------|-----------|-----------------|
| DRY/YAGNI/TDD | Direct instruction | §6 Test Strategy + §4 acceptance criteria |
| Exact file paths | In step descriptions | In §5 Change Specifications (line-level) |
| Complete code | In step code blocks | In §5 with Verification Level tags |
| Bite-sized tasks | 2-5 min steps | TaskCreate with bounded scope + AC |
| Frequent commits | Per-step commits | §8 Commit Strategy (single or per-task) |
| Saved to docs/plans/ | Single location | Dual-save: docs/plans/ + .agent/teams/ |

### GC Version Continuity

```
brainstorming-pipeline:  GC-v1 (P1) → GC-v2 (P2) → GC-v3 (P3)
agent-teams-write-plan:  GC-v3 (input) → GC-v4 (output)
```

GC-v4 adds 6 sections (Implementation Plan Reference, Task Decomposition, File Ownership Map, Phase 6 Entry Conditions, Phase 5 Validation Targets, Commit Strategy), updates 2 (Pipeline Status, Decisions Log), preserves all GC-v3 sections.

## Q2 Compensating Mechanisms (LDAP Defense → Design)

The LDAP Q2 challenge identified architect tool limitations affecting §5 accuracy. Four compensating mechanisms were designed and integrated:

1. **Verification Level tags** → §5 Change Specifications (every spec tagged)
2. **V6 Code Plausibility** → §7 Validation Checklist (new 6th category, mandatory)
3. **AC-0 Plan Verification Step** → §4 TaskCreate Definitions (every task, mandatory)
4. **Read-First-Write-Second** → task-context architect instructions

These propagate through Gate 4 criteria (G4-5, G4-6, G4-7) ensuring enforcement.

## Phase 4 Readiness Assessment

**Ready for implementation.** Design produces:
- 1 new file: `.claude/skills/agent-teams-write-plan/SKILL.md`
- 1 design document: `docs/plans/2026-02-07-agent-teams-write-plan-design.md`
- 0 existing files modified

**Dependencies satisfied:**
- brainstorming-pipeline SKILL.md exists (precedent pattern)
- brainstorming-pipeline design doc exists (precedent structure)
- CH-001 implementation plan exists (template exemplar)
- CLAUDE.md v3.0 with DIA + LDAP exists (protocol infrastructure)
- Architect agent definition exists with correct tool restrictions

**Risks mitigated:**
- R-1 (single precedent): Parametric template design
- R-2 (context continuity): 4-layer injection + CIP + DIAVP + LDAP
- R-3 (code accuracy): Verification Level + AC-0 + V6
- R-4 (Phase 5 rework): Pipeline ordering + GC versioning + Clean Termination
