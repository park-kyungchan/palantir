# Palantir Ontology Decomposition Guide: Complete YAML Reference

**Version**: 1.0.0 | **Verification Date**: February 8, 2026 | **Target Consumer**: Claude-Opus-4.6

---

## COMPONENT 1: Ontology Decomposition Methodology

### 1.1 Official Definition

```yaml
official_definition:
  term: Ontology Decomposition
  source_urls:
    - https://www.palantir.com/docs/foundry/ontology/core-concepts
    - https://www.palantir.com/docs/foundry/ontology/overview
  verification_date: "2026-02-08"

  attribution: "Community-derived methodology — NOT from official Palantir documentation"
  note: |
    This decomposition methodology was synthesized using authentic Palantir Ontology
    concepts (ObjectType, LinkType, etc.) but the 8-phase sequential workflow, decision
    trees, indicator counts, and output templates are locally created. Palantir does NOT
    provide a formal multi-phase decomposition guide. Individual component concepts ARE
    transferable Palantir knowledge; the systematic workflow is OUR approach.

  definition_en: |
    Ontology Decomposition is the systematic methodology for analyzing an existing codebase,
    data model, or business domain and producing a complete set of Palantir Ontology definitions.
    It provides a step-by-step, decision-tree-driven process that an LLM or architect can follow
    to decompose any system into ObjectTypes, LinkTypes, ActionTypes, Functions, Interfaces,
    Automations, and Security policies.

  definition_kr: |
    온톨로지 분해(Ontology Decomposition)는 기존 코드베이스, 데이터 모델 또는 비즈니스 도메인을
    분석하여 완전한 Palantir 온톨로지 정의 세트를 생성하는 체계적인 방법론입니다.

  prerequisites:
    required_inputs:
      - source: "Source code repository or data model documentation"
        purpose: "Identify entities, relationships, mutations, and access patterns"
      - source: "Business domain glossary or stakeholder interviews"
        purpose: "Map technical concepts to business-meaningful Ontology names"
      - source: "Existing database schema (ERD, DDL, or ORM models)"
        purpose: "Identify primary keys, foreign keys, constraints, indexes"

    reference_documents:
      ontology_core: "palantir_ontology_1.md through palantir_ontology_7.md"
      osdk_patterns: "palantir_ontology_6.md (OSDK Reference)"
      security_model: "palantir_ontology_8.md (Security & Governance)"
```

### 1.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - source: "Database Normalization"
      mapping: "Decomposition normalizes business domain into Ontology primitives"
    - source: "Domain-Driven Design (DDD)"
      mapping: "Entity Discovery maps to Aggregate Roots; Interfaces map to Bounded Contexts"
    - source: "API Design"
      mapping: "Mutation Discovery maps to endpoint definitions; Functions map to resolvers"

  anti_concepts:
    - name: "Ad-hoc schema creation"
      contrast: "Decomposition is systematic and decision-tree-driven, not improvised"
    - name: "One-to-one table mirroring"
      contrast: "Decomposition considers business semantics, not just database structure"
```

---

## COMPONENT 2: Phase 1 — Entity Discovery (→ ObjectType candidates)

### 2.1 Official Definition

```yaml
official_definition:
  term: Entity Discovery
  description: "Identify all domain entities that should become ObjectTypes"
  output: "List of ObjectType candidates with primary keys and property maps"
