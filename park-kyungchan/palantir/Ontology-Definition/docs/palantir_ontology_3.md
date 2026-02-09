# Palantir Ontology Kinetic Primitives: Complete YAML Reference

**Version**: 1.0.0 | **Verification Date**: February 5, 2026 | **Target Consumer**: Claude-Opus-4.5

---

## COMPONENT 1: ActionType

### 1.1 Official Definition

```yaml
official_definition:
  term: ActionType
  source_urls:
    - https://www.palantir.com/docs/foundry/action-types/overview
    - https://www.palantir.com/docs/foundry/action-types/rules
    - https://www.palantir.com/docs/foundry/action-types/parameter-overview
    - https://www.palantir.com/docs/foundry/action-types/submission-criteria
  verification_date: "2026-02-05"
  
  definition_en: |
    An ActionType is the schema definition of a set of changes or edits to objects, 
    property values, and links that a user can execute as a single atomic transaction.
    
  definition_kr: |
    ActionType(액션 타입)은 사용자가 단일 원자적 트랜잭션으로 실행할 수 있는 객체, 
    속성 값, 링크에 대한 변경 세트의 스키마 정의입니다.

  relationship:
    actiontype: "Schema/template defining what changes are possible"
    action: "Single execution instance applying the ActionType"

  rule_types_complete_list:
    - CREATE_OBJECT: "Creates new object with required primary key"
    - MODIFY_OBJECT: "Updates existing object properties"
    - CREATE_OR_MODIFY_OBJECT: "Upsert pattern based on object reference"
    - DELETE_OBJECT: "Removes object (links implicitly removed)"
    - CREATE_LINK: "Creates many-to-many links only"
    - DELETE_LINK: "Removes many-to-many links only"
    - FUNCTION_RULE: "Delegates to Ontology Edit Function (exclusive)"
    - CREATE_OBJECT_OF_INTERFACE: "Polymorphic object creation"
    - MODIFY_OBJECT_OF_INTERFACE: "Polymorphic property update"
    - DELETE_OBJECT_OF_INTERFACE: "Polymorphic object deletion"

  parameter_types_complete_list:
    - STRING
    - INTEGER
    - LONG
    - SHORT
    - FLOAT
    - DOUBLE
    - DECIMAL
    - BYTE
    - BOOLEAN
    - DATE
    - TIMESTAMP
    - OBJECT
    - OBJECT_SET
    - INTERFACE_REFERENCE
    - ATTACHMENT
    - ARRAY
    - STRUCT
    - GEOPOINT
    - GEOSHAPE
    - MEDIA
    - VECTOR

  value_source_options:
    - FROM_PARAMETER
    - OBJECT_PROPERTY
    - STATIC_VALUE
    - CURRENT_USER
    - CURRENT_TIME

  transaction_semantics:
    atomicity: true
    description: "All rules in an Action execute atomically (all-or-nothing)"
```

### 1.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - source: "Database Stored Procedure"
      mapping: "ActionType defines the procedure; Action executes it"
    - source: "GraphQL Mutation"
      mapping: "ActionType is mutation definition; Action is execution"

  anti_concepts:
    - name: "Query"
      contrast: "Queries read data; ActionTypes write/mutate data"
```

### 1.3 Structural Schema

```yaml
structural_schema:
  $schema: "https://json-schema.org/draft/2020-12/schema"
  $id: "https://palantir.com/ontology/action-type/v1"
  title: "ActionType"
  type: object
  required: [apiName, displayName, objectTypes, rules]
  
  properties:
    apiName:
      type: string
      pattern: "^[a-z][a-zA-Z0-9]*$"
    displayName:
      type: string
    objectTypes:
      type: array
      items: { type: string }
    parameters:
      type: array
    rules:
      type: array
    submissionCriteria:
      type: array
    sideEffects:
      type: object
      properties:
        notifications: { type: array }
        webhooks: { type: array }
    actionLog:
      type: object
      properties:
        enabled: { type: boolean }
        includeParameters: { type: boolean }
