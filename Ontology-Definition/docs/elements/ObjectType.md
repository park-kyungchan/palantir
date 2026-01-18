# ObjectType

> **Schema Version:** 1.0.0
> **Last Updated:** 2026-01-17
> **Palantir Alignment:** Foundry Ontology OSv2

---

## Definition

### Palantir Official Definition

> An ObjectType is the schema definition of a real-world entity or event in Palantir Foundry Ontology.

### Internal Clarification

An ObjectType is the most fundamental schema type in the ontology system. It defines:
- **Properties** (attributes) of the entity
- **Primary key** for unique identification
- **Backing dataset** configuration for data storage
- **Security configuration** including mandatory control and row-level filtering
- **Lifecycle status** and endorsement flags

ObjectTypes serve as the structural blueprint for **Objects** (instances), similar to how a database table schema relates to individual rows.

---

## Core Concepts

### What is an ObjectType

An ObjectType represents the schema definition of a real-world entity or event. It is NOT the data itself, but rather the **contract** that defines:

1. **What attributes** an entity has (Properties)
2. **How to identify** unique instances (Primary Key)
3. **Where data comes from** (Backing Dataset)
4. **Who can see what** (Security Configuration)
5. **What state it's in** (Lifecycle Status)

### Relationship to Real-World Entities

