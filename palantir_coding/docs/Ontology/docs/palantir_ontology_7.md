# Palantir Ontology Logic & Automation Primitives: Complete YAML Reference

**Version**: 2.0.0 | **Verification Date**: February 8, 2026 | **Target Consumer**: Claude-Opus-4.6

> **Cross-references:**
> - ObjectType/Property/SharedProperty → `palantir_ontology_1.md`
> - LinkType/Interface → `palantir_ontology_2.md`
> - ActionType/Function/Constraint → `palantir_ontology_3.md`
> - Dataset/Pipeline/Transform → `palantir_ontology_4.md`
> - ObjectSet operations → `palantir_ontology_5.md`
> - OSDK SDK patterns → `palantir_ontology_6.md`
> - Security & Governance → `palantir_ontology_8.md`

---

## COMPONENT 1: Function

### 1.1 Official Definition

```yaml
official_definition:
  term: Function
  source_urls:
    - https://www.palantir.com/docs/foundry/functions/edits-overview/
    - https://www.palantir.com/docs/foundry/functions/typescript-v2-ontology-edits
    - https://www.palantir.com/docs/foundry/functions/python-ontology-edits
    - https://www.palantir.com/docs/foundry/functions/query-functions
  verification_date: "2026-02-08"

  definition_en: |
    Functions are executable logic units in the Ontology that enable custom computations,
    data transformations, and Ontology modifications through code. They serve as the
    programmable layer of the Ontology, enabling business logic that exceeds the
    capabilities of built-in Action rules.

  definition_kr: |
    Function(함수)은 온톨로지에서 커스텀 계산, 데이터 변환, 온톨로지 수정을 코드를 통해
    수행하는 실행 가능한 로직 단위입니다.

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

    typescript_v2_function:
      runtime: "OSDK Functions (TypeScript v2)"
      purpose: "Modern serverless functions with OSDK client access"
      features:
        - "Full OSDK client for Ontology access"
        - "Async/await native support"
        - "Automatic type generation from Ontology schema"
        - "Direct deployment from Developer Console"
      decorator: "@function()"
      differences_from_v1:
        - "Uses OSDK client instead of Objects API"
        - "Supports modern TypeScript features"
        - "Better type inference from generated types"

    python_function:
      runtime: "Python Functions"
      purpose: "Python-based Ontology functions"
      features:
        - "PySpark integration for large-scale data processing"
        - "Pandas/NumPy support for data science workloads"
        - "ML model inference within functions"
      decorators: ["@function", "@query"]

    pipeline_builder_function:
      runtime: "Pipeline Builder"
      purpose: "Visual function composition with Python callables"
      integration: "Python functions callable from Pipeline Builder nodes"
      use_case: "Low-code users compose logic visually, with custom Python for complex steps"

  critical_caveat: |
    "Changes to objects and links are propagated to the object set APIs after your
    function has finished executing." — Palantir Docs. Search results within an edit
    function return stale data until the function completes.

  supported_types:
    primitives: [String, Integer, Long, Double, Float, Boolean, Timestamp, Date, LocalDate]
    ontology: [ObjectType, "ObjectSet<T>", "SingleLink<T>", "MultiLink<T>"]
    collections: ["Array<T>", "Map<K,V>", "Set<T>"]
    custom: [DataClass, CustomStruct]
```

### 1.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - source: "SQL Stored Procedure"
      mapping: "Encapsulates reusable logic with Ontology access"
    - source: "GraphQL Resolver"
      mapping: "Query resolves fields; Edit handles mutations"
    - source: "Serverless Lambda"
      mapping: "Executes on-demand in managed environment"
    - source: "Spring @Service method"
      mapping: "Business logic layer operating on domain objects"

  anti_concepts:
    - name: "Raw SQL/DML"
      contrast: "Functions operate on Ontology objects, not raw database tables"
    - name: "Client-side logic"
      contrast: "Functions execute server-side with full Ontology access and security enforcement"
```

### 1.3 Structural Schema

```yaml
structural_schema:
  Function:
    metadata:
      className: string       # TypeScript class name
      methodName: string      # Method name (unique identifier)
      version: semver         # Semantic version
      apiName: string         # For @Query functions

    decorator:
      type: enum              # @Function | @OntologyEditFunction | @Query | @function (v2)
      edits: "list[ObjectType]"  # For @OntologyEditFunction

    signature:
      inputs:
        - name: string
          type: FunctionType
          optional: boolean
      returnType: "FunctionType | void"

  languages:
    typescript_v2:
      imports: ["@osdk/client", "@osdk/functions", "@ontology/sdk"]
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
          return batch.getEdits();
        }

    typescript_v1:
      imports: ["@foundry/functions-api", "@foundry/ontology-api"]
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
      imports: ["functions.api", "ontology_sdk"]
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

  execution_modes:
    serverless:
      description: "On-demand, cost-efficient, multiple versions"
      deployment: "Publish from Code Repositories"
      limits: { timeout: "45 seconds", memory: "Platform-managed" }
    deployed:
      description: "Long-running compute with custom resources"
      deployment: "Deploy via Code Repositories"
      limits: { timeout: "Configurable", memory: "Configurable (up to cluster limits)" }
