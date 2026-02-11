# Decision 010: Ontological Lenses Reference Design

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · D-005 approved · ARE/RELATE/DO/IMPACT framework  
**Depends on:** Decision 005

---

## 1. Problem Statement

D-005 proposes agent decomposition based on an ontological framework:
ARE (Structure), RELATE (Connections), DO (Behavior), IMPACT (Consequences).

This framework is referenced throughout D-005 but has no formal definition document.
Without a canonical reference:

1. New agents cannot understand WHAT their ontological dimension means
2. Coordinators cannot verify whether workers are staying within their dimension
3. The framework cannot be applied to future decomposition decisions
4. The connection to Palantir Ontology's Schema/Relationship/Behavior layers is implicit

**Core question:** What goes into `ontological-lenses.md`, and how does it connect
the INFRA framework to the Palantir Ontology framework?

---

## 2. Framework Origins

### 2.1 INFRA Pattern: 4 INFRA Analysts

The ARE/RELATE/DO/IMPACT model emerges from the existing INFRA Quality category:

| Agent | Lens | What It Asks |
|-------|------|-------------|
| `infra-static-analyst` | **ARE** | "What IS this? Structure, schema, naming, types" |
| `infra-relational-analyst` | **RELATE** | "How does this CONNECT? Dependencies, coupling, references" |
| `infra-behavioral-analyst` | **DO** | "What does this DO? Lifecycle, permissions, protocols" |
| `infra-impact-analyst` | **IMPACT** | "What CHANGES if this changes? Ripple, cascade, risk" |

### 2.2 Palantir Ontology Pattern: 3 Layers + Cross-Layer

From `ontology-communication-protocol.md` §2:

| Ontology Layer | Maps to Lens | Components |
|---------------|-------------|-----------|
| **Schema Layer** | **ARE** | ObjectType, Property, SharedProperty — "What entities exist and what are their attributes?" |
| **Relationship Layer** | **RELATE** | LinkType, Interface — "How do entities connect and share shape?" |
| **Behavior Layer** | **DO** | ActionType, Function, Constraint — "What operations modify the system?" |
| **Cross-Layer Critical Edges** | **IMPACT** | PrimaryKey propagation, cardinality change, FK→LinkType — "What breaks when this changes?" |

### 2.3 Alignment Table

| INFRA Lens | Ontology Layer | Key Question | Analysis Method | Output Type |
|-----------|---------------|-------------|-----------------|-------------|
| **ARE** | Schema | "What IS this component?" | Glob + Read + Compare naming/types | Structural inventory |
| **RELATE** | Relationship | "How does it CONNECT?" | Grep cross-references + Read both sides | Dependency map |
| **DO** | Behavior | "How does it BEHAVE?" | Read lifecycle + Verify permissions | Protocol compliance |
| **IMPACT** | Cross-Layer | "What HAPPENS if changed?" | Sequential-thinking + Grep cascade | Impact checklist |

---

## 3. Proposed Reference Document Structure

### 3.1 Document: `.claude/references/ontological-lenses.md`

