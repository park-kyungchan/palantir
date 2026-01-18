# Metadata Types

이 문서는 Ontology 메타데이터 타입들을 설명합니다. 메타데이터는 Ontology의 전체적인 상태, 변경 이력, 감사 로그, 내보내기/가져오기, 변경 제안서 워크플로우를 관리합니다.

**Schema Source:** `Metadata.schema.json`

**Discriminator Field:** `$type`

**Supported Types:**
- `OntologyMetadata` - 전체 Ontology 메타데이터
- `AuditLog` - 감사 로그 엔트리
- `ChangeSet` - 트랜잭션 변경 컬렉션
- `ExportMetadata` - JSON 내보내기 메타데이터
- `ProposalMetadata` - 변경 제안서 워크플로우

---

# Part 1: OntologyMetadata

## Definition

전체 Ontology의 메타데이터를 포함합니다. Ontology 인스턴스의 식별 정보, 버전 관리, 통계, 거버넌스 설정을 담고 있습니다.

```json
{
  "$type": "OntologyMetadata"
}
```

## Schema Structure

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$type` | `const` | Yes | `"OntologyMetadata"` |
| `ontologyRid` | `string` | No | Resource ID for this Ontology instance |
| `apiName` | `string` | Yes | Programmatic name for this Ontology |
| `displayName` | `string` | Yes | Human-friendly Ontology name |
| `description` | `string` | No | Documentation for this Ontology |
| `schemaVersion` | `string` | Yes | Semantic version of the schema format |
| `version` | `integer` | No | Ontology version number (increments on each published change) |
| `serviceVersion` | `string` | No | Ontology Service version (`OSv1` or `OSv2`) |

#### Field Details

**ontologyRid**
```json
{
  "type": "string",
  "pattern": "^ri\\.ontology\\.[a-z]+\\.[a-zA-Z0-9-]+$"
}
```
- Example: `ri.ontology.main.oda-enterprise`

**apiName**
```json
{
  "type": "string",
  "pattern": "^[a-zA-Z][a-zA-Z0-9_]*$"
}
```
- Must start with a letter
- Only alphanumeric characters and underscores allowed
- Example: `ODAEnterprise`

**schemaVersion**
```json
{
  "type": "string",
  "pattern": "^\\d+\\.\\d+\\.\\d+$",
  "examples": ["4.0.0", "3.2.1"]
}
```
- Follows Semantic Versioning (SemVer)

**serviceVersion**
```json
{
  "type": "string",
  "enum": ["OSv1", "OSv2"],
  "default": "OSv2"
}
```
- `OSv1`: Legacy Ontology Service
- `OSv2`: Current Ontology Service (default)

### Audit Fields

| Field | Type | ReadOnly | Description |
|-------|------|----------|-------------|
| `createdAt` | `date-time` | Yes | Creation timestamp |
| `createdBy` | `string` | Yes | Creator user/system ID |
| `modifiedAt` | `date-time` | Yes | Last modification timestamp |
| `modifiedBy` | `string` | Yes | Last modifier user/system ID |

### OntologyStats

통계 정보는 `stats` 필드에 포함됩니다.

```json
{
  "stats": {
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
}
```

| Field | Type | Description |
|-------|------|-------------|
| `objectTypeCount` | `integer` | Total number of ObjectTypes |
| `linkTypeCount` | `integer` | Total number of LinkTypes |
| `actionTypeCount` | `integer` | Total number of ActionTypes |
| `interfaceCount` | `integer` | Total number of Interfaces |
| `valueTypeCount` | `integer` | Total number of ValueTypes |
| `structTypeCount` | `integer` | Total number of StructTypes |
| `sharedPropertyCount` | `integer` | Total number of shared properties |
| `activeObjectTypeCount` | `integer` | ObjectTypes in ACTIVE status |
| `deprecatedObjectTypeCount` | `integer` | ObjectTypes in DEPRECATED status |

### GovernanceConfig

거버넌스 설정은 `governance` 필드에 포함됩니다.

```json
{
  "governance": {
    "owner": "ontology-team",
    "editors": ["dev-team", "data-team"],
    "viewers": ["all-employees"],
    "proposalRequired": true,
    "endorsementEnabled": true
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `owner` | `string` | - | User or team ID that owns this Ontology |
| `editors` | `string[]` | - | Users/teams with edit permission |
| `viewers` | `string[]` | - | Users/teams with view permission |
| `proposalRequired` | `boolean` | `true` | If true, changes require Proposal approval |
| `endorsementEnabled` | `boolean` | `true` | If true, ObjectTypes can be marked as endorsed |

## Complete Example

```json
{
  "$type": "OntologyMetadata",
  "ontologyRid": "ri.ontology.main.oda-enterprise",
  "apiName": "ODAEnterprise",
  "displayName": "ODA Enterprise Ontology",
  "description": "Main enterprise ontology for the ODA system.",
  "schemaVersion": "4.0.0",
  "createdAt": "2026-01-01T00:00:00Z",
  "createdBy": "admin",
  "modifiedAt": "2026-01-17T10:00:00Z",
  "modifiedBy": "system",
  "version": 42,
  "stats": {
    "objectTypeCount": 25,
    "linkTypeCount": 18,
    "actionTypeCount": 45,
    "interfaceCount": 5,
    "valueTypeCount": 12,
    "structTypeCount": 8,
    "sharedPropertyCount": 15,
    "activeObjectTypeCount": 22,
    "deprecatedObjectTypeCount": 3
  },
  "governance": {
    "owner": "ontology-team",
    "editors": ["dev-team", "data-team"],
    "viewers": ["all-employees"],
    "proposalRequired": true,
    "endorsementEnabled": true
  },
  "serviceVersion": "OSv2"
}
```

---

# Part 2: AuditLog

## Definition

불변의 감사 로그 엔트리입니다. 누가(who), 무엇을(what), 언제(when), 왜(why) 변경했는지를 추적합니다. 모든 변경 작업에 대한 완전한 이력을 제공합니다.

```json
{
  "$type": "AuditLog"
}
```

## Schema Structure

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$type` | `const` | Yes | `"AuditLog"` |
| `logId` | `uuid` | Yes | Unique identifier for this log entry |
| `timestamp` | `date-time` | Yes | When the operation occurred |
| `operationType` | `enum` | Yes | Type of operation performed |
| `actor` | `ActorInfo` | Yes | Who performed the operation |
| `target` | `TargetInfo` | Yes | What was affected |
| `success` | `boolean` | No | Whether the operation succeeded (default: `true`) |

#### operationType

```json
{
  "type": "string",
  "enum": [
    "CREATE",
    "READ",
    "UPDATE",
    "DELETE",
    "LINK",
    "UNLINK",
    "EXECUTE",
    "APPROVE",
    "REJECT",
    "TRANSITION",
    "EXPORT",
    "IMPORT"
  ]
}
```

| Value | Description |
|-------|-------------|
| `CREATE` | New entity created |
| `READ` | Entity accessed (optional logging) |
| `UPDATE` | Entity modified |
| `DELETE` | Entity removed |
| `LINK` | Link relationship created |
| `UNLINK` | Link relationship removed |
| `EXECUTE` | Action executed |
| `APPROVE` | Proposal approved |
| `REJECT` | Proposal rejected |
| `TRANSITION` | Status transition |
| `EXPORT` | Ontology exported |
| `IMPORT` | Ontology imported |

### ActorInfo

작업을 수행한 주체에 대한 정보입니다.

```json
{
  "actor": {
    "actorType": "USER",
    "actorId": "user-123",
    "actorName": "John Doe",
    "roles": ["Developer", "Ontology Editor"],
    "permissions": ["ontology:write", "object:create"]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actorType` | `enum` | Yes | Type of actor |
| `actorId` | `string` | Yes | Unique identifier for the actor |
| `actorName` | `string` | No | Display name of the actor |
| `roles` | `string[]` | No | Roles the actor had at time of operation |
| `permissions` | `string[]` | No | Relevant permissions used |

**actorType Values:**
- `USER` - Human user
- `AGENT` - AI agent or automated process
- `SYSTEM` - System-level operation
- `SERVICE` - External service

### TargetInfo

작업의 대상에 대한 정보입니다.

```json
{
  "target": {
    "targetType": "OBJECT",
    "objectTypeApiName": "Employee",
    "primaryKey": "emp-456"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `targetType` | `enum` | Yes | Type of target |
| `targetRid` | `string` | No | RID of the target (if applicable) |
| `targetApiName` | `string` | No | apiName of the target |
| `objectTypeApiName` | `string` | No | For OBJECT targets, the ObjectType |
| `primaryKey` | `string` | No | For OBJECT targets, the primary key value |

**targetType Values:**
- `OBJECT` - Object instance
- `LINK` - Link instance
- `OBJECT_TYPE` - ObjectType definition
- `LINK_TYPE` - LinkType definition
- `ACTION_TYPE` - ActionType definition
- `PROPERTY` - Property definition
- `ONTOLOGY` - Ontology itself
- `PROPOSAL` - Proposal

### PropertyChange

개별 속성 변경에 대한 상세 정보입니다.

```json
{
  "changes": [
    {
      "propertyApiName": "department",
      "oldValue": "Engineering",
      "newValue": "Product",
      "changeType": "SET"
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `propertyApiName` | `string` | Yes | Property that was changed |
| `oldValue` | `any` | No | Value before change (null for CREATE) |
| `newValue` | `any` | No | Value after change (null for DELETE) |
| `changeType` | `enum` | Yes | Type of change operation |

**changeType Values:**
- `SET` - Property value set
- `UNSET` - Property value cleared
- `APPEND` - Value appended to array
- `REMOVE` - Value removed from array
- `REPLACE` - Array/object replaced entirely

### State Snapshots

변경 전후 상태 스냅샷입니다.

| Field | Type | Description |
|-------|------|-------------|
| `beforeState` | `object` | State snapshot before the change (for UPDATE/DELETE) |
| `afterState` | `object` | State snapshot after the change (for CREATE/UPDATE) |

### Reference Fields

| Field | Type | Description |
|-------|------|-------------|
| `actionRef` | `string` | If operation was via ActionType, the action's apiName |
| `proposalRef` | `string` | If operation required approval, the Proposal ID |
| `reason` | `string` | User-provided reason for the change |
| `correlationId` | `string` | ID linking related log entries (multi-step operations) |
| `sessionId` | `string` | Session ID for the actor |
| `ipAddress` | `string` | IP address of the actor (if applicable) |
| `errorMessage` | `string` | If failed, the error message |

## Complete Example

```json
{
  "$type": "AuditLog",
  "logId": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-17T10:30:00Z",
  "operationType": "UPDATE",
  "actor": {
    "actorType": "USER",
    "actorId": "user-123",
    "actorName": "John Doe",
    "roles": ["Developer", "Ontology Editor"]
  },
  "target": {
    "targetType": "OBJECT",
    "objectTypeApiName": "Employee",
    "primaryKey": "emp-456"
  },
  "actionRef": "updateEmployeeInfo",
  "reason": "Correcting department assignment",
  "beforeState": {
    "department": "Engineering"
  },
  "afterState": {
    "department": "Product"
  },
  "changes": [
    {
      "propertyApiName": "department",
      "oldValue": "Engineering",
      "newValue": "Product",
      "changeType": "SET"
    }
  ],
  "success": true,
  "correlationId": "corr-789",
  "sessionId": "session-abc"
}
```

---

# Part 3: ChangeSet

## Definition

트랜잭션과 같은 변경 컬렉션입니다. 여러 변경 작업을 하나의 단위로 묶어 원자적으로 적용하거나 롤백할 수 있습니다.

```json
{
  "$type": "ChangeSet"
}
```

## Schema Structure

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$type` | `const` | Yes | `"ChangeSet"` |
| `changeSetId` | `uuid` | Yes | Unique identifier |
| `timestamp` | `date-time` | Yes | When the change set was created |
| `actor` | `ActorInfo` | Yes | Who created the change set |
| `description` | `string` | No | Description of what this change set accomplishes |
| `operations` | `ChangeOperation[]` | Yes | Operations in this change set (min: 1) |
| `status` | `enum` | No | Current status (default: `PENDING`) |

#### status

```json
{
  "type": "string",
  "enum": ["PENDING", "APPLIED", "ROLLED_BACK", "FAILED"],
  "default": "PENDING"
}
```

| Status | Description |
|--------|-------------|
| `PENDING` | Change set created but not yet applied |
| `APPLIED` | All operations successfully applied |
| `ROLLED_BACK` | Change set was rolled back |
| `FAILED` | Application failed, partial rollback may have occurred |

### ChangeOperation

변경 세트 내의 개별 작업입니다.

```json
{
  "operations": [
    {
      "operationType": "ADD_PROPERTY",
      "targetApiName": "Employee",
      "payload": {
        "apiName": "securityLevel",
        "dataType": "string"
      },
      "sequenceNumber": 0
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operationType` | `enum` | Yes | Type of schema change operation |
| `targetApiName` | `string` | Yes | Target entity apiName |
| `payload` | `object` | No | Operation-specific data |
| `sequenceNumber` | `integer` | No | Order within the change set |

#### operationType Values

**Schema-Level Operations:**
| Value | Description |
|-------|-------------|
| `CREATE_OBJECT_TYPE` | Create new ObjectType |
| `MODIFY_OBJECT_TYPE` | Modify existing ObjectType |
| `DELETE_OBJECT_TYPE` | Delete ObjectType |
| `CREATE_LINK_TYPE` | Create new LinkType |
| `MODIFY_LINK_TYPE` | Modify existing LinkType |
| `DELETE_LINK_TYPE` | Delete LinkType |
| `CREATE_ACTION_TYPE` | Create new ActionType |
| `MODIFY_ACTION_TYPE` | Modify existing ActionType |
| `DELETE_ACTION_TYPE` | Delete ActionType |

**Property Operations:**
| Value | Description |
|-------|-------------|
| `ADD_PROPERTY` | Add property to type |
| `MODIFY_PROPERTY` | Modify property definition |
| `REMOVE_PROPERTY` | Remove property from type |

**Instance-Level Operations:**
| Value | Description |
|-------|-------------|
| `CREATE_OBJECT` | Create object instance |
| `MODIFY_OBJECT` | Modify object instance |
| `DELETE_OBJECT` | Delete object instance |
| `CREATE_LINK` | Create link instance |
| `DELETE_LINK` | Delete link instance |

### Rollback Support

롤백 정보는 `rollbackInfo` 필드에 포함됩니다.

```json
{
  "rollbackInfo": {
    "rollbackable": true,
    "rollbackDeadline": "2026-01-24T10:30:00Z",
    "inverseOperations": [
      {
        "operationType": "REMOVE_PROPERTY",
        "targetApiName": "Employee",
        "payload": { "apiName": "securityLevel" },
        "sequenceNumber": 0
      }
    ]
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rollbackable` | `boolean` | `true` | Whether this change set can be rolled back |
| `rollbackDeadline` | `date-time` | - | Deadline for rollback (after this, rollback may not be possible) |
| `inverseOperations` | `ChangeOperation[]` | - | Operations to execute for rollback |

### Rollback Workflow

```
1. PENDING     → User creates change set
                      ↓
2. APPLIED    → All operations succeed
                      ↓ (if rollback requested)
3. ROLLED_BACK → inverseOperations applied

Alternative Flow:
1. PENDING     → User creates change set
                      ↓
2. FAILED      → Some operations failed
                      ↓
   (partial state - manual intervention may be required)
```

## Complete Example

```json
{
  "$type": "ChangeSet",
  "changeSetId": "880e8400-e29b-41d4-a716-446655440003",
  "timestamp": "2026-01-17T11:00:00Z",
  "actor": {
    "actorType": "USER",
    "actorId": "user-456",
    "actorName": "Jane Smith"
  },
  "description": "Add security-related properties to Employee ObjectType",
  "operations": [
    {
      "operationType": "ADD_PROPERTY",
      "targetApiName": "Employee",
      "payload": {
        "apiName": "securityLevel",
        "dataType": "string",
        "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "SECRET"]
      },
      "sequenceNumber": 0
    },
    {
      "operationType": "ADD_PROPERTY",
      "targetApiName": "Employee",
      "payload": {
        "apiName": "clearanceDate",
        "dataType": "date"
      },
      "sequenceNumber": 1
    }
  ],
  "status": "APPLIED",
  "rollbackInfo": {
    "rollbackable": true,
    "rollbackDeadline": "2026-01-24T11:00:00Z",
    "inverseOperations": [
      {
        "operationType": "REMOVE_PROPERTY",
        "targetApiName": "Employee",
        "payload": { "apiName": "clearanceDate" },
        "sequenceNumber": 0
      },
      {
        "operationType": "REMOVE_PROPERTY",
        "targetApiName": "Employee",
        "payload": { "apiName": "securityLevel" },
        "sequenceNumber": 1
      }
    ]
  }
}
```

---

# Part 4: ExportMetadata

## Definition

JSON 내보내기 메타데이터입니다. Ontology를 JSON 형식으로 내보낼 때 포함되는 메타 정보로, 무결성 검증 및 가져오기 시 필요한 정보를 담고 있습니다.

**Palantir Requirement:** P2-HIGH - Ontology JSON Export/Import

```json
{
  "$type": "ExportMetadata"
}
```

## Schema Structure

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$type` | `const` | Yes | `"ExportMetadata"` |
| `exportId` | `uuid` | Yes | Unique identifier for this export |
| `exportedAt` | `date-time` | Yes | When the export was created |
| `exportedBy` | `string` | No | Who performed the export |
| `schemaVersion` | `string` | Yes | Schema format version |

### Source Information

| Field | Type | Description |
|-------|------|-------------|
| `sourceOntologyRid` | `string` | RID of the source Ontology |
| `sourceOntologyVersion` | `integer` | Version of the source Ontology at export time |

### Export Scope

```json
{
  "exportScope": "FULL",
  "includedTypes": {
    "objectTypes": true,
    "linkTypes": true,
    "actionTypes": true,
    "interfaces": true,
    "valueTypes": true,
    "structTypes": true,
    "sharedProperties": true
  }
}
```

#### exportScope

| Value | Description |
|-------|-------------|
| `FULL` | Complete Ontology export (default) |
| `PARTIAL` | Subset based on filter criteria |
| `DIFF` | Only changes since specified version |

#### includedTypes

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `objectTypes` | `boolean` | `true` | Include ObjectType definitions |
| `linkTypes` | `boolean` | `true` | Include LinkType definitions |
| `actionTypes` | `boolean` | `true` | Include ActionType definitions |
| `interfaces` | `boolean` | `true` | Include Interface definitions |
| `valueTypes` | `boolean` | `true` | Include ValueType definitions |
| `structTypes` | `boolean` | `true` | Include StructType definitions |
| `sharedProperties` | `boolean` | `true` | Include SharedProperty definitions |

### Filter Criteria

부분 내보내기 시 적용되는 필터입니다.

```json
{
  "filterCriteria": {
    "statusFilter": ["ACTIVE", "EXPERIMENTAL"],
    "tagFilter": ["core", "security"],
    "moduleFilter": ["hr", "finance"]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `statusFilter` | `string[]` | Only export entities with these statuses |
| `tagFilter` | `string[]` | Only export entities with these tags |
| `moduleFilter` | `string[]` | Only export entities in these modules |

### Checksums

무결성 검증을 위한 체크섬입니다.

```json
{
  "checksums": {
    "sha256": "abc123def456...",
    "md5": "xyz789..."
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `sha256` | `string` | SHA-256 hash of export content |
| `md5` | `string` | MD5 hash of export content (legacy support) |

### Warnings

내보내기 중 발생한 경고 메시지입니다.

```json
{
  "warnings": [
    "3 deprecated ObjectTypes excluded from export",
    "LinkType 'legacyRelation' references deprecated ObjectType"
  ]
}
```

## Complete Example

```json
{
  "$type": "ExportMetadata",
  "exportId": "660e8400-e29b-41d4-a716-446655440001",
  "exportedAt": "2026-01-17T11:00:00Z",
  "exportedBy": "admin",
  "sourceOntologyRid": "ri.ontology.main.oda-enterprise",
  "sourceOntologyVersion": 42,
  "schemaVersion": "4.0.0",
  "exportScope": "FULL",
  "includedTypes": {
    "objectTypes": true,
    "linkTypes": true,
    "actionTypes": true,
    "interfaces": true,
    "valueTypes": true,
    "structTypes": true,
    "sharedProperties": true
  },
  "checksums": {
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "warnings": []
}
```

---

# Part 5: ProposalMetadata

## Definition

변경 제안서 워크플로우입니다. Ontology에 대한 변경 사항을 제안하고, 검토하고, 승인하고, 실행하는 전체 워크플로우를 관리합니다.

```json
{
  "$type": "ProposalMetadata"
}
```

## ProposalStatus Workflow

```
     ┌──────────────────────────────────────────────────────────┐
     │                                                          │
     │   DRAFT ──────► PENDING ──────► APPROVED ──────► EXECUTED
     │     │              │                │
     │     │              ▼                │
     │     │          REJECTED             │
     │     │              │                │
     │     ▼              ▼                ▼
     │  CANCELLED     CANCELLED        CANCELLED
     │     │              │                │
     │     ▼              ▼                ▼
     └── DELETED ◄── DELETED ◄─────── DELETED
```

### Status Definitions

| Status | Description | Transitions To |
|--------|-------------|----------------|
| `DRAFT` | Initial state, proposal being prepared | `PENDING`, `CANCELLED` |
| `PENDING` | Submitted for review | `APPROVED`, `REJECTED`, `CANCELLED` |
| `APPROVED` | Review passed, ready for execution | `EXECUTED`, `CANCELLED` |
| `REJECTED` | Review failed | `CANCELLED` |
| `EXECUTED` | Changes applied to Ontology | `CANCELLED` (triggers rollback) |
| `CANCELLED` | Proposal abandoned | `DELETED` |
| `DELETED` | Soft-deleted from system | - (terminal) |

## Schema Structure

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$type` | `const` | Yes | `"ProposalMetadata"` |
| `proposalId` | `uuid` | Yes | Unique identifier |
| `title` | `string` | No | Brief title for the proposal |
| `description` | `string` | No | Detailed description of proposed changes |
| `status` | `enum` | Yes | Current workflow status (default: `DRAFT`) |
| `priority` | `enum` | No | Priority level (default: `MEDIUM`) |
| `createdAt` | `date-time` | Yes | Creation timestamp |
| `createdBy` | `string` | Yes | Creator user/system ID |

#### priority

```json
{
  "type": "string",
  "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
  "default": "MEDIUM"
}
```

| Priority | Description |
|----------|-------------|
| `LOW` | Non-urgent change, can wait |
| `MEDIUM` | Standard priority (default) |
| `HIGH` | Important change, needs prompt attention |
| `CRITICAL` | Urgent change, requires immediate review |

### Workflow Timestamps

| Field | Type | Description |
|-------|------|-------------|
| `submittedAt` | `date-time` | When moved from DRAFT to PENDING |
| `reviewedAt` | `date-time` | When review was completed |
| `reviewedBy` | `string` | Who performed the review |
| `reviewComment` | `string` | Reviewer's comment |
| `executedAt` | `date-time` | When changes were applied |
| `executedBy` | `string` | Who executed the proposal |

### Action Reference

| Field | Type | Description |
|-------|------|-------------|
| `actionTypeRef` | `string` | ActionType apiName this proposal is for |
| `payload` | `object` | Action parameters for execution |
| `changeSet` | `ChangeSet` | Changes this proposal will apply |

### ValidationResults

제출 기준 검증 결과입니다.

```json
{
  "validationResults": [
    {
      "criterionApiName": "hasOntologyEditorRole",
      "passed": true,
      "message": "User has Ontology Editor role"
    },
    {
      "criterionApiName": "noBreakingChanges",
      "passed": false,
      "message": "Property removal would break existing consumers"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `criterionApiName` | `string` | Name of the validation criterion |
| `passed` | `boolean` | Whether validation passed |
| `message` | `string` | Validation result message |

### Status History

상태 전이 이력입니다.

```json
{
  "history": [
    {
      "fromStatus": "DRAFT",
      "toStatus": "PENDING",
      "timestamp": "2026-01-17T09:30:00Z",
      "actor": "security-team",
      "comment": "Ready for review"
    },
    {
      "fromStatus": "PENDING",
      "toStatus": "APPROVED",
      "timestamp": "2026-01-17T10:15:00Z",
      "actor": "ontology-admin",
      "comment": "LGTM"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `fromStatus` | `string` | Previous status |
| `toStatus` | `string` | New status |
| `timestamp` | `date-time` | When transition occurred |
| `actor` | `string` | Who triggered the transition |
| `comment` | `string` | Optional comment |

## Complete Example

```json
{
  "$type": "ProposalMetadata",
  "proposalId": "770e8400-e29b-41d4-a716-446655440002",
  "title": "Add Security Markings to Employee ObjectType",
  "description": "Adding mandatory control property for row-level security compliance.",
  "status": "PENDING",
  "priority": "HIGH",
  "createdAt": "2026-01-17T09:00:00Z",
  "createdBy": "security-team",
  "submittedAt": "2026-01-17T09:30:00Z",
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
      "timestamp": "2026-01-17T09:30:00Z",
      "actor": "security-team",
      "comment": "Ready for review"
    }
  ]
}
```

---

## API Reference

### Serialization Methods

메타데이터 타입들은 `OntologyEntity` 기반 클래스의 직렬화 메서드를 사용할 수 있습니다.

#### to_foundry_dict()

Palantir Foundry 호환 딕셔너리 형식으로 내보냅니다.

```python
from ontology_definition.core.base import OntologyEntity

entity = OntologyEntity(
    api_name="MyEntity",
    display_name="My Entity"
)

# Export to Foundry format
foundry_dict = entity.to_foundry_dict()
# Returns:
# {
#   "rid": "ri.ontology.entity.xxx",
#   "apiName": "MyEntity",
#   "displayName": "My Entity",
#   "description": None,
#   "metadata": {
#     "createdAt": "2026-01-17T10:00:00Z",
#     "createdBy": None,
#     "modifiedAt": "2026-01-17T10:00:00Z",
#     "modifiedBy": None,
#     "version": 1
#   }
# }
```

#### from_foundry_dict()

Palantir Foundry JSON 형식에서 인스턴스를 생성합니다.

```python
# Import from Foundry format
data = {
    "rid": "ri.ontology.entity.existing",
    "apiName": "ImportedEntity",
    "displayName": "Imported Entity",
    "metadata": {
        "createdAt": "2026-01-01T00:00:00Z",
        "version": 5
    }
}

entity = OntologyEntity.from_foundry_dict(data)
```

#### touch()

수정 타임스탬프와 버전을 업데이트합니다.

```python
entity.touch(modified_by="user-123")
# Updates:
# - modified_at = current UTC time
# - version = version + 1
# - modified_by = "user-123"
```

### JSON Schema Validation

메타데이터 JSON은 스키마 검증을 통해 유효성을 확인할 수 있습니다.

```python
import json
from jsonschema import validate

# Load schema
with open("Metadata.schema.json") as f:
    schema = json.load(f)

# Validate metadata
metadata = {
    "$type": "OntologyMetadata",
    "apiName": "TestOntology",
    "displayName": "Test Ontology",
    "schemaVersion": "4.0.0"
}

validate(instance=metadata, schema=schema)  # Raises on invalid
```

### Type Discrimination

`$type` 필드를 사용하여 메타데이터 타입을 구분합니다.

```python
def process_metadata(data: dict):
    metadata_type = data.get("$type")

    if metadata_type == "OntologyMetadata":
        return process_ontology_metadata(data)
    elif metadata_type == "AuditLog":
        return process_audit_log(data)
    elif metadata_type == "ChangeSet":
        return process_change_set(data)
    elif metadata_type == "ExportMetadata":
        return process_export_metadata(data)
    elif metadata_type == "ProposalMetadata":
        return process_proposal_metadata(data)
    else:
        raise ValueError(f"Unknown metadata type: {metadata_type}")
```

---

## Related Documentation

- **ObjectType.md** - Entity schema definitions
- **LinkType.md** - Relationship definitions
- **ActionType.md** - Action/mutation definitions
- **Property.md** - Property type definitions

## Schema References

- **Source Schema:** `/docs/research/schemas/Metadata.schema.json`
- **Base Class:** `/ontology_definition/core/base.py`
- **Identifier Utils:** `/ontology_definition/core/identifiers.py`
