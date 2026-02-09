# Palantir Ontology Core Semantic Primitives: Complete Reference

## Executive Summary

This comprehensive reference document provides **complete specifications** for defining Palantir Ontology components (ObjectType, Property, SharedProperty) for K-12 Education domain modeling. Claude-Opus-4.5 can use this document to generate unambiguous, spec-compliant Ontology definitions for any codebase analysis.

**Key finding**: Palantir Ontology maps real-world concepts to data assets through three core primitives. **ObjectTypes** define entity schemas (like database tables), **Properties** define typed attributes with rich constraints, and **SharedProperties** enable cross-type consistency and interface polymorphism. For K-12 math education, mathematical concepts like LinearEquation warrant ObjectType status when they have independent identity and relationships, while atomic components like coefficients are better modeled as Properties.

---

# Component 1: ObjectType

## 1. official_definition

**Source**: https://www.palantir.com/docs/foundry/object-link-types/object-types-overview

> "An **object type** is the schema definition of a real-world entity or event."

| Term | Definition |
|------|------------|
| **ObjectType** | Schema definition (type-level metadata: display name, property names, property data types, description) |
| **Object/Object Instance** | The actual primary key and property values for a specific instance |
| **Object Set** | A collection of multiple object instances representing a group of real-world entities |

**Analogy to Datasets**:
- ObjectType ≈ Dataset schema
- Object ≈ Row in a dataset
- Object Set ≈ Filtered set of rows

**Source URL**: https://www.palantir.com/docs/foundry/object-link-types/create-object-type

---

## 2. semantic_definition

| Paradigm | Equivalent Concept | Mapping Notes |
|----------|-------------------|---------------|
| **OOP** | Class | ObjectType = Class definition; Object = Instance |
| **RDBMS** | Table Schema | ObjectType = CREATE TABLE definition; Object = Row |
| **RDF/OWL** | owl:Class | ObjectType = Class in ontology; Object = Individual |
| **JSON Schema** | Object Schema | ObjectType = schema definition; Object = validated document |
| **TypeScript** | interface/type | ObjectType = type definition; Object = value conforming to type |

**Semantic Role**: ObjectType defines the **intension** (definitional properties) of a concept, while Objects are the **extension** (actual instances) of that concept.

---

## 3. structural_schema

```yaml
# JSON Schema Draft 2020-12 for ObjectType Definition
$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "palantir-objecttype-schema"
title: "Palantir ObjectType Definition"
type: object

required:
  - apiName
  - displayName
  - pluralDisplayName
  - primaryKey
  - titleKey
  - backingDatasource

properties:
  # REQUIRED FIELDS
  apiName:
    type: string
    description: "Programmatic identifier for the ObjectType"
    pattern: "^[A-Z][a-zA-Z0-9_]*$"  # PascalCase, starts with uppercase
    minLength: 1
    maxLength: 255  # Inferred limit
    not:
      enum: ["Ontology", "Object", "Property", "Link", "Relation", "Rid", "PrimaryKey", "TypeId", "OntologyObject"]
    examples: ["LinearEquation", "MathProblem", "CurriculumUnit"]
    
  displayName:
    type: string
    description: "Human-readable name shown in UI"
    minLength: 1
    examples: ["Linear Equation", "Math Problem"]
    
  pluralDisplayName:
    type: string
    description: "Plural form for collections"
    examples: ["Linear Equations", "Math Problems"]
    
  primaryKey:
    type: array
    description: "Properties uniquely identifying each object instance"
    items:
      type: string
    minItems: 1
    examples: [["equationId"], ["gradeLevel", "conceptCode"]]
    
  titleKey:
    type: string
    description: "Property used as display name for objects"
    examples: ["displayNotation", "conceptName"]
    
  backingDatasource:
    type: string
    description: "RID of the dataset backing this ObjectType"
    pattern: "^ri\\..*"
    
  # OPTIONAL FIELDS
  rid:
    type: string
    description: "Auto-generated Resource Identifier"
    pattern: "^ri\\.ontology\\.main\\.object-type\\.[a-f0-9-]+$"
    readOnly: true
    
  description:
    type: string
    description: "Explanatory text for the ObjectType"
    
  status:
    type: string
    enum: ["ACTIVE", "EXPERIMENTAL", "DEPRECATED", "EXAMPLE", "ENDORSED"]
    default: "EXPERIMENTAL"
    
  visibility:
    type: string
    enum: ["PROMINENT", "NORMAL", "HIDDEN"]
    default: "NORMAL"
    
  icon:
    type: string
    description: "Visual identifier icon name"
    
  color:
    type: string
    description: "Visual identifier color"
    
  groups:
    type: array
    items:
      type: string
    description: "Classification labels for organization"
    
  aliases:
    type: array
    items:
      type: string
    description: "Additional search terms"
    
  typeClasses:
    type: array
    items:
      type: string
    description: "Additional metadata for user applications"
    
  properties:
    type: object
    additionalProperties:
      $ref: "#/$defs/PropertyDefinition"
    maxProperties: 2000  # OSv2 limit

$defs:
  PropertyDefinition:
    type: object
    required: ["baseType"]
    properties:
      baseType:
        type: string
      description:
        type: string
```

---

## 3a. UI Metadata & Render Hints

> Source: Ontology.md Section 1 — Ontology Manager UI Metadata

