# Secondary Components Reference — Ontology Framework

> **Purpose:** Summary-level bridge reference for T-4 Framework Integration Architecture.
> Consolidates ontology_4 (Data Pipeline), ontology_5 (Collection & Storage), ontology_6 (Application & API), ontology_8 (Security & Governance).
> **Consumer:** Opus 4.6 agents during architecture/design phases.
> **Scope:** What adapts to local CLI, what stays Foundry-only, and integration implications.

---

## 1. Data Pipeline Layer (from ontology_4)

### Key concepts for local adaptation

**Dataset** — The atomic unit of data in Foundry. A versioned wrapper around files with schema, permissions, and transaction history. Transaction types: SNAPSHOT (full replace), APPEND (add-only), UPDATE (modify existing), DELETE (retention compliance).

**Pipeline** — Directed graph of transforms that reads source data and produces clean output datasets. Two types: visual Pipeline Builder (no-code) and Code Repository (Python/SQL/Java). Processing modes: BATCH, INCREMENTAL, STREAMING.

**Transform** — A single computation unit within a pipeline. Takes input datasets, applies logic (filter, join, aggregate), produces output datasets. Engine selection: LIGHTWEIGHT (Polars/pandas, <10M rows) vs SPARK (distributed, billions of rows). Incremental transforms process only new/changed data.

**OntologySync** — The bridge from tabular datasets to Ontology objects. Steps: changelog computation, merge with user edits, indexing, hydration to search nodes. Link mapping types: FOREIGN_KEY (1:1, M:1), JOIN_TABLE (M:M, supports edits), OBJECT_BACKED (M:1 with metadata).

**Multi-Dataset Objects (MDO)** — Single ObjectType backed by multiple datasets joined on primary key. LEFT JOIN from primary to additional datasets. Limit: avoid 5+ additional datasets.

### What to adapt vs what to skip

**ADAPT for local framework:**
- Dataset concept as versioned data files (YAML/JSON on disk with transaction metadata)
- Schema definition model (field name, type, nullable) — directly reusable in YAML schemas
- Transaction types as file operation semantics (SNAPSHOT = overwrite, APPEND = add)
- Primary key uniqueness and determinism rules
- Transform concept as composable data processing steps (Python scripts, jq transforms)
- OntologySync's property mapping pattern (source column -> target property)
- Link mapping types (FOREIGN_KEY as reference field, JOIN_TABLE as mapping file)
- Validation rules (DS-E001 through OS-E004) — adapt as schema validation checks
- Anti-patterns as framework design constraints

**SKIP (Foundry-only):**
- RID format (`ri.foundry.main.dataset.<uuid>`) — replace with local path-based IDs
- Spark/Flink execution engines — replace with local Python/jq processing
- Pipeline Builder visual UI — not applicable to CLI
- Streaming pipelines (Kafka, Kinesis, Event Hubs) — no local equivalent needed
- Data Connection sources (JDBC, S3, GCS, SFTP) — replace with local file reads
- Object Data Funnel microservice — replace with local sync script
- Hydration to search nodes — replace with file-based index
- Cron scheduling — replace with hook-based triggers or manual invocation
- Resource configuration (CPU cores, GPU) — not applicable

---

## 2. Collection & Storage (from ontology_5)

### Object Storage model

**ObjectSet** — An immutable, unordered, single-typed collection of objects. Lazy-evaluated: operations (filter, union, intersect, subtract, searchAround/pivotTo) build query definitions without execution until terminal operations (.all(), .fetchPage(), .count()). Key constraint: filters only work on properties with Searchable render hint.

**Query operations:**
- Filtering: comparison ($eq, $ne, $gt, $gte, $lt, $lte), string (exactMatch, phrase, phrasePrefix, matchAnyToken, fuzzy), boolean (isTrue, isFalse), geo (withinDistanceOf, withinPolygon), null (.hasProperty, .is_null)
- Set operations: union, intersect, subtract
- Traversal: searchAround/pivotTo (max 3 hops, 10M object limit on OSv2)
- Aggregation: count, average, max, min, sum, cardinality. GroupBy: topValues, exactValues, byRanges, byFixedWidth, byYear/Month/Week/Day. Max 10,000 buckets.
- 3D aggregation: multi-dimension groupBy + multi-metric select (pivot-table-style)

