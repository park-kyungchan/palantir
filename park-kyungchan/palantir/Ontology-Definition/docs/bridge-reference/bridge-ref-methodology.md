# Decomposition Methodology Reference -- Agent Teams Bridge Focus

> Version: 1.0 | Date: 2026-02-08 | Consumer: Opus 4.6 agents building the Agent Teams Ontology Bridge
>
> This document applies the Palantir Ontology Decomposition methodology to the Agent Teams domain.
> It walks through all 8 decomposition phases with concrete Agent Teams decisions already resolved,
> and provides the output template and validation checklist. Self-contained; no external docs required.

---

## 1. 8-Phase Methodology Overview

Ontology Decomposition is a systematic, decision-tree-driven process for converting a domain model into
Palantir Ontology primitives. The 8 phases and their Agent Teams bridge mapping:

| Phase | Decomposition Phase | Output Primitive | Agent Teams Mapping |
|-------|-------------------|-----------------|---------------------|
| 1 | Entity Discovery | ObjectType candidates | CLAUDE.md entities, task-api structures, hook events |
| 2 | Relationship Discovery | LinkType candidates | FK references in orchestration-plan, task dependencies |
| 3 | Mutation Discovery | ActionType candidates | DIA protocol state transitions, pipeline phase changes |
| 4 | Logic Discovery | Function candidates | Gate evaluation logic, RC checklist scoring, spawn decisions |
| 5 | Interface Discovery | Interface candidates | Shared patterns across Session, Task, Teammate, etc. |
| 6 | Automation Discovery | Automation candidates | Hook scripts, context pressure handlers, compact recovery |
| 7 | Security Mapping | Security definitions | File ownership rules, protected files, disallowedTools |
| 8 | Output Assembly | Complete YAML | Final bridge ontology definition package |

The methodology is analogous to Domain-Driven Design: Phase 1 discovers Aggregate Roots (ObjectTypes),
Phase 2 discovers relationships between aggregates (LinkTypes), and Phases 3-4 discover the commands
and queries that operate on them (ActionTypes and Functions).

### Mapping to Agent Teams Pipeline Phases

The decomposition methodology itself maps onto the Agent Teams 9-phase pipeline:

| Decomposition Phase | Best Mapped To AT Phase | Rationale |
|---------------------|------------------------|-----------|
| Phase 1 (Entity) | P1 Discovery + P2 Research | Requires scanning source code and domain documents |
| Phase 2 (Relationship) | P2 Research | FK indicators found during source analysis |
| Phase 3 (Mutation) | P3 Architecture | State transitions are architectural decisions |
| Phase 4 (Logic) | P3-P4 Architecture/Design | Business rules need design-level thinking |
| Phase 5 (Interface) | P4 Detailed Design | Interface extraction is a design refinement |
| Phase 6 (Automation) | P4 Detailed Design | Trigger mapping requires detailed analysis |
| Phase 7 (Security) | P4 Detailed Design | Security is a cross-cutting design concern |
| Phase 8 (Output) | P6-P8 Implementation/Integration | Producing the actual YAML artifacts |

---

## 2. Entity Discovery Applied to Agent Teams

### 2.1 Source Scanning Results

The "source code" for Agent Teams is the infrastructure configuration itself:

| Source | Location | Entities Found |
|--------|----------|---------------|
| CLAUDE.md | `.claude/CLAUDE.md` | Session (Team Identity), Phase (Phase Pipeline), Teammate (Role Protocol) |
| task-api-guideline.md | `.claude/references/task-api-guideline.md` | Task (Task Storage), DIAWorkflow (DIA Protocol) |
| orchestration-plan.md | `.agent/teams/{id}/orchestration-plan.md` | GateRecord (Gate Checklist), Module (File Ownership) |
| gate-record.yaml | `.agent/teams/{id}/phase-{N}/gate-record.yaml` | GateRecord (structured approval) |
| Hook scripts | `.claude/hooks/` | Automation triggers (not ObjectTypes themselves) |

### 2.2 Decision Tree Results for Each Entity

#### Session

| Question | Answer | Conclusion |
|----------|--------|------------|
| Has unique, stable identifier? | Yes -- session UUID from TeamCreate | Continue |
| Is persisted? | Yes -- `.agent/teams/{session-id}/` directory | Continue |
| Independently queryable? | Yes -- "show me all past sessions" is a valid query | Strong candidate |
| Participates in relationships? | Yes -- parent of Phases, Tasks, Teammates | Continue |
| Has multiple properties? | Yes -- workspace, gcVersion, currentPhase, status | Continue |
| Independent lifecycle? | Yes -- created, active, completed independently | Continue |

Result: **ObjectType** (`AgentTeamsSession`)

#### Phase

| Question | Answer | Conclusion |
|----------|--------|------------|
| Has unique, stable identifier? | Yes -- composite `{sessionId}-P{number}` | Continue |
| Is persisted? | Yes -- `phase-{N}/` directories, gate records | Continue |
| Independently queryable? | Yes -- "which phases have been completed?" | Strong candidate |
| Participates in relationships? | Yes -- linked to Session, Tasks, GateRecords | Continue |
| Has multiple properties? | Yes -- number, name, zone, status, effort, iteration | Continue |
| Independent lifecycle? | Yes -- transitions through PENDING/ACTIVE/APPROVED | Continue |

Result: **ObjectType** (`PipelinePhase`)

#### Task

