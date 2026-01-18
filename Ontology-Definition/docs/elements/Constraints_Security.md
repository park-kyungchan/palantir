# Constraints and Security

이 문서는 Ontology-Definition 프로젝트의 속성 제약조건(Property Constraints)과 보안 모델(Security Model)을 설명합니다.

**Source Files:**
- `/ontology_definition/constraints/property_constraints.py`
- `/ontology_definition/constraints/mandatory_control.py`
- `/ontology_definition/core/enums.py`

---

# Part 1: PropertyConstraints

## Definition

`PropertyConstraints`는 속성 값에 대한 유효성 검사 규칙을 정의하는 Pydantic 모델입니다. 스키마 수준에서 데이터 품질 규칙을 강제하여 잘못된 데이터가 저장되는 것을 방지합니다.

```python
from ontology_definition.constraints.property_constraints import (
    PropertyConstraints,
    StringConstraints,
    NumericConstraints,
    ArrayConstraints,
    DecimalConstraints,
    VectorConstraints,
)
```

## Core Constraints

### required

속성 값의 필수 여부를 지정합니다.

| Value | Description |
|-------|-------------|
| `true` | 값 필수 (null/empty 불가) |
| `false` | nullable (기본값) |

```python
# 필수 속성 정의
constraints = PropertyConstraints(required=True)
```

**사용 시점:**
- Primary Key 속성
- 비즈니스 로직에 필수적인 속성
- Mandatory Control Property로 지정할 속성

### immutable

생성 후 변경 가능 여부를 지정합니다.

| Value | Description |
|-------|-------------|
| `true` | 생성 후 변경 불가 |
| `false` | 변경 가능 (기본값) |

```python
# 변경 불가 속성 정의
constraints = PropertyConstraints(
    required=True,
    immutable=True
)
```

**사용 시점:**
- ID 필드
- 감사(audit) 추적 필드 (created_at, created_by)
- 외부 시스템과 동기화되는 필드

### unique

고유값 필수 여부를 지정합니다.

| Value | Description |
|-------|-------------|
| `true` | 모든 인스턴스에서 고유값 필수 |
| `false` | 중복 허용 (기본값) |

```python
# 고유값 필수 속성
constraints = PropertyConstraints(
    required=True,
    unique=True
)
```

**사용 시점:**
- Primary Key 속성
- 이메일 주소, 사용자명
- 외부 시스템 연동 ID

### default_value

기본값을 지정합니다.

```python
# 기본값 설정
constraints = PropertyConstraints(
    default_value="PENDING"
)
```

**주의사항:**
- Mandatory Control Property에는 default_value 설정 불가
- required=True와 함께 사용 시, 값이 없을 때 기본값 적용

---

## String Constraints

### StringConstraints Model

STRING 타입 속성에 대한 세부 제약조건입니다.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `min_length` | `int` | 최소 문자열 길이 (inclusive) | None |
| `max_length` | `int` | 최대 문자열 길이 (inclusive) | None |
| `pattern` | `str` | 정규표현식 패턴 | None |
| `rid_format` | `bool` | Foundry RID 형식 검증 | False |
| `uuid_format` | `bool` | UUID 형식 검증 | False |
| `email_format` | `bool` | 이메일 형식 검증 | False |
| `url_format` | `bool` | URL 형식 검증 | False |

```python
# 문자열 제약조건 예시
string_constraints = StringConstraints(
    min_length=1,
    max_length=100,
    pattern=r"^[A-Z][a-zA-Z0-9_]*$"
)

constraints = PropertyConstraints(
    required=True,
    string=string_constraints
)
```

### Format Validators

```python
# UUID 형식 검증
uuid_constraints = StringConstraints(uuid_format=True)

# RID 형식 검증 (Foundry Resource ID)
rid_constraints = StringConstraints(rid_format=True)

# 이메일 형식 검증
email_constraints = StringConstraints(email_format=True)

# URL 형식 검증
url_constraints = StringConstraints(url_format=True)
```

### Validation Rules

- `min_length <= max_length` 조건 자동 검증
- `min_length >= 0` 조건 강제
- `max_length >= 0` 조건 강제

---

## Numeric Constraints

### NumericConstraints Model

