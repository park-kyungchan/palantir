---
name: oda-linktype
description: |
  LinkType definition management with 5-Stage Lifecycle Protocol.
  Schema source: ontology_definition/schemas/LinkType.schema.json
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
context: fork
agent: general-purpose
intents:
  korean: ["링크타입", "관계", "연결", "외래키", "참조"]
  english: ["linktype", "link type", "relationship", "foreign key", "reference"]
---

# ODA LinkType Skill

## Purpose

Manage LinkType definitions following 5-Stage Lifecycle:
1. **DEFINE** - Collect relationship specification
2. **VALIDATE** - Verify against JSON Schema
3. **STAGE** - Preview before deployment
4. **REVIEW** - Human approval gate
5. **DEPLOY** - Persist to ontology database

---

## Schema Reference

**Location:** `/home/palantir/park-kyungchan/palantir/ontology_definition/schemas/LinkType.schema.json`

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `id` | `^[a-z][a-z0-9-]*$` | `employee-department` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` | `EmployeeToDepartment` |
| `displayName` | String (1-255) | `Employee to Department` |
| `sourceObjectType` | ObjectTypeReference | `{ "apiName": "Employee" }` |
| `targetObjectType` | ObjectTypeReference | `{ "apiName": "Department" }` |
| `cardinality` | Cardinality object | `{ "type": "MANY_TO_ONE" }` |
| `implementation` | LinkImplementation | Foreign key or backing table config |

### Conditional Requirements

- `status: deprecated` requires `deprecation` with `reason` and `removalDeadline`
- `cardinality.type: MANY_TO_MANY` requires `implementation.type: BACKING_TABLE`

---

## Cardinality Reference

| Type | Source Max | Target Max | Use Case |
|------|------------|------------|----------|
| `ONE_TO_ONE` | 1 | 1 | User to Profile |
| `ONE_TO_MANY` | N | 1 | Department to Employees |
| `MANY_TO_ONE` | 1 | N | Employee to Department |
| `MANY_TO_MANY` | N | N | Projects to Team Members |

### Cardinality Object

```json
{
  "type": "MANY_TO_ONE",
  "sourceMin": 0,
  "sourceMax": 1,
  "targetMin": 0,
  "targetMax": "N",
  "enforced": false
}
```

---

## Implementation Types

### FOREIGN_KEY (1:1, 1:N, N:1)

```json
{
  "implementation": {
    "type": "FOREIGN_KEY",
    "foreignKey": {
      "foreignKeyProperty": "departmentId",
      "foreignKeyLocation": "SOURCE",
      "referencedProperty": "departmentId"
    }
  }
}
```

**FK Location Rules:**
| Cardinality | FK Location |
|-------------|-------------|
| ONE_TO_ONE | Either side |
| ONE_TO_MANY | TARGET |
| MANY_TO_ONE | SOURCE |

### BACKING_TABLE (N:N)

```json
{
  "implementation": {
    "type": "BACKING_TABLE",
    "backingTable": {
      "datasetRid": "ri.foundry.main.dataset.project-team-junction",
      "sourceKeyColumn": "project_id",
      "targetKeyColumn": "member_id",
      "additionalColumns": [
        { "columnName": "role", "propertyApiName": "assignedRole" }
      ]
    }
  }
}
```

---

## Bidirectional Navigation

```json
{
  "forwardApiName": "department",
  "forwardDisplayName": "Department",
  "forwardVisibility": "normal",
  "bidirectional": true,
  "reverseApiName": "employees",
  "reverseDisplayName": "Employees",
  "reverseVisibility": "normal"
}
```

**Visibility:** `prominent`, `normal`, `hidden`

---

## Link Properties (N:N only)

```json
{
  "linkProperties": [
    {
      "apiName": "assignedRole",
      "displayName": "Assigned Role",
      "dataType": "STRING",
      "backingColumn": "role",
      "required": true
    }
  ]
}
```

**DataTypes:** STRING, INTEGER, LONG, FLOAT, DOUBLE, BOOLEAN, DATE, TIMESTAMP

---

## Cascade Policy

```json
{
  "cascadePolicy": {
    "onSourceDelete": "CASCADE",
    "onTargetDelete": "SET_NULL",
    "onSourceUpdate": "CASCADE",
    "onTargetUpdate": "CASCADE"
  }
}
```

**Actions:** `RESTRICT`, `CASCADE`, `SET_NULL`, `SET_DEFAULT`, `NO_ACTION`

---

## Security Configuration

```json
{
  "securityConfig": {
    "inheritSourceSecurity": true,
    "inheritTargetSecurity": false,
    "requireBothVisible": false,
    "linkPropertySecurity": [
      { "propertyApiName": "sensitiveData", "accessLevel": "MASKED" }
    ]
  }
}
```

**Access Levels:** `FULL`, `READ_ONLY`, `MASKED`, `HIDDEN`

---

## 5-Stage Lifecycle Protocol

### Stage 1: DEFINE

1. Basic Identity (id, apiName, displayName)
2. Source/Target ObjectType selection
3. Cardinality configuration
4. Implementation type (FK vs Backing Table)
5. Bidirectional navigation settings

**Output:** `.agent/tmp/staging/<id>.json`

### Stage 2: VALIDATE

**Checks:**
1. Required fields present
2. Pattern validation (id, apiName)
3. ObjectType references exist
4. Cardinality-Implementation compatibility
5. FK property exists on ObjectType
6. Deprecated requires deprecation info

**Output:** Validation report

### Stage 3: STAGE

1. Generate RID: `ri.ontology.main.link-type.{apiName}`
2. Add metadata (timestamps, version)
3. Calculate diff (if modifying)

**Output:** `.agent/tmp/staging/<id>.staged.json`

### Stage 4: REVIEW

Display: Definition summary, cardinality diagram, implementation details

**Approval Prompt:** Approve? [y/n]

### Stage 5: DEPLOY

1. Write to `.agent/tmp/ontology.db`
2. Create audit log entry
3. Register reverse link (if bidirectional)

---

## Actions

| Action | Usage |
|--------|-------|
| `define` | `/linktype define` |
| `validate <path>` | `/linktype validate employee-dept.json` |
| `stage <id>` | `/linktype stage employee-department` |
| `review <id>` | `/linktype review employee-department` |
| `deploy <id>` | `/linktype deploy employee-department` |
| `list` | `/linktype list` |
| `show <id>` | `/linktype show employee-department` |

---

## Example: MANY_TO_ONE (Foreign Key)

```json
{
  "id": "employee-department",
  "apiName": "EmployeeToDepartment",
  "displayName": "Employee to Department",
  "sourceObjectType": { "apiName": "Employee" },
  "targetObjectType": { "apiName": "Department" },
  "cardinality": {
    "type": "MANY_TO_ONE",
    "sourceMin": 0,
    "sourceMax": 1,
    "targetMin": 0,
    "targetMax": "N"
  },
  "implementation": {
    "type": "FOREIGN_KEY",
    "foreignKey": {
      "foreignKeyProperty": "departmentId",
      "foreignKeyLocation": "SOURCE",
      "referencedProperty": "departmentId"
    }
  },
  "bidirectional": true,
  "reverseApiName": "employees",
  "reverseDisplayName": "Employees",
  "cascadePolicy": {
    "onSourceDelete": "CASCADE",
    "onTargetDelete": "SET_NULL"
  },
  "status": "active"
}
```

---

## Example: MANY_TO_MANY (Backing Table)

```json
{
  "id": "project-team-member",
  "apiName": "ProjectToTeamMember",
  "displayName": "Project to Team Member",
  "sourceObjectType": { "apiName": "Project" },
  "targetObjectType": { "apiName": "TeamMember" },
  "cardinality": {
    "type": "MANY_TO_MANY",
    "sourceMin": 0,
    "sourceMax": "N",
    "targetMin": 0,
    "targetMax": "N"
  },
  "implementation": {
    "type": "BACKING_TABLE",
    "backingTable": {
      "datasetRid": "ri.foundry.main.dataset.project-team-junction",
      "sourceKeyColumn": "project_id",
      "targetKeyColumn": "member_id"
    }
  },
  "linkProperties": [
    {
      "apiName": "assignedRole",
      "displayName": "Assigned Role",
      "dataType": "STRING",
      "backingColumn": "role",
      "required": true
    }
  ],
  "bidirectional": true,
  "reverseApiName": "projects",
  "status": "active"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field not present |
| `INVALID_PATTERN` | Value doesn't match regex |
| `OBJECTTYPE_NOT_FOUND` | Referenced ObjectType doesn't exist |
| `INVALID_CARDINALITY_IMPL` | MANY_TO_MANY requires BACKING_TABLE |
| `FK_PROPERTY_NOT_FOUND` | FK property not on ObjectType |
| `BACKING_TABLE_REQUIRED` | Missing backingTable config |
| `DEPRECATED_MISSING_INFO` | Deprecated without deprecation |
| `APPROVAL_REQUIRED` | Deploy without approval |

---

## Database Operations

### Schema

```sql
CREATE TABLE IF NOT EXISTS link_types (
    id TEXT PRIMARY KEY,
    api_name TEXT UNIQUE NOT NULL,
    source_object_type TEXT NOT NULL,
    target_object_type TEXT NOT NULL,
    cardinality TEXT NOT NULL,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);
```

### Insert

```python
cursor.execute("""
    INSERT OR REPLACE INTO link_types
    (id, api_name, source_object_type, target_object_type, cardinality, definition, created_at, modified_at, version)
    VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1)
""", (
    definition["id"],
    definition["apiName"],
    definition["sourceObjectType"]["apiName"],
    definition["targetObjectType"]["apiName"],
    definition["cardinality"]["type"],
    json.dumps(definition)
))
```

---

## Validation

### ObjectType Existence Check

```python
def validate_objecttype_exists(api_name: str) -> bool:
    conn = sqlite3.connect(".agent/tmp/ontology.db")
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM object_types WHERE api_name = ?", (api_name,))
    return cursor.fetchone() is not None
```

### Cardinality-Implementation Check

```python
def validate_cardinality_impl(definition: dict) -> list[str]:
    errors = []
    if definition["cardinality"]["type"] == "MANY_TO_MANY":
        if definition["implementation"]["type"] != "BACKING_TABLE":
            errors.append("MANY_TO_MANY requires BACKING_TABLE")
    return errors
```

---

## Audit Log Format

```json
{
  "timestamp": "2026-01-18T10:00:00Z",
  "action": "linktype.deploy",
  "resource_id": "employee-department",
  "details": {
    "apiName": "EmployeeToDepartment",
    "sourceObjectType": "Employee",
    "targetObjectType": "Department",
    "cardinality": "MANY_TO_ONE"
  }
}
```

---

## TodoWrite Integration

```json
[
  {"content": "[Stage 1] Define LinkType: employee-department", "status": "completed", "activeForm": "Defining LinkType"},
  {"content": "[Stage 2] Validate source/target ObjectTypes", "status": "in_progress", "activeForm": "Validating references"},
  {"content": "[Stage 3] Stage for review", "status": "pending", "activeForm": "Staging definition"},
  {"content": "[Stage 4] Review cardinality and implementation", "status": "pending", "activeForm": "Reviewing definition"},
  {"content": "[Stage 5] Deploy to database", "status": "pending", "activeForm": "Deploying definition"}
]
```

---

## Visual Cardinality

```
ONE_TO_ONE:    [Source] 1 ──── 1 [Target]
ONE_TO_MANY:   [Source] 1 ──── * [Target]
MANY_TO_ONE:   [Source] * ──── 1 [Target]
MANY_TO_MANY:  [Source] * ──── * [Target] (backing table)
```

---

## Common Patterns

### Self-Referential Link

```json
{
  "id": "employee-manager",
  "sourceObjectType": { "apiName": "Employee" },
  "targetObjectType": { "apiName": "Employee" },
  "cardinality": { "type": "MANY_TO_ONE" },
  "reverseApiName": "directReports"
}
```

### Required vs Optional

- `sourceMin: 0` = Optional link
- `sourceMin: 1` = Required link

---

## Integration Paths

| Path | Purpose |
|------|---------|
| `.agent/tmp/ontology.db` | Database |
| `.agent/tmp/staging/<id>.json` | Staging |
| `.agent/logs/ontology_changes.log` | Audit |

### Related Skills

- `oda-objecttype` - ObjectType definitions
- `oda-property` - Property definitions
- `oda-actiontype` - ActionType definitions
- `oda-interface` - Interface definitions
