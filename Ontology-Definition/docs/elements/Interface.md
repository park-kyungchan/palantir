# Interface

## Definition

> An Interface defines a contract that ObjectTypes can implement, enabling polymorphism in Palantir Foundry Ontology.
>
> -- Palantir Foundry Documentation

An Interface is an abstract Ontology type that defines common properties and actions for multiple ObjectTypes. It enables:

- **Polymorphism**: ObjectTypes can implement multiple interfaces
- **Contract Enforcement**: Implementers must satisfy all interface requirements
- **Type-Safe Querying**: Query all objects implementing a specific interface
- **Interface-Level Actions**: Define actions that operate on any implementer

---

## Core Concepts

### Contract-Based Design

Interfaces define **contracts** rather than implementations. When an ObjectType implements an Interface:

1. The ObjectType MUST have all required properties defined by the Interface
2. Property data types MUST be compatible with the Interface specification
3. If the Interface extends other Interfaces, ALL parent requirements apply transitively

### Polymorphism in Ontology

Interfaces enable polymorphic operations in Palantir Foundry:

```
Query: "Find all Auditable objects modified today"
        |
        v
+-------+-------+-------+
|       |       |       |
Employee Order  Document
(implements Auditable)
```

Without interfaces, you would need separate queries for each ObjectType.

### Type-Safe Querying

Interface-based queries are type-safe because:
- The query system knows all implementers satisfy the interface contract
- Property access is guaranteed to work on any result
- Actions defined on the interface can operate on any implementer

---

## Schema Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `api_name` | `str` | Unique programmatic identifier (immutable once active) |
| `display_name` | `str` | Human-readable name for UI display |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `rid` | `str` | Auto-generated | Resource ID in format `ri.ontology.{region}.interface.{uuid}` |
| `description` | `str` | `None` | Documentation for the Interface |
| `extends` | `list[str]` | `[]` | Parent Interface apiNames for inheritance |
| `required_properties` | `list[InterfacePropertyRequirement]` | `[]` | Properties implementers must have |
| `interface_actions` | `list[InterfaceActionDefinition]` | `[]` | Actions defined at interface level |
| `status` | `InterfaceStatus` | `EXPERIMENTAL` | Lifecycle status |
| `metadata` | `InterfaceMetadata` | `None` | Extended metadata for versioning/audit |

### Field Validation Rules

1. **api_name**: Must match pattern `^[a-zA-Z][a-zA-Z0-9_]*$`, max 255 chars
2. **display_name**: Max 255 chars
3. **description**: Max 4096 chars
4. **extends**: Cannot include self (prevents trivial circular dependency)
5. **required_properties**: All `property_api_name` values must be unique
6. **interface_actions**: All `action_api_name` values must be unique

---

## Interface Inheritance

### The `extends` Mechanism

Interfaces can extend other Interfaces to create inheritance hierarchies:

```python
from ontology_definition.types.interface import Interface, InterfacePropertyRequirement
from ontology_definition.types.property_def import DataTypeSpec
from ontology_definition.core.enums import DataType

# Base interface
trackable = Interface(
    api_name="Trackable",
    display_name="Trackable Entity",
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="trackingId",
            data_type=DataTypeSpec(type=DataType.STRING),
            required=True
        )
    ]
)

# Derived interface - inherits Trackable's requirements
auditable = Interface(
    api_name="Auditable",
    display_name="Auditable Entity",
    extends=["Trackable"],  # Inherits trackingId requirement
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="createdAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        ),
        InterfacePropertyRequirement(
            property_api_name="createdBy",
            data_type=DataTypeSpec(type=DataType.STRING)
        )
    ]
)
```

When an ObjectType implements `Auditable`, it must satisfy:
- `trackingId` (from Trackable)
- `createdAt` (from Auditable)
- `createdBy` (from Auditable)

### Multiple Inheritance Rules

1. **Diamond Problem Resolution**: If multiple parent interfaces define the same property, the most specific (child) definition wins
2. **Circular Dependency Prevention**: Validated at registration time via `InterfaceRegistry.detect_circular_inheritance()`
3. **Transitive Requirements**: All ancestor interface requirements apply

```
     Identifiable
        /    \
   Trackable  Timestamped
        \    /
       Auditable
```