```

### 2.2 Structural Schema

```yaml
structural_schema:
  step_1_scan_sources:
    description: "Systematically scan source code for entity indicators"
    patterns:
      - indicator: "Class with @Entity, @Table, @Document annotation (JPA/Hibernate/Mongo)"
        confidence: HIGH
        action: "Map to ObjectType"
      - indicator: "Class representing DDD Aggregate Root"
        confidence: HIGH
        action: "Map to ObjectType (primary entity, owns child entities)"
      - indicator: "Database table with PRIMARY KEY constraint"
        confidence: HIGH
        action: "Map to ObjectType"
      - indicator: "REST resource endpoint (/api/v1/{resource})"
        confidence: MEDIUM
        action: "Candidate ObjectType (verify it represents a noun, not a verb)"
      - indicator: "GraphQL type with ID field"
        confidence: HIGH
        action: "Map to ObjectType"
      - indicator: "Protobuf message with unique identifier"
        confidence: MEDIUM
        action: "Candidate if it represents a persistent entity"
      - indicator: "TypeScript interface/class with 'id' or 'uuid' field"
        confidence: MEDIUM
        action: "Candidate ObjectType (verify persistence and uniqueness)"

  step_2_classify_entities:
    description: "Distinguish ObjectTypes from ValueObjects and transient data"
    decision_tree:
      question_1: "Does this entity have a unique, stable identifier?"
      yes_path: "Continue to question_2"
      no_path: "NOT an ObjectType → consider as PropertyType (Struct) or skip"

      question_2: "Is this entity persisted (database, file, external system)?"
      yes_path: "Continue to question_3"
      no_path: "NOT an ObjectType → consider as Function input/output DTO"

      question_3: "Do users need to search, filter, or reference this entity independently?"
      yes_path: "STRONG ObjectType candidate"
      no_path: "Consider as embedded Struct property on parent ObjectType"

  step_3_define_primary_keys:
    description: "Select primary key strategy for each ObjectType"
    rules:
      - "Use existing database PK if unique and stable"
      - "Prefer String or Integer types (avoid Long for JavaScript precision)"
      - "Composite keys: concatenate into single String with delimiter"
      - "If no natural key exists: generate deterministic composite from business attributes"
    anti_patterns:
      - "Mutable fields as PK (email, name) → use synthetic ID instead"
      - "Auto-increment across multiple data sources → collision risk"
      - "Timestamp as sole PK → microsecond collision risk"

  step_4_map_properties:
    description: "Convert entity fields to Ontology PropertyTypes"
    type_mapping:
      java:
        "String": "String"
        "Integer/int": "Integer"
        "Long/long": "String  # Avoid JS precision loss for values > 1e15"
        "Double/double": "Double"
        "BigDecimal": "String  # Preserve precision"
        "Boolean/boolean": "Boolean"
        "LocalDate": "Date"
        "Instant/ZonedDateTime": "Timestamp"
        "UUID": "String"
        "List<T>": "Array<T>"
        "Map<K,V>": "Struct  # Convert to named struct type"
        "enum": "String  # Store enum name, not ordinal"
        "byte[]": "Attachment  # Binary data"
      typescript:
        "string": "String"
        "number (integer usage)": "Integer"
        "number (decimal usage)": "Double"
        "boolean": "Boolean"
        "Date": "Timestamp"
        "bigint": "String"
        "T[]": "Array<T>"
        "Record<K,V>": "Struct"
        "Buffer/Blob": "Attachment"
      python:
        "str": "String"
        "int": "Integer"
        "float": "Double"
        "bool": "Boolean"
        "datetime": "Timestamp"
        "date": "Date"
        "list[T]": "Array<T>"
        "dict": "Struct"
        "bytes": "Attachment"
    property_metadata:
      - "Set titleProperty to the most human-readable field (name, title, label)"
      - "Set descriptionProperty to the longest text field that describes the entity"
      - "Set status=ACTIVE for production-ready ObjectTypes"
      - "Set visibility=PROMINENT for core domain entities, HIDDEN for internal/system entities"
```

### 2.3 Decision Tree

```yaml
decision_tree:
  root:
    question: "Is this a candidate domain entity?"
    filters:
      has_unique_id: "Must have a stable, unique identifier"
      is_persisted: "Must be stored in database/file/external system"
      is_independently_queryable: "Users need to search/filter/reference independently"

  result_mapping:
    all_yes: "STRONG ObjectType candidate"
    no_unique_id: "PropertyType (Struct) or skip"
    not_persisted: "Function input/output DTO"
    not_independent: "Embedded Struct on parent ObjectType"
