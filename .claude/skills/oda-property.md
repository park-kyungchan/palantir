---
name: oda-property
description: |
  Property definition management with 5-Stage Lifecycle Protocol.
  Schema source: ontology_definition/schemas/Property.schema.json
  Supports: SharedProperty, ValueType, StructType
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
context: fork
agent: general-purpose
intents:
  korean: ["속성", "프로퍼티", "공유속성", "값타입", "구조체"]
  english: ["property", "sharedproperty", "valuetype", "structtype", "constraint"]
---

# ODA Property Skill

## Purpose

Manage Property definitions following 5-Stage Lifecycle:
1. **DEFINE** - Collect specification
2. **VALIDATE** - Verify against JSON Schema
3. **STAGE** - Preview before deployment
4. **REVIEW** - Human approval gate
5. **DEPLOY** - Persist to ontology database

---

## Schema Reference

**Location:** `/home/palantir/park-kyungchan/palantir/ontology_definition/schemas/Property.schema.json`

### Property Types Overview

| Type | `$type` Value | Purpose |
|------|---------------|---------|
| SharedProperty | `SharedProperty` | Reusable property across ObjectTypes |
| ValueType | `ValueType` | Custom constrained types |
| StructType | `StructType` | Complex nested structures |

---

## SharedProperty

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `$type` | `SharedProperty` | `"SharedProperty"` |
| `id` | `^[a-z][a-z0-9-]*$` | `created-at`, `security-markings` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` | `createdAt`, `securityMarkings` |
| `displayName` | String (1-255) | `Created At` |
| `dataType` | DataType object | `{ "type": "TIMESTAMP" }` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | String (max 4096) | Documentation |
| `aliases` | String[] | Alternative names |
| `visibility` | enum | `prominent`, `normal`, `hidden` |
| `constraints` | PropertyConstraints | Validation rules |
| `valueFormatting` | ValueFormatting | Display formatting |
| `renderHints` | RenderHints | UI hints |
| `semanticType` | enum | Semantic meaning (IDENTIFIER, NAME, etc.) |
| `isMandatoryControl` | boolean | Security marking property |
| `status` | enum | `experimental`, `active`, `deprecated` |

### Semantic Types

```
IDENTIFIER, NAME, DESCRIPTION, TIMESTAMP, CREATED_AT, MODIFIED_AT,
CREATED_BY, MODIFIED_BY, STATUS, CATEGORY, TAG, URL, EMAIL, PHONE,
ADDRESS, CURRENCY, PERCENTAGE, SECURITY_MARKING, CUSTOM
```

### SharedProperty Example

```json
{
  "$type": "SharedProperty",
  "id": "created-at",
  "apiName": "createdAt",
  "displayName": "Created At",
  "description": "Timestamp when this object was created.",
  "dataType": { "type": "TIMESTAMP" },
  "constraints": {
    "required": true,
    "immutable": true
  },
  "semanticType": "CREATED_AT",
  "status": "active"
}
```

### Security Marking SharedProperty

```json
{
  "$type": "SharedProperty",
  "id": "security-markings",
  "apiName": "securityMarkings",
  "displayName": "Security Markings",
  "dataType": {
    "type": "ARRAY",
    "arrayItemType": { "type": "STRING" }
  },
  "constraints": {
    "required": true,
    "arrayUnique": true
  },
  "isMandatoryControl": true,
  "mandatoryControlConfig": {
    "controlType": "MARKINGS",
    "markingColumnType": "STRING_ARRAY",
    "enforcementLevel": "STRICT"
  },
  "semanticType": "SECURITY_MARKING",
  "status": "active"
}
```

---

## ValueType

Custom types derived from base types with additional constraints.

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `$type` | `ValueType` | `"ValueType"` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` | `EmailAddress`, `PositiveInteger` |
| `displayName` | String (1-255) | `Email Address` |
| `baseType` | enum | `STRING`, `INTEGER`, etc. |
| `constraints` | ValueTypeConstraints | At least one constraint |

### Base Types

```
STRING, INTEGER, SHORT, BYTE, LONG, FLOAT, DOUBLE,
BOOLEAN, DATE, TIMESTAMP, DATETIME, DECIMAL, ARRAY, STRUCT
```

