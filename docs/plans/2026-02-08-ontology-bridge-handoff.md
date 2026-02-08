# Ontology Framework — Brainstorming Handoff Document

> **Purpose:** Enable Lead to guide user through defining Ontology Components for any domain
> via `/brainstorming-pipeline`. One design file per Ontology Component topic.
> **Format:** Machine-readable for Opus 4.6. English only.
> **Date:** 2026-02-08
> **Last Updated:** 2026-02-08T07:45 (added: educational dimension, Foundry scope decision)
> **Prerequisite:** PERMANENT Task design complete (committed: 7abd080)

---

## 0. User Decisions Log (Confirmed, Chronological)

| # | Decision | User Statement (translated) |
|---|----------|-----------------------------|
| 1 | Topic scope: T-1~T-4 (Core Ontology Components) | "Core Schema 중심으로" |
| 2 | Separate design file per topic | "별도의 brainstorming 세션으로" |
| 3 | Full migration awareness in every design | "항상 Ontology 전체로 마이그레이션할 것임을 고려해야한다" |
| 4 | Full Ontology doc reference (all 9 docs), restructured | "전체 Ontology 문서 참조, 재구조화해서 저장" |
| 5 | Layer 2 = general-purpose Ontology Framework | "범용 프레임워크" |
| 6 | First domain: TBD | "아직 미정" |
| 7 | CORRECTION: Entities are NOT Claude native capabilities | "왜 Entity가 Claude Native Capabilities 자체가 되어버렸나?" |
| 8 | Foundry scope: definition system first → runtime later | "정의 시스템이 가장 중요하다" |
| 9 | Brainstorming = user learning + decision-making | "사용자가 Ontology/Foundry에 대한 학습을 해서 더 상세한 feedback을 해나갈 수 있도록" |

### Critical Architectural Correction (Decision #7)

The initial approach incorrectly mapped Agent Teams infrastructure (Task, Teammate, Phase)
as Ontology ObjectTypes. This conflated the TOOL with the DOMAIN.

Correct architecture:
```
Layer 1: Claude Code CLI + Agent Teams INFRA
         (Task API, SendMessage, Hooks, Skills, Agent .md files)
         → Keep as-is. These are native capabilities, not Ontology entities.

Layer 2: General-Purpose Ontology Framework
         (Mimics Palantir Foundry architecture)
         → Enables defining ObjectType, LinkType, ActionType, Interface for ANY domain.
         → First domain application: TBD (user decides later).
         → Could be: Agent Teams itself, codebase modules, or any other domain.
```

The Framework must be domain-agnostic. It provides the SYSTEM for defining Ontology,
not a specific Ontology for a specific domain.

---

## 1. User Intent

The user wants to build a **general-purpose Ontology Framework** on top of Layer 1
(Claude Code CLI + Agent Teams), mimicking Palantir Foundry's Ontology architecture
as closely as practically feasible within a local CLI environment.

Key principles:
- Layer 1 (Opus 4.6 native capabilities) is preserved — creativity, reasoning, adaptivity
- Layer 2 (Ontology Framework) compensates for LLM weaknesses — structure, constraints, verification
- The Framework enables defining Ontology for any domain the user works on
- The brainstorming process helps user decide WHAT to define as ObjectType, LinkType, etc.
- Each brainstorming session produces one design file for one Ontology Component

---

## 2. What the Ontology Framework Must Provide

Based on Palantir Foundry architecture (from 9 reference documents):

