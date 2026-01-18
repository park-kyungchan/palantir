---
name: oda-interface
description: |
  Interface definition management with 5-Stage Lifecycle Protocol.
  Schema source: ontology_definition/schemas/Interface.schema.json
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
context: fork
agent: general-purpose
intents:
  korean: ["인터페이스", "공유속성", "다형성", "계약"]
  english: ["interface", "shared property", "polymorphism", "contract"]
---

# ODA Interface Skill

## Purpose

Manage Interface definitions following 5-Stage Lifecycle:
1. **DEFINE** - Collect specification
2. **VALIDATE** - Verify against JSON Schema
3. **STAGE** - Preview before deployment
4. **REVIEW** - Human approval gate
5. **DEPLOY** - Persist to ontology database

---

## Schema Reference

**Location:** `/home/palantir/park-kyungchan/palantir/ontology_definition/schemas/Interface.schema.json`

### Required Fields

| Field | Pattern | Example |
|-------|---------|---------|
| `apiName` | `^[a-zA-Z][a-zA-Z0-9_]*$` | `facility`, `Auditable` |
| `displayName` | String (1-255) | `Facility`, `Auditable Entity` |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `^[a-z][a-z0-9-]*$` | Lowercase identifier |
| `description` | String (max 4096) | Documentation |
| `aliases` | Array | Alternative names for search |
| `icon` | `{name, color}` | Visual identifier |
| `status` | enum | `experimental` (default), `active`, `deprecated`, `example` |
| `searchable` | Boolean | Enable polymorphic search (default: true) |
| `sharedProperties` | Array | Property contracts |
| `linkTypeConstraints` | Array | Required relationships |
| `extends` | Array | Interface inheritance |

### Conditional: Deprecation

When `status: deprecated`, requires:
```json
{
  "deprecation": {
    "reason": "Replaced by FacilityV2",
    "removalDeadline": "2026-06-01T00:00:00Z",
    "replacement": { "kind": "interface", "apiName": "FacilityV2" }
  }
}
```

---

## SharedPropertyReference

Interfaces define property contracts via shared properties.

