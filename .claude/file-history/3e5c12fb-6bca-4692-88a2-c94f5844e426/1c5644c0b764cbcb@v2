# Palantir AIP/Foundry External Reference Documentation

**Generated:** 2026-01-17
**Purpose:** External validation reference for Ontology-Definition deep-audit
**Source:** Palantir Official Documentation (WebSearch/WebFetch)

---

## 1. Core Ontology Components

### 1.1 ObjectType
**Source:** Palantir Foundry Documentation

> An ObjectType is the schema definition of a real-world entity or event in Palantir Foundry Ontology.

**Key Characteristics:**
- Schema definition of real-world entity or event
- Contains properties (attributes)
- Has a primary key for unique identification
- Backed by one or more Foundry datasets
- Supports status lifecycle management

### 1.2 LinkType
**Source:** Palantir Foundry Documentation

> A LinkType is the schema definition of a relationship between two object types.

**Key Characteristics:**
- Defines relationship between two ObjectTypes
- Supports cardinality: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY
- Implementation types: FOREIGN_KEY, BACKING_TABLE
- **Note:** Endorsed status NOT supported for LinkType

### 1.3 ActionType
**Source:** Palantir Foundry Documentation

> An ActionType is the schema definition of a change or edit a user can make to the Ontology.

**Key Characteristics:**
- Defines edits users can perform on objects
- Connected to Functions for validation and persistence
- Can affect multiple ObjectTypes
- **Note:** Endorsed status NOT supported for ActionType

---

## 2. Status Values

### 2.1 Official Palantir Status Values (from documentation)
**Source:** Palantir Type Reference Documentation

| Status | Description |
|--------|-------------|
| **ACTIVE** | Object types in active use |
| **EXPERIMENTAL** | Object types in experimental/development phase |
| **DEPRECATED** | Object types marked for deprecation |
| **EXAMPLE** | Sample/example object types |
| **ENDORSED** | Officially endorsed object types (**ObjectTypes ONLY**) |

### 2.2 Internal Implementation Status Values

**ObjectStatus (enums.py):**
- DRAFT, EXPERIMENTAL, ALPHA, BETA, ACTIVE, STABLE, DEPRECATED, SUNSET, ARCHIVED, DELETED

**LinkTypeStatus (enums.py):**
- DRAFT, EXPERIMENTAL, ALPHA, BETA, ACTIVE, STABLE, DEPRECATED, SUNSET, ARCHIVED, DELETED
- **No ENDORSED status** (matches Palantir docs)

**InterfaceStatus (interface.py):**
- DRAFT, EXPERIMENTAL, ACTIVE, STABLE, DEPRECATED, ARCHIVED
- **No ENDORSED status** (interfaces themselves are not endorsed)

### 2.3 Status Comparison Matrix

| Internal Status | Palantir Official | Notes |
|----------------|-------------------|-------|
| DRAFT | - | Pre-release, internal only |
| EXPERIMENTAL | EXPERIMENTAL | ✅ Matches |
| ALPHA | - | Extended lifecycle stage |
| BETA | - | Extended lifecycle stage |
| ACTIVE | ACTIVE | ✅ Matches |
| STABLE | - | Schema frozen stage |
| DEPRECATED | DEPRECATED | ✅ Matches |
| SUNSET | - | Extended end-of-life |
| ARCHIVED | - | Soft-delete state |
| DELETED | - | Hard-delete state |
| - | EXAMPLE | Not implemented internally |
| - | ENDORSED | Only for ObjectTypes |

---

## 3. Property Base Types

### 3.1 Official Palantir Base Types
**Source:** Palantir Property Types Documentation

| Type | Description |
|------|-------------|
| String | Text values |
| Integer | 32-bit integer |
| Long | 64-bit integer |
| Float | Single-precision floating point |
| Double | Double-precision floating point |
| Boolean | True/false values |
| Date | Calendar date |
| Timestamp | Date and time with timezone |
| Array | Collection of values |
| Vector | AI/ML embedding vectors |
| Geopoint | Geographic point (lat/lon) |
| Geoshape | Geographic shape |
| Attachment | File attachment reference |
| Time series | Time-indexed values |
| Media reference | Media file reference |
| Cipher text | Encrypted text |
| Struct | Nested structure |

### 3.2 Important Constraints from Palantir Docs

> **Map, Decimal, and Binary types are NOT valid base types in Palantir Foundry.**

> **Vector and Time series types cannot be used as array items.**

### 3.3 Internal DataType Enum (enums.py)

```python
# 20 types defined:
# Primitives: STRING, INTEGER, LONG, FLOAT, DOUBLE, BOOLEAN, DECIMAL
# Temporal: DATE, TIMESTAMP, DATETIME, TIMESERIES
# Complex: ARRAY, STRUCT, JSON
# Spatial: GEOPOINT, GEOSHAPE
# Media: MEDIA_REFERENCE, BINARY, MARKDOWN
# AI/ML: VECTOR
```

### 3.4 Type Comparison Matrix

