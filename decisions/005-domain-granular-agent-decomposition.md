# Decision 005: Domain-Granular Agent Decomposition (Shift-Left)

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 27 Agents · 10 Categories · Shift-Left philosophy  
**Depends on:** Decision 004 (SRP & Alignment)

---

## 1. Problem Statement

The INFRA Quality category already demonstrates a **4-dimensional domain split** pattern:
- `infra-static-analyst` — ARE (configuration, naming, schemas)
- `infra-relational-analyst` — RELATE (dependencies, coupling)
- `infra-behavioral-analyst` — DO (lifecycle, protocol compliance)
- `infra-impact-analyst` — IMPACT (ripple prediction)

**User intent:** Apply this same multi-dimensional decomposition pattern to ALL other agent categories. The user explicitly rejects token optimization in favor of Shift-Left investment — investing heavily in PRE phases (research, design, planning) to catch problems early when they are cheapest to fix.

---

## 2. Question 2 Confirmation: How INFRA Analysts Work

**Yes — all 4 INFRA analysts read the SAME `.claude/` files but extract DIFFERENT aspects:**

```
.claude/agents/architect.md (same file)
     │
     ├── infra-static-analyst reads it for:
     │   "Does YAML frontmatter match schema? Are naming conventions followed?"
     │
     ├── infra-relational-analyst reads it for:
     │   "What does this file reference? What references it? Are bidirectional refs consistent?"
     │
     ├── infra-behavioral-analyst reads it for:
     │   "Does the tool list match the role? Is the lifecycle pattern correct?"
     │
     └── infra-impact-analyst reads it for:
         "If I change this file, what cascades? How many files break?"
```

**This is the ARE/RELATE/DO/IMPACT ontological lens model:**

| Dimension | Question | Scope |
|-----------|----------|-------|
| **STATIC (ARE)** | "What IS this component?" | Configuration, naming, schema, type definitions |
| **RELATIONAL (RELATE)** | "How does it CONNECT?" | Dependencies, coupling, cross-references, interfaces |
| **BEHAVIORAL (DO)** | "What does it DO?" | Lifecycle, actions, rules, protocol compliance |
| **IMPACT (CHANGE)** | "What BREAKS if changed?" | Cascade prediction, ripple analysis, backward compatibility |

---

## 3. Current Agent Decomposition Map

### 3.1 Categories with Domain Splits (well-decomposed)

| Category | Phase | Agents | Split Basis | Depth |
|----------|-------|--------|-------------|-------|
| **Research** | P2 | codebase-researcher, external-researcher, auditor | Source type (local/web/structured) | 3-way |
| **Verification** | P2b | static-verifier, relational-verifier, behavioral-verifier | ARE/RELATE/DO ontology | 3-way |
| **INFRA Quality** | X-cut | 4 analysts | ARE/RELATE/DO/IMPACT ontology | 4-way |
| **Review (P6)** | P6 | spec-reviewer, code-reviewer | Review dimension (conformance/quality) | 2-way |

### 3.2 Categories WITHOUT Domain Splits (monolithic)

| Category | Phase | Agents | Current Split | Granularity |
|----------|-------|--------|---------------|-------------|
| **Architecture** | P3 | architect (1) | NONE | ⚠️ MONOLITHIC |
| **Planning** | P4 | plan-writer (1) | NONE | ⚠️ MONOLITHIC |
| **Validation** | P5 | devils-advocate (1) | NONE | ⚠️ MONOLITHIC |
| **Implementation** | P6 | implementer (1-4) | File ownership (parallel instances) | Instance-based, not domain-based |
| **Testing** | P7 | tester (1-2) | Component group (parallel instances) | Instance-based, not domain-based |
| **Integration** | P8 | integrator (1) | NONE | ⚠️ MONOLITHIC |
| **Impact** | P2d | impact-verifier, dynamic-impact-analyst | Time direction (post-hoc/pre-impl) | 2-way |
| **Monitoring** | P6+ | execution-monitor (1) | NONE | ⚠️ MONOLITHIC |

---

## 4. Proposed Decomposition — Phase by Phase

### Design Principle: Apply Ontological Lenses to Every Category

The ARE/RELATE/DO/IMPACT model that works for INFRA analysts and verifiers can be generalized:

```
For ANY domain, asking these 4 questions produces 4 specialized agents:
  1. STATIC:     "What ARE the components?" → inventory, classification, structure
  2. RELATIONAL: "How do they CONNECT?"    → dependencies, interfaces, contracts
  3. BEHAVIORAL: "What do they DO?"        → actions, rules, side effects, lifecycle
  4. IMPACT:     "What CHANGES when X changes?" → cascade, ripple, compatibility
```

Not all 4 dimensions apply equally to every phase. Below is a **principled evaluation** of where splits add value.

---

### 4.1 Phase 3: Architecture — SPLIT RECOMMENDED

**Current:** 1 agent (`architect`) does everything — ADRs, risk matrices, component design, interface design.

**Proposed Split (3-way):**

| New Agent | Dimension | Responsibility | Output |
|-----------|-----------|---------------|--------|
| `structure-architect` | STATIC | Component structure, module boundaries, directory layout, naming conventions | Component diagram, module map |
| `interface-architect` | RELATIONAL | API contracts, data flow, dependency graph, integration points between modules | Interface specs, dependency graph, data flow diagram |
| `risk-architect` | BEHAVIORAL + IMPACT | Risk assessment, failure mode analysis, performance characteristics, scalability concerns | Risk matrix, ADRs (decision rationale), constraint documentation |

**Why 3 not 4:** BEHAVIORAL and IMPACT are tightly coupled in architecture — risk analysis (DO: what can fail?) and cascade analysis (IMPACT: what breaks?) share the same reasoning mode. Splitting them would create artificial boundaries.

**Coordinator:** existing `architect` role repurposed as `architecture-coordinator` (or Lead-direct with 3 workers).

**Shift-Left Value:** Architecture mistakes are the costliest. Dedicated structure, interface, and risk agents ensure no dimension is shortchanged when the architect is under context pressure.

---

### 4.2 Phase 4: Planning — SPLIT RECOMMENDED

**Current:** 1 agent (`plan-writer`) produces the entire 10-section implementation plan.

**Proposed Split (3-way):**

| New Agent | Dimension | Responsibility | Plan Sections |
|-----------|-----------|---------------|---------------|
| `decomposition-planner` | STATIC | Task breakdown, file inventory, ownership assignment | §1 Summary, §3 Impact Map, §4 File Inventory |
| `interface-planner` | RELATIONAL | Interface contracts, dependency ordering, cross-boundary specs | §6 Interface Contracts, §7 Dependency Order |
| `strategy-planner` | BEHAVIORAL + IMPACT | Testing strategy, risk mitigation, rollback planning, acceptance criteria | §5 Change Spec, §8 Risk Matrix, §9 Testing Strategy, §10 Rollback |

**Why this split:** The 10-section plan naturally clusters into structure (what files?), relationships (what interfaces?), and behavior+impact (what tests? what risks?).

**Coordinator:** `planning-coordinator` (new) or Lead-direct sequential assembly.

**Shift-Left Value:** A decomposition error in §3-§4 propagates to every implementer. An interface error in §6 causes Phase 8 integration failures. Dedicated agents catch these at planning time, not implementation time.

---

### 4.3 Phase 5: Validation — SPLIT RECOMMENDED

**Current:** 1 agent (`devils-advocate`) challenges across ALL 6 categories (Correctness, Completeness, Consistency, Feasibility, Robustness, Interface Contracts).

**Proposed Split (3-way):**

| New Agent | Dimension | Challenge Categories |
|-----------|-----------|---------------------|
| `correctness-challenger` | STATIC + BEHAVIORAL | Correctness (are the specs right?), Feasibility (can this be built?) |
| `completeness-challenger` | RELATIONAL | Completeness (is anything missing?), Interface Contracts (are contracts consistent?) |
| `robustness-challenger` | IMPACT | Robustness (what about edge cases/failures?), Consistency (does it align with existing architecture?) |

**Why this split:** Each challenger examines the plan through a different failure lens. A correctness failure is fundamentally different from a robustness failure — they require different kinds of evidence and reasoning.

**Coordinator:** `validation-coordinator` (new) or Lead-direct parallel spawn.

**Shift-Left Value:** A single devils-advocate under context pressure may shortcut categories 4-6. Three dedicated challengers ensure ALL categories receive full attention.

---

### 4.4 Phase P2: Research — ALREADY SPLIT, Possible Enhancement

**Current 3-way split:** codebase-researcher (local), external-researcher (web), auditor (structured).

