# LinkType + Interface Reference -- Agent Teams Bridge Focus

**Version**: 1.0.0 | **Date**: 2026-02-08 | **Consumer**: Opus 4.6 Agent Teams Bridge
**Source**: `palantir_ontology_2.md` (LinkType & Interface Reference, 1477 lines)

---

## 1. LinkType Fundamentals

A **LinkType** is the schema definition of a relationship between two ObjectTypes. A **Link** is a single instance of that relationship between two objects in the same Ontology. This maps to relational database concepts: LinkType defines the join logic, Link represents the joined rows.

Key properties of every LinkType:

| Property | Type | Description |
|----------|------|-------------|
| `apiName` | string (`^[a-z][a-zA-Z0-9]*$`, 1-100 chars) | Programmatic name for code references |
| `displayName` | string (max 256) | Human-readable label |
| `sourceObjectType` | string | API name of source ObjectType |
| `targetObjectType` | string | API name of target ObjectType |
| `sourceApiName` | string | Traversal name from source side |
| `targetApiName` | string | Traversal name from target side |
| `cardinality` | enum | ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY |
| `backingMechanism` | object | FOREIGN_KEY, JOIN_TABLE, or OBJECT_BACKED |

Analogies:
- Database: JOIN definition between tables
- ORM: Foreign key relationship
- Graph: Edge type in a property graph

---

## 2. Cardinality Decision Matrix

| Cardinality | Definition | FK Location | Backing | Agent Teams Example |
|-------------|-----------|-------------|---------|---------------------|
| ONE_TO_ONE | One A links to exactly one B | Either side (configurable) | FOREIGN_KEY | Phase -> GateRecord (each phase has exactly one gate record) |
| ONE_TO_MANY | One A links to many B | Target side (the "many" side holds the FK) | FOREIGN_KEY | Session -> Phase (one session contains many phases); Phase -> Task (one phase contains many tasks) |
| MANY_TO_ONE | Many A link to one B | Source side (the "many" side holds the FK) | FOREIGN_KEY | Inverse of ONE_TO_MANY -- Task -> Phase from the task's perspective |
| MANY_TO_MANY | Many A link to many B and vice versa | Neither -- uses join table or backing object | JOIN_TABLE or OBJECT_BACKED | Task <-> Teammate (many tasks assigned to many teammates, with DIA workflow metadata); Module <-> Module (self-referential dependency graph); Phase <-> Phase (self-referential precedence DAG) |

Important platform behaviors:
- ONE_TO_ONE cardinality is **not enforced** at the platform level -- it serves as a semantic indicator only.
- ONE_TO_MANY and MANY_TO_ONE are inverse perspectives of the same relationship; choose based on which side is the "owner."
- MANY_TO_MANY is the only cardinality supporting direct link writeback through Create/Delete Link action rules.

Cardinality change rules (post-creation):
- Changes are allowed but trigger Object Storage V1 unregister/reregister.
- Links become unavailable during reindex.
- Writeback history is deleted for writeback-enabled links.
- Future writeback dataset builds will fail.
- High-risk changes: changing cardinality, changing FK property, changing M:N backing datasource, deleting link type.

---

## 3. Backing Mechanism Selection

### FOREIGN_KEY

Use for ONE_TO_ONE, ONE_TO_MANY, and MANY_TO_ONE relationships where no properties are needed on the relationship itself.

Configuration:
- `foreignKeyObjectType`: which ObjectType holds the FK column
- `foreignKeyProperty`: the property name on the FK-holding side
- `primaryKeyObjectType`: which ObjectType is referenced

Agent Teams examples:
- **Session -> Phase**: Phase holds `sessionId` as FK referencing Session's primary key.
- **Phase -> Task**: Task holds `phaseId` as FK referencing Phase's primary key.
- **Task -> File**: File holds `taskId` as FK referencing Task's primary key.
- **Phase -> GateRecord**: GateRecord holds `phaseId` as FK referencing Phase's primary key.

### JOIN_TABLE

