# Palantir Ontology: LinkType & Interface Reference

Palantir's Ontology relationship and abstraction components enable sophisticated data modeling through **LinkTypes** (schema definitions for relationships between ObjectTypes) and **Interfaces** (abstract shapes implemented by multiple ObjectTypes). This reference provides machine-readable specifications for both components, enabling precise codebase analysis and ontology design.

**LinkType** defines relationships analogous to database joins—supporting four cardinalities (ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY) backed by foreign keys or join tables. **Interface** provides object-type polymorphism through shared properties and link type constraints, supporting multiple inheritance.

---

## Component 1: LinkType specification

A LinkType is the schema definition of a relationship between two ObjectTypes; a Link is a single instance of that relationship. This maps directly to relational database concepts where LinkType defines the join logic and Link represents joined rows.

```yaml
# PALANTIR ONTOLOGY LINKTYPE REFERENCE
# Machine-readable specification for Claude-Opus-4.5
# Version: 2026-02-03
# Source: palantir.com/docs/foundry/object-link-types

linktype:
  official_definition:
    source_url: "https://www.palantir.com/docs/foundry/object-link-types/link-types-overview"
    definition: |
      A link type is the schema definition of a relationship between two 
      object types. A link refers to a single instance of that relationship 
      between two objects in the same Ontology.
    
  semantic_definition:
    analogies:
      - database_concept: "JOIN definition between tables"
        link_concept: "A row joined with fields from another table"
      - programming_concept: "Foreign key relationship in ORM"
      - graph_concept: "Edge type in a property graph"
    
    relationship_to_link:
      linktype: "Schema (blueprint)"
      link: "Instance (data)"
      example:
        linktype_name: "Employee → Employer"
        link_instance: "Melissa Chang → Acme, Inc."

  json_schema:
    $schema: "https://json-schema.org/draft/2020-12/schema"
    $id: "palantir-ontology-linktype-v1"
    title: "Palantir Ontology LinkType"
    type: "object"
    required:
      - "apiName"
      - "sourceObjectType"
      - "targetObjectType"
      - "cardinality"
      - "backingMechanism"
    properties:
      apiName:
        type: "string"
        pattern: "^[a-z][a-zA-Z0-9]*$"
        minLength: 1
        maxLength: 100
        description: "Programmatic name for code references"
      displayName:
        type: "string"
        maxLength: 256
      description:
        type: "string"
      sourceObjectType:
        type: "string"
        description: "API name of source ObjectType"
      targetObjectType:
        type: "string"
        description: "API name of target ObjectType"
      sourceApiName:
        type: "string"
        pattern: "^[a-z][a-zA-Z0-9]*$"
        description: "API name from source side for traversal"
      targetApiName:
        type: "string"
        pattern: "^[a-z][a-zA-Z0-9]*$"
        description: "API name from target side for traversal"
      cardinality:
        type: "string"
        enum:
          - "ONE_TO_ONE"
          - "ONE_TO_MANY"
          - "MANY_TO_ONE"
          - "MANY_TO_MANY"
      backingMechanism:
        oneOf:
          - $ref: "#/$defs/foreignKeyBacking"
          - $ref: "#/$defs/joinTableBacking"
          - $ref: "#/$defs/objectBackedBacking"
    $defs:
      foreignKeyBacking:
        type: "object"
        required: ["type", "foreignKeyProperty", "primaryKeyObjectType"]
        properties:
          type:
            const: "FOREIGN_KEY"
          foreignKeyObjectType:
            type: "string"
          foreignKeyProperty:
            type: "string"
          primaryKeyObjectType:
            type: "string"
      joinTableBacking:
        type: "object"
        required: ["type", "datasetRid", "sourceColumn", "targetColumn"]
        properties:
          type:
            const: "JOIN_TABLE"
          datasetRid:
            type: "string"
          sourceColumn:
            type: "string"
          targetColumn:
            type: "string"
      objectBackedBacking:
        type: "object"
        required: ["type", "backingObjectType", "sourceLink", "targetLink"]
        properties:
          type:
            const: "OBJECT_BACKED"
          backingObjectType:
            type: "string"
          sourceLink:
            type: "string"
          targetLink:
            type: "string"
```

### Cardinality types with backing mechanisms

The **ONE_TO_ONE** cardinality indicates one object of Type A should link to exactly one object of Type B. The foreign key can reside on either side, though this constraint is **not enforced** at the platform level—it serves as an indicator of intended relationship semantics.

**ONE_TO_MANY** means one object links to many targets. The foreign key resides on the "many" side (target). For example, Aircraft (one) → Flights (many) uses `flight_tail_number` on Flight referencing Aircraft's `tail_number`.

**MANY_TO_ONE** is the inverse perspective where many objects link to one target. The foreign key resides on the source side. Both ONE_TO_MANY and MANY_TO_ONE use foreign key property backing.

**MANY_TO_MANY** requires a join table dataset containing primary key pairs from both ObjectTypes. This is the only cardinality supporting direct link writeback through Create/Delete Link action rules.