**Assessment:** This split is by **source type**, not by **ontological dimension**. An alternative split would be:

| Alternative Agent | Dimension | Source |
|-------------------|-----------|--------|
| `structure-researcher` | STATIC | Both local + external — what components exist, what schemas, what types |
| `relationship-researcher` | RELATIONAL | Both local + external — how components connect, what APIs, what deps |
| `behavior-researcher` | BEHAVIORAL | Both local + external — how things work, what patterns, what anti-patterns |

**Evaluation:** The current source-based split is pragmatic (different tools: Glob/Grep vs WebSearch/tavily). Switching to ontological split would lose this tool-based separation. 

**Proposed Enhancement (hybrid):** Keep source-based split BUT add research-question tagging:

```
Research Question: "What TypeORM entity definitions exist?"
  Tags: STATIC + LOCAL → assigned to codebase-researcher
  Tags: STATIC + EXTERNAL → assigned to external-researcher (if verification needed)
```

The coordinator already distributes questions by type. Adding ARE/RELATE/DO tags improves distribution quality without creating new agents.

**Recommendation: NO new agents. Enhance research-coordinator's distribution logic with ontological tagging.**

---

### 4.5 Phase P2b: Verification — ALREADY SPLIT (3-way)

**Current:** static-verifier, relational-verifier, behavioral-verifier — ARE/RELATE/DO ontology.

**Missing Dimension:** IMPACT. Currently `impact-verifier` is in a separate category (P2d).

**Proposed Enhancement:** Formally integrate `impact-verifier` as the 4th verification dimension:

| Agent | Dimension | Current Phase | Proposed |
|-------|-----------|---------------|----------|
| `static-verifier` | ARE | P2b | P2b (unchanged) |
| `relational-verifier` | RELATE | P2b | P2b (unchanged) |
| `behavioral-verifier` | DO | P2b | P2b (unchanged) |
| `impact-verifier` | IMPACT | P2d (separate) | P2b (integrated as 4th verifier) |

**Rationale:** The impact-verifier already consumes output from the other 3 verifiers. Moving it into the verification coordinator's scope makes the 4-dimensional model complete and mirrors INFRA Quality.

**Recommendation: Merge P2d impact-verifier into P2b verification-coordinator. Keep `dynamic-impact-analyst` as separate Lead-direct agent for pre-implementation prediction.**

---

### 4.6 Phase P6: Implementation — Instance-Based Split is Correct

**Current:** implementer instances split by file ownership (1-4 parallel).

**Assessment:** Implementation is inherently file-scoped. Splitting by ontological dimension (one implementer for structures, another for interfaces, another for behavior) would create overlapping file access — violating the file ownership isolation principle.

**Recommendation: NO change. Instance-based split by file ownership is the correct model for implementation.**

---

### 4.7 Phase P6: Review — ALREADY SPLIT (2-way), Possible Enhancement

**Current:** spec-reviewer (conformance), code-reviewer (quality).

**Possible 4-way split:**

| Agent | Dimension | Focus |
|-------|-----------|-------|
| `spec-reviewer` | STATIC | Does implementation match spec? (unchanged) |
| `contract-reviewer` | RELATIONAL | Are interface contracts honored across boundaries? |
| `quality-reviewer` | BEHAVIORAL | Code quality, patterns, safety (current code-reviewer) |
| `regression-reviewer` | IMPACT | Could this change break existing functionality? |

**Evaluation:** The current 2-way split (spec vs quality) maps to ARE + DO. Adding RELATIONAL (contracts) and IMPACT (regression) captures dimensions currently unchecked at review time.

**Recommendation: Add `contract-reviewer` and `regression-reviewer`. High value for Shift-Left — catching interface and regression issues during code review rather than Phase 7-8 testing.**

---

### 4.8 Phase P7: Testing — SPLIT RECOMMENDED

**Current:** tester instances split by component group (1-2 parallel). Each tester writes AND executes ALL test types.

**Proposed Split (3-way per instance group):**

| New Agent | Dimension | Test Focus |
|-----------|-----------|------------|
| `unit-tester` | STATIC + BEHAVIORAL | Unit tests — individual function behavior, edge cases, error handling |
| `contract-tester` | RELATIONAL | Integration tests — interface contracts, API compatibility, data flow between modules |
| `regression-tester` | IMPACT | Regression tests — existing functionality preserved, no unintended side effects |

