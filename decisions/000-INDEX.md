# Decision Index Map

**Last Updated:** 2026-02-11T17:05  
**Total Decisions:** 17 (001–017)  
**Status Legend:** ⬜ PENDING · ✅ APPROVED · ❌ REJECTED · 🔄 SUPERSEDED

---

## Quick Reference

| ID | Title | Status | Key Finding | Depends On |
|----|-------|--------|-------------|------------|
| 001 | [Pipeline Routing Strategy](./001-pipeline-routing-strategy.md) | ⬜ PENDING | No complexity-based phase skipping exists. 3 options proposed. | — |
| 002 | [Skills vs Agents Architecture](./002-skills-vs-agents-architecture.md) | ⬜ PENDING | Skills are orchestration playbooks, not agent substitutes. Teammate=Agent enforcement missing. | 001 |
| 003 | [Skill Routing Discovery](./003-skill-routing-discovery.md) | ⬜ PENDING | 8/10 Skills not referenced in CLAUDE.md. Lead cannot self-discover Skills. | 001, 002 |
| 004 | [Agent SRP & INFRA Alignment](./004-agent-srp-infra-alignment.md) | ⬜ PENDING | 14/27 Agents have no Skill. architect/plan-writer dual-role conflict. | 002, 003 |
| 005 | [Domain-Granular Agent Decomposition](./005-domain-granular-agent-decomposition.md) | ✅ APPROVED (Option A — Full Decomposition) | Shift-Left: 15 new agents (12 workers + 3 coordinators). 27→42 agents. | 004 |
| 006 | [INFRA Code-Level Audit & Layer Boundary](./006-infra-code-audit-layer-boundary.md) | ⬜ PENDING | 18 findings (2 CRITICAL, 5 HIGH, 5 MEDIUM, 6 LOW). L1-first→L2-overlay confirmed sound. | 004, 005 |
| 007 | [Bottleneck Analysis & Layer-2 Boundary](./007-bottleneck-layer-boundary.md) | ⬜ PENDING | 7 bottlenecks identified. BN-001 (Lead Context Saturation) is CRITICAL. Definitive L1/L2 boundary table. | 005, 006 |
| 008 | [Gate Evaluation Standardization](./008-gate-evaluation-standardization.md) | ⬜ PENDING | 9 gates with inconsistent criteria. Universal 5-element gate framework + D-001-aligned severity tiers. | 005, 007 |
| 009 | [Agent Memory Architecture](./009-agent-memory-architecture.md) | ⬜ PENDING | Category-level memory (13 files vs 42). Coordinator-mediated writes. Cold start seeding. | 005, 007 |
| 010 | [Ontological Lenses Reference Design](./010-ontological-lenses-design.md) | ⬜ PENDING | ARE/RELATE/DO/IMPACT formal definition + Palantir Ontology Schema/Relationship/Behavior mapping. | 005 |
| 011 | [Cross-Phase Handoff Protocol](./011-cross-phase-handoff-protocol.md) | ⬜ PENDING | "Telephone game" prevention. Mandatory Downstream Handoff section. Reference-based directives. | 005, 007, 008 |
| 012 | [PERMANENT Task Scalability](./012-permanent-task-scalability.md) | ⬜ PENDING | PT 5→8 sections. Risk/Contract lifecycle. 42-agent read cost analysis (84K tokens). | 005, 011 |
| 013 | [Coordinator Shared Protocol](./013-coordinator-shared-protocol.md) | ⬜ PENDING | 8 coordinators × 80 shared lines = 640 lines duplication → single shared protocol. 50% file reduction. | 005, 006, 008, 009, 011 |
| 014 | [Observability & RTD Scalability](./014-observability-rtd-scalability.md) | ⬜ PENDING | 4 hooks audit (all solid). 42-agent event volume ~1000/pipeline. Session registry race (LOW). | 005, 006 |
| 015 | [Output Format Standardization](./015-output-format-standardization.md) | ⬜ PENDING | L1 canonical schema (4 mandatory keys). L2 canonical section order. Progressive adoption. | 005, 011, 013 |
| 016 | [CLAUDE.md Constitution Redesign](./016-claude-md-constitution-redesign.md) | ⬜ PENDING | v6.0→v7.0 atomic rewrite. Reference-heavy architecture. 337→400-450 lines. | 001–015 (all) |
| 017 | [Error Handling & Recovery Protocol](./017-error-handling-recovery-protocol.md) | ⬜ PENDING | 3-tier error taxonomy. 11/27 agents lack error handling. Coordinator escalation matrix. Tmux recovery. | 005, 007, 013, 014 |