```yaml
cardinality_specifications:

  ONE_TO_ONE:
    definition: "One object of Type A links to exactly one object of Type B"
    enforcement: "NOT ENFORCED - serves as semantic indicator only"
    fk_location: "Either side (configurable)"
    backing_mechanism: "FOREIGN_KEY"
    use_cases:
      - "Aircraft → AssignedFlight (single assignment)"
      - "Employee → EmployeeProfile"
      - "Country → CapitalCity"
    
  ONE_TO_MANY:
    definition: "One object of Type A can link to many objects of Type B"
    fk_location: "TARGET side (the 'many' side holds the FK)"
    backing_mechanism: "FOREIGN_KEY"
    example:
      source: "Aircraft"
      target: "Flight"
      foreign_key_on: "Flight.flight_tail_number"
      references: "Aircraft.tail_number"
    use_cases:
      - "Department → Employees"
      - "Author → Books"
      - "Concept → ExampleProblems"
    
  MANY_TO_ONE:
    definition: "Many objects of Type A can link to one object of Type B"
    fk_location: "SOURCE side (the 'many' side holds the FK)"
    backing_mechanism: "FOREIGN_KEY"
    relationship_to_one_to_many: "Inverse perspective of same relationship"
    use_cases:
      - "Employees → Department"
      - "Orders → Customer"
      - "ExampleProblems → Concept"
    
  MANY_TO_MANY:
    definition: "Objects of Type A can link to many of Type B and vice versa"
    fk_location: "NEITHER - uses join table"
    backing_mechanism: "JOIN_TABLE (mandatory) or OBJECT_BACKED"
    join_table_requirements:
      required_columns:
        - "Column matching source ObjectType primary key"
        - "Column matching target ObjectType primary key"
      constraints:
        - "Each column can only map to ONE primary key"
        - "Can auto-generate via 'Generate join table' option"
    writeback_support: "FULL - supports Create/Delete Link actions"
    use_cases:
      - "Students ↔ Courses"
      - "Tags ↔ Documents"
      - "ConceptPrerequisites (self-referential)"

  cardinality_change_rules:
    can_change_after_creation: true
    consequences:
      - "Triggers Object Storage V1 unregister/reregister"
      - "Links UNAVAILABLE during reindex"
      - "Writeback history DELETED for writeback-enabled links"
      - "Future writeback dataset builds will FAIL"
    high_risk_changes:
      - "Changing cardinality"
      - "Changing foreign key property"
      - "Changing M:N backing datasource"
      - "Deleting link type"
```

### Object-backed links for relationship properties

When links require additional metadata (relationship start date, weight, context), use **Object-backed Links**. This creates an intermediary ObjectType that holds link properties while maintaining M:1 relationships to both sides.

```yaml
object_backed_links:
  definition: |
    Object-backed link types expand on many-to-one cardinality, providing 
    first-class support for object types as a link type storage solution. 
    They allow inclusion of additional metadata on the link.
  
  when_to_use:
    - "Link needs properties (dates, scores, status)"
    - "Relationship has its own identity"
    - "Need restricted views on links"
    - "Audit trail required for link changes"
  
  architecture_pattern: |
    ObjectA ←[M:1]→ LinkObject ←[M:1]→ ObjectB
    
  example:
    name: "Flight Assignment"
    pattern: "Aircraft ← FlightManifest → Flight"
    link_object_properties:
      - "pilot_id"
      - "first_mate_id"
      - "assignment_date"
      - "assignment_status"
  
  creation_steps:
    1: "Create ObjectTypes on both sides"
    2: "Create backing ObjectType with link properties"
    3: "Create M:1 LinkType from backing object to source"
    4: "Create M:1 LinkType from backing object to target"
    5: "In Ontology Manager, configure as object-backed"
```

### Link traversal and Search Around

**Search Around** enables graph traversal through linked objects at the ObjectSet level. Bidirectional traversal is automatic when both sourceApiName and targetApiName are configured.

```yaml
link_traversal:
  search_around:
    definition: |
      Search Around methods traverse links based on object type, 
      returning ObjectSets that can be further filtered.
    
    code_example: |
      const passengers = Objects.search()
        .flights()
        .filter(f => f.departureAirportCode.exactMatch(code))
        .searchAroundPassengers();
    
    performance_limits:
      max_search_around_operations: 3
      scale_threshold: "50,000 objects"
      recommendation: "Use join materializations above threshold"
    
  api_names:
    sourceApiName:
      purpose: "Enables traversal FROM source TO target"
      usage: "sourceObject.{targetApiName}.all()"
    targetApiName:
      purpose: "Enables traversal FROM target TO source"
      usage: "targetObject.{sourceApiName}.get()"
    
  bidirectional_traversal:
    automatic: true
    requirement: "Both API names must be configured"
    link_types_generated:
      SingleLink: "For 'one' side - use .get() or .getAsync()"
      MultiLink: "For 'many' side - use .all() or .allAsync()"
```

### LinkType decision tree

```yaml
linktype_decision_tree:
  entry_point: "Need to model relationship between entities?"
  
  branches:
    cardinality_selection:
      question: "How many objects on each side?"
      paths:
        one_to_one:
          condition: "Exactly one on both sides"
          backing: "FOREIGN_KEY"
          fk_location: "Either side"
        one_to_many:
          condition: "One source, many targets"
          backing: "FOREIGN_KEY"
          fk_location: "Target side"
        many_to_one:
          condition: "Many sources, one target"
          backing: "FOREIGN_KEY"
          fk_location: "Source side"
        many_to_many:
          condition: "Many on both sides"
          next_question: "Does link need properties?"
          
    link_properties_needed:
      question: "Does the relationship itself need attributes?"
      paths:
        yes:
          solution: "OBJECT_BACKED link"
          create: "Intermediary ObjectType with M:1 links to both sides"
        no:
          solution: "JOIN_TABLE backing"
          create: "Dataset with primary key columns from both types"
    
    self_referential:
      question: "Same ObjectType on both sides?"
      paths:
        yes:
          cardinality: "MANY_TO_MANY"
          api_names: "Use distinct meaningful names (prerequisites/enables)"
          example: "Concept → Concept via ConceptPrerequisite"
```

### LinkType validation rules