```yaml
ui_metadata:
  description: "Configuration that controls how ObjectTypes appear in Ontology Manager, Workshop, Object Explorer, and other platform UIs"

  display_configuration:
    titleProperty:
      description: "Property used as the display name for object instances in all UIs"
      selection_rules:
        - "Must be a String property"
        - "Choose the most human-readable identifier (name, title, label)"
        - "Avoid using primary key as title if a more readable property exists"
      example: "Employee.fullName, not Employee.employeeId"

    descriptionProperty:
      description: "Property shown as subtitle/detail text below the title in search results and cards"
      selection_rules:
        - "Typically the longest descriptive text field"
        - "Should provide context beyond the title"
      example: "Employee.jobTitle or Employee.department"

    icon:
      description: "Blueprint icon displayed next to the ObjectType in UI"
      source: "Blueprint icon set (https://blueprintjs.com/docs/#icons)"
      format: "Icon name string, e.g., 'person', 'office', 'document'"
      recommendations:
        person_entities: "person, people, user"
        location_entities: "map-marker, office, globe"
        document_entities: "document, folder-close, archive"
        event_entities: "calendar, time, history"
        financial_entities: "dollar, credit-card, bank-account"
        product_entities: "box, shopping-cart, barcode"

    color:
      description: "Accent color for ObjectType in graphs, maps, and visualizations"
      purpose: "Visual differentiation between ObjectTypes in multi-type displays"

  visibility_levels:
    NORMAL: "Standard visibility — appears in all searches and listings"
    PROMINENT: "Highlighted in Ontology Manager — used for core domain entities"
    HIDDEN: "Excluded from casual browsing — used for system/internal ObjectTypes"
    recommendation: "Set core business entities to PROMINENT, utility/join types to HIDDEN"

  status_lifecycle:
    EXPERIMENTAL: "New ObjectType under development — may change without notice"
    ACTIVE: "Production-ready — stable schema, safe to build applications on"
    ENDORSED: "Recommended for organization-wide use — curated and maintained"
    DEPRECATED: "Scheduled for removal — migrate dependents to replacement"
    governance: "Status transitions require Ontology Proposal approval"

  search_configuration:
    searchable_properties:
      description: "Properties indexed for full-text search in Object Explorer and OSDK"
      default: "Only titleProperty is searchable by default"
      recommendation: "Enable search on name, description, and key business identifiers"
      performance: "Each searchable property increases index size — enable selectively"
    sort_configuration:
      description: "Properties available for ordering in Object Explorer and OSDK queries"
      default: "All properties are sortable unless explicitly disabled"
      recommendation: "Disable sorting on large text fields and struct properties"

  render_hints:
    description: "Render hint types that control property display behavior in platform UIs"
    official_types:
      disable_formatting: "Display raw value without any formatting applied"
      identifier: "Marks property as an object identifier — monospace or badge styling"
      keywords: "Tokenized keyword display (tags/chips) for skills, categories, labels"
      long_text: "Multi-line text rendering with expand/collapse for description fields"
      low_cardinality: "Enables dropdown/filter UIs for few distinct values (requires Searchable)"
      selectable: "Enables selection in tables and lists (requires Searchable)"
      sortable: "Enables column sorting in tables (requires Searchable)"
      searchable: "Enables full-text search indexing for this property"
    dependency_chain: |
      Searchable ─┬─→ Selectable
                  ├─→ Sortable
                  └─→ Low cardinality
      You must enable Searchable before enabling any dependent hints.
    note: "Render hints are advisory — consuming applications may interpret with platform-specific behavior"
```

---

## 4. decision_tree

```
START: Should this concept be an ObjectType?
│
├─► Q1: Does it represent a REAL-WORLD ENTITY or EVENT?
│   ├─ NO → ❌ NOT an ObjectType (consider Property or Struct)
│   └─ YES → Continue
│
├─► Q2: Does it have a NATURAL PRIMARY KEY for unique identification?
│   ├─ NO → ❌ Reconsider modeling (or use synthetic UUID)
│   └─ YES → Continue
│
├─► Q3: Does it need to PARTICIPATE IN RELATIONSHIPS (links) with other types?
│   ├─ NO → Consider: Is it a characteristic of another entity?
│   │       ├─ YES → ❌ Model as Property
│   │       └─ NO → Continue (may still be ObjectType)
│   └─ YES → Continue
│
├─► Q4: Does it have MULTIPLE PROPERTIES describing its characteristics?
│   ├─ NO (only 1-2 attributes) → ⚠️ Consider embedding as Property
│   └─ YES → Continue
│
├─► Q5: Does it need INDEPENDENT LIFECYCLE (create, update, delete separately)?
│   ├─ NO (always created/deleted with parent) → Consider Struct or embedded Property
│   └─ YES → Continue
│
├─► Q6: Will users QUERY or FILTER on this entity independently?
│   ├─ NO → ⚠️ Consider if ObjectType overhead is justified
│   └─ YES → Continue
│
├─► Q7: Does it need PERMISSION CONTROLS separate from parent?
│   ├─ NO → May still be ObjectType
│   └─ YES → ✅ Definitely ObjectType
│
└─► RESULT: ✅ Create as ObjectType

EDGE CASES:
├─► Mathematical Variable (x in "3x - 2 = 5")
│   └─ Decision: Property (no independent identity in educational context)
│
├─► Coefficient (3 in "3x")
│   └─ Decision: Property (scalar value, no relationships)
│
├─► LinearEquation ("3x - 2 = 5")
│   └─ Decision: ObjectType (independent identity, relationships, queried)
│
├─► MathematicalConcept ("일차방정식" as curriculum concept)
│   └─ Decision: ObjectType (curriculum entity, has prerequisites)
│
└─► Term/Monomial ("3x" as component)
    └─ Decision: Struct Property on Polynomial (OR ObjectType if tracked independently)
```

---

## 5. validation_rules

```yaml
# Machine-executable validation rules for ObjectType
validation_rules:
  apiName:
    - rule: "must_start_with_uppercase"
      regex: "^[A-Z]"
      error: "apiName must begin with uppercase character"
      
    - rule: "alphanumeric_underscore_only"
      regex: "^[A-Za-z0-9_]+$"
      error: "apiName must contain only alphanumeric characters and underscores"
      
    - rule: "pascal_case_format"
      regex: "^[A-Z][a-z0-9]*([A-Z][a-z0-9]*)*$"
      error: "apiName should follow PascalCase convention"
      
    - rule: "not_reserved_word"
      forbidden: ["ontology", "object", "property", "link", "relation", "rid", "primaryKey", "typeId", "ontologyObject"]
      case_insensitive: true
      error: "apiName cannot be a reserved word"
      
    - rule: "globally_unique"
      scope: "ontology"
      error: "apiName must be unique across all object types"

  primaryKey:
    - rule: "must_be_deterministic"
      description: "Primary key values must not change between builds"
      error: "Non-deterministic primary keys cause edit loss and link disappearance"
      
    - rule: "must_be_unique_per_row"
      description: "Each row in datasource must have unique primary key"
      error: "OSv2: Duplicate primary keys cause Funnel batch pipeline errors"
      
    - rule: "no_null_values"
      description: "Primary key properties cannot contain null"
      error: "Null primary key values are not permitted"
      
    - rule: "recommended_types"
      preferred: ["String", "Integer"]
      discouraged: ["Long", "Boolean", "Date", "Timestamp"]
      forbidden: ["Float", "Double", "Decimal", "Geopoint", "Geoshape"]

  backingDatasource:
    - rule: "single_objecttype_per_datasource"
      description: "A datasource can only back one object type"
      error: "Phonograph2:DatasetAndBranchAlreadyRegistered"
      
    - rule: "no_maptype_columns"
      description: "Datasource may not contain MapType columns"
      
    - rule: "no_structtype_columns"
      description: "Datasource may not contain StructType columns"

  limits:
    max_properties_per_objecttype: 2000
    max_datasources_per_objecttype: 70
    max_objects_per_action: 10000
    search_around_default_limit: 100000
```

---

## 6. canonical_examples

### Example 1: LinearEquation (일차방정식)

