# Component: Property

> **Version:** 1.0.0 | **Last Verified:** 2026-02-06
> **Source:** https://www.palantir.com/docs/foundry/object-link-types/properties-overview

---

## 1. formal_definition

```yaml
formal_definition:
  component: "Property"
  version: "1.0.0"
  last_verified: "2026-02-06"
  source: "https://www.palantir.com/docs/foundry/object-link-types/properties-overview"

  necessary_conditions:
    - id: NC-P-1
      condition: "ObjectType의 속성(attribute)을 표현한다"
      test: "이 데이터가 특정 ObjectType 인스턴스의 특성을 기술하는가?"
      violation_means: "독립 엔티티라면 ObjectType으로 모델링"

    - id: NC-P-2
      condition: "유효한 Base Type에 매핑 가능하다"
      test: "Palantir 지원 baseType(String, Integer, Short, Long, Byte, Boolean, Float, Double, Decimal, Date, Timestamp, Geopoint, Geoshape, Array, Struct, Vector, MediaReference, Attachment, TimeSeries, GeotimeSeriesReference, CipherText, MandatoryControl -- 22종) 중 하나에 매핑되는가?"
      violation_means: "데이터 구조 재설계 필요"

    - id: NC-P-3
      condition: "소속 ObjectType의 backing dataset 컬럼에 매핑 가능하다"
      test: "Dataset에 해당 컬럼이 존재하거나 Transform으로 생성 가능한가?"
      violation_means: "Derived/computed field는 Transform에서 처리"

  sufficient_conditions:
    - id: SC-P-1
      condition: "단일 값이며 소속 ObjectType 없이 독립 의미가 없다"
      rationale: "Scalar attribute with no independent identity = Property"

    - id: SC-P-2
      condition: "소속 ObjectType과 동일한 생명주기를 가진다"
      rationale: "Created/deleted with parent = embedded attribute"

  boundary_conditions:
    - id: BC-P-1
      scenario: "복합 구조 데이터 (여러 필드로 구성)"
      guidance: "필드 수 <=10이고 depth 1이면 Struct, 아니면 별도 ObjectType"
      threshold: "필드 수 >10 또는 nested structure 필요 -> ObjectType"
      examples:
        struct: "Address (street, city, zip, country) -> Struct (4 fields, flat)"
        objecttype: "OrderItem (product, qty, price, discount, tax, ...) -> ObjectType (독립 조회 필요)"

    - id: BC-P-2
      scenario: "다른 ObjectType을 참조하는 값"
      guidance: "FK-like 단방향 참조만 필요하면 Property, 양방향이면 LinkType"
      threshold: "역방향 조회 빈도 >10%이면 LinkType"
      examples:
        property: "createdByUserId (단방향 기록용) -> String Property"
        linktype: "assignedTo (User <-> Task 양방향 필요) -> LinkType"

    - id: BC-P-3
      scenario: "여러 ObjectType에서 동일 속성 필요"
      guidance: "2+ ObjectType에서 동일 의미면 SharedProperty, 아니면 각각 local"
      threshold: "사용 OT >=3 + 의미 동일 -> SharedProperty 승격; 2 OT = SharedProperty.md BC-SP-1 참조 (메타데이터 변경 빈도로 판단) [V4 수정]"
```

### Formal Definition Summary

| Condition Type | ID | 핵심 질문 |
|---------------|----|----------|
| Necessary | NC-P-1 | 특정 ObjectType 인스턴스의 특성인가? |
| Necessary | NC-P-2 | 22종 baseType 중 하나에 매핑 가능한가? |
| Necessary | NC-P-3 | Backing dataset 컬럼에 매핑 가능한가? |
| Sufficient | SC-P-1 | 독립 의미 없이 부모 OT에 종속된 단일 값인가? |
| Sufficient | SC-P-2 | 부모 OT와 동일 생명주기인가? |
| Boundary | BC-P-1 | 복합 구조 -> Struct vs ObjectType |
| Boundary | BC-P-2 | 참조 값 -> Property vs LinkType |
| Boundary | BC-P-3 | 공유 속성 -> Local vs SharedProperty |

---

## 2. official_definition

**Source**: https://www.palantir.com/docs/foundry/object-link-types/properties-overview

> "Properties are the attributes that define an object type. Each property has a base type that determines what types of values it can hold and what operations can be performed on it."

Properties store the actual data values for each object instance. The **base type** determines:
- Valid values the property can contain
- Available operations (search, sort, aggregate)
- Indexing behavior
- Action type parameter compatibility

### Value Types Layer

Properties can be wrapped with **Value Types** to add semantic constraints above the base type layer. Value Types provide:

- **Semantic meaning**: e.g., a String property wrapped with `EmailAddress` Value Type enforces email format
- **Constraint inheritance**: regex, enum, range constraints defined once, applied to all properties using that Value Type
- **Cross-property consistency**: multiple properties across different ObjectTypes share the same Value Type for uniform validation
- **Examples**: Currency codes (ISO 4217), email format, URL format, phone number pattern

**Reference**: https://www.palantir.com/docs/foundry/object-link-types/value-types-overview

> Value Types add a semantic layer above base types. Where a base type says "this is a String," a Value Type says "this is an Email Address that must match a specific format."

### Property Metadata Attributes

