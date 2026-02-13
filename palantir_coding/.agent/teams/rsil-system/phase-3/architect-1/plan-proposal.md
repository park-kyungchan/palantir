# Phase 3 Architecture Plan Proposal — architect-1

**Date:** 2026-02-09
**Task:** RSIL System Architecture (Task #3)

---

## Probing Question Responses

### Q1: Three-Tier Graceful Degradation by Work Type

The key is that **Tier 0 classifies work type FIRST**, then subsequent tiers adapt their data sources. Evidence: researcher-1 L2 §1.2 (OW-2) defines three detection patterns, and §1.3 (OW-3) shows Tier 0 shell injection outputs "Work type classification (A/B/C) + session identification."

**Type A (Pipeline with session dir):**

| Tier | What to Read | Budget | Escalation Trigger |
|------|-------------|--------|-------------------|
| 0 | `ls -d .agent/teams/*/`, gate count, L1 count, git diff count | ~100 tok | Always → Tier 1 |
| 1 | Latest gate-record.yaml + latest L1-index.yaml + orchestration-plan tail | ~500 tok | ≥1 FAIL in gate, ≥2 HIGH unresolved, or re-spawn detected |
| 2 | L2-summary.md for flagged areas + TEAM-MEMORY.md warning density | ~1000 tok | ≥3 cross-file anomalies, or ≥2 BREAK severity |
| 3 | Explore subagent for systemic cross-file investigation | Separate ctx | Terminal |

**Type B (Skill-only — /rsil-review, /permanent-tasks, no session dir):**

| Tier | What to Read | Budget | Escalation Trigger |
|------|-------------|--------|-------------------|
| 0 | git diff --name-only (.claude/ changes), confirm no session dir | ~100 tok | Always → Tier 1 |
| 1 | `git diff HEAD~1` content for .claude/ files + tracker diff | ~500 tok | ≥1 cross-file inconsistency, or modified files reference unreflected files |
| 2 | Read modified files + their reference targets for consistency | ~1000 tok | Changes span ≥3 files with bidirectional references |
| 3 | Explore subagent for reference graph validation | Separate ctx | Terminal |

**Type C (Direct Lead edit — manual CLAUDE.md fix, MEMORY.md update):**

| Tier | What to Read | Budget | Escalation Trigger |
|------|-------------|--------|-------------------|
| 0 | git diff --name-only (specific .md), confirm no session dir/skill trace | ~100 tok | Always → Tier 1 |
| 1 | `git diff HEAD~1` content + MEMORY.md diff | ~500 tok | Modified file has ≥2 unreflected downstream references |
| 2 | Read referenced files to verify consistency | ~1000 tok | Stale references detected |
| 3 | Explore subagent (unlikely for Type C) | Separate ctx | Terminal |

**Key insight:** For Type B/C, `git diff` content replaces gate records as primary signal. Budget and escalation logic are preserved; only data sources change. Most B/C runs terminate at Tier 1 (localized changes).

Evidence: researcher-1 L2 §1.2, §1.3

---

### Q2: BREAK Escalation Path Under Auto-Invoke

Tension: D-3 ("Immediate Cat B application") vs GC-v2 constraint ("Findings-only output, user approves before application").

Resolution: **"Immediate" = Lead proposes for immediate action, NOT auto-applies.** /rsil-global is not a background daemon — it runs in the same session where the user just completed work. User is present.

```
Finding discovered
      │
  ┌───┴───┐
  BREAK   FIX / WARN / DEFER
  │       │
  ▼       ▼
AskUser   Record to tracker + memory.
"RSIL Global found {N}    Present summary.
 BREAK-severity issues.   User decides.
 Fix now or defer?"
  │
┌─┴─┐
Fix  Defer
│    │
▼    ▼
Lead applies    Record with BREAK priority.
(user present)  Flag in agent-memory §3
                for next-session attention.
```

**Session termination edge case:** Findings persist in tracker + agent memory BEFORE presentation. Next session, Tier 0 re-detects unfixed BREAKs. Self-healing through persistence.

Evidence: /rsil-review SKILL.md line 546, GC-v2 line 50

---

### Q3: Sequential Tracker Consistency

Three structural guarantees for sequential /rsil-global → /rsil-review in same session:

1. **ID Namespacing:** G-{N} (global) vs {Phase}-R{N} (narrow). Zero collision. (researcher-1 L2 §2.2)
2. **Section Isolation:** Global findings → "Global Findings" subsection. Narrow → sprint-specific subsection. Different file regions.
3. **Read-Merge-Write:** Second skill reads first's additions before writing. Sequential = monotonic.

**§4 Cross-Cutting Patterns (shared section):** Both skills propose pattern candidates via Read-Merge-Write. Sequential ordering prevents conflict. /rsil-global naturally runs first (post-delivery auto-invoke), /rsil-review later (user-invoked).

Evidence: researcher-1 L2 §2.5 (source_skill field), L1 R-3

---

## [PLAN] — Architecture Deliverables

### 6 Components

**Component 1: /rsil-global Complete Flow Design (G-0 → G-4)**
- G-0: Observation Window — work type classification + Three-Tier per type (A/B/C tables)
- G-1: Lens Application — which lenses apply to global health, research question generation from observation data
- G-2: Discovery — Tier 3 escalation criteria, parallel agent spawn decision (cc-guide + Explore)
- G-3: Classification — AD-15 filter, findings-only output, AskUser for BREAK severity
- G-4: Record — tracker (G-{N} namespace) + agent memory update + terminal summary
- Plus: YAML frontmatter, Dynamic Context (Tier 0 shell commands), When to Use tree, Error Handling, Principles

**Component 2: /rsil-review Refinement Delta**
- 6 exact change specs with line ranges, old→new text, rationale:
  - IMP-1: ultrathink placement (intro paragraph)
  - IMP-2: wc -l pre-check in Dynamic Context
  - IMP-3: Agent memory read (R-0) + write (R-4)
  - IMP-4/6: Merge Key Principles + Never → single ~15-item section (-8L)
  - IMP-5: Agent memory shell command as 8th dynamic context
  - IMP-7: Output format → guidance (-5L)

**Component 3: Shared Foundation Specification**
- 8 Lenses: IDENTICAL text in both skills (stable, copy not reference)
- AD-15 Filter: IDENTICAL
- Layer 1/2 Boundary Test: IDENTICAL
- Cross-reference protocol: G-{N} ↔ P-R{N} via cross_refs/promoted_to/decomposed_to fields

**Component 4: CLAUDE.md Integration**
- Phase 9.5 NL discipline: exact wording, placement
- Non-pipeline work trigger wording
- ~5-8 lines addition

**Component 5: Agent Memory Schema**
- 4-section: Config (8L), Statistics (20L), Patterns (60-80L), Evolution (30-50L)
- Seed data from current 24 findings / 79% acceptance
- Read: dynamic context `!`cat`` at skill load
- Write: R-4/G-4 Read-Merge-Write protocol

**Component 6: Cumulative Data Flow**
- ASCII: observation → findings → tracker → memory → next cycle
- Trigger matrix for each data store
- Version tracking

### Architecture Decisions (new)

| # | Decision | Rationale |
|---|----------|-----------|
| AD-6 | Findings-only output (no auto-apply) | GC-v2 constraint; user always confirms |
| AD-7 | Three-Tier per work type (adaptive sources, fixed budget) | Type B/C have no gate records; git diff substitutes |
| AD-8 | BREAK escalation via AskUserQuestion | User present in auto-invoke context; safe |
| AD-9 | Tracker section isolation + ID namespacing | Sequential consistency without locking |
| AD-10 | Shared Foundation = embedded copy per skill | Stability; no external reference file dependency |
| AD-11 | Single shared agent memory for both skills | Both contribute stats/patterns; separation unnecessary |

### Risk Matrix

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R-1 | Tier 0 misclassification | LOW | MEDIUM | Multiple signals (session dir + git diff + skill trace) |
| R-2 | Context budget overrun (large sessions) | MEDIUM | LOW | Cap: 3 most recent L1 files per researcher-1 U-2 |
| R-3 | NL discipline non-compliance | MEDIUM | LOW | CLAUDE.md instruction + agent memory reminder |
| R-4 | Tracker growth >150 findings | LOW | LOW | Archive strategy defined (split at 150) |
| R-5 | Agent memory 200-line pressure | MEDIUM | LOW | Budget allocation pre-defined; §3 Patterns capped |

### Approach

1. Use sequential-thinking for each major design decision
2. Reference researcher L1/L2 evidence for every choice
3. Complete L3 with ASCII flow diagrams + exact text specifications
4. Write L1/L2 proactively throughout work

**Estimated output:** L1 (~45L), L2 (~180L), L3 (~400-500L)

---

Awaiting Lead approval to proceed.
