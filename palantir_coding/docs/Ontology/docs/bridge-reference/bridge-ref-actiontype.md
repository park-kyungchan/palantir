# ActionType + Pre/Postconditions Reference -- Agent Teams Bridge Focus

**Version**: 1.0.0 | **Date**: 2026-02-08 | **Consumer**: Opus 4.6 Agent Teams Bridge
**Sources**: `palantir_ontology_3.md` (ActionType/Function/Constraint, 938 lines), `palantir_ontology_7.md` (Function/Automation/Rules/Writeback/AIP, 1380 lines)

---

## 1. ActionType Fundamentals

An **ActionType** is the schema definition of a set of changes or edits to objects, property values, and links that a user can execute as a single atomic transaction. It is "the verb of the Ontology" -- while ObjectTypes define nouns and LinkTypes define relationships, ActionTypes define what can happen.

Key distinction:
- **ActionType**: Schema/template defining what changes are possible
- **Action**: Single execution instance applying the ActionType

All rules within an Action execute atomically (all-or-nothing). If any rule fails, no changes are persisted.

### Rule types (complete list)

| Rule Type | Purpose | Constraint |
|-----------|---------|------------|
| CREATE_OBJECT | Creates new object with required primary key | Must include PK |
| MODIFY_OBJECT | Updates existing object properties | Object must exist |
| CREATE_OR_MODIFY_OBJECT | Upsert pattern based on object reference | -- |
| DELETE_OBJECT | Removes object (links implicitly removed) | Object must exist |
| CREATE_LINK | Creates many-to-many links only | M:N cardinality only |
| DELETE_LINK | Removes many-to-many links only | M:N cardinality only |
| FUNCTION_RULE | Delegates to Ontology Edit Function | Must be the only rule |
| CREATE_OBJECT_OF_INTERFACE | Polymorphic object creation | Via interface |
| MODIFY_OBJECT_OF_INTERFACE | Polymorphic property update | Via interface |
| DELETE_OBJECT_OF_INTERFACE | Polymorphic object deletion | Via interface |

### Value sources for property edits

| Source | Description | Agent Teams Usage |
|--------|-------------|-------------------|
| FROM_PARAMETER | User-provided parameter value | Task description, teammate role |
| OBJECT_PROPERTY | Copy from existing object | Copy phaseId to task |
| STATIC_VALUE | Hardcoded constant | Default status values |
| CURRENT_USER | Authenticated user ID | Lead identity |
| CURRENT_TIME | Execution timestamp | createdAt, assignedAt |

### Simple vs Complex ActionTypes

**Simple (Rule-based)**: Straightforward CRUD operations using built-in rules. No custom logic. Use when the operation is a direct property assignment, object creation, or link management.

**Complex (Function-backed)**: Uses FUNCTION_RULE to delegate to an Ontology Edit Function. Required when business logic involves reading multiple objects, graph traversal, conditional logic, or multi-step operations.

Critical constraint: FUNCTION_RULE must be the **only** rule in an ActionType. It cannot be mixed with other rule types.

---

## 2. Simple Actions (modifyObject)

Use simple rule-based Actions when the operation is a direct property change without conditional logic.

### When to use

- Single object creation with known property values
- Property updates on an existing object
- Link creation/deletion for M:N relationships
- No conditional logic needed beyond submission criteria

### Agent Teams examples

#### terminateTeammate

```yaml
terminateTeammate:
  displayName: "Terminate Teammate"
  complexity: SIMPLE
  parameters:
    - apiName: teammate
      type: OBJECT
      objectType: teammate
      required: true
    - apiName: terminationReason
      type: STRING
      required: true
  rules:
    - ruleType: MODIFY_OBJECT
      objectType: teammate
      propertyEdits:
        - property: status
          valueSource: STATIC_VALUE
          value: "TERMINATED"
        - property: terminatedAt
          valueSource: CURRENT_TIME
        - property: terminationReason
          valueSource: FROM_PARAMETER
          parameter: terminationReason
  submissionCriteria:
    - condition: "teammate.status IS_NOT 'TERMINATED'"
      failureMessage: "Teammate is already terminated"
```

#### rejectImpactAnalysis

```yaml
rejectImpactAnalysis:
  displayName: "Reject Impact Analysis"
  complexity: SIMPLE
  parameters:
    - apiName: workflow
      type: OBJECT
      objectType: diaWorkflow
      required: true
    - apiName: rejectionReason
      type: STRING
      required: true
  rules:
    - ruleType: MODIFY_OBJECT
      objectType: diaWorkflow
      propertyEdits:
        - property: impactAnalysisStatus
          valueSource: STATIC_VALUE
          value: "REJECTED"
        - property: rejectionCount
          valueSource: OBJECT_PROPERTY
          expression: "rejectionCount + 1"
        - property: lastRejectionReason
          valueSource: FROM_PARAMETER
          parameter: rejectionReason
        - property: updatedAt
          valueSource: CURRENT_TIME
  submissionCriteria:
    - condition: "workflow.impactAnalysisStatus IS 'SUBMITTED'"
      failureMessage: "Can only reject a submitted impact analysis"
    - condition: "workflow.rejectionCount IS_LESS_THAN 3"
      failureMessage: "Maximum 3 rejection attempts reached; must abort and re-spawn"
```

