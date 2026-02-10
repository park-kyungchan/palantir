# Ontology Framework — Sequential Calling Protocol

> **Purpose:** Concrete specification for executing T-0→T-1→T-2→T-3→T-4 brainstorming
> topics sequentially via `/brainstorming-pipeline` with proper dependency chains.
> **Format:** English only. Machine-readable for Opus 4.6.
> **Date:** 2026-02-10
> **Companion docs:**
> - `docs/plans/2026-02-10-rtdi-codebase-assessment.md` — WHY Layer 2 (T-0 input)
> - `docs/plans/2026-02-08-ontology-bridge-handoff.md` — WHAT to brainstorm (T-1~T-4 methodology)

---

## 1. Execution Overview

```
T-0: RTDI Layer 2 Strategy          ← START HERE
  │   Input: rtdi-codebase-assessment.md + ontology-bridge-handoff.md
  │   Output: layer2-strategy-design.md (scope, domain, migration)
  │
  └──→ T-1: ObjectType + Property + Struct
        │   Input: T-0 output + bridge-reference/ (5 files)
        │   Output: objecttype-design.md
        │
        ├──→ T-2: LinkType + Interface
        │     Input: T-1 output + ontology_2.md + ontology_9.md
        │     Output: linktype-design.md
        │
        ├──→ T-3: ActionType + Pre/Postconditions
        │     Input: T-1 output + ontology_3.md + ontology_7.md
        │     Output: actiontype-design.md
        │
        └────┬───→ T-4: Framework Integration Architecture
             │     Input: T-1 + T-2 + T-3 outputs + ontology_4/5/6.md
             │     Output: integration-design.md
             │
             └──→ IMPLEMENTATION (P4→P5→P6→P9 per component or all-at-once)
```

**Execution order:** T-0 → T-1 → T-2 → T-3 → T-4 (strictly sequential)
**Each topic:** One `/brainstorming-pipeline` session (P0-3 only, design not implementation)
**PT accumulation:** PT-v{N} grows monotonically across topics

---

## 2. PT Version Evolution

```
T-0 start:  PT-v1 created (or reuse existing if Ontology Framework PT exists)
T-0 Gate 3: PT-v1 → PT-v2 (T-0 summary + strategy decisions)
T-1 start:  PT-v2 reused
T-1 Gate 3: PT-v2 → PT-v3 (T-1 summary + ObjectType decisions)
T-2 start:  PT-v3 reused
T-2 Gate 3: PT-v3 → PT-v4 (T-2 summary + LinkType decisions)
T-3 start:  PT-v4 reused
T-3 Gate 3: PT-v4 → PT-v5 (T-3 summary + ActionType decisions)
T-4 start:  PT-v5 reused
T-4 Gate 3: PT-v5 → PT-v6 (T-4 summary + Integration decisions, ALL COMPLETE)
```

---

## 3. Topic Specifications

### T-0: RTDI Layer 2 Integration Strategy

```yaml
topic:
  id: T-0
  name: "RTDI Layer 2 Integration Strategy"
  dependencies: []

invocation:
  skill: /brainstorming-pipeline
  arguments: >
    Design RTDI Layer 2 Integration Strategy — bridge between
    Layer 1 INFRA (v7.0, ~6000L, 35 entities) and Layer 2
    Ontology Framework. See docs/plans/2026-02-10-rtdi-codebase-assessment.md
    for gap analysis and docs/plans/2026-02-08-ontology-bridge-handoff.md
    for component definitions.

preconditions:
  permanent_task: none (will create)
  prior_designs: []
  reference_docs:
    - docs/plans/2026-02-10-rtdi-codebase-assessment.md
    - docs/plans/2026-02-08-ontology-bridge-handoff.md

phase_focus:
  phase_1_qa:
    - PURPOSE: What Layer 2 strategy achieves (close 6 gaps from assessment §3)
    - SCOPE: Which gaps to address first? All 6 or prioritized subset?
    - APPROACH: Incremental adoption vs full migration? YAML-on-disk confirmed?
    - DOMAIN: INFRA itself as bootstrap domain (confirmed in assessment §9)
    - RISK: Layer 1 readability preserved? RSIL findings remain valid?
    - LEARNING: Explain Layer 1/Layer 2 distinction and gap concepts to user
      before asking strategy decisions (Rule 7: TEACH → CONTEXTUALIZE → ASK)
  phase_2_research:
    - Read assessment §3-§4 (gap analysis + component mapping)
    - Read handoff §2-§3 (framework components + topic dependency)
    - Read handoff §5.0-§5.1 (Dual Purpose session flow + teaching methodology)
    - Read bridge-ref-methodology.md (decomposition guide)
    - Investigate: how do YAML-on-disk schemas coexist with markdown?
    - Prepare teaching materials: Ontology vocabulary, concrete examples for user
  phase_3_architecture:
    - Migration strategy (NL → NL+Schema, incremental per ObjectType)
    - Bootstrap sequence (which INFRA entity first?)
    - Storage format decision (YAML-on-disk details)
    - Success criteria mapping (assessment §10 SC-1~SC-8)
    - Include learning notes in design file (user comprehension checkpoint)

output:
  design_file: docs/plans/YYYY-MM-DD-ontology-layer2-strategy-design.md
  pt_version: PT-v2
  handoff: T-0 output defines scope/domain/strategy for T-1~T-4
```

