# Component Definition: SharedProperty

> **Version:** 1.0.0 | **Last Verified:** 2026-02-06
> **Source:** https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview
> **Feature Status:** GA (Generally Available) -- NOT Beta
> **Visual Identifier:** Globe icon (🌐)

---

## 1. formal_definition

```yaml
formal_definition:
  component: "SharedProperty"
  version: "1.0.0"
  last_verified: "2026-02-06"
  source: "https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview"
  feature_status: "GA (NOT Beta)"  # confirmed in WF-1

  # ─────────────────────────────────────────────────
  # Necessary Conditions (모든 조건 충족 필수)
  # ─────────────────────────────────────────────────
  necessary_conditions:
    - id: NC-SP-1
      condition: "2개 이상의 ObjectType에서 사용되는 Property이다"
      test: "이 속성이 여러 ObjectType에 걸쳐 존재하는가?"
      violation_means: "Local Property로 유지"

    - id: NC-SP-2
      condition: "모든 사용 ObjectType에서 동일한 의미(semantics)를 가진다"
      test: "'gradeLevel'이 모든 타입에서 '학년'을 의미하는가? 아니면 타입마다 다른 뜻인가?"
      violation_means: "별도 Local Property로 분리 (e.g., gradeLevel vs difficultyLevel)"

    - id: NC-SP-3
      condition: "유효한 Base Type에 매핑 가능하다"
      test: "Property와 동일한 baseType 체계를 사용하는가?"
      violation_means: "데이터 구조 재설계"

  # ─────────────────────────────────────────────────
  # Sufficient Conditions (하나라도 충족 시 SharedProperty 확정)
  # ─────────────────────────────────────────────────
  sufficient_conditions:
    - id: SC-SP-1
      condition: "3개 이상의 ObjectType에서 동일 의미로 사용되며, Interface를 통한 cross-type 일관성이 필요하다"
      rationale: >
        Interface는 local property(권장) 또는 SharedProperty로 구성 가능하다.
        그러나 3+ types에서 동일 속성을 Interface로 강제하려면 SharedProperty가
        cross-type 메타데이터 일관성을 보장하는 가장 효과적인 수단이다.
      note: >
        [V3 검증 수정] 공식 문서: "Interface properties can be defined locally on
        the interface (recommended) or using shared properties."
        Interface가 SharedProperty를 필수로 요구하지 않음. 이전 버전의
        "Interface schema는 SharedProperty로만 구성 가능" 주장은 incorrect.

    - id: SC-SP-2
      condition: "3개 이상의 ObjectType에서 동일 의미로 사용되며, 메타데이터 일괄 관리가 필요하다"
      rationale: "3+ types + centralized management = clear SharedProperty case"

  # ─────────────────────────────────────────────────
  # Boundary Conditions (회색 영역 판단 기준)
  # ─────────────────────────────────────────────────
  boundary_conditions:
    - id: BC-SP-1
      scenario: "2개 ObjectType에서만 사용, Interface 불필요"
      guidance: "메타데이터 변경 빈도가 높으면 SharedProperty, 안정적이면 Local"
      threshold: "월 1회 이상 메타데이터 변경 → SharedProperty, 분기 1회 미만 → Local"
      examples:
        promote: "createdAt (timestamp) across 2 types, formatting rules change frequently → SharedProperty"
        demote: "score (Integer) on 2 types, stable schema → keep Local"

    - id: BC-SP-2
      scenario: "이름은 같지만 의미가 미묘하게 다른 속성"
      guidance: "90% 이상 의미 중첩이면 SharedProperty 가능, 미만이면 분리"
      threshold: "의미 중첩 >=90% → SharedProperty (단, description에서 차이 명시)"
      examples:
        promote: "status (ACTIVE/INACTIVE) on Employee and Project → same lifecycle semantics"
        demote: "date on Invoice (issue date) vs Event (occurrence date) → different semantics"

    - id: BC-SP-3
      scenario: "현재 1개 ObjectType이지만 확장 예정"
      guidance: "확정된 로드맵에 2+ type 사용이 있으면 선제 승격 가능"
      threshold: "3개월 내 확정된 추가 ObjectType 계획이 있으면 승격"
      examples:
        promote: "gradeLevel on MathProblem only, but Lesson and Assessment planned for Q2"
        demote: "polynomialDegree, no other type will ever need this"
```

### Formal Definition Summary

| Category | ID | Core Statement |
|----------|----|----------------|
| Necessary | NC-SP-1 | 2+ ObjectType에서 사용 |
| Necessary | NC-SP-2 | 의미 동일성 보장 |
| Necessary | NC-SP-3 | 유효 baseType 매핑 |
| Sufficient | SC-SP-1 | 3+ types + Interface cross-type 일관성 필요 시 |
| Sufficient | SC-SP-2 | 3+ types + 중앙관리 필요 |
| Boundary | BC-SP-1 | 2 types only → 변경빈도로 판단 |
| Boundary | BC-SP-2 | 의미 유사 → 90% 기준 |
| Boundary | BC-SP-3 | 미래 확장 → 3개월 로드맵 기준 |

---

## 2. official_definition

**Source**: https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview

> "A shared property is a property that can be used on multiple object types in your ontology. Shared properties allow for consistent data modeling across object types and centralized management of property metadata."

### Key Clarifications

| Aspect | Clarification |
|--------|---------------|
| **Feature Status** | SharedProperty is **NOT Beta**. It is a **GA (Generally Available)** feature. (WF-1 검증 결과) |
| **Metadata vs Data** | **Metadata is shared, DATA is NOT shared.** 각 ObjectType은 자체 데이터 값을 독립적으로 유지한다. SharedProperty가 공유하는 것은 이름, 설명, baseType, renderHints 등의 메타데이터 사양이지, 실제 데이터 행/값이 아니다. |
| **Visual Identifier** | SharedProperty는 UI에서 **globe icon** (🌐)으로 표시된다. Ontology Manager에서 SharedProperty를 사용하는 Property 옆에 🌐 아이콘이 나타난다. |
| **Governance Model** | SharedProperty 변경은 해당 SharedProperty를 사용하는 **모든** ObjectType에 전파된다. 중앙 관리 = 중앙 책임. |