```

---

## COMPONENT 3: Phase 2 — Relationship Discovery (→ LinkType candidates)

### 3.1 Structural Schema

```yaml
structural_schema:
  step_1_scan_relationships:
    patterns:
      - indicator: "Foreign key constraint (FK → PK of another table)"
        confidence: HIGH
        action: "Map to LinkType (many-to-one direction matches FK direction)"
      - indicator: "Join table (table with only FK columns)"
        confidence: HIGH
        action: "Map to many-to-many LinkType"
      - indicator: "@ManyToOne / @OneToMany / @ManyToMany annotation"
        confidence: HIGH
        action: "Map to LinkType with matching cardinality"
      - indicator: "GraphQL field resolving to another type"
        confidence: HIGH
        action: "Map to LinkType"
      - indicator: "Object reference by ID (userId, orderId field)"
        confidence: MEDIUM
        action: "Candidate LinkType (verify target ObjectType exists)"
      - indicator: "Array of IDs referencing another entity"
        confidence: MEDIUM
        action: "Candidate many-to-many LinkType"

  step_2_classify_cardinality:
    decision_tree:
      question: "How many target objects can one source object link to?"
      one: "ONE_TO_ONE or MANY_TO_ONE → single link"
      many: "ONE_TO_MANY or MANY_TO_MANY → multi link"

    cardinality_mapping:
      ONE_TO_ONE:
        ontology: "LinkType with cardinality ONE on both sides"
        example: "Employee → EmployeeBadge"
      MANY_TO_ONE:
        ontology: "LinkType with cardinality MANY on source, ONE on target"
        example: "Order → Customer (many orders per customer)"
      ONE_TO_MANY:
        ontology: "Reverse of MANY_TO_ONE (same LinkType, opposite direction)"
        example: "Customer → Orders"
      MANY_TO_MANY:
        ontology: "LinkType with cardinality MANY on both sides"
        example: "Student ↔ Course"
        backing: "Requires a join dataset or Function-based link"

  step_3_define_link_metadata:
    required_fields:
      apiName: "camelCase, e.g., 'employeeOrders'"
      displayName: "Human-readable from source perspective, e.g., 'Orders'"
      reverseDisplayName: "Human-readable from target perspective, e.g., 'Customer'"
    optional_fields:
      description: "Business meaning of the relationship"
      visibility: "NORMAL (default) | HIDDEN (internal system links)"
```

### 3.2 Decision Tree

```yaml
decision_tree:
  root:
    question: "Is there a relationship between two ObjectTypes?"
    yes: "Determine cardinality"
    no: "Skip"

  cardinality:
    question: "How many target objects per source?"
    one: "ONE_TO_ONE or MANY_TO_ONE"
    many: "ONE_TO_MANY or MANY_TO_MANY"

  backing:
    question: "How is the relationship stored?"
    foreign_key: "FK-backed LinkType (most common)"
    join_table: "Many-to-many with backing dataset"
    computed: "Function-based link (dynamic resolution)"
```

---

## COMPONENT 4: Phase 3 — Mutation Discovery (→ ActionType candidates)

### 4.1 Structural Schema

```yaml
structural_schema:
  step_1_scan_mutations:
    patterns:
      - indicator: "POST/PUT/PATCH/DELETE REST endpoint"
        confidence: HIGH
        action: "Map to ActionType"
      - indicator: "GraphQL mutation"
        confidence: HIGH
        action: "Map to ActionType"
      - indicator: "Service method that modifies entity state"
        confidence: HIGH
        action: "Map to ActionType (one per distinct business operation)"
      - indicator: "Database INSERT/UPDATE/DELETE in repository layer"
        confidence: MEDIUM
        action: "Candidate — prefer business-level Actions over CRUD"
      - indicator: "Event handler that triggers state change"
        confidence: MEDIUM
        action: "Candidate ActionType (verify it's user-initiated, not automated)"
      - indicator: "Form submission handler"
        confidence: HIGH
        action: "Map to ActionType (parameters match form fields)"

  step_2_classify_action_complexity:
    decision_tree:
      question_1: "Does this mutation just create/update/delete a single ObjectType?"
      yes_path: "Simple ActionType (no Function rule needed, use built-in edit rules)"
      no_path: "Continue to question_2"

      question_2: "Does this mutation involve validation, business logic, or cross-object updates?"
      yes_path: "Complex ActionType (requires Function rule — TypeScript v2 or Python)"
      no_path: "Medium ActionType (built-in rules may suffice)"

    action_type_mapping:
      simple_create: "ActionType with createObjectRule"
      simple_update: "ActionType with modifyObjectRule"
      simple_delete: "ActionType with deleteObjectRule"
      business_operation: "ActionType with Function rule (@OntologyEditFunction)"
      batch_operation: "ActionType with Function rule iterating over ObjectSet"

  step_3_define_parameters:
    rules:
      - "Each form field / API parameter becomes an ActionType parameter"
      - "Use the same PropertyType as the corresponding ObjectType property"
      - "Mark parameters required/optional matching the API contract"
      - "Reference ObjectTypes by primary key (not embedded objects)"
    example:
      source_endpoint: "POST /api/orders { customerId, items[], shippingAddress }"
      action_definition:
        apiName: "createOrder"
        parameters:
          customerId: { type: "String", required: true }
          items: { type: "Array<Struct>", required: true }
          shippingAddress: { type: "String", required: true }
