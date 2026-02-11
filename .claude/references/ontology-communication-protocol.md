# Ontology Communication Protocol — Reference Document

> Verified against official palantir.com/docs (2026-02-10)
> 3 researcher verifications: 40+ official pages, 60+ source URLs
> Use alongside: park-kyungchan/palantir/Ontology-Definition/docs/ (9 docs, 15 files)

---

## 1. Response Pattern: TEACH → IMPACT ASSESS → RECOMMEND → ASK

Active whenever Palantir Ontology or Foundry concepts arise in any context.
User = concept-level decision-maker. Opus = teaching implementer.

### TEACH
- Define the component: official definition + paradigm mapping (OOP / RDBMS / RDF analog)
- Distinguish 3 knowledge layers (see §6): Palantir Concept / Our Methodology / Bridge Adaptation
- State non-obvious constraints that affect downstream decisions

### IMPACT ASSESS
3 analysis axes, 4 risk dimensions.

**Axis 1 — Component Chain:** Trace the verified dependency map (§2). Show direct
and transitive effects using edge labels. Count affected components.

**Axis 2 — Implementation Feasibility:** Classify as Preserved (use as-is) / Adapted
(YAML equivalent exists) / Redesign (fundamentally different) / Drop (not applicable locally).

**Axis 3 — Domain Fitness:** Apply the relevant decision tree (§4). Check the
anti-pattern catalog (§3). Assess from 8-phase methodology perspective — does this
decision create problems in later phases?

**Risk 1 — Design Complexity:** Dependency edge count (Low 1-2, Med 3-5, High 6+)
**Risk 2 — Domain Mismatch:** Named anti-pattern match from §3
**Risk 3 — Extensibility:** Future constraint severity (blocked / cascade / reindex)
**Risk 4 — Performance:** Known threshold patterns from §5

### RECOMMEND
Present the relevant decision tree from §4. Highlight recommended path with rationale.
Note which anti-patterns the recommended path avoids. If trade-offs exist, present
them with impact severity.

### ASK
Frame the decision reflecting IMPACT ASSESS findings. Offer 2-3 options with clear
trade-off profiles. The question should test understanding: "Given that [impact], which approach?"

---

## 2. Verified Dependency Map

All edges verified against official palantir.com/docs (Feb 2026).

### Schema Layer
```
ObjectType --contains--> Property (1:N, max ~2000)
ObjectType --uses--> SharedProperty (optional, metadata inheritance)
ObjectType --has--> ID (lowercase+dashes) + apiName (PascalCase) [two identifiers]
ObjectType --backed_by--> Dataset (1:1, no MapType/StructType columns)
Property --backed_by--> SharedProperty (optional, disables direct metadata editing)
Property --typed_by--> BaseType (22+ types, see §5)
Property --constrained_by--> ValueTypeConstraint (8 core types)
SharedProperty --propagates_to--> Property (metadata + render hint inheritance)
SharedProperty --governs--> Struct fields (if struct-typed)
SharedProperty --used_by--> Interface (optional, enables auto-mapping)
```

### Relationship Layer
```
LinkType --connects--> ObjectType × ObjectType (4 cardinalities)
LinkType --backed_by--> FK (1:1/1:N/N:1) | JoinTable (M:N) | ObjectType (extends N:1, effective M:N)
LinkType --self_referential--> ObjectType (same source and target allowed)
LinkType --scoped_to--> single Ontology (no cross-ontology links)
Interface --defines--> InterfaceProperty (local, RECOMMENDED) | SharedProperty (imported)
Interface --extends--> Interface (multiple inheritance, inherits properties + link constraints)
Interface --constrains_links--> Interface | ObjectType (cardinality: ONE or MANY)
Interface --implemented_by--> ObjectType (required + optional property mapping)
ObjectType --implements--> Interface (N:M)
ObjectType --participates_in--> LinkType (as source or target)
```