### What SharedProperty IS

- 여러 ObjectType에 걸쳐 **일관된 property 사양**을 보장하는 메커니즘
- Interface contract를 구성하는 **유일한 수단** (local Property는 Interface에 사용 불가)
- 메타데이터 (displayName, description, renderHints, constraints)의 **단일 진실 공급원** (single source of truth)

### What SharedProperty is NOT

- 데이터 공유 메커니즘이 아니다 (각 ObjectType은 별도 데이터)
- 외래 키(FK) 또는 관계(Link)의 대체물이 아니다
- ObjectType 간 데이터 동기화 도구가 아니다
- Beta 기능이 아니다 (정식 GA 기능)

### Official Documentation URLs

| Page | URL |
|------|-----|
| SharedProperty Overview | https://www.palantir.com/docs/foundry/object-link-types/shared-property-overview |
| Create SharedProperty | https://www.palantir.com/docs/foundry/object-link-types/create-shared-property |
| SharedProperty Metadata | https://www.palantir.com/docs/foundry/object-link-types/shared-property-metadata |
| Interface Overview | https://www.palantir.com/docs/foundry/interfaces/interface-overview |

---

## 3. semantic_definition

| Paradigm | Equivalent Concept | Mapping Notes |
|----------|-------------------|---------------|
| **OOP** | Abstract property / Trait field | Shared across implementing classes |
| **RDBMS** | Shared column definition | Same column spec across tables (but each table has its own data) |
| **RDF/OWL** | owl:DatatypeProperty (domain-independent) | Property usable by multiple classes |
| **TypeScript** | Property in shared interface | Reused via interface implementation |
| **Design Patterns** | Template Method field | Consistent field across hierarchy |
| **Java** | Interface method signature | 구현은 각 class에서, 계약은 중앙에서 |
| **Protobuf** | Shared field definition | 같은 field number/type을 여러 message에서 사용 |

**Semantic Role**: SharedProperty defines a **canonical property specification** that ensures semantic consistency across multiple ObjectTypes. It is the mechanism for implementing Interface contracts.

### Analogy: SharedProperty = Blueprint, Property = Instance

```
SharedProperty "gradeLevel"       ← Blueprint (메타데이터 사양)
  │
  ├── MathProblem.gradeLevel      ← Instance (각자 데이터 보유)
  ├── Lesson.gradeLevel           ← Instance (각자 데이터 보유)
  ├── Assessment.gradeLevel       ← Instance (각자 데이터 보유)
  └── LinearEquation.gradeLevel   ← Instance (각자 데이터 보유)
```

Blueprint(SharedProperty)를 수정하면 모든 Instance(Property)의 메타데이터가 변경되지만, 각 Instance의 **데이터 값은 독립적**이다.

---

## 4. structural_schema

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
    description: "Programmatic identifier (camelCase, unique across ontology)"
    pattern: "^[a-z][a-zA-Z0-9]*$"
    examples: ["gradeLevel", "displayNotation", "difficultyLevel"]
    immutable_after_creation: true  # apiName cannot be changed after creation

  displayName:
    type: string
    description: "Human-readable name shown in UI"
    examples: ["Grade Level", "Display Notation", "Difficulty Level"]

  description:
    type: string
    description: "Explanatory text describing the property's purpose and semantics"
    examples: ["The target grade level for this educational content"]

  baseType:
    type: string
    description: "Data type (same options as Property)"
    enum:
      - "Boolean"
      - "Byte"
      - "Date"
      - "Decimal"
      - "Double"
      - "Float"
      - "GeoPoint"
      - "GeoShape"
      - "Integer"
      - "Long"
      - "Short"
      - "String"
      - "Timestamp"
      # Complex types:
      - "Array"       # Array of base types
      - "Struct"      # Structured type (depth 1, max 10 fields)
      - "TimeSeries"  # Time series data
      - "Vector"      # ML embedding vector (max 2048 dimensions)
    immutable_when_in_use: true  # Cannot change baseType when ObjectTypes reference this SP

  rid:
    type: string
    description: "Auto-generated Resource Identifier (system-assigned)"
    readOnly: true

  visibility:
    type: string
    enum: ["PROMINENT", "NORMAL", "HIDDEN"]
    default: "NORMAL"
    description: |
      PROMINENT: Always shown in object views
      NORMAL: Shown when expanded
      HIDDEN: Only available in API/programmatic access

  renderHints:
    type: object
    properties:
      searchable:
        type: boolean
        description: "Property is indexed for search"
      sortable:
        type: boolean
        description: "Property can be used for sorting (requires searchable)"
      selectable:
        type: boolean
        description: "Property appears in filter dropdowns (requires searchable)"
    dependencies:
      sortable: ["searchable"]    # sortable implies searchable
      selectable: ["searchable"]  # selectable implies searchable

  valueFormatting:
    type: object
    description: "Numeric, date/time, user ID formatting rules"

  typeClasses:
    type: array
    items:
      type: string
    description: "Additional metadata type classes"

  constraints:
    type: object
    description: "Same constraint options as Property (range, regex, enum, etc.)"
    properties:
      range:
        type: object
        properties:
          min: { type: number }
          max: { type: number }
      regex:
        type: string
        description: "Regular expression pattern for String values"
      enum:
        type: array
        description: "Allowed values list"
      required:
        type: boolean
        description: "Whether value is required (cannot add if existing data has nulls)"

  # ─── Relationship metadata (read-only, system-managed) ───
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
    description: "ObjectTypes currently using this SharedProperty"
    readOnly: true
