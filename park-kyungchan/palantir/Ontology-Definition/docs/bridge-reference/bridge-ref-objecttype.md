# ObjectType + Property Reference -- Agent Teams Bridge Focus

> Version: 1.0 | Date: 2026-02-08 | Consumer: Opus 4.6 agents building the Agent Teams Ontology Bridge
>
> This document restructures Palantir Ontology primitives (ObjectType, Property, SharedProperty, Struct)
> with concrete mappings to Agent Teams entities. It is self-contained and requires no external docs.

---

## 1. ObjectType Definition Essentials

### 1.1 What is an ObjectType?

An ObjectType is the schema definition of a real-world entity or event. It is analogous to a database table schema, an OOP class, or a TypeScript interface. Each ObjectType defines:

- A set of typed properties (attributes)
- A primary key for unique identification of instances
- A title property for human-readable display
- Metadata (status, visibility, groups)

An ObjectType instance (called an "Object") is a single record conforming to that schema, like a row in a table.

### 1.2 When to Use ObjectType vs Struct vs Property

| Question | Yes | No |
|----------|-----|-----|
| Does it have a unique, stable identifier? | ObjectType candidate | Struct or Property |
| Is it persisted independently? | ObjectType candidate | Struct on parent |
| Do users query/filter it independently? | Strong ObjectType | Embedded Struct |
| Does it participate in relationships (links)? | ObjectType | Consider Struct |
| Does it have an independent lifecycle (CRUD)? | ObjectType | Struct on parent |
| Does it need separate permission controls? | Definitely ObjectType | May still be ObjectType |

Agent Teams examples:

| Entity | Decision | Rationale |
|--------|----------|-----------|
| Session | ObjectType | Root context, independently queried, has unique sessionId |
| Phase | ObjectType | 9 distinct stages, own lifecycle, linked to Session/Tasks |
| Task | ObjectType | Core work unit, unique taskId, full CRUD lifecycle |
| Teammate | ObjectType | Agent instance, unique identity, linked to Tasks/Phases |
| GateRecord | ObjectType | Approval artifact, independent query for audit trail |
| Module | ObjectType | Codebase entity, linked to Tasks via impact analysis |
| DIAWorkflow | ObjectType | Protocol chain with own lifecycle and state machine |
| L1/L2 indexes | Struct on Task | No independent query need; always accessed via parent Task |
| DIA step detail | Struct on DIAWorkflow | Step-level data embedded in workflow; depth-1 flat fields |
| GC version number | Property on Session | Scalar attribute, no independent identity |

### 1.3 Primary Key Strategy

Rules from the Palantir spec:

- Must be deterministic (same value across builds/runs)
- Must be unique per instance (duplicates cause pipeline failure)
- Cannot be null
- Recommended types: String, Integer (avoid Long for JavaScript precision, never use Float/Double)
- Composite keys: concatenate into single String with delimiter

For Agent Teams entities, String-based UUIDs or semantic composite keys are preferred because agent sessions generate identifiers at runtime.

### 1.4 Required ObjectType Fields

| Field | Type | Convention | Example |
|-------|------|------------|---------|
| apiName | String | PascalCase, starts uppercase | `AgentTeamsSession` |
| displayName | String | Human-readable | `Agent Teams Session` |
| pluralDisplayName | String | Plural form | `Agent Teams Sessions` |
| primaryKey | Array<String> | Property name(s) | `["sessionId"]` |
| titleKey | String | Most readable property | `"sessionName"` |
| backingDatasource | String (RID) | Dataset backing | `ri.foundry.main...` |

Optional but recommended: description, status (ACTIVE/EXPERIMENTAL), visibility (PROMINENT/NORMAL/HIDDEN), groups, icon, color.

### 1.5 Naming Rules

- apiName: PascalCase, `^[A-Z][a-z0-9]*([A-Z][a-z0-9]*)*$`
- Forbidden names: Ontology, Object, Property, Link, Relation, Rid, PrimaryKey, TypeId, OntologyObject
- Must be globally unique within the ontology

---

## 2. Property Type Catalog

### 2.1 Primitive Types

