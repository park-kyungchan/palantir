# Ontology-Definition Quick Reference

**Version:** 1.0.0 | **Palantir Alignment:** 78%

---

## 1. Core Elements at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    ONTOLOGY ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐        LinkType         ┌──────────────┐   │
│   │  ObjectType  │◄──────────────────────►│  ObjectType  │   │
│   │              │   (1:1, 1:N, N:1, N:N)  │              │   │
│   │  - Properties│                         │  - Properties│   │
│   │  - PK        │                         │  - PK        │   │
│   │  - Security  │                         │  - Security  │   │
│   └──────┬───────┘                         └──────┬───────┘   │
│          │                                        │           │
│          │ implements                             │           │
│          ▼                                        ▼           │
│   ┌──────────────┐                        ┌──────────────┐   │
│   │  Interface   │                        │  ActionType  │   │
│   │              │                        │              │   │
│   │  - Required  │                        │  - Parameters│   │
│   │    Properties│                        │  - Side      │   │
│   │  - Actions   │                        │    Effects   │   │
│   └──────────────┘                        └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Element Quick Reference

### ObjectType
```python
ObjectType(
    api_name="Employee",           # Required: camelCase
    display_name="Employee",       # Required: human-readable
    primary_key=PrimaryKeyDefinition(
        property_api_name="employeeId",
        key_type="DATASET_PRIMARY_KEY"
    ),
    properties=[...],              # List[PropertyDefinition]
    status=ObjectStatus.ACTIVE,    # DRAFT → ACTIVE → DEPRECATED
    # ENDORSED status available (ObjectType only!)
)
```

### LinkType
```python
LinkType(
    api_name="employeeToDepartment",
    source_object_type="Employee",  # Required
    target_object_type="Department",# Required
    cardinality=Cardinality.MANY_TO_ONE,
    implementation=LinkImplementation(
        type="FOREIGN_KEY",
        foreign_key_config=ForeignKeyConfig(
            source_property="departmentId",
            target_property="departmentId"
        )
    ),
    # Note: ENDORSED status NOT supported
)
```

### ActionType
```python
ActionType(
    api_name="assignEmployee",
    implementation_type=ActionImplementationType.DECLARATIVE,
    parameters=[
        ActionParameter(
            api_name="employeeId",
            data_type=ParameterDataType(type="OBJECT_PICKER"),
            required=True
        )
    ],
    affected_object_types=[...],
    side_effects=[SideEffect(type="AUDIT_LOG")],
    # Note: ENDORSED status NOT supported
)
```

### Interface
```python
Interface(
    api_name="Auditable",
    extends=["BaseEntity"],        # Interface inheritance
    required_properties=[
        InterfacePropertyRequirement(
            api_name="createdAt",
            data_type=DataType.TIMESTAMP,
            required=True
        )
    ],
    # Note: ENDORSED status NOT supported
)
```

---

## 3. Data Types

### Primitive Types
| Type | Python | Example |
|------|--------|---------|
| `STRING` | str | "Hello" |
| `INTEGER` | int (32-bit) | 42 |
| `LONG` | int (64-bit) | 9223372036854775807 |
| `FLOAT` | float (32-bit) | 3.14 |
| `DOUBLE` | float (64-bit) | 3.141592653589793 |
| `BOOLEAN` | bool | True |

### Temporal Types
| Type | Format | Example |
|------|--------|---------|
| `DATE` | YYYY-MM-DD | "2026-01-17" |
| `TIMESTAMP` | ISO 8601 | "2026-01-17T15:30:00Z" |
| `DATETIME` | ISO 8601 | "2026-01-17T15:30:00" |
| `TIMESERIES` | Array of (time, value) | ⚠️ Cannot be array item |

### Complex Types
| Type | Configuration | Example |
|------|--------------|---------|
| `ARRAY` | array_item_type required | ["a", "b", "c"] |
| `STRUCT` | struct_fields required | {street: "...", city: "..."} |
| `VECTOR` | vector_dimension required | [0.1, 0.2, ...] ⚠️ Cannot be array item |

### ⚠️ Extension Types (Not Palantir Standard)
| Type | Note |
|------|------|
| `DECIMAL` | ❌ NOT valid Palantir base type |
| `BINARY` | ❌ NOT valid Palantir base type |
| `JSON` | Internal extension |
| `MARKDOWN` | Internal extension |

---

## 4. Status Lifecycle

### ObjectType Status (with ENDORSED)
```
DRAFT → EXPERIMENTAL → ALPHA → BETA → ACTIVE → STABLE → DEPRECATED → SUNSET → ARCHIVED → DELETED
                                         ↓
                                     ENDORSED (ObjectType only, set by Ontology Owner)
```

### LinkType/ActionType/Interface Status (NO ENDORSED)
```
DRAFT → EXPERIMENTAL → ALPHA → BETA → ACTIVE → STABLE → DEPRECATED → SUNSET → ARCHIVED → DELETED
```

---

## 5. Cardinality Quick Reference

