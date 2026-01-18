---
name: oda-actiontype
description: |
  ActionType definition management with 5-Stage Lifecycle Protocol.
  Schema source: ontology_definition/schemas/ActionType.schema.json
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
context: fork
agent: general-purpose
intents:
  korean: ["액션타입", "액션", "동작", "실행", "hazardous"]
  english: ["actiontype", "action type", "action", "executable", "hazardous action"]
---

# ODA ActionType Skill

## Purpose

Manage ActionType definitions following 5-Stage Lifecycle:
1. **DEFINE** - Collect specification
2. **VALIDATE** - Verify against JSON Schema
3. **STAGE** - Preview before deployment
4. **REVIEW** - Human approval gate (critical for hazardous actions)
5. **DEPLOY** - Persist to ontology database

---

## Schema Reference

**Location:** `/home/palantir/park-kyungchan/palantir/ontology_definition/schemas/ActionType.schema.json`

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `id` | `^[a-z][a-z0-9-]*$` | `file-modify`, `assign-employee` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_.]*$` | `file.modify`, `assignEmployee` |
| `displayName` | String (1-255) | `Modify File` |
| `affectedObjectTypes` | Array (minItems: 1) | See AffectedObjectType |
| `implementation` | ActionImplementation | `{ "type": "DECLARATIVE" }` |

### Conditional Requirements

When `status: deprecated`, requires `deprecation` with:
- `reason` (required)
- `removalDeadline` (required, ISO 8601)

---

## Hazardous Actions

Actions marked `hazardous: true` require **Proposal workflow** before execution:

```json
{ "hazardous": true }
```

### Common Hazardous Actions
- `file.modify`, `file.delete` - File operations
- `git.commit` - Git operations
- `db.migrate` - Database changes

---

## ActionParameter Reference

### ParameterDataType

| Type | Additional Fields |
|------|-------------------|
| `STRING`, `INTEGER`, `LONG`, `FLOAT`, `DOUBLE`, `BOOLEAN`, `DATE`, `TIMESTAMP` | None |
| `ARRAY` | `arrayItemType` |
| `OBJECT_PICKER`, `OBJECT_SET` | `objectTypeRef` |
| `STRUCT` | `structDefinition` |
| `ATTACHMENT` | None |

### Parameter Example

```json
{
  "apiName": "filePath",
  "displayName": "File Path",
  "dataType": { "type": "STRING" },
  "required": true,
  "constraints": { "pattern": "^[a-zA-Z0-9/_.-]+$" }
}
```

### ParameterConstraints

```json
{
  "enum": ["A", "B"],
  "minValue": 0, "maxValue": 100,
  "minLength": 1, "maxLength": 255,
  "pattern": "^[a-zA-Z0-9]+$"
}
```

---

## AffectedObjectType

```json
{
  "objectTypeApiName": "File",
  "operations": ["CREATE", "MODIFY", "DELETE"],
  "modifiableProperties": ["content", "modifiedAt"]
}
```

---

## EditSpecification

### Operation Types
`CREATE_OBJECT`, `MODIFY_OBJECT`, `CREATE_OR_MODIFY_OBJECT`, `DELETE_OBJECT`, `CREATE_LINK`, `DELETE_LINK`, `FUNCTION_RULE`, `MODIFY_PROPERTY`

### Example

```json
{
  "operationType": "MODIFY_OBJECT",
  "targetObjectType": "File",
  "objectSelection": {
    "selectionType": "QUERY",
    "queryExpression": "path == $filePath"
  },
  "propertyMappings": [
    { "targetProperty": "content", "sourceParameter": "content" }
  ]
}
```

---

## SubmissionCriteria

### Criterion Types
`PARAMETER_VALIDATION`, `OBJECT_STATE_CHECK`, `PERMISSION_CHECK`, `CARDINALITY_CHECK`, `CUSTOM_FUNCTION`

### Example

```json
{
  "apiName": "fileExists",
  "criterionType": "OBJECT_STATE_CHECK",
  "expression": "File.exists($filePath)",
  "errorMessage": "File does not exist.",
  "severity": "ERROR"
}
```

### Condition Operators
`IS`, `IS_NOT`, `MATCHES_REGEX`, `LT`, `LTE`, `GT`, `GTE`, `INCLUDES`, `IS_EMPTY`, `IS_NOT_EMPTY`

---

## SideEffects

### Effect Types
`NOTIFICATION`, `WEBHOOK`, `EMAIL`, `AUDIT_LOG`, `TRIGGER_ACTION`, `CUSTOM_FUNCTION`

### Example

```json
{
  "apiName": "notifyOwner",
  "effectType": "NOTIFICATION",
  "configuration": {
    "notificationConfig": {
      "recipientExpression": "File.getOwner($filePath)",
      "messageTemplate": "File modified: ${filePath}",
      "channel": "IN_APP"
    }
  },
  "async": true
}
```

---

## ActionImplementation

| Type | Description |
|------|-------------|
| `DECLARATIVE` | Rule-based via EditSpecifications |
| `FUNCTION_BACKED` | Custom function (requires `functionRef`) |
| `INLINE_EDIT` | Inline property editing |

### FUNCTION_BACKED Example

```json
{
  "type": "FUNCTION_BACKED",
  "functionRef": "lib.oda.actions.file.modify_file",
  "functionLanguage": "PYTHON",
  "functionConfig": { "timeout": 30000 }
}
```

---

## 5-Stage Lifecycle Protocol

### Stage 1: DEFINE

**Interactive Flow:**
1. Basic Identity (id, apiName, displayName)
2. Hazardous flag configuration
3. Parameters definition
4. Affected ObjectTypes
5. Implementation type

**Output:** `.agent/tmp/staging/<id>.json`

### Stage 2: VALIDATE

**Checks:**
1. Required fields present
2. Pattern validation (id, apiName)
3. Parameter dataType consistency
4. AffectedObjectTypes (min 1)
5. Implementation type validation

**Output:** Validation report (pass/fail + errors)

### Stage 3: STAGE

**Actions:**
1. Generate RID: `ri.ontology.main.action-type.{apiName}`
2. Add metadata (timestamps, version)
3. Calculate diff (if modifying existing)

**Output:** `.agent/tmp/staging/<id>.staged.json`

### Stage 4: REVIEW

**Display:**
- Definition summary
- **Hazardous warning** (if applicable)
- Parameters table
- Affected ObjectTypes

**Approval:** `Approve? [y/n]` (elevated for hazardous)

### Stage 5: DEPLOY

**Actions:**
1. Write to `.agent/tmp/ontology.db`
2. Create audit log entry
3. Register with Proposal system (if hazardous)

---

## Actions

| Action | Usage |
|--------|-------|
| `define` | Interactive creation |
| `validate <json>` | Validate against schema |
| `stage <id>` | Stage for review |
| `review <id>` | Approve staged changes |
| `deploy <id>` | Deploy to database |
| `list` | List all ActionTypes |
| `show <id>` | Show details |

---

## Example: Hazardous ActionType

```json
{
  "id": "file-modify",
  "apiName": "file.modify",
  "displayName": "Modify File",
  "category": "file",
  "hazardous": true,
  "parameters": [
    {
      "apiName": "filePath",
      "displayName": "File Path",
      "dataType": { "type": "STRING" },
      "required": true
    },
    {
      "apiName": "content",
      "displayName": "New Content",
      "dataType": { "type": "STRING" },
      "required": true
    }
  ],
  "affectedObjectTypes": [
    {
      "objectTypeApiName": "File",
      "operations": ["MODIFY"],
      "modifiableProperties": ["content", "modifiedAt"]
    }
  ],
  "editSpecifications": [
    {
      "operationType": "MODIFY_OBJECT",
      "targetObjectType": "File",
      "objectSelection": {
        "selectionType": "QUERY",
        "queryExpression": "path == $filePath"
      },
      "propertyMappings": [
        { "targetProperty": "content", "sourceParameter": "content" }
      ]
    }
  ],
  "submissionCriteria": [
    {
      "apiName": "fileExists",
      "criterionType": "OBJECT_STATE_CHECK",
      "expression": "File.exists($filePath)",
      "errorMessage": "File does not exist."
    }
  ],
  "implementation": {
    "type": "FUNCTION_BACKED",
    "functionRef": "lib.oda.actions.file.modify_file",
    "functionLanguage": "PYTHON"
  },
  "permissions": {
    "requiredRoles": ["Developer", "Admin"],
    "objectTypePermissions": [
      { "objectTypeApiName": "File", "requiredAccess": "WRITE" }
    ]
  },
  "auditConfig": {
    "enabled": true,
    "logLevel": "DETAILED"
  },
  "undoConfig": {
    "undoable": true,
    "undoWindowMinutes": 60,
    "undoStrategy": "RESTORE_SNAPSHOT"
  },
  "status": "active"
}
```

---

## Example: Non-Hazardous ActionType

```json
{
  "id": "assign-employee",
  "apiName": "assignEmployee",
  "displayName": "Assign Employee",
  "category": "project",
  "hazardous": false,
  "parameters": [
    {
      "apiName": "employee",
      "displayName": "Employee",
      "dataType": { "type": "OBJECT_PICKER", "objectTypeRef": "Employee" },
      "required": true
    },
    {
      "apiName": "project",
      "displayName": "Project",
      "dataType": { "type": "OBJECT_PICKER", "objectTypeRef": "Project" },
      "required": true
    }
  ],
  "affectedObjectTypes": [
    { "objectTypeApiName": "Employee", "operations": ["MODIFY"] },
    { "objectTypeApiName": "Project", "operations": ["MODIFY"] }
  ],
  "editSpecifications": [
    {
      "operationType": "CREATE_LINK",
      "targetLinkType": "ProjectToTeamMember",
      "linkSelection": {
        "sourceObjectParameter": "project",
        "targetObjectParameter": "employee"
      }
    }
  ],
  "implementation": { "type": "DECLARATIVE" },
  "status": "active"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field not present |
| `INVALID_PATTERN` | Value doesn't match regex |
| `INVALID_PARAMETER_TYPE` | Unknown parameter dataType |
| `MISSING_OBJECT_TYPE_REF` | OBJECT_PICKER without objectTypeRef |
| `NO_AFFECTED_OBJECT_TYPES` | Empty affectedObjectTypes |
| `INVALID_IMPLEMENTATION` | Unknown implementation type |
| `DEPRECATED_MISSING_INFO` | Deprecated without deprecation |
| `APPROVAL_REQUIRED` | Deploy without approval |

---

## Database Operations

### Schema

```sql
CREATE TABLE IF NOT EXISTS action_types (
    id TEXT PRIMARY KEY,
    api_name TEXT UNIQUE NOT NULL,
    hazardous BOOLEAN DEFAULT FALSE,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);
```

### Insert

```python
cursor.execute("""
    INSERT OR REPLACE INTO action_types
    (id, api_name, hazardous, definition, created_at, modified_at, version)
    VALUES (?, ?, ?, ?, datetime('now'), datetime('now'), 1)
""", (definition["id"], definition["apiName"],
      definition.get("hazardous", False), json.dumps(definition)))
```

---

## Audit Log Format

```json
{
  "timestamp": "2026-01-18T10:00:00Z",
  "action": "actiontype.deploy",
  "resource_id": "file-modify",
  "details": {
    "apiName": "file.modify",
    "hazardous": true,
    "version": 1
  }
}
```

---

## TodoWrite Integration

```json
[
  {"content": "[Stage 1] Define ActionType: file-modify", "status": "completed", "activeForm": "Defining ActionType"},
  {"content": "[Stage 2] Validate against schema", "status": "in_progress", "activeForm": "Validating schema"},
  {"content": "[Stage 3] Stage for review", "status": "pending", "activeForm": "Staging definition"},
  {"content": "[Stage 4] Review (HAZARDOUS)", "status": "pending", "activeForm": "Reviewing hazardous action"},
  {"content": "[Stage 5] Deploy to database", "status": "pending", "activeForm": "Deploying definition"}
]
```

---

## Proposal Integration

When hazardous ActionType is deployed, it registers with the Proposal system:

```python
# After deploy, if hazardous
if definition.get("hazardous"):
    mcp__oda_ontology__execute_action(
        action_type="actiontype.register_hazardous",
        payload={"apiName": definition["apiName"]}
    )
```

### Runtime Execution

```python
# 1. Create proposal
proposal = mcp__oda_ontology__create_proposal(
    action_type="file.modify",
    payload={"filePath": "...", "content": "..."}
)

# 2. Await approval (interactive)

# 3. Execute after approval
mcp__oda_ontology__execute_proposal(proposal_id=proposal["id"])
```

---

## Related Skills

- `oda-objecttype` - ObjectType definitions
- `oda-linktype` - LinkType definitions
- `oda-property` - Property management
- `oda-interface` - Interface definitions

---

## Best Practices

1. **Set hazardous appropriately** - File/DB changes = true
2. **Include SubmissionCriteria** - Validate before execution
3. **Enable audit for hazardous** - `auditConfig.enabled: true`
4. **Provide undo config** - For reversible actions