| BaseType | Description | PK Allowed | Action Param | Agent Teams Usage |
|----------|-------------|------------|--------------|-------------------|
| String | Text data, UTF-8 | Yes (recommended) | Yes | IDs, names, descriptions, enum-as-string |
| Integer | Whole number, +/-2 billion | Yes (recommended) | Yes | Phase number, iteration count, priority |
| Short | Whole number, +/-32K | Yes (discouraged) | Yes | Rarely needed |
| Long | Whole number, large range | Yes (discouraged) | Yes | Avoid for JS-exposed values |
| Byte | Whole number, -128 to 127 | Yes (discouraged) | Yes | Rarely needed |
| Boolean | true/false | Yes (discouraged) | Yes | Flags: isBlocked, isApproved |
| Float | Approx decimal, lower precision | No | No | Rarely needed |
| Double | Approx decimal | No | No | Confidence scores, metrics |
| Decimal | Exact decimal | No | No | Financial values (not needed here) |

### 2.2 Time Types

| BaseType | Description | Agent Teams Usage |
|----------|-------------|-------------------|
| Date | Date only (no time) | Not commonly needed |
| Timestamp | Date + time | createdAt, completedAt, gateApprovedAt, spawnedAt |

### 2.3 Complex Types

| BaseType | Description | Constraints | Agent Teams Usage |
|----------|-------------|-------------|-------------------|
| Array<T> | List of primitives or Structs | No nulls, no nested arrays (OSv2) | Array<String> for file lists, tag lists |
| Struct | Embedded object | Max depth 1, max 10 fields | L1/L2 index data, DIA step details |
| Vector | ML embeddings | Max 2048 dimensions, OSv2 only | Semantic search on task descriptions (future) |

### 2.4 Reference/Special Types

| BaseType | Description | Agent Teams Usage |
|----------|-------------|-------------------|
| MediaReference | File reference | Attached artifacts |
| Attachment | Document attachment | L3 full detail archives |
| TimeSeries | Time series data | Session metrics over time (future) |
| CipherText | Encrypted text | Sensitive credentials (if any) |

### 2.5 Property Naming and Metadata

- apiName: camelCase, `^[a-z][a-zA-Z0-9]*$`
- Forbidden: ontology, object, property, link, relation, rid, primaryKey, typeId
- Must be unique within the ObjectType (max 2000 properties per ObjectType)

Render hints control UI behavior:

| Hint | Purpose | Dependency | Agent Teams Properties |
|------|---------|------------|----------------------|
| searchable | Full-text search index | None | sessionName, taskSubject, teammateName |
| sortable | Column sorting | Requires searchable | createdAt, priority, phaseNumber |
| selectable | Selection in tables | Requires searchable | status, role, phaseNumber |
| lowCardinality | Dropdown filter UI | Requires searchable | status enums, role enums, phase enums |
| longText | Multi-line text | None | description, impactAnalysis, notes |
| keywords | Tag/chip display | None | tags, groups, labels |
| identifier | Monospace/badge style | None | sessionId, taskId, teammateId |

### 2.6 Constraints

| Constraint | Applies To | Example |
|------------|-----------|---------|
| enum | Any type | `["PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED"]` |
| range | Numeric | `{ min: 1, max: 9 }` for phaseNumber |
| regex | String | `^[A-Z][a-z]+-[0-9]+$` for taskId patterns |
| uuid | String | True for primary key IDs |
| uniqueness | Array | Array elements must be distinct |

---

## 3. Struct Type (Embedded Objects)

### 3.1 When to Embed vs Separate ObjectType

Use Struct when the data:
- Has no independent identity or lifecycle
- Is always accessed through a parent entity
- Does not need independent query/filter
- Does not participate in its own relationships (LinkTypes)

Use a separate ObjectType when:
- The data needs to be independently queried
- It participates in relationships with multiple other entities
- It has its own CRUD lifecycle
- More than 10 fields are needed (Struct limit)

### 3.2 Struct Constraints

- Maximum depth: 1 (no nested Structs)
- Maximum fields per Struct: 10
- Allowed field types: Boolean, Byte, Date, Decimal, Double, Float, Geopoint, Integer, Long, Short, String, Timestamp
- Arrays of Structs are allowed (Array<Struct>)

### 3.3 Agent Teams Struct Examples

**L1 Index Entry (on Task)**

```yaml
l1IndexEntry:
  baseType: "Struct"
  structSchema:
    fileName:
      baseType: "String"
      description: "Artifact file path"
    artifactType:
      baseType: "String"
      description: "L1, L2, or L3"
    lineCount:
      baseType: "Integer"
      description: "Lines in artifact"
    lastUpdated:
      baseType: "Timestamp"
      description: "When artifact was last written"
```