An ObjectType implementing `Auditable` must satisfy requirements from all four interfaces.

### Inheritance Resolution

Use `InterfaceRegistry` to resolve the full inheritance hierarchy:

```python
from ontology_definition.registry.interface_registry import get_interface_registry

registry = get_interface_registry()

# Get direct parents
parents = registry.get_parent_interfaces("Auditable")
# Returns: ["Trackable"]

# Get all ancestors (transitive)
ancestors = registry.get_all_ancestor_interfaces("Auditable")
# Returns: ["Trackable", "Identifiable", ...] in breadth-first order

# Get full hierarchy tree
hierarchy = registry.get_interface_hierarchy("Auditable")
# Returns: {"Auditable": ["Trackable"], "Trackable": ["Identifiable"], ...}
```

---

## Required Properties

### InterfacePropertyRequirement

Defines a property that implementing ObjectTypes MUST have:

```python
class InterfacePropertyRequirement(BaseModel):
    property_api_name: str  # apiName implementers must use
    data_type: DataTypeSpec  # Required data type
    description: Optional[str]  # Documentation
    required: bool  # If true, implementers must have this as required property
```

**Important**: `InterfacePropertyRequirement` defines the **contract**, not the actual property. The implementing ObjectType's `PropertyDefinition` must be compatible.

### Field Constraints

| Field | Type | Constraints |
|-------|------|-------------|
| `property_api_name` | `str` | Pattern: `^[a-zA-Z][a-zA-Z0-9_]*$`, 1-255 chars |
| `data_type` | `DataTypeSpec` | Any valid Palantir data type |
| `description` | `str` | Max 4096 chars |
| `required` | `bool` | Default: `False` |

### Example: Defining Property Requirements

```python
from ontology_definition.types.interface import Interface, InterfacePropertyRequirement
from ontology_definition.types.property_def import DataTypeSpec
from ontology_definition.core.enums import DataType

audit_interface = Interface(
    api_name="Auditable",
    display_name="Auditable Entity",
    description="Interface for entities that track audit information",
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="createdAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP),
            description="When the entity was created",
            required=True  # Implementers MUST have this as required
        ),
        InterfacePropertyRequirement(
            property_api_name="createdBy",
            data_type=DataTypeSpec(type=DataType.STRING),
            description="User who created the entity"
        ),
        InterfacePropertyRequirement(
            property_api_name="modifiedAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP),
            description="When the entity was last modified"
        ),
        InterfacePropertyRequirement(
            property_api_name="modifiedBy",
            data_type=DataTypeSpec(type=DataType.STRING),
            description="User who last modified the entity"
        )
    ]
)
```

### Mapping Requirements

When an ObjectType implements an Interface:

1. **Name Match**: ObjectType property `api_name` must match `property_api_name`
2. **Type Compatibility**: ObjectType property `data_type` must be compatible
3. **Required Flag**: If interface property is `required=True`, ObjectType property must also be required

---

## Interface Actions

### InterfaceActionDefinition

Actions defined at the interface level enable polymorphic operations:

```python
class InterfaceActionDefinition(BaseModel):
    action_api_name: str  # apiName of the ActionType
    description: Optional[str]  # Documentation
    is_abstract: bool  # If true, each implementer must provide implementation
```

**Note**: This is a **reference** to an ActionType, not a full definition. The actual ActionType must be defined separately.

### Action Inheritance

1. **Concrete Actions**: Defined once at interface level, apply to all implementers
2. **Abstract Actions**: Each implementing ObjectType must provide its own implementation

### Example: Interface with Actions

```python
from ontology_definition.types.interface import Interface, InterfaceActionDefinition

approvable = Interface(
    api_name="Approvable",
    display_name="Approvable Entity",
    description="Interface for entities that require approval workflow",
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="approvalStatus",
            data_type=DataTypeSpec(type=DataType.STRING),
            description="Current approval status"
        ),
        InterfacePropertyRequirement(
            property_api_name="approvedBy",
            data_type=DataTypeSpec(type=DataType.STRING),
            description="User who approved"
        ),
        InterfacePropertyRequirement(
            property_api_name="approvedAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP),
            description="When approved"
        )
    ],
    interface_actions=[
        InterfaceActionDefinition(
            action_api_name="approve",
            description="Approve this entity",
            is_abstract=False  # Single implementation for all
        ),
        InterfaceActionDefinition(
            action_api_name="reject",
            description="Reject this entity",
            is_abstract=False
        ),
        InterfaceActionDefinition(
            action_api_name="sendForReview",
            description="Send entity for review - implementation varies",
            is_abstract=True  # Each ObjectType must implement
        )
    ]
)
```

