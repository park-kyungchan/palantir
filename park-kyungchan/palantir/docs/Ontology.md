# Palantir AIP/Foundry Ontology: Complete Machine-Readable Reference

This document provides unambiguous definitions and practical mapping guidelines for all Palantir Ontology components, enabling Claude-Code-CLI to refactor projects to Ontology-Driven Architecture with precision.

---

## Component Reference Index

```yaml
ontology_components:
  data_model:
    - ObjectType      # Entity/domain object schema
    - PropertyType    # Attribute definitions with 20+ base types
  relationships:
    - LinkType        # Object-to-object relationships
    - Interface       # Polymorphic type contracts
  behavior:
    - ActionType      # Atomic data mutation operations
    - Function        # Executable logic units (@Function, @Query, @OntologyEditFunction)
  operations:
    - ObjectSet       # Filtered object collections with operators
    - Workflow        # Sequential/conditional execution via Foundry Rules
    - Automation      # Event-driven triggers (Automate)
  advanced:
    - RulesEngine     # Dynamic business rule evaluation
    - Writeback       # External system synchronization
    - Versioning      # Schema evolution and governance
```

---

# 1. ObjectType

## Official Definition
> "An **object type** is the schema definition of a real-world entity or event. An **object** or **object instance** refers to a single instance of an object type; an object corresponds to a single real-world entity or event."
> — Palantir Foundry Documentation

## Schema
```yaml
ObjectType:
  apiName: string           # PascalCase, e.g., "Employee"
  rid: string               # Resource ID: "ri.ontology.main.object-type.xxx"
  displayName: string       # Human-readable name
  pluralDisplayName: string # Plural form for UI
  description: string       # Documentation
  status: enum              # ACTIVE | ENDORSED | EXPERIMENTAL | DEPRECATED
  visibility: enum          # NORMAL | PROMINENT | HIDDEN
  primaryKey: list[PropertyApiName]  # Properties forming unique identifier
  properties: map[PropertyApiName, Property]  # Property definitions
  titleProperty: PropertyApiName  # Display name property
  descriptionProperty: PropertyApiName  # Description property
  icon: BlueprintIcon       # UI icon configuration
```

## Primary Key Rules
```yaml
primary_key_constraints:
  uniqueness: "Must be unique for every record in backing datasource"
  determinism: "Must be deterministic; changes cause lost edits and broken links"
  immutability: "Actions cannot edit primary keys (equivalent to delete + create)"
  duplicates: "OSv2: Duplicates cause Funnel pipeline build failures"

valid_pk_types:
  recommended: [String, Integer, Short]
  discouraged:
    Long: "JavaScript precision loss for values > 1e15; use String instead"
    Date: "Format collision risk; use String"
    Timestamp: "Format collision risk; use String"
    Boolean: "Limits to 2 object instances"
    Byte: "Use Integer instead"
  invalid: [Float, Double, Decimal, Array, Struct, Vector, GeoPoint, Geoshape]
```

## Code Pattern Identification Rules
```yaml
identification_rules:
  - pattern: "Class with @Entity or @Id annotation"
    mapping: ObjectType
    confidence: HIGH
    
  - pattern: "Class representing Aggregate Root (DDD)"
    mapping: ObjectType
    confidence: HIGH
    
  - pattern: "Class with unique identifier field + business attributes"
    mapping: ObjectType
    confidence: HIGH
    
  - pattern: "Database table with primary key"
    mapping: ObjectType
    confidence: HIGH
    
  - pattern: "Value Object (no identity)"
    mapping: "Struct property on parent ObjectType OR separate ObjectType if shared"
    confidence: MEDIUM
    
  - pattern: "Enum type"
    mapping: "String property with validation"
    confidence: HIGH
```

## Anti-Patterns
```yaml
anti_patterns:
  - name: "Long as Primary Key for Frontend"
    problem: "JavaScript loses precision for values > 1e15"
    solution: "Use String type for IDs passed to frontend"
    
  - name: "Non-deterministic Primary Keys"
    problem: "Random or auto-increment IDs not derived from business data"
    solution: "Derive from stable business attributes"
    
  - name: "Changing Primary Keys After Creation"
    problem: "Breaks links and loses user edits"
    solution: "Treat as delete + create if key must change"
```

---

# 2. PropertyType

## Official Definition
> "A **property** of an object type is the schema definition of a characteristic of a real-world entity or event. A **property value** refers to the value of a property on an object."
> — Palantir Foundry Documentation

