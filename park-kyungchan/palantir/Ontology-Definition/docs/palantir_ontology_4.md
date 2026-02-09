# Palantir Foundry Data Pipeline Layer - Complete Reference

I have compiled comprehensive YAML reference files for all 4 data pipeline components based on official Palantir documentation. Below are the complete files.

---

## FILE 1: SESSION_4_OUTPUT_Dataset.yaml

```yaml
# =============================================================================
# SESSION_4_OUTPUT_Dataset.yaml
# Palantir Foundry Dataset Component - Complete Reference
# Generated: 2026-02-03
# Consumer: Claude-Opus-4.5 (Claude Code CLI)
# =============================================================================

metadata:
  componentName: Dataset
  version: "1.0.0"
  lastUpdated: "2026-02-03"
  sources:
    - url: "https://www.palantir.com/docs/foundry/data-integration/datasets"
      accessDate: "2026-02-03"
    - url: "https://www.palantir.com/docs/foundry/api/datasets-v2-resources/datasets/get-dataset-schema"
      accessDate: "2026-02-03"

official_definition:
  definition: |
    A dataset is the most essential representation of data from when it lands 
    in Foundry through when it is mapped into the Ontology. Fundamentally, 
    a dataset is a wrapper around a collection of files which are stored in 
    a backing file system.
  source: "https://www.palantir.com/docs/foundry/data-integration/datasets"
  verificationDate: "2026-02-03"
  keyCharacteristics:
    - "Provides integrated support for permission management"
    - "Provides schema management capabilities"
    - "Supports version control via transactions"
    - "Enables updates over time with full lineage"
  ridFormat: "ri.foundry.main.dataset.<uuid>"

semantic_definition:
  analogy: |
    A Dataset is like a versioned Git repository for data files. Just as Git 
    tracks changes to code files with commits, a Dataset tracks changes to 
    data files with transactions.
  similarConcepts:
    - name: "Data Lake Table"
      similarity: "Both store structured/unstructured data"
      difference: "Dataset has integrated governance, versioning, and Ontology sync"
    - name: "S3 Bucket"
      similarity: "Both store files in object storage"
      difference: "Dataset adds schema, versioning, permissions, lineage"
  oppositeConcepts:
    - name: "Virtual Table"
      description: "Points to external data without storing in Foundry"

structural_schema:
  $schema: "https://json-schema.org/draft/2020-12/schema"
  $id: "https://palantir.com/foundry/schema/dataset"
  title: "Foundry Dataset Schema"
  type: object
  required:
    - rid
    - name
  properties:
    rid:
      type: string
      pattern: "^ri\\.foundry\\.main\\.dataset\\.[a-f0-9-]+$"
    name:
      type: string
      minLength: 1
      maxLength: 1024
    path:
      type: string
      pattern: "^/.*$"
    branch:
      type: string
      default: "master"
    schema:
      type: object
      properties:
        fieldSchemaList:
          type: array
          items:
            type: object
            required: [name, type]
            properties:
              name:
                type: string
                pattern: "^[a-z][a-zA-Z0-9]*$"
              type:
                type: string
                enum: [STRING, BOOLEAN, INTEGER, LONG, FLOAT, DOUBLE, DECIMAL, DATE, TIMESTAMP, BINARY, ARRAY, MAP, STRUCT]
              nullable:
                type: boolean
                default: true
              precision:
                type: integer
                minimum: 1
                maximum: 38
              scale:
                type: integer
                minimum: 0
                maximum: 38

decision_tree:
  title: "Dataset Usage Decision Flow"
  transactionSelectionMatrix:
    SNAPSHOT:
      useWhen:
        - "Initial data load"
        - "Full batch refresh"
        - "Small datasets that can be fully reprocessed"
      avoidWhen:
        - "Large datasets with frequent small updates"
        - "Incremental processing is required"
    APPEND:
      useWhen:
        - "Log/event data"
        - "Time-series data"
        - "Incremental pipelines"
      constraint: "Fails if existing files are overwritten"
    UPDATE:
      useWhen:
        - "CDC (Change Data Capture) workflows"
        - "Files may be modified"
      constraint: "Breaks downstream incremental if files modified"
    DELETE:
      useWhen:
        - "Data retention compliance"
        - "GDPR/privacy requirements"
      constraint: "Cannot sync with DELETE via Data Connection"

validation_rules:
  errors:
    - id: "DS-E001"
      severity: ERROR
      rule: "Primary key column must have unique values"
      description: "Duplicate primary keys cause OntologySync failures"
    - id: "DS-E002"
      severity: ERROR
      rule: "DECIMAL precision must be 1-38"
    - id: "DS-E003"
      severity: ERROR
      rule: "APPEND transaction cannot overwrite existing files"
  warnings:
    - id: "DS-W001"
      severity: WARNING
      rule: "Path references are mutable"
      recommendation: "Use dataset RID for stable references"
    - id: "DS-W002"
      severity: WARNING
      rule: "Foundry saves all columns as nullable internally"

canonical_examples:
  - id: "mathematical-concepts-master"
    scenario: "Mathematical Concepts Master Data"
    description: "Stores curriculum-aligned math concepts for K-12 standards"
    datasetConfig:
      name: "Mathematical Concepts"
      path: "/K12Education/MasterData/mathematicalConcepts"
      transactionType: SNAPSHOT
      rationale: "Master data changes infrequently; full refresh acceptable"
    schema:
      fieldSchemaList:
        - name: conceptId
          type: STRING
          nullable: false
        - name: conceptName
          type: STRING
          nullable: false
        - name: gradeLevel
          type: INTEGER
          nullable: false
        - name: domain
          type: STRING
          nullable: false
        - name: standardCode
          type: STRING
          nullable: true
        - name: prerequisiteConcepts
          type: ARRAY
          nullable: true
          arraySubtype:
            type: STRING
        - name: difficultyLevel
          type: INTEGER
          nullable: true
        - name: lastUpdatedTimestamp
          type: TIMESTAMP
          nullable: false

  - id: "student-learning-records"
    scenario: "Student Learning Records Incremental Processing"
    description: "Stores individual student learning activity records"
    datasetConfig:
      name: "Student Learning Records"
      path: "/K12Education/Transactional/studentLearningRecords"
      transactionType: APPEND
      rationale: "High volume event data; incremental processing required"
    schema:
      fieldSchemaList:
        - name: recordId
          type: STRING
          nullable: false
        - name: studentId
          type: STRING
          nullable: false
        - name: conceptId
          type: STRING
          nullable: false
        - name: activityType
          type: STRING
          nullable: false
        - name: scorePercentage
          type: DOUBLE
          nullable: true
        - name: timeSpentSeconds
          type: LONG
          nullable: true
        - name: completedTimestamp
          type: TIMESTAMP
          nullable: false

  - id: "concept-problem-mapping"
    scenario: "Concept-Problem Mapping Dataset"
    description: "Maps mathematical concepts to practice problems"
    datasetConfig:
      name: "Concept Problem Mapping"
      path: "/K12Education/Mapping/conceptProblemMapping"
      transactionType: UPDATE
      rationale: "Mappings may be modified when problems are reassigned"
    schema:
      fieldSchemaList:
        - name: mappingId
          type: STRING
          nullable: false
        - name: conceptId
          type: STRING
          nullable: false
        - name: problemId
          type: STRING
          nullable: false
        - name: difficultyAlignment
          type: STRING
          nullable: false
        - name: isPrimary
          type: BOOLEAN
          nullable: false

anti_patterns:
  - id: "AP-DS-001"
    name: "Path-Based Production References"
    description: "Using filesystem paths instead of RIDs in production code"
    badExample: |
      @transform(output=Output("/Company/Project/MyDataset"))  # BAD
    goodExample: |
      @transform(output=Output("ri.foundry.main.dataset.abc-123"))  # GOOD
    severity: HIGH

  - id: "AP-DS-002"
    name: "Non-Deterministic Primary Keys"
    description: "Using generated UUIDs or timestamps as primary keys"
    badExample: |
      df = df.withColumn("primaryKey", F.monotonically_increasing_id())
    goodExample: |
      df = df.withColumn("primaryKey", F.concat(F.col("studentId"), F.lit("_"), F.col("date")))
    severity: CRITICAL

integration_points:
  - component: Pipeline
    relationship: "Dataset is INPUT and OUTPUT of Pipeline transforms"
    dataFlowDirection: BIDIRECTIONAL
  - component: Transform
    relationship: "Transform reads from and writes to Datasets"
    dataFlowDirection: BIDIRECTIONAL
  - component: OntologySync
    relationship: "Dataset serves as backing source for Ontology objects"
    dataFlowDirection: OUTBOUND
    requirements:
      - "Unique primary key column required"
      - "Deterministic primary keys mandatory"
```