```yaml
linktype_validation_rules:
  - rule_id: "LT001"
    name: "Valid API name format"
    condition: "apiName matches ^[a-z][a-zA-Z0-9]*$ and length 1-100"
    severity: "ERROR"
    
  - rule_id: "LT002"
    name: "Unique API names per ObjectType"
    condition: "No duplicate sourceApiName or targetApiName for same ObjectType"
    severity: "ERROR"
    
  - rule_id: "LT003"
    name: "FK backing requires valid FK property"
    condition: "If FOREIGN_KEY backing, foreignKeyProperty must exist on specified ObjectType"
    severity: "ERROR"
    
  - rule_id: "LT004"
    name: "M:N requires join table or object backing"
    condition: "If cardinality=MANY_TO_MANY, backing must be JOIN_TABLE or OBJECT_BACKED"
    severity: "ERROR"
    
  - rule_id: "LT005"
    name: "Join table columns map to primary keys"
    condition: "sourceColumn and targetColumn must match PKs of respective ObjectTypes"
    severity: "ERROR"
    
  - rule_id: "LT006"
    name: "Bidirectional names defined"
    condition: "Both sourceApiName and targetApiName should be defined for full traversal"
    severity: "WARNING"
    
  - rule_id: "LT007"
    name: "Meaningful API names"
    condition: "Avoid generic names like 'Employee2' or 'object'"
    severity: "WARNING"
    
  - rule_id: "LT008"
    name: "Plural names for many-side"
    condition: "API name on 'many' side should be plural (employees not employee)"
    severity: "WARNING"
```

### LinkType anti-patterns

```yaml
linktype_antipatterns:
  - id: "LT_ANTI_001"
    name: "Isolated Objects"
    description: "ObjectTypes with no configured links"
    problem: "Reduces ontology utility; objects cannot be discovered via traversal"
    solution: "Configure all semantically valid relationships"
    detection: "ObjectType has zero LinkTypes referencing it"
    
  - id: "LT_ANTI_002"
    name: "Spiderweb Ontology"
    description: "Excessive links creating overly complex graph"
    problem: "Query performance degradation; cognitive overload"
    solution: "Link only operationally necessary relationships"
    detection: "ObjectType has >10 LinkTypes; circular dependencies"
    
  - id: "LT_ANTI_003"
    name: "Generic Link Names"
    description: "Non-descriptive API names like 'link1', 'Employee2'"
    problem: "Code readability; navigation confusion"
    solution: "Use semantic names: 'manager', 'directReports', 'prerequisiteConcepts'"
    detection: "API name contains numbers or generic terms"
    
  - id: "LT_ANTI_004"
    name: "Missing Bidirectional Names"
    description: "Only one API name defined for a relationship"
    problem: "Cannot traverse from one direction"
    solution: "Define both sourceApiName and targetApiName"
    detection: "LinkType missing one of the API names"
    
  - id: "LT_ANTI_005"
    name: "Singular Names on Many Side"
    description: "Using 'employee' instead of 'employees' for many-side API"
    problem: "Code confusion: employee.subordinate.all() vs employee.subordinates.all()"
    solution: "Use plural form for many-side API names"
    detection: "API name on MANY cardinality side is singular"
```

---

## Component 2: Interface specification

An Interface is an Ontology type describing the shape of ObjectTypes and their capabilities. Unlike traditional OOP interfaces that define method signatures, Palantir Interfaces define **shared properties** and **link type constraints** for data shape abstraction.

```yaml
# PALANTIR ONTOLOGY INTERFACE REFERENCE
# Machine-readable specification for Claude-Opus-4.5
# Version: 2026-02-03
# Source: palantir.com/docs/foundry/interfaces

interface:
  official_definition:
    source_url: "https://www.palantir.com/docs/foundry/interfaces/interface-overview"
    definition: |
      An interface is an Ontology type that describes the shape of an 
      object type and its capabilities. Interfaces allow for consistent 
      modeling of and interaction with object types that share a common shape.
    
  semantic_definition:
    analogies:
      - programming_concept: "Interface in OOP (but for data shape, not methods)"
      - database_concept: "View that unions multiple tables with common columns"
      - api_concept: "Polymorphic API layer over multiple entity types"
    
    key_differences_from_oop:
      oop_interface: "Defines method signatures"
      palantir_interface: "Defines shared properties and link type constraints"
      oop_focus: "Behavior abstraction"
      palantir_focus: "Data shape abstraction and API polymorphism"

  json_schema:
    $schema: "https://json-schema.org/draft/2020-12/schema"
    $id: "palantir-ontology-interface-v1"
    title: "Palantir Ontology Interface"
    type: "object"
    required:
      - "apiName"
      - "sharedProperties"
    properties:
      apiName:
        type: "string"
        pattern: "^[a-z][a-zA-Z0-9]*$"
        minLength: 1
        maxLength: 100
      displayName:
        type: "string"
        maxLength: 256
      description:
        type: "string"
      icon:
        type: "string"
      extendsInterfaces:
        type: "array"
        items:
          type: "string"
        description: "API names of parent interfaces"
      sharedProperties:
        type: "array"
        items:
          $ref: "#/$defs/sharedProperty"
      linkTypeConstraints:
        type: "array"
        items:
          $ref: "#/$defs/linkTypeConstraint"
    $defs:
      sharedProperty:
        type: "object"
        required: ["apiName", "dataType", "required"]
        properties:
          apiName:
            type: "string"
            pattern: "^[a-z][a-zA-Z0-9]*$"
          displayName:
            type: "string"
          dataType:
            type: "string"
            enum:
              - "STRING"
              - "INTEGER"
              - "LONG"
              - "DOUBLE"
              - "BOOLEAN"
              - "DATE"
              - "TIMESTAMP"
              - "ARRAY"
              - "STRUCT"
          required:
            type: "boolean"
          description:
            type: "string"
      linkTypeConstraint:
        type: "object"
        required: ["apiName", "targetType", "cardinality"]
        properties:
          apiName:
            type: "string"
            pattern: "^[a-z][a-zA-Z0-9]*$"
          displayName:
            type: "string"
          description:
            type: "string"
          targetType:
            oneOf:
              - type: "object"
                properties:
                  type:
                    const: "INTERFACE"
                  interfaceApiName:
                    type: "string"
              - type: "object"
                properties:
                  type:
                    const: "OBJECT_TYPE"
                  objectTypeApiName:
                    type: "string"
          cardinality:
            type: "string"
            enum: ["ONE", "MANY"]
          required:
            type: "boolean"
```