| Question | Answer | Conclusion |
|----------|--------|------------|
| Has unique, stable identifier? | Yes -- numeric ID from Task API | Continue |
| Is persisted? | Yes -- `~/.claude/tasks/{scope}/{id}.json` | Continue |
| Independently queryable? | Yes -- TaskList/TaskGet are core operations | Strong candidate |
| Participates in relationships? | Yes -- linked to Session, Phase, Teammate, Modules | Continue |
| Has multiple properties? | Yes -- subject, description, status, priority, files, criteria | Continue |
| Independent lifecycle? | Yes -- OPEN/IN_PROGRESS/COMPLETED/CANCELLED | Continue |

Result: **ObjectType** (`AgentTask`)

#### Teammate

| Question | Answer | Conclusion |
|----------|--------|------------|
| Has unique, stable identifier? | Yes -- agent instance ID at spawn time | Continue |
| Is persisted? | Yes -- tracked in orchestration-plan, L1/L2/L3 directories | Continue |
| Independently queryable? | Yes -- "which teammates are active?" | Strong candidate |
| Participates in relationships? | Yes -- linked to Session, Tasks, DIAWorkflows | Continue |
| Has multiple properties? | Yes -- role, status, gcVersion, tier, intensity, timestamps | Continue |
| Independent lifecycle? | Yes -- SPAWNING/ACTIVE/IDLE/SHUTDOWN | Continue |

Result: **ObjectType** (`AgentTeammate`)

#### GateRecord

| Question | Answer | Conclusion |
|----------|--------|------------|
| Has unique, stable identifier? | Yes -- composite `{sessionId}-P{N}-gate` | Continue |
| Is persisted? | Yes -- `gate-record.yaml` files | Continue |
| Independently queryable? | Yes -- audit trail queries, "which gates were ITERATE?" | Strong candidate |
| Participates in relationships? | Yes -- linked to Phase (1:1), evaluated by Lead | Continue |
| Has multiple properties? | Yes -- decision, checklist, issues, iteration, timestamps | Continue |
| Independent lifecycle? | Partial -- created at gate time, immutable after | Acceptable |

Result: **ObjectType** (`GateRecord`)

#### Module

| Question | Answer | Conclusion |
|----------|--------|------------|
| Has unique, stable identifier? | Yes -- deterministic path hash | Continue |
| Is persisted? | Yes -- filesystem entries tracked in impact analysis | Continue |
| Independently queryable? | Yes -- "which files are modified?" "who owns this file?" | Strong candidate |
| Participates in relationships? | Yes -- linked to Tasks via impact analysis, ownership | Continue |
| Has multiple properties? | Yes -- path, type, lineCount, owner, protected status | Continue |
| Independent lifecycle? | Yes -- exists independently of any task | Continue |

Result: **ObjectType** (`CodebaseModule`)

#### DIAWorkflow

| Question | Answer | Conclusion |
|----------|--------|------------|
| Has unique, stable identifier? | Yes -- composite `{taskId}-dia-{attempt}` | Continue |
| Is persisted? | Yes -- tracked in orchestration-plan and message history | Continue |
| Independently queryable? | Yes -- "how many impacts were rejected?" "show DIA audit" | Strong candidate |
| Participates in relationships? | Yes -- linked to Task, Teammate | Continue |
| Has multiple properties? | Yes -- step, tier, attempt, gcVersion, mode, RC results, challenge | Continue |
| Independent lifecycle? | Yes -- state machine from DIRECTIVE_SENT to terminal state | Continue |

Result: **ObjectType** (`DIAWorkflow`)

### 2.3 Entities Rejected as ObjectTypes

| Candidate | Decision | Rationale |
|-----------|----------|-----------|
| L1 Index | Struct on Task | No independent identity; always accessed via parent Task |
| L2 Summary | Struct on Task | Same as L1 -- artifact metadata, not independent entity |
| L3 Full Detail | File reference (String path) | Directory of files, not a queryable entity |
| RC Checklist Item | Struct on DIAWorkflow | Max 10 items, no independent query need |
| LDAP Challenge | Property on DIAWorkflow | Single challenge per workflow, not independent |
| GC Version Delta | Property on Session | Scalar version number, not an entity |
| Hook Event | Not an entity | Trigger mechanism, not persisted state |
| Context Injection | Step in DIAWorkflow | Part of workflow state machine, not independent |

### 2.4 Primary Key Strategy Summary

| ObjectType | PK Field | PK Type | Strategy |
|------------|----------|---------|----------|
| AgentTeamsSession | sessionId | String (UUID) | System-generated UUID at TeamCreate |
| PipelinePhase | phaseId | String | Composite: `{sessionId}-P{phaseNumber}` |
| AgentTask | taskId | String | Numeric ID from Task API, stored as String |
| AgentTeammate | teammateId | String (UUID) | System-generated UUID at spawn |
| GateRecord | gateId | String | Composite: `{sessionId}-P{phaseNumber}-gate` |
| CodebaseModule | moduleId | String | Deterministic hash of absolute path |
| DIAWorkflow | workflowId | String | Composite: `{taskId}-dia-{attempt}` |

---

## 3. Relationship Discovery Patterns

### 3.1 FK Indicators in Current Agent Teams Infrastructure

| Source Location | FK Pattern Found | Relationship |
|----------------|-----------------|--------------|
| CLAUDE.md Phase Pipeline | Phase belongs to a Session | Session 1:N Phase |
| CLAUDE.md Spawn Matrix | Teammate spawned per Phase | Phase 1:N Teammate |
| task-api-guideline.md Task Storage | Task exists within team scope | Session 1:N Task |
| task-api-guideline.md | Task assigned to teammate (assigneeId) | Task N:1 Teammate |
| orchestration-plan.md | Phase has gate-record.yaml | Phase 1:1 GateRecord |
| CLAUDE.md File Ownership | Task owns file set | Task N:M Module |
| task-api-guideline.md DIA | DIA workflow per task attempt | Task 1:N DIAWorkflow |
| CLAUDE.md DIA Engine | Teammate executes DIA | Teammate 1:N DIAWorkflow |
| CLAUDE.md Phase Pipeline | Task belongs to a Phase | Phase 1:N Task |
| CLAUDE.md GC Tracking | Teammate receives GC version from Session | Session 1:N Teammate |

