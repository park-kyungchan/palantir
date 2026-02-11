# Decision 004: Agent Catalog SRP Analysis & INFRA Alignment

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 27 Agents (22 Workers + 5 Coordinators) · 10 Categories  
**Depends on:** Decision 002 (Skills vs Agents), Decision 003 (Skill Routing)

---

## 1. Problem Statement

Two questions:

1. **Do the current 27 Agents sufficiently follow the Single Responsibility Principle (SRP)?**
2. **Is the INFRA designed so that Lead can fully utilize the Agent Catalog?**

---

## 2. SRP Audit — All 27 Agents

### 2.1 Audit Methodology

For each Agent, evaluate:
- **Responsibility statement:** Does the `.md` file define ONE clear responsibility?
- **Phase scope:** Is the Agent bound to a specific Phase or a narrow Phase range?
- **Tool surface:** Does the tool list match the responsibility (no excess, no deficit)?
- **Output boundary:** Does the Agent produce one type of output?
- **Overlap:** Does the Agent's responsibility overlap with another Agent's?

### 2.2 SRP Compliance Summary

| # | Agent | Responsibility | SRP Verdict | Notes |
|---|-------|---------------|-------------|-------|
| 1 | `codebase-researcher` | Local codebase exploration | ✅ PASS | Clear: local-only, read-only + L1/L2 write |
| 2 | `external-researcher` | External doc research | ✅ PASS | Clear: web-only, read + L1/L2 write |
| 3 | `auditor` | Structured inventory & gap analysis | ✅ PASS | Clear: quantification methodology |
| 4 | `static-verifier` | Structural claims verification | ✅ PASS | ARE claims — types, schemas, enums |
| 5 | `relational-verifier` | Relationship claims verification | ✅ PASS | RELATE claims — links, cardinality |
| 6 | `behavioral-verifier` | Behavioral claims verification | ✅ PASS | DO claims — actions, rules |
| 7 | `impact-verifier` | Correction cascade analysis | ✅ PASS | Traces WRONG/MISSING propagation |
| 8 | `dynamic-impact-analyst` | Change impact prediction | ✅ PASS | Forward-looking impact, not correction |
| 9 | `architect` | Architecture design (ADRs, risk) | ⚠️ PARTIAL | See §2.3.1 |
| 10 | `plan-writer` | Implementation plan creation | ⚠️ PARTIAL | See §2.3.2 |
| 11 | `devils-advocate` | Design critique & challenge | ✅ PASS | Clear: critique only, no modification |
| 12 | `spec-reviewer` | Spec compliance verification | ✅ PASS | Clear: read-only, evidence-mandatory |
| 13 | `code-reviewer` | Code quality assessment | ✅ PASS | Clear: quality dimensions, read-only |
| 14 | `implementer` | Application code changes | ✅ PASS | Clear: file-ownership bounded |
| 15 | `infra-implementer` | INFRA file changes | ✅ PASS | Clear: .claude/ scope only |
| 16 | `tester` | Test creation & execution | ✅ PASS | Clear: cannot modify source code |
| 17 | `integrator` | Cross-boundary conflict resolution | ✅ PASS | Clear: ONLY agent crossing boundaries |
| 18 | `execution-monitor` | Real-time drift detection | ✅ PASS | Clear: polling observer, no intervention |
| 19 | `infra-static-analyst` | INFRA config/naming integrity | ✅ PASS | ARE dimension of INFRA |
| 20 | `infra-relational-analyst` | INFRA dependency mapping | ✅ PASS | RELATE dimension of INFRA |
| 21 | `infra-behavioral-analyst` | INFRA lifecycle compliance | ✅ PASS | DO dimension of INFRA |
| 22 | `infra-impact-analyst` | INFRA change ripple prediction | ✅ PASS | Impact dimension of INFRA |
| 23 | `research-coordinator` | Research team management | ✅ PASS | Distribute + consolidate |
| 24 | `verification-coordinator` | Verification team management | ✅ PASS | Distribute + synthesize |
| 25 | `execution-coordinator` | Implementation lifecycle management | ✅ PASS | Task distribution + review dispatch |
| 26 | `testing-coordinator` | Testing lifecycle management | ✅ PASS | Sequential tester → integrator |
| 27 | `infra-quality-coordinator` | INFRA quality team management | ✅ PASS | 4-dimension parallel analysis |

### 2.3 SRP Violations Found

#### 2.3.1 `architect` — Phase 3 AND Phase 4 Dual Role