```

### 1.4 Decision Tree

```yaml
decision_tree:
  root:
    question: "Does operation modify Ontology data?"
    yes: "Is logic simple CRUD? → Rule-based ActionType"
    no: "Use Query Function"
  
  function_vs_rules:
    use_rules_when:
      - "Simple create/modify/delete operations"
      - "Straightforward property mapping"
    use_function_when:
      - "Complex business logic"
      - "Reading multiple objects to determine changes"
      - "Graph traversal required"

  rule_type_selection:
    many_to_many_link: "CREATE_LINK or DELETE_LINK"
    foreign_key_link: "MODIFY_OBJECT (edit FK property)"
    complex_logic: "FUNCTION_RULE (exclusive)"
```

### 1.5 Validation Rules

```yaml
validation_rules:
  - id: "ACT-VAL-001"
    name: "API Name Format"
    severity: ERROR
    check: "/^[a-z][a-zA-Z0-9]*$/.test(apiName)"
    
  - id: "ACT-VAL-002"
    name: "Forbidden Words"
    severity: ERROR
    forbidden: [ontology, object, property, link, relation, rid, primaryKey, typeId]
    
  - id: "ACT-VAL-003"
    name: "Function Rule Exclusivity"
    severity: ERROR
    check: "FUNCTION_RULE must be only rule when present"
    
  - id: "ACT-VAL-004"
    name: "Primary Key Required"
    severity: ERROR
    check: "CREATE_OBJECT must include primary key"
    
  - id: "ACT-VAL-005"
    name: "Link Cardinality"
    severity: ERROR
    check: "CREATE_LINK/DELETE_LINK only for many-to-many"
```

### 1.6 Canonical Examples

```yaml
canonical_examples:
  k12_education:
    addLearningRecord:
      displayName: "Add Learning Record"
      description_kr: "학생 학습 기록 추가"
      parameters:
        - { apiName: student, type: OBJECT, required: true }
        - { apiName: concept, type: OBJECT, required: true }
        - { apiName: activityType, type: STRING, constraints: [ONE_OF] }
        - { apiName: durationMinutes, type: INTEGER, constraints: [RANGE: 1-480] }
        - { apiName: masteryScore, type: DOUBLE, constraints: [RANGE: 0-1] }
      rules:
        - ruleType: CREATE_OBJECT
          objectType: learningRecord
          propertyEdits:
            - { property: recordId, valueSource: FROM_PARAMETER, isPrimaryKey: true }
            - { property: recordedAt, valueSource: CURRENT_TIME }
            - { property: recordedBy, valueSource: CURRENT_USER }

    linkPrerequisiteConcept:
      displayName: "Link Prerequisite Concept"
      description_kr: "선수 개념 연결 추가"
      parameters:
        - { apiName: targetConcept, type: OBJECT }
        - { apiName: prerequisiteConcept, type: OBJECT }
      rules:
        - ruleType: CREATE_LINK
          linkType: conceptPrerequisites
      submissionCriteria:
        - condition: "targetConcept != prerequisiteConcept"
          failureMessage_kr: "개념은 자기 자신의 선수 개념이 될 수 없습니다"

    unlinkPrerequisiteConcept:
      displayName: "Unlink Prerequisite Concept"
      description_kr: "선수 개념 연결 삭제"
      rules:
        - ruleType: DELETE_LINK
          linkType: conceptPrerequisites

    modifyConceptDifficulty:
      displayName: "Modify Concept Difficulty"
      description_kr: "개념 난이도 수정"
      parameters:
        - { apiName: newDifficultyLevel, type: INTEGER, constraints: [RANGE: 1-10] }
      rules:
        - ruleType: MODIFY_OBJECT
          objectType: concept
      submissionCriteria:
        - condition: "user in curriculum-editors group"
          failureMessage_kr: "교육과정 편집자만 수정 가능"

    gradeQuizAndSaveResults:
      displayName: "Grade Quiz And Save Results"
      description_kr: "퀴즈 채점 및 결과 저장"
      rules:
        - ruleType: FUNCTION_RULE
          functionReference:
            functionApiName: gradeQuizAndSaveResultsFunction
            autoUpgrade: true