```

### 1.4 Decision Tree

```yaml
decision_tree:
  root:
    question: "Does this logic modify Ontology data?"
    yes: "Ontology Edit Function → backed by ActionType with FUNCTION_RULE"
    no: "Continue to query vs pure function"

  query_vs_pure:
    question: "Should this be exposed as an API endpoint?"
    yes: "@Query with apiName → accessible via OSDK and API Gateway"
    no: "@Function → internal reusable computation"

  language_selection:
    typescript_v2:
      when: ["Recommended for new projects", "Need npm ecosystem", "Explicit edit returns with type safety"]
    typescript_v1:
      when: ["Debugger support needed", "Simpler void return pattern", "Legacy codebase compatibility"]
    python:
      when: ["DataFrame/PySpark support", "ML/data science workflows", "Pandas/NumPy required"]
    aip_logic:
      when: ["Natural language definable rule", "Non-technical authors", "Classification/extraction/summarization"]
```

### 1.5 Validation Rules

```yaml
validation_rules:
  - id: "FUNC-VAL-001"
    name: "API Name Format"
    severity: ERROR
    check: "apiName is camelCase; /^[a-z][a-zA-Z0-9]*$/"

  - id: "FUNC-VAL-002"
    name: "Edits Declaration Required"
    severity: ERROR
    check: "Edit functions must declare @Edits with ObjectTypes"

  - id: "FUNC-VAL-003"
    name: "Search Around Limit"
    severity: ERROR
    check: "Max 3 searchAround calls per function"

  - id: "FUNC-VAL-004"
    name: "Query No Side Effects"
    severity: ERROR
    check: "@Query functions must not modify Ontology state"

  - id: "FUNC-VAL-005"
    name: "Function Rule Exclusivity"
    severity: ERROR
    check: "FUNCTION_RULE must be the only rule in its ActionType"
```

### 1.6 Canonical Examples

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

    gradeQuizAndSaveResults:
      title_kr: "퀴즈 채점 및 결과 저장 함수"
      function_type: ONTOLOGY_EDIT
      language: TYPESCRIPT_V2
      code: |
        type OntologyEdit = Edits.Object<QuizAttempt> | Edits.Object<LearningRecord>;
        export default async function gradeQuizAndSaveResults(
            client: Client,
            quizAttempt: Osdk.Instance<QuizAttempt>,
            responses: QuizResponse[]
        ): Promise<OntologyEdit[]> {
            const batch = createEditBatch<OntologyEdit>(client);
            const score = calculateScore(responses);
            batch.update(quizAttempt, {
                score, completedAt: new Date().toISOString(), status: "GRADED"
            });
            batch.create(LearningRecord, {
                recordId: Uuid.random(),
                studentId: quizAttempt.studentId,
                masteryScore: score / 100
            });
            return batch.getEdits();
        }
```

### 1.7 Anti-Patterns

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

  - id: "FUNC-ANTI-003"
    name: "Side Effects in Query Function"
    bad: "@Query function that modifies objects"
    problem: "Violates read-only contract; may execute multiple times"
    good: "Use @OntologyEditFunction for mutations"
```

### 1.8 Integration Points

```yaml
integration_points:
  dependencies:
    sdk_packages:
      typescript_v2: ["@osdk/client", "@osdk/functions"]
      typescript_v1: ["@foundry/functions-api", "@foundry/ontology-api"]
      python: ["functions.api", "ontology_sdk"]
    ontology_types:
      - "ObjectType (palantir_ontology_1.md)"
      - "LinkType (palantir_ontology_2.md)"

  reverse_dependencies:
    - "ActionType FUNCTION_RULE (palantir_ontology_3.md §1)"
    - "Workshop widget bindings"
    - "API Gateway (@Query exposed endpoints)"
    - "AIP Logic (this document §5)"
    - "Automation effects (this document §2)"
```

---

## COMPONENT 2: Automation (Automate)

### 2.1 Official Definition

```yaml
official_definition:
  term: Automation
  source_urls:
    - https://www.palantir.com/docs/foundry/automate/overview
    - https://www.palantir.com/docs/foundry/automate/conditions
    - https://www.palantir.com/docs/foundry/automate/effects
  verification_date: "2026-02-08"

  definition_en: |
    Automate is an application for setting up business automation. It allows users to define
    conditions and effects. Conditions are checked continuously, and effects are executed
    automatically when the specified conditions are met.

  definition_kr: |
    Automate(자동화)는 비즈니스 자동화를 설정하는 애플리케이션입니다. 조건과 효과를 정의하면
    조건이 지속적으로 확인되고 충족 시 효과가 자동으로 실행됩니다.
```

### 2.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - source: "Cron Job + Event Handler"
      mapping: "Schedule-based or data-change-based triggers"
    - source: "AWS EventBridge Rule"
      mapping: "Event pattern matching → target action invocation"
    - source: "Database Trigger"
      mapping: "ObjectSet condition → Action effect on data change"
    - source: "IFTTT / Zapier"
      mapping: "If condition met, then execute effect"

  anti_concepts:
    - name: "Manual Action execution"
      contrast: "Automation triggers Actions without user intervention"
    - name: "Pipeline/Transform"
      contrast: "Pipelines move data; Automations react to Ontology events"
```