---

## Implementing ObjectTypes

### How ObjectTypes Implement Interfaces

ObjectTypes declare interface implementation via the `interfaces` field:

```python
from ontology_definition.types.object_type import ObjectType
from ontology_definition.types.property_def import PropertyDefinition, DataTypeSpec
from ontology_definition.core.enums import DataType

employee = ObjectType(
    api_name="Employee",
    display_name="Employee",
    primary_key="employeeId",
    interfaces=["Auditable", "Approvable"],  # Implements both
    properties=[
        PropertyDefinition(
            api_name="employeeId",
            data_type=DataTypeSpec(type=DataType.STRING),
            description="Unique employee identifier"
        ),
        # Satisfies Auditable requirements
        PropertyDefinition(
            api_name="createdAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        ),
        PropertyDefinition(
            api_name="createdBy",
            data_type=DataTypeSpec(type=DataType.STRING)
        ),
        PropertyDefinition(
            api_name="modifiedAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        ),
        PropertyDefinition(
            api_name="modifiedBy",
            data_type=DataTypeSpec(type=DataType.STRING)
        ),
        # Satisfies Approvable requirements
        PropertyDefinition(
            api_name="approvalStatus",
            data_type=DataTypeSpec(type=DataType.STRING)
        ),
        PropertyDefinition(
            api_name="approvedBy",
            data_type=DataTypeSpec(type=DataType.STRING)
        ),
        PropertyDefinition(
            api_name="approvedAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        )
    ]
)
```

### Validation Rules

Validation is performed by `InterfaceRegistry`:

```python
from ontology_definition.registry.interface_registry import get_interface_registry

registry = get_interface_registry()

# Validate single interface implementation
is_valid, missing = registry.validate_object_type_implements(employee, "Auditable")
if not is_valid:
    print(f"Missing properties: {missing}")

# Validate all declared interfaces
results = registry.validate_all_interfaces_for_object_type(employee)
for interface_name, (is_valid, missing) in results.items():
    if not is_valid:
        print(f"{interface_name}: missing {missing}")
```

### Validation Checks

| Check | Description | Error |
|-------|-------------|-------|
| Property Existence | All required properties must exist | `Missing property: {name}` |
| Type Compatibility | Property types must match | `Type mismatch: expected {X}, got {Y}` |
| Required Flag | If interface says required, ObjectType must too | `Property must be required` |

---

## Lifecycle Status

### InterfaceStatus Enum

```python
class InterfaceStatus(str, Enum):
    DRAFT = "DRAFT"           # Under development, not ready for use
    EXPERIMENTAL = "EXPERIMENTAL"  # Ready for testing, may change
    ACTIVE = "ACTIVE"         # In active use
    STABLE = "STABLE"         # Schema frozen, production-ready
    DEPRECATED = "DEPRECATED"  # Marked for removal
    ARCHIVED = "ARCHIVED"     # No longer in use, retained for history
```

### Status Lifecycle

```
DRAFT -> EXPERIMENTAL -> ACTIVE -> STABLE -> DEPRECATED -> ARCHIVED
```

### ENDORSED Status Exclusion

**Important**: Interfaces do NOT support `ENDORSED` status.

This is intentional and aligns with Palantir Foundry behavior:
- **Endorsement applies to ObjectTypes**, not contracts
- Interfaces define contracts; ObjectTypes implement them
- An Interface being "endorsed" doesn't make sense conceptually
- Individual ObjectTypes implementing an interface can be endorsed separately

This design decision is documented as **GAP-005** in the implementation.

---

## Examples

### Basic Interface (Auditable)

A minimal interface defining audit trail requirements:

```python
from ontology_definition.types.interface import Interface, InterfacePropertyRequirement, InterfaceStatus
from ontology_definition.types.property_def import DataTypeSpec
from ontology_definition.core.enums import DataType

auditable = Interface(
    api_name="Auditable",
    display_name="Auditable Entity",
    description="Interface for entities that track audit information",
    status=InterfaceStatus.ACTIVE,
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="createdAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP),
            description="When the entity was created"
        ),
        InterfacePropertyRequirement(
            property_api_name="createdBy",
            data_type=DataTypeSpec(type=DataType.STRING),
            description="Who created the entity"
        )
    ]
)

# Export to Foundry format
foundry_dict = auditable.to_foundry_dict()
# {
#   "apiName": "Auditable",
#   "displayName": "Auditable Entity",
#   "description": "Interface for entities that track audit information",
#   "status": "ACTIVE",
#   "requiredProperties": [
#     {"propertyApiName": "createdAt", "dataType": {"type": "TIMESTAMP"}, ...},
#     {"propertyApiName": "createdBy", "dataType": {"type": "STRING"}, ...}
#   ]
# }
```

### Interface with Actions (Approvable)

An interface defining both properties and polymorphic actions:

```python
approvable = Interface(
    api_name="Approvable",
    display_name="Approvable Entity",
    description="Interface for entities requiring approval workflow",
    status=InterfaceStatus.ACTIVE,
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="approvalStatus",
            data_type=DataTypeSpec(type=DataType.STRING),
            description="Current approval status (PENDING, APPROVED, REJECTED)",
            required=True
        ),
        InterfacePropertyRequirement(
            property_api_name="approvedBy",
            data_type=DataTypeSpec(type=DataType.STRING)
        ),
        InterfacePropertyRequirement(
            property_api_name="approvedAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        ),
        InterfacePropertyRequirement(
            property_api_name="rejectionReason",
            data_type=DataTypeSpec(type=DataType.STRING)
        )
    ],
    interface_actions=[
        InterfaceActionDefinition(
            action_api_name="approve",
            description="Mark entity as approved"
        ),
        InterfaceActionDefinition(
            action_api_name="reject",
            description="Mark entity as rejected"
        ),
        InterfaceActionDefinition(
            action_api_name="requestReview",
            description="Send for human review",
            is_abstract=True  # Each implementer defines
        )
    ]
)
```

### Interface Inheritance

Building a hierarchy of related interfaces:

```python
# Level 1: Base identity
identifiable = Interface(
    api_name="Identifiable",
    display_name="Identifiable Entity",
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="uuid",
            data_type=DataTypeSpec(type=DataType.STRING),
            required=True
        )
    ]
)

# Level 2: Extends Identifiable
trackable = Interface(
    api_name="Trackable",
    display_name="Trackable Entity",
    extends=["Identifiable"],
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="trackingId",
            data_type=DataTypeSpec(type=DataType.STRING)
        ),
        InterfacePropertyRequirement(
            property_api_name="lastSeen",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        )
    ]
)

# Level 2: Also extends Identifiable
timestamped = Interface(
    api_name="Timestamped",
    display_name="Timestamped Entity",
    extends=["Identifiable"],
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="createdAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        ),
        InterfacePropertyRequirement(
            property_api_name="modifiedAt",
            data_type=DataTypeSpec(type=DataType.TIMESTAMP)
        )
    ]
)

# Level 3: Multiple inheritance
audit_compliant = Interface(
    api_name="AuditCompliant",
    display_name="Audit Compliant Entity",
    extends=["Trackable", "Timestamped"],  # Both parents
    required_properties=[
        InterfacePropertyRequirement(
            property_api_name="auditLog",
            data_type=DataTypeSpec(type=DataType.JSON)
        )
    ]
)

# An ObjectType implementing AuditCompliant must have:
# - uuid (from Identifiable)
# - trackingId, lastSeen (from Trackable)
# - createdAt, modifiedAt (from Timestamped)
# - auditLog (from AuditCompliant)
```

---

## Palantir Alignment

### Confirmed Alignment

| Feature | Palantir Foundry | Implementation | Status |
|---------|-----------------|----------------|--------|
| Required properties | Yes | `required_properties` | Aligned |
| Interface inheritance | Yes | `extends` | Aligned |
| Interface-level actions | Yes | `interface_actions` | Aligned |
| Polymorphic queries | Yes | Via `InterfaceRegistry` | Aligned |
| No ENDORSED status | Correct | `InterfaceStatus` excludes it | Aligned |

### Implementation Notes