```

### 1.7 Anti-Patterns

```yaml
anti_patterns:
  - id: "ACT-ANTI-001"
    name: "Mixing FUNCTION_RULE with Other Rules"
    bad: "FUNCTION_RULE + CREATE_OBJECT together"
    good: "FUNCTION_RULE alone handles all edits"
    
  - id: "ACT-ANTI-002"
    name: "Using CREATE_LINK for Foreign Key Links"
    bad: "CREATE_LINK for one-to-many relationship"
    good: "MODIFY_OBJECT to edit FK property"
```

### 1.8 Integration Points

```yaml
integration_points:
  dependencies: [ObjectType, LinkType, PropertyType, Interface, Function]
  reverse_dependencies: [Workshop, Object Explorer, Quiver, API Gateway, Action Log]
```

### 1.9 Code Pattern Identification

> Source: Ontology.md Section 5 — Code Pattern Identification Rules

```yaml
actiontype_identification_rules:
  - pattern: "Command class with execute() method"
    mapping: ActionType
    rule_type: "Based on operation complexity"

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

### 1.10 AIP Logic Block Types

> Source: Ontology.md Section 17 — AIP Logic Function Configuration

```yaml
aip_logic_blocks:
  description: "AIP Logic functions are composed of blocks — discrete execution steps that form a pipeline"

  block_types:
    use_llm:
      description: "Sends a prompt to a language model with configured tools and context"
      capabilities: "Text generation, classification, extraction, reasoning"
      tools_available: ["Apply Actions", "Call Function", "Query Objects", "Calculator"]
      configuration: "Prompt template + model selection + tool bindings + output format"

    apply_action:
      description: "Executes an Ontology ActionType within the logic flow"
      capabilities: "Create, modify, or delete objects as part of the function execution"
      use_case: "Side effects within an AIP Logic pipeline (e.g., update status after classification)"

    execute_function:
      description: "Calls a Foundry Function (TypeScript v2 or Python) for computation"
      capabilities: "Delegate complex logic to typed functions; receive structured results"
      use_case: "Hybrid pattern — LLM for reasoning, Function for precise computation"

    conditionals:
      description: "Branching logic based on variable values from previous blocks"
      capabilities: "If/else flow control within the function pipeline"
      use_case: "Route logic based on LLM classification output or intermediate values"

    loops:
      description: "Iteration over object sets or lists"
      capabilities: "Process multiple objects with the same logic block sequence"
      use_case: "Batch classification, iterative enrichment of object collections"

    create_variable:
      description: "Stores intermediate computation results for use in later blocks"
      capabilities: "Named variables accessible by subsequent blocks in the pipeline"
      use_case: "Accumulate context across blocks; store LLM output for conditional branching"

  llm_tool_types:
    description: "Tools that the LLM can invoke during a 'Use LLM' block"
    apply_actions:
      description: "LLM can trigger Ontology Actions based on reasoning"
      example: "LLM classifies a ticket as CRITICAL → triggers 'escalateTicket' Action"
    call_function:
      description: "LLM can invoke Foundry Functions to get computed results"
      example: "LLM asks Function to calculate risk score → uses result in response"
    query_objects:
      description: "LLM can search and retrieve Ontology objects for context"
      example: "LLM queries related customer objects to inform support ticket response"
    calculator:
      description: "LLM can perform arithmetic computations"
      example: "LLM computes discount percentage based on order total and loyalty tier"

  composition_pattern:
    description: "Blocks are composed sequentially with branching via Conditionals"
    example_pipeline:
      1: "Create Variable: load input object properties"
      2: "Use LLM: classify the input (tools: Query Objects for context)"
      3: "Conditionals: branch on classification result"
      4: "Apply Action: update object status based on classification"
      5: "Use LLM: generate summary of action taken"
```

---

## COMPONENT 2: Function

### 2.1 Official Definition

```yaml
official_definition:
  term: Function
  source_urls:
    - https://www.palantir.com/docs/foundry/functions/edits-overview/
    - https://www.palantir.com/docs/foundry/functions/typescript-v2-ontology-edits
    - https://www.palantir.com/docs/foundry/functions/python-ontology-edits
  verification_date: "2026-02-05"

  function_types:
    query_function:
      description_kr: "읽기 전용 함수"
      capabilities: [read properties, filter ObjectSets, traverse links, aggregations]
      constraints: [cannot create/update/delete]
      
    ontology_edit_function:
      description_kr: "온톨로지 편집 함수"
      capabilities: [create objects, update properties, manage links, delete objects]
      constraints: [must be Action-backed to apply, search returns stale data during execution]

  critical_caveat: |
    "Changes to objects and links are propagated to the object set APIs after your 
    function has finished executing." — Palantir Docs
```