Use for MANY_TO_MANY relationships where the relationship has no properties beyond the two connected keys.

Configuration:
- `datasetRid`: the join table dataset resource identifier
- `sourceColumn`: column matching source ObjectType primary key
- `targetColumn`: column matching target ObjectType primary key

Constraints:
- Each column can only map to one primary key.
- Can auto-generate via "Generate join table" option in Ontology Manager.
- Supports full writeback (Create/Delete Link actions).

Agent Teams examples:
- **Module <-> Module** (dependency graph): Join table `module_dependency_links` with `dependent_module_id` and `dependency_module_id`.
- **Phase <-> Phase** (precedence DAG): Join table `phase_precedence_links` with `predecessor_phase_id` and `successor_phase_id`.

### OBJECT_BACKED

Use for MANY_TO_MANY relationships where the relationship itself carries meaningful properties (dates, scores, status, context). This is the most important backing mechanism for the Agent Teams bridge.

Architecture pattern:
```
ObjectA <-[M:1]-> BackingObject <-[M:1]-> ObjectB
```

The backing object is a full ObjectType with its own primary key and properties. It maintains M:1 links to both sides.

When to use:
- Link needs properties (dates, scores, status)
- Relationship has its own identity (e.g., a DIA workflow instance)
- Need restricted views on links
- Audit trail required for link changes

Agent Teams example -- **DIAWorkflow** (Task <-> Teammate):

This is the critical OBJECT_BACKED link for Agent Teams. The DIAWorkflow object captures the full DIA protocol exchange between a task and a teammate:

```
Task <-[M:1]-> DIAWorkflow <-[M:1]-> Teammate
```

DIAWorkflow properties:
- `workflowId` (PK): Unique workflow instance ID
- `taskId` (FK): Reference to Task
- `teammateId` (FK): Reference to Teammate
- `impactAnalysisStatus`: NOT_SUBMITTED | SUBMITTED | VERIFIED | REJECTED
- `challengeStatus`: NONE | CHALLENGED | DEFENDED | FAILED
- `planStatus`: NONE | SUBMITTED | APPROVED | REJECTED
- `rejectionCount`: Integer (max 3 before ABORT)
- `gcVersionAtAssignment`: GC version when task was assigned
- `assignedAt`: Timestamp
- `verifiedAt`: Timestamp
- `completedAt`: Timestamp

Creation steps:
1. Create ObjectTypes on both sides (Task, Teammate)
2. Create backing ObjectType (DIAWorkflow) with all link properties
3. Create M:1 LinkType from DIAWorkflow to Task
4. Create M:1 LinkType from DIAWorkflow to Teammate
5. In Ontology Manager, configure as object-backed

### Decision summary

```
Need to model a relationship?
  |
  +-- How many on each side?
       |
       +-- 1:1  -> FOREIGN_KEY (FK on either side)
       +-- 1:N  -> FOREIGN_KEY (FK on target/many side)
       +-- N:1  -> FOREIGN_KEY (FK on source/many side)
       +-- M:N  -> Does link need properties?
                    |
                    +-- Yes -> OBJECT_BACKED (intermediary ObjectType)
                    +-- No  -> JOIN_TABLE (dataset with PK pairs)
```

---

## 4. Search Around (Graph Traversal)

Search Around enables graph traversal through linked objects at the ObjectSet level. It is the primary mechanism for navigating the Agent Teams entity graph.

### How it works

Each LinkType generates typed traversal methods based on its API names:
- `SingleLink`: For the "one" side -- use `.get()` or `.getAsync()`
- `MultiLink`: For the "many" side -- use `.all()` or `.allAsync()`

Bidirectional traversal is automatic when both `sourceApiName` and `targetApiName` are configured.

### Performance limits

| Constraint | Value |
|-----------|-------|
| Max searchAround operations per function | 3 |
| Scale threshold for materialization | 50,000 objects |
| Recommendation above threshold | Use join materializations |

### Agent Teams traversal examples