**Why this split:** Different test types require different reasoning modes. A unit tester thinks about function internals. A contract tester thinks about cross-module interfaces. A regression tester thinks about pre-existing behavior.

**Coordinator:** existing `testing-coordinator` expands to manage more workers.

**Shift-Left Value:** When a single tester handles all test types, integration and regression testing often receive insufficient attention (token budget exhausted on unit tests first).

---

### 4.9 Phase P8: Integration — NO SPLIT (Inherently Singular)

**Current:** 1 integrator crosses file ownership boundaries.

**Assessment:** Integration is a unique cross-cutting responsibility. Splitting it by dimension would create coordination overhead exceeding the value. The integrator must see the WHOLE picture to resolve conflicts.

**Recommendation: NO change. Integrator remains singular.**

---

### 4.10 Phase P6+: Monitoring — SPLIT POSSIBLE

**Current:** 1 execution-monitor observes all dimensions.

**Possible Split:**

| Agent | Dimension | Monitors |
|-------|-----------|----------|
| `progress-monitor` | STATIC | Task completion %, file modification counts, time budget |
| `drift-monitor` | BEHAVIORAL | Spec compliance drift, pattern deviation |
| `conflict-monitor` | RELATIONAL + IMPACT | Ownership violation, cross-boundary modifications |

**Evaluation:** Monitoring overhead is already lightweight (polling model). Splitting into 3 monitors triples the polling reads. For monitoring (unlike research/design), the cost-benefit may be negative.

**Recommendation: NO split for monitoring. The polling model benefits from a single observer with holistic view.**

---

## 5. Summary: Proposed New Agent Roster

### New Agents (12 additions)

| # | New Agent | Phase | Dimension | Replaces/Extends |
|---|-----------|-------|-----------|-----------------|
| 1 | `structure-architect` | P3 | STATIC | Splits from `architect` |
| 2 | `interface-architect` | P3 | RELATIONAL | Splits from `architect` |
| 3 | `risk-architect` | P3 | BEHAVIORAL+IMPACT | Splits from `architect` |
| 4 | `decomposition-planner` | P4 | STATIC | Splits from `plan-writer` |
| 5 | `interface-planner` | P4 | RELATIONAL | Splits from `plan-writer` |
| 6 | `strategy-planner` | P4 | BEHAVIORAL+IMPACT | Splits from `plan-writer` |
| 7 | `correctness-challenger` | P5 | STATIC+BEHAVIORAL | Splits from `devils-advocate` |
| 8 | `completeness-challenger` | P5 | RELATIONAL | Splits from `devils-advocate` |
| 9 | `robustness-challenger` | P5 | IMPACT | Splits from `devils-advocate` |
| 10 | `contract-reviewer` | P6 | RELATIONAL | New (P6 review expansion) |
| 11 | `regression-reviewer` | P6 | IMPACT | New (P6 review expansion) |
| 12 | `contract-tester` | P7 | RELATIONAL | Splits from `tester` |

### Renamed/Repurposed Existing Agents (5 changes)

| Current Agent | Change | New Name |
|---------------|--------|----------|
| `architect` | Removed (split into 3) | — |
| `plan-writer` | Removed (split into 3) | — |
| `devils-advocate` | Removed (split into 3) | — |
| `code-reviewer` | Renamed | `quality-reviewer` (behavioral focus clarified) |
| `tester` (per instance) | Split role | `unit-tester` (static+behavioral) + `regression-tester` (impact) |

### Unchanged Agents (20 agents)

All agents not listed above remain unchanged: codebase-researcher, external-researcher, auditor, static-verifier, relational-verifier, behavioral-verifier, impact-verifier, dynamic-impact-analyst, spec-reviewer, implementer, infra-implementer, integrator, execution-monitor, 4 INFRA analysts, 5 coordinators.

### New Coordinators (3 additions)

| # | New Coordinator | Phase | Manages |
|---|----------------|-------|---------|
| 1 | `architecture-coordinator` | P3 | structure-architect, interface-architect, risk-architect |
| 2 | `planning-coordinator` | P4 | decomposition-planner, interface-planner, strategy-planner |
| 3 | `validation-coordinator` | P5 | correctness-challenger, completeness-challenger, robustness-challenger |

### Total Agent Count After Changes