### 2.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - { source: "SQL Stored Procedure", mapping: "Encapsulates reusable logic" }
    - { source: "GraphQL Resolver", mapping: "Query resolves fields; Edit handles mutations" }
    - { source: "Serverless Lambda", mapping: "Executes on-demand in managed environment" }
```

### 2.3 Structural Schema

```yaml
structural_schema:
  languages:
    typescript_v2:
      imports:
        - "@osdk/client"
        - "@osdk/functions"
        - "@ontology/sdk"
      query_function: |
        export const config = { apiName: "myFunction" };
        export default function myFunction(client: Client): ReturnType { }
      edit_function: |
        type OntologyEdit = Edits.Object<MyType>;
        export default function myEdit(client: Client): OntologyEdit[] {
          const batch = createEditBatch<OntologyEdit>(client);
          batch.create(MyType, { id: "123" });
          batch.update(obj, { property: "value" });
          batch.delete(obj);
          batch.link(source, "linkName", target);
          return batch.getEdits();
        }

    typescript_v1:
      imports:
        - "@foundry/functions-api"
        - "@foundry/ontology-api"
      query_function: |
        @Function()
        public myFunction(): ReturnType { }
      edit_function: |
        @Edits(ObjectType1, ObjectType2)
        @OntologyEditFunction()
        public myEdit(): void {
          object.property = "value";
        }

    python:
      imports:
        - "functions.api"
        - "ontology_sdk"
      query_function: |
        @function(api_name="myFunction")
        def my_function() -> ReturnType:
            pass
      edit_function: |
        @function(edits=[ObjectType])
        def my_edit() -> list[OntologyEdit]:
            edits = FoundryClient().ontology.edits()
            edits.objects.MyType.create(pk)
            return edits.get_edits()
```

### 2.4 Decision Tree

```yaml
decision_tree:
  root:
    question: "Modify Ontology data?"
    yes: "Ontology Edit Function"
    no: "Query Function"
    
  language_selection:
    typescript_v2:
      - "Recommended for new projects"
      - "Explicit edit returns with type safety"
    typescript_v1:
      - "Debugger support"
      - "Simpler void return"
    python:
      - "DataFrame support"
      - "ML/data science workflows"
```

### 2.5 Validation Rules

```yaml
validation_rules:
  - id: "FUNC-VAL-001"
    check: "apiName is camelCase"
    severity: ERROR
    
  - id: "FUNC-VAL-002"
    check: "Edit functions declare @Edits types"
    severity: ERROR
    
  - id: "FUNC-VAL-003"
    check: "Max 3 search arounds per function"
    severity: ERROR
```

### 2.6 Canonical Examples

```yaml
canonical_examples:
  k12_education:
    detectCircularPrerequisites:
      title_kr: "선수 개념 순환 검사"
      function_type: QUERY
      language: TYPESCRIPT_V2
      code: |
        export default async function detectCircularPrerequisites(
            client: Client,
            targetConcept: Osdk.Instance<Concept>,
            potentialPrerequisite: Osdk.Instance<Concept>
        ): Promise<boolean> {
            const visited = new Set<string>();
            const stack = [potentialPrerequisite.$primaryKey];
            
            while (stack.length > 0) {
                const current = stack.pop()!;
                if (current === targetConcept.$primaryKey) return true;
                if (visited.has(current)) continue;
                visited.add(current);
                
                const concept = await client(Concept).fetchOne(current);
                if (concept) {
                    for await (const prereq of concept.$link.prerequisites.asyncIter()) {
                        stack.push(prereq.$primaryKey);
                    }
                }
            }
            return false;
        }

    gradeQuizAndSaveResultsFunction:
      title_kr: "퀴즈 채점 함수"
      function_type: ONTOLOGY_EDIT
      language: TYPESCRIPT_V2
      code: |
        type OntologyEdit = Edits.Object<QuizAttempt> | Edits.Object<LearningRecord>;
        
        export default async function gradeQuizAndSaveResultsFunction(
            client: Client,
            quizAttempt: Osdk.Instance<QuizAttempt>,
            responses: QuizResponse[]
        ): Promise<OntologyEdit[]> {
            const batch = createEditBatch<OntologyEdit>(client);
            
            // Calculate score
            const score = calculateScore(responses);
            
            // Update quiz attempt
            batch.update(quizAttempt, {
                score: score,
                completedAt: new Date().toISOString(),
                status: "GRADED"
            });
            
            // Create learning record
            batch.create(LearningRecord, {
                recordId: Uuid.random(),
                studentId: quizAttempt.studentId,
                masteryScore: score / 100
            });
            
            return batch.getEdits();
        }