---

## FILE 2: SESSION_4_OUTPUT_Pipeline.yaml

```yaml
# =============================================================================
# SESSION_4_OUTPUT_Pipeline.yaml
# Palantir Foundry Pipeline Component - Complete Reference
# Generated: 2026-02-03
# Consumer: Claude-Opus-4.5 (Claude Code CLI)
# =============================================================================

metadata:
  componentName: Pipeline
  version: "1.0.0"
  lastUpdated: "2026-02-03"
  sources:
    - url: "https://www.palantir.com/docs/foundry/pipeline-builder/overview"
      accessDate: "2026-02-03"
    - url: "https://www.palantir.com/docs/foundry/building-pipelines/pipeline-types"
      accessDate: "2026-02-03"

official_definition:
  definition: |
    Pipeline Builder is Foundry's primary application for data integration. 
    You can use Pipeline Builder to build data integration pipelines that 
    transform raw data sources into clean outputs ready for further analysis.
  source: "https://www.palantir.com/docs/foundry/pipeline-builder/overview"
  verificationDate: "2026-02-03"
  keyCharacteristics:
    - "Graph and form-based interface for visual pipeline design"
    - "Uses Spark and Flink as execution engines"
    - "Enables collaboration between technical and non-technical users"
    - "No code required for most transformations"
  workflowSteps:
    - step: 1
      name: "Inputs"
      description: "Add data sources or datasets"
    - step: 2
      name: "Transform"
      description: "Transform, join, or union data"
    - step: 3
      name: "Preview"
      description: "Preview output after transformations"
    - step: 4
      name: "Deliver"
      description: "Build the pipeline outputs"
    - step: 5
      name: "Outputs"
      description: "Add object types, link types, or dataset outputs"

semantic_definition:
  analogy: |
    A Pipeline is like an automated factory assembly line for data. Raw 
    materials (source data) enter, pass through workstations (transforms), 
    and finished products (clean datasets) come out the other end.
  similarConcepts:
    - name: "ETL Process"
      similarity: "Both extract, transform, and load data"
      difference: "Pipeline has visual interface, integrated governance"
    - name: "Apache Airflow DAG"
      similarity: "Both define directed data transformation graphs"
      difference: "Pipeline Builder is no-code"
  oppositeConcepts:
    - name: "Ad-hoc Query"
      description: "One-time query without automation"

structural_schema:
  $schema: "https://json-schema.org/draft/2020-12/schema"
  $id: "https://palantir.com/foundry/schema/pipeline"
  title: "Foundry Pipeline Schema"
  type: object
  required:
    - pipelineId
    - name
    - inputs
    - outputs
  properties:
    pipelineId:
      type: string
    name:
      type: string
      minLength: 1
      maxLength: 256
    pipelineType:
      type: string
      enum: [PIPELINE_BUILDER, CODE_REPOSITORY]
      default: PIPELINE_BUILDER
    processingMode:
      type: string
      enum: [BATCH, INCREMENTAL, STREAMING]
      default: BATCH
    inputs:
      type: array
      minItems: 1
      items:
        type: object
        required: [inputId, sourceType, reference]
        properties:
          inputId:
            type: string
          sourceType:
            type: string
            enum: [DATASET, MEDIA_SET, STREAM, DATA_CONNECTION]
          reference:
            type: string
          isIncremental:
            type: boolean
            default: false
    outputs:
      type: array
      minItems: 1
      items:
        type: object
        required: [outputId, outputType, reference]
        properties:
          outputId:
            type: string
          outputType:
            type: string
            enum: [DATASET, OBJECT_TYPE, LINK_TYPE, STREAMING_DATASET]
          reference:
            type: string
          transactionType:
            type: string
            enum: [SNAPSHOT, APPEND, UPDATE]
    schedule:
      type: object
      properties:
        triggerType:
          type: string
          enum: [TIME_BASED, EVENT_BASED, MANUAL, COMPOUND]
        cronExpression:
          type: string
          description: "5-field Unix cron format"
        timezone:
          type: string
          default: "UTC"
        eventTriggers:
          type: array
          items:
            type: object
            properties:
              eventType:
                type: string
                enum: [DATA_UPDATED, JOB_SUCCEEDED, LOGIC_UPDATED]
              sourceReference:
                type: string
        retryPolicy:
          type: object
          properties:
            maxRetries:
              type: integer
              default: 3
            retryDelayMinutes:
              type: integer
              default: 1

decision_tree:
  title: "Pipeline Type and Mode Selection"
  pipelineTypeComparison:
    PIPELINE_BUILDER:
      interface: "Graph and form-based"
      languages: "No code required"
      typeSafety: "Strongly typed; errors flagged immediately"
      recommendedFor: "Production pipelines, cross-team collaboration"
    CODE_REPOSITORY:
      interface: "Web-based IDE"
      languages: "Python, SQL, Java, Mesa"
      typeSafety: "Code-based; errors at build time"
      recommendedFor: "API calls, custom libraries, complex logic"
  processingModeComparison:
    BATCH:
      latency: "High (minutes to hours)"
      complexity: "Low"
      computeCost: "Medium per run"
      bestFor:
        - "Small datasets"
        - "Initial development"
        - "Complex aggregations on full history"
    INCREMENTAL:
      latency: "Medium (minutes)"
      complexity: "Medium"
      computeCost: "Low per run"
      bestFor:
        - "Large append-only datasets"
        - "Event/log data"
        - "CDC workflows"
      constraints:
        - "Input must use APPEND/UPDATE transactions"
        - "Logic cannot depend on full history"
    STREAMING:
      latency: "Very low (< 15 seconds)"
      complexity: "High"
      computeCost: "High (continuous)"
      bestFor:
        - "Real-time operational workflows"
        - "Live dashboards"
      constraints:
        - "1 MB max per row"
        - "Requires careful state management"

validation_rules:
  errors:
    - id: "PL-E001"
      severity: ERROR
      rule: "Pipeline must have at least one input"
    - id: "PL-E002"
      severity: ERROR
      rule: "Pipeline must have at least one output"
    - id: "PL-E003"
      severity: ERROR
      rule: "Incremental input requires APPEND/UPDATE transactions"
    - id: "PL-E004"
      severity: ERROR
      rule: "Circular dependencies are not allowed"
  warnings:
    - id: "PL-W001"
      severity: WARNING
      rule: "Large SNAPSHOT builds are expensive"
      recommendation: "Consider INCREMENTAL for large datasets"
    - id: "PL-W002"
      severity: WARNING
      rule: "Retry policy should have at least 3 retries"

canonical_examples:
  - id: "math-concepts-batch-pipeline"
    scenario: "Mathematical Concepts Master Data Pipeline"
    description: "Batch pipeline that refreshes mathematical concept reference data"
    pipelineType: PIPELINE_BUILDER
    processingMode: BATCH
    rationale: "Master data is small and updated infrequently"
    configuration:
      name: "Mathematical Concepts Ingestion"
      inputs:
        - inputId: rawConceptsCsv
          sourceType: DATA_CONNECTION
          reference: "ri.foundry.main.dataset.raw-concepts-csv"
      outputs:
        - outputId: cleanedConcepts
          outputType: DATASET
          reference: "/K12Education/MasterData/mathematicalConcepts"
          transactionType: SNAPSHOT
      transforms:
        - nodeId: parseHeaders
          transformType: "Rename columns"
          configuration:
            mappings:
              "Concept ID": conceptId
              "Concept Name": conceptName
              "Grade Level": gradeLevel
        - nodeId: validateGrade
          transformType: "Filter"
          configuration:
            condition: "gradeLevel >= 1 AND gradeLevel <= 12"
      schedule:
        triggerType: TIME_BASED
        cronExpression: "0 2 * * 0"
        timezone: "America/New_York"

  - id: "student-records-incremental-pipeline"
    scenario: "Student Learning Records Incremental Pipeline"
    description: "Incremental pipeline processing student activity events"
    pipelineType: CODE_REPOSITORY
    processingMode: INCREMENTAL
    rationale: "High-volume event data; only new records need processing"
    configuration:
      name: "Student Learning Records Processing"
      inputs:
        - inputId: rawActivityEvents
          sourceType: STREAM
          reference: "ri.foundry.main.dataset.raw-activity-stream"
          isIncremental: true
      outputs:
        - outputId: processedRecords
          outputType: DATASET
          reference: "/K12Education/Transactional/studentLearningRecords"
          transactionType: APPEND
      codeExample: |
        from transforms.api import transform, incremental, Input, Output
        
        @incremental()
        @transform.using(
            raw_events=Input('/K12Education/Raw/activityEvents'),
            processed=Output('/K12Education/Transactional/studentLearningRecords')
        )
        def process_learning_records(raw_events, processed):
            df = raw_events.polars(mode='added')
            result = df.filter(pl.col('studentId').is_not_null())
            processed.write_table(result)
      schedule:
        triggerType: EVENT_BASED
        eventTriggers:
          - eventType: DATA_UPDATED
            sourceReference: "ri.foundry.main.dataset.raw-activity-stream"

anti_patterns:
  - id: "AP-PL-001"
    name: "Streaming for Batch-Appropriate Workloads"
    description: "Using streaming mode when batch would suffice"
    badExample:
      scenario: "Daily attendance summary using streaming pipeline"
    goodExample:
      scenario: "Daily attendance summary using batch with nightly schedule"
    severity: HIGH

  - id: "AP-PL-002"
    name: "Schedule Without Retry Policy"
    description: "Scheduled pipelines without configured retries"
    badExample: |
      schedule:
        triggerType: TIME_BASED
        cronExpression: "0 6 * * *"
    goodExample: |
      schedule:
        triggerType: TIME_BASED
        cronExpression: "0 6 * * *"
        retryPolicy:
          maxRetries: 3
          retryDelayMinutes: 5
    severity: MEDIUM

integration_points:
  - component: Dataset
    relationship: "Pipeline reads from and writes to Datasets"
    dataFlowDirection: BIDIRECTIONAL
  - component: Transform
    relationship: "Transforms are processing units within Pipelines"
    dataFlowDirection: INTERNAL
  - component: OntologySync
    relationship: "Pipeline outputs can directly sync to Ontology"
    dataFlowDirection: OUTBOUND
  - component: Schedule
    relationship: "Schedules trigger pipeline execution"
    dataFlowDirection: CONTROL
```