---

## Decision Dependency Graph

```
D-001 (Pipeline Routing)
  │
  ├──→ D-002 (Skills vs Agents)
  │      │
  │      ├──→ D-003 (Skill Routing Discovery)
  │      │      │
  │      │      └──→ D-004 (Agent SRP & INFRA Alignment)
  │      │             │
  │      │             └──→ D-005 ✅ (Domain-Granular Agent Decomposition)
  │      │                    │
  │      │                    ├──→ D-006 (INFRA Code Audit & Layer Boundary)
  │      │                    │      │
  │      │                    │      └──→ D-007 (Bottleneck & Layer-2 Boundary)
  │      │                    │             │
  │      │                    │             ├──→ D-008 (Gate Evaluation Standardization)
  │      │                    │             │      │
  │      │                    │             │      └──→ D-011 (Cross-Phase Handoff)
  │      │                    │             │
  │      │                    │             ├──→ D-009 (Agent Memory Architecture)
  │      │                    │             │
  │      │                    │             └──→ D-011
  │      │                    │                    │
  │      │                    │                    └──→ D-012 (PT Scalability)
  │      │                    │
  │      │                    ├──→ D-010 (Ontological Lenses Design)
  │      │                    │
  │      │                    ├──→ D-013 (Coordinator Shared Protocol)
  │      │                    │      │
  │      │                    │      └──→ D-015 (Output Format Standardization)
  │      │                    │
  │      │                    ├──→ D-014 (RTD Scalability)
  │      │                    │      │
  │      │                    │      └──→ D-017 (Error Handling & Recovery)
  │      │                    │
  │      │                    └──→ D-007
  │      │
  │      └──→ D-004
  │
  └──→ D-003

  D-001 through D-015 ──→ D-016 (CLAUDE.md v7.0 Redesign) [TERMINAL]
```

---

## Detailed Contents Map