```

### 2.7 Anti-Patterns

```yaml
anti_patterns:
  - id: "FUNC-ANTI-001"
    name: "Search After Edit"
    bad: "Search for just-created object within same function"
    problem: "Search APIs use stale data until function completes"
    good: "Use primary key references instead of search"
    
  - id: "FUNC-ANTI-002"
    name: "Missing Edits Declaration"
    bad: "@OntologyEditFunction() without @Edits decorator"
    good: "@Edits(Type1, Type2) @OntologyEditFunction()"
```

### 2.8 Integration Points

```yaml
integration_points:
  dependencies:
    sdk_packages:
      typescript_v2: ["@osdk/client", "@osdk/functions"]
      typescript_v1: ["@foundry/functions-api", "@foundry/ontology-api"]
      python: ["functions.api", "ontology_sdk"]
      
  reverse_dependencies: [ActionType FUNCTION_RULE, Workshop, API Gateway]
  
  execution_modes:
    serverless: "On-demand, cost-efficient, multiple versions"
    deployed: "Long-lived, caching, GPU support"
```

---

## COMPONENT 3: Rule_Constraint

### 3.1 Official Definition

```yaml
official_definition:
  term: Rule_Constraint
  source_urls:
    - https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints
    - https://www.palantir.com/docs/foundry/action-types/submission-criteria
    - https://www.palantir.com/docs/foundry/dynamic-scheduling/scheduling-validation-rules
  verification_date: "2026-02-05"

  constraint_categories:
    property_level:
      description_kr: "속성 수준 제약 조건"
      enforcement: ["Index time", "Action apply time"]
      
    action_level:
      description_kr: "액션 수준 제약 조건 (제출 기준)"
      enforcement: "Pre-execution validation"
      
    scheduling_level:
      description_kr: "스케줄링 수준 제약 조건"
      types: { HARD: "Blocks submission", SOFT: "Warning only" }

  property_constraint_types_complete_list:
    - ONE_OF: "Enum - static set of allowed values"
    - RANGE: "Min/max for numbers, dates, string length, array size"
    - STRING_REGEX_MATCH: "Pattern matching with regex"
    - STRING_LENGTH: "String length bounds"
    - ARRAY_SIZE: "Array length bounds"
    - UNIQUENESS: "Array elements must be unique"
    - NESTED: "Constraint applied to each array element"
    - STRUCT_ELEMENT: "Constraint on specific struct field"
    - RID: "Must be valid Foundry Resource Identifier"
    - UUID: "Must be valid UUID"
    - REQUIRED: "Property must have non-null value"
```

### 3.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - { source: "Database CHECK Constraint", mapping: "Property constraints validate values" }
    - { source: "Form Validation", mapping: "Submission criteria validate before submit" }
    - { source: "Business Rule Engine", mapping: "Scheduling rules evaluate domain logic" }
```

### 3.3 Structural Schema