```
┌──────────────────────────────────────────────────────────────┐
│  Ontology Framework (Layer 2)                                │
│  ════════════════════════════════════════════════════════════ │
│                                                              │
│  Static Primitives (define WHAT exists):                     │
│  ├── ObjectType: Entity definitions with typed properties    │
│  ├── Property: Typed fields (STRING, INTEGER, TIMESTAMP...)  │
│  ├── Struct: Embedded complex objects within ObjectTypes      │
│  ├── LinkType: Relationships between ObjectTypes              │
│  └── Interface: Shared property contracts across ObjectTypes  │
│                                                              │
│  Kinetic Primitives (define HOW things change):              │
│  ├── ActionType: State mutations with parameters             │
│  ├── Precondition: Constraints that MUST be met before action│
│  ├── Postcondition: Constraints verified after action        │
│  └── Function: Business logic backing complex actions        │
│                                                              │
│  Behavioral Primitives (define WHEN things happen):          │
│  ├── Automation: Event-triggered workflows                   │
│  ├── Trigger: Conditions that activate automations           │
│  └── Rule: Validation logic for data quality                 │
│                                                              │
│  Governance Primitives (define WHO can do what):             │
│  ├── Security: Permission models per ObjectType              │
│  └── Restricted View: Filtered data access                   │
│                                                              │
│  Infrastructure (HOW it runs):                               │
│  ├── Storage: YAML-on-disk, JSON graph, or Foundry API       │
│  ├── Validation: Schema validation engine                    │
│  └── Query: Graph traversal (Search Around equivalent)       │
│                                                              │
│  Methodology (HOW to define):                                │
│  └── Decomposition Guide: 8-phase process for any domain     │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Brainstorming Topics (T-1 through T-4)

Each topic produces one design file via `/brainstorming-pipeline`.
Topics are ordered by dependency.

### Topic Dependency Graph

```
T-1: ObjectType + Property + Struct
  │   "How does our Framework define entities, their properties, and embedded structures?"
  │   Core question: What makes something an ObjectType vs a Struct vs a Property?
  │   Framework output: ObjectType definition system, Property type catalog, Struct model
  │   Design file: docs/plans/YYYY-MM-DD-ontology-objecttype-design.md
  │
  ├──→ T-2: LinkType + Interface
  │     "How does our Framework define relationships and shared contracts?"
  │     Core question: How to model cardinality, backing, traversal, and polymorphism?
  │     Framework output: LinkType definition system, Interface contract model
  │     Design file: docs/plans/YYYY-MM-DD-ontology-linktype-design.md
  │     Depends on: T-1 (links connect ObjectTypes)
  │
  ├──→ T-3: ActionType + Pre/Postconditions
  │     "How does our Framework define state changes and enforce constraints?"
  │     Core question: How to model actions, parameters, and automated verification?
  │     Framework output: ActionType definition system, condition enforcement engine
  │     Design file: docs/plans/YYYY-MM-DD-ontology-actiontype-design.md
  │     Depends on: T-1 (actions operate on ObjectTypes)
  │
  └──→ T-4: Framework Integration Architecture
        "How does Layer 2 integrate with Layer 1 at runtime?"
        Core question: Storage format, query engine, validation pipeline, agent access patterns?
        Framework output: Integration architecture, file layout, CLI tooling
        Design file: docs/plans/YYYY-MM-DD-ontology-integration-design.md
        Depends on: T-1, T-2, T-3 (need full component model before integration)