**Get all tasks in a phase:**
```typescript
const tasks = phase.tasks.all();
```

**Get the phase that contains a task:**
```typescript
const phase = task.containingPhase.get();
```

**Get all teammates assigned to a task (via DIAWorkflow):**
```typescript
const workflows = task.diaWorkflows.all();
// Each workflow links to a teammate
for (const wf of workflows) {
  const teammate = wf.assignedTeammate.get();
}
```

**Get all tasks assigned to a teammate:**
```typescript
const workflows = teammate.diaWorkflows.all();
for (const wf of workflows) {
  const task = wf.associatedTask.get();
}
```

**Multi-hop: Get all files owned by tasks in a specific phase:**
```typescript
// Phase -> Tasks -> Files (2 hops)
const tasks = phase.tasks.all();
// Then for each task:
const files = task.ownedFiles.all();
```

**Self-referential: Get all prerequisite phases:**
```typescript
const prereqPhases = phase.predecessorPhases.all();
```

**Self-referential: Get all modules that depend on a module:**
```typescript
const dependents = module.dependentModules.all();
```

Important: With the 3-hop limit, you can traverse Session -> Phase -> Task -> File in a single chain, but adding Teammate via DIAWorkflow would require a separate query.

---

## 5. Interface Patterns

An **Interface** is an Ontology type describing the shape of ObjectTypes and their capabilities. Unlike OOP interfaces that define method signatures, Palantir Interfaces define **shared properties** and **link type constraints** for data shape abstraction.

### Key characteristics

| Aspect | Interface | ObjectType |
|--------|-----------|------------|
| Nature | Abstract | Concrete |
| Schema source | Only shared properties | Shared or local properties |
| Data backing | Not backed by datasets | Backed by datasets |
| Instantiation | Cannot be instantiated directly | Can be instantiated as objects |
| Visual indicator | Dashed-line icons | Solid line icons |

### Shared properties

Interfaces define shared properties that all implementing ObjectTypes must map. Mapping can be automatic (when names match) or manual (when names differ).

When accessed as the concrete type, local property API names are used. When accessed as the interface type, shared property API names are used.

### Link type constraints

Interfaces can define link constraints that all implementing ObjectTypes must satisfy:
- Target can be a specific ObjectType (concrete) or another Interface (polymorphic)
- Cardinality: ONE or MANY
- Required: whether implementing objects must have this link

Use Interface target when both sides of the relationship are abstract and maximum flexibility is needed. Use ObjectType target when one side must be concrete.

### Multiple inheritance

Interfaces can extend any number of other interfaces, inheriting all shared properties and link type constraints. This enables composition of capability interfaces.

Example: `DIACompliant` extends `Identifiable` and `Trackable`, inheriting properties from both.

### Agent Teams Interface candidates

The Agent Teams bridge benefits from four interfaces:

1. **Identifiable** -- shared identity across all Agent Teams entities
2. **Trackable** -- shared lifecycle tracking (timestamps, status)
3. **ContextAware** -- shared GC version tracking for DIA compliance
4. **DIACompliant** -- composite interface for entities that participate in the DIA protocol

### Platform support (as of February 2026)

| Platform | Interface Support |
|----------|------------------|
| Ontology Manager | Full (define, edit, implement) |
| Functions (TypeScript v2) | Full |
| Actions | Create/modify/delete objects via interfaces; cannot reference interface link type constraints directly |
| Object Set Service | Search and sort; aggregating and interface link types in development |
| OSDK TypeScript | Use as API layer; interface link types and aggregations not yet supported |
| Workshop | Not supported |
| OSDK Java/Python | In development |

---

## 6. Agent Teams LinkType Mapping

### 6.1 Session -> Phase (Containment)

| Field | Value |
|-------|-------|
| apiName | `sessionToPhases` |
| displayName | Session Phases |
| sourceObjectType | `session` |
| targetObjectType | `phase` |
| cardinality | ONE_TO_MANY |
| backingMechanism | FOREIGN_KEY |
| FK ObjectType | `phase` |
| FK Property | `sessionId` |
| PK ObjectType | `session` |
| sourceApiName (from Session) | `phases` |
| targetApiName (from Phase) | `containingSession` |