---

## FILE 3: SESSION_4_OUTPUT_Transform.yaml

```yaml
# =============================================================================
# SESSION_4_OUTPUT_Transform.yaml
# Palantir Foundry Transform Component - Complete Reference
# Generated: 2026-02-03
# Consumer: Claude-Opus-4.5 (Claude Code CLI)
# =============================================================================

metadata:
  componentName: Transform
  version: "1.0.0"
  lastUpdated: "2026-02-03"
  sources:
    - url: "https://www.palantir.com/docs/foundry/transforms-python/transforms"
      accessDate: "2026-02-03"
    - url: "https://www.palantir.com/docs/foundry/pipeline-builder/transforms-overview"
      accessDate: "2026-02-03"

official_definition:
  definition: |
    A Transform is a unit of computation that reads from input datasets, 
    applies transformation logic, and writes results to output datasets. 
    Transforms can be defined visually in Pipeline Builder or programmatically 
    in Code Repositories using Python, SQL, or Java.
  source: "https://www.palantir.com/docs/foundry/transforms-python/transforms"
  verificationDate: "2026-02-03"
  transformCategories:
    - category: "Expressions"
      description: "Column-level operations producing single output column"
      examples: ["Cast", "Concat", "Split string"]
    - category: "Transforms"
      description: "Table-level operations returning entire table"
      examples: ["Filter", "Aggregate", "Pivot"]
    - category: "Structural Transforms"
      description: "Combine multiple tables"
      examples: ["Join", "Union"]

semantic_definition:
  analogy: |
    A Transform is like a single workstation in a factory assembly line. 
    Each workstation receives partially assembled products (input data), 
    performs a specific operation (filter, join, aggregate), and passes 
    the result to the next workstation.
  similarConcepts:
    - name: "SQL Query"
      similarity: "Both transform data from inputs to outputs"
      difference: "Transform is versioned, scheduled, tracked in lineage"
    - name: "dbt Model"
      similarity: "Both are SQL-based transformation units"
      difference: "Transform supports Python/Java; has visual builder"

structural_schema:
  $schema: "https://json-schema.org/draft/2020-12/schema"
  $id: "https://palantir.com/foundry/schema/transform"
  title: "Foundry Transform Schema"
  type: object
  required:
    - transformId
    - transformType
    - inputs
    - outputs
  properties:
    transformId:
      type: string
    transformType:
      type: string
      enum: [PIPELINE_BUILDER, CODE_PYTHON, CODE_SQL, CODE_JAVA]
    inputs:
      type: array
      minItems: 1
      items:
        type: object
        required: [inputName, reference]
        properties:
          inputName:
            type: string
            pattern: "^[a-z][a-zA-Z0-9_]*$"
          reference:
            type: string
          readMode:
            type: string
            enum: [CURRENT, ADDED, PREVIOUS]
            default: CURRENT
    outputs:
      type: array
      minItems: 1
      items:
        type: object
        required: [outputName, reference]
        properties:
          outputName:
            type: string
            pattern: "^[a-z][a-zA-Z0-9_]*$"
          reference:
            type: string
          transactionType:
            type: string
            enum: [SNAPSHOT, APPEND]
    computeEngine:
      type: string
      enum: [LIGHTWEIGHT, SPARK]
      default: LIGHTWEIGHT
    incrementalConfig:
      type: object
      properties:
        enabled:
          type: boolean
          default: false
        semanticVersion:
          type: integer
          minimum: 0
        strictAppend:
          type: boolean
          default: false
        requireIncremental:
          type: boolean
          default: false
        v2Semantics:
          type: boolean
          default: true
    resourceConfig:
      type: object
      properties:
        cpuCores:
          type: integer
          minimum: 1
          maximum: 32
          default: 2
        memoryGb:
          type: integer
          minimum: 1
          maximum: 256
          default: 4
        gpuType:
          type: string
          enum: [NVIDIA_T4, NVIDIA_A10, null]
          default: null

decision_tree:
  title: "Transform Configuration Decision Flow"
  engineSelectionMatrix:
    LIGHTWEIGHT:
      dataScale: "< 10 million rows"
      libraries: "Polars, pandas, DuckDB"
      startup: "Fast"
      gpu: "Supported"
      bestFor:
        - "API calls"
        - "ML inference"
        - "File processing"
    SPARK:
      dataScale: "Billions of rows"
      libraries: "PySpark"
      startup: "Slower (cluster allocation)"
      gpu: "Not directly supported"
      bestFor:
        - "Large joins"
        - "Heavy aggregations"
        - "Distributed ETL"
  decoratorSelection:
    "@transform.using()":
      engine: LIGHTWEIGHT
      useCase: "Default single-node, Polars/pandas"
    "@transform.spark.using()":
      engine: SPARK
      useCase: "Multi-node distributed processing"
    "@transform_df()":
      engine: SPARK
      useCase: "Single DataFrame output"
    "@transform_pandas()":
      engine: SPARK
      useCase: "pandas DataFrames with Spark conversion"

validation_rules:
  errors:
    - id: "TR-E001"
      severity: ERROR
      rule: "Transform must have at least one input"
    - id: "TR-E002"
      severity: ERROR
      rule: "Transform must have at least one output"
    - id: "TR-E003"
      severity: ERROR
      rule: "SQL transforms do not support incremental processing"
    - id: "TR-E004"
      severity: ERROR
      rule: "Lightweight transforms cannot use PySpark"
    - id: "TR-E005"
      severity: ERROR
      rule: "GPU transforms require @lightweight decorator"
  warnings:
    - id: "TR-W001"
      severity: WARNING
      rule: "Non-nullable schema may cause incremental SchemaMismatchError"
    - id: "TR-W002"
      severity: WARNING
      rule: "Large transforms should use Spark"
      threshold: "Expected data > 10M rows"

canonical_examples:
  - id: "concept-data-transform"
    scenario: "Mathematical Concepts Data Cleaning Transform"
    description: "Cleans and validates mathematical concept master data"
    transformType: CODE_PYTHON
    computeEngine: LIGHTWEIGHT
    rationale: "Small reference data; simple validation logic"
    codeExample: |
      from transforms.api import transform, Input, Output
      import polars as pl
      from datetime import datetime
      
      @transform.using(
          raw_concepts=Input('/K12Education/Raw/conceptsCsv'),
          clean_concepts=Output('/K12Education/MasterData/mathematicalConcepts')
      )
      def clean_mathematical_concepts(raw_concepts, clean_concepts):
          df = raw_concepts.polars()
          
          result = (df
              .rename({
                  'Concept ID': 'conceptId',
                  'Concept Name': 'conceptName',
                  'Grade Level': 'gradeLevel',
                  'Domain': 'domain'
              })
              .filter((pl.col('gradeLevel') >= 1) & (pl.col('gradeLevel') <= 12))
              .filter(pl.col('conceptId').is_not_null())
              .with_columns(pl.lit(datetime.now()).alias('lastUpdatedTimestamp'))
          )
          
          clean_concepts.write_table(result)

  - id: "student-records-incremental-transform"
    scenario: "Student Learning Records Incremental Transform"
    description: "Incrementally processes student activity events"
    transformType: CODE_PYTHON
    computeEngine: LIGHTWEIGHT
    incrementalConfig:
      enabled: true
      v2Semantics: true
    rationale: "High-volume append-only event data"
    codeExample: |
      from transforms.api import transform, incremental, Input, Output
      import polars as pl
      
      @incremental()
      @transform.using(
          raw_events=Input('/K12Education/Raw/activityEvents'),
          processed=Output('/K12Education/Transactional/studentLearningRecords')
      )
      def process_student_records(raw_events, processed):
          # Read only new records since last build
          df = raw_events.polars(mode='added')
          
          result = (df
              .with_columns([
                  (pl.col('score') / pl.col('maxScore') * 100).alias('scorePercentage'),
                  pl.col('timestamp').alias('completedTimestamp')
              ])
              .filter(pl.col('studentId').is_not_null())
              .select([
                  'recordId', 'studentId', 'conceptId', 'activityType',
                  'scorePercentage', 'timeSpentSeconds', 'attemptCount',
                  'completedTimestamp', 'deviceType', 'sessionId'
              ])
          )
          
          processed.write_table(result)

  - id: "concept-problem-mapping-spark-transform"
    scenario: "Large-Scale Concept-Problem Mapping Transform"
    description: "Distributed processing for large mapping datasets"
    transformType: CODE_PYTHON
    computeEngine: SPARK
    rationale: "Large dataset requiring distributed processing"
    codeExample: |
      from transforms.api import transform, Input, Output
      from pyspark.sql import functions as F
      
      @transform.spark.using(
          concepts=Input('/K12Education/MasterData/mathematicalConcepts'),
          problems=Input('/K12Education/MasterData/problems'),
          mapping=Output('/K12Education/Mapping/conceptProblemMapping')
      )
      def create_concept_problem_mapping(concepts, problems, mapping):
          concepts_df = concepts.dataframe()
          problems_df = problems.dataframe()
          
          result = (problems_df
              .join(concepts_df, problems_df.primaryConceptId == concepts_df.conceptId, 'inner')
              .select(
                  F.concat(F.col('conceptId'), F.lit('_'), F.col('problemId')).alias('mappingId'),
                  F.col('conceptId'),
                  F.col('problemId'),
                  F.col('difficultyAlignment'),
                  F.lit(True).alias('isPrimary'),
                  F.col('weightFactor'),
                  F.current_date().alias('effectiveDate')
              )
          )
          
          mapping.write_dataframe(result)

anti_patterns:
  - id: "AP-TR-001"
    name: "Spark for Small Data"
    description: "Using Spark engine for datasets under 10M rows"
    badExample: |
      @transform.spark.using(...)  # For 100K row dataset
      def small_transform(...):
          ...
    goodExample: |
      @transform.using(...)  # Lightweight for small data
      def small_transform(...):
          ...
    severity: MEDIUM

  - id: "AP-TR-002"
    name: "Incremental Without APPEND Input"
    description: "Using @incremental with SNAPSHOT inputs"
    badExample: |
      @incremental()
      @transform.using(
          source=Input('/path/snapshot-dataset'),  # Uses SNAPSHOT
          ...
      )
    problem: "Falls back to full recomputation; no benefit"
    severity: MEDIUM

integration_points:
  - component: Dataset
    relationship: "Transform reads from and writes to Datasets"
    dataFlowDirection: BIDIRECTIONAL
  - component: Pipeline
    relationship: "Transform is a processing unit within Pipeline"
    dataFlowDirection: INTERNAL
  - component: OntologySync
    relationship: "Transform output feeds OntologySync backing"
    dataFlowDirection: OUTBOUND

pipelineBuilderTransformTypes:
  tableTransforms:
    - name: "Filter"
      description: "Filter rows based on conditions"
    - name: "Aggregate"
      description: "Group rows and apply aggregation functions"
    - name: "Aggregate over window"
      description: "Window-based aggregations"
    - name: "Pivot"
      description: "Convert rows to columns"
    - name: "Unpivot"
      description: "Convert columns to rows"
    - name: "Drop columns"
      description: "Remove specified columns"
    - name: "Drop duplicates"
      description: "Remove duplicate rows"
    - name: "Select columns"
      description: "Select specific columns"
    - name: "Rename columns"
      description: "Rename specified columns"
    - name: "Sort"
      description: "Order rows"
    - name: "Top rows"
      description: "Limit to first N rows"
  structuralTransforms:
    - name: "Inner join"
      description: "Standard inner join"
    - name: "Left join"
      description: "Left outer join"
    - name: "Outer join"
      description: "Full outer join"
    - name: "Anti join"
      description: "Return rows with no match"
    - name: "Semi join"
      description: "Return rows with matches"
    - name: "Cross join"
      description: "Cartesian product"
    - name: "Union by name"
      description: "Combine tables by column names"
```

