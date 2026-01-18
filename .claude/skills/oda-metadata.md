---
name: oda-metadata
description: |
  Metadata definition management with 6-Stage Lifecycle Protocol.
  Polymorphic schema with $type discriminator pattern (5 variants).
  Schema source: ontology_definition/schemas/Metadata.schema.json
  Implements: classify -> define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
context: fork
agent: general-purpose
intents:
  korean: ["메타데이터", "감사로그", "변경세트", "내보내기", "제안"]
  english: ["metadata", "audit log", "changeset", "export", "proposal"]
---

# ODA Metadata Skill

## Purpose

Manage Metadata definitions following 6-Stage Lifecycle (extended for polymorphic $type):
0. **CLASSIFY** - Determine $type variant from user intent
1. **DEFINE** - Collect $type-specific specification
2. **VALIDATE** - Verify against JSON Schema with discriminator
3. **STAGE** - Preview before deployment
4. **REVIEW** - Human approval gate
5. **DEPLOY** - Persist to ontology database

---

## Schema Reference

**Location:** `/home/palantir/park-kyungchan/palantir/ontology_definition/schemas/Metadata.schema.json`

### $type Discriminator Pattern

Metadata uses a polymorphic `$type` field to select one of 5 variants:

```json
{
  "$type": "OntologyMetadata | AuditLog | ChangeSet | ExportMetadata | ProposalMetadata"
}
```

**oneOf Resolution:** The `$type` field determines which variant schema applies.

---

## Variant 1: OntologyMetadata