Traversal: `session.phases.all()` / `phase.containingSession.get()`

Semantics: A session is the top-level orchestration container. It contains an ordered sequence of phases (1-9). Each phase belongs to exactly one session.

### 6.2 Phase -> Task (Containment)

| Field | Value |
|-------|-------|
| apiName | `phaseToTasks` |
| displayName | Phase Tasks |
| sourceObjectType | `phase` |
| targetObjectType | `task` |
| cardinality | ONE_TO_MANY |
| backingMechanism | FOREIGN_KEY |
| FK ObjectType | `task` |
| FK Property | `phaseId` |
| PK ObjectType | `phase` |
| sourceApiName (from Phase) | `tasks` |
| targetApiName (from Task) | `containingPhase` |

Traversal: `phase.tasks.all()` / `task.containingPhase.get()`

Semantics: Each phase contains one or more tasks. Tasks cannot move between phases once assigned.

### 6.3 Task <-> Teammate (DIA Workflow, Object-Backed)

| Field | Value |
|-------|-------|
| apiName | `taskTeammateAssignment` |
| displayName | Task-Teammate DIA Assignment |
| sourceObjectType | `task` |
| targetObjectType | `teammate` |
| cardinality | MANY_TO_MANY |
| backingMechanism | OBJECT_BACKED |
| backingObjectType | `diaWorkflow` |
| sourceLink | `taskWorkflows` (Task -> DIAWorkflow, M:1) |
| targetLink | `teammateWorkflows` (Teammate -> DIAWorkflow, M:1) |
| sourceApiName (from Task) | `assignedTeammates` |
| targetApiName (from Teammate) | `assignedTasks` |

This is the most complex and most important link in the Agent Teams bridge. The backing object (`DIAWorkflow`) captures:
- Impact analysis submission and verification state
- LDAP challenge/response state
- Plan submission and approval state
- Rejection count (max 3 before ABORT)
- GC version at assignment time
- Full timestamp audit trail

Traversal to link properties:
```typescript
// Get workflow details for a task-teammate pair
const workflows = task.taskWorkflows.all();
for (const wf of workflows) {
  console.log(wf.impactAnalysisStatus, wf.challengeStatus, wf.planStatus);
  const teammate = wf.assignedTeammate.get();
}
```

### 6.4 Phase -> GateRecord (One-to-One)

| Field | Value |
|-------|-------|
| apiName | `phaseGateRecord` |
| displayName | Phase Gate Record |
| sourceObjectType | `phase` |
| targetObjectType | `gateRecord` |
| cardinality | ONE_TO_ONE |
| backingMechanism | FOREIGN_KEY |
| FK ObjectType | `gateRecord` |
| FK Property | `phaseId` |
| PK ObjectType | `phase` |
| sourceApiName (from Phase) | `gateRecord` |
| targetApiName (from GateRecord) | `evaluatedPhase` |

Traversal: `phase.gateRecord.get()` / `gateRecord.evaluatedPhase.get()`

Note: ONE_TO_ONE is not enforced at the platform level. The bridge must enforce the constraint that each phase has at most one gate record through ActionType preconditions.

### 6.5 Task -> File (Ownership)

| Field | Value |
|-------|-------|
| apiName | `taskFileOwnership` |
| displayName | Task File Ownership |
| sourceObjectType | `task` |
| targetObjectType | `file` |
| cardinality | ONE_TO_MANY |
| backingMechanism | FOREIGN_KEY |
| FK ObjectType | `file` |
| FK Property | `ownerTaskId` |
| PK ObjectType | `task` |
| sourceApiName (from Task) | `ownedFiles` |
| targetApiName (from File) | `ownerTask` |

Traversal: `task.ownedFiles.all()` / `file.ownerTask.get()`