---

## FILE 4: SESSION_4_OUTPUT_OntologySync.yaml

```yaml
# =============================================================================
# SESSION_4_OUTPUT_OntologySync.yaml
# Palantir Foundry OntologySync Component - Complete Reference
# Generated: 2026-02-03
# Consumer: Claude-Opus-4.5 (Claude Code CLI)
# =============================================================================

metadata:
  componentName: OntologySync
  version: "1.0.0"
  lastUpdated: "2026-02-03"
  sources:
    - url: "https://www.palantir.com/docs/foundry/object-indexing/funnel-batch-pipelines"
      accessDate: "2026-02-03"
    - url: "https://www.palantir.com/docs/foundry/object-link-types/create-object-type"
      accessDate: "2026-02-03"
    - url: "https://www.palantir.com/docs/foundry/object-link-types/create-link-type"
      accessDate: "2026-02-03"

official_definition:
  definition: |
    OntologySync is the process by which tabular Foundry datasets are 
    synchronized to the Ontology's object storage backend, translating 
    dataset rows and columns into objects, properties, and links. The 
    synchronization is orchestrated by the Object Data Funnel microservice.
  source: "https://www.palantir.com/docs/foundry/object-indexing/funnel-batch-pipelines"
  verificationDate: "2026-02-03"
  syncPipelineSteps:
    - step: 1
      name: "Changelog Job"
      description: "Computes data difference, creates changelog with delta only"
    - step: 2
      name: "Merge Changes Job"
      description: "Joins all changelogs plus user edits by primary key"
    - step: 3
      name: "Indexing Job"
      description: "Converts merged data to index files for object databases"
    - step: 4
      name: "Hydration"
      description: "Downloads index files to search nodes for querying"
  pipelineTypes:
    livePipelines:
      description: "Update object types with new datasource data"
      trigger: "Runs on every datasource update; also every 6 hours if edits detected"
    replacementPipelines:
      description: "Provisioned when schema changes occur"
      trigger: "New properties, changed types, or datasource replacement"

semantic_definition:
  analogy: |
    OntologySync is like a library cataloging system. When new books (dataset rows) 
    arrive, the system creates catalog cards (objects) with properties (title, author, 
    ISBN) and links them to related items (subject categories, series). The catalog 
    stays in sync as the collection changes.
  similarConcepts:
    - name: "Database Foreign Key Constraint"
      similarity: "Both establish relationships between entities"
      difference: "OntologySync is declarative, supports multiple sync modes"
    - name: "CDC (Change Data Capture)"
      similarity: "Both track and propagate data changes"
      difference: "OntologySync targets Ontology objects specifically"
  oppositeConcepts:
    - name: "Manual Object Creation"
      description: "Creating objects one-by-one without sync"
    - name: "Static Snapshot"
      description: "One-time data load without ongoing sync"

structural_schema:
  $schema: "https://json-schema.org/draft/2020-12/schema"
  $id: "https://palantir.com/foundry/schema/ontology-sync"
  title: "Foundry OntologySync Schema"
  type: object
  required:
    - objectTypeId
    - backingDatasource
    - primaryKeyMapping
  properties:
    objectTypeId:
      type: string
      description: "Target object type API name"
    backingDatasource:
      type: object
      required:
        - datasetReference
        - syncMode
      properties:
        datasetReference:
          type: string
          description: "Dataset RID or path"
        syncMode:
          type: string
          enum: [BATCH, STREAMING]
          default: BATCH
        conflictResolution:
          type: string
          enum: [APPLY_USER_EDITS, APPLY_MOST_RECENT]
          default: APPLY_USER_EDITS
    primaryKeyMapping:
      type: object
      required:
        - sourceColumn
        - objectTypeProperty
      properties:
        sourceColumn:
          type: string
          description: "Column name in backing dataset"
        objectTypeProperty:
          type: string
          description: "Property API name in object type"
    propertyMappings:
      type: array
      items:
        type: object
        required:
          - sourceColumn
          - targetProperty
        properties:
          sourceColumn:
            type: string
          targetProperty:
            type: string
          transformExpression:
            type: string
            description: "Optional transformation expression"
    linkMappings:
      type: array
      items:
        $ref: "#/$defs/LinkMapping"
    editsConfig:
      type: object
      properties:
        enabled:
          type: boolean
          default: false
        trackHistory:
          type: boolean
          default: false
        materialization:
          type: object
          properties:
            enabled:
              type: boolean
              default: false
            datasetReference:
              type: string
  $defs:
    LinkMapping:
      type: object
      required:
        - linkTypeId
        - mappingType
      properties:
        linkTypeId:
          type: string
        mappingType:
          type: string
          enum: [FOREIGN_KEY, JOIN_TABLE, OBJECT_BACKED]
        foreignKeyConfig:
          type: object
          properties:
            sourceColumn:
              type: string
              description: "Foreign key column in this object's dataset"
            targetObjectType:
              type: string
            targetPrimaryKey:
              type: string
        joinTableConfig:
          type: object
          properties:
            joinDatasetReference:
              type: string
            sourceKeyColumn:
              type: string
            targetKeyColumn:
              type: string
            autoGenerate:
              type: boolean
              default: false

decision_tree:
  title: "OntologySync Configuration Decision Flow"
  linkMappingSelection:
    nodes:
      - id: start
        question: "What is the relationship cardinality?"
        options:
          - condition: "One-to-one or Many-to-one"
            next: checkEditRequirement
          - condition: "Many-to-many"
            action: "Use JOIN_TABLE mapping"
      - id: checkEditRequirement
        question: "Do users need to edit links?"
        yes: useJoinTable
        no: useForeignKey
      - id: useForeignKey
        action: "Use FOREIGN_KEY mapping"
        characteristics:
          - "Simple configuration"
          - "No separate dataset required"
          - "Link stored as property"
        terminal: true
      - id: useJoinTable
        action: "Use JOIN_TABLE mapping"
        characteristics:
          - "Supports user edits"
          - "Requires separate dataset"
          - "Can auto-generate"
        terminal: true
  linkMappingComparison:
    FOREIGN_KEY:
      cardinality: "One-to-one, Many-to-one"
      storage: "Property on object"
      userEdits: "Not supported"
      useCase: "Simple parent-child relationships"
    JOIN_TABLE:
      cardinality: "Many-to-many"
      storage: "Separate dataset"
      userEdits: "Supported"
      useCase: "Complex relationships requiring edits"
    OBJECT_BACKED:
      cardinality: "Many-to-one with metadata"
      storage: "Intermediary object type"
      userEdits: "Supported"
      useCase: "Links with additional properties"

validation_rules:
  errors:
    - id: "OS-E001"
      severity: ERROR
      rule: "Primary key must be unique across all records"
      description: "Duplicate primary keys cause sync pipeline failures"
    - id: "OS-E002"
      severity: ERROR
      rule: "Primary keys must be deterministic"
      description: "Non-deterministic keys cause edit loss and link breaks"
    - id: "OS-E003"
      severity: ERROR
      rule: "Streaming datasources do not support user edits"
      description: "Edits only available for batch-synced objects"
    - id: "OS-E004"
      severity: ERROR
      rule: "Foreign key must reference valid target primary key"
      description: "Orphan foreign keys create broken links"
  warnings:
    - id: "OS-W001"
      severity: WARNING
      rule: "Schema changes may trigger replacement pipeline"
      description: "New properties or type changes require full reindex"
    - id: "OS-W002"
      severity: WARNING
      rule: "User edit throughput limited to 10,000 objects per Action"
      description: "Higher limits available via support request"
    - id: "OS-W003"
      severity: WARNING
      rule: "Sync propagation delay should be monitored"
      description: "Configure alerts for freshness thresholds"

canonical_examples:
  - id: "concept-object-sync"
    scenario: "Mathematical Concept Object Type Sync"
    description: "Syncs mathematical concepts dataset to Ontology"
    configuration:
      objectTypeId: mathematicalConcept
      displayName: "Mathematical Concept"
      backingDatasource:
        datasetReference: "/K12Education/MasterData/mathematicalConcepts"
        syncMode: BATCH
      primaryKeyMapping:
        sourceColumn: conceptId
        objectTypeProperty: conceptId
      propertyMappings:
        - sourceColumn: conceptId
          targetProperty: conceptId
        - sourceColumn: conceptName
          targetProperty: conceptName
        - sourceColumn: gradeLevel
          targetProperty: gradeLevel
        - sourceColumn: domain
          targetProperty: domain
        - sourceColumn: standardCode
          targetProperty: standardCode
        - sourceColumn: difficultyLevel
          targetProperty: difficultyLevel
      editsConfig:
        enabled: false
        rationale: "Master data managed by curriculum team; no user edits"

  - id: "student-object-sync"
    scenario: "Student Object Type Sync with Edits"
    description: "Syncs student records with user edit support"
    configuration:
      objectTypeId: student
      displayName: "Student"
      backingDatasource:
        datasetReference: "/K12Education/MasterData/students"
        syncMode: BATCH
        conflictResolution: APPLY_USER_EDITS
      primaryKeyMapping:
        sourceColumn: studentId
        objectTypeProperty: studentId
      propertyMappings:
        - sourceColumn: studentId
          targetProperty: studentId
        - sourceColumn: firstName
          targetProperty: firstName
        - sourceColumn: lastName
          targetProperty: lastName
        - sourceColumn: gradeLevel
          targetProperty: currentGradeLevel
        - sourceColumn: enrollmentDate
          targetProperty: enrollmentDate
      editsConfig:
        enabled: true
        trackHistory: true
        materialization:
          enabled: true
          datasetReference: "/K12Education/Materialized/studentEdits"

  - id: "concept-problem-link-sync"
    scenario: "Concept-Problem Mapping OntologySync"
    description: "Many-to-many link between concepts and problems"
    configuration:
      linkTypeId: conceptProblemMapping
      displayName: "Concept Problem Mapping"
      sourceObjectType: mathematicalConcept
      targetObjectType: problem
      mappingType: JOIN_TABLE
      joinTableConfig:
        joinDatasetReference: "/K12Education/Mapping/conceptProblemMapping"
        sourceKeyColumn: conceptId
        targetKeyColumn: problemId
        autoGenerate: false
      editsConfig:
        enabled: true
        rationale: "Teachers may need to reassign problems to concepts"

  - id: "student-concept-progress-link"
    scenario: "Student-Concept Progress Link (Foreign Key)"
    description: "Links students to concepts they have mastered"
    configuration:
      linkTypeId: studentConceptMastery
      displayName: "Student Concept Mastery"
      sourceObjectType: studentLearningRecord
      targetObjectType: mathematicalConcept
      mappingType: FOREIGN_KEY
      foreignKeyConfig:
        sourceColumn: conceptId
        targetObjectType: mathematicalConcept
        targetPrimaryKey: conceptId

anti_patterns:
  - id: "AP-OS-001"
    name: "Non-Deterministic Primary Keys"
    description: "Using auto-generated IDs that change on rebuild"
    badExample:
      scenario: "Using row number or random UUID as primary key"
      code: |
        df = df.withColumn("objectId", F.monotonically_increasing_id())
    problem: "Edit loss, link breaks, duplicate objects on rebuild"
    goodExample:
      scenario: "Using natural business key"
      code: |
        df = df.withColumn("objectId", F.col("studentId"))
    severity: CRITICAL

  - id: "AP-OS-002"
    name: "Schema Transformation in Ontology"
    description: "Renaming/transforming columns in Ontology Manager"
    badExample:
      scenario: "Mapping raw column 'STUDENT_ID' directly to property"
    problem: "Ontology becomes dependent on raw schema; hard to maintain"
    goodExample:
      scenario: "Clean data in pipeline, sync clean dataset to Ontology"
    severity: MEDIUM

  - id: "AP-OS-003"
    name: "Missing Sync Health Monitoring"
    description: "No alerts on sync pipeline failures or delays"
    badExample:
      scenario: "Sync configured without monitoring view"
    problem: "Silent failures; stale data; broken user experience"
    goodExample:
      scenario: "Monitoring view with failure and freshness alerts"
    severity: HIGH

integration_points:
  - component: Dataset
    relationship: "Dataset is backing source for Ontology objects"
    dataFlowDirection: INBOUND
    requirements:
      - "Unique primary key column"
      - "Deterministic primary keys"
      - "Supported data types"

  - component: Pipeline
    relationship: "Pipeline prepares clean data for sync"
    dataFlowDirection: UPSTREAM
    bestPractice: "Transform raw data in pipeline before syncing"

  - component: Transform
    relationship: "Transform creates backing dataset"
    dataFlowDirection: UPSTREAM

  - component: ObjectDataFunnel
    relationship: "Funnel orchestrates sync pipelines"
    dataFlowDirection: INTERNAL
    responsibilities:
      - "Changelog computation"
      - "User edit merging"
      - "Indexing orchestration"
      - "Hydration management"

  - component: Monitoring
    relationship: "Monitoring Views track sync health"
    dataFlowDirection: OBSERVABILITY
    metrics:
      - "Pipeline failures"
      - "Invalid records"
      - "Sync propagation delay"

objectDataFunnel:
  description: |
    The Object Data Funnel is a microservice responsible for orchestrating 
    data writes into the Ontology. It reads from datasources, processes 
    user edits, indexes data, and keeps indexed data up-to-date.
  capabilities:
    - "Incremental computation (delta processing)"
    - "Changelog tracking with APPEND transactions"
    - "User edit merging by primary key"
    - "Offset tracking for consistency"
  streamingSupport:
    indexingOrder: "Records indexed in order written"
    strategy: "Most recent update wins"
    checkpointFrequency: "~1 second (Flink checkpointing)"
    throughputLimit: "2 MB/s per object type"
```