```json
{
  "sharedProperties": [
    { "apiName": "facilityName" },
    { "apiName": "location", "rid": "ri.ontology.main.shared-property.location" }
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `apiName` | Yes | Shared property API name |
| `id` | No | Optional ID reference |
| `rid` | No | Full resource identifier |

**Contract Rules:**
1. Implementing ObjectTypes MUST map a property to each shared property
2. Property types must be compatible
3. Define SharedProperty resources first via `/property`

---

## InterfaceLinkConstraint

Link constraints define required relationships for implementing types.

```json
{
  "linkTypeConstraints": [
    {
      "apiName": "manager",
      "description": "Facility manager",
      "target": { "type": "objectType", "apiName": "Employee" },
      "cardinality": "ONE",
      "required": true
    },
    {
      "apiName": "airlines",
      "target": { "type": "interface", "apiName": "Airline" },
      "cardinality": "MANY",
      "required": false
    }
  ]
}
```

| Field | Required | Values |
|-------|----------|--------|
| `apiName` | Yes | `^[a-zA-Z][a-zA-Z0-9_]*$` |
| `target` | Yes | `{type: "objectType"|"interface", apiName: string}` |
| `cardinality` | Yes | `ONE` or `MANY` |
| `description` | No | Documentation |
| `required` | No | If true, implementing types must satisfy (default: false) |

---

## Interface Inheritance

Interfaces can extend other interfaces via `extends`:

```json
{
  "extends": [
    { "apiName": "Auditable" },
    { "apiName": "Searchable", "rid": "ri.ontology.main.interface.Searchable" }
  ]
}
```

**Inheritance Rules:**
1. Extended interfaces' sharedProperties are inherited
2. Extended interfaces' linkTypeConstraints are inherited
3. Implementing ObjectTypes must satisfy ALL inherited requirements
4. Circular inheritance is NOT allowed

---

## 5-Stage Lifecycle Protocol

### Stage 1: DEFINE

**Interactive Flow:**
1. Basic Identity (apiName, displayName)
2. Shared properties definition
3. Link type constraints
4. Interface inheritance (extends)
5. Optional config (icon, searchable)

**Output:** `.agent/tmp/staging/<apiName>.interface.json`

### Stage 2: VALIDATE

**Checks:**
- Required fields present
- Pattern validation (id, apiName)
- SharedPropertyReference validation
- InterfaceLinkConstraint validation
- Deprecation requirement when deprecated
- No circular inheritance

**Output:** Validation report

### Stage 3: STAGE

**Actions:**
1. Generate RID: `ri.ontology.main.interface.{apiName}`
2. Add metadata (timestamps, version)
3. Resolve inheritance chain
4. Calculate diff if modifying

**Output:** `.agent/tmp/staging/<apiName>.interface.staged.json`

### Stage 4: REVIEW

**Display:** Definition summary, properties table, link constraints, inheritance chain, diff

**Gate:** Approve? [y/n]

### Stage 5: DEPLOY

**Actions:**
1. Write to `.agent/tmp/ontology.db`
2. Create audit log entry
3. Validate no implementing ObjectTypes are broken

---

## Actions

| Action | Usage | Description |
|--------|-------|-------------|
| `define` | `/interface define` | Interactive creation |
| `validate <path>` | `/interface validate facility.json` | Validate JSON |
| `stage <apiName>` | `/interface stage facility` | Stage for review |
| `review <apiName>` | `/interface review facility` | Approve staged |
| `deploy <apiName>` | `/interface deploy facility` | Deploy to DB |
| `list` | `/interface list` | List all interfaces |
| `show <apiName>` | `/interface show facility` | Show details |
| `implementers <apiName>` | `/interface implementers facility` | List implementing types |

---

## Output Formats

### Success
```json
{
  "status": "success",
  "action": "deploy",
  "interface": {
    "apiName": "facility",
    "rid": "ri.ontology.main.interface.facility"
  }
}
```

### Error
```json
{
  "status": "error",
  "errors": [{ "code": "CIRCULAR_INHERITANCE", "path": "$.extends", "message": "..." }]
}
```

---

## Example: Complete Interface

```json
{
  "id": "facility",
  "apiName": "facility",
  "displayName": "Facility",
  "description": "Abstract interface for facilities (airports, warehouses, etc.)",
  "icon": { "name": "building", "color": "#1F77B4" },
  "status": "active",
  "searchable": true,
  "sharedProperties": [
    { "apiName": "facilityName" },
    { "apiName": "location" },
    { "apiName": "capacity" }
  ],
  "linkTypeConstraints": [
    {
      "apiName": "manager",
      "target": { "type": "objectType", "apiName": "Employee" },
      "cardinality": "ONE",
      "required": true
    },
    {
      "apiName": "airlines",
      "target": { "type": "objectType", "apiName": "Airline" },
      "cardinality": "MANY",
      "required": false
    }
  ],
  "extends": [{ "apiName": "Auditable" }]
}
```

---

## ObjectType Implementation Mapping

When ObjectType implements an interface:

```json
{
  "apiName": "Airport",
  "interfaces": [
    {
      "interfaceApiName": "facility",
      "propertyMappings": [
        { "interfaceSharedPropertyApiName": "facilityName", "objectPropertyApiName": "airportName" },
        { "interfaceSharedPropertyApiName": "location", "objectPropertyApiName": "geoLocation" }
      ],
      "linkMappings": [
        { "interfaceLinkApiName": "manager", "objectLinkApiName": "facilityManager" }
      ]
    }
  ]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field missing |
| `INVALID_PATTERN` | Value doesn't match regex |
| `DEPRECATED_MISSING_INFO` | Deprecated without deprecation |
| `SHARED_PROPERTY_NOT_FOUND` | Referenced property doesn't exist |
| `INTERFACE_NOT_FOUND` | Extended interface doesn't exist |
| `CIRCULAR_INHERITANCE` | Interface extends itself |
| `INVALID_LINK_TARGET` | Link target not found |
| `IMPLEMENTERS_BROKEN` | Change breaks implementing types |

---

## Database Operations

### Schema
```sql
CREATE TABLE IF NOT EXISTS interfaces (
    api_name TEXT PRIMARY KEY,
    id TEXT,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);
```

### Validation
```python
import json, jsonschema
schema = json.load(open('ontology_definition/schemas/Interface.schema.json'))
definition = json.load(open('.agent/tmp/staging/facility.interface.json'))
jsonschema.validate(definition, schema)
```

### Find Implementers
```python
cursor.execute("""
    SELECT api_name, definition FROM object_types
    WHERE json_extract(definition, '$.interfaces') LIKE ?
""", (f'%{interface_api_name}%',))
```

---

## Inheritance Resolution

```python
def resolve_inheritance(interface_def, registry, visited=None):
    if visited is None:
        visited = set()

    if interface_def["apiName"] in visited:
        raise CircularInheritanceError(interface_def["apiName"])
    visited.add(interface_def["apiName"])

    resolved = {
        "sharedProperties": list(interface_def.get("sharedProperties", [])),
        "linkTypeConstraints": list(interface_def.get("linkTypeConstraints", []))
    }

    for parent_ref in interface_def.get("extends", []):
        parent_def = registry.get_interface(parent_ref["apiName"])
        parent_resolved = resolve_inheritance(parent_def, registry, visited.copy())
        resolved["sharedProperties"] = parent_resolved["sharedProperties"] + resolved["sharedProperties"]
        resolved["linkTypeConstraints"] = parent_resolved["linkTypeConstraints"] + resolved["linkTypeConstraints"]

    return resolved
```

---

## Polymorphic Search

When `searchable: true`, search across all implementing ObjectTypes:

```python
def search_interface(interface_name, query):
    implementers = get_interface_implementers(interface_name)
    return [obj for impl in implementers for obj in search_type(impl, query)]
```

---

## Interface vs ObjectType

| Aspect | Interface | ObjectType |
|--------|-----------|------------|
| Purpose | Define contracts | Define entities |
| Properties | SharedPropertyReference | Full PropertyDefinition |
| Links | LinkTypeConstraints | Concrete LinkTypes |
| Instantiable | No | Yes |
| Data Storage | None | Requires backingDataset |
| Search | Polymorphic | Single type |

---

## Integration Paths

| Path | Purpose |
|------|---------|
| `.agent/tmp/ontology.db` | Database storage |
| `.agent/tmp/staging/<apiName>.interface.json` | Draft definitions |
| `.agent/tmp/staging/<apiName>.interface.staged.json` | Staged definitions |
| `.agent/logs/ontology_changes.log` | Audit trail |

---

## TodoWrite Integration

```json
[
  {"content": "[Stage 1] Define Interface: facility", "status": "completed", "activeForm": "Defining Interface"},
  {"content": "[Stage 2] Validate against schema", "status": "in_progress", "activeForm": "Validating schema"},
  {"content": "[Stage 3] Stage for review", "status": "pending", "activeForm": "Staging definition"},
  {"content": "[Stage 4] Review and approve", "status": "pending", "activeForm": "Reviewing definition"},
  {"content": "[Stage 5] Deploy to database", "status": "pending", "activeForm": "Deploying definition"}
]
```

---

## Related Skills

- `oda-objecttype` - ObjectType definitions (implements interfaces)
- `oda-property` - Property/SharedProperty management
- `oda-linktype` - LinkType definitions
- `oda-actiontype` - ActionType definitions