숫자 타입(INTEGER, LONG, FLOAT, DOUBLE, DECIMAL)에 대한 제약조건입니다.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `min_value` | `int\|float` | 최소값 (inclusive by default) | None |
| `max_value` | `int\|float` | 최대값 (inclusive by default) | None |
| `exclusive_min` | `bool` | True면 min_value 배타적 (>) | False |
| `exclusive_max` | `bool` | True면 max_value 배타적 (<) | False |
| `multiple_of` | `int\|float` | 배수 제약 (값이 이 숫자의 배수여야 함) | None |

```python
# 숫자 제약조건 예시
numeric_constraints = NumericConstraints(
    min_value=0,
    max_value=100,
    exclusive_min=False,  # >= 0
    exclusive_max=False   # <= 100
)

constraints = PropertyConstraints(
    required=True,
    numeric=numeric_constraints
)
```

### Range Examples

```python
# 0 < value < 100 (exclusive)
exclusive_range = NumericConstraints(
    min_value=0,
    max_value=100,
    exclusive_min=True,
    exclusive_max=True
)

# 배수 제약: 10의 배수만 허용
multiple_constraint = NumericConstraints(
    multiple_of=10
)

# 양수만 허용 (0 제외)
positive_only = NumericConstraints(
    min_value=0,
    exclusive_min=True
)
```

### Validation Rules

- `min_value <= max_value` 조건 자동 검증

---

## Array Constraints

### ArrayConstraints Model

ARRAY 타입에 대한 제약조건입니다.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `min_items` | `int` | 배열 최소 아이템 수 | None |
| `max_items` | `int` | 배열 최대 아이템 수 | None |
| `unique_items` | `bool` | 배열 내 아이템 고유성 강제 | False |

```python
# 배열 제약조건 예시
array_constraints = ArrayConstraints(
    min_items=1,
    max_items=10,
    unique_items=True
)

constraints = PropertyConstraints(
    required=True,
    array=array_constraints
)
```

### Use Cases

```python
# 최소 1개 태그 필수
tag_constraints = ArrayConstraints(
    min_items=1,
    unique_items=True  # 중복 태그 방지
)

# 최대 5개 첨부파일
attachment_constraints = ArrayConstraints(
    max_items=5
)
```

### Validation Rules

- `min_items <= max_items` 조건 자동 검증
- `min_items >= 0` 조건 강제
- `max_items >= 0` 조건 강제

---

## Decimal Constraints

### DecimalConstraints Model

DECIMAL 타입(정밀 숫자값)에 대한 제약조건입니다.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `precision` | `int` | 총 자릿수 (1-38) | 18 |
| `scale` | `int` | 소수점 이하 자릿수 (0-precision) | 2 |

```python
# 통화값: 최대 16자리, 소수점 이하 2자리
currency_constraints = DecimalConstraints(
    precision=18,
    scale=2
)

constraints = PropertyConstraints(
    required=True,
    decimal=currency_constraints
)
```

### Examples

```python
# 예: 1234567890123456.99 (precision=18, scale=2)
money = DecimalConstraints(precision=18, scale=2)

# 예: 12345678.12345 (precision=13, scale=5)
scientific = DecimalConstraints(precision=13, scale=5)

# 정수만 (scale=0)
integer_decimal = DecimalConstraints(precision=10, scale=0)
```

### Validation Rules

- `1 <= precision <= 38`
- `0 <= scale <= precision`

---

## Vector Constraints

### VectorConstraints Model

VECTOR 타입(AI/ML 임베딩)에 대한 제약조건입니다.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `dimension` | `int` | 벡터 차원 수 (>= 1) | Yes |

```python
# OpenAI embedding dimension (1536)
embedding_constraints = VectorConstraints(
    dimension=1536
)

constraints = PropertyConstraints(
    required=True,
    vector=embedding_constraints
)
```

### Common Dimensions

| Model | Dimension |
|-------|-----------|
| OpenAI text-embedding-3-small | 1536 |
| OpenAI text-embedding-3-large | 3072 |
| Cohere embed-english-v3.0 | 1024 |
| Sentence Transformers (default) | 768 |

---

## Enum Constraints

### enum_values

허용된 값 목록을 지정합니다.

```python
# Enum 제약조건
constraints = PropertyConstraints(
    required=True,
    enum=["PENDING", "APPROVED", "REJECTED"]
)

# 숫자 enum
priority_constraints = PropertyConstraints(
    enum=[1, 2, 3, 4, 5]
)

# 불리언 enum (특수 케이스)
boolean_constraints = PropertyConstraints(
    enum=[True, False]
)
```