### Behavior Layer
```
ActionType --modifies--> ObjectType (via 10 edit rules)
ActionType --delegates_to--> Function (via FUNCTION_RULE, exclusive)
ActionType --triggers--> Notification | Webhook (2 side-effect rules)
ActionType --validated_by--> SubmissionCriteria (at submission time)
ActionType --manipulates--> LinkType (CREATE_LINK/DELETE_LINK for M:N only)
Function --reads/edits--> ObjectType (edits see STALE data during execution)
Function --traverses--> LinkType (max 3 search arounds)
ValueTypeConstraint --validates--> Property (8 core types at write time)
SubmissionCriteria --validates--> ActionType (user/parameter conditions at submission)
```

### Cross-Layer Critical Edges
```
SharedProperty ←→ Interface: optional (NOT mandatory), auto-mapping convenience
PrimaryKey → all components: deterministic, stable, natural business keys mandatory
ONE_TO_ONE cardinality: NOT platform-enforced (semantic indicator only)
Object-backed link: extends MANY_TO_ONE (not M:N), intermediary ObjectType pattern
FK links: manipulated via MODIFY_OBJECT (not CREATE_LINK)
```

---

## 3. Verified Anti-Pattern Catalog

Source: Official palantir.com/docs signals + community patterns.
Labeled as "derived from documentation signals" (Palantir has no formal anti-pattern guide).

### Schema Layer Anti-Patterns
| ID | Name | Severity | Impact | Official Basis |
|----|------|----------|--------|---------------|
| OT-1 | Over-Normalization | Medium | ObjectType for atomic values → unnecessary links | Entity decision tree |
| OT-2 | Non-Deterministic PK | Critical | Edit loss, link breaks, OSv2 failure | CONFIRMED: "be deterministic" |
| OT-3 | Duplicate PKs | Critical | OSv2 build failure, OSv1 silent corruption | CONFIRMED: Funnel batch errors |
| P-1 | Float/Double as PK | Critical | Imprecise comparison, uniqueness fails | CONFIRMED: not valid PK types |
| P-2 | Deeply Nested Struct | Error | Struct depth limited to 1 | CONFIRMED: "no nesting allowed" |
| P-3 | Struct Array Fields | Error | Struct fields cannot be arrays (12 primitive types only) | CONFIRMED: official restriction |
| P-4 | Long as JS Identifier | High | Precision loss > 2^53 | CONFIRMED: "discouraged as PKs" |
| P-5 | Unindexed Filter Property | Medium | Searchable render hint required for filtering | CONFIRMED: silent failure |
| SP-1 | SP for Single Type | Low | Governance overhead without benefit | Plausible |
| SP-2 | Generic SP Naming | Medium | Semantic confusion across types | Plausible |
| SP-3 | SP BaseType Change | High | Breaks all using ObjectTypes | CONFIRMED: type must match column |

### Relationship Layer Anti-Patterns
| ID | Name | Severity | Impact | Official Basis |
|----|------|----------|--------|---------------|
| LT-1 | Isolated Objects | Medium | No links → reduced ontology utility | Plausible |
| LT-2 | Spiderweb (>10 links/OT) | High | Query performance, cognitive overload | Plausible |
| LT-3 | Missing Bidirectional Names | Medium | One-way traversal only | CONFIRMED: needs both API names |
| LT-4 | Cardinality Change Post-Deploy | High | Reindex + unavailability + history deletion | CONFIRMED: official warning |
| LT-5 | FK Without Formal LinkType | High | No graph navigation possible | CONFIRMED |
| LT-6 | Cross-Ontology Link Assumption | Error | Not supported at runtime | CONFIRMED |
| LT-7 | CREATE_LINK for FK Links | Error | CREATE_LINK is M:N only | CONFIRMED: "use Modify object" |
| IF-1 | OOP Behavior Assumption | Medium | Interface = data SHAPE, not methods | CONFIRMED |
| IF-2 | Non-Unique PKs Across Implementors | High | Polymorphic reference collision | Community-reported |
| IF-3 | Over-Abstraction (1 implementor) | Medium | Min 2 required | CONFIRMED |
| IF-4 | "Only SharedProperties" Assumption | High | Local properties are RECOMMENDED | CONFIRMED wrong claim |