```yaml
structural_schema:
  property_constraint:
    ONE_OF:
      valid_types: [String, Boolean, Decimal, Double, Float, Integer, Short]
      config:
        options: [{ displayName: string, value: any }]
        otherValuesAllowed: boolean
        caseSensitive: boolean  # for strings
        
    RANGE:
      valid_types: [Decimal, Double, Float, Integer, Short, Date, Timestamp, String, Array]
      config:
        gte: number  # greater than or equal
        lte: number  # less than or equal
        gt: number   # greater than (exclusive)
        lt: number   # less than (exclusive)
      notes:
        - "For String: constrains length"
        - "For Array: constrains size"
        
    STRING_REGEX_MATCH:
      valid_types: [String]
      config:
        regex: string
        configuredFailureMessage: string
        
    UNIQUENESS:
      valid_types: [Array]
      description: "All array elements must be unique"
      
    REQUIRED:
      description: "Property must have non-null value"
      notes: "Only available in Object Storage V2"

  action_constraint:
    operators_single_value:
      - IS
      - IS_NOT
      - MATCHES
      - IS_LESS_THAN
      - IS_GREATER_THAN
      - IS_LESS_THAN_OR_EQUALS
      - IS_GREATER_THAN_OR_EQUALS
      
    operators_multi_value:
      - INCLUDES
      - INCLUDES_ANY
      - IS_INCLUDED_IN
      - EACH_IS
      - EACH_IS_NOT
      
    logical_operators: [AND, OR, NOT]
    
    condition_types:
      - CURRENT_USER: "User ID, group membership, Multipass attributes"
      - PARAMETER: "Compare parameter values"
      
  scheduling_constraint:
    severity_levels:
      HARD: { visual: "Red circle", behavior: "Blocks submission" }
      SOFT: { visual: "Orange triangle", behavior: "Warning only" }
```

### 3.4 Decision Tree

```yaml
decision_tree:
  root:
    question: "What level of validation needed?"
    
  branches:
    property_validation:
      use_when: "Validate individual property values"
      options:
        - "Enum values → ONE_OF"
        - "Numeric range → RANGE"
        - "String pattern → STRING_REGEX_MATCH"
        - "Array uniqueness → UNIQUENESS"
        
    action_validation:
      use_when: "Validate before Action execution"
      options:
        - "User permissions → CURRENT_USER condition"
        - "Parameter relationships → PARAMETER condition"
        - "Complex logic → COMPOSITE with AND/OR/NOT"
        
    scheduling_validation:
      use_when: "Validate scheduling scenarios"
      options:
        - "Must satisfy → HARD constraint"
        - "Should satisfy → SOFT constraint"
```

### 3.5 Validation Rules

```yaml
validation_rules:
  - id: "CONS-VAL-001"
    name: "Constraint Type Compatibility"
    severity: ERROR
    check: "Constraint type valid for property base type"
    
  - id: "CONS-VAL-002"
    name: "Range Bounds Consistency"
    severity: ERROR
    check: "gte <= lte when both specified"
    
  - id: "CONS-VAL-003"
    name: "Failure Message Required"
    severity: WARNING
    check: "All constraints should have custom failure messages"
```

### 3.6 Canonical Examples

```yaml
canonical_examples:
  k12_education:
    property_constraints:
      difficulty_level:
        property: difficultyLevel
        constraint: RANGE
        config: { gte: 1, lte: 10 }
        failureMessage_kr: "난이도는 1-10 사이여야 합니다"
        
      subject_type:
        property: subjectType
        constraint: ONE_OF
        config:
          options:
            - { value: "KOREAN", displayName: "국어" }
            - { value: "MATH", displayName: "수학" }
            - { value: "SCIENCE", displayName: "과학" }
        failureMessage_kr: "유효한 과목을 선택하세요"
        
      concept_code:
        property: conceptCode
        constraint: STRING_REGEX_MATCH
        config:
          regex: "^[A-Z]{2}-[0-9]{4}-[0-9]{2}$"
        failureMessage_kr: "개념 코드 형식: XX-0000-00"
        
    action_constraints:
      self_prerequisite_check:
        condition: "targetConcept.conceptId != prerequisiteConcept.conceptId"
        failureMessage: "A concept cannot be its own prerequisite"
        failureMessage_kr: "개념은 자기 자신의 선수 개념이 될 수 없습니다"
        
      curriculum_editor_only:
        conditionType: CURRENT_USER
        operator: IS_INCLUDED_IN
        groups: ["curriculum-editors", "admin-users"]
        failureMessage_kr: "교육과정 편집자만 수정 가능"
        
      valid_mastery_score:
        conditionType: PARAMETER
        operator: IS_GREATER_THAN_OR_EQUALS
        leftOperand: { parameter: masteryScore }
        rightOperand: { value: 0 }
        failureMessage_kr: "숙달 점수는 0 이상이어야 합니다"
        
    scheduling_constraints:
      no_overlapping_lessons:
        type: HARD
        description_kr: "수업 시간 중복 불가"
        
      preferred_teacher_match:
        type: SOFT
        description_kr: "선호 교사 배정 권장"
```