### 3.2 LinkType Candidates

| LinkType apiName | Source ObjectType | Target ObjectType | Cardinality | Backing Mechanism |
|-----------------|-------------------|-------------------|-------------|-------------------|
| sessionPhases | AgentTeamsSession | PipelinePhase | ONE_TO_MANY | Phase.phaseId embeds sessionId |
| sessionTeammates | AgentTeamsSession | AgentTeammate | ONE_TO_MANY | Teammate scoped to session |
| sessionTasks | AgentTeamsSession | AgentTask | ONE_TO_MANY | Task scoped to team session |
| phaseTasks | PipelinePhase | AgentTask | ONE_TO_MANY | Task created during phase |
| phaseGate | PipelinePhase | GateRecord | ONE_TO_ONE | GateRecord.gateId embeds phaseId |
| taskAssignee | AgentTask | AgentTeammate | MANY_TO_ONE | Task.assigneeId FK |
| taskDIAWorkflows | AgentTask | DIAWorkflow | ONE_TO_MANY | DIAWorkflow.workflowId embeds taskId |
| taskImpactedModules | AgentTask | CodebaseModule | MANY_TO_MANY | Task.fileOwnership array + impact list |
| teammateDIAWorkflows | AgentTeammate | DIAWorkflow | ONE_TO_MANY | DIA assigned to teammate |
| moduleOwner | CodebaseModule | AgentTask | MANY_TO_ONE | Module.ownedBy FK |
| phaseTeammates | PipelinePhase | AgentTeammate | ONE_TO_MANY | Teammate spawned for phase |

### 3.3 Relationship Characteristics from CLAUDE.md

**Hierarchical relationships (tree structure):**
```
Session
  +-- Phase (1-9, ordered)
  |     +-- Task (1-N per phase)
  |     |     +-- DIAWorkflow (1-N per task, for retry attempts)
  |     +-- GateRecord (exactly 1 per phase completion)
  |     +-- Teammate (1-N per phase, by role)
  +-- Module (N, codebase files tracked across session)
```

**Cross-cutting relationships:**
- Task <-> Teammate: assignment (N:1, a task has one assignee, a teammate handles multiple tasks)
- Task <-> Module: impact/ownership (N:M, a task impacts many modules, a module may be impacted by multiple tasks across phases)
- Teammate <-> DIAWorkflow: execution (1:N, a teammate goes through DIA for each task)

### 3.4 Join Dataset Needs

The MANY_TO_MANY relationship `taskImpactedModules` requires either:
- A join dataset with columns `(taskId, moduleId, impactType)` where impactType indicates READ, WRITE, or OWNERSHIP
- Or a Function-based link that resolves the Task.fileOwnership array against Module records

[GAP: The current Agent Teams infrastructure stores file ownership as a flat array of paths on the task. There is no explicit join structure. The bridge will need to decide whether to create a backing join dataset or use Function-based link resolution.]

---

## 4. Mutation Discovery (ActionType Candidates)

### 4.1 DIA Protocol State Changes

The DIA protocol is the richest source of ActionType candidates because it has a well-defined state machine:

| State Transition | ActionType Candidate | Parameters | Preconditions |
|-----------------|---------------------|------------|---------------|
| None -> DIRECTIVE_SENT | sendDirective | taskId, teammateId, gcVersion, injectionMode | Teammate is ACTIVE, task is OPEN |
| DIRECTIVE_SENT -> CONTEXT_RECEIVED | acknowledgeContext | workflowId, acknowledgedVersion | Workflow at DIRECTIVE_SENT |
| CONTEXT_RECEIVED -> IMPACT_SUBMITTED | submitImpactAnalysis | workflowId, analysisContent | Workflow at CONTEXT_RECEIVED |
| IMPACT_SUBMITTED -> RC_REVIEWING | startRCReview | workflowId | Workflow at IMPACT_SUBMITTED |
| RC_REVIEWING -> CHALLENGE_SENT | issueChallenge | workflowId, category, questions | RC review complete, LDAP intensity > NONE |
| CHALLENGE_SENT -> CHALLENGE_RESPONDED | respondToChallenge | workflowId, responseContent | Workflow at CHALLENGE_SENT |
| * -> IMPACT_VERIFIED | verifyImpact | workflowId | RC passed and challenge defended (if applicable) |
| * -> IMPACT_REJECTED | rejectImpact | workflowId, reason | RC failed or challenge failed |
| IMPACT_VERIFIED -> PLAN_SUBMITTED | submitPlan | workflowId, planContent | Workflow at IMPACT_VERIFIED, role is implementer/integrator |
| PLAN_SUBMITTED -> PLAN_APPROVED | approvePlan | workflowId | Plan meets requirements |
| PLAN_SUBMITTED -> PLAN_REJECTED | rejectPlan | workflowId, reason | Plan has issues |

### 4.2 Pipeline State Changes