| Attribute | Description | Default |
|-----------|-------------|---------|
| `apiName` | Programmatic identifier (camelCase) | Required |
| `displayName` | Human-readable name | Required |
| `description` | Detailed description text | Optional |
| `baseType` | Data type (22 supported types) | Required |
| `required` | Whether value must be present | `false` |
| `visibility` | UI display level (PROMINENT/NORMAL/HIDDEN) | `NORMAL` |
| `editOnly` | Property visible only in edit mode, hidden in read view | `false` |
| `conditionalFormatting` | Rules for dynamic visual formatting based on value | `null` |
| `renderHints` | Indexing and display configuration | See below |
| `constraints` | Validation rules (enum, range, regex, etc.) | `null` |
| `sharedProperty` | Reference to SharedProperty apiName | `null` |
| `valueType` | Reference to Value Type definition | `null` |

**Edit-Only Properties**: Properties marked `editOnly: true` are displayed only when creating or editing an object. They are hidden from the default read/detail view. Use case: internal processing fields, admin-only fields, or staging data that should not appear in normal workflows.

**Required Properties**: When `required: true`, the property must have a non-null value for every object instance. The primaryKey property is implicitly always required. Actions that create objects must provide values for all required properties.

**Conditional Formatting**: Allows dynamic visual styling (color, icon, text format) of property values based on rules. Common patterns:
- Status-based coloring (e.g., red for "overdue", green for "completed")
- Threshold-based formatting (e.g., bold if value > 100)
- Enum-based icons

---

## 3. semantic_definition

| Paradigm | Equivalent Concept | Mapping Notes |
|----------|-------------------|---------------|
| **OOP** | Instance field/attribute | Property = field declaration |
| **RDBMS** | Column | Property = column definition with type |
| **RDF/OWL** | owl:DatatypeProperty / owl:ObjectProperty | Property defines predicate |
| **JSON Schema** | Property in properties object | With type and constraints |
| **TypeScript** | Property in interface/type | With type annotation |

### Semantic Precision Table

| Palantir Concept | OOP (Java) | RDBMS (SQL) | RDF/OWL | JSON Schema |
|-----------------|------------|-------------|---------|-------------|
| Property apiName | field name | column name | predicate URI | property key |
| baseType | field type | column type | range declaration | `type` keyword |
| required: true | @NotNull | NOT NULL | owl:minCardinality 1 | `required` array |
| constraints.enum | enum type | CHECK IN (...) | owl:oneOf | `enum` keyword |
| constraints.regex | @Pattern | CHECK REGEXP | xsd:pattern | `pattern` keyword |
| renderHints.searchable | @Indexed | CREATE INDEX | n/a | n/a |
| sharedProperty | interface field | shared column def | rdfs:subPropertyOf | $ref |
| valueType | wrapper type | DOMAIN | owl:DatatypeProperty + facets | format + pattern |
| visibility: HIDDEN | private field | n/a (always visible) | n/a | readOnly |

---

## 4. structural_schema

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
      # NOTE: Decimal은 standalone property base type으로 사용 불가.
      # 공식 문서: "All field types are valid base types except for Map, Decimal, and Binary types."
      # Decimal은 Struct field type으로만 유효. [V3 검증 반영]
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
      # NOTE: MandatoryControl은 별도 기능 카테고리이며 base type이 아님. [V3 검증 반영]

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

  editOnly:
    type: boolean
    default: false
    description: "When true, property is visible only in edit/create mode"

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

  conditionalFormatting:
    type: object
    description: "Dynamic visual formatting rules based on property value"
    properties:
      rules:
        type: array
        items:
          type: object
          properties:
            condition:
              type: object
              description: "Condition expression (operator, value)"
            style:
              type: object
              description: "Visual style to apply (color, icon, bold, etc.)"

  sharedProperty:
    type: string
    description: "Reference to SharedProperty apiName"

  valueType:
    type: object
    description: "Optional Value Type wrapper for semantic constraints"
    properties:
      valueTypeId:
        type: string
        description: "Reference to Value Type definition (apiName or RID)"
      constraints:
        type: object
        description: "Value Type specific constraints (regex, enum, range, etc.)"
        properties:
          regex:
            type: string
            description: "Pattern constraint from Value Type"
          enum:
            type: array
            description: "Allowed values from Value Type"
          range:
            type: object
            description: "Min/max bounds from Value Type"
          format:
            type: string
            description: "Semantic format hint (email, url, iso-date, etc.)"
