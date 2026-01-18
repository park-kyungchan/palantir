# LinkType

> **Version:** 1.0.0
> **Last Updated:** 2026-01-17
> **Schema Source:** `LinkType.schema.json`
> **Implementation:** `ontology_definition/types/link_type.py`

---

## Definition

> **Official Palantir Definition:**
> "A LinkType is the schema definition of a relationship between two object types."

A LinkType defines how two ObjectTypes are related in the Ontology. It specifies the source and target object types, the cardinality of the relationship, and how the relationship is physically stored (via foreign key or backing table).

---

## Core Concepts

### Relationship Modeling

LinkTypes model real-world relationships between entities:
- **Employee to Department** - Many employees belong to one department
- **Project to Team Member** - Many projects involve many team members
- **Order to Customer** - Many orders belong to one customer

### Cardinality Types

| Type | Notation | Description |
|------|----------|-------------|
| `ONE_TO_ONE` | 1:1 | Single object on both sides |
| `ONE_TO_MANY` | 1:N | One source to many targets |
| `MANY_TO_ONE` | N:1 | Many sources to one target |
| `MANY_TO_MANY` | N:N | Multiple objects on both sides |

### Implementation Types

| Type | Use Case | Storage |
|------|----------|---------|
| `FOREIGN_KEY` | 1:1, 1:N, N:1 relationships | FK column on one side |
| `BACKING_TABLE` | N:N relationships (required) | Junction/bridge table |

---

## Schema Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `apiName` | string | Programmatic identifier (immutable once Active) |
| `displayName` | string | Human-friendly UI name |
| `sourceObjectType` | ObjectTypeReference | ObjectType on the 'from' side |
| `targetObjectType` | ObjectTypeReference | ObjectType on the 'to' side |
| `cardinality` | Cardinality | Relationship cardinality configuration |
| `implementation` | LinkImplementation | Physical storage configuration |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | - | Documentation (max 4096 chars) |
| `rid` | string | auto-generated | Resource ID (globally unique) |
| `bidirectional` | boolean | `true` | Enable navigation from both sides |
| `reverseApiName` | string | - | apiName for reverse navigation |
| `reverseDisplayName` | string | - | Display name for reverse direction |
| `cascadePolicy` | CascadePolicy | - | Referential integrity behavior |
| `linkProperties` | LinkPropertyDefinition[] | `[]` | Properties on the link itself |
| `status` | LinkTypeStatus | `EXPERIMENTAL` | Lifecycle status |
| `linkMerging` | LinkMergingConfig | - | Duplicate link handling |
| `securityConfig` | LinkSecurityConfig | - | Access control configuration |
| `metadata` | LinkTypeMetadata | - | Tracking information |

### Nested Types

#### ObjectTypeReference