Top-level metadata for the entire Ontology schema.

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `$type` | `"OntologyMetadata"` | `"OntologyMetadata"` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` | `ODAEnterprise` |
| `displayName` | String (1-255) | `ODA Enterprise Ontology` |
| `schemaVersion` | `^\d+\.\d+\.\d+$` | `4.0.0` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `ontologyRid` | String (pattern) | `ri.ontology.main.<apiName>` |
| `description` | String | Ontology documentation |
| `stats` | OntologyStats | Type counts |
| `governance` | GovernanceConfig | Access control |
| `serviceVersion` | Enum | `OSv1` or `OSv2` (default) |
| `version` | Integer (readOnly) | Auto-incremented |
| `createdAt/By` | DateTime/String (readOnly) | Auto-populated |
| `modifiedAt/By` | DateTime/String (readOnly) | Auto-updated |

### OntologyStats

```json
{
  "objectTypeCount": 25,
  "linkTypeCount": 18,
  "actionTypeCount": 45,
  "interfaceCount": 5,
  "valueTypeCount": 12,
  "structTypeCount": 8,
  "sharedPropertyCount": 15,
  "activeObjectTypeCount": 22,
  "deprecatedObjectTypeCount": 3
}
```

### GovernanceConfig

```json
{
  "owner": "ontology-team",
  "editors": ["dev-team", "data-team"],
  "viewers": ["all-employees"],
  "proposalRequired": true,
  "endorsementEnabled": true
}
```

### Example

```json
{
  "$type": "OntologyMetadata",
  "ontologyRid": "ri.ontology.main.oda-enterprise",
  "apiName": "ODAEnterprise",
  "displayName": "ODA Enterprise Ontology",
  "description": "Main enterprise ontology for the ODA system.",
  "schemaVersion": "4.0.0",
  "serviceVersion": "OSv2",
  "stats": {
    "objectTypeCount": 25,
    "linkTypeCount": 18
  },
  "governance": {
    "owner": "ontology-team",
    "proposalRequired": true
  }
}
```

---

## Variant 2: AuditLog

Immutable audit log entry tracking who/what/when/why for all changes.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `$type` | `"AuditLog"` | Discriminator |
| `logId` | UUID | Unique identifier |
| `timestamp` | DateTime | When operation occurred |
| `operationType` | Enum (12) | Type of operation |
| `actor` | ActorInfo | Who performed |
| `target` | TargetInfo | What was affected |

### operationType Enum (12 Types)

| Operation | Category | Description |
|-----------|----------|-------------|
| `CREATE` | CRUD | Create new entity |
| `READ` | CRUD | Access entity data |
| `UPDATE` | CRUD | Modify entity |
| `DELETE` | CRUD | Remove entity |
| `LINK` | Relationship | Create link between objects |
| `UNLINK` | Relationship | Remove link |
| `EXECUTE` | Action | Execute ActionType |
| `APPROVE` | Workflow | Approve proposal |
| `REJECT` | Workflow | Reject proposal |
| `TRANSITION` | FSM | State transition |
| `EXPORT` | Transfer | Export ontology |
| `IMPORT` | Transfer | Import ontology |

### ActorInfo

```json
{
  "actorType": "USER | AGENT | SYSTEM | SERVICE",
  "actorId": "user-123",
  "actorName": "John Doe",
  "roles": ["Developer", "Ontology Editor"],
  "permissions": ["ontology:edit", "object:create"]
}
```

**actorType Values:**
- `USER` - Human user
- `AGENT` - AI agent (Claude, etc.)
- `SYSTEM` - Automated system process
- `SERVICE` - External service

### TargetInfo

```json
{
  "targetType": "OBJECT | LINK | OBJECT_TYPE | LINK_TYPE | ACTION_TYPE | PROPERTY | ONTOLOGY | PROPOSAL",
  "targetRid": "ri.ontology.main.object.Employee.emp-456",
  "targetApiName": "updateEmployeeInfo",
  "objectTypeApiName": "Employee",
  "primaryKey": "emp-456"
}
```

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `actionRef` | String | ActionType apiName (if action) |
| `proposalRef` | String | Proposal ID (if approved action) |
| `reason` | String | User-provided reason |
| `beforeState` | Object | State before change |
| `afterState` | Object | State after change |
| `changes` | PropertyChange[] | Detailed property changes |
| `success` | Boolean | Operation succeeded (default: true) |
| `errorMessage` | String | Error message if failed |
| `correlationId` | String | Link related entries |
| `sessionId` | String | Actor session |
| `ipAddress` | IPv4 | Actor IP |

### PropertyChange

```json
{
  "propertyApiName": "department",
  "oldValue": "Engineering",
  "newValue": "Product",
  "changeType": "SET | UNSET | APPEND | REMOVE | REPLACE"
}
```

### Example

```json
{
  "$type": "AuditLog",
  "logId": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-18T10:30:00Z",
  "operationType": "UPDATE",
  "actor": {
    "actorType": "USER",
    "actorId": "user-123",
    "actorName": "John Doe",
    "roles": ["Developer"]
  },
  "target": {
    "targetType": "OBJECT",
    "objectTypeApiName": "Employee",
    "primaryKey": "emp-456"
  },
  "actionRef": "updateEmployeeInfo",
  "reason": "Correcting department assignment",
  "beforeState": { "department": "Engineering" },
  "afterState": { "department": "Product" },
  "changes": [{
    "propertyApiName": "department",
    "oldValue": "Engineering",
    "newValue": "Product",
    "changeType": "SET"
  }],
  "success": true
}
```

---

## Variant 3: ChangeSet

Collection of changes applied together (transaction-like).

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `$type` | `"ChangeSet"` | Discriminator |
| `changeSetId` | UUID | Unique identifier |
| `timestamp` | DateTime | When created |
| `actor` | ActorInfo | Who created |
| `operations` | ChangeOperation[] | Operations (minItems: 1) |

### ChangeOperation

```json
{
  "operationType": "CREATE_OBJECT_TYPE | MODIFY_OBJECT_TYPE | DELETE_OBJECT_TYPE | ...",
  "targetApiName": "Employee",
  "payload": { ... },
  "sequenceNumber": 0
}
```

### operationType Enum (17 Types)

| Category | Operations |
|----------|------------|
| ObjectType | `CREATE_OBJECT_TYPE`, `MODIFY_OBJECT_TYPE`, `DELETE_OBJECT_TYPE` |
| LinkType | `CREATE_LINK_TYPE`, `MODIFY_LINK_TYPE`, `DELETE_LINK_TYPE` |
| ActionType | `CREATE_ACTION_TYPE`, `MODIFY_ACTION_TYPE`, `DELETE_ACTION_TYPE` |
| Property | `ADD_PROPERTY`, `MODIFY_PROPERTY`, `REMOVE_PROPERTY` |
| Object | `CREATE_OBJECT`, `MODIFY_OBJECT`, `DELETE_OBJECT` |
| Link | `CREATE_LINK`, `DELETE_LINK` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | String | What this change set accomplishes |
| `status` | Enum | `PENDING`, `APPLIED`, `ROLLED_BACK`, `FAILED` |
| `rollbackInfo` | Object | Rollback support |

### RollbackInfo

```json
{
  "rollbackable": true,
  "rollbackDeadline": "2026-01-25T10:00:00Z",
  "inverseOperations": [
    { "operationType": "DELETE_OBJECT_TYPE", "targetApiName": "Employee" }
  ]
}
```

### Example

```json
{
  "$type": "ChangeSet",
  "changeSetId": "660e8400-e29b-41d4-a716-446655440002",
  "timestamp": "2026-01-18T11:00:00Z",
  "actor": {
    "actorType": "AGENT",
    "actorId": "claude-agent-001",
    "actorName": "Claude"
  },
  "description": "Add Employee ObjectType with properties",
  "operations": [
    {
      "operationType": "CREATE_OBJECT_TYPE",
      "targetApiName": "Employee",
      "payload": { "displayName": "Employee", "primaryKey": { "propertyApiName": "id" } },
      "sequenceNumber": 0
    },
    {
      "operationType": "ADD_PROPERTY",
      "targetApiName": "Employee.fullName",
      "payload": { "dataType": { "type": "STRING" } },
      "sequenceNumber": 1
    }
  ],
  "status": "PENDING",
  "rollbackInfo": {
    "rollbackable": true
  }
}
```

---

## Variant 4: ExportMetadata

Metadata for Ontology JSON export (Palantir P2-HIGH requirement).

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `$type` | `"ExportMetadata"` | Discriminator |
| `exportId` | UUID | Unique identifier |
| `exportedAt` | DateTime | When exported |
| `schemaVersion` | SemVer | Schema format version |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `exportedBy` | String | Who performed export |
| `sourceOntologyRid` | String | Source ontology RID |
| `sourceOntologyVersion` | Integer | Version at export |
| `exportScope` | Enum | `FULL`, `PARTIAL`, `DIFF` |
| `includedTypes` | Object | Type category flags |
| `filterCriteria` | Object | Filters applied |
| `checksums` | Object | Integrity checksums |
| `warnings` | String[] | Export warnings |

### IncludedTypes

```json
{
  "objectTypes": true,
  "linkTypes": true,
  "actionTypes": true,
  "interfaces": true,
  "valueTypes": true,
  "structTypes": true,
  "sharedProperties": true
}
```

### FilterCriteria

```json
{
  "statusFilter": ["active", "experimental"],
  "tagFilter": ["core", "security"],
  "moduleFilter": ["hr", "finance"]
}
```

### Example

```json
{
  "$type": "ExportMetadata",
  "exportId": "770e8400-e29b-41d4-a716-446655440003",
  "exportedAt": "2026-01-18T12:00:00Z",
  "exportedBy": "admin",
  "sourceOntologyRid": "ri.ontology.main.oda-enterprise",
  "sourceOntologyVersion": 42,
  "schemaVersion": "4.0.0",
  "exportScope": "FULL",
  "includedTypes": {
    "objectTypes": true,
    "linkTypes": true,
    "actionTypes": true
  },
  "checksums": {
    "sha256": "abc123def456..."
  }
}
```

---

## Variant 5: ProposalMetadata

Metadata for Ontology Proposal workflow with 7-state FSM.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `$type` | `"ProposalMetadata"` | Discriminator |
| `proposalId` | UUID | Unique identifier |
| `status` | Enum (7) | FSM state |
| `createdAt` | DateTime | When created |
| `createdBy` | String | Who created |

### Status FSM (7 States)

```
                    +-----------+
                    |   DRAFT   | (initial)
                    +-----+-----+
                          |
                          v submit()
                    +-----------+
                    |  PENDING  |
                    +-----+-----+
                         / \
            approve()   /   \  reject()
                       v     v
              +--------+     +--------+
              |APPROVED|     |REJECTED|
              +---+----+     +--------+
                  |
                  v execute()
              +--------+
              |EXECUTED| (terminal)
              +--------+

              Side paths:
              - Any state -> CANCELLED (via cancel())
              - Any state -> DELETED (via delete(), soft delete)