## Schema
```yaml
Property:
  apiName: string           # camelCase, e.g., "startDate"
  displayName: string       # Human-readable name
  description: string       # Documentation
  rid: string               # Resource ID
  baseType: BaseType        # See complete list below
  status: enum              # ACTIVE | EXPERIMENTAL | DEPRECATED
  visibility: enum          # NORMAL | PROMINENT | HIDDEN
  isPrimaryKey: boolean
  isTitleKey: boolean
  searchable: boolean       # Enable text search
  sortable: boolean         # Enable sorting
  nullable: boolean         # Default: true (all properties nullable)
```

## Complete BaseType Reference
```yaml
base_types:
  primitives:
    String:
      title_key: true
      primary_key: true
      actions_support: FULL
      notes: "Recommended for most identifiers"
      
    Integer:
      title_key: true
      primary_key: true
      actions_support: FULL
      range: "-2^31 to 2^31-1"
      
    Long:
      title_key: true
      primary_key: DISCOURAGED
      actions_support: LIMITED
      notes: "JS precision loss >1e15; use String for IDs"
      
    Double:
      title_key: true
      primary_key: false
      actions_support: FULL
      notes: "64-bit floating point"
      
    Float:
      title_key: true
      primary_key: false
      actions_support: LIMITED
      notes: "32-bit floating point; prefer Double"
      
    Boolean:
      title_key: true
      primary_key: DISCOURAGED
      actions_support: FULL
      
    Short:
      title_key: true
      primary_key: true
      actions_support: LIMITED
      range: "-32768 to 32767"
      
    Byte:
      title_key: true
      primary_key: DISCOURAGED
      actions_support: LIMITED
      notes: "Use Integer instead"
      
    Decimal:
      title_key: true
      primary_key: false
      actions_support: NONE
      notes: "NOT supported in OSv2; use Double or String"

  date_time:
    Date:
      title_key: true
      primary_key: DISCOURAGED
      format: "YYYY-MM-DD"
      
    Timestamp:
      title_key: true
      primary_key: DISCOURAGED
      format: "ISO 8601"

  specialized:
    GeoPoint:
      title_key: true
      primary_key: false
      notes: "Geographic point (lat/long)"
      
    Geoshape:
      title_key: false
      primary_key: false
      notes: "Polygons, lines, shapes"
      
    Attachment:
      title_key: false
      primary_key: false
      notes: "File attachments"
      
    Timeseries:
      title_key: false
      primary_key: false
      notes: "Temporal data series"
      
    MediaReference:
      title_key: false
      primary_key: false
      notes: "Reference to media in media sets"
      
    Marking:
      title_key: false
      primary_key: false
      notes: "Access control markings"
      
    Ciphertext:
      title_key: true
      primary_key: false
      notes: "Encrypted string values"
      
    Vector:
      title_key: false
      primary_key: false
      max_dimensions: 2048
      notes: "Semantic search embeddings"

  complex:
    Array:
      title_key: "Only if inner type valid"
      primary_key: false
      constraints:
        - "No null elements"
        - "No nested arrays in OSv2"
        
    Struct:
      title_key: false
      primary_key: false
      constraints:
        max_depth: 1
        min_fields: 1
        max_fields: 10
        supported_field_types: [BOOLEAN, BYTE, DATE, DECIMAL, DOUBLE, FLOAT, GEOPOINT, INTEGER, LONG, SHORT, STRING, TIMESTAMP]
        
    Map:
      supported: false
      notes: "Not supported as Ontology base type"
```

## Code Pattern Identification Rules
```yaml
field_type_mapping:
  java_typescript:
    "String, UUID": String
    "int, Integer, number": Integer
    "long, Long, bigint": String  # Avoid Long for JS precision
    "double, Double": Double
    "boolean, Boolean": Boolean
    "LocalDate": Date
    "Instant, ZonedDateTime, DateTime": Timestamp
    "BigDecimal": String  # Decimal not in OSv2
    "List<T>, T[]": "Array<T>"
    "enum": "String with validation"
    
  complex_object_rules:
    - condition: "Nested object with ≤10 fields, depth 1"
      mapping: Struct
      
    - condition: "Nested object with >10 fields OR depth >1"
      mapping: "Separate ObjectType + LinkType"
      
    - condition: "Shared across multiple parent objects"
      mapping: "Separate ObjectType + LinkType"
```

---

# 3. LinkType

## Official Definition
> "A link type is the schema definition of a relationship between two object types. A link refers to a single instance of that relationship between two objects."
> — Palantir Foundry Documentation