### Interface vs ObjectType comparison

Interfaces are **abstract** with schemas defined only by shared properties, no dataset backing, and cannot be instantiated directly. ObjectTypes are **concrete** with schemas defined by shared or local properties, backed by datasets, and can be instantiated as objects. Interfaces appear with dashed-line icons in UI to distinguish them.

```yaml
interface_vs_objecttype:
  objecttype:
    nature: "Concrete"
    schema_source: "Shared OR local properties"
    data_backing: "Backed by datasets"
    instantiation: "Can be instantiated as objects"
    visual_indicator: "Solid line icons"
    
  interface:
    nature: "Abstract"
    schema_source: "ONLY shared properties"
    data_backing: "NOT backed by datasets"
    instantiation: "Must instantiate as specific ObjectType"
    visual_indicator: "Dashed line icons"
```

### Inheritance model supporting multiple extension

Interfaces can extend **any number** of other interfaces, inheriting all shared properties and link type constraints. This enables composition of capability interfaces into abstract object interfaces.

```yaml
interface_inheritance:
  supports_extension: true
  multiple_inheritance: true
  
  inherited_elements:
    - "All shared properties from parent interface(s)"
    - "All link type constraints from parent interface(s)"
  
  extension_steps:
    1: "Navigate to interface in Ontology Manager"
    2: "Select Extension from left panel"
    3: "Click Add extension"
    4: "Select interface(s) to extend"
    5: "Review inherited properties and constraints"
    6: "Save"
  
  removal_consequences:
    - "Removes all inherited shared properties"
    - "Removes all inherited link type constraints"
    - "Disassociates extending interface from base"
  
  example:
    child: "EducationalContent"
    parents: ["Identifiable", "Timestamped", "Searchable"]
    inherited_properties:
      from_Identifiable: ["contentId"]
      from_Timestamped: ["createdAt", "updatedAt"]
      from_Searchable: ["searchKeywords", "tags"]
```

### Implementation patterns with property mapping

ObjectTypes implement Interfaces by mapping their local properties to interface shared properties. Auto-mapping occurs when property names match; manual mapping handles mismatches. Multiple interface implementation is fully supported.

```yaml
interface_implementation:
  multiple_implementation: true
  
  requirements:
    - "Object type must contain required shared properties OR declare mapping"
    - "Object type must possess links satisfying required link type constraints"
  
  property_mapping:
    auto_mapping: "Occurs when shared property exists on both interface and object type"
    manual_mapping: "Required when property names differ"
    api_context:
      as_concrete_type: "Use local property API names"
      as_interface_type: "Use shared property API names"
  
  implementation_methods:
    from_object_type:
      steps:
        1: "Navigate to ObjectType in Ontology Manager"
        2: "Open Interfaces tab"
        3: "Select + Implement new interface"
        4: "Choose interface and map properties"
    from_interface:
      steps:
        1: "Navigate to Interface overview"
        2: "Select + New in Implementations section"
        3: "Choose implementing ObjectType"
    from_pipeline:
      note: "Does not support link type constraint mapping"
  
  required_vs_optional:
    required_properties: "MUST have property OR provide mapping"
    optional_properties: "Mapping may be skipped"
    use_case_for_optional: "Iterating on interfaces; Marketplace packages"
```

### Link type constraints on interfaces

Interfaces can define link type constraints that all implementing ObjectTypes must satisfy. Constraints can target either specific ObjectTypes (concrete) or other Interfaces (polymorphic).

```yaml
interface_link_constraints:
  definition: |
    An interface link type constraint defines an object-to-object 
    relationship common across all object types implementing an interface.
  
  parameters:
    link_target_type:
      options:
        - "INTERFACE - for polymorphic relationships"
        - "OBJECT_TYPE - for concrete relationships"
    target:
      description: "Specific interface or object type to link to"
    cardinality:
      ONE: "Each implementing object links to one target"
      MANY: "Each implementing object links to multiple targets"
    required:
      description: "Whether implementing objects must have this link"
  
  target_type_guidance:
    use_interface_target:
      - "Both sides of relationship are abstract"
      - "Multiple object types could be on either end"
      - "Maximum flexibility needed"
      example: "Facility → Alert (any facility type to any alert type)"
    use_objecttype_target:
      - "One side must be concrete"
      - "Enforce specific relationship"
      example: "Facility → Airlines (all facilities link to Airlines specifically)"
```

### Platform support matrix (current as of February 2026)

```yaml
interface_platform_support:
  full_support:
    - platform: "Ontology Manager"
      capabilities: ["Define", "Edit", "Implement interfaces"]
    - platform: "Marketplace"
      capabilities: ["Package", "Install interfaces"]
    - platform: "Functions (TypeScript v2)"
      capabilities: ["Full interface usage in code"]
  
  partial_support:
    - platform: "Actions"
      supported: ["Create/modify/delete objects via interfaces"]
      not_supported: ["Reference interface link type constraints directly"]
    - platform: "Object Set Service"
      supported: ["Search and sort by interfaces"]
      in_development: ["Aggregating by interfaces", "Interface link types"]
    - platform: "OSDK TypeScript"
      supported: ["Use as API layer"]
      not_supported: ["Interface link types", "Aggregations"]
    - platform: "OSDK Java"
      status: "In development"
    - platform: "OSDK Python"
      status: "In development"
  
  not_supported:
    - "Workshop"
    - "Functions (TypeScript v1)"
```