| Internal Type | Palantir Supported | Gap Analysis |
|---------------|-------------------|--------------|
| STRING | ✅ String | Match |
| INTEGER | ✅ Integer | Match |
| LONG | ✅ Long | Match |
| FLOAT | ✅ Float | Match |
| DOUBLE | ✅ Double | Match |
| BOOLEAN | ✅ Boolean | Match |
| **DECIMAL** | ❌ NOT VALID | **GAP: Remove or clarify usage** |
| DATE | ✅ Date | Match |
| TIMESTAMP | ✅ Timestamp | Match |
| DATETIME | ⚠️ Not explicitly listed | May map to Timestamp |
| TIMESERIES | ✅ Time series | Match |
| ARRAY | ✅ Array | Match |
| STRUCT | ✅ Struct | Match |
| JSON | ⚠️ Not explicitly listed | May need clarification |
| GEOPOINT | ✅ Geopoint | Match |
| GEOSHAPE | ✅ Geoshape | Match |
| MEDIA_REFERENCE | ✅ Media reference | Match |
| **BINARY** | ❌ NOT VALID | **GAP: Remove or clarify usage** |
| MARKDOWN | ⚠️ Not explicitly listed | May be custom extension |
| VECTOR | ✅ Vector | Match |

---

## 4. Security Model

### 4.1 Mandatory Control Types
**Source:** Palantir Security Documentation

| Control Type | Description |
|--------------|-------------|
| **MARKINGS** | Security markings (most common) |
| **ORGANIZATIONS** | Organization-based access |
| **CLASSIFICATIONS** | Classification-Based Access Control (CBAC, government use) |

### 4.2 Internal Implementation

```python
# From enums.py:
class ControlType(str, Enum):
    MARKINGS = "MARKINGS"
    ORGANIZATIONS = "ORGANIZATIONS"
    CLASSIFICATIONS = "CLASSIFICATIONS"
```

**✅ Matches Palantir documentation exactly.**

---

## 5. Interface Definition

### 5.1 Interface Concept
**Source:** Palantir Documentation

> An Interface defines a contract that ObjectTypes can implement, enabling polymorphism.

**Key Characteristics:**
- Required properties that all implementers must have
- Interface inheritance (extends other interfaces)
- Interface-level actions
- Type-safe querying across implementing types

### 5.2 Internal Implementation

```python
# From interface.py:
class Interface(OntologyEntity):
    extends: list[str]  # Parent interfaces
    required_properties: list[InterfacePropertyRequirement]
    interface_actions: list[InterfaceActionDefinition]
    status: InterfaceStatus  # No ENDORSED
```

**Note:** Correctly implements the constraint that interfaces are NOT endorsed.

---

## 6. ActionType Definition

### 6.1 Action Concept
**Source:** Palantir AIP Documentation

> ActionTypes define edits users can perform on the Ontology, with validation and persistence via Functions.

**Key Characteristics:**
- Declarative or function-backed implementation
- Parameter definitions
- Affected ObjectType mappings
- Side effects (notification, webhook, audit)
- Submission criteria for validation

### 6.2 Internal Implementation

```python
# From action_type.py:
class ActionImplementationType(str, Enum):
    DECLARATIVE = "DECLARATIVE"
    FUNCTION_BACKED = "FUNCTION_BACKED"
    INLINE_EDIT = "INLINE_EDIT"

class SideEffectType(str, Enum):
    NOTIFICATION = "NOTIFICATION"
    WEBHOOK = "WEBHOOK"
    EMAIL = "EMAIL"
    AUDIT_LOG = "AUDIT_LOG"
    TRIGGER_ACTION = "TRIGGER_ACTION"
```

**✅ Comprehensive implementation with extended features.**

---

## 7. Cardinality Model

### 7.1 Official Cardinality Types
**Source:** Palantir Link Documentation

| Type | Description |
|------|-------------|
| ONE_TO_ONE | Single object on both sides |
| ONE_TO_MANY | One source to many targets |
| MANY_TO_ONE | Many sources to one target |
| MANY_TO_MANY | Requires backing/junction table |

### 7.2 Implementation Notes

> **ONE_TO_ONE is typically an indicator rather than strictly enforced in Palantir Foundry.**
> Use `enforced=True` for strict enforcement.

### 7.3 Internal Implementation

```python
# From enums.py:
class Cardinality(str, Enum):
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"

    @property
    def requires_backing_table(self) -> bool:
        return self == Cardinality.MANY_TO_MANY
```

**✅ Correctly implements backing table requirement for MANY_TO_MANY.**

---

## 8. Identified Gaps Summary

| Category | Gap | Severity | Recommendation |
|----------|-----|----------|----------------|
| DataType | DECIMAL included but NOT valid Palantir base type | HIGH | Review usage, consider removal or document as extension |
| DataType | BINARY included but NOT valid Palantir base type | HIGH | Review usage, consider removal or document as extension |
| DataType | DATETIME not in official list | MEDIUM | Document as mapping to TIMESTAMP |
| DataType | JSON not explicitly in official list | MEDIUM | Document as extension |
| DataType | MARKDOWN not in official list | LOW | Document as extension |
| Status | EXAMPLE status from Palantir not implemented | LOW | Consider adding for example ObjectTypes |
| Status | Extended lifecycle (ALPHA, BETA, SUNSET, ARCHIVED, DELETED) | INFO | Internal extensions, document clearly |

---

## 9. References

1. **Palantir Foundry Ontology Documentation**
   - ObjectType Reference
   - LinkType Reference
   - ActionType Reference

2. **Palantir AIP Documentation**
   - Ontology SDK
   - Actions and Functions

3. **Palantir Property Types Documentation**
   - Base Property Types
   - Type Constraints

4. **Palantir Security Documentation**
   - Mandatory Controls
   - Row-Level Security

---

*This document serves as the canonical external reference for Ontology-Definition validation.*
*Last Updated: 2026-01-17*