## Schema
```yaml
LinkType:
  id: string                # Unique identifier (kebab-case)
  rid: string               # Resource ID
  status: enum              # ACTIVE | EXPERIMENTAL | DEPRECATED
  
  source:
    objectType: ObjectTypeApiName
    displayName: string     # Name shown from source perspective
    apiName: string         # Code reference name
    
  target:
    objectType: ObjectTypeApiName
    displayName: string     # Name shown from target perspective
    apiName: string         # Code reference name
    
  cardinality: enum         # ONE_TO_ONE | ONE_TO_MANY | MANY_TO_ONE | MANY_TO_MANY
  
  implementation:
    type: enum              # FOREIGN_KEY | JOIN_TABLE | OBJECT_BACKED
    foreignKeyProperty: PropertyApiName  # For FK-based
    joinDataset: DatasetRid              # For N:N
    backingObjectType: ObjectTypeApiName # For object-backed
    
  visibility: enum          # NORMAL | PROMINENT | HIDDEN
```

## Implementation Patterns
```yaml
link_implementations:
  foreign_key:
    cardinality: [ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE]
    configuration: "FK property on 'many' side references PK of 'one' side"
    example:
      Flight.aircraftTailNumber → Aircraft.tailNumber
      
  join_table:
    cardinality: MANY_TO_MANY
    configuration: "Backing dataset with columns mapping to both PKs"
    required_for: "Editable many-to-many links"
    example:
      EmployeeProject:
        employee_id → Employee.employeeId
        project_id → Project.projectId
        
  object_backed:
    cardinality: "Many-to-one on each side"
    use_case: "Relationships with additional metadata"
    configuration: "Create backing ObjectType linked to both sides"
    example:
      Aircraft ←→ FlightManifest(pilot, copilot) ←→ Flight
```

## Code Pattern Identification Rules
```yaml
identification_rules:
  - pattern: "@OneToOne annotation OR single entity reference"
    mapping:
      cardinality: ONE_TO_ONE
      implementation: FOREIGN_KEY
      
  - pattern: "@OneToMany/@ManyToOne OR Collection<Entity>"
    mapping:
      cardinality: ONE_TO_MANY / MANY_TO_ONE
      implementation: FOREIGN_KEY
      
  - pattern: "@ManyToMany OR bidirectional Collection"
    mapping:
      cardinality: MANY_TO_MANY
      implementation: JOIN_TABLE
      
  - pattern: "Association class with attributes"
    mapping:
      implementation: OBJECT_BACKED
      notes: "Create backing ObjectType for relationship metadata"
      
  relationship_semantics:
    Association: "Standard LinkType"
    Aggregation: "LinkType; child can exist independently"
    Composition: "Object-backed link OR cascade rules in Actions"
```

## Anti-Patterns
```yaml
anti_patterns:
  - name: "Cross-Ontology Links"
    problem: "Links between object types in different Ontologies"
    solution: "Not supported; redesign data model"
    
  - name: "FK Without Formal LinkType"
    problem: "Using foreign key properties without defining LinkType"
    solution: "Always create LinkType for navigation capabilities"
    
  - name: "Many-to-Many Without Backing Dataset"
    problem: "Prevents writeback and editing"
    solution: "Always provide backing dataset for M:N links"
```

---

# 4. Interface

## Official Definition
> "An Interface is an Ontology type that describes the shape of an object type and its capabilities. Interfaces provide object type polymorphism, allowing for consistent modeling of and interaction with object types that share a common shape."
> — Palantir Foundry Documentation

## Schema
```yaml
Interface:
  apiName: string           # Programmatic name
  displayName: string       # UI display name
  description: string       # Documentation
  icon: BlueprintIcon       # Visual representation
  
  sharedProperties:
    - propertyApiName: string
      optionality: enum     # REQUIRED | OPTIONAL
      
  linkTypeConstraints:
    - targetType: enum      # INTERFACE | OBJECT_TYPE
      target: ApiName       # Target interface or object type
      cardinality: enum     # ONE | MANY
      required: boolean
      
  extends: list[InterfaceApiName]  # Parent interfaces
```

## Key Differences from ObjectType
```yaml
comparison:
  ObjectType:
    nature: Concrete
    schema: Shared or local properties
    backing: Backed by datasets
    instantiation: Can create objects
    visual: Solid lines
    
  Interface:
    nature: Abstract
    schema: Only shared properties
    backing: Not backed by datasets
    instantiation: Cannot create directly
    visual: Dashed lines
```

