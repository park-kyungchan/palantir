# Palantir Ontology: Component Taxonomy (분류 체계)

> **Phase 1: Core Primitives** | **Version:** 1.0.0 | **Last Verified:** 2026-02-06
> **Source Material:** ObjectType.md, Property.md, SharedProperty.md, WF-2 Design Spec

---

## Table of Contents

1. [Component Hierarchy (컴포넌트 계층도)](#1-component-hierarchy-컴포넌트-계층도)
2. [Component Dependency Graph (의존성 그래프)](#2-component-dependency-graph-의존성-그래프)
3. [Quantitative Decision Flows (정량 판단 플로우)](#3-quantitative-decision-flows-정량-판단-플로우)
   - [3.1 ObjectType 판단 Flow](#31-objecttype-판단-flow)
   - [3.2 Property baseType 선택 Flow](#32-property-basetype-선택-flow)
   - [3.3 SharedProperty 승격 Flow](#33-sharedproperty-승격-flow)
   - [3.4 Cross-Component Decision Matrices](#34-cross-component-decision-matrices)
4. [Migration Sequence (마이그레이션 순서)](#4-migration-sequence-마이그레이션-순서)

---

## 1. Component Hierarchy (컴포넌트 계층도)

> Palantir Foundry Ontology의 전체 컴포넌트를 계층적으로 분류한다.
> Phase 1 (Core Primitives)이 현재 문서화 범위이며, Phase 2-6은 향후 확장 대상이다.

```
Palantir Foundry Ontology
|
+-- Schema Layer (정의 계층) ────────────────────── Phase 1 [CURRENT]
|   |
|   +-- ObjectType                    <- entity/event schema definition
|   |   |
|   |   +-- Property                  <- attribute definition (local)
|   |   |   |
|   |   |   +-- Base Types (22종)
|   |   |   |   +-- Primitive ......... String, Integer, Short, Long,
|   |   |   |   |                       Byte, Boolean, Float, Double, Decimal
|   |   |   |   +-- Time .............. Date, Timestamp
|   |   |   |   +-- Geospatial ........ Geopoint, Geoshape
|   |   |   |   +-- Complex ........... Array, Struct, Vector
|   |   |   |   +-- Reference ......... MediaReference, Attachment,
|   |   |   |   |                       TimeSeries, GeotimeSeriesReference
|   |   |   |   +-- Special ........... CipherText, MandatoryControl
|   |   |   |
|   |   |   +-- Struct                <- composite property (depth=1, max 10 fields)
|   |   |   |
|   |   |   +-- Value Types           <- semantic wrapper above base type
|   |   |       (email, URL, currency code, phone number, ...)
|   |   |
|   |   +-- SharedProperty            <- reusable property (cross-type consistency)
|   |       |
|   |       +-- Interface             <- abstract shape contract ──── Phase 2
|   |           (requires SharedProperty only; local Property 사용 불가)
|   |
|   +-- LinkType                      <- relationship schema ──────── Phase 2
|       |
|       +-- Cardinality: oneToOne, oneToMany, manyToOne, manyToMany
|       +-- Self-referencing (same ObjectType, directional semantics 필수)
|
+-- Kinetic Layer (실행 계층) ────────────────────── Phase 3
|   |
|   +-- ActionType                    <- CRUD operations on Objects
|   |   (max 10,000 objects per action; Float/Double/Decimal 파라미터 금지)
|   |
|   +-- Function                      <- reusable logic/computation
|   |
|   +-- Rule / Constraint             <- declarative validation
|
+-- Data Layer (데이터 계층) ─────────────────────── Phase 4
|   |
|   +-- Dataset                       <- backing datasource for ObjectType
|   |   (1:1 mapping with ObjectType; no MapType/StructType columns)
|   |
|   +-- Pipeline                      <- data transformation chain
|   |
|   +-- Transform                     <- individual data transformation step
|   |
|   +-- OntologySync                  <- real-time sync mechanism
|
+-- Collection Layer (수집 계층) ─────────────────── Phase 5
|   |
|   +-- ObjectSet                     <- filtered/grouped collection of Objects
|   |
|   +-- TimeSeries                    <- time-indexed data collection
|   |
|   +-- MediaSet                      <- media/file collection
|
+-- Application Layer (응용 계층) ────────────────── Phase 6
    |
    +-- Workshop                      <- low-code application builder
    |
    +-- OSDK                          <- programmatic SDK (TypeScript, Python)
    |   (apiName-based code generation; immutable apiName 주의)
    |
    +-- Slate                         <- custom dashboard builder
    |
    +-- REST API                      <- HTTP interface (v2 endpoints)
    |   (endpoint URL에 ObjectType apiName 포함)
    |
    +-- Automate                      <- workflow automation
```

### Phase Coverage Summary

| Phase | Layer | Components | Documentation Status |
|-------|-------|------------|---------------------|
| **1** | Schema (Core) | ObjectType, Property, SharedProperty | **Complete** (v1.0.0) |
| **2** | Schema (Relations) | LinkType, Interface | Planned |
| **3** | Kinetic | ActionType, Function, Rule/Constraint | Planned |
| **4** | Data | Dataset, Pipeline, Transform, OntologySync | Planned |
| **5** | Collection | ObjectSet, TimeSeries, MediaSet | Planned |
| **6** | Application | Workshop, OSDK, Slate, REST API, Automate | Planned |

---

## 2. Component Dependency Graph (의존성 그래프)

> 컴포넌트 간 의존 관계를 시각화한다.
> 화살표 방향은 "X depends on Y" (X --> Y) 또는 관계 레이블에 따른다.

### 2.1 Core Dependency Diagram

```
                              +------------------+
                              |     Dataset      |
                              | (backing source) |
                              +--------+---------+
                                       |
                                 backs |  1:1 mapping
                                       |
                                       v
+-------------------+         +------------------+         +-------------------+
|   SharedProperty  |<--refs--+   ObjectType     +--has--->|    Property       |
| (metadata source) |         | (entity schema)  |         | (local attribute) |
+--------+----------+         +--------+---------+         +--------+----------+
         |                             |                            |
         |                             |                            |
    +---------+               +--------+--------+          +-------+--------+
    |         |               |        |        |          |                |
    v         v               v        v        v          v                v
Interface   N OTs        LinkType  ActionType  ObjectSet  Struct        Value Type
(Phase 2)  use SP        (Phase 2) (Phase 3)  (Phase 5)  (depth=1,     (semantic
                                                          max 10)       wrapper)
```

### 2.2 Detailed Relationship Diagram

```
Dataset ────── backs (1:1) ──────> ObjectType ────── has (1:many) ──────> Property
  |                                     |                                     |
  | no MapType/StructType               |                                     |
  | columns allowed                     |                          +----------+---------+
  |                                     |                          |          |         |
  | max 70 datasources                  |                     refs SP   uses VT   maps to
  | per ObjectType                      |                          |          |     column
                                        |                          v          v
                                        |                   SharedProperty  Value Type
                                        |                          |
                                        +--- implements ---------> Interface (Phase 2)
                                        |                          |
                                        |                     requires SP only
                                        |
                                        +--- participates -------> LinkType (Phase 2)
                                        |     (source/target)
                                        |
                                        +--- acted-on-by --------> ActionType (Phase 3)
                                                                       |
                                                                  uses Function
```

### 2.3 YAML Dependency Matrix

```yaml
dependencies:
  # ═══════════════════════════════════════════════════
  # Phase 1: Core Schema Components
  # ═══════════════════════════════════════════════════

  ObjectType:
    requires: [Dataset]                     # NC-OT-3: backing datasource 필수
    contains: [Property]                    # max 2000 properties per ObjectType
    can_use: [SharedProperty, Interface]    # optional cross-type consistency
    participates_in: [LinkType]             # Phase 2: relationship participation
    acted_on_by: [ActionType]              # Phase 3: CRUD operations
    consumed_by: [ObjectSet, Workshop, OSDK, Slate, REST_API, Automate]
    constraints:
      max_properties: 2000                 # OSv2 hard limit
      max_datasources: 70
      max_objects_per_action: 10000
      apiName_immutable: true              # PascalCase, cannot change after creation
      primaryKey_immutable: true           # OSv2: cannot change after creation

  Property:
    belongs_to: [ObjectType]               # exactly one parent ObjectType
    can_reference: [SharedProperty]        # via sharedProperty field
    can_wrap: [ValueType]                  # semantic constraint layer
    backed_by: [Dataset_Column]            # baseType must be compatible
    used_in: [ActionType]                  # with restrictions (no Float/Double/Decimal)
    constraints:
      apiName_format: "camelCase"          # ^[a-z][a-zA-Z0-9]*$
      max_per_objecttype: 2000
      struct_max_depth: 1
      struct_max_fields: 10
      vector_max_dimensions: 2048
      array_no_nulls: true                 # OSv2

  SharedProperty:
    used_by: [ObjectType, Interface]       # cross-type metadata sharing
    requires: []                           # independent creation (no prerequisites)
    composed_of: [BaseType, RenderHints, Constraints]
    constraints:
      min_usage_recommended: 2             # NC-SP-1: 2+ ObjectTypes
      semantic_consistency: "100%"         # NC-SP-2: identical meaning
      apiName_immutable: true
      baseType_immutable_when_in_use: true
      interface_only_composition: true     # Interface는 SP로만 구성

  # ═══════════════════════════════════════════════════
  # Phase 2: Relationship Components (forward reference)
  # ═══════════════════════════════════════════════════

  Interface:
    requires: [SharedProperty]              # schema composed ONLY of SharedProperties
    implemented_by: [ObjectType]            # ObjectType must have all required SPs
    phase: 2
    constraints:
      local_property_forbidden: true       # local Property 사용 불가

  LinkType:
    connects: [ObjectType, ObjectType]     # source and target (may be same OT)
    requires: [ObjectType]                 # both endpoints must exist
    phase: 2
    constraints:
      cardinality: ["oneToOne", "oneToMany", "manyToOne", "manyToMany"]
      self_reference_requires_direction: true

  # ═══════════════════════════════════════════════════
  # Phase 3: Kinetic Components (forward reference)
  # ═══════════════════════════════════════════════════

  ActionType:
    targets: [ObjectType]
    uses: [Function]
    phase: 3
    constraints:
      max_objects: 10000
      forbidden_param_types: ["Float", "Double", "Decimal", "Vector"]
      max_primitive_list: 10000
      max_object_ref_list: 1000

  # ═══════════════════════════════════════════════════
  # Phase 4: Data Components (forward reference)
  # ═══════════════════════════════════════════════════

  Dataset:
    backs: [ObjectType]                    # 1:1 mapping
    fed_by: [Pipeline, Transform]
    phase: 4
    constraints:
      one_objecttype_per_dataset: true     # error: Phonograph2:DatasetAndBranchAlreadyRegistered
      no_maptype_columns: true
      no_structtype_columns: true
```

### 2.4 Creation Order (의존성 기반 생성 순서)

> 컴포넌트 생성 시 아래 순서를 지켜야 한다. 의존 대상이 먼저 존재해야 한다.

```
Step 1: Dataset              (독립 -- 선행 조건 없음)
Step 2: SharedProperty       (독립 -- 선행 조건 없음)
Step 3: ObjectType           (requires: Dataset)
Step 4: Property             (requires: ObjectType)
Step 5: Property <-> SP 연결  (requires: Property + SharedProperty)
Step 6: Interface            (requires: SharedProperty)  -- Phase 2
Step 7: OT implements IF     (requires: ObjectType + Interface)  -- Phase 2
Step 8: LinkType             (requires: ObjectType x2)  -- Phase 2
Step 9: ActionType           (requires: ObjectType)  -- Phase 3
```

---

## 3. Quantitative Decision Flows (정량 판단 플로우)

> 각 컴포넌트의 모델링 여부를 판단하기 위한 **정량적** 의사결정 흐름도.
> 모든 threshold는 ObjectType.md, Property.md, SharedProperty.md의
> `quantitative_decision_matrix` 섹션과 일치한다.

### 3.1 ObjectType 판단 Flow

> "이 개념을 ObjectType으로 모델링해야 하는가?"
> Source: ObjectType.md Section 1 (formal_definition) + Section 5 (quantitative_decision_matrix)

#### Signal Matrix (Quick Reference)

| Signal | Strong YES | Gray Zone | Strong NO | Weight |
|--------|-----------|-----------|-----------|--------|
| 자연 PK 존재 | Natural key 명확 | Synthetic UUID OK | PK 불가능 | **CRITICAL** |
| 독립 생명주기 | 완전 독립 CRUD | 부분 독립 | 부모 종속 | **HIGH** |
| 관계(Link) 수 | >=2 | 1 | 0 | **HIGH** |
| Property 수 | >=3 | 1-2 | 0 | MEDIUM |
| 독립 조회 비율 | >30% | 10-30% | <10% | MEDIUM |
| 별도 권한 필요 | Yes (ACL 분리) | - | No | LOW (decisive) |

#### Complete Decision Flow

```
START: 새로운 개념 C를 모델링해야 한다
|
|   ╔════════════════════════════════════════════════════════════╗
|   ║  NECESSARY CONDITIONS (필요조건) -- 전부 YES 필수          ║
|   ║  하나라도 NO이면 ObjectType 불가                           ║
|   ╚════════════════════════════════════════════════════════════╝
|
+--[NC-OT-1] 실세계 entity 또는 event를 표현하는가?
|   |
|   +-- NO ----> X  NOT ObjectType
|   |                +-> Property, Struct, 또는 enum으로 모델링
|   +-- YES --> continue
|
+--[NC-OT-2] 고유 식별자(Primary Key)가 존재하거나 생성 가능한가?
|   |
|   +-- NO ----> X  NOT ObjectType
|   |                +-> 다른 ObjectType의 속성(Property)으로 임베딩
|   +-- YES --> continue
|
+--[NC-OT-3] 하나 이상의 Backing Dataset에 매핑 가능한가?
|   |
|   +-- NO ----> X  NOT ObjectType
|   |                +-> Derived Property 또는 computed field로 처리
|   +-- YES --> continue
|
|   ╔════════════════════════════════════════════════════════════╗
|   ║  SUFFICIENT CONDITIONS (충분조건) -- 하나라도 YES이면 확정  ║
|   ╚════════════════════════════════════════════════════════════╝
|
+-- 별도 권한(ACL) 제어가 필요한가?
|   |
|   +-- YES ---> V  MUST be ObjectType (SC-OT-3, decisive)
|   +-- NO ---> continue
|
+-- Property 수는?
|   |
|   +-- 0개 ----------> X  Invalid (최소 1개 Property = PK 필수)
|   +-- 1-2개 ---------> !  Gray Zone --> BC-OT-1~BC-OT-5 참조
|   +-- >=3개 ---------> Strong signal --> continue to SC check
|
+-- 다른 ObjectType과의 Link 수는?
|   |
|   +-- 0개 ----------> Check: 독립 조회가 필요한가?
|   |                    +-- >30% --> ObjectType 가능
|   |                    +-- <10% --> Struct/Property 쪽으로
|   +-- 1개 ----------> !  판단 필요 (단독으로 충분조건 아님)
|   +-- >=2개 ---------> V  SC-OT-2 충족 --> ObjectType 확정
|
+-- 독립 생명주기가 필요한가?
|   |
|   +-- YES + >=3 Properties --> V  SC-OT-1 충족 --> ObjectType 확정
|   +-- Partial ------------> !  Gray Zone --> BC 참조
|   +-- NO -----------------> Struct Property 고려
|
|   ╔════════════════════════════════════════════════════════════╗
|   ║  DECISION RULE (최종 판단 공식)                            ║
|   ╚════════════════════════════════════════════════════════════╝
|
+-- NC 전부 YES + (1 CRITICAL Strong YES + 1 HIGH Strong YES)
|       --> V  ObjectType 확정
|
+-- NC 전부 YES + Gray Zone만 해당
|       --> !  boundary_conditions (BC-OT-1 ~ BC-OT-5) 참조하여 판단
|
+-- NC 하나라도 NO
        --> X  NOT ObjectType (Property 또는 Struct)
```

#### Boundary Conditions Quick Reference

| ID | Scenario | Threshold | Promote 사례 | Demote 사례 |
|----|----------|-----------|-------------|-------------|
| BC-OT-1 | Property 1-2개, Link 1개 | 독립 조회 >30%이면 OT | Tag (독립 검색 필수) | Priority (enum 3값) |
| BC-OT-2 | 항상 부모와 함께 생성/삭제 | 별도 권한 >=1이면 OT | Address (독립 조회 + geocoding) | Address (항상 embedded) |
| BC-OT-3 | Lookup/Reference data | 항목 >20 또는 속성 >=2이면 OT | Country (code,name,region,pop) | DifficultyLevel (1-5) |
| BC-OT-4 | Mathematical Variable | 독립 추적/관계 필요 시 OT | Variable (연구 패턴 추적) | Variable (방정식 속성) |
| BC-OT-5 | Term/Monomial | 독립 추적 필요 시 OT | Term (항별 오류 추적) | Term (다항식 내부 구조) |

---

### 3.2 Property baseType 선택 Flow

> "이 Property에 어떤 baseType을 지정해야 하는가?"
> Source: Property.md Section 5 (quantitative_decision_matrix Matrix B)

#### 22종 BaseType 카테고리

> **Formal Definition References:** 이 플로우는 Property NC/SC/BC 조건이 충족된 상태에서의
> baseType 선택을 다룬다. NC-P-1(ObjectType 소속), NC-P-2(유효 baseType), NC-P-3(dataset 컬럼 매핑)이
> 전제된다. Property vs ObjectType vs Struct 판단은 Section 3.4의 Matrix A/B를 참조하라.
> SC-P-1(단일 값, 독립 의미 없음), SC-P-2(부모 생명주기 종속), BC-P-1~3은 Property.md를 참조.
> [V2 검증 반영: 8개 Property NC/SC/BC ID 참조 추가]

| Category | Types | Count |
|----------|-------|-------|
| Primitive | String, Integer, Short, Long, Byte, Boolean, Float, Double | 8 |
| **NOTE** | Decimal은 standalone base type 아님 (Struct field에서만 유효). [V3 검증 반영] | - |
| Time | Date, Timestamp | 2 |
| Geospatial | Geopoint, Geoshape | 2 |
| Complex | Array, Struct, Vector | 3 |
| Reference | MediaReference, Attachment, TimeSeries, GeotimeSeriesReference | 4 |
| Special | CipherText, MandatoryControl | 2 |
| **Total** | | **22** |

#### Complete Selection Flow

```
START: Property P의 데이터 특성을 분석한다
|
+---> TEXT 데이터인가?
|     |
|     +-- Short text (< 256 chars) -----------> String
|     +-- Long text / prose ------------------> String + renderHints.longText: true
|     +-- Encrypted / sensitive --------------> CipherText
|     +-- Pattern-constrained ----------------> String + constraints.regex
|     +-- Semantic type needed ---------------> String + Value Type
|         (email, URL, phone, currency code)
|
+---> NUMERIC 데이터인가?
|     |
|     +-- Whole number (정수)?
|     |   |
|     |   +-- Range -128 ~ 127 ----------------> Byte
|     |   +-- Range -32,768 ~ 32,767 ----------> Short
|     |   +-- Range +/-2,147,483,647 ----------> Integer  [RECOMMENDED]
|     |   +-- Range beyond +/-2B --------------> Long
|     |       |
|     |       +-- WARNING: JavaScript Number.MAX_SAFE_INTEGER
|     |       |   = 9,007,199,254,740,991
|     |       |   브라우저/프론트엔드에서 초과 시 PRECISION LOSS
|     |       +-- 프론트엔드 노출 ID라면 String 사용 권장
|     |
|     +-- Decimal number (소수)?
|         |
|         +-- Approximate OK -----------------> Double  [RECOMMENDED]
|         |   WARNING: Action parameter로 사용 불가
|         +-- Financial / exact precision -----> Decimal
|         |   WARNING: Action parameter로 사용 불가
|         +-- Lower precision sufficient ------> Float
|             WARNING: Action parameter로 사용 불가
|
+---> TRUE/FALSE 값인가?
|     |
|     +-- Boolean
|         WARNING: Primary Key로 사용 비권장
|
+---> DATE/TIME 값인가?
|     |
|     +-- Date only (시간 불필요) -------------> Date
|     +-- Date with time ---------------------> Timestamp
|         NOTE: 내부 저장은 UTC. UI에서 timezone 변환 표시.
|
+---> LOCATION 데이터인가?
|     |
|     +-- Single point (위도/경도) ------------> Geopoint
|     |   (WGS 84: "lat,long" or geohash)
|     +-- Shape / polygon --------------------> Geoshape
|         (GeoJSON RFC 7946)
|
+---> COLLECTION / 복합 구조인가?
|     |
|     +-- List of primitives -----------------> Array<baseType>
|     |   |
|     |   +-- NOTE: null 원소 불가 (OSv2)
|     |   +-- NOTE: 중첩 배열 불가 (OSv2)
|     |
|     +-- Structured object ------------------> Struct
|         |
|         +-- Constraints:
|         |   +-- depth = 1 only (중첩 불가)
|         |   +-- max 10 fields
|         |   +-- no nested Struct/Array/Vector
|         |
|         +-- Query caveat:
|             ES array matching semantics 주의
|             (cross-element matching 가능 -> 부정확한 결과)
|
+---> ML / EMBEDDING 벡터인가?
|     |
|     +-- Vector
|         +-- max 2048 dimensions
|         +-- KNN queries ONLY (exact match, range, sort 불가)
|         +-- OSv2 전용
|         +-- Array 내 포함 불가
|         +-- Action parameter 불가
|
+---> FILE / MEDIA 참조인가?
      |
      +-- Media file --------------------------> MediaReference
      +-- Attached document -------------------> Attachment
      +-- Time series data --------------------> TimeSeries
      +-- Geotime series ---------------------> GeotimeSeriesReference
```

#### Numeric Type Decision Table

| Scenario | Recommended Type | Range | Action Parameter? | Notes |
|----------|-----------------|-------|-------------------|-------|
| Small counter (0-127) | Byte | -128 ~ 127 | Yes | Rarely used |
| Port number, year | Short | -32,768 ~ 32,767 | Yes | |
| General count/quantity | **Integer** | +/-2.1B | **Yes** | **Default choice** |
| Large counter, epoch ms | Long | +/-9.2E18 | Yes | JS precision risk |
| Percentage, ratio | **Double** | ~15 sig digits | **No** | Approx OK |
| Money, financial | Decimal | Arbitrary precision | **No** | Exact |
| Sensor reading | Float | ~7 sig digits | **No** | Low precision |

#### Primary Key Allowed Types

| Recommended | Discouraged | Forbidden |
|-------------|-------------|-----------|
| String, Integer | Short, Long, Byte, Boolean, Date, Timestamp | Float, Double, Decimal, Geopoint, Geoshape, Array, Struct, Vector, MediaReference, Attachment |

---

### 3.3 SharedProperty 승격 Flow

> "이 Local Property를 SharedProperty로 승격해야 하는가?"
> Source: SharedProperty.md Section 1 (formal_definition) + Section 5 (quantitative_decision_matrix)

#### Signal Matrix (Quick Reference)

| Signal | Promote | Gray Zone | Keep Local | Weight |
|--------|---------|-----------|------------|--------|
| 사용 ObjectType 수 | >=3 | 2 | 1 | **CRITICAL** |
| 의미 동일성 | 100% 동일 | 90%+ 유사 | <90% | **CRITICAL** |
| Interface 요구 | Yes | - | No | **HIGH (decisive)** |
| 메타데이터 변경 빈도 | 월 1회+ | 분기 1회 | 연 1회 미만 | MEDIUM |

#### Complete Decision Flow

```
START: Property P를 SharedProperty로 승격해야 하는가?
|
|   ╔════════════════════════════════════════════════════════════╗
|   ║  NECESSARY CONDITIONS (필요조건) -- 전부 YES 필수          ║
|   ╚════════════════════════════════════════════════════════════╝
|
+--[NC-SP-1] 2개 이상의 ObjectType에서 사용되는가?
|   |
|   +-- NO (1 only) -------> X  Keep Local
|   |   |
|   |   +-- Exception: 3개월 내 확정된 추가 OT 계획?
|   |       +-- YES -------> !  선제 승격 가능 (BC-SP-3)
|   |       +-- NO --------> X  Keep Local
|   |
|   +-- YES --> continue
|
+--[NC-SP-2] 모든 사용 ObjectType에서 동일한 의미(semantics)인가?
|   |
|   +-- NO (<90% 중첩) ----> X  Keep Local (별도 Property로 분리)
|   |
|   +-- GRAY (90%+ 유사) --> !  SharedProperty 가능
|   |                            단, description에 차이 명시 필수 (BC-SP-2)
|   |
|   +-- YES (100%) --------> continue
|
+--[NC-SP-3] 유효한 baseType에 매핑 가능한가?
|   |
|   +-- NO -----------------> X  데이터 구조 재설계
|   +-- YES ----------------> continue
|
|   ╔════════════════════════════════════════════════════════════╗
|   ║  SUFFICIENT CONDITIONS (충분조건) -- 하나라도 YES이면 확정  ║
|   ╚════════════════════════════════════════════════════════════╝
|
+-- Interface 구현에 필요한가? (SC-SP-1)
|   |
|   +-- YES ---> V  MUST promote to SharedProperty
|   |                (Interface는 SharedProperty로만 구성 가능)
|   +-- NO ---> continue
|
+-- 3+ ObjectType에서 동일 의미 + 중앙관리 필요? (SC-SP-2)
|   |
|   +-- YES ---> V  SharedProperty 확정
|   +-- NO ---> continue
|
|   ╔════════════════════════════════════════════════════════════╗
|   ║  BOUNDARY CONDITIONS (2 types, no Interface)              ║
|   ╚════════════════════════════════════════════════════════════╝
|
+-- 메타데이터 변경 빈도는? (BC-SP-1)
|   |
|   +-- 월 1회 이상 ------> V  SharedProperty (중앙 관리 이점 큼)
|   +-- 분기 1회 ---------> !  판단 필요 (사용 OT 수 + 확장 계획 고려)
|   +-- 거의 없음 --------> !  Either OK (향후 확장 가능성 고려)
|
|   ╔════════════════════════════════════════════════════════════╗
|   ║  DECISION RULE (최종 판단 공식)                            ║
|   ╚════════════════════════════════════════════════════════════╝
|
+-- (>=2 types + 100% same semantics) OR (Interface required)
|       --> V  SharedProperty
|
+-- 2 types + 동일 의미 + 안정 메타데이터
|       --> !  Gray Zone: 향후 확장 가능성 고려하여 결정
|
+-- 1 type only (확장 계획 없음)
        --> X  Keep Local
```

#### Boundary Conditions Quick Reference

| ID | Scenario | Threshold | Promote 사례 | Demote 사례 |
|----|----------|-----------|-------------|-------------|
| BC-SP-1 | 2 OTs only, no Interface | 메타데이터 변경 월1회+ -> SP | createdAt (formatting 변경 빈번) | score (Integer, 안정 스키마) |
| BC-SP-2 | 이름 같지만 의미 미묘하게 다름 | 의미 중첩 >=90% -> SP 가능 | status (ACTIVE/INACTIVE, 동일 lifecycle) | date (issue date vs occurrence date) |
| BC-SP-3 | 현재 1 OT, 확장 예정 | 3개월 내 확정 로드맵 -> 선제 승격 | gradeLevel (Lesson, Assessment Q2 계획) | polynomialDegree (확장 불필요) |

---

### 3.4 Cross-Component Decision Matrices

> 컴포넌트 간 선택 판단을 위한 비교 매트릭스.
> Source: WF-2 Design Spec Section 5

#### Matrix A: ObjectType vs Property

> "이 데이터를 독립 엔티티(ObjectType)로 모델링할 것인가, 속성(Property)으로 모델링할 것인가?"

| Criterion | ObjectType (독립 엔티티) | Property (속성) | Weight |
|-----------|----------------------|---------------|--------|
| 독립 식별성 | PK로 유일 식별 가능 | 소속 OT 없이 무의미 | **CRITICAL** |
| 관계 참여 | LinkType source/target 가능 | 직접 관계 불가 | **HIGH** |
| Property 수 | >=3개 독립 속성 | 1개 (단일 값) | MEDIUM |
| 독립 생명주기 | 독립 CRUD 필요 | 부모 생명주기 종속 | **HIGH** |
| 독립 조회 | >30% 독립 조회 | 부모 통해서만 접근 (<10%) | MEDIUM |
| 권한 분리 | 별도 ACL 필요 시 필수 OT | 부모 권한 상속 충분 | LOW (decisive) |

**Decision Rule:**
- CRITICAL signal이 ObjectType 쪽 --> ObjectType
- CRITICAL signal이 Property 쪽 + HIGH signals도 Property --> Property
- Gray Zone --> BC-OT-1 ~ BC-OT-5 참조

#### Matrix B: ObjectType vs Struct Property

> "복합 구조 데이터를 독립 ObjectType으로 분리할 것인가, Struct Property로 임베딩할 것인가?"

| Criterion | ObjectType | Struct Property | Weight |
|-----------|-----------|-----------------|--------|
| 독립 식별성 | 고유 PK 존재 | 부모 OT의 속성 | **CRITICAL** |
| 필드 수 | 무제한 (max 2000) | **max 10 fields** | **HIGH** |
| 중첩(nesting) | 관계(LinkType)로 표현 | **depth 1만 가능** | MEDIUM |
| 조회 방식 | 독립 필터/검색/정렬 | ES array matching만 (부정확 가능) | **HIGH** |
| 생명주기 | 독립 CRUD | 부모 종속 (부모와 함께 생성/삭제) | **HIGH** |
| 관계 참여 | 다른 OT와 Link 가능 | 불가 | **HIGH** |

**Decision Rule:**
- 필드 >10 --> 반드시 ObjectType (Struct hard limit 초과)
- 독립 조회 >30% --> ObjectType
- 항상 부모와 함께 + 필드 <=10 + 독립 조회 <10% --> Struct
- ES array matching 부정확 문제 허용 불가 --> ObjectType

#### Matrix C: Local Property vs SharedProperty

> "이 Property를 개별 관리할 것인가, 중앙 SharedProperty로 승격할 것인가?"

| Criterion | Local Property | SharedProperty | Weight |
|-----------|---------------|----------------|--------|
| 사용 범위 | 1개 ObjectType | >=2개 ObjectType | **CRITICAL** |
| 의미 동일성 | 타입별 고유 가능 | 타입간 100% 동일 필수 | **CRITICAL** |
| 메타데이터 관리 | 개별 관리 (N개 OT) | 중앙 관리 (1곳 변경 -> 전파) | MEDIUM |
| Interface 요구 | 사용 불가 | **필수** (Interface는 SP만 사용) | HIGH (decisive) |
| baseType 변경 | 가능 (주의 필요) | **차단** (사용 OT 있으면) | LOW |
| Governance 비용 | Low | Medium~High | LOW |
| Visual | 아이콘 없음 | Globe icon 표시 | - |

**Decision Rule:**
- Interface 필요 --> 반드시 SharedProperty (SC-SP-1)
- 3+ OTs + 동일 의미 --> SharedProperty (SC-SP-2)
- 2 OTs + 동일 의미 + 변경 빈번 --> SharedProperty (BC-SP-1)
- 1 OT only --> Keep Local

#### Matrix D: Property vs LinkType (Phase 2 Preview)

> "참조 값을 FK-style Property로 저장할 것인가, LinkType으로 모델링할 것인가?"
> NOTE: LinkType 상세는 Phase 2에서 정의 예정. 아래는 판단 지침 미리보기.

| Criterion | FK Property | LinkType | Weight |
|-----------|------------|----------|--------|
| 방향성 | 단방향 (source -> target만) | **양방향** (양쪽 인덱싱) | **HIGH** |
| 역방향 조회 빈도 | <10% | **>10%** | **HIGH** |
| Graph 순회 | 불가 | 가능 (Search Around) | HIGH |
| Ontology 시각화 | 관계 표시 안 됨 | 관계 표시됨 | MEDIUM |
| 구현 복잡도 | Low (String 값만) | Medium (LinkType 정의 필요) | LOW |

**Decision Rule:**
- 역방향 조회 >10% --> LinkType
- 양방향 탐색 필요 --> LinkType
- Write-once 감사용 (createdByUserId 등) --> FK Property

---

## 4. Migration Sequence (마이그레이션 순서)

> 기존 시스템을 Palantir Ontology로 마이그레이션하거나 새로 구축할 때의 권장 순서.
> 각 Step은 이전 Step의 완료(및 사용자 승인)를 전제한다.

### 4.1 Phase Roadmap Overview

```
Phase 1: Core Schema ───────────────────────────────────
  Step 1: SharedProperty 정의      (독립, 선행 조건 없음)
  Step 2: ObjectType 정의          (requires: Dataset backing plan)
  Step 3: Property 정의            (per ObjectType)
  Step 4: Property <-> SP 연결     (SharedProperty 승격 적용)
  ---- approval gate ----

Phase 2: Relationships ─────────────────────────────────
  Step 5: Interface 정의           (requires: SharedProperty)
  Step 6: OT implements Interface  (requires: ObjectType + Interface)
  Step 7: LinkType 정의            (requires: ObjectType x2)
  ---- approval gate ----

Phase 3: Kinetics ──────────────────────────────────────
  Step 8:  ActionType 정의         (requires: ObjectType)
  Step 9:  Function 정의
  Step 10: Rule/Constraint 정의
  ---- approval gate ----

Phase 4: Data Infrastructure ───────────────────────────
  Step 11: Dataset 생성/연결       (1:1 with ObjectType)
  Step 12: Pipeline 구축
  Step 13: Transform 정의
  Step 14: OntologySync 설정
  ---- approval gate ----

Phase 5: Collections ───────────────────────────────────
  Step 15: ObjectSet 정의
  Step 16: TimeSeries 설정
  Step 17: MediaSet 설정
  ---- approval gate ----

Phase 6: Applications ─────────────────────────────────
  Step 18: Workshop 모듈 구축
  Step 19: OSDK 코드 생성
  Step 20: Slate 대시보드
  Step 21: REST API 엔드포인트 설정
  Step 22: Automate 워크플로우
  ---- final approval ----
```

### 4.2 Phase 1 Detailed Checklist

> Phase 1 (Core Schema)의 상세 체크리스트. 각 항목은 user approval이 필요하다.

#### Step 1: SharedProperty 정의

```
[ ] 1.1  Cross-type 재사용 대상 Property 식별
         - 2+ ObjectType에서 동일 의미로 사용되는 속성 목록 작성
         - Interface 필요 속성 식별
[ ] 1.2  각 SharedProperty에 대해:
         - apiName 확정 (camelCase, immutable after creation)
         - baseType 확정 (사용 중 변경 불가)
         - description 작성 (모든 사용 맥락에서 정확한 의미)
         - constraints 설계 (range, regex, enum)
[ ] 1.3  Quantitative validation:
         - NC-SP-1: 2+ ObjectTypes 사용 확인
         - NC-SP-2: 100% 의미 동일성 확인
         - SC-SP-1/SC-SP-2 또는 BC-SP-1~3으로 승격 근거 확보
[ ] 1.4  --- USER APPROVAL ---
```

#### Step 2: ObjectType 정의

```
[ ] 2.1  모델링 대상 entity/event 식별
[ ] 2.2  각 ObjectType에 대해:
         - apiName 확정 (PascalCase, immutable after creation)
         - displayName, pluralDisplayName 작성
         - primaryKey 설계 (deterministic, immutable in OSv2)
         - titleKey 선택
         - backingDatasource 계획 (1:1 매핑)
         - status 설정 (ACTIVE / EXPERIMENTAL / DEPRECATED)
[ ] 2.3  Quantitative validation:
         - NC-OT-1~3 전부 충족 확인
         - SC 또는 BC 기반 판단 근거 문서화
[ ] 2.4  --- USER APPROVAL ---
```

#### Step 3: Property 정의

```
[ ] 3.1  각 ObjectType별 Property 목록 작성
[ ] 3.2  각 Property에 대해:
         - apiName 확정 (camelCase)
         - baseType 선택 (Section 3.2 Flow 참조)
         - renderHints 설정 (searchable, sortable, selectable, lowCardinality)
         - constraints 설계 (enum, range, regex)
         - required 여부 결정
         - visibility 설정
[ ] 3.3  Struct Property 검증:
         - depth = 1 확인
         - field 수 <= 10 확인
         - ES array matching caveat 인지
[ ] 3.4  --- USER APPROVAL ---
```

#### Step 4: SharedProperty 연결

```
[ ] 4.1  Step 1에서 정의한 SharedProperty를 각 ObjectType Property에 연결
         - Property.sharedProperty = SharedProperty.apiName
[ ] 4.2  메타데이터 상속 확인
         - displayName, description, renderHints 전파 확인
         - 필요 시 local override 설정
[ ] 4.3  연결 후 검증:
         - 사용처 수 확인 (usedByObjectTypes)
         - Interface 요구사항 충족 확인
[ ] 4.4  --- USER APPROVAL ---
```

### 4.3 Immutability Awareness (변경 불가 항목)

> 생성 후 변경할 수 없는 항목. 설계 시 신중히 결정해야 한다.

| Component | Field | Immutability | Impact of Wrong Choice |
|-----------|-------|-------------|----------------------|
| ObjectType | apiName | Immutable (user-set) | 새 OT 생성 + 전체 consumer 코드 변경 |
| ObjectType | primaryKey | Immutable (OSv2) | 새 OT 생성 + 데이터 마이그레이션 |
| ObjectType | RID | Immutable (system) | 변경 불가 (시스템 생성) |
| SharedProperty | apiName | Immutable | 새 SP 생성 + 전체 OT 전환 |
| SharedProperty | baseType | Immutable when in use | 새 SP 생성 + OT별 순차 전환 |

### 4.4 OSv2 Breaking Changes Awareness

> OSv2에서 OSv1 대비 강화된 제약사항. 마이그레이션 계획 시 반드시 인지해야 한다.

| Behavior | OSv1 | OSv2 | Action Required |
|----------|------|------|-----------------|
| Duplicate PK | Silent data loss | **Build failure** | PK 중복 검사 필수 |
| PK Change | Allowed (risky) | **Blocked** | 최초 PK 설계에 신중 |
| apiName Change | Allowed (risky) | **Blocked** | 최초 apiName 선정에 신중 |
| Nested Arrays | Allowed | **Forbidden** | Array<Array<T>> 평탄화 |
| Array Nulls | Allowed | **Forbidden** | Transform에서 null 제거 |
| Property Limit | Soft limit | **Hard limit (2000)** | 초과 시 OT 분리 |
| Edit Size | 32KB | 3MB | 더 큰 편집 가능하나 상한 존재 |

---

## Appendix A: Edge Case Decision Examples

> ObjectType.md Section 5.4의 Edge Case를 Taxonomy 관점에서 정리.

| Concept | PK | Lifecycle | Links | Props | Query% | Perms | Decision | Confidence |
|---------|-----|-----------|-------|-------|--------|-------|----------|------------|
| LinearEquation | Natural | Independent | >=2 | 10+ | >50% | No | **ObjectType** | HIGH |
| MathematicalConcept | Natural | Independent | >=3 | 7+ | >60% | No | **ObjectType** | HIGH |
| Coefficient (3 in "3x") | No PK | Parent-bound | 0 | 1 | <1% | No | **Property** | HIGH |
| Variable (x) | No PK | Parent-bound | 0 | 1-2 | <5% | No | **Property** | HIGH |
| Tag (name only) | Natural | Independent | Many-to-many | 1-2 | >40% | No | **ObjectType** | MEDIUM |
| DifficultyLevel (1-5) | Enum | N/A | 0 | 1 | <5% | No | **enum Property** | HIGH |
| Address (embedded) | No PK | Parent-bound | 0 | 3-5 | <5% | No | **Struct** | MEDIUM |
| Address (independent) | Natural | Independent | >=1 | 5+ | >30% | No | **ObjectType** | HIGH |
| Country (reference) | Natural | Independent | >=1 | 4+ | >20% | No | **ObjectType** | MEDIUM |

## Appendix B: SharedProperty Registry (Phase 1)

> Phase 1에서 식별된 SharedProperty 목록.

| apiName | displayName | baseType | Used By (OT count) | Interface Required | Status |
|---------|-------------|----------|---------------------|-------------------|--------|
| gradeLevel | Grade Level | Integer | 6+ | EducationalContent | Active |
| difficultyLevel | Difficulty Level | Integer | 4+ | EducationalContent | Active |
| displayNotation | Display Notation | String | 4+ | AlgebraicExpression | Active |
| curriculumStandard | Curriculum Standard | String | 3+ | EducationalContent | Active |
| variableSymbol | Variable Symbol | String | 3+ | AlgebraicExpression | Active |
| degree | Degree | Integer | 2+ | AlgebraicExpression | Active |

---

## Appendix C: Document Cross-References

| Document | Purpose | Relationship to TAXONOMY.md |
|----------|---------|----------------------------|
| `ObjectType.md` | ObjectType complete definition (11 sections) | Section 3.1 thresholds sourced from sections 1, 5 |
| `Property.md` | Property complete definition (11 sections) | Section 3.2 flow sourced from sections 1, 5 |
| `SharedProperty.md` | SharedProperty complete definition (11 sections) | Section 3.3 flow sourced from sections 1, 5 |
| `DEFINITIONS.md` | Cross-component formal definitions overlay | Complements TAXONOMY with glossary + definitions |
| `NAMING_AUDIT.md` | Naming consistency audit overlay | Complements TAXONOMY with naming rules |

---

> **Document Version:** 1.0.0
> **Created:** 2026-02-06
> **Author:** Claude Opus 4.6
> **Source Material:** ObjectType.md, Property.md, SharedProperty.md, WF-2 Design Spec
> **Gap Coverage:** G2 (formal definitions in flows), G3 (LinkType preview in 3.4D), G4 (cross-component matrices in 3.4), G10 (quantitative decision flows)