```

### BaseType Category Reference

| Category | Types | Count |
|----------|-------|-------|
| Primitive | String, Integer, Short, Long, Byte, Boolean, Float, Double, Decimal | 9 |
| Time | Date, Timestamp | 2 |
| Geospatial | Geopoint, Geoshape | 2 |
| Complex | Array, Struct, Vector | 3 |
| Reference | MediaReference, Attachment, TimeSeries, GeotimeSeriesReference | 4 |
| Special | CipherText, MandatoryControl | 2 |
| **Total** | | **22** |

---

## 5. quantitative_decision_matrix

### Matrix A: "Is this a Property?" (vs ObjectType / Struct)

```yaml
quantitative_decision_matrix_a:
  question: "이 데이터를 Property로 모델링해야 하는가?"

  signals:
    - signal: "독립 식별성 (Independent Identity)"
      metric: "고유 PK로 단독 식별 가능 여부"
      thresholds:
        strong_property: "PK 없음, 부모 OT 통해서만 접근"
        gray_zone: "Synthetic PK 생성 가능하나 단독 조회 드묾"
        strong_objecttype: "자연 PK 존재 + 독립 조회 >30%"
      weight: CRITICAL

    - signal: "속성 수 (Attribute Count)"
      metric: "관련 필드 수"
      thresholds:
        strong_property: "1개 (단일 값)"
        gray_zone: "2-10개 (Struct 후보)"
        strong_objecttype: ">10개 + 독립 관계"
      weight: HIGH

    - signal: "생명주기 독립성"
      metric: "부모 OT와 독립적 CRUD 필요 여부"
      thresholds:
        strong_property: "부모와 동일 생명주기"
        gray_zone: "부분적 독립 (soft delete 등)"
        strong_objecttype: "완전 독립 CRUD"
      weight: HIGH

    - signal: "관계 참여 (Relationship Participation)"
      metric: "다른 OT와의 LinkType 수"
      thresholds:
        strong_property: "0개 (관계 불필요)"
        gray_zone: "1개 (단방향 참조)"
        strong_objecttype: ">=2개 (양방향 + 다중 관계)"
      weight: HIGH

    - signal: "독립 조회 비율"
      metric: "전체 접근 중 부모 OT 없이 직접 조회하는 비율"
      thresholds:
        strong_property: "<10%"
        gray_zone: "10-30%"
        strong_objecttype: ">30%"
      weight: MEDIUM

    - signal: "권한 분리"
      metric: "별도 ACL 필요 여부"
      thresholds:
        strong_property: "부모 권한 상속 충분"
        gray_zone: "-"
        strong_objecttype: "별도 ACL 필수"
      weight: "LOW (있으면 결정적)"

  decision_rule: |
    NC-P-1~3 전부 충족 + CRITICAL signal이 strong_property
    -> Property 확정

    NC-P-1~3 충족 + gray_zone 다수
    -> Struct 검토 (필드 <=10, depth 1)

    NC 위반 또는 CRITICAL signal이 strong_objecttype
    -> ObjectType으로 승격

  quick_reference:
    - scenario: "단일 값, 부모 종속, 관계 없음"
      decision: "Property"
      confidence: "HIGH"
    - scenario: "2-10 필드 묶음, depth 1, 부모 종속"
      decision: "Struct Property"
      confidence: "HIGH"
    - scenario: "단일 값이나 2+ OT에서 동일 의미"
      decision: "SharedProperty 후보"
      confidence: "MEDIUM"
    - scenario: ">10 필드 또는 독립 조회 >30%"
      decision: "ObjectType으로 승격"
      confidence: "HIGH"
    - scenario: "FK 값, 역방향 조회 >10%"
      decision: "LinkType으로 전환"
      confidence: "MEDIUM"
```

### Matrix B: "Which baseType?" (Type Selection)

```
START: What baseType should this Property use?
|
+---> Is it TEXT data?
|     +-- Short text (< 256 chars) -> String
|     +-- Long text/prose -> String + renderHints.longText: true
|     +-- Encrypted sensitive -> CipherText
|     +-- Pattern constrained -> String + constraints.regex
|     +-- Semantic type needed -> String + Value Type (email, URL, etc.)
|
+---> Is it NUMERIC data?
|     +-- Whole number?
|     |   +-- Range -128 to 127 -> Byte
|     |   +-- Range -32,768 to 32,767 -> Short
|     |   +-- Range -2,147,483,648 to 2,147,483,647 -> Integer  [RECOMMENDED]
|     |   +-- Range -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 -> Long
|     |       WARNING: JavaScript Number.MAX_SAFE_INTEGER = 9,007,199,254,740,991
|     |       Values above this LOSE PRECISION in browser/frontend contexts
|     |       Use String for IDs that may exceed MAX_SAFE_INTEGER
|     |
|     +-- Decimal number?
|         +-- Approximate OK -> Double  [RECOMMENDED]
|         |   WARNING: Cannot use as Action parameter
|         +-- Financial/exact precision -> Decimal
|         |   WARNING: Cannot use as Action parameter
|         +-- Lower precision sufficient -> Float
|             WARNING: Cannot use as Action parameter
|
+---> Is it TRUE/FALSE?
|     +-- Boolean
|         WARNING: Discouraged for primary key
|
+---> Is it DATE/TIME?
|     +-- Date only (no time component) -> Date
|     +-- Date with time -> Timestamp
|
+---> Is it LOCATION?
|     +-- Single point -> Geopoint (WGS 84: "lat,long" or geohash)
|     +-- Shape/polygon -> Geoshape (GeoJSON RFC 7946)
|
+---> Is it a COLLECTION?
|     +-- List of primitives -> Array<baseType>
|     |   +-- Note: Cannot contain nulls
|     |   +-- Note: No nested arrays in OSv2
|     |
|     +-- Structured object -> Struct
|         +-- Constraints: depth=1, max 10 fields, no nested structs
|         +-- Querying: ES array matching semantics (see runtime_caveats)
|
+---> Is it for ML/EMBEDDINGS?
|     +-- Vector (max 2048 dimensions, KNN queries only)
|         +-- OSv2 only
|
+---> Is it a FILE/MEDIA reference?
      +-- Media file -> MediaReference
      +-- Attached document -> Attachment
      +-- Time series data -> TimeSeries
      +-- Geotime series -> GeotimeSeriesReference