**Current state:**
- agent-catalog.md: Phase 3, 4 — "Architecture decisions needed"
- architect.md Line 4: "Phase 3-4"
- architect.md Line 54: "Phase 3-4 — plan-writer is an alternative for Phase 4 detailed planning"
- CLAUDE.md Line 36: "architect | 3, 4 | Architecture decisions, detailed design"

**SRP Concern:**
The architect serves TWO distinct purposes:
1. **Phase 3 (Architecture):** Produces ADRs, risk matrices, component designs
2. **Phase 4 (Detailed Design):** Produces 10-section implementation plan (when used via `agent-teams-write-plan` Skill)

The architect.md says "plan-writer is an alternative for Phase 4" — meaning architect and plan-writer OVERLAP in Phase 4.

**Question:** Does the architect do **architecture** (Phase 3) or **planning** (Phase 4) or **both**?

**Evidence of confusion:**
- `agent-teams-write-plan` Skill spawns `architect` (not `plan-writer`) as the primary agent for Phase 4
- But `plan-writer` exists as a separate Agent specifically for Phase 4
- The Agent Dependency Chain in agent-catalog.md shows: `architect → devils-advocate → plan-writer` — implying they are SEQUENTIAL, not alternatives
- But architect.md says they are "alternatives" for Phase 4

**Verdict: SRP PARTIAL — ambiguous Phase 4 ownership between architect and plan-writer**

#### 2.3.2 `plan-writer` — Underutilized or Redundant?

**Current state:**
- `plan-writer` is defined as "Phase 4 ONLY"
- But `agent-teams-write-plan` Skill actually spawns `architect` for Phase 4 work
- `plan-writer` appears in the dependency chain (`architect → devils-advocate → plan-writer`)
- Yet the Skill that covers Phase 4 (`agent-teams-write-plan`) does NOT use `plan-writer`

**Question:** Is `plan-writer` actually used? Or is it a dead Agent?

**Analysis:**
- `agent-teams-write-plan` Phase 4.3 says "Architect Spawn + Verification" — the Skill calls the architect, not the plan-writer
- plan-writer's role ("translates architecture decisions into actionable implementation plans") IS what the architect does in Phase 4 via the `agent-teams-write-plan` Skill
- This creates a situation where:
  - `plan-writer` has a well-defined single responsibility (10-section plan)
  - `architect` has a DUAL responsibility (architecture + planning)
  - The Skill (`agent-teams-write-plan`) uses the DUAL agent, not the SINGLE-responsibility agent

**Verdict: SRP violation is in the INFRA routing, not in the Agent definitions themselves.** Both Agents individually have clear single responsibilities. But the Skill routes to the wrong Agent for Phase 4 work, creating a de facto SRP violation for `architect`.

---

## 3. INFRA Alignment Audit — Does INFRA Enable Full Agent Utilization?

### 3.1 Agent Utilization Mapping

For each Agent, trace whether INFRA (CLAUDE.md, Skills, agent-catalog.md) explicitly directs Lead to use it:

| Agent | Referenced in CLAUDE.md? | Invoked by a Skill? | In agent-catalog "WHEN"? | Lead Can Find It? |
|-------|:---:|:---:|:---:|:---:|
| `codebase-researcher` | ✅ (table) | ✅ brainstorming, rsil | ✅ | ✅ |
| `external-researcher` | ✅ (table) | ✅ brainstorming | ✅ | ✅ |
| `auditor` | ✅ (table) | ✅ brainstorming | ✅ | ✅ |
| `static-verifier` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `relational-verifier` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `behavioral-verifier` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `impact-verifier` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `dynamic-impact-analyst` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `architect` | ✅ (table) | ✅ brainstorming, write-plan | ✅ | ✅ |
| `plan-writer` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `devils-advocate` | ✅ (table) | ✅ plan-validation | ✅ | ✅ |
| `spec-reviewer` | ✅ (table) | ✅ execution-plan | ✅ | ✅ |
| `code-reviewer` | ✅ (table) | ✅ execution-plan | ✅ | ✅ |
| `implementer` | ✅ (table) | ✅ execution-plan | ✅ | ✅ |
| `infra-implementer` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `tester` | ✅ (table) | ✅ verification | ✅ | ✅ |
| `integrator` | ✅ (table) | ✅ verification | ✅ | ✅ |
| `execution-monitor` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `infra-static-analyst` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `infra-relational-analyst` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `infra-behavioral-analyst` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `infra-impact-analyst` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `research-coordinator` | ✅ (table) | ✅ brainstorming | ✅ | ✅ |
| `verification-coordinator` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |
| `execution-coordinator` | ✅ (table) | ✅ execution-plan | ✅ | ✅ |
| `testing-coordinator` | ✅ (table) | ✅ verification | ✅ | ✅ |
| `infra-quality-coordinator` | ✅ (table) | ❌ No Skill invokes | ✅ | ⚠️ |