```

### 4.2 Decision Tree

```yaml
decision_tree:
  root:
    question: "Does this operation modify Ontology data?"
    yes: "ActionType candidate"
    no: "Query Function or read-only operation"

  complexity:
    simple_crud: "Built-in edit rules (createObject, modifyObject, deleteObject)"
    business_logic: "Function rule (@OntologyEditFunction)"
    multi_object: "Function rule with ObjectSet iteration"
```

---

## COMPONENT 5: Phase 4 — Logic Discovery (→ Function candidates)

### 5.1 Structural Schema

```yaml
structural_schema:
  step_1_scan_logic:
    patterns:
      - indicator: "Pure computation (no side effects, returns value)"
        confidence: HIGH
        action: "Map to @Function (query Function)"
      - indicator: "Complex validation logic used across multiple endpoints"
        confidence: HIGH
        action: "Map to @Function, referenced by ActionType validation"
      - indicator: "Data transformation or aggregation pipeline"
        confidence: MEDIUM
        action: "Candidate @Function with ObjectSet input"
      - indicator: "Scheduled computation (cron job, batch process)"
        confidence: MEDIUM
        action: "Candidate @Function called by Automation"
      - indicator: "Business rule evaluation (pricing, scoring, eligibility)"
        confidence: HIGH
        action: "Map to @Function (can be used by AIP Logic or ActionType)"

  step_2_choose_function_type:
    decision_tree:
      question_1: "Does this logic modify Ontology data?"
      yes_path: "@OntologyEditFunction (used as ActionType rule)"
      no_path: "Continue to question_2"

      question_2: "Does this logic return computed data or aggregations?"
      yes_path: "@Function (Query function — called by OSDK or Workshop)"
      no_path: "Continue to question_3"

      question_3: "Is this logic a natural-language-describable business rule?"
      yes_path: "AIP Logic Function (no-code, LLM-powered)"
      no_path: "@Function with explicit implementation"

  step_3_choose_runtime:
    options:
      typescript_v2:
        when: "Need OSDK access, npm libraries, API calls, modern JS"
        benefits: "Full Node.js runtime, NPM ecosystem, fastest iteration"
      python:
        when: "Need data science libs, ML inference, complex transforms"
        benefits: "Pandas, NumPy, scikit-learn, full Python ecosystem"
      aip_logic:
        when: "Simple business rules, non-technical authors, natural language"
        benefits: "No-code, prompt-based, quick iteration"
```

### 5.2 Decision Tree

```yaml
decision_tree:
  root:
    question: "What type of logic is this?"
    modifies_data: "@OntologyEditFunction"
    returns_data: "@Function (Query)"
    natural_language_rule: "AIP Logic Function"
    complex_implementation: "@Function with explicit code"
```

---

## COMPONENT 6: Phase 5 — Interface Discovery (→ Interface candidates)

### 6.1 Structural Schema

```yaml
structural_schema:
  step_1_scan_interfaces:
    patterns:
      - indicator: "Multiple ObjectTypes with identical property subsets"
        confidence: HIGH
        action: "Extract shared properties into Interface"
        example: "Employee, Contractor, Vendor all have (name, email, phone) → Contactable interface"
      - indicator: "Code that operates on multiple entity types polymorphically"
        confidence: HIGH
        action: "Create Interface that all target ObjectTypes implement"
      - indicator: "Abstract base class or shared mixin in source code"
        confidence: MEDIUM
        action: "Candidate Interface (only if shared properties are semantically equivalent)"
      - indicator: "UI component that renders different entity types identically"
        confidence: HIGH
        action: "Create Interface for the common display contract"

  step_2_define_interface:
    rules:
      - "Interface properties must be semantically identical across implementing ObjectTypes"
      - "Property apiNames in the Interface need not match ObjectType apiNames (use property mapping)"
      - "Links can also be part of an Interface definition"
      - "ObjectTypes can implement multiple Interfaces"
    anti_patterns:
      - "Creating an Interface for only one ObjectType → unnecessary indirection"
      - "Forcing semantically different properties to share an Interface → data model confusion"