**TimeSeries** — Property type for temporal measurements. Each point = (timestamp, value). Backed by Time Series Sync on datasets. Query: getFirstPoint, getLastPoint, streamPoints with time range. Aggregations: min, max, mean, sum, stddev over granularity windows. FoundryTS library for advanced operations (interpolate, rolling_aggregate).

**MediaSet** — Collection of media files (audio, documents, images, video) with schema type. MediaReference (recommended) links objects to media items. Supports OCR, transcription, format conversion. Hard limits: 200MB attachments, 20MB in Functions, 10K files per transaction.

### Local adaptation

**ObjectSet -> Local query interface:**
- Adapt filter/sort/paginate semantics for YAML/JSON files on disk
- Implement as Python functions that read object files, apply filters, return results
- searchAround -> follow reference fields in YAML objects (resolve foreign keys)
- Aggregation -> Python aggregation over in-memory collections or SQLite

**Storage alternatives:**
| Foundry Component | Local Alternative | Notes |
|---|---|---|
| Object Storage V2 | YAML files in `objects/{type}/{pk}.yaml` | One file per object instance |
| ObjectSet queries | Python filter functions + SQLite FTS | For search and aggregation |
| TimeSeries | CSV/Parquet files with timestamp index | Or SQLite time-series table |
| MediaSet | Directory-based storage `media/{type}/{id}/` | With metadata sidecar YAML |
| searchAround | Reference resolution via foreign key fields | Max depth configurable |
| Aggregation | Python collections + pandas/polars | Or SQLite aggregate queries |

**Skip (Foundry-only):**
- Temporary ObjectSets with 1-hour expiry and RID format
- Object Storage V1 (Phonograph) specifics
- Real-time subscriptions (WebSocket-based)
- OSDK TypeScript/Python SDK client setup
- FoundryTS library (cloud-only caching database)
- MediaSet OCR/transcription services — replace with local tools if needed

[GAP: No local full-text search strategy defined. Need to decide between SQLite FTS5, simple substring match, or external tool like ripgrep for object content search.]

---

## 3. Application & API Layer (from ontology_6)

### OSDK and API patterns

**Five application components in Foundry:**

1. **Workshop** — No-code operational app builder. Widget-based (Object Table, Charts, Filters, Action Buttons, AI widgets). Variables manage state. Module-based architecture with pages and overlays. Mobile support. State saving. Validation: max 50 columns per table, 200K export limit.

2. **OSDK** — Type-safe SDK generated from Ontology schema. TypeScript (NPM), Python (pip), Java (Maven), OpenAPI for others. Core pattern: `client(ObjectType).where({...}).fetchPage()`. Actions for all writes (objects are immutable). Subscriptions for real-time updates (TS only). v2 syntax uses object-based filters and aggregation.

3. **Slate** — Legacy custom HTML/CSS/JS app builder using Blueprint framework and Handlebars. Full pixel-control. Postgres/SQL direct queries (legacy). Phonograph writeback (deprecated). Still supported but Workshop preferred for new projects.

4. **REST API v2** — HTTP endpoints with OAuth 2.0. Base: `https://{hostname}/api/v2/ontologies/{name}/...`. Operations: GET objects, POST search, POST aggregate, GET links, POST actions/apply. Rate limits: 5000 req/min per user, 800 concurrent for service accounts. Max page size: 2000.

5. **Automate** — Condition-effect workflow automation. Conditions: time-based (cron), object-set changes (added/removed/modified), threshold. Effects: Actions execution, notifications (email/platform), fallback handlers. Limits: 100K objects scheduled, 10K real-time.

**Cross-cutting patterns:**
- All five components depend on Ontology definitions (ObjectType, Property, LinkType, ActionType)
- Authentication: Workshop/Slate use session-based; OSDK/REST use OAuth 2.0; Automate uses owner permissions
- All writes go through ActionTypes — objects are immutable outside Actions

**Palantir MCP (2025-2026):**
- MCP server for IDE integration (view/manage SDK from IDE)
- Ontology MCP: external AI agents query objects and execute Actions via MCP tools

### Local adaptation

**CLI Read/Write patterns (replacing Workshop/OSDK/REST):**