### 3.2 Critical Finding: 14 of 27 Agents Have No Skill

**14 Agents (52%) are not invoked by ANY Skill:**

1. `static-verifier` (Phase 2b)
2. `relational-verifier` (Phase 2b)
3. `behavioral-verifier` (Phase 2b)
4. `impact-verifier` (Phase 2d)
5. `dynamic-impact-analyst` (Phase 6+)
6. `plan-writer` (Phase 4)
7. `infra-implementer` (Phase 6)
8. `execution-monitor` (Phase 6+)
9. `infra-static-analyst` (X-cut)
10. `infra-relational-analyst` (X-cut)
11. `infra-behavioral-analyst` (X-cut)
12. `infra-impact-analyst` (X-cut)
13. `verification-coordinator` (Phase 2b)
14. `infra-quality-coordinator` (X-cut)

These Agents rely ENTIRELY on Lead's discretion + `agent-catalog.md` "WHEN to Spawn" table for activation. There is no procedural playbook (Skill) guiding their orchestration.

### 3.3 Impact Assessment

**Agents with Skills (13/27):**
- Lead reads Skill → gets directive template, gate criteria, error recovery
- Orchestration is **standardized and repeatable**
- Agent receives carefully constructed context

**Agents without Skills (14/27):**
- Lead reads CLAUDE.md §Custom Agents + agent-catalog.md → improvises directive
- Orchestration quality **depends on Lead's context window state**
- Agent receives whatever Lead constructs — no template standardization
- No procedural gate criteria for Phase 2b, 2d, or Cross-cutting quality work

**This means:**
- Phase 2b (Verification) has dedicated Agent definitions but NO orchestration Skill
- Phase 2d (Impact Analysis) has dedicated Agent definitions but NO orchestration Skill
- Cross-cutting INFRA Quality has 5 Agents (coordinator + 4 analysts) but NO orchestration Skill
- Phase 6 monitoring (`execution-monitor`) is defined but has NO activation protocol beyond "Lead-direct"

### 3.4 Missing Skills Matrix

| Phase | Agents Defined | Skill Exists? | Gap |
|-------|---------------|:---:|-----|
| P2 Research | 3 workers + coordinator | ✅ brainstorming-pipeline | — |
| P2b Verification | 3 verifiers + coordinator | ❌ | **MISSING: verification-orchestration** |
| P2d Impact | 2 analysts | ❌ | **MISSING: impact-analysis-orchestration** |
| P3 Architecture | architect | ✅ brainstorming-pipeline | — |
| P4 Design | architect, plan-writer | ✅ agent-teams-write-plan | ⚠️ Uses architect not plan-writer |
| P5 Validation | devils-advocate | ✅ plan-validation-pipeline | — |
| P6 Implementation | coordinator + workers + reviewers | ✅ agent-teams-execution-plan | — |
| P6+ Monitoring | execution-monitor | ❌ | **MISSING: monitoring-orchestration** |
| P7-8 Testing | coordinator + workers | ✅ verification-pipeline | — |
| P9 Delivery | Lead-only | ✅ delivery-pipeline | — |
| X-cut INFRA Quality | coordinator + 4 analysts | ❌ | **MISSING: infra-quality-orchestration** |
| X-cut INFRA Implementation | infra-implementer | ❌ | Agent used ad-hoc within existing Skills |

---

## 4. Architectural Issues Found

### 4.1 Issue: architect ↔ plan-writer Ambiguity

**Current:** Both can serve Phase 4. `agent-teams-write-plan` Skill uses architect. plan-writer is defined but orphaned.

**Options:**

| Option | Description | Impact |
|--------|-------------|--------|
| **A. Clarify roles** | architect = P3 ONLY, plan-writer = P4 ONLY | Requires modifying `agent-teams-write-plan` Skill to spawn plan-writer instead of architect |
| **B. Merge agents** | Absorb plan-writer into architect (Phase 3+4) | Violates SRP but matches current operational reality |
| **C. Keep both, fix routing** | architect = P3 architecture, then plan-writer = P4 detailed plan. Dependency chain: architect → plan-writer (not alternatives) | Clean SRP, requires Skill update |