**DIA Verification Step (on DIAWorkflow)**

```yaml
verificationStep:
  baseType: "Struct"
  structSchema:
    stepNumber:
      baseType: "Integer"
    rcItemId:
      baseType: "String"
      description: "RC-01 through RC-10"
    result:
      baseType: "String"
      description: "PASS or FAIL"
    note:
      baseType: "String"
      description: "Reviewer note"
    timestamp:
      baseType: "Timestamp"
```

**Gate Checklist Item (on GateRecord)**

```yaml
checklistItem:
  baseType: "Struct"
  structSchema:
    checkId:
      baseType: "String"
    description:
      baseType: "String"
    passed:
      baseType: "Boolean"
    evidence:
      baseType: "String"
```

---

## 4. Agent Teams ObjectType Mapping

### 4.1 Session

```yaml
apiName: "AgentTeamsSession"
displayName: "Agent Teams Session"
pluralDisplayName: "Agent Teams Sessions"
description: "Root context for an Agent Teams pipeline execution"
primaryKey: ["sessionId"]
titleProperty: "sessionName"
status: "ACTIVE"
visibility: "PROMINENT"

properties:
  sessionId:
    baseType: "String"
    description: "Unique session identifier (UUID)"
    required: true
    renderHints: { searchable: true, identifier: true }
    constraints: { uuid: true }

  sessionName:
    baseType: "String"
    description: "Human-readable session name derived from user request"
    required: true
    renderHints: { searchable: true, sortable: true }

  gcVersion:
    baseType: "Integer"
    description: "Current Global Context version number (monotonic)"
    required: true
    constraints: { range: { min: 1 } }

  currentPhase:
    baseType: "Integer"
    description: "Currently active phase number (1-9)"
    required: true
    constraints: { range: { min: 1, max: 9 } }

  status:
    baseType: "String"
    description: "Overall session status"
    required: true
    renderHints: { searchable: true, selectable: true, lowCardinality: true }
    constraints:
      enum: ["INITIALIZING", "ACTIVE", "PAUSED", "COMPLETED", "ABORTED"]

  workspace:
    baseType: "String"
    description: "Filesystem workspace path"
    required: true

  createdAt:
    baseType: "Timestamp"
    description: "Session creation timestamp"
    required: true
    renderHints: { searchable: true, sortable: true }

  completedAt:
    baseType: "Timestamp"
    description: "Session completion timestamp"
    required: false

  totalTasks:
    baseType: "Integer"
    description: "Total number of tasks created in this session"
    required: false

  totalTeammates:
    baseType: "Integer"
    description: "Total number of teammates spawned in this session"
    required: false

  outputDirectory:
    baseType: "String"
    description: "Path to .agent/teams/{session-id}/ directory"
    required: true
```

### 4.2 Phase

```yaml
apiName: "PipelinePhase"
displayName: "Pipeline Phase"
pluralDisplayName: "Pipeline Phases"
description: "A stage in the 9-phase Agent Teams pipeline (P1-P9)"
primaryKey: ["phaseId"]
titleProperty: "phaseName"
status: "ACTIVE"
visibility: "PROMINENT"

properties:
  phaseId:
    baseType: "String"
    description: "Composite key: {sessionId}-P{phaseNumber}"
    required: true
    renderHints: { searchable: true, identifier: true }

  phaseNumber:
    baseType: "Integer"
    description: "Phase ordinal (1 through 9)"
    required: true
    renderHints: { searchable: true, selectable: true, lowCardinality: true }
    constraints: { range: { min: 1, max: 9 } }

  phaseName:
    baseType: "String"
    description: "Phase display name"
    required: true
    renderHints: { searchable: true }
    constraints:
      enum:
        - "Discovery"
        - "Deep Research"
        - "Architecture"
        - "Detailed Design"
        - "Plan Validation"
        - "Implementation"
        - "Testing"
        - "Integration"
        - "Delivery"

  zone:
    baseType: "String"
    description: "Execution zone classification"
    required: true
    renderHints: { selectable: true, lowCardinality: true }
    constraints:
      enum: ["PRE-EXEC", "EXEC", "POST-EXEC"]

  status:
    baseType: "String"
    description: "Phase execution status"
    required: true
    renderHints: { searchable: true, selectable: true, lowCardinality: true }
    constraints:
      enum: ["PENDING", "ACTIVE", "ITERATING", "GATE_REVIEW", "APPROVED", "ABORTED"]

  effortLevel:
    baseType: "String"
    description: "Expected effort level from CLAUDE.md"
    required: true
    constraints:
      enum: ["max", "high", "medium"]

  iterationCount:
    baseType: "Integer"
    description: "Number of iterations within this phase (max 3)"
    required: true
    constraints: { range: { min: 0, max: 3 } }

  teammateRole:
    baseType: "String"
    description: "Role type assigned to this phase"
    required: true
    renderHints: { selectable: true, lowCardinality: true }
    constraints:
      enum: ["lead", "researcher", "architect", "devils-advocate", "implementer", "tester", "integrator"]

  startedAt:
    baseType: "Timestamp"
    description: "When this phase began"
    required: false

  completedAt:
    baseType: "Timestamp"
    description: "When this phase was approved/completed"
    required: false
```