```yaml
# K-12 Education: Linear Equation ObjectType
apiName: "LinearEquation"
displayName: "Linear Equation"
pluralDisplayName: "Linear Equations"
description: "A first-degree polynomial equation of form ax + b = c"

primaryKey: ["equationId"]
titleKey: "displayNotation"

status: "ACTIVE"
visibility: "PROMINENT"

groups:
  - "Mathematics"
  - "Algebra"
  - "Grade 8"

properties:
  equationId:
    baseType: "String"
    description: "UUID identifier for the equation"
    
  displayNotation:
    baseType: "String"
    description: "Human-readable notation (e.g., '3x - 2 = 5')"
    renderHints:
      searchable: true
      
  latexNotation:
    baseType: "String"
    description: "LaTeX formatted notation"
    
  variableSymbol:
    baseType: "String"
    description: "Variable used (e.g., 'x', 'y')"
    constraints:
      regex: "^[a-zA-Z]$"
      
  coefficient:
    baseType: "Double"
    description: "Coefficient of variable (e.g., 3 in '3x')"
    
  constantLeft:
    baseType: "Double"
    description: "Constant on left side (e.g., -2 in '3x - 2')"
    
  constantRight:
    baseType: "Double"
    description: "Constant on right side (e.g., 5 in '= 5')"
    
  solution:
    baseType: "Double"
    description: "Computed solution value"
    
  gradeLevel:
    baseType: "Integer"
    description: "Target grade level (Shared Property)"
    sharedProperty: "gradeLevel"
    
  difficultyLevel:
    baseType: "Integer"
    description: "Difficulty 1-5"
    sharedProperty: "difficultyLevel"
    constraints:
      range:
        min: 1
        max: 5
```

### Example 2: MathematicalConcept (수학 개념)

```yaml
apiName: "MathematicalConcept"
displayName: "Mathematical Concept"
pluralDisplayName: "Mathematical Concepts"
description: "Core curriculum concept in mathematics education"

primaryKey: ["conceptId"]
titleKey: "conceptName"

status: "ACTIVE"
visibility: "PROMINENT"

properties:
  conceptId:
    baseType: "String"
    description: "Natural key (e.g., 'linear-equation', 'polynomial')"
    
  conceptName:
    baseType: "String"
    description: "English name"
    renderHints:
      searchable: true
      
  conceptNameKo:
    baseType: "String"
    description: "Korean name (e.g., '일차방정식')"
    renderHints:
      searchable: true
      
  definition:
    baseType: "String"
    description: "Formal definition"
    renderHints:
      longText: true
      
  gradeLevel:
    baseType: "Integer"
    sharedProperty: "gradeLevel"
    
  curriculumDomain:
    baseType: "String"
    description: "Domain (Algebra, Geometry, etc.)"
    constraints:
      enum: ["Algebra", "Geometry", "Arithmetic", "Statistics", "Calculus"]
      
  exampleNotations:
    baseType: "Array<String>"
    description: "Example mathematical notations"
```

### Example 3: Polynomial (다항식)

```yaml
apiName: "Polynomial"
displayName: "Polynomial"
pluralDisplayName: "Polynomials"
description: "Mathematical expression of sum of terms"

primaryKey: ["polynomialId"]
titleKey: "displayNotation"

properties:
  polynomialId:
    baseType: "String"
    
  displayNotation:
    baseType: "String"
    sharedProperty: "displayNotation"
    
  degree:
    baseType: "Integer"
    description: "Highest exponent in polynomial"
    
  variableSymbol:
    baseType: "String"
    
  coefficients:
    baseType: "Array<Double>"
    description: "Coefficients ordered by ascending degree [a0, a1, a2, ...]"
    
  terms:
    baseType: "Array<Struct>"
    description: "Detailed term breakdown"
    structSchema:
      coefficient:
        baseType: "Double"
      variableSymbol:
        baseType: "String"
      exponent:
        baseType: "Integer"
        
  isMonomial:
    baseType: "Boolean"
    description: "True if polynomial has exactly one term"
    
  gradeLevel:
    baseType: "Integer"
    sharedProperty: "gradeLevel"
```

---

## 7. anti_patterns

### Anti-Pattern 1: Over-Normalization (과도한 세분화)

```yaml
# ❌ WRONG: Creating ObjectTypes for atomic values
apiName: "Coefficient"
displayName: "Coefficient"
primaryKey: ["coefficientId"]
properties:
  coefficientId:
    baseType: "String"
  value:
    baseType: "Double"

# WHY IT'S WRONG:
# - Coefficient has no independent identity
# - No relationships needed
# - Always accessed via parent equation
# - Creates unnecessary complexity and joins

# ✅ CORRECT: Model as Property on parent
# On LinearEquation ObjectType:
properties:
  coefficient:
    baseType: "Double"
    description: "Coefficient of variable term"
```

### Anti-Pattern 2: Non-Deterministic Primary Key

```yaml
# ❌ WRONG: Using runtime-generated values as primary key
apiName: "MathProblem"
primaryKey: ["rowNumber"]  # Generated at pipeline runtime

# WHY IT'S WRONG:
# - rowNumber changes between builds
# - Edits attached to old rowNumber are lost
# - Links between objects disappear
# - OSv2 fails; OSv1 silently corrupts data

# ✅ CORRECT: Use deterministic identifier
primaryKey: ["problemId"]  # UUID or natural key from source
properties:
  problemId:
    baseType: "String"
    description: "Stable UUID generated at content creation time"
```

### Anti-Pattern 3: Duplicate Primary Keys Across Rows

```yaml
# ❌ WRONG: Dataset with non-unique primary key
# Dataset rows:
# | equationId | displayNotation |
# | eq-001     | "2x + 3 = 7"    |
# | eq-001     | "3x - 1 = 5"    |  ← DUPLICATE KEY

# CONSEQUENCE:
# - OSv2: Build failure (Funnel batch pipeline error)
# - OSv1: Silent data loss, unpredictable behavior

# ✅ CORRECT: Ensure unique primary keys
# Deduplicate in pipeline before Ontology indexing
```

### Anti-Pattern 4: Circular Link Dependencies Without Clear Direction

```yaml
# ❌ PROBLEMATIC: Bidirectional without semantic clarity
linkTypes:
  - name: "relatedTo"
    from: "MathematicalConcept"
    to: "MathematicalConcept"
    # No cardinality or direction semantics

# ✅ CORRECT: Clear directional semantics
linkTypes:
  - name: "isPrerequisiteOf"
    from: "MathematicalConcept"  # Source (simpler concept)
    to: "MathematicalConcept"    # Target (dependent concept)
    cardinality: "manyToMany"
    # Direction: A isPrerequisiteOf B means A must be learned before B
```

---

## 7a. code_pattern_identification

> Source: Ontology.md Section 1 — Code Pattern Identification Rules

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

---

## 8. integration_points