```

### Schema Notes

| Field | Mutability | Notes |
|-------|-----------|-------|
| `apiName` | Immutable after creation | 생성 후 변경 불가 |
| `displayName` | Mutable | 모든 사용처에 전파 |
| `description` | Mutable | 모든 사용처에 전파 |
| `baseType` | Immutable when in use | 사용 중인 OT가 있으면 변경 불가 |
| `visibility` | Mutable | 모든 사용처에 전파 |
| `renderHints` | Mutable | 모든 사용처에 전파 |
| `constraints` | Conditionally mutable | 기존 데이터와 호환되어야 함 |
| `usedByInterfaces` | System-managed | 읽기 전용 |
| `usedByObjectTypes` | System-managed | 읽기 전용 |

---

## 5. quantitative_decision_matrix

```yaml
quantitative_decision_matrix:
  component: "SharedProperty"
  purpose: "Local Property를 SharedProperty로 승격할지 판단하는 정량 매트릭스"

  signals:
    - signal: "사용 ObjectType 수"
      metric: "이 Property를 사용하는 (또는 사용 예정인) ObjectType 개수"
      thresholds:
        promote: ">=3"
        gray_zone: "2"
        keep_local: "1"
      weight: CRITICAL
      rationale: "SharedProperty의 핵심 가치는 cross-type 재사용. 1개면 의미 없음."

    - signal: "의미 동일성"
      metric: "모든 사용 ObjectType에서 동일 semantics인지 (%, 전문가 판단)"
      thresholds:
        promote: "100% 동일"
        gray_zone: "90%+ 유사"
        keep_local: "<90%"
      weight: CRITICAL
      rationale: "의미가 다른 속성을 강제 공유하면 semantic corruption 발생"

    - signal: "Interface 활용"
      metric: "이 Property를 포함하는 Interface가 있고, cross-type 메타데이터 일관성이 필요한가"
      thresholds:
        promote: "Yes (Interface + 메타데이터 일관성 필요)"
        gray_zone: "Interface 있지만 local property로도 충분"
        keep_local: "No (Interface 불필요 또는 local property 권장)"
      weight: MEDIUM
      rationale: >
        Interface는 local property(권장) 또는 SharedProperty로 구성 가능.
        SharedProperty는 cross-type 메타데이터 일관성이 필요할 때 선택.
        [V3 수정: 이전 "결정적" 가중치에서 MEDIUM으로 하향]

    - signal: "메타데이터 변경 빈도"
      metric: "displayName, description, renderHints 등 메타데이터가 얼마나 자주 바뀌는가"
      thresholds:
        promote: "월 1회 이상"
        gray_zone: "분기 1회"
        keep_local: "거의 없음 (연 1회 미만)"
      weight: MEDIUM
      rationale: "변경 빈도가 높으면 중앙 관리 이점이 커짐 (N개 OT 개별 수정 불필요)"

  # ─── Decision Rule ───
  decision_rule: "(>=3 types + 100% same semantics + centralized management needed) = SharedProperty. 2 types + same semantics = consult BC-SP-1 (metadata change frequency). Interface alone does NOT mandate SharedProperty."

  # ─── Quick Reference ───
  quick_reference:
    - scenario: "3+ ObjectType, 100% 동일 의미"
      decision: "SharedProperty"
      confidence: HIGH

    - scenario: "Interface + cross-type 메타데이터 일관성 필요"
      decision: "SharedProperty (강한 권장)"
      confidence: MEDIUM
      note: "Interface는 local property도 지원 (공식 권장). 메타데이터 일관성 필요 시 SharedProperty 선택."

    - scenario: "2 ObjectType, 100% 동일, 메타데이터 변경 빈번"
      decision: "SharedProperty"
      confidence: MEDIUM

    - scenario: "2 ObjectType, 100% 동일, 메타데이터 안정"
      decision: "Keep Local (or SharedProperty)"
      confidence: LOW
      note: "Gray zone - 향후 확장 가능성 고려"

    - scenario: "2 ObjectType, 90%+ 유사"
      decision: "SharedProperty 가능 (description에 차이 명시)"
      confidence: LOW

    - scenario: "2 ObjectType, <90% 의미 중첩"
      decision: "Keep Local (별도 Property)"
      confidence: HIGH

    - scenario: "1 ObjectType"
      decision: "Keep Local"
      confidence: HIGH

    - scenario: "1 ObjectType, 3개월 내 확장 확정"
      decision: "선제 승격 가능"
      confidence: MEDIUM