---

---

## Streaming Pipeline Patterns

> Source: Ontology.md Section 15 — Streaming Pipeline Patterns

Foundry supports near-real-time data ingestion and Ontology indexing through streaming pipelines, complementing batch transforms for use cases requiring low-latency data freshness.

```yaml
streaming_pipelines:
  architecture:
    source: "Streaming Data Connection (Kafka, Kinesis, Azure Event Hubs, PubSub)"
    processing: "Spark Structured Streaming or Funnel Streaming"
    sink: "Foundry Dataset → Funnel → Ontology (Object Storage v2)"
    latency: "Seconds to low minutes (platform-dependent)"

  funnel_streaming:
    description: "Near-real-time dataset-to-Ontology indexing"
    configuration:
      mode: STREAMING
      primary_key_mapping: "Dataset column → ObjectType primary key"
      property_mapping: "Dataset columns → ObjectType properties"
      change_detection: "Row-level change tracking (insert/update/delete)"
    behavior:
      insert: "New primary key → create new object"
      update: "Existing primary key → update object properties"
      delete: "Tombstone record → mark object for deletion"
      ordering: "Events processed in order within partition key"

  spark_structured_streaming:
    description: "Custom streaming transforms with PySpark"
    python: |
      from transforms.api import transform, Input, Output, incremental

      @incremental()
      @transform(
          input_stream=Input("/datasets/kafka_raw_events"),
          output_ds=Output("/datasets/processed_events"),
      )
      def compute(input_stream, output_ds):
          df = input_stream.dataframe("streaming")
          df = df \
              .withColumn("event_time", F.from_json("payload", event_schema)) \
              .withColumn("processed_at", F.current_timestamp())
          output_ds.write_dataframe(
              df,
              mode="append",
              trigger={"processingTime": "30 seconds"},
          )

  data_connection_streaming:
    sources:
      kafka:
        config:
          bootstrap_servers: "broker1:9092,broker2:9092"
          topics: ["events", "transactions"]
          consumer_group: "foundry-ingestion"
          offset_reset: "earliest"
          serialization: "JSON | AVRO | PROTOBUF"
      kinesis:
        config:
          stream_name: "my-kinesis-stream"
          region: "us-east-1"
          shard_iterator_type: "TRIM_HORIZON | LATEST"
      event_hubs:
        config:
          namespace: "my-namespace.servicebus.windows.net"
          event_hub_name: "my-hub"
          consumer_group: "$Default"

  monitoring:
    metrics:
      - "Ingestion lag (seconds behind source)"
      - "Throughput (records/second)"
      - "Error rate (failed records / total records)"
      - "Checkpoint progress (latest committed offset)"
    alerts:
      - "Lag exceeds threshold → notify pipeline owner"
      - "Error rate exceeds threshold → pause ingestion"
```