Semantics: Each file is owned by exactly one task. Two teammates must never edit the same file concurrently (enforced via task ownership). The integrator is the only role that can cross file ownership boundaries.

### 6.6 Module <-> Module (Self-Referential Dependency Graph)

| Field | Value |
|-------|-------|
| apiName | `moduleDependency` |
| displayName | Module Dependencies |
| sourceObjectType | `module` |
| targetObjectType | `module` |
| cardinality | MANY_TO_MANY |
| backingMechanism | JOIN_TABLE |
| datasetRid | `module_dependency_links` |
| sourceColumn | `dependent_module_id` |
| targetColumn | `dependency_module_id` |
| sourceApiName (from dependent) | `dependencies` |
| targetApiName (from dependency) | `dependentModules` |

Traversal: `module.dependencies.all()` / `module.dependentModules.all()`

Self-referential links require distinct, meaningful API names on each side. "dependencies" (what this module depends on) vs "dependentModules" (what depends on this module).

### 6.7 Phase <-> Phase (Self-Referential Precedence DAG)

| Field | Value |
|-------|-------|
| apiName | `phasePrecedence` |
| displayName | Phase Precedence |
| sourceObjectType | `phase` |
| targetObjectType | `phase` |
| cardinality | MANY_TO_MANY |
| backingMechanism | JOIN_TABLE |
| datasetRid | `phase_precedence_links` |
| sourceColumn | `successor_phase_id` |
| targetColumn | `predecessor_phase_id` |
| sourceApiName (from successor) | `predecessorPhases` |
| targetApiName (from predecessor) | `successorPhases` |

Traversal: `phase.predecessorPhases.all()` / `phase.successorPhases.all()`

This models the phase pipeline (Phases 1-9) where some phases must complete before others can begin. The Lead uses this to enforce gate sequencing.

---

## 7. Agent Teams Interface Mapping

### 7.1 Identifiable

| Field | Value |
|-------|-------|
| apiName | `identifiable` |
| displayName | Identifiable |
| description | Common identity interface for all Agent Teams entities |

Shared properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `entityId` | STRING | yes | Globally unique entity identifier |
| `entityType` | STRING | yes | Discriminator (e.g., "SESSION", "PHASE", "TASK", "TEAMMATE") |
| `displayName` | STRING | yes | Human-readable name |

Implementors:

| ObjectType | entityId mapping | entityType mapping | displayName mapping |
|------------|-----------------|-------------------|---------------------|
| Session | `sessionId` | STATIC_VALUE "SESSION" | `sessionName` |
| Phase | `phaseId` | STATIC_VALUE "PHASE" | `phaseName` |
| Task | `taskId` | STATIC_VALUE "TASK" | `taskTitle` |
| Teammate | `teammateId` | STATIC_VALUE "TEAMMATE" | `teammateName` |
| GateRecord | `gateRecordId` | STATIC_VALUE "GATE_RECORD" | `gateTitle` |
| File | `fileId` | STATIC_VALUE "FILE" | `filePath` |
| Module | `moduleId` | STATIC_VALUE "MODULE" | `moduleName` |
| DIAWorkflow | `workflowId` | STATIC_VALUE "DIA_WORKFLOW" | `workflowTitle` |

Polymorphic query example:
```typescript
// Find all Agent Teams entities matching a search term
const results = Objects.search()
  .identifiable()
  .filter(e => e.displayName.contains("architect"))
  .all();
```

Important: To avoid the IF_ANTI_001 anti-pattern (non-unique primary keys across implementors), use composite IDs with type prefixes: `SES-001`, `PH-003`, `TSK-042`, `TM-architect-1`.

### 7.2 Trackable

| Field | Value |
|-------|-------|
| apiName | `trackable` |
| displayName | Trackable |
| description | Lifecycle tracking interface for entities with status and timestamps |

Shared properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | STRING | yes | Current lifecycle status |
| `createdAt` | TIMESTAMP | yes | Creation timestamp |
| `updatedAt` | TIMESTAMP | yes | Last update timestamp |
| `completedAt` | TIMESTAMP | no | Completion timestamp (null if in progress) |