| Type | Source | Target | Implementation |
|------|--------|--------|----------------|
| ONE_TO_ONE | 1 | 1 | FK (indicator only, not enforced) |
| ONE_TO_MANY | 1 | N | FK on target |
| MANY_TO_ONE | N | 1 | FK on source |
| MANY_TO_MANY | N | N | **Backing table required** |

---

## 6. Security Model

### ControlType
| Type | Use Case |
|------|----------|
| `MARKINGS` | Security markings (most common) |
| `ORGANIZATIONS` | Organization-based access |
| `CLASSIFICATIONS` | CBAC (government use) |

### Mandatory Control Rules
```python
# When isMandatoryControl=True:
# ✓ Must have mandatory_control_config
# ✓ Must have required=True
# ✓ Cannot have default_value
# ✓ Must be STRING or ARRAY[STRING]
```

---

## 7. Constraint Quick Reference

### PropertyConstraints
```python
PropertyConstraints(
    required=True,              # Cannot be null
    immutable=True,             # Cannot change after creation
    unique=True,                # Must be unique
    default_value="draft",      # Default if not provided
    enum_values=["a", "b"],     # Allowed values
    string=StringConstraints(
        min_length=1,
        max_length=255,
        pattern=r"^[A-Z]"
    ),
    numeric=NumericConstraints(
        min_value=0,
        max_value=100
    ),
    array=ArrayConstraints(
        min_items=1,
        max_items=10,
        unique_items=True
    )
)
```

---

## 8. Common Patterns

### Audit Properties (SharedProperty)
```python
CommonSharedProperties.created_at()   # TIMESTAMP, required, immutable
CommonSharedProperties.modified_at()  # TIMESTAMP, required
CommonSharedProperties.created_by()   # STRING, required, immutable
CommonSharedProperties.modified_by()  # STRING, required
```

### Security Markings
```python
CommonSharedProperties.security_markings()
# → ARRAY[STRING], required, mandatory_control
#   ControlType.MARKINGS, EnforcementLevel.STRICT
```

### Common StructTypes
```python
CommonStructTypes.address()           # street, city, state, postalCode, country
CommonStructTypes.monetary_amount()   # amount (DECIMAL), currency
CommonStructTypes.geo_coordinate()    # latitude, longitude, altitude
CommonStructTypes.contact_info()      # email, phone, fax
```

### Common ValueTypes
```python
CommonValueTypes.email_address()      # STRING with email pattern
CommonValueTypes.positive_integer()   # INTEGER with min_value=1
CommonValueTypes.priority()           # STRING enum [LOW, MEDIUM, HIGH, CRITICAL]
CommonValueTypes.url()                # STRING with URL format
CommonValueTypes.uuid()               # STRING with UUID pattern
CommonValueTypes.percentage()         # DOUBLE 0-100
```

---

## 9. Cascade Policies

| Policy | On Delete | On Update |
|--------|-----------|-----------|
| `CASCADE` | Delete linked | Update linked |
| `SET_NULL` | Set FK to null | Set FK to null |
| `RESTRICT` | Block if linked | Block if linked |
| `NO_ACTION` | No automatic action | No automatic action |

---

## 10. Validation Order

```
1. PERMISSION_CHECK           # User has access?
2. SCHEMA_VALIDATION          # Type/constraint check
3. BUSINESS_RULE_VALIDATION   # Custom rules
4. REFERENTIAL_INTEGRITY      # FK exists?
5. SECURITY_MARKING_VALIDATION # Marking access?
6. AUDIT_LOGGING              # Log the operation
```

---

## 11. API Methods

### Serialization
```python
# Export to Palantir Foundry format
obj.to_foundry_dict()  # Returns dict

# Import from Palantir Foundry format
ObjectType.from_foundry_dict(data)  # Returns ObjectType
```

### Helper Methods
```python
# ObjectType
obj.get_property("propertyName")
obj.get_required_properties()
obj.is_primary_key("propertyName")

# LinkType
link.get_cardinality_description()
link.requires_backing_table()  # True for MANY_TO_MANY

# StructType
struct.get_field("fieldName")
struct.get_required_fields()
struct.get_field_names()
```

---

## 12. Gap Summary (Critical)

| ID | Gap | Priority | Status |
|----|-----|----------|--------|
| GAP-001 | Restricted Views | P1 | ❌ |
| GAP-002 | Mandatory Control | P1 | ⚠️ |
| GAP-003 | Schema Export | P2 | ⚠️ |
| GAP-005 | ENDORSED Status | P2 | ❌ |
| GAP-007 | 1:1 Indicator Only | P2 | ❌ |

---

## 13. File Reference

| Element | File |
|---------|------|
| ObjectType | `types/object_type.py` |
| LinkType | `types/link_type.py` |
| ActionType | `types/action_type.py` |
| Interface | `types/interface.py` |
| Property | `types/property_def.py` |
| Enums | `core/enums.py` |
| SharedProperty | `types/shared_property.py` |
| StructType | `types/struct_type.py` |
| ValueType | `types/value_type.py` |
| Constraints | `constraints/property_constraints.py` |
| MandatoryControl | `constraints/mandatory_control.py` |

---

*Quick Reference v1.0.0 | Ontology-Definition Project*