1. **Status Values**: Extended beyond Palantir's official list (ACTIVE, EXPERIMENTAL, DEPRECATED) to include DRAFT, STABLE, ARCHIVED for enhanced lifecycle management

2. **ENDORSED Exclusion**: Palantir documentation confirms ENDORSED applies only to ObjectTypes. Our `InterfaceStatus` enum correctly excludes this status.

3. **Beta Feature**: Per Palantir documentation, Interfaces are an "OSv2 / Beta feature". Implementation supports current documented behavior.

---

## API Reference

### Interface Class

```python
class Interface(OntologyEntity):
    """Interface schema definition - enabling polymorphism in Palantir Ontology."""

    # Inherited from OntologyEntity
    rid: str                          # Auto-generated resource ID
    api_name: str                     # Unique programmatic identifier
    display_name: str                 # Human-readable name
    description: Optional[str]        # Documentation

    # Interface-specific
    extends: list[str]                # Parent interface apiNames
    required_properties: list[InterfacePropertyRequirement]
    interface_actions: list[InterfaceActionDefinition]
    status: InterfaceStatus
    metadata: Optional[InterfaceMetadata]
```

### Key Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_required_property(api_name)` | `InterfacePropertyRequirement | None` | Get property requirement by name |
| `get_interface_action(api_name)` | `InterfaceActionDefinition | None` | Get action definition by name |
| `has_parent(interface_api_name)` | `bool` | Check if extends given interface |
| `get_all_required_property_names()` | `set[str]` | Get all direct property apiNames |
| `to_foundry_dict()` | `dict[str, Any]` | Export to Foundry JSON format |
| `from_foundry_dict(data)` | `Interface` | Create from Foundry JSON |

### InterfacePropertyRequirement Class

```python
class InterfacePropertyRequirement(BaseModel):
    property_api_name: str      # Required property apiName
    data_type: DataTypeSpec     # Required data type
    description: Optional[str]  # Documentation
    required: bool = False      # Must implementer property be required?
```

### InterfaceActionDefinition Class

```python
class InterfaceActionDefinition(BaseModel):
    action_api_name: str        # Reference to ActionType
    description: Optional[str]  # Documentation
    is_abstract: bool = False   # Must each implementer provide implementation?
```

### InterfaceImplementation Class

```python
class InterfaceImplementation(BaseModel):
    """Tracks ObjectType interface implementations."""
    interface_api_name: str     # Interface being implemented
    object_type_api_name: str   # Implementing ObjectType
    is_valid: bool = True       # Validation passed?
    validation_errors: list[str] = []  # Error messages if invalid
```

### InterfaceRegistry Class

```python
class InterfaceRegistry:
    """Singleton registry for Interface inheritance tracking."""

    # Registration
    def register_interface(interface: Interface) -> None
    def unregister_interface(api_name: str) -> None

    # Inheritance queries
    def get_parent_interfaces(api_name: str) -> list[str]
    def get_all_ancestor_interfaces(api_name: str) -> list[str]
    def get_interface_hierarchy(api_name: str) -> dict[str, list[str]]

    # Property resolution
    def resolve_properties(api_name: str) -> list[PropertyDefinition]
    def resolve_required_properties(api_name: str) -> list[PropertyDefinition]

    # Validation
    def validate_object_type_implements(obj_type, interface_name) -> tuple[bool, list[str]]
    def validate_all_interfaces_for_object_type(obj_type) -> dict[str, tuple[bool, list[str]]]
    def detect_circular_inheritance(api_name: str) -> list[str] | None
```

---

## Related Documentation

- [ObjectType](./ObjectType.md) - Schema definition for entities that implement interfaces
- [PropertyDefinition](./PropertyDefinition.md) - Property schema used in requirements
- [DataType](./DataType.md) - Supported data types for properties
- [ActionType](./ActionType.md) - Actions that can be defined at interface level

---

## Source Files

| File | Purpose |
|------|---------|
| `ontology_definition/types/interface.py` | Interface, InterfacePropertyRequirement, InterfaceActionDefinition, InterfaceImplementation |
| `ontology_definition/registry/interface_registry.py` | InterfaceRegistry for inheritance tracking |
| `ontology_definition/core/metadata.py` | InterfaceMetadata for audit/versioning |