```

### State Transitions

| From | To | Action | Validator |
|------|----|--------|-----------|
| DRAFT | PENDING | submit() | All validationResults passed |
| PENDING | APPROVED | approve() | Has review permission |
| PENDING | REJECTED | reject() | Has review permission |
| APPROVED | EXECUTED | execute() | ChangeSet applied successfully |
| Any | CANCELLED | cancel() | Owner or admin |
| Any | DELETED | delete() | Soft delete |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `title` | String | Brief title |
| `description` | String | Detailed description |
| `priority` | Enum | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `submittedAt` | DateTime | When moved to PENDING |
| `reviewedAt/By` | DateTime/String | Review info |
| `reviewComment` | String | Reviewer feedback |
| `executedAt/By` | DateTime/String | Execution info |
| `actionTypeRef` | String | ActionType apiName |
| `payload` | Object | Action parameters |
| `changeSet` | ChangeSet | Proposed changes |
| `validationResults` | ValidationResult[] | Pre-submit checks |
| `history` | StatusTransition[] | Transition history |

### ValidationResult

```json
{
  "criterionApiName": "hasOntologyEditorRole",
  "passed": true,
  "message": "User has Ontology Editor role"
}
```

### StatusTransition (History)

```json
{
  "fromStatus": "DRAFT",
  "toStatus": "PENDING",
  "timestamp": "2026-01-18T09:30:00Z",
  "actor": "security-team",
  "comment": "Ready for review"
}
```

### Example

```json
{
  "$type": "ProposalMetadata",
  "proposalId": "880e8400-e29b-41d4-a716-446655440004",
  "title": "Add Security Markings to Employee ObjectType",
  "description": "Adding mandatory control property for row-level security compliance.",
  "status": "PENDING",
  "priority": "HIGH",
  "createdAt": "2026-01-18T09:00:00Z",
  "createdBy": "security-team",
  "submittedAt": "2026-01-18T09:30:00Z",
  "actionTypeRef": "addPropertyToObjectType",
  "payload": {
    "objectTypeApiName": "Employee",
    "property": {
      "apiName": "securityMarkings",
      "isMandatoryControl": true
    }
  },
  "validationResults": [
    {
      "criterionApiName": "hasOntologyEditorRole",
      "passed": true,
      "message": "User has Ontology Editor role"
    }
  ],
  "history": [
    {
      "fromStatus": "DRAFT",
      "toStatus": "PENDING",
      "timestamp": "2026-01-18T09:30:00Z",
      "actor": "security-team",
      "comment": "Ready for review"
    }
  ]
}
```

---

## 6-Stage Lifecycle Protocol

### Stage 0: CLASSIFY

**Purpose:** Determine which $type variant to use based on user intent.

**Intent Mapping:**

| User Intent | $type | Keywords |
|-------------|-------|----------|
| Ontology versioning, stats | `OntologyMetadata` | "ontology", "version", "stats" |
| Operation tracking | `AuditLog` | "audit", "log", "track", "who changed" |
| Batch changes | `ChangeSet` | "batch", "transaction", "rollback" |
| Export/Import | `ExportMetadata` | "export", "import", "backup" |
| Approval workflow | `ProposalMetadata` | "proposal", "approve", "review" |

**Interactive Flow:**

```
What type of metadata do you want to create?