## Code Pattern Identification Rules
```yaml
identification_rules:
  - pattern: "Interface definition with method signatures"
    mapping: Ontology Interface with shared properties
    
  - pattern: "Abstract class with common fields"
    mapping: Interface with required/optional shared properties
    
  - pattern: "Multiple classes implementing same contract"
    mapping: Interface implemented by multiple ObjectTypes
    
  - pattern: "Polymorphic queries needed"
    mapping: Interface for cross-type filtering
    
  decision_matrix:
    use_interface_when:
      - "Multiple ObjectTypes share same properties"
      - "Need polymorphic queries across types"
      - "Building reusable marketplace packages"
      - "Future extensibility required"
      
    use_direct_properties_when:
      - "Type-specific properties only"
      - "No cross-type operations needed"
      - "Simple, single-purpose ObjectType"
```

---

# 5. ActionType

## Official Definition
> "An Action type is the definition of a set of changes or edits to objects, property values, and links that a user can take at once. It also includes the side effect behaviors that occur with Action submission."
> — Palantir Foundry Documentation

## Schema
```yaml
ActionType:
  metadata:
    apiName: string         # Unique, immutable after save
    displayName: string     # User-facing name
    description: string     # User-facing description
    rid: string             # Resource ID
    status: enum            # ACTIVE | INACTIVE
    
  parameters:
    - parameterId: string
      displayName: string
      description: string
      baseType: enum        # String | Integer | Decimal | Boolean | Timestamp | Date
      required: boolean
      constraintType: enum  # USER_INPUT | MULTIPLE_CHOICE | OBJECT_REFERENCE
      objectType: string    # For OBJECT_REFERENCE
      allowedValues: list   # For MULTIPLE_CHOICE
      defaultValue: any     # Static or Environment variable
      
  rules:
    ontologyRules:
      - createObject:
          objectType: string
          primaryKey: ValueSource
          properties: map[propertyId, ValueSource]
          
      - modifyObject:
          objectReference: parameterId
          properties: map[propertyId, ValueSource]
          
      - deleteObject:
          objectReference: parameterId
          
      - createLink:
          linkType: string
          sourceObject: parameterId
          targetObject: parameterId
          
      - deleteLink:
          linkType: string
          sourceObject: parameterId
          targetObject: parameterId
          
      - functionRule:          # EXCLUSIVE - no other rules allowed
          functionId: string
          version: string
          autoUpgrade: boolean
          inputs: map[functionParam, actionParam]
          
  submissionCriteria:
    conditions:
      - conditionType: enum   # PARAMETER | CURRENT_USER
        leftValue:
          parameterId: string
          property: string    # For object parameters
        operator: enum        # is | is_not | matches | includes | is_less_than | etc.
        rightValue:
          type: enum          # PARAMETER | SPECIFIC_VALUE | NO_VALUE
          value: any
        failureMessage: string
        
    logicalOperators:
      type: enum              # AND | OR | NOT
      children: list[condition]
      
  sideEffects:
    notifications:
      - recipients: list[userId | groupId | parameterId]
        template: string
        trigger: AFTER_EDITS_APPLIED
        
    webhooks:
      - type: enum            # WRITEBACK | SIDE_EFFECT
        webhookPluginId: string
        parameters: map
        
# ValueSource options
ValueSource:
  - fromParameter: parameterId
  - objectParameterProperty: { parameterId, propertyId }
  - staticValue: any
  - currentUser: userId | groupIds | multipassAttribute
  - currentTime: timestamp
```

## Code Pattern Identification Rules
```yaml
identification_rules:
  - pattern: "Command class with execute() method"
    mapping: ActionType
    rule_type: Based on operation complexity
    
  - pattern: "CRUD operation method"
    mapping:
      Create: "ActionType with createObject rule"
      Read: "Query Function (not Action)"
      Update: "ActionType with modifyObject rule"
      Delete: "ActionType with deleteObject rule"
      
  - pattern: "Transaction with multiple entity changes"
    mapping: "ActionType with functionRule (complex logic)"
    
  - pattern: "Validation before persistence"
    mapping: "submissionCriteria conditions"
    
  - pattern: "Post-save notifications"
    mapping: "sideEffects.notifications"
    
  - pattern: "External system webhook"
    mapping: "sideEffects.webhooks"
```

## Transaction Semantics
```yaml
transaction_rules:
  atomicity: "All edits succeed or all fail"
  rule_ordering: "Later rules override earlier property updates"
  scale_limits: "Default ~10,000 objects per action"
  
  invalid_combinations:
    - "Delete before add/modify"
    - "Modify before create"
    - "Create same object twice"
```

---

# 6. Function