```

### Decision Flow (Visual)

```
START: Should this Property be SharedProperty?
│
├─► [CRITICAL] Q1: >=2 ObjectType에서 사용?
│   ├─ NO (1 only) ─────────────────────────────► ❌ Keep Local
│   │   └─ Exception: 3개월 내 확장 확정? ──YES──► ⚠️ 선제 승격 가능
│   └─ YES → Continue
│
├─► [CRITICAL] Q2: 모든 타입에서 100% 동일 의미?
│   ├─ NO (<90% 중첩) ──────────────────────────► ❌ Keep Local (별도 Property)
│   ├─ GRAY (90%+ 유사) ────────────────────────► ⚠️ SharedProperty 가능
│   │   └─ 단, description에 차이 명시 필수
│   └─ YES (100%) → Continue
│
├─► [HIGH] Q3: Interface에 필요한가?
│   ├─ YES ──────────────────────────────────────► ✅ SharedProperty (무조건)
│   └─ NO → Continue
│
├─► [MEDIUM] Q4: 메타데이터 변경 빈도?
│   ├─ 월 1회+ ──────────────────────────────────► ✅ SharedProperty (강한 권장)
│   ├─ 분기 1회 ─────────────────────────────────► ⚠️ 판단 필요 (type 수 고려)
│   └─ 거의 없음 → Continue
│
├─► Q5: >=3 ObjectType?
│   ├─ YES ──────────────────────────────────────► ✅ SharedProperty
│   └─ NO (2 only) ─────────────────────────────► ⚠️ Either OK
│
└─► DEFAULT: 2 types + 동일 의미 + 안정 메타데이터 → 향후 확장 가능성 고려하여 결정
```

---

## 6. validation_rules

```yaml
validation_rules:
  # ─── Promotion Criteria ───
  promotion_criteria:
    - rule: "minimum_usage_threshold"
      recommendation: ">=2 ObjectTypes"
      rationale: "SharedProperty overhead unjustified for single-type usage"
      enforcement: WARNING  # 1개 사용 시 경고, 차단은 아님

    - rule: "semantic_consistency"
      description: "Property must have identical meaning across all using types"
      error: "SharedProperty with inconsistent semantics causes data quality degradation"
      enforcement: MANUAL_REVIEW  # 자동 검증 불가, 설계자 판단

    - rule: "baseType_compatibility"
      description: "All using ObjectTypes must have compatible data sources for the baseType"
      error: "baseType change breaks existing ObjectType mappings"
      enforcement: SYSTEM_BLOCKED  # 시스템이 자동 차단

  # ─── Interface Requirement ───
  interface_requirement:
    - rule: "interfaces_require_sharedproperties"
      description: "Interface schema is defined ONLY by SharedProperties"
      error: "Cannot add local Property to Interface definition"
      enforcement: SYSTEM_BLOCKED

  # ─── Change Propagation ───
  change_propagation:
    - rule: "breaking_changes_blocked"
      description: "Changes that would break any using ObjectType are rejected by the system"
      examples:
        - "Changing baseType from String to Integer"
        - "Adding required constraint when existing data has nulls"
        - "Removing a SharedProperty that is part of an Interface"
      error: "SharedProperty edit would break ObjectType: {objectTypeName}"
      enforcement: SYSTEM_BLOCKED

    - rule: "non_breaking_changes_propagate"
      description: "Non-breaking metadata changes propagate automatically"
      examples:
        - "Changing displayName"
        - "Updating description"
        - "Modifying renderHints"
        - "Changing visibility"
      behavior: "All using ObjectTypes see the change immediately"
      enforcement: AUTOMATIC

  # ─── Detachment ───
  detachment:
    - rule: "detachment_reverts_to_local"
      description: "Detaching SharedProperty converts to local Property on that ObjectType"
      behavior:
        - "Local apiName and metadata preserved"
        - "Property continues to function as local Property"
        - "No data loss occurs"
        - "Other ObjectTypes still reference the SharedProperty"
      enforcement: USER_ACTION

  # ─── Deletion ───
  deletion:
    - rule: "deletion_cascades"
      description: "Deleting SharedProperty reverts ALL using Properties to local"
      warning: "All {count} ObjectTypes will have their properties reverted to local"
      behavior:
        - "Each ObjectType keeps its local copy of the property"
        - "Metadata is preserved as-is at time of deletion"
        - "Interface references are removed"
      enforcement: CONFIRMATION_REQUIRED

  # ─── Naming ───
  naming:
    - rule: "apiName_camelCase"
      pattern: "^[a-z][a-zA-Z0-9]*$"
      enforcement: SYSTEM_BLOCKED

    - rule: "consistent_naming"
      recommendation: "Use domain-specific, unambiguous names"
      good: ["gradeLevel", "difficultyLevel", "displayNotation", "curriculumStandard"]
      bad: ["level", "name", "value", "data", "type"]  # Too generic
      enforcement: WARNING

    - rule: "no_reserved_words"
      forbidden: ["property", "sharedProperty", "interface", "objectType", "rid"]
      enforcement: SYSTEM_BLOCKED
```

---

## 7. canonical_examples

### Example 1: status (Domain-Independent)

```yaml
# ─── Domain-Independent Example ───
# SharedProperty: 엔티티 상태 (여러 도메인에서 공통)
apiName: "entityStatus"
displayName: "Status"
description: "Current lifecycle status of the entity (ACTIVE, INACTIVE, ARCHIVED)"
baseType: "String"
visibility: "PROMINENT"

renderHints:
  searchable: true
  selectable: true    # low cardinality → dropdown filter

constraints:
  enum: ["ACTIVE", "INACTIVE", "ARCHIVED"]

usedByObjectTypes:
  - "Employee"
  - "Project"
  - "Contract"
  - "Asset"

usedByInterfaces:
  - "ManagedEntity"

# WHY SharedProperty:
# - 4 ObjectTypes (>= 3 → CRITICAL threshold met)
# - 100% identical semantics (all use ACTIVE/INACTIVE/ARCHIVED lifecycle)
# - Part of ManagedEntity Interface
# - Metadata changes (adding a new status value) should propagate to all types
```

### Example 2: createdAt (Domain-Independent)

```yaml
# ─── Domain-Independent Example ───
# SharedProperty: 생성 타임스탬프 (audit trail)
apiName: "createdAt"
displayName: "Created At"
description: "Timestamp when this entity was first created"
baseType: "Timestamp"
visibility: "NORMAL"

renderHints:
  searchable: true
  sortable: true

valueFormatting:
  dateFormat: "yyyy-MM-dd HH:mm:ss"
  timezone: "UTC"

usedByObjectTypes:
  - "Employee"
  - "Project"
  - "Document"
  - "Task"
  - "Incident"

usedByInterfaces:
  - "Auditable"

# WHY SharedProperty:
# - 5+ ObjectTypes
# - 100% identical semantics (creation timestamp everywhere)
# - Formatting changes (e.g., timezone display) should propagate centrally
```

### Example 3: gradeLevel [K-12 Education Domain]

```yaml
# ─── K-12 Education Domain Example ───
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