### Behavior Layer Anti-Patterns
| ID | Name | Severity | Impact | Official Basis |
|----|------|----------|--------|---------------|
| ACT-1 | FUNCTION_RULE + Other Rules | Error | FUNCTION_RULE must be exclusive | CONFIRMED: "no other rule" |
| ACT-2 | CREATE_LINK for FK Links | Error | CREATE_LINK = M:N only | CONFIRMED |
| FUNC-1 | Search After Edit | High | Stale data during function execution | CONFIRMED: multiple sources |
| FUNC-2 | Missing Edits Declaration | High | Edits silently dropped (TS v2) | CONFIRMED |
| FUNC-3 | Side Effects in Query Function | High | Read-only contract violation | CONFIRMED |
| CONS-1 | Missing Failure Messages | Medium | Generic error UX | CONFIRMED |
| AUTO-1 | Self-Triggering Loop | High | Infinite automation cycle | CONFIRMED |

---

## 4. Decision Tree Index

### Schema Layer
**ObjectType (7 questions):**
Q1: Real-world entity or event? → Q2: Unique stable identifier? → Q3: Persisted?
→ Q4: Users search/filter/reference independently? → Q5: Multiple properties?
→ Q6: Independent lifecycle? → Q7: Separate permission controls?
Result: Strong OT candidate requires Yes to Q1-Q4 minimum.

**Property BaseType:** Branch by data nature:
TEXT → String | NUMERIC → Integer/Long/Double/Decimal | BOOLEAN | DATE/TIME
→ Date/Timestamp | LOCATION → Geopoint/Geoshape | COLLECTION → Array/Struct
| ML → Vector | FILE → MediaReference/Attachment/TimeSeries
Key: Long has JS precision issues. Struct: depth 1, max 10 fields, 12 primitive
types only, no arrays. Array: no null elements.

