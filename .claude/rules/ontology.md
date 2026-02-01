# Ontology Rules (ODA - Ontology-Driven Architecture)

## ObjectType Definitions

### Naming
- PascalCase for type names: `Employee`, `ProjectTask`
- Singular form: `Employee` (not `Employees`)
- Descriptive and domain-specific

### Required Properties
| Property | Description |
|----------|-------------|
| `rid` | Resource ID (primary key) |
| `displayName` | Human-readable name |
| `createdAt` | Creation timestamp |
| `updatedAt` | Last modification timestamp |

### Property Types
```yaml
# Primitive types
string, boolean, integer, long, double, date, timestamp

# Complex types
array<T>, struct<...>, map<K,V>

# Reference types
ObjectReference<TypeName>
```

## LinkType Definitions

### Structure
```yaml
linkType:
  name: EmployeeProject
  source: Employee
  target: Project
  cardinality: many-to-many
  properties:
    role: string
    startDate: date
```

### Cardinality Rules
- `one-to-one`: Strict 1:1 relationship
- `one-to-many`: Parent-child relationship
- `many-to-many`: Association with link properties

## ActionType Definitions

### Naming
- Verb + Noun format: `CreateEmployee`, `AssignProject`
- Clear intent description

### Parameters
- Required vs optional clearly marked
- Validation rules defined
- Default values specified

## Integrity Rules

1. **Immutability**: RIDs never change after creation
2. **Referential Integrity**: Links only to existing objects
3. **Semantic Consistency**: Property types match definitions
4. **Lifecycle Management**: Proper status transitions

## Validation

Before any ontology change:
1. Run `/ontology-core validate`
2. Check cross-type references
3. Verify property type compatibility
4. Test with sample data