### 4.3 Task

```yaml
apiName: "AgentTask"
displayName: "Agent Task"
pluralDisplayName: "Agent Tasks"
description: "A unit of work assigned by Lead to a teammate"
primaryKey: ["taskId"]
titleProperty: "subject"
status: "ACTIVE"
visibility: "PROMINENT"

properties:
  taskId:
    baseType: "String"
    description: "Unique task identifier (numeric string from Task API)"
    required: true
    renderHints: { searchable: true, identifier: true }

  subject:
    baseType: "String"
    description: "Imperative action verb + specific target (task title)"
    required: true
    renderHints: { searchable: true, sortable: true }

  description:
    baseType: "String"
    description: "Full task description with objective, requirements, file ownership, acceptance criteria"
    required: true
    renderHints: { longText: true }

  status:
    baseType: "String"
    description: "Task lifecycle status"
    required: true
    renderHints: { searchable: true, selectable: true, lowCardinality: true }
    constraints:
      enum: ["OPEN", "IN_PROGRESS", "BLOCKED", "REVIEW", "COMPLETED", "CANCELLED"]

  priority:
    baseType: "Integer"
    description: "Task priority (1=highest, 5=lowest)"
    required: true
    renderHints: { sortable: true, selectable: true }
    constraints: { range: { min: 1, max: 5 } }

  assigneeRole:
    baseType: "String"
    description: "Teammate role assigned to this task"
    required: true
    renderHints: { selectable: true, lowCardinality: true }
    constraints:
      enum: ["researcher", "architect", "devils-advocate", "implementer", "tester", "integrator"]

  assigneeId:
    baseType: "String"
    description: "Specific teammate instance identifier"
    required: false

  fileOwnership:
    baseType: "Array"
    arraySubtype: "String"
    description: "List of file paths this task owns exclusively"
    required: false

  acceptanceCriteria:
    baseType: "Array"
    arraySubtype: "String"
    description: "Explicit criteria for task completion"
    required: true

  l1Artifacts:
    baseType: "Array"
    arraySubtype: "Struct"
    description: "L1 index entries for this task's output artifacts"
    structSchema:
      fileName:
        baseType: "String"
      artifactType:
        baseType: "String"
      lineCount:
        baseType: "Integer"
      lastUpdated:
        baseType: "Timestamp"

  impactVerified:
    baseType: "Boolean"
    description: "Whether DIA impact analysis has been verified for this task"
    required: true

  createdAt:
    baseType: "Timestamp"
    description: "Task creation timestamp"
    required: true
    renderHints: { sortable: true }

  completedAt:
    baseType: "Timestamp"
    description: "Task completion timestamp"
    required: false
```

### 4.4 Teammate