Implementors:

| ObjectType | status values | Notes |
|------------|--------------|-------|
| Session | ACTIVE, COMPLETED, ABORTED | Top-level lifecycle |
| Phase | PENDING, ACTIVE, COMPLETED, BLOCKED | Phase pipeline state |
| Task | CREATED, ASSIGNED, IN_PROGRESS, COMPLETED, FAILED | Task execution state |
| Teammate | SPAWNED, ACTIVE, IDLE, TERMINATED | Agent lifecycle |
| GateRecord | PENDING, APPROVED, ITERATE, ABORTED | Gate evaluation result |
| DIAWorkflow | INITIATED, IMPACT_SUBMITTED, IMPACT_VERIFIED, CHALLENGED, PLAN_SUBMITTED, PLAN_APPROVED, COMPLETED, REJECTED | Full DIA protocol state |

Polymorphic query example:
```typescript
// Find all active entities
const activeItems = Objects.search()
  .trackable()
  .filter(t => t.status.exactMatch("ACTIVE"))
  .all();
```

### 7.3 ContextAware

| Field | Value |
|-------|-------|
| apiName | `contextAware` |
| displayName | Context Aware |
| description | Interface for entities that track GC version for DIA context injection |

Shared properties:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `gcVersion` | INTEGER | yes | Global Context version number this entity was last synchronized with |
| `gcVersionReceivedAt` | TIMESTAMP | yes | When the GC version was received/acknowledged |
| `contextStatus` | STRING | yes | CURRENT, STALE, CONTEXT_LOST |

Implementors:

| ObjectType | Notes |
|------------|-------|
| Teammate | Tracks which GC version the teammate has acknowledged |
| DIAWorkflow | Tracks GC version at the time of assignment |
| Task | Tracks the GC version under which the task was defined |

This interface is central to DIA enforcement. The Lead can query all ContextAware entities to find those with stale context:
```typescript
// Find all entities with stale context
const staleEntities = Objects.search()
  .contextAware()
  .filter(c => c.contextStatus.exactMatch("STALE"))
  .all();
```

[GAP: The original Ontology docs do not describe a pattern for "version comparison" in interfaces. The bridge must implement GC version comparison logic in Functions rather than relying on property constraints alone, since the "current" GC version is dynamic.]

### 7.4 DIACompliant

| Field | Value |
|-------|-------|
| apiName | `diaCompliant` |
| displayName | DIA Compliant |
| description | Composite interface for entities that participate in the full DIA protocol |
| extendsInterfaces | `["identifiable", "trackable", "contextAware"]` |

Additional shared properties (beyond inherited):

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `impactAnalysisRequired` | BOOLEAN | yes | Whether this entity requires impact analysis before work |
| `diaTier` | STRING | yes | TIER_0, TIER_1, TIER_2, TIER_3 -- determines verification rigor |

Implementors:

| ObjectType | diaTier | impactAnalysisRequired |
|------------|---------|----------------------|
| DIAWorkflow | Inherited from Teammate role | true |
| Task | Based on phase | true |
| Teammate | Based on role (implementer=TIER_1, architect=TIER_2, researcher=TIER_3, devils-advocate=TIER_0) | Varies by tier |

Link type constraint:

| Constraint | Value |
|-----------|-------|
| apiName | `diaArtifacts` |
| targetType | INTERFACE: `identifiable` |
| cardinality | MANY |
| required | false |
| description | Links to any artifacts produced during DIA compliance (L1/L2/L3 files) |

Polymorphic query example:
```typescript
// Find all DIA-compliant entities that need re-injection
const needsReinjection = Objects.search()
  .diaCompliant()
  .filter(d => d.contextStatus.exactMatch("STALE"))
  .filter(d => d.impactAnalysisRequired.eq(true))
  .all();
```

---

## 8. Validation Rules (Bridge-Relevant)

### LinkType validation rules