[GAP: The Palantir docs describe property edit value sources (FROM_PARAMETER, OBJECT_PROPERTY, STATIC_VALUE, CURRENT_USER, CURRENT_TIME) but do not document an "expression" capability for OBJECT_PROPERTY (e.g., `rejectionCount + 1`). The increment operation may need to be implemented as a FUNCTION_RULE instead of a simple MODIFY_OBJECT rule.]

---

## 3. Complex Actions (Function-Backed)

Use Function-backed Actions when the operation requires reading other objects, conditional branching, graph traversal, or multi-step logic.

### When to use

- Business logic that reads multiple objects to determine changes
- Graph traversal required (e.g., checking predecessor phases)
- Multiple objects must be created/modified in a single transaction
- Conditional logic based on runtime state

### Function rule architecture

A Function-backed Action uses `FUNCTION_RULE` as its sole rule. The Function receives parameters, performs logic, and returns a set of Ontology edits that are applied atomically.

```typescript
type OntologyEdit = Edits.Object<Task> | Edits.Object<DIAWorkflow> | Edits.Object<Teammate>;

export default async function assignTask(
    client: Client,
    task: Osdk.Instance<Task>,
    teammate: Osdk.Instance<Teammate>,
    directiveContent: string
): Promise<OntologyEdit[]> {
    const batch = createEditBatch<OntologyEdit>(client);

    // Create DIAWorkflow backing object
    batch.create(DIAWorkflow, {
        workflowId: `WF-${task.taskId}-${teammate.teammateId}`,
        taskId: task.taskId,
        teammateId: teammate.teammateId,
        impactAnalysisStatus: "NOT_SUBMITTED",
        challengeStatus: "NONE",
        planStatus: "NONE",
        rejectionCount: 0,
        gcVersionAtAssignment: task.gcVersion,
        assignedAt: new Date().toISOString(),
        status: "INITIATED"
    });

    // Update task status
    batch.update(task, {
        status: "ASSIGNED",
        updatedAt: new Date().toISOString()
    });

    // Update teammate status
    batch.update(teammate, {
        status: "ACTIVE",
        updatedAt: new Date().toISOString()
    });

    return batch.getEdits();
}
```

Critical caveat: Search results within an edit function return stale data until the function completes. Use primary key references instead of search for objects created within the same function.

### Agent Teams examples requiring FUNCTION_RULE

#### assignTask

Requires: creating DIAWorkflow object + updating Task status + updating Teammate status atomically. Must verify impact analysis preconditions by reading DIAWorkflow state.

#### approveGate

Requires: reading all tasks in the phase to verify completion, reading all teammate context versions to ensure none are stale, creating GateRecord object, updating Phase status. Multi-object read + multi-object write = FUNCTION_RULE.

#### spawnTeammate

Requires: checking S-1/S-2/S-3 pre-spawn gates by reading existing teammates and tasks, creating Teammate object, potentially creating initial Task objects. Conditional logic based on gate evaluation = FUNCTION_RULE.

---

## 4. Parameter Types

### Complete parameter type list

| Type | Description | Agent Teams Usage |
|------|-------------|-------------------|
| STRING | Text value | Task descriptions, reasons, directive content |
| INTEGER | Whole number | Phase number (1-9), rejection count |
| LONG | Large whole number | -- |
| DOUBLE | Decimal number | -- |
| BOOLEAN | True/false | `impactAnalysisRequired` |
| DATE | Calendar date | -- |
| TIMESTAMP | Date + time | Assignment timestamps |
| OBJECT | Single object reference | `task`, `teammate`, `diaWorkflow` |
| OBJECT_SET | Set of object references | Tasks to evaluate in a gate |
| INTERFACE_REFERENCE | Reference via interface | Any `identifiable` entity |
| ATTACHMENT | File attachment | L3 detail files |
| ARRAY | Ordered collection | List of file paths |
| STRUCT | Nested structure | Challenge question structure |

### Agent Teams parameter examples for each ActionType

| ActionType | Key Parameters | Types |
|-----------|---------------|-------|
| assignTask | task: OBJECT, teammate: OBJECT, directiveContent: STRING | OBJECT + STRING |
| approveGate | phase: OBJECT | OBJECT |
| rejectImpactAnalysis | workflow: OBJECT, rejectionReason: STRING | OBJECT + STRING |
| spawnTeammate | role: STRING, phaseNumber: INTEGER, taskDescription: STRING | STRING + INTEGER |
| terminateTeammate | teammate: OBJECT, terminationReason: STRING | OBJECT + STRING |
| submitImpactAnalysis | workflow: OBJECT, analysisContent: STRING, impactedFiles: ARRAY[STRING] | OBJECT + STRING + ARRAY |
| respondToChallenge | workflow: OBJECT, challengeId: STRING, responseContent: STRING | OBJECT + STRING |
| submitPlan | workflow: OBJECT, planContent: STRING, fileList: ARRAY[STRING] | OBJECT + STRING + ARRAY |