# WHY SharedProperty:
# - 6 ObjectTypes (far exceeds CRITICAL threshold)
# - 100% identical semantics ("target grade level" everywhere)
# - Part of EducationalContent Interface (SC-SP-1 satisfied)
# - Constraint changes (e.g., extending to 13 for special ed) propagate centrally
```

### Example 4: displayNotation [K-12 Education Domain]

```yaml
# ─── K-12 Education Domain Example ───
apiName: "displayNotation"
displayName: "Display Notation"
description: "Human-readable mathematical or scientific notation for display purposes"
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

# WHY SharedProperty:
# - 4 ObjectTypes across math/science
# - Interface requirement (AlgebraicExpression)
# - Consistent formatting rules for notation display
```

### Example 5: difficultyLevel [K-12 Education Domain]

```yaml
# ─── K-12 Education Domain Example ───
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

# WHY SharedProperty:
# - 4 ObjectTypes
# - EducationalContent Interface requirement
# - Enum values centrally managed (e.g., changing to 1-10 scale)
```

### Example 6: curriculumStandard [K-12 Education Domain]

```yaml
# ─── K-12 Education Domain Example ───
apiName: "curriculumStandard"
displayName: "Curriculum Standard"
description: "Reference to national curriculum standard code (e.g., KR-Math-8-A-1)"
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

# WHY SharedProperty:
# - 3 ObjectTypes (meets CRITICAL threshold)
# - Regex pattern centrally managed (format changes propagate)
# - Part of EducationalContent Interface
```

---

## 8. anti_patterns

### Anti-Pattern 1: SharedProperty for Single ObjectType

```yaml
severity: HIGH
category: "Unnecessary Promotion"

# ❌ WRONG: Creating SharedProperty used by only one type
apiName: "polynomialDegree"
displayName: "Polynomial Degree"
baseType: "Integer"
usedByObjectTypes:
  - "Polynomial"  # Only one!

# WHY IT'S WRONG:
# - NC-SP-1 위반: 2개 이상의 ObjectType에서 사용되지 않음
# - No reuse benefit
# - Added governance overhead (변경 시 SharedProperty 권한 필요)
# - Unnecessary complexity in ontology management

# ✅ CORRECT: Keep as local Property on Polynomial
# Only promote to SharedProperty when 2+ types need it

# RESOLUTION:
# 1. Delete the SharedProperty
# 2. Ensure local Property exists on Polynomial
# 3. OR wait until genuine second use case emerges
```

### Anti-Pattern 2: Generic Naming Without Context

```yaml
severity: MEDIUM
category: "Naming Violation"

# ❌ WRONG: Overly generic SharedProperty name
apiName: "level"
displayName: "Level"
description: "A level value"  # Vague!

# WHY IT'S WRONG:
# - "level" could mean grade level, difficulty, game level, access level...
# - NC-SP-2 위반 위험: 타입마다 다른 의미로 해석 가능
# - Causes semantic confusion when reused across ObjectTypes
# - Different types may interpret differently → silent semantic corruption

# ✅ CORRECT: Specific, domain-qualified names
apiName: "gradeLevel"
displayName: "Grade Level"
description: "Target grade level (1-12) for educational content"

# RESOLUTION:
# 1. Rename to domain-specific name (gradeLevel, difficultyLevel, accessLevel)
# 2. Update all referencing ObjectTypes
# 3. Add clear description with constraints
```

### Anti-Pattern 3: Forcing Inconsistent Semantics

```yaml
severity: CRITICAL
category: "Semantic Violation"

# ❌ WRONG: Same SharedProperty for different meanings
apiName: "startDate"
# Used on:
#   - Employee: "Date employee began working"
#   - Project: "Date project was initiated"
#   - Subscription: "Date subscription became active"
# These have subtly different semantics!

# WHY IT'S WRONG:
# - NC-SP-2 위반: 의미 동일성이 보장되지 않음
# - Queries may conflate different concepts
# - Metadata (like "required") may not apply uniformly
# - Interface contracts become confusing
# - Adding a constraint for one type may break another

# ✅ CORRECT: Either accept the abstraction OR separate
# Option A: If truly equivalent lifecycle concept → keep SharedProperty
#   apiName: "lifecycleStartDate"
#   description: "Date this entity's lifecycle began"
# Option B: If semantics differ → separate local Properties
#   employeeStartDate, projectStartDate, subscriptionActivationDate

# RESOLUTION:
# 1. Assess semantic overlap (>=90% test from BC-SP-2)
# 2. If <90% → split into separate local Properties
# 3. If >=90% → keep but clarify description
```

### Anti-Pattern 4: Changing BaseType on Active SharedProperty

```yaml
severity: CRITICAL
category: "Breaking Change"

# ❌ WRONG: Attempting baseType change on in-use SharedProperty
# Original:
apiName: "gradeLevel"
baseType: "Integer"

# Attempted change:
baseType: "String"  # To support "K" for kindergarten

# WHY IT'S WRONG:
# - Breaks ALL ObjectTypes using this SharedProperty
# - Data type mismatch with existing data in all using ObjectTypes
# - System BLOCKS this change (validation_rules: breaking_changes_blocked)
# - Could cause data pipeline failures across the ontology

# ✅ CORRECT: Plan baseType carefully upfront
# Or create new SharedProperty with the desired type:
apiName: "gradeLevelExtended"
baseType: "String"
description: "Grade level supporting K-12 (K, 1, 2, ..., 12)"

# RESOLUTION:
# 1. Create new SharedProperty with correct baseType
# 2. Migrate each ObjectType to use the new SharedProperty
# 3. Deprecate the old SharedProperty
# 4. Delete old SharedProperty after all migrations complete
```

### Anti-Pattern 5: Premature Promotion Without Roadmap

```yaml
severity: LOW
category: "Over-Engineering"

# ❌ WRONG: Promoting to SharedProperty "just in case"
apiName: "taxIdentificationNumber"
baseType: "String"
usedByObjectTypes:
  - "Organization"  # Only current user
# Justification: "Maybe Employee will need it someday"

