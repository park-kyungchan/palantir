---
version: GC-v4
pt_version: PT-v2
created: 2026-02-12
feature: skill-optimization-v9
tier: COMPLEX
---

## Scope
9 skills + related agents deep redesigned for INFRA v9.0 alignment.
Context:fork revolution for 4 Lead-only skills.
20+ files, Big Bang simultaneous change.
Full details: PT Task #1

## Phase Pipeline Status
| Phase | Status |
|-------|--------|
| P1 Discovery | COMPLETE (Gate 1 APPROVED) |
| P2 Research | COMPLETE (Gate 2 APPROVED) |
| P3 Architecture | COMPLETE (Gate 3 APPROVED) |
| P4 Design | COMPLETE (Gate 4 APPROVED — recovery) |
| P5 Validation | CONDITIONAL_PASS (4 mandatory conditions, user acceptance pending) |
| P6-P9 | PENDING |

## Architecture Summary
149 evidence points across 3 specialized architects + 1 coordinator.

**2 Skill Template Variants (ADR-S1):**
- Coordinator-based (5 Pipeline Core: brainstorming, write-plan, validation, execution, verification)
  - Prologue + A)Spawn + B)Core Workflow + C)Interface + D)Cross-Cutting
  - Consumer: Lead. Voice: third person.
- Fork-based (4 Lead-Only/RSIL: delivery, permanent-tasks, rsil-global, rsil-review)
  - Prologue (context:fork, agent:) + Phase 0 + Core Workflow + Interface + Cross-Cutting
  - Consumer: Fork agent. Voice: second person.

**PT-Centric Interface (C-1~C-5):**
- PT = sole cross-phase source of truth (all 9 skills read/write PT)
- GC 14→3: 9 eliminate (→ L2 Downstream Handoff) + 2 migrate (→ PT) + 3 keep (scratch)
- 5 contracts: PT Read/Write, L2 Handoff Chain, GC Scratch-Only, Fork-to-PT Direct, §10 Exception

**3 Fork Agent .md (D-11):**
- pt-manager: TaskCreate+Update, maxTurns 30, 3-layer history mitigation
- delivery-agent: TaskUpdate only, maxTurns 50, no nested skills, 6 user gates
- rsil-agent (shared): TaskUpdate+Task, maxTurns 50, skill body differentiates behavior

**Coordinator Convergence (D-13):**
- Template B: 768→402L (-48%, -366L), 5-section body, unified frontmatter
- memory: project (all 8), disallowedTools: 4-item (all 8)

**CLAUDE.md §10 Modification (C-5):**
- 3 named fork agents exception, 3-layer enforcement (frontmatter → agent .md NL → CLAUDE.md)

**Per-Skill Delta:**
- 61-75% unique, 8-24% template-as-is, 15-20% new (Interface Section C)
- All 9 get NEW Interface Section