| Foundry Pattern | Local CLI Equivalent |
|---|---|
| `client(Type).where({...}).fetchPage()` | `python query.py --type Student --filter "grade_level=10"` or hook-based file reads |
| `client(Action).applyAction({...})` | Write operation with validation rules, audit log |
| Workshop dashboard | ASCII status visualization in terminal / orchestration-plan.md |
| REST API search endpoint | Python function: `search_objects(type, filters, page_size)` |
| Automate conditions | Hook triggers (on-file-change, on-schedule via cron) |
| OSDK subscriptions | File watcher (inotify) or polling |
| Pagination (pageToken) | Offset-based iteration over sorted file lists |

**Agent file access patterns (replacing OSDK):**
- Agent reads object files directly via Read tool
- Agent writes through validated write operations (equivalent to Actions)
- Hook enforcement replaces server-side authorization
- Tool restrictions (disallowedTools) replace OAuth scopes

**What to adapt:**
- ObjectSet query semantics as a local Python query library
- Action pattern: all writes through validated, audited operations
- Pagination pattern for large object collections
- Variable/state management concepts for agent context
- Condition-effect automation pattern for hooks

**Skip (Foundry-only):**
- Workshop widget system, module layout, mobile support
- Slate HTML/CSS/JS runtime, Blueprint framework, Handlebars
- OAuth 2.0 flows (authorization code, client credentials, refresh)
- REST API rate limiting infrastructure
- Real-time subscriptions WebSocket protocol
- OSDK code generation from Ontology schema
- Automate notification system (email, platform notifications)

[GAP: No local equivalent for OSDK type-safe code generation. Need to decide if we generate Python dataclasses or TypedDict from YAML schema definitions.]

---

## 4. Security & Governance (from ontology_8)

### Permission model

**Marking-Based Access Control:**
- MANDATORY_MARKING: user must be a member to access marked data. Additive (AND logic).
- CLASSIFICATION_MARKING: hierarchical levels (UNCLASSIFIED < CUI < CONFIDENTIAL < SECRET < TOP_SECRET). Higher clearance includes lower.
- Scoping: property-level (column hidden), row-level (object hidden), cell-level (combined).
- Enforcement: server-side at query time. Client never receives unauthorized data.
- Combined: row markings AND property markings evaluated together.

**RBAC Roles:**
- Viewer: read-only objects/schema/links. No action execution.
- Editor: read + write via Actions. Execute permitted actions/functions.
- Owner: full CRUD + schema modification + permission management.
- Discoverer: see existence in search results but not property values.

**Restricted Views:**
- Filtered views of ObjectTypes limiting visible objects by criteria.
- Server-side query rewriting: filter added to all queries transparently.
- Composable: multiple views AND-ed together.
- Recommended for business segmentation; markings for security.

**Granular Policies (Object & Property Security Policies):**
- Object Security Policy: row-level. 4 operators (Equal, Intersects, Subset_of, Superset_of).
- Property Security Policy: column-level. All 8 operators (adds LT/GT/LTE/GTE).
- Cell-level: combination of object + property policies. Failed property policy -> null value.
- User attributes: organization, group membership (UUIDs, not names), user ID.
- Weight limits: max 10 comparisons, 10,000 total weight. Collection comparisons = 1000 weight each.

**Ontology Proposals & Governance:**
- Git-like branching for schema changes. Branch -> Propose -> Review -> Rebase -> Merge.
- Per-task review: each resource change reviewed independently.
- Conflict resolution: auto for non-overlapping, manual rebase for conflicts.
- Breaking changes require explicit migration approval.

**Audit Trail:**
- Action audit: every execution logged (who, what, when, result, context).
- Schema audit: every Ontology change tracked (who, when, what, why).
- Access logging: object queries, property access, link traversals, exports.
- Compliance: GDPR (PII markings, DSAR, consent tracking, 3yr retention), HIPAA (PHI markings, minimum necessary, 6yr), SOX (segregation of duties, immutable audit, 7yr).

### Local adaptation

**File ownership model (replacing markings + RBAC):**