### Validation Rules

- enum 리스트가 제공되면 비어있을 수 없음
- 지원 타입: `str`, `int`, `float`, `bool`

---

## Validation Methods

### validate_value()

**Note:** 현재 구현에서는 Pydantic의 자동 검증을 통해 값 검증이 이루어집니다.

### to_foundry_dict()

Foundry 호환 딕셔너리 형식으로 내보내기:

```python
constraints = PropertyConstraints(
    required=True,
    unique=True,
    string=StringConstraints(min_length=1, max_length=100)
)

foundry_dict = constraints.to_foundry_dict()
# Output:
# {
#     "required": True,
#     "unique": True,
#     "minLength": 1,
#     "maxLength": 100
# }
```

### from_foundry_dict()

Foundry JSON 형식에서 생성:

```python
foundry_data = {
    "required": True,
    "unique": True,
    "minLength": 1,
    "maxLength": 100
}

constraints = PropertyConstraints.from_foundry_dict(foundry_data)
```

### Field Mapping (Python <-> Foundry)

| Python Field | Foundry Field |
|--------------|---------------|
| `min_length` | `minLength` |
| `max_length` | `maxLength` |
| `min_value` | `minValue` |
| `max_value` | `maxValue` |
| `min_items` | `arrayMinItems` |
| `max_items` | `arrayMaxItems` |
| `unique_items` | `arrayUnique` |
| `rid_format` | `ridFormat` |
| `uuid_format` | `uuidFormat` |
| `default_value` | `defaultValue` |
| `custom_validator` | `customValidator` |

---

# Part 2: MandatoryControlConfig

## Definition

`MandatoryControlConfig`는 행 수준 보안(Row-Level Security)을 위한 필수 제어 속성 설정입니다.

Palantir Foundry의 Mandatory Control Properties는 보안 마킹, 조직 멤버십, 또는 분류 수준에 기반한 행 수준 접근 제어를 강제합니다.

```python
from ontology_definition.constraints.mandatory_control import (
    MandatoryControlConfig,
    MandatoryControlPropertyRequirements,
    SecurityMarkingReference,
)
from ontology_definition.core.enums import ControlType, ClassificationLevel
```

**Priority:** P1-CRITICAL (보안 기능)

## ControlType Enum

| Type | Description | Use Case |
|------|-------------|----------|
| `MARKINGS` | Security markings 기반 접근 제어 | 가장 일반적, 대부분의 배포 환경 |
| `ORGANIZATIONS` | Organization membership 기반 접근 제어 | 조직 계층 구조 기반 접근 |
| `CLASSIFICATIONS` | CBAC (Classification-Based Access Control) | 정부/군사 배포 환경 |

```python
from ontology_definition.core.enums import ControlType

# 가장 일반적인 사용
control = ControlType.MARKINGS

# 조직 기반
control = ControlType.ORGANIZATIONS

# 정부 환경 (CBAC)
control = ControlType.CLASSIFICATIONS
```

**Palantir Alignment:** ControlType 값은 Palantir 공식 문서와 정확히 일치합니다.

## ClassificationLevel Enum

CBAC에서 사용되는 분류 수준입니다.

| Level | Description |
|-------|-------------|
| `UNCLASSIFIED` | 비분류 (공개) |
| `CONFIDENTIAL` | 기밀 |
| `SECRET` | 비밀 |
| `TOP_SECRET` | 극비 |

```python
from ontology_definition.core.enums import ClassificationLevel

max_level = ClassificationLevel.SECRET
```

## MandatoryControlConfig Fields

### property_api_name (required)

필수 제어로 지정된 속성의 apiName입니다.

```python
config = MandatoryControlConfig(
    property_api_name="securityMarking",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="security_markings"
)
```

**제약조건:**
- 1-255자
- 패턴: `^[a-zA-Z][a-zA-Z0-9_]*$`

### control_type (required)

필수 제어 메커니즘 유형입니다.

### marking_column_mapping

MARKINGS 타입에서 마킹 ID를 포함하는 Restricted View 컬럼명입니다.

```python
# MARKINGS 타입 필수
config = MandatoryControlConfig(
    property_api_name="securityMarking",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="security_markings"  # 필수
)
```

**데이터 타입:** STRING ARRAY of UUIDs

### allowed_markings

MARKINGS 타입에서 허용된 마킹 UUID 목록입니다.