# WHY IT'S WRONG:
# - BC-SP-3 기준 미충족: 확정된 3개월 내 로드맵 없음
# - YAGNI (You Aren't Gonna Need It)
# - Premature SharedProperty adds governance overhead
# - Easy to promote later when genuine need arises

# ✅ CORRECT: Keep as local Property until confirmed need
# Promote when: confirmed roadmap shows 2+ types within 3 months

# RESOLUTION:
# 1. Revert to local Property
# 2. Document future promotion candidate in design notes
# 3. Promote when second type is confirmed (not speculated)
```

### Anti-Pattern 6: SharedProperty as Foreign Key Substitute

```yaml
severity: HIGH
category: "Structural Misuse"

# ❌ WRONG: Using SharedProperty to link ObjectTypes
apiName: "parentOrganizationId"
baseType: "String"
usedByObjectTypes:
  - "Department"
  - "Team"
  - "Project"
# Intent: "All these belong to an Organization"

# WHY IT'S WRONG:
# - SharedProperty는 관계(Link) 대체물이 아님
# - ObjectType 간 관계는 LinkType으로 모델링해야 함
# - SharedProperty로 FK를 표현하면:
#   - 참조 무결성 없음
#   - Graph traversal 불가
#   - Ontology 시각화에서 관계 표시 안 됨

# ✅ CORRECT: Use LinkType
# BELONGS_TO: Department → Organization (manyToOne)
# BELONGS_TO: Team → Organization (manyToOne)
# OWNED_BY: Project → Organization (manyToOne)

# RESOLUTION:
# 1. Create appropriate LinkTypes
# 2. Remove FK-style SharedProperty
# 3. Migrate data references to Link objects
```

---

## 9. integration_points

```yaml
integration_points:
  # ─── Property ───
  property:
    relationship: "Property REFERENCES SharedProperty"
    reference_doc: "→ See Property.md for full Property definition"
    mechanism:
      - "Property.sharedProperty field contains SharedProperty apiName"
      - "Property inherits metadata from SharedProperty"
      - "Property retains local apiName (backward compatibility)"
      - "Property data values are independent of SharedProperty"
    behavior:
      - "Render hint overrides apply when associating"
      - "Breaking changes to SharedProperty blocked if Properties would break"
      - "Detaching reverts Property to local (preserves apiName + metadata snapshot)"
    lifecycle:
      association: "ObjectType의 Property를 SharedProperty에 연결"
      inheritance: "메타데이터 (displayName, description, renderHints, constraints) 상속"
      override: "일부 renderHints는 ObjectType 수준에서 override 가능"
      detachment: "연결 해제 시 local Property로 복귀 (메타데이터 복사본 보존)"

  # ─── Interface ───
  interface:
    relationship: "Interface CAN USE SharedProperty (or local properties)"
    reference_doc: "→ See Interface documentation (Phase 2 - not yet documented)"
    constraint: >
      Interface는 local property(권장) 또는 SharedProperty로 구성 가능.
      [V3 수정] 공식 문서: "Interface properties can be defined locally on
      the interface (recommended) or using shared properties."
    workflow:
      1: "Create SharedProperties first (선행 조건)"
      2: "Create Interface referencing SharedProperties"
      3: "ObjectTypes implement Interface by having required SharedProperties"
    dependency_note: |
      Interface는 SharedProperty에 의존한다. 따라서:
      - Interface 생성 전에 필요한 SharedProperty가 모두 존재해야 한다
      - SharedProperty 삭제 시 해당 Interface 정의가 깨진다
      - SharedProperty의 baseType 변경은 Interface contract 위반

  # ─── ObjectType ───
  objectType:
    relationship: "ObjectType USES SharedProperty"
    reference_doc: "→ See ObjectType.md for full ObjectType definition"
    mechanism:
      - "ObjectType Property references SharedProperty via sharedProperty field"
      - "ObjectType can map local property to SharedProperty during Interface implementation"
      - "ObjectType retains independent data values"
    governance:
      - "Changes to SharedProperty propagate to all using ObjectTypes"
      - "Detaching reverts to local Property"
      - "ObjectType must have Ontology Editor permission to associate SharedProperty"
    constraints:
      - "ObjectType cannot have two Properties referencing the same SharedProperty"
      - "ObjectType Property baseType must match SharedProperty baseType"

  # ─── Permissions ───
  permissions:
    relationship: "SharedProperty HAS Permissions"
    requirements:
      - "Ontology Editor permission on SharedProperty itself to create/modify/delete"
      - "Ontology Editor permission on ObjectType to associate SharedProperty"
      - "Both permissions needed: SP modification + OT association"
    visibility:
      - "Usage tab shows all ObjectTypes using SharedProperty"
      - "🌐 icon appears on Properties that reference a SharedProperty"

  # ─── Cross-Component Dependencies ───
  dependency_chain:
    creation_order:
      1: "SharedProperty (must exist before Interface or OT association)"
      2: "Interface (references SharedProperties)"
      3: "ObjectType (implements Interface by using SharedProperties)"
    deletion_order:
      1: "Remove ObjectType associations (or detach)"
      2: "Remove Interface references"
      3: "Delete SharedProperty (cascades to local if any remaining)"
```

### Integration Diagram

```
                    ┌─────────────────────┐
                    │     Interface        │
                    │  (requires SP only)  │
                    └──────────┬──────────┘
                               │ REQUIRES
                               ▼
                    ┌─────────────────────┐
                    │   SharedProperty    │◄─── 🌐 Globe Icon
                    │  (metadata source)  │
                    └──┬──────┬──────┬───┘
                       │      │      │  REFERENCES
                       ▼      ▼      ▼
                   ┌──────┐┌──────┐┌──────┐
                   │OT-A  ││OT-B  ││OT-C  │
                   │.prop ││.prop ││.prop │  ← 각자 데이터 보유
                   └──────┘└──────┘└──────┘