**Recommendation: Option C.** The dependency chain in agent-catalog.md already shows `architect → plan-writer` as sequential. The Agent definitions already have clean SRP. The ONLY fix needed is in `agent-teams-write-plan` Skill to spawn `plan-writer` instead of `architect`, and in `architect.md` to remove "Phase 4" from its scope.

### 4.2 Issue: 14 Skill-less Agents — Are They Over-Designed or Under-Supported?

**Two interpretations:**

| Interpretation | Implication | Action |
|----------------|-------------|--------|
| **A. Over-designed** | These Agents were created speculatively and are not needed in practice. No user has ever needed a P2b verification Skill. | Remove unused Agents, simplify catalog |
| **B. Under-supported** | These Agents SHOULD have Skills but were never built. The Phase 2b, 2d, and X-cut capabilities are valuable but cannot be reliably activated. | Create missing Skills for P2b, P2d, X-cut |
| **C. Intentionally Lead-managed** | Some Agents (like execution-monitor) are designed for ad-hoc, situational use. They don't need a repeatable Skill — Lead spawns them when judgment dictates. | Add clearer "Lead-direct ad-hoc" documentation |

**Analysis:**
- **P2b Verification (static/relational/behavioral):** These are sophisticated, purpose-built agents with clear ontological separation. They appear DESIGNED for a verification pipeline that was never formalized as a Skill. → **Interpretation B**
- **P2d Impact (impact-verifier, dynamic-impact-analyst):** The impact-verifier works on correction cascades (requires P2b output). dynamic-impact-analyst works pre-implementation. Both are sequentially dependent on other phases. → **Mixed B + C**
- **X-cut INFRA Quality:** 5 agents with a dedicated coordinator. This is a fully designed team structure without a Skill. → **Interpretation B**
- **execution-monitor:** Polling-based observer with a monitoring loop. This is inherently ad-hoc (not all P6 work needs monitoring). → **Interpretation C**
- **infra-implementer:** Used within existing Pipeline Skills when .claude/ changes needed. → **Interpretation C**
- **plan-writer:** Orphaned by `agent-teams-write-plan` Skill routing to architect. → **Interpretation A (redundant in practice) or C (fix routing)**

### 4.3 Issue: Lead's Utilization of agent-catalog.md

**Question:** Does the Lead actually consult `agent-catalog.md` during pipeline execution?

**Evidence:**
- CLAUDE.md Line 67: "Full agent details and tool matrix in `agent-catalog.md`"
- CLAUDE.md Line 85: "agent-catalog.md (two-level selection: category first, then specific agent)"
- agent-catalog.md is 1416 lines long — significant context cost to read

**Problem:** Lead is told to consult agent-catalog.md, but:
1. During Skill execution, the Skill ITSELF tells Lead which agents to spawn
2. Agent-catalog.md is only needed when NO Skill is active (Lead-direct ad-hoc scenarios)
3. Reading 1416 lines for a routing decision is expensive (context budget)

**Implication:** agent-catalog.md's "Level 1" (~300 lines for routing) is the relevant portion. Level 2 (~700+ lines of detail) is only needed when constructing directives. The two-level design is correct but underutilized — Lead may not know when to use Level 1 vs Level 2.

---

## 5. Consolidated Findings

### 5.1 SRP Assessment: 25/27 PASS, 2/27 PARTIAL

**The Agent Catalog is well-designed for SRP.** The ontological separation (ARE/RELATE/DO for verifiers, static/relational/behavioral/impact for INFRA analysts) is clean and principled. Each agent has a clear, non-overlapping responsibility with one exception:

- **architect** has dual Phase 3+4 scope (SRP violation)
- **plan-writer** is orphaned by Skill routing (not an SRP violation, but a utilization gap)

### 5.2 INFRA Alignment Assessment: SIGNIFICANT GAPS

| Gap Category | Count | Severity |
|---|---|---|
| Agents without orchestration Skills | 14 / 27 | HIGH — orchestration quality depends on Lead improvisation |
| Skills not indexed in CLAUDE.md | 8 / 10 | MEDIUM — Lead cannot self-discover Skills (see Decision 003) |
| architect ↔ plan-writer routing ambiguity | 1 | MEDIUM — SRP violation in practice |
| agent-catalog.md utilization guidance | 1 | LOW — Level 1/2 usage patterns undocumented |

---

## 6. Options

### Option A: Minimal Fix — Resolve architect/plan-writer + Document Gaps