### ValueType Constraints

| Constraint | Type | Applies To |
|------------|------|------------|
| `enum` | array | All types |
| `enumCaseSensitive` | boolean | STRING enums |
| `minValue` | number | Numeric types |
| `maxValue` | number | Numeric types |
| `minLength` | integer | STRING |
| `maxLength` | integer | STRING |
| `pattern` | regex | STRING |
| `regexMatchSubstring` | boolean | STRING regex |
| `ridFormat` | boolean | STRING |
| `uuidFormat` | boolean | STRING |
| `emailFormat` | boolean | STRING |
| `urlFormat` | boolean | STRING |
| `dateFormat` | string | DATE types |
| `arrayUnique` | boolean | ARRAY |
| `arrayMinItems` | integer | ARRAY |
| `arrayMaxItems` | integer | ARRAY |
| `arrayElementConstraints` | nested | ARRAY elements |

### ValueType Examples

**Email Address:**
```json
{
  "$type": "ValueType",
  "apiName": "EmailAddress",
  "displayName": "Email Address",
  "description": "Valid email address format.",
  "baseType": "STRING",
  "constraints": {
    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
    "maxLength": 255,
    "emailFormat": true
  },
  "status": "active"
}
```

**Positive Integer:**
```json
{
  "$type": "ValueType",
  "apiName": "PositiveInteger",
  "displayName": "Positive Integer",
  "description": "Integer greater than zero.",
  "baseType": "INTEGER",
  "constraints": {
    "minValue": 1
  },
  "status": "active"
}
```

**Priority Enum:**
```json
{
  "$type": "ValueType",
  "apiName": "Priority",
  "displayName": "Priority Level",
  "description": "Task or item priority level.",
  "baseType": "STRING",
  "constraints": {
    "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
  },
  "status": "active"
}
```

**Phone Number:**
```json
{
  "$type": "ValueType",
  "apiName": "PhoneNumber",
  "displayName": "Phone Number",
  "baseType": "STRING",
  "constraints": {
    "pattern": "^\\+?[1-9]\\d{1,14}$",
    "minLength": 7,
    "maxLength": 16
  },
  "status": "active"
}
```

**Percentage:**
```json
{
  "$type": "ValueType",
  "apiName": "Percentage",
  "displayName": "Percentage",
  "baseType": "DOUBLE",
  "constraints": {
    "minValue": 0,
    "maxValue": 100
  },
  "status": "active"
}
```

---

## StructType