```markdown
# Ontological Lenses — Analysis Framework Reference

## Purpose
This document defines the 4-dimensional analysis framework used across
all multi-agent analysis categories. Every category that uses dimension-based
decomposition references this framework.

## The Four Lenses

### ARE (Structural / Static Analysis)
**Question:** "What IS this component? What does it contain?"
**Focus:** 
  - Naming conventions and consistency
  - Type systems and schemas
  - Configuration structure
  - File organization and hierarchy
  - Attribute completeness

**Example prompts for agents:**
  - "List all properties of this ObjectType and verify types"
  - "Does this agent's YAML frontmatter contain all required fields?"
  - "Are naming conventions consistent across all files in this category?"

**Tools emphasis:** Glob (discovery), Read (inspection), Grep (pattern matching)

**Palantir Ontology equivalent:** Schema Layer (ObjectType, Property, SharedProperty)

---

### RELATE (Relational / Dependency Analysis)
**Question:** "How does this component CONNECT to others?"
**Focus:**
  - Reference integrity (A→B exists, B knows about A)
  - Dependency direction and coupling
  - Interface contracts between components
  - Cardinality and multiplicity
  - Import/export relationships

**Example prompts for agents:**
  - "What files reference this component? Do they reference it correctly?"
  - "Is the dependency bidirectionally documented?"
  - "Does the interface contract match what the consumer expects?"

**Tools emphasis:** Grep (find references), Read (verify both sides),
  Sequential-thinking (chain reasoning: A→B→C)

**Palantir Ontology equivalent:** Relationship Layer (LinkType, Interface)

---

### DO (Behavioral / Lifecycle Analysis)
**Question:** "What does this component DO? How does it behave?"
**Focus:**
  - Lifecycle phases (creation → use → modification → deletion)
  - Permission model (who can do what)
  - Protocol compliance (does it follow stated procedures?)
  - Side effects and mutations
  - Tool usage patterns

**Example prompts for agents:**
  - "Does this agent follow the spawn→understand→plan→execute→output lifecycle?"
  - "Are disallowedTools correctly preventing unauthorized actions?"
  - "Does this ActionType's behavior match its declared rules?"

**Tools emphasis:** Read (inspect behavior), Grep (verify compliance patterns)

**Palantir Ontology equivalent:** Behavior Layer (ActionType, Function, Constraint)

---

### IMPACT (Consequence / Cascade Analysis)
**Question:** "What HAPPENS in the system if this component changes?"
**Focus:**
  - Direct effects (immediate consumers of this component)
  - Cascade effects (transitive downstream impacts)
  - Risk severity (how many things break?)
  - Change reversibility (can the change be undone?)
  - Mitigation requirements (what must be updated alongside?)

**Example prompts for agents:**
  - "If this file changes, what other files need updating?"
  - "What is the blast radius of changing this interface?"
  - "Can this change be made safely without coordination?"

**Tools emphasis:** Grep (find all references), Read (assess each),
  Sequential-thinking (reason about cascades), PT Impact Map (NL dependency graph)

**Palantir Ontology equivalent:** Cross-Layer Critical Edges
  (PrimaryKey propagation, cardinality change effects)

---

## Applying the Framework

### When to Decompose by Lens
A category should use lens-based decomposition when:
1. The analysis target is complex enough to warrant multiple perspectives
2. Different dimensions require different expertise or tool emphasis
3. Cross-dimension synthesis reveals issues invisible to any single dimension
4. Parallel analysis is possible (dimensions are independent)

### When NOT to Decompose
A category should NOT decompose when:
1. The analysis target is singular/atomic (e.g., single-file analysis)
2. File ownership makes decomposition unnecessary (implementation phase)
3. The task is inherently holistic (integration, monitoring)
4. A single agent can cover all dimensions within context budget

### Application Matrix (D-005 Aligned)

| Category | ARE | RELATE | DO | IMPACT | Decomposed? |
|----------|:---:|:------:|:--:|:------:|:-----------:|
| Architecture (P3) | structure-architect | interface-architect | — | risk-architect | ✅ 3-way |
| Planning (P4) | decomposition-planner | interface-planner | strategy-planner | — | ✅ 3-way |
| Validation (P5) | correctness-challenger | — | completeness-challenger | robustness-challenger | ✅ 3-way |
| Research (P2) | — | — | — | — | ❌ Enhanced coordinator |
| Verification (P2b) | static-verifier | relational-verifier | behavioral-verifier | impact-verifier | ✅ 4-way |
| INFRA Quality (X-cut) | infra-static | infra-relational | infra-behavioral | infra-impact | ✅ 4-way |
| Review (P6) | spec-reviewer | contract-reviewer | code-reviewer | regression-reviewer | ✅ 4-way |
| Testing (P7) | unit-tester | contract-tester | — | regression-tester | ✅ 3-way |
| Implementation (P6) | — | — | — | — | ❌ File ownership |
| Integration (P8) | — | — | — | — | ❌ Singular |
| Monitoring (P6+) | — | — | — | — | ❌ Holistic |

### Coordinator Synthesis Protocol
When a coordinator manages lens-decomposed workers:
1. Distribute one dimension per worker
2. After all workers complete: read ALL worker L2 reports
3. Cross-dimension synthesis: check if findings in Lens A affect Lens B
4. Consolidated L2 must include "Cross-Dimension Findings" section
5. Flag any cross-dimension conflicts for Lead resolution
```

### 3.2 Size and Scope

**Estimated size:** ~150 lines  
**Purpose:** Agent-readable reference (agents Read this file when starting work)  
**Audience:** Coordinators (for dimension distribution), Workers (for scope verification),
Lead (for routing decisions), RSIL review (for applying lenses)

---

## 4. Mapping Precision: Are the Lenses Perfect?

### 4.1 Gaps in the 4-Lens Model