| Rule ID | Name | Condition | Severity | Agent Teams Relevance |
|---------|------|-----------|----------|----------------------|
| LT001 | Valid API name format | `apiName` matches `^[a-z][a-zA-Z0-9]*$`, length 1-100 | ERROR | All 7 LinkTypes must follow camelCase naming |
| LT002 | Unique API names per ObjectType | No duplicate sourceApiName or targetApiName for same ObjectType | ERROR | Phase has multiple links (to Task, GateRecord, Session, and self-referential) -- each must have unique API names |
| LT003 | FK backing requires valid FK property | If FOREIGN_KEY backing, foreignKeyProperty must exist on specified ObjectType | ERROR | All FK-backed links (Session->Phase, Phase->Task, Phase->GateRecord, Task->File) must reference actual properties |
| LT004 | M:N requires join table or object backing | If cardinality=MANY_TO_MANY, backing must be JOIN_TABLE or OBJECT_BACKED | ERROR | Module<->Module and Phase<->Phase use JOIN_TABLE; Task<->Teammate uses OBJECT_BACKED |
| LT005 | Join table columns map to primary keys | sourceColumn and targetColumn must match PKs of respective ObjectTypes | ERROR | Join tables for Module dependency and Phase precedence must reference correct PKs |
| LT006 | Bidirectional names defined | Both sourceApiName and targetApiName should be defined for full traversal | WARNING | All 7 LinkTypes should define both names for complete graph navigation |
| LT007 | Meaningful API names | Avoid generic names like "Employee2" or "object" | WARNING | Use semantic names: `predecessorPhases`, `assignedTeammates`, `ownedFiles` |
| LT008 | Plural names for many-side | API name on "many" side should be plural | WARNING | `phases` (not `phase`), `tasks` (not `task`), `ownedFiles` (not `ownedFile`) |

### Interface validation rules

| Rule ID | Name | Condition | Severity | Agent Teams Relevance |
|---------|------|-----------|----------|----------------------|
| IF001 | Valid API name format | `apiName` matches `^[a-z][a-zA-Z0-9]*$`, length 1-100 | ERROR | `identifiable`, `trackable`, `contextAware`, `diaCompliant` |
| IF002 | At least one shared property | Interface must define at least one sharedProperty | WARNING | All 4 interfaces define multiple shared properties |
| IF003 | Required properties mapped | All required sharedProperties must be mapped in implementations | ERROR | All 8 ObjectTypes implementing Identifiable must map entityId, entityType, displayName |
| IF004 | Link constraints satisfied | Required linkTypeConstraints must be satisfied by concrete links | ERROR | DIACompliant's `diaArtifacts` link constraint must be satisfied by all implementors |
| IF005 | No circular extension | Interface cannot extend itself directly or indirectly | ERROR | DIACompliant extends Identifiable, Trackable, ContextAware -- no cycles |
| IF006 | Unique primary keys across implementors | Implementors should have globally unique PKs for polymorphic refs | WARNING | Use composite IDs: `SES-001`, `PH-003`, `TSK-042`, `TM-architect-1` |
| IF007 | Property type compatibility | Mapped local properties must be type-compatible with shared properties | ERROR | All property mappings must match types (e.g., entityId:STRING -> sessionId:STRING) |

---

## 9. Anti-Patterns to Avoid

### LinkType anti-patterns with Agent Teams warnings