```

### Forward-Compatibility Requirement

Every design must include a "Forward-Compatibility" section addressing:
- How this component interacts with subsequent components (T-2 needs T-1 decisions, etc.)
- How this component supports future domain application (not locked to any specific domain)
- How this component supports future extension (Automation, Security, etc. from T-5~T-7)

---

## 4. Reference Document Inventory

All source documents at: `/home/palantir/park-kyungchan/palantir/Ontology-Definition/docs/`

### 4.1 Document-to-Topic Mapping

| Doc | Lines | Primary Topic | Secondary Topics | Content Summary |
|-----|-------|--------------|------------------|-----------------|
| palantir_ontology_1.md | 1910 | T-1 | T-2 (PK for links) | ObjectType definition, Property types (13 types), Struct model, validation (OT001-016, PT001-012), anti-patterns |
| palantir_ontology_2.md | 1477 | T-2 | T-1 (Interface shapes) | LinkType (4 cardinalities, 3 backings), Interface (shared props, link constraints, multiple inheritance), Search Around, validation (LT001-008, IF001-007) |
| palantir_ontology_3.md | 938 | T-3 | — | ActionType (Simple/Complex), Parameters, Pre/Postconditions, Function rules, validation |
| palantir_ontology_4.md | 1752 | T-4 | — | Data Pipeline Layer — transforms, datasets, scheduling (Foundry-specific, adapt for local) |
| palantir_ontology_5.md | 698 | T-4 | — | Collection & Storage — object storage, indexing (adapt for YAML/JSON on disk) |
| palantir_ontology_6.md | 1361 | T-4 | — | Application & API Layer — OSDK, REST endpoints (adapt for CLI access patterns) |
| palantir_ontology_7.md | 1380 | T-3, T-4 | — | Logic & Automation — Functions, Triggers, Automations (maps to hooks) |
| palantir_ontology_8.md | 978 | Future (T-5+) | T-4 | Security & Governance — permissions, restricted views |
| palantir_ontology_9.md | 792 | ALL | — | Decomposition Guide — 8-phase methodology for defining Ontology for any domain |
| LLM-Agnostic_*.md | 808 | Context | — | 5 LLM limits analysis, YAML-on-disk architecture recommendation (§5.1) |

### 4.2 Key Sections to Read Per Topic

**T-1 (ObjectType) brainstorming — Lead reads or delegates to researcher:**
- `ontology_1.md` lines 1-80: ObjectType core definition, PK strategy, titleProperty
- `ontology_1.md` lines 81-250: Full PropertyType catalog (13 types with constraints)
- `ontology_1.md` lines 250-400: Struct type — when to embed vs separate ObjectType
- `ontology_1.md` lines 400-700: Validation rules + anti-patterns
- `ontology_9.md` lines 100-250: Entity Discovery decision tree
  - Three questions: unique ID? persisted? independently queryable?
  - All yes → ObjectType. Otherwise → Struct, Property, or skip.

**T-2 (LinkType) brainstorming:**
- `ontology_2.md` lines 1-100: Cardinality types (1:1, 1:N, N:1, M:N)
- `ontology_2.md` lines 100-250: Backing mechanisms (FK, JOIN_TABLE, OBJECT_BACKED)
- `ontology_2.md` lines 250-400: Search Around graph traversal (max 3 hops, 50K threshold)
- `ontology_2.md` lines 400-600: Interface definition, shared properties, link constraints
- `ontology_9.md` lines 250-400: Relationship Discovery patterns (6 indicators)

**T-3 (ActionType) brainstorming:**
- `ontology_3.md` lines 1-60: ActionType concept ("the verb of the Ontology")
- `ontology_3.md` lines 60-180: Simple (modifyObject) vs Complex (Function-backed)
- `ontology_3.md` lines 180-300: Parameter types
- `ontology_3.md` lines 300-450: Pre/Postconditions (core value)
- `ontology_7.md` lines relevant to: Function types, Automation triggers, Logic patterns
- `ontology_9.md` lines 400-550: Mutation Discovery (ActionType candidates)

**T-4 (Integration) brainstorming:**
- `ontology_4.md`: Data pipeline adaptation for local environment
- `ontology_5.md`: Storage adaptation (Foundry Object Storage → local YAML/JSON)
- `ontology_6.md`: API adaptation (OSDK → CLI Read/Write patterns)
- `LLM-Agnostic_*.md` §5.1: YAML-on-disk architecture recommendation

### 4.3 Restructured Reference Files

Agents are currently producing restructured versions of these docs, focused on
Framework design rather than raw Palantir documentation:

| File | Source Docs | Status | Purpose |
|------|------------|--------|---------|
| `bridge-ref-objecttype.md` | ontology_1 + ontology_9 §Entity | COMPLETE (33KB) | T-1 reference |
| `bridge-ref-linktype.md` | ontology_2 + ontology_9 §Relationship | COMPLETE (31KB) | T-2 reference |
| `bridge-ref-actiontype.md` | ontology_3 + ontology_7 + ontology_9 §Mutation | COMPLETE (39KB) | T-3 reference |
| `bridge-ref-methodology.md` | ontology_9 (full) + LLM-Agnostic §5.1 | COMPLETE (43KB) | All topics |
| `bridge-ref-secondary.md` | ontology_4 + ontology_5 + ontology_6 + ontology_8 | COMPLETE (388 lines) | T-4 reference |

Location: `park-kyungchan/palantir/Ontology-Definition/docs/bridge-reference/`

Note: These files contain Agent Teams examples as ILLUSTRATIONS of how to apply
Ontology concepts. They are NOT the definitive domain mapping — the user will define
the actual domain during brainstorming.

---

## 5. How to Run Each Brainstorming Session

### 5.0 Dual Purpose: Decision-Making + Learning

Each brainstorming session serves TWO purposes simultaneously:

1. **Decision-Making:** Lead guides user through Ontology Component design decisions
2. **Learning:** User progressively learns Ontology/Foundry concepts, enabling
   increasingly detailed and informed feedback in subsequent sessions

The learning progression:
```
T-1 (ObjectType): User learns what entities are, property typing, PK strategy
  → T-2 (LinkType): User applies entity knowledge to relationships, asks deeper questions
    → T-3 (ActionType): User designs constraints with entity+relationship understanding
      → T-4 (Integration): User makes architecture decisions with full schema comprehension
