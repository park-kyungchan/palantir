# DataTypes and Enums

> **Version:** 1.0.0
> **Last Updated:** 2026-01-17
> **Source:** `ontology_definition/core/enums.py`, `ontology_definition/types/*.py`

This document provides comprehensive documentation for all DataTypes and Enumerations used in the Ontology-Definition project, including Palantir Foundry alignment analysis.

---

## Table of Contents

1. [DataType Enum](#datatype-enum)
   - [Primitive Types](#primitive-types)
   - [Temporal Types](#temporal-types)
   - [Complex Types](#complex-types)
   - [Spatial Types](#spatial-types)
   - [Media Types](#media-types)
   - [AI/ML Types](#aiml-types)
2. [Status Enums](#status-enums)
   - [ObjectStatus](#objectstatus)
   - [LinkTypeStatus](#linktypestatus)
   - [ActionTypeStatus](#actiontypestatus)
   - [InterfaceStatus](#interfacestatus)
   - [SharedPropertyStatus](#sharedpropertystatus)
3. [Relationship Enums](#relationship-enums)
   - [Cardinality](#cardinality)
   - [CascadeAction](#cascadeaction)
   - [LinkImplementationType](#linkimplementationtype)
   - [ForeignKeyLocation](#foreignkeylocation)
4. [Security Enums](#security-enums)
   - [ControlType](#controltype)
   - [ClassificationLevel](#classificationlevel)
   - [SecurityPolicyType](#securitypolicytype)
   - [AccessLevel](#accesslevel)
5. [Data Management Enums](#data-management-enums)
   - [MergeStrategy](#mergestrategy)
   - [BackingDatasetMode](#backingdatasetmode)
6. [ActionType Enums](#actiontype-enums)
   - [ParameterType](#parametertype)
   - [ObjectOperation](#objectoperation)
   - [ActionImplementationType](#actionimplementationtype)
   - [SideEffectType](#sideeffecttype)
7. [SemanticType Enum](#semantictype-enum)
8. [Gap Analysis Summary](#gap-analysis-summary)
9. [Recommendations](#recommendations)

---

## DataType Enum

**Location:** `ontology_definition/core/enums.py`

The `DataType` enum defines 20 supported property data types in Palantir Foundry Ontology.

### Primitive Types

| Type | Value | Description | Palantir Support | Notes |
|------|-------|-------------|------------------|-------|
| `STRING` | `"STRING"` | Text values | ✅ Supported | Base type |
| `INTEGER` | `"INTEGER"` | 32-bit signed integer | ✅ Supported | Range: -2^31 to 2^31-1 |
| `LONG` | `"LONG"` | 64-bit signed integer | ✅ Supported | Range: -2^63 to 2^63-1 |
| `FLOAT` | `"FLOAT"` | Single-precision (32-bit) floating point | ✅ Supported | IEEE 754 |
| `DOUBLE` | `"DOUBLE"` | Double-precision (64-bit) floating point | ✅ Supported | IEEE 754 |
| `BOOLEAN` | `"BOOLEAN"` | True/false values | ✅ Supported | Base type |
| `DECIMAL` | `"DECIMAL"` | Arbitrary-precision decimal | ❌ **NOT VALID** | **Internal extension** - NOT a valid Palantir base type |

> **CRITICAL:** Per Palantir documentation: "Map, Decimal, and Binary types are NOT valid base types in Palantir Foundry."

### Temporal Types

| Type | Value | Description | Palantir Support | Notes |
|------|-------|-------------|------------------|-------|
| `DATE` | `"DATE"` | Calendar date (YYYY-MM-DD) | ✅ Supported | No time component |
| `TIMESTAMP` | `"TIMESTAMP"` | Date and time with timezone | ✅ Supported | ISO 8601 format |
| `DATETIME` | `"DATETIME"` | Date and time (extension) | ⚠️ Extension | May map to TIMESTAMP |
| `TIMESERIES` | `"TIMESERIES"` | Time-indexed values | ✅ Supported | **Cannot be array item** |

> **CONSTRAINT:** Vector and Time series types cannot be used as array items.

### Complex Types

| Type | Value | Description | Palantir Support | Required Configuration |
|------|-------|-------------|------------------|----------------------|
| `ARRAY` | `"ARRAY"` | Collection of values | ✅ Supported | `array_item_type` required |
| `STRUCT` | `"STRUCT"` | Nested structure | ✅ Supported | `struct_fields` required |
| `JSON` | `"JSON"` | JSON object | ⚠️ Extension | Not explicitly listed in Palantir docs |

**Array Item Type Restrictions:**
- VECTOR cannot be used as array item type
- TIMESERIES cannot be used as array item type

### Spatial Types

| Type | Value | Description | Palantir Support | Notes |
|------|-------|-------------|------------------|-------|
| `GEOPOINT` | `"GEOPOINT"` | Geographic point (lat/lon) | ✅ Supported | WGS84 coordinate system |
| `GEOSHAPE` | `"GEOSHAPE"` | Geographic shape/polygon | ✅ Supported | GeoJSON format |

### Media Types

| Type | Value | Description | Palantir Support | Notes |
|------|-------|-------------|------------------|-------|
| `MEDIA_REFERENCE` | `"MEDIA_REFERENCE"` | Media file reference | ✅ Supported | References Foundry media |
| `BINARY` | `"BINARY"` | Binary data | ❌ **NOT VALID** | **Internal extension** - NOT a valid Palantir base type |
| `MARKDOWN` | `"MARKDOWN"` | Markdown formatted text | ⚠️ Extension | Not explicitly listed |

> **CRITICAL:** Per Palantir documentation: "Map, Decimal, and Binary types are NOT valid base types in Palantir Foundry."

### AI/ML Types

| Type | Value | Description | Palantir Support | Required Configuration |
|------|-------|-------------|------------------|----------------------|
| `VECTOR` | `"VECTOR"` | AI/ML embedding vectors | ✅ Supported | `vector_dimension` required, **Cannot be array item** |

### DataType Helper Methods

```python
# Get all primitive types
DataType.primitive_types()
# Returns: [STRING, INTEGER, LONG, FLOAT, DOUBLE, BOOLEAN, DECIMAL]

# Get all temporal types
DataType.temporal_types()
# Returns: [DATE, TIMESTAMP, DATETIME, TIMESERIES]

# Get all complex types
DataType.complex_types()
# Returns: [ARRAY, STRUCT, JSON]

# Get types requiring additional configuration
DataType.requires_config()
# Returns: [ARRAY, STRUCT, VECTOR, DECIMAL]
```

---

## Status Enums

### ObjectStatus

**Location:** `ontology_definition/core/enums.py`

Lifecycle status for ObjectTypes. **ObjectTypes are the ONLY entity type that can be endorsed.**

| Status | Value | Description | Schema Changes? | Production? | End of Life? |
|--------|-------|-------------|-----------------|-------------|--------------|
| `DRAFT` | `"DRAFT"` | Initial creation, not visible to others | ✅ Yes | No | No |
| `EXPERIMENTAL` | `"EXPERIMENTAL"` | Visible but schema may change significantly | ✅ Yes | No | No |
| `ALPHA` | `"ALPHA"` | Early testing phase | ✅ Yes | No | No |
| `BETA` | `"BETA"` | Feature complete, stabilizing | ✅ Yes | No | No |
| `ACTIVE` | `"ACTIVE"` | Production-ready, schema changes need migration | No | ✅ Yes | No |
| `STABLE` | `"STABLE"` | Frozen schema, no changes allowed | No | ✅ Yes | No |
| `DEPRECATED` | `"DEPRECATED"` | Marked for removal, use alternative | No | No | ✅ Yes |
| `SUNSET` | `"SUNSET"` | Removal in progress | No | No | ✅ Yes |
| `ARCHIVED` | `"ARCHIVED"` | Soft-deleted, data preserved but inaccessible | No | No | ✅ Yes |
| `DELETED` | `"DELETED"` | Hard-deleted state | No | No | ✅ Yes |

**Palantir Official Status Values:**
- ✅ ACTIVE - Matches
- ✅ EXPERIMENTAL - Matches
- ✅ DEPRECATED - Matches
- ❌ EXAMPLE - **Not implemented** (Should add)
- ❌ ENDORSED - **Not implemented** (Should add for ObjectTypes only)

**Gap Analysis:**
| Internal Status | Palantir Official | Notes |
|-----------------|-------------------|-------|
| DRAFT | - | Pre-release, internal only |
| EXPERIMENTAL | ✅ EXPERIMENTAL | Matches |
| ALPHA | - | Extended lifecycle stage |
| BETA | - | Extended lifecycle stage |
| ACTIVE | ✅ ACTIVE | Matches |
| STABLE | - | Schema frozen stage |
| DEPRECATED | ✅ DEPRECATED | Matches |
| SUNSET | - | Extended end-of-life |
| ARCHIVED | - | Soft-delete state |
| DELETED | - | Hard-delete state |
| - | ❌ EXAMPLE | **Missing** - Not implemented |
| - | ❌ ENDORSED | **Missing** - Only for ObjectTypes |

### LinkTypeStatus

**Location:** `ontology_definition/core/enums.py`

Lifecycle status for LinkTypes. **LinkTypes do NOT support ENDORSED status.**

| Status | Value | Description |
|--------|-------|-------------|
| `DRAFT` | `"DRAFT"` | Initial creation |
| `EXPERIMENTAL` | `"EXPERIMENTAL"` | Development phase |
| `ALPHA` | `"ALPHA"` | Early testing |
| `BETA` | `"BETA"` | Stabilizing |
| `ACTIVE` | `"ACTIVE"` | Production-ready |
| `STABLE` | `"STABLE"` | Frozen schema |
| `DEPRECATED` | `"DEPRECATED"` | Marked for removal |
| `SUNSET` | `"SUNSET"` | Removal in progress |
| `ARCHIVED` | `"ARCHIVED"` | Soft-deleted |
| `DELETED` | `"DELETED"` | Hard-deleted |

> **Palantir Alignment:** ✅ Correctly excludes ENDORSED status per Palantir documentation.

### ActionTypeStatus

**Location:** `ontology_definition/types/action_type.py`

Lifecycle status for ActionTypes. **ActionTypes do NOT support ENDORSED status.**

| Status | Value | Description |
|--------|-------|-------------|
| `DRAFT` | `"DRAFT"` | Initial creation |
| `EXPERIMENTAL` | `"EXPERIMENTAL"` | Development phase |
| `ALPHA` | `"ALPHA"` | Early testing |
| `BETA` | `"BETA"` | Stabilizing |
| `ACTIVE` | `"ACTIVE"` | Production-ready |
| `STABLE` | `"STABLE"` | Frozen schema |
| `DEPRECATED` | `"DEPRECATED"` | Marked for removal |
| `SUNSET` | `"SUNSET"` | Removal in progress |
| `ARCHIVED` | `"ARCHIVED"` | Soft-deleted |
| `DELETED` | `"DELETED"` | Hard-deleted |

> **Palantir Alignment:** ✅ Correctly excludes ENDORSED status per Palantir documentation.

### InterfaceStatus

**Location:** `ontology_definition/types/interface.py`

Lifecycle status for Interfaces. **Interfaces do NOT support ENDORSED status** (interfaces themselves are not endorsed; implementers are).

| Status | Value | Description |
|--------|-------|-------------|
| `DRAFT` | `"DRAFT"` | Initial creation |
| `EXPERIMENTAL` | `"EXPERIMENTAL"` | Development phase |
| `ACTIVE` | `"ACTIVE"` | Production-ready |
| `STABLE` | `"STABLE"` | Frozen contract |
| `DEPRECATED` | `"DEPRECATED"` | Marked for removal |
| `ARCHIVED` | `"ARCHIVED"` | Soft-deleted |

> **Note:** InterfaceStatus has fewer states than ObjectStatus (no ALPHA, BETA, SUNSET, DELETED).

### SharedPropertyStatus

**Location:** `ontology_definition/types/shared_property.py`

Lifecycle status for SharedProperties.

| Status | Value | Description |
|--------|-------|-------------|
| `DRAFT` | `"DRAFT"` | Initial creation |
| `EXPERIMENTAL` | `"EXPERIMENTAL"` | Development phase |
| `ALPHA` | `"ALPHA"` | Early testing |
| `BETA` | `"BETA"` | Stabilizing |
| `ACTIVE` | `"ACTIVE"` | Production-ready |
| `STABLE` | `"STABLE"` | Frozen definition |
| `DEPRECATED` | `"DEPRECATED"` | Marked for removal |
| `SUNSET` | `"SUNSET"` | Removal in progress |
| `ARCHIVED` | `"ARCHIVED"` | Soft-deleted |
| `DELETED` | `"DELETED"` | Hard-deleted |

---

## Relationship Enums

### Cardinality

**Location:** `ontology_definition/core/enums.py`

LinkType relationship cardinality constraints.

| Cardinality | Value | Short Notation | Requires Backing Table | Description |
|-------------|-------|----------------|------------------------|-------------|
| `ONE_TO_ONE` | `"ONE_TO_ONE"` | 1:1 | No | Single object on both sides |
| `ONE_TO_MANY` | `"ONE_TO_MANY"` | 1:N | No | FK on "many" side pointing to "one" side |
| `MANY_TO_ONE` | `"MANY_TO_ONE"` | N:1 | No | Reverse of ONE_TO_MANY |
| `MANY_TO_MANY` | `"MANY_TO_MANY"` | N:N | ✅ Yes | Requires backing/junction table |

> **IMPORTANT:** In Palantir Foundry, ONE_TO_ONE is typically an indicator rather than a strictly enforced constraint. Use `enforced=True` for strict enforcement.

**Helper Properties:**
```python
cardinality.requires_backing_table  # Returns True for MANY_TO_MANY
cardinality.short_notation          # Returns "1:1", "1:N", "N:1", or "N:N"
```

### CascadeAction

**Location:** `ontology_definition/core/enums.py`

Referential integrity actions for LinkType cascade policies.

| Action | Value | Description |
|--------|-------|-------------|
| `RESTRICT` | `"RESTRICT"` | Prevent operation if links exist |
| `CASCADE` | `"CASCADE"` | Propagate the operation to linked objects/links |
| `SET_NULL` | `"SET_NULL"` | Set foreign key to null (requires nullable FK) |
| `SET_DEFAULT` | `"SET_DEFAULT"` | Set foreign key to default value |
| `NO_ACTION` | `"NO_ACTION"` | Take no action (may leave orphan references) |

### LinkImplementationType

**Location:** `ontology_definition/core/enums.py`

Physical implementation type for LinkTypes.

| Type | Value | Use Case |
|------|-------|----------|
| `FOREIGN_KEY` | `"FOREIGN_KEY"` | Standard FK relationship (1:1, 1:N, N:1) |
| `BACKING_TABLE` | `"BACKING_TABLE"` | Junction table (required for N:N) |

### ForeignKeyLocation

**Location:** `ontology_definition/core/enums.py`

Which side of the link holds the foreign key.

| Location | Value | Description |
|----------|-------|-------------|
| `SOURCE` | `"SOURCE"` | FK is on the source ObjectType |
| `TARGET` | `"TARGET"` | FK is on the target ObjectType |

---

## Security Enums

### ControlType

**Location:** `ontology_definition/core/enums.py`

Mandatory control types for row-level security.

| Type | Value | Description | Common Usage |
|------|-------|-------------|--------------|
| `MARKINGS` | `"MARKINGS"` | Controls based on security markings | Most common in Foundry |
| `ORGANIZATIONS` | `"ORGANIZATIONS"` | Controls based on organization membership | Multi-tenant applications |
| `CLASSIFICATIONS` | `"CLASSIFICATIONS"` | Classification-Based Access Control (CBAC) | Government deployments |

> **Palantir Alignment:** ✅ **Exact match** with Palantir Security Documentation.

### ClassificationLevel

**Location:** `ontology_definition/core/enums.py`

Classification levels for CBAC (Classification-Based Access Control).

| Level | Value | Description |
|-------|-------|-------------|
| `UNCLASSIFIED` | `"UNCLASSIFIED"` | No classification |
| `CONFIDENTIAL` | `"CONFIDENTIAL"` | Confidential information |
| `SECRET` | `"SECRET"` | Secret information |
| `TOP_SECRET` | `"TOP_SECRET"` | Top secret information |

> **Note:** Used with `ControlType.CLASSIFICATIONS` in government deployments.

### SecurityPolicyType

**Location:** `ontology_definition/core/enums.py`

Types of security policies for ObjectTypes.

| Type | Value | Description |
|------|-------|-------------|
| `RESTRICTED_VIEW` | `"RESTRICTED_VIEW"` | Uses Foundry Restricted View for row filtering |
| `PROPERTY_BASED` | `"PROPERTY_BASED"` | Filter based on property values and user attributes |
| `CUSTOM` | `"CUSTOM"` | Custom security logic via function/expression |

### AccessLevel

**Location:** `ontology_definition/core/enums.py`

Property access level for security policies.

| Level | Value | Description |
|-------|-------|-------------|
| `FULL` | `"FULL"` | Complete read/write access |
| `READ_ONLY` | `"READ_ONLY"` | Can view but not modify |
| `MASKED` | `"MASKED"` | Partial visibility (e.g., last 4 digits of SSN) |
| `HIDDEN` | `"HIDDEN"` | Completely hidden from user |

---

## Data Management Enums

### MergeStrategy

**Location:** `ontology_definition/core/enums.py`

Merge strategy for conflicting data from multiple sources (Multi-Dataset Objects - MDO).

| Strategy | Value | Description |
|----------|-------|-------------|
| `FIRST_WINS` | `"FIRST_WINS"` | First value encountered takes precedence |
| `LAST_WINS` | `"LAST_WINS"` | Last value encountered takes precedence |
| `PRIORITY_BASED` | `"PRIORITY_BASED"` | Use priority field to determine winner |

> **Alias:** `LinkMergeStrategy = MergeStrategy`

### BackingDatasetMode

**Location:** `ontology_definition/core/enums.py`

Mode for ObjectType backing dataset configuration.

| Mode | Value | Description |
|------|-------|-------------|
| `SINGLE` | `"SINGLE"` | Single dataset backs the ObjectType (default) |
| `MULTI` | `"MULTI"` | Multi-Dataset Object (MDO) - multiple datasets merged |

---

## ActionType Enums

**Location:** `ontology_definition/types/action_type.py`

### ParameterType

Data types available for action parameters.

| Type | Value | Description |
|------|-------|-------------|
| `STRING` | `"STRING"` | Text input |
| `INTEGER` | `"INTEGER"` | 32-bit integer |
| `LONG` | `"LONG"` | 64-bit integer |
| `FLOAT` | `"FLOAT"` | Single-precision float |
| `DOUBLE` | `"DOUBLE"` | Double-precision float |
| `BOOLEAN` | `"BOOLEAN"` | True/false |
| `DATE` | `"DATE"` | Calendar date |
| `TIMESTAMP` | `"TIMESTAMP"` | Date and time |
| `ARRAY` | `"ARRAY"` | Collection (requires `array_item_type`) |
| `STRUCT` | `"STRUCT"` | Nested structure |
| `OBJECT_PICKER` | `"OBJECT_PICKER"` | Select an object instance (requires `object_type_ref`) |
| `OBJECT_SET` | `"OBJECT_SET"` | Select multiple objects (requires `object_type_ref`) |
| `ATTACHMENT` | `"ATTACHMENT"` | File attachment |

### ObjectOperation

Operations that an action can perform on ObjectTypes.

| Operation | Value | Description |
|-----------|-------|-------------|
| `CREATE` | `"CREATE"` | Create new object |
| `MODIFY` | `"MODIFY"` | Modify existing object |
| `DELETE` | `"DELETE"` | Delete object |

### ActionImplementationType

How the action logic is implemented.

| Type | Value | Description |
|------|-------|-------------|
| `DECLARATIVE` | `"DECLARATIVE"` | Uses EditSpecifications to define changes |
| `FUNCTION_BACKED` | `"FUNCTION_BACKED"` | Calls a function (TypeScript or Python) |
| `INLINE_EDIT` | `"INLINE_EDIT"` | Simple property edits without logic |

### SideEffectType

Types of post-execution side effects.

| Type | Value | Description |
|------|-------|-------------|
| `NOTIFICATION` | `"NOTIFICATION"` | Send notification to users |
| `WEBHOOK` | `"WEBHOOK"` | Call external webhook |
| `EMAIL` | `"EMAIL"` | Send email |
| `AUDIT_LOG` | `"AUDIT_LOG"` | Write to audit log |
| `TRIGGER_ACTION` | `"TRIGGER_ACTION"` | Trigger another action |
| `CUSTOM_FUNCTION` | `"CUSTOM_FUNCTION"` | Custom side effect function |

### Other ActionType Enums

| Enum | Values | Purpose |
|------|--------|---------|
| `EditOperationType` | CREATE_OBJECT, MODIFY_OBJECT, DELETE_OBJECT, CREATE_LINK, DELETE_LINK, MODIFY_PROPERTY | Types of declarative edit operations |
| `ObjectSelectionType` | PARAMETER, QUERY, CURRENT | How to select objects for operations |
| `EditConditionType` | PARAMETER_EQUALS, PARAMETER_NOT_NULL, OBJECT_STATE, EXPRESSION | Condition types for conditional edits |
| `SubmissionCriterionType` | PARAMETER_VALIDATION, OBJECT_STATE_CHECK, PERMISSION_CHECK, CARDINALITY_CHECK, CUSTOM_FUNCTION | Types of submission criteria |
| `CriterionSeverity` | ERROR, WARNING | Severity level for criteria failures |
| `NotificationChannel` | IN_APP, EMAIL, SLACK, TEAMS | Notification delivery channels |
| `FunctionLanguage` | TYPESCRIPT, PYTHON | Languages for function-backed actions |
| `ObjectAccessLevel` | READ, WRITE, DELETE, ADMIN | Required access levels |
| `AuditLogLevel` | MINIMAL, STANDARD, DETAILED | Audit log detail levels |
| `UndoStrategy` | INVERSE_ACTION, RESTORE_SNAPSHOT, CUSTOM_FUNCTION | Undo strategies |
| `ParameterInputType` | text, textarea, number, select, multiselect, datepicker, filepicker, objectpicker | UI input types |

---

## SemanticType Enum

**Location:** `ontology_definition/types/shared_property.py`

Semantic meaning of a property for cross-ObjectType consistency and querying.

### Identity

| Type | Value | Description |
|------|-------|-------------|
| `IDENTIFIER` | `"IDENTIFIER"` | Unique identifier |
| `NAME` | `"NAME"` | Display name |
| `DESCRIPTION` | `"DESCRIPTION"` | Description text |

### Temporal (Audit)

| Type | Value | Description | Data Type Requirement |
|------|-------|-------------|----------------------|
| `TIMESTAMP` | `"TIMESTAMP"` | Generic timestamp | TIMESTAMP, DATETIME, or DATE |
| `CREATED_AT` | `"CREATED_AT"` | Creation timestamp | TIMESTAMP, DATETIME, or DATE |
| `MODIFIED_AT` | `"MODIFIED_AT"` | Modification timestamp | TIMESTAMP, DATETIME, or DATE |
| `CREATED_BY` | `"CREATED_BY"` | Creator user ID | STRING |
| `MODIFIED_BY` | `"MODIFIED_BY"` | Last modifier user ID | STRING |

### Classification

| Type | Value | Description |
|------|-------|-------------|
| `STATUS` | `"STATUS"` | Lifecycle status |
| `CATEGORY` | `"CATEGORY"` | Category classification |
| `TAG` | `"TAG"` | Tag/label |

### Contact

| Type | Value | Description |
|------|-------|-------------|
| `URL` | `"URL"` | Web URL |
| `EMAIL` | `"EMAIL"` | Email address |
| `PHONE` | `"PHONE"` | Phone number |
| `ADDRESS` | `"ADDRESS"` | Physical address |

### Numeric

| Type | Value | Description |
|------|-------|-------------|
| `CURRENCY` | `"CURRENCY"` | Monetary value |
| `PERCENTAGE` | `"PERCENTAGE"` | Percentage value |

### Security

| Type | Value | Description | Special Requirement |
|------|-------|-------------|---------------------|
| `SECURITY_MARKING` | `"SECURITY_MARKING"` | Security marking property | Requires `is_mandatory_control=True` |

### Other

| Type | Value | Description |
|------|-------|-------------|
| `CUSTOM` | `"CUSTOM"` | Custom semantic type |

**Validation Rules:**
- Temporal semantic types (TIMESTAMP, CREATED_AT, MODIFIED_AT) require temporal data types (TIMESTAMP, DATETIME, DATE)
- SECURITY_MARKING requires `is_mandatory_control=True`

---

## Gap Analysis Summary

### Critical Gaps (HIGH Priority)

| Gap ID | Category | Issue | Impact | Recommendation |
|--------|----------|-------|--------|----------------|
| GAP-007 | DataType | `DECIMAL` and `BINARY` included but NOT valid Palantir base types | Schema incompatibility | Remove or document as internal extensions |

### Medium Priority Gaps

| Gap ID | Category | Issue | Impact | Recommendation |
|--------|----------|-------|--------|----------------|
| GAP-009 | Status | `EXAMPLE` status from Palantir not implemented | Missing sample object support | Add EXAMPLE to ObjectStatus |
| - | Status | `ENDORSED` status missing from ObjectStatus | Cannot mark endorsed ObjectTypes | Add ENDORSED to ObjectStatus only |
| - | DataType | `DATETIME` not in official Palantir list | Potential confusion | Document as mapping to TIMESTAMP |
| - | DataType | `JSON` not explicitly in official list | Unclear support | Document as extension |
| - | DataType | `MARKDOWN` not in official list | Unclear support | Document as extension |

### Correctly Implemented (No Action Required)

| Category | Status | Details |
|----------|--------|---------|
| ControlType | ✅ Correct | Exact match with Palantir (MARKINGS, ORGANIZATIONS, CLASSIFICATIONS) |
| Cardinality | ✅ Correct | All four types, backing table logic correct |
| LinkTypeStatus | ✅ Correct | Correctly excludes ENDORSED |
| ActionTypeStatus | ✅ Correct | Correctly excludes ENDORSED |
| InterfaceStatus | ✅ Correct | Correctly excludes ENDORSED |
| Array Item Constraints | ✅ Implemented | VECTOR and TIMESERIES validation needed |

---

## Recommendations

### Immediate Actions (This Week)

1. **Document DECIMAL/BINARY as Internal Extensions**
   ```python
   # In enums.py, update docstrings:
   DECIMAL = "DECIMAL"  # WARNING: Internal extension - NOT a valid Palantir base type
   BINARY = "BINARY"    # WARNING: Internal extension - NOT a valid Palantir base type
   ```

2. **Add ENDORSED to ObjectStatus**
   ```python
   class ObjectStatus(str, Enum):
       # ... existing values ...
       ENDORSED = "ENDORSED"  # Palantir official - ObjectTypes ONLY
   ```

3. **Add EXAMPLE to ObjectStatus**
   ```python
   class ObjectStatus(str, Enum):
       # ... existing values ...
       EXAMPLE = "EXAMPLE"  # Palantir official - Sample/example ObjectTypes
   ```

### Short-Term Actions (Next Sprint)

4. **Add Array Item Type Validation**
   ```python
   # In DataTypeSpec validator:
   NON_ARRAY_ITEM_TYPES = {DataType.VECTOR, DataType.TIMESERIES}
   if self.array_item_type and self.array_item_type.type in NON_ARRAY_ITEM_TYPES:
       raise ValueError(f"{self.array_item_type.type} cannot be used as array item")
   ```

5. **Document Extension Types**
   - Create clear documentation that DATETIME, JSON, MARKDOWN are internal extensions
   - Provide mapping guidance to Palantir-compatible types

### Long-Term Actions

6. **Consider Removing Non-Standard Types**
   - Evaluate if DECIMAL and BINARY are actually needed
   - If needed, implement as custom types or STRUCT fields

7. **Schema Export Validation**
   - Add validation in Foundry export to warn/error on non-standard types

---

## Type Compatibility Matrix

| Internal Type | Palantir Type | Export Strategy |
|---------------|---------------|-----------------|
| STRING | String | Direct |
| INTEGER | Integer | Direct |
| LONG | Long | Direct |
| FLOAT | Float | Direct |
| DOUBLE | Double | Direct |
| BOOLEAN | Boolean | Direct |
| DECIMAL | ❌ None | Convert to STRING or DOUBLE |
| DATE | Date | Direct |
| TIMESTAMP | Timestamp | Direct |
| DATETIME | Timestamp | Convert to TIMESTAMP |
| TIMESERIES | Time series | Direct |
| ARRAY | Array | Direct |
| STRUCT | Struct | Direct |
| JSON | ❌ None | Convert to STRING or STRUCT |
| GEOPOINT | Geopoint | Direct |
| GEOSHAPE | Geoshape | Direct |
| MEDIA_REFERENCE | Media reference | Direct |
| BINARY | ❌ None | Convert to MEDIA_REFERENCE |
| MARKDOWN | ❌ None | Convert to STRING |
| VECTOR | Vector | Direct |

---

## References

1. **Source Files:**
   - `ontology_definition/core/enums.py` - Core enum definitions
   - `ontology_definition/types/action_type.py` - ActionType enums
   - `ontology_definition/types/interface.py` - InterfaceStatus
   - `ontology_definition/types/shared_property.py` - SemanticType, SharedPropertyStatus

2. **Palantir Documentation:**
   - Palantir Foundry Ontology Documentation
   - Palantir Property Types Documentation
   - Palantir Security Documentation

3. **Internal Analysis:**
   - `.agent/reports/palantir_external_reference_2026_01_17.md`
   - `.agent/reports/deep_audit_final_synthesis_2026_01_17.md`

---

*Document generated for Ontology-Definition project*
*Last updated: 2026-01-17*