1. Fix `architect.md` to be Phase 3 ONLY
2. Fix `agent-teams-write-plan` Skill to spawn `plan-writer` for Phase 4
3. Document which Agents are "Skill-supported" vs "Lead-direct ad-hoc" in agent-catalog.md
4. No new Skills created

**Pros:** Low effort, resolves SRP violation.  
**Cons:** 14 Agents remain without orchestration guidance.

### Option B: Create Missing Skills for Critical Gaps

In addition to Option A:
1. Create `verification-orchestration` Skill (P2b)
2. Create `infra-quality-orchestration` Skill (X-cut)
3. Keep P2d and execution-monitor as Lead-direct ad-hoc (documented)

**Pros:** Critical agents get proper orchestration playbooks.  
**Cons:** 2 new Skills to design and maintain.

### Option C: Full Coverage — Skill for Every Phase

In addition to Option B:
1. Create `impact-analysis-orchestration` Skill (P2d)
2. Create `monitoring-orchestration` Skill (P6+)
3. Result: every Phase with agents has a corresponding Skill

**Pros:** Complete coverage, maximum consistency.  
**Cons:** Some Skills may be thin (P6+ monitoring is inherently ad-hoc). Over-engineering risk.

### Option D: Restructure — Merge Skill-less Agents

Remove agents that have no Skill and no clear ad-hoc use case:
1. Merge `plan-writer` into `architect` (acknowledge dual role)
2. Consider whether 3 separate verifiers + coordinator are needed without a Skill
3. Consider whether 4 separate INFRA analysts + coordinator are needed without a Skill

**Pros:** Smaller, simpler catalog. Only agents with clear activation paths survive.  
**Cons:** Loses the clean ontological separation. May need to recreate agents later.

---

## 7. Recommendation

**Option B (Create Missing Skills for Critical Gaps) + Option A fixes.**

**Rationale:**
1. The architect/plan-writer fix is straightforward and resolves the only SRP violation
2. P2b Verification (3 verifiers + coordinator = 4 agents) is the largest "Skill-less team" — it deserves a Skill
3. INFRA Quality (4 analysts + coordinator = 5 agents) is the largest "Skill-less team" — it deserves a Skill
4. P2d impact and P6+ monitoring are genuinely ad-hoc — documenting them as "Lead-direct" is sufficient
5. This bridges the gap between "27 agents designed" and "13 agents operationally supported"

**If Decision 001 selects Tiered Fixed Pipelines:** The verification Skill (P2b) would only be included in MEDIUM and COMPLEX tiers. INFRA Quality would be cross-cutting and invokable on any tier.

---

## 8. User Decision Items

- [ ] **Option A** — Minimal fix (architect/plan-writer + documentation)
- [ ] **Option B** — Create 2 missing Skills (verification, INFRA quality) (RECOMMENDED)
- [ ] **Option C** — Full coverage (Skill for every Phase)
- [ ] **Option D** — Restructure (merge Skill-less agents)

### Sub-decisions:

- [ ] Fix architect.md to Phase 3 ONLY? (Yes/No)
- [ ] Fix `agent-teams-write-plan` to spawn `plan-writer` instead of `architect`? (Yes/No)
- [ ] Document "Lead-direct ad-hoc" category in agent-catalog.md? (Yes/No)
- [ ] Is the 3-way verifier split (static/relational/behavioral) worth maintaining? (Yes/No)
- [ ] Is the 4-way INFRA analyst split worth maintaining? (Yes/No)

---

## 9. Claude Code Directive (Fill after decision)

```
DECISION: Option [A/B/C/D]
SCOPE:
  - architect.md: Remove Phase 4 from scope
  - agent-teams-write-plan/SKILL.md: Change spawn from architect to plan-writer
  - agent-catalog.md: Add "Skill-supported" vs "Lead-direct" classification
  - [If B/C]: Create verification-orchestration/SKILL.md (P2b)
  - [If B/C]: Create infra-quality-orchestration/SKILL.md (X-cut)
  - [If C]: Create impact-analysis-orchestration/SKILL.md (P2d)
  - [If C]: Create monitoring-orchestration/SKILL.md (P6+)
CONSTRAINTS:
  - Existing Agent .md files preserved (only architect.md modified)
  - No new hooks (AD-15)
  - All text in English
  - SRP verified for all modified/created Agents
PRIORITY: SRP compliance > Utilization coverage > Simplicity
DEPENDS_ON: D-001 (tier mapping), D-002 (Skill necessity), D-003 (Skill index)
```