| State Transition | ActionType Candidate | Parameters | Preconditions |
|-----------------|---------------------|------------|---------------|
| Create new session | createSession | sessionName, workspace | Workspace exists |
| Start a phase | startPhase | sessionId, phaseNumber | Previous phase APPROVED or phaseNumber == 1 |
| Iterate a phase | iteratePhase | sessionId, phaseNumber | Phase status is GATE_REVIEW, iteration < 3 |
| Approve phase gate | approvePhaseGate | gateId, decision, checklist | All checklist items evaluated, no stale contexts |
| Abort phase | abortPhase | sessionId, phaseNumber, reason | Phase is ACTIVE or ITERATING |
| Complete session | completeSession | sessionId | Phase 9 APPROVED |

### 4.3 Teammate Lifecycle Changes

| State Transition | ActionType Candidate | Parameters | Preconditions |
|-----------------|---------------------|------------|---------------|
| Spawn teammate | spawnTeammate | sessionId, role, phaseNumber | Phase is ACTIVE, Gate S-1/S-2/S-3 passed |
| Assign task to teammate | assignTask | taskId, teammateId | Teammate ACTIVE, task OPEN, impact not yet started |
| Report context pressure | reportContextPressure | teammateId | Teammate is ACTIVE |
| Shutdown teammate | shutdownTeammate | teammateId, reason | Teammate is ACTIVE or IDLE |
| Re-spawn teammate | respawnTeammate | sessionId, role, phaseNumber, previousTeammateId | Previous teammate SHUTDOWN or ABORTED, Gate S-3 passed |

### 4.4 ActionType Complexity Classification

| ActionType | Complexity | Implementation Strategy |
|------------|-----------|----------------------|
| createSession | Simple | createObjectRule (single object creation) |
| startPhase | Medium | Built-in rules (create Phase + update Session.currentPhase) |
| spawnTeammate | Medium | Built-in rules + Gate S-1/S-2/S-3 validation |
| sendDirective | Complex | Function rule (creates DIAWorkflow, injects context, handles delta/full mode) |
| submitImpactAnalysis | Medium | modifyObjectRule (update DIAWorkflow.currentStep) |
| verifyImpact | Complex | Function rule (RC checklist evaluation, LDAP challenge logic) |
| approvePhaseGate | Complex | Function rule (cross-impact analysis, staleness check, checklist evaluation) |
| assignTask | Medium | modifyObjectRule (update Task.assigneeId, Task.status) |
| shutdownTeammate | Medium | modifyObjectRule (update status, set terminatedAt) |

---

## 5. Interface Discovery Criteria

### 5.1 Shared Property Pattern Analysis

Scanning all 7 ObjectTypes for identical property subsets:

**Pattern: Timestamped entities**

All 7 ObjectTypes share:
- `createdAt` (or `startedAt` / `spawnedAt` / `evaluatedAt`) -- Timestamp, when entity was created
- `completedAt` (or `terminatedAt`) -- Timestamp, when entity reached terminal state

These have identical semantics: "when did this thing start" and "when did this thing end."

Candidate Interface: `Timestamped`
- SharedProperties: `createdAt` (Timestamp), `completedAt` (Timestamp, optional)
- Implementing: All 7 ObjectTypes

**Pattern: Session-scoped entities**

6 of 7 ObjectTypes (all except Session itself) are scoped to a session:
- Phase, Task, Teammate, GateRecord, Module, DIAWorkflow all logically belong to a Session

However, the FK is implemented differently: Phase embeds sessionId in its composite PK, Task uses team scope, Teammate is spawned within a session, etc. An Interface would need a `sessionId` SharedProperty, which is reasonable.

Candidate Interface: `SessionScoped`
- SharedProperties: `sessionId` (String, FK reference)
- Implementing: PipelinePhase, AgentTask, AgentTeammate, GateRecord, CodebaseModule, DIAWorkflow

**Pattern: Stateful lifecycle entities**

5 ObjectTypes have a `status` property with enum constraints representing lifecycle states:
- Session: INITIALIZING/ACTIVE/PAUSED/COMPLETED/ABORTED
- Phase: PENDING/ACTIVE/ITERATING/GATE_REVIEW/APPROVED/ABORTED
- Task: OPEN/IN_PROGRESS/BLOCKED/REVIEW/COMPLETED/CANCELLED
- Teammate: SPAWNING/ACTIVE/IDLE/CONTEXT_PRESSURE/SHUTDOWN/ABORTED
- DIAWorkflow: (uses `currentStep` instead of `status`, with 11 states)

The enum values differ significantly across types. Creating a shared `status` property with a generic String type is possible but loses the type-safety of enum constraints.

Decision: Do not create a Stateful interface. The semantic differences outweigh the structural similarity.

**Pattern: Auditable entities**

GateRecord and DIAWorkflow both have evaluation/review semantics with `evaluatedBy`/`evaluatedAt` style properties.

Candidate Interface: `Auditable`
- SharedProperties: `evaluatedBy` (String), `evaluatedAt` (Timestamp)
- Implementing: GateRecord, DIAWorkflow

This is marginal (only 2 implementors) but worth creating if audit trail queries across both types are anticipated.

### 5.2 Interface Decision Summary

| Interface Candidate | SharedProperties | Implementors | Decision |
|--------------------|-----------------|-------------|----------|
| Timestamped | createdAt, completedAt | 7 | Create -- universal pattern |
| SessionScoped | sessionId | 6 | Create -- enables cross-type session queries |
| Stateful | status | 5 | Skip -- enum values too divergent |
| Auditable | evaluatedBy, evaluatedAt | 2 | Defer -- evaluate after initial build |

### 5.3 Interface Anti-Patterns Applied

