# Ontology Docs Corrections — Verified Against Official Palantir Documentation

> Date: 2026-02-10
> Method: 3 researcher verifications using WebSearch + WebFetch against palantir.com/docs
> Source: 40+ official pages, 60+ source URLs
> Target: park-kyungchan/palantir/Ontology-Definition/docs/ (9 primary + 6 bridge files)
> **Status: APPLIED** — All CRITICAL and HIGH corrections applied. Most MEDIUM applied. LOW deferred.

---

## Priority: CRITICAL (Must Fix — Fundamental Errors)

### CRT-1: Interface ≠ "ONLY SharedProperties"
- **File:** palantir_ontology_2.md (Interface section)
- **Current:** "Interface schemas are composed ONLY of SharedProperties — you cannot add local Properties"
- **Correct:** Interfaces support BOTH local properties (RECOMMENDED) and SharedProperties (optional, auto-mapping convenience)
- **Source:** https://www.palantir.com/docs/foundry/interfaces/create-interface
- **Impact:** Cascades into dependency map, design decisions, SharedProperty over-creation

### CRT-2: Object-Backed Link = extends M:1 (not M:N)
- **File:** palantir_ontology_2.md (LinkType section)
- **Current:** "OBJECT_BACKED: M:N with properties via intermediary ObjectType"
- **Correct:** Object-backed links "expand on many-to-one cardinality link types" — the intermediary has TWO N:1 links achieving effective M:N
- **Source:** https://www.palantir.com/docs/foundry/object-link-types/link-types-overview
- **Impact:** Affects backing mechanism selection and intermediary ObjectType design

## Priority: HIGH (Should Fix — Significant Inaccuracies)

### HI-1: Status Enum (ObjectType)
- **File:** palantir_ontology_1.md
- **Current:** 5 values (ACTIVE/EXPERIMENTAL/DEPRECATED/EXAMPLE/ENDORSED)
- **Correct:** 4 values (remove EXAMPLE — not in API v2)
- **Source:** Get Object Type API v2

### HI-2: SharedProperty Deletion = Safe Revert
- **File:** palantir_ontology_1.md
- **Current:** "deleting cascades to all users" (implies destructive)
- **Correct:** "all using object types revert to regular properties" (safe, like detaching for all)
- **Source:** https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview

### HI-3: Struct Field Restrictions Incomplete
- **File:** palantir_ontology_1.md
- **Current:** "depth=1, max 10 fields"
- **Add:** Fields CANNOT be arrays. Only 12 primitive types: BOOLEAN, BYTE, DATE, DECIMAL, DOUBLE, FLOAT, GEOPOINT, INTEGER, LONG, SHORT, STRING, TIMESTAMP. OSv2 only.
- **Source:** https://www.palantir.com/docs/foundry/object-link-types/structs-overview

### HI-4: 50K Scale Threshold Does Not Exist
- **File:** palantir_ontology_2.md
- **Current:** "50,000 objects (use join materializations above)"
- **Correct:** Real limits: OSv2 SA = 10M, OSv1 = 100K, object loading = 100K, timeout risk >10K
- **Source:** https://www.palantir.com/docs/foundry/functions/enforced-limits

### HI-5: Rule Types = 12 (not 10)
- **File:** palantir_ontology_3.md
- **Current:** "10 Rule Types"
- **Correct:** 10 Ontology Edit Rules + 2 Side-Effect Rules (Notification, Webhook) = 12
- **Source:** https://www.palantir.com/docs/foundry/action-types/rules

### HI-6: Function Taxonomy Flat List
- **File:** palantir_ontology_3.md, palantir_ontology_7.md
- **Current:** "6 function types" (Generic, OntologyEdit, Query, TS v2, Python, AIP Logic)
- **Correct:** 2 primary types (Query / OntologyEdit) × 3 languages (TS v2 / TS v1 / Python) + AIP Logic (separate). Language is orthogonal to type.
- **Source:** https://www.palantir.com/docs/foundry/functions/overview