```

---

## 10. migration_constraints

```yaml
migration_constraints:
  component: "SharedProperty"
  description: "SharedProperty 변경/삭제 시 발생하는 마이그레이션 제약사항"

  # ─── baseType Change Blocks ───
  baseType_change:
    rule: "baseType 변경은 사용 중인 ObjectType이 있으면 시스템이 차단"
    reason: "baseType은 데이터 저장 형식을 결정 → 변경 시 모든 사용 OT의 데이터 호환성 파괴"
    impact:
      - "All using ObjectTypes would have data type mismatch"
      - "Data pipeline indexing failures (OSv2)"
      - "Query filters and sorts would break"
    workaround:
      steps:
        - "새 SharedProperty 생성 (원하는 baseType으로)"
        - "각 ObjectType에서 순차적으로 새 SharedProperty로 전환"
        - "데이터 마이그레이션 (old type → new type) 수행"
        - "원래 SharedProperty에서 모든 OT 분리 후 삭제"
      estimated_effort: "ObjectType 수에 비례 (N개 OT × 마이그레이션 시간)"

  # ─── Deletion Cascade ───
  deletion_cascade:
    rule: "SharedProperty 삭제 시 모든 사용 Property가 local로 복귀"
    behavior:
      - "각 ObjectType의 Property는 삭제 시점의 메타데이터 스냅샷을 보존"
      - "apiName은 그대로 유지 (local apiName이 이미 있으므로)"
      - "데이터는 영향 없음 (데이터는 원래 각 OT에 독립적)"
      - "Interface 참조가 있으면 Interface 정의가 깨짐 → 주의 필요"
    risk_level: MEDIUM
    mitigation: "삭제 전 usedByObjectTypes와 usedByInterfaces 확인 필수"

  # ─── Detachment (개별 분리) ───
  detachment:
    rule: "특정 ObjectType에서 SharedProperty 연결을 해제"
    behavior:
      - "해당 OT의 Property가 local Property로 복귀"
      - "Local apiName과 메타데이터가 보존됨"
      - "다른 ObjectType은 영향 없음"
      - "Interface 구현을 위한 SharedProperty였다면 Interface compliance 깨짐"
    risk_level: LOW
    use_case: "특정 OT만 SharedProperty 사양에서 벗어나야 할 때"

  # ─── Required Constraint Addition ───
  required_constraint:
    rule: "기존 데이터에 null이 있으면 required constraint 추가 불가"
    reason: "required=true는 모든 사용 OT의 데이터에 null이 없어야 함"
    check_process:
      - "모든 usedByObjectTypes의 해당 Property 데이터 확인"
      - "null 값이 있는 ObjectType 식별"
      - "null 데이터 정리 후 constraint 추가"
    workaround: "데이터 backfill → null 제거 → required constraint 적용"

  # ─── apiName Immutability ───
  apiName_change:
    rule: "SharedProperty apiName은 생성 후 변경 불가"
    reason: "apiName은 API, 코드, 쿼리에서 참조되므로 변경 시 하위 호환성 파괴"
    workaround:
      steps:
        - "새 apiName으로 SharedProperty 생성"
        - "각 ObjectType 전환"
        - "기존 SharedProperty 삭제"
        - "API 클라이언트 코드 업데이트"

  # ─── Promotion (Local → Shared) ───
  promotion:
    rule: "기존 local Property를 SharedProperty로 승격"
    process:
      - "SharedProperty 생성 (동일 apiName, baseType)"
      - "각 ObjectType의 local Property를 SharedProperty에 연결"
      - "메타데이터가 SharedProperty 사양으로 통합됨"
    considerations:
      - "baseType이 모든 OT에서 동일해야 함"
      - "apiName 충돌 확인 필요"
      - "기존 constraint 호환성 검증"