### 2.3 Structural Schema

```yaml
structural_schema:
  Automation:
    metadata:
      name: string
      description: string
      enabled: boolean
      expiry: timestamp         # Optional auto-disable date

    condition:
      type: enum                # TIME | OBJECT_SET

      time_condition:
        mode: enum              # HOURLY | DAILY | WEEKLY | MONTHLY | CRON
        cron: string            # 5-field cron expression
        timezone: string

      objectset_condition:
        type: enum
        # OBJECTS_ADDED | OBJECTS_REMOVED | OBJECTS_MODIFIED
        # METRIC_CHANGED | THRESHOLD_CROSSED | OBJECTS_EXIST
        objectSet: "ObjectSetDefinition | FunctionReference"

    effects:
      - type: enum              # ACTION | NOTIFICATION | FALLBACK

        action_effect:
          actionType: ActionTypeApiName
          parameterMapping: "map[actionParam, effectInput]"
          executionMode: enum   # ONCE_ALL | ONCE_BATCH | ONCE_EACH_GROUP
          retryPolicy:
            type: enum          # CONSTANT | EXPONENTIAL
            maxRetries: integer
            initialDelay: duration

        notification_effect:
          type: enum            # PLATFORM | EMAIL
          recipients: list
          template: string
          attachments: "list[NotepadRef]"

        fallback_effect:
          description: "Executed when primary effects fail"
          actions: "list[ActionEffect]"

    execution_settings:
      batchSize: integer
      parallelism: integer
      evaluationLatency: enum   # LIVE | SCHEDULED
```

### 2.4 Decision Tree

```yaml
decision_tree:
  trigger_selection:
    question: "What triggers this automation?"
    schedule_based:
      trigger: "TIME condition"
      options:
        hourly: "mode: HOURLY"
        daily: "mode: DAILY + time"
        weekly: "mode: WEEKLY + dayOfWeek + time"
        monthly: "mode: MONTHLY + dayOfMonth + time"
        custom: "mode: CRON + 5-field cron expression"
    data_change_based:
      trigger: "OBJECT_SET condition"
      options:
        new_objects: "OBJECTS_ADDED"
        deleted_objects: "OBJECTS_REMOVED"
        modified_objects: "OBJECTS_MODIFIED"
        metric_threshold: "METRIC_CHANGED or THRESHOLD_CROSSED"
        existence: "OBJECTS_EXIST (batch processing)"

  effect_selection:
    question: "What should happen when triggered?"
    options:
      execute_action: "ACTION effect — runs an ActionType"
      send_notification: "NOTIFICATION effect — platform or email"
      both_with_fallback: "Primary ACTION + FALLBACK for failure handling"
```

### 2.5 Code Pattern Identification Rules

```yaml
code_pattern_identification:
  rules:
    - pattern: "@Scheduled(cron='...')"
      mapping: { condition_type: TIME, cron: "extracted from annotation" }
      confidence: HIGH

    - pattern: "@EventListener / onEntityCreate()"
      mapping: { condition_type: OBJECT_SET, trigger: OBJECTS_ADDED }
      confidence: HIGH

    - pattern: "onEntityUpdate()"
      mapping: { condition_type: OBJECT_SET, trigger: OBJECTS_MODIFIED }
      confidence: HIGH

    - pattern: "onEntityDelete()"
      mapping: { condition_type: OBJECT_SET, trigger: OBJECTS_REMOVED }
      confidence: HIGH

    - pattern: "Webhook handler endpoint"
      mapping: "Action with webhook side effect"
      confidence: MEDIUM

    - pattern: "Message queue consumer"
      mapping: "Object set condition + Action effect"
      confidence: MEDIUM

    - pattern: "Batch processor"
      mapping: { condition_type: OBJECT_SET, trigger: OBJECTS_EXIST, execution_mode: ONCE_BATCH }
      confidence: HIGH
```

### 2.6 Canonical Examples

```yaml
canonical_examples:
  k12_education:
    daily_attendance_report:
      title_kr: "일일 출석 보고서 자동 생성"
      condition:
        type: TIME
        mode: DAILY
        cron: "0 18 * * MON-FRI"
        timezone: "Asia/Seoul"
      effects:
        - type: ACTION
          actionType: generateAttendanceReport
          parameterMapping: { reportDate: "{{trigger.date}}" }
        - type: NOTIFICATION
          notificationType: EMAIL
          recipients: ["school-admin-group"]
          template: "Daily attendance report generated for {{trigger.date}}"

    new_student_onboarding:
      title_kr: "신입생 자동 온보딩"
      condition:
        type: OBJECT_SET
        trigger: OBJECTS_ADDED
        objectSet: { objectType: Student, filter: { status: "ENROLLED" } }
      effects:
        - type: ACTION
          actionType: createStudentProfile
          executionMode: ONCE_EACH_GROUP
          retryPolicy: { type: EXPONENTIAL, maxRetries: 3, initialDelay: "PT5M" }

    low_mastery_alert:
      title_kr: "학습 숙달도 저하 알림"
      condition:
        type: OBJECT_SET
        trigger: THRESHOLD_CROSSED
        objectSet: { objectType: LearningRecord, filter: { masteryScore: { lt: 0.3 } } }
      effects:
        - type: NOTIFICATION
          notificationType: PLATFORM
          recipients: ["{{object.teacherId}}"]
          template: "Student {{object.studentName}} mastery below 30%"
```