### Interface decision tree

```yaml
interface_decision_tree:
  entry_point: "Need to model shared shape/behavior across types?"
  
  branches:
    shared_properties:
      question: "Do multiple ObjectTypes share the same properties?"
      yes: "Define SharedProperties on Interface"
      no: "Interface may not be needed"
      
    polymorphic_operations:
      question: "Need to perform same operations on different types?"
      yes: "Interface enables polymorphic Actions and Functions"
      example: "Search all EducationalContent regardless of concrete type"
      
    link_abstraction:
      question: "Should relationships be defined at abstract level?"
      paths:
        concrete_target:
          condition: "All implementors link to same specific type"
          solution: "Interface LinkTypeConstraint with ObjectType target"
        polymorphic_target:
          condition: "Implementors can link to any implementation of abstract type"
          solution: "Interface LinkTypeConstraint with Interface target"
    
    inheritance_needed:
      question: "Need to compose multiple capability interfaces?"
      yes: "Use interface extension (multiple inheritance supported)"
      example: "EducationalContent extends Identifiable, Timestamped, Searchable"
```

### Interface validation rules

```yaml
interface_validation_rules:
  - rule_id: "IF001"
    name: "Valid API name format"
    condition: "apiName matches ^[a-z][a-zA-Z0-9]*$ and length 1-100"
    severity: "ERROR"
    
  - rule_id: "IF002"
    name: "At least one shared property"
    condition: "Interface must define at least one sharedProperty"
    severity: "WARNING"
    
  - rule_id: "IF003"
    name: "Required properties mapped"
    condition: "All required sharedProperties must be mapped in implementations"
    severity: "ERROR"
    
  - rule_id: "IF004"
    name: "Link constraints satisfied"
    condition: "Required linkTypeConstraints must be satisfied by concrete links"
    severity: "ERROR"
    
  - rule_id: "IF005"
    name: "No circular extension"
    condition: "Interface cannot extend itself directly or indirectly"
    severity: "ERROR"
    
  - rule_id: "IF006"
    name: "Unique primary keys across implementors"
    condition: "Implementors should have globally unique PKs for polymorphic refs"
    severity: "WARNING"
    message: "Use composite IDs like {type}_TSK-001 to avoid collisions"
    
  - rule_id: "IF007"
    name: "Property type compatibility"
    condition: "Mapped local properties must be type-compatible with shared properties"
    severity: "ERROR"
```

### Interface anti-patterns

```yaml
interface_antipatterns:
  - id: "IF_ANTI_001"
    name: "Non-Unique Primary Keys Across Implementors"
    description: "Same ID format used by multiple implementing types"
    problem: "Polymorphic references break; task_id '001' exists in Incident, Case, and Problem"
    solution: "Use globally unique composite IDs: {type}_TSK-001"
    detection: "Multiple implementors with overlapping PK value spaces"
    
  - id: "IF_ANTI_002"
    name: "Breaking Interface Changes"
    description: "Removing required properties or changing types"
    problem: "Downstream applications and functions break"
    solution: "Create new interface version; migrate gradually; use optional for new properties"
    detection: "Required property removed or type changed in existing interface"
    
  - id: "IF_ANTI_003"
    name: "Over-Abstraction"
    description: "Creating interfaces for single implementors"
    problem: "Unnecessary complexity; no polymorphic benefit"
    solution: "Only create interfaces when 2+ types share shape AND need polymorphic access"
    detection: "Interface has exactly one implementing ObjectType"
    
  - id: "IF_ANTI_004"
    name: "Property Explosion"
    description: "Interface with too many shared properties"
    problem: "Implementors forced to map many properties; reduces flexibility"
    solution: "Keep interfaces focused; use composition via extension"
    detection: "Interface has >15 required shared properties"
```

---

## K-12 Education domain examples

The following canonical examples demonstrate LinkType and Interface modeling for an educational content management system tracking mathematical concepts, problems, and student mastery.

### ObjectType definitions