```

---

## 11. runtime_caveats

```yaml
runtime_caveats:
  component: "SharedProperty"
  description: "SharedProperty 사용 시 런타임/운영 환경에서 알아야 할 주의사항"

  # ─── Performance ───
  performance:
    metadata_propagation:
      description: "SharedProperty 메타데이터 변경 시 모든 사용 ObjectType에 전파"
      impact: |
        - N개 ObjectType이 사용하는 SharedProperty의 메타데이터 변경 시
          N개의 ObjectType 메타데이터가 업데이트됨
        - 대규모 Ontology에서 많은 OT가 하나의 SP를 참조하면
          변경 전파에 시간이 소요될 수 있음
      mitigation:
        - "메타데이터 변경은 off-peak 시간에 수행"
        - "변경 전 usedByObjectTypes 수 확인"
        - "대규모 변경은 배치로 처리"

    query_performance:
      description: "SharedProperty 자체는 쿼리 성능에 직접 영향 없음"
      note: |
        SharedProperty는 메타데이터 레이어이므로, 쿼리 시에는 각 ObjectType의
        local Property를 통해 데이터에 접근한다. 따라서 SharedProperty 여부가
        쿼리 성능에 직접적인 영향을 주지는 않는다.
        다만, renderHints.searchable/sortable 설정이 인덱싱에 영향을 미친다.

  # ─── Governance ───
  governance:
    permission_model:
      description: "SharedProperty 수정과 ObjectType 연결 모두 Ontology Editor 권한 필요"
      details:
        - "SharedProperty 생성/수정/삭제: Ontology Editor on SharedProperty"
        - "ObjectType에 SharedProperty 연결: Ontology Editor on ObjectType"
        - "양쪽 권한이 모두 필요하므로 권한 분리된 팀에서 협업 필요 가능"
      best_practice: |
        SharedProperty 관리는 Ontology 설계 담당자(architect)에게 집중하고,
        개별 ObjectType 소유자는 연결/분리만 수행하도록 역할 분리.

    change_governance:
      description: "SharedProperty 변경은 영향도가 크므로 변경 관리 프로세스 권장"
      recommendations:
        - "변경 전 usedByObjectTypes 리스트 확인"
        - "영향받는 팀에 사전 공지"
        - "Staging 환경에서 변경 검증 후 Production 적용"
        - "변경 이력 문서화"

  # ─── Breaking Change Detection ───
  breaking_change_detection:
    description: "시스템이 호환되지 않는 SharedProperty 변경을 자동 차단"
    detected_changes:
      - change: "baseType 변경"
        blocked: true
        reason: "데이터 타입 불일치 → 모든 사용 OT 파손"
      - change: "required constraint 추가 (null 데이터 존재 시)"
        blocked: true
        reason: "기존 데이터 무결성 위반"
      - change: "SharedProperty 삭제 (Interface에서 참조 중)"
        blocked: true
        reason: "Interface contract 파손"
      - change: "displayName 변경"
        blocked: false
        reason: "non-breaking metadata change → 자동 전파"
      - change: "description 변경"
        blocked: false
        reason: "non-breaking metadata change → 자동 전파"
      - change: "renderHints 변경"
        blocked: false
        reason: "non-breaking metadata change → 자동 전파"
      - change: "visibility 변경"
        blocked: false
        reason: "non-breaking metadata change → 자동 전파"

  # ─── OSv2 Considerations ───
  osv2:
    description: "Object Storage v2에서의 SharedProperty 동작"
    notes:
      - "SharedProperty는 메타데이터 레이어이므로 OSv1/OSv2 차이에 직접 영향 없음"
      - "다만, SharedProperty와 연결된 Property의 baseType이 OSv2에서 지원되는지 확인 필요"
      - "OSv2에서 primary key 중복 시 indexing failure 발생 (OSv1의 silent corruption과 다름)"
      - "SharedProperty가 primary key로 사용되는 경우는 없음 (PK는 항상 local)"

  # ─── Monitoring Recommendations ───
  monitoring:
    recommended_checks:
      - check: "Orphaned SharedProperty 탐지"
        description: "usedByObjectTypes가 비어있는 SharedProperty"
        frequency: "Monthly"
        action: "삭제 또는 사용 계획 확인"

      - check: "Single-use SharedProperty 탐지"
        description: "usedByObjectTypes가 1개뿐인 SharedProperty"
        frequency: "Quarterly"
        action: "local로 강등하거나 추가 사용 계획 확인"

      - check: "메타데이터 일관성 검증"
        description: "SharedProperty의 description이 모든 사용 맥락에서 정확한지"
        frequency: "Semi-annually"
        action: "description 업데이트 또는 SharedProperty 분리"
```

---

## Appendix A: SharedProperty Registry Template

| apiName | displayName | baseType | usedBy Count | Interface Required | Last Reviewed |
|---------|-------------|----------|--------------|-------------------|---------------|
| gradeLevel | Grade Level | Integer | 6+ | EducationalContent | 2026-02-06 |
| difficultyLevel | Difficulty Level | Integer | 4+ | EducationalContent | 2026-02-06 |
| displayNotation | Display Notation | String | 4+ | MathematicalConceptInterface | 2026-02-06 |
| curriculumStandard | Curriculum Standard | String | 4+ | EducationalContent | 2026-02-06 |
| variableSymbol | Variable Symbol | String | 3+ | AlgebraicExpression | 2026-02-06 |
| degree | Degree | Integer | 2+ | AlgebraicExpression | 2026-02-06 |

## Appendix B: SharedProperty vs Local Property Comparison

| Aspect | Local Property | SharedProperty |
|--------|---------------|----------------|
| **Scope** | 1 ObjectType | 2+ ObjectTypes |
| **Metadata 관리** | ObjectType별 독립 | 중앙 관리, 전파 |
| **Data** | ObjectType 내 독립 | ObjectType 내 독립 (동일) |
| **Interface 사용** | 불가 | 필수 |
| **변경 영향** | 해당 ObjectType만 | 모든 사용 ObjectType |
| **권한** | ObjectType Editor | SharedProperty Editor + ObjectType Editor |
| **Governance 비용** | Low | Medium~High |
| **Visual** | No icon | 🌐 Globe icon |
| **apiName 변경** | 가능 (주의 필요) | 불가 (immutable) |
| **baseType 변경** | 가능 (주의 필요) | 차단 (사용 중일 때) |

## Appendix C: Checklist for SharedProperty Creation

```yaml
pre_creation_checklist:
  - id: CHK-1
    question: "2개 이상의 ObjectType에서 사용하는가?"
    required: true
    if_no: "Local Property로 유지"

  - id: CHK-2
    question: "모든 사용처에서 100% 동일한 의미인가?"
    required: true
    if_no: "의미가 다르면 별도 local Property"

  - id: CHK-3
    question: "baseType을 확정했는가? (나중에 변경 불가)"
    required: true
    if_no: "baseType 결정 후 진행"

  - id: CHK-4
    question: "apiName을 확정했는가? (나중에 변경 불가)"
    required: true
    if_no: "apiName 결정 후 진행"

  - id: CHK-5
    question: "domain-specific하고 명확한 이름인가?"
    required: true
    if_no: "generic name (level, name, value) 피할 것"

  - id: CHK-6
    question: "Interface에 사용될 예정인가?"
    required: false
    if_yes: "Interface 설계와 함께 계획"

  - id: CHK-7
    question: "constraints (range, regex, enum)을 설계했는가?"
    required: false
    if_no: "나중에 추가 가능하지만, required는 null 데이터 시 차단됨"

  - id: CHK-8
    question: "Ontology Editor 권한이 확보되었는가?"
    required: true
    if_no: "권한 요청 후 진행"
```

---

> **Document Version:** 1.0.0
> **Created:** 2026-02-06
> **Source Material:** session1.md (lines 1170-1795), WF-1 Gap Report, WF-2 Design Spec
> **Gap Coverage:** G2 (formal_definition), G4 (integration_points), G10 (quantitative_decision_matrix)