### 2.7 Anti-Patterns

```yaml
anti_patterns:
  - id: "AUTO-ANTI-001"
    name: "Infinite Automation Loop"
    bad: "Automation modifies object → triggers another automation → infinite cycle"
    problem: "Cascading modifications causing runaway effects"
    good: "Add status flag check (e.g., 'processedByAutomation: true') to break cycles"

  - id: "AUTO-ANTI-002"
    name: "No Fallback Effect"
    bad: "Action effect without fallback for failure scenarios"
    problem: "Silent failures with no alerting or recovery"
    good: "Always configure FALLBACK effect with at least a notification"

  - id: "AUTO-ANTI-003"
    name: "Overly Broad ObjectSet Condition"
    bad: "OBJECTS_MODIFIED on large ObjectType without filters"
    problem: "Triggers on every modification, overwhelming the system"
    good: "Apply specific property filters to narrow the trigger scope"
```

### 2.8 Integration Points

```yaml
integration_points:
  dependencies:
    - "ActionType (palantir_ontology_3.md) — executed by ACTION effects"
    - "ObjectSet (palantir_ontology_5.md) — used in OBJECT_SET conditions"
    - "Function (this document §1) — can be used as ObjectSet source"

  reverse_dependencies:
    - "Rules Engine (this document §3) — Rules output can trigger Automations"
    - "Writeback (this document §4) — external sync after Action execution"
```

---

## COMPONENT 3: Rules Engine (Foundry Rules)

### 3.1 Official Definition

```yaml
official_definition:
  term: FoundryRules
  source_urls:
    - https://www.palantir.com/docs/foundry/rules-engine/overview
    - https://www.palantir.com/docs/foundry/rules-engine/logic-boards
  verification_date: "2026-02-08"

  definition_en: |
    Foundry Rules (formerly Taurus) enables users to actively manage complex business logic
    in Foundry with a point-and-click, low-code interface. Users can create rules and apply
    them to datasets, objects, and time series for alert generation, data categorization,
    and task generation.

  definition_kr: |
    Foundry Rules(파운드리 규칙 엔진)은 포인트 앤 클릭, 로우코드 인터페이스를 통해 복잡한
    비즈니스 로직을 관리할 수 있게 해주는 기능입니다.
```

### 3.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - source: "Business Rules Management System (BRMS)"
      mapping: "Low-code rule definition with visual boards"
    - source: "SQL Pipeline (SELECT → WHERE → GROUP BY → JOIN)"
      mapping: "Logic boards compose like SQL operators"
    - source: "Excel Power Query / Pivot Tables"
      mapping: "Visual data transformation with filter/aggregate/join"

  anti_concepts:
    - name: "Functions (TypeScript/Python)"
      contrast: "Rules Engine is no-code visual; Functions require programming"
    - name: "Automation"
      contrast: "Rules Engine transforms data; Automation reacts to events"
```

### 3.3 Structural Schema

```yaml
structural_schema:
  FoundryRule:
    inputs:
      - type: enum              # DATASET | OBJECT
        source: "rid | ObjectTypeApiName"

    logic_boards:
      filter_board:
        purpose: "Filter rows/objects based on conditions"
        conditions: "list[FilterCondition]"

      aggregation_board:
        purpose: "Group and aggregate data"
        groupBy: "list[column]"
        aggregations: "map[outputColumn, aggregateFunction]"

      join_board:
        purpose: "Join with additional datasets"
        joinType: enum          # INNER | LEFT | RIGHT | FULL
        joinDataset: rid
        joinConditions: list

      expression_board:
        purpose: "Compute derived columns"
        expressions: "map[outputColumn, expression]"

      window_board:
        purpose: "Window functions over partitions"
        partitionBy: "list[column]"
        orderBy: "list[column]"
        windowFunction: string

      select_columns_board:
        purpose: "Select/rename output columns"
        columns: "list[column]"

      union_board:
        purpose: "Combine multiple datasets"
        datasets: "list[rid]"

    output:
      dataset: rid
      schema: "list[ColumnDefinition]"

  action_rules:
    description: "10 rule types available in ActionTypes (cross-ref: palantir_ontology_3.md §1)"
    object_operations: [createObject, modifyObject, createOrModifyObject, deleteObject]
    link_operations: [createLink, deleteLink]        # Many-to-many only
    function_rule: [functionRule]                     # EXCLUSIVE — no other rules allowed
    interface_operations: [createObjectOfInterface, modifyObjectOfInterface, deleteObjectOfInterface]