```python
config = MandatoryControlConfig(
    property_api_name="securityMarking",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="security_markings",
    allowed_markings=[
        "550e8400-e29b-41d4-a716-446655440000",
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    ]
)
```

### allowed_organizations

ORGANIZATIONS 타입에서 허용된 조직 UUID 목록입니다.

```python
config = MandatoryControlConfig(
    property_api_name="organizationId",
    control_type=ControlType.ORGANIZATIONS,
    allowed_organizations=[
        "org-uuid-1",
        "org-uuid-2"
    ]
)
```

### max_classification_level

CLASSIFICATIONS 타입에서 최대 분류 수준입니다.

```python
config = MandatoryControlConfig(
    property_api_name="classificationLevel",
    control_type=ControlType.CLASSIFICATIONS,
    max_classification_level=ClassificationLevel.SECRET
)
```

## Validation Rules

### Control Type Requirements

| Control Type | Required Fields |
|--------------|-----------------|
| MARKINGS | `marking_column_mapping` |
| ORGANIZATIONS | `allowed_organizations` |
| CLASSIFICATIONS | `max_classification_level` |

### Property Requirements for Mandatory Control

`MandatoryControlPropertyRequirements` 클래스는 속성이 Mandatory Control로 지정될 때 준수해야 하는 규칙을 정의합니다:

| Requirement | Description |
|-------------|-------------|
| Property must be `required=True` | null 불가 |
| Property cannot have `default_value` | 기본값 불가 |
| Data type must be STRING or ARRAY[STRING] | 마킹 ID용 |
| Property should be indexed | 성능 최적화 |

```python
from ontology_definition.constraints.mandatory_control import (
    MandatoryControlPropertyRequirements
)

# 속성 검증
errors = MandatoryControlPropertyRequirements.validate_property_for_mandatory_control(
    is_required=True,
    has_default=False,
    data_type="STRING",
    is_array=True
)

if errors:
    print("Validation failed:", errors)
else:
    print("Property is valid for mandatory control")
```

### UUID Validation

`allowed_markings`와 `allowed_organizations`의 모든 항목은 유효한 UUID 형식이어야 합니다.

```python
# 유효
config = MandatoryControlConfig(
    property_api_name="securityMarking",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="security_markings",
    allowed_markings=["550e8400-e29b-41d4-a716-446655440000"]  # Valid UUID
)

# 유효하지 않음 - ValueError 발생
config = MandatoryControlConfig(
    property_api_name="securityMarking",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="security_markings",
    allowed_markings=["not-a-uuid"]  # Invalid
)
```

## SecurityMarkingReference

보안 마킹 정의에 대한 참조입니다.

```python
from ontology_definition.constraints.mandatory_control import SecurityMarkingReference

marking = SecurityMarkingReference(
    marking_id="550e8400-e29b-41d4-a716-446655440000",
    display_name="Confidential - Finance",
    description="Access restricted to finance department"
)
```

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `marking_id` | `str` | 보안 마킹의 UUID | Yes |
| `display_name` | `str` | 사람이 읽을 수 있는 이름 | No |
| `description` | `str` | 마킹에 대한 설명 | No |

## Serialization Methods

### to_foundry_dict()

```python
config = MandatoryControlConfig(
    property_api_name="securityMarking",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="security_markings",
    allowed_markings=["550e8400-e29b-41d4-a716-446655440000"]
)

foundry_dict = config.to_foundry_dict()
# Output:
# {
#     "propertyApiName": "securityMarking",
#     "controlType": "MARKINGS",
#     "markingColumnMapping": "security_markings",
#     "allowedMarkings": ["550e8400-e29b-41d4-a716-446655440000"]
# }
```

### from_foundry_dict()

```python
foundry_data = {
    "propertyApiName": "securityMarking",
    "controlType": "MARKINGS",
    "markingColumnMapping": "security_markings"
}

config = MandatoryControlConfig.from_foundry_dict(foundry_data)
```

---

# Part 3: RestrictedViews (GAP-001)

## Concept

RestrictedView는 행 수준 보안을 위한 뷰 정의입니다. Mandatory Control Properties와 함께 사용되어 사용자의 보안 마킹에 따라 데이터 접근을 필터링합니다.

## Current Status

| Status | Description |
|--------|-------------|
| GAP-001 | Critical - Not yet implemented |

현재 Ontology-Definition에서 RestrictedView는 아직 구현되지 않았습니다.