## Architecture Decisions
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | Exclude palantir-dev | Non-pipeline skill | P1 |
| D-2 | All Deep Redesign | README.md as ground truth | P1 |
| D-3 | A+B only (Spawn + Prompt) | Lead Orchestration Define | P1 |
| D-4 | No compression target | YAGNI | P1 |
| D-5 | Common 1x CC research | Shared mechanism | P1 |
| D-6 | Precision Refocus (4-section) | Spawn+Directive+Interface+Cross-Cutting | P1 |
| D-7 | PT-centric interface | GC → session scratch | P1 |
| D-8 | Big Bang | Interface consistency | P1 |
| D-9 | 4 skills → context:fork | Lead context isolation | P1 |
| D-10 | CLAUDE.md §10 modification | Fork agent Task API | P1 |
| D-11 | 3 new fork agent .md | delivery-agent, rsil-agent, pt-manager | P1 |
| D-12 | Task API frontmatter-enforced | Not platform-level, NL modification only | P2 |
| D-13 | Template B convergence | Lean, protocol-referencing coordinator .md | P2 |
| D-14 | GC 14→3 reduction | 2 PT migrate + 9 L2 Handoff eliminate | P2 |
| D-15 | Custom agents in fork FEASIBLE | CC research confirmed agent: field support | P2 |
| ADR-S1 | 2 template variants | Fork complexity varies in content, not structure | P3 |
| ADR-S2 | Template B convergence (8 coord) | 45L unique review dispatch logic justified | P3 |
| ADR-S3 | memory: project for all coordinators | Project-scoped learning > user-scoped | P3 |
| ADR-S4 | Skills preload DEFERRED | Token cost unfavorable; Dynamic Context better | P3 |
| ADR-S5 | Shared rsil-agent | Same tools; skill body differentiates behavior | P3 |
| ADR-S6 | Interface Section (C) NEW | D-7 PT-centric interface needs structural home | P3 |
| ADR-S7 | Phase 0 in fork skills | Fork agent needs PT context | P3 |
| ADR-S8 | Inline cross-cutting for fork | Fork keeps inline (no CLAUDE.md in fork context) | P3 |
| C-1 | PT Read/Write contract (N:1) | All skills share one PT | P3 |
| C-2 | L2 Downstream Handoff chain | Replaces 9 GC sections | P3 |
| C-3 | GC scratch-only (3 concerns) | Metrics, gate records, version marker | P3 |
| C-4 | Fork-to-PT Direct | TaskGet/TaskUpdate from fork | P3 |
| C-5 | §10 exception (3 named agents) | Frontmatter-enforced, 3-layer | P3 |
| CLC-1 | SendMessage removed from pt-manager | No team context in fork, RISK-9 eliminated | P3 |
| OQ-1 | Fork spawning YES (85%) | Pre-deploy validation, rsil-review fallback | P3 |
| OQ-2 | 2 variants confirmed | Fork complexity varies in content, not structure | P3 |
| OQ-3 | GC elimination in v9.0 | Big Bang = right time for atomic interface change | P3 |

## Phase 4 Entry Requirements
**From arch-coord L2 §Downstream Handoff:**

Decisions Made (forward-binding):
- 2 template variants: coordinator-based (5) + fork-based (4)
- PT-centric interface: PT = sole cross-phase source of truth
- 3 fork agent .md: pt-manager, delivery-agent, rsil-agent
- §10 modification: 3 named agents, 3-layer enforcement
- 8 coordinators → Template B (768→402L)
- GC elimination in v9.0: 9 sections removed, 2 migrated, 3 kept
- Shared rsil-agent (ADR-S5), skills preload DEFERRED (ADR-S4)
- Fork cross-cutting inline (ADR-S8), SendMessage removed from pt-manager (CLC-1)

Risks (must-track):
- RISK-2 (MED-HIGH): permanent-tasks history loss — 3-layer mitigation
- RISK-3 (MEDIUM): delivery fork complexity — fork last, no nested skills
- RISK-5 (HIGH): Big Bang 22+ files — YAML validation, atomic commit, rollback
- RISK-8 (MEDIUM): Task list scope — pre-deploy validation + $ARGUMENTS fallback

Interface Contracts (must-satisfy): C-1~C-5 + Template §C format
Constraints: Big Bang atomic, YAGNI, 60-80% unique per skill, BUG-001, fork starts clean
Open Questions: Task list scope (RISK-8), fork return model (non-blocking)
Pre-deploy validation sequence: A→B→C→D (CRITICAL before production commit)

Key reference files for Phase 4:
- arch-coord L2: `.agent/teams/skill-opt-v9/phase-3/arch-coord/L2-summary.md`
- structure-architect L3: `phase-3/structure-architect-1/L3-full/structure-design.md`
- interface-architect L3: `phase-3/interface-architect-1/L3-full/interface-design.md`
- risk-architect L3: `phase-3/risk-architect-1/L3-full/risk-design.md`

## Constraints
- YAGNI only (no compression target)
- Big Bang (simultaneous, interface consistency)
- BUG-001: mode "default" always
- palantir-dev excluded
- Worker agent .md files NOT in scope