```

### 3.4 Code Pattern Identification Rules

```yaml
code_pattern_identification:
  rules:
    - pattern: "if/else conditional logic"
      mapping: "Filter board + Expression board"
      confidence: HIGH

    - pattern: "GROUP BY aggregation"
      mapping: "Aggregation board"
      confidence: HIGH

    - pattern: "JOIN operations"
      mapping: "Join board"
      confidence: HIGH

    - pattern: "Window functions (ROW_NUMBER, RANK, LAG/LEAD)"
      mapping: "Window board"
      confidence: HIGH

    - pattern: "UNION operations"
      mapping: "Union board"
      confidence: HIGH

    - pattern: "Business validation rules"
      mapping: "Submission criteria on ActionTypes"
      confidence: HIGH

    - pattern: "Rule-based alert generation"
      mapping: "Foundry Rules → Alert output dataset"
      confidence: HIGH
```

### 3.5 Anti-Patterns

```yaml
anti_patterns:
  - id: "RULE-ANTI-001"
    name: "Overly Complex Rule Chains"
    bad: "20+ boards in a single rule"
    problem: "Debugging difficulty, performance degradation"
    good: "Break into multiple smaller rules with intermediate datasets"

  - id: "RULE-ANTI-002"
    name: "Rules for Code-Level Logic"
    bad: "Using Rules Engine for complex graph traversal or ML inference"
    problem: "Rules Engine is optimized for tabular transformations, not algorithms"
    good: "Use Functions (TypeScript/Python) for algorithmic logic"
```

### 3.6 Integration Points

```yaml
integration_points:
  dependencies:
    - "Dataset (palantir_ontology_4.md) — input sources"
    - "ObjectType (palantir_ontology_1.md) — OBJECT input type"

  reverse_dependencies:
    - "ActionType (palantir_ontology_3.md) — 10 rule types define Action behavior"
    - "Automation (this document §2) — Rules output can trigger Automations"
    - "Alert systems — Rules generate alert datasets"
```

---

## COMPONENT 4: Writeback

### 4.1 Official Definition

```yaml
official_definition:
  term: Writeback
  source_urls:
    - https://www.palantir.com/docs/foundry/object-edits/writeback-datasets
    - https://www.palantir.com/docs/foundry/action-types/webhooks
  verification_date: "2026-02-08"

  definition_en: |
    Writeback is the mechanism for synchronizing Ontology changes (user edits via Actions)
    back to writeback datasets and external systems via Webhooks, Exports, or External
    Functions.

  definition_kr: |
    Writeback(쓰기 동기화)는 온톨로지 변경사항(액션을 통한 사용자 편집)을 쓰기 데이터셋과
    외부 시스템으로 동기화하는 메커니즘입니다.
```

### 4.2 Structural Schema

```yaml
structural_schema:
  Writeback:
    internal:
      writeback_dataset:
        description: "Stores user-modified version of source data"
        source: "Unchanged original dataset"
        destination: "Merged dataset with user edits applied"
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

### 4.3 Code Pattern Identification Rules

```yaml
code_pattern_identification:
  cqrs_mapping:
    "Event Store": "Funnel queue + writeback datasets"
    "Command Side (Write)": "Actions with Ontology Rules"
    "Event Publication": "Side Effect Webhooks OR Streaming Exports"
    "Read Model Update": "Object indexing via Funnel pipelines"
    "Saga/Compensation": "Writeback Webhook (fail-safe external call first)"
    "Event Replay": "Dataset versioning + Funnel replacement pipelines"
```

### 4.4 Anti-Patterns

```yaml
anti_patterns:
  - id: "WB-ANTI-001"
    name: "Multiple Writeback Webhooks"
    bad: "Trying to add 2+ writeback webhooks to one Action"
    problem: "Platform limit: ONE writeback webhook per Action"
    good: "Use one writeback webhook + multiple side-effect webhooks"

  - id: "WB-ANTI-002"
    name: "Side Effect for Critical Operations"
    bad: "Using side-effect webhook for must-succeed external calls"
    problem: "Side effects are best-effort; failures are silent"
    good: "Use writeback webhook (blocking) for critical external calls"
```

### 4.5 Integration Points

```yaml
integration_points:
  dependencies:
    - "ActionType (palantir_ontology_3.md) — Actions trigger writebacks"
    - "Dataset (palantir_ontology_4.md) — writeback datasets as targets"

  reverse_dependencies:
    - "External systems — Webhooks notify external services"
    - "Data pipelines — Streaming exports feed downstream systems"
```

---

## COMPONENT 5: AIP (Artificial Intelligence Platform)

### 5.1 Official Definition