```

### Numeric Type Decision Table

| Scenario | Type | Range | Action Parameter? | Notes |
|----------|------|-------|-------------------|-------|
| Small counter (0-127) | Byte | -128 ~ 127 | Yes | Rarely used |
| Port number, year | Short | -32,768 ~ 32,767 | Yes | |
| General count/quantity | **Integer** | -2.1B ~ 2.1B | **Yes** | **Default choice** |
| Large counter, epoch ms | Long | -9.2E18 ~ 9.2E18 | Yes | JS precision risk |
| Percentage, ratio | **Double** | ~15 sig digits | **No** | Approx OK |
| Money, financial | Decimal | Arbitrary precision | **No** | Exact |
| Sensor reading | Float | ~7 sig digits | **No** | Low precision |

### Action Parameter Restrictions

| BaseType | Allowed as Action Parameter? | Max List Size |
|----------|------------------------------|--------------|
| String | Yes | 10,000 (primitive list) |
| Integer | Yes | 10,000 |
| Short | Yes | 10,000 |
| Long | Yes | 10,000 |
| Byte | Yes | 10,000 |
| Boolean | Yes | 10,000 |
| Date | Yes | 10,000 |
| Timestamp | Yes | 10,000 |
| **Float** | **No** | - |
| **Double** | **No** | - |
| **Decimal** | **No** | - |
| Geopoint | Yes | 10,000 |
| Geoshape | Yes | 10,000 |
| Array | Partial (depends on subtype) | - |
| Struct | Yes (with limits) | - |
| **Vector** | **No** | - |
| Object Reference | Yes | 1,000 (reference list) |

### BaseType Quick Reference

| Use Case | Recommended BaseType | Notes |
|----------|---------------------|-------|
| UUID identifier | String | Pattern: UUID constraint |
| Count/quantity | Integer | Safe for most cases |
| Money/currency | Decimal | Exact precision |
| Percentage/ratio | Double | Approximate OK |
| Status/category | String | With enum constraint |
| Email address | String + Value Type | Regex-validated |
| URL | String + Value Type | Format-validated |
| Creation date | Timestamp | Include time for precision |
| Encrypted field | CipherText | Access-controlled |
| Coefficients array | Array<Double> | For polynomial terms |
| Structured sub-data | Struct | Max 10 fields, depth 1 |
| Concept embeddings | Vector | 768-2048 dimensions typical |
| Grade level (1-12) | Integer | With range constraint |
| Difficulty (1-5) | Integer | With enum constraint |
| Korean text | String | UTF-8 supported |
| LaTeX notation | String | Escape handling in app |

---

## 6. validation_rules

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
      forbidden:
        - "ontology"
        - "object"
        - "property"
        - "link"
        - "relation"
        - "rid"
        - "primaryKey"
        - "typeId"

  baseType_compatibility:
    primaryKey_allowed:
      - "String"           # Recommended
      - "Integer"          # Recommended
      - "Short"            # Discouraged
      - "Long"             # Discouraged (JS precision)
      - "Byte"             # Discouraged
      - "Boolean"          # Discouraged
      - "Date"             # Discouraged
      - "Timestamp"        # Discouraged
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
      - "Byte"              # [V3 추가] 공식 문서 확인
      - "Short"             # [V3 추가] 공식 문서 확인
      - "GeotimeSeriesReference"  # [V3 추가] geo time-series 포함

  required_metadata:
    - rule: "required_property_must_have_value"
      condition: "required: true"
      enforcement: "Actions creating objects MUST supply value for required properties"
      error: "Required property {apiName} must be provided"

    - rule: "editOnly_visibility_interaction"
      condition: "editOnly: true"
      enforcement: "editOnly properties are hidden in read view regardless of visibility setting"
      note: "editOnly takes precedence over visibility: PROMINENT"

  valueType_constraints:
    - rule: "valueType_must_match_baseType"
      condition: "valueType is defined"
      enforcement: "Value Type's underlying base type must match property's baseType"
      error: "Value Type {valueTypeId} expects baseType {expected}, got {actual}"

    - rule: "valueType_constraints_override"
      condition: "valueType.constraints defined"
      enforcement: "Value Type constraints are applied AFTER base type validation"
      note: "Local property constraints can further restrict (but not loosen) Value Type constraints"

    - rule: "valueType_regex_applied"
      condition: "valueType.constraints.regex defined"
      enforcement: "Every value must match the Value Type regex pattern"
      error: "Value '{value}' does not match Value Type pattern '{regex}'"

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
    forbidden_field_types:
      - "Struct"      # No nested structs
      - "Array"       # No arrays within struct fields
      - "Vector"      # No vectors within struct fields

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
    note: "Setting sortable/selectable/lowCardinality without searchable=true will cause validation error"

  renderHints_searchable_false:
    - rule: "unsearchable_property_cannot_filter"
      condition: "renderHints.searchable: false"
      enforcement: "Property excluded from search, filter, and sort operations in Object Explorer"
      note: "Useful for large text blobs or internal-only data"

  conditionalFormatting_rules:
    - rule: "formatting_requires_supported_baseType"
      supported_types:
        - "String"
        - "Integer"
        - "Short"
        - "Long"
        - "Double"
        - "Boolean"
        - "Date"
        - "Timestamp"
      error: "Conditional formatting not supported for baseType {baseType}"

  limits:
    max_properties_per_objecttype: 2000
    action_primitive_list_max: 10000
    action_object_reference_list_max: 1000
    action_edit_size_osv1: "32KB"
    action_edit_size_osv2: "3MB"
```

---

## 7. canonical_examples

### Domain-Independent Examples

#### Example 1: Primary Key Property (Generic Entity ID)

```yaml
entityId:
  apiName: "entityId"
  displayName: "Entity ID"
  description: "Unique identifier for the entity"
  baseType: "String"
  required: true
  visibility: "HIDDEN"
  renderHints:
    searchable: true
    identifier: true
  constraints:
    uuid: true
```

**Design Rationale**: String with UUID constraint is the safest primary key pattern. It avoids Long/Integer overflow issues and provides global uniqueness.

#### Example 2: Status Property with Enum Constraint