```yaml
k12_objecttypes:
  MathematicalConcept:
    primary_key: "concept_id"
    primary_key_type: "STRING"
    properties:
      - name: "concept_id"
        type: "STRING"
        required: true
      - name: "title"
        type: "STRING"
        required: true
      - name: "description"
        type: "STRING"
      - name: "grade_level"
        type: "INTEGER"
        constraints: "1-12"
      - name: "subject"
        type: "STRING"
        default: "Mathematics"
      - name: "difficulty"
        type: "STRING"
        enum: ["Beginner", "Intermediate", "Advanced"]
      - name: "domain"
        type: "STRING"
        enum: ["Number Sense", "Algebra", "Geometry", "Statistics"]
      - name: "standard_codes"
        type: "ARRAY[STRING]"
        description: "e.g., CCSS.MATH.3.OA.A.1"
      - name: "created_at"
        type: "TIMESTAMP"
      - name: "updated_at"
        type: "TIMESTAMP"

  ExampleProblem:
    primary_key: "problem_id"
    primary_key_type: "STRING"
    properties:
      - name: "problem_id"
        type: "STRING"
        required: true
      - name: "title"
        type: "STRING"
        required: true
      - name: "problem_statement"
        type: "STRING"
        required: true
      - name: "solution_explanation"
        type: "STRING"
      - name: "answer"
        type: "STRING"
      - name: "grade_level"
        type: "INTEGER"
      - name: "subject"
        type: "STRING"
      - name: "difficulty"
        type: "STRING"
        enum: ["Easy", "Medium", "Hard"]
      - name: "total_points"
        type: "INTEGER"
      - name: "estimated_time_minutes"
        type: "INTEGER"
      - name: "rubric"
        type: "STRING"
        description: "JSON rubric structure"
      - name: "concept_id"
        type: "STRING"
        description: "FK to MathematicalConcept"

  Student:
    primary_key: "student_id"
    primary_key_type: "STRING"
    properties:
      - name: "student_id"
        type: "STRING"
        required: true
      - name: "first_name"
        type: "STRING"
        required: true
      - name: "last_name"
        type: "STRING"
        required: true
      - name: "current_grade"
        type: "INTEGER"
      - name: "enrollment_date"
        type: "DATE"
      - name: "school_id"
        type: "STRING"

  StudentConceptMastery:
    description: "Join object for Student-Concept M:N with properties"
    primary_key: "mastery_id"
    primary_key_type: "STRING"
    properties:
      - name: "mastery_id"
        type: "STRING"
        required: true
        description: "Composite: student_id + concept_id"
      - name: "student_id"
        type: "STRING"
        required: true
      - name: "concept_id"
        type: "STRING"
        required: true
      - name: "learning_date"
        type: "DATE"
      - name: "mastery_level"
        type: "STRING"
        enum: ["Not Started", "In Progress", "Mastered", "Needs Review"]
      - name: "mastery_score"
        type: "DOUBLE"
        constraints: "0.0-1.0"
      - name: "time_spent_minutes"
        type: "INTEGER"
      - name: "attempts_count"
        type: "INTEGER"
      - name: "last_assessed"
        type: "TIMESTAMP"

  Formula:
    primary_key: "formula_id"
    primary_key_type: "STRING"
    properties:
      - name: "formula_id"
        type: "STRING"
        required: true
      - name: "name"
        type: "STRING"
        required: true
      - name: "latex_notation"
        type: "STRING"
        required: true
      - name: "plain_text"
        type: "STRING"
      - name: "description"
        type: "STRING"
      - name: "category"
        type: "STRING"
        enum: ["Algebraic", "Geometric", "Trigonometric", "Statistical"]
```

### LinkType examples for K-12 domain

```yaml
k12_linktypes:
  # 1. PREREQUISITE RELATIONSHIP (Self-referential M:N)
  # Korean: 선수 개념 → 후속 개념
  ConceptPrerequisite:
    display_name: "Concept Prerequisites"
    description: "Mathematical concept dependencies - what must be learned first"
    source_object_type: "MathematicalConcept"
    target_object_type: "MathematicalConcept"
    cardinality: "MANY_TO_MANY"
    backing:
      type: "JOIN_TABLE"
      dataset: "prerequisite_links"
      source_column: "dependent_concept_id"
      target_column: "prerequisite_concept_id"
    api_names:
      from_dependent: "prerequisites"
      from_prerequisite: "enables"
    
    example_data:
      join_table_schema:
        columns:
          - "dependent_concept_id"
          - "prerequisite_concept_id"
          - "strength"  # optional: required|recommended
        sample_rows:
          - ["MULT_001", "ADD_001", "required"]
          - ["DIV_001", "MULT_001", "required"]
          - ["DIV_001", "SUB_001", "recommended"]
          - ["FRAC_001", "DIV_001", "required"]
      
    traversal_examples:
      get_prerequisites: "multiplication.prerequisites.all()"
      get_enabled_concepts: "addition.enables.all()"
      chain_traversal: |
        Objects.search()
          .mathematicalConcepts()
          .filter(c => c.title.exactMatch("Fractions"))
          .searchAroundPrerequisites()
          .searchAroundPrerequisites()  // Get 2 levels deep

  # 2. CONCEPT TO EXAMPLE PROBLEMS (ONE_TO_MANY)
  # Korean: 개념 → 예제 문제
  ConceptToExamples:
    display_name: "Concept Example Problems"
    description: "A concept has multiple example problems demonstrating it"
    source_object_type: "MathematicalConcept"
    target_object_type: "ExampleProblem"
    cardinality: "ONE_TO_MANY"
    backing:
      type: "FOREIGN_KEY"
      foreign_key_object_type: "ExampleProblem"
      foreign_key_property: "concept_id"
      primary_key_object_type: "MathematicalConcept"
    api_names:
      from_concept: "exampleProblems"
      from_problem: "demonstratedConcept"
    
    traversal_examples:
      get_problems: "additionConcept.exampleProblems.all()"
      get_concept: "problem123.demonstratedConcept.get()"

  # 3. CONCEPT TO RELATED FORMULAS (MANY_TO_MANY)
  # Korean: 개념 → 관련 공식
  ConceptToFormulas:
    display_name: "Concept Related Formulas"
    description: "Concepts reference formulas; formulas apply to multiple concepts"
    source_object_type: "MathematicalConcept"
    target_object_type: "Formula"
    cardinality: "MANY_TO_MANY"
    backing:
      type: "JOIN_TABLE"
      dataset: "concept_formula_links"
      source_column: "concept_id"
      target_column: "formula_id"
    api_names:
      from_concept: "relatedFormulas"
      from_formula: "applicableConcepts"
    
    example_data:
      join_table_schema:
        columns:
          - "concept_id"
          - "formula_id"
          - "usage_context"  # primary|derived|auxiliary
        sample_rows:
          - ["AREA_001", "QUAD_AREA_F", "primary"]
          - ["PERIM_001", "QUAD_AREA_F", "derived"]

  # 4. STUDENT TO LEARNED CONCEPTS (MANY_TO_MANY with Properties)
  # Korean: 학생 → 학습한 개념
  StudentLearning:
    display_name: "Student Learning Progress"
    description: "Students learn many concepts with tracked mastery"
    source_object_type: "Student"
    target_object_type: "MathematicalConcept"
    cardinality: "MANY_TO_MANY"
    backing:
      type: "OBJECT_BACKED"
      backing_object_type: "StudentConceptMastery"
      source_link: "studentMasteryRecords"  # Student → StudentConceptMastery
      target_link: "conceptMasteryRecords"  # MathematicalConcept → StudentConceptMastery
    api_names:
      from_student: "learnedConcepts"
      from_concept: "studentLearners"
    
    link_properties_via_backing_object:
      - "learning_date"
      - "mastery_level"
      - "mastery_score"
      - "time_spent_minutes"
      - "attempts_count"
    
    traversal_examples:
      get_student_concepts: "student123.learnedConcepts.all()"
      get_concept_students: "additionConcept.studentLearners.all()"
      get_mastery_details: |
        // Access link properties via backing object
        const masteryRecords = student123.studentMasteryRecords.all();
        masteryRecords.forEach(record => {
          console.log(record.masteryLevel, record.masteryScore);
        });
```