## Official Definition
> "Functions are executable logic units in the Ontology that enable custom computations, data transformations, and Ontology modifications through code."
> — Palantir Foundry Documentation

## Function Types
```yaml
function_types:
  generic_function:
    decorator: "@Function()"
    purpose: "General computation, derived values, data transformation"
    return_type: "Any supported type"
    side_effects: "Allowed (read-only preferred)"
    
  ontology_edit_function:
    decorator: "@OntologyEditFunction()"
    purpose: "Write operations to Ontology"
    return_type: "void | Promise<void>"
    requirement: "Must be configured as Function-backed Action"
    additional_decorator: "@Edits(ObjectType1, ObjectType2)"
    
  query_function:
    decorator: "@Query({ apiName: 'string' })"
    purpose: "Read-only queries exposed via API Gateway"
    constraint: "NO side effects allowed"
    return_type: "Any supported type including ObjectSet"
```

## Schema
```yaml
Function:
  metadata:
    className: string       # TypeScript class name
    methodName: string      # Method name (unique identifier)
    version: semver         # Semantic version
    apiName: string         # For @Query functions
    
  decorator:
    type: enum              # @Function | @OntologyEditFunction | @Query
    edits: list[ObjectType] # For @OntologyEditFunction
    
  signature:
    inputs:
      - name: string
        type: FunctionType
        optional: boolean
        
    returnType: FunctionType | void
    
  supported_types:
    primitives: [String, Integer, Long, Double, Float, Boolean, Timestamp, Date, LocalDate]
    ontology: [ObjectType, ObjectSet<T>, SingleLink<T>, MultiLink<T>]
    collections: [Array<T>, Map<K,V>, Set<T>]
    custom: [DataClass/CustomStruct]
```

## Code Pattern Identification Rules
```yaml
identification_rules:
  - pattern: "Service layer method with state changes"
    mapping: "@OntologyEditFunction()"
    
  - pattern: "Repository query method"
    mapping: "@Query() returning ObjectSet"
    
  - pattern: "Pure computation / data transformation"
    mapping: "@Function()"
    
  - pattern: "API endpoint for data retrieval"
    mapping: "@Query() with apiName"
```

## Code Examples
```typescript
// Query Function (Repository Pattern)
@Query({ apiName: "getEmployeesByDepartment" })
public async findByDepartment(dept: string): Promise<ObjectSet<Employee>> {
    return Objects.search().employee()
        .filter(e => e.department.exactMatch(dept));
}

// Ontology Edit Function (Service Pattern)
@Edits(Employee, Ticket)
@OntologyEditFunction()
public createTicketAndAssign(employee: Employee, ticketId: Integer): void {
    const newTicket = Objects.create().ticket(ticketId);
    newTicket.dueDate = LocalDate.now().plusDays(7);
    employee.assignedTickets.add(newTicket);
}
```

---

# 7. ObjectSet

## Official Definition
> "An object set represents an unordered collection of objects of a single type. You can use the functions APIs to filter object sets, perform Search Arounds to other object types based on defined link types, and compute aggregated values or retrieve the concrete objects."
> — Palantir Foundry Documentation

## Operators Reference
```yaml
filter_operators:
  all_types:
    - exactMatch(value)
    - hasProperty()         # null check
    
  string:
    - phrase(text)          # Token matching in order
    - phrasePrefix(text)    # Phrase + prefix on last token
    - matchAnyToken(text)   # Contains any token
    - matchAllTokens(text)  # Contains all tokens
    - fuzzyMatchAnyToken(text, maxEdits)
    - fuzzyMatchAllTokens(text, maxEdits)
    
  numeric_date:
    - range().lt(value)
    - range().lte(value)
    - range().gt(value)
    - range().gte(value)
    
  boolean:
    - isTrue()
    - isFalse()
    
  geo:
    - withinDistanceOf(point, distance)
    - withinPolygon(polygon)
    - withinBoundingBox(box)
    
  array:
    - contains(value)
    
  link:
    - isPresent()

set_operations:
  - union(otherSet)         # Objects in any set
  - intersect(otherSet)     # Objects in all sets
  - subtract(otherSet)      # Remove objects

combining_filters:
  - Filters.and(f1, f2)     # All must pass
  - Filters.or(f1, f2)      # Any passes
  - Filters.not(f)          # Negate

ordering:
  - orderBy(o => o.prop.asc())
  - orderBy(o => o.prop.desc())
  - orderByRelevance()

retrieval:
  - all()                   # Sync load all (max 100K)
  - allAsync()              # Async load all
  - take(n)                 # Load n after ordering
  - takeAsync(n)            # Async variant

traversal:
  - searchAroundLinkedType()  # Max 3 levels
  
aggregations:
  - count()
  - average(prop)
  - max(prop)
  - min(prop)
  - sum(prop)
  - cardinality(prop)
  
grouping:
  - groupBy(o => o.dateProp.byDays())
  - groupBy(o => o.numProp.byRanges({min, max}))
  - segmentBy(o => o.stringProp.topValues())
```