- Single-implementor Interface: None of our candidates have this problem.
- Forcing semantically different properties: The "Stateful" Interface would have this problem, which is why we skip it.
- Coincidental similarity: Module and Task both have `ownedBy`-style properties but with different meanings (file ownership vs task assignment). Not an Interface.

---

## 6. Output Template

The final Ontology decomposition output follows this YAML structure:

```yaml
# Agent Teams Ontology Bridge — Decomposition Output
metadata:
  project_name: "Agent Teams Ontology Bridge"
  source_repository: "park-kyungchan/palantir"
  source_documents:
    - ".claude/CLAUDE.md"
    - ".claude/references/task-api-guideline.md"
    - ".claude/references/agent-common-protocol.md"
  decomposition_date: "2026-02-08"
  decomposition_version: "1.0"

object_types:
  - apiName: "AgentTeamsSession"
    displayName: "Agent Teams Session"
    description: "Root context for an Agent Teams pipeline execution"
    primaryKey: ["sessionId"]
    titleProperty: "sessionName"
    source_entity: "CLAUDE.md §1 Team Identity"
    properties:
      sessionId: { type: "String", required: true }
      sessionName: { type: "String", required: true }
      gcVersion: { type: "Integer", required: true }
      currentPhase: { type: "Integer", required: true }
      status: { type: "String", required: true }
      workspace: { type: "String", required: true }
      createdAt: { type: "Timestamp", required: true }
      completedAt: { type: "Timestamp", required: false }
    status: "ACTIVE"

  - apiName: "PipelinePhase"
    displayName: "Pipeline Phase"
    description: "A stage in the 9-phase Agent Teams pipeline"
    primaryKey: ["phaseId"]
    titleProperty: "phaseName"
    source_entity: "CLAUDE.md §2 Phase Pipeline"
    properties:
      phaseId: { type: "String", required: true }
      phaseNumber: { type: "Integer", required: true }
      phaseName: { type: "String", required: true }
      zone: { type: "String", required: true }
      status: { type: "String", required: true }
      effortLevel: { type: "String", required: true }
      iterationCount: { type: "Integer", required: true }
      teammateRole: { type: "String", required: true }
      startedAt: { type: "Timestamp", required: false }
      completedAt: { type: "Timestamp", required: false }
    status: "ACTIVE"

  - apiName: "AgentTask"
    displayName: "Agent Task"
    description: "A unit of work assigned by Lead to a teammate"
    primaryKey: ["taskId"]
    titleProperty: "subject"
    source_entity: "task-api-guideline.md §3 Task Creation"
    properties:
      taskId: { type: "String", required: true }
      subject: { type: "String", required: true }
      description: { type: "String", required: true }
      status: { type: "String", required: true }
      priority: { type: "Integer", required: true }
      assigneeRole: { type: "String", required: true }
      assigneeId: { type: "String", required: false }
      fileOwnership: { type: "Array<String>", required: false }
      acceptanceCriteria: { type: "Array<String>", required: true }
      impactVerified: { type: "Boolean", required: true }
      createdAt: { type: "Timestamp", required: true }
      completedAt: { type: "Timestamp", required: false }
    status: "ACTIVE"

  - apiName: "AgentTeammate"
    displayName: "Agent Teammate"
    description: "An agent instance spawned to perform work in a specific phase"
    primaryKey: ["teammateId"]
    titleProperty: "teammateName"
    source_entity: "CLAUDE.md §3 Role Protocol + agent .md files"
    properties:
      teammateId: { type: "String", required: true }
      teammateName: { type: "String", required: true }
      role: { type: "String", required: true }
      status: { type: "String", required: true }
      gcVersionReceived: { type: "Integer", required: true }
      diaTier: { type: "Integer", required: true }
      ldapIntensity: { type: "String", required: true }
      impactAttempts: { type: "Integer", required: true }
      spawnedAt: { type: "Timestamp", required: true }
      terminatedAt: { type: "Timestamp", required: false }
      contextPressureReported: { type: "Boolean", required: true }
    status: "ACTIVE"

  - apiName: "GateRecord"
    displayName: "Gate Record"
    description: "Approval record for a phase transition gate"
    primaryKey: ["gateId"]
    titleProperty: "gateName"
    source_entity: "CLAUDE.md §6 Gate Checklist + gate-record.yaml"
    properties:
      gateId: { type: "String", required: true }
      gateName: { type: "String", required: true }
      decision: { type: "String", required: true }
      checklist: { type: "Array<Struct>", required: true }
      gateType: { type: "String", required: true }
      unresolvedIssues: { type: "Array<String>", required: false }
      iterationNumber: { type: "Integer", required: true }
      evaluatedAt: { type: "Timestamp", required: true }
      evaluatedBy: { type: "String", required: true }
    status: "ACTIVE"

  - apiName: "CodebaseModule"
    displayName: "Codebase Module"
    description: "A file or directory tracked in impact analysis"
    primaryKey: ["moduleId"]
    titleProperty: "modulePath"
    source_entity: "CLAUDE.md §5 File Ownership + impact analysis"
    properties:
      moduleId: { type: "String", required: true }
      modulePath: { type: "String", required: true }
      moduleType: { type: "String", required: true }
      lineCount: { type: "Integer", required: false }
      lastModified: { type: "Timestamp", required: false }
      ownedBy: { type: "String", required: false }
      isProtected: { type: "Boolean", required: true }
    status: "ACTIVE"

  - apiName: "DIAWorkflow"
    displayName: "DIA Workflow"
    description: "A Directive-Impact-Analysis protocol chain"
    primaryKey: ["workflowId"]
    titleProperty: "workflowName"
    source_entity: "CLAUDE.md §6 DIA Engine + task-api-guideline.md §11"
    properties:
      workflowId: { type: "String", required: true }
      workflowName: { type: "String", required: true }
      currentStep: { type: "String", required: true }
      tier: { type: "Integer", required: true }
      attempt: { type: "Integer", required: true }
      gcVersionInjected: { type: "Integer", required: true }
      injectionMode: { type: "String", required: true }
      rcCheckResults: { type: "Array<Struct>", required: false }
      challengeCategory: { type: "String", required: false }
      startedAt: { type: "Timestamp", required: true }
      completedAt: { type: "Timestamp", required: false }
    status: "ACTIVE"

link_types:
  - apiName: "sessionPhases"
    source: "AgentTeamsSession"
    target: "PipelinePhase"
    cardinality: "ONE_TO_MANY"
    displayName: "Phases"
    reverseDisplayName: "Session"
    source_relationship: "Phase.phaseId embeds Session.sessionId"

  - apiName: "sessionTeammates"
    source: "AgentTeamsSession"
    target: "AgentTeammate"
    cardinality: "ONE_TO_MANY"
    displayName: "Teammates"
    reverseDisplayName: "Session"

  - apiName: "sessionTasks"
    source: "AgentTeamsSession"
    target: "AgentTask"
    cardinality: "ONE_TO_MANY"
    displayName: "Tasks"
    reverseDisplayName: "Session"

  - apiName: "phaseTasks"
    source: "PipelinePhase"
    target: "AgentTask"
    cardinality: "ONE_TO_MANY"
    displayName: "Tasks"
    reverseDisplayName: "Phase"

  - apiName: "phaseGate"
    source: "PipelinePhase"
    target: "GateRecord"
    cardinality: "ONE_TO_ONE"
    displayName: "Gate"
    reverseDisplayName: "Phase"

  - apiName: "taskAssignee"
    source: "AgentTask"
    target: "AgentTeammate"
    cardinality: "MANY_TO_ONE"
    displayName: "Assignee"
    reverseDisplayName: "Assigned Tasks"
    source_relationship: "AgentTask.assigneeId FK"

  - apiName: "taskDIAWorkflows"
    source: "AgentTask"
    target: "DIAWorkflow"
    cardinality: "ONE_TO_MANY"
    displayName: "DIA Workflows"
    reverseDisplayName: "Task"

  - apiName: "taskImpactedModules"
    source: "AgentTask"
    target: "CodebaseModule"
    cardinality: "MANY_TO_MANY"
    displayName: "Impacted Modules"
    reverseDisplayName: "Impacting Tasks"
    source_relationship: "Task.fileOwnership array (requires join dataset)"

  - apiName: "teammateDIAWorkflows"
    source: "AgentTeammate"
    target: "DIAWorkflow"
    cardinality: "ONE_TO_MANY"
    displayName: "DIA Workflows"
    reverseDisplayName: "Teammate"

  - apiName: "phaseTeammates"
    source: "PipelinePhase"
    target: "AgentTeammate"
    cardinality: "ONE_TO_MANY"
    displayName: "Teammates"
    reverseDisplayName: "Phase"

action_types:
  - apiName: "createSession"
    description: "Initialize a new Agent Teams session"
    parameters: ["sessionName: String", "workspace: String"]
    edit_rules: ["createObjectRule: AgentTeamsSession"]
    source_endpoint: "TeamCreate API"

  - apiName: "startPhase"
    description: "Begin execution of a pipeline phase"
    parameters: ["sessionId: String", "phaseNumber: Integer"]
    edit_rules: ["createObjectRule: PipelinePhase", "modifyObjectRule: AgentTeamsSession.currentPhase"]
    source_endpoint: "Phase transition in orchestration-plan"

  - apiName: "spawnTeammate"
    description: "Spawn a new agent teammate for a phase"
    parameters: ["sessionId: String", "role: String", "phaseNumber: Integer"]
    edit_rules: ["createObjectRule: AgentTeammate"]
    source_endpoint: "Spawn Matrix + Gate S-1/S-2/S-3"

  - apiName: "sendDirective"
    description: "Send directive with context injection to a teammate"
    parameters: ["taskId: String", "teammateId: String", "gcVersion: Integer", "injectionMode: String"]
    function_rule: "sendDirectiveFunction"
    source_endpoint: "DIA Protocol Step 1"

  - apiName: "verifyImpact"
    description: "Evaluate impact analysis against RC checklist and LDAP challenge"
    parameters: ["workflowId: String"]
    function_rule: "verifyImpactFunction"
    source_endpoint: "DIA Protocol Gate A"

  - apiName: "approvePhaseGate"
    description: "Evaluate and approve a phase transition gate"
    parameters: ["gateId: String", "decision: String", "checklist: Array<Struct>"]
    function_rule: "approvePhaseGateFunction"
    source_endpoint: "CLAUDE.md §6 Gate Checklist"

interfaces:
  - apiName: "Timestamped"
    shared_properties: ["createdAt", "completedAt"]
    implementing_types:
      - "AgentTeamsSession"
      - "PipelinePhase"
      - "AgentTask"
      - "AgentTeammate"
      - "GateRecord"
      - "CodebaseModule"
      - "DIAWorkflow"
    source_pattern: "Universal timestamp pattern across all entities"

  - apiName: "SessionScoped"
    shared_properties: ["sessionId"]
    implementing_types:
      - "PipelinePhase"
      - "AgentTask"
      - "AgentTeammate"
      - "GateRecord"
      - "CodebaseModule"
      - "DIAWorkflow"
    source_pattern: "All non-root entities scoped to a session"

automations:
  - name: "On Context Pressure"
    trigger: "object_changed (AgentTeammate.contextPressureReported = true)"
    action: "Read L1/L2/L3 -> shutdownTeammate -> respawnTeammate"
    source_trigger: "CLAUDE.md §9 Lead Response to CONTEXT_PRESSURE"

  - name: "On Teammate Idle"
    trigger: "object_changed (AgentTeammate.status = IDLE)"
    action: "Verify L1/L2 artifacts exist (exit 2 if missing)"
    source_trigger: ".claude/hooks/on-teammate-idle.sh"

  - name: "On Task Completed"
    trigger: "object_changed (AgentTask.status = COMPLETED)"
    action: "Verify L1/L2 artifacts exist, update orchestration-plan"
    source_trigger: ".claude/hooks/on-task-completed.sh"

  - name: "On Subagent Start"
    trigger: "agent_spawned"
    action: "Inject GC version via additionalContext"
    source_trigger: ".claude/hooks/on-subagent-start.sh"

security:
  file_ownership:
    description: "Each implementer owns a non-overlapping file set; only integrator crosses boundaries"
    source: "CLAUDE.md §5 File Ownership Rules"
  protected_files:
    patterns: [".env*", "*credentials*", ".ssh/id_*", "**/secrets/**"]
    source: "CLAUDE.md §8 Safety Rules"
  blocked_commands:
    commands: ["rm -rf", "sudo rm", "chmod 777", "DROP TABLE", "DELETE FROM"]
    source: "CLAUDE.md §8 Safety Rules"
  task_api_rbac:
    lead: ["TaskCreate", "TaskUpdate", "TaskList", "TaskGet"]
    teammate: ["TaskList", "TaskGet"]
    enforcement: "disallowedTools on teammate spawn"
    source: "task-api-guideline.md §2 Ownership Partitioning"
```