### 3.7 Anti-Patterns

```yaml
anti_patterns:
  - id: "CONS-ANTI-001"
    name: "Missing Failure Messages"
    bad: "Constraint without custom error message"
    problem: "Users see generic errors, poor UX"
    good: "Always provide descriptive failure messages"
    
  - id: "CONS-ANTI-002"
    name: "Overly Permissive Constraints"
    bad: "ONE_OF with otherValuesAllowed: true when not needed"
    problem: "Defeats purpose of enumeration"
    good: "Use otherValuesAllowed: false for strict enums"
```

### 3.8 Integration Points

```yaml
integration_points:
  dependencies:
    - ObjectType: "Property constraints attached to ObjectType properties"
    - ValueType: "Constraints can reference shared ValueType definitions"
    - ActionType: "Action constraints are part of ActionType definition"
    
  reverse_dependencies:
    - Object Storage: "Enforces property constraints at index/write time"
    - Actions Service: "Enforces submission criteria before execution"
    - Workshop: "Displays validation errors to users"
    - Dynamic Scheduling: "Evaluates scheduling constraints"
    
  enforcement_flow:
    property_constraint:
      - "1. Data indexed into Object Storage"
      - "2. Constraint evaluated against value"
      - "3. If violated: index fails OR action blocked"
      
    action_constraint:
      - "1. User fills Action parameters"
      - "2. Submission criteria evaluated"
      - "3. If any fail: submission blocked with error"
      - "4. If all pass: rules executed atomically"
```

---

## Naming Conventions Summary

```yaml
naming_conventions:
  api_names:
    format: camelCase
    examples: [addLearningRecord, linkPrerequisiteConcept, modifyConceptDifficulty]
    
  display_names:
    format: "Title Case with spaces"
    examples: ["Add Learning Record", "Link Prerequisite Concept"]
    
  forbidden_patterns:
    - PascalCase
    - snake_case
    - Reserved words: [ontology, object, property, link, relation, rid, primaryKey, typeId]
```

---

## Quick Reference: Complete Type Lists

```yaml
quick_reference:
  action_rule_types:
    - CREATE_OBJECT
    - MODIFY_OBJECT
    - CREATE_OR_MODIFY_OBJECT
    - DELETE_OBJECT
    - CREATE_LINK
    - DELETE_LINK
    - FUNCTION_RULE
    - CREATE_OBJECT_OF_INTERFACE
    - MODIFY_OBJECT_OF_INTERFACE
    - DELETE_OBJECT_OF_INTERFACE

  parameter_types:
    - STRING, INTEGER, LONG, SHORT, FLOAT, DOUBLE, DECIMAL, BYTE
    - BOOLEAN, DATE, TIMESTAMP
    - OBJECT, OBJECT_SET, INTERFACE_REFERENCE
    - ATTACHMENT, ARRAY, STRUCT
    - GEOPOINT, GEOSHAPE, MEDIA, VECTOR

  value_sources:
    - FROM_PARAMETER
    - OBJECT_PROPERTY
    - STATIC_VALUE
    - CURRENT_USER
    - CURRENT_TIME

  property_constraints:
    - ONE_OF, RANGE, STRING_REGEX_MATCH, STRING_LENGTH
    - ARRAY_SIZE, UNIQUENESS, NESTED, STRUCT_ELEMENT
    - RID, UUID, REQUIRED

  submission_operators:
    single: [IS, IS_NOT, MATCHES, IS_LESS_THAN, IS_GREATER_THAN, IS_LESS_THAN_OR_EQUALS, IS_GREATER_THAN_OR_EQUALS]
    multi: [INCLUDES, INCLUDES_ANY, IS_INCLUDED_IN, EACH_IS, EACH_IS_NOT]
    logical: [AND, OR, NOT]
```

---

**Document Complete** | Sources verified from official Palantir documentation | K-12 Education examples included with Korean translations