## Planned Structure

```python
# 계획된 구조 (미구현)
class RestrictedView(BaseModel):
    """
    행 수준 보안을 위한 Restricted View 정의.
    """

    view_rid: str = Field(
        ...,
        description="Foundry Resource ID of the restricted view"
    )

    backing_table: str = Field(
        ...,
        description="Reference to the backing dataset RID"
    )

    filter_expression: str = Field(
        ...,
        description="SQL-like filter expression for row filtering"
    )

    visibility_rules: list[VisibilityRule] = Field(
        default_factory=list,
        description="Rules determining row visibility based on user attributes"
    )

    mandatory_control_property: str = Field(
        ...,
        description="API name of the mandatory control property"
    )
```

## How Restricted Views Work

```
┌─────────────────────────────────────────────────────────────┐
│                    Backing Dataset                          │
│  ┌─────────┬───────────┬──────────────────────────────────┐│
│  │ id      │ data      │ security_markings                ││
│  ├─────────┼───────────┼──────────────────────────────────┤│
│  │ 1       │ Row 1     │ [finance-uuid, hr-uuid]          ││
│  │ 2       │ Row 2     │ [finance-uuid]                   ││
│  │ 3       │ Row 3     │ [hr-uuid]                        ││
│  │ 4       │ Row 4     │ [engineering-uuid]               ││
│  └─────────┴───────────┴──────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Restricted View                          │
│   Filter: user_markings INTERSECT row_markings != EMPTY     │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Finance  │      │   HR     │      │ Engineer │
    │  User    │      │  User    │      │   User   │
    │          │      │          │      │          │
    │ Sees:    │      │ Sees:    │      │ Sees:    │
    │ Row 1, 2 │      │ Row 1, 3 │      │ Row 4    │
    └──────────┘      └──────────┘      └──────────┘
```

## Implementation Roadmap

1. **Phase 1:** `RestrictedViewConfig` 모델 정의
2. **Phase 2:** ObjectType과의 연결 구현
3. **Phase 3:** Foundry 내보내기/가져오기 지원
4. **Phase 4:** 유효성 검증 규칙 구현

---

# Part 4: Security Best Practices

## Mandatory Control Usage

### When to Use

| Scenario | Recommendation |
|----------|----------------|
| 민감한 데이터 | MARKINGS 사용 |
| 부서/팀 격리 | ORGANIZATIONS 사용 |
| 정부/군사 환경 | CLASSIFICATIONS 사용 |
| 멀티테넌트 애플리케이션 | MARKINGS 또는 ORGANIZATIONS |
| 규제 준수 (HIPAA, GDPR) | MARKINGS + 감사 로깅 |

### When NOT to Use

- 모든 사용자가 모든 데이터에 접근해야 하는 경우
- 성능이 최우선인 대용량 분석 워크로드
- 개발/테스트 환경 (단, 프로덕션 환경 미러링 시 예외)

## Configuration Examples

### Example 1: Basic Security Marking

```python
from ontology_definition.constraints.property_constraints import PropertyConstraints
from ontology_definition.constraints.mandatory_control import MandatoryControlConfig
from ontology_definition.core.enums import ControlType

# 1. 속성 제약조건 정의
security_property_constraints = PropertyConstraints(
    required=True,  # 필수 - Mandatory Control 요구사항
    # default_value 없음 - Mandatory Control 요구사항
)

# 2. Mandatory Control 설정
mandatory_control = MandatoryControlConfig(
    property_api_name="securityMarking",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="security_markings",
    allowed_markings=[
        "550e8400-e29b-41d4-a716-446655440000",  # Finance
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8",  # HR
        "123e4567-e89b-12d3-a456-426614174000"   # Engineering
    ]
)
```

### Example 2: Organization-Based Access

```python
from ontology_definition.constraints.mandatory_control import MandatoryControlConfig
from ontology_definition.core.enums import ControlType

org_control = MandatoryControlConfig(
    property_api_name="ownerOrganization",
    control_type=ControlType.ORGANIZATIONS,
    allowed_organizations=[
        "org-north-america-uuid",
        "org-europe-uuid",
        "org-asia-pacific-uuid"
    ]
)
```

### Example 3: Government Classification (CBAC)

```python
from ontology_definition.constraints.mandatory_control import MandatoryControlConfig
from ontology_definition.core.enums import ControlType, ClassificationLevel

classification_control = MandatoryControlConfig(
    property_api_name="classificationLevel",
    control_type=ControlType.CLASSIFICATIONS,
    max_classification_level=ClassificationLevel.SECRET
)
```