1. OntologyMetadata - Ontology version and configuration
2. AuditLog - Track an operation (who/what/when)
3. ChangeSet - Batch multiple changes with rollback
4. ExportMetadata - Document an export
5. ProposalMetadata - Create approval workflow

Select [1-5] or describe your intent:
```

**Output:** `$type` value for subsequent stages

### Stage 1: DEFINE

**$type-Specific Collection:**

#### OntologyMetadata Define
```
1. API Name (PascalCase): ODAEnterprise
2. Display Name: ODA Enterprise Ontology
3. Schema Version (x.y.z): 4.0.0
4. Description (optional): Main enterprise ontology
5. Service Version [OSv1/OSv2]: OSv2
6. Configure governance? [y/n]
```

#### AuditLog Define
```
1. Operation Type:
   [CREATE/READ/UPDATE/DELETE/LINK/UNLINK/EXECUTE/APPROVE/REJECT/TRANSITION/EXPORT/IMPORT]
2. Actor Type [USER/AGENT/SYSTEM/SERVICE]: USER
3. Actor ID: user-123
4. Target Type [OBJECT/LINK/OBJECT_TYPE/...]: OBJECT
5. Target API Name (if applicable): Employee
6. Primary Key (for OBJECT): emp-456
7. Reason (optional): Correcting data
8. Include state snapshots? [y/n]
```

#### ChangeSet Define
```
1. Description: Add Employee ObjectType
2. Number of operations: 2
   Operation 1:
   - Type: CREATE_OBJECT_TYPE
   - Target API Name: Employee
   - Payload: {...}
   Operation 2:
   - Type: ADD_PROPERTY
   - Target API Name: Employee.fullName
   - Payload: {...}