### T-1: ObjectType + Property + Struct

```yaml
topic:
  id: T-1
  name: "ObjectType + Property + Struct"
  dependencies: [T-0]

invocation:
  skill: /brainstorming-pipeline
  arguments: >
    Ontology Framework — ObjectType, Property, and Struct component
    design for INFRA domain. Depends on T-0 strategy
    (see docs/plans/YYYY-MM-DD-ontology-layer2-strategy-design.md)

preconditions:
  permanent_task: PT-v2 (contains T-0 COMPLETE + strategy decisions)
  prior_designs:
    - docs/plans/YYYY-MM-DD-ontology-layer2-strategy-design.md
  reference_docs:
    - palantir_ontology_1.md (lines 1-700: ObjectType, PropertyType, Struct)
    - palantir_ontology_9.md (lines 100-250: Entity Discovery tree)
    - bridge-ref-objecttype.md (restructured reference)
    - bridge-ref-methodology.md (decomposition guide)

phase_focus:
  phase_1_qa:
    - Which INFRA entities become ObjectTypes? (35 candidates from R-1 inventory)
    - What PK strategy? (composite ID with type prefix recommended)
    - Which entities are Structs vs ObjectTypes? (Entity Discovery decision tree)
    - What property types needed? (13 Palantir types as catalog)
  phase_2_research:
    - Read ontology_1.md for ObjectType/Property/Struct definitions
    - Read T-0 design for domain selection and bootstrap sequence
    - Apply Entity Discovery tree to INFRA entities
  phase_3_architecture:
    - ObjectType definition schema (YAML format)
    - Property type catalog with constraints
    - Struct embedding rules
    - Forward-compatibility with T-2 LinkTypes and T-3 ActionTypes

output:
  design_file: docs/plans/YYYY-MM-DD-ontology-objecttype-design.md
  pt_version: PT-v3
  handoff: T-1 ObjectTypes referenced by T-2 LinkTypes (via PK) and T-3 ActionTypes
```

### T-2: LinkType + Interface

```yaml
topic:
  id: T-2
  name: "LinkType + Interface"
  dependencies: [T-1]

invocation:
  skill: /brainstorming-pipeline
  arguments: >
    Ontology Framework — LinkType and Interface component for INFRA
    domain. Depends on T-1 ObjectType design
    (see docs/plans/YYYY-MM-DD-ontology-objecttype-design.md)

preconditions:
  permanent_task: PT-v3 (contains T-0 + T-1 COMPLETE)
  prior_designs:
    - T-0 strategy design
    - T-1 objecttype design (REQUIRED — LinkTypes reference ObjectTypes)
  reference_docs:
    - palantir_ontology_2.md (cardinality, backing, Interface, Search Around)
    - palantir_ontology_9.md (lines 250-400: Relationship Discovery)
    - bridge-ref-linktype.md

phase_focus:
  phase_1_qa:
    - What relationships exist between T-1's ObjectTypes?
    - Cardinality per relationship? (1:1, 1:N, N:1, M:N)
    - Backing mechanism? (FK, JOIN_TABLE, OBJECT_BACKED)
    - Which ObjectTypes share property shapes? (Interface candidates)
  phase_2_research:
    - Read T-1 ObjectTypes to identify relationship candidates
    - Read ontology_2.md for LinkType patterns
    - Apply Relationship Discovery (6 indicators)
  phase_3_architecture:
    - LinkType definition schema
    - Interface contract system
    - Graph traversal rules (Search Around)
    - Forward-compatibility with T-3 preconditions and T-4 query engine

output:
  design_file: docs/plans/YYYY-MM-DD-ontology-linktype-design.md
  pt_version: PT-v4
```