---

## 5. Preconditions -- The Core Value for DIA

Preconditions are the bridge's mechanism for automating what the DIA protocol currently enforces manually. In Palantir Ontology, preconditions are modeled as **submission criteria** -- conditions evaluated before an Action can execute.

### How preconditions work

Submission criteria are evaluated at submission time (before any rules execute). If any criterion fails, the entire Action is blocked and the user sees the failure message.

Criteria can reference:
- **CURRENT_USER**: User ID, group membership, Multipass attributes
- **PARAMETER**: Compare parameter values against each other or against constants
- **OBJECT_PROPERTY** (via parameter): Compare object properties through parameter references

Operators available:

| Category | Operators |
|----------|-----------|
| Single value | IS, IS_NOT, MATCHES, IS_LESS_THAN, IS_GREATER_THAN, IS_LESS_THAN_OR_EQUALS, IS_GREATER_THAN_OR_EQUALS |
| Multi value | INCLUDES, INCLUDES_ANY, IS_INCLUDED_IN, EACH_IS, EACH_IS_NOT |
| Logical | AND, OR, NOT |

### Agent Teams precondition definitions

#### assignTask preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `task.status IS 'CREATED'` | Task must not already be assigned |
| 2 | `teammate.status IS_NOT 'TERMINATED'` | Cannot assign to terminated teammate |
| 3 | `teammate.contextStatus IS 'CURRENT'` | DIA: teammate must have current GC version |
| 4 | `task.phaseId IS_NOT null` | Task must belong to a phase |

[GAP: Submission criteria operate on parameter values and cannot perform complex queries like "does this teammate already have 4+ active tasks?" Such conditions require FUNCTION_RULE logic rather than submission criteria.]

#### approveGate preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `phase.status IS 'ACTIVE'` | Phase must be active |
| 2 | `phase.gateRecord IS null` | Phase must not already have a gate record |

Note: The "all tasks completed" check and "no stale context" check cannot be expressed as simple submission criteria because they require iterating over ObjectSets. These must be implemented as FUNCTION_RULE precondition logic.

#### rejectImpactAnalysis preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `workflow.impactAnalysisStatus IS 'SUBMITTED'` | Can only reject a submitted analysis |
| 2 | `workflow.rejectionCount IS_LESS_THAN 3` | Max 3 attempts before ABORT |

#### spawnTeammate preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `role IS_INCLUDED_IN ['researcher', 'architect', 'devils-advocate', 'implementer', 'tester', 'integrator']` | Valid role types |
| 2 | `phaseNumber IS_GREATER_THAN_OR_EQUALS 1 AND phaseNumber IS_LESS_THAN_OR_EQUALS 9` | Valid phase range |

Note: The S-1 (ambiguity resolution), S-2 (scope feasibility), and S-3 (post-failure divergence) gates require complex logic and must be implemented in the Function rather than as submission criteria.

#### terminateTeammate preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `teammate.status IS_NOT 'TERMINATED'` | Cannot terminate already-terminated teammate |

Note: "No active tasks" check requires querying the teammate's DIAWorkflow links, which is too complex for submission criteria.

#### submitImpactAnalysis preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `workflow.impactAnalysisStatus IS_INCLUDED_IN ['NOT_SUBMITTED', 'REJECTED']` | Can only submit if not yet submitted or previously rejected |

#### respondToChallenge preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `workflow.challengeStatus IS 'CHALLENGED'` | Can only respond to an active challenge |

#### submitPlan preconditions

| # | Condition | Maps to DIA Rule |
|---|-----------|------------------|
| 1 | `workflow.impactAnalysisStatus IS 'VERIFIED'` | DIA: impact must be verified before plan submission (Gate A -> Gate B inviolable) |
| 2 | `workflow.planStatus IS_INCLUDED_IN ['NONE', 'REJECTED']` | Can only submit if not yet submitted or previously rejected |

### Mapping current DIA manual checks to automated preconditions

| Current DIA Manual Check | Automated Precondition |
|--------------------------|----------------------|
| Lead reviews [IMPACT-ANALYSIS] against RC checklist | submitImpactAnalysis creates workflow record; Lead's verifyImpactAnalysis ActionType updates status |
| "Never approve [PLAN] without prior [IMPACT_VERIFIED]" | submitPlan submission criterion: `workflow.impactAnalysisStatus IS 'VERIFIED'` |
| "3x [IMPACT_REJECTED] -> ABORT -> re-spawn" | rejectImpactAnalysis criterion: `rejectionCount IS_LESS_THAN 3`; rejection function auto-triggers ABORT at count 3 |
| "Gates blocked while stale context" | approveGate function checks all teammate contextStatus values |
| "No gate approval while any teammate has stale context" | approveGate function queries ContextAware interface for stale entities |
| Lead tracks per-teammate GC version | ContextAware interface `gcVersion` property on Teammate |
| File ownership: "Two teammates must never edit the same file" | assignTask function verifies no file overlap between task file sets |