```json
{
  "apiName": "Employee",
  "rid": "ri.ontology.main.object-type.abc123"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `apiName` | Yes | apiName of the referenced ObjectType |
| `rid` | No | RID for external references |

#### Cardinality

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

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | enum | - | ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY |
| `sourceMin` | integer | 0 | Minimum links from source (0 = optional, 1 = required) |
| `sourceMax` | integer/string | "N" | Maximum links from source ("N" or -1 for unlimited) |
| `targetMin` | integer | 0 | Minimum links to target |
| `targetMax` | integer/string | "N" | Maximum links to target |
| `enforced` | boolean | false | Strictly enforce constraints |

---

## Cardinality Model

### ONE_TO_ONE (1:1)

**Description:** Each source object links to at most one target object, and vice versa.

**Important Note:** In Palantir Foundry, ONE_TO_ONE is typically an **indicator only** - it is not strictly enforced at the database level by default. Use `enforced: true` for strict enforcement.

**Example:** Person to Passport
```json
{
  "type": "ONE_TO_ONE",
  "sourceMin": 0,
  "sourceMax": 1,
  "targetMin": 0,
  "targetMax": 1,
  "enforced": true
}
```

**Implementation:** Use `FOREIGN_KEY` on either side.

### ONE_TO_MANY (1:N)

**Description:** One source object can link to many target objects, but each target links to at most one source.

**Example:** Department to Employees
```json
{
  "type": "ONE_TO_MANY",
  "sourceMin": 0,
  "sourceMax": "N",
  "targetMin": 0,
  "targetMax": 1
}
```

**Implementation:** `FOREIGN_KEY` on the TARGET side (the "many" side).

### MANY_TO_ONE (N:1)

**Description:** Many source objects can link to one target object.

**Example:** Employee to Department
```json
{
  "type": "MANY_TO_ONE",
  "sourceMin": 0,
  "sourceMax": 1,
  "targetMin": 0,
  "targetMax": "N"
}
```

**Implementation:** `FOREIGN_KEY` on the SOURCE side (the "many" side).

### MANY_TO_MANY (N:N)

**Description:** Multiple source objects can link to multiple target objects.

**CRITICAL:** MANY_TO_MANY relationships **REQUIRE** `BACKING_TABLE` implementation. Palantir Foundry needs a junction table to store N:N relationships.

**Example:** Project to Team Members
```json
{
  "type": "MANY_TO_MANY",
  "sourceMin": 0,
  "sourceMax": "N",
  "targetMin": 0,
  "targetMax": "N"
}
```

**Implementation:** MUST use `BACKING_TABLE` with a junction dataset.

---

## Implementation Types

### FOREIGN_KEY

Used for 1:1, 1:N, and N:1 relationships where one side holds a reference to the other.

#### Configuration

```json
{
  "type": "FOREIGN_KEY",
  "foreignKey": {
    "foreignKeyProperty": "departmentId",
    "foreignKeyLocation": "SOURCE",
    "referencedProperty": "departmentId"
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `foreignKeyProperty` | Yes | Property apiName that holds the FK |
| `foreignKeyLocation` | Yes | `SOURCE` or `TARGET` - which side has the FK |
| `referencedProperty` | No | Property being referenced (defaults to primary key) |

#### Foreign Key Location Rules

| Cardinality | FK Location | Reason |
|-------------|-------------|--------|
| ONE_TO_ONE | Either side | Choose based on domain logic |
| ONE_TO_MANY | TARGET | FK on the "many" side |
| MANY_TO_ONE | SOURCE | FK on the "many" side |

### BACKING_TABLE

Used for MANY_TO_MANY relationships. Requires a junction/bridge table dataset.

#### Configuration

```json
{
  "type": "BACKING_TABLE",
  "backingTable": {
    "datasetRid": "ri.foundry.main.dataset.project-team-junction",
    "sourceKeyColumn": "project_id",
    "targetKeyColumn": "member_id",
    "additionalColumns": [
      { "columnName": "role", "propertyApiName": "assignedRole" },
      { "columnName": "joined_at", "propertyApiName": "joinedAt" }
    ]
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `datasetRid` | No | RID of the backing Foundry Dataset |
| `sourceKeyColumn` | Yes | Column containing source object's primary key |
| `targetKeyColumn` | Yes | Column containing target object's primary key |
| `additionalColumns` | No | Mappings for link property columns |

#### Junction Table Requirements

The backing dataset must have:
1. **Source key column** - References source ObjectType's primary key
2. **Target key column** - References target ObjectType's primary key
3. **Optional property columns** - For link properties (e.g., role, date)

---

## Cascade Policies

Cascade policies define referential integrity behavior when linked objects are modified or deleted.

### Configuration

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

### Cascade Actions

| Action | Description |
|--------|-------------|
| `RESTRICT` | Prevent operation if links exist |
| `CASCADE` | Propagate operation to linked objects/links |
| `SET_NULL` | Set foreign key to null (requires nullable FK) |
| `SET_DEFAULT` | Set foreign key to default value |
| `NO_ACTION` | Take no action (may leave orphan references) |

### On Delete Behavior

| Policy | Source Delete | Target Delete |
|--------|---------------|---------------|
| `CASCADE` | Delete all links from this source | Delete all links to this target |
| `RESTRICT` | Block if links exist | Block if links exist |
| `SET_NULL` | Set FK to null | Set FK to null |

### On Update Behavior

| Policy | Source Update | Target Update |
|--------|---------------|---------------|
| `CASCADE` | Update FK references | Update FK references |
| `RESTRICT` | Block if links exist | Block if links exist |

### Common Patterns

**Master-Detail (strict):**
```json
{
  "onSourceDelete": "CASCADE",
  "onTargetDelete": "RESTRICT"
}
```

**Loose Association:**
```json
{
  "onSourceDelete": "SET_NULL",
  "onTargetDelete": "SET_NULL"
}
```

---

## Link Properties

Link properties store data about the relationship itself, not the related objects. Only available with `BACKING_TABLE` implementation.

### Definition

```json
{
  "linkProperties": [
    {
      "apiName": "assignedRole",
      "displayName": "Assigned Role",
      "dataType": "STRING",
      "backingColumn": "role",
      "required": true,
      "description": "The role assigned to the team member on this project"
    },
    {
      "apiName": "joinedAt",
      "displayName": "Joined At",
      "dataType": "TIMESTAMP",
      "backingColumn": "joined_at",
      "required": false
    }
  ]
}
```

### Allowed Data Types

Link properties are restricted to simple types:

| Type | Description |
|------|-------------|
| `STRING` | Text values |
| `INTEGER` | 32-bit integer |
| `LONG` | 64-bit integer |
| `FLOAT` | Single-precision float |
| `DOUBLE` | Double-precision float |
| `BOOLEAN` | True/false |
| `DATE` | Calendar date |
| `TIMESTAMP` | Date and time |

**Note:** Complex types (ARRAY, STRUCT, JSON, VECTOR) are NOT allowed for link properties.

---

## Lifecycle Status

### LinkTypeStatus Values

| Status | Description | Schema Changes |
|--------|-------------|----------------|
| `DRAFT` | Initial creation, not visible | Allowed |
| `EXPERIMENTAL` | Visible but may change significantly | Allowed |
| `ALPHA` | Early testing phase | Allowed |
| `BETA` | Late testing phase | Allowed |
| `ACTIVE` | Production-ready | Migration required |
| `STABLE` | Frozen schema | Not allowed |
| `DEPRECATED` | Marked for removal | Not allowed |
| `SUNSET` | End-of-life period | Not allowed |
| `ARCHIVED` | Soft-deleted | Not allowed |
| `DELETED` | Hard-deleted | N/A |

### ENDORSED Status NOT Supported

> **IMPORTANT GAP (GAP-005):** The `ENDORSED` status is NOT supported for LinkTypes.
> Only ObjectTypes can be endorsed. This is aligned with Palantir Foundry behavior.

**Palantir Documentation:**
> "Endorsed status applies ONLY to ObjectTypes, not to LinkTypes, Properties, or ActionTypes."

---

## Bidirectional Navigation

Links can be navigated from both source and target directions when `bidirectional: true`.

### Configuration

```json
{
  "bidirectional": true,
  "reverseApiName": "DepartmentToEmployees",
  "reverseDisplayName": "Department to Employees"
}
```

### Navigation Example

Given `EmployeeToDepartment` link:
- **Forward:** `Employee.department` -> Department
- **Reverse:** `Department.employees` -> Employee[]

---

## Link Merging

Configuration for handling duplicate links from multiple data sources.

### Configuration

```json
{
  "linkMerging": {
    "enabled": true,
    "strategy": "FIRST_WINS",
    "priorityField": "sourceTimestamp"
  }
}
```

### Merge Strategies

| Strategy | Description |
|----------|-------------|
| `FIRST_WINS` | First value encountered takes precedence |
| `LAST_WINS` | Last value encountered takes precedence |
| `PRIORITY_BASED` | Use priority field to determine winner |

---

## Security Configuration

### Configuration

```json
{
  "securityConfig": {
    "inheritSourceSecurity": true,
    "inheritTargetSecurity": false,
    "requireBothVisible": false,
    "linkPropertySecurity": [
      {
        "propertyApiName": "sensitiveNote",
        "accessLevel": "MASKED"
      }
    ]
  }
}
```

### Access Levels

| Level | Description |
|-------|-------------|
| `FULL` | Complete read/write access |
| `READ_ONLY` | Can view but not modify |
| `MASKED` | Partial visibility (e.g., last 4 digits) |
| `HIDDEN` | Completely hidden |

---

## Examples

### Example 1: MANY_TO_ONE with Foreign Key

**Scenario:** Many employees belong to one department.

```json
{
  "apiName": "EmployeeToDepartment",
  "displayName": "Employee to Department",
  "description": "Links employees to their assigned department.",
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
  "reverseApiName": "DepartmentToEmployees",
  "reverseDisplayName": "Department to Employees",
  "cascadePolicy": {
    "onSourceDelete": "CASCADE",
    "onTargetDelete": "SET_NULL"
  },
  "status": "ACTIVE",
  "metadata": {
    "createdAt": "2026-01-17T10:00:00Z",
    "createdBy": "admin",
    "version": 1,
    "tags": ["org-structure"]
  }
}
```

### Example 2: MANY_TO_MANY with Backing Table

**Scenario:** Projects have many team members, and team members work on many projects.

```json
{
  "apiName": "ProjectToTeamMember",
  "displayName": "Project to Team Member",
  "description": "Many-to-many relationship between projects and team members with role assignment.",
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
      "targetKeyColumn": "member_id",
      "additionalColumns": [
        { "columnName": "role", "propertyApiName": "assignedRole" },
        { "columnName": "joined_at", "propertyApiName": "joinedAt" }
      ]
    }
  },
  "linkProperties": [
    {
      "apiName": "assignedRole",
      "displayName": "Assigned Role",
      "dataType": "STRING",
      "backingColumn": "role",
      "required": true
    },
    {
      "apiName": "joinedAt",
      "displayName": "Joined At",
      "dataType": "TIMESTAMP",
      "backingColumn": "joined_at",
      "required": false
    }
  ],
  "bidirectional": true,
  "reverseApiName": "TeamMemberToProjects",
  "reverseDisplayName": "Team Member to Projects",
  "status": "ACTIVE"
}
```

### Example 3: Python Implementation

```python
from ontology_definition.types.link_type import (
    LinkType,
    ObjectTypeReference,
    CardinalityConfig,
    LinkImplementation,
    ForeignKeyConfig,
    BackingTableConfig,
    LinkPropertyDefinition,
    CascadePolicy,
)
from ontology_definition.core.enums import (
    Cardinality,
    LinkImplementationType,
    ForeignKeyLocation,
    CascadeAction,
    DataType,
    LinkTypeStatus,
)