---

## Incremental Pipeline Configuration

> Source: Ontology.md Section 15 — Incremental Pipeline Configuration

Incremental pipelines process only new or changed data since the last build, reducing compute cost and build time for large datasets.

```yaml
incremental_pipelines:
  modes:
    append_only:
      description: "Only new rows added; no updates or deletes"
      decorator: "@incremental(snapshot_inputs=[])"
      use_case: "Event logs, audit trails, sensor readings"
      python: |
        from transforms.api import transform, incremental, Input, Output

        @incremental()
        @transform(
            input_ds=Input("/datasets/raw_events"),
            output_ds=Output("/datasets/processed_events"),
        )
        def compute(input_ds, output_ds):
            df = input_ds.dataframe("added")
            df = df.withColumn("enriched", F.upper(F.col("event_type")))
            output_ds.write_dataframe(df, mode="append")

    upsert:
      description: "Insert new rows and update existing rows by key"
      use_case: "Slowly changing dimensions, entity updates"
      python: |
        @incremental(require_incremental=True)
        @transform(
            input_ds=Input("/datasets/employee_updates"),
            output_ds=Output("/datasets/employee_current"),
        )
        def compute(input_ds, output_ds):
            new_data = input_ds.dataframe("added")
            modified_data = input_ds.dataframe("modified")
            all_changes = new_data.union(modified_data)
            output_ds.write_dataframe(
                all_changes,
                mode="merge",
                merge_key="employee_id",
            )

    snapshot_with_incremental:
      description: "Combine snapshot (full) and incremental inputs"
      use_case: "Join incremental events with slowly changing lookup table"
      python: |
        @incremental(snapshot_inputs=["lookup_table"])
        @transform(
            events=Input("/datasets/new_events"),
            lookup_table=Input("/datasets/reference_data"),
            output_ds=Output("/datasets/enriched_events"),
        )
        def compute(events, lookup_table, output_ds):
            new_events = events.dataframe("added")
            lookup_df = lookup_table.dataframe()  # Always full snapshot
            enriched = new_events.join(
                lookup_df,
                on="category_id",
                how="left",
            )
            output_ds.write_dataframe(enriched, mode="append")

  funnel_incremental:
    description: "Incremental indexing from dataset to Ontology"
    configuration:
      mode: INCREMENTAL
      change_detection: "Row-level diff based on primary key"
      behavior:
        new_rows: "Create new objects in Ontology"
        modified_rows: "Update existing object properties"
        deleted_rows: "Remove objects from Ontology index"
    advantages:
      - "Faster indexing (process only changes)"
      - "Lower compute cost"
      - "Reduced Object Storage write amplification"
    prerequisites:
      - "Dataset must have stable primary key column"
      - "Dataset must support change tracking (transaction log)"
```