### Interface examples for K-12 domain

```yaml
k12_interfaces:
  # 1. EDUCATIONAL CONTENT INTERFACE
  EducationalContent:
    display_name: "Educational Content"
    description: "Common interface for all educational materials"
    api_name: "educationalContent"
    
    shared_properties:
      - api_name: "contentId"
        display_name: "Content ID"
        type: "STRING"
        required: true
      - api_name: "title"
        display_name: "Title"
        type: "STRING"
        required: true
      - api_name: "gradeLevel"
        display_name: "Grade Level"
        type: "INTEGER"
        required: true
      - api_name: "subject"
        display_name: "Subject"
        type: "STRING"
        required: true
      - api_name: "difficulty"
        display_name: "Difficulty"
        type: "STRING"
        required: true
      - api_name: "createdAt"
        display_name: "Created At"
        type: "TIMESTAMP"
        required: false
      - api_name: "updatedAt"
        display_name: "Updated At"
        type: "TIMESTAMP"
        required: false
    
    link_type_constraints:
      - api_name: "relatedContent"
        display_name: "Related Content"
        target_type: "INTERFACE"
        target: "EducationalContent"
        cardinality: "MANY"
        required: false
        description: "Links to other educational content"
    
    implementors:
      MathematicalConcept:
        property_mapping:
          contentId: "concept_id"
          title: "title"
          gradeLevel: "grade_level"
          subject: "subject"
          difficulty: "difficulty"
          createdAt: "created_at"
          updatedAt: "updated_at"
      
      ExampleProblem:
        property_mapping:
          contentId: "problem_id"
          title: "title"
          gradeLevel: "grade_level"
          subject: "subject"
          difficulty: "difficulty"
      
      LectureVideo:
        object_type_properties:
          - "video_id"
          - "title"
          - "grade_level"
          - "subject"
          - "difficulty"
          - "duration_minutes"
          - "video_url"
          - "transcript"
        property_mapping:
          contentId: "video_id"
          title: "title"
          gradeLevel: "grade_level"
          subject: "subject"
          difficulty: "difficulty"
      
      TextbookChapter:
        object_type_properties:
          - "chapter_id"
          - "title"
          - "grade_level"
          - "subject"
          - "difficulty"
          - "page_count"
          - "chapter_number"
          - "textbook_id"
        property_mapping:
          contentId: "chapter_id"
          title: "title"
          gradeLevel: "grade_level"
          subject: "subject"
          difficulty: "difficulty"
    
    usage_examples:
      search_all_content: |
        // Find all educational content for Grade 5 Mathematics
        const grade5Content = Objects.search()
          .educationalContent()
          .filter(c => c.gradeLevel.eq(5))
          .filter(c => c.subject.exactMatch("Mathematics"))
          .all();
      
      polymorphic_action: |
        // Action that works on any EducationalContent
        @Action({
          parameters: {
            content: { type: "interface", interface: "EducationalContent" }
          }
        })
        function archiveContent(content: EducationalContent): void {
          // Works for Concept, Problem, Video, or Chapter
        }

  # 2. ASSESSABLE INTERFACE
  Assessable:
    display_name: "Assessable"
    description: "Interface for items that can be graded/scored"
    api_name: "assessable"
    
    shared_properties:
      - api_name: "assessmentId"
        display_name: "Assessment ID"
        type: "STRING"
        required: true
      - api_name: "totalPoints"
        display_name: "Total Points"
        type: "INTEGER"
        required: true
      - api_name: "difficulty"
        display_name: "Difficulty"
        type: "STRING"
        required: true
      - api_name: "estimatedTimeMinutes"
        display_name: "Estimated Time (minutes)"
        type: "INTEGER"
        required: true
      - api_name: "rubric"
        display_name: "Grading Rubric"
        type: "STRING"
        required: false
        description: "JSON structure for grading criteria"
    
    link_type_constraints:
      - api_name: "assessedConcepts"
        display_name: "Assessed Concepts"
        target_type: "OBJECT_TYPE"
        target: "MathematicalConcept"
        cardinality: "MANY"
        required: true
        description: "What concepts does this assessment evaluate?"
    
    implementors:
      ExampleProblem:
        property_mapping:
          assessmentId: "problem_id"
          totalPoints: "total_points"
          difficulty: "difficulty"
          estimatedTimeMinutes: "estimated_time_minutes"
          rubric: "rubric"
        link_mapping:
          assessedConcepts: "demonstratedConcept"
      
      Quiz:
        object_type_properties:
          - "quiz_id"
          - "quiz_title"
          - "total_points"
          - "difficulty"
          - "estimated_time_minutes"
          - "rubric"
          - "question_count"
          - "passing_score"
          - "attempts_allowed"
        property_mapping:
          assessmentId: "quiz_id"
          totalPoints: "total_points"
          difficulty: "difficulty"
          estimatedTimeMinutes: "estimated_time_minutes"
          rubric: "rubric"
        link_mapping:
          assessedConcepts: "coveredConcepts"
      
      Exam:
        object_type_properties:
          - "exam_id"
          - "exam_title"
          - "total_points"
          - "difficulty"
          - "estimated_time_minutes"
          - "rubric"
          - "exam_date"
          - "proctor_required"
          - "calculator_allowed"
        property_mapping:
          assessmentId: "exam_id"
          totalPoints: "total_points"
          difficulty: "difficulty"
          estimatedTimeMinutes: "estimated_time_minutes"
          rubric: "rubric"
        link_mapping:
          assessedConcepts: "testedConcepts"
    
    usage_examples:
      find_assessments_by_concept: |
        // Find all assessments for a specific concept
        const algebraAssessments = Objects.search()
          .assessable()
          .searchAroundAssessedConcepts()
          .filter(c => c.domain.exactMatch("Algebra"))
          .all();
      
      calculate_total_study_time: |
        // Sum estimated time for all assessments
        const assessments = Objects.search().assessable().all();
        const totalMinutes = assessments.reduce(
          (sum, a) => sum + a.estimatedTimeMinutes, 0
        );
```