# MANY_TO_ONE Example
emp_to_dept = LinkType(
    api_name="EmployeeToDepartment",
    display_name="Employee to Department",
    source_object_type=ObjectTypeReference(api_name="Employee"),
    target_object_type=ObjectTypeReference(api_name="Department"),
    cardinality=CardinalityConfig(type=Cardinality.MANY_TO_ONE),
    implementation=LinkImplementation(
        type=LinkImplementationType.FOREIGN_KEY,
        foreign_key=ForeignKeyConfig(
            foreign_key_property="departmentId",
            foreign_key_location=ForeignKeyLocation.SOURCE,
        ),
    ),
    bidirectional=True,
    reverse_api_name="DepartmentToEmployees",
    cascade_policy=CascadePolicy(
        on_source_delete=CascadeAction.CASCADE,
        on_target_delete=CascadeAction.SET_NULL,
    ),
    status=LinkTypeStatus.ACTIVE,
)

# Export to Foundry format
foundry_dict = emp_to_dept.to_foundry_dict()

# Import from Foundry format
imported = LinkType.from_foundry_dict(foundry_dict)
```

---

## Palantir Alignment

### Fully Aligned Features

| Feature | Status | Notes |
|---------|--------|-------|
| Cardinality types | Aligned | ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY |
| FOREIGN_KEY implementation | Aligned | With location and referenced property |
| BACKING_TABLE implementation | Aligned | Required for MANY_TO_MANY |
| Bidirectional navigation | Aligned | With reverse names |
| Link properties | Aligned | For backing table only |
| Cascade policies | Aligned | All 5 actions supported |

### Gap Analysis

| Gap ID | Description | Severity | Notes |
|--------|-------------|----------|-------|
| GAP-005 | ENDORSED status not supported | INFO | By design - matches Palantir |
| - | ONE_TO_ONE indicator only | INFO | `enforced` flag available |
| - | Extended lifecycle statuses | INFO | ALPHA, BETA, SUNSET, ARCHIVED, DELETED are extensions |

### ONE_TO_ONE Enforcement Note

> **Palantir Behavior:** "ONE_TO_ONE is typically an indicator rather than strictly enforced in Palantir Foundry."

Our implementation provides the `enforced` flag for strict enforcement when needed, but defaults to `false` to match Palantir's indicator-only behavior.

---

## Validation Rules

### Schema Validation

1. **apiName Pattern:** `^[a-zA-Z][a-zA-Z0-9_]*$`
2. **apiName Length:** 1-255 characters
3. **description Length:** max 4096 characters
4. **RID Pattern:** `^ri\.ontology\.[a-z]+\.link-type\.[a-zA-Z0-9-]+$`

### Business Rule Validation

1. **MANY_TO_MANY requires BACKING_TABLE:**
   ```
   if cardinality.type == "MANY_TO_MANY":
       assert implementation.type == "BACKING_TABLE"
       assert implementation.backingTable is not None
   ```

2. **FOREIGN_KEY requires foreignKey config:**
   ```
   if implementation.type == "FOREIGN_KEY":
       assert implementation.foreignKey is not None
   ```

3. **Link properties require BACKING_TABLE:**
   ```
   if linkProperties is not empty:
       assert implementation.type == "BACKING_TABLE"
   ```

4. **Unique link property names:**
   ```
   assert len(linkProperties) == len(set(p.apiName for p in linkProperties))
   ```

5. **PRIORITY_BASED strategy requires priorityField:**
   ```
   if linkMerging.strategy == "PRIORITY_BASED":
       assert linkMerging.priorityField is not None
   ```

---

## API Reference

### Python Classes

| Class | Description |
|-------|-------------|
| `LinkType` | Main LinkType schema definition |
| `ObjectTypeReference` | Reference to source/target ObjectType |
| `CardinalityConfig` | Cardinality specification |
| `LinkImplementation` | Physical storage configuration |
| `ForeignKeyConfig` | Foreign key implementation config |
| `BackingTableConfig` | Junction table implementation config |
| `BackingTableColumnMapping` | Column to property mapping |
| `CascadePolicy` | Referential integrity behavior |
| `LinkPropertyDefinition` | Property on the link itself |
| `LinkMergingConfig` | Duplicate link handling |
| `LinkSecurityConfig` | Security configuration |
| `LinkPropertySecurityPolicy` | Per-property security |

### Key Methods

| Method | Description |
|--------|-------------|
| `to_foundry_dict()` | Export to Palantir Foundry JSON format |
| `from_foundry_dict(data)` | Import from Palantir Foundry JSON format |
| `is_many_to_many()` | Check if N:N relationship |
| `has_backing_table()` | Check if uses backing table |
| `get_link_property(api_name)` | Get link property by name |

### Enums

| Enum | Values |
|------|--------|
| `Cardinality` | ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY |
| `LinkImplementationType` | FOREIGN_KEY, BACKING_TABLE |
| `ForeignKeyLocation` | SOURCE, TARGET |
| `CascadeAction` | RESTRICT, CASCADE, SET_NULL, SET_DEFAULT, NO_ACTION |
| `LinkTypeStatus` | DRAFT, EXPERIMENTAL, ALPHA, BETA, ACTIVE, STABLE, DEPRECATED, SUNSET, ARCHIVED, DELETED |
| `LinkMergeStrategy` | FIRST_WINS, LAST_WINS, PRIORITY_BASED |
| `AccessLevel` | FULL, READ_ONLY, MASKED, HIDDEN |

---

## Related Documentation

- [ObjectType](./ObjectType.md) - Schema definition of entities
- [ActionType](./ActionType.md) - Schema definition of mutations
- [Property](./Property.md) - Property definitions
- [Interface](./Interface.md) - Polymorphic type contracts

---

*Document generated from schema analysis and Palantir Foundry documentation.*