```yaml
official_definition:
  term: AIP
  source_urls:
    - https://www.palantir.com/docs/foundry/aip/overview
    - https://www.palantir.com/docs/foundry/aip/aip-features
    - https://www.palantir.com/docs/foundry/logic/overview
  verification_date: "2026-02-08"

  definition_en: |
    AIP brings large language models into the Foundry platform, enabling AI agents that can
    query the Ontology, execute Actions, and call Functions — all with proper security
    enforcement and citation support.

  definition_kr: |
    AIP(인공지능 플랫폼)는 대규모 언어 모델을 Foundry 플랫폼에 통합하여 온톨로지 쿼리,
    액션 실행, 함수 호출이 가능한 AI 에이전트를 지원합니다.

  components:
    agents:
      purpose: "LLM-powered agents with full Ontology access"
      capabilities:
        - "Natural language queries over ObjectSets"
        - "Action execution (with user confirmation)"
        - "Function calling (Query and Edit functions)"
        - "Link traversal and relationship reasoning"
        - "Multi-step reasoning chains"
      retrieval_context:
        method: "Object sets as RAG context for agents"
        configuration:
          - "Select ObjectTypes to include in agent context"
          - "Configure which properties are visible to the agent"
          - "Set maximum context window per ObjectType"
      citations:
        features:
          - "Per-ObjectType citation format overrides"
          - "Property-level citation (link to specific object)"
          - "Source traceability in generated responses"
      security:
        - "Agents inherit user's permissions (markings, RBAC)"
        - "Action execution requires user confirmation by default"
        - "Audit logging of all agent interactions"

    logic:
      purpose: "No-code AI function builder"
      backed_by: "LLM with Ontology context"
      capabilities:
        - "Natural language function definition"
        - "Input: ObjectSet or object properties"
        - "Output: Classification, extraction, summarization, scoring"
        - "No coding required — define behavior in plain language"
```

### 5.2 Semantic Definition

```yaml
semantic_definition:
  analogies:
    - source: "LangChain Agent"
      mapping: "AIP Agent — LLM with tool use over Ontology"
    - source: "OpenAI Function Calling"
      mapping: "AIP Agent with Ontology Functions as tools"
    - source: "RAG with Vector Store"
      mapping: "AIP Agent with ObjectSet retrieval context"
    - source: "ML Classification Endpoint"
      mapping: "AIP Logic function — no-code classification"
    - source: "Copilot / Assistant UI"
      mapping: "AIP Agent embedded in Workshop"

  anti_concepts:
    - name: "Standalone LLM API"
      contrast: "AIP agents are Ontology-aware with security enforcement"
    - name: "Custom ML Pipeline"
      contrast: "AIP Logic requires no training — uses prompt engineering"
```

### 5.3 AIP Logic Function Configuration

```yaml
aip_logic_configuration:
  function_types:
    classification:
      description: "Categorize objects into predefined classes"
      output_type: "String (from enumerated values)"
      example:
        name: "classifySupportTicketPriority"
        input: "SupportTicket object (subject, description, customerTier)"
        output: "CRITICAL | HIGH | MEDIUM | LOW"
        prompt: "Based on the ticket subject, description, and customer tier, classify the priority"

    extraction:
      description: "Extract structured data from unstructured text"
      output_type: "String or Struct"
      example:
        name: "extractContractKeyTerms"
        input: "Contract object (fullText)"
        output: "Struct { effectiveDate, terminationClause, liability }"
        prompt: "Extract the effective date, termination clause, and liability cap from the contract text"

    summarization:
      description: "Generate concise summaries of object data"
      output_type: "String"
      example:
        name: "summarizeIncidentReport"
        input: "Incident object (timeline, affectedSystems, rootCause, resolution)"
        output: "String (2-3 sentence summary)"

    scoring:
      description: "Assign numeric scores based on qualitative criteria"
      output_type: "Double"
      example:
        name: "scoreLeadQuality"
        input: "Lead object (companySize, industry, engagement, source)"
        output: "Double (0.0 to 1.0)"

    boolean_evaluation:
      description: "Yes/no determination based on object properties"
      output_type: "Boolean"
      example:
        name: "requiresEscalation"
        input: "SupportTicket object (description, sentiment, responseCount)"
        output: "Boolean"

  configuration_steps:
    1: "Navigate to Ontology Manager → Functions → Create AIP Logic Function"
    2: "Select input ObjectType and properties to include"
    3: "Define output type (String, Double, Boolean, or Struct)"
    4: "Write prompt template with property placeholders"
    5: "Select LLM model from available stack models"
    6: "Test with sample objects"
    7: "Publish and bind to Actions, Workshop widgets, or other Functions"
```

### 5.4 AIP Logic Block Types

```yaml
aip_logic_blocks:
  description: "AIP Logic functions are composed of blocks — discrete execution steps forming a pipeline"

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
    apply_actions:
      description: "LLM can trigger Ontology Actions based on reasoning"
      example: "LLM classifies ticket as CRITICAL → triggers 'escalateTicket' Action"
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
    example_pipeline:
      1: "Create Variable: load input object properties"
      2: "Use LLM: classify the input (tools: Query Objects for context)"
      3: "Conditionals: branch on classification result"
      4: "Apply Action: update object status based on classification"
      5: "Use LLM: generate summary of action taken"
```

### 5.5 Prompt Template Patterns