## Code Pattern Identification Rules
```yaml
sql_to_objectset_mapping:
  "SELECT * FROM table WHERE": "Objects.search().type().filter()"
  "JOIN table2 ON": ".searchAroundLinkedType()"
  "UNION/INTERSECT/EXCEPT": ".union()/.intersect()/.subtract()"
  "ORDER BY col ASC": ".orderBy(o => o.col.asc())"
  "LIMIT n": ".take(n)"
  "GROUP BY": ".groupBy()"
  "COUNT(*)": ".count()"
  
repository_pattern_mapping:
  "findById(id)": ".filter(o => o.pk.exactMatch(id))"
  "findAll()": ".all()"
  "findByProperty(value)": ".filter(o => o.prop.exactMatch(value))"
  "findByRange(min, max)": ".filter(o => o.prop.range().gte(min).lte(max))"
  "Specification Pattern": ".filter(o => Filters.and(...))"
```

## Limits
```yaml
limits:
  max_objects_all: 100000
  timeout_threshold: 10000
  search_around_depth: 3
  osv2_max_result: 10000000
  aggregation_buckets: 10000
```

---

# 8. Automation (Automate)

## Official Definition
> "Automate is an application for setting up business automation. The Automate application allows users to define conditions and effects. Conditions are checked continuously, and effects are executed automatically when the specified conditions were met."
> — Palantir Foundry Documentation

## Schema
```yaml
Automation:
  metadata:
    name: string
    description: string
    enabled: boolean
    expiry: timestamp
    
  condition:
    type: enum              # TIME | OBJECT_SET
    
    time_condition:
      mode: enum            # HOURLY | DAILY | WEEKLY | MONTHLY | CRON
      cron: string          # 5-field cron expression
      timezone: string
      
    objectset_condition:
      type: enum
      # OBJECTS_ADDED | OBJECTS_REMOVED | OBJECTS_MODIFIED
      # METRIC_CHANGED | THRESHOLD_CROSSED | OBJECTS_EXIST
      objectSet: ObjectSetDefinition | FunctionReference
      
  effects:
    - type: enum            # ACTION | NOTIFICATION | FALLBACK
      
      action_effect:
        actionType: ActionTypeApiName
        parameterMapping: map[actionParam, effectInput]
        executionMode: enum # ONCE_ALL | ONCE_BATCH | ONCE_EACH_GROUP
        retryPolicy:
          type: enum        # CONSTANT | EXPONENTIAL
          maxRetries: integer
          initialDelay: duration
          
      notification_effect:
        type: enum          # PLATFORM | EMAIL
        recipients: list
        template: string
        attachments: list[NotepadRef]
        
      fallback_effect:
        # Executed when primary effects fail
        actions: list[ActionEffect]
        
  execution_settings:
    batchSize: integer
    parallelism: integer
    evaluationLatency: enum # LIVE | SCHEDULED
```

## Code Pattern Identification Rules
```yaml
identification_rules:
  - pattern: "@Scheduled(cron='...')"
    mapping:
      condition_type: TIME
      cron: "extracted from annotation"
      
  - pattern: "@EventListener / onEntityCreate()"
    mapping:
      condition_type: OBJECT_SET
      trigger: OBJECTS_ADDED
      
  - pattern: "onEntityUpdate()"
    mapping:
      condition_type: OBJECT_SET
      trigger: OBJECTS_MODIFIED
      
  - pattern: "onEntityDelete()"
    mapping:
      condition_type: OBJECT_SET
      trigger: OBJECTS_REMOVED
      
  - pattern: "Webhook handler endpoint"
    mapping: "Action with webhook side effect"
    
  - pattern: "Message queue consumer"
    mapping: "Object set condition + Action effect"
    
  - pattern: "Batch processor"
    mapping:
      condition_type: OBJECT_SET
      trigger: OBJECTS_EXIST
      execution_mode: ONCE_BATCH
```

---

# 9. Rules Engine