```yaml
apiName: "AgentTeammate"
displayName: "Agent Teammate"
pluralDisplayName: "Agent Teammates"
description: "An agent instance spawned to perform work in a specific phase"
primaryKey: ["teammateId"]
titleProperty: "teammateName"
status: "ACTIVE"
visibility: "PROMINENT"

properties:
  teammateId:
    baseType: "String"
    description: "Unique teammate instance identifier"
    required: true
    renderHints: { searchable: true, identifier: true }

  teammateName:
    baseType: "String"
    description: "Human-readable name (e.g., researcher-1, implementer-3)"
    required: true
    renderHints: { searchable: true }

  role:
    baseType: "String"
    description: "Agent role type"
    required: true
    renderHints: { searchable: true, selectable: true, lowCardinality: true }
    constraints:
      enum: ["researcher", "architect", "devils-advocate", "implementer", "tester", "integrator"]

  status:
    baseType: "String"
    description: "Teammate lifecycle status"
    required: true
    renderHints: { selectable: true, lowCardinality: true }
    constraints:
      enum: ["SPAWNING", "ACTIVE", "IDLE", "CONTEXT_PRESSURE", "SHUTDOWN", "ABORTED"]

  gcVersionReceived:
    baseType: "Integer"
    description: "Latest Global Context version this teammate has acknowledged"
    required: true

  diaTier:
    baseType: "Integer"
    description: "DIA verification tier (0=exempt, 1=full, 2=medium, 3=light)"
    required: true
    constraints: { range: { min: 0, max: 3 } }

  ldapIntensity:
    baseType: "String"
    description: "LDAP adversarial challenge intensity level"
    required: true
    constraints:
      enum: ["NONE", "EXEMPT", "MEDIUM", "HIGH", "MAXIMUM"]

  impactAttempts:
    baseType: "Integer"
    description: "Number of impact analysis attempts (max 3)"
    required: true
    constraints: { range: { min: 0, max: 3 } }

  spawnedAt:
    baseType: "Timestamp"
    description: "When this teammate was spawned"
    required: true

  terminatedAt:
    baseType: "Timestamp"
    description: "When this teammate was shut down"
    required: false

  contextPressureReported:
    baseType: "Boolean"
    description: "Whether this teammate has reported context pressure"
    required: true
```

### 4.5 GateRecord

```yaml
apiName: "GateRecord"
displayName: "Gate Record"
pluralDisplayName: "Gate Records"
description: "Approval record for a phase transition gate"
primaryKey: ["gateId"]
titleProperty: "gateName"
status: "ACTIVE"
visibility: "NORMAL"

properties:
  gateId:
    baseType: "String"
    description: "Composite key: {sessionId}-P{phaseNumber}-gate"
    required: true
    renderHints: { searchable: true, identifier: true }

  gateName:
    baseType: "String"
    description: "Display name (e.g., 'Phase 3 Architecture Gate')"
    required: true
    renderHints: { searchable: true }

  decision:
    baseType: "String"
    description: "Gate outcome"
    required: true
    renderHints: { selectable: true, lowCardinality: true }
    constraints:
      enum: ["APPROVE", "ITERATE", "ABORT"]

  checklist:
    baseType: "Array"
    arraySubtype: "Struct"
    description: "Gate checklist items and results"
    structSchema:
      checkId:
        baseType: "String"
      description:
        baseType: "String"
      passed:
        baseType: "Boolean"
      evidence:
        baseType: "String"

  gateType:
    baseType: "String"
    description: "Whether this is Gate A (impact) or Gate B (plan)"
    required: true
    constraints:
      enum: ["GATE_A", "GATE_B", "PHASE_GATE"]

  unresolvedIssues:
    baseType: "Array"
    arraySubtype: "String"
    description: "List of unresolved issues at gate time"
    required: false

  iterationNumber:
    baseType: "Integer"
    description: "Which iteration of the phase this gate evaluates"
    required: true
    constraints: { range: { min: 1, max: 3 } }

  evaluatedAt:
    baseType: "Timestamp"
    description: "When the gate evaluation was performed"
    required: true
    renderHints: { sortable: true }

  evaluatedBy:
    baseType: "String"
    description: "Always 'Lead' for phase gates"
    required: true
```

### 4.6 Module

```yaml
apiName: "CodebaseModule"
displayName: "Codebase Module"
pluralDisplayName: "Codebase Modules"
description: "A file or directory in the codebase tracked in impact analysis"
primaryKey: ["moduleId"]
titleProperty: "modulePath"
status: "ACTIVE"
visibility: "NORMAL"

properties:
  moduleId:
    baseType: "String"
    description: "Deterministic hash of the module path"
    required: true
    renderHints: { identifier: true }

  modulePath:
    baseType: "String"
    description: "Absolute filesystem path"
    required: true
    renderHints: { searchable: true }

  moduleType:
    baseType: "String"
    description: "Classification of the module"
    required: true
    renderHints: { selectable: true, lowCardinality: true }
    constraints:
      enum: ["FILE", "DIRECTORY", "CONFIG", "HOOK", "AGENT_MD", "SKILL"]

  lineCount:
    baseType: "Integer"
    description: "Number of lines in the file (0 for directories)"
    required: false

  lastModified:
    baseType: "Timestamp"
    description: "Last modification timestamp from filesystem"
    required: false

  ownedBy:
    baseType: "String"
    description: "Current task/teammate that has write ownership"
    required: false

  isProtected:
    baseType: "Boolean"
    description: "Whether this file is in the protected list (.env, credentials, etc.)"
    required: true
```