---

## 7. Validation Checklist

### 7.1 Decomposition Quality Checks

| ID | Check | Severity | Status | Notes |
|----|-------|----------|--------|-------|
| DEC-VAL-001 | Every ObjectType has exactly one PK property | Error | Pass | All 7 entities have single-field PKs |
| DEC-VAL-002 | Every FK reference has a corresponding LinkType | Warning | Pass | 11 LinkTypes cover all FK patterns found |
| DEC-VAL-003 | Every user-facing mutation has a corresponding ActionType | Warning | Partial | Core mutations covered; some convenience actions may be missing |
| DEC-VAL-004 | Every Interface has at least 2 implementing ObjectTypes | Warning | Pass | Timestamped (7), SessionScoped (6) |
| DEC-VAL-005 | Every sensitive property has a marking or security policy | Warning | Pass | Protected files and blocked commands documented |
| DEC-VAL-006 | All apiNames follow naming conventions | Error | Pass | ObjectTypes PascalCase, properties camelCase, verified |

### 7.2 Agent Teams Domain-Specific Checks

| ID | Check | Severity | Status | Notes |
|----|-------|----------|--------|-------|
| AT-VAL-001 | All 9 pipeline phases representable | Error | Pass | PipelinePhase with phaseNumber 1-9 |
| AT-VAL-002 | All 6 teammate roles representable | Error | Pass | AgentTeammate.role enum covers all 6 |
| AT-VAL-003 | DIA protocol state machine fully captured | Error | Pass | DIAWorkflow.currentStep has 11 states covering full protocol |
| AT-VAL-004 | Gate checklist can hold 5 items | Warning | Pass | Array<Struct> with no size limit beyond Struct field max |
| AT-VAL-005 | L1/L2/L3 artifact tracking possible | Warning | Pass | L1 as Struct array on Task, L3 as file path reference |
| AT-VAL-006 | GC version propagation trackable | Error | Pass | Session.gcVersion + Teammate.gcVersionReceived + DIAWorkflow.gcVersionInjected |
| AT-VAL-007 | File ownership non-overlap enforceable | Warning | Partial | Requires runtime validation via ActionType preconditions |
| AT-VAL-008 | LDAP challenge categories all representable | Warning | Pass | DIAWorkflow.challengeCategory enum has all 7 categories |
| AT-VAL-009 | Compact recovery state reconstructable | Warning | Pass | All state in persistent ObjectTypes; no ephemeral-only data |
| AT-VAL-010 | Max 3 iteration limit enforceable | Warning | Pass | Phase.iterationCount with range constraint + ActionType precondition |