```

Lead should:
- Explain concepts BEFORE asking for decisions (teach, then ask)
- Use concrete examples from reference docs (§7 Agent Teams example, plus Palantir's
  education domain examples from ontology_1/2/3/9)
- When user asks a question, reference the specific doc section that answers it
  (e.g., "This is covered in ontology_2.md lines 100-250, the backing mechanism section")
- Present design choices with trade-offs, not just "pick one"
- Build on previous session's learning (T-2 assumes T-1 knowledge)

### 5.1 Session Flow (for Lead)

```
Phase 1 (Discovery):
  1. TEACH: Explain what this Ontology Component is, using reference docs
     - Show Palantir's definition from restructured doc (bridge-ref-*.md)
     - Show concrete examples (education domain from Palantir docs + Agent Teams example)
  2. CONTEXTUALIZE: How this component relates to previously designed components
  3. ASK: "What domain do you want to apply this component to?"
     (Or: "Do you want to define the Framework system itself first?")

Phase 2 (Research — delegate to researcher):
  1. Read relevant original Ontology doc sections (§4.2 line references)
  2. Read Decomposition Guide relevant section
  3. If domain chosen: read domain-specific artifacts for entity discovery
  4. Prepare teaching materials for user (key concepts, decision points, examples)

Phase 3 (Architecture — iterative with user):
  1. TEACH: Present Decomposition Guide methodology for this component
  2. APPLY: Walk user through discovery process for chosen domain
  3. DECIDE: Present candidates with trade-offs, get user confirmation/modification
  4. DOCUMENT: Generate design file with YAML definitions + learning notes