3. Rollbackable? [y/n]: y
4. Rollback deadline (optional): 2026-01-25
```

#### ExportMetadata Define
```
1. Source Ontology RID: ri.ontology.main.oda-enterprise
2. Source Version: 42
3. Schema Version: 4.0.0
4. Export Scope [FULL/PARTIAL/DIFF]: FULL
5. Include types? (select all that apply)
   [x] ObjectTypes
   [x] LinkTypes
   [x] ActionTypes
   [ ] Interfaces
6. Apply filters? [y/n]
7. Generate checksums? [y/n]
```

#### ProposalMetadata Define
```
1. Title: Add Security Markings
2. Description: Adding mandatory control property
3. Priority [LOW/MEDIUM/HIGH/CRITICAL]: HIGH
4. Action Type Reference (optional): addPropertyToObjectType
5. Include ChangeSet? [y/n]
6. Run validation criteria? [y/n]
```

**Output:** `.agent/tmp/staging/<id>.json`

### Stage 2: VALIDATE

**Common Checks:**
1. `$type` is one of 5 valid values
2. `$type` matches required fields for variant

**$type-Specific Validation:**

#### OntologyMetadata Validation
- `apiName` matches `^[a-zA-Z][a-zA-Z0-9_]*$`
- `schemaVersion` matches `^\d+\.\d+\.\d+$`
- `ontologyRid` matches `^ri\.ontology\.[a-z]+\.[a-zA-Z0-9-]+$` (if present)
- `serviceVersion` is `OSv1` or `OSv2` (if present)

#### AuditLog Validation
- `logId` is valid UUID
- `timestamp` is valid ISO 8601 DateTime
- `operationType` is one of 12 valid values
- `actor.actorType` is one of 4 valid values
- `target.targetType` is one of 8 valid values
- `ipAddress` matches IPv4 format (if present)

#### ChangeSet Validation
- `changeSetId` is valid UUID
- `operations` array has minItems: 1
- Each operation has valid `operationType` (17 values)
- `status` is one of 4 valid values (if present)
- `rollbackInfo.inverseOperations` are valid (if present)

#### ExportMetadata Validation
- `exportId` is valid UUID
- `exportedAt` is valid ISO 8601 DateTime
- `schemaVersion` matches SemVer pattern
- `exportScope` is one of 3 valid values (if present)

#### ProposalMetadata Validation
- `proposalId` is valid UUID
- `status` is one of 7 valid FSM states
- `priority` is one of 4 valid values (if present)
- FSM transition validation (see Stage 0 rules)

**Output:** Validation report (pass/fail + errors)

### Stage 3: STAGE

**Actions:**
1. Generate ID: `meta-{uuid[:8]}`
2. Add metadata timestamps
3. Calculate diff (if modifying existing)
4. For ChangeSet: Generate inverse operations
5. For ProposalMetadata: Initialize history array

**Output:** `.agent/tmp/staging/<id>.staged.json`

### Stage 4: REVIEW

**Display Format:**

```
=== METADATA REVIEW ===
Type: {$type}
ID: {id}
Created: {timestamp}

[Variant-specific summary]

--- Staged Content ---
{JSON preview}

--- Changes from Existing ---
{diff if applicable}

--- Security Review ---
[x] No sensitive data exposed
[x] Actor permissions verified
[x] Audit trail complete