### HI-7: Constraint Types = 8 Core (not 11)
- **File:** palantir_ontology_3.md
- **Current:** "11 Property Constraint Types" including STRING_LENGTH, ARRAY_SIZE, REQUIRED
- **Correct:** 8 core: Enum(ONE_OF), Range, Regex, RID, UUID, Uniqueness, Nested, StructElement. STRING_LENGTH/ARRAY_SIZE = Range variants. REQUIRED = property flag, not constraint.
- **Source:** https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints

### HI-8: Missing Constraint Types
- **File:** palantir_ontology_1.md
- **Current:** Lists 6 constraint types (enum, range, regex, rid, uuid, uniqueness)
- **Add:** Nested (constraints on array elements), StructElement (constraints on struct fields)
- **Source:** https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints

## Priority: MEDIUM (Completeness Gaps)

### MD-1: Missing ObjectType "ID" Field
- ObjectType has TWO identifiers: "ID" (lowercase+dashes) and "apiName" (PascalCase)

### MD-2: PrimaryKey is Array
- Platform supports multi-property PKs natively (array of PropertyApiName)
- Concatenation is best practice but not the only option

### MD-3: Missing Value Types Concept
- Semantic wrappers for baseTypes with constraints (e.g., "EmailAddress" = String + regex)
- Significant feature omitted from docs

### MD-4: Interface Link Constraints Use ONE/MANY
- Simpler than LinkType's 4-way cardinality (1:1/1:N/N:1/M:N)
- Required vs optional flag on constraints

### MD-5: Missing Self-Referential Links
- LinkType can connect ObjectType to itself (e.g., Employee → Manager)

### MD-6: Cross-Ontology Links Not Supported
- Important constraint for multi-ontology architectures

### MD-7: VECTOR Not Valid Action Parameter
- VECTOR is Property baseType only, not Action parameter type
- Remove from ActionType parameter list in palantir_ontology_3.md

### MD-8: Scale Limits Table Missing
- ActionType: 10K objects/submission, 50 OTs/submission, 32KB-3MB edit size
- Function: 60s runtime, 128MB-5GB memory, 30s CPU (TS v1)
- Add to palantir_ontology_3.md and palantir_ontology_7.md

### MD-9: 8-Phase Decomposition Attribution
- palantir_ontology_9.md must explicitly state: "Community-derived methodology"
- NOT from official Palantir documentation
- Individual component concepts ARE Palantir knowledge

### MD-10: Array Restrictions
- Array properties cannot contain null elements
- Cannot use Vector or TimeSeries as inner types

## Priority: LOW (Editorial / Unverified)

### LO-1: "aliases" Field Unverified (ObjectType)
### LO-2: Vector Max 2048 Dims — Unverified (no official source)
### LO-3: Render Hint Dependency Chain — Unverified (searchable → sortable etc.)
### LO-4: apiName Case Contradiction (Palantir's own docs inconsistent: PascalCase vs camelCase)
### LO-5: SharedProperty "Name" vs "apiName" Discrepancy

---

## Anti-Pattern Verification Summary

| Status | Count | Details |
|--------|-------|---------|
| CONFIRMED by official docs | 12 | OT-2, OT-3, P-1, P-2, P-4, LT-4 cardinality change, ACT-1, ACT-2, FUNC-1, FUNC-2, FUNC-3, CONS-1 |
| PLAUSIBLE (doc signals) | 8 | OT-1, SP-1, SP-2, LT-1, LT-2, LT-3, IF-2, IF-3 |
| COMMUNITY-REPORTED | 1 | IF-2 (non-unique PKs across implementors) |
| Palantir has NO formal anti-pattern guide | — | Label all as "derived from documentation signals" |

---

## Verification Source Summary

| Verifier | Components | Pages Fetched | Key Findings |
|----------|-----------|---------------|--------------|
| verifier-static | ObjectType, Property, SharedProperty | 23 pages | 1 CRITICAL, 4 HIGH, 5 MEDIUM |
| verifier-relational | LinkType, Interface | 14 pages | 3 WRONG, 9 MISSING |
| verifier-behavioral | ActionType, Function, Rule_Constraint, Decomposition | 14 pages | 7 corrections, decomposition = community-derived |
| **Total** | **8 components** | **51 pages** | **2 CRITICAL, 8 HIGH, 10 MEDIUM, 5 LOW** |