```yaml
integration_points:
  property:
    relationship: "ObjectType CONTAINS Properties"
    description: "Properties define the attributes of an ObjectType"
    constraints:
      - "Property apiNames must be unique within ObjectType"
      - "Maximum 2000 properties per ObjectType (OSv2)"
      - "At least one property must be designated as primaryKey"
      - "One property must be designated as titleKey"
      
  sharedProperty:
    relationship: "ObjectType CAN USE SharedProperty"
    description: "SharedProperties provide cross-type consistency"
    mechanism: "Property references SharedProperty via sharedProperty field"
    behavior:
      - "Local property inherits metadata from SharedProperty"
      - "Local apiName remains unchanged (prevents breaking changes)"
      - "Render hint overrides apply when associating"
      
  interface:
    relationship: "ObjectType IMPLEMENTS Interface"
    description: "Interfaces define polymorphic shape via SharedProperties"
    requirements:
      - "ObjectType must have all required SharedProperties from Interface"
      - "SharedProperties can be mapped from existing local properties"
      
  linkType:
    relationship: "ObjectType PARTICIPATES IN LinkType"
    description: "LinkTypes connect ObjectTypes in relationships"
    roles: ["source", "target"]
    
  datasource:
    relationship: "ObjectType IS BACKED BY Datasource"
    constraints:
      - "One datasource backs exactly one ObjectType"
      - "Column types must be compatible with Property baseTypes"
      - "No MapType or StructType columns in backing dataset"
```

---

# Component 2: Property

## 1. official_definition

**Source**: https://www.palantir.com/docs/foundry/object-link-types/properties-overview

> "Properties are the attributes that define an object type. Each property has a base type that determines what types of values it can hold and what operations can be performed on it."

Properties store the actual data values for each object instance. The **base type** determines:
- Valid values the property can contain
- Available operations (search, sort, aggregate)
- Indexing behavior
- Action type parameter compatibility

---

## 2. semantic_definition

| Paradigm | Equivalent Concept | Mapping Notes |
|----------|-------------------|---------------|
| **OOP** | Instance field/attribute | Property = field declaration |
| **RDBMS** | Column | Property = column definition with type |
| **RDF/OWL** | owl:DatatypeProperty / owl:ObjectProperty | Property defines predicate |
| **JSON Schema** | Property in properties object | With type and constraints |
| **TypeScript** | Property in interface/type | With type annotation |

---

## 3. structural_schema

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "palantir-property-schema"
title: "Palantir Property Definition"
type: object

required:
  - apiName
  - baseType

properties:
  apiName:
    type: string
    description: "Programmatic identifier"
    pattern: "^[a-z][a-zA-Z0-9]*$"  # camelCase, starts lowercase
    not:
      enum: ["ontology", "object", "property", "link", "relation", "rid", "primaryKey", "typeId"]
    examples: ["equationId", "displayNotation", "gradeLevel"]
    
  displayName:
    type: string
    description: "Human-readable name"
    
  description:
    type: string
    
  baseType:
    type: string
    enum:
      # Primitive Types
      - "String"
      - "Integer"
      - "Short"
      - "Long"
      - "Byte"
      - "Boolean"
      - "Float"
      - "Double"
      - "Decimal"
      # Time Types
      - "Date"
      - "Timestamp"
      # Geospatial Types
      - "Geopoint"
      - "Geoshape"
      # Complex Types
      - "Array"
      - "Struct"
      - "Vector"
      # Reference Types
      - "MediaReference"
      - "Attachment"
      - "TimeSeries"
      - "GeotimeSeriesReference"
      # Special Types
      - "CipherText"
      - "MandatoryControl"
      
  arraySubtype:
    type: string
    description: "Element type for Array baseType"
    
  structSchema:
    type: object
    description: "Field definitions for Struct baseType"
    maxProperties: 10
    
  vectorDimension:
    type: integer
    description: "Dimension for Vector baseType"
    maximum: 2048
    
  required:
    type: boolean
    default: false
    
  visibility:
    type: string
    enum: ["PROMINENT", "NORMAL", "HIDDEN"]
    default: "NORMAL"
    
  renderHints:
    type: object
    properties:
      searchable:
        type: boolean
        default: false
      sortable:
        type: boolean
        default: false
      selectable:
        type: boolean
        default: false
      lowCardinality:
        type: boolean
        default: false
      longText:
        type: boolean
        default: false
      keywords:
        type: boolean
        default: false
      identifier:
        type: boolean
        default: false
      disableFormatting:
        type: boolean
        default: false
        
  constraints:
    type: object
    properties:
      enum:
        type: array
        description: "Allowed values"
      range:
        type: object
        properties:
          min: {}
          max: {}
      regex:
        type: string
        description: "Pattern for String validation"
      rid:
        type: boolean
        description: "Must be valid RID format"
      uuid:
        type: boolean
        description: "Must be valid UUID format"
      uniqueness:
        type: boolean
        description: "Array elements must be unique"
        
  sharedProperty:
    type: string
    description: "Reference to SharedProperty apiName"
```

---

## 4. decision_tree

```
START: What baseType should this Property use?
│
├─► Is it TEXT data?
│   ├─ Short text (< 256 chars) → String
│   ├─ Long text/prose → String + renderHints.longText: true
│   ├─ Encrypted sensitive → CipherText
│   └─ Pattern constrained → String + constraints.regex
│
├─► Is it NUMERIC data?
│   ├─ Whole number?
│   │   ├─ Range -128 to 127 → Byte
│   │   ├─ Range -32768 to 32767 → Short
│   │   ├─ Range ±2 billion → Integer ✅ (recommended)
│   │   └─ Larger than ±2 billion → Long ⚠️ (JavaScript precision issues)
│   │
│   └─ Decimal number?
│       ├─ Approximate OK → Double ✅ (cannot use in Actions)
│       ├─ Financial/exact → Decimal (cannot use in Actions)
│       └─ Lower precision → Float (cannot use in Actions)
│
├─► Is it TRUE/FALSE?
│   └─ Boolean ⚠️ (discouraged for primary key)
│
├─► Is it DATE/TIME?
│   ├─ Date only (no time) → Date
│   └─ Date with time → Timestamp
│
├─► Is it LOCATION?
│   ├─ Single point → Geopoint (WGS 84: "lat,long" or geohash)
│   └─ Shape/polygon → Geoshape (GeoJSON RFC 7946)
│
├─► Is it a COLLECTION?
│   ├─ List of primitives → Array<baseType>
│   │   └─ Note: Cannot contain nulls, no nested arrays in OSv2
│   │
│   └─ Structured object → Struct
│       └─ Constraints: depth=1, max 10 fields, no nested structs
│
├─► Is it for ML/EMBEDDINGS?
│   └─ Vector (max 2048 dimensions, KNN queries only)
│
└─► Is it a FILE/MEDIA reference?
    ├─ Media file → MediaReference
    ├─ Attached document → Attachment
    └─ Time series data → TimeSeries