```yaml
status:
  apiName: "status"
  displayName: "Status"
  description: "Current lifecycle status of the record"
  baseType: "String"
  required: true
  visibility: "PROMINENT"
  renderHints:
    searchable: true
    selectable: true
    lowCardinality: true
  constraints:
    enum: ["ACTIVE", "INACTIVE", "ARCHIVED", "DELETED"]
  conditionalFormatting:
    rules:
      - condition: { operator: "eq", value: "ACTIVE" }
        style: { color: "green", icon: "check-circle" }
      - condition: { operator: "eq", value: "INACTIVE" }
        style: { color: "gray", icon: "pause-circle" }
      - condition: { operator: "eq", value: "DELETED" }
        style: { color: "red", icon: "x-circle" }
```

**Design Rationale**: Low cardinality string with enum is preferred over Integer codes for readability. `lowCardinality: true` optimizes ES aggregation queries.

#### Example 3: Email Property with Value Type

```yaml
contactEmail:
  apiName: "contactEmail"
  displayName: "Contact Email"
  description: "Primary contact email address"
  baseType: "String"
  required: false
  visibility: "NORMAL"
  renderHints:
    searchable: true
  valueType:
    valueTypeId: "emailAddress"
    constraints:
      regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      format: "email"
```

**Design Rationale**: Value Type wrapper ensures all email properties across the ontology share the same validation pattern. Changing the regex in the Value Type definition propagates to all properties using it.

#### Example 4: Address as Struct Property

```yaml
address:
  apiName: "address"
  displayName: "Address"
  description: "Mailing address"
  baseType: "Struct"
  required: false
  visibility: "NORMAL"
  structSchema:
    street:
      baseType: "String"
      description: "Street address line"
    city:
      baseType: "String"
      description: "City name"
    state:
      baseType: "String"
      description: "State or province"
    zipCode:
      baseType: "String"
      description: "Postal/ZIP code"
    country:
      baseType: "String"
      description: "Country code (ISO 3166-1 alpha-2)"
  # 5 fields, depth 1 -> suitable for Struct
```

**Design Rationale**: Address has 5 flat fields and is always accessed in the context of its parent object. No independent queries needed, so Struct is appropriate. If addresses needed independent lifecycle or cross-entity deduplication, promote to ObjectType.

#### Example 5: Edit-Only Internal Processing Property

```yaml
internalNotes:
  apiName: "internalNotes"
  displayName: "Internal Notes"
  description: "Admin notes visible only during editing"
  baseType: "String"
  required: false
  editOnly: true
  visibility: "NORMAL"
  renderHints:
    longText: true
```

**Design Rationale**: `editOnly: true` ensures this administrative field does not clutter the read view. Users only see it when actively creating or editing the object.

---

### Domain-Specific: K-12 Education

#### Example 6: Primary Key Property (Equation ID)

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

#### Example 7: Searchable Text Property (Math Notation)

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

#### Example 8: Enum Constrained Property (Difficulty Level)

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

#### Example 9: Array Property (Solution Steps)

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

#### Example 10: Struct Property (Polynomial Terms)

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

#### Example 11: Vector Property (Semantic Embeddings)

```yaml
conceptEmbedding:
  apiName: "conceptEmbedding"
  displayName: "Concept Embedding"
  description: "768-dimensional semantic embedding for similarity search"
  baseType: "Vector"
  vectorDimension: 768
  # OSv2 only, max 2048 dimensions
  # Query via KNN only -- no exact match or range queries
```

#### Example 12: Geopoint Property (School Location)

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

## 8. anti_patterns

### Anti-Pattern 1: Float/Double as Primary Key

**Severity: CRITICAL**

```yaml
# WRONG: Floating point as primary key
properties:
  equationValue:
    baseType: "Double"
    # Used as primary key - FORBIDDEN

# WHY IT'S WRONG:
# - Floating point comparison is imprecise (0.1 + 0.2 != 0.3)
# - Cannot guarantee uniqueness
# - Primary key operations will fail
# - OSv2 rejects this at schema definition time

# CORRECT: Use String or Integer
properties:
  equationId:
    baseType: "String"
    constraints:
      uuid: true
```

**Resolution**: Always use String (UUID), Integer, or Long for primary keys. String with UUID is the safest universal pattern.

---

### Anti-Pattern 2: Deeply Nested Struct

**Severity: CRITICAL**

```yaml
# WRONG: Attempting nested structs
terms:
  baseType: "Struct"
  structSchema:
    innerTerm:
      baseType: "Struct"  # NOT ALLOWED - depth > 1
      structSchema:
        value: ...

# WHY IT'S WRONG:
# - Struct depth limited to 1 (Palantir hard constraint)
# - Will fail validation at schema definition time

# CORRECT: Flatten structure or use multiple properties
termCoefficient:
  baseType: "Double"
termVariable:
  baseType: "String"
termExponent:
  baseType: "Integer"
```

**Resolution**: Flatten to multiple properties, or if the structure truly needs nesting, promote to a separate ObjectType with a LinkType relationship.

---

### Anti-Pattern 3: Unindexed Property Used in Filters

**Severity: HIGH**

```yaml
# WRONG: Filtering on non-searchable property
gradeLevel:
  baseType: "Integer"
  renderHints:
    searchable: false
# User tries to filter "show all Grade 8 problems"
# -> Query returns empty or scans all objects (performance degradation)

# CORRECT: Enable searchable for filtered properties
gradeLevel:
  baseType: "Integer"
  renderHints:
    searchable: true
    selectable: true   # For aggregations
    lowCardinality: true  # Only 12 grades
```