| Category | Current | Proposed | Delta |
|----------|---------|----------|-------|
| Research | 3W + 1C = 4 | 4 (unchanged) | 0 |
| Verification | 3W + 1C = 4 | 4W + 1C = 5 (impact-verifier moved in) | +1 |
| Impact | 2W = 2 | 1W = 1 (dynamic-impact-analyst only) | -1 |
| Architecture | 1W = 1 | 3W + 1C = 4 | **+3** |
| Planning | 1W = 1 | 3W + 1C = 4 | **+3** |
| Review | 3W = 3 | 4W = 4 | **+1** |
| Validation | 1W = 1 | 3W + 1C = 4 | **+3** |
| Implementation | 1-4W + 1C = 2-5 | unchanged | 0 |
| Testing | 1-2W + 1C = 2-3 | 2-6W + 1C = 3-7 | **+2-4** |
| Integration | 1W = 1 | unchanged | 0 |
| INFRA Quality | 4W + 1C = 5 | unchanged | 0 |
| Monitoring | 1W = 1 | unchanged | 0 |
| **TOTAL** | **27** | **42** | **+15** |

---

## 6. New Skills Required

Each new multi-agent category needs an orchestration Skill:

| New Skill | Covers | Agents |
|-----------|--------|--------|
| `architecture-orchestration` | P3 | architecture-coordinator + 3 architects |
| `planning-orchestration` | P4 | planning-coordinator + 3 planners |
| `validation-orchestration` | P5 | validation-coordinator + 3 challengers |
| `verification-orchestration` | P2b (from D-004) | verification-coordinator + 4 verifiers (now with impact-verifier) |
| `infra-quality-orchestration` | X-cut (from D-004) | infra-quality-coordinator + 4 analysts |

**Updated Existing Skills:**
- `brainstorming-pipeline`: Update P3 section to use architecture-coordinator
- `agent-teams-write-plan`: Update to use planning-coordinator
- `plan-validation-pipeline`: Update to use validation-coordinator
- `agent-teams-execution-plan`: Add contract-reviewer, regression-reviewer to review dispatch
- `verification-pipeline`: Update tester spawning (unit-tester + contract-tester + regression-tester)

---

## 7. INFRA-Wide Impact Assessment

### 7.1 CLAUDE.md Changes

| Section | Change |
|---------|--------|
| Custom Agents Reference | Update from 27 to 42 agents, 10→13 categories, add 3 new coordinators |
| Agent table (Lines 24-59) | Add new coordinator rows, update Lead-direct table |
| Phase Pipeline §2 | Update phase-agent mapping |
| Spawning rules | Update category routing for new coordinators |

### 7.2 agent-catalog.md Changes

| Section | Change |
|---------|--------|
| WHEN to Spawn | Add routing for architecture-coordinator, planning-coordinator, validation-coordinator |
| Agent Dependency Chain | Update: research → architecture-coordinator → validation-coordinator → planning-coordinator → execution |
| Categories and Routing | Add 3 new coordinated categories |
| Agent Matrix | Add 15 new rows |
| Level 2 descriptions | Add complete descriptions for all new agents |

### 7.3 agent-common-protocol.md Changes

Minimal — new agents follow existing shared protocol. No structural changes needed.

### 7.4 settings.json / hooks Changes

NONE — new agents use existing Team infrastructure and lifecycle hooks.

---

## 8. Token Budget Analysis

**User stated:** Token optimization is NOT a priority. Shift-Left investment is the priority.

**For the record (informational only):**

| Phase | Current Agent Spawns | Proposed Agent Spawns | Token Multiplier |
|-------|---------------------|----------------------|-----------------|
| P3 Architecture | 1 agent (50 turns) | 1 coordinator + 3 workers | ~3.5x |
| P4 Planning | 1 agent (50 turns) | 1 coordinator + 3 workers | ~3.5x |
| P5 Validation | 1 agent (30 turns) | 1 coordinator + 3 workers | ~3.5x |
| P6 Review | 2 reviewers | 4 reviewers | ~2x |
| P7 Testing | 1-2 testers | 3-6 testers | ~3x |
| Total PRE increase | — | — | **~3x for PRE phases** |

**Shift-Left ROI justification:** Every issue caught in P3-P5 (PRE) avoids a much costlier fix cycle in P6-P8 (EXEC). A single architecture oversight caught at P3 by dedicated `interface-architect` prevents an integration failure at P8 that requires implementer re-spawn + re-testing.

