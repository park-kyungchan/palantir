# Palantir Ontology: Formal Definitions (통합 정의서)

> **Phase 1: Core Primitives** (ObjectType, Property, SharedProperty)
> **Version:** 1.0.0 | **Last Verified:** 2026-02-06
> **Architecture:** Cross-cutting overlay -- aggregates formal definitions from all Phase 1 component files

---

## Table of Contents

1. [Glossary (용어 사전)](#1-glossary-용어-사전)
2. [Formal Definitions (NC/SC/BC)](#2-formal-definitions-ncscbc)
3. [Cross-Component Decision Matrix](#3-cross-component-decision-matrix)
4. [Quantitative Thresholds Summary (전체 정량 기준 집약)](#4-quantitative-thresholds-summary-전체-정량-기준-집약)
5. [Source URLs Registry](#5-source-urls-registry)
6. [Version History](#6-version-history)

---

## 1. Glossary (용어 사전)

> 전체 Ontology 컴포넌트 1줄 정의 + 공식 출처. Phase 1 컴포넌트는 본 문서에서 상세 정의 제공.

### Phase 1 -- Core Primitives (본 문서 범위)

| Component | Definition (정의) | Phase | Source |
|-----------|-------------------|-------|--------|
| **ObjectType** | 실세계 Entity 또는 Event의 Schema 정의. ObjectType은 type-level metadata(display name, property names, property data types, description)를 기술한다. | ✅ Phase 1 | [Object Types Overview](https://www.palantir.com/docs/foundry/object-link-types/object-types-overview) |
| **Property** | ObjectType의 속성을 정의하는 typed attribute. 각 Property는 baseType(22종)을 가지며, 값의 종류와 가능한 연산을 결정한다. | ✅ Phase 1 | [Properties Overview](https://www.palantir.com/docs/foundry/object-link-types/properties-overview) |
| **SharedProperty** | 여러 ObjectType에 걸쳐 재사용 가능한 property 사양. 메타데이터가 공유되며 데이터는 공유되지 않는다 (metadata shared, data NOT shared). | ✅ Phase 1 | [Shared Property Overview](https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview) |

### Phase 2 -- Relationships & Abstraction

| Component | Definition (정의) | Phase | Source |
|-----------|-------------------|-------|--------|
| **LinkType** | 두 ObjectType 간 관계(relationship)의 schema 정의. ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY 4가지 cardinality를 지원한다. | 📋 Phase 2 | [Link Types Overview](https://www.palantir.com/docs/foundry/object-link-types/link-types-overview) |
| **Interface** | SharedProperty로 구성된 추상 형태(abstract shape). 여러 ObjectType이 Interface를 구현하면 polymorphic query가 가능해진다. Multiple inheritance를 지원한다. | 📋 Phase 2 | [Interface Overview](https://www.palantir.com/docs/foundry/interfaces/interface-overview) |
| **ValueType** | Property의 baseType 위에 semantic constraint를 추가하는 래퍼. Email, URL, Currency Code 등 의미 기반 검증 패턴을 제공한다. | 📋 Phase 2 | [Value Types Overview](https://www.palantir.com/docs/foundry/object-link-types/value-types-overview) |

### Phase 3 -- Kinetic Primitives (Actions & Logic)

| Component | Definition (정의) | Phase | Source |
|-----------|-------------------|-------|--------|
| **ActionType** | 객체, 속성 값, 링크에 대한 변경 세트(create/modify/delete)의 schema 정의. 단일 원자적 트랜잭션으로 실행된다. | 📋 Phase 3 | [Action Types Overview](https://www.palantir.com/docs/foundry/action-types/overview) |
| **Function** | TypeScript로 작성되는 서버-side 비즈니스 로직. Ontology 데이터에 대한 쿼리, 집계, 변환을 수행하며 Workshop/OSDK/Actions에서 호출 가능하다. | 📋 Phase 3 | [Functions Overview](https://www.palantir.com/docs/foundry/functions/overview) |
| **Rule / Constraint** | ActionType 내에서 변경의 유효성을 검증하는 제약 조건. submission criteria, parameter validation, conditional logic을 포함한다. | 📋 Phase 3 | [Action Type Rules](https://www.palantir.com/docs/foundry/action-types/rules) |

### Phase 4 -- Data Pipeline Layer

| Component | Definition (정의) | Phase | Source |
|-----------|-------------------|-------|--------|
| **Dataset** | Foundry 내 데이터의 가장 기본적인 표현 단위. 파일 컬렉션의 래퍼로, 스키마 관리, 권한 관리, 트랜잭션 기반 버전 관리를 제공한다. | 📋 Phase 4 | [Datasets](https://www.palantir.com/docs/foundry/data-integration/datasets) |
| **Pipeline** | Dataset 간 데이터 흐름을 정의하는 DAG(Directed Acyclic Graph). 스케줄링, 의존성 관리, 증분 처리를 지원한다. | 📋 Phase 4 | [Pipeline Builder](https://www.palantir.com/docs/foundry/data-integration/pipeline-builder) |
| **Transform** | Python/SQL/Java로 작성되는 데이터 변환 로직. Dataset을 입력받아 새 Dataset을 출력하며, incremental/snapshot 모드를 지원한다. | 📋 Phase 4 | [Transforms Overview](https://www.palantir.com/docs/foundry/transforms-python/transforms-python-overview) |
| **OntologySync** | Dataset에서 Ontology로의 데이터 동기화 메커니즘. ObjectType, LinkType을 backing datasource에 매핑하고 Phonograph2(OSv2) 인덱싱을 수행한다. | 📋 Phase 4 | [Object Storage V2](https://www.palantir.com/docs/foundry/object-backend/object-storage-v2-breaking-changes) |

### Phase 5 -- Collection & Storage

| Component | Definition (정의) | Phase | Source |
|-----------|-------------------|-------|--------|
| **ObjectSet** | 단일 ObjectType의 object 인스턴스 컬렉션. 필터링, 관계 순회, 집계를 위한 기본 쿼리 단위이며, lazy-evaluation으로 동작한다. | 📋 Phase 5 | [Object Sets](https://www.palantir.com/docs/foundry/ontology-management/object-sets) |
| **TimeSeries** | 시간 축을 따라 측정되는 temporal measurement data의 저장/조회 컴포넌트. 센서 데이터, 모니터링 데이터 등에 적합하다. | 📋 Phase 5 | [Time Series](https://www.palantir.com/docs/foundry/time-series/overview) |
| **MediaSet** | 비정형 파일(이미지, 문서, 비디오 등)을 Ontology 오브젝트와 연결하여 저장/관리하는 컴포넌트. | 📋 Phase 5 | [Media Sets](https://www.palantir.com/docs/foundry/data-integration/media-sets) |

### Phase 6 -- Application & API Layer

| Component | Definition (정의) | Phase | Source |
|-----------|-------------------|-------|--------|
| **Workshop** | Ontology 기반 no-code 애플리케이션 빌더. 위젯 기반 인터렉티브 UI를 통해 운영 워크플로우를 구축한다. | 📋 Phase 6 | [Workshop Overview](https://www.palantir.com/docs/foundry/workshop/overview) |
| **OSDK** | Ontology Software Development Kit. TypeScript/Python 코드 자동 생성을 통해 Ontology를 프로그래밍 언어의 네이티브 객체로 접근 가능하게 한다. | 📋 Phase 6 | [OSDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview) |
| **REST API (v2)** | Foundry Ontology에 대한 HTTP 기반 프로그래밍 인터페이스. ObjectType CRUD, 검색, 집계, Action 실행을 지원한다. | 📋 Phase 6 | [API V2 Overview](https://www.palantir.com/docs/foundry/api/ontologies-v2-overview) |
| **Automate** | 이벤트 기반 워크플로우 자동화 플랫폼. ObjectSet 변경 감지, 스케줄 트리거, 조건부 Action 실행 체인을 구성한다. | 📋 Phase 6 | [Automate Overview](https://www.palantir.com/docs/foundry/automate/overview) |

---

## 2. Formal Definitions (NC/SC/BC)

> 각 Phase 1 컴포넌트의 Necessary Conditions (필요조건), Sufficient Conditions (충분조건),
> Boundary Conditions (경계조건)을 자기완결적(self-contained)으로 기술한다.
>
> - **NC (Necessary Condition):** 하나라도 위반하면 해당 컴포넌트가 될 수 없다.
> - **SC (Sufficient Condition):** 하나라도 충족하면 (NC 전제 하에) 해당 컴포넌트임이 확정된다.
> - **BC (Boundary Condition):** NC 충족 + SC 미충족인 회색 영역(Gray Zone)의 판단 지침.

---

### 2.1 ObjectType

> "이 개념을 ObjectType으로 모델링해야 하는가?"에 대한 형식적 판단 근거.
> Source: [Object Types Overview](https://www.palantir.com/docs/foundry/object-link-types/object-types-overview)

#### Necessary Conditions (필요조건) -- 하나라도 위반 시 ObjectType 불가

| ID | Condition (조건) | Test (검증 질문) | Violation (위반 시) |
|----|------------------|------------------|---------------------|
| **NC-OT-1** | 실세계 Entity 또는 Event를 표현한다 | 이 개념이 물리적/논리적으로 독립 존재하거나 발생하는가? | Property 또는 Struct로 모델링 |
| **NC-OT-2** | 고유 식별자(Primary Key)가 존재하거나 생성 가능하다 | 자연 키(natural key) 또는 합성 UUID로 각 인스턴스를 유일 식별할 수 있는가? | 다른 ObjectType의 속성으로 임베딩 |
| **NC-OT-3** | 하나 이상의 Backing Datasource에 매핑 가능하다 | 이 개념의 데이터가 Dataset으로 존재하거나 생성 가능한가? | Derived Property 또는 computed field로 처리 |

**Rationale:**
- **NC-OT-1**: Palantir Ontology의 근본 설계 원칙은 "ObjectType은 real-world entity 또는 event의 schema definition"이라는 것이다. 계산 결과, 집계값, 임시 상태 등은 해당되지 않는다.
- **NC-OT-2**: ObjectType의 각 인스턴스(Object)는 반드시 유일하게 식별되어야 한다. PK가 존재할 수 없는 개념(예: "분위기", "난이도 수준")은 Property나 enum으로 모델링한다.
- **NC-OT-3**: ObjectType은 반드시 하나 이상의 Datasource에 의해 뒷받침되어야 한다. 순수 계산값은 Derived Property로 처리하는 것이 적절하다.

#### Sufficient Conditions (충분조건) -- 하나라도 충족 시 ObjectType 확정 (NC 전제)

| ID | Condition (조건) | Rationale (근거) |
|----|------------------|-------------------|
| **SC-OT-1** | 3개 이상의 독립적 Property를 가지며, 독립 생명주기가 필요하다 | 3+ properties + independent lifecycle = unambiguous ObjectType. 충분한 속성을 보유하고 독립적으로 생성/수정/삭제되는 개념은 반드시 독립 엔티티로 모델링해야 한다. |
| **SC-OT-2** | 2개 이상의 다른 ObjectType과 LinkType 관계가 필요하다 | Multiple relationships = entity-level modeling required. 여러 엔티티와의 관계 참여는 해당 개념이 독립적 존재임을 입증한다. |
| **SC-OT-3** | 별도의 권한(ACL) 제어가 필요하다 | Permission boundary = must be independent entity. 권한 경계가 필요하면 반드시 독립 ObjectType이어야 한다. Weight는 LOW이지만 결정적(decisive)이다. |

#### Boundary Conditions (경계조건 / Gray Zone)

| ID | Scenario (시나리오) | Guidance (지침) | Threshold (정량 기준) |
|----|---------------------|-----------------|----------------------|
| **BC-OT-1** | Property 수 1-2개, 관계 1개 | Property로 시작하되, 독립 조회 필요 시 ObjectType으로 승격 | 독립 조회 빈도 > 전체 조회의 30%이면 ObjectType |
| **BC-OT-2** | 항상 부모 엔티티와 함께 생성/삭제되는 하위 구조 | Struct Property로 모델링. 단, 독립 권한/독립 Link 필요 시 ObjectType | 별도 권한 요구사항이 1개 이상이면 ObjectType |
| **BC-OT-3** | Lookup table / Reference data (변경 거의 없음) | 독립 조회/필터/Link 필요 시 ObjectType, 아니면 enum Property | 항목 수 >20 또는 항목별 속성 >=2개이면 ObjectType |
| **BC-OT-4** | Mathematical Variable (예: x in '3x - 2 = 5') | 교육 도메인에서 변수 자체는 독립 identity가 없으므로 Property | 독립 추적/관계가 필요한 경우에만 ObjectType |
| **BC-OT-5** | Term/Monomial (예: '3x' as component of polynomial) | 부모 Polynomial의 Struct Property로 시작 | 독립 추적 필요 시 ObjectType으로 승격 |

**BC Examples:**

| BC | Promote (승격) | Demote (강등) |
|----|----------------|---------------|
| BC-OT-1 | Tag (name만 있지만 독립 검색/필터 필수) --> ObjectType | Priority (High/Medium/Low 3값) --> enum Property |
| BC-OT-2 | Address (independent lookup + geocoding relationships) --> ObjectType | Address (always embedded in Person, never queried alone) --> Struct |
| BC-OT-3 | Country (code, name, region, population) --> ObjectType | DifficultyLevel (1-5 integer) --> enum Property |
| BC-OT-4 | Variable (연구 목적으로 변수 사용 패턴 독립 추적 필요) --> ObjectType | Variable (방정식 속성으로만 사용) --> Property |
| BC-OT-5 | Term (교육 분석에서 항별 오류 패턴 추적) --> ObjectType | Term (다항식의 내부 구조로만 표현) --> Struct Property |

---

### 2.2 Property

> "이 데이터를 Property로 모델링해야 하는가?"에 대한 형식적 판단 근거.
> Source: [Properties Overview](https://www.palantir.com/docs/foundry/object-link-types/properties-overview)

#### Necessary Conditions (필요조건) -- 하나라도 위반 시 Property 불가

| ID | Condition (조건) | Test (검증 질문) | Violation (위반 시) |
|----|------------------|------------------|---------------------|
| **NC-P-1** | ObjectType의 속성(attribute)을 표현한다 | 이 데이터가 특정 ObjectType 인스턴스의 특성을 기술하는가? | 독립 엔티티라면 ObjectType으로 모델링 |
| **NC-P-2** | 유효한 Base Type에 매핑 가능하다 | Palantir 지원 baseType 22종(String, Integer, Short, Long, Byte, Boolean, Float, Double, Decimal, Date, Timestamp, Geopoint, Geoshape, Array, Struct, Vector, MediaReference, Attachment, TimeSeries, GeotimeSeriesReference, CipherText, MandatoryControl) 중 하나에 매핑되는가? | 데이터 구조 재설계 필요 |
| **NC-P-3** | 소속 ObjectType의 backing dataset 컬럼에 매핑 가능하다 | Dataset에 해당 컬럼이 존재하거나 Transform으로 생성 가능한가? | Derived/computed field는 Transform에서 처리 |

#### Sufficient Conditions (충분조건) -- 하나라도 충족 시 Property 확정 (NC 전제)

| ID | Condition (조건) | Rationale (근거) |
|----|------------------|-------------------|
| **SC-P-1** | 단일 값이며 소속 ObjectType 없이 독립 의미가 없다 | Scalar attribute with no independent identity = Property. 독립 식별자 없이 부모 ObjectType에 종속된 단일 값은 반드시 Property이다. |
| **SC-P-2** | 소속 ObjectType과 동일한 생명주기를 가진다 | Created/deleted with parent = embedded attribute. 부모와 함께 생성/삭제되는 데이터는 부모의 속성으로 모델링한다. |

#### Boundary Conditions (경계조건 / Gray Zone)

| ID | Scenario (시나리오) | Guidance (지침) | Threshold (정량 기준) |
|----|---------------------|-----------------|----------------------|
| **BC-P-1** | 복합 구조 데이터 (여러 필드로 구성) | 필드 수 <=10이고 depth 1이면 Struct, 아니면 별도 ObjectType | 필드 수 >10 또는 nested structure 필요 --> ObjectType |
| **BC-P-2** | 다른 ObjectType을 참조하는 값 | FK-like 단방향 참조만 필요하면 Property, 양방향이면 LinkType | 역방향 조회 빈도 >10%이면 LinkType |
| **BC-P-3** | 여러 ObjectType에서 동일 속성 필요 | 2+ ObjectType에서 동일 의미면 SharedProperty, 아니면 각각 local | 사용 OT >=2 + 의미 동일 --> SharedProperty 승격 |

**BC Examples:**

| BC | Struct/Property | ObjectType/LinkType |
|----|-----------------|---------------------|
| BC-P-1 | Address (street, city, zip, country) --> Struct (4 fields, flat) | OrderItem (product, qty, price, discount, tax, ...) --> ObjectType (독립 조회 필요) |
| BC-P-2 | createdByUserId (단방향 기록용) --> String Property | assignedTo (User <-> Task 양방향 필요) --> LinkType |
| BC-P-3 | score (Integer) on 2 types, stable schema --> Local Property | gradeLevel on 6+ types with Interface --> SharedProperty |

---

### 2.3 SharedProperty

> "이 Property를 SharedProperty로 승격해야 하는가?"에 대한 형식적 판단 근거.
> Source: [Shared Property Overview](https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview)

#### Necessary Conditions (필요조건) -- 하나라도 위반 시 SharedProperty 불가

| ID | Condition (조건) | Test (검증 질문) | Violation (위반 시) |
|----|------------------|------------------|---------------------|
| **NC-SP-1** | 2개 이상의 ObjectType에서 사용되는 Property이다 | 이 속성이 여러 ObjectType에 걸쳐 존재하는가? | Local Property로 유지 |
| **NC-SP-2** | 모든 사용 ObjectType에서 동일한 의미(semantics)를 가진다 | 'gradeLevel'이 모든 타입에서 '학년'을 의미하는가? 아니면 타입마다 다른 뜻인가? | 별도 Local Property로 분리 |
| **NC-SP-3** | 유효한 Base Type에 매핑 가능하다 | Property와 동일한 baseType 체계를 사용하는가? | 데이터 구조 재설계 |

#### Sufficient Conditions (충분조건) -- 하나라도 충족 시 SharedProperty 확정 (NC 전제)

| ID | Condition (조건) | Rationale (근거) |
|----|------------------|-------------------|
| **SC-SP-1** | 3+ types에서 동일 의미로 사용되며, Interface cross-type 일관성이 필요하다 | Interface는 local property(권장) 또는 SharedProperty로 구성 가능. SharedProperty는 cross-type 메타데이터 일관성이 필요할 때 선택. [V3 수정] |
| **SC-SP-2** | 3개 이상의 ObjectType에서 동일 의미로 사용되며, 메타데이터 일괄 관리가 필요하다 | 3+ types + centralized management = clear SharedProperty case. |

#### Boundary Conditions (경계조건 / Gray Zone)

| ID | Scenario (시나리오) | Guidance (지침) | Threshold (정량 기준) |
|----|---------------------|-----------------|----------------------|
| **BC-SP-1** | 2개 ObjectType에서만 사용, Interface 불필요 | 메타데이터 변경 빈도가 높으면 SharedProperty, 안정적이면 Local | 월 1회 이상 메타데이터 변경 --> SharedProperty, 분기 1회 미만 --> Local |
| **BC-SP-2** | 이름은 같지만 의미가 미묘하게 다른 속성 | 90% 이상 의미 중첩이면 SharedProperty 가능, 미만이면 분리 | 의미 중첩 >=90% --> SharedProperty (단, description에서 차이 명시) |
| **BC-SP-3** | 현재 1개 ObjectType이지만 확장 예정 | 확정된 로드맵에 2+ type 사용이 있으면 선제 승격 가능 | 3개월 내 확정된 추가 ObjectType 계획이 있으면 승격 |

**BC Examples:**

| BC | Promote (승격) | Demote (유지) |
|----|----------------|---------------|
| BC-SP-1 | createdAt (timestamp) across 2 types, formatting rules change frequently --> SharedProperty | score (Integer) on 2 types, stable schema --> keep Local |
| BC-SP-2 | status (ACTIVE/INACTIVE) on Employee and Project --> same lifecycle semantics | date on Invoice (issue date) vs Event (occurrence date) --> different semantics, keep Local |
| BC-SP-3 | gradeLevel on MathProblem only, but Lesson and Assessment planned for Q2 --> 선제 승격 | polynomialDegree, no other type will ever need this --> keep Local |

---

## 3. Cross-Component Decision Matrix

> 컴포넌트 간 모델링 선택 시 사용하는 비교 매트릭스.

---

### 3.1 ObjectType vs Property

> **핵심 질문:** "이 개념을 독립 엔티티(ObjectType)로 모델링할 것인가, 기존 ObjectType의 속성(Property)으로 모델링할 것인가?"

| Criterion (기준) | ObjectType | Property | Weight |
|-------------------|-----------|----------|--------|
| **독립 식별성** | PK로 유일 식별 가능 | 소속 OT 없이 무의미 | **CRITICAL** |
| **관계 참여** | LinkType source/target으로 참여 | 직접 관계 참여 불가 | **HIGH** |
| **독립 생명주기** | 독립 CRUD (생성/수정/삭제) | 부모 생명주기에 종속 | **HIGH** |
| **Property 수** | 3개 이상 독립 속성 보유 | 1개 (단일 값) | MEDIUM |
| **독립 조회 비율** | 전체 조회의 >30% 독립 접근 | 부모 OT 통해서만 접근 (<10%) | MEDIUM |
| **권한 분리** | 별도 ACL 필요 시 필수 | 부모 권한 상속으로 충분 | LOW (decisive)* |

*\* 있으면 결정적: 별도 ACL이 필요하면 무조건 ObjectType*

**Decision Rule:**
```
IF 독립 PK 존재 AND (3+ Properties + 독립 생명주기) → ObjectType
IF 독립 PK 존재 AND (2+ LinkType 관계) → ObjectType
IF 별도 ACL 필요 → ObjectType (무조건)
IF 위 조건 모두 미충족 → Property
```

---

### 3.2 ObjectType vs Struct Property

> **핵심 질문:** "복합 구조 데이터를 독립 ObjectType으로 모델링할 것인가, 부모 ObjectType의 Struct Property로 모델링할 것인가?"

| Criterion (기준) | ObjectType | Struct Property | Weight |
|-------------------|-----------|-----------------|--------|
| **독립 식별성** | 고유 PK로 독립 식별 | 부모 OT의 속성 (PK 없음) | **CRITICAL** |
| **필드 수** | 무제한 (max 2000 properties) | max 10 fields | **HIGH** |
| **조회 방식** | 독립 필터/검색/정렬 지원 | ES array matching만 가능 (제한적) | **HIGH** |
| **생명주기** | 독립 CRUD | 부모 종속 (함께 생성/삭제) | **HIGH** |
| **중첩** | 관계(LinkType)로 자유 표현 | depth 1만 가능 (nested struct 불가) | MEDIUM |
| **권한** | 별도 ACL 가능 | 부모 ACL 상속 | MEDIUM |

**Decision Rule:**
```
IF 필드 수 >10 → ObjectType (Struct 한계 초과)
IF nested structure 필요 → ObjectType (Struct depth=1 제한)
IF 독립 조회 >30% → ObjectType
IF 독립 관계(LinkType) 필요 → ObjectType
IF 필드 수 <=10 AND depth 1 AND 부모 종속 → Struct Property
```

**Struct Property 제약 요약:**
- Max 10 fields
- Depth 1 only (no nested structs)
- No Array/Vector within struct fields
- ES array matching semantics (cross-element 매칭 주의 -- runtime caveat)

---

### 3.3 Property vs SharedProperty

> **핵심 질문:** "이 Property를 SharedProperty로 승격해야 하는가, Local Property로 유지할 것인가?"

| Criterion (기준) | Property (Local) | SharedProperty | Weight |
|-------------------|-----------------|----------------|--------|
| **사용 범위** | 1개 ObjectType | 2개 이상 ObjectType | **CRITICAL** |
| **의미 동일성** | 타입별 고유 의미 가능 | 모든 타입에서 100% 동일 의미 필수 | **CRITICAL** |
| **Interface 요구** | Interface 참여 불가 | Interface 구현 시 필수 | **HIGH (decisive)** |
| **메타데이터 관리** | 개별 관리 (N개 OT 각각 수정) | 중앙 관리 (1회 변경 = 전체 전파) | MEDIUM |
| **Governance 비용** | Low (OT Editor만 필요) | Medium~High (SP Editor + OT Editor) | LOW |
| **baseType 변경** | 자유 (주의 필요) | 사용 중 변경 시스템 차단 | LOW |

**Decision Rule:**
```
IF Interface 요구 → SharedProperty (무조건, SC-SP-1)
IF >=3 ObjectType + 100% 동일 의미 → SharedProperty (SC-SP-2)
IF 2 ObjectType + 100% 동일 + 메타데이터 변경 빈번 → SharedProperty
IF 2 ObjectType + 100% 동일 + 메타데이터 안정 → Either OK (향후 확장 고려)
IF 1 ObjectType → Local Property (BC-SP-3 예외: 3개월 내 확장 확정 시 선제 승격)
IF <90% 의미 중첩 → Local Property (별도 분리)
```

---

### 3.4 Quick Decision Flowchart

```
START: 새로운 개념을 모델링해야 한다
│
├─ Q1: 실세계 Entity/Event인가? (NC-OT-1)
│   │
│   ├─ NO ──────────────────────────────────────────────────→ Property
│   │
│   └─ YES
│       │
│       ├─ Q2: 독립 PK 존재 가능? (NC-OT-2)
│       │   │
│       │   ├─ NO ─────────────────────────────────────────→ Property
│       │   │
│       │   └─ YES
│       │       │
│       │       ├─ Q3: Backing Datasource 매핑 가능? (NC-OT-3)
│       │       │   │
│       │       │   ├─ NO ─────────────────────────────────→ Derived Property / Computed Field
│       │       │   │
│       │       │   └─ YES (NC 모두 충족)
│       │       │       │
│       │       │       ├─ Q4: 독립 생명주기? (CRUD)
│       │       │       │   │
│       │       │       │   ├─ NO ─────────────────────────→ Struct Property
│       │       │       │   │   (단, 필드 >10 또는 depth >1 → ObjectType)
│       │       │       │   │
│       │       │       │   └─ YES
│       │       │       │       │
│       │       │       │       ├─ Q5: >=3 Properties?
│       │       │       │       │   │
│       │       │       │       │   ├─ NO ─────────────────→ [!] Gray Zone (BC-OT-1~5 참조)
│       │       │       │       │   │
│       │       │       │       │   └─ YES
│       │       │       │       │       │
│       │       │       │       │       └─────────────────→ ObjectType (SC-OT-1 충족)
│       │       │       │       │
│       │       │       │       └─ (or) 2+ LinkType 관계? → ObjectType (SC-OT-2 충족)
│       │       │       │       └─ (or) 별도 ACL 필요?    → ObjectType (SC-OT-3 충족)
│       │       │       │
│       │       │       └─ Q6: ObjectType으로 확정됨
│       │       │           │
│       │       │           └─ Q7: 이 ObjectType의 각 Property에 대해:
│       │       │               │
│       │       │               ├─ 2+ ObjectType에서 동일 의미로 사용?
│       │       │               │   │
│       │       │               │   ├─ YES ────────────────→ SharedProperty 후보 (Section 2.3 참조)
│       │       │               │   │
│       │       │               │   └─ NO ─────────────────→ Local Property
│       │       │               │
│       │       │               └─ 역방향 조회 >10% 필요?
│       │       │                   │
│       │       │                   ├─ YES ────────────────→ LinkType 전환 검토
│       │       │                   │
│       │       │                   └─ NO ─────────────────→ FK-style Property 유지
```

---

## 4. Quantitative Thresholds Summary (전체 정량 기준 집약)

> Phase 1 전체 컴포넌트의 정량 판단 기준을 단일 테이블로 집약한다.

### 4.1 ObjectType 판단 기준

| Decision | Signal (신호) | Strong YES | Gray Zone | Strong NO | Weight |
|----------|--------------|-----------|-----------|-----------|--------|
| Is ObjectType? | 자연 PK 존재 | Yes (natural key) | Synthetic OK | No PK possible | **CRITICAL** |
| Is ObjectType? | 독립 생명주기 | Yes (full CRUD) | Partial (생성은 부모와 함께, 수정은 독립) | No (parent-bound) | **HIGH** |
| Is ObjectType? | 관계(Link) 수 | >=2 relationships | 1 relationship | 0 relationships | **HIGH** |
| Is ObjectType? | Property 수 | >=3 properties | 1-2 properties | 0 properties | MEDIUM |
| Is ObjectType? | 독립 조회 비율 | >30% | 10-30% | <10% | MEDIUM |
| Is ObjectType? | 별도 권한 필요 | Yes (ACL) | - | No | LOW (decisive) |

**ObjectType Decision Rule:**
```
NC-OT-1 AND NC-OT-2 AND NC-OT-3 ALL 충족:
  IF "별도 권한 필요" = Yes → ObjectType (SC-OT-3, decisive)
  ELIF "자연 PK" = Strong YES AND ("독립 생명주기" = Strong YES OR "관계 수" = Strong YES)
    → ObjectType (CRITICAL + HIGH = confirmed)
  ELIF any SC (SC-OT-1, SC-OT-2, SC-OT-3) satisfied → ObjectType
  ELIF all signals Gray Zone → BC-OT-1~5 참조
  ELSE → NOT ObjectType (Property or Struct)
NC 하나라도 미충족 → NOT ObjectType
```

### 4.2 Property 판단 기준

| Decision | Signal (신호) | Strong Property | Gray Zone | Strong ObjectType | Weight |
|----------|--------------|----------------|-----------|-------------------|--------|
| Is Property? | 독립 식별성 | PK 없음, 부모 OT 통해서만 접근 | Synthetic PK 가능하나 단독 조회 드묾 | 자연 PK 존재 + 독립 조회 >30% | **CRITICAL** |
| Is Property? | 속성 수 | 1개 (단일 값) | 2-10개 (Struct 후보) | >10개 + 독립 관계 | **HIGH** |
| Is Property? | 생명주기 독립성 | 부모와 동일 생명주기 | 부분적 독립 | 완전 독립 CRUD | **HIGH** |
| Is Property? | 관계 참여 | 0개 (관계 불필요) | 1개 (단방향 참조) | >=2개 (양방향 + 다중 관계) | **HIGH** |
| Is Property? | 독립 조회 비율 | <10% | 10-30% | >30% | MEDIUM |
| Is Property? | 권한 분리 | 부모 권한 상속 충분 | - | 별도 ACL 필수 | LOW (decisive) |

**Property Decision Rule:**
```
NC-P-1~3 전부 충족 + CRITICAL signal이 strong_property → Property 확정
NC-P-1~3 충족 + gray_zone 다수 → Struct 검토 (필드 <=10, depth 1)
NC 위반 또는 CRITICAL signal이 strong_objecttype → ObjectType으로 승격
```

### 4.3 SharedProperty 승격 기준

| Decision | Signal (신호) | Promote (승격) | Gray Zone | Keep Local (유지) | Weight |
|----------|--------------|---------------|-----------|-------------------|--------|
| Promote to SP? | 사용 ObjectType 수 | >=3 types | 2 types | 1 type | **CRITICAL** |
| Promote to SP? | 의미 동일성 | 100% 동일 | 90%+ 유사 | <90% | **CRITICAL** |
| Promote to SP? | Interface 요구 | Yes (Interface 필요) | - | No (Interface 불필요) | **HIGH (decisive)** |
| Promote to SP? | 메타데이터 변경 빈도 | 월 1회 이상 | 분기 1회 | 거의 없음 (연 1회 미만) | MEDIUM |

**SharedProperty Decision Rule:**
```
(>=2 types + 100% same semantics) OR (Interface required) = SharedProperty
Interface 요구 → 무조건 SharedProperty (SC-SP-1)
3+ types + 100% 동일 → SharedProperty (SC-SP-2)
2 types + 100% 동일 + 변경 빈번 → SharedProperty
2 types + 100% 동일 + 안정 → Either OK
1 type → Local (3개월 내 확장 확정 시 예외)
<90% 의미 중첩 → Local (별도 분리)
```

### 4.4 Struct vs ObjectType 승격 기준

| Decision | Signal (신호) | Struct OK | Gray Zone | ObjectType 필요 | Weight |
|----------|--------------|-----------|-----------|-----------------|--------|
| Struct or OT? | 필드 수 | <=10 | - | >10 | **HIGH** |
| Struct or OT? | 중첩 필요 | depth 1 충분 | - | nested structure 필요 | **HIGH** |
| Struct or OT? | 독립 조회 | <10% | 10-30% | >30% | **HIGH** |
| Struct or OT? | 독립 관계(Link) | 불필요 | - | 필요 | **HIGH** |
| Struct or OT? | 독립 생명주기 | 부모 종속 | 부분적 독립 | 완전 독립 | MEDIUM |

### 4.5 Property vs LinkType 전환 기준

| Decision | Signal (신호) | Property (FK) OK | Gray Zone | LinkType 필요 | Weight |
|----------|--------------|-----------------|-----------|---------------|--------|
| FK or Link? | 역방향 조회 빈도 | <10% | 10-30% | >10% | **HIGH** |
| FK or Link? | 관계 방향 | 단방향만 | - | 양방향 필요 | **HIGH** |
| FK or Link? | 관계 카디널리티 | N:1 단순 참조 | - | M:N 다대다 관계 | **HIGH** |
| FK or Link? | Graph traversal | 불필요 | - | 필요 | MEDIUM |

---

## 5. Source URLs Registry

> WF-1 검증 완료된 공식 Palantir 문서 URL 목록.

### ObjectType URLs

| Topic | URL | Verified |
|-------|-----|----------|
| Object Types Overview | https://www.palantir.com/docs/foundry/object-link-types/object-types-overview | 2026-02-06 |
| Create Object Type | https://www.palantir.com/docs/foundry/object-link-types/create-object-type | 2026-02-06 |
| Object Type Metadata | https://www.palantir.com/docs/foundry/object-link-types/object-type-metadata | 2026-02-06 |

### Property URLs

| Topic | URL | Verified |
|-------|-----|----------|
| Properties Overview | https://www.palantir.com/docs/foundry/object-link-types/properties-overview | 2026-02-06 |
| Property Metadata | https://www.palantir.com/docs/foundry/object-link-types/property-metadata | 2026-02-06 |
| Base Types | https://www.palantir.com/docs/foundry/object-link-types/base-types | 2026-02-06 |
| Structs Overview | https://www.palantir.com/docs/foundry/object-link-types/structs-overview | 2026-02-06 |
| Value Types Overview | https://www.palantir.com/docs/foundry/object-link-types/value-types-overview | 2026-02-06 |
| Value Type Constraints | https://www.palantir.com/docs/foundry/object-link-types/value-type-constraints | 2026-02-06 |

### SharedProperty URLs

| Topic | URL | Verified |
|-------|-----|----------|
| Shared Property Overview | https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview | 2026-02-06 |
| Create Shared Property | https://www.palantir.com/docs/foundry/object-link-types/create-shared-property | 2026-02-06 |
| Shared Property Metadata | https://www.palantir.com/docs/foundry/object-link-types/shared-property-metadata | 2026-02-06 |
| Interface Overview | https://www.palantir.com/docs/foundry/interfaces/interface-overview | 2026-02-06 |

### Cross-Cutting URLs

| Topic | URL | Verified |
|-------|-----|----------|
| Action Scale/Limits | https://www.palantir.com/docs/foundry/action-types/scale-property-limits | 2026-02-06 |
| OSv2 Breaking Changes | https://www.palantir.com/docs/foundry/object-backend/object-storage-v2-breaking-changes | 2026-02-06 |

### Phase 2+ Component URLs (참고용)

| Topic | URL | Verified |
|-------|-----|----------|
| Link Types Overview | https://www.palantir.com/docs/foundry/object-link-types/link-types-overview | 2026-02-03 |
| Action Types Overview | https://www.palantir.com/docs/foundry/action-types/overview | 2026-02-05 |
| Action Type Rules | https://www.palantir.com/docs/foundry/action-types/rules | 2026-02-05 |
| Functions Overview | https://www.palantir.com/docs/foundry/functions/overview | 2026-02-05 |
| Datasets | https://www.palantir.com/docs/foundry/data-integration/datasets | 2026-02-03 |
| Pipeline Builder | https://www.palantir.com/docs/foundry/data-integration/pipeline-builder | 2026-02-03 |
| Transforms (Python) | https://www.palantir.com/docs/foundry/transforms-python/transforms-python-overview | 2026-02-03 |
| Workshop Overview | https://www.palantir.com/docs/foundry/workshop/overview | 2026-02-03 |
| OSDK Overview | https://www.palantir.com/docs/foundry/ontology-sdk/overview | 2026-02-03 |

---

## 6. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-06 | Initial Phase 1 release -- ObjectType, Property, SharedProperty formal definitions, cross-component decision matrices, quantitative thresholds, source URLs registry |

### Source Documents

| Document | Purpose |
|----------|---------|
| `ObjectType.md` | Component 1 정의서 (11 sections) |
| `Property.md` | Component 2 정의서 (11 sections) |
| `SharedProperty.md` | Component 3 정의서 (11 sections) |
| `wf1_gap_report.md` | Gap analysis identifying G1-G10 |
| `wf2_design_spec.md` | Design spec with 11-section template and quantitative thresholds |
| `session1.md` ~ `session6.md` | Original session reference material (16 components across 6 sessions) |

### Gap Coverage (이 문서에서 해결)

| Gap | Severity | Resolution |
|-----|----------|------------|
| G2 (Boundary conditions 비정량적) | HIGH | Section 2 formal definitions + Section 4 quantitative thresholds |
| G4 (Interface vs SharedProperty 구분 부재) | HIGH | Section 3.3 Property vs SharedProperty matrix |
| G10 (Decision tree 정량 기준 부재) | HIGH | Section 4 전체 정량 기준 집약 + Section 3.4 Decision Flowchart |

### Related Documents

| Document | Relationship |
|----------|-------------|
| `TAXONOMY.md` | Component hierarchy, dependency graph, migration sequence (Phase 2 예정) |
| `NAMING_AUDIT.md` | Naming consistency audit, reserved words registry (G5 coverage) |