### T-3: ActionType + Pre/Postconditions

```yaml
topic:
  id: T-3
  name: "ActionType + Pre/Postconditions"
  dependencies: [T-1]  # T-2 optional but beneficial

invocation:
  skill: /brainstorming-pipeline
  arguments: >
    Ontology Framework — ActionType and Pre/Postconditions component
    for INFRA domain. Depends on T-1 ObjectType design.

preconditions:
  permanent_task: PT-v4 (contains T-0 + T-1 + T-2 COMPLETE)
  prior_designs:
    - T-1 objecttype design (REQUIRED — actions operate on ObjectTypes)
    - T-2 linktype design (OPTIONAL — for precondition examples using relationships)
  reference_docs:
    - palantir_ontology_3.md (ActionType, Parameters, Pre/Postconditions)
    - palantir_ontology_7.md (Functions, Automation, Logic patterns)
    - palantir_ontology_9.md (lines 400-550: Mutation Discovery)
    - bridge-ref-actiontype.md

phase_focus:
  phase_1_qa:
    - What state changes occur in INFRA? (gate approval, task assignment, etc.)
    - Simple vs Complex actions?
    - What "Never" rules become Preconditions?
    - What gate criteria become Postconditions?
  phase_2_research:
    - Read ontology_3.md for ActionType patterns
    - Read ontology_7.md for automation/function patterns
    - Map current INFRA "Never" rules to formal preconditions
  phase_3_architecture:
    - ActionType definition schema
    - Precondition/Postcondition engine
    - Parameter types
    - Forward-compatibility with T-4 runtime execution

output:
  design_file: docs/plans/YYYY-MM-DD-ontology-actiontype-design.md
  pt_version: PT-v5
```

### T-4: Framework Integration Architecture

```yaml
topic:
  id: T-4
  name: "Framework Integration Architecture"
  dependencies: [T-1, T-2, T-3]

invocation:
  skill: /brainstorming-pipeline
  arguments: >
    Ontology Framework — Integration Architecture synthesizing
    T-1/T-2/T-3 component designs with current INFRA v7.0 state.

preconditions:
  permanent_task: PT-v5 (contains T-0 + T-1 + T-2 + T-3 ALL COMPLETE)
  prior_designs:
    - T-0 strategy design
    - T-1 objecttype design
    - T-2 linktype design
    - T-3 actiontype design
  reference_docs:
    - palantir_ontology_4.md (Data Pipeline → adapt for local)
    - palantir_ontology_5.md (Storage → YAML/JSON on disk)
    - palantir_ontology_6.md (API → CLI access patterns)
    - bridge-ref-secondary.md
    - bridge-ref-methodology.md

phase_focus:
  phase_1_qa:
    - Storage format decision (YAML confirmed? directory structure?)
    - Query engine (graph traversal, Search Around implementation)
    - Validation pipeline (schema enforcement mechanism)
    - Agent access patterns (how agents use Ontology at runtime)
  phase_2_research:
    - Read all 3 prior design files + strategy
    - Read ontology_4/5/6.md for infrastructure patterns
    - BUG-002 mitigation: split research if >6000L total read load
  phase_3_architecture:
    - Storage format + directory layout
    - Query engine architecture
    - Validation pipeline (hooks? pre-action checks?)
    - Runtime integration (Layer 1 ↔ Layer 2 interface)
    - SC-1~SC-8 mapping (from assessment §10)

output:
  design_file: docs/plans/YYYY-MM-DD-ontology-integration-design.md
  pt_version: PT-v6 (ALL COMPLETE — ready for implementation)
```

---

## 4. Dependency Graph

```
T-0 ─────────────────────────────────────────────────────────┐
  │                                                           │
  └──→ T-1 ──┬──→ T-2 ──┐                                   │
              │           │                                   │
              └──→ T-3 ──┼──→ T-4 ──→ IMPLEMENTATION        │
                          │                                   │
                          └───────────────────────────────────┘
                                    (all reference T-0 strategy)

Strict dependencies (must complete before):
  T-0 → T-1 → T-2 → T-4
  T-0 → T-1 → T-3 → T-4

T-2 and T-3 both depend only on T-1 (parallelizable in theory,
but sequential recommended to avoid PT version conflicts).
```

---

## 5. Coordination Rules