---

## 6. Postconditions -- Automated Verification

Postconditions in the Agent Teams bridge verify that the system reached the expected state after an Action executed. While Palantir's Ontology does not have a native "postcondition" primitive, the bridge achieves postcondition verification through two mechanisms:

1. **Automation triggers** (OBJECT_SET conditions): React to state changes and verify correctness
2. **Side-effect webhooks**: Notify external systems (or the Lead) of completed Actions

### How postconditions work in practice

After an ActionType executes its rules atomically, the resulting object modifications trigger any configured Automations whose OBJECT_SET conditions match. These Automations can then:
- Run verification Actions
- Send notifications
- Execute fallback logic on failure

### Agent Teams postcondition definitions

#### assignTask postconditions

| Verification | Mechanism |
|-------------|-----------|
| DIAWorkflow object exists with correct task/teammate references | Automation: OBJECTS_ADDED on DIAWorkflow triggers verification function |
| Task status is ASSIGNED | Verified in the atomic transaction (same function creates workflow + updates task) |
| Teammate status is ACTIVE | Verified in the atomic transaction |
| GC version recorded on workflow matches current GC | Verified in the function logic before commit |

#### approveGate postconditions

| Verification | Mechanism |
|-------------|-----------|
| GateRecord object exists with APPROVED status | Automation: OBJECTS_ADDED on GateRecord triggers next-phase activation |
| Next phase status transitions to ACTIVE | Automation effect: modifyObject on successor phase via Phase precedence link |
| All L1/L2 artifacts exist for the phase | Verification function checks artifact existence before approving gate |

#### rejectImpactAnalysis postconditions

| Verification | Mechanism |
|-------------|-----------|
| Workflow rejection count incremented | Atomic in MODIFY_OBJECT rule |
| If count reaches 3: teammate status -> ABORTED | Automation: OBJECTS_MODIFIED on DIAWorkflow, condition: rejectionCount = 3 |
| Re-spawn notification sent to Lead | Automation: NOTIFICATION effect when ABORT triggered |

### Mapping current gate checklist to automated postconditions

| Gate Checklist Item | Automated Postcondition |
|--------------------|----------------------|
| "All phase output artifacts exist" | Verification function checks L1/L2/L3 file existence via Task->File links |
| "Quality meets next-phase entry conditions" | Verification function evaluates quality criteria per phase type |
| "No unresolved critical issues" | Query: all Tasks in phase have status COMPLETED (no FAILED) |
| "No inter-teammate conflicts" | Query: no file ownership overlaps across Task->File links |
| "L1/L2/L3 generated" | Query: each teammate's task has associated L1, L2, L3 files |

---

## 7. Logic & Automation Patterns (from ontology_7)

### Function types relevant to ActionType implementation

| Function Type | When to Use | Agent Teams Application |
|--------------|-------------|------------------------|
| Ontology Edit Function (TypeScript v2) | Complex write operations | assignTask, approveGate, spawnTeammate |
| Query Function | Read-only validation | Circular dependency check for Phase precedence, file ownership conflict detection |
| AIP Logic Function | LLM-based evaluation | Impact analysis quality scoring, challenge question generation |

Key patterns for Agent Teams Functions:

**Pattern 1: Multi-object atomic edit**
```typescript
type OntologyEdit = Edits.Object<Task> | Edits.Object<DIAWorkflow> | Edits.Object<Teammate>;
// Single function creates/modifies multiple objects atomically
```

**Pattern 2: Graph traversal for validation**
```typescript
// Check all tasks in a phase are completed (max 3 searchAround operations)
const tasks = await phase.$link.tasks.all();
const allCompleted = tasks.every(t => t.status === "COMPLETED");
```

**Pattern 3: Circular dependency detection**
```typescript
// Prevent cycles in Phase precedence DAG or Module dependency graph
// Same pattern as K-12 detectCircularPrerequisites
const visited = new Set<string>();
const stack = [targetPhase.$primaryKey];
while (stack.length > 0) { /* BFS/DFS cycle detection */ }
```

### Automation triggers that map to Agent Teams hooks

The Agent Teams infrastructure uses shell hooks (`.claude/hooks/`) to enforce behavior. These map directly to Palantir Automation conditions:

| Agent Teams Hook | Automation Condition | Effect |
|-----------------|---------------------|--------|
| `on-subagent-start.sh` | OBJECTS_ADDED on Teammate (status: SPAWNED) | ACTION: inject GC version context |
| `on-task-completed.sh` | OBJECTS_MODIFIED on Task (status -> COMPLETED) | ACTION: verify L1/L2 existence; NOTIFICATION to Lead |
| `on-teammate-idle.sh` | OBJECTS_MODIFIED on Teammate (status -> IDLE) | ACTION: verify L1/L2 existence; NOTIFICATION to Lead |
| `on-session-compact.sh` | OBJECTS_MODIFIED on Session (contextPressure: true) | ACTION: trigger context save; NOTIFICATION to Lead |
| `on-tool-failure.sh` | [GAP: No direct Ontology equivalent] | FALLBACK effect on Action failure |
| `on-pre-compact.sh` | [GAP: Proactive context pressure detection has no Ontology equivalent] | Would require THRESHOLD_CROSSED on a "contextUsage" metric |
| `on-task-update.sh` | OBJECTS_MODIFIED on Task (any property change) | ACTION: update parent Phase progress |

### Hook to Automation mapping table

| Hook | Trigger Type | Condition | Effect Type | Action/Notification |
|------|-------------|-----------|-------------|---------------------|
| on-subagent-start | OBJECTS_ADDED | Teammate.status = SPAWNED | ACTION | injectContext (assigns GC version) |
| on-task-completed | OBJECTS_MODIFIED | Task.status changed to COMPLETED | ACTION + NOTIFICATION | verifyArtifacts + notify Lead |
| on-teammate-idle | OBJECTS_MODIFIED | Teammate.status changed to IDLE | ACTION + NOTIFICATION | verifyArtifacts + notify Lead |
| on-session-compact | OBJECTS_MODIFIED | Session.contextPressure = true | ACTION | triggerContextSave |
| on-task-update | OBJECTS_MODIFIED | Task.updatedAt changed | ACTION | updatePhaseProgress |

Automation execution modes relevant to Agent Teams:

| Mode | Description | Use Case |
|------|-------------|----------|
| ONCE_ALL | Execute once for entire ObjectSet | Phase-level aggregation (e.g., calculate phase completion %) |
| ONCE_BATCH | Execute once per batch | Batch teammate context refresh |
| ONCE_EACH_GROUP | Execute once per group | Per-task artifact verification |

Important anti-pattern: **Infinite Automation Loop** (AUTO-ANTI-001). If an Automation modifies an object that triggers another Automation, it can create infinite cycles. For Agent Teams, ensure that status update Automations check a "processedByAutomation" flag to break cycles.

---

## 8. Agent Teams ActionType Mapping

### 8.1 assignTask

| Field | Value |
|-------|-------|
| apiName | `assignTask` |
| displayName | Assign Task to Teammate |
| complexity | COMPLEX (FUNCTION_RULE) |
| objectTypes | `[task, teammate, diaWorkflow]` |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| task | OBJECT (task) | yes | -- |
| teammate | OBJECT (teammate) | yes | -- |
| directiveContent | STRING | yes | -- |
| gcVersion | INTEGER | yes | Must match current GC version |

Preconditions (submission criteria):
- task.status IS "CREATED"
- teammate.status IS_NOT "TERMINATED"
- teammate.contextStatus IS "CURRENT"

Function logic:
1. Verify no file ownership conflicts with other active tasks
2. Create DIAWorkflow object with INITIATED status
3. Update task status to ASSIGNED
4. Update teammate status to ACTIVE
5. Record gcVersion on DIAWorkflow

Postconditions (verified by Automation):
- DIAWorkflow exists linking task and teammate
- Task status is ASSIGNED
- Teammate status is ACTIVE

Side effects:
- Automation: OBJECTS_ADDED on DIAWorkflow triggers context injection notification

### 8.2 approveGate

| Field | Value |
|-------|-------|
| apiName | `approveGate` |
| displayName | Approve Phase Gate |
| complexity | COMPLEX (FUNCTION_RULE) |
| objectTypes | `[phase, gateRecord, task, teammate]` |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| phase | OBJECT (phase) | yes | -- |
| decision | STRING | yes | ONE_OF: APPROVE, ITERATE, ABORT |
| notes | STRING | no | -- |

Preconditions:
- phase.status IS "ACTIVE"

Function logic:
1. Query all tasks in phase; verify all COMPLETED (or handle ITERATE/ABORT)
2. Query all teammates with active context; verify none STALE
3. Verify L1/L2 artifacts exist for each task
4. Create GateRecord object with decision
5. If APPROVE: update phase status to COMPLETED; activate successor phases via precedence links
6. If ITERATE: increment iteration count (max 3); keep phase ACTIVE
7. If ABORT: update phase status to ABORTED; terminate affected teammates

Postconditions:
- GateRecord exists with recorded decision
- If APPROVE: successor phases have status ACTIVE
- All L1/L2 artifacts verified

Side effects:
- Automation: OBJECTS_ADDED on GateRecord triggers phase transition notifications

### 8.3 rejectImpactAnalysis