**SharedProperty (6 questions):**
Q1: Used by >1 ObjectType? → Q2: Same semantic meaning? → Q3: Centralized management?
→ Q4: Building an Interface? (YES doesn't require SP — local properties work too)
→ Q5: Used by 3+ ObjectTypes? → Q6: Definition likely to change?

### Relationship Layer
**LinkType:** Cardinality → Backing:
1:1/1:N/N:1 → FK | M:N without properties → JoinTable (auto-generate available)
| M:N with properties → Object-Backed (intermediary OT with two N:1 links)
Note: Object-backed extends MANY_TO_ONE pattern, not M:N directly.

**Interface (4 questions):**
Q1: Multiple OTs share same properties? → Q2: Need polymorphic operations?
→ Q3: Should relationships be abstract? → Q4: Need to compose capabilities?
Note: Properties can be local (recommended) or SharedProperty (auto-mapping convenience).
Link constraints use ONE/MANY (simpler than LinkType's 4-way cardinality).

### Behavior Layer
**ActionType:** Modify data?
→ No → Query Function | Yes → Simple CRUD? → Rule-based | Complex logic?
→ FUNCTION_RULE (exclusive) | M:N links? → CREATE_LINK/DELETE_LINK
| FK links? → MODIFY_OBJECT (change FK property value)

**Function:** 2 primary types × 3 languages:
Query (read-only) | OntologyEdit (mutations, stale data caveat)
× TypeScript v2 (recommended) | Python (data science) | TypeScript v1 (legacy)
+ AIP Logic (separate: no-code, LLM-powered)

**Constraint:** 3 independent levels:
Property → ValueTypeConstraint (8 types: Enum, Range, Regex, RID, UUID, Uniqueness, Nested, StructElement)
Action → SubmissionCriteria (CURRENT_USER / PARAMETER conditions)
Schedule → ValidationRules (Hard blocks / Soft warnings)

---

## 5. Scale Limits and Performance Thresholds

### ObjectType
- Properties per ObjectType: ~2000
- Backing datasource: 1:1 (no MapType/StructType columns)
- Multi-Dataset Objects: max ~5 additional datasets before degradation

### LinkType
- Search Around: max 3 operations per function
- OSv2 search around result: 10,000,000 objects
- OSv1 search around result: 100,000 objects
- Object loading: 100,000 (>10,000 may timeout)
- Pagination: 10,000 per page

### ActionType
- Objects per submission: 10,000
- Object types per submission: 50
- Primitive list parameters: 10,000 elements
- Object reference list: 1,000 elements
- Individual edit size: 32KB (OSv1) / 3MB (OSv2)
- Batch calls: 10,000 (standard) / 20 (function-backed without batching)
- Notification recipients: 500 (standard) / 50 (function-rendered)

### Function
- Default runtime: 60 seconds (280s for live preview)
- TS v1: 128 MB memory, 30s CPU time
- Serverless: 512-5120 MiB configurable (default 1024 MiB)
- Deployed Python: 2 GiB (not configurable)

### Property
- Struct: depth 1, max 10 fields, 12 primitive types only, no array fields
- Array: no null elements
- Aggregation buckets: 10,000 total

### BaseType Catalog (22+ verified)
Primitive: String, Integer, Short, Long, Byte, Boolean, Float, Double, Decimal
Time: Date, Timestamp
Geospatial: Geopoint (WGS 84), Geoshape (GeoJSON)
Complex: Array, Struct, Vector
Reference: MediaReference, Attachment, TimeSeries, GeotimeSeriesReference
Special: CipherText, Marking (aka MandatoryControl)

---

## 6. Three-Layer Knowledge Classification

### Layer A — Palantir Concepts (transferable knowledge)
Everything below is from official Palantir Foundry documentation and applies
to any Palantir deployment. Teach these AS Palantir knowledge.

- 8 core components: ObjectType, Property, SharedProperty, LinkType, Interface,
  ActionType, Function, Rule_Constraint (split: ValueTypeConstraint + SubmissionCriteria)
- Property type system (22+ baseTypes)
- Cardinality model (1:1, 1:N, N:1, M:N) and backing mechanisms (FK, JoinTable, Object-Backed)
- Pre/postcondition contract pattern on ActionTypes
- FUNCTION_RULE exclusivity, stale data caveat, Search Around limits
- Anti-patterns (all verified entries in §3)
- Security concepts (RBAC, Markings, Restricted Views, Granular Policies)
- Platform support matrix for Interfaces

### Layer B — Our Decomposition Methodology (locally synthesized)
Systematic workflow created by us using Palantir concepts. Palantir does NOT
provide a multi-phase decomposition methodology. Teach these as OUR approach.

- 8-phase sequential workflow (Entity → Relationship → Mutation → Logic → Interface → Automation → Security → Assembly)
- Decision trees with specific question counts (7Q ObjectType, 6Q SharedProperty, etc.)
- Source scanning indicators (7/6/6 counts)
- Quality checklist (7 items)
- Validation rules (DEC-VAL-001 through DEC-VAL-006)
- YAML output template structure

### Layer C — Bridge Adaptations (local-specific)
Translation from Palantir Foundry platform to local Claude Code CLI environment.
Teach these as LOCAL IMPLEMENTATION CHOICES.

- YAML files instead of Foundry platform storage
- Filesystem directories (ontology/objects/, ontology/links/, etc.)
- CLI orchestration instead of Workshop UI
- LLM agents reading YAML directly instead of OSDK code generation
- NL enforcement instead of platform-enforced constraints
- ontology.lock instead of Foundry versioning
- Agent Teams messaging instead of API Gateway

---

## 7. Component Definition Order

Dependency-chain-based sequential order for defining Ontology components.
Each component is defined only after its dependencies are established.

```
Phase 1: ObjectType (entity definition, PK strategy, property schema)
  ↓ depends on nothing — foundational component
Phase 2: Property + SharedProperty (type system, constraints, cross-type consistency)
  ↓ depends on ObjectType (properties belong to ObjectTypes)
Phase 3: LinkType (relationships, cardinality, backing mechanism)
  ↓ depends on ObjectType (links connect ObjectTypes)
Phase 4: Interface (polymorphic shape, property contracts, link constraints)
  ↓ depends on SharedProperty (auto-mapping) + LinkType (link constraints)
Phase 5: ActionType (mutations, rules, parameters)
  ↓ depends on ObjectType + LinkType (rules target OTs, manipulate links)
Phase 6: Function (logic, Query vs Edit, language selection)
  ↓ depends on ActionType (FUNCTION_RULE delegation) + ObjectType/LinkType (read/edit/traverse)
Phase 7: Constraints (ValueTypeConstraint + SubmissionCriteria + SchedulingRules)
  ↓ depends on Property (property constraints) + ActionType (submission criteria)
Phase 8: Automation + Security
  ↓ depends on all above (monitors ObjectTypes, triggers Actions, enforces access)
```

Each definition session follows TEACH → IMPACT ASSESS → RECOMMEND → ASK.
IMPACT ASSESS traces the dependency map starting from the current component.

---

## 8. Corrections to Original Docs

Summary of verified corrections for `park-kyungchan/palantir/Ontology-Definition/docs/`.
Apply these when updating the reference materials.

### palantir_ontology_1.md (ObjectType, Property, SharedProperty)
- Remove "EXAMPLE" from Status enum (4 values: ACTIVE/EXPERIMENTAL/DEPRECATED/ENDORSED)
- Add ObjectType "ID" field (lowercase+dashes, separate from apiName)
- Note primaryKey is an ARRAY (multi-property PK natively supported)
- Add Struct restrictions: no array fields, 12 primitive types only, OSv2 only
- Add Array restriction: no null elements
- Add missing constraint types: Nested, StructElement
- Correct SharedProperty deletion: safe revert to local properties (not destructive)
- Add Value Types concept (semantic wrappers for baseTypes)
- Add SharedProperty-Struct interaction (governs struct field metadata)
- Flag as UNVERIFIED: Vector max 2048 dims, render hint dependency chain

### palantir_ontology_2.md (LinkType, Interface)
- CRITICAL: Change "Interface schemas ONLY SharedProperties" → "Local properties recommended, SharedProperty optional (auto-mapping)"
- Change Object-backed: "extends MANY_TO_ONE" (not "M:N with properties")
- Remove 50K scale threshold; add real limits (10M OSv2, 100K OSv1, 100K loading)
- Add: self-referential links supported
- Add: cross-ontology linking NOT supported
- Add: Interface link constraints use ONE/MANY (not 4-way cardinality)
- Add: required vs optional properties and link constraints on interfaces
- Add: ONE_TO_ONE not supported in Pipeline Builder
- Add: auto-generate join table available for M:N links
- Add: LinkType metadata (status, visibility, type classes)

### palantir_ontology_3.md (ActionType, Function, Rule_Constraint)
- Expand to 12 rules: 10 edit + 2 side-effect (Notification, Webhook)
- Remove VECTOR from parameter types (property baseType only)
- Restructure Function taxonomy: 2 types × 3 languages + AIP Logic
- Correct constraint count: 8 core types (STRING_LENGTH/ARRAY_SIZE = RANGE variants)
- Remove REQUIRED from constraint types (it's a property flag, not a constraint)
- Add scale limits table
- Add interface action limitations (no link edits, no function compat, no logs)

### palantir_ontology_9.md (Decomposition)
- Add explicit label: "Community-derived methodology, Palantir-grounded"
- Not from official Palantir documentation

---

## Source URLs

### ObjectType + Property
- https://www.palantir.com/docs/foundry/object-link-types/object-types-overview
- https://www.palantir.com/docs/foundry/object-link-types/create-object-type
- https://www.palantir.com/docs/foundry/object-link-types/properties-overview
- https://www.palantir.com/docs/foundry/object-link-types/base-types
- https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints
- https://www.palantir.com/docs/foundry/object-link-types/structs-overview

### SharedProperty + Interface
- https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview
- https://www.palantir.com/docs/foundry/interfaces/interface-overview
- https://www.palantir.com/docs/foundry/interfaces/create-interface
- https://www.palantir.com/docs/foundry/interfaces/implement-interface

### LinkType
- https://www.palantir.com/docs/foundry/object-link-types/link-types-overview
- https://www.palantir.com/docs/foundry/object-link-types/create-link-type

### ActionType + Function
- https://www.palantir.com/docs/foundry/action-types/rules
- https://www.palantir.com/docs/foundry/action-types/submission-criteria
- https://www.palantir.com/docs/foundry/action-types/scale-property-limits
- https://www.palantir.com/docs/foundry/functions/overview
- https://www.palantir.com/docs/foundry/functions/typescript-v2-ontology-edits
- https://www.palantir.com/docs/foundry/functions/enforced-limits