---

## Multi-Dataset Objects (MDO)

> Source: Ontology.md Section 15 — Multi-Dataset Objects

Multi-Dataset Objects allow a single ObjectType to be backed by multiple datasets, merging properties from different data sources into a unified object view.

```yaml
multi_dataset_objects:
  definition: "ObjectType backed by MULTI mode with additional datasets"
  purpose: "Combine data from multiple pipelines into a single object view"

  configuration:
    backing_mode: MULTI
    primary_dataset:
      dataset: "/datasets/employee_core"
      provides: ["employeeId", "fullName", "department", "level"]
    additional_datasets:
      - dataset: "/datasets/employee_compensation"
        join_key: "employee_id"
        provides: ["baseSalary", "bonus", "stockGrant"]
      - dataset: "/datasets/employee_performance"
        join_key: "employee_id"
        provides: ["performanceScore", "lastReviewDate"]

  merge_behavior:
    join_type: "LEFT JOIN from primary to additional"
    conflict_resolution: "Primary dataset wins for overlapping columns"
    null_handling: "Properties from missing additional rows are null"
    indexing: "All datasets re-indexed when any changes"

  use_cases:
    - "Combining core HR data with separate compensation feed"
    - "Merging real-time sensor data with batch analytics"
    - "Joining internal data with external enrichment sources"

  limitations:
    - "Primary key must exist in primary dataset"
    - "Additional datasets join on primary key only"
    - "Write-back targets primary dataset by default"
    - "All datasets must be in the same Foundry project (or shared)"
    - "Performance scales with number of additional datasets"

  anti_patterns:
    - name: "Too Many Additional Datasets"
      problem: "5+ additional datasets cause slow indexing and complex debugging"
      solution: "Pre-join datasets in transforms; use MDO only for cross-pipeline merges"

    - name: "Using MDO Instead of LinkType"
      problem: "MDO for related but distinct entities (Employee + Department)"
      solution: "Use LinkType for entity relationships; MDO for single-entity data merge"

    - name: "Inconsistent Primary Keys Across Datasets"
      problem: "Different ID formats or missing keys cause silent data loss"
      solution: "Normalize primary key format in transforms before MDO configuration"
```