```

### BaseType Quick Reference

| Use Case | Recommended BaseType | Notes |
|----------|---------------------|-------|
| UUID identifier | String | Pattern: UUID constraint |
| Count/quantity | Integer | Safe for most cases |
| Money/currency | Decimal | Exact precision |
| Percentage/ratio | Double | Approximate OK |
| Grade level (1-12) | Integer | With range constraint |
| Difficulty (1-5) | Integer | With enum constraint |
| Creation date | Timestamp | Include time for precision |
| Korean text | String | UTF-8 supported |
| LaTeX notation | String | Escape handling in app |
| Coefficients array | Array<Double> | For polynomial terms |
| Term structure | Struct | coefficient, variable, exponent |
| Concept embeddings | Vector | 768-2048 dimensions typical |

---

## 5. validation_rules

```yaml
validation_rules:
  apiName:
    - rule: "must_start_with_lowercase"
      regex: "^[a-z]"
      error: "Property apiName must begin with lowercase character"
      
    - rule: "camel_case_format"
      regex: "^[a-z][a-zA-Z0-9]*$"
      error: "Property apiName must be camelCase"
      
    - rule: "unique_within_objecttype"
      scope: "objectType"
      error: "Property apiName must be unique within its ObjectType"
      
    - rule: "not_reserved_word"
      forbidden: ["ontology", "object", "property", "link", "relation", "rid", "primaryKey", "typeId"]
      
  baseType_compatibility:
    primaryKey_allowed:
      - "String"
      - "Integer"
      - "Short"
      - "Long"  # Discouraged
      - "Byte"  # Discouraged
      - "Boolean"  # Discouraged
      - "Date"  # Discouraged
      - "Timestamp"  # Discouraged
    primaryKey_forbidden:
      - "Float"
      - "Double"
      - "Decimal"
      - "Geopoint"
      - "Geoshape"
      - "Array"
      - "Struct"
      - "Vector"
      - "MediaReference"
      - "Attachment"
      
    action_parameter_forbidden:
      - "Float"
      - "Double"
      - "Decimal"
      
  struct_constraints:
    max_depth: 1
    max_fields: 10
    allowed_field_types:
      - "Boolean"
      - "Byte"
      - "Date"
      - "Decimal"
      - "Double"
      - "Float"
      - "Geopoint"
      - "Integer"
      - "Long"
      - "Short"
      - "String"
      - "Timestamp"
      
  vector_constraints:
    max_dimension: 2048
    osv2_only: true
    cannot_be_in_array: true
    
  array_constraints:
    cannot_contain_null: true
    nested_arrays_forbidden_osv2: true
    
  renderHints_dependencies:
    sortable_requires: ["searchable"]
    selectable_requires: ["searchable"]
    lowCardinality_requires: ["searchable"]
    
  limits:
    action_primitive_list_max: 10000
    action_object_reference_list_max: 1000
    action_edit_size_osv1: "32KB"
    action_edit_size_osv2: "3MB"
```

---

## 6. canonical_examples

### Example 1: Primary Key Property

```yaml
equationId:
  apiName: "equationId"
  displayName: "Equation ID"
  description: "Unique identifier for the equation"
  baseType: "String"
  required: true
  visibility: "HIDDEN"
  renderHints:
    searchable: true
  constraints:
    uuid: true
```

### Example 2: Searchable Text Property

```yaml
displayNotation:
  apiName: "displayNotation"
  displayName: "Display Notation"
  description: "Human-readable mathematical notation"
  baseType: "String"
  required: true
  visibility: "PROMINENT"
  renderHints:
    searchable: true
    sortable: true
```

### Example 3: Enum Constrained Property

```yaml
difficultyLevel:
  apiName: "difficultyLevel"
  displayName: "Difficulty Level"
  description: "Problem difficulty on 1-5 scale"
  baseType: "Integer"
  required: true
  visibility: "NORMAL"
  renderHints:
    searchable: true
    selectable: true
    lowCardinality: true
  constraints:
    enum: [1, 2, 3, 4, 5]
```

### Example 4: Array Property

```yaml
solutionSteps:
  apiName: "solutionSteps"
  displayName: "Solution Steps"
  description: "Step-by-step solution procedure"
  baseType: "Array"
  arraySubtype: "String"
  required: false
  visibility: "NORMAL"
  constraints:
    range:
      min: 1
      max: 20
```

### Example 5: Struct Property (Polynomial Terms)

```yaml
terms:
  apiName: "terms"
  displayName: "Terms"
  description: "Individual terms of the polynomial"
  baseType: "Array"
  arraySubtype: "Struct"
  structSchema:
    coefficient:
      baseType: "Double"
      description: "Numeric coefficient"
    variableSymbol:
      baseType: "String"
      description: "Variable letter (nullable for constants)"
    exponent:
      baseType: "Integer"
      description: "Power of the variable"
  # Note: Max 10 fields per struct, depth 1 only
```

### Example 6: Vector Property (Semantic Embeddings)

```yaml
conceptEmbedding:
  apiName: "conceptEmbedding"
  displayName: "Concept Embedding"
  description: "768-dimensional semantic embedding for similarity search"
  baseType: "Vector"
  vectorDimension: 768
  # OSv2 only, max 2048 dimensions
  # Query via KNN only
```

### Example 7: Geopoint Property

```yaml
schoolLocation:
  apiName: "schoolLocation"
  displayName: "School Location"
  description: "Geographic coordinates of the school"
  baseType: "Geopoint"
  # Format: "latitude,longitude" (e.g., "37.5665,126.9780")
  # Or geohash (e.g., "wydm9qy3pv")
  # Must use WGS 84 coordinate reference system
```

---

## 7. anti_patterns

### Anti-Pattern 1: Float/Double as Primary Key

```yaml
# ❌ WRONG: Floating point as primary key
properties:
  equationValue:
    baseType: "Double"
    # Used as primary key - FORBIDDEN
    
# WHY IT'S WRONG:
# - Floating point comparison is imprecise
# - Cannot guarantee uniqueness
# - Primary key operations will fail

# ✅ CORRECT: Use String or Integer
properties:
  equationId:
    baseType: "String"
```

### Anti-Pattern 2: Deeply Nested Struct

```yaml
# ❌ WRONG: Attempting nested structs
terms:
  baseType: "Struct"
  structSchema:
    innerTerm:
      baseType: "Struct"  # NOT ALLOWED - depth > 1
      structSchema:
        value: ...

# WHY IT'S WRONG:
# - Struct depth limited to 1
# - Will fail validation

# ✅ CORRECT: Flatten structure or use multiple properties
termCoefficient:
  baseType: "Double"
termVariable:
  baseType: "String"
termExponent:
  baseType: "Integer"
```

### Anti-Pattern 3: Unindexed Property Used in Filters

```yaml
# ❌ WRONG: Filtering on non-searchable property
gradeLevel:
  baseType: "Integer"
  renderHints:
    searchable: false
# User tries to filter "show all Grade 8 problems"
# → Performance degradation or failure

# ✅ CORRECT: Enable searchable for filtered properties
gradeLevel:
  baseType: "Integer"
  renderHints:
    searchable: true
    selectable: true  # For aggregations
    lowCardinality: true  # Only 12 grades
```

### Anti-Pattern 4: Long as JavaScript-Exposed Identifier

```yaml
# ❌ WRONG: Long for IDs used in frontend
problemNumber:
  baseType: "Long"
  # Value: 9007199254740993
  # JavaScript max safe integer: 9007199254740991
  # → Precision loss in browser!