## Row-Level Security Patterns

### Pattern 1: Marking-Based Access

가장 일반적인 패턴입니다. 각 행에 보안 마킹이 할당되고, 사용자는 자신의 마킹과 교집합이 있는 행만 볼 수 있습니다.

```
User Markings: [A, B]
Row Markings:  [B, C]
Intersection:  [B] (non-empty)
Result:        ACCESS GRANTED
```

```python
# 속성 정의 예시
from ontology_definition.core.property_definition import PropertyDefinition
from ontology_definition.core.enums import DataType

security_marking_property = PropertyDefinition(
    api_name="securityMarkings",
    display_name="Security Markings",
    data_type=DataType.ARRAY,
    array_item_type=DataType.STRING,
    constraints=PropertyConstraints(
        required=True,
        array=ArrayConstraints(min_items=1)
    ),
    is_mandatory_control=True,
    mandatory_control_config=MandatoryControlConfig(
        property_api_name="securityMarkings",
        control_type=ControlType.MARKINGS,
        marking_column_mapping="security_markings"
    )
)
```

### Pattern 2: Organization Hierarchy

조직 계층 구조를 기반으로 접근을 제어합니다. 상위 조직의 사용자는 하위 조직의 데이터에 접근할 수 있습니다.

```
Organization Hierarchy:
Global
├── North America
│   ├── US-East
│   └── US-West
├── Europe
│   ├── UK
│   └── Germany
└── Asia Pacific
    ├── Japan
    └── Australia

User Org: North America
Accessible: North America, US-East, US-West
```

### Pattern 3: Multi-Tenant Isolation

멀티테넌트 환경에서 테넌트 간 데이터 격리를 구현합니다.

```python
# 테넌트별 보안 마킹 설정
tenant_markings = {
    "tenant-a": "tenant-a-marking-uuid",
    "tenant-b": "tenant-b-marking-uuid",
    "tenant-c": "tenant-c-marking-uuid",
}

multi_tenant_control = MandatoryControlConfig(
    property_api_name="tenantId",
    control_type=ControlType.MARKINGS,
    marking_column_mapping="tenant_markings",
    allowed_markings=list(tenant_markings.values())
)
```

## Security Checklist

### Before Production Deployment

- [ ] 모든 민감한 ObjectType에 Mandatory Control 설정 완료
- [ ] 보안 마킹 UUID가 Foundry에 등록됨
- [ ] 속성이 `required=True`, `default_value=None` 확인
- [ ] Restricted View가 올바르게 구성됨
- [ ] 감사 로깅 활성화
- [ ] 접근 정책 문서화

### Common Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| `required=False` 설정 | 마킹 없는 행 생성 가능 | 항상 `required=True` |
| `default_value` 설정 | 의도치 않은 접근 허용 | 기본값 사용 금지 |
| 마킹 UUID 하드코딩 | 환경 간 불일치 | 환경 변수/설정 파일 사용 |
| Restricted View 누락 | 행 수준 필터링 없음 | RestrictedView 구성 필수 |

---

# Part 5: AccessLevel Enum

## Definition

속성 수준의 접근 제어를 위한 열거형입니다.

```python
from ontology_definition.core.enums import AccessLevel
```

| Level | Description | Use Case |
|-------|-------------|----------|
| `FULL` | 완전한 읽기/쓰기 접근 | 일반 속성 |
| `READ_ONLY` | 읽기만 가능, 수정 불가 | 감사 필드, 시스템 필드 |
| `MASKED` | 부분 가시성 (예: SSN 마지막 4자리) | 민감한 개인정보 |
| `HIDDEN` | 완전히 숨김 | 내부 시스템 필드 |

## Usage Examples

```python
from ontology_definition.core.enums import AccessLevel

# 일반 필드
name_access = AccessLevel.FULL

# 생성 일시 (수정 불가)
created_at_access = AccessLevel.READ_ONLY

# SSN (마스킹)
ssn_access = AccessLevel.MASKED

# 내부 해시 (숨김)
internal_hash_access = AccessLevel.HIDDEN
```

---

# Part 6: SecurityPolicyType Enum

## Definition

ObjectType에 적용할 수 있는 보안 정책 유형입니다.