### 7.3 Gaps and Open Questions

| ID | Gap | Impact | Resolution Path |
|----|-----|--------|----------------|
| GAP-001 | taskImpactedModules needs join dataset | Medium | Design join dataset schema during implementation phase |
| GAP-002 | Team Memory (TEAM-MEMORY.md) not modeled as ObjectType | Low | It is a shared file, not a queryable entity; may add later if needed |
| GAP-003 | Orchestration-plan.md is the source of truth but not an ObjectType | Medium | Session + Phase + Task collectively represent its content; evaluate if a dedicated OT is needed |
| GAP-004 | Context delta content (what changed between GC versions) not captured | Low | Could add a `contextDelta` String property to DIAWorkflow |
| GAP-005 | Interface local constraint override behavior unverified | Medium | Need to verify Palantir spec before implementing Stateful interface |

---

## 8. YAML-Based Implementation Architecture

> This section incorporates the implementation architecture from the LLM-Agnostic vs Palantir Ontology
> Architecture document (Section 5.1), adapted for the Agent Teams bridge.

### 8.1 Directory Structure

The YAML-based Ontology registry lives alongside the Agent Teams infrastructure:

```
{workspace}/
├── ontology/
│   ├── objects/                     # ObjectType definitions
│   │   ├── AgentTeamsSession.yaml
│   │   ├── PipelinePhase.yaml
│   │   ├── AgentTask.yaml
│   │   ├── AgentTeammate.yaml
│   │   ├── GateRecord.yaml
│   │   ├── CodebaseModule.yaml
│   │   └── DIAWorkflow.yaml
│   ├── links/                       # LinkType definitions
│   │   ├── session-phases.yaml
│   │   ├── session-teammates.yaml
│   │   ├── session-tasks.yaml
│   │   ├── phase-tasks.yaml
│   │   ├── phase-gate.yaml
│   │   ├── phase-teammates.yaml
│   │   ├── task-assignee.yaml
│   │   ├── task-dia-workflows.yaml
│   │   ├── task-impacted-modules.yaml
│   │   ├── teammate-dia-workflows.yaml
│   │   └── module-owner.yaml
│   ├── actions/                     # ActionType definitions
│   │   ├── createSession.yaml
│   │   ├── startPhase.yaml
│   │   ├── spawnTeammate.yaml
│   │   ├── sendDirective.yaml
│   │   ├── submitImpactAnalysis.yaml
│   │   ├── verifyImpact.yaml
│   │   ├── approvePhaseGate.yaml
│   │   ├── assignTask.yaml
│   │   └── shutdownTeammate.yaml
│   ├── interfaces/                  # Interface definitions
│   │   ├── Timestamped.yaml
│   │   └── SessionScoped.yaml
│   ├── rules/                       # Business rules
│   │   ├── dia-protocol-rules.yaml
│   │   ├── phase-transition-rules.yaml
│   │   └── file-ownership-rules.yaml
│   └── ontology.lock                # Schema version + integrity hash
```