## Official Definition
> "Foundry Rules (formerly Taurus) enables users to actively manage complex business logic in Foundry with a point-and-click, low-code interface. Users can create rules and apply them to datasets, objects, and time series for alert generation, data categorization, and task generation."
> — Palantir Foundry Documentation

## Schema
```yaml
FoundryRule:
  inputs:
    - type: enum            # DATASET | OBJECT
      source: rid | ObjectTypeApiName
      
  logic_blocks:
    - filter_board:
        conditions: list[FilterCondition]
        
    - aggregation_board:
        groupBy: list[column]
        aggregations: map[outputColumn, aggregateFunction]
        
    - join_board:
        joinType: enum      # INNER | LEFT | RIGHT | FULL
        joinDataset: rid
        joinConditions: list
        
    - expression_board:
        expressions: map[outputColumn, expression]
        
    - window_board:
        partitionBy: list[column]
        orderBy: list[column]
        windowFunction: string
        
    - select_columns_board:
        columns: list[column]
        
    - union_board:
        datasets: list[rid]
        
  output:
    dataset: rid
    schema: list[ColumnDefinition]
```

## Action Type Rules (10 Types)
```yaml
action_rules:
  object_operations:
    - createObject
    - modifyObject
    - createOrModifyObject
    - deleteObject
    
  link_operations:
    - createLink           # Many-to-many only
    - deleteLink
    
  function_rule:           # EXCLUSIVE - no other rules
    - functionRule
    
  interface_operations:
    - createObjectOfInterface
    - modifyObjectOfInterface
    - deleteObjectOfInterface
```

## Code Pattern Identification Rules
```yaml
code_pattern_mapping:
  "if/else conditional": "Filter board + Expression board"
  "GROUP BY aggregation": "Aggregation board"
  "JOIN operations": "Join board"
  "Window functions": "Window board"
  "UNION operations": "Union board"
  "Business validation": "Submission criteria on Actions"
  "Rule-based alerts": "Foundry Rules → Alert output"
```

---

# 10. Writeback

## Official Definition
> "Writeback is the mechanism for synchronizing Ontology changes (user edits via Actions) back to writeback datasets and external systems via Webhooks, Exports, or External Functions."
> — Palantir Foundry Documentation

## Schema
```yaml
Writeback:
  internal:
    writeback_dataset:
      description: "Stores user-modified version of source data"
      source: "Unchanged"
      destination: "Merged dataset with edits"
      conflict_resolution: "Timestamp-based; later edit wins"
      
  external:
    webhooks:
      writeback_webhook:
        execution_order: BEFORE_OTHER_RULES
        failure_handling: "Blocks all changes; error shown to user"
        output_parameters: "Available for subsequent rules"
        limit: "ONE per Action"
        
      side_effect_webhook:
        execution_order: AFTER_OTHER_RULES
        failure_handling: "Best-effort; may fail silently"
        limit: "Multiple allowed"
        
    exports:
      file_export:
        targets: [S3, GCS, Azure_Blob]
        mode: BATCH
        
      streaming_export:
        targets: [Kafka, Kinesis, PubSub]
        mode: REALTIME
        
      table_export:
        targets: [JDBC_databases]
        modes: [TRUNCATE_INSERT, APPEND, UPSERT]
```

## Code Pattern Identification Rules
```yaml
cqrs_mapping:
  "Event Store": "Funnel queue + writeback datasets"
  "Command Side (Write)": "Actions with Ontology Rules"
  "Event Publication": "Side Effect Webhooks OR Streaming Exports"
  "Read Model Update": "Object indexing via Funnel pipelines"
  "Saga/Compensation": "Writeback Webhook (fail-safe external call first)"
  "Event Replay": "Dataset versioning + Funnel replacement pipelines"
```

---

# 11. Versioning & Governance

## Schema Evolution
```yaml
schema_changes:
  breaking_changes:
    - "Changing input datasources"
    - "Changing primary key"
    - "Changing property data type"
    - "Changing property ID (with existing edits)"
    - "Deleting property (with existing edits)"
    - "Changing struct field data type"
    
  non_breaking_changes:
    - "Display name changes"
    - "Title key changes"
    - "Render hints changes"
    - "Visibility changes"
    - "Deleting never-edited properties"
    
  supported_migrations:
    - drop_property_edits
    - drop_struct_field_edits
    - drop_all_edits
    - move_edits
    - cast_property_type
    - revert_migration
    
  type_casts:
    String: [Integer, Long, Double, Boolean, Date, Timestamp, Geopoint, Geoshape]
    Integer: [Long, Double, String]
    Long: [Integer, Double, String]
    Double: [Integer, Long, String]
    
  limits:
    max_migrations_per_batch: 500
```