### Rule 1: One Topic = One Session
Each T-N gets its own `/brainstorming-pipeline` invocation (P0-3).
Sessions are independent — no shared GC-v{N} across topics.
PT is the ONLY cross-session state carrier.

### Rule 2: PT is Accumulator
PT grows monotonically. Each topic adds its summary and decisions.
Never reset PT version. Never create a new PT if one exists for "Ontology Framework".

### Rule 3: Design Files are Handoff Artifacts
Design files in `docs/plans/` persist across sessions.
$ARGUMENTS for T-N+1 references T-N's design file path.
Researcher directives embed prior design file paths.

### Rule 4: Dependencies Validated in Phase 0
Before starting T-N, Phase 0 validates:
- PT contains "T-{dependency} COMPLETE" for each dependency
- Prior design files exist on disk (Glob check)
If validation fails: ABORT with message indicating which dependency to complete first.

### Rule 5: Design File Naming
Pattern: `docs/plans/YYYY-MM-DD-ontology-{component}-design.md`
Revisions: append `-v2` suffix on same day.

### Rule 6: Forward-Compatibility Section Mandatory
Every design file must include a "Forward-Compatibility" section explaining:
- How subsequent components will reference this design
- What decisions are deferred to later topics
- What interface contracts this design exposes

### Rule 7: Dual Purpose — Decision-Making + Learning
Every session serves two purposes simultaneously (see handoff §5.0):
1. **Decision-Making:** Lead guides user through Ontology component design decisions
2. **Learning:** User progressively learns Ontology/Foundry concepts across sessions

Lead must follow TEACH → CONTEXTUALIZE → ASK flow:
- Phase 1: Explain the component concept using reference docs BEFORE asking decisions
- Phase 2: Researcher prepares teaching materials (key concepts, examples, decision points)
- Phase 3: Walk user through discovery process, present trade-offs, build on prior sessions

Learning progression accumulates: T-0 (strategy vocabulary) → T-1 (entity concepts) →
T-2 (relationship patterns) → T-3 (state machine thinking) → T-4 (full schema comprehension).
Each T-N assumes knowledge from all prior topics.

---

## 6. Edge Cases

### Skip a Topic
T-3 can start without T-2 (both depend on T-1 only). T-4 CANNOT start
without both T-2 and T-3 complete.

### Revise a Completed Topic
Option A (major): New brainstorming session producing `-v2` design file.
Option B (minor): Manual edit + `/permanent-tasks` update.
Dependent topics may need revision if changes are significant.

### PT Already Exists from Prior Work
Phase 0 matches PT subject against "Ontology Framework".
If match: reuse. If mismatch: ask user. Never create duplicate PTs.

### Context Compaction During Research (BUG-002)
T-4 reads 3+ design files + 3+ reference docs (~15K+ lines).
Mitigation: split research across 2 researchers, or sequential reads with
L1/L2 written proactively after each document group.

---

## 7. Post-Design Implementation Path

After T-4 completes (PT-v6, all 4 design files exist):

**Option A (all-at-once):**
```
/agent-teams-write-plan → P4 (implementation plan for all components)
/plan-validation-pipeline → P5 (validate plan)
/agent-teams-execution-plan → P6 (implement all)
/delivery-pipeline → P9 (commit + deliver)
```

**Option B (per-component):**
```
For each T-N (T-1 → T-2 → T-3 → T-4):
  /agent-teams-write-plan → P4
  /agent-teams-execution-plan → P6
  /delivery-pipeline → P9
```

Decision deferred to T-4 brainstorming (depends on coupling between components).

---

## 8. Reference Documentation Index

| Topic | Primary Reference | Bridge Reference | Ontology_9 Section |
|-------|-------------------|------------------|-------------------|
| T-0 | rtdi-codebase-assessment.md | ontology-bridge-handoff.md | — |
| T-1 | palantir_ontology_1.md (1-700) | bridge-ref-objecttype.md | §Entity Discovery (100-250) |
| T-2 | palantir_ontology_2.md (1-600) | bridge-ref-linktype.md | §Relationship Discovery (250-400) |
| T-3 | palantir_ontology_3.md + _7.md | bridge-ref-actiontype.md | §Mutation Discovery (400-550) |
| T-4 | palantir_ontology_4/5/6.md | bridge-ref-secondary.md | — |
| ALL | — | bridge-ref-methodology.md | Full (8-phase process) |

Reference file location: `park-kyungchan/palantir/Ontology-Definition/docs/`
Bridge reference location: `park-kyungchan/palantir/Ontology-Definition/docs/bridge-reference/`
