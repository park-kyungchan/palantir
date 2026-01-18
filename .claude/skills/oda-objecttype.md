---
name: oda-objecttype
description: |
  ObjectType definition management with 5-Stage Lifecycle Protocol.
  Schema source: ontology_definition/schemas/ObjectType.schema.json
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
context: fork
agent: general-purpose
intents:
  korean: ["객체타입", "오브젝트타입", "엔티티", "스키마"]
  english: ["objecttype", "object type", "entity", "schema definition"]
---

# ODA ObjectType Skill

## Purpose

Manage ObjectType definitions following 5-Stage Lifecycle:
1. **DEFINE** - Collect specification
2. **VALIDATE** - Verify against JSON Schema
3. **STAGE** - Preview before deployment
4. **REVIEW** - Human approval gate
5. **DEPLOY** - Persist to ontology database

---

## Schema Reference

**Location:** `/home/palantir/park-kyungchan/palantir/ontology_definition/schemas/ObjectType.schema.json`

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `id` | `^[a-z][a-z0-9-]*$` | `employee`, `flight-log` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` | `Employee`, `FlightLog` |
| `displayName` | String (1-255) | `Employee` |
| `primaryKey` | PrimaryKeyDefinition | `{ "propertyApiName": "id" }` |
| `properties` | Array (minItems: 1) | See PropertyReference |

### Conditional Requirements

When `status: deprecated`, requires `deprecation` with:
- `reason` (required)
- `removalDeadline` (required, ISO 8601)

---

## DataType Reference

### Base Types

| Type | Required Fields |
|------|-----------------|
| STRING, INTEGER, LONG, BOOLEAN | None |
| ARRAY | `arrayItemType` |
| STRUCT | `structFields` (1-10 items) |
| VECTOR | `vectorDimension` |
| DECIMAL | `precision`, `scale` (optional) |

### ARRAY Example
```json
{ "type": "ARRAY", "arrayItemType": { "type": "STRING" } }
```

### STRUCT Example
```json
{
  "type": "STRUCT",
  "structFields": [
    { "id": "street", "apiName": "street", "displayName": "Street", "dataType": { "type": "STRING" } }
  ]
}
```

### Full Type List
STRING, INTEGER, SHORT, BYTE, LONG, FLOAT, DOUBLE, DECIMAL, BOOLEAN, DATE, TIMESTAMP, DATETIME, ARRAY, STRUCT, VECTOR, GEOPOINT, GEOSHAPE, MEDIA_REFERENCE, TIME_SERIES, ATTACHMENT, MARKING, CIPHER, JSON, MARKDOWN, BINARY

---

## PropertyReference

### Required Property Fields

| Field | Pattern |
|-------|---------|
| `id` | `^[a-z][a-z0-9-]*$` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` |
| `displayName` | String |
| `dataType` | DataType object |

### PropertyConstraints

```json
{
  "required": true,
  "unique": false,
  "immutable": false,
  "enum": ["A", "B"],
  "minValue": 0,
  "maxValue": 100,
  "minLength": 1,
  "maxLength": 255,
  "pattern": "^[A-Z]{2}\\d{4}$"
}
```

---

## 5-Stage Lifecycle Protocol

### Stage 1: DEFINE

**Interactive Flow:**
1. Basic Identity (id, apiName, displayName)
2. Properties definition
3. Primary key selection
4. Optional configuration

**Output:** `.agent/tmp/staging/<id>.json`

### Stage 2: VALIDATE

**Checks:**
1. Required fields present
2. Pattern validation (id, apiName)
3. Property validation (min 1 property)
4. Conditional validation (deprecated -> deprecation)
5. DataType-specific (ARRAY needs arrayItemType, etc.)

**Output:** Validation report (pass/fail + errors)

### Stage 3: STAGE

**Actions:**
1. Generate RID: `ri.ontology.main.object-type.{apiName}`
2. Add metadata (timestamps, version)
3. Calculate diff (if modifying existing)

**Output:** `.agent/tmp/staging/<id>.staged.json`

### Stage 4: REVIEW

**Display:**
- Complete definition summary
- Properties table
- Security configuration
- Diff from existing (if applicable)

**Approval Prompt:** Approve? [y/n]

### Stage 5: DEPLOY

**Actions:**
1. Write to `.agent/tmp/ontology.db`
2. Create audit log entry
3. Update registry

---

## Actions

### define
Interactive ObjectType creation.
```bash
/objecttype define
```

### validate <json_path>
Validate JSON against schema.
```bash
/objecttype validate employee.json
```

### stage <id>
Stage validated definition.
```bash
/objecttype stage employee
```

### review <id>
Review and approve.
```bash
/objecttype review employee
```

### deploy <id>
Deploy approved definition.
```bash
/objecttype deploy employee
```

### list
List all ObjectTypes.
```bash
/objecttype list
```

**Output:**
| ID | API Name | Status | Properties | Version |
|----|----------|--------|------------|---------|
| employee | Employee | active | 5 | 3 |

### show <id>
Show ObjectType details.
```bash
/objecttype show employee
```

---

## Output Formats

### Success Response
```json
{
  "status": "success",
  "action": "deploy",
  "objectType": {
    "id": "employee",
    "apiName": "Employee",
    "rid": "ri.ontology.main.object-type.Employee"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "errors": [
    { "code": "MISSING_REQUIRED_FIELD", "path": "$.primaryKey", "message": "primaryKey is required" }
  ]
}
```

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
- `oda-property` - Property management
- `oda-interface` - Interface definitions
- `oda-actiontype` - ActionType definitions
- `oda-linktype` - LinkType definitions

---

## Example: Complete ObjectType

