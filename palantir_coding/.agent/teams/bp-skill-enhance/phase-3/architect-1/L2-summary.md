## Summary

This architecture redesigns the brainstorming-pipeline P0/P1 flow to address all 8 reported issues through 8 architecture decisions (AD-1 through AD-8). The core changes: P0 becomes a lightweight PT existence check only (AD-1), a new Feasibility Check validates topics early in Q&A (AD-2), the checkpoint moves earlier to protect Q&A context (AD-3), Scope Crystallization absorbs Tier Classification (AD-4), and PT creation defers to Gate 1 where richer context is available (AD-5). Three cross-cutting changes consolidate sequential-thinking reminders (AD-6), cap Dynamic Context verbosity (AD-7), and reduce RTD Decision Points (AD-8). Net line reduction: ~64-94L depending on Phase 2/3 sequential-thinking removal scope.

---

## Architecture Decisions

### AD-1: P0 Becomes PT Existence Check Only
**Problem:** H1 (PT creation too early) + H3 (Tier classification before scope known).
**Decision:** P0 does exactly one thing: `TaskList` search for `[PERMANENT]`. If found, carry its context forward. If not found, note "will create at Gate 1." No PT creation. No tier classification.
**Rationale:** PT creation at P0 wastes cycles when the user pivots topics (observed: 2 pivots before valid topic). Tier classification at P0 is meaningless — scope isn't known yet.
**Impact:** P0 shrinks from 57L to ~20L. `/permanent-tasks` invocation moves to Gate 1.

### AD-2: Feasibility Check After PURPOSE
**Problem:** H2 (No topic validation — 2 invalid topics before a real one).
**Decision:** After the PURPOSE category is explored in Q&A (1.2), run a 3-criterion feasibility gate before proceeding to deeper categories. Soft gate — user can override.
**Criteria:** (1) Actionable deliverable? (2) Not duplicating completed work? (3) Scope estimable?
**Rationale:** PURPOSE is the minimum information needed to judge feasibility. Checking earlier (during Recon) lacks user input; checking later (after Approach) wastes significant Q&A effort.
**Impact:** +15L for the decision tree and pivot handling. Saves potentially 100+ tokens per invalid topic by failing fast.