## Proposal Workflow
```yaml
ontology_proposals:
  workflow:
    1_branch_creation:
      - "Derived from main version"
      - "Isolated experimentation"
      
    2_proposal:
      - "Contains reviews and metadata"
      - "Each resource = separate Task"
      
    3_rebase:
      - "Manual incorporation of Main changes"
      - "Conflict resolution"
      
    4_review:
      - "Reviewer assignment"
      - "Individual task approval"
      
    5_merge:
      - "Integration into Main"
```

## Code Pattern Identification Rules
```yaml
database_migration_mapping:
  "Schema migration files": "Ontology schema changes + migrations"
  "Rolling migrations": "OSv2 migration framework"
  "Blue-green deployment": "Ontology branches + proposals"
  "Version rollback": "Revert migration"
  "Breaking change detection": "Automatic in Ontology Manager"
  "Data transformation scripts": "Cast/Move migrations"
```

---

# 12. Complete Decision Matrix

## When to Create Each Component

```yaml
decision_matrix:
  ObjectType:
    create_when:
      - "Entity with unique identifier"
      - "Aggregate Root in DDD"
      - "Database table representation"
      - "Domain object with business identity"
    avoid_when:
      - "Value object without identity"
      - "Enum or lookup value"
      
  PropertyType:
    considerations:
      - "Use String for Long IDs (JS precision)"
      - "Use Double instead of Decimal (OSv2)"
      - "Struct for complex objects ≤10 fields"
      - "Separate ObjectType for shared complex objects"
      
  LinkType:
    create_when:
      - "Entity references another entity"
      - "Navigation between objects needed"
      - "Relationship has semantic meaning"
    implementation_choice:
      ONE_TO_ONE: "Foreign key on either side"
      ONE_TO_MANY: "Foreign key on 'many' side"
      MANY_TO_MANY: "Join table required"
      WITH_METADATA: "Object-backed link"
      
  Interface:
    create_when:
      - "Multiple ObjectTypes share properties"
      - "Polymorphic queries needed"
      - "Building reusable packages"
      
  ActionType:
    create_when:
      - "User needs to modify Ontology data"
      - "Atomic business operation"
      - "Audit trail required"
      - "Pre-submission validation needed"
    use_function_rule_when:
      - "Complex business logic"
      - "Multiple object types involved"
      - "Conditional branching required"
      
  Function:
    query_function:
      - "Read-only data retrieval"
      - "Expose via API Gateway"
      - "Complex filtering/aggregation"
    edit_function:
      - "Complex write logic"
      - "Multiple linked object changes"
      - "Computed values during mutation"
      
  ObjectSet:
    use_for:
      - "All read queries"
      - "Filtering and searching"
      - "Aggregations and grouping"
      - "Link traversal"
      
  Automation:
    create_when:
      - "Scheduled tasks needed"
      - "React to object changes"
      - "Event-driven processing"
      
  Writeback:
    configure_when:
      - "External system integration"
      - "Audit in external database"
      - "Real-time sync needed"
```

---

# Appendix: Quick Reference Tables

## Type Mapping: Code → Ontology
```yaml
java_to_ontology:
  String: String
  Integer/int: Integer
  Long/long: String  # Avoid precision loss
  Double/double: Double
  Boolean/boolean: Boolean
  LocalDate: Date
  Instant: Timestamp
  BigDecimal: String
  UUID: String
  List<T>: Array<T>
  enum: String
  
typescript_to_ontology:
  string: String
  number: Integer | Double  # Based on usage
  boolean: Boolean
  Date: Timestamp
  bigint: String  # Avoid precision loss
  T[]: Array<T>
```

## SDK Type Support Matrix
```yaml
sdk_support:
  TypeScript_OSDK: [String, Integer, Long, Double, Float, Boolean, Date, Timestamp, GeoPoint, Geoshape, Attachment, Array, Struct, TimeSeries, Media]
  Python_OSDK: [String, Integer, Long, Double, Float, Boolean, Date, Timestamp, GeoPoint, Geoshape, Attachment, Array, TimeSeries]
  Java_OSDK: [String, Integer, Long, Double, Float, Boolean, Date, Timestamp, GeoPoint, Geoshape, Attachment, Array, Media]
  
  not_supported_any:
    - Cipher
    - Marking
    - Vector
```

---

**Document Version:** 1.0  
**Based on:** Palantir Foundry Documentation (January 2026)  
**Purpose:** Machine-readable reference for AI-assisted Ontology-Driven Architecture refactoring