**Resolution**: Any property used in search, filter, sort, or aggregation MUST have `searchable: true`. Add `lowCardinality` for fields with few distinct values.

---

### Anti-Pattern 4: Long as JavaScript-Exposed Identifier

**Severity: HIGH**

```yaml
# WRONG: Long for IDs used in frontend
problemNumber:
  baseType: "Long"
  # Value: 9007199254740993
  # JavaScript max safe integer: 9007199254740991
  # -> Precision loss in browser!

# CORRECT: Use String for large identifiers
problemNumber:
  baseType: "String"
  constraints:
    regex: "^[0-9]+$"
```

**Resolution**: If a Long value might exceed `9,007,199,254,740,991` (Number.MAX_SAFE_INTEGER), use String instead. This affects all frontend applications, APIs returning JSON, and any JavaScript-based processing.

---

### Anti-Pattern 5: Using Property for Bidirectional Relationships

**Severity: HIGH**

```yaml
# WRONG: FK property for bidirectional navigation
student:
  properties:
    teacherId:
      baseType: "String"
      description: "ID of assigned teacher"
    # Frontend needs: "show all students for teacher X"
    # -> Requires full scan of all students!

# CORRECT: Use LinkType for bidirectional relationships
linkTypes:
  studentTeacher:
    source: "Student"
    target: "Teacher"
    cardinality: "many-to-one"
    # Efficient: teacher.linkedStudents() uses index
```

**Resolution**: If reverse navigation frequency exceeds ~10% of total access patterns, use a LinkType. FK-style properties are only appropriate for write-once audit fields (e.g., `createdByUserId`) where reverse lookup is rare.

---

### Anti-Pattern 6: Overloaded Struct (>10 Fields)

**Severity: MEDIUM**

```yaml
# WRONG: Struct with too many fields
orderDetails:
  baseType: "Struct"
  structSchema:
    productName: { baseType: "String" }
    productCode: { baseType: "String" }
    quantity: { baseType: "Integer" }
    unitPrice: { baseType: "Decimal" }
    discount: { baseType: "Double" }
    tax: { baseType: "Double" }
    subtotal: { baseType: "Decimal" }
    currency: { baseType: "String" }
    warehouse: { baseType: "String" }
    shippingMethod: { baseType: "String" }
    trackingNumber: { baseType: "String" }
    # 11 fields -> exceeds max 10!

# CORRECT: Promote to ObjectType
# OrderItem as ObjectType with its own properties + LinkType to Order
```

**Resolution**: Struct max is 10 fields. If you need more, promote to an ObjectType with a LinkType relationship. Even if under 10 fields, consider promotion if independent queries or lifecycle management is needed.

---

### Anti-Pattern 7: Missing Enum on Low-Cardinality String

**Severity: LOW**

```yaml
# WRONG: No constraint on known-set values
status:
  baseType: "String"
  renderHints:
    searchable: true
  # Accepts any string -> "active", "Active", "ACTIVE", "actve" all valid

# CORRECT: Constrain with enum
status:
  baseType: "String"
  renderHints:
    searchable: true
    lowCardinality: true
  constraints:
    enum: ["ACTIVE", "INACTIVE", "ARCHIVED"]
```

**Resolution**: Always apply enum constraints for properties with a known, finite set of values. This prevents data quality issues from typos and inconsistent casing.

---

### Anti-Pattern 8: Using Double for Action-Editable Financial Data

**Severity: MEDIUM**

```yaml
# WRONG: Double used in Action parameter context
price:
  baseType: "Double"
  # Then trying to use in an Action:
  # -> "Float, Double, Decimal cannot be Action parameters"
  # -> Action definition fails

# CORRECT: Use Integer (cents) or String with parsing
priceCents:
  baseType: "Integer"
  description: "Price in cents (divide by 100 for display)"
  # Can be used in Actions
```

**Resolution**: If a numeric property must be editable via Actions, use Integer (store in smallest unit like cents/mills) or String. Float/Double/Decimal are forbidden as Action parameters.

---

## 9. integration_points