| Category | Expected Lens | Actual Agent Focus | Gap |
|----------|--------------|-------------------|-----|
| P3 Architecture | structure=ARE, interface=RELATE, risk=IMPACT | risk-architect focuses on "what could go wrong" which is IMPACT+predictive | Risk is IMPACT-adjacent but includes speculative reasoning |
| P4 Planning | decomposition=ARE, interface=RELATE, strategy=DO | strategy-planner focuses on "how to execute" which is DO+meta-level | Strategy is DO-adjacent but includes orchestration |
| P5 Validation | correctness=ARE, completeness=DO, robustness=IMPACT | correctness-challenger checks "is the plan correct?" which is ARE+verification | Correctness is ARE-adjacent but includes negative testing |

### 4.2 Is the Mapping Forced?

**Honest assessment:** The mapping is approximately 80% clean. Some agents map to a primary
lens with a secondary influence. This is acceptable because:

1. The lenses are ANALYTICAL PERSPECTIVES, not rigid categories
2. An agent can PRIMARILY focus on one lens while acknowledging adjacent lenses
3. Cross-dimension synthesis by the coordinator catches inter-lens issues
4. The alternative (perfect mapping with more lenses) would create too many agents

### 4.3 Proposed Resolution

In the reference document, explicitly note the primary and secondary lens:

```
| Agent | Primary Lens | Secondary Lens | Note |
|-------|:---:|:---:|------|
| risk-architect | IMPACT | ARE | Analyzes structural risks, not just pure cascade |
| strategy-planner | DO | RELATE | Strategy includes execution coordination |
| correctness-challenger | ARE | DO | Checks structural correctness through negative cases |
```

This preserves the 4-lens model while acknowledging real-world nuance.

---

## 5. Connection to Layer-2 (Palantir Ontology)

When L2 is implemented, the ontological lenses map directly to Ontology query patterns:

| Lens | L2 Query Pattern |
|------|-----------------|
| ARE | `SearchAround(ObjectType WHERE category="X") → Property` — "What properties does this entity have?" |
| RELATE | `SearchAround(ObjectType) → LinkType → ObjectType` — "What is this connected to?" |
| DO | `SearchAround(ObjectType) → ActionType → Function` — "What operations affect this?" |
| IMPACT | `SearchAround(ObjectType) → LinkType → ... (depth 3)` — "What is transitively affected?" |

This alignment is NOT coincidental — the INFRA lenses were implicitly designed
to mirror Ontology layers. Making this explicit in the reference document strengthens
the L1→L2 migration path.

---

## 6. Options

### Option A: Full Reference Document (as §3.1)
- Create the complete `ontological-lenses.md` with all sections
- Include Application Matrix and Coordinator Synthesis Protocol
- Reference Palantir Ontology alignment explicitly

### Option B: Minimal Reference (Definitions Only)
- Create `ontological-lenses.md` with only the 4 lens definitions
- No Application Matrix (leave mapping to individual agent .md files)
- No Palantir Ontology alignment (keep layers separate)

### Option C: Embedded in Agent Catalog (No Separate File)
- Add lens definitions directly to `agent-catalog.md` Level 2
- Each agent entry references its lens inline
- No separate reference file

### Option D: Full Document + Living Standard (Recommended)
- Create the full reference document (§3.1)
- Mark the Application Matrix as "living" — updated whenever new agents are added
- Include Palantir alignment as "Future L2 Mapping" section
- Version the document with CLAUDE.md version bumps

---

## 7. User Decision Items

- [ ] Which option? (A / B / C / **D recommended**)
- [ ] Accept the 4-lens model (ARE/RELATE/DO/IMPACT)?
- [ ] Accept the primary/secondary lens mapping for imperfect fits (§4.3)?
- [ ] Include explicit Palantir Ontology alignment in the document?
- [ ] Accept the Application Matrix per D-005 approved splits?
- [ ] Accept the Coordinator Synthesis Protocol?

---

## 8. Claude Code Directive (Fill after decision)

```
DECISION: Ontological Lenses reference — Option [X]
SCOPE:
  - Create .claude/references/ontological-lenses.md
  - Contains: 4 lens definitions, application matrix, coordinator protocol
  - Referenced by: all D-005 agent .md files, coordinator .md files
  - Living standard: updated with agent additions
CONSTRAINTS:
  - ~150 lines (agent-readable, not Lead-only)
  - Lenses are analytical perspectives, not rigid boundaries
  - Primary/secondary mapping for imperfect fits
  - Palantir Ontology alignment is informational, not binding
PRIORITY: Lens definitions > Application Matrix > Palantir alignment
DEPENDS_ON: D-005 (agent list determines Application Matrix)
```