# ✅ CORRECT: Use String for large identifiers
problemNumber:
  baseType: "String"
  constraints:
    regex: "^[0-9]+$"
```

---

## 8. integration_points

```yaml
integration_points:
  objectType:
    relationship: "Property BELONGS TO ObjectType"
    constraints:
      - "Every ObjectType must have at least one property (primaryKey)"
      - "Property apiName unique within ObjectType scope"
      - "Maximum 2000 properties per ObjectType"
      
  sharedProperty:
    relationship: "Property CAN REFERENCE SharedProperty"
    mechanism: "sharedProperty field contains SharedProperty apiName"
    inheritance:
      - "Metadata inherited from SharedProperty"
      - "Local apiName preserved"
      - "Render hints can be overridden"
      
  constraints:
    relationship: "Property CAN HAVE Constraints"
    types: ["enum", "range", "regex", "rid", "uuid", "uniqueness"]
    
  renderHints:
    relationship: "Property HAS RenderHints"
    performance_impact:
      searchable: "adds raw index"
      sortable: "adds raw index (requires searchable)"
      selectable: "adds raw index (requires searchable)"
      
  actions:
    relationship: "Property USED IN Actions"
    restrictions:
      - "Float, Double, Decimal cannot be Action parameters"
      - "Vector arrays not supported in Actions"
      - "Max 10000 elements in primitive list parameters"
```

---

# Component 3: SharedProperty

## 1. official_definition

**Source**: https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview

> "A shared property is a property that can be used on multiple object types in your ontology. Shared properties allow for consistent data modeling across object types and centralized management of property metadata."

**Key Distinction**: While property *metadata* is shared across objects, the **underlying object data is NOT shared**. Each object type maintains its own data values.

**Visual Identifier**: Shared properties are denoted with a **globe icon** (🌐) in the UI.

---

## 2. semantic_definition

| Paradigm | Equivalent Concept | Mapping Notes |
|----------|-------------------|---------------|
| **OOP** | Abstract property / Trait field | Shared across implementing classes |
| **RDBMS** | Shared column definition | Same column spec across tables |
| **RDF/OWL** | owl:DatatypeProperty (domain-independent) | Property usable by multiple classes |
| **TypeScript** | Property in shared interface | Reused via interface implementation |
| **Design Patterns** | Template Method field | Consistent field across hierarchy |

**Semantic Role**: SharedProperty defines a **canonical property specification** that ensures semantic consistency across multiple ObjectTypes. It is the mechanism for implementing Interface contracts.

---

## 3. structural_schema

```yaml
$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "palantir-sharedproperty-schema"
title: "Palantir SharedProperty Definition"
type: object

required:
  - apiName
  - displayName
  - baseType

properties:
  apiName:
    type: string
    description: "Programmatic identifier"
    pattern: "^[a-z][a-zA-Z0-9]*$"
    examples: ["gradeLevel", "displayNotation", "difficultyLevel"]
    
  displayName:
    type: string
    description: "Human-readable name"
    examples: ["Grade Level", "Display Notation"]
    
  description:
    type: string
    description: "Explanatory text"
    examples: ["The target grade level for this educational content"]
    
  baseType:
    type: string
    description: "Data type (same options as Property)"
    
  rid:
    type: string
    description: "Auto-generated Resource Identifier"
    readOnly: true
    
  visibility:
    type: string
    enum: ["PROMINENT", "NORMAL", "HIDDEN"]
    default: "NORMAL"
    
  renderHints:
    type: object
    properties:
      searchable:
        type: boolean
      sortable:
        type: boolean
      selectable:
        type: boolean
        
  valueFormatting:
    type: object
    description: "Numeric, date/time, user ID formatting"
    
  typeClasses:
    type: array
    items:
      type: string
    description: "Additional metadata"
    
  constraints:
    type: object
    description: "Same constraint options as Property"
    
  # Interface relationship
  usedByInterfaces:
    type: array
    items:
      type: string
    description: "Interfaces requiring this SharedProperty"
    readOnly: true
    
  usedByObjectTypes:
    type: array
    items:
      type: string
    description: "ObjectTypes using this SharedProperty"
    readOnly: true
```

---

## 4. decision_tree

```
START: Should this Property be a SharedProperty?
│
├─► Q1: Is this property used by MORE THAN ONE ObjectType?
│   ├─ NO (only 1 ObjectType) → ❌ Keep as local Property
│   └─ YES → Continue
│
├─► Q2: Does the property have the SAME SEMANTIC MEANING across types?
│   ├─ NO (different meanings) → ❌ Keep as separate local Properties
│   │   Example: "date" means "creation date" in one, "due date" in another
│   └─ YES → Continue
│
├─► Q3: Do you need CENTRALIZED METADATA MANAGEMENT?
│   ├─ NO → Consider keeping local (less governance overhead)
│   └─ YES → Continue
│
├─► Q4: Are you building an INTERFACE?
│   ├─ YES → ✅ MUST create SharedProperty (Interface requirement)
│   └─ NO → Continue
│
├─► Q5: Is the property used by 3+ ObjectTypes?
│   ├─ YES → ✅ Strong case for SharedProperty
│   └─ NO (only 2 types) → ⚠️ Evaluate governance benefit vs overhead
│
├─► Q6: Will the property definition likely CHANGE?
│   ├─ YES (frequent updates) → ✅ SharedProperty (update once)
│   └─ NO (stable) → Either option acceptable
│
└─► RESULT: ✅ Create SharedProperty

EDGE CASES:
├─► "gradeLevel" across MathProblem, MathematicalConcept, Lesson, Assessment
│   └─ Decision: ✅ SharedProperty (4+ types, same meaning, centralized updates)
│
├─► "displayNotation" across LinearEquation, Polynomial, QuadraticEquation
│   └─ Decision: ✅ SharedProperty (Interface requirement for AlgebraicExpression)
│
├─► "solutionSteps" only on MathProblem
│   └─ Decision: ❌ Local Property (single type)
│
└─► "name" meaning differs: "conceptName" vs "userName" vs "schoolName"
    └─ Decision: ❌ Keep separate (different semantics)