```yaml
prompt_templates:
  property_injection:
    description: "Properties injected into prompts using {{propertyName}} placeholders"
    template_example: |
      You are analyzing a support ticket.
      Subject: {{subject}}
      Description: {{description}}
      Customer Tier: {{customerTier}}
      Classify the priority as one of: CRITICAL, HIGH, MEDIUM, LOW.
      Respond with ONLY the priority level.

  few_shot_prompting:
    description: "Include examples in the prompt for consistent output"
    template_example: |
      Classify the following contract clause type.
      Examples:
      - "The agreement shall terminate on December 31, 2026" -> TERMINATION
      - "Liability shall not exceed $1,000,000" -> LIABILITY_CAP
      Clause: {{clauseText}}
      Classification:

  structured_output:
    description: "Request JSON-formatted output for Struct return types"
    template_example: |
      Extract key information from this incident report.
      Report: {{fullText}}
      Respond in this exact JSON format:
      { "severity": "P1|P2|P3|P4", "rootCause": "brief description" }
```

### 5.6 Model Selection Patterns

```yaml
model_selection:
  selection_criteria:
    classification_tasks:
      recommended: "Medium model (GPT-3.5 class)"
      reason: "Simple categorical output; large models add cost without accuracy gain"
    extraction_tasks:
      recommended: "Large model (GPT-4 class)"
      reason: "Complex text understanding; structured output requires stronger reasoning"
    summarization_tasks:
      recommended: "Large model (GPT-4 class)"
      reason: "Nuanced language generation; quality correlates with model size"
    scoring_tasks:
      recommended: "Medium model with few-shot examples"
      reason: "Calibrated scoring benefits from examples more than model size"
    boolean_tasks:
      recommended: "Medium model (GPT-3.5 class)"
      reason: "Binary decision; simpler reasoning sufficient"

  cost_optimization:
    - "Use smaller models for high-volume, simple tasks"
    - "Reserve large models for complex tasks"
    - "Minimize input token count via property sub-selection"
    - "Cache results for deterministic inputs"
    - "Use batch processing for non-real-time tasks"
```

### 5.7 Code Pattern Identification Rules

```yaml
code_pattern_identification:
  rules:
    - pattern: "Chatbot querying structured data"
      mapping: "AIP Agent with ObjectSet context"
      confidence: HIGH

    - pattern: "NLP classification on entity fields"
      mapping: "AIP Logic function"
      confidence: HIGH

    - pattern: "RAG (Retrieval Augmented Generation) pipeline"
      mapping: "AIP Agent with retrieval context configuration"
      confidence: HIGH

    - pattern: "AI-assisted decision support"
      mapping: "AIP Agent with Action execution capability"
      confidence: HIGH

    - pattern: "Text extraction / summarization service"
      mapping: "AIP Logic function"
      confidence: HIGH

    - pattern: "LLM function calling / tool use"
      mapping: "AIP Agent with Function calling"
      confidence: HIGH

  ai_pattern_mapping:
    "LangChain agent": "AIP Agent"
    "OpenAI function calling": "AIP Agent with Ontology Functions"
    "RAG with vector store": "AIP Agent with ObjectSet retrieval"
    "ML classification endpoint": "AIP Logic function"
    "Copilot / assistant UI": "AIP Agent in Workshop"
```

### 5.8 Anti-Patterns

```yaml
anti_patterns:
  - id: "AIP-ANTI-001"
    name: "Overly Vague Prompts"
    bad: "'Analyze this object' without specifying what to analyze"
    problem: "Inconsistent, low-quality LLM outputs"
    good: "Be specific about input properties, expected output format, and evaluation criteria"

  - id: "AIP-ANTI-002"
    name: "No Output Format Constraint"
    bad: "Expecting structured output without format specification"
    problem: "LLM returns free-form text when structured output is needed"
    good: "Explicitly specify output format with examples; use few-shot prompting"

  - id: "AIP-ANTI-003"
    name: "Too Many Properties in Context"
    bad: "Including all 50 properties when only 3 are relevant"
    problem: "Increased token cost, reduced accuracy"
    good: "Select only properties relevant to the task"

  - id: "AIP-ANTI-004"
    name: "Skipping Agent Security"
    bad: "Granting agent broad Action execution without user confirmation"
    problem: "Unintended mutations from LLM hallucination"
    good: "Keep user confirmation enabled; scope agent Actions to minimum necessary"
```

### 5.9 Integration Points

```yaml
integration_points:
  dependencies:
    - "ObjectType (palantir_ontology_1.md) — objects as agent context"
    - "ActionType (palantir_ontology_3.md) — agent Action execution"
    - "Function (this document §1) — agent Function calling"
    - "Security & Governance (palantir_ontology_8.md) — agents inherit user permissions"

  reverse_dependencies:
    - "Workshop — AIP Agent embedded in operational UIs"
    - "OSDK — AIP Logic functions callable via SDK"
    - "Automation (this document §2) — AIP Logic can be triggered by Automations"
```

---

## COMPONENT 6: Versioning & Governance

### 6.1 Schema Evolution