### AD-3: Checkpoint Moved to 1.2.5 (Post-Feasibility)
**Problem:** M1 (Checkpoint at 1.3.5 triggers after Approach — too late, Q&A context lost on compact).
**Decision:** Checkpoint triggers at 1.2.5 — after feasibility passes and at least 2 Q&A categories are covered. Lighter content than current 1.3.5 (no approach selection saved, since that hasn't happened yet).
**Rationale:** The checkpoint's purpose is compact recovery. The worst case is losing Q&A context — protecting it immediately after feasibility (when meaningful decisions exist) is optimal.
**Impact:** -5L (simpler checkpoint content). Recovery reads 1.2.5 checkpoint instead of 1.3.5.

### AD-4: Scope + Tier Unified at 1.4
**Problem:** H3 (Tier classification at P0 is premature).
**Decision:** Scope Crystallization (1.4) absorbs Tier Classification. The Scope Statement gains a formal `Tier Classification` field derived from file count, module count, and cross-boundary assessment — all known by this point.
**Rationale:** Tier depends on file count, module count, and cross-module impact — none of which are known at P0. At 1.4, all three are established through Q&A. The current P0 tier is always "estimated" and often changes; making 1.4 the single determination point eliminates the estimate-then-confirm pattern.
**Impact:** Tier Routing subsection (lines 93-106) deleted from P0. Scope Statement template gains ~3L for tier fields. Tier confirmation at 1.4 (currently a note at line 103) becomes the ONLY tier determination.

### AD-5: Gate 1 PT Creation Sequence
**Problem:** H1 (PT creation at P0 is premature).
**Decision:** Gate 1 creates PT via `/permanent-tasks`, then GC-v1, then orchestration-plan, then gate-record. PT is created FIRST because it's the authority; GC references it.
**Rationale:** At Gate 1, the full Scope Statement, approach selection, complexity tier, and all Q&A decisions are available — making PT-v1 maximally rich. Research finding D2 confirms `/permanent-tasks` is standalone and can be invoked at Gate 1 without modification.
**Impact:** Gate 1 artifact creation section gains ~10L. P0 PT creation deleted. Downstream skills find PT already created (per D2: they handle "PT found" gracefully).

### AD-6: Sequential-Thinking Consolidation
**Problem:** L1 (9 scattered sequential-thinking reminders).
**Decision:** Remove all 9 inline reminders. Add a single consolidated instruction in the Cross-Cutting section: "All agents (Lead and teammates) use sequential-thinking for every analysis, judgment, and decision throughout all phases."
**Rationale:** 9 reminders of the same instruction adds line count without adding compliance. The cross-cutting section is the natural home for universal requirements. Opus 4.6 follows a single clear instruction reliably.
**Impact:** -8L (P1 inline removals) -6L (P2/P3 inline removals, if allowed) -10L (CC table compression) +3L (single consolidated instruction) = net -21L to -15L.

### AD-7: Dynamic Context Git Branch Capping
**Problem:** L2 (35+ branches in `git branch` output).
**Decision:** Change `git branch 2>/dev/null` to `git branch 2>/dev/null | head -10`.
**Rationale:** 10 most recent branches is sufficient for recon. Full branch list consumes tokens without informational value.
**Impact:** -3L (accounting for comment explaining the cap). Prevents token waste at skill load.

### AD-8: RTD Decision Points Reduced (7 → 3)
**Problem:** L3 (7 DPs in Phase 1 is excessive — most aren't meaningful phase transitions).
**Decision:** Keep 3 DPs: Gate 1 evaluation, Gate 2 evaluation, Gate 3 evaluation. Remove: Approach selection, Scope crystallization, Researcher spawn, Architect spawn.
**Rationale:** DPs should mark phase transitions (externally meaningful state changes). Approach selection and scope crystallization are intra-phase decisions captured in L1/L2. Spawn events are operational, not decisional.
**Impact:** -8L in the RTD DP list. RTD index stays lean during P1.

---

## New P0/P1 Flow (Detailed)

### New P0 (~20L)
```
P0: PERMANENT Task Check
     │
TaskList search for [PERMANENT]
     │
┌────┼────────┐
none  1        2+
│     │        │
▼     ▼        ▼
Note  Validate  Match $ARGUMENTS
"no PT" match   against each PT
│     │        │
▼     ▼     ┌──┴──┐
Continue   Continue  AskUser
to P1      to P1
```
No PT creation. No tier classification. ~500 tokens as before.

### New P1 Flow
```
1.1: Structured Recon (unchanged)
1.2: Q&A + Feasibility Check (NEW)
     ├── After PURPOSE → run feasibility gate
     ├── PASS → continue to SCOPE/CONSTRAINTS/etc.
     └── FAIL → pivot or refine
1.2.5: Incremental Checkpoint (MOVED earlier)
1.3: Approach Exploration (unchanged)
1.4: Scope + Tier Classification (MERGED)
1.5: Gate 1 → PT creation + GC-v1 + gate-record
```

### Feasibility Check Detail (within 1.2)
```
After user explains PURPOSE:
     │
├── Produces a concrete codebase deliverable?
│     ├── NO → refine: "Can you describe what files or systems would change?"
│     └── YES ↓
│
├── Overlaps with recently completed work? (check git log, MEMORY.md)
│     ├── YES → clarify: "This overlaps with {X}. Extending it or starting fresh?"
│     └── NO ↓
│
├── Scope estimable? (can you identify affected modules/files?)
│     ├── NO → refine: "The scope is too open. What's the specific deliverable?"
│     └── YES ↓
│
└── FEASIBLE → continue Q&A for remaining categories
```
On repeated failure (3 pivots): suggest stepping back to clarify goals before continuing.
User override: always available ("I want to proceed anyway").

### Checkpoint 1.2.5 Content
```markdown
# Phase 1 Q&A Checkpoint — {feature}

## Feasibility
{PASS with rationale}

## Categories Covered
{List of PURPOSE + others explored so far}

## Key Decisions So Far
{Decisions from Q&A}

## Scope Direction (Draft)
{Early boundary draft}
```
Triggers when: feasibility PASS AND ≥2 categories covered.

### Scope + Tier at 1.4
Scope Statement template gains these fields:
```markdown
**Pipeline Tier:** TRIVIAL | STANDARD | COMPLEX
**Tier Rationale:**
- File count: ~N (TRIVIAL ≤2 / STANDARD 3-8 / COMPLEX >8)
- Module count: ~N (TRIVIAL 1 / STANDARD 1-2 / COMPLEX 3+)
- Cross-boundary: YES/NO
```
This replaces the P0 Tier Routing subsection entirely.

### Gate 1 Artifact Creation Sequence
1. **Create PT via `/permanent-tasks`** — invoke with conversation context. Returns PT-v1 with User Intent, Impact Map, Decisions, Phase Status, Constraints. PT is now the Single Source of Truth.
2. **Create GC-v1** — references PT-v1, carries Scope Statement and phase pipeline status. Structure unchanged (downstream compatibility per D1).
3. **Create orchestration-plan.md** — references GC-v1, contains Phase 2 plan.
4. **Create gate-record.yaml** — standard gate record format.

GC-v1 now includes a PT reference:
```markdown
---
version: GC-v1
pt_version: PT-v1
...
---
```

---

## Line Budget Analysis

| Section | Current | New | Delta | Notes |
|---------|---------|-----|-------|-------|
| Frontmatter/header | 28L | 25L | -3 | Minor trim |
| Dynamic Context | 21L | 18L | -3 | AD-7 branch cap |
| Phase 0 | 57L | 20L | -37 | AD-1 check-only |
| Phase 1.1 Recon | 16L | 14L | -2 | Remove seq-thinking inline |
| Phase 1.2 Q&A | 23L | 38L | +15 | AD-2 feasibility check |
| Phase 1.2.5 Checkpoint | — | 18L | +18 | AD-3 new location |
| Phase 1.3 Approach | 18L | 16L | -2 | Remove seq-thinking inline |
| Phase 1.3.5 Checkpoint | 25L | 0L | -25 | Deleted (replaced by 1.2.5) |
| Phase 1.4 Scope | 30L | 33L | +3 | AD-4 tier merge |
| Phase 1.5 Gate 1 | 82L | 75L | -7 | AD-5 PT creation + template trim |
| Phase 2 | 129L | 123L | -6 | Seq-thinking removals only |
| Phase 3 | 127L | 121L | -6 | Seq-thinking removals only |
| Clean Termination | 35L | 35L | 0 | Unchanged |
| Cross-Cutting | 74L | 52L | -22 | AD-6 + AD-8 |
| **Total** | **672L** | **~578L** | **-94L** | |

The ~578L estimate includes Phase 2/3 sequential-thinking removals (-12L). Without those (strict "unchanged" interpretation): ~590L.

Path to 550L (if needed): compress Gate 1 GC-v1/orchestration-plan templates from code blocks to inline descriptions (-20L), compress Q&A category table (-5L). This sacrifices implementer clarity for line count.

---

## Risks

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R-1 | 550L target may require Phase 2/3 edits | LOW | Sequential-thinking removal is cross-cutting, not logic change. Document as "minimal cross-cutting edit." |
| R-2 | Feasibility Check false positives | MEDIUM | Soft gate with user override. 3-criteria are intentionally generous (estimable scope, not "fully planned scope"). |
| R-3 | No PT during Phase 1 Q&A | LOW | All Phase 1 is Lead-only — no teammates need PT. PT is only consumed from Phase 2 onward. Research D2 confirms downstream skills handle PT gracefully. |
| R-4 | GC-v1 now references PT version | LOW | Simple field addition (`pt_version:`). Downstream skills that don't read this field are unaffected. |

---

## PT Goal Linkage

| Issue | AD | Resolution |
|-------|-----|------------|
| H1: PT creation too early | AD-1, AD-5 | Deferred to Gate 1 where full context available |
| H2: No topic validation | AD-2 | 3-criterion feasibility check after PURPOSE |
| H3: Tier at P0 premature | AD-1, AD-4 | Moved to Scope Crystallization at 1.4 |
| M1: Checkpoint too late | AD-3 | Moved to 1.2.5 (post-feasibility, pre-approach) |
| L1: Sequential-thinking scattered | AD-6 | Consolidated to 1 cross-cutting instruction |
| L2: Git branch verbose | AD-7 | Capped to 10 lines |
| L3: RTD DPs excessive | AD-8 | Reduced from 7 to 3 (gate transitions only) |

---

## Evidence Sources

| Source | What Used | Decision |
|--------|-----------|----------|
| SKILL.md lines 52-106 | Current P0 flow, PT creation, tier routing | AD-1, AD-4, AD-5 |
| SKILL.md lines 125-147 | Current Q&A category tracking | AD-2 |
| SKILL.md lines 168-192 | Current 1.3.5 checkpoint | AD-3 |
| SKILL.md lines 194-223 | Current scope crystallization | AD-4 |
| SKILL.md lines 225-306 | Current Gate 1 artifacts | AD-5 |
| SKILL.md lines 599-672 | Cross-cutting sections | AD-6, AD-7, AD-8 |
| Researcher L2 D1 | GC role classification (phase gating, session discovery, context carrier) | AD-5 |
| Researcher L2 D2 | /permanent-tasks standalone, invocable at Gate 1 | AD-5 |
| Researcher L2 D3 | Hook reads only version: frontmatter, PT fallback built in | AD-1 |
| permanent-tasks/SKILL.md | Interface contract, PT Description Template | AD-5 |
| gate-evaluation-standard.md | Gate record format, tier→depth mapping | AD-4 |

## Downstream Handoff

### Decisions Made (forward-binding)
- AD-1 through AD-8 define the complete P0/P1 restructuring
- P0 is check-only; all creation happens at Gate 1
- Feasibility check is a soft gate (user can override)
- Tier classification source of truth is 1.4, not P0

### Risks Identified (must-track)
- R-2: Feasibility false positives — monitor first 3 uses
- 550L target may require judgment call on Phase 2/3 sequential-thinking removal

### Interface Contracts (must-satisfy)
- GC-v1 structure unchanged (downstream D1 compatibility)
- GC-v1 adds `pt_version:` field in frontmatter (non-breaking)
- /permanent-tasks invocation at Gate 1 uses existing interface (no changes to that skill)
- Tier Routing subsection (lines 93-106) fully deleted, absorbed into 1.4

### Constraints (must-enforce)
- Phase 2/3 logic unchanged (only sequential-thinking inline removal allowed)
- Clean Termination section unchanged
- GC structure must persist for downstream compatibility

### Open Questions (requires resolution)
- Strict vs soft interpretation of "Phase 2/3 unchanged" for sequential-thinking removal
- 550L vs 578L: is the extra compression worth readability cost?

### Artifacts Produced
- L1-index.yaml, L2-summary.md, L3-full/architecture-design.md
