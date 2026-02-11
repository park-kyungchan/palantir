# Decision 012: PERMANENT Task Scalability

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 42 agents (D-005) · D-011 handoff categories · Opus-4.6 tmux  
**Depends on:** Decision 005, Decision 011

---

## 1. Problem Statement

The PERMANENT Task (PT) is the Single Source of Truth for pipeline execution. It
currently has 5 sections: User Intent, Codebase Impact Map, Architecture Decisions,
Phase Status, Constraints.

With D-005 (42 agents, 8 coordinators) and D-011 (handoff categories), the PT must
absorb significantly more information:
- **D-011 adds 5 categories** per gate passage: Decisions, Risks, Interface Contracts,
  Constraints, Open Questions
- **D-005 increases phase count** from ~7 to ~9 distinct phases
- **Gate verdicts** should be tracked for downstream reference
- **42 agents** may query PT simultaneously — context cost per query increases

**Core question:** Does the current 5-section PT structure scale, or does it need
restructuring to serve 42 agents without becoming a context bottleneck?

---

## 2. Current PT Structure (from permanent-tasks/SKILL.md §PT Description Template)

```markdown
## [PERMANENT] — PT-v{N}

### User Intent
What the user wants to achieve. Refined current state only.

### Codebase Impact Map
Module dependencies, ripple paths, interface boundaries, risk hotspots.

### Architecture Decisions
Confirmed design decisions with rationale.

### Phase Status
Pipeline progress. Phase-by-phase COMPLETE/IN_PROGRESS/PENDING.

### Constraints
Technical constraints, project rules, safety rules.
```

### 2.1 Strengths
- Clean, purpose-driven sections
- Interface contract (section headers used by Phase 0 blocks)
- Read-Merge-Write consolidation prevents bloat
- Single entity — no confusion about where truth lives

### 2.2 Scalability Concerns

| Concern | Current Impact | Post D-005/D-011 Impact |
|---------|---------------|------------------------|
| **Section overload** | 5 sections, manageable | D-011 adds 5 handoff categories per gate → 7+ gates × 5 = 35 potential items accumulating |
| **Impact Map growth** | Moderate for single-module features | Complex features with 42 agents produce much richer Impact Maps |
| **Architecture Decisions** | 3-5 ADRs typical | D-005 P3 produces 3 architect dimensions × ADRs each = potentially 9+ ADRs |
| **Phase Status** | 7 phases, single line each | 9 phases with sub-phases (P2a, P2b, P3a, P4a, P5a) = 12+ status entries |
| **Context cost per read** | ~200 lines → ~1000 tokens | ~400+ lines → ~2000+ tokens × frequent reads by 42 agents |

### 2.3 Tmux/Agent Teams Constraint

In tmux-based Agent Teams:
- Each agent runs in its own tmux pane
- TaskGet is the primary mechanism for PT access
- Multiple agents calling TaskGet simultaneously is normal
- The TASK API returns full description — no way to request partial sections
- **Every agent pays the full PT context cost on every read**

---

## 3. Analysis

### 3.1 What Agents Actually Need from PT

Not all agents need all PT sections:

| Agent Category | User Intent | Impact Map | Arch Decisions | Phase Status | Constraints | D-011 Handoff |
|----------------|:-:|:-:|:-:|:-:|:-:|:-:|
| Research (P2) | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Verification (P2b) | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Architecture (P3) | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ (P2→P3) |
| Planning (P4) | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ (P3→P4) |
| Validation (P5) | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ (P4→P5) |
| Implementation (P6) | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ (P5→P6) |
| Review (P6) | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ |
| Testing (P7) | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ (P6→P7) |
| Integration (P8) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ (P7→P8) |

**Key insight:** No agent needs the full PT. But every agent gets it because TaskGet
returns the complete description.

### 3.2 PT Size Projection

| Pipeline Tier | Current PT Lines | Post D-005/D-011 PT Lines |
|--------------|:---:|:---:|
| TRIVIAL | ~80 | ~120 |
| STANDARD | ~150 | ~250 |
| COMPLEX | ~250 | ~400+ |

A 400-line PT read by 42 agents = 42 × ~2000 tokens = ~84,000 tokens just for PT reads.
Most of these tokens are for sections the agent doesn't need.

### 3.3 Opus-4.6 Mitigation

Opus-4.6 can efficiently scan a 400-line document and focus on relevant sections.
The 200K context window means PT reads are a small fraction (~1-2%) of available context.

**This is NOT a catastrophic bottleneck.** But it is an efficiency concern that compounds
with agent count increases.

---

## 4. Proposed: PT Structure Evolution

### 4.1 Option A: Flat Structure (Current + Extensions)

Keep current 5 sections, add D-011 handoff integration:

```markdown
## [PERMANENT] — PT-v{N}

### User Intent
(no change)

### Codebase Impact Map
(no change — but grows per D-011)

### Architecture Decisions
(absorbs D-011 AD-N items)

### Active Contracts
NEW: Interface contracts from D-011 (IC-1, IC-2, ...)

### Risk Registry
NEW: Active risks from D-011 (R-1, R-2, ...)

### Phase Status
(expanded for sub-phases)

### Constraints
(absorbs D-011 C-N items + legacy constraints)

### Open Questions
NEW: Unresolved items from D-011 (OQ-1, OQ-2, ...)
```

**8 sections instead of 5.** Estimated lines: ~300-400 for COMPLEX tier.

### 4.2 Option B: Tiered PT (Summary + Detail)

Split PT into two documents:

**PT-Summary** (in Task API description — what agents read):
```markdown
## [PERMANENT] — PT-v{N}

### User Intent
(compact — 3-5 lines max)

### Key Decisions (top 5)
AD-1: ..., AD-2: ..., AD-3: ...

### Active Risks (top 3)
R-1: ..., R-2: ...

### Current Phase
P6 IN_PROGRESS | P5 COMPLETE | P7 PENDING

### Constraints
(compact — bullet points only)

### Detail Reference
Full PT detail at: .agent/teams/{team}/permanent-task-detail.md
```

**PT-Detail** (in filesystem — agents read only if needed):
```markdown
# PERMANENT Task Detail — PT-v{N}

## Full Codebase Impact Map
(complete dependency graph, ripple paths, interface boundaries)

## All Architecture Decisions
(AD-1 through AD-N with full rationale)

## All Interface Contracts
(IC-1 through IC-N with signatures)

## Full Risk Registry
(R-1 through R-N with severity and mitigation)

## Phase-by-Phase Status
(detailed per-phase with timestamps and gate verdicts)

## Open Questions
(OQ-1 through OQ-N with assignees)
```

**Pros:** Agents read compact PT (~100 lines) by default, detail only when needed  
**Cons:** Two documents to maintain, sync risk, Read-Merge-Write more complex

### 4.3 Option C: PT + Phase Context Files (Recommended)

Keep PT as Single Source of Truth (NOT split), but **offload phase-specific handoff
to filesystem**:

```markdown
## [PERMANENT] — PT-v{N}

### User Intent
(no change — refined current state)

### Codebase Impact Map
(no change — core dependency graph)

### Architecture Decisions
(all decisions — this section grows naturally)

### Active Contracts
NEW: Live interface contracts (IC-N items)

### Risk Registry
NEW: Active risks (R-N items with status: OPEN/MITIGATED/ACCEPTED)

### Phase Status
(sub-phase compatible: P2a, P2b, P3, P4, P5, P6, P7, P8, P9)

### Constraints
(all active constraints)

### Open Questions
NEW: Unresolved items requiring user or downstream resolution
```

**Phase-specific context** lives in coordinator L2 files (per D-011):
- Agents in Phase N+1 read the PT + Phase N coordinator's L2 handoff section
- PT contains the ACCUMULATED truth; L2 contains the PHASE-SPECIFIC handoff
- No duplication — PT has decisions, L2 has the reasoning that led to them

**Estimated PT size:** ~250-350 lines for COMPLEX (acceptable for Opus-4.6)

---

## 5. Consolidation Rules Update

Current Read-Merge-Write rules (3 rules: deduplicate, resolve contradictions, elevate abstraction).

**Proposed addition (2 rules):**

4. **Risk lifecycle:** Risks start as OPEN (D-011), transition to MITIGATED (when addressed
   in downstream phase) or ACCEPTED (when user decides to proceed despite risk). Remove
   MITIGATED risks after the phase that resolved them.

5. **Contract completion:** Interface contracts start as DEFINED (in P3/P4), transition to
   IMPLEMENTED (in P6) and TESTED (in P7). Remove TESTED contracts — they're now code.

These lifecycle rules prevent PT from growing unboundedly.

---

## 6. Interface Contract Update

If PT sections change, Phase 0 blocks in pipeline Skills must update their
`[PERMANENT]` parsing logic. Current interface contract:

```
Section headers are the interface contract for Phase 0 blocks and teammate TaskGet parsing.
```

**Impact of adding Active Contracts / Risk Registry / Open Questions:**
- Phase 0 blocks: minor update (3 new section headers to extract)
- Agent TaskGet: no change (agents read full description regardless)
- Read-Merge-Write: must handle 3 new sections

---

## 7. Options Summary

| Aspect | A: Flat+Extend | B: Tiered PT | **C: PT+Phase Context** |
|--------|:-:|:-:|:-:|
| PT sections | 8 | 2 (summary+detail) | **8** |
| PT lines (COMPLEX) | 300-400 | 100 (summary) + 300 (detail) | **250-350** |
| Maintenance burden | LOW | HIGH (sync 2 docs) | **LOW** |
| Agent read cost | ~2000 tokens | ~500 tokens + optional detail read | **~1500-2000 tokens** |
| D-011 integration | Direct | Split across 2 docs | **PT for accumulated, L2 for phase-specific** |
| Interface contract change | +3 sections | Major rewrite | **+3 sections** |
| Read-Merge-Write change | Minor | Major | **Minor** |

---

## 8. User Decision Items

- [ ] Which option? (A / B / **C recommended**)
- [ ] Accept 8-section PT structure (add Active Contracts, Risk Registry, Open Questions)?
- [ ] Accept risk/contract lifecycle rules for consolidation (§5)?
- [ ] Accept sub-phase status format (P2a, P2b, P3, P4, P5, P6, P7, P8, P9)?
- [ ] Is 250-350 line PT acceptable for Opus-4.6 context budget?
- [ ] Accept Phase 0 interface contract update?

---

## 9. Claude Code Directive (Fill after decision)

```
DECISION: PT scalability — Option [X]
SCOPE:
  - permanent-tasks/SKILL.md §PT Description Template: add 3 sections
  - permanent-tasks/SKILL.md §Consolidation Rules: add risk/contract lifecycle
  - Pipeline Skills Phase 0 blocks: update section header parsing
  - agent-common-protocol.md: no change (agents read full PT regardless)
CONSTRAINTS:
  - Section headers are interface contracts — change requires updating all Phase 0 blocks
  - Read-Merge-Write idempotency must be preserved
  - PT remains Single Source of Truth — no split
  - D-011 handoff is phase-specific (in L2), not PT-specific
PRIORITY: PT structure > Consolidation rules > Interface contract
DEPENDS_ON: D-011 (handoff categories define new PT sections)
```