```

---

## 5. validation_rules

```yaml
validation_rules:
  promotion_criteria:
    - rule: "minimum_usage_threshold"
      recommendation: "≥2 ObjectTypes"
      rationale: "SharedProperty overhead unjustified for single-type usage"
      
    - rule: "semantic_consistency"
      description: "Property must have identical meaning across all using types"
      error: "SharedProperty with inconsistent semantics causes confusion"
      
    - rule: "baseType_compatibility"
      description: "All using ObjectTypes must have compatible data sources"
      error: "baseType change breaks existing ObjectType mappings"

  interface_requirement:
    - rule: "interfaces_require_sharedproperties"
      description: "Interface schema is defined ONLY by SharedProperties"
      error: "Cannot add local Property to Interface definition"

  change_propagation:
    - rule: "breaking_changes_blocked"
      description: "Changes that would break any using ObjectType are rejected"
      examples:
        - "Changing baseType from String to Integer"
        - "Adding required constraint when existing data has nulls"
      error: "SharedProperty edit would break ObjectType: {objectTypeName}"

  detachment:
    - rule: "detachment_reverts_to_local"
      description: "Detaching SharedProperty converts to local Property"
      behavior: "Local apiName and metadata preserved"

  deletion:
    - rule: "deletion_cascades"
      description: "Deleting SharedProperty reverts all using Properties to local"
      warning: "All {count} ObjectTypes will have their properties reverted"

  naming:
    - rule: "consistent_naming"
      recommendation: "Use domain-specific, unambiguous names"
      good: ["gradeLevel", "difficultyLevel", "displayNotation"]
      bad: ["level", "name", "value"]  # Too generic
```

---

## 6. canonical_examples

### Example 1: gradeLevel (학년)

```yaml
# SharedProperty: Used across all K-12 educational content
apiName: "gradeLevel"
displayName: "Grade Level"
description: "Target grade level (1-12) for this educational content"
baseType: "Integer"
visibility: "PROMINENT"

renderHints:
  searchable: true
  selectable: true
  lowCardinality: true

constraints:
  range:
    min: 1
    max: 12

usedByObjectTypes:
  - "MathProblem"
  - "MathematicalConcept"
  - "Lesson"
  - "Assessment"
  - "LinearEquation"
  - "Polynomial"

usedByInterfaces:
  - "EducationalContent"
  - "MathematicalConcept"
```

### Example 2: displayNotation (표기법)

```yaml
apiName: "displayNotation"
displayName: "Display Notation"
description: "Human-readable mathematical or scientific notation"
baseType: "String"
visibility: "PROMINENT"

renderHints:
  searchable: true
  sortable: true

usedByObjectTypes:
  - "LinearEquation"
  - "Polynomial"
  - "QuadraticEquation"
  - "ChemicalFormula"

usedByInterfaces:
  - "AlgebraicExpression"
```

### Example 3: difficultyLevel (난이도)

```yaml
apiName: "difficultyLevel"
displayName: "Difficulty Level"
description: "Difficulty rating from 1 (easiest) to 5 (hardest)"
baseType: "Integer"
visibility: "NORMAL"

renderHints:
  searchable: true
  selectable: true
  lowCardinality: true

constraints:
  enum: [1, 2, 3, 4, 5]

usedByObjectTypes:
  - "MathProblem"
  - "LinearEquation"
  - "Polynomial"
  - "Assessment"

usedByInterfaces:
  - "EducationalContent"
```

### Example 4: curriculumStandard (교육과정 표준)

```yaml
apiName: "curriculumStandard"
displayName: "Curriculum Standard"
description: "Reference to national curriculum standard code"
baseType: "String"
visibility: "NORMAL"

renderHints:
  searchable: true

constraints:
  regex: "^[A-Z]{2}-[A-Za-z]+-[0-9]+-[A-Z]-[0-9]+$"
  # Example: "KR-Math-8-A-1" (Korea, Math, Grade 8, Algebra, Standard 1)

usedByObjectTypes:
  - "MathProblem"
  - "MathematicalConcept"
  - "Lesson"

usedByInterfaces:
  - "EducationalContent"
```

---

## 7. anti_patterns

### Anti-Pattern 1: SharedProperty for Single ObjectType

```yaml
# ❌ WRONG: Creating SharedProperty used by only one type
apiName: "polynomialDegree"
displayName: "Polynomial Degree"
baseType: "Integer"
usedByObjectTypes:
  - "Polynomial"  # Only one!

# WHY IT'S WRONG:
# - No reuse benefit
# - Added governance overhead
# - Unnecessary complexity

# ✅ CORRECT: Keep as local Property on Polynomial
# Only promote to SharedProperty when 2+ types need it
```

### Anti-Pattern 2: Generic Naming Without Context

```yaml
# ❌ WRONG: Overly generic SharedProperty name
apiName: "level"
displayName: "Level"
description: "A level value"  # Vague!

# WHY IT'S WRONG:
# - "level" could mean grade level, difficulty, game level...
# - Causes semantic confusion when reused
# - Different types may interpret differently

# ✅ CORRECT: Specific, domain-qualified names
apiName: "gradeLevel"
displayName: "Grade Level"
description: "Target grade level (1-12) for educational content"
```

### Anti-Pattern 3: Forcing Inconsistent Semantics

```yaml
# ❌ WRONG: Same SharedProperty for different meanings
apiName: "startDate"
# Used on:
#   - Employee: "Date employee began working"
#   - Project: "Date project was initiated"
#   - Subscription: "Date subscription became active"
# These have subtly different semantics!

# WHY IT'S WRONG:
# - Queries may conflate different concepts
# - Metadata (like "required") may not apply uniformly
# - Interface contracts become confusing

# ✅ CORRECT: Separate properties when semantics differ
# employeeStartDate, projectStartDate, subscriptionStartDate
# OR accept the abstraction if truly equivalent
```

### Anti-Pattern 4: Changing BaseType on Active SharedProperty

```yaml
# ❌ WRONG: Attempting baseType change
# Original:
apiName: "gradeLevel"
baseType: "Integer"

# Attempted change:
baseType: "String"  # To support "K" for kindergarten

# WHY IT'S WRONG:
# - Breaks all ObjectTypes using this SharedProperty
# - Data type mismatch with existing data
# - Edit is blocked by validation

# ✅ CORRECT: Plan baseType carefully upfront
# Or create new SharedProperty: "gradeLevelExtended" with String
```

---

## 8. integration_points

```yaml
integration_points:
  property:
    relationship: "Property REFERENCES SharedProperty"
    mechanism:
      - "Property.sharedProperty field contains SharedProperty apiName"
      - "Property inherits metadata from SharedProperty"
      - "Property retains local apiName (backward compatibility)"
    behavior:
      - "Render hint overrides apply when associating"
      - "Breaking changes to SharedProperty blocked if Properties would break"
      
  interface:
    relationship: "Interface REQUIRES SharedProperty"
    constraint: "Interface schema composed ONLY of SharedProperties"
    workflow:
      1: "Create SharedProperties first"
      2: "Create Interface referencing SharedProperties"
      3: "ObjectTypes implement Interface by having required SharedProperties"
      
  objectType:
    relationship: "ObjectType USES SharedProperty"
    mechanism:
      - "ObjectType Property references SharedProperty via sharedProperty field"
      - "ObjectType can map local property to SharedProperty during Interface implementation"
    governance:
      - "Changes to SharedProperty propagate to all using ObjectTypes"
      - "Detaching reverts to local Property"
      
  permissions:
    relationship: "SharedProperty HAS Permissions"
    requirements:
      - "Ontology Editor permission on SharedProperty to modify"
      - "Ontology Editor permission on ObjectType to associate SharedProperty"
    visibility:
      - "Usage tab shows all ObjectTypes using SharedProperty"