| Real World | Ontology Concept |
|------------|------------------|
| Employee | ObjectType `Employee` |
| John Smith (employee #12345) | Object instance of `Employee` |
| Employee's name | Property `fullName` on `Employee` ObjectType |
| Employee's ID | Primary Key property `employeeId` |

### Role in Ontology Architecture

```
Ontology
    |
    +-- ObjectTypes (schema definitions)
    |       |
    |       +-- Properties (attributes)
    |       +-- Primary Key
    |       +-- Backing Dataset
    |       +-- Security Config
    |
    +-- LinkTypes (relationships between ObjectTypes)
    +-- ActionTypes (mutations on ObjectTypes)
    +-- Interfaces (polymorphism contracts)
```

---

## Schema Structure

### Required Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `apiName` | `string` | Programmatic identifier | `^[a-zA-Z][a-zA-Z0-9_]*$`, 1-255 chars, **immutable once Active** |
| `displayName` | `string` | Human-friendly UI name | 1-255 chars, allows spaces, **mutable** |
| `primaryKey` | `PrimaryKeyDefinition` | Unique instance identifier | Must reference existing property |
| `properties` | `PropertyDefinition[]` | List of properties | Minimum 1 property required |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | `string` | `null` | Documentation (max 4096 chars) |
| `rid` | `string` | Auto-generated | Resource ID (global unique) |
| `status` | `ObjectStatus` | `EXPERIMENTAL` | Lifecycle status |
| `endorsed` | `boolean` | `false` | Trustworthy flag (Owner only) |
| `interfaces` | `string[]` | `[]` | Implemented Interface apiNames |
| `backingDataset` | `BackingDatasetConfig` | `null` | Dataset configuration |
| `securityConfig` | `SecurityConfig` | `null` | Security settings |
| `metadata` | `ObjectTypeMetadata` | `null` | Audit and tracking info |

### Nested Types

#### PrimaryKeyDefinition

```json
{
  "propertyApiName": "employeeId",
  "backingColumn": "employee_id"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `propertyApiName` | `string` | Yes | apiName of the primary key property |
| `backingColumn` | `string` | No | Column name in backing dataset |

#### BackingDatasetConfig

```json
{
  "datasetRid": "ri.foundry.main.dataset.abc123",
  "mode": "SINGLE",
  "additionalDatasets": [],
  "restrictedViewRid": "ri.foundry.main.restricted-view.xyz789"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `datasetRid` | `string` | - | RID of backing Foundry Dataset |
| `mode` | `enum` | `SINGLE` | `SINGLE` or `MULTI` (MDO) |
| `additionalDatasets` | `string[]` | `[]` | Additional dataset RIDs for MULTI mode |
| `restrictedViewRid` | `string` | - | RID of Restricted View for row-level security |

#### ObjectTypeMetadata

```json
{
  "createdAt": "2026-01-17T10:00:00Z",
  "createdBy": "admin",
  "modifiedAt": "2026-01-17T10:00:00Z",
  "modifiedBy": "admin",
  "version": 1,
  "tags": ["hr", "core"],
  "sourceModule": "human_resources"
}
```

| Field | Type | Read-Only | Description |
|-------|------|-----------|-------------|
| `createdAt` | `datetime` | Yes | ISO 8601 creation timestamp |
| `createdBy` | `string` | Yes | Creator user/agent ID |
| `modifiedAt` | `datetime` | Yes | Last modification timestamp |
| `modifiedBy` | `string` | Yes | Last modifier user/agent ID |
| `version` | `integer` | Yes | Schema version (auto-increments) |
| `tags` | `string[]` | No | Classification tags |
| `sourceModule` | `string` | No | Module/domain this ObjectType belongs to |

---

## Properties

### Primary Key

Every ObjectType **MUST** have a primary key that uniquely identifies each Object instance.

**Requirements:**
- References an existing property by `apiName`
- The referenced property should have `unique=true` constraint
- Maps to a column in the backing dataset

**Example:**
```python
primary_key = PrimaryKeyDefinition(
    property_api_name="employeeId",
    backing_column="employee_id"
)
```

### Property Definition

Each property within an ObjectType is defined by a `PropertyDefinition`:

```python
PropertyDefinition(
    api_name="fullName",
    display_name="Full Name",
    description="Employee's full legal name",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(required=True, max_length=255),
    backing_column="full_name"
)
```

**Property Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `apiName` | `string` | Yes | Unique identifier within ObjectType |
| `displayName` | `string` | Yes | Human-friendly name |
| `description` | `string` | No | Documentation |
| `dataType` | `DataTypeSpec` | Yes | Data type specification |
| `constraints` | `PropertyConstraints` | No | Validation rules |
| `backingColumn` | `string` | No | Dataset column mapping |
| `isEditOnly` | `boolean` | No | Not from dataset, user-edit only |
| `isDerived` | `boolean` | No | Computed in real-time |
| `derivedExpression` | `string` | No | Expression for derived properties |
| `isMandatoryControl` | `boolean` | No | Security marking property |
| `sharedPropertyRef` | `string` | No | Reference to SharedProperty |

### Supported Data Types (20 Types)

| Category | Types | Notes |
|----------|-------|-------|
| **Primitive** | `STRING`, `INTEGER`, `LONG`, `FLOAT`, `DOUBLE`, `BOOLEAN`, `DECIMAL` | DECIMAL requires precision/scale |
| **Temporal** | `DATE`, `TIMESTAMP`, `DATETIME`, `TIMESERIES` | TIMESERIES cannot be array item |
| **Complex** | `ARRAY`, `STRUCT`, `JSON` | ARRAY/STRUCT require configuration |
| **Spatial** | `GEOPOINT`, `GEOSHAPE` | Geographic data |
| **Media** | `MEDIA_REFERENCE`, `BINARY`, `MARKDOWN` | File and rich text |
| **AI/ML** | `VECTOR` | Requires vectorDimension, cannot be array item |

**Palantir Alignment Notes:**
- `DECIMAL` and `BINARY` are NOT valid Palantir base types (internal extensions)
- `DATETIME` maps to `TIMESTAMP` in Palantir
- `JSON` and `MARKDOWN` are internal extensions

### Property Constraints

```python
PropertyConstraints(
    required=True,
    unique=False,
    immutable=False,
    enum=["Engineering", "Sales", "HR"],
    min_value=0,
    max_value=100,
    min_length=1,
    max_length=255,
    pattern=r"^[A-Z]{2}\d{6}$",
    rid_format=False,
    uuid_format=False,
    array_unique=False,
    array_min_items=0,
    array_max_items=100,
    default_value="Unknown"
)
```

| Constraint | Type | Description |
|------------|------|-------------|
| `required` | `boolean` | Cannot be null/empty |
| `unique` | `boolean` | Value must be unique across instances |
| `immutable` | `boolean` | Cannot change after initial set |
| `enum` | `array` | Allowed values list |
| `minValue` | `number` | Minimum numeric value (inclusive) |
| `maxValue` | `number` | Maximum numeric value (inclusive) |
| `minLength` | `integer` | Minimum string length |
| `maxLength` | `integer` | Maximum string length |
| `pattern` | `string` | Regex pattern for string validation |
| `ridFormat` | `boolean` | Must be valid RID format |
| `uuidFormat` | `boolean` | Must be valid UUID format |
| `arrayUnique` | `boolean` | Array elements must be unique |
| `arrayMinItems` | `integer` | Minimum array length |
| `arrayMaxItems` | `integer` | Maximum array length |
| `defaultValue` | `any` | Default if not provided |
| `customValidator` | `string` | Custom validation function reference |

### Special Property Types

#### Edit-Only Properties

Properties not populated from the dataset, only via user edits:

```python
PropertyDefinition(
    api_name="notes",
    display_name="Notes",
    data_type=DataTypeSpec(type=DataType.STRING),
    is_edit_only=True,
    backing_column=None  # Must be None
)
```

#### Derived Properties

Properties computed in real-time:

```python
PropertyDefinition(
    api_name="fullAddress",
    display_name="Full Address",
    data_type=DataTypeSpec(type=DataType.STRING),
    is_derived=True,
    derived_expression="concat(street, ', ', city, ' ', zipCode)"
)
```

#### Mandatory Control Properties

Security marking properties for row-level access control:

```python
PropertyDefinition(
    api_name="securityMarkings",
    display_name="Security Markings",
    data_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING)
    ),
    constraints=PropertyConstraints(required=True),  # MUST be required
    is_mandatory_control=True
)
```

**Mandatory Control Rules:**
1. **MUST** have `required=True`
2. **CANNOT** have `defaultValue`
3. **MUST** be `STRING` or `ARRAY[STRING]` type

---

## Security Model

### Mandatory Control

**Palantir P1-CRITICAL Requirement:** Mandatory control properties enable row-level security based on user permissions.

```json
{
  "securityConfig": {
    "mandatoryControlProperties": [
      {
        "propertyApiName": "securityMarkings",
        "controlType": "MARKINGS",
        "markingColumnMapping": "security_markings",
        "allowedMarkings": ["uuid-1", "uuid-2"]
      }
    ]
  }
}
```

**Control Types:**

| Type | Description | Use Case |
|------|-------------|----------|
| `MARKINGS` | Security markings | Most common, controls data visibility |
| `ORGANIZATIONS` | Organization-based access | Multi-tenant scenarios |
| `CLASSIFICATIONS` | Classification-Based Access Control (CBAC) | Government deployments only |

**Classification Levels (CBAC):**
- `UNCLASSIFIED`
- `CONFIDENTIAL`
- `SECRET`
- `TOP_SECRET`

### Restricted Views

Restricted Views provide row-level filtering based on user attributes:

```json
{
  "backingDataset": {
    "datasetRid": "ri.foundry.main.dataset.abc123",
    "restrictedViewRid": "ri.foundry.main.restricted-view.xyz789"
  },
  "securityConfig": {
    "objectSecurityPolicy": {
      "policyType": "RESTRICTED_VIEW",
      "restrictedViewPolicy": {
        "logicalOperator": "AND",
        "terms": [
          {
            "termType": "MARKING_CHECK",
            "columnName": "security_markings",
            "userAttribute": "user.markings"
          }
        ]
      }
    }
  }
}
```

**Policy Term Types:**

| Type | Description |
|------|-------------|
| `USER_ATTRIBUTE_COMPARISON` | Compare row column to user attribute |
| `COLUMN_VALUE_MATCH` | Match column against static value |
| `MARKING_CHECK` | Verify user has required markings |

**User Identifier:** UUID only (names not supported in Palantir)

### Property-Level Security

Control visibility and access for individual properties:

```json
{
  "securityConfig": {
    "propertySecurityPolicies": [
      {
        "propertyApiName": "ssn",
        "accessLevel": "MASKED",
        "maskingPattern": "{last4}"
      },
      {
        "propertyApiName": "salary",
        "accessLevel": "HIDDEN"
      }
    ]
  }
}
```

**Access Levels:**

| Level | Description | Example |
|-------|-------------|---------|
| `FULL` | Complete read/write access | Default |
| `READ_ONLY` | Can view but not modify | Audit fields |
| `MASKED` | Partial visibility | SSN showing last 4 digits |
| `HIDDEN` | Completely hidden | Sensitive internal data |

**Masking Patterns:**
- `{last4}` - Show last 4 characters
- `{first3}...{last3}` - Show first 3 and last 3
- `***` - Replace entirely with asterisks

---

## Lifecycle Status

### Status Enum Values

| Status | Description | Schema Changes? | Production? |
|--------|-------------|-----------------|-------------|
| `DRAFT` | Initial creation, not visible to others | Yes | No |
| `EXPERIMENTAL` | Visible but schema may change significantly | Yes | No |
| `ALPHA` | Early testing, breaking changes expected | Yes | No |
| `BETA` | Feature complete, minor changes possible | Yes | No |
| `ACTIVE` | Production-ready, changes need migration | No | Yes |
| `STABLE` | Schema frozen, no changes allowed | No | Yes |
| `DEPRECATED` | Marked for removal, use alternative | No | No |
| `SUNSET` | End-of-life countdown | No | No |
| `ARCHIVED` | Soft-deleted, data preserved | No | No |
| `DELETED` | Hard-deleted | No | No |

### Status Progression

```
DRAFT --> EXPERIMENTAL --> ALPHA --> BETA --> ACTIVE --> STABLE
                                                  |
                                                  v
                                            DEPRECATED --> SUNSET --> ARCHIVED --> DELETED
```

### Palantir Alignment

| Internal Status | Palantir Official | Notes |
|-----------------|-------------------|-------|
| `DRAFT` | - | Internal extension |
| `EXPERIMENTAL` | `EXPERIMENTAL` | Matches |
| `ALPHA` | - | Internal extension |
| `BETA` | - | Internal extension |
| `ACTIVE` | `ACTIVE` | Matches |
| `STABLE` | - | Internal extension |
| `DEPRECATED` | `DEPRECATED` | Matches |
| `SUNSET` | - | Internal extension |
| `ARCHIVED` | - | Internal extension |
| `DELETED` | - | Internal extension |
| - | `EXAMPLE` | Not implemented |
| - | `ENDORSED` | Implemented as `endorsed` flag |

### Endorsed Status

**Important:** `endorsed` is a **boolean flag**, not a status value.

- Only ObjectTypes can be endorsed (NOT LinkTypes, ActionTypes)
- Can only be set by **Ontology Owner**
- Indicates a trustworthy, recommended ObjectType
- Independent of lifecycle status

```python
ObjectType(
    api_name="Employee",
    status=ObjectStatus.ACTIVE,
    endorsed=True  # Separate flag, not a status
)
```

---

## Backing Dataset Configuration

### Dataset Mapping

ObjectTypes are backed by Foundry Datasets for data storage:

```json
{
  "backingDataset": {
    "datasetRid": "ri.foundry.main.dataset.abc123",
    "mode": "SINGLE"
  }
}
```

### Sync Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `SINGLE` | One dataset backs the ObjectType | Standard scenario |
| `MULTI` | Multi-Dataset Object (MDO) | Data from multiple sources |

### Multi-Dataset Objects (MDO)

```json
{
  "backingDataset": {
    "datasetRid": "ri.foundry.main.dataset.primary",
    "mode": "MULTI",
    "additionalDatasets": [
      "ri.foundry.main.dataset.secondary",
      "ri.foundry.main.dataset.tertiary"
    ]
  }
}
```

MDO enables merging data from multiple datasets into a single ObjectType view.

### RID Formats

| Resource | Pattern |
|----------|---------|
| ObjectType | `ri.ontology.{env}.object-type.{id}` |
| Dataset | `ri.foundry.{env}.dataset.{id}` |
| Restricted View | `ri.foundry.{env}.restricted-view.{id}` |

---

## Examples

### Basic Example

Minimal valid ObjectType:

```json
{
  "apiName": "Employee",
  "displayName": "Employee",
  "primaryKey": {
    "propertyApiName": "employeeId"
  },
  "properties": [
    {
      "apiName": "employeeId",
      "displayName": "Employee ID",
      "dataType": { "type": "STRING" },
      "constraints": { "required": true, "unique": true }
    }
  ]
}
```

### Full Example with Security

Complete ObjectType with all features:

```json
{
  "apiName": "Employee",
  "displayName": "Employee",
  "description": "Represents an employee in the organization.",
  "rid": "ri.ontology.main.object-type.Employee",
  "primaryKey": {
    "propertyApiName": "employeeId",
    "backingColumn": "employee_id"
  },
  "properties": [
    {
      "apiName": "employeeId",
      "displayName": "Employee ID",
      "description": "Unique identifier for the employee.",
      "dataType": { "type": "STRING" },
      "constraints": { "required": true, "unique": true },
      "backingColumn": "employee_id"
    },
    {
      "apiName": "fullName",
      "displayName": "Full Name",
      "description": "Employee's full name.",
      "dataType": { "type": "STRING" },
      "constraints": { "required": true, "maxLength": 255 },
      "backingColumn": "full_name"
    },
    {
      "apiName": "department",
      "displayName": "Department",
      "description": "Department the employee belongs to.",
      "dataType": { "type": "STRING" },
      "constraints": {
        "enum": ["Engineering", "Sales", "HR", "Finance", "Operations"]
      },
      "backingColumn": "department"
    },
    {
      "apiName": "salary",
      "displayName": "Salary",
      "description": "Annual salary (restricted visibility).",
      "dataType": { "type": "DOUBLE" },
      "constraints": { "minValue": 0 },
      "backingColumn": "salary"
    },
    {
      "apiName": "securityMarkings",
      "displayName": "Security Markings",
      "description": "Mandatory control property for row-level security.",
      "dataType": {
        "type": "ARRAY",
        "arrayItemType": { "type": "STRING" }
      },
      "constraints": { "required": true },
      "isMandatoryControl": true,
      "backingColumn": "security_markings"
    }
  ],
  "status": "ACTIVE",
  "endorsed": true,
  "interfaces": ["Person", "OrganizationMember"],
  "backingDataset": {
    "datasetRid": "ri.foundry.main.dataset.abc123",
    "mode": "SINGLE",
    "restrictedViewRid": "ri.foundry.main.restricted-view.xyz789"
  },
  "securityConfig": {
    "mandatoryControlProperties": [
      {
        "propertyApiName": "securityMarkings",
        "controlType": "MARKINGS",
        "markingColumnMapping": "security_markings"
      }
    ],
    "objectSecurityPolicy": {
      "policyType": "RESTRICTED_VIEW",
      "restrictedViewPolicy": {
        "logicalOperator": "AND",
        "terms": [
          {
            "termType": "MARKING_CHECK",
            "columnName": "security_markings",
            "userAttribute": "user.markings"
          }
        ]
      }
    },
    "propertySecurityPolicies": [
      {
        "propertyApiName": "salary",
        "accessLevel": "HIDDEN"
      }
    ]
  },
  "metadata": {
    "createdAt": "2026-01-17T10:00:00Z",
    "createdBy": "admin",
    "modifiedAt": "2026-01-17T10:00:00Z",
    "modifiedBy": "admin",
    "version": 1,
    "tags": ["hr", "core"],
    "sourceModule": "human_resources"
  }
}
```

### Python Example

```python
from ontology_definition.types.object_type import (
    ObjectType,
    BackingDatasetConfig,
    SecurityConfig,
    PropertySecurityPolicy,
)
from ontology_definition.types.property_def import (
    PropertyDefinition,
    PrimaryKeyDefinition,
    DataTypeSpec,
)
from ontology_definition.constraints.property_constraints import PropertyConstraints
from ontology_definition.constraints.mandatory_control import MandatoryControlConfig
from ontology_definition.core.enums import (
    DataType,
    ObjectStatus,
    AccessLevel,
    ControlType,
    BackingDatasetMode,
)

# Create ObjectType
employee_type = ObjectType(
    api_name="Employee",
    display_name="Employee",
    description="Company employee entity",
    primary_key=PrimaryKeyDefinition(
        property_api_name="employeeId",
        backing_column="employee_id"
    ),
    properties=[
        PropertyDefinition(
            api_name="employeeId",
            display_name="Employee ID",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(required=True, unique=True),
            backing_column="employee_id"
        ),
        PropertyDefinition(
            api_name="fullName",
            display_name="Full Name",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(required=True, max_length=255),
            backing_column="full_name"
        ),
        PropertyDefinition(
            api_name="securityMarkings",
            display_name="Security Markings",
            data_type=DataTypeSpec(
                type=DataType.ARRAY,
                array_item_type=DataTypeSpec(type=DataType.STRING)
            ),
            constraints=PropertyConstraints(required=True),
            is_mandatory_control=True,
            backing_column="security_markings"
        ),
    ],
    status=ObjectStatus.ACTIVE,
    endorsed=True,
    interfaces=["Person"],
    backing_dataset=BackingDatasetConfig(
        dataset_rid="ri.foundry.main.dataset.abc123",
        mode=BackingDatasetMode.SINGLE,
        restricted_view_rid="ri.foundry.main.restricted-view.xyz789"
    ),
    security_config=SecurityConfig(
        mandatory_control_properties=[
            MandatoryControlConfig(
                property_api_name="securityMarkings",
                control_type=ControlType.MARKINGS,
                marking_column_mapping="security_markings"
            )
        ],
        property_security_policies=[
            PropertySecurityPolicy(
                property_api_name="salary",
                access_level=AccessLevel.HIDDEN
            )
        ]
    )
)

# Export to Foundry format
foundry_dict = employee_type.to_foundry_dict()
```

---

## Palantir Alignment

### Gap Analysis

| Feature | Internal Implementation | Palantir Official | Gap |
|---------|------------------------|-------------------|-----|
| **Base Types** | 20 types | 16 types | `DECIMAL`, `BINARY`, `JSON`, `MARKDOWN` are extensions |
| **Status Values** | 10 values | 5 values | Extended lifecycle stages |
| **Endorsed** | `endorsed` boolean flag | `ENDORSED` status | Correct - endorsed is ObjectType-only |
| **Security** | Full support | Full support | Aligned |
| **MDO** | Supported | Supported | Aligned |

### Compliance Notes

1. **Endorsed Status:** Correctly implemented as a boolean flag on ObjectType only (not LinkType or ActionType)

2. **Mandatory Control:** Implements P1-CRITICAL requirement:
   - Property must be required
   - Property cannot have default value
   - Property must be STRING or ARRAY[STRING]

3. **Restricted Views:** Full support for row-level security via Restricted View integration

4. **Status Lifecycle:** Extended beyond Palantir's official statuses for finer-grained control

### Recommended Actions

| Priority | Item | Action |
|----------|------|--------|
| HIGH | DECIMAL type | Document as internal extension or remove |
| HIGH | BINARY type | Document as internal extension or remove |
| MEDIUM | DATETIME | Document as mapping to TIMESTAMP |
| LOW | EXAMPLE status | Consider adding for sample ObjectTypes |

---

## API Reference

### `to_foundry_dict()`

Exports the ObjectType to Palantir Foundry-compatible JSON format.

```python
def to_foundry_dict(self) -> dict[str, Any]:
    """Export to Palantir Foundry-compatible dictionary format."""
```

**Returns:** Dictionary with camelCase keys matching Foundry JSON schema.

**Example:**
```python
employee_type = ObjectType(...)
foundry_json = employee_type.to_foundry_dict()
# {
#   "apiName": "Employee",
#   "displayName": "Employee",
#   "primaryKey": {...},
#   "properties": [...],
#   ...
# }
```

### `from_foundry_dict()`

Creates an ObjectType instance from Palantir Foundry JSON format.

```python
@classmethod
def from_foundry_dict(cls, data: dict[str, Any]) -> "ObjectType":
    """Create ObjectType from Palantir Foundry JSON format."""
```

**Parameters:**
- `data`: Dictionary in Foundry JSON format (camelCase keys)

**Returns:** ObjectType instance

**Example:**
```python
foundry_data = {
    "apiName": "Employee",
    "displayName": "Employee",
    "primaryKey": {"propertyApiName": "employeeId"},
    "properties": [...]
}
employee_type = ObjectType.from_foundry_dict(foundry_data)
```

### Utility Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `get_property(api_name)` | Get property by apiName | `PropertyDefinition` or `None` |
| `get_primary_key_property()` | Get the primary key property | `PropertyDefinition` |
| `get_mandatory_control_properties()` | Get all mandatory control properties | `list[PropertyDefinition]` |
| `get_required_properties()` | Get all required properties | `list[PropertyDefinition]` |
| `implements_interface(api_name)` | Check if ObjectType implements interface | `bool` |

### Validation Rules

The ObjectType class enforces these validation rules via Pydantic validators:

1. **Primary Key Exists:** The `primaryKey.propertyApiName` must reference an existing property
2. **Unique Property Names:** All property `apiName` values must be unique
3. **Mandatory Control Properties:** If security config references a mandatory control property, that property must exist and have `is_mandatory_control=True`

---

## Related Documentation

- **PropertyDefinition:** `/docs/elements/PropertyDefinition.md`
- **LinkType:** `/docs/elements/LinkType.md`
- **ActionType:** `/docs/elements/ActionType.md`
- **Interface:** `/docs/elements/Interface.md`
- **JSON Schema:** `/docs/research/schemas/ObjectType.schema.json`

---

## Implementation References

| File | Purpose |
|------|---------|
| `ontology_definition/types/object_type.py` | Main ObjectType class |
| `ontology_definition/types/property_def.py` | PropertyDefinition, DataTypeSpec |
| `ontology_definition/core/enums.py` | DataType, ObjectStatus, etc. |
| `ontology_definition/constraints/mandatory_control.py` | MandatoryControlConfig |
| `ontology_definition/constraints/property_constraints.py` | PropertyConstraints |

---

*Document generated for Ontology-Definition project.*
*Last updated: 2026-01-17*