```

### 6.2 Decision Tree

```yaml
decision_tree:
  root:
    question: "Do multiple ObjectTypes share identical property subsets?"
    yes: "Extract into Interface"
    no: "Skip"

  validation:
    question: "Are the shared properties semantically equivalent across types?"
    yes: "Create Interface"
    no: "Do NOT create Interface — coincidental similarity is not a contract"
```

---

## COMPONENT 7: Phase 6 — Automation & Trigger Discovery

### 7.1 Structural Schema

```yaml
structural_schema:
  step_1_scan_triggers:
    patterns:
      - indicator: "Cron job / scheduled task"
        confidence: HIGH
        action: "Map to Automation with schedule trigger"
      - indicator: "Event listener (object created/modified/deleted)"
        confidence: HIGH
        action: "Map to Automation with ObjectChanged trigger"
      - indicator: "Webhook handler (external system notifies your system)"
        confidence: MEDIUM
        action: "Map to Automation with webhook trigger or Action-based trigger"
      - indicator: "Email/notification trigger on data change"
        confidence: HIGH
        action: "Map to Automation with notification action"
      - indicator: "Workflow state machine (status transitions with side effects)"
        confidence: HIGH
        action: "Map to Rules Engine conditions + Automation triggers"

  step_2_map_to_automation_type:
    decision_tree:
      question_1: "Is this triggered by a schedule (time-based)?"
      yes_path: "Schedule-based Automation (cron expression)"
      no_path: "Continue to question_2"

      question_2: "Is this triggered by an Ontology data change?"
      yes_path: "ObjectChanged Automation (object create/modify/delete)"
      no_path: "Continue to question_3"

      question_3: "Is this triggered by an external event?"
      yes_path: "Webhook or API-triggered Action"
      no_path: "Manual trigger (ActionType invoked by user)"
```

### 7.2 Decision Tree

```yaml
decision_tree:
  root:
    question: "What triggers this process?"
    schedule: "Schedule-based Automation"
    data_change: "ObjectChanged Automation"
    external_event: "Webhook or API-triggered Action"
    user_action: "Manual trigger (ActionType)"
```

---

## COMPONENT 8: Phase 7 — Security Mapping

### 8.1 Structural Schema

```yaml
structural_schema:
  step_1_scan_access_patterns:
    patterns:
      - indicator: "@Secured / @PreAuthorize / role-based annotation"
        confidence: HIGH
        action: "Map to RBAC roles on ObjectType/ActionType"
      - indicator: "Row-level security filter (WHERE tenant_id = ?)"
        confidence: HIGH
        action: "Map to Object Security Policy or Restricted View"
      - indicator: "Column-level access control (field-level permissions)"
        confidence: HIGH
        action: "Map to Property Security Policy"
      - indicator: "Data classification labels (PII, HIPAA, CONFIDENTIAL)"
        confidence: HIGH
        action: "Map to Markings (mandatory or classification)"
      - indicator: "Multi-tenant data isolation"
        confidence: HIGH
        action: "Map to Organizations + Markings"

  step_2_map_security_model:
    mapping_table:
      "Role-based access (admin, editor, viewer)": "RBAC roles on Project/ObjectType"
      "Row-level filter (tenant isolation)": "Object Security Policy (see palantir_ontology_8.md §10)"
      "Column-level restriction (PII masking)": "Property Security Policy"
      "Data classification (CONFIDENTIAL, etc.)": "Marking (mandatory or classification)"
      "Attribute-based access (department, region)": "Granular Policy with user attributes"
      "Approval workflow for schema changes": "Ontology Proposals with reviewer assignment"
```

### 8.2 Decision Tree

```yaml
decision_tree:
  root:
    question: "What type of access control exists in the source system?"
    role_based: "RBAC roles on ObjectType/ActionType"
    row_level: "Object Security Policy"
    column_level: "Property Security Policy"
    classification: "Markings (mandatory or classification)"
    multi_tenant: "Organizations + Object Security Policy"
    attribute_based: "Granular Policy templates"
