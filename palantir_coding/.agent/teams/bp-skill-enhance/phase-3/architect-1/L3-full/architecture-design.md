# brainstorming-pipeline P0/P1 Flow Redesign — Architecture Design

## Table of Contents

1. [Architecture Decisions (AD-1 through AD-8)](#1-architecture-decisions)
2. [New P0 Flow Design](#2-new-p0-flow-design)
3. [Feasibility Check Design](#3-feasibility-check-design)
4. [Incremental Checkpoint Design](#4-incremental-checkpoint-design)
5. [Scope + Tier Merge Design](#5-scope--tier-merge-design)
6. [Gate 1 PT Creation Design](#6-gate-1-pt-creation-design)
7. [Cross-Cutting Changes](#7-cross-cutting-changes)
8. [Migration Guide](#8-migration-guide)
9. [Risk Matrix](#9-risk-matrix)

---

## 1. Architecture Decisions

### AD-1: P0 Becomes PT Existence Check Only

**Context:** Current P0 creates a PERMANENT Task and classifies pipeline tier. Both are premature — the user may pivot topics (observed: 2 pivots before valid topic), and scope isn't known yet for tier classification.

**Decision:** P0 does exactly one thing: search TaskList for `[PERMANENT]`. Record the result (exists/not-exists, task ID if found). No PT creation. No tier classification. Both are deferred.

**Consequences:**
- (+) No wasted PT creation for pivoted topics
- (+) P0 shrinks from 57L to ~20L
- (+) Tier classification happens when data is available (1.4)
- (-) No PT exists during Phase 1 (acceptable: Phase 1 is Lead-only, no teammates need PT)

### AD-2: Feasibility Check After PURPOSE Category

**Context:** Users proposed 2 invalid topics before finding a real one. No validation exists in the current flow.

**Decision:** After the PURPOSE category is explored in 1.2 Q&A, execute a 3-criterion feasibility gate. This is a soft gate — user can override.

**Criteria:**
1. **Actionable Deliverable** — does the topic produce concrete codebase changes?
2. **No Duplication** — does it overlap with recently completed work?
3. **Estimable Scope** — can affected modules/files be identified?

**Consequences:**
- (+) Fails fast on invalid topics (saves 100+ tokens of wasted Q&A per pivot)
- (+) Soft gate preserves user agency
- (-) +15L to SKILL.md for the decision tree
- (-) Risk of false positives on exploratory/research topics (mitigated by override)

### AD-3: Checkpoint Moved to 1.2.5

**Context:** Current 1.3.5 checkpoint triggers after Approach Exploration. By then, significant Q&A context exists that would be lost on auto-compact.

**Decision:** Move checkpoint to 1.2.5, triggered after feasibility check passes AND at least 2 Q&A categories are covered. Lighter content (no approach selection, since that hasn't happened yet).

**Consequences:**
- (+) Protects Q&A context earlier
- (+) Simpler checkpoint content (-5L)
- (-) Checkpoint doesn't include approach selection (acceptable: approach is in 1.3, which writes its own comparison table to the user's visible chat)

### AD-4: Scope Crystallization Absorbs Tier Classification

**Context:** Current P0 tier classification is always "estimated" and often changes at 1.4. This creates an estimate-then-confirm pattern that adds complexity.

**Decision:** 1.4 Scope Crystallization becomes the single point for tier determination. The Scope Statement gains formal tier fields: file count → module count → cross-boundary → tier.

**Tier Decision Logic:**
```
File count: ≤2 → TRIVIAL, 3-8 → STANDARD, >8 → COMPLEX
Module count: 1 → TRIVIAL/STANDARD, 2 → STANDARD, 3+ → COMPLEX
Cross-boundary: NO → TRIVIAL/STANDARD, YES → STANDARD/COMPLEX
Final tier = MAX(file tier, module tier, boundary tier)
```

**Consequences:**
- (+) Tier determined with real data, not estimates
- (+) Eliminates P0 Tier Routing subsection (-14L)
- (+) Single source of truth for tier
- (-) TRIVIAL tier short-circuits now happen at 1.4 instead of P0 (later, but more accurate)

### AD-5: Gate 1 PT Creation via /permanent-tasks

**Context:** PT was created at P0 with minimal context. At Gate 1, the full Scope Statement, approach selection, complexity tier, and all Q&A decisions are available.

**Decision:** Gate 1 creates artifacts in this sequence:
1. Invoke `/permanent-tasks` with conversation context → creates PT-v1
2. Create GC-v1 (references PT-v1 via `pt_version` frontmatter field)
3. Create orchestration-plan.md
4. Create gate-record.yaml

**Why this order:** PT is the authority (Single Source of Truth). GC references PT. Orchestration plan references GC. Gate record captures all three.

**Research validation:** D2 confirms `/permanent-tasks` is standalone and can be invoked at Gate 1 without modification. D3 confirms the hook handles "no GC" gracefully via PT fallback path.

**Consequences:**
- (+) PT-v1 is maximally rich (all Q&A decisions, scope, tier, approach)
- (+) No wasted PT for pivoted topics
- (+) Downstream skills find PT already created
- (-) +10L for the /permanent-tasks invocation step in Gate 1
- (-) GC-v1 gains `pt_version` frontmatter field (non-breaking addition)

### AD-6: Sequential-Thinking Consolidation (9 → 1)

**Context:** 9 inline reminders of the same instruction scattered across P1, P2, and P3.

**Decision:** Remove all 9 inline reminders. Replace with a single consolidated instruction in Cross-Cutting: "All agents (Lead and teammates) use `mcp__sequential-thinking__sequentialthinking` for every analysis, judgment, and decision throughout all phases. No exceptions."

**Removal locations:**
1. Line 112: P1 header "Use sequential-thinking before every analysis step..."
2. Line 122: Recon "Use sequential-thinking to synthesize Recon..."
3. Line 147: Q&A "Use sequential-thinking after each user response..."
4. Line 165: Approach "Use sequential-thinking to formulate the trade-off..."
5. Line 220: Scope "Use sequential-thinking to synthesize all Q&A..."
6. Line 314: P2 header "Use sequential-thinking for all Lead decisions..."
7. Line 388: P2 verification "All agents use sequential-thinking throughout."
8. Line 444: P3 header "Use sequential-thinking for all Lead decisions..."
9. Line 484: P3 verification "All agents use sequential-thinking throughout."

**Cross-cutting replacement (replaces lines 619-631):**
```markdown
### Sequential Thinking

All agents (Lead and teammates) use `mcp__sequential-thinking__sequentialthinking`
for every analysis, judgment, and decision throughout all phases. No exceptions.
```

**Consequences:**
- (+) -15 to -21L savings (depending on Phase 2/3 inclusion)
- (+) Single authoritative location
- (-) Implementers reading only one phase section might not see the instruction (mitigated: cross-cutting is always read first per agent-common-protocol)

### AD-7: Dynamic Context Git Branch Cap

**Context:** `git branch` output shows 35+ branches, consuming tokens without value.

**Decision:** Change line 46 from `git branch 2>/dev/null` to `git branch 2>/dev/null | head -10`.

**Consequences:**
- (+) -3L (verbose output trimmed at load time)
- (+) Token savings at skill invocation
- (-) Might miss relevant branches beyond the 10 shown (low risk: branches are sorted, and recent ones appear first with some git configs)

### AD-8: RTD Decision Points Reduced (7 → 3)

**Context:** 7 DPs in the current skill, most representing intra-phase operational events.

**Decision:** Keep 3 DPs that represent genuine phase transitions:
- DP-1: Gate 1 evaluation (P1 → P2 transition)
- DP-2: Gate 2 evaluation (P2 → P3 transition)
- DP-3: Gate 3 evaluation (P3 → Clean Termination)

Remove 4 DPs: Approach selection (intra-P1), Scope crystallization (intra-P1), Researcher spawn (operational P2), Architect spawn (operational P3).

**Rationale:** DPs should mark externally meaningful state transitions. Intra-phase decisions and spawn events are captured in L1/L2 naturally. 7 DPs during a 3-phase skill creates noise in the rtd-index.

**Consequences:**
- (+) -8L in the DP list
- (+) Cleaner rtd-index with higher signal-to-noise
- (-) Less granular observability within Phase 1 (acceptable: Phase 1 is Lead-only, full context is in chat history)

---

## 2. New P0 Flow Design

### Current (Lines 52-106, 57L)

```
P0: PT Check → Create PT (via /permanent-tasks if needed) → Tier Classification
```
- PT creation decision tree: 38L
- Tier Routing subsection: 14L
- Separator/commentary: 5L

### New (~20L)

```markdown
## Phase 0: PERMANENT Task Check

Lightweight step (~500 tokens). No teammates spawned, no verification required.

Call `TaskList` and search for tasks with `[PERMANENT]` in their subject.

```
TaskList result
     │
┌────┼────────┐
none  1        2+
│     │        │
▼     ▼        ▼
Note  Validate  Match $ARGUMENTS
"no PT" match   against each
→ P1  → P1     │
              ┌──┴──┐
            match  no match
            → P1   → AskUser
```

If a [PERMANENT] task is found and matches `$ARGUMENTS`, its content (user intent,
impact map, prior decisions) provides additional context for Phase 1 discovery.
If no PT exists, one will be created at Gate 1 (1.5).

---
```

**Key differences from current:**
- No `/permanent-tasks` invocation
- No Tier Routing subsection
- No "If the user opts to create one" branch
- Decision tree simplified (3 terminal states: note/validate/ask)

---

## 3. Feasibility Check Design

### Placement

Embedded within Section 1.2 (Q&A), triggered after the PURPOSE category is explored. This is NOT a separate step — it's a gate within the Q&A flow.

### Implementation Text (~15L addition to 1.2)

```markdown
**Feasibility Check** — After the user explains PURPOSE, validate before deep-diving:

```
PURPOSE answered
     │
├── Produces a concrete codebase deliverable?
│     ├── NO → "This sounds strategic/philosophical. Can you identify
│     │         what would change in the codebase?"
│     └── YES ↓
├── Overlaps with completed work? (check git log, MEMORY.md)
│     ├── YES → "This overlaps with {X}. Extending it or new?"
│     └── NO ↓
├── Scope estimable? (can you name affected modules/files?)
│     ├── NO → "Too open-ended. What's the specific deliverable?"
│     └── YES ↓
└── FEASIBLE → continue Q&A for remaining categories
```

On failure: the user refines their answer (looping back to the failed criterion)
or pivots to a new topic (restart 1.2 from PURPOSE). User can always override:
"I want to proceed anyway" bypasses the check with a warning logged to the checkpoint.
If 3 pivots occur without a feasible topic, suggest stepping back to clarify goals.
```

### Criteria Rationale

| Criterion | Why | False Positive Risk |
|-----------|-----|---------------------|
| Actionable deliverable | Filters philosophical/strategic topics that can't crystallize scope | LOW — "changes codebase" is a generous bar |
| No duplication | Prevents re-work; catches user confusion about prior completions | MEDIUM — user might want to extend, not duplicate. Clarification question handles this. |
| Estimable scope | Filters topics so vague they'd derail Approach Exploration | LOW — "can you name modules" is generous |

### Interaction with Category Awareness

The feasibility check integrates naturally:
- PURPOSE is already the first category (unchanged)
- After feasibility PASS, the remaining categories (SCOPE, CONSTRAINTS, APPROACH, RISK, INTEGRATION) proceed as normal
- The category table in 1.2 is unchanged — feasibility is an additional check, not a replacement

---

## 4. Incremental Checkpoint Design

### Trigger Condition

Checkpoint 1.2.5 triggers when BOTH conditions are met:
1. Feasibility check PASSED (or user overrode)
2. At least 2 Q&A categories have been covered (PURPOSE + at least one other)

### Content

```markdown
# Phase 1 Q&A Checkpoint — {feature}

## Feasibility
{PASS | OVERRIDE with rationale}

## Categories Covered
{List which of PURPOSE/SCOPE/CONSTRAINTS/APPROACH/RISK/INTEGRATION are resolved}

## Key Decisions So Far
{Decisions locked in from conversation — approach not yet selected}

## Scope Direction (Draft)
{Early boundary draft — what's in, what's obviously out}
```

### Differences from Current 1.3.5

| Aspect | Current 1.3.5 | New 1.2.5 |
|--------|--------------|-----------|
| Trigger point | After Approach Exploration (1.3) | After feasibility + 2 categories |
| Content | Categories + Approach + Decisions + Scope | Feasibility + Categories + Decisions + Scope |
| Approach section | Selected approach from comparison | Not yet available (approach is in 1.3) |
| File location | Same: `.agent/teams/{session-id}/phase-1/qa-checkpoint.md` | Same |
| Recovery use | Resume Q&A from last category | Resume Q&A from last category |

### Recovery Protocol

On compact recovery:
1. Read `phase-1/qa-checkpoint.md`
2. Resume Q&A from the last covered category
3. If approach was already explored (visible in chat or checkpoint), skip to 1.4
4. If only checkpoint exists, continue from 1.3 (Approach Exploration)

---

## 5. Scope + Tier Merge Design

### Modified 1.4 Section

The Scope Statement template gains formal tier fields. Current template (lines 198-218, 21L of template) becomes:

```markdown
## Scope Statement

**Goal:** {one sentence}
**In Scope:**
- {item}

**Out of Scope:**
- {item}

**Approach:** {selected option summary}
**Success Criteria:**
- {measurable outcome}

**Pipeline Tier:** TRIVIAL | STANDARD | COMPLEX
**Tier Rationale:**
- File count: ~N
- Module count: ~N
- Cross-boundary impact: YES/NO

**Phase 2 Research Needs:**
- {topic}

**Phase 3 Architecture Needs:**
- {decision}
```

### Tier Decision Algorithm

```
Input: File count (F), Module count (M), Cross-boundary (B)

tier_file    = TRIVIAL if F ≤ 2, STANDARD if 3 ≤ F ≤ 8, COMPLEX if F > 8
tier_module  = TRIVIAL if M = 1, STANDARD if M = 2, COMPLEX if M ≥ 3
tier_bound   = TRIVIAL if !B, STANDARD if B and M ≤ 2, COMPLEX if B and M ≥ 3

final_tier   = MAX(tier_file, tier_module, tier_bound)
               where TRIVIAL < STANDARD < COMPLEX
```

### TRIVIAL Short-Circuit

If tier = TRIVIAL at 1.4:
- Skip Phase 2/3 entirely
- Create a lightweight scope statement only
- Route user to `/agent-teams-execution-plan` directly
- This behavior is unchanged from current (line 103-104) — just the trigger point moves from P0 to 1.4

### Interaction with Gate 1

Gate 1 checklist item G1-2 changes from "Complexity classification confirmed" to "Pipeline tier determined (TRIVIAL/STANDARD/COMPLEX) with rationale." The gate record includes the tier.

---

## 6. Gate 1 PT Creation Design

### Artifact Creation Sequence

```
Gate 1 APPROVE
     │
     ├── Step 1: Invoke /permanent-tasks
     │   └── Creates PT-v1 with full Q&A context
     │       (User Intent, Impact Map, Decisions, Phase Status, Constraints)
     │
     ├── Step 2: Create GC-v1
     │   └── Carries Scope Statement, phase status, constraints
     │       Frontmatter includes pt_version: PT-v1
     │
     ├── Step 3: Create orchestration-plan.md
     │   └── References GC-v1, contains Phase 2 plan
     │
     └── Step 4: Create gate-record.yaml
         └── Standard format per gate-evaluation-standard.md
```

### Why PT First

1. `/permanent-tasks` uses `$ARGUMENTS` and conversation context — both maximally rich at Gate 1
2. PT becomes the Single Source of Truth immediately
3. GC-v1 can reference `pt_version: PT-v1` (backward-traceable)
4. If GC creation fails, PT still exists (most critical artifact created first)

### GC-v1 Modification

Current GC-v1 frontmatter:
```yaml
---
version: GC-v1
created: {date}
feature: {name}
complexity: {level}
---
```

New GC-v1 frontmatter:
```yaml
---
version: GC-v1
pt_version: PT-v1
created: {date}
feature: {name}
tier: TRIVIAL | STANDARD | COMPLEX
---
```

Changes: `pt_version` added, `complexity` renamed to `tier` for consistency with AD-4.

GC body structure is UNCHANGED — Scope, Phase Pipeline Status, Constraints, Decisions Log all remain. This preserves downstream compatibility (research finding D1: write-plan embeds full GC-v3 in directives).

### /permanent-tasks Invocation

```
Lead (at Gate 1): "I'm using permanent-tasks to create the PERMANENT Task."
/permanent-tasks "{Scope Statement summary + approach + tier}"
```

The skill handles TaskCreate with the full PT Description Template. Lead provides conversation context (Scope Statement, approach selection, Q&A decisions) as the invocation context. No changes to `/permanent-tasks` SKILL.md needed (research finding D2).

---

## 7. Cross-Cutting Changes

### 7.1 Sequential-Thinking Consolidation (AD-6)

**Current Cross-Cutting section (lines 619-631, 13L):**
```markdown
### Sequential Thinking

All agents (Lead and teammates) use `mcp__sequential-thinking__sequentialthinking` for
analysis, judgment, design, and verification throughout the entire pipeline.

| Agent | When |
|-------|------|
| Lead (P1) | After Recon, after each user response, before Scope Statement, at Gates |
| Lead (P2-3) | Understanding verification, probing questions, Gate evaluation, PT/GC updates |
| research-coordinator (P2) | Research distribution, worker verification, progress monitoring, findings consolidation |
| Researcher (P2) | Research strategy, findings synthesis, L2 writing |
| Architect (P3) | Component design, trade-off analysis, interface definition |
```

**New (3L):**
```markdown
### Sequential Thinking

All agents (Lead and teammates) use `mcp__sequential-thinking__sequentialthinking`
for every analysis, judgment, and decision throughout all phases. No exceptions.
```

**Savings:** -10L (table removed). The per-agent detail is unnecessary — "every analysis, judgment, and decision" covers all cases listed in the table.

**Inline removals (9 locations):**

| # | Location | Current Text | Action |
|---|----------|-------------|--------|
| 1 | Line 112 (P1 header) | "Use `sequential-thinking` before every analysis step, judgment, and decision in this phase." | DELETE entire line |
| 2 | Line 122 (1.1 Recon) | "Use `sequential-thinking` to synthesize Recon into an internal assessment before starting Q&A." | DELETE entire line |
| 3 | Line 147 (1.2 Q&A) | "Use `sequential-thinking` after each user response to analyze the answer and determine the next question or whether to proceed to Scope Crystallization." | DELETE entire line+wrap |
| 4 | Line 165 (1.3 Approach) | "Use `sequential-thinking` to formulate the trade-off analysis before presenting." | DELETE entire line |
| 5 | Line 220 (1.4 Scope) | "Use `sequential-thinking` to synthesize all Q&A into the Scope Statement." | DELETE entire line |
| 6 | Line 314 (P2 header) | "Use `sequential-thinking` for all Lead decisions in this phase." | DELETE entire line |
| 7 | Line 388 (2.3 tail) | "All agents use `sequential-thinking` throughout." | DELETE entire line |
| 8 | Line 444 (P3 header) | "Use `sequential-thinking` for all Lead decisions in this phase." | DELETE entire line |
| 9 | Line 484 (3.2 tail) | "All agents use `sequential-thinking` throughout." | DELETE entire line |

**P1 savings:** 5 removals × ~1.5L avg = ~8L
**P2/P3 savings:** 4 removals × ~1.5L avg = ~6L (requires interpretation that cross-cutting edits are allowed in "unchanged" sections)

### 7.2 Dynamic Context Change (AD-7)

**Current (line 46):**
```
!`cd /home/palantir && git branch 2>/dev/null`
```

**New:**
```
!`cd /home/palantir && git branch 2>/dev/null | head -10`
```

Single-line edit. -3L savings from reduced output at skill load time (output reduction, not source reduction).

### 7.3 RTD Decision Points Reduction (AD-8)

**Current (lines 610-618, 9L of DP list):**
```markdown
Decision Points for this skill:
- DP: Scope crystallization (1.4 approval)
- DP: Approach selection (1.3 user choice)
- DP: Researcher spawn (2.3)
- DP: Gate 1 evaluation
- DP: Gate 2 evaluation
- DP: Architect spawn (3.1)
- DP: Gate 3 evaluation
```

**New (4L):**
```markdown
Decision Points for this skill:
- DP-1: Gate 1 evaluation (P1 → P2 transition)
- DP-2: Gate 2 evaluation (P2 → P3 transition)
- DP-3: Gate 3 evaluation (P3 → termination)
```

**Savings:** -5L. IDs added for clarity.

---

## 8. Migration Guide

### Section-by-Section Mapping

#### Header and Dynamic Context (Lines 1-49)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 1-28 (frontmatter, header, When to Use) | KEEP | Minor description update to mention "PT Check → Discovery → Research → Architecture" (remove "Tier Classification" from core flow line 13) |
| 29-45 (Dynamic Context) | KEEP | No changes |
| 46 (git branch) | MODIFY | Add `\| head -10` (AD-7) |
| 47-49 ($ARGUMENTS, separator) | KEEP | No changes |

#### Phase 0 (Lines 50-106)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 50-51 (header + commentary) | KEEP | Same header, same "~500 tokens" |
| 52-89 (PT Check decision tree) | REPLACE | Simplified check-only tree (AD-1). ~15L replaces ~38L. Remove all "/permanent-tasks creates PT-v1" branches. Remove "If the user opts to create one" paragraph. |
| 90-92 (separator) | KEEP | |
| 93-106 (Tier Routing subsection) | DELETE | Entire subsection removed. Tier logic moves to 1.4 (AD-4). |

**Net change:** 57L → ~20L (-37L)

#### Phase 1.1 Recon (Lines 108-123)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 108-111 (header + "Lead-only") | KEEP | |
| 112 (sequential-thinking) | DELETE | AD-6 consolidation |
| 113-121 (Layer A/B/C) | KEEP | |
| 122 (sequential-thinking) | DELETE | AD-6 consolidation |
| 123 (No files created) | KEEP | |

**Net change:** 16L → 14L (-2L)

#### Phase 1.2 Q&A (Lines 125-147)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 125-128 (header + description) | KEEP | |
| 129-130 (question count) | KEEP | |
| 131-145 (category table + commentary) | KEEP | |
| 146-147 (sequential-thinking + next) | DELETE line 147 | AD-6 |
| NEW: after 145 | INSERT | Feasibility Check subsection (~15L, AD-2) |

**Net change:** 23L → 36L (+13L) — feasibility check is the primary addition

#### Phase 1.2.5 Checkpoint (NEW)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| N/A | INSERT after 1.2 | New checkpoint section (~18L, AD-3) |

**Net change:** +18L

#### Phase 1.3 Approach (Lines 149-166)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 149-164 (header + table + description) | KEEP | |
| 165 (sequential-thinking) | DELETE | AD-6 |
| 166 (After user selection) | KEEP | |

**Net change:** 18L → 16L (-2L)

#### Phase 1.3.5 Checkpoint (Lines 168-192)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 168-192 (entire section) | DELETE | Replaced by 1.2.5 (AD-3) |

**Net change:** 25L → 0L (-25L)

#### Phase 1.4 Scope (Lines 194-223)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 194-196 (header + judgment) | KEEP | |
| 197-218 (Scope Statement template) | MODIFY | Add tier fields: `Pipeline Tier`, `Tier Rationale` (~+3L). Rename "Estimated Complexity" to "Pipeline Tier" (AD-4) |
| 219-220 (sequential-thinking) | DELETE line 220 | AD-6 |
| 221-223 (user reject/approve) | KEEP | |

**Net change:** 30L → 32L (+2L)

#### Phase 1.5 Gate 1 (Lines 225-306)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 225-237 (gate criteria table) | MODIFY | G1-2 becomes "Pipeline tier determined with rationale" |
| 238 (gate audit note) | KEEP | |
| 239 ("On APPROVE") | KEEP | |
| NEW: before GC-v1 | INSERT | Step 1: `/permanent-tasks` invocation (~8L, AD-5) |
| 240-268 (GC-v1 template) | MODIFY | Add `pt_version: PT-v1` and `tier:` to frontmatter. Rename `complexity:` to `tier:` (-1L net) |
| 269-291 (orchestration-plan template) | MODIFY | Minor trim: compress Phase 2 Plan bullets (-3L) |
| 292-306 (gate-record template) | KEEP | |

**Net change:** 82L → 83L (+1L) — PT creation step added, templates slightly trimmed

#### Phase 2 (Lines 309-436) — Minimal Changes

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 314 | DELETE | sequential-thinking removal (AD-6) |
| 388 | DELETE | sequential-thinking removal (AD-6) |
| All other lines | KEEP | |

**Net change:** 129L → 127L (-2L) — cross-cutting only, no logic changes

#### Phase 3 (Lines 438-563) — Minimal Changes

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 444 | DELETE | sequential-thinking removal (AD-6) |
| 484 | DELETE | sequential-thinking removal (AD-6) |
| All other lines | KEEP | |

**Net change:** 127L → 125L (-2L) — cross-cutting only, no logic changes

#### Clean Termination (Lines 565-598)

UNCHANGED. 35L.

#### Cross-Cutting (Lines 599-672)

| Current Lines | Action | New Content |
|---------------|--------|-------------|
| 599-600 (header + separator) | KEEP | |
| 601-618 (RTD section) | MODIFY | Reduce DP list from 7 to 3 (AD-8). -5L |
| 619-631 (Sequential Thinking) | REPLACE | 13L → 3L consolidated instruction (AD-6). -10L |
| 632-648 (Error + Recovery) | KEEP | |
| 649-660 (Key Principles) | MODIFY | Remove "Sequential thinking always" bullet (-1L, covered by CC). Add "Feasibility first — validate topic before deep Q&A" (+1L). Net 0L. |
| 661-672 (Never list) | MODIFY | Add: "Skip the feasibility check" (+1L). Remove: "Present the Scope Statement without using sequential-thinking first" (-1L, covered by CC). Net 0L. |

**Net change:** 74L → 58L (-16L)

### Line Count Summary

| Section | Current | New | Delta |
|---------|---------|-----|-------|
| Header/DC | 49L | 46L | -3 |
| Phase 0 | 57L | 20L | -37 |
| Phase 1.1 | 16L | 14L | -2 |
| Phase 1.2 | 23L | 36L | +13 |
| Phase 1.2.5 | 0L | 18L | +18 |
| Phase 1.3 | 18L | 16L | -2 |
| Phase 1.3.5 | 25L | 0L | -25 |
| Phase 1.4 | 30L | 32L | +2 |
| Phase 1.5 Gate 1 | 82L | 83L | +1 |
| Phase 2 | 129L | 127L | -2 |
| Phase 3 | 127L | 125L | -2 |
| Clean Termination | 35L | 35L | 0 |
| Cross-Cutting | 74L | 58L | -16 |
| Separators/blanks | 7L | 7L | 0 |
| **Total** | **672L** | **~617L** | **-55L** |

### Reaching 550L — Additional Compression Options

The mandatory changes achieve ~617L. To reach the 550L target (-67L more), these optional compressions are available:

| Option | Savings | Trade-off |
|--------|---------|-----------|
| A: Compress GC-v1 template from code block to inline description | -15L | Less copy-pasteable for implementer |
| B: Compress orchestration-plan template similarly | -10L | Same trade-off |
| C: Compress gate-record template similarly | -8L | Same trade-off |
| D: Compress Q&A category table to inline list | -5L | Less scannable |
| E: Compress Approach comparison table to prose | -8L | Less structured |
| F: Merge Error Handling + Compact Recovery sections | -4L | Minor clarity reduction |
| G: Remove Gate 1 criteria table (reference gate-evaluation-standard.md instead) | -8L | Requires external reference lookup |
| H: Remove Gate 2/3 criteria tables (same reference approach) | -16L | Same trade-off |

**Recommended path:** Options A + B + G = -33L → ~584L.
With options A + B + C + G + H = -57L → ~560L (close to target, preserves all logic).
Full set: all options = -74L → ~543L (slightly below target, some readability loss).

**Recommendation:** Apply options A, B, C, G, H (template compression + gate reference). These move gate criteria to the already-published `gate-evaluation-standard.md` and compress templates that implementers can reconstruct from the prose description. This achieves ~560L — within range of the 550L target.

---

## 9. Risk Matrix

| ID | Risk | Likelihood | Impact | Severity | Mitigation |
|----|------|-----------|--------|----------|------------|
| R-1 | 550L target requires template compression that reduces implementer clarity | HIGH | LOW | LOW | Gate criteria already in gate-evaluation-standard.md. Templates are examples, not contracts. |
| R-2 | Feasibility check false positives frustrate advanced users | LOW | MEDIUM | MEDIUM | Soft gate with explicit override. 3 criteria are generous (not restrictive). |
| R-3 | No PT during Phase 1 Q&A | LOW | LOW | LOW | Phase 1 is Lead-only. No teammates need PT. PT only consumed from Phase 2 onward. |
| R-4 | GC-v1 `pt_version` field breaks downstream parsing | LOW | LOW | LOW | Additive field in YAML frontmatter. No downstream skill parses individual frontmatter fields (they read content sections). |
| R-5 | Phase 2/3 sequential-thinking removal interpreted as "logic change" | MEDIUM | LOW | LOW | Removal is cross-cutting (same instruction, different location). No behavioral change. Document as "minimal cross-cutting edit" in implementation task. |
| R-6 | TRIVIAL short-circuit at 1.4 (later than current P0) wastes more Q&A time | LOW | LOW | LOW | TRIVIAL topics are rare in Agent Teams context (users invoke brainstorming-pipeline for substantial features). At worst, 5-10 minutes of Q&A for a TRIVIAL topic that could have been caught at P0. |