Output: docs/plans/YYYY-MM-DD-ontology-{component}-design.md
```

### 5.2 Key Questions Lead Should Ask Per Topic

**T-1 (ObjectType) questions:**
1. "What is the domain you want to model?" (or "Framework definition system first?")
2. For each candidate entity: "Does this have a unique, stable ID? Is it persisted?
   Do users need to search/filter it independently?" (Entity Discovery decision tree)
3. "Should X be an ObjectType or a Struct embedded in Y?" (boundary decision)
4. "What properties does this entity have? What types?" (property catalog reference)
5. "What is the primary key strategy?" (composite ID, natural key, generated?)

**T-2 (LinkType) questions:**
1. "What relationships exist between the ObjectTypes defined in T-1?"
2. "What is the cardinality?" (1:1, 1:N, N:1, M:N)
3. "Does this relationship have its own properties?" (if yes → OBJECT_BACKED)
4. "Do you need bidirectional traversal?" (Search Around)
5. "Do multiple ObjectTypes share the same property shape?" (Interface candidate)

**T-3 (ActionType) questions:**
1. "What state changes occur in this domain?"
2. "Is this action simple (modify one object) or complex (multi-step with logic)?"
3. "What must be true BEFORE this action can execute?" (Preconditions)
4. "What must be true AFTER this action completes?" (Postconditions)
5. "What parameters does the user provide to trigger this action?"

**T-4 (Integration) questions:**
1. "How should Ontology definitions be stored?" (YAML, JSON, database)
2. "How do Layer 1 agents access Ontology at runtime?" (file read, API, in-memory)
3. "How are Ontology validation rules enforced?" (hooks, pre-action checks, post-commit)
4. "What is the Ontology lifecycle?" (define → validate → deploy → query → evolve)

---

## 6. LLM-Agnostic Limits Context

These 5 limits motivate WHY the Ontology Framework is needed. They apply regardless
of which domain the Framework models. Lead should reference these when explaining
component value during brainstorming.

| # | Limit | What Layer 2 Framework Provides |
|---|-------|--------------------------------|
| ① | Context Collapse | ObjectType + LinkType → queryable graph replaces flat text |
| ② | Domain Ignorance | ObjectType schema → formal domain definition with types/constraints |
| ③ | Action Non-determinism | ActionType Preconditions → constraints BEFORE action executes |
| ④ | Agent Isolation | Shared Ontology graph → structured state all agents can query |
| ⑤ | Unverifiability | Postconditions → automated verification of action outcomes |

Source: `LLM-Agnostic_vs_Palantir_Ontology_Architecture.md` (808 lines, already analyzed).

---

## 7. Illustrative Example: Agent Teams as a Domain

This section preserves the researcher analysis as an EXAMPLE of how Ontology Components
would be applied to the Agent Teams infrastructure domain. This is NOT the Framework design —
it is a demonstration of what the Framework enables.

When the user chooses their first domain (Decision #6: TBD), this example serves as a
reference for the brainstorming process.

### Example ObjectType Candidates (from Entity Discovery)

| Entity | Unique ID? | Persisted? | Queryable? | Verdict |
|--------|-----------|-----------|-----------|---------|
| Session | team session id | orchestration-plan.md | Yes | ObjectType |
| Phase | P1-P9 | orchestration-plan.md | Yes | ObjectType |
| Task | TSK-xxx | Task API JSON | Yes | ObjectType |
| Teammate | agent-id | orchestration-plan.md | Yes | ObjectType |
| GateRecord | phase+gate id | gate-record.yaml | Yes | ObjectType |
| Module | file/dir path | Codebase Impact Map | Yes | ObjectType |
| DIA Step | No stable ID | Embedded in messages | No | Struct on Task |
| L1/L2/L3 | file path | Phase output files | By path only | Struct on Task |

### Example LinkType Candidates

| Relationship | Cardinality | Backing | Rationale |
|-------------|-------------|---------|-----------|
| Session → Phase | ONE_TO_MANY | FK on Phase | Containment |
| Phase → Task | ONE_TO_MANY | FK on Task | Containment |
| Task ↔ Teammate | MANY_TO_MANY | OBJECT_BACKED | Assignment has properties (DIA state) |
| Phase → GateRecord | ONE_TO_ONE | FK | Each phase has one gate |
| Module → Module | MANY_TO_MANY | JOIN_TABLE | Self-referential dependency graph |

### Example ActionType Candidates

| Action | Type | Precondition Example |
|--------|------|---------------------|
| assignTask | Complex | impactAnalysisStatus == VERIFIED |
| approveGate | Complex | all phase tasks COMPLETED |
| spawnTeammate | Complex | S-1/S-2/S-3 gates passed |

### Example Interface Candidates

| Interface | Shared Properties | Example Implementors |
|-----------|-------------------|---------------------|
| Identifiable | entityId, displayName, status | Session, Phase, Task |
| Trackable | status, startedAt, completedAt | Task, Phase, GateRecord |

---

## 8. Anti-Patterns (Domain-Agnostic)

These anti-patterns apply regardless of which domain is modeled.
Lead should warn user about these during every brainstorming session.

| Code | Name | Risk | Prevention |
|------|------|------|-----------|
| DEC-ANTI-001 | One-to-One Table Mirroring | Over-engineering | Only create ObjectTypes for independently queryable entities |
| DEC-ANTI-002 | CRUD-Only Actions | Semantic loss | Use business-meaningful action names, not generic CRUD |
| LT_ANTI_001 | Isolated Objects | Reduced utility | Every ObjectType must participate in at least one LinkType |
| LT_ANTI_002 | Spiderweb Ontology | Query degradation | Keep <10 LinkTypes per ObjectType |
| LT_ANTI_007 | FK Without Formal Link | Lost traversal | Always create formal LinkType for FK references |
| IF_ANTI_001 | Non-Unique PKs | Collision | Use composite IDs with type prefix |
| IF_ANTI_003 | Over-Abstraction | Complexity | Only create Interface when 2+ types share semantically identical properties |
| GENERAL | Coincidental Similarity | Semantic confusion | Same name ≠ same concept across domains |

---

## 9. Feasibility Considerations

### Storage Options (user decision needed in T-4)

| Option | Description | Complexity |
|--------|-------------|-----------|
| A: YAML-on-disk | Ontology definitions as `.yaml` files, validated by hooks | LOW |
| B: JSON graph | ObjectTypes as JSON with FK references, queried by scripts | MEDIUM |
| C: Foundry API | Full Ontology on Foundry platform via REST | HIGH |

Previous analysis recommended Option A for initial implementation.

### Scope Boundary

Each brainstorming session produces a design file, not implementation.
Design file → `/agent-teams-write-plan` → `/agent-teams-execution-plan`.

---

## 10. Operational Constraints

- Max 2 teammates spawned concurrently (local PC memory)
- Shift-left 80%+ effort in Phases 1-5
- Max token usage (Claude Max X20, no conservation)
- Sequential and thorough execution
- claude-code-guide research mandatory before any skill/protocol design
- Each design file must include Forward-Compatibility section