### 4.7 DIAWorkflow

```yaml
apiName: "DIAWorkflow"
displayName: "DIA Workflow"
pluralDisplayName: "DIA Workflows"
description: "A Directive-Impact-Analysis protocol chain tracking context injection through verification"
primaryKey: ["workflowId"]
titleProperty: "workflowName"
status: "ACTIVE"
visibility: "NORMAL"

properties:
  workflowId:
    baseType: "String"
    description: "Unique workflow identifier: {taskId}-dia-{attempt}"
    required: true
    renderHints: { searchable: true, identifier: true }

  workflowName:
    baseType: "String"
    description: "Display name linking task and teammate"
    required: true
    renderHints: { searchable: true }

  currentStep:
    baseType: "String"
    description: "Current step in the DIA protocol"
    required: true
    renderHints: { selectable: true, lowCardinality: true }
    constraints:
      enum:
        - "DIRECTIVE_SENT"
        - "CONTEXT_RECEIVED"
        - "IMPACT_SUBMITTED"
        - "RC_REVIEWING"
        - "CHALLENGE_SENT"
        - "CHALLENGE_RESPONDED"
        - "IMPACT_VERIFIED"
        - "IMPACT_REJECTED"
        - "PLAN_SUBMITTED"
        - "PLAN_APPROVED"
        - "PLAN_REJECTED"

  tier:
    baseType: "Integer"
    description: "DIA verification tier (0-3)"
    required: true
    constraints: { range: { min: 0, max: 3 } }

  attempt:
    baseType: "Integer"
    description: "Which attempt number (max 3 for Tier 1/2, max 2 for Tier 3)"
    required: true
    constraints: { range: { min: 1, max: 3 } }

  gcVersionInjected:
    baseType: "Integer"
    description: "GC version embedded in the directive"
    required: true

  injectionMode:
    baseType: "String"
    description: "Whether context was injected as delta or full"
    required: true
    constraints:
      enum: ["DELTA", "FULL"]

  rcCheckResults:
    baseType: "Array"
    arraySubtype: "Struct"
    description: "Results for each RC checklist item"
    structSchema:
      rcItemId:
        baseType: "String"
      result:
        baseType: "String"
      note:
        baseType: "String"
      timestamp:
        baseType: "Timestamp"

  challengeCategory:
    baseType: "String"
    description: "LDAP challenge category if challenge was issued"
    required: false
    constraints:
      enum:
        - "INTERCONNECTION_MAP"
        - "SCOPE_BOUNDARY"
        - "RIPPLE_TRACE"
        - "FAILURE_MODE"
        - "DEPENDENCY_RISK"
        - "ASSUMPTION_PROBE"
        - "ALTERNATIVE_DEMAND"

  startedAt:
    baseType: "Timestamp"
    description: "When the directive was first sent"
    required: true

  completedAt:
    baseType: "Timestamp"
    description: "When the workflow reached a terminal state"
    required: false
```

---

## 5. Validation Rules (Bridge-Relevant)

### 5.1 ObjectType-Level Validation

| Rule | Check | Severity | Agent Teams Note |
|------|-------|----------|-----------------|
| apiName starts uppercase | `^[A-Z]` | Error | All 7 entity types use PascalCase |
| apiName is PascalCase | `^[A-Z][a-z0-9]*([A-Z][a-z0-9]*)*$` | Error | AgentTeamsSession, not Agent_Teams_Session |
| apiName not reserved | Not in forbidden list | Error | None of our names conflict |
| primaryKey property exists | PK refs valid property | Error | All entities have explicit PK |
| titleProperty exists | titleKey refs valid property | Error | All entities have titleProperty |
| PK type is allowed | String or Integer | Error | All PKs use String |
| Max 2000 properties | Count check | Error | Largest entity (Task) has ~15 properties, well within limit |

### 5.2 Property-Level Validation