```json
{
  "id": "employee",
  "apiName": "Employee",
  "displayName": "Employee",
  "primaryKey": { "propertyApiName": "employeeId" },
  "properties": [
    {
      "id": "employee-id",
      "apiName": "employeeId",
      "displayName": "Employee ID",
      "dataType": { "type": "STRING" },
      "constraints": { "required": true, "unique": true }
    },
    {
      "id": "full-name",
      "apiName": "fullName",
      "displayName": "Full Name",
      "dataType": { "type": "STRING" },
      "constraints": { "required": true, "maxLength": 255 }
    },
    {
      "id": "department",
      "apiName": "department",
      "displayName": "Department",
      "dataType": { "type": "STRING" },
      "constraints": { "enum": ["Engineering", "Sales", "HR"] }
    }
  ],
  "status": "active"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field not present |
| `INVALID_PATTERN` | Value doesn't match regex |
| `ARRAY_MISSING_ITEM_TYPE` | ARRAY without arrayItemType |
| `STRUCT_MISSING_FIELDS` | STRUCT without structFields |
| `VECTOR_MISSING_DIMENSION` | VECTOR without vectorDimension |
| `DEPRECATED_MISSING_INFO` | Deprecated without deprecation info |
| `PRIMARYKEY_NOT_FOUND` | Primary key references missing property |
| `APPROVAL_REQUIRED` | Deploy without approval |

---

## Security Configuration

ObjectTypes support comprehensive security via `securityConfig`:

### Mandatory Control Properties

Properties marked `isMandatoryControl: true` enforce row-level security.

```json
{
  "securityConfig": {
    "mandatoryControlProperties": [
      {
        "propertyApiName": "securityMarkings",
        "controlType": "MARKINGS",
        "markingColumnMapping": "security_markings"
      }
    ]
  }
}
```

**Control Types:** `MARKINGS`, `ORGANIZATIONS`, `CLASSIFICATIONS`

### Property Security Policies

```json
{
  "propertySecurityPolicies": [
    {
      "propertyApiName": "salary",
      "accessLevel": "MASKED",
      "maskingPattern": "***"
    }
  ]
}
```

**Access Levels:** `FULL`, `READ_ONLY`, `MASKED`, `HIDDEN`

---

## Backing Dataset Configuration

```json
{
  "backingDataset": {
    "datasetRid": "ri.foundry.main.dataset.abc123",
    "mode": "SINGLE",
    "objectStorageVersion": "V2",
    "restrictedViewRid": "ri.foundry.main.restricted-view.xyz789"
  }
}
```

**Modes:** `SINGLE`, `MULTI` (for Multi-Dataset Objects)

---

## Interface Implementation

ObjectTypes can implement interfaces for polymorphism:

```json
{
  "interfaces": [
    {
      "interfaceApiName": "Auditable",
      "propertyMappings": [
        {
          "interfaceSharedPropertyApiName": "createdAt",
          "objectPropertyApiName": "creationDate"
        }
      ]
    }
  ]
}
```

---

## Validation Execution

### Using JSON Schema Validator

```python
import json
import jsonschema

schema_path = "ontology_definition/schemas/ObjectType.schema.json"
with open(schema_path) as f:
    schema = json.load(f)

definition_path = ".agent/tmp/staging/employee.json"
with open(definition_path) as f:
    definition = json.load(f)

try:
    jsonschema.validate(definition, schema)
    print("Validation passed")
except jsonschema.ValidationError as e:
    print(f"Validation failed: {e.message}")
```

### CLI Validation

```bash
python -c "
import json, jsonschema
schema = json.load(open('ontology_definition/schemas/ObjectType.schema.json'))
definition = json.load(open('$FILE'))
jsonschema.validate(definition, schema)
print('Valid')
"
```

---

## Database Operations

### Schema

```sql
CREATE TABLE IF NOT EXISTS object_types (
    id TEXT PRIMARY KEY,
    api_name TEXT UNIQUE NOT NULL,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);
```

### Insert

```python
import sqlite3
import json

conn = sqlite3.connect(".agent/tmp/ontology.db")
cursor = conn.cursor()
cursor.execute("""
    INSERT OR REPLACE INTO object_types
    (id, api_name, definition, created_at, modified_at, version)
    VALUES (?, ?, ?, datetime('now'), datetime('now'), 1)
""", (
    definition["id"],
    definition["apiName"],
    json.dumps(definition)
))
conn.commit()
```

### Query

```python
cursor.execute("SELECT definition FROM object_types WHERE id = ?", (id,))
row = cursor.fetchone()
if row:
    definition = json.loads(row[0])
```

---

## Audit Log Format

```json
{
  "timestamp": "2026-01-18T10:00:00Z",
  "action": "objecttype.deploy",
  "resource_id": "employee",
  "user": "agent",
  "details": {
    "apiName": "Employee",
    "version": 1,
    "properties_count": 5
  }
}
```

---

## Anti-Hallucination Rule

**CRITICAL:** All operations MUST reference actual files.

```python
if not evidence.get("source_file") and not evidence.get("user_input"):
    raise AntiHallucinationError("Operation without evidence source")
```

---

## TodoWrite Integration

Track lifecycle progress:

```json
[
  {"content": "[Stage 1] Define ObjectType: employee", "status": "completed", "activeForm": "Defining ObjectType"},
  {"content": "[Stage 2] Validate against schema", "status": "in_progress", "activeForm": "Validating schema"},
  {"content": "[Stage 3] Stage for review", "status": "pending", "activeForm": "Staging definition"},
  {"content": "[Stage 4] Review and approve", "status": "pending", "activeForm": "Reviewing definition"},
  {"content": "[Stage 5] Deploy to database", "status": "pending", "activeForm": "Deploying definition"}
]
```
