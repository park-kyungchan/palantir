# Ontology Progressive Learning System — Architecture Design (Phase 3)

> **Date:** 2026-02-10
> **Author:** Phase 3 Researcher (Architecture Analysis)
> **PT:** #3 PT-v3 — Ontology Progressive Learning System
> **Inputs:** Communication Protocol ref (388L), Corrections tracker (147L), Sequential Protocol (437L), Brainstorming SKILL.md (581L), RTDI Assessment (660L), Bridge Handoff (444L)
> **Continues:** AD-1 through AD-7 from Phase 1-2

---

## 1. System Overview

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MEMORY.md System Prompt (~15L, always loaded)                          │
│  ┌──────────────────────────────────────┐                               │
│  │ "Ontology Communication Protocol     │                               │
│  │  [PERMANENT]" section                │──── TRIGGER ────┐             │
│  │  • 4-step pattern reminder           │                  │             │
│  │  • 3-layer knowledge classification  │                  │             │
│  │  • Topic dependency chain index      │                  ▼             │
│  └──────────────────────────────────────┘        ┌─────────────────┐    │
│                                                  │  Opus 4.6       │    │
│                                                  │  Response Engine │    │
│                                                  │  (interprets    │    │
│                                                  │   protocol)     │    │
│                                                  └────────┬────────┘    │
│                                                           │              │
│                       ON-DEMAND LOAD (when protocol fires) │              │
│                       ┌───────────────────────────────────┘              │
│                       ▼                                                  │
│  ┌──────────────────────────────────────────┐                           │
│  │  Reference Doc (~388L)                    │                           │
│  │  .claude/references/ontology-             │                           │
│  │  communication-protocol.md                │                           │
│  │  • §1: TEACH→IMPACT ASSESS→RECOMMEND→ASK │                           │
│  │  • §2: Verified Dependency Map            │                           │
│  │  • §3: Anti-Pattern Catalog (25+)         │                           │
│  │  • §4: Decision Tree Index                │                           │
│  │  • §5: Scale Limits                       │                           │
│  │  • §6: 3-Layer Classification             │                           │
│  │  • §7: Component Definition Order         │                           │
│  └──────────────────────────────────────────┘                           │
│                                                                          │
│  ┌──────────────────────────────────────────┐                           │
│  │  Ontology Docs (~15K lines total)         │                           │
│  │  park-kyungchan/.../docs/                 │  ◄── SELECTIVE LOAD       │
│  │  • 9 primary docs (ontology_1~9.md)       │      (per-topic sections) │
│  │  • 6 bridge-reference files               │                           │
│  └──────────────────────────────────────────┘                           │
│                                                                          │
│  ┌──────────────────────────────────────────┐                           │
│  │  Brainstorming Pipeline                   │                           │
│  │  .claude/skills/brainstorming-pipeline/    │                           │
│  │  • Phases 0-3 orchestration               │  ◄── VEHICLE              │
│  │  • Q&A + Research + Architecture           │      (where learning      │
│  │  • Rule 7: TEACH→CONTEXTUALIZE→ASK        │       happens in practice)│
│  └──────────────────────────────────────────┘                           │
│                                                                          │
│  ┌──────────────────────────────────────────┐                           │
│  │  State Carriers                           │                           │
│  │  • PT-v{N}: Topic completion status       │  ◄── IMPLICIT STATE       │
│  │  • Design files: docs/plans/*.md          │      (no tracking system)  │
│  │  • MEMORY.md topic chain index            │                           │
│  └──────────────────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

1. **Zero New Infrastructure:** The system uses existing INFRA v7.0 mechanisms — no new hooks (AD-15), no new file types, no new APIs.
2. **Two-Tier Knowledge:** Always-loaded trigger (MEMORY.md, 15L) + on-demand detail (reference doc, 388L).
3. **Protocol-Driven, Not State-Driven:** Learning emerges from the Communication Protocol's response pattern, not from tracking what the user knows (AD-1).
4. **Budget-Conscious:** Reference doc loading is gated by actual need, not preemptive.
5. **Backward-Compatible:** All changes are additive to existing INFRA v7.0 artifacts.

---

## 2. Protocol Activation Architecture (Q1)

### 2.1 The Activation Problem

The Communication Protocol must activate "whenever Ontology/Foundry concepts arise"
(reference doc §1, line 11). But the reference doc (388L) is NOT in the system prompt.
Only the MEMORY.md section (~15L) is always loaded.

**Core tension:** Loading 388L on every Ontology mention costs ~3000-4000 tokens of context.
NOT loading it means Opus must rely on its parametric knowledge, which may produce
unverified or incorrect Palantir-specific facts.

### 2.2 Three-Mode Activation Design

The key insight is that MEMORY.md's 15L already contains sufficient information to
execute a basic TEACH pattern (4-step name, 3-layer classification, topic chain).
The reference doc is needed only when specific verified facts are required. This
creates **three activation modes**, not a binary load/don't-load decision.

```
User prompt arrives
       │
       ▼
┌──────────────────────────────────────┐
│ MEMORY.md Trigger (~15L, always)     │
│                                      │
│ DECISION: Does this prompt involve   │
│ Ontology/Foundry concepts?           │
└──────────┬───────────────────────────┘
           │
      ┌────┴────────────────────────────┐
      NO                                YES
      │                                 │
      ▼                          ┌──────┴──────────────────┐
   Normal                        │ What level of detail     │
   response                      │ does the response need?  │
                                 └──────┬──────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              PASSING MENTION     FOCUSED QUESTION    BRAINSTORMING
              ("like a Foundry    ("What types can     (T-0~T-4
               ObjectType")        Properties be?")    sessions)
                    │                   │                   │
                    ▼                   ▼                   ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │ MODE 1:          │ │ MODE 2:          │ │ MODE 3:          │
          │ MEMORY-Only      │ │ Section-Selective│ │ Full-Load        │
          │                  │ │                  │ │                  │
          │ ~150 tokens      │ │ ~1200-2100 tok   │ │ ~3500 tokens     │
          │                  │ │                  │ │                  │
          │ Apply TEACH from │ │ Load ONLY the    │ │ Load entire      │
          │ MEMORY.md:       │ │ sections needed: │ │ reference doc    │
          │ • Label layers   │ │ §6 for TEACH     │ │ at session start │
          │   A/B/C          │ │ §2 for IMPACT    │ │                  │
          │ • Note reference │ │ §3 for RECOMMEND │ │ All 4 protocol   │
          │   doc exists     │ │ §4 for decisions │ │ steps with full  │
          │ • Basic pattern  │ │ §5 for scale     │ │ reference        │
          └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 2.3 Reference Doc Section Map for Selective Loading

| Section | Lines | ~Tokens | Protocol Step | Load When |
|---------|-------|---------|---------------|-----------|
| §1 Pattern description | 1-46 | ~450 | — | MEMORY.md already covers this |
| §2 Dependency map | 48-101 | ~500 | IMPACT ASSESS (Axis 1: Component Chain) | Question involves component relationships |
| §3 Anti-pattern catalog | 103-149 | ~450 | RECOMMEND (anti-pattern avoidance) | User making a design decision |
| §4 Decision tree index | 151-200 | ~500 | RECOMMEND (decision tree navigation) | Classification question (OT? Struct? Link?) |
| §5 Scale limits | 202-244 | ~400 | IMPACT ASSESS (Risk 4: Performance) | Performance or constraint question |
| §6 3-layer classification | 246-286 | ~400 | TEACH (layer distinction detail) | Any concept explanation |
| §7 Component order | 287-314 | ~250 | Session ordering context | Session start or ordering question |
| §8 Corrections + URLs | 316-388 | ~600 | — (provenance) | Fact verification or source citation |

**Section-selective loading examples:**
- "What is an ObjectType?" → Load §6 (TEACH) + §4 (RECOMMEND decision tree) = ~900 tokens
- "Can an ObjectType reference itself?" → Load §2 (self_referential edge) = ~500 tokens
- "Is struct nesting allowed?" → Load §3 (P-2 anti-pattern) + §5 (Struct limits) = ~850 tokens
- "What should our PK strategy be?" → Load §2 + §3 + §4 = ~1450 tokens

### 2.4 When to Use Each Mode

| Context | Mode | Rationale |
|---------|------|-----------|
| Brainstorming session (T-0~T-4) | **Mode 3: Full-Load** | All sections needed across multi-turn Q&A |
| Specific Ontology concept question | **Mode 2: Section-Selective** | Load §6 + step-relevant sections only |
| User mentions Foundry in passing | **Mode 1: MEMORY-Only** | 3-layer label from MEMORY.md sufficient |
| Lead writing PT updates | **Mode 1** | Administrative, not teaching |
| Researcher producing L2 | **Mode 2 or 3** | Cross-verify against specific sections |
| Agent mid-implementation | **Mode 1** | Uses design files, not teaching protocol |

**Decision heuristic:** If the response needs to CITE a specific verified fact (anti-pattern
ID, scale limit number, dependency edge, decision tree question), use Mode 2 or 3. If the
response only needs to LABEL knowledge layers or ACKNOWLEDGE Ontology concepts exist, Mode 1
is sufficient.

### 2.5 Context Cost Analysis

| Artifact | Lines | Tokens | Mode 1 | Mode 2 | Mode 3 |
|----------|-------|--------|--------|--------|--------|
| MEMORY.md section | 15L | ~150 | YES | YES | YES |
| Reference §6 (TEACH) | 40L | ~400 | — | YES | YES |
| Reference §2 (IMPACT) | 53L | ~500 | — | if needed | YES |
| Reference §3 (RECOMMEND) | 47L | ~450 | — | if needed | YES |
| Reference §4 (RECOMMEND) | 50L | ~500 | — | if needed | YES |
| Reference §5 (IMPACT) | 43L | ~400 | — | if needed | YES |
| Reference §7 (order) | 28L | ~250 | — | if needed | YES |
| **Protocol cost** | | | **~150** | **~1200-2100** | **~3500** |
| Ontology doc section | 100-300L | 1000-2500 | — | — | if needed |
| Bridge reference | 500-800L | 4000-6000 | — | — | rare |

**Weighted interaction model (estimated usage distribution):**
- 70% of sessions: No Ontology mention → Mode 1 or inactive → ~0-150 tokens
- 20% of sessions: Focused Ontology question → Mode 2 → ~1200-2100 tokens
- 10% of sessions: Brainstorming → Mode 3 → ~3500-5150 tokens
- **Average overhead: ~500 tokens/session** (vs 3500 if always full-loading)

### 2.6 Architecture Decision

**AD-8: Three-Mode Protocol Activation** (refined from PQ-1 analysis)
- **Mode 1 — MEMORY-Only (~150 tokens):** For passing mentions. MEMORY.md's 15L provides pattern name, 3-layer labels, and reference doc path. Opus labels knowledge layers and acknowledges concepts. No Read call needed.
- **Mode 2 — Section-Selective (~1200-2100 tokens):** For focused questions. Opus loads only the reference doc sections needed for the specific protocol steps in the response. §6 for TEACH, §2/§5 for IMPACT ASSESS, §3/§4 for RECOMMEND. 1-3 targeted Read calls.
- **Mode 3 — Full-Load (~3500 tokens):** For brainstorming sessions (T-0~T-4). Full reference doc loaded once at session start. All sections available for multi-turn Q&A without repeated reads.
- **Decision heuristic:** Need to CITE a specific verified fact → Mode 2+. Multi-turn Ontology discussion → Mode 3. Everything else → Mode 1.
- Rationale: Average overhead drops from ~3500 to ~500 tokens/session. MEMORY.md alone IS sufficient for basic TEACH pattern. Verified facts require the reference doc, but rarely all 388L at once.

---

## 3. Brainstorming Integration (Q2)

### 3.1 Current State: Two Overlapping Patterns

The system currently has two teaching patterns that partially overlap:

| Aspect | Brainstorming Rule 7 | Communication Protocol |
|--------|---------------------|----------------------|
| Source | Sequential Protocol §5, Rule 7 | Reference doc §1 |
| Pattern | TEACH → CONTEXTUALIZE → ASK | TEACH → IMPACT ASSESS → RECOMMEND → ASK |
| Scope | During brainstorming sessions | Whenever Ontology concepts arise |
| Depth | Light — "explain concepts before asking" | Deep — 3-axis impact analysis, 4 risk dimensions |
| Target | Lead guiding user through Q&A | Any Opus response on Ontology topics |

### 3.2 Resolution: Protocol Subsumes Rule 7

The Communication Protocol is a **superset** of Rule 7. Rule 7's "TEACH → CONTEXTUALIZE → ASK" maps directly to the first, second, and fourth steps of the full protocol:

```
Rule 7 simplified:              Communication Protocol (full):
TEACH                     →     TEACH (with 3-layer distinction)
CONTEXTUALIZE             →     IMPACT ASSESS (3 axes, 4 risks)
(implicit)                →     RECOMMEND (decision tree + anti-patterns)
ASK                       →     ASK (2-3 options with trade-off profiles)
```

**During brainstorming sessions**, Lead should use the **full Communication Protocol** instead of the simplified Rule 7. The protocol provides richer teaching (3-layer distinction), structured impact assessment (dependency map traversal), and evidence-based recommendations (anti-pattern avoidance).

### 3.3 Protocol is a Lead-to-User Interface

**Critical architectural insight:** The Communication Protocol (TEACH → IMPACT ASSESS →
RECOMMEND → ASK) is fundamentally a **Lead-to-User communication interface**. Only Lead
executes the 4 protocol steps toward the user. Other agents support the protocol by
providing materials and analysis, but they do not execute it themselves.

```
                    ┌──────────────┐
                    │     USER     │
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │     LEAD     │ ◄── SOLE EXECUTOR of all 4 protocol steps
                    │  (Protocol   │     TEACH → IMPACT ASSESS → RECOMMEND → ASK
                    │   Executor)  │
                    └──┬───────┬───┘
                       │       │
              ┌────────┘       └────────┐
              ▼                         ▼
    ┌─────────────────┐       ┌─────────────────┐
    │   RESEARCHER    │       │   ARCHITECT     │
    │  (Material      │       │  (Constraint    │
    │   Preparer)     │       │   Validator)    │
    │                 │       │                 │
    │ Reads Tier 2    │       │ Uses §2 to      │
    │ docs, organizes │       │ validate design │
    │ by 3-layer      │       │ Uses §3 as      │
    │ classification  │       │ design guardrail│
    │ → L2 = Lead's   │       │ → Design = input│
    │   teaching script│       │   for Lead's    │
    └─────────────────┘       │   RECOMMEND step│
                              └─────────────────┘
```

### 3.4 Precise Agent-to-Protocol-Step Mapping (T-1 Scenario)

Scenario: User starts `/brainstorming-pipeline` for T-1 (ObjectType + Property + Struct).

**Phase 0 — PT Check (Lead only):**
| Protocol Step | Executor | Action |
|---------------|----------|--------|
| — (inactive) | — | Phase 0 is administrative. Validates PT-v2 exists. No protocol activation. |

**Phase 1 — Discovery Q&A (Lead only, user-facing):**

| Substep | Protocol Step | Executor | What Happens | Reference Doc Section |
|---------|--------------|----------|--------------|----------------------|
| 1.1 Recon | — (preparation) | Lead | Loads reference doc (Mode 3). Reads PT-v2, design files. No user-facing protocol yet. | Full load at session start |
| 1.2 Q&A (per concept) | **TEACH** | **Lead → User** | "In Palantir Foundry, ObjectType is an entity with typed properties and a stable PK [Layer A]. Our Entity Discovery approach classifies using 7 questions [Layer B]. In our CLI, ObjectTypes become YAML files [Layer C]." | §6 (3-layer), §4 (decision tree questions) |
| 1.2 Q&A (per concept) | **IMPACT ASSESS** | **Lead → User** | "Defining X as ObjectType affects N downstream components: Properties scoped to it (§2 Schema), LinkTypes reference it (§2 Relationship), ActionTypes operate on it (§2 Behavior). Risk: OT-2 if PK is non-deterministic." | §2 (dependency map), §5 (scale limits), §3 (risk) |
| 1.2 Q&A (per concept) | **RECOMMEND** | **Lead → User** | "Decision tree §4: Q1 entity? YES → Q2 unique ID? YES → Q3 persisted? YES → Q4 queryable? YES → Strong OT candidate. Anti-pattern OT-1 warns against over-normalization of atomic values." | §3 (anti-patterns), §4 (decision trees) |
| 1.2 Q&A (per concept) | **ASK** | **Lead → User** | "Given that this entity passes 4/4 decision tree questions and affects N components, should we define it as: (a) Full ObjectType, (b) Struct in parent, (c) Defer?" | — (synthesizes above) |
| 1.3 Approach | IMPACT ASSESS dominant | Lead → User | Compares approach options using dependency chain analysis. | §2, §5 |
| 1.4 Scope | All 4 compressed | Lead → User | Synthesizes Q&A into Scope Statement with protocol evidence. | All sections as needed |

**Phase 2 — Research (Researcher, NOT user-facing):**

| Protocol Step | Executor | Action | Reference Doc Section |
|---------------|----------|--------|----------------------|
| — (material prep for TEACH) | Researcher | Reads ontology_1.md (Tier 2), extracts key facts. Organizes by Layer A/B/C classification. L2 summary becomes Lead's teaching script for resumed Q&A or Phase 3. | §6 (to classify findings) |
| — (material prep for IMPACT ASSESS) | Researcher | Maps dependency edges from §2 relevant to ObjectType. Identifies which downstream components are affected. | §2 (dependency edges) |
| — (material prep for RECOMMEND) | Researcher | Catalogs topic-relevant anti-patterns from §3. Identifies decision tree branch for each candidate entity. | §3, §4 |
| — (NOT executed) | — | Researcher does NOT execute TEACH/IMPACT/RECOMMEND/ASK toward user. Only prepares materials. | — |

**Phase 3 — Architecture (Architect + Lead mediation):**

| Protocol Step | Executor | Action | Reference Doc Section |
|---------------|----------|--------|----------------------|
| — (constraint validation) | Architect | Uses §2 dependency map to validate design's component interactions. Uses §3 anti-patterns as design guardrails. Does NOT communicate with user. | §2, §3 (consumed, not executed) |
| **TEACH** | **Lead → User** | Presents architect's ObjectType schema design with 3-layer framing: "This YAML structure maps to Palantir's ObjectType definition [A], follows our decomposition methodology [B], and adapts to YAML-on-disk [C]." | §6 |
| **IMPACT ASSESS** | **Lead → User** | Shows how the design choice affects T-2 (LinkTypes need ObjectType PKs), T-3 (ActionTypes operate on these ObjectTypes), T-4 (storage must accommodate this schema). | §2, §5 |
| **RECOMMEND** | **Lead → User** | Highlights architect's recommendation with anti-pattern avoidance evidence: "This design avoids OT-1 (over-normalization), OT-2 (non-deterministic PK), P-2 (deep struct nesting)." | §3, §4 |
| **ASK** | **Lead → User** | "Do you approve this ObjectType design direction? Options: (a) Approve as-is, (b) Modify [specific aspect], (c) Request redesign." | — |

### 3.5 Protocol Execution Summary by Role

| Role | Protocol Relationship | What They Do |
|------|----------------------|-------------|
| **Lead** | **SOLE EXECUTOR** of all 4 steps toward user | Executes TEACH/IMPACT/RECOMMEND/ASK in Phase 1 Q&A and Phase 3 user mediation. Loads reference doc (Mode 3). |
| **Researcher** | **MATERIAL PREPARER** (indirect support) | Reads Tier 2 docs, organizes findings by 3-layer classification, catalogs relevant anti-patterns. L2 = Lead's teaching script. |
| **Architect** | **CONSTRAINT CONSUMER** (indirect support) | Uses §2 dependency map and §3 anti-patterns to validate/constrain design. Output feeds Lead's RECOMMEND step. |
| **User** | **DECISION MAKER** (receives protocol output) | Receives TEACH → IMPACT ASSESS → RECOMMEND → ASK from Lead. Makes decisions at ASK step. |

### 3.6 Skill Modification Assessment

**The brainstorming-pipeline SKILL.md does NOT need modification.** Here's why:

1. **Rule 7 is already compatible.** It says "TEACH → CONTEXTUALIZE → ASK" which is a simplified version of the protocol. Lead can apply the full protocol without the skill prescribing it.

2. **The protocol works through MEMORY.md.** The MEMORY.md section triggers the protocol automatically when Ontology concepts arise. The skill doesn't need to reference the protocol explicitly — the system prompt already ensures it.

3. **Researcher directives embed protocol context.** The sequential protocol (§3) already specifies reference docs per topic. Lead includes these in researcher spawn directives.

4. **Forward-compatible.** If a future skill version wants to explicitly reference the protocol, it can add a "When brainstorming Ontology topics, follow the Communication Protocol in .claude/references/" instruction. But this is optional enhancement, not a requirement.

### 3.7 Dependency Map Guides Session Ordering

The reference doc §2 (Verified Dependency Map) directly supports the sequential protocol's topic ordering:

```
§2 Dependency Map                     Sequential Protocol Topics
────────────────                     ──────────────────────────
Schema Layer:                        T-1: ObjectType + Property + Struct
  ObjectType → Property → Struct     (defines Schema Layer primitives)

Relationship Layer:                  T-2: LinkType + Interface
  LinkType → ObjectType × ObjectType (defines Relationship Layer)
  Interface → SharedProperty         (defines abstraction mechanisms)

Behavior Layer:                      T-3: ActionType + Pre/Postconditions
  ActionType → ObjectType/LinkType   (defines Behavior Layer)
  Function → ActionType              (defines logic delegation)

Cross-Layer:                         T-4: Framework Integration
  SharedProperty ←→ Interface        (connects all layers)
  PrimaryKey → all components        (universal constraint)
```

The mapping is 1:1. The dependency map provides the TEACH content for why topics must be ordered this way. Each T-N session uses the dependency map to show what prior decisions constrain current choices.

### 3.8 Architecture Decision

**AD-9: Protocol Subsumes Brainstorming Rule 7; Lead is Sole Executor** (refined from PQ-2)
- During Ontology brainstorming (T-0~T-4), Lead applies the full Communication Protocol (TEACH → IMPACT ASSESS → RECOMMEND → ASK) instead of the simplified Rule 7 (TEACH → CONTEXTUALIZE → ASK).
- **Lead is the SOLE EXECUTOR** of all 4 protocol steps toward the user. Researcher prepares materials (L2 = teaching script). Architect validates constraints (§2/§3 = design guardrails). Neither executes the protocol directly.
- No skill modification required — the protocol activates through MEMORY.md automatically.
- The dependency map (§2) provides the structural backbone for IMPACT ASSESS during each topic.
- Protocol steps map to brainstorming phases: Phase 1 Q&A = iterative TEACH→IMPACT→RECOMMEND→ASK per concept. Phase 2 = material preparation. Phase 3 = Lead-mediated TEACH→ASK on architect output.

---

## 4. Knowledge Base Retrieval Strategy (Q3)

### 4.1 The Retrieval Problem

The backing knowledge base consists of ~15K lines across 15 files. Loading everything
is impossible (context window, BUG-002 risk). Loading nothing means unverified responses.

### 4.2 Three-Tier Retrieval Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Tier 1: Verified Summary (ALWAYS available during Ontology work)│
│                                                                  │
│ Source: .claude/references/ontology-communication-protocol.md    │
│ Size: ~388L (~3500 tokens)                                      │
│ Content:                                                         │
│   • Dependency map with edge labels and cardinalities            │
│   • Anti-pattern catalog with severity and official basis        │
│   • Decision tree questions and branch logic                     │
│   • Scale limits and performance thresholds                      │
│   • 3-layer knowledge tags                                       │
│   • Component definition order                                   │
│                                                                  │
│ USE WHEN: Any Ontology-related response. Contains the essential  │
│ verified facts needed for TEACH and IMPACT ASSESS steps.         │
│ The reference doc IS the primary knowledge base for teaching.    │
└─────────────────────────────────────────────────────────────────┘
                           │
                  Need more detail?
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 2: Per-Topic Source Sections (SELECTIVE during brainstorm) │
│                                                                  │
│ Source: park-kyungchan/.../docs/palantir_ontology_{N}.md         │
│ Size: 100-400L per section (~1000-3000 tokens)                  │
│ Loading map (from handoff §4.2):                                │
│   T-1: ontology_1.md lines 1-700 + ontology_9.md lines 100-250 │
│   T-2: ontology_2.md lines 1-600 + ontology_9.md lines 250-400 │
│   T-3: ontology_3.md + ontology_7.md + ontology_9.md 400-550   │
│   T-4: ontology_4/5/6.md (overview sections only)               │
│                                                                  │
│ USE WHEN: Researcher phase of brainstorming. Preparing detailed  │
│ teaching materials for Lead's Q&A with user.                     │
│ NOT loaded by Lead directly — researcher reads and synthesizes.  │
└─────────────────────────────────────────────────────────────────┘
                           │
                  Need raw detail?
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tier 3: Bridge Reference Files (RARE — deep dive only)          │
│                                                                  │
│ Source: .../docs/bridge-reference/bridge-ref-{component}.md      │
│ Size: 500-800L per file (~4000-6000 tokens)                     │
│ Files:                                                           │
│   bridge-ref-objecttype.md (33KB)                               │
│   bridge-ref-linktype.md (31KB)                                 │
│   bridge-ref-actiontype.md (39KB)                               │
│   bridge-ref-methodology.md (43KB)                              │
│   bridge-ref-secondary.md (388L)                                │
│                                                                  │
│ USE WHEN: User asks for deep detail that Tier 1+2 cannot answer.│
│ Example: specific validation rule wording, full property type    │
│ catalog, exhaustive anti-pattern examples.                       │
│ WARNING: Loading these files consumes 4000-6000 tokens EACH.    │
│ Only read sections relevant to the question.                     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Retrieval Flow During Brainstorming

```
Brainstorming Topic T-N starts
       │
       ▼
Lead loads Tier 1 (reference doc) ── always
       │
       ▼
Lead spawns researcher with directive:
  "Read Tier 2 sources for topic T-N"
  (specific file+line ranges from handoff §4.2)
       │
       ▼
Researcher reads Tier 2, synthesizes into L2 summary
  → L2 organized by 3-layer classification
  → Key facts, decision points, examples extracted
  → Anti-patterns relevant to this topic highlighted
       │
       ▼
Lead receives researcher L2
  → Uses L2 + Tier 1 for TEACH step in Q&A
  → Cites specific doc sections when user asks
       │
       ▼
If user asks deep question beyond L2 coverage:
  → Lead reads specific Tier 3 section (targeted, not whole file)
  → Or spawns follow-up researcher for specific investigation
```

### 4.4 Why NOT Create a Separate Index File

One option considered was creating a lightweight index file mapping concepts to file+line references. This was rejected because:

1. **The reference doc already serves as an index.** §2 maps component relationships, §3 maps anti-patterns, §4 maps decision trees. It IS the curated index.

2. **A separate index adds maintenance burden.** If Ontology docs are updated, both the reference doc and the index would need updating. Single source of truth is better.

3. **Tier 2 loading is guided by the handoff doc.** The handoff doc §4.2 already specifies exact file+line ranges per topic. Duplicating this into an index file is redundant.

4. **Opus 4.6 can navigate the reference doc efficiently.** Given the 388L reference doc's clear section structure (§1-§8), Opus can jump directly to the relevant section without needing a separate index.

### 4.5 Architecture Decision

**AD-10: Three-Tier Knowledge Retrieval**
- Tier 1 (Reference doc, ~388L): Loaded whenever protocol activates. Contains all verified facts needed for the TEACH and IMPACT ASSESS steps.
- Tier 2 (Ontology doc sections, 100-400L per read): Loaded by researcher during brainstorming Phase 2. Guided by handoff doc §4.2 file+line ranges.
- Tier 3 (Bridge reference files, 500-800L each): Loaded on-demand for deep-dive questions only. Read targeted sections, never full files.
- No separate index file — the reference doc IS the index.

---

## 5. Deferred Work Strategy (Q4)

### 5.1 Current Deferred Items

From the corrections tracker:

**5 MEDIUM (Completeness Gaps):**
| ID | Content | Relevant Topic |
|----|---------|---------------|
| MD-1 | Missing ObjectType "ID" field (two identifiers) | T-1 |
| MD-2 | PrimaryKey is Array (multi-property PK) | T-1 |
| MD-3 | Missing Value Types concept (semantic wrappers) | T-1 |
| MD-4 | Interface link constraints use ONE/MANY (simpler cardinality) | T-2 |
| MD-5 | Missing self-referential links | T-2 |

**5 LOW (Editorial / Unverified):**
| ID | Content | Status |
|----|---------|--------|
| LO-1 | "aliases" field — unverified | Unknown |
| LO-2 | Vector max 2048 dims — unverified | No official source |
| LO-3 | Render hint dependency chain — unverified | No official source |
| LO-4 | apiName case contradiction | Palantir docs inconsistent |
| LO-5 | SharedProperty name vs apiName | Discrepancy |

### 5.2 Strategy: MEDIUM Items Become Teaching Opportunities

The MEDIUM items (MD-1 through MD-5) are **additive content** — they add concepts
that were missing from the original docs. Rather than patching the docs now, they
should be **addressed during brainstorming as teaching moments**:

```
During T-1 brainstorming:
  ├── MD-1: When teaching ObjectType, explain that there are TWO identifiers
  │   (ID: lowercase+dashes, apiName: PascalCase). TEACH step includes this.
  │
  ├── MD-2: When teaching PrimaryKey, explain that PK is natively an ARRAY
  │   (multi-property support). IMPACT ASSESS shows cascade to LinkType backing.
  │
  └── MD-3: When teaching Property types, introduce Value Types as semantic
      wrappers (e.g., "EmailAddress" = String + regex constraint).
      RECOMMEND shows how this affects constraint design.

During T-2 brainstorming:
  ├── MD-4: When teaching Interface link constraints, explain ONE/MANY
  │   simplification vs LinkType's 4-way cardinality.
  │
  └── MD-5: When teaching LinkType, mention self-referential links
      (e.g., Employee → Manager pattern). IMPACT ASSESS shows graph cycles.
```

**After brainstorming:** The design files from T-1 and T-2 will incorporate these
concepts as part of the design. The Ontology docs should then be updated to match
the design file decisions. This ensures docs, design, and reference doc all converge.

### 5.3 Strategy: LOW Items Remain Deferred

The LOW items (LO-1 through LO-5) are **unverified** and should NOT trigger new
verification rounds:

1. **LO-1, LO-2, LO-3:** Flag as "UNVERIFIED" in the reference doc (already done in §8, line 332-333). If these concepts arise during brainstorming, Lead says "This is unverified — we'll use a conservative approach."

2. **LO-4, LO-5:** These are Palantir documentation inconsistencies, not our errors. When they arise during T-1 teaching, Lead explains the discrepancy and lets the user decide which convention to follow for the local framework.

3. **No new verification rounds.** The Phase 2 verification effort (51 official pages, 60+ URLs) is sufficient. LOW items don't justify additional MCP tool usage.

### 5.4 Architecture Decision

**AD-11: Deferred Corrections as Teaching Opportunities**
- MEDIUM items (MD-1~MD-5): Addressed during their relevant brainstorming topic as TEACH content. Design files incorporate the concepts. Docs updated post-brainstorming.
- LOW items (LO-1~LO-5): Remain deferred. Flagged as "UNVERIFIED" in reference doc. Addressed ad-hoc if they arise during brainstorming. No new verification rounds.
- Timeline: MEDIUM items resolved across T-1 and T-2 brainstorming sessions. LOW items deferred indefinitely until official Palantir docs clarify.

---

## 6. Session State Management (Q5)

### 6.1 The State Problem

Between brainstorming sessions, how does Opus know which Ontology components the
user has already defined? AD-1 says "Learning = Communication Protocol, NOT tracking
system" — so formal state tracking is out of scope for Layer 1.

### 6.2 Implicit State Carriers (Already Exist)

The system already has three implicit state carriers that together provide sufficient
session continuity WITHOUT a formal tracking system:

```
┌─────────────────────────────────────────────────────────────────┐
│ State Carrier 1: PERMANENT Task (PT-v{N})                        │
│                                                                  │
│ Sequential protocol §2 defines PT version evolution:             │
│   PT-v1 = created                                                │
│   PT-v2 = T-0 COMPLETE (strategy decisions embedded)             │
│   PT-v3 = T-1 COMPLETE (ObjectType decisions embedded)           │
│   PT-v4 = T-2 COMPLETE (LinkType decisions embedded)             │
│   PT-v5 = T-3 COMPLETE (ActionType decisions embedded)           │
│   PT-v6 = T-4 COMPLETE (Integration decisions, ALL COMPLETE)     │
│                                                                  │
│ PT version number → which topics are done                        │
│ PT content → what was decided (accumulated summaries)            │
│                                                                  │
│ HOW: Phase 0 of each brainstorming session reads PT via          │
│ TaskGet. The version number and content tell Opus exactly         │
│ where the user is in the learning journey.                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ State Carrier 2: Design Files (docs/plans/)                      │
│                                                                  │
│ Each completed topic produces a design file:                     │
│   T-0 → ontology-layer2-strategy-design.md                       │
│   T-1 → ontology-objecttype-design.md                            │
│   T-2 → ontology-linktype-design.md                              │
│   T-3 → ontology-actiontype-design.md                            │
│   T-4 → ontology-integration-design.md                           │
│                                                                  │
│ File existence → topic completed                                 │
│ File content → specific design decisions                         │
│                                                                  │
│ HOW: Sequential protocol Rule 4 validates dependencies in         │
│ Phase 0 — Glob check confirms prior design files exist.          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ State Carrier 3: MEMORY.md Topic Chain Index                     │
│                                                                  │
│ The "Ontology Framework — Brainstorming Chain" section in         │
│ MEMORY.md is ALWAYS in the system prompt:                         │
│                                                                  │
│   | Topic | Name | Depends On | Output |                         │
│   | T-0 | RTDI Layer 2 Strategy | — | L2 scope |                │
│   | T-1 | ObjectType + Property | T-0 | Schema definitions |    │
│   | ... | ... | ... | ... |                                      │
│                                                                  │
│ This gives Opus the full topic map without loading any files.    │
│ Combined with PT version, Opus knows what's done and what's next.│
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 State Query Mechanics

| Question | How Opus Answers | State Carrier |
|----------|-----------------|---------------|
| "Which topics are done?" | PT version number (e.g., PT-v3 = T-0, T-1 done) | PT |
| "What was decided for ObjectType?" | Read T-1 design file | Design files |
| "What's the next topic?" | MEMORY.md topic chain + PT version | MEMORY.md + PT |
| "What concepts does the user know?" | PT version implies learning progression (T-0 = strategy vocabulary, T-1 = entity concepts, etc.) | PT + Rule 7 progression |
| "Has the user defined any LinkTypes?" | PT-v4+ means T-2 complete → yes | PT |

### 6.4 What About Non-Brainstorming Sessions?

When the user asks about Ontology outside of brainstorming (e.g., in a regular session):

1. **MEMORY.md trigger fires** → Opus knows the protocol applies.
2. **MEMORY.md topic chain shows current progress** → Opus sees which topics are listed with outputs.
3. **Opus reads PT if needed** → PT-v{N} has accumulated decisions.
4. **Opus adjusts teaching to user's level** → If PT-v3 (T-1 done), user understands ObjectType concepts. Opus can reference them without re-teaching.

This works because the PT is accessible from any session (not scoped to brainstorming teams).

### 6.5 Layer 1 vs Layer 2 Boundary

| Capability | Layer 1 (Current) | Layer 2 (Future) |
|------------|-------------------|-----------------|
| Topic completion tracking | PT version + design file existence | ObjectType: TopicCompletion with typed status |
| Decision retrieval | Read design file | Query: Decision.where(topic="T-1") |
| Learning progression | Inferred from PT version | ObjectType: UserKnowledge with skill levels per concept |
| Cross-topic dependency | MEMORY.md chain + sequential protocol | LinkType: Topic → Topic with dependency semantics |
| Component definition state | Design file content | ObjectType instances with schema validation |

**AD-1 compliance:** Layer 1 uses IMPLICIT state (PT version, file existence, MEMORY.md index) — not a tracking system. Layer 2 would formalize this into typed state, but that's deferred.

### 6.6 Architecture Decision

**AD-12: Implicit State via PT + Design Files + MEMORY.md Index**
- No new state management system for Layer 1 (AD-1 compliance).
- PT version number encodes topic completion (PT-v{N} ↔ T-{N-1} complete).
- Design files serve as both output artifacts and implicit state.
- MEMORY.md topic chain provides the always-loaded navigation index.
- Non-brainstorming sessions use MEMORY.md trigger + PT content for context.
- Layer 2 boundary: formal typed state tracking is deferred to Ontology Framework implementation.

---

## 7. Three-Layer Teaching Design (Q6)

### 7.1 The Three Layers

From reference doc §6, all Ontology knowledge is classified into three layers:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer A — Palantir Concepts (Transferable Knowledge)             │
│                                                                  │
│ What: Official Palantir Foundry documentation.                   │
│ Tone: Authoritative. "In Palantir Foundry, X works like this."  │
│ Teaching: Present as established facts with official sources.    │
│ Certainty: HIGH — verified against 51 official pages.            │
│                                                                  │
│ Examples:                                                        │
│ • "ObjectType has 22+ base types including String, Integer..."   │
│ • "FUNCTION_RULE must be exclusive — no other rules allowed"     │
│ • "Struct depth is limited to 1 — no nested structs"             │
│ • "Search Around operations are limited to 3 per function"       │
│                                                                  │
│ When user asks WHY: cite the official Palantir constraint.       │
│ When user disagrees: explain this is a platform constraint,      │
│ our bridge may adapt it differently (→ Layer C).                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer B — Our Decomposition Methodology (Locally Synthesized)    │
│                                                                  │
│ What: 8-phase systematic workflow we created using Palantir      │
│ concepts. Palantir does NOT provide this methodology.            │
│ Tone: Prescriptive but adjustable. "Our approach uses X method." │
│ Teaching: Present as our systematic process with reasoning.      │
│ Certainty: MEDIUM — derived from Palantir concepts, not         │
│ verified as "the correct" way.                                   │
│                                                                  │
│ Examples:                                                        │
│ • "Our Entity Discovery tree asks 7 questions to classify..."    │
│ • "We use 6 scanning indicators for Relationship Discovery"      │
│ • "Our validation rules DEC-VAL-001 through DEC-VAL-006..."     │
│ • "The 8-phase sequential order ensures dependencies are met"    │
│                                                                  │
│ When user asks WHY: explain the reasoning behind our choice.     │
│ When user disagrees: adapt. This is OUR methodology — the user   │
│ can modify the process while keeping Palantir concepts (Layer A) │
│ intact.                                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Layer C — Bridge Adaptations (Local Implementation)              │
│                                                                  │
│ What: How we translate Palantir Foundry concepts to local CLI.   │
│ Tone: Open. "In our environment, we implement X using Y."        │
│ Teaching: Present as implementation choices with alternatives.    │
│ Certainty: LOW — these are design choices, not facts.            │
│                                                                  │
│ Examples:                                                        │
│ • "We use YAML files instead of Foundry platform storage"        │
│ • "CLI orchestration replaces Workshop UI"                       │
│ • "NL enforcement replaces platform-enforced constraints"        │
│ • "ontology.lock replaces Foundry versioning"                    │
│                                                                  │
│ When user asks WHY: present trade-offs between alternatives.     │
│ When user disagrees: change. These are LOCAL CHOICES — the user  │
│ decides the implementation approach.                              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 How Layers Interact in the TEACH Step

The TEACH step of the Communication Protocol should present concepts in layer order:

```
TEACH step for any Ontology concept:

1. Layer A first: "In Palantir Foundry, [concept] is defined as..."
   → Official definition + paradigm mapping (OOP/RDBMS/RDF)
   → Non-obvious constraints from official docs
   → Anti-patterns from §3 (verified against official signals)

2. Layer B second: "In our decomposition methodology, we handle this by..."
   → Decision tree questions and their rationale
   → Scanning indicators for this component type
   → Our validation rules and quality checklist

3. Layer C third: "In our local implementation, this translates to..."
   → YAML structure / file layout
   → CLI-specific considerations
   → NL enforcement approach
   → Known differences from Foundry platform behavior
```

**Why this order matters:** The user needs to understand WHAT a concept IS (Layer A) before understanding HOW we approach it (Layer B) and HOW it's implemented locally (Layer C). Teaching in reverse order (starting with YAML files) would obscure the conceptual foundation.

### 7.3 Layer-Aware IMPACT ASSESS

The IMPACT ASSESS step should also distinguish layers:

```
IMPACT ASSESS for a decision:

Axis 1 — Component Chain (Layer A):
  "This decision affects [N] components in the dependency map..."
  (Uses §2 verified edges — these are Palantir facts)

Axis 2 — Implementation Feasibility (Layer C):
  "In our local environment, this requires [Preserved/Adapted/Redesign/Drop]..."
  (Translation assessment — our bridge choices)

Axis 3 — Domain Fitness (Layer B):
  "Applying decision tree §4: [question flow and result]..."
  (Our methodology — user can challenge the tree)
```

### 7.4 Layer Tags in Reference Doc

The reference doc §6 already tags each component with its layer. The current tagging
is at the section level (entire §6 is organized by layer). For the TEACH step to work
efficiently, no additional tagging is needed — Opus reads §6 once and knows which
facts belong to which layer.

However, §2 (dependency map), §3 (anti-patterns), and §4 (decision trees) don't have
explicit layer tags on each item. This is acceptable because:

- §2 dependency map: All Layer A (platform-defined relationships).
- §3 anti-patterns: Labeled as "CONFIRMED by official docs" vs "PLAUSIBLE" vs "COMMUNITY-REPORTED". This IS the implicit layer tag (CONFIRMED = Layer A, PLAUSIBLE = Layer A-B boundary, COMMUNITY = Layer B).
- §4 decision trees: Layer B (our methodology), using Layer A concepts.

No changes needed to the reference doc's tagging approach.

### 7.5 Teaching Progression Across Topics

| Topic | Layer A Teaching Focus | Layer B Teaching Focus | Layer C Teaching Focus |
|-------|----------------------|----------------------|----------------------|
| T-0 | Ontology vocabulary, 8 core components | 8-phase methodology overview | YAML-on-disk architecture, INFRA as bootstrap domain |
| T-1 | ObjectType definition, 22+ base types, PK rules, Struct limits | Entity Discovery tree (7Q), scanning indicators | ObjectType YAML schema, property type mapping |
| T-2 | Cardinality model, FK/JoinTable/Object-Backed, Interface constraints | Relationship Discovery (6 indicators), Interface decision (4Q) | LinkType YAML, graph traversal implementation |
| T-3 | 12 rule types, FUNCTION_RULE exclusivity, stale data caveat | Mutation Discovery, pre/postcondition patterns | ActionType YAML, NL enforcement of constraints |
| T-4 | Scale limits, Search Around, platform support matrix | Quality checklist (7 items), validation rules | Storage format, query engine, validation pipeline |

Each topic builds on prior teaching. By T-4, the user understands all three layers
for all core components and can make informed architecture decisions.

### 7.6 Architecture Decision

**AD-13: Layer-Ordered Teaching in TEACH Step**
- Always present Layer A (Palantir facts) first, then Layer B (our methodology), then Layer C (bridge implementation).
- Layer A = authoritative tone + official sources. Layer B = prescriptive but adjustable. Layer C = open + user decides.
- User can challenge Layer B and C freely. Layer A challenges require official documentation evidence.
- Anti-pattern confidence labels (CONFIRMED/PLAUSIBLE/COMMUNITY) serve as implicit layer tags.
- No structural changes to reference doc — existing organization supports three-layer teaching.

---

## 8. Architecture Decisions Summary

| AD | Decision | Scope | Phase |
|----|----------|-------|-------|
| AD-1 | Learning = Communication Protocol, NOT state tracking | System-wide | Phase 1 |
| AD-2 | 4-step pattern: TEACH → IMPACT ASSESS → RECOMMEND → ASK | Protocol | Phase 1 |
| AD-3 | Always-active trigger via MEMORY.md | Activation | Phase 1 |
| AD-4 | MEMORY.md core + reference doc at .claude/references/ | Storage | Phase 1 |
| AD-5 | 3-axis IMPACT ASSESS + 4 risk dimensions | Protocol | Phase 1 |
| AD-6 | 3-layer knowledge classification: Palantir/Methodology/Bridge | Teaching | Phase 2 |
| AD-7 | 15 corrections applied, 10 deferred | Docs | Phase 2 |
| **AD-8** | **Three-Mode Protocol Activation (MEMORY-Only / Section-Selective / Full-Load)** | **Activation** | **Phase 3** |
| **AD-9** | **Protocol Subsumes Rule 7; Lead is Sole Executor** | **Integration** | **Phase 3** |
| **AD-10** | **Three-Tier Knowledge Retrieval** | **Retrieval** | **Phase 3** |
| **AD-11** | **Deferred Corrections as Teaching Opportunities** | **Docs** | **Phase 3** |
| **AD-12** | **Implicit State via PT + Design Files + MEMORY.md** | **State** | **Phase 3** |
| **AD-13** | **Layer-Ordered Teaching in TEACH Step** | **Teaching** | **Phase 3** |

---

## 9. Risks and Mitigations

### 9.1 Risk Register

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|-----------|------------|
| R-1 | Opus fails to load reference doc when needed (Tier 2 not triggered) | HIGH | LOW | MEMORY.md explicitly states "Read reference doc for any Ontology response." The trigger text is imperative, not suggestive. |
| R-2 | Reference doc (388L) becomes stale if Palantir updates official docs | MEDIUM | LOW | Reference doc includes source URLs (§8). Periodic re-verification possible but not scheduled. Flag as risk only. |
| R-3 | Context budget exceeded during brainstorming with large Ontology doc reads | HIGH | MEDIUM | Three-tier retrieval ensures only relevant sections are loaded. BUG-002 mitigated by researcher reading, not Lead directly loading 15K lines. |
| R-4 | User confusion between Layer A/B/C during teaching | MEDIUM | MEDIUM | TEACH step explicitly labels each layer. Reference doc §6 has clear classification. Lead reinforces layer distinction in Q&A. |
| R-5 | PT version number doesn't capture partial topic completion | LOW | LOW | PT versioning is coarse-grained (per-topic, not per-decision). This is acceptable for Layer 1. Layer 2 would provide finer granularity. |
| R-6 | Protocol activation in non-brainstorming context produces low-quality teaching without researcher-prepared materials | MEDIUM | MEDIUM | Tier 1 (reference doc) provides sufficient verified facts for basic TEACH. Full teaching quality requires brainstorming context, but casual responses are still accurate. |
| R-7 | MEDIUM deferred corrections (MD-1~MD-5) create confusion if user reads raw Ontology docs | LOW | LOW | Raw Ontology docs are not user-facing. Brainstorming uses the reference doc (which includes corrections summary in §8). |

### 9.2 Risk Acceptance

All risks are at acceptable levels for Layer 1 implementation:
- No HIGH likelihood risks
- The two HIGH severity risks (R-1, R-3) both have LOW-MEDIUM likelihood with clear mitigations
- All risks would be further mitigated by Layer 2 (formal validation, typed queries)

---

## 10. Implementation Roadmap

### 10.1 What Needs to Change in INFRA

**Nothing.** All components are already in place:

| Component | Current State | Change Needed |
|-----------|-------------|---------------|
| MEMORY.md protocol section | ~15L, already in system prompt | NONE — already triggers protocol |
| Reference doc | 388L at .claude/references/ | NONE — already complete |
| Ontology docs | 4 files corrected, verified | NONE for now — MD items addressed during brainstorming |
| Brainstorming SKILL.md | Rule 7 compatible with protocol | NONE — protocol works through MEMORY.md |
| Sequential protocol | Topic chain with PT versioning | NONE — already specifies session ordering |
| PERMANENT Task mechanism | PT-v{N} with Read-Merge-Write | NONE — existing mechanism sufficient |

### 10.2 What the User Does Next

```
This document (Phase 3 Architecture)
       │
       ▼
Phase 4-5: (If additional design refinement needed)
  → /agent-teams-write-plan for implementation plan
  → /plan-validation-pipeline to validate
       │
       ▼
OR: Proceed directly to brainstorming execution:
       │
       ▼
T-0: /brainstorming-pipeline "RTDI Layer 2 Integration Strategy"
  │   → Protocol activates automatically through MEMORY.md
  │   → Reference doc loaded by Lead during Phase 1
  │   → Researcher reads RTDI assessment for Phase 2
  │
  └──→ T-1 through T-4: Sequential execution per sequential protocol
       → Each session uses the full Communication Protocol
       → Teaching follows Layer A → B → C order
       → State carried through PT-v{N} and design files
```

### 10.3 Optional Future Enhancements (Layer 2 Scope)

These are NOT required for the current system to work, but could improve it when
Layer 2 is implemented:

| Enhancement | What It Does | Layer 2 Component |
|-------------|-------------|------------------|
| Topic completion ObjectType | Typed state for each T-N with status fields | T-1 ObjectType |
| Decision audit trail | Each decision as an ObjectType instance linked to its topic | T-1 + T-2 |
| Learning progression tracker | User knowledge levels per concept | T-1 (deferred per AD-1) |
| Teaching quality validator | Postcondition: TEACH step covered all 3 layers | T-3 Postcondition |
| Cross-session knowledge graph | Decisions from T-1 linked to T-2 constraints | T-2 LinkType |

---

## Appendix A: Integration Test Scenarios

These scenarios validate the architecture works as designed:

### A.1 Protocol Activation Test
1. Start a new session (non-brainstorming)
2. User asks: "What is an ObjectType in Palantir Foundry?"
3. Expected: MEMORY.md trigger fires → Opus reads reference doc → Full TEACH step with Layer A/B/C → IMPACT ASSESS using §2 dependency map → RECOMMEND → ASK
4. Validation: Response distinguishes Palantir facts from our methodology from bridge adaptations

### A.2 Brainstorming Session Test
1. Start T-1 brainstorming session via `/brainstorming-pipeline`
2. Phase 0 validates PT-v2 exists (T-0 COMPLETE)
3. Phase 1: Lead uses full Communication Protocol for Q&A
4. Phase 2: Researcher loads Tier 2 (ontology_1.md sections + ontology_9.md)
5. Phase 3: Architecture uses reference doc anti-patterns for validation
6. Validation: Design file includes Forward-Compatibility section, MD-1/MD-2/MD-3 concepts addressed

### A.3 State Continuity Test
1. Complete T-1 brainstorming → PT-v3, design file exists
2. Start T-2 brainstorming
3. Phase 0 validates: PT contains "T-1 COMPLETE", objecttype-design.md exists
4. Phase 1: Lead's TEACH step for LinkType references T-1 ObjectType concepts
5. Validation: User is not re-taught ObjectType basics; LinkType teaching builds on prior knowledge

### A.4 Non-Brainstorming Protocol Test
1. After T-1 complete, user asks in a regular session: "Can an ObjectType reference itself?"
2. Expected: MEMORY.md trigger → Opus loads reference doc → Finds §2 "self_referential" edge → TEACH with Layer A answer → ASK if this affects their design
3. Validation: Accurate response without full brainstorming overhead

---

## Appendix B: Context Budget Worksheet (Three-Mode Architecture)

| Scenario | Mode | MEMORY.md | Ref Doc Sections | Tier 2 | Tier 3 | Total |
|----------|------|-----------|-----------------|--------|--------|-------|
| Non-Ontology session | — | 150 | 0 | 0 | 0 | **150 tok** |
| Passing Ontology mention | Mode 1 | 150 | 0 | 0 | 0 | **150 tok** |
| Focused concept question | Mode 2 | 150 | ~900 (§6+§4) | 0 | 0 | **1050 tok** |
| Decision-heavy question | Mode 2 | 150 | ~1450 (§2+§3+§4) | 0 | 0 | **1600 tok** |
| Full protocol question | Mode 2 | 150 | ~2100 (§2-§7) | 0 | 0 | **2250 tok** |
| Brainstorming turn (typical) | Mode 3 | 150 | 3500 (full) | 1500 | 0 | **5150 tok** |
| Brainstorming turn (deep) | Mode 3 | 150 | 3500 (full) | 2500 | 5000 | **11150 tok** |
| Maximum possible | Mode 3 | 150 | 3500 (full) | 3000 | 6000 | **12650 tok** |

**Savings vs always-full-load model:**
| Scenario | Always-Full Cost | Three-Mode Cost | Savings |
|----------|-----------------|-----------------|---------|
| Passing mention | 3650 | 150 | **3500 tok (96%)** |
| Focused question | 3650 | 1050 | **2600 tok (71%)** |
| Decision question | 3650 | 1600 | **2050 tok (56%)** |
| Brainstorming | 5150 | 5150 | 0 (same) |

Weighted average (70% no-Ontology, 20% focused, 10% brainstorming):
- Always-full: 0.7×150 + 0.2×3650 + 0.1×5150 = **~1350 tok/session**
- Three-mode: 0.7×150 + 0.2×1050 + 0.1×5150 = **~830 tok/session**
- **Net savings: ~520 tok/session (~39% reduction)**

Opus 4.6 context window: ~200K tokens. Maximum protocol cost (12650 tok) = **6.3%** of context. Well within BUG-002 safety margins.