```yaml
integration_points:
  objectType:
    relationship: "Property BELONGS TO ObjectType"
    constraints:
      - "Every ObjectType must have at least one property (primaryKey)"
      - "Property apiName unique within ObjectType scope"
      - "Maximum 2000 properties per ObjectType"
    forward_reference: "See ObjectType.md for full ObjectType specification"

  sharedProperty:
    relationship: "Property CAN REFERENCE SharedProperty"
    mechanism: "sharedProperty field contains SharedProperty apiName"
    inheritance:
      - "Metadata inherited from SharedProperty"
      - "Local apiName preserved"
      - "Render hints can be overridden locally"
    promotion_criteria:
      - ">=2 ObjectTypes use same property with identical semantics"
      - "Central metadata management desired"
      - "Interface-based polymorphism required"
    forward_reference: "See SharedProperty.md for promotion criteria and management"

  valueTypes:
    relationship: "Property CAN BE WRAPPED WITH Value Type"
    mechanism: "valueType.valueTypeId references Value Type definition"
    behavior:
      - "Value Type provides semantic constraints above base type"
      - "Constraints from Value Type are applied during validation"
      - "Local constraints can further restrict (not loosen) Value Type constraints"
      - "Changing Value Type definition propagates to all using properties"
    common_value_types:
      - "emailAddress: String + email regex"
      - "phoneNumber: String + phone pattern"
      - "currencyCode: String + ISO 4217 enum"
      - "url: String + URL format validation"
      - "countryCode: String + ISO 3166-1 enum"
    reference: "https://www.palantir.com/docs/foundry/object-link-types/value-types-overview"

  constraints:
    relationship: "Property CAN HAVE Constraints"
    types:
      - "enum: restricts to specific values"
      - "range: min/max bounds"
      - "regex: pattern matching"
      - "rid: valid RID format"
      - "uuid: valid UUID format"
      - "uniqueness: array elements must be unique"

  renderHints:
    relationship: "Property HAS RenderHints"
    performance_impact:
      searchable: "adds raw index (Elasticsearch) -- required for filtering"
      sortable: "adds raw index (requires searchable) -- enables sort operations"
      selectable: "adds raw index (requires searchable) -- enables aggregation"
      lowCardinality: "optimizes for few distinct values -- term aggregation"
      longText: "enables full-text search tokenization"
      keywords: "keyword-level indexing (not tokenized)"
      identifier: "marks as identifying property in UI"
    dependency_chain: "sortable/selectable/lowCardinality -> requires searchable"

  actions:
    relationship: "Property USED IN Actions"
    restrictions:
      - "Float, Double, Decimal, Byte, Short, geo time-series cannot be Action parameters [V3 수정]"
      - "Vector arrays not supported in Actions"
      - "Max 10,000 elements in primitive list parameters"
      - "Max 1,000 elements in object reference list parameters"
      - "Max edit size: 32KB (OSv1) / 3MB (OSv2)"

  linkType:
    relationship: "Property VALUE MAY REFERENCE another ObjectType"
    distinction:
      property: "Stores FK value as String -- unidirectional, no indexing on target side"
      linkType: "First-class bidirectional relationship with indexing on both sides"
    decision_guide: "If reverse lookup needed >10% of access patterns, use LinkType instead"
    forward_reference: "See LinkType.md for relationship modeling patterns (Phase 2 - not yet documented)"

  backingDataset:
    relationship: "Property MAPS TO Dataset Column"
    constraints:
      - "Property apiName maps to dataset column name (possibly transformed)"
      - "baseType must be compatible with dataset column type"
      - "Transform pipeline may rename/convert columns to match property definition"
```

---

## 10. migration_constraints

### OSv2 Breaking Changes

| Constraint | OSv1 Behavior | OSv2 Behavior | Impact |
|------------|--------------|---------------|--------|
| Nested arrays | Allowed | **Forbidden** | Array<Array<T>> must be flattened |
| Array nulls | Allowed | **Forbidden** | Null elements must be filtered in Transform |
| Duplicate PK | Silent corruption | **Indexing failure** | Must guarantee PK uniqueness |
| Edit size limit | 32KB | 3MB | Larger edits possible, but bounded |
| Vector support | Not available | Available | New property type, 2048 max dims |

### BaseType Change After Creation

```
WARNING: Changing a property's baseType after creation is NOT a simple operation.

Scenario: Integer -> Long (range expansion)
  -> May work in some cases (type widening)
  -> But downstream Actions/Widgets referencing this property may break

Scenario: String -> Integer (type change)
  -> REQUIRES: new property + data migration Transform + old property deprecation
  -> Cannot change in-place

Scenario: Adding Value Type to existing property
  -> Safe if all existing values comply with Value Type constraints
  -> Existing violating values will cause validation errors

Recommended Migration Pattern:
  1. Create new property with desired baseType
  2. Write Transform to populate new property from old
  3. Update all Actions, Widgets, Functions referencing old property
  4. Mark old property visibility: HIDDEN
  5. After full migration verified, remove old property
```

### Struct Field Changes

| Operation | Allowed? | Notes |
|-----------|----------|-------|
| Add new field | Yes | New field will be null for existing objects |
| Remove field | **No** | Must keep field, set values to null |
| Rename field | **No** | Add new field + migrate data |
| Change field type | **No** | Add new field with new type + migrate |
| Reorder fields | Yes | Display order only, no data impact |

### SharedProperty Migration

```
Local Property -> SharedProperty:
  1. Create SharedProperty with matching spec
  2. Update each ObjectType's property to reference sharedProperty
  3. Verify metadata inheritance is correct
  4. WARNING: Once shared, changing SharedProperty affects ALL referencing ObjectTypes

SharedProperty -> Local Property:
  1. Remove sharedProperty reference from individual properties
  2. Copy inherited metadata to local property definition
  3. Safe operation, no data migration needed
```

### Primary Key Migration (OSv2)

```
CRITICAL: Primary key CANNOT be changed in OSv2 after ObjectType creation.

If PK change is required:
  1. Create new ObjectType with desired PK
  2. Migrate all data via Transform
  3. Recreate all LinkTypes pointing to the old ObjectType
  4. Update all Actions, Widgets, Functions
  5. Delete old ObjectType

This is a high-risk, high-effort operation. Choose PK carefully at design time.
```

---

## 11. runtime_caveats

### Struct Querying Semantics (Elasticsearch Array Matching)

```
CAVEAT: When a Struct property is stored as Array<Struct>, Elasticsearch
flattens all struct fields into parallel arrays internally.

Example data:
  contacts: [
    { name: "Alice", role: "admin" },
    { name: "Bob",   role: "viewer" }
  ]

ES internal representation:
  contacts.name: ["Alice", "Bob"]
  contacts.role: ["admin", "viewer"]

Query: "Find objects where contacts has name=Alice AND role=viewer"
Result: MATCHES! (incorrect -- Alice is admin, not viewer)
Reason: ES matches across array elements, not within individual structs

Workaround:
  - Use nested queries if available in your Object Storage version
  - Or model as separate ObjectType with LinkType for precise matching
  - Or add a computed "contactKey" property (e.g., "Alice:admin") for exact lookup
```