---

## Code Pattern Identification Rules

> Source: Ontology.md Section 15 — Code Pattern Identification Rules

```yaml
identification_rules:
  - pattern: "ETL pipeline (Extract-Transform-Load)"
    mapping: "Data Connection → Python Transforms → Funnel"
    confidence: HIGH

  - pattern: "Spark job / PySpark script"
    mapping: "Python Transform with @transform_df"
    confidence: HIGH

  - pattern: "Incremental data processing"
    mapping: "@incremental decorator"
    confidence: HIGH

  - pattern: "Database CDC (Change Data Capture)"
    mapping: "Streaming Data Connection + Incremental Funnel"
    confidence: HIGH

  - pattern: "Batch ETL cron job"
    mapping: "Scheduled Python Transform"
    confidence: HIGH

  - pattern: "Data lake ingestion"
    mapping: "Data Connection (S3/GCS) → Dataset"
    confidence: HIGH

  pipeline_pattern_mapping:
    "Spring Batch job": "Scheduled Python Transform"
    "Airflow DAG": "Foundry build pipeline (dependency DAG)"
    "dbt model": "SQL Transform or Python Transform"
    "Kafka consumer": "Streaming Data Connection"
    "JDBC import script": "Batch Data Connection (JDBC)"
    "File watcher": "Data Connection with file system sync"
```

---

## Data Connection Sources

> Source: Ontology.md Section 15 — Data Connection

```yaml
data_connection:
  purpose: "Ingest data from external systems into Foundry datasets"
  sync_types:
    Batch: "Periodic full or incremental sync"
    Streaming: "Continuous real-time ingestion"
    Virtual: "Query external source on-demand (no data copy)"
  sources:
    databases: ["JDBC (PostgreSQL, MySQL, Oracle, SQL Server)", "ODBC"]
    cloud_storage: ["S3", "GCS", "Azure Blob", "ADLS"]
    apis: ["REST API", "GraphQL", "SOAP"]
    streaming: ["Kafka", "Kinesis", "Azure Event Hubs"]
    files: ["SFTP", "FTP", "Local upload"]
    saas: ["Salesforce", "SAP", "Workday", "ServiceNow"]
```

---

## Summary

These 4 YAML files plus supplementary sections provide a complete machine-readable reference for Palantir Foundry's Data Pipeline Layer components:

| File | Component | Key Topics |
|------|-----------|------------|
| SESSION_4_OUTPUT_Dataset.yaml | Dataset | Transaction types, schema, path vs RID, data types |
| SESSION_4_OUTPUT_Pipeline.yaml | Pipeline | Pipeline Builder vs Code, Batch/Incremental/Streaming, scheduling |
| SESSION_4_OUTPUT_Transform.yaml | Transform | Decorators, engines, incremental processing, transform types |
| SESSION_4_OUTPUT_OntologySync.yaml | OntologySync | Object Data Funnel, link mapping, writeback, health monitoring |

Each file contains all 8 required sections with K-12 Education domain examples, follows the specified naming conventions (camelCase for API names, Title Case for display names), and is structured for consumption by Claude-Opus-4.5.