```yaml
schema_evolution:
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

### 6.2 Proposal Workflow

```yaml
proposal_workflow:
  workflow:
    1_branch_creation: "Derived from main version; isolated experimentation"
    2_proposal: "Contains reviews and metadata; each resource = separate Task"
    3_rebase: "Manual incorporation of Main changes; conflict resolution"
    4_review: "Reviewer assignment; individual task approval"
    5_merge: "Integration into Main (atomic)"

  review_actions: [approve, request_changes, reject, comment]

  conflict_resolution:
    detection: "Automatic on rebase"
    types:
      schema_conflict: "Same property modified in both branch and main"
      dependency_conflict: "Branch depends on main change that was reverted"
    resolution:
      auto: "Simple non-overlapping changes resolved automatically"
      manual: "Incorporate main changes → resolve → re-validate"

  migration_approval:
    breaking_changes: "Require explicit migration approval"
    migrations: ["drop_property_edits", "cast_property_type", "move_edits", "drop_all_edits"]

  merge_prerequisites:
    - "All tasks approved by reviewers"
    - "No unresolved conflicts"
    - "All migrations approved"
    - "Schema validation passes"

  post_merge:
    - "All stakeholders notified"
    - "Object Storage re-indexes affected types"
    - "OSDK packages should be regenerated"
    - "Downstream pipelines may need rebuilding"
```

### 6.3 Code Pattern Identification Rules

```yaml
code_pattern_identification:
  database_migration_mapping:
    "Schema migration files (Flyway, Liquibase)": "Ontology schema changes + migrations"
    "Rolling migrations": "OSv2 migration framework"
    "Blue-green deployment": "Ontology branches + proposals"
    "Version rollback": "Revert migration"
    "Breaking change detection": "Automatic in Ontology Manager"
    "Data transformation scripts": "Cast/Move migrations"
```

---

## Quick Reference: Complete Type Lists

```yaml
quick_reference:
  function_types:
    - "@Function (general computation)"
    - "@OntologyEditFunction (write operations)"
    - "@Query (read-only API endpoint)"
    - "@function (TypeScript v2 OSDK)"
    - "Python @function"
    - "AIP Logic (no-code LLM)"

  function_runtimes:
    - "TypeScript v2 (OSDK — recommended for new projects)"
    - "TypeScript v1 (legacy, debugger support)"
    - "Python (data science, ML)"
    - "Pipeline Builder (visual, low-code)"
    - "AIP Logic (no-code, LLM-powered)"

  automation_condition_types:
    time: [HOURLY, DAILY, WEEKLY, MONTHLY, CRON]
    object_set: [OBJECTS_ADDED, OBJECTS_REMOVED, OBJECTS_MODIFIED, METRIC_CHANGED, THRESHOLD_CROSSED, OBJECTS_EXIST]

  automation_effect_types: ["ACTION", "NOTIFICATION", "FALLBACK"]

  automation_execution_modes: ["ONCE_ALL", "ONCE_BATCH", "ONCE_EACH_GROUP"]

  rules_engine_board_types:
    - "Filter Board"
    - "Aggregation Board"
    - "Join Board"
    - "Expression Board"
    - "Window Board"
    - "Select Columns Board"
    - "Union Board"

  aip_logic_block_types: ["Use LLM", "Apply Action", "Execute Function", "Conditionals", "Loops", "Create Variable"]

  aip_llm_tool_types: ["Apply Actions", "Call Function", "Query Objects", "Calculator"]

  writeback_types: ["Internal (writeback dataset)", "Writeback Webhook (blocking)", "Side Effect Webhook (best-effort)", "File Export", "Streaming Export", "Table Export"]

  migration_types: [drop_property_edits, drop_struct_field_edits, drop_all_edits, move_edits, cast_property_type, revert_migration]
```

---

## Cross-Document Reference Map

```yaml
cross_references:
  this_document: "palantir_ontology_7.md v2.0 — Function, Automation, Rules Engine, Writeback, AIP, Versioning"

  related_documents:
    palantir_ontology_1: "ObjectType/Property definitions — Function inputs/outputs"
    palantir_ontology_2: "LinkType/Interface — Interface support in Functions"
    palantir_ontology_3: "ActionType — Function-backed Actions, edit rules, submission criteria"
    palantir_ontology_4: "Dataset/Pipeline — Transform inputs, writeback destinations"
    palantir_ontology_5: "ObjectSet — Function queries, Automation conditions"
    palantir_ontology_6: "OSDK — SDK patterns for calling Functions and Actions"
    palantir_ontology_8: "Security — RBAC for Functions, AIP agent security inheritance"

  source_sections:
    "Ontology.md §6": "Function types, schema, code examples"
    "Ontology.md §8": "Automation schema, pattern mapping"
    "Ontology.md §9": "Rules Engine, logic blocks, action rules"
    "Ontology.md §10": "Writeback, CQRS mapping"
    "Ontology.md §11": "Versioning, proposal workflow"
    "Ontology.md §17": "AIP agents, logic functions, prompt patterns, block types"
```

---

**Document Version:** 2.0 | **Date:** 2026-02-08
**Source:** Ontology.md Sections 6, 8-11, 17 + Security_and_Governance.md cross-refs
**Coverage:** Function (6 types), Automation, Rules Engine (7 boards), Writeback (6 types), AIP (6 block types + 4 LLM tools), Versioning & Governance
**Format:** YAML spec with official_definition, semantic_definition, structural_schema, decision_tree, code_pattern_identification, canonical_examples, anti_patterns, integration_points per component