| ID | Name | Agent Teams Warning |
|----|------|-------------------|
| LT_ANTI_001 | Isolated Objects | Every Agent Teams ObjectType must be linked. An isolated `Module` or `File` defeats graph traversal for impact analysis. |
| LT_ANTI_002 | Spiderweb Ontology | Phase has 5+ links (Session, Tasks, GateRecord, self-referential precedence, containment). Monitor complexity -- if Phase exceeds 10 links, consider splitting into sub-entities. |
| LT_ANTI_003 | Generic Link Names | Never use `link1` or `Phase2`. Use `predecessorPhases`, `successorPhases`, `assignedTeammates`. |
| LT_ANTI_004 | Missing Bidirectional Names | All Agent Teams links need bidirectional traversal. The Lead navigates Session->Phase->Task (forward) and Teammate->DIAWorkflow->Task (reverse). |
| LT_ANTI_005 | Singular Names on Many Side | Use `tasks` not `task`, `phases` not `phase`, `ownedFiles` not `ownedFile`. |
| LT_ANTI_006 | Cross-Ontology Links | All Agent Teams entities must reside in the same Ontology. Do not split Session/Phase/Task across Ontologies. |
| LT_ANTI_007 | FK Without Formal LinkType | Every FK property (sessionId on Phase, phaseId on Task, etc.) must have a corresponding formal LinkType. Without it, graph navigation is impossible. |
| LT_ANTI_008 | M:N Without Backing Dataset | Task<->Teammate without the DIAWorkflow backing object would lose all DIA protocol metadata. Module<->Module without a join table would prevent dependency writeback. |

### Interface anti-patterns with Agent Teams warnings

| ID | Name | Agent Teams Warning |
|----|------|-------------------|
| IF_ANTI_001 | Non-Unique PKs Across Implementors | If Session uses `001` and Task also uses `001`, polymorphic queries on Identifiable will collide. Use type-prefixed IDs. |
| IF_ANTI_002 | Breaking Interface Changes | Once Trackable is live, removing the `status` property would break all downstream Actions and Functions. Use optional properties for new additions; create new interface versions for breaking changes. |
| IF_ANTI_003 | Over-Abstraction | Do not create an interface for a single ObjectType. All four proposed interfaces have 2+ implementors. If only DIAWorkflow needed ContextAware, it would be better as local properties. |
| IF_ANTI_004 | Property Explosion | Keep interfaces focused. Identifiable has 3 properties, Trackable has 4, ContextAware has 3. If DIACompliant grows beyond 15 required properties, split into smaller composable interfaces. |

---

## 10. Forward-Compatibility Notes

### Impact on ActionType design

- **FK-backed links** (Session->Phase, Phase->Task, etc.) are managed by MODIFY_OBJECT rules that edit the FK property. No CREATE_LINK/DELETE_LINK rules apply.
- **JOIN_TABLE-backed links** (Module<->Module, Phase<->Phase) can use CREATE_LINK and DELETE_LINK action rules directly.
- **OBJECT_BACKED links** (Task<->Teammate via DIAWorkflow) require CREATE_OBJECT and MODIFY_OBJECT rules on the backing object, not link rules. The `assignTask` ActionType must create a DIAWorkflow object, not a link.
- **Interface-based actions**: Actions on interfaces (CREATE_OBJECT_OF_INTERFACE, MODIFY_OBJECT_OF_INTERFACE) enable polymorphic operations. However, interface link type constraints cannot be directly referenced in Actions (platform limitation as of February 2026).

### Impact on Bridge Integration design

- The **Identifiable** interface enables a universal entity lookup function that works across all Agent Teams types.
- The **Trackable** interface enables a unified status dashboard query.
- The **ContextAware** interface enables the DIA engine to detect stale context across all entities in a single query.
- The **DIACompliant** composite interface enables the full DIA verification pipeline to operate polymorphically.
- Self-referential links (Module<->Module, Phase<->Phase) will require circular dependency detection Functions (similar to the K-12 `detectCircularPrerequisites` pattern).
- The 3-hop searchAround limit means the bridge must design queries carefully. Session->Phase->Task->File is 3 hops (the maximum). Adding DIAWorkflow->Teammate requires a separate query path.

[GAP: The original docs do not specify whether OBJECT_BACKED links can be queried via interface link type constraints. The bridge should assume they cannot and design direct queries on the backing ObjectType instead.]

[GAP: The original docs do not describe transactional guarantees for creating an OBJECT_BACKED link (creating the backing object and both M:1 links atomically). The bridge should use a FUNCTION_RULE ActionType to ensure atomicity of DIAWorkflow creation.]