### D-001: Pipeline Routing Strategy
**File:** `001-pipeline-routing-strategy.md` (197 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §1 As-Is Analysis | §1.1–1.2 | Current hybrid state, 3 core problems (no skip criteria, distributed Skill-Phase mapping, no complexity branching) |
| §2 Options | §2.A–C | Option A: Full RTD, Option B: Tiered Fixed Pipelines, Option C: Adaptive Gates |
| §3 Comparison Matrix | — | 8-criterion comparison (speed, predictability, LLM dependency, debuggability, etc.) |
| §4 Recommendation | — | Option B (Tiered Fixed) recommended |
| §5 User Decision Items | — | 4 options + Hybrid A+B |
| §6 Claude Code Directive | — | Template, fill after decision |

**Open Questions:** Which option? If B, what tier boundaries (file count, module count)?

---

### D-002: Skills vs Agents Architecture
**File:** `002-skills-vs-agents-architecture.md` (310 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2.1 What Skills Do | — | Skill→Phase→Agent mapping table (all 10 Skills) |
| §2.2 What Skills Are NOT | — | Skills ≠ Agent definitions/identity/routing |
| §2.3 Actual Relationship | — | "HOW to orchestrate" (Skill) vs "WHO does work" (Agent) diagram |
| §2.4 Redundancy Question | — | Skills provide 7 things CLAUDE.md does not (directive templates, gates, algorithms, etc.) |
| §3 Q1: Are Skills Redundant? | — | NO — but 2 are thin (write-plan, plan-validation) |
| §4 Q2: Teammate=Agent Enforcement | — | 3 gaps found. Proposed CLAUDE.md amendment text provided |
| §5 Q3: Formal Relationship | — | Dependency direction: Skills→Agents (not reverse) |
| §6 Q4: Minimization Impact | — | Direct=zero, Indirect=significant (directive quality degrades) |
| §7 Decision Matrix | — | 4 options (Keep All / Remove Thin / Remove All / Keep+Enforce) |
| §8 CLAUDE.md Amendment | — | Exact text for "Skills↔Agents Relationship" block |

**Open Questions:** Option D (recommended) approved? Teammate=Agent text approved?

---

### D-003: Skill Routing Discovery  
**File:** `003-skill-routing-discovery.md` (191 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Discovery Mechanisms | §2.1–2.4 | 7 signals audited. Critical gap: 8/10 Skills not in CLAUDE.md |
| §3 Discovery Models | §3.1–3.2 | Current: user-initiated. Gap: no self-selection mechanism |
| §4 Analysis | §4.1–4.2 | Description sufficient for user, NOT for Lead self-selection |
| §5 Options | A–D | Status Quo / Add Index / Index+Auto / Index+Recommend |
| §6 Recommendation | — | Option B (Add Skill Index to CLAUDE.md) |
| §7 User Decision Items | — | 4 options + 3 sub-decisions |

**Open Questions:** Option B approved? Include "When to Invoke" column? Allow Lead recommendation?

---

### D-004: Agent SRP & INFRA Alignment
**File:** `004-agent-srp-infra-alignment.md` (350 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 SRP Audit | §2.1–2.3 | All 27 Agents audited. 25 PASS, 2 PARTIAL |
| §2.3.1 architect issue | — | Phase 3+4 dual role violates SRP |
| §2.3.2 plan-writer issue | — | Orphaned — Skill routes to architect instead |
| §3 INFRA Alignment Audit | §3.1–3.4 | Utilization map: 14/27 Agents have no Skill |
| §3.2 Critical Finding | — | 14 Agents listed individually with gap classification |
| §3.3 Impact Assessment | — | Skill-supported (standardized) vs Skill-less (improvised) |
| §3.4 Missing Skills Matrix | — | 4 missing Skills identified (P2b, P2d, P6+, X-cut) |
| §4 Architectural Issues | §4.1–4.3 | architect↔plan-writer, 14 Skill-less agents, catalog utilization |
| §5 Consolidated Findings | — | 25/27 SRP pass, significant INFRA gaps |
| §6 Options | A–D | Minimal Fix / Create 2 Skills / Full Coverage / Restructure |
| §7 Recommendation | — | Option B (2 missing Skills + architect fix) |

**Open Questions:** Fix architect→P3 only? Create verification Skill? Create INFRA quality Skill? Maintain 3-way verifier split?

---

### D-005: Domain-Granular Agent Decomposition ✅ APPROVED
**File:** `005-domain-granular-agent-decomposition.md` (420 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Q2 Confirmation | — | INFRA analysts: same files, different ontological lenses (ARE/RELATE/DO/IMPACT) |
| §3 Current Map | §3.1–3.2 | Well-split categories vs Monolithic categories |
| §4.1 P3 Architecture | — | SPLIT → structure-architect + interface-architect + risk-architect + architecture-coordinator |
| §4.2 P4 Planning | — | SPLIT → decomposition-planner + interface-planner + strategy-planner + planning-coordinator |
| §4.3 P5 Validation | — | SPLIT → correctness-challenger + completeness-challenger + robustness-challenger + validation-coordinator |
| §4.4 P2 Research | — | NO SPLIT — enhance coordinator with ontological tagging |
| §4.5 P2b Verification | — | Merge impact-verifier into P2b (4th dimension) |
| §4.6 P6 Implementation | — | NO SPLIT — file ownership model correct |
| §4.7 P6 Review | — | ADD contract-reviewer + regression-reviewer |
| §4.8 P7 Testing | — | SPLIT → unit-tester + contract-tester + regression-tester |
| §4.9 P8 Integration | — | NO SPLIT — inherently singular |
| §4.10 P6+ Monitoring | — | NO SPLIT — polling benefits from holistic view |
| §5 New Agent Roster | — | 12 new workers + 3 new coordinators = 15 additions (27→42) |
| §6 New Skills Required | — | 5 new Skills needed |
| §7 INFRA Impact | §7.1–7.4 | CLAUDE.md, agent-catalog, settings/hooks impact assessment |
| §8 Token Budget | — | ~3x PRE phase increase (acceptable per Shift-Left) |
| §9 Options | A–D | Full / PRE-only / Selective / Framework First |
| §10 Recommendation | — | Option D recommended, **Option A approved by user** |

**Decision:** Full decomposition. All 15 new agents + 3 coordinators.

---

### D-006: INFRA Code-Level Audit & Layer Boundary
**File:** `006-infra-code-audit-layer-boundary.md` (306 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Audit Results | §2.1–2.5 | 48 files, 18 findings by severity |
| §2.2 CRITICAL | — | F-001 (stale agent count), F-004 (architect Phase ambiguity) |
| §2.3 HIGH | — | F-006 (session registry limit), F-007 (set-e anti-pattern), F-008 (JSON construction), F-009 (ls anti-pattern), F-010 (invisible level boundary) |
| §2.4 MEDIUM | — | F-011 (coordinator boilerplate), F-012 (worker count format), F-013 (version mismatch), F-014 (hardcoded date), F-015 (wrong example), F-016 (unreferenced MCP servers) |
| §2.5 LOW | — | F-017 (YAML format), F-018 (finding ID prefix) |
| §3 Applied Fixes | — | 5 immediate fixes, 6 deferred to D-005 |
| §4 Layer-1/Layer-2 Strategy | §4.1–4.6 | User's L1→L2 strategy judged EXCELLENT. L2 Ontology schema preliminary design. 4 risks with mitigations. |
| §5 Decision Items | — | Code fixes + Layer strategy confirmation |

**Open Questions:** Apply immediate fixes? Confirm L1-first→L2-overlay? Confirm L2 sync direction?

---

### D-007: Bottleneck Analysis & Layer-2 Boundary Definition
**File:** `007-bottleneck-layer-boundary.md` (330 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Opus-4.6 Characteristics | §2.1–2.3 | 6 strengths, 7 limitations, 6 Agent Teams properties |
| §3 Bottlenecks | BN-001–BN-007 | Lead Context Saturation (CRITICAL), Coordinator Spawn Overhead (HIGH), Cross-Phase Handoff (HIGH), Gate Consistency (MEDIUM), Memory Fragmentation (MEDIUM), No Rollback (MEDIUM), Silent Skill Failure (LOW) |
| §4 Boundary Definition | §4.1–4.3 | Definitive L1/L2 table (17 capabilities mapped), Gray Zone (4 items), L2 Anti-patterns (5 from Ontology Protocol) |
| §5 Priority Actions | — | 18 items: Immediate (5), Short-term (5), Medium-term (4), Long-term (4) |
| §6 Decision Items | — | Boundary, memory, handoff, gate standard, git checkpoint, L2 priority |

**Open Questions:** Confirm L1/L2 boundary table? Category-level memory? Gate standard? Git checkpoints?

---

### D-008: Gate Evaluation Standardization
**File:** `008-gate-evaluation-standardization.md` (~280 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Gate Inventory | §2.1–2.3 | 9 existing gates audited, 4 inconsistencies (evidence, verdict taxonomy, failure recovery, evidence count) |
| §2.3 D-005 Impact | — | 3 new gates, 22 total gate events projected |
| §3 Analysis | §3.1–3.3 | Why standardization needed, why over-standardization dangerous, tiered balance point |
| §4.1 Gate Structure | — | Universal 5-element framework (Evidence/Checklist/Verdict/Justification/Downstream) |
| §4.2 Severity Tiers | — | TRIVIAL (3-item), STANDARD (5-item), COMPLEX (7-10 item) aligned with D-001 |
| §4.3 Shift-Left Profile | — | PRE 70-80%, EXEC 15-20%, POST 5-10% |
| §4.4 Per-Gate Checklists | — | Explicit checklists for all 9 gates (G0–G8) |
| §4.5 Coordinator Sub-Gates | — | Worker completion readiness check protocol |
| §5 Options | A–D | Full / PRE-only / Tiers-only / Progressive (recommended) |

**Open Questions:** Which option? Accept tiered depth? Accept per-gate checklists? CONDITIONAL needs user confirmation?

---

### D-009: Agent Memory Architecture
**File:** `009-agent-memory-architecture.md` (~300 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Current State | §2.1–2.3 | Per-agent MEMORY.md protocol, category structure (10→13) |
| §3 Options | §3.1–3.4 | Per-Agent (42 files) / Category (13 files) / Hierarchical (55 files) / Category+Tags (13, recommended) |
| §4 Merge Conflicts | §4.1–4.2 | Coordinator-mediated writes strategy |
| §5 Cold Start | §5.1–5.2 | Seed from existing agent memory vs start fresh |
| §6 Lifecycle | §6.1–6.2 | Staleness detection, 100-line soft limit |
| §7 Options Summary | — | Comparison matrix (files, cross-learning, role separation, merge safety, complexity) |

**Open Questions:** Which option? Coordinator-mediated writes? Cold start seeding? 100-line limit?

---

### D-010: Ontological Lenses Reference Design
**File:** `010-ontological-lenses-design.md` (~260 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Framework Origins | §2.1–2.3 | INFRA 4-analyst pattern, Palantir 3-layer+cross-layer alignment |
| §3 Document Structure | §3.1–3.2 | Full `ontological-lenses.md` content proposal (~150 lines), Application Matrix, Coordinator Synthesis Protocol |
| §4 Mapping Precision | §4.1–4.3 | 80% clean fit honest assessment, primary/secondary lens proposal |
| §5 L2 Connection | — | Lens→Ontology query pattern mapping |
| §6 Options | A–D | Full / Minimal / Embedded / Full+Living (recommended) |

**Open Questions:** Accept 4-lens model? Accept imperfect mapping? Include Palantir alignment? Application Matrix?

---

### D-011: Cross-Phase Handoff Protocol
**File:** `011-cross-phase-handoff-protocol.md` (~290 lines)

| Section | Lines | Content |
|---------|-------|---------|
| §2 Current State | §2.1–2.3 | Current handoff mechanism, 5 information loss points, telephone game example |
| §3 Analysis | §3.1–3.3 | What MUST survive (6 categories), what can be summarized, PT connection |
| §4 Proposed Protocol | §4.1–4.4 | Coordinator L2 Downstream Handoff section (6 categories), Lead gate→PT update protocol, reference-based directive template, information flow diagram |
| §5 Cross-Coordinator | §5.1–5.3 | Direct file handoff (optional), risk assessment |
| §6 Options | A–D | Handoff section only / Section+PT update / Full protocol (recommended) / No change |

**Open Questions:** Which option? Accept 6-category handoff section? PT update protocol? Reference-based directives? Coordinator cross-read?

---

## Cross-Decision Impact Matrix

Changes approved in one Decision propagate to others:

| If Approved... | Impacts... |
|----------------|-----------|
| D-001 Option B (Tiered) | D-003 (Skill Index must include tier mapping), D-005 (tiers determine which agents activate) |
| D-002 Option D (Keep+Enforce) | D-003 (Skill Index becomes essential), D-004 (no agents removed) |
| D-003 Option B (Skill Index) | CLAUDE.md modification required, D-001 (tiers reference Skills) |
| D-004 Option B (2 new Skills) | D-003 (Index must include new Skills), D-005 (new Skills need new agents?) |
| D-004 architect fix | D-002 (write-plan Skill changes spawn target), agent-catalog.md update |
| **D-005 ✅ Full Decomposition** | **D-004 (catalog 27→42), D-003 (8 new Skills in index), D-002 (more Skills), D-006 (new files to audit), D-007 (BN-001 worsens)** |
| D-005 ontological framework | ALL decisions — provides canonical ARE/RELATE/DO/IMPACT vocabulary |
| D-005 P3 split | D-004 (architect.md removed, 3 new agents + coordinator replace it) |
| D-005 P4 split | D-004 (plan-writer.md removed, 3 new agents + coordinator replace it) |
| D-005 P5 split | D-002 (plan-validation Skill must be rewritten for 3 challengers) |
| D-005 P2b merge | D-004 (impact-verifier moves to verification category) |
| D-006 INFRA fixes | D-007 (quality baseline established, bottlenecks partially addressed) |
| D-006 L1→L2 strategy | D-007 (boundary table formalized, L2 design sequenced) |
| D-007 BN-001 (Lead Saturation) | D-003 (Skill Index is critical mitigation), D-001 (Tiered pipeline reduces agent count per run) |
| D-007 BN-003 (Handoff) | D-005 (coordinator output format must include Downstream Handoff section) |
| D-007 BN-005 (Memory) | D-005 (new agents use category-level memory, not per-agent) |
| D-008 Gate Framework | D-011 (Downstream Impact Note feeds handoff), D-013 (coordinator sub-gate is part of shared protocol) |
| D-008 Severity Tiers | D-001 (gate depth = pipeline tier), D-005 (new gates use same framework) |
| D-009 Category Memory | D-005 (42 agents → 13 categories), D-013 (coordinator memory write is part of shared protocol) |
| D-009 Cold Start | D-005 (existing agent memory seeds new category memory) |
| D-010 Ontological Lenses | D-005 (agents reference lenses for scope verification), D-013 (coordinator synthesis references lenses) |
| D-010 Palantir Alignment | D-006 L2 strategy (lens→Ontology query pattern validates L2 design) |
| D-011 Handoff Section | D-005 (all coordinators must include it), D-008 (gate evidence collection references handoff) |
| D-011 PT Update Protocol | D-012 (PT structure must accommodate handoff categories), D-008 (gate passage triggers PT update) |
| D-011 Reference-Based Directives | D-007 BN-001 (reduces Lead paraphrase burden → mitigates context saturation) |
| D-012 PT 8-Section Structure | D-011 (handoff categories become PT sections), D-005 (sub-phase status format) |
| D-012 Risk/Contract Lifecycle | D-008 (gate passage triggers lifecycle transition), D-013 (coordinator writes risk/contract to PT) |
| D-013 Shared Protocol | D-008 (sub-gate evaluation), D-009 (memory mediation), D-011 (handoff section) |
| D-013 Coordinator Template | D-005 (3 new coordinators use template), D-016 (CLAUDE.md references shared protocol) |
| D-014 Execution Monitor Enhancement | D-005 (42 agents = 42 events files), D-015 (L1 canonical format enables automated monitoring) |
| D-014 ISS-RTD-001 | D-006 F-006 (session registry known limitation) |
| D-015 L1 Canonical Schema | D-014 (execution monitor reads L1 mandatory keys), D-009 (category memory may reference L1 patterns) |
| D-015 L2 Section Order | D-011 (Downstream Handoff = last section), D-008 (Evidence Sources placement standardized) |
| D-016 CLAUDE.md v7.0 | ALL previous decisions (D-001–D-015 must be finalized before writing v7.0) |
| D-017 3-Tier Taxonomy | D-013 (coordinator escalation matrix uses tiers), D-008 (gate failure is Tier 3) |
| D-017 Silent Failure Detection | D-008 (post-Skill validation in gate checklist), D-015 (L1 mandatory keys enable validation) |

---

## Integration Checklist (for final consolidated directive)

When all decisions are finalized:

### L1 Immediate
- [ ] CLAUDE.md §2: Pipeline routing changes (D-001)
- [ ] CLAUDE.md §new: Skills↔Agents Relationship block (D-002)
- [ ] CLAUDE.md §new: Teammate=Agent enforcement (D-002)
- [ ] CLAUDE.md §new: Skill Reference Table (D-003)
- [ ] architect.md: Phase scope change (D-004)
- [ ] agent-teams-write-plan/SKILL.md: Spawn target change (D-004)
- [ ] agent-catalog.md: Skill-supported classification + visible Level boundary (D-004, D-006)
- [ ] New Skill files: verification-orchestration, infra-quality-orchestration (D-004)
- [ ] .claude/references/ontological-lenses.md: ARE/RELATE/DO/IMPACT framework (D-005)
- [ ] .claude/references/gate-evaluation-standard.md: Minimum gate criteria (D-007)
- [ ] .claude/references/coordinator-shared-protocol.md: DRY coordinator boilerplate (D-006)

### L1 D-005 Agents (12 workers + 3 coordinators)
- [ ] architecture-coordinator.md, structure-architect.md, interface-architect.md, risk-architect.md
- [ ] planning-coordinator.md, decomposition-planner.md, interface-planner.md, strategy-planner.md
- [ ] validation-coordinator.md, correctness-challenger.md, completeness-challenger.md, robustness-challenger.md
- [ ] contract-reviewer.md, regression-reviewer.md, contract-tester.md

### L1 D-005 Skills (3 new + 2 from D-004 + 5 updated)
- [ ] architecture-orchestration/SKILL.md (P3)
- [ ] planning-orchestration/SKILL.md (P4)
- [ ] validation-orchestration/SKILL.md (P5)
- [ ] verification-orchestration/SKILL.md (P2b — from D-004)
- [ ] infra-quality-orchestration/SKILL.md (X-cut — from D-004)
- [ ] UPDATE brainstorming-pipeline (P3 routing)
- [ ] UPDATE agent-teams-write-plan (P4 routing)
- [ ] UPDATE plan-validation-pipeline (P5 routing)
- [ ] UPDATE agent-teams-execution-plan (P6 review agents)
- [ ] UPDATE verification-pipeline (P7 tester split)

### L1 D-006 INFRA Fixes
- [ ] F-007: on-rtd-post-tool.sh — remove set -e + ERR trap
- [ ] F-009: on-pre-compact.sh — ls → [ -f ]
- [ ] F-010: agent-catalog.md — visible level boundary
- [ ] F-012: coordinator worker counts standardized
- [ ] F-015: layer-boundary-model.md — correct example

### L1 D-007 Bottleneck Mitigations
- [ ] Git checkpoint instruction in delivery-pipeline

### L1 D-008 Gate Framework
- [ ] .claude/references/gate-evaluation-standard.md (D-008)
- [ ] Per-gate checklists: G0–G8 defined (D-008)
- [ ] Severity tiers: TRIVIAL/STANDARD/COMPLEX depth (D-008)
- [ ] Coordinator sub-gate protocol added to coordinator .md files (D-008)
- [ ] Existing Skills: add gate evaluation reference to brainstorming, write-plan, plan-validation, execution-plan, verification (D-008)

### L1 D-009 Agent Memory
- [ ] agent-common-protocol.md §Agent Memory: path change to category-level (D-009)
- [ ] Memory directory restructure: per-agent → per-category (D-009)
- [ ] Coordinator .md files: add memory write delegation instruction (D-009)
- [ ] Seed existing agent memory into category structure (D-009)

### L1 D-010 Ontological Lenses
- [ ] .claude/references/ontological-lenses.md: full framework document (D-010)
- [ ] Application Matrix: which categories decompose by which lenses (D-010)
- [ ] All D-005 agent .md files reference ontological-lenses.md for scope (D-010)

### L1 D-011 Handoff Protocol
- [ ] All coordinator .md files: add Downstream Handoff section requirement (D-011)
- [ ] agent-common-protocol.md: add handoff protocol for coordinators (D-011)
- [ ] Skills: add gate→PT update step after each gate PASS (D-011)
- [ ] Directive template: reference-based, not paraphrase-based (D-011)

### L1 D-012 PT Scalability
- [ ] permanent-tasks/SKILL.md §PT Description Template: add 3 sections (Active Contracts, Risk Registry, Open Questions)
- [ ] permanent-tasks/SKILL.md §Consolidation Rules: add risk/contract lifecycle rules
- [ ] Pipeline Skills Phase 0 blocks: update section header parsing for 8 sections

### L1 D-013 Coordinator Shared Protocol
- [ ] .claude/references/coordinator-shared-protocol.md: create shared protocol (~100 lines)
- [ ] Refactor 5 existing coordinators: extract shared content → reference shared protocol
- [ ] 3 new D-005 coordinators: create using coordinator template

### L1 D-014 RTD Scalability
- [ ] execution-monitor.md: update monitoring loop for 42-agent scale
- [ ] on-subagent-start.sh: add spawned_at timestamp to registry entries
- [ ] Verify delivery-pipeline handles 42-agent event archive

### L1 D-015 Output Format
- [ ] agent-common-protocol.md §Saving Your Work: add L1/L2 canonical format specification
- [ ] New D-005 agents: created with canonical format references
- [ ] Existing agents: progressive adoption on next modification

### L1 D-016 CLAUDE.md Redesign
- [ ] Pre-req: all D-001–D-015 decided
- [ ] Pre-req: all reference files created
- [ ] CLAUDE.md: v6.0 → v7.0 atomic rewrite
- [ ] Post: test pipeline run to verify Lead reads correctly

### L1 D-017 Error Handling
- [ ] agent-common-protocol.md: add §Error Handling (3-tier taxonomy)
- [ ] coordinator-shared-protocol.md (D-013): add §Error Escalation Matrix
- [ ] gate-evaluation-standard.md (D-008): add post-Skill validation checklist
- [ ] CLAUDE.md (or reference): add Lead error decision framework

### L1 Existing File Updates
- [ ] agent-common-protocol.md: agent count + Edit-capable list (D-006 F-001, F-002)
- [ ] agent-catalog.md: expanded catalog 27→42, 10→13 categories (D-005)
- [ ] CLAUDE.md agent reference tables: updated counts (D-005)
- [ ] verification-coordinator.md: add impact-verifier as 4th worker (D-005)

### L1 Code-Level Fixes Applied (this session)
- [x] F-001b: agent-common-protocol.md agent count 22→27 (stale count)
- [x] F-009b: on-pre-compact.sh redundant jq check removed (line 70)
- [x] F-006b: on-subagent-start.sh redundant jq check removed (line 34)

### L2 Preparation (Post L1 Stabilization)
- [ ] Ontology schema design: AgentDefinition, SkillDefinition ObjectTypes
- [ ] L2 sync direction decision
- [ ] SearchAround for agent routing
- [ ] ActionTypes: SpawnTeam, PassGate, RollbackPhase