```

---

## COMPONENT 9: Phase 8 — Decomposition Output Template

### 9.1 Structural Schema

```yaml
structural_schema:
  decomposition_output:
    description: "Final output format for a complete Ontology decomposition"

    template:
      metadata:
        project_name: "{project}"
        source_repository: "{repo_url}"
        decomposition_date: "{date}"
        decomposition_version: "1.0"

      object_types:
        - apiName: "{PascalCase}"
          displayName: "{Human Readable Name}"
          description: "{Business purpose}"
          primaryKey: ["{pkField}"]
          titleProperty: "{displayField}"
          source_entity: "{SourceClass or table name}"
          properties:
            "{propApiName}":
              type: "{OntologyType}"
              description: "{purpose}"
              source_field: "{original field name}"
          status: "ACTIVE | EXPERIMENTAL"

      link_types:
        - apiName: "{camelCase}"
          source: "{SourceObjectType}"
          target: "{TargetObjectType}"
          cardinality: "ONE_TO_ONE | MANY_TO_ONE | MANY_TO_MANY"
          source_relationship: "{FK column or join table}"
          displayName: "{from source perspective}"
          reverseDisplayName: "{from target perspective}"

      action_types:
        - apiName: "{camelCase}"
          description: "{what this mutation does}"
          parameters: ["{param: type}"]
          edit_rules: ["{rule description}"]
          source_endpoint: "{original API endpoint or service method}"
          function_rule: "{functionApiName or null}"

      functions:
        - apiName: "{camelCase}"
          type: "Query | OntologyEdit | AIPLogic"
          runtime: "typescript_v2 | python | aip_logic"
          description: "{what this function computes or does}"
          source_logic: "{original class/method}"

      interfaces:
        - apiName: "{PascalCase}"
          shared_properties: ["{prop1}", "{prop2}"]
          implementing_types: ["{ObjectType1}", "{ObjectType2}"]
          source_pattern: "{original abstract class or shared mixin}"

      automations:
        - name: "{descriptive name}"
          trigger: "schedule | object_changed | manual"
          action: "{Function to call or notification to send}"
          source_trigger: "{original cron job or event handler}"

      security:
        markings: ["{marking definitions}"]
        rbac_roles: ["{role: permissions}"]
        object_policies: ["{row-level policy definitions}"]
        property_policies: ["{column-level policy definitions}"]
        source_access_model: "{original RBAC/ACL description}"
```

---

## Decomposition Workflow Summary

```yaml
workflow_summary:
  phases:
    1: "Entity Discovery → ObjectType candidates (scan classes, tables, APIs)"
    2: "Relationship Discovery → LinkType candidates (scan FKs, joins, references)"
    3: "Mutation Discovery → ActionType candidates (scan endpoints, service methods)"
    4: "Logic Discovery → Function candidates (scan business rules, computations)"
    5: "Interface Discovery → Interface candidates (scan shared property sets)"
    6: "Automation Discovery → Automation candidates (scan triggers, cron jobs)"
    7: "Security Mapping → Security definitions (scan ACLs, roles, classifications)"
    8: "Output Assembly → Complete Ontology decomposition YAML"

  quality_checklist:
    - "Every ObjectType has a clear primary key strategy"
    - "Every relationship is captured as a LinkType (no orphaned FK references)"
    - "Every user-facing mutation is an ActionType (not raw database write)"
    - "Complex business logic lives in Functions (not embedded in ActionTypes)"
    - "Shared property sets are extracted into Interfaces"
    - "All access control patterns are mapped to Markings/RBAC/Policies"
    - "Cross-references: every ObjectType references its Section 1-19 definition"
    - "Naming: all apiNames follow conventions (PascalCase for types, camelCase for properties/actions)"