---

## Integration reference for both components

```yaml
integration_points:
  linktype_with_interface:
    link_constraints_on_interfaces:
      description: "Interfaces can define abstract links that implementors must satisfy"
      target_options:
        interface_target: "Polymorphic - any implementor can satisfy"
        objecttype_target: "Concrete - specific type required"
    
    interface_references_in_links:
      supported: true
      use_case: "Create links where either side is an interface"
      example: "EducationalContent → Alert interface"
  
  actions_integration:
    linktype_actions:
      create_link: "M:N links only - use Create Link rule"
      delete_link: "M:N links only - use Delete Link rule"
      fk_based_links: "Modify foreign key property via Modify Object rule"
    
    interface_actions:
      create_object: "Create object of any implementing type"
      modify_object: "Only interface shared properties modifiable"
      delete_object: "Delete any implementing object"
      limitation: "Cannot reference interface link type constraints directly"
  
  osdk_integration:
    typescript:
      interfaces: "Supported as API layer"
      interface_link_types: "Not yet supported"
      interface_aggregations: "Not yet supported"
    java_python: "In development"
  
  functions_integration:
    typescript_v2:
      interfaces: "Full support"
      edits_declaration: |
        type OntologyEdit = 
          | Edits.Object<Concept> 
          | Edits.Interface<EducationalContent>
          | Edits.Link<Student, "learnedConcepts">;
    typescript_v1: "Not supported for interfaces"

documentation_sources:
  linktype:
    - url: "https://www.palantir.com/docs/foundry/object-link-types/link-types-overview"
      topic: "Core definitions"
    - url: "https://www.palantir.com/docs/foundry/object-link-types/create-link-type"
      topic: "Creation and configuration"
    - url: "https://www.palantir.com/docs/foundry/object-link-types/link-type-metadata"
      topic: "Metadata and API names"
    - url: "https://www.palantir.com/docs/foundry/object-link-types/edit-link-types"
      topic: "Editing and cardinality changes"
    - url: "https://www.palantir.com/docs/foundry/action-types/rules"
      topic: "Link writeback via Actions"
    - url: "https://www.palantir.com/docs/foundry/functions/api-object-sets"
      topic: "Search Around traversal"
  
  interface:
    - url: "https://www.palantir.com/docs/foundry/interfaces/interface-overview"
      topic: "Core definitions and platform support"
    - url: "https://www.palantir.com/docs/foundry/interfaces/create-interface"
      topic: "Creation and shared properties"
    - url: "https://www.palantir.com/docs/foundry/interfaces/implement-interface"
      topic: "Implementation patterns"
    - url: "https://www.palantir.com/docs/foundry/interfaces/extend-interface"
      topic: "Inheritance and extension"
    - url: "https://www.palantir.com/docs/foundry/interfaces/interface-link-types-overview"
      topic: "Link type constraints"
    - url: "https://www.palantir.com/docs/foundry/action-types/actions-on-interfaces"
      topic: "Actions on interfaces"
```

---

## Conclusion

This reference enables precise Palantir Ontology modeling through two complementary components. **LinkType** handles relationships with four cardinality options backed by foreign keys, join tables, or intermediary objects—the choice depends on whether the relationship is 1:1/N:1 (FK), M:N without properties (join table), or M:N with properties (object-backed). **Interface** enables polymorphism through shared properties and link constraints, supporting multiple inheritance and implementation by multiple ObjectTypes.

The K-12 education examples demonstrate practical application: self-referential concept prerequisites use M:N with join tables, concept-to-problem relationships use 1:N with foreign keys, and student learning progress uses object-backed links to capture mastery metadata. The EducationalContent and Assessable interfaces show how to abstract common shapes across content types while enforcing link constraints.

Key constraints to remember: ONE_TO_ONE cardinality is **not enforced** at platform level, Workshop does **not** support interfaces, and interface link type constraints cannot be directly referenced in Actions. Cardinality changes trigger reindexing that makes links temporarily unavailable and deletes writeback history.