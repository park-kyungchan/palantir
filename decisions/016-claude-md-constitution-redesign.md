# Decision 016: CLAUDE.md Constitution Redesign Plan

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 (337 lines) · D-001–D-015 combined impact · 42 agents  
**Depends on:** Decision 001–015 (all)

---

## 1. Problem Statement

CLAUDE.md is the Team Constitution — the first document Lead reads on every session.
Decisions D-001 through D-015 collectively require substantial CLAUDE.md modifications:

- D-001: Pipeline tier routing tables
- D-002: Skills↔Agents relationship block + Teammate=Agent enforcement
- D-003: Skill Reference Table
- D-005: Agent count 27→42, category count 10→13, new coordinator list
- D-008: Gate evaluation standard reference
- D-011: Handoff protocol reference
- D-012: PT section update

If each decision is applied independently, CLAUDE.md becomes a patchwork of incremental
additions. A coordinated redesign produces a cleaner, more coherent document.

**Core question:** What should the post-D-015 CLAUDE.md look like, and should we
redesign it holistically?

---

## 2. Current CLAUDE.md Structure (from code-level audit)

### 2.1 Section Map (337 lines)

| Section | Lines | Content |
|---------|:---:|---------|
| §1 Identity & Team Overview | 1-15 | Lead role definition, infrastructure version |
| §2 Phase Pipeline | 16-50 | P2-P8 phase descriptions, conditional phases |
| §3 PERMANENT Task | 51-70 | PT as SSoT, Phase 0 Block pattern |
| §4 Agent Selection & Routing | 71-140 | Agent catalog reference, tiered routing, coordinator vs lead-direct |
| §5 Communication & Messaging | 141-170 | SendMessage, broadcasting, mode switching |
| §6 Constraints & Architecture Decisions | 171-220 | AD-1 through AD-29, numbered architecture decisions |
| §7 Cross-Cutting Protocols | 221-260 | Understanding verification, RTD, DIA integration |
| §8 Security & Delivery | 261-290 | Secret management, git workflow |
| §9 Context Management | 291-337 | Compact recovery, L1/L2/L3, context pressure handling |

### 2.2 What D-001–D-015 Would Change

| CLAUDE.md Section | Decisions Impacting | Type of Change |
|-------------------|-------|----------------|
| §2 Phase Pipeline | D-001 (tier routing), D-005 (sub-phases P2a/P2b/P3a/P4a/P5a) | Major rewrite |
| §3 PERMANENT Task | D-012 (8-section PT) | Update template |
| §4 Agent Selection | D-002 (Teammate=Agent), D-003 (Skill Index), D-005 (42 agents, 13 categories) | Major expansion |
| §5 Communication | D-011 (handoff protocol reference), D-013 (coordinator shared protocol) | Add references |
| §6 Constraints/ADs | D-008 (gate standard reference), D-014 (RTD updates) | Add 3-4 new ADs |
| §7 Cross-Cutting | D-008 (gate evaluation), D-010 (ontological lenses), D-015 (output format) | Add references |
| §9 Context Mgmt | D-009 (category memory) | Update memory paths |
| NEW section | D-003 (Skill Reference Table) | New section |

### 2.3 Projected CLAUDE.md Size

| Scenario | Lines | Token Cost | Impact |
|----------|:---:|:---:|---------|
| Current (v6.0) | 337 | ~1700 | Lead reads on every start |
| Incremental patches (all Ds) | ~500+ | ~2500+ | Bloated, repetitive |
| Coordinated redesign | ~400-450 | ~2000-2200 | Clean, coherent |

---

## 3. Proposed: CLAUDE.md v7.0 Structure

### 3.1 Design Principles

1. **Lead-first:** CLAUDE.md is for Lead. Agent-specific content → reference files.
2. **Reference-heavy:** Keep CLAUDE.md as a routing document. Details in references.
3. **Hierarchical:** Top-level sections → subsection references → detail files.
4. **Scannable:** Lead should find any information in <3 levels of reading.

### 3.2 Proposed Section Structure

