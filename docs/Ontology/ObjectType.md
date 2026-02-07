# Palantir Ontology Component: ObjectType

> **Version:** 1.0.0 | **Last Verified:** 2026-02-06
> **Source:** [Object Types Overview](https://www.palantir.com/docs/foundry/object-link-types/object-types-overview) | [Create Object Type](https://www.palantir.com/docs/foundry/object-link-types/create-object-type) | [Object Type Metadata](https://www.palantir.com/docs/foundry/object-link-types/object-type-metadata)

---

## Table of Contents

1. [formal_definition](#1-formal_definition)
2. [official_definition](#2-official_definition)
3. [semantic_definition](#3-semantic_definition)
4. [structural_schema](#4-structural_schema)
5. [quantitative_decision_matrix](#5-quantitative_decision_matrix)
6. [validation_rules](#6-validation_rules)
7. [canonical_examples](#7-canonical_examples)
8. [anti_patterns](#8-anti_patterns)
9. [integration_points](#9-integration_points)
10. [migration_constraints](#10-migration_constraints)
11. [runtime_caveats](#11-runtime_caveats)

---

## 1. formal_definition

> ObjectType을 정의하기 위한 **필요조건(NC)**, **충분조건(SC)**, **경계조건(BC)**을 형식화한다.
> 이 섹션은 "이 개념을 ObjectType으로 모델링해야 하는가?"에 대한 판단 근거를 제공한다.

```yaml
formal_definition:
  component: "ObjectType"
  version: "1.0.0"
  last_verified: "2026-02-06"
  source: "https://www.palantir.com/docs/foundry/object-link-types/object-types-overview"

  # ═══════════════════════════════════════════════════════════════
  # NECESSARY CONDITIONS (필요조건)
  # 하나라도 위반하면 ObjectType이 될 수 없다.
  # ALL must be satisfied; violation of ANY single NC → NOT ObjectType.
  # ═══════════════════════════════════════════════════════════════

  necessary_conditions:
    - id: NC-OT-1
      condition: "실세계 Entity 또는 Event를 표현한다"
      test: "이 개념이 물리적/논리적으로 독립 존재하거나 발생하는가?"
      violation_means: "Property 또는 Struct로 모델링"
      rationale: >
        Palantir Ontology의 근본 설계 원칙은 "ObjectType은 real-world entity 또는 event의
        schema definition"이라는 것이다. 계산 결과, 집계값, 임시 상태 등은 해당되지 않는다.

    - id: NC-OT-2
      condition: "고유 식별자(Primary Key)가 존재하거나 생성 가능하다"
      test: "자연 키(natural key) 또는 합성 UUID로 각 인스턴스를 유일 식별할 수 있는가?"
      violation_means: "다른 ObjectType의 속성으로 임베딩"
      rationale: >
        ObjectType의 각 인스턴스(Object)는 반드시 유일하게 식별되어야 한다.
        PK가 존재할 수 없는 개념(예: "분위기", "난이도 수준")은 Property나 enum으로 모델링한다.

    - id: NC-OT-3
      condition: "하나 이상의 Backing Datasource에 매핑 가능하다"
      test: "이 개념의 데이터가 Dataset으로 존재하거나 생성 가능한가?"
      violation_means: "Derived Property 또는 computed field로 처리"
      rationale: >
        ObjectType은 반드시 하나 이상의 Datasource에 의해 뒷받침되어야 한다.
        순수 계산값은 Derived Property로 처리하는 것이 적절하다.

  # ═══════════════════════════════════════════════════════════════
  # SUFFICIENT CONDITIONS (충분조건)
  # 하나라도 충족하면 ObjectType임이 확정된다.
  # ANY single SC satisfied (given all NCs met) → ObjectType confirmed.
  # ═══════════════════════════════════════════════════════════════

  sufficient_conditions:
    - id: SC-OT-1
      condition: "3개 이상의 독립적 Property를 가지며, 독립 생명주기가 필요하다"
      rationale: >
        3+ properties + independent lifecycle = unambiguous ObjectType.
        충분한 속성을 보유하고 독립적으로 생성/수정/삭제되는 개념은
        반드시 독립 엔티티로 모델링해야 한다.

    - id: SC-OT-2
      condition: "2개 이상의 다른 ObjectType과 LinkType 관계가 필요하다"
      rationale: >
        Multiple relationships = entity-level modeling required.
        여러 엔티티와의 관계 참여는 해당 개념이 독립적 존재임을 입증한다.

    - id: SC-OT-3
      condition: "별도의 권한(ACL) 제어가 필요하다"
      rationale: >
        Permission boundary = must be independent entity.
        권한 경계가 필요하면 반드시 독립 ObjectType이어야 한다.
        이 조건은 LOW weight이지만 결정적(decisive)이다.

  # ═══════════════════════════════════════════════════════════════
  # BOUNDARY CONDITIONS (경계조건 / Gray Zone)
  # NC는 충족하나 SC는 미충족인 회색 영역 판단 지침.
  # ═══════════════════════════════════════════════════════════════

  boundary_conditions:
    - id: BC-OT-1
      scenario: "Property 수 1-2개, 관계 1개"
      guidance: "Property로 시작하되, 독립 조회 필요 시 ObjectType으로 승격"
      threshold: "독립 조회 빈도 > 전체 조회의 30%이면 ObjectType"
      examples:
        promote: "Tag (name만 있지만 독립 검색/필터 필수) -> ObjectType"
        demote: "Priority (High/Medium/Low 3값) -> enum Property"
      decision_factors:
        - "독립 조회 필요성이 핵심 판단 기준"
        - "향후 속성 추가 가능성도 고려"
        - "Tag처럼 다대다 관계가 필요하면 ObjectType 쪽으로 기울임"

    - id: BC-OT-2
      scenario: "항상 부모 엔티티와 함께 생성/삭제되는 하위 구조"
      guidance: "Struct Property로 모델링. 단, 독립 권한/독립 Link 필요 시 ObjectType"
      threshold: "별도 권한 요구사항이 1개 이상이면 ObjectType"
      examples:
        promote: "Address (independent lookup + geocoding relationships) -> ObjectType"
        demote: "Address (always embedded in Person, never queried alone) -> Struct"
      decision_factors:
        - "Struct는 depth 1, max 10 fields 제한이 있음"
        - "Struct는 ES array matching으로만 조회 가능 (제한적)"
        - "독립 조회가 전혀 없으면 Struct가 적합"

    - id: BC-OT-3
      scenario: "Lookup table / Reference data (변경 거의 없음)"
      guidance: "독립 조회/필터/Link 필요 시 ObjectType, 아니면 enum Property"
      threshold: "항목 수 >20 또는 항목별 속성 >=2개이면 ObjectType"
      examples:
        promote: "Country (code, name, region, population) -> ObjectType"
        demote: "DifficultyLevel (1-5 integer) -> enum Property"
      decision_factors:
        - "항목 수가 적고 속성이 1개면 enum이 단순하고 효과적"
        - "참조 데이터라도 관계가 필요하면 ObjectType"
        - "향후 속성 확장 가능성이 높으면 ObjectType 선호"

    - id: BC-OT-4
      scenario: "Mathematical Variable (x in '3x - 2 = 5')"
      guidance: "교육 도메인에서 변수 자체는 독립 identity가 없으므로 Property"
      threshold: "독립 추적/관계가 필요한 경우에만 ObjectType"
      examples:
        promote: "Variable (연구 목적으로 변수 사용 패턴 독립 추적 필요) -> ObjectType"
        demote: "Variable (방정식 속성으로만 사용) -> Property"

    - id: BC-OT-5
      scenario: "Term/Monomial ('3x' as component of polynomial)"
      guidance: "부모 Polynomial의 Struct Property로 시작"
      threshold: "독립 추적 필요 시 ObjectType으로 승격"
      examples:
        promote: "Term (교육 분석에서 항별 오류 패턴 추적) -> ObjectType"
        demote: "Term (다항식의 내부 구조로만 표현) -> Struct Property"
```

---

## 2. official_definition

**Source**: [Object Types Overview](https://www.palantir.com/docs/foundry/object-link-types/object-types-overview)

> "An **object type** is the schema definition of a real-world entity or event."

| Term | Definition |
|------|------------|
| **ObjectType** | Schema definition (type-level metadata: display name, property names, property data types, description) |
| **Object / Object Instance** | The actual primary key and property values for a specific instance |
| **Object Set** | A collection of multiple object instances representing a group of real-world entities |

### Analogy to Datasets

| Ontology Concept | Dataset Analogy |
|------------------|-----------------|
| ObjectType | Dataset schema (column definitions) |
| Object | Row in a dataset |
| Object Set | Filtered set of rows |

### ObjectType Identifiers (G8 Clarification)

> ObjectType은 두 개의 서로 다른 식별자를 가진다. 혼동하지 않아야 한다.

| Identifier | Name | Format | Mutability | Usage |
|------------|------|--------|------------|-------|
| **ObjectType RID** | Resource Identifier | `ri.ontology.main.object-type.{uuid}` | Immutable (system-generated) | System-internal reference, cross-environment linking |
| **ObjectType apiName** | API Name | PascalCase (e.g., `LinearEquation`) | Immutable after creation | API calls, OSDK code generation, programmatic access |

**Key distinctions:**
- **RID**는 시스템이 자동 생성하며, 사용자가 지정하거나 변경할 수 없다.
- **apiName**은 사용자가 생성 시 지정하며, 생성 후 변경할 수 없다 (OSv2).
- API 호출 시에는 apiName을 사용한다 (예: `GET /api/v2/ontologies/{ontologyRid}/objectTypes/{apiName}`).
- RID는 내부 시스템 참조 및 환경 간 연결에 사용된다.

**Source URL**: [Create Object Type](https://www.palantir.com/docs/foundry/object-link-types/create-object-type)

---

## 3. semantic_definition

> 다양한 패러다임에서의 ObjectType 등가 개념을 매핑한다.

| Paradigm | Equivalent Concept | Mapping Notes |
|----------|-------------------|---------------|
| **OOP** | Class | ObjectType = Class definition; Object = Instance |
| **RDBMS** | Table Schema | ObjectType = CREATE TABLE definition; Object = Row |
| **RDF/OWL** | owl:Class | ObjectType = Class in ontology; Object = Individual |
| **JSON Schema** | Object Schema | ObjectType = schema definition; Object = validated document |
| **TypeScript** | interface / type | ObjectType = type definition; Object = value conforming to type |
| **GraphQL** | Type | ObjectType = type definition; fields = Properties |
| **Domain-Driven Design** | Entity | ObjectType = Entity with identity; Object = specific entity instance |

**Semantic Role**: ObjectType defines the **intension** (definitional properties) of a concept, while Objects are the **extension** (actual instances) of that concept.

**Ontological Commitment**: ObjectType으로 정의된 개념은 Foundry Ontology 내에서 "first-class citizen"으로 존재하게 된다. 이는 해당 개념이:
- 독립적으로 조회/필터/검색 가능
- 다른 엔티티와 명시적 관계(LinkType) 형성 가능
- 별도의 권한(ACL) 제어 대상
- Actions의 대상 (생성/수정/삭제)
- Workshop, Object Explorer 등 모든 Foundry 애플리케이션에서 접근 가능

---

## 4. structural_schema

> ObjectType의 JSON Schema 정의. OSv2 기준.

```yaml
# JSON Schema Draft 2020-12 for ObjectType Definition
$schema: "https://json-schema.org/draft/2020-12/schema"
$id: "palantir-objecttype-schema-v1.0.0"
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
  # ═══════════════════════════════════════════
  # REQUIRED FIELDS
  # ═══════════════════════════════════════════

  apiName:
    type: string
    description: >
      Programmatic identifier for the ObjectType.
      이것은 ObjectType RID와 다른 식별자이다.
      - apiName: 사용자 지정, PascalCase, API 호출에 사용
      - RID: 시스템 자동생성, ri.ontology.main.object-type.{uuid} 형식
      둘 다 생성 후 변경 불가 (immutable).
    pattern: "^[A-Z][a-zA-Z0-9_]*$"  # PascalCase, starts with uppercase
    minLength: 1
    maxLength: 255  # Inferred limit
    not:
      enum:
        - "Ontology"
        - "Object"
        - "Property"
        - "Link"
        - "Relation"
        - "Rid"
        - "PrimaryKey"
        - "TypeId"
        - "OntologyObject"
    examples: ["Employee", "Product", "LinearEquation", "MathProblem"]

  displayName:
    type: string
    description: "Human-readable name shown in Foundry UI"
    minLength: 1
    examples: ["Employee", "Product", "Linear Equation"]

  pluralDisplayName:
    type: string
    description: "Plural form for collections in UI"
    examples: ["Employees", "Products", "Linear Equations"]

  primaryKey:
    type: array
    description: >
      Properties uniquely identifying each object instance.
      OSv2에서는 생성 후 변경 불가. Composite key 지원.
    items:
      type: string
    minItems: 1
    examples:
      - ["employeeId"]
      - ["equationId"]
      - ["gradeLevel", "conceptCode"]

  titleKey:
    type: string
    description: "Property used as display name for objects in UI"
    examples: ["fullName", "productName", "displayNotation"]

  backingDatasource:
    type: string
    description: >
      RID of the dataset backing this ObjectType.
      하나의 Datasource는 정확히 하나의 ObjectType만 backing할 수 있다.
    pattern: "^ri\\..*"

  # ═══════════════════════════════════════════
  # OPTIONAL FIELDS
  # ═══════════════════════════════════════════

  rid:
    type: string
    description: >
      Auto-generated Resource Identifier (system-internal).
      apiName과 구별할 것: RID는 시스템 생성, apiName은 사용자 지정.
    pattern: "^ri\\.ontology\\.main\\.object-type\\.[a-f0-9-]+$"
    readOnly: true

  description:
    type: string
    description: "Explanatory text for the ObjectType"

  status:
    type: string
    # 공식 문서에서 확인된 값만 포함 (G1 report 반영)
    # EXAMPLE, ENDORSED는 공식 문서에서 확인되지 않아 제거
    enum: ["ACTIVE", "EXPERIMENTAL", "DEPRECATED"]
    default: "EXPERIMENTAL"

  visibility:
    type: string
    enum: ["PROMINENT", "NORMAL", "HIDDEN"]
    default: "NORMAL"

  icon:
    type: string
    description: "Blueprint icon name for visual identification"

  color:
    type: string
    description: "Hex color code for visual identification"

  groups:
    type: array
    items:
      type: string
    description: "Classification labels for organization in Ontology Manager"

  aliases:
    type: array
    items:
      type: string
    description: "Additional search terms for discovery"

  typeClasses:
    type: array
    items:
      type: string
    description: "Additional metadata tags for user applications"

  properties:
    type: object
    additionalProperties:
      $ref: "#/$defs/PropertyDefinition"
    maxProperties: 2000  # OSv2 hard limit

# ═══════════════════════════════════════════
# Type Definitions
# ═══════════════════════════════════════════

$defs:
  PropertyDefinition:
    type: object
    required: ["baseType"]
    properties:
      baseType:
        type: string
        description: "See Property.md for complete baseType reference"
      description:
        type: string
      sharedProperty:
        type: string
        description: "See SharedProperty.md for cross-type consistency"
```

### Schema Notes

| Field | Immutability | Notes |
|-------|-------------|-------|
| `rid` | Immutable (auto) | 시스템 자동 생성. 변경 불가. |
| `apiName` | Immutable (user) | 생성 시 사용자 지정. 생성 후 변경 불가 (OSv2). |
| `primaryKey` | Immutable (OSv2) | 생성 후 변경 불가. See [migration_constraints](#10-migration_constraints). |
| `displayName` | Mutable | UI 표시명. 변경 가능. |
| `status` | Mutable | ACTIVE / EXPERIMENTAL / DEPRECATED만 공식 확인. |

---

## 5. quantitative_decision_matrix

> session1.md의 decision_tree를 정량 기준으로 업그레이드한 것이다.
> "이 개념을 ObjectType으로 모델링해야 하는가?"에 대한 체계적 판단 프레임워크.

### 5.1 Signal Matrix

```yaml
quantitative_decision_matrix:
  component: "ObjectType"

  signals:
    - signal: "자연 PK 존재"
      metric: "자연 키 또는 합성 UUID로 유일 식별 가능 여부"
      thresholds:
        strong_yes: "자연 키가 명확히 존재 (e.g., employeeId, ISBN)"
        gray_zone: "합성 UUID 생성 필요 (Synthetic OK)"
        strong_no: "PK 자체가 불가능한 개념"
      weight: "CRITICAL"
      note: "NC-OT-2 연동. 이 조건이 NO이면 ObjectType 불가."

    - signal: "독립 생명주기"
      metric: "부모 엔티티와 독립적으로 CRUD 가능 여부"
      thresholds:
        strong_yes: "완전히 독립적 생성/수정/삭제"
        gray_zone: "부분적 독립 (생성은 부모와 함께, 수정은 독립)"
        strong_no: "항상 부모와 함께 생성/삭제"
      weight: "HIGH"

    - signal: "관계(Link) 수"
      metric: "다른 ObjectType과의 LinkType 관계 수"
      thresholds:
        strong_yes: ">=2 relationships"
        gray_zone: "1 relationship"
        strong_no: "0 relationships"
      weight: "HIGH"

    - signal: "Property 수"
      metric: "독립적 속성(Property) 개수"
      thresholds:
        strong_yes: ">=3 properties"
        gray_zone: "1-2 properties"
        strong_no: "0 properties (pure reference)"
      weight: "MEDIUM"

    - signal: "독립 조회 비율"
      metric: "전체 조회 중 독립 조회 비율"
      thresholds:
        strong_yes: ">30%"
        gray_zone: "10-30%"
        strong_no: "<10%"
      weight: "MEDIUM"

    - signal: "별도 권한 필요"
      metric: "부모와 다른 ACL 제어 필요 여부"
      thresholds:
        strong_yes: "별도 ACL 필요"
        gray_zone: "-"
        strong_no: "부모 권한 상속으로 충분"
      weight: "LOW (결정적)"
      note: >
        Weight는 LOW이지만 결정적(decisive)이다.
        별도 권한이 필요하면 무조건 ObjectType이어야 한다 (SC-OT-3).

  decision_rule: >
    NC 전부 충족 + (1 CRITICAL Strong YES + 1 HIGH Strong YES) = ObjectType 확정.
    NC 전부 충족 + Gray Zone만 해당 = boundary_conditions 참조하여 판단.
    NC 하나라도 미충족 = ObjectType 불가.
    별도 권한 필요 = 무조건 ObjectType (SC-OT-3).
```

### 5.2 Quick Reference Table

| Signal | Strong YES | Gray Zone | Strong NO | Weight |
|--------|-----------|-----------|-----------|--------|
| 자연 PK 존재 | Yes (natural key) | Synthetic OK | No PK possible | **CRITICAL** |
| 독립 생명주기 | Yes (full CRUD) | Partial | No (parent-bound) | **HIGH** |
| 관계(Link) 수 | >=2 | 1 | 0 | **HIGH** |
| Property 수 | >=3 | 1-2 | 0 | MEDIUM |
| 독립 조회 비율 | >30% | 10-30% | <10% | MEDIUM |
| 별도 권한 필요 | Yes | - | No | LOW (decisive) |

### 5.3 Decision Rule Summary

```
IF NC-OT-1 AND NC-OT-2 AND NC-OT-3 are ALL satisfied:
  IF "별도 권한 필요" = Yes:
    → ObjectType (SC-OT-3, decisive)
  ELIF "자연 PK" = Strong YES AND ("독립 생명주기" = Strong YES OR "관계 수" = Strong YES):
    → ObjectType (CRITICAL + HIGH = confirmed)
  ELIF any SC (SC-OT-1, SC-OT-2, SC-OT-3) is satisfied:
    → ObjectType (sufficient condition met)
  ELIF all signals are in Gray Zone:
    → Consult boundary_conditions (BC-OT-1 through BC-OT-5)
  ELSE:
    → NOT ObjectType (consider Property or Struct)
ELSE:
  → NOT ObjectType (necessary condition violated)
```

### 5.4 Edge Cases (Quantitative Reasoning)

| Concept | PK | Lifecycle | Links | Props | Query% | Perms | Decision | Confidence |
|---------|-----|-----------|-------|-------|--------|-------|----------|------------|
| LinearEquation | Natural (equationId) | Independent | >=2 (Concept, Problem) | 10+ | >50% | No | **ObjectType** | HIGH |
| MathematicalConcept | Natural (conceptId) | Independent | >=3 (prereq, equation, unit) | 7+ | >60% | No | **ObjectType** | HIGH |
| Coefficient (3 in "3x") | No natural PK | Parent-bound | 0 | 1 (value) | <1% | No | **Property** | HIGH |
| Variable (x) | No independent PK | Parent-bound | 0 | 1-2 (symbol, domain) | <5% | No | **Property** | HIGH |
| Tag (name only) | Natural (tagName) | Independent | Many-to-many | 1-2 | >40% | No | **ObjectType** | MEDIUM |
| DifficultyLevel (1-5) | Enum value | N/A | 0 | 1 | <5% | No | **enum Property** | HIGH |
| Address (embedded) | No independent PK | Parent-bound | 0 | 3-5 | <5% | No | **Struct Property** | MEDIUM |
| Address (independent) | Natural (addressId) | Independent | >=1 (geocoding) | 5+ | >30% | No | **ObjectType** | HIGH |
| Country (reference) | Natural (countryCode) | Independent | >=1 | 4+ (code,name,region,pop) | >20% | No | **ObjectType** | MEDIUM |

---

## 6. validation_rules

> Machine-executable validation rules for ObjectType definitions.

```yaml
validation_rules:
  # ═══════════════════════════════════════════
  # apiName Rules
  # ═══════════════════════════════════════════

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
      forbidden:
        - "Ontology"
        - "Object"
        - "Property"
        - "Link"
        - "Relation"
        - "Rid"
        - "PrimaryKey"
        - "TypeId"
        - "OntologyObject"
      case_insensitive: true
      error: "apiName cannot be a reserved word"

    - rule: "globally_unique"
      scope: "ontology"
      error: "apiName must be unique across all object types in the ontology"

    - rule: "immutable_after_creation"
      enforcement: "OSv2"
      error: "apiName cannot be changed after ObjectType creation"

  # ═══════════════════════════════════════════
  # primaryKey Rules
  # ═══════════════════════════════════════════

  primaryKey:
    - rule: "must_be_deterministic"
      description: "Primary key values must not change between pipeline builds"
      error: "Non-deterministic primary keys cause edit loss and link disappearance"

    - rule: "must_be_unique_per_row"
      description: "Each row in datasource must have unique primary key combination"
      error: "OSv2: Duplicate primary keys cause Funnel batch pipeline errors"
      osv1_behavior: "Silent data loss, unpredictable behavior"
      osv2_behavior: "Build failure with explicit error"

    - rule: "no_null_values"
      description: "Primary key properties cannot contain null"
      error: "Null primary key values are not permitted"

    - rule: "recommended_types"
      preferred: ["String", "Integer"]
      discouraged: ["Long", "Boolean", "Date", "Timestamp"]
      forbidden:
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
        - "TimeSeries"
        - "GeotimeSeriesReference"
        # Note: CipherText, MandatoryControl도 PK로 사용 불가 (기능적 제약)
      rationale: >
        공식 문서: "The following types cannot be used as primary keys: Geopoint,
        Geoshapes, Arrays, Time series properties, Real number types (decimal,
        double, float)." Complex/Reference types도 PK로 부적합.
        [V2/V3 검증 반영: Property.md와 일치하도록 전체 목록 포함]

    - rule: "strongly_discouraged_change"
      enforcement: "OSv2"
      description: >
        Primary key CAN be changed, but all existing edits will be deleted.
        The system prompts users to acknowledge this consequence.
        [V3 수정] 이전 "immutable" → 실제로는 변경 가능하나 매우 위험.
      warning: "Changing PK triggers deletion of all existing edits. Strongly discouraged."
      migration_note: "PK 변경 시 새 ObjectType 생성 + 데이터 마이그레이션 권장"

  # ═══════════════════════════════════════════
  # backingDatasource Rules
  # ═══════════════════════════════════════════

  backingDatasource:
    - rule: "single_objecttype_per_datasource"
      description: "A datasource can only back one object type"
      error: "Phonograph2:DatasetAndBranchAlreadyRegistered"
      rationale: "1:1 mapping between Datasource and ObjectType is enforced"

    - rule: "no_maptype_columns"
      description: "Datasource may not contain MapType columns"

    - rule: "no_structtype_columns"
      description: "Datasource may not contain StructType columns"
      note: "Struct는 ObjectType Property에서 정의, Datasource 컬럼에서 직접 매핑 아님"

  # ═══════════════════════════════════════════
  # status Rules
  # ═══════════════════════════════════════════

  status:
    - rule: "valid_values_only"
      # 공식 문서에서 확인된 값만 허용 (G1 gap report 반영)
      allowed: ["ACTIVE", "EXPERIMENTAL", "DEPRECATED"]
      error: "Status must be one of ACTIVE, EXPERIMENTAL, DEPRECATED"
      note: >
        EXAMPLE 및 ENDORSED는 공식 문서에서 확인되지 않았으므로 제외.
        향후 공식 확인 시 추가 가능.

  # ═══════════════════════════════════════════
  # Limits
  # ═══════════════════════════════════════════

  limits:
    max_properties_per_objecttype: 2000  # [V3 NOTE: 공식 문서에서 미확인. session 문서 및 실무 기반 추정치]
    max_datasources_per_objecttype: 70
    max_objects_per_action: 10000
    search_around_default_limit: 100000
```

---

## 7. canonical_examples

### Example 0: Employee (Domain-Independent)

> 도메인에 독립적인 범용 예시. ObjectType의 기본 구조를 보여준다.

```yaml
# Domain-Independent: Employee ObjectType
apiName: "Employee"
displayName: "Employee"
pluralDisplayName: "Employees"
description: "A person employed by the organization"

primaryKey: ["employeeId"]
titleKey: "fullName"

status: "ACTIVE"
visibility: "PROMINENT"

groups:
  - "Human Resources"
  - "Core"

properties:
  employeeId:
    baseType: "String"
    description: "Unique employee identifier (e.g., 'EMP-00001')"

  fullName:
    baseType: "String"
    description: "Full display name"
    renderHints:
      searchable: true

  email:
    baseType: "String"
    description: "Corporate email address"
    renderHints:
      searchable: true

  department:
    baseType: "String"
    description: "Department name"

  title:
    baseType: "String"
    description: "Job title"

  hireDate:
    baseType: "Date"
    description: "Date of hire"

  isActive:
    baseType: "Boolean"
    description: "Whether currently employed"

# ObjectType 판단 근거:
#   NC-OT-1: 실세계 Entity (직원) ✅
#   NC-OT-2: 자연 PK (employeeId) ✅
#   NC-OT-3: HR 데이터셋 존재 ✅
#   SC-OT-1: 7 properties + 독립 생명주기 ✅
#   SC-OT-2: Department, Manager, Project 등 2+ 관계 ✅
#   Confidence: HIGH
```

### Example 1: Product (Domain-Independent)

> 또 하나의 범용 예시. Reference data와 관계를 포함한다.

```yaml
# Domain-Independent: Product ObjectType
apiName: "Product"
displayName: "Product"
pluralDisplayName: "Products"
description: "A product offered by the company"

primaryKey: ["productId"]
titleKey: "productName"

status: "ACTIVE"
visibility: "PROMINENT"

groups:
  - "Commerce"
  - "Catalog"

properties:
  productId:
    baseType: "String"
    description: "Unique product SKU"

  productName:
    baseType: "String"
    description: "Display name for the product"
    renderHints:
      searchable: true

  category:
    baseType: "String"
    description: "Product category"

  price:
    baseType: "Decimal"
    description: "Current price"

  description:
    baseType: "String"
    description: "Product description"
    renderHints:
      longText: true

  createdDate:
    baseType: "Timestamp"
    description: "When the product was added to catalog"

  isAvailable:
    baseType: "Boolean"
    description: "Whether product is currently available"

# ObjectType 판단 근거:
#   NC-OT-1: 실세계 Entity (제품) ✅
#   NC-OT-2: 자연 PK (SKU) ✅
#   NC-OT-3: 제품 카탈로그 데이터셋 존재 ✅
#   SC-OT-1: 7 properties + 독립 생명주기 ✅
#   SC-OT-2: Category, Supplier, Order 등 2+ 관계 ✅
#   Confidence: HIGH
```

---

### Domain-Specific: K-12 Education

> 아래 예시들은 K-12 수학 교육 도메인에 특화된 ObjectType이다.

### Example 2: LinearEquation (일차방정식)

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

# ObjectType 판단 근거:
#   NC-OT-1: 실세계 Entity (수학 문제로서의 일차방정식) ✅
#   NC-OT-2: 자연 PK (equationId - UUID) ✅
#   NC-OT-3: 방정식 데이터셋 생성 가능 ✅
#   SC-OT-1: 10 properties + 독립 생명주기 ✅
#   SC-OT-2: MathematicalConcept, MathProblem 등 2+ 관계 ✅
#   Confidence: HIGH
```

### Example 3: MathematicalConcept (수학 개념)

```yaml
# K-12 Education: Mathematical Concept ObjectType
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

# ObjectType 판단 근거:
#   NC-OT-1: 교육과정 Entity (수학 개념) ✅
#   NC-OT-2: 자연 PK (conceptId) ✅
#   NC-OT-3: 교육과정 데이터셋 존재 ✅
#   SC-OT-1: 7 properties + 독립 생명주기 ✅
#   SC-OT-2: prerequisite, equation, unit 등 3+ 관계 ✅
#   Confidence: HIGH
```

### Example 4: Polynomial (다항식)

```yaml
# K-12 Education: Polynomial ObjectType
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

# ObjectType 판단 근거:
#   NC-OT-1: 수학적 Entity (다항식) ✅
#   NC-OT-2: 자연 PK (polynomialId) ✅
#   NC-OT-3: 다항식 데이터셋 생성 가능 ✅
#   SC-OT-1: 8 properties + 독립 생명주기 ✅
#   SC-OT-2: Concept, Equation 등 2+ 관계 ✅
#   Note: terms는 Struct Property로 모델링 (BC-OT-5 적용)
#   Confidence: HIGH
```

---

## 8. anti_patterns

### Anti-Pattern 1: Over-Normalization (과도한 세분화)

> **Severity: CRITICAL** | Atomic value를 ObjectType으로 만드는 가장 흔한 실수

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
# - NC-OT-1 위반: Coefficient는 독립적 실세계 Entity가 아님
# - NC-OT-2 위반: 자연 PK가 없음 (합성 ID만으로 정당화 불가)
# - Property 1개 (value)만 존재 → SC-OT-1 미충족
# - 0개 관계 → SC-OT-2 미충족
# - 불필요한 complexity와 join overhead 발생

# ✅ CORRECT: Model as Property on parent
# On LinearEquation ObjectType:
properties:
  coefficient:
    baseType: "Double"
    description: "Coefficient of variable term"
```

**Resolution:** Property 수가 1-2개이고 독립 조회가 불필요하면 항상 Property로 모델링한다.

---

### Anti-Pattern 2: Non-Deterministic Primary Key

> **Severity: CRITICAL** | 데이터 손실을 초래하는 치명적 오류

```yaml
# ❌ WRONG: Using runtime-generated values as primary key
apiName: "MathProblem"
primaryKey: ["rowNumber"]  # Generated at pipeline runtime

# WHY IT'S WRONG:
# - rowNumber changes between pipeline builds
# - Edits attached to old rowNumber are lost
# - Links between objects disappear
# - OSv2: Build failure (Funnel batch pipeline error)
# - OSv1: Silent data corruption

# ✅ CORRECT: Use deterministic identifier
primaryKey: ["problemId"]  # UUID or natural key from source
properties:
  problemId:
    baseType: "String"
    description: "Stable UUID generated at content creation time"
```

**Resolution:** PK는 반드시 결정적(deterministic)이어야 하며, 파이프라인 빌드 간 불변이어야 한다.

---

### Anti-Pattern 3: Duplicate Primary Keys Across Rows

> **Severity: CRITICAL** | OSv2에서 빌드 실패, OSv1에서 무성 데이터 손실

```yaml
# ❌ WRONG: Dataset with non-unique primary key
# Dataset rows:
# | equationId | displayNotation |
# | eq-001     | "2x + 3 = 7"    |
# | eq-001     | "3x - 1 = 5"    |  <-- DUPLICATE KEY

# CONSEQUENCE:
# - OSv2: Build failure (Funnel batch pipeline error)
# - OSv1: Silent data loss, unpredictable behavior
# - 어떤 row가 사용될지 예측 불가

# ✅ CORRECT: Ensure unique primary keys
# Deduplicate in pipeline before Ontology indexing
# Use unique key generation: hash(content) or sequential UUID
```

**Resolution:** 파이프라인에서 Ontology indexing 전에 반드시 중복 제거를 수행한다.

---

### Anti-Pattern 4: Circular Link Dependencies Without Clear Direction

> **Severity: HIGH** | 쿼리 성능 저하 및 의미적 모호성

```yaml
# ❌ PROBLEMATIC: Bidirectional without semantic clarity
linkTypes:
  - name: "relatedTo"
    from: "MathematicalConcept"
    to: "MathematicalConcept"
    # No cardinality or direction semantics

# WHY IT'S PROBLEMATIC:
# - "relatedTo"는 의미적으로 모호함
# - 방향성이 없으면 그래프 순회 시 무한루프 위험
# - Search Around 쿼리 성능에 부정적 영향

# ✅ CORRECT: Clear directional semantics
linkTypes:
  - name: "isPrerequisiteOf"
    from: "MathematicalConcept"  # Source (simpler concept)
    to: "MathematicalConcept"    # Target (dependent concept)
    cardinality: "manyToMany"
    # Direction: A isPrerequisiteOf B means A must be learned before B
```

**Resolution:** Self-referencing LinkType은 반드시 명확한 방향성과 의미를 가져야 한다.

---

### Anti-Pattern 5: Premature ObjectType Creation (조급한 ObjectType 생성)

> **Severity: HIGH** | 향후 유지보수 부담 증가

```yaml
# ❌ WRONG: ObjectType for simple enum values
apiName: "DifficultyLevel"
displayName: "Difficulty Level"
primaryKey: ["levelId"]
properties:
  levelId:
    baseType: "Integer"
  levelName:
    baseType: "String"
    # Only 5 values: Easy, Medium, Hard, Very Hard, Expert

# WHY IT'S WRONG:
# - Property 수 2개 → SC-OT-1 미충족
# - 관계 0개 → SC-OT-2 미충족
# - 5개 고정값은 enum Property로 충분
# - 불필요한 ObjectType은 Ontology 복잡도 증가

# ✅ CORRECT: Use enum Property on parent
properties:
  difficultyLevel:
    baseType: "Integer"
    description: "Difficulty level 1-5"
    constraints:
      range:
        min: 1
        max: 5
```

**Resolution:** BC-OT-3 기준 적용 - 항목 수 <=20이고 속성 1개이면 enum Property로 시작한다.

---

### Anti-Pattern 6: Ignoring apiName Immutability

> **Severity: MEDIUM** | 마이그레이션 복잡도 증가

```yaml
# ❌ WRONG: Planning to rename apiName later
# Phase 1: Quick prototype
apiName: "MathObj"  # "We'll rename it later to MathProblem"

# WHY IT'S WRONG:
# - OSv2에서 apiName은 생성 후 변경 불가
# - OSDK 코드, API 호출, Actions 모두 apiName에 의존
# - 변경하려면 새 ObjectType 생성 + 데이터 마이그레이션 필요

# ✅ CORRECT: Choose definitive apiName from the start
apiName: "MathProblem"  # Final, meaningful name
```

**Resolution:** apiName은 처음부터 최종적이고 의미 있는 이름을 선택한다.

---

## 9. integration_points

> ObjectType과 다른 Ontology 컴포넌트 간의 관계를 정의한다.
> 상세 스펙은 각 컴포넌트의 정의 파일을 참조한다.

```yaml
integration_points:
  # ═══════════════════════════════════════════
  # Property (→ Property.md 참조)
  # ═══════════════════════════════════════════

  property:
    relationship: "ObjectType CONTAINS Properties"
    description: "Properties define the attributes of an ObjectType"
    forward_reference: "Property.md"
    constraints:
      - "Property apiNames must be unique within ObjectType"
      - "Maximum 2000 properties per ObjectType (OSv2 hard limit)"
      - "At least one property must be designated as primaryKey"
      - "One property must be designated as titleKey"
      - "Property baseType must be compatible with backing datasource column type"
    notes:
      - "Property 정의 상세는 Property.md 참조"
      - "baseType 목록, Value Types, Struct 스펙은 Property.md에서 관리"

  # ═══════════════════════════════════════════
  # SharedProperty (→ SharedProperty.md 참조)
  # ═══════════════════════════════════════════

  sharedProperty:
    relationship: "ObjectType CAN USE SharedProperty"
    description: "SharedProperties provide cross-type consistency"
    forward_reference: "SharedProperty.md"
    mechanism: "Property references SharedProperty via sharedProperty field"
    behavior:
      - "Local property inherits metadata from SharedProperty"
      - "Local apiName remains unchanged (prevents breaking changes)"
      - "Render hint overrides apply when associating"
    notes:
      - "SharedProperty 승격 기준 및 정량 판단은 SharedProperty.md 참조"
      - "Interface와의 관계는 SharedProperty.md에서 상세 기술"

  # ═══════════════════════════════════════════
  # Interface
  # ═══════════════════════════════════════════

  interface:
    relationship: "ObjectType IMPLEMENTS Interface"
    description: "Interfaces define polymorphic shape via SharedProperties"
    requirements:
      - "ObjectType must have all required SharedProperties from Interface"
      - "SharedProperties can be mapped from existing local properties"
      - "Interface 구현으로 ObjectType은 polymorphic query 대상이 됨"
    notes:
      - "Interface vs SharedProperty만 사용 시점 구분은 SharedProperty.md에서 다룸"

  # ═══════════════════════════════════════════
  # LinkType
  # ═══════════════════════════════════════════

  linkType:
    relationship: "ObjectType PARTICIPATES IN LinkType"
    description: "LinkTypes connect ObjectTypes in relationships"
    roles: ["source", "target"]
    constraints:
      - "LinkType은 반드시 두 ObjectType(또는 같은 ObjectType의 self-reference)을 연결"
      - "FK Property vs LinkType 선택 기준은 TAXONOMY.md에서 다룸 (Phase 2)"
      - "Self-referencing LinkType은 명확한 방향성 필수 (anti_pattern 4 참조)"
    notes:
      - "LinkType vs FK Property 승격 기준은 Gap G3로 Phase 2에서 상세 정의 예정"

  # ═══════════════════════════════════════════
  # Datasource
  # ═══════════════════════════════════════════

  datasource:
    relationship: "ObjectType IS BACKED BY Datasource"
    constraints:
      - "One datasource backs exactly one ObjectType (1:1 mapping)"
      - "Column types must be compatible with Property baseTypes"
      - "No MapType or StructType columns in backing dataset"
      - "Maximum 70 datasources per ObjectType"
    errors:
      duplicate_mapping: "Phonograph2:DatasetAndBranchAlreadyRegistered"

  # ═══════════════════════════════════════════
  # Action Type
  # ═══════════════════════════════════════════

  actionType:
    relationship: "ObjectType IS TARGET OF ActionType"
    description: "Actions perform create/update/delete operations on Objects"
    constraints:
      - "Maximum 10,000 objects per single action execution"
      - "Action must reference valid ObjectType apiName"
```

---

## 10. migration_constraints

> ObjectType 생성 후 변경이 제한되는 항목과 마이그레이션 시 주의사항.
> OSv2 기준으로 작성되었으며, OSv1과의 차이를 명시한다.

### 10.1 Immutable Fields (생성 후 변경 불가)

| Field | OSv1 | OSv2 | Impact |
|-------|------|------|--------|
| **Primary Key** | 변경 가능 (위험) | **변경 가능하나 기존 edits 전부 삭제** | 변경 시 모든 edits 손실. 새 ObjectType 생성 + 마이그레이션 강력 권장 |
| **apiName** | 변경 가능 (위험) | **변경 가능 (Overview page)** | 변경 시 OSDK, API, Actions 모든 참조 breakage. 강력 비권장 |
| **RID** | Immutable | Immutable | 시스템 자동 생성, 항상 불변 |

### 10.2 OSv2 Breaking Changes (G9)

```yaml
osv2_breaking_changes:
  primary_key:
    rule: >
      Primary key CAN be changed in OSv2, but all existing edits will be deleted.
      [V3 수정] 공식 문서: "Any time you change the primary key of an object type,
      you will be prompted to delete all existing edits."
    impact: "CRITICAL"
    recommendation: "PK 변경 대신 새 ObjectType 생성 + 데이터 마이그레이션 강력 권장"
    migration_path: >
      1. 새 ObjectType 생성 (새 apiName, 원하는 PK)
      2. 데이터 마이그레이션 파이프라인 작성
      3. 기존 LinkType 재연결
      4. 기존 Actions/OSDK 코드 업데이트
      5. 이전 ObjectType DEPRECATED 처리
    osv1_behavior: "PK 변경 가능했으나, 기존 edits/links 손실 위험"
    osv2_behavior: "PK 변경 가능하지만 모든 기존 edits 삭제됨"

  duplicate_primary_key:
    rule: "Duplicate PK values cause indexing failure"
    impact: "HIGH"
    osv2_behavior: "Funnel batch pipeline error (build failure)"
    osv1_behavior: "Silent data loss, unpredictable row selection"
    prevention: >
      파이프라인에서 Ontology indexing 전에 반드시 PK 중복 검사 수행.
      중복 발견 시 deduplicate 또는 composite key 사용.

  apiName:
    rule: >
      apiName CAN be edited via Overview page, but strongly discouraged.
      [V3 수정] 공식 문서: "An object type's API name can be edited in the
      object type's Overview page." 변경 시 모든 downstream 참조 breakage.
    impact: "MEDIUM"
    affected_consumers:
      - "OSDK generated code"
      - "API endpoint URLs"
      - "Action definitions"
      - "Workshop modules"
      - "Pipeline references"
    recommendation: >
      apiName 변경 대신 새 ObjectType 생성 권장. 변경할 경우 모든 consumer 코드
      업데이트 필수. "Once a property's ID is saved and the property is referenced
      in user applications, any change to the property ID will break the application."
```

### 10.3 Datasource Constraints

```yaml
datasource_constraints:
  single_objecttype_per_datasource:
    rule: "하나의 Datasource는 정확히 하나의 ObjectType만 backing할 수 있다"
    error: "Phonograph2:DatasetAndBranchAlreadyRegistered"
    note: "이미 다른 ObjectType에 매핑된 Datasource를 재사용하려 하면 에러 발생"

  no_complex_column_types:
    rule: "Backing dataset에 MapType 또는 StructType 컬럼이 포함되면 안 된다"
    prevention: >
      파이프라인에서 complex type을 flat columns로 변환 후 backing dataset에 저장.
      Struct는 ObjectType의 Property 수준에서 정의한다.

  property_limit:
    rule: "최대 2000 properties per ObjectType"
    impact: "Hard limit - 초과 시 ObjectType 생성/수정 불가"
    guidance: >
      2000개에 근접하면 ObjectType 분리를 고려한다.
      관련 속성 그룹을 별도 ObjectType으로 분리 + LinkType 연결.
```

### 10.4 Migration Checklist

ObjectType 마이그레이션 수행 시 아래 항목을 반드시 확인한다:

```
[ ] 1. 새 ObjectType의 apiName 확정 (변경 가능하나 모든 downstream 참조 breakage → 신중히)
[ ] 2. Primary Key 설계 확정 (변경 가능하나 기존 edits 전부 삭제됨 → 신중히)
[ ] 3. Backing Datasource 준비 (1:1 매핑, no MapType/StructType)
[ ] 4. 데이터 마이그레이션 파이프라인 작성 및 테스트
[ ] 5. PK 중복 검사 완료
[ ] 6. 기존 LinkType 재연결 계획
[ ] 7. OSDK/API/Actions 코드 업데이트 계획
[ ] 8. 기존 ObjectType DEPRECATED 처리 시점 결정
[ ] 9. 권한(ACL) 마이그레이션 계획
[ ] 10. Workshop/Application 참조 업데이트 확인
```

---

## 11. runtime_caveats

> ObjectType 운영 시 알아야 할 런타임 동작, 성능 특성, OSv1/v2 차이.

### 11.1 Search Around Limits

```yaml
search_around:
  default_limit: 100000
  description: >
    Search Around 기능으로 관련 Objects를 조회할 때의 기본 반환 수 제한.
    이 한도를 초과하면 결과가 잘려서 반환된다.
  guidance:
    - "대규모 관계 조회 시 필터를 적용하여 결과 수를 줄인다"
    - "100,000건 초과 예상 시 페이지네이션 또는 배치 처리 고려"
    - "Workshop에서 Search Around 사용 시 성능 영향 인지 필요"
```

### 11.2 OSv2 vs OSv1 Behavioral Differences

| Behavior | OSv1 | OSv2 | Impact |
|----------|------|------|--------|
| Duplicate PK | Silent data loss | Build failure | OSv2가 더 안전 (fail-fast) |
| PK Change | Allowed (risky) | Blocked | 마이그레이션 전략 변경 필요 |
| apiName Change | Allowed (risky) | Blocked | 최초 설계의 중요성 증가 |
| Property Limit | Soft limit | Hard limit (2000) | 초과 시 ObjectType 분리 필요 |
| Indexing | Phonograph1 | Phonograph2 (Funnel) | 에러 메시지 형식 변경 |

### 11.3 apiName Immutability After Creation

```yaml
apiName_immutability:
  rule: "apiName은 생성 후 변경할 수 없다 (OSv2)"
  impact:
    - "OSDK가 apiName 기반으로 TypeScript/Python 코드를 생성"
    - "REST API endpoint에 apiName이 포함됨"
    - "Actions에서 ObjectType을 apiName으로 참조"
    - "Workshop, Object Explorer 등 UI에서 apiName 기반 참조"
  best_practice:
    - "최초 생성 시 영구적으로 사용할 명확한 이름 선택"
    - "PascalCase 엄수: Employee (O), employee (X), EMPLOYEE (X)"
    - "도메인 축약어 피하기: MathematicalConcept (O), MathConc (X)"
    - "Reserved words 회피: Property (X), MathProperty (O)"
```

### 11.4 Performance Considerations

```yaml
performance:
  object_count_impact:
    description: "Object 수 증가에 따른 성능 영향"
    guidance:
      - "수백만 Objects까지 일반적으로 양호"
      - "Property 수가 많을수록 indexing 시간 증가"
      - "Search 및 Filter 성능은 Property에 Searchable 설정 여부에 의존"

  link_traversal:
    description: "LinkType 순회 성능"
    guidance:
      - "Search Around는 기본 100,000건 제한"
      - "다단계 순회(A → B → C)는 각 단계마다 제한 적용"
      - "Self-referencing Link의 순환 참조 주의"

  struct_query:
    description: "Struct Property 조회 시 주의사항 (G6)"
    guidance:
      - "Struct 내부 필드 검색은 Elasticsearch array matching으로 동작"
      - "Struct 배열에서 특정 필드 조합 조회 시 의도치 않은 결과 가능"
      - "정확한 필터링이 필요하면 ObjectType으로 승격 고려 (BC-OT-2)"
    example: >
      Array<Struct>에서 {name: "A", value: 1}을 찾을 때,
      실제로는 name="A"인 항목과 value=1인 항목이 별개 Struct에 있어도
      매칭될 수 있음 (ES cross-object matching).
```

### 11.5 Concurrent Editing

```yaml
concurrent_editing:
  description: "여러 사용자/프로세스가 동시에 같은 Object를 수정할 때"
  behavior:
    - "Foundry는 last-write-wins 전략을 사용"
    - "Action을 통한 수정은 트랜잭션 보장"
    - "Pipeline rebuild는 전체 Object를 덮어씀"
  guidance:
    - "사용자 편집(Actions)과 파이프라인 빌드가 동시에 일어나지 않도록 스케줄링"
    - "편집 빈도가 높은 ObjectType은 별도 편집 전용 Datasource 고려"
```

---

## Appendix: Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-06 | Claude Opus 4.6 | Initial creation from session1.md + WF-1/WF-2 gap analysis |

### Source Documents

| Document | Purpose |
|----------|---------|
| `session1.md` (Component 1: ObjectType) | Original content (sections 1-8) |
| `wf1_gap_report.md` | Gap analysis identifying G1-G10 |
| `wf2_design_spec.md` | Design spec with 11-section template and quantitative thresholds |

### Gap Coverage

| Gap | Severity | Section | Resolution |
|-----|----------|---------|------------|
| G1 (Value Types) | HIGH | Property.md (forward ref) | Deferred to Property.md |
| G2 (Boundary conditions) | HIGH | formal_definition (NC/SC/BC) | Fully resolved |
| G3 (LinkType vs FK) | HIGH | integration_points (forward ref) | Phase 2 reference |
| G4 (Interface vs SharedProperty) | HIGH | integration_points | Forward ref to SharedProperty.md |
| G5 (Naming inconsistency) | MEDIUM | NAMING_AUDIT.md (separate) | Separate document |
| G6 (Struct ES matching) | MEDIUM | runtime_caveats 11.4 | Fully resolved |
| G7 (Edit-only/Required) | LOW | Property.md (forward ref) | Deferred to Property.md |
| G8 (ID vs apiName) | LOW | official_definition 2, structural_schema 4 | Fully resolved |
| G9 (OSv2 PK migration) | LOW | migration_constraints 10 | Fully resolved |
| G10 (Decision tree quantification) | HIGH | quantitative_decision_matrix 5 | Fully resolved |
