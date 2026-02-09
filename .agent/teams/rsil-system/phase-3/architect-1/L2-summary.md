# L2 Summary — RSIL System Architecture

**architect-1 | Phase 3 | rsil-system | 2026-02-09**

---

## Executive Summary

The RSIL System architecture defines two independent skills sharing a stable foundation:
**/rsil-global** (NEW, ~400-500L) for lightweight auto-invoked INFRA health assessment, and
**/rsil-review** (REFINED, 561→~551L) for deep user-invoked component analysis. Both share
the 8 Meta-Research Lenses, AD-15 Filter, and Layer 1/2 Boundary Test as embedded copies.
A unified tracker with ID namespacing (G-{N} vs P-R{N}) and shared agent memory enable
cross-session cumulative learning.

Six architecture decisions (AD-6~AD-11) extend Phase 1 decisions (D-1~D-5). The key
architectural innovation is the **Three-Tier Observation Window** that adapts data sources
per work type (A=pipeline, B=skill, C=direct edit) while maintaining fixed context budgets.

---

## Architecture Narrative

### The Two-Skill System

The fundamental insight is that **breadth and depth require different architectures.**
/rsil-global discovers what to look at (observation-first, Three-Tier escalation, ~2000
token budget). /rsil-review knows what to look at and goes deep (synthesis-first, full
target read, parallel agent research). Merging them would force a single skill to support
both lightweight scanning and heavy analysis — branching complexity without benefit.

The Shared Foundation (8 Lenses, AD-15, Boundary Test) is stable infrastructure (~85 lines)
that changes only when a new Lens is discovered. Embedding identical copies in both skills
eliminates external dependency while keeping each skill self-contained.

### Three-Tier Observation Window

The core /rsil-global architecture. Tier 0 (Dynamic Context shell commands, ~100 tokens)
classifies work type and identifies observation targets. Tier 1 (~500 tokens) reads the
highest-signal artifacts: gate records for pipeline work, git diffs for non-pipeline work.
Tier 2 (~1000 tokens) selectively reads L2/TEAM-MEMORY only for flagged areas. Tier 3
(Explore subagent, separate context) activates only when Tier 2 reveals systemic anomalies.

**Critical design property:** Most runs terminate at Tier 1 with zero findings. The system
is designed for the common case (healthy INFRA) while having escalation paths for anomalies.

### Findings-Only Output (AD-6)

Despite D-3 ("Immediate Cat B application"), the architecture enforces user approval for
ALL changes. "Immediate" means Lead proposes immediately upon discovery, not auto-applies.
The user is always present (just completed work in the same session). BREAK findings
escalate via AskUserQuestion; all others are presented in a summary for user decision.

### Cumulative Learning Loop

```
Work → /rsil-global (reads memory) → findings → tracker + memory
                                                       ↓
            user invokes /rsil-review (reads memory) → findings → tracker + memory
                                                                        ↓
                                                               next /rsil-global
                                                               (informed by all
                                                                previous findings)
```

Agent memory serves as the cross-session learning substrate. Both skills read it at
startup (dynamic context injection, first 50 lines) and write at completion (Read-Merge-Write).
The tracker is the permanent audit trail; agent memory is the distilled working knowledge.

---

## Key Decisions and Trade-offs

### AD-6: No Auto-Apply
**Trade-off:** Slower feedback loop (user must approve) vs. safety (no unintended changes).
**Resolution:** User is present → approval is fast. Safety >> speed for INFRA changes.

### AD-7: Adaptive Three-Tier
**Trade-off:** Complexity (3 work types × 4 tiers) vs. uniform strategy.
**Resolution:** Uniform strategy wastes tokens on nonexistent artifacts for Type B/C.
The complexity is encapsulated in G-0 classification; subsequent phases are type-aware
but structurally identical.

### AD-10: Embedded Copy vs. Shared Reference
**Trade-off:** Duplication (~85 lines in each skill) vs. single source of truth.
**Resolution:** 85 lines is a small cost for full independence. The shared elements change
only when new Lenses are added (rare). A shared reference file creates fragile coupling.

### AD-11: Shared vs. Separate Memory
**Trade-off:** Shared memory risks write conflicts vs. separate memories fragment learning.
**Resolution:** Sequential execution (global then review) eliminates write conflicts.
Patterns discovered by either skill benefit the other's synthesis phase.

---

## /rsil-review Refinement Summary

Five targeted deltas totaling -10 lines (561→~551):

1. **Ultrathink** (Delta 1): keyword in intro paragraph. Enables extended thinking budget.
2. **File size pre-check** (Delta 2): `wc -l $ARGUMENTS` in Dynamic Context. Helps R-0 planning.
3. **Agent memory integration** (Delta 3): Read at skill load (+1L Dynamic Context), write
   at R-4 (+7L instructions). Closes the cross-session learning loop.
4. **Principles merge** (Delta 4): 21 items (Key Principles + Never) → 11 items (-14L).
   Positive-form statements that incorporate prohibitions.
5. **Output format simplify** (Delta 5): Nested templates → structured guidance (-5L).
   Opus 4.6 follows guidance reliably without exact format prescription.

All deltas are independently applicable (no ordering dependency).

---

## CLAUDE.md Integration

Five-line NL discipline instruction inserted after §2 Phase Pipeline table:

> After completing pipeline delivery (Phase 9) or committing .claude/ infrastructure
> changes, Lead invokes /rsil-global for INFRA health assessment. Skip for trivial
> single-file edits (typo fixes), non-.claude/ changes, or read-only sessions.
> The review is lightweight (~2000 token observation budget) and presents findings
> for user approval before any changes are applied.

Measured tone. Clear invoke/skip criteria. No mechanical enforcement — NL discipline
is a conscious Lead choice reinforced by agent memory staleness tracking.

---

## Risk Assessment

Seven risks identified. Highest scores (4/9):
- **R-2 (context overrun):** Mitigated by 3-L1-file cap
- **R-3 (NL non-compliance):** Mitigated by CLAUDE.md instruction + memory staleness
- **R-5 (memory limit):** Mitigated by budget allocation + universality filter
- **R-7 (noise):** Mitigated by tier gates + AD-15 + acceptance rate self-correction

No HIGH-impact risks. All mitigations are Layer 1 (NL + existing infrastructure).

---

## Phase 4 Readiness

Architecture provides:
- Complete /rsil-global flow specification (G-0→G-4 with all decision points)
- Exact /rsil-review delta specifications (5 changes with line references)
- Precise CLAUDE.md insertion text (5 lines)
- Agent memory seed content (ready to create)
- Tracker migration strategy (add Global section + extended schema)
- Recommended implementation split: 2 implementers, zero file overlap

Phase 4 needs to produce: exact SKILL.md text for /rsil-global, exact change specs
for all other files, and implementation task breakdown with file ownership.

---

## Evidence Sources

| Source | Used For |
|--------|----------|
| researcher-1 L1/L2 (OW-1~6, TA-1~5) | Three-Tier architecture, tracker schema, health indicators |
| researcher-2 L1/L2 (IMP-1~9, MEM-1~3) | /rsil-review deltas, agent memory schema |
| /rsil-review SKILL.md (561L) | Existing architecture, shared foundation text |
| CLAUDE.md (172L) | Integration point, constraint verification |
| narrow-rsil-tracker.md (254L) | Current tracker schema, seed data |
| GC-v2 (83L) | Constraints, decisions D-1~D-5 |
| agent-common-protocol.md (89L) | Agent memory section, completion protocol |
| Architect agent memory | Previous design patterns (embedded copy, YAGNI) |