---

## 9. Options

### Option A: Full Decomposition (All 15 New Agents + 3 Coordinators)

Implement all proposed splits as described in §5-§6.

**Pros:** Maximum Shift-Left coverage. Every Phase has ontological dimension-aware agents.  
**Cons:** Significant INFRA update effort. 42 agents to maintain.

### Option B: PRE-Only Decomposition (P3, P4, P5 Splits Only)

Split architecture (3), planning (3), validation (3) = 9 new agents + 3 coordinators.
Leave P6 review and P7 testing unchanged.

**Pros:** Shift-Left focus exactly where it matters most. EXEC phases untouched.  
**Cons:** Misses P6 contract/regression review and P7 test type specialization.

### Option C: Selective Decomposition

Pick specific splits based on observed pain points:
- Architecture split (P3): YES — costliest mistakes
- Planning split (P4): YES — most complex output (10 sections)
- Validation split (P5): MAYBE — current gates may suffice
- Review expansion (P6): YES — contract and regression gaps are real
- Testing split (P7): MAYBE — depends on test framework capabilities

**Pros:** Pragmatic, targeted investment.  
**Cons:** Inconsistent decomposition model.

### Option D: Ontological Framework First, Agents Second

Before creating agents, formalize the ARE/RELATE/DO/IMPACT ontology as a reference document (`.claude/references/ontological-lenses.md`). Then apply it incrementally:
1. Phase 1: Document the ontological framework
2. Phase 2: Split P3 (highest ROI) and validate the model
3. Phase 3: Extend to P4, P5 based on P3 learnings
4. Phase 4: Extend to P6 review, P7 testing based on need

**Pros:** Validated approach, avoids over-engineering.  
**Cons:** Slower rollout, but more sustainable.

---

## 10. Recommendation

**Option D (Ontological Framework First, Agents Second).**

**Rationale:**
1. Creating 15 agents at once risks quality inconsistency — each agent needs careful tool matrix, constraints, and output format design
2. The P3 Architecture split has the highest Shift-Left ROI — validate the pattern there first
3. The ontological reference document (`ontological-lenses.md`) becomes a reusable framework for all future agent design
4. Incremental rollout allows learning from each split before extending to the next
5. Aligns with the existing RSIL framework — the 8 Meta-Research Lenses already use a similar dimensional approach

---

## 11. User Decision Items

- [ ] **Option A** — Full decomposition (15 new agents, 3 new coordinators)
- [ ] **Option B** — PRE-only decomposition (9 new agents, 3 new coordinators)
- [ ] **Option C** — Selective decomposition (pick specific splits)
- [ ] **Option D** — Ontological Framework first, incremental agents (RECOMMENDED)

### Sub-decisions:

- [ ] Confirm ARE/RELATE/DO/IMPACT as the canonical decomposition model? (Yes/No)
- [ ] P3 Architecture split as first implementation target? (Yes/No)
- [ ] Merge impact-verifier into P2b verification-coordinator? (Yes/No)
- [ ] Add contract-reviewer and regression-reviewer to P6? (Yes/No)
- [ ] Split tester into unit/contract/regression? (Yes/No)
- [ ] Create `ontological-lenses.md` reference document? (Yes/No)

---

## 12. Claude Code Directive (Fill after decision)

```
DECISION: Option [A/B/C/D]
SCOPE:
  Phase 1: Create .claude/references/ontological-lenses.md
  Phase 2: [If D] P3 architecture split (3 new agents + coordinator)
  Phase 3: [If D] P4, P5 splits based on P3 validation
  Phase 4: [If D] P6, P7 extensions based on need
  [If A/B] All splits implemented in single batch
CONSTRAINTS:
  - Existing agent files preserved until replacement agents validated
  - Each new agent follows agent-common-protocol.md
  - Each new coordinator follows coordinator shared constraints
  - New Skills created for each new multi-agent category
  - AD-15 inviolable (no new hooks)
  - All text in English
  - Tool matrices designed per ontological dimension (read-only for STATIC/RELATIONAL analysis agents)
PRIORITY: Shift-Left quality > Coverage > Token efficiency
DEPENDS_ON: D-001 (tier mapping), D-002 (Skill necessity), D-003 (Skill index), D-004 (architect fix, missing Skills)
```