### Array<Struct> Filtering Behavior

```
CAVEAT: Filtering on Array<Struct> properties tests ALL elements.

Example:
  tags: [
    { category: "math", confidence: 0.9 },
    { category: "physics", confidence: 0.3 }
  ]

Filter: tags.confidence > 0.5
Result: MATCHES (because 0.9 > 0.5, even though 0.3 is not)
Semantics: "at least one element matches" (OR across array)

There is no built-in "all elements must match" (AND across array) filter.

Workaround:
  - Pre-compute a "minConfidence" property in Transform
  - Or model tags as separate ObjectType for precise per-element filtering
```

### Vector Query Limitations

```
CAVEAT: Vector properties support ONLY KNN (K-Nearest Neighbors) queries.

Supported:
  - findNearestNeighbors(queryVector, k=10) -> top-k similar objects

NOT Supported:
  - Exact match: vector == [0.1, 0.2, ...]
  - Range query: vector[0] > 0.5
  - Aggregation: avg(vector)
  - Sorting by vector distance (except within KNN result)

Additional constraints:
  - Max 2048 dimensions
  - OSv2 only
  - Cannot be inside Array
  - Cannot be Action parameter
  - Query vector must have same dimension as stored vectors
```

### renderHints.searchable=false Impact

```
CAVEAT: Setting searchable: false excludes the property from:

Excluded operations:
  - Object Explorer filtering
  - Object Explorer search
  - Sort operations
  - Aggregation queries
  - Function on Objects filtering
  - Workshop filter widgets

Still available:
  - Direct object detail view (reading the value)
  - Action parameter (if baseType allows)
  - Transform processing

Use cases for searchable: false:
  - Large text blobs (performance optimization)
  - Internal IDs not needed in search
  - Binary/encoded data
  - Embedding vectors (use Vector type instead for KNN)

WARNING: Changing searchable from false to true requires re-indexing,
which may take significant time for large object sets.
```

### Long Value JavaScript Precision Loss

```
CAVEAT: Long values exceeding Number.MAX_SAFE_INTEGER lose precision in JavaScript.

Number.MAX_SAFE_INTEGER = 9,007,199,254,740,991 (2^53 - 1)

Example:
  Java/Python value:  9007199254740993
  JavaScript value:   9007199254740992  (WRONG -- precision lost)

Affected contexts:
  - All browser-based UIs (Object Explorer, Workshop, Slate)
  - REST API responses consumed by JavaScript clients
  - JSON serialization (JSON spec uses IEEE 754 double)

Safe range for Long in JS contexts:
  -9,007,199,254,740,991 to 9,007,199,254,740,991

Workaround:
  - Use String baseType for identifiers that may exceed this range
  - Use Integer if range fits within +/-2,147,483,647
  - Backend-only Long values (Transform, Functions) are safe at full range
```

### Timestamp Timezone Handling

```
CAVEAT: Timestamp values are stored in UTC internally.

Behavior:
  - Input: local time is converted to UTC at write time
  - Storage: always UTC epoch milliseconds
  - Display: converted to user's timezone in UI

Implications:
  - Date-only queries (e.g., "created on 2026-01-15") may miss
    objects depending on timezone offset
  - Use Date type if time component is not needed
  - For precise date-boundary queries, use Timestamp with explicit
    UTC range (e.g., 2026-01-15T00:00:00Z to 2026-01-15T23:59:59Z)
```

### CipherText Access Control

```
CAVEAT: CipherText properties have special access semantics.

Behavior:
  - Value is encrypted at rest
  - Only users/groups with explicit decrypt permission can read
  - Other users see the property exists but cannot read its value
  - Search/filter/sort NOT supported on CipherText
  - Cannot be used as primary key

Use cases:
  - SSN, credit card numbers, health records
  - Any PII requiring column-level encryption
```

### Decimal Precision in Aggregations

```
CAVEAT: Decimal provides exact precision for storage but aggregations
may behave differently.

Behavior:
  - Individual values: exact (no floating-point drift)
  - SUM aggregation: exact (Elasticsearch uses BigDecimal internally)
  - AVG aggregation: may lose precision (division result)
  - Division operations in Functions: depends on implementation

Recommendation:
  - Use Decimal for financial amounts and exact-precision requirements
  - Be aware that computed/aggregated results may not maintain full precision
  - For Actions: Decimal is FORBIDDEN as parameter -- use Integer (cents) + divide
```

---

## Appendix: Source URLs Registry

| Topic | URL | Verified |
|-------|-----|----------|
| Properties Overview | https://www.palantir.com/docs/foundry/object-link-types/properties-overview | 2026-02-06 |
| Property Metadata | https://www.palantir.com/docs/foundry/object-link-types/property-metadata | 2026-02-06 |
| Base Types | https://www.palantir.com/docs/foundry/object-link-types/base-types | 2026-02-06 |
| Structs Overview | https://www.palantir.com/docs/foundry/object-link-types/structs-overview | 2026-02-06 |
| Value Types Overview | https://www.palantir.com/docs/foundry/object-link-types/value-types-overview | 2026-02-06 |
| Value Type Constraints | https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints | 2026-02-06 |
| Shared Property Overview | https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview | 2026-02-06 |
| Action Scale/Limits | https://www.palantir.com/docs/foundry/action-types/scale-property-limits | 2026-02-06 |
| OSv2 Breaking Changes | https://www.palantir.com/docs/foundry/object-backend/object-storage-v2-breaking-changes | 2026-02-06 |