| Rule | Check | Severity | Agent Teams Note |
|------|-------|----------|-----------------|
| apiName starts lowercase | `^[a-z]` | Error | All properties use camelCase |
| apiName is camelCase | `^[a-z][a-zA-Z0-9]*$` | Error | gcVersion, not gc_version |
| apiName unique in ObjectType | Scope check | Error | Verified in section 4 definitions |
| Struct depth is 1 | No nested structs | Error | All structs are flat |
| Struct max 10 fields | Field count check | Error | Largest struct has 5 fields |
| sortable requires searchable | Dependency check | Warning | All sortable props have searchable |
| selectable requires searchable | Dependency check | Warning | All selectable props have searchable |
| Array contains no nulls | Runtime check | Error | File lists and criteria lists are non-nullable |

### 5.3 SharedProperty Candidates

Properties shared across multiple Agent Teams ObjectTypes that should become SharedProperties:

| Property | Shared Across | Semantic Consistency | Recommend SharedProperty? |
|----------|--------------|---------------------|--------------------------|
| status | Session, Phase, Task, Teammate, DIAWorkflow | Different enums per type | No -- different semantics |
| createdAt / startedAt | All 7 types | Same meaning (creation time) | Yes -- universal timestamp |
| completedAt | Session, Phase, Task, Teammate, DIAWorkflow | Same meaning (completion time) | Yes -- universal timestamp |
| sessionId (as FK) | Phase, Task, Teammate, GateRecord | Same FK reference | Consider for Interface |
| gcVersion | Session (as current), Teammate (as received), DIAWorkflow (as injected) | Subtly different meanings | No -- different semantics |

---

## 6. Anti-Patterns to Avoid

### Anti-Pattern 1: Over-Normalization of DIA Steps

```yaml
# Wrong: Creating ObjectTypes for each DIA protocol step
apiName: "DirectiveSent"
apiName: "ImpactSubmitted"
apiName: "ChallengeIssued"
# These have no independent identity and always belong to a DIAWorkflow

# Correct: Model DIA steps as enum status + Struct array on DIAWorkflow
currentStep: "IMPACT_SUBMITTED"
rcCheckResults: [{ rcItemId: "RC-01", result: "PASS", ... }]
```

### Anti-Pattern 2: Non-Deterministic Primary Keys

```yaml
# Wrong: Using runtime-generated row numbers or timestamps as PK
primaryKey: ["spawnOrder"]  # Changes if teammates are spawned in different order

# Correct: Use deterministic composite keys
primaryKey: ["teammateId"]  # UUID assigned at spawn time
# Or: "{sessionId}-{role}-{instanceNumber}" for semantic composite
```

### Anti-Pattern 3: Mutable Fields as Primary Key

```yaml
# Wrong: Using status or phase number as part of PK
primaryKey: ["sessionId", "currentPhase"]  # currentPhase changes!

# Correct: Use stable identifiers only
primaryKey: ["phaseId"]  # Composite: "{sessionId}-P{phaseNumber}" is immutable
```

### Anti-Pattern 4: Deeply Nested Structs for L3 Data

```yaml
# Wrong: Trying to embed full L3 detail as nested structs
l3Detail:
  baseType: "Struct"
  structSchema:
    section:
      baseType: "Struct"  # Depth > 1, forbidden!
      structSchema: ...

# Correct: L3 is a directory of files, reference by path
l3DirectoryPath:
  baseType: "String"
  description: "Path to L3-full/ directory"
```

### Anti-Pattern 5: Overloading a Single Status Enum

```yaml
# Wrong: One status field that mixes lifecycle and DIA state
status:
  constraints:
    enum: ["OPEN", "IMPACT_PENDING", "IMPACT_VERIFIED", "IN_PROGRESS", "COMPLETED"]
# Mixes task lifecycle (OPEN/IN_PROGRESS/COMPLETED) with DIA state

# Correct: Separate concerns into distinct properties
status:
  constraints:
    enum: ["OPEN", "IN_PROGRESS", "BLOCKED", "REVIEW", "COMPLETED", "CANCELLED"]
impactVerified:
  baseType: "Boolean"
```

### Anti-Pattern 6: Creating SharedProperty for Single-Use Properties