```python
from ontology_definition.core.enums import SecurityPolicyType
```

| Type | Description | Use Case |
|------|-------------|----------|
| `RESTRICTED_VIEW` | Foundry Restricted View 사용 | 행 수준 필터링 |
| `PROPERTY_BASED` | 속성 값과 사용자 속성 기반 필터링 | 유연한 정책 |
| `CUSTOM` | 함수/표현식을 통한 커스텀 로직 | 복잡한 보안 요구사항 |

---

# Complete Example

## Secure ObjectType Definition

```python
from ontology_definition.core.object_type import ObjectType
from ontology_definition.core.property_definition import PropertyDefinition
from ontology_definition.core.enums import DataType, ObjectStatus, ControlType
from ontology_definition.constraints.property_constraints import (
    PropertyConstraints,
    StringConstraints,
    ArrayConstraints,
)
from ontology_definition.constraints.mandatory_control import MandatoryControlConfig

# 민감한 고객 데이터 ObjectType 정의
customer_object_type = ObjectType(
    api_name="SecureCustomer",
    display_name="Secure Customer",
    plural_display_name="Secure Customers",
    description="Customer data with row-level security",
    status=ObjectStatus.ACTIVE,

    # Primary Key
    primary_key_property="customerId",

    # Properties
    properties=[
        # Primary Key
        PropertyDefinition(
            api_name="customerId",
            display_name="Customer ID",
            data_type=DataType.STRING,
            constraints=PropertyConstraints(
                required=True,
                unique=True,
                immutable=True,
                string=StringConstraints(
                    pattern=r"^CUST-[A-Z0-9]{8}$"
                )
            )
        ),

        # Customer Name
        PropertyDefinition(
            api_name="customerName",
            display_name="Customer Name",
            data_type=DataType.STRING,
            constraints=PropertyConstraints(
                required=True,
                string=StringConstraints(
                    min_length=1,
                    max_length=200
                )
            )
        ),

        # Email (Unique)
        PropertyDefinition(
            api_name="email",
            display_name="Email Address",
            data_type=DataType.STRING,
            constraints=PropertyConstraints(
                required=True,
                unique=True,
                string=StringConstraints(
                    email_format=True
                )
            )
        ),

        # Security Markings (Mandatory Control)
        PropertyDefinition(
            api_name="securityMarkings",
            display_name="Security Markings",
            data_type=DataType.ARRAY,
            array_item_type=DataType.STRING,
            constraints=PropertyConstraints(
                required=True,  # MANDATORY for security
                # NO default_value - MANDATORY for security
                array=ArrayConstraints(
                    min_items=1,
                    unique_items=True
                )
            )
        ),
    ],

    # Security Configuration
    mandatory_control_config=MandatoryControlConfig(
        property_api_name="securityMarkings",
        control_type=ControlType.MARKINGS,
        marking_column_mapping="security_markings",
        allowed_markings=[
            "550e8400-e29b-41d4-a716-446655440000",  # Sales
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8",  # Support
            "123e4567-e89b-12d3-a456-426614174000"   # Finance
        ]
    )
)

# Foundry 형식으로 내보내기
foundry_export = customer_object_type.to_foundry_dict()
```

---

## Summary

| Component | Purpose | Key Points |
|-----------|---------|------------|
| PropertyConstraints | 속성 값 검증 | required, unique, immutable, type-specific |
| StringConstraints | 문자열 검증 | length, pattern, format |
| NumericConstraints | 숫자 검증 | min/max, exclusive, multiple_of |
| ArrayConstraints | 배열 검증 | item count, uniqueness |
| DecimalConstraints | DECIMAL 검증 | precision, scale |
| VectorConstraints | VECTOR 검증 | dimension |
| MandatoryControlConfig | 행 수준 보안 | MARKINGS, ORGANIZATIONS, CLASSIFICATIONS |
| SecurityMarkingReference | 마킹 참조 | UUID, display_name, description |
| AccessLevel | 속성 접근 제어 | FULL, READ_ONLY, MASKED, HIDDEN |

---

## Related Documentation

- [ObjectType.md](./ObjectType.md) - ObjectType 정의
- [PropertyDefinition.md](./PropertyDefinition.md) - 속성 정의
- [Interface.md](./Interface.md) - 인터페이스 정의
- [LinkType.md](./LinkType.md) - 링크 타입 정의

---

*Last Updated: 2026-01-17*
*Version: 1.0.0*