```markdown
# Team Constitution — CLAUDE.md v7.0

## §1 Identity & Team Architecture
- Lead role: pure orchestrator (no direct editing)
- Team composition: 42 agents across 13 categories
- Infrastructure version and reference

## §2 Pipeline Framework
- Phase Pipeline: P0 → P2a → P2b → P3 → P4 → P5 → P6 → P7 → P8 → P9
- Pipeline tiers: TRIVIAL / STANDARD / COMPLEX (D-001)
- Conditional phases: P2b, P7, P8, P9
- Gate evaluation: reference gate-evaluation-standard.md (D-008)

## §3 PERMANENT Task (Single Source of Truth)
- PT structure: 8 sections (D-012)
- Phase 0 Block pattern (no change)
- Read-Merge-Write consolidation

## §4 Skill Reference Table (NEW — D-003)
| Skill | Phases | Tier | When to Invoke |
|-------|--------|------|----------------|
(10+ Skills indexed)

## §5 Agent Selection & Routing
- Teammate = Agent enforcement (D-002)
- Agent catalog: .claude/references/agent-catalog.md
- Tiered routing: catalog Level 1 (phase scan) → Level 2 (agent detail)
- Coordinator vs Lead-direct agent types
- Categories: 13 (list)
- Ontological lenses: reference ontological-lenses.md (D-010)

## §6 Communication & Coordination
- SendMessage protocol
- Coordinator shared protocol: reference coordinator-shared-protocol.md (D-013)
- Cross-phase handoff: reference via D-011 protocol
- Broadcasting and cadence

## §7 Architecture Decisions (AD-1 through AD-N)
- Numbered decisions (existing + new from D-014)
- Constraints and prohibitions

## §8 Cross-Cutting Protocols
- Understanding verification (AD-11)
- RTD observability (D-014 updates)
- DIA integration
- Output format standard: reference agent-common-protocol.md L1/L2 (D-015)

## §9 Security & Delivery
- Secret management
- Git workflow
- Git checkpoint (D-007 BN-006)

## §10 Context Management
- Compact recovery
- Category-level agent memory: reference agent-common-protocol.md (D-009)
- L1/L2/L3 save protocol
- Context pressure handling
```

### 3.3 What Moves OUT of CLAUDE.md

| Content | Current Location | New Location | Rationale |
|---------|:---:|:---:|---------|
| Detailed agent listing | §4 (inline) | agent-catalog.md Level 1 | Already exists, just enforce |
| Gate criteria | §2 (inline per phase) | gate-evaluation-standard.md | D-008 |
| Coordinator protocol details | §5 (partially inline) | coordinator-shared-protocol.md | D-013 |
| Memory protocol details | §9 (inline) | agent-common-protocol.md §Memory | D-009 |
| Ontological lens definitions | Not present | ontological-lenses.md | D-010 |
| Output format specification | §9 (brief) | agent-common-protocol.md §Output | D-015 |

### 3.4 What Stays IN CLAUDE.md

- Lead's identity and role
- Phase pipeline overview and tier classification
- PT structure and Phase 0 pattern
- Skill Index (routing table — Lead needs this for discovery)
- Agent category listing (not individual agents)
- Architecture Decisions (ADs are the constitution's "laws")
- Security rules
- Contact pressure handling

---

## 4. Version Migration Strategy

### 4.1 Approach

CLAUDE.md v7.0 is NOT an emergency fix. It should be:
1. **Planned:** After D-001–D-015 are all decided (currently D-005 only approved)
2. **Implemented atomically:** One commit transforms v6.0 → v7.0
3. **Tested:** Run one pipeline immediately after to verify Lead reads correctly
4. **Versioned:** Increment header from v6.0 to v7.0

### 4.2 Pre-Requisites

Before writing v7.0:
- [ ] All D-001 through D-015 decided (approved/rejected)
- [ ] Reference files created: gate-evaluation-standard.md, coordinator-shared-protocol.md, ontological-lenses.md
- [ ] Agent-common-protocol.md updated with D-009/D-015 content
- [ ] Agent-catalog.md expanded with D-005 agents
- [ ] D-005 agent `.md` files created

### 4.3 Fallback

If v7.0 causes Lead confusion (unlikely with Opus-4.6), revert to v6.0 via git.
AD-15 (no structural changes without testing) applies.

---

## 5. Options

### Option A: Incremental Patches (Apply each D one-by-one)
- Each decision adds its content to CLAUDE.md when implemented
- No coordinated redesign
- Risk: bloated, incoherent document

### Option B: Full Redesign to v7.0 (Recommended)
- Coordinated redesign after all decisions are finalized
- Atomic migration v6.0 → v7.0
- Reference-heavy architecture (details pushed to reference files)

### Option C: Minimal Restructure (Reorder sections only)
- Keep current content, rearrange sections
- Add missing items without removing anything
- Less disruptive but less clean

---

## 6. User Decision Items

- [ ] Which option? (A / **B recommended** / C)
- [ ] Accept v7.0 structure per §3.2?
- [ ] Accept content migration (§3.3 — what moves out)?
- [ ] Accept pre-requisites before writing v7.0 (§4.2)?
- [ ] Accept 400-450 line target for v7.0?
- [ ] Confirm atomic migration approach (one commit)?

---

## 7. Claude Code Directive (Fill after decision)

```
DECISION: CLAUDE.md redesign — Option [X]
SCOPE:
  - CLAUDE.md: v6.0 → v7.0 atomic rewrite
  - Pre-req: all reference files created first
  - Pre-req: all D-001–D-015 decided
  - Post: test pipeline run to verify
CONSTRAINTS:
  - Section headers are interface contracts (Phase 0 blocks parse them)
  - AD numbering must be preserved (AD-1 through AD-29+)
  - v6.0 preserved in git for fallback
  - Lead must still find all critical info in <3 levels
PRIORITY: Last in sequence — depends on all other decisions
DEPENDS_ON: D-001 through D-015 (all must be finalized first)
```