```yaml
# Wrong: Making phaseNumber a SharedProperty because it appears on Phase and GateRecord
# It has the same name but the semantic role differs (Phase.phaseNumber = identity,
# GateRecord references it as FK context)

# Correct: Only promote to SharedProperty when 2+ types share identical semantics
# createdAt and completedAt are good SharedProperty candidates
```

---

## 7. Forward-Compatibility Notes

### 7.1 Impact on LinkType Design

The ObjectType definitions directly determine which LinkTypes are needed. Based on section 4:

| Anticipated LinkType | Source | Target | Cardinality | FK Indicator |
|---------------------|--------|--------|-------------|--------------|
| sessionContainsPhases | AgentTeamsSession | PipelinePhase | ONE_TO_MANY | Phase.phaseId includes sessionId |
| sessionSpawnedTeammates | AgentTeamsSession | AgentTeammate | ONE_TO_MANY | implicit session scope |
| phaseContainsTasks | PipelinePhase | AgentTask | ONE_TO_MANY | Task assigned during phase |
| taskAssignedToTeammate | AgentTask | AgentTeammate | MANY_TO_ONE | Task.assigneeId |
| phaseHasGate | PipelinePhase | GateRecord | ONE_TO_ONE | GateRecord.phaseId |
| taskImpactModule | AgentTask | CodebaseModule | MANY_TO_MANY | impact analysis file list |
| taskHasDIAWorkflow | AgentTask | DIAWorkflow | ONE_TO_MANY | multiple attempts |
| teammateExecutesDIA | AgentTeammate | DIAWorkflow | ONE_TO_MANY | teammate assigned |
| moduleOwnedByTask | CodebaseModule | AgentTask | MANY_TO_ONE | Module.ownedBy |

Design the ObjectType PKs with these anticipated links in mind. Composite keys that embed parent IDs (like phaseId = "{sessionId}-P{N}") simplify FK-backed link resolution.

### 7.2 Impact on ActionType Design

State transitions in the Agent Teams protocol map to ActionType candidates:

| State Change | Candidate ActionType | Parameters | Preconditions |
|-------------|---------------------|------------|---------------|
| Create session | createSession | workspace, sessionName | None |
| Advance phase | advancePhase | sessionId, targetPhase | currentPhase < targetPhase, gate APPROVED |
| Spawn teammate | spawnTeammate | sessionId, role, phaseNumber | Phase is ACTIVE |
| Assign task | assignTask | taskId, teammateId | Teammate is ACTIVE, task is OPEN |
| Submit impact | submitImpactAnalysis | workflowId, analysisContent | Workflow at DIRECTIVE_SENT or CONTEXT_RECEIVED |
| Approve gate | approveGate | gateId, decision | All checklist items evaluated |
| Terminate teammate | terminateTeammate | teammateId, reason | Teammate is ACTIVE or IDLE |

These ActionTypes will use the property types and enum values defined in the ObjectTypes above, so property enum lists must be stable before ActionType design begins.

### 7.3 Impact on Interface Design

Candidate Interfaces based on shared property patterns:

| Interface Candidate | SharedProperties | Implementing ObjectTypes |
|--------------------|-----------------|------------------------|
| Timestamped | createdAt, completedAt | All 7 ObjectTypes |
| SessionScoped | sessionId (FK) | Phase, Task, Teammate, GateRecord, DIAWorkflow |
| Stateful | status (generic lifecycle) | Session, Phase, Task, Teammate |
| Auditable | evaluatedBy, evaluatedAt | GateRecord, DIAWorkflow |

Note: The "status" properties have different enum values across types, so the Interface would need to define status as a generic String SharedProperty without enum constraints, with each implementing type adding its own constraints locally. This is a design tradeoff to evaluate during Interface phase.

[GAP: The source documentation does not specify whether Palantir Interfaces support local constraint overrides on SharedProperties that have base constraints defined at the Interface level. This needs verification before implementing the Stateful interface.]

### 7.4 OSv2 Limits to Keep in Mind

| Limit | Value | Agent Teams Impact |
|-------|-------|--------------------|
| Properties per ObjectType | 2000 | Well within limit (max ~15 per entity) |
| Max objects per action | 10,000 | Relevant for batch task creation |
| Search-around default limit | 100,000 | Relevant for large session histories |
| Action primitive list max | 10,000 | Relevant for fileOwnership arrays |
| Struct max fields | 10 | Constrains L1 index and RC check structs |
| Struct max depth | 1 | Prevents nested embedding of L3 data |