Complex nested structures with multiple fields.

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `$type` | `StructType` | `"StructType"` |
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` | `Address`, `MonetaryAmount` |
| `displayName` | String (1-255) | `Address` |
| `fields` | StructField[] (1-10) | See StructField |

### StructField Definition

| Field | Required | Pattern |
|-------|----------|---------|
| `id` | Yes | `^[a-z][a-z0-9-]*$` |
| `apiName` | Yes | `^[a-zA-Z][a-zA-Z0-9_]*$` |
| `displayName` | Yes | String |
| `dataType` | Yes | StructFieldDataType |
| `required` | No | boolean (default: false) |
| `defaultValue` | No | any |
| `constraints` | No | PropertyConstraints |

### StructField DataTypes (Restricted)

Struct fields support limited types (no nesting, no arrays):
```
BOOLEAN, BYTE, DATE, DECIMAL, DOUBLE, FLOAT,
GEOPOINT, INTEGER, LONG, SHORT, STRING, TIMESTAMP
```

### StructType Examples

**Address:**
```json
{
  "$type": "StructType",
  "apiName": "Address",
  "displayName": "Address",
  "description": "Physical or mailing address.",
  "fields": [
    {
      "id": "street",
      "apiName": "street",
      "displayName": "Street",
      "dataType": { "type": "STRING" },
      "required": true,
      "constraints": { "maxLength": 255 }
    },
    {
      "id": "city",
      "apiName": "city",
      "displayName": "City",
      "dataType": { "type": "STRING" },
      "required": true,
      "constraints": { "maxLength": 100 }
    },
    {
      "id": "state",
      "apiName": "state",
      "displayName": "State/Province",
      "dataType": { "type": "STRING" },
      "required": false,
      "constraints": { "maxLength": 100 }
    },
    {
      "id": "postal-code",
      "apiName": "postalCode",
      "displayName": "Postal Code",
      "dataType": { "type": "STRING" },
      "required": true,
      "constraints": { "pattern": "^[A-Z0-9\\- ]{3,10}$" }
    },
    {
      "id": "country",
      "apiName": "country",
      "displayName": "Country",
      "dataType": { "type": "STRING" },
      "required": true,
      "constraints": { "maxLength": 100 }
    }
  ],
  "status": "active"
}
```

**Monetary Amount:**
```json
{
  "$type": "StructType",
  "apiName": "MonetaryAmount",
  "displayName": "Monetary Amount",
  "description": "Amount with currency.",
  "fields": [
    {
      "id": "amount",
      "apiName": "amount",
      "displayName": "Amount",
      "dataType": { "type": "DECIMAL", "precision": 18, "scale": 2 },
      "required": true
    },
    {
      "id": "currency",
      "apiName": "currency",
      "displayName": "Currency",
      "dataType": { "type": "STRING" },
      "required": true,
      "constraints": {
        "pattern": "^[A-Z]{3}$",
        "enum": ["USD", "EUR", "GBP", "JPY", "KRW", "CNY"]
      }
    }
  ],
  "status": "active"
}
```

**Geo Coordinate:**
```json
{
  "$type": "StructType",
  "apiName": "GeoCoordinate",
  "displayName": "Geographic Coordinate",
  "fields": [
    {
      "id": "latitude",
      "apiName": "latitude",
      "displayName": "Latitude",
      "dataType": { "type": "DOUBLE" },
      "required": true,
      "constraints": { "minValue": -90, "maxValue": 90 }
    },
    {
      "id": "longitude",
      "apiName": "longitude",
      "displayName": "Longitude",
      "dataType": { "type": "DOUBLE" },
      "required": true,
      "constraints": { "minValue": -180, "maxValue": 180 }
    }
  ],
  "status": "active"
}
```

---

## DataType Reference

### Full Type List

| Type | Required Fields | Notes |
|------|-----------------|-------|
| STRING | None | Text data |
| INTEGER | None | 32-bit integer |
| SHORT | None | 16-bit integer |
| BYTE | None | 8-bit integer |
| LONG | None | 64-bit integer |
| FLOAT | None | 32-bit float |
| DOUBLE | None | 64-bit float |
| DECIMAL | `precision`, `scale` (optional) | Exact decimal |
| BOOLEAN | None | true/false |
| DATE | None | Date only |
| TIMESTAMP | None | Date + time |
| DATETIME | None | Alias for TIMESTAMP |
| ARRAY | `arrayItemType` | List of items |
| STRUCT | `structTypeRef` | Nested structure |
| VECTOR | `vectorDimension` | Fixed-size vector |
| GEOPOINT | None | Latitude/longitude |
| GEOSHAPE | None | Geographic shape |
| MEDIA_REFERENCE | None | Media file reference |
| TIME_SERIES | None | Time series data |
| TIMESERIES | `timeseriesValueType` | Value type: INTEGER/LONG/FLOAT/DOUBLE |
| ATTACHMENT | None | File attachment |
| MARKING | None | Security marking |
| CIPHER | None | Encrypted data |
| JSON | None | JSON blob |
| MARKDOWN | None | Markdown text |
| BINARY | None | Binary data |

### ARRAY Type

```json
{
  "type": "ARRAY",
  "arrayItemType": { "type": "STRING" }
}
```

### STRUCT Reference

```json
{
  "type": "STRUCT",
  "structTypeRef": "Address"
}
```

### VECTOR Type

```json
{
  "type": "VECTOR",
  "vectorDimension": 384
}
```

### DECIMAL Type

```json
{
  "type": "DECIMAL",
  "precision": 18,
  "scale": 2
}
```

---

## PropertyConstraints

Common constraints for properties:

| Constraint | Type | Description |
|------------|------|-------------|
| `required` | boolean | Cannot be null/empty |
| `allowEmptyArray` | boolean | For ARRAY, allow empty (not null) |
| `unique` | boolean | Must be unique across instances |
| `immutable` | boolean | Cannot change after set |
| `enum` | array | Allowed values |
| `minValue` | number | Minimum numeric value |
| `maxValue` | number | Maximum numeric value |
| `minLength` | integer | Minimum string length |
| `maxLength` | integer | Maximum string length |
| `pattern` | regex | String pattern |
| `ridFormat` | boolean | Must be valid RID |
| `uuidFormat` | boolean | Must be valid UUID |
| `arrayUnique` | boolean | Array elements unique |
| `arrayMinItems` | integer | Minimum array size |
| `arrayMaxItems` | integer | Maximum array size |
| `customValidator` | string | Custom validation function |
| `defaultValue` | any | Default if not provided |

### Constraint Examples

```json
{
  "required": true,
  "unique": true,
  "pattern": "^[A-Z]{2}\\d{4}$",
  "maxLength": 6
}
```

---

## 5-Stage Lifecycle Protocol

### Stage 1: DEFINE

**Interactive Flow:**
1. Select property type (SharedProperty/ValueType/StructType)
2. Basic identity (id, apiName, displayName)
3. DataType or baseType selection
4. Constraints configuration
5. Optional metadata

**Output:** `.agent/tmp/staging/<id>.json`

### Stage 2: VALIDATE

**Checks:**
1. Required fields present
2. Pattern validation (id, apiName)
3. `$type` discriminator valid
4. DataType/baseType valid
5. Constraints syntax valid
6. Conditional: deprecated -> deprecation required
7. ValueType: At least one constraint
8. StructType: 1-10 fields

**Output:** Validation report (pass/fail + errors)

### Stage 3: STAGE

**Actions:**
1. Generate RID based on type:
   - SharedProperty: `ri.ontology.main.shared-property.{apiName}`
   - ValueType: `ri.ontology.main.value-type.{apiName}`
   - StructType: `ri.ontology.main.struct-type.{apiName}`
2. Add metadata (timestamps, version)
3. Calculate diff (if modifying existing)

**Output:** `.agent/tmp/staging/<id>.staged.json`

### Stage 4: REVIEW

**Display:**
- Property type and identity
- DataType/baseType specification
- Constraints summary
- Usage information (if modifying)
- Diff from existing (if applicable)

**Approval Prompt:** Approve? [y/n]

### Stage 5: DEPLOY

**Actions:**
1. Write to `.agent/tmp/ontology.db`
2. Create audit log entry
3. Update registry

---

## Actions

### define <type>
Interactive property creation.
```bash
/property define sharedproperty   # SharedProperty
/property define valuetype        # ValueType
/property define structtype       # StructType
```

### validate <json_path>
Validate JSON against schema.
```bash
/property validate email.json
```

### stage <id>
Stage validated definition.
```bash
/property stage email-address
```

### review <id>
Review and approve.
```bash
/property review email-address
```

### deploy <id>
Deploy approved definition.
```bash
/property deploy email-address
```

### list [type]
List properties, optionally filtered by type.
```bash
/property list                    # All properties
/property list sharedproperty     # SharedProperties only
/property list valuetype          # ValueTypes only
/property list structtype         # StructTypes only
```

**Output:**
| ID | Type | API Name | Status | Used By |
|----|------|----------|--------|---------|
| created-at | SharedProperty | createdAt | active | 5 ObjectTypes |
| EmailAddress | ValueType | EmailAddress | active | 3 properties |
| Address | StructType | Address | active | 2 ObjectTypes |

### show <id>
Show property details.
```bash
/property show created-at
/property show EmailAddress
```

---

## Output Formats

### Success Response
```json
{
  "status": "success",
  "action": "deploy",
  "property": {
    "$type": "ValueType",
    "apiName": "EmailAddress",
    "rid": "ri.ontology.main.value-type.EmailAddress"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "errors": [
    { "code": "MISSING_REQUIRED_FIELD", "path": "$.constraints", "message": "ValueType requires at least one constraint" }
  ]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field not present |
| `INVALID_PATTERN` | Value doesn't match regex |
| `INVALID_TYPE_DISCRIMINATOR` | `$type` not valid |
| `VALUETYPE_NO_CONSTRAINTS` | ValueType without constraints |
| `STRUCTTYPE_NO_FIELDS` | StructType without fields |
| `STRUCTTYPE_TOO_MANY_FIELDS` | StructType > 10 fields |
| `INVALID_BASE_TYPE` | baseType not recognized |
| `INVALID_STRUCT_FIELD_TYPE` | Struct field uses unsupported type |
| `DEPRECATED_MISSING_INFO` | Deprecated without deprecation |
| `ARRAY_MISSING_ITEM_TYPE` | ARRAY without arrayItemType |
| `APPROVAL_REQUIRED` | Deploy without approval |

---

## Integration

### Database

```
.agent/tmp/ontology.db
```

### Tables

```sql
CREATE TABLE IF NOT EXISTS shared_properties (
    id TEXT PRIMARY KEY,
    api_name TEXT UNIQUE NOT NULL,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS value_types (
    api_name TEXT PRIMARY KEY,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS struct_types (
    api_name TEXT PRIMARY KEY,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);
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

---

## Validation Execution

### Using JSON Schema Validator

```python
import json
import jsonschema

schema_path = "ontology_definition/schemas/Property.schema.json"
with open(schema_path) as f:
    schema = json.load(f)

definition_path = ".agent/tmp/staging/email.json"
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
schema = json.load(open('ontology_definition/schemas/Property.schema.json'))
definition = json.load(open('$FILE'))
jsonschema.validate(definition, schema)
print('Valid')
"
```

---

## Cross-ObjectType Reuse

### Using SharedProperty in ObjectType

```json
{
  "id": "employee",
  "apiName": "Employee",
  "properties": [
    {
      "sharedPropertyReference": {
        "kind": "sharedProperty",
        "apiName": "createdAt"
      }
    }
  ]
}
```

### Using ValueType in Property

```json
{
  "id": "email",
  "apiName": "email",
  "displayName": "Email",
  "dataType": {
    "type": "STRING",
    "valueTypeRef": "EmailAddress"
  }
}
```

### Using StructType in Property

```json
{
  "id": "home-address",
  "apiName": "homeAddress",
  "displayName": "Home Address",
  "dataType": {
    "type": "STRUCT",
    "structTypeRef": "Address"
  }
}
```

---

## MandatoryControl Configuration

For security marking properties:

```json
{
  "isMandatoryControl": true,
  "mandatoryControlConfig": {
    "controlType": "MARKINGS",
    "markingColumnType": "STRING_ARRAY",
    "allowedMarkings": ["uuid1", "uuid2"],
    "enforcementLevel": "STRICT"
  }
}
```

**Control Types:**
- `MARKINGS` - Row-level security markings
- `ORGANIZATIONS` - Organization-based access
- `CLASSIFICATIONS` - Classification levels (CBAC)

**Enforcement Levels:**
- `STRICT` - Always enforced
- `WARN` - Warning only
- `AUDIT_ONLY` - Logged but not enforced

---

## Value Formatting

Configure display formatting:

```json
{
  "valueFormatting": {
    "type": "NUMERIC",
    "numeric": {
      "baseType": "CURRENCY",
      "currencyCode": "USD",
      "useGrouping": true,
      "notation": "STANDARD"
    }
  }
}
```

### Formatting Types

| Type | Use Case |
|------|----------|
| `NONE` | No formatting |
| `NUMERIC` | Numbers (currency, units, percentage) |
| `DATE_TIME` | Dates and times |
| `FOUNDRY_ID` | Foundry resource IDs |
| `RESOURCE_RID` | Resource RIDs |
| `ARTIFACT_GID` | Artifact global IDs |

---

## Render Hints

Control UI behavior:

```json
{
  "renderHints": {
    "identifier": true,
    "searchable": true,
    "sortable": true,
    "selectable": false,
    "longText": false
  }
}
```

---

## Related Skills

- `oda-objecttype` - ObjectType definitions
- `oda-interface` - Interface definitions
- `oda-actiontype` - ActionType definitions
- `oda-linktype` - LinkType definitions

---

## TodoWrite Integration

Track lifecycle progress:

```json
[
  {"content": "[Stage 1] Define Property: EmailAddress", "status": "completed", "activeForm": "Defining Property"},
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