| Field | Value |
|-------|-------|
| apiName | `rejectImpactAnalysis` |
| displayName | Reject Impact Analysis |
| complexity | SIMPLE (MODIFY_OBJECT) or COMPLEX if auto-ABORT needed |
| objectTypes | `[diaWorkflow]` (or `[diaWorkflow, teammate]` if auto-ABORT) |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| workflow | OBJECT (diaWorkflow) | yes | -- |
| rejectionReason | STRING | yes | -- |

Preconditions:
- workflow.impactAnalysisStatus IS "SUBMITTED"
- workflow.rejectionCount IS_LESS_THAN 3

Function logic (if COMPLEX):
1. Increment rejectionCount
2. Set impactAnalysisStatus to REJECTED
3. Record rejection reason and timestamp
4. If rejectionCount reaches 3: set workflow status to ABORTED; set teammate status to TERMINATED

Postconditions:
- Workflow status updated
- If count = 3: Automation triggers re-spawn notification

### 8.4 spawnTeammate

| Field | Value |
|-------|-------|
| apiName | `spawnTeammate` |
| displayName | Spawn Teammate |
| complexity | COMPLEX (FUNCTION_RULE) |
| objectTypes | `[teammate]` |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| role | STRING | yes | ONE_OF: researcher, architect, devils-advocate, implementer, tester, integrator |
| phaseNumber | INTEGER | yes | RANGE: 1-9 |
| taskDescription | STRING | yes | -- |
| gcVersion | INTEGER | yes | Current GC version |

Preconditions:
- role IS_INCLUDED_IN valid roles list
- phaseNumber RANGE 1-9

Function logic:
1. Gate S-1: Verify requirements are not ambiguous (may require human input)
2. Gate S-2: Verify scope is feasible (< 4 files per teammate)
3. Gate S-3: If re-spawn after failure, verify approach differs from previous
4. Create Teammate object with SPAWNED status
5. Set gcVersion and contextStatus to CURRENT

Postconditions:
- Teammate object exists with SPAWNED status
- Automation: OBJECTS_ADDED triggers on-subagent-start hook equivalent

[GAP: Gates S-1, S-2, and S-3 involve qualitative judgments (is the requirement ambiguous? does the approach differ from the previous failure?) that cannot be fully automated as submission criteria. These may benefit from AIP Logic functions for LLM-based evaluation.]

### 8.5 terminateTeammate

| Field | Value |
|-------|-------|
| apiName | `terminateTeammate` |
| displayName | Terminate Teammate |
| complexity | COMPLEX (FUNCTION_RULE) -- needs to check active tasks |
| objectTypes | `[teammate, diaWorkflow]` |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| teammate | OBJECT (teammate) | yes | -- |
| terminationReason | STRING | yes | -- |

Preconditions:
- teammate.status IS_NOT "TERMINATED"

Function logic:
1. Query all active DIAWorkflows for this teammate
2. Verify no workflows in IN_PROGRESS state (or handle gracefully)
3. Update teammate status to TERMINATED
4. Record termination reason and timestamp

Postconditions:
- Teammate status is TERMINATED
- No active workflows remain

### 8.6 submitImpactAnalysis

| Field | Value |
|-------|-------|
| apiName | `submitImpactAnalysis` |
| displayName | Submit Impact Analysis |
| complexity | SIMPLE (MODIFY_OBJECT) |
| objectTypes | `[diaWorkflow]` |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| workflow | OBJECT (diaWorkflow) | yes | -- |
| analysisContent | STRING | yes | -- |
| impactedFiles | ARRAY[STRING] | yes | -- |

Preconditions:
- workflow.impactAnalysisStatus IS_INCLUDED_IN ["NOT_SUBMITTED", "REJECTED"]

Rules:
```yaml
- ruleType: MODIFY_OBJECT
  objectType: diaWorkflow
  propertyEdits:
    - property: impactAnalysisStatus
      valueSource: STATIC_VALUE
      value: "SUBMITTED"
    - property: analysisContent
      valueSource: FROM_PARAMETER
      parameter: analysisContent
    - property: impactedFiles
      valueSource: FROM_PARAMETER
      parameter: impactedFiles
    - property: updatedAt
      valueSource: CURRENT_TIME
```

Postconditions:
- Workflow impactAnalysisStatus is SUBMITTED
- Automation: OBJECTS_MODIFIED on DIAWorkflow triggers Lead notification for review

### 8.7 respondToChallenge

| Field | Value |
|-------|-------|
| apiName | `respondToChallenge` |
| displayName | Respond to LDAP Challenge |
| complexity | SIMPLE (MODIFY_OBJECT) |
| objectTypes | `[diaWorkflow]` |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| workflow | OBJECT (diaWorkflow) | yes | -- |
| challengeId | STRING | yes | -- |
| responseContent | STRING | yes | -- |
| evidenceReferences | ARRAY[STRING] | no | File paths or references supporting the response |

Preconditions:
- workflow.challengeStatus IS "CHALLENGED"

Rules:
```yaml
- ruleType: MODIFY_OBJECT
  objectType: diaWorkflow
  propertyEdits:
    - property: challengeStatus
      valueSource: STATIC_VALUE
      value: "DEFENDED"
    - property: challengeResponseContent
      valueSource: FROM_PARAMETER
      parameter: responseContent
    - property: updatedAt
      valueSource: CURRENT_TIME
```