```

---

# K-12 Education Domain: Complete Modeling Example

## Interface Hierarchy

```yaml
# Interface: EducationalContent (최상위 교육 콘텐츠)
interfaces:
  EducationalContent:
    description: "Base interface for all educational content"
    sharedProperties:
      required:
        - gradeLevel
        - curriculumStandard
      optional:
        - difficultyLevel
        - createdAt
    implementedBy:
      - MathProblem
      - Lesson
      - Assessment

  MathematicalConceptInterface:
    description: "Interface for mathematical concepts"
    extends: EducationalContent
    sharedProperties:
      required:
        - displayNotation
      optional:
        - latexNotation
    implementedBy:
      - LinearEquation
      - Polynomial
      - MathematicalConcept

  AlgebraicExpression:
    description: "Interface for algebraic expressions"
    extends: MathematicalConceptInterface
    sharedProperties:
      required:
        - variableSymbol
        - degree
    implementedBy:
      - LinearEquation
      - Polynomial
```

## ObjectType Definitions Summary

| ObjectType | Primary Key | Title Key | Key Properties | Interfaces |
|------------|-------------|-----------|----------------|------------|
| **MathProblem** | problemId (UUID) | displayNotation | gradeLevel, difficultyLevel, solutionSteps, correctAnswer | EducationalContent |
| **LinearEquation** | equationId (UUID) | displayNotation | variableSymbol, coefficient, constantLeft, constantRight, solution | AlgebraicExpression |
| **Polynomial** | polynomialId (UUID) | displayNotation | degree, coefficients, terms (Struct array), isMonomial | AlgebraicExpression |
| **MathematicalConcept** | conceptId (natural key) | conceptName | conceptNameKo, definition, curriculumDomain, exampleNotations | MathematicalConceptInterface |
| **CurriculumUnit** | unitId (natural key) | unitName | gradeLevel, subject, sequence | EducationalContent |

## Link Types

```yaml
linkTypes:
  REQUIRES_CONCEPT:
    from: MathProblem
    to: MathematicalConcept
    cardinality: manyToMany
    description: "Problem requires understanding of concept"
    
  PREREQUISITE_OF:
    from: MathematicalConcept
    to: MathematicalConcept
    cardinality: manyToMany
    description: "Source concept must be learned before target"
    
  BELONGS_TO:
    from: MathProblem
    to: CurriculumUnit
    cardinality: manyToOne
    description: "Problem belongs to curriculum unit"
    
  TAUGHT_IN:
    from: MathematicalConcept
    to: CurriculumUnit
    cardinality: manyToMany
    description: "Concept is taught in curriculum unit"
```

## SharedProperty Registry

| apiName | displayName | baseType | usedBy Count | Interface Required |
|---------|-------------|----------|--------------|-------------------|
| gradeLevel | Grade Level | Integer | 6+ | EducationalContent |
| difficultyLevel | Difficulty Level | Integer | 4+ | EducationalContent |
| displayNotation | Display Notation | String | 4+ | MathematicalConceptInterface |
| curriculumStandard | Curriculum Standard | String | 4+ | EducationalContent |
| variableSymbol | Variable Symbol | String | 3+ | AlgebraicExpression |
| degree | Degree | Integer | 2+ | AlgebraicExpression |

---

# Validation Checklist (기계 실행 가능)

```yaml
# Pre-deployment validation checklist
validation_checklist:
  objectType:
    - check: "apiName starts with uppercase"
      rule: "/^[A-Z]/"
    - check: "apiName is PascalCase"
      rule: "/^[A-Z][a-z0-9]*([A-Z][a-z0-9]*)*$/"
    - check: "apiName not reserved word"
      forbidden: ["Ontology", "Object", "Property", "Link", "Relation", "Rid", "PrimaryKey", "TypeId"]
    - check: "primaryKey property exists"
    - check: "titleKey property exists"
    - check: "primaryKey baseType is allowed"
      allowed: ["String", "Integer", "Short"]
    - check: "maximum 2000 properties"
      
  property:
    - check: "apiName starts with lowercase"
      rule: "/^[a-z]/"
    - check: "apiName is camelCase"
      rule: "/^[a-z][a-zA-Z0-9]*$/"
    - check: "apiName unique within ObjectType"
    - check: "baseType is valid enum value"
    - check: "Struct depth is 1"
    - check: "Struct has max 10 fields"
    - check: "Vector dimension ≤ 2048"
    - check: "Array does not contain nulls"
    - check: "renderHints.sortable implies renderHints.searchable"
    - check: "renderHints.selectable implies renderHints.searchable"
    
  sharedProperty:
    - check: "Used by ≥2 ObjectTypes"
      warning: "SharedProperty overhead unjustified for single use"
    - check: "Semantic meaning consistent across types"
    - check: "apiName follows camelCase"
    - check: "Part of Interface if Interface exists for types"
```

---

# Source Documentation URLs

| Component | Official Documentation |
|-----------|----------------------|
| ObjectType Overview | https://www.palantir.com/docs/foundry/object-link-types/object-types-overview |
| Create ObjectType | https://www.palantir.com/docs/foundry/object-link-types/create-object-type |
| Property Overview | https://www.palantir.com/docs/foundry/object-link-types/properties-overview |
| Base Types | https://www.palantir.com/docs/foundry/object-link-types/base-types |
| Structs | https://www.palantir.com/docs/foundry/object-link-types/structs-overview |
| SharedProperty Overview | https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview |
| Create SharedProperty | https://www.palantir.com/docs/foundry/object-link-types/create-shared-property |
| Interfaces | https://www.palantir.com/docs/foundry/interfaces/interface-overview |
| Statuses | https://www.palantir.com/docs/foundry/object-link-types/metadata-statuses |
| Render Hints | https://www.palantir.com/docs/foundry/object-link-types/metadata-render-hints |
| Value Constraints | https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints |
| OSv2 Overview | https://www.palantir.com/docs/foundry/object-backend/overview |
| Scale Limits | https://www.palantir.com/docs/foundry/action-types/scale-property-limits |

---

## Conclusion

This reference document provides the **complete specification** for defining Palantir Ontology primitives in K-12 Education contexts. The key insights are:

1. **ObjectTypes** represent real-world entities with independent identity—LinearEquation and MathematicalConcept warrant ObjectType status, while Coefficient and Variable are better as Properties

2. **Properties** support **16+ baseTypes** with rich constraints; Struct (max 10 fields, depth 1) and Vector (max 2048 dimensions) enable complex data modeling

3. **SharedProperties** enable cross-type consistency and are **mandatory for Interfaces**; promote only when ≥2 types share semantically identical properties

4. **Naming conventions** are strict: ObjectType apiNames use PascalCase, Property apiNames use camelCase, with reserved words forbidden

5. **OSv2 limits** include 2000 properties per ObjectType, 70 datasources for MDO, and strict duplicate primary key validation