### 8.2 How Agents Consume the Ontology

The architecture from the LLM-Agnostic document applies directly to Agent Teams:

```
                     ┌─────────────────────────┐
                     │    Lead (Orchestrator)   │
                     │    Opus 4.6 instance     │
                     └───────────┬─────────────┘
                                 │
                    Loads ontology/ YAML at session start
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │    ONTOLOGY REGISTRY     │
                     │    ontology/ directory   │
                     │                         │
                     │  ObjectTypes define:     │
                     │    "what exists"         │
                     │  ActionTypes define:     │
                     │    "what can be done"    │
                     │  Rules define:           │
                     │    "what constraints     │
                     │     must hold"           │
                     └─────────┬───────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Implementer  │ │   Tester     │ │  Integrator  │
     │              │ │              │ │              │
     │ Reads OT     │ │ Reads AT     │ │ Reads OT+LT │
     │ definitions  │ │ preconditions│ │ to validate  │
     │ to generate  │ │ to generate  │ │ cross-module │
     │ code         │ │ test cases   │ │ consistency  │
     └──────────────┘ └──────────────┘ └──────────────┘
```

The key insight from the LLM-Agnostic architecture document: the Ontology serves as a "world model" that all agents share. Instead of each agent maintaining its own understanding of the domain through context windows, agents reference the YAML files as the single source of truth.

### 8.3 ActionType YAML Format with Pre/Postconditions

Following the architecture document's pattern for ActionType definitions:

```yaml
# ontology/actions/approvePhaseGate.yaml
actionType:
  name: approvePhaseGate
  description: "Evaluate and record a phase transition gate decision"
  parameters:
    gateId:
      type: ObjectRef<GateRecord>
      required: true
    decision:
      type: String
      required: true
      enum: ["APPROVE", "ITERATE", "ABORT"]
    checklist:
      type: Array<Struct>
      required: true
  preconditions:
    - check: "gate.gateType == 'PHASE_GATE'"
      error: "Can only approve phase-level gates with this action"
    - check: "ALL teammates WHERE gcVersionReceived == session.gcVersion"
      error: "Cannot approve gate while any teammate has stale context"
    - check: "phase.iterationCount < 3 OR decision != 'ITERATE'"
      error: "Maximum 3 iterations reached; must APPROVE or ABORT"
    - check: "ALL checklist items evaluated (no unevaluated items)"
      error: "All checklist items must be evaluated before gate decision"
  sideEffects:
    - "SET gate.decision = ${decision}"
    - "SET gate.evaluatedAt = NOW()"
    - "SET gate.evaluatedBy = 'Lead'"
    - "IF decision == 'APPROVE': SET phase.status = 'APPROVED'"
    - "IF decision == 'ITERATE': SET phase.status = 'ITERATING', INCREMENT phase.iterationCount"
    - "IF decision == 'ABORT': SET phase.status = 'ABORTED'"
  postconditions:
    - check: "gate.decision IN ['APPROVE', 'ITERATE', 'ABORT']"
    - check: "gate.evaluatedAt IS NOT NULL"
    - check: "phase.status reflects decision outcome"
```

This format enables:
1. Lead validates preconditions before executing the action
2. Side effects are deterministic and documented
3. Postconditions can be verified after execution
4. Any agent (researcher, tester) can read these to understand the domain constraints
5. Testers can auto-generate test cases from precondition/postcondition pairs

### 8.4 Schema Versioning

The `ontology.lock` file tracks schema integrity:

```yaml
# ontology/ontology.lock
version: "1.0.0"
last_modified: "2026-02-08T00:00:00Z"
object_types: 7
link_types: 11
action_types: 9
interfaces: 2
integrity_hash: "{sha256 of all YAML files concatenated}"
```

Schema changes follow the Ontology Proposal pattern: any modification to the YAML files requires updating the lock file and notifying all active agents via GC version bump.