Postconditions:
- Workflow challengeStatus is DEFENDED
- Automation: Lead reviews defense and either approves (sets to DEFENDED) or rejects (sets to FAILED, which triggers IMPACT_REJECTED)

[GAP: The challenge defense evaluation is a judgment call by the Lead. An AIP Logic function could assist by scoring the response quality, but the final approval remains manual.]

### 8.8 submitPlan

| Field | Value |
|-------|-------|
| apiName | `submitPlan` |
| displayName | Submit Implementation Plan |
| complexity | SIMPLE (MODIFY_OBJECT) |
| objectTypes | `[diaWorkflow]` |

Parameters:

| Parameter | Type | Required | Constraints |
|-----------|------|----------|-------------|
| workflow | OBJECT (diaWorkflow) | yes | -- |
| planContent | STRING | yes | -- |
| fileList | ARRAY[STRING] | yes | Files that will be created/modified |

Preconditions:
- workflow.impactAnalysisStatus IS "VERIFIED" (Gate A -> Gate B inviolable)
- workflow.planStatus IS_INCLUDED_IN ["NONE", "REJECTED"]

Rules:
```yaml
- ruleType: MODIFY_OBJECT
  objectType: diaWorkflow
  propertyEdits:
    - property: planStatus
      valueSource: STATIC_VALUE
      value: "SUBMITTED"
    - property: planContent
      valueSource: FROM_PARAMETER
      parameter: planContent
    - property: plannedFiles
      valueSource: FROM_PARAMETER
      parameter: fileList
    - property: updatedAt
      valueSource: CURRENT_TIME
```

Postconditions:
- Workflow planStatus is SUBMITTED
- Automation: Lead notification for plan review

---

## 9. Validation Rules (Bridge-Relevant)

### ActionType validation rules

| Rule ID | Name | Condition | Severity | Agent Teams Impact |
|---------|------|-----------|----------|-------------------|
| ACT-VAL-001 | API Name Format | `apiName` matches `^[a-z][a-zA-Z0-9]*$` | ERROR | All 8 ActionTypes: assignTask, approveGate, etc. |
| ACT-VAL-002 | Forbidden Words | apiName cannot include: ontology, object, property, link, relation, rid, primaryKey, typeId | ERROR | None of the 8 ActionTypes use forbidden words |
| ACT-VAL-003 | Function Rule Exclusivity | FUNCTION_RULE must be the only rule when present | ERROR | assignTask, approveGate, spawnTeammate, terminateTeammate use FUNCTION_RULE exclusively |
| ACT-VAL-004 | Primary Key Required | CREATE_OBJECT must include primary key | ERROR | DIAWorkflow, GateRecord, Teammate creation must provide PK |
| ACT-VAL-005 | Link Cardinality | CREATE_LINK/DELETE_LINK only for M:N | ERROR | Module<->Module and Phase<->Phase link management only |

### Function validation rules

| Rule ID | Name | Condition | Severity | Agent Teams Impact |
|---------|------|-----------|----------|-------------------|
| FUNC-VAL-001 | API Name Format | camelCase | ERROR | All function names |
| FUNC-VAL-002 | Edits Declaration | Edit functions must declare @Edits with ObjectTypes | ERROR | All FUNCTION_RULE functions must declare edited types |
| FUNC-VAL-003 | Search Around Limit | Max 3 searchAround calls per function | ERROR | approveGate traverses Phase->Tasks, Phase->Teammates, Phase->GateRecord -- exactly 3 |
| FUNC-VAL-004 | Query No Side Effects | @Query functions must not modify state | ERROR | Validation queries (circular dependency check) must be read-only |
| FUNC-VAL-005 | Function Rule Exclusivity | FUNCTION_RULE must be the only rule | ERROR | Same as ACT-VAL-003 |

### Constraint validation rules

| Rule ID | Name | Condition | Severity | Agent Teams Impact |
|---------|------|-----------|----------|-------------------|
| CONS-VAL-001 | Type Compatibility | Constraint type valid for property base type | ERROR | RANGE on INTEGER (phaseNumber), ONE_OF on STRING (role, status) |
| CONS-VAL-002 | Range Bounds | gte <= lte when both specified | ERROR | phaseNumber: 1-9, rejectionCount: 0-3 |
| CONS-VAL-003 | Failure Message Required | All constraints should have custom failure messages | WARNING | All submission criteria should include descriptive messages |

---

## 10. Anti-Patterns to Avoid

### ActionType anti-patterns