| Foundry Mechanism | Local Equivalent | Implementation |
|---|---|---|
| Mandatory markings | File/directory permissions | Unix file permissions + ownership rules in CLAUDE.md |
| RBAC roles | Agent role restrictions | `disallowedTools` per agent type (already in agents/*.md) |
| Restricted views | Directory-scoped access | Agent assigned specific object directories |
| Object Security Policy | Pre-read hook validation | Hook checks agent identity before file read |
| Property Security Policy | Field-level redaction | Read wrapper that filters sensitive fields |
| Audit trail | Git history + log files | All writes committed to git; hook logs in `.agent/logs/` |
| Proposals | Git branches + PR review | Schema changes via branch -> PR -> review -> merge |
| CBAC hierarchy | Not needed locally | Single-user system; skip classification hierarchy |

**Agent tool restrictions (replacing OAuth scopes):**
- `disallowedTools: [TaskCreate, TaskUpdate]` for teammates (already implemented)
- Read access unrestricted (matching Foundry's viewer role)
- Write access through validated operations only (matching Action pattern)
- Hook enforcement at tool execution time (on-pre-tool hooks)

**Hook enforcement (replacing server-side authorization):**
- `on-subagent-start.sh`: inject context (replacing token-based auth)
- `on-task-completed.sh`: verify L1/L2 existence (replacing audit checks)
- `on-tool-failure.sh`: log failures (replacing error audit)
- Custom hooks for file access validation (to be designed)

**What to adapt:**
- File ownership model from CLAUDE.md section 5
- Audit via git commits (who changed what, when, why)
- Schema governance via git branch + PR workflow
- Agent role-based tool restrictions
- Validation rules as pre-write checks

**Skip (Foundry-only):**
- Multi-tenant Organizations isolation
- OAuth 2.0 token management and service accounts
- mTLS and service mesh security
- Network policies (Kubernetes)
- Rate limiting infrastructure
- CBAC classification hierarchy (single-user system)
- Compliance-specific templates (GDPR/HIPAA/SOX) — not applicable to local dev tool

[GAP: No local equivalent for cell-level security (object + property policy combination). Need to decide if field-level redaction is needed for agent access, or if tool restrictions suffice.]

[GAP: No audit trail strategy for agent object reads. Git tracks writes, but reads are unlogged. Decide if read logging is needed.]

---

## 5. Cross-Cutting Patterns

### Pattern 1: Immutable Objects + Action-Based Writes

Foundry enforces that all object modifications go through ActionTypes. Objects are immutable snapshots; changes create new versions. This pattern appears in:
- ontology_4: Dataset transactions (SNAPSHOT/APPEND/UPDATE)
- ontology_5: ObjectSet immutability
- ontology_6: OSDK `.applyAction()` as sole write path
- ontology_8: Audit logging of every Action execution

**Local adaptation:** All object file writes must go through a validated write function that: (1) validates schema, (2) checks permissions, (3) logs the operation, (4) commits to git. Direct file edits by agents should be discouraged except through the write path.

### Pattern 2: Primary Key Determinism

Stressed across all four documents. Non-deterministic PKs (auto-increment, random UUID) cause:
- OntologySync failures (ontology_4)
- Edit loss and link breaks (ontology_4, OntologySync)
- Duplicate objects on rebuild
- Broken foreign key references (ontology_5, searchAround)

**Local adaptation:** Object file naming convention must use deterministic primary keys. Example: `objects/Student/STU-2024-001.yaml`. PKs derived from business keys, not generated IDs.

### Pattern 3: Schema-Driven Everything

All components derive behavior from the Ontology schema:
- ontology_4: Dataset schema defines column types
- ontology_5: ObjectSet filter operators depend on property type and Searchable hint
- ontology_6: OSDK generates type-safe code from schema; REST validates against schema
- ontology_8: Security policies reference schema columns; proposals govern schema changes

**Local adaptation:** A single schema definition (YAML) should drive: validation rules, query capabilities, type checking, security policies, and documentation. Schema-as-code pattern.

### Pattern 4: Layered Security

Foundry applies security in layers, each independently evaluated:
1. Authentication (OAuth/session)
2. Organization isolation
3. RBAC roles (feature-level)
4. Markings (data-level, row + column)
5. Restricted views (business segmentation)
6. Granular policies (cell-level)
7. Action submission criteria (operation-level)

**Local adaptation:** Layer model for agent access:
1. Agent identity (role from spawn directive)
2. Tool restrictions (disallowedTools)
3. File ownership (directory-level)
4. Hook enforcement (operation-level)
5. Write validation (schema + business rules)

### Pattern 5: Query + Traversal + Aggregation Triad

All access layers implement the same three operations:
- Query: filter objects by property conditions
- Traverse: follow links to related objects (searchAround/pivotTo)
- Aggregate: compute statistics over object collections

This triad appears in ObjectSet (ontology_5), OSDK (ontology_6), REST API (ontology_6), and is constrained by security policies (ontology_8).

**Local adaptation:** The local query library must implement all three: filter objects in a directory, resolve references to linked objects, compute aggregations over collections.

### Pattern 6: Sync Pipeline (Data -> Ontology)

The flow: raw data -> transform/clean -> dataset -> OntologySync -> indexed objects. This is the single path from external data to queryable Ontology objects. Property mapping (source column -> target property) is explicit.

**Local adaptation:** Import pipeline: raw data (CSV/JSON) -> transform script -> validated YAML objects in `objects/{type}/` directory. Mapping configuration in a sync manifest file.

---

## 6. Integration Architecture Implications

### For T-4 Framework Design

**6.1 Storage Layer Design**

The framework needs a file-based storage layer that mirrors Foundry's object storage semantics:
- One directory per ObjectType: `objects/{typeApiName}/`
- One file per object instance: `{primaryKey}.yaml`
- Schema definition file per type: `schemas/{typeApiName}.schema.yaml`
- Link resolution via foreign key fields within object files
- Optional: SQLite index for search/aggregation performance

**6.2 Query Interface Design**

A Python query library that implements ObjectSet-like semantics:
- `query(type, filters, order_by, page_size, page_offset)` -> list of objects
- `traverse(object, link_type)` -> list of linked objects (max depth configurable)
- `aggregate(type, filters, metrics, group_by)` -> aggregation results
- Filter operators: eq, ne, gt, gte, lt, lte, contains, is_null, prefix
- All operations read from file system; no server required

**6.3 Write Path Design**

Action-based write pattern:
- Define ActionTypes in `actions/{actionApiName}.yaml` with parameter schema and validation rules
- Write function: validate parameters -> check permissions -> apply edits -> log -> git commit
- No direct object file modification by agents outside the write path
- Audit log: `.agent/logs/action_audit.log` (who, what, when, result)

**6.4 Schema Governance Design**

Git-based proposal workflow:
- Schema changes via feature branches
- PR review for breaking changes (property removal, type changes)
- Migration scripts for data transformations
- Schema versioning in YAML front matter

**6.5 Security Design**

Layered access control adapted from Foundry's model:
- Agent roles map to RBAC (researcher=Viewer, implementer=Editor, integrator=Owner-scoped)
- disallowedTools as scope restriction
- File ownership rules from CLAUDE.md section 5 as data-level access
- Hook enforcement as runtime authorization
- Git history as audit trail

**6.6 Data Pipeline Design**

Local transform pipeline:
- Import: raw file -> Python transform -> validated object YAML
- Sync: Object YAML -> optional SQLite index for queries
- Incremental: process only new/modified files (based on git diff or file mtime)
- Batch: full re-process of all source files

**6.7 Identified Gaps for T-4 Resolution**

| ID | Gap | Priority | Notes |
|---|---|---|---|
| GAP-S1 | Full-text search strategy for object contents | HIGH | SQLite FTS5 vs ripgrep vs custom |
| GAP-S2 | Type-safe code generation from YAML schemas | MEDIUM | Python dataclasses / TypedDict generation |
| GAP-S3 | Cell-level security (field redaction) for agents | LOW | May not be needed if tool restrictions suffice |
| GAP-S4 | Read audit logging for agents | LOW | Git tracks writes; reads currently unlogged |
| GAP-S5 | Real-time change notification (file watcher) | LOW | Needed only if agent coordination requires it |
| GAP-S6 | Aggregation engine for large object collections | MEDIUM | In-memory Python vs SQLite vs skip |
| GAP-S7 | Multi-dataset object (MDO) local equivalent | LOW | Pre-join in transform or reference resolution |
| GAP-S8 | TimeSeries storage format for temporal data | LOW | Only if time-series use cases emerge |