Approve? [y/n]
```

### Stage 5: DEPLOY

**Actions:**
1. Write to `.agent/tmp/ontology.db`
2. Create AuditLog entry (meta-operation)
3. Update registry

**Database Tables:**

```sql
-- Main metadata table
CREATE TABLE IF NOT EXISTS metadata (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- $type discriminator
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);

-- Index for $type queries
CREATE INDEX IF NOT EXISTS idx_metadata_type ON metadata(type);

-- Specialized table for AuditLog (append-only)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    definition JSON NOT NULL
);

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id);

-- Specialized table for ProposalMetadata (FSM tracking)
CREATE TABLE IF NOT EXISTS proposals (
    proposal_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    definition JSON NOT NULL
);

-- Index for proposal status
CREATE INDEX IF NOT EXISTS idx_proposal_status ON proposals(status);
```

---

## Actions

### define [<$type>]
Interactive Metadata creation.
```bash
/metadata define                    # Auto-classify
/metadata define OntologyMetadata   # Specific variant
/metadata define AuditLog
/metadata define ChangeSet
/metadata define ExportMetadata
/metadata define ProposalMetadata
```

### validate <json_path>
Validate JSON against schema.
```bash
/metadata validate ontology-meta.json
```

### stage <id>
Stage validated definition.
```bash
/metadata stage meta-001
```

### review <id>
Review and approve.
```bash
/metadata review meta-001
```

### deploy <id>
Deploy approved definition.
```bash
/metadata deploy meta-001
```

### list [<$type>]
List Metadata entries.
```bash
/metadata list                 # All types
/metadata list AuditLog        # Only audit logs
/metadata list ProposalMetadata # Only proposals
```

**Output:**
| ID | $type | Status | Created |
|----|-------|--------|---------|
| meta-001 | OntologyMetadata | deployed | 2026-01-18 |
| audit-002 | AuditLog | deployed | 2026-01-18 |

### show <id>
Show Metadata details.
```bash
/metadata show meta-001
```

### rollback <changeSetId>
Rollback a ChangeSet (executes inverse operations).
```bash
/metadata rollback cs-001
```

**Preconditions:**
- ChangeSet status is `APPLIED`
- `rollbackInfo.rollbackable` is true
- Current time < `rollbackDeadline` (if set)

### transition <proposalId> <status>
Transition ProposalMetadata FSM.
```bash
/metadata transition prop-001 PENDING    # submit()
/metadata transition prop-001 APPROVED   # approve()
/metadata transition prop-001 REJECTED   # reject()
/metadata transition prop-001 EXECUTED   # execute()
/metadata transition prop-001 CANCELLED  # cancel()
```

**Validation:** Enforces FSM rules from Stage 0.

---

## Output Formats

### Success Response
```json
{
  "status": "success",
  "action": "deploy",
  "metadata": {
    "id": "meta-001",
    "$type": "OntologyMetadata",
    "apiName": "ODAEnterprise"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "errors": [
    { "code": "INVALID_TYPE", "path": "$.$type", "message": "$type must be one of 5 valid values" }
  ]
}
```

### FSM Transition Response
```json
{
  "status": "success",
  "action": "transition",
  "proposal": {
    "id": "prop-001",
    "previousStatus": "PENDING",
    "newStatus": "APPROVED",
    "transitionedAt": "2026-01-18T14:00:00Z"
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_TYPE` | $type not one of 5 valid values |
| `MISSING_REQUIRED_FIELD` | Required field not present |
| `INVALID_PATTERN` | Value doesn't match regex |
| `INVALID_UUID` | UUID format invalid |
| `INVALID_DATETIME` | DateTime format invalid |
| `INVALID_OPERATION_TYPE` | operationType not in enum |
| `INVALID_FSM_TRANSITION` | Status transition not allowed |
| `CHANGESET_EMPTY` | ChangeSet has no operations |
| `ROLLBACK_NOT_ALLOWED` | ChangeSet cannot be rolled back |
| `ROLLBACK_DEADLINE_PASSED` | Rollback deadline exceeded |
| `VALIDATION_FAILED` | ProposalMetadata validation criteria failed |
| `APPROVAL_REQUIRED` | Deploy without approval |

---

## Integration

### Database
```
.agent/tmp/ontology.db
```

### Staging
```
.agent/tmp/staging/<id>.json
.agent/tmp/staging/<id>.staged.json
```

### Audit Log
```
.agent/logs/ontology_changes.log
```

### Related Skills
- `oda-objecttype` - ObjectType definitions
- `oda-actiontype` - ActionType definitions
- `oda-linktype` - LinkType definitions
- `oda-property` - Property definitions
- `oda-interface` - Interface definitions

---

## Validation Execution

### Using JSON Schema Validator

```python
import json
import jsonschema

schema_path = "ontology_definition/schemas/Metadata.schema.json"
with open(schema_path) as f:
    schema = json.load(f)

definition_path = ".agent/tmp/staging/meta-001.json"
with open(definition_path) as f:
    definition = json.load(f)

try:
    jsonschema.validate(definition, schema)
    print("Validation passed")
except jsonschema.ValidationError as e:
    print(f"Validation failed: {e.message}")
```

### $type-Specific Validation

```python
def validate_metadata(definition: dict) -> list[str]:
    errors = []

    # Check $type discriminator
    type_value = definition.get("$type")
    valid_types = ["OntologyMetadata", "AuditLog", "ChangeSet", "ExportMetadata", "ProposalMetadata"]

    if type_value not in valid_types:
        errors.append(f"$type must be one of {valid_types}")
        return errors

    # Type-specific validation
    if type_value == "OntologyMetadata":
        errors.extend(validate_ontology_metadata(definition))
    elif type_value == "AuditLog":
        errors.extend(validate_audit_log(definition))
    elif type_value == "ChangeSet":
        errors.extend(validate_change_set(definition))
    elif type_value == "ExportMetadata":
        errors.extend(validate_export_metadata(definition))
    elif type_value == "ProposalMetadata":
        errors.extend(validate_proposal_metadata(definition))

    return errors
```

---

## FSM Implementation

### ProposalMetadata State Machine

```python
from enum import Enum
from typing import Optional

class ProposalStatus(Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    DELETED = "DELETED"

# Valid transitions
VALID_TRANSITIONS = {
    ProposalStatus.DRAFT: [ProposalStatus.PENDING, ProposalStatus.CANCELLED, ProposalStatus.DELETED],
    ProposalStatus.PENDING: [ProposalStatus.APPROVED, ProposalStatus.REJECTED, ProposalStatus.CANCELLED, ProposalStatus.DELETED],
    ProposalStatus.APPROVED: [ProposalStatus.EXECUTED, ProposalStatus.CANCELLED, ProposalStatus.DELETED],
    ProposalStatus.REJECTED: [ProposalStatus.CANCELLED, ProposalStatus.DELETED],
    ProposalStatus.EXECUTED: [ProposalStatus.DELETED],  # Terminal, only soft delete
    ProposalStatus.CANCELLED: [ProposalStatus.DELETED],
    ProposalStatus.DELETED: [],  # Terminal
}

def can_transition(from_status: ProposalStatus, to_status: ProposalStatus) -> bool:
    return to_status in VALID_TRANSITIONS.get(from_status, [])

def transition_proposal(proposal: dict, new_status: str, actor: str, comment: Optional[str] = None) -> dict:
    current = ProposalStatus(proposal["status"])
    target = ProposalStatus(new_status)

    if not can_transition(current, target):
        raise ValueError(f"Invalid transition: {current.value} -> {target.value}")

    # Update status
    proposal["status"] = target.value

    # Add to history
    if "history" not in proposal:
        proposal["history"] = []

    proposal["history"].append({
        "fromStatus": current.value,
        "toStatus": target.value,
        "timestamp": datetime.now().isoformat() + "Z",
        "actor": actor,
        "comment": comment
    })

    # Update timestamps based on transition
    if target == ProposalStatus.PENDING:
        proposal["submittedAt"] = datetime.now().isoformat() + "Z"
    elif target in [ProposalStatus.APPROVED, ProposalStatus.REJECTED]:
        proposal["reviewedAt"] = datetime.now().isoformat() + "Z"
        proposal["reviewedBy"] = actor
        if comment:
            proposal["reviewComment"] = comment
    elif target == ProposalStatus.EXECUTED:
        proposal["executedAt"] = datetime.now().isoformat() + "Z"
        proposal["executedBy"] = actor

    return proposal
```

---

## ChangeSet Rollback Implementation

```python
def rollback_changeset(changeset: dict) -> dict:
    """Execute inverse operations to rollback a ChangeSet."""

    # Validate preconditions
    if changeset.get("status") != "APPLIED":
        raise ValueError("Can only rollback APPLIED ChangeSets")

    rollback_info = changeset.get("rollbackInfo", {})
    if not rollback_info.get("rollbackable", True):
        raise ValueError("ChangeSet is not rollbackable")

    deadline = rollback_info.get("rollbackDeadline")
    if deadline and datetime.fromisoformat(deadline.replace("Z", "+00:00")) < datetime.now(timezone.utc):
        raise ValueError("Rollback deadline has passed")

    # Execute inverse operations in reverse order
    inverse_ops = rollback_info.get("inverseOperations", [])
    if not inverse_ops:
        # Generate inverse operations if not pre-computed
        inverse_ops = generate_inverse_operations(changeset["operations"])

    for op in reversed(inverse_ops):
        execute_operation(op)

    # Update status
    changeset["status"] = "ROLLED_BACK"

    return changeset

def generate_inverse_operations(operations: list) -> list:
    """Generate inverse operations for rollback."""
    inverse_map = {
        "CREATE_OBJECT_TYPE": "DELETE_OBJECT_TYPE",
        "DELETE_OBJECT_TYPE": "CREATE_OBJECT_TYPE",
        "MODIFY_OBJECT_TYPE": "MODIFY_OBJECT_TYPE",  # Requires beforeState
        "ADD_PROPERTY": "REMOVE_PROPERTY",
        "REMOVE_PROPERTY": "ADD_PROPERTY",
        # ... etc
    }

    inverse_ops = []
    for op in operations:
        inverse_type = inverse_map.get(op["operationType"])
        if inverse_type:
            inverse_ops.append({
                "operationType": inverse_type,
                "targetApiName": op["targetApiName"],
                "payload": op.get("beforeState", op.get("payload"))
            })

    return inverse_ops
```

---

## TodoWrite Integration

Track lifecycle progress:

```json
[
  {"content": "[Stage 0] Classify Metadata: AuditLog", "status": "completed", "activeForm": "Classifying metadata type"},
  {"content": "[Stage 1] Define AuditLog entry", "status": "completed", "activeForm": "Defining audit log"},
  {"content": "[Stage 2] Validate against schema", "status": "in_progress", "activeForm": "Validating schema"},
  {"content": "[Stage 3] Stage for review", "status": "pending", "activeForm": "Staging definition"},
  {"content": "[Stage 4] Review and approve", "status": "pending", "activeForm": "Reviewing definition"},
  {"content": "[Stage 5] Deploy to database", "status": "pending", "activeForm": "Deploying definition"}
]
```

---

## Anti-Hallucination Rule

**CRITICAL:** All operations MUST reference actual files.

```python
if not evidence.get("source_file") and not evidence.get("user_input"):
    raise AntiHallucinationError("Operation without evidence source")
```

---

## Query Examples

### List Recent Audit Logs

```sql
SELECT log_id, timestamp, operation_type, actor_id, target_type
FROM audit_logs
WHERE timestamp > datetime('now', '-7 days')
ORDER BY timestamp DESC
LIMIT 50;
```

### List Pending Proposals

```sql
SELECT proposal_id,
       json_extract(definition, '$.title') as title,
       json_extract(definition, '$.priority') as priority,
       created_at
FROM proposals
WHERE status = 'PENDING'
ORDER BY
    CASE json_extract(definition, '$.priority')
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        ELSE 4
    END,
    created_at;
```

### Audit Trail for Object

```sql
SELECT log_id, timestamp, operation_type,
       json_extract(definition, '$.actor.actorName') as actor,
       json_extract(definition, '$.reason') as reason
FROM audit_logs
WHERE json_extract(definition, '$.target.objectTypeApiName') = 'Employee'
  AND json_extract(definition, '$.target.primaryKey') = 'emp-456'
ORDER BY timestamp;
```