| ID | Name | Agent Teams Warning |
|----|------|-------------------|
| ACT-ANTI-001 | Mixing FUNCTION_RULE with Other Rules | assignTask must use FUNCTION_RULE alone. Do not add a MODIFY_OBJECT rule alongside the FUNCTION_RULE for updating task status -- the function handles everything. |
| ACT-ANTI-002 | Using CREATE_LINK for FK Links | Session->Phase is FK-backed. Do not use CREATE_LINK to add phases to a session. Instead use MODIFY_OBJECT to set the phaseId property on the Phase object. CREATE_LINK is only for M:N join-table-backed links (Module<->Module, Phase<->Phase). |

### Function anti-patterns

| ID | Name | Agent Teams Warning |
|----|------|-------------------|
| FUNC-ANTI-001 | Search After Edit | In assignTask, do not search for the just-created DIAWorkflow. Use its primary key reference directly. Search APIs return stale data until the function completes. |
| FUNC-ANTI-002 | Missing Edits Declaration | The assignTask function must declare `@Edits(Task, Teammate, DIAWorkflow)` or equivalent TypeScript v2 type declaration. |
| FUNC-ANTI-003 | Side Effects in Query | The circular dependency detection function (for Phase precedence or Module dependencies) must be a @Query function with no mutations. |

### Constraint anti-patterns

| ID | Name | Agent Teams Warning |
|----|------|-------------------|
| CONS-ANTI-001 | Missing Failure Messages | Every submission criterion must have a descriptive failure message. "Validation failed" is useless; "Can only reject a submitted impact analysis" is actionable. |
| CONS-ANTI-002 | Overly Permissive Constraints | Do not use `otherValuesAllowed: true` on the role ONE_OF constraint. There are exactly 6 valid roles; no others should be accepted. |

### Automation anti-patterns

| ID | Name | Agent Teams Warning |
|----|------|-------------------|
| AUTO-ANTI-001 | Infinite Loop | If approveGate Automation modifies successor Phase status, and that triggers another Automation that modifies the Phase, you get infinite cycles. Add a `processedByAutomation` flag. |
| AUTO-ANTI-002 | No Fallback | Every ACTION effect Automation should have a FALLBACK with at least a NOTIFICATION. If the verifyArtifacts Action fails, the Lead must be notified. |
| AUTO-ANTI-003 | Overly Broad Trigger | Do not trigger on all OBJECTS_MODIFIED on Task without filters. Filter to specific property changes (e.g., status changed to COMPLETED). |

---

## 11. Forward-Compatibility Notes

### Impact on Bridge Integration design

**ActionType complexity distribution:**
- 4 Complex (FUNCTION_RULE): assignTask, approveGate, spawnTeammate, terminateTeammate
- 4 Simple (MODIFY_OBJECT): rejectImpactAnalysis, submitImpactAnalysis, respondToChallenge, submitPlan
- Note: rejectImpactAnalysis may need to be promoted to COMPLEX if auto-ABORT at count 3 is required in the same transaction.

**Submission criteria limitations:**
- Cannot query ObjectSets (e.g., "all tasks in phase completed")
- Cannot perform graph traversal
- Cannot compare against dynamic values (e.g., "current GC version")
- These limitations push most DIA enforcement into FUNCTION_RULE logic

**AIP Logic integration opportunities:**
- Impact analysis quality scoring: An AIP Logic function could evaluate the completeness of a submitted impact analysis against the RC checklist.
- Challenge question generation: An AIP Logic function could generate LDAP challenge questions based on the task context and known risk categories.
- Plan quality assessment: An AIP Logic function could score plan completeness.
- These would be @Query functions called within FUNCTION_RULE implementations.

**Automation as the DIA enforcement backbone:**
- The 7 Agent Teams hooks map directly to Automation conditions.
- Automations provide the reactive layer that current hooks provide.
- The key difference: Automations operate on Ontology state changes (typed, queryable), while hooks operate on shell events (untyped, ephemeral).
- Migration path: each hook becomes an Automation with equivalent trigger and effect.

**Writeback considerations:**
- If Agent Teams state needs to be synchronized to external systems (e.g., a dashboard, a monitoring system), use side-effect webhooks on key ActionTypes (assignTask, approveGate).
- For critical external calls (e.g., notifying a CI/CD system on gate approval), use writeback webhooks (blocking, guaranteed execution).
- Limit: one writeback webhook per ActionType; multiple side-effect webhooks allowed.

**Versioning strategy:**
- ActionType definitions should be managed through the Ontology proposal workflow.
- Breaking changes (parameter type changes, rule modifications) require migration approval.
- Non-breaking additions (new optional parameters, new submission criteria) can be deployed incrementally.
- The bridge should version its ActionTypes with the same monotonic versioning used for GC (GC-v{N}).

[GAP: The Palantir docs do not describe a mechanism for "conditional side effects" -- e.g., only send a webhook if the gate decision is APPROVE but not ITERATE. The bridge may need to handle this routing in the FUNCTION_RULE logic before applying the final edits.]

[GAP: The Palantir docs describe Automation retry policies (CONSTANT, EXPONENTIAL) but do not specify what happens when all retries fail for an ACTION effect without a FALLBACK. The bridge should always configure FALLBACK effects for critical Automations.]