```

---

## Validation Rules

```yaml
validation_rules:
  - id: "DEC-VAL-001"
    name: "Primary Key Required"
    severity: ERROR
    check: "Every ObjectType must have exactly one primary key property"

  - id: "DEC-VAL-002"
    name: "Orphaned Foreign Key"
    severity: WARNING
    check: "Every FK reference in source code should have a corresponding LinkType"

  - id: "DEC-VAL-003"
    name: "Mutation Coverage"
    severity: WARNING
    check: "Every user-facing write endpoint should have a corresponding ActionType"

  - id: "DEC-VAL-004"
    name: "Interface Minimum Implementors"
    severity: WARNING
    check: "Every Interface should have at least 2 implementing ObjectTypes"

  - id: "DEC-VAL-005"
    name: "Security Coverage"
    severity: WARNING
    check: "Every sensitive property should have a marking or security policy"

  - id: "DEC-VAL-006"
    name: "Naming Convention"
    severity: ERROR
    check: "ObjectType/Interface apiNames are PascalCase; property/action/link apiNames are camelCase"
    forbidden: [ontology, object, property, link, relation, rid, primaryKey, typeId]
```

---

## Anti-Patterns

```yaml
anti_patterns:
  - id: "DEC-ANTI-001"
    name: "One-to-One Table Mirroring"
    bad: "Creating an ObjectType for every database table including junction/metadata tables"
    good: "Only create ObjectTypes for business entities that users query independently"

  - id: "DEC-ANTI-002"
    name: "CRUD-Only Actions"
    bad: "createUser, updateUser, deleteUser as separate ActionTypes for simple fields"
    good: "Business-meaningful Actions like 'onboardEmployee', 'transferDepartment', 'deactivateAccount'"

  - id: "DEC-ANTI-003"
    name: "Premature Interface Extraction"
    bad: "Creating Interface for properties shared by only one ObjectType"
    good: "Wait until at least 2 ObjectTypes share semantically identical properties"

  - id: "DEC-ANTI-004"
    name: "Ignoring Security Mapping"
    bad: "Decomposing entities and mutations without mapping access control"
    good: "Phase 7 (Security Mapping) is mandatory — every sensitive field needs a policy"

  - id: "DEC-ANTI-005"
    name: "Mutable Primary Key"
    bad: "Using email or username as ObjectType primary key"
    good: "Use stable synthetic ID (UUID, auto-increment, composite hash)"
```

---

## Integration Points

```yaml
integration_points:
  dependencies:
    palantir_ontology_1: "ObjectType definitions — target output of Phase 1 (Entity Discovery)"
    palantir_ontology_2: "LinkType definitions — target output of Phase 2 (Relationship Discovery)"
    palantir_ontology_3: "ActionType/Function — target output of Phases 3-4 (Mutation/Logic Discovery)"
    palantir_ontology_4: "Dataset/Pipeline — backing data structure for ObjectTypes"
    palantir_ontology_5: "ObjectSet operations — query patterns inform ActionType parameters"
    palantir_ontology_6: "OSDK patterns — client-side consumption of decomposed types"
    palantir_ontology_7: "Versioning/Governance — proposal workflow for schema changes"
    palantir_ontology_8: "Security model — target output of Phase 7 (Security Mapping)"

  reverse_dependencies:
    code_generation: "Decomposition output feeds OSDK code generation"
    workshop: "Decomposition output feeds Workshop application building"
    aip_agents: "Decomposition output feeds AIP Agent/Logic configuration"
```

---

## Cross-Document Reference Map

```yaml
cross_references:
  this_document: "palantir_ontology_9.md — Ontology Decomposition Guide (v1.0)"

  related_documents:
    palantir_ontology_1: "ObjectType — Phase 1 output target"
    palantir_ontology_2: "LinkType — Phase 2 output target"
    palantir_ontology_3: "ActionType/Function — Phases 3-4 output target"
    palantir_ontology_4: "Dataset/Pipeline — backing data context"
    palantir_ontology_5: "ObjectSet — query pattern context"
    palantir_ontology_6: "OSDK — client consumption context"
    palantir_ontology_7: "Versioning — governance workflow for schema output"
    palantir_ontology_8: "Security — Phase 7 output target"

  source_document: "Ontology.md (v4.0) Section 20 — Decomposition Guide"
```

---

**Document Version:** 1.0
**Date:** 2026-02-08
**Source:** Ontology.md v4.0, Section 20 (Decomposition Guide, lines 3308-3812)
**Coverage:** 8-phase decomposition methodology (Entity → Relationship → Mutation → Logic → Interface → Automation → Security → Output), decision trees per phase, type mapping tables (Java/TypeScript/Python), YAML output template, validation rules, anti-patterns
