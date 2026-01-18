# SharedProperty, StructType, ValueType

이 문서는 Ontology-Definition 시스템에서 재사용 가능한 타입 정의 요소들을 설명합니다. 이 세 가지 요소는 ObjectType 간 일관성을 유지하고 스키마 재사용을 가능하게 하는 핵심 빌딩 블록입니다.

**Source Files:**
- `ontology_definition/types/shared_property.py` (494 lines)
- `ontology_definition/types/struct_type.py` (557 lines)
- `ontology_definition/types/value_type.py` (537 lines)

**JSON Schema Reference:**
- `docs/research/schemas/Property.schema.json`

---

# Part 1: SharedProperty

## Definition

SharedProperty는 여러 ObjectType에서 재사용할 수 있는 속성 정의입니다. SharedProperty를 사용하면 다음을 달성할 수 있습니다:

- **일관된 속성 스키마**: 여러 ObjectType에 걸쳐 동일한 속성 정의 재사용
- **시맨틱 타이핑**: 속성명이 달라도 의미 기반의 크로스-ObjectType 쿼리 가능
- **중앙화된 제약 관리**: 한 곳에서 제약 조건 변경 시 모든 참조 위치에 적용
- **Mandatory Control 지원**: 보안 속성에 대한 행 수준 접근 제어

## Core Concepts

### Schema Reuse Pattern

SharedProperty는 `sharedPropertyRef`를 통해 여러 ObjectType에서 참조됩니다:

```python
# SharedProperty 정의
created_at = SharedProperty(
    api_name="createdAt",
    display_name="Created At",
    description="Timestamp when this object was created",
    data_type=DataTypeSpec(type=DataType.TIMESTAMP),
    constraints=PropertyConstraints(required=True, immutable=True),
    semantic_type=SemanticType.CREATED_AT,
)

# ObjectType에서 참조 (sharedPropertyRef 사용)
# 모든 ObjectType이 동일한 createdAt 정의를 공유
```

### Semantic Typing for Cross-ObjectType Queries

SemanticType을 통해 속성의 의미를 정의하면, 실제 `apiName`과 관계없이 동일한 의미를 가진 속성들을 쿼리할 수 있습니다:

```python
# 예: 모든 ObjectType에서 "생성 시간" 속성 찾기
# apiName이 "createdAt", "createTime", "creation_date" 등으로 달라도
# SemanticType.CREATED_AT로 통합 쿼리 가능
```

### Mandatory Control Support (GAP-002)

보안 마킹 속성을 위한 Mandatory Control 지원:

```python
security_markings = SharedProperty(
    api_name="securityMarkings",
    display_name="Security Markings",
    data_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING)
    ),
    is_mandatory_control=True,
    mandatory_control_config=MandatoryControlConfig(
        control_type=ControlType.MARKINGS,
        enforcement_level=EnforcementLevel.STRICT,
    ),
    semantic_type=SemanticType.SECURITY_MARKING,
)
```

## Schema Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `api_name` | `str` | 고유 식별자 (camelCase, 1-255자) |
| `display_name` | `str` | 사람이 읽을 수 있는 이름 (1-255자) |
| `data_type` | `DataTypeSpec` | 데이터 타입 명세 |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | `str` | `None` | 문서화용 설명 (최대 4096자) |
| `constraints` | `PropertyConstraints` | `None` | 유효성 검증 제약 조건 |
| `semantic_type` | `SemanticType` | `None` | 시맨틱 의미 분류 |
| `is_mandatory_control` | `bool` | `False` | 보안 마킹 속성 여부 |
| `mandatory_control_config` | `MandatoryControlConfig` | `None` | Mandatory Control 설정 |
| `status` | `SharedPropertyStatus` | `EXPERIMENTAL` | 라이프사이클 상태 |
| `used_by_object_types` | `list[str]` | `[]` | 이 속성을 사용하는 ObjectType 목록 (자동 생성, readOnly) |

### RID Format

```
^ri\.ontology\.[a-z]+\.shared-property\.[a-zA-Z0-9-]+$
```

예: `ri.ontology.main.shared-property.abc123-def456`

## SemanticType Enum

SharedProperty의 의미를 분류하는 열거형:

### Identity (식별)
| Value | Description |
|-------|-------------|
| `IDENTIFIER` | 고유 식별자 |
| `NAME` | 이름 필드 |
| `DESCRIPTION` | 설명 필드 |

### Temporal / Audit (시간/감사)
| Value | Description |
|-------|-------------|
| `TIMESTAMP` | 일반 타임스탬프 |
| `CREATED_AT` | 생성 시간 |
| `MODIFIED_AT` | 수정 시간 |
| `CREATED_BY` | 생성자 |
| `MODIFIED_BY` | 수정자 |

### Classification (분류)
| Value | Description |
|-------|-------------|
| `STATUS` | 상태 필드 |
| `CATEGORY` | 카테고리 |
| `TAG` | 태그 |

### Contact (연락처)
| Value | Description |
|-------|-------------|
| `URL` | URL |
| `EMAIL` | 이메일 |
| `PHONE` | 전화번호 |
| `ADDRESS` | 주소 |

### Numeric (숫자)
| Value | Description |
|-------|-------------|
| `CURRENCY` | 통화 금액 |
| `PERCENTAGE` | 백분율 |

### Security (보안)
| Value | Description |
|-------|-------------|
| `SECURITY_MARKING` | 보안 마킹 (Mandatory Control 필수) |

### Other
| Value | Description |
|-------|-------------|
| `CUSTOM` | 사용자 정의 |

## SharedPropertyStatus Enum

라이프사이클 상태를 나타내는 열거형:

| Status | Description |
|--------|-------------|
| `DRAFT` | 초안 상태 |
| `EXPERIMENTAL` | 실험적 (기본값) |
| `ALPHA` | 알파 버전 |
| `BETA` | 베타 버전 |
| `ACTIVE` | 활성 상태 |
| `STABLE` | 안정 버전 |
| `DEPRECATED` | 더 이상 사용 권장하지 않음 |
| `SUNSET` | 종료 예정 |
| `ARCHIVED` | 보관됨 |
| `DELETED` | 삭제됨 |

## Mandatory Control Configuration

### Requirements

`isMandatoryControl=true`일 때 적용되는 필수 규칙:

1. **mandatory_control_config 필수**: 설정이 반드시 존재해야 함
2. **required=True 필수**: 제약 조건에서 필수 속성이어야 함
3. **default_value 금지**: 기본값을 가질 수 없음
4. **데이터 타입 제한**: STRING 또는 ARRAY[STRING]만 허용

### MandatoryControlConfig Fields

| Field | Type | Description |
|-------|------|-------------|
| `control_type` | `ControlType` | MARKINGS, ORGANIZATIONS, CLASSIFICATIONS |
| `enforcement_level` | `EnforcementLevel` | STRICT, WARN, AUDIT_ONLY |
| `allowed_markings` | `list[str]` | MARKINGS 타입일 때 허용되는 마킹 ID 목록 |
| `allowed_organizations` | `list[str]` | ORGANIZATIONS 타입일 때 허용되는 조직 ID 목록 |
| `max_classification_level` | `str` | CLASSIFICATIONS 타입일 때 최대 분류 수준 |

### Validation Rules

```python
@model_validator(mode="after")
def validate_mandatory_control_config(self) -> "SharedProperty":
    if self.is_mandatory_control:
        # Must have mandatory control config
        if self.mandatory_control_config is None:
            raise ValueError("Mandatory control property must have mandatory_control_config")

        # Must be required
        if not self.constraints or not self.constraints.required:
            raise ValueError("Mandatory control property must have required=True constraint")

        # Cannot have default value
        if self.constraints and self.constraints.default_value is not None:
            raise ValueError("Mandatory control property cannot have a default value")

        # Must be STRING or ARRAY[STRING]
        valid_type = (
            self.data_type.type == DataType.STRING
            or (
                self.data_type.type == DataType.ARRAY
                and self.data_type.array_item_type
                and self.data_type.array_item_type.type == DataType.STRING
            )
        )
        if not valid_type:
            raise ValueError("Mandatory control property must be STRING or ARRAY[STRING] type")
    return self
```

### SemanticType Validation

```python
@model_validator(mode="after")
def validate_semantic_type_matches(self) -> "SharedProperty":
    if self.semantic_type is None:
        return self

    # Temporal semantic types should have temporal data types
    temporal_semantics = {SemanticType.TIMESTAMP, SemanticType.CREATED_AT, SemanticType.MODIFIED_AT}
    temporal_types = {DataType.TIMESTAMP, DataType.DATETIME, DataType.DATE}

    if self.semantic_type in temporal_semantics:
        if self.data_type.type not in temporal_types:
            raise ValueError(
                f"Semantic type {self.semantic_type.value} requires a temporal "
                f"data type (TIMESTAMP, DATETIME, DATE)"
            )

    # Security marking must be mandatory control
    if self.semantic_type == SemanticType.SECURITY_MARKING:
        if not self.is_mandatory_control:
            raise ValueError("SECURITY_MARKING semantic type requires is_mandatory_control=True")

    return self
```

## CommonSharedProperties Factory

자주 사용되는 SharedProperty를 쉽게 생성하기 위한 팩토리 클래스:

### created_at()

생성 시간 속성:

```python
@staticmethod
def created_at() -> SharedProperty:
    return SharedProperty(
        api_name="createdAt",
        display_name="Created At",
        description="Timestamp when this object was created.",
        data_type=DataTypeSpec(type=DataType.TIMESTAMP),
        constraints=PropertyConstraints(required=True, immutable=True),
        semantic_type=SemanticType.CREATED_AT,
        status=SharedPropertyStatus.ACTIVE,
    )
```

### modified_at()

수정 시간 속성:

```python
@staticmethod
def modified_at() -> SharedProperty:
    return SharedProperty(
        api_name="modifiedAt",
        display_name="Modified At",
        description="Timestamp when this object was last modified.",
        data_type=DataTypeSpec(type=DataType.TIMESTAMP),
        constraints=PropertyConstraints(required=True),
        semantic_type=SemanticType.MODIFIED_AT,
        status=SharedPropertyStatus.ACTIVE,
    )
```

### created_by()

생성자 속성:

```python
@staticmethod
def created_by() -> SharedProperty:
    return SharedProperty(
        api_name="createdBy",
        display_name="Created By",
        description="User ID who created this object.",
        data_type=DataTypeSpec(type=DataType.STRING),
        constraints=PropertyConstraints(required=True, immutable=True),
        semantic_type=SemanticType.CREATED_BY,
        status=SharedPropertyStatus.ACTIVE,
    )
```

### modified_by()

수정자 속성:

```python
@staticmethod
def modified_by() -> SharedProperty:
    return SharedProperty(
        api_name="modifiedBy",
        display_name="Modified By",
        description="User ID who last modified this object.",
        data_type=DataTypeSpec(type=DataType.STRING),
        constraints=PropertyConstraints(required=True),
        semantic_type=SemanticType.MODIFIED_BY,
        status=SharedPropertyStatus.ACTIVE,
    )
```

### security_markings()

보안 마킹 속성 (Mandatory Control):

```python
@staticmethod
def security_markings() -> SharedProperty:
    from ontology_definition.constraints.mandatory_control import (
        MandatoryControlConfig, EnforcementLevel,
    )
    from ontology_definition.core.enums import ControlType

    return SharedProperty(
        api_name="securityMarkings",
        display_name="Security Markings",
        description="Mandatory control property for row-level security based on user markings.",
        data_type=DataTypeSpec(
            type=DataType.ARRAY,
            array_item_type=DataTypeSpec(type=DataType.STRING),
        ),
        constraints=PropertyConstraints(
            required=True,
            array={"unique_items": True},
        ),
        is_mandatory_control=True,
        mandatory_control_config=MandatoryControlConfig(
            control_type=ControlType.MARKINGS,
            enforcement_level=EnforcementLevel.STRICT,
        ),
        semantic_type=SemanticType.SECURITY_MARKING,
        status=SharedPropertyStatus.ACTIVE,
    )
```

### status_field()

상태 필드 (enum 값 커스터마이즈 가능):

```python
@staticmethod
def status_field(allowed_values: Optional[list[str]] = None) -> SharedProperty:
    if allowed_values is None:
        allowed_values = ["DRAFT", "ACTIVE", "INACTIVE", "ARCHIVED"]

    return SharedProperty(
        api_name="status",
        display_name="Status",
        description="Lifecycle status of the object.",
        data_type=DataTypeSpec(type=DataType.STRING),
        constraints=PropertyConstraints(
            required=True,
            enum_values=allowed_values,
        ),
        semantic_type=SemanticType.STATUS,
        status=SharedPropertyStatus.ACTIVE,
    )
```

### name_field()

이름 필드:

```python
@staticmethod
def name_field() -> SharedProperty:
    return SharedProperty(
        api_name="name",
        display_name="Name",
        description="Display name of the object.",
        data_type=DataTypeSpec(type=DataType.STRING),
        constraints=PropertyConstraints(
            required=True,
            string={"min_length": 1, "max_length": 255},
        ),
        semantic_type=SemanticType.NAME,
        status=SharedPropertyStatus.ACTIVE,
    )
```

### description_field()

설명 필드:

```python
@staticmethod
def description_field() -> SharedProperty:
    return SharedProperty(
        api_name="description",
        display_name="Description",
        description="Detailed description of the object.",
        data_type=DataTypeSpec(type=DataType.STRING),
        constraints=PropertyConstraints(
            string={"max_length": 4096},
        ),
        semantic_type=SemanticType.DESCRIPTION,
        status=SharedPropertyStatus.ACTIVE,
    )
```

## Helper Methods

### is_audit_property()

감사(audit) 관련 속성인지 확인:

```python
def is_audit_property(self) -> bool:
    audit_semantics = {
        SemanticType.CREATED_AT, SemanticType.MODIFIED_AT,
        SemanticType.CREATED_BY, SemanticType.MODIFIED_BY,
    }
    return self.semantic_type in audit_semantics
```

### is_security_property()

보안 관련 속성인지 확인:

```python
def is_security_property(self) -> bool:
    return self.is_mandatory_control or self.semantic_type == SemanticType.SECURITY_MARKING
```

## Examples

### Basic SharedProperty

```python
from ontology_definition.types.shared_property import SharedProperty, SemanticType
from ontology_definition.types.property_def import DataTypeSpec
from ontology_definition.core.enums import DataType
from ontology_definition.constraints.property_constraints import PropertyConstraints

# 기본 타임스탬프 속성
created_at = SharedProperty(
    api_name="createdAt",
    display_name="Created At",
    description="When this object was created",
    data_type=DataTypeSpec(type=DataType.TIMESTAMP),
    constraints=PropertyConstraints(required=True, immutable=True),
    semantic_type=SemanticType.CREATED_AT,
)
```

### Security Marking Property

```python
from ontology_definition.types.shared_property import SharedProperty, SemanticType
from ontology_definition.constraints.mandatory_control import MandatoryControlConfig, EnforcementLevel
from ontology_definition.core.enums import ControlType, DataType

security_markings = SharedProperty(
    api_name="securityMarkings",
    display_name="Security Markings",
    data_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING)
    ),
    constraints=PropertyConstraints(required=True),
    is_mandatory_control=True,
    mandatory_control_config=MandatoryControlConfig(
        control_type=ControlType.MARKINGS,
        enforcement_level=EnforcementLevel.STRICT,
    ),
    semantic_type=SemanticType.SECURITY_MARKING,
)
```

### Using Factory Methods

```python
from ontology_definition.types.shared_property import CommonSharedProperties

# 팩토리 메서드로 간편 생성
created_at = CommonSharedProperties.created_at()
modified_at = CommonSharedProperties.modified_at()
security = CommonSharedProperties.security_markings()

# 커스텀 상태 값
custom_status = CommonSharedProperties.status_field(
    allowed_values=["PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"]
)
```

---

# Part 2: StructType

## Definition

StructType은 여러 필드를 가진 중첩 구조 타입입니다. 복잡한 데이터를 하나의 논리적 단위로 그룹화하여 여러 ObjectType에서 재사용할 수 있습니다.

**주요 용도:**
- 주소 (Address): street, city, state, postalCode, country
- 연락처 (ContactInfo): email, phone, fax
- 위치 좌표 (GeoCoordinate): latitude, longitude, altitude
- 금액 (MonetaryAmount): amount, currency

## Core Concepts

### Reusable Nested Structures

StructType은 `structTypeRef`를 통해 Property의 데이터 타입으로 참조됩니다:

```python
# StructType 정의
address_type = StructType(
    api_name="Address",
    display_name="Address",
    fields=[
        StructTypeField(api_name="street", ...),
        StructTypeField(api_name="city", ...),
    ]
)

# Property에서 structTypeRef로 참조
billing_address = PropertyDef(
    api_name="billingAddress",
    display_name="Billing Address",
    data_type=DataTypeSpec(type=DataType.STRUCT, struct_type_ref="Address"),
)
```

### Field-Level Constraints

각 필드에 개별적인 제약 조건을 설정할 수 있습니다:

```python
StructTypeField(
    api_name="postalCode",
    display_name="Postal Code",
    data_type=DataTypeSpec(type=DataType.STRING),
    required=True,
    constraints=StructFieldConstraints(
        pattern=r"^[A-Z0-9\- ]{3,10}$"
    ),
)
```

### Default Values Support

필드별 기본값 설정:

```python
StructTypeField(
    api_name="country",
    display_name="Country",
    data_type=DataTypeSpec(type=DataType.STRING),
    required=True,
    default_value="KR",  # 기본값 설정
)
```

## Schema Structure

### StructType

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `api_name` | `str` | Yes | 고유 식별자 (1-255자) |
| `display_name` | `str` | Yes | 사람이 읽을 수 있는 이름 |
| `description` | `str` | No | 문서화용 설명 |
| `fields` | `list[StructTypeField]` | Yes | 필드 정의 목록 (최소 1개) |
| `status` | `StructTypeStatus` | No | 라이프사이클 상태 (기본: EXPERIMENTAL) |

### RID Format

```
^ri\.ontology\.[a-z]+\.struct-type\.[a-zA-Z0-9-]+$
```

### StructTypeField

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `api_name` | `str` | Yes | - | 필드 이름 (camelCase) |
| `display_name` | `str` | Yes | - | 사람이 읽을 수 있는 이름 |
| `description` | `str` | No | `None` | 필드 설명 |
| `data_type` | `DataTypeSpec` | Yes | - | 필드 데이터 타입 |
| `required` | `bool` | No | `False` | 필수 여부 |
| `default_value` | `Any` | No | `None` | 기본값 |
| `constraints` | `StructFieldConstraints` | No | `None` | 유효성 검증 제약 |

### StructFieldConstraints

| Field | Type | Alias | Description |
|-------|------|-------|-------------|
| `min_value` | `float` | `minValue` | 최소 숫자 값 |
| `max_value` | `float` | `maxValue` | 최대 숫자 값 |
| `min_length` | `int` | `minLength` | 최소 문자열 길이 |
| `max_length` | `int` | `maxLength` | 최대 문자열 길이 |
| `pattern` | `str` | - | 정규식 패턴 |
| `enum` | `list[Any]` | - | 허용되는 값 목록 |

## StructTypeStatus Enum

| Status | Description |
|--------|-------------|
| `DRAFT` | 초안 상태 |
| `EXPERIMENTAL` | 실험적 (기본값) |
| `ALPHA` | 알파 버전 |
| `BETA` | 베타 버전 |
| `ACTIVE` | 활성 상태 |
| `STABLE` | 안정 버전 |
| `DEPRECATED` | 더 이상 사용 권장하지 않음 |
| `SUNSET` | 종료 예정 |
| `ARCHIVED` | 보관됨 |
| `DELETED` | 삭제됨 |

## Validation Rules

### Unique Field Names Required

```python
@model_validator(mode="after")
def validate_unique_field_names(self) -> "StructType":
    names = [f.api_name for f in self.fields]
    duplicates = [n for n in names if names.count(n) > 1]
    if duplicates:
        raise ValueError(f"Duplicate field apiNames found: {set(duplicates)}")
    return self
```

### At Least One Field Required

```python
fields: list[StructTypeField] = Field(
    ...,
    description="Field definitions within this struct.",
    min_length=1,  # 최소 1개 필드 필수
)
```

## CommonStructTypes Factory

### address()

물리적 주소 구조:

```python
@staticmethod
def address() -> StructType:
    return StructType(
        api_name="Address",
        display_name="Address",
        description="Physical or mailing address.",
        fields=[
            StructTypeField(
                api_name="street",
                display_name="Street",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
                constraints=StructFieldConstraints(max_length=255),
            ),
            StructTypeField(
                api_name="city",
                display_name="City",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
                constraints=StructFieldConstraints(max_length=100),
            ),
            StructTypeField(
                api_name="state",
                display_name="State/Province",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=False,
                constraints=StructFieldConstraints(max_length=100),
            ),
            StructTypeField(
                api_name="postalCode",
                display_name="Postal Code",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
                constraints=StructFieldConstraints(pattern=r"^[A-Z0-9\- ]{3,10}$"),
            ),
            StructTypeField(
                api_name="country",
                display_name="Country",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
                constraints=StructFieldConstraints(max_length=100),
            ),
        ],
        status=StructTypeStatus.ACTIVE,
    )
```

**필드 구성:**
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| street | STRING | Yes | maxLength: 255 |
| city | STRING | Yes | maxLength: 100 |
| state | STRING | No | maxLength: 100 |
| postalCode | STRING | Yes | pattern: `^[A-Z0-9\- ]{3,10}$` |
| country | STRING | Yes | maxLength: 100 |

### monetary_amount()

금액과 통화 구조:

```python
@staticmethod
def monetary_amount(currencies: Optional[list[str]] = None) -> StructType:
    if currencies is None:
        currencies = ["USD", "EUR", "GBP", "JPY", "KRW", "CNY"]

    return StructType(
        api_name="MonetaryAmount",
        display_name="Monetary Amount",
        description="Amount with currency.",
        fields=[
            StructTypeField(
                api_name="amount",
                display_name="Amount",
                data_type=DataTypeSpec(type=DataType.DECIMAL, precision=18, scale=2),
                required=True,
            ),
            StructTypeField(
                api_name="currency",
                display_name="Currency",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
                constraints=StructFieldConstraints(
                    pattern=r"^[A-Z]{3}$",
                    enum=currencies,
                ),
            ),
        ],
        status=StructTypeStatus.ACTIVE,
    )
```

**필드 구성:**
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| amount | DECIMAL(18,2) | Yes | - |
| currency | STRING | Yes | pattern: `^[A-Z]{3}$`, enum: [USD, EUR, GBP, JPY, KRW, CNY] |

### geo_coordinate()

지리 좌표 구조:

```python
@staticmethod
def geo_coordinate() -> StructType:
    return StructType(
        api_name="GeoCoordinate",
        display_name="Geographic Coordinate",
        description="Latitude/longitude coordinate with optional altitude.",
        fields=[
            StructTypeField(
                api_name="latitude",
                display_name="Latitude",
                data_type=DataTypeSpec(type=DataType.DOUBLE),
                required=True,
                constraints=StructFieldConstraints(min_value=-90.0, max_value=90.0),
            ),
            StructTypeField(
                api_name="longitude",
                display_name="Longitude",
                data_type=DataTypeSpec(type=DataType.DOUBLE),
                required=True,
                constraints=StructFieldConstraints(min_value=-180.0, max_value=180.0),
            ),
            StructTypeField(
                api_name="altitude",
                display_name="Altitude (meters)",
                data_type=DataTypeSpec(type=DataType.DOUBLE),
                required=False,
            ),
        ],
        status=StructTypeStatus.ACTIVE,
    )
```

**필드 구성:**
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| latitude | DOUBLE | Yes | minValue: -90.0, maxValue: 90.0 |
| longitude | DOUBLE | Yes | minValue: -180.0, maxValue: 180.0 |
| altitude | DOUBLE | No | - |

### contact_info()

연락처 정보 구조:

```python
@staticmethod
def contact_info() -> StructType:
    return StructType(
        api_name="ContactInfo",
        display_name="Contact Information",
        description="Contact details including email and phone.",
        fields=[
            StructTypeField(
                api_name="email",
                display_name="Email",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=False,
                constraints=StructFieldConstraints(
                    pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    max_length=255,
                ),
            ),
            StructTypeField(
                api_name="phone",
                display_name="Phone",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=False,
                constraints=StructFieldConstraints(
                    pattern=r"^\+?[0-9\-\s\(\)]{7,20}$",
                ),
            ),
            StructTypeField(
                api_name="fax",
                display_name="Fax",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=False,
            ),
        ],
        status=StructTypeStatus.ACTIVE,
    )
```

**필드 구성:**
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| email | STRING | No | pattern: email regex, maxLength: 255 |
| phone | STRING | No | pattern: `^\+?[0-9\-\s\(\)]{7,20}$` |
| fax | STRING | No | - |

## Helper Methods

### get_field(api_name)

특정 필드 조회:

```python
def get_field(self, api_name: str) -> Optional[StructTypeField]:
    for field in self.fields:
        if field.api_name == api_name:
            return field
    return None
```

### get_required_fields()

필수 필드 목록 조회:

```python
def get_required_fields(self) -> list[StructTypeField]:
    return [f for f in self.fields if f.required]
```

### get_optional_fields()

선택 필드 목록 조회:

```python
def get_optional_fields(self) -> list[StructTypeField]:
    return [f for f in self.fields if not f.required]
```

### get_field_names()

모든 필드 이름 목록:

```python
def get_field_names(self) -> list[str]:
    return [f.api_name for f in self.fields]
```

## Examples

### Custom StructType

```python
from ontology_definition.types.struct_type import StructType, StructTypeField, StructFieldConstraints
from ontology_definition.types.property_def import DataTypeSpec
from ontology_definition.core.enums import DataType

# 사용자 정의 구조 타입
payment_method = StructType(
    api_name="PaymentMethod",
    display_name="Payment Method",
    description="Credit card or bank account information.",
    fields=[
        StructTypeField(
            api_name="methodType",
            display_name="Method Type",
            data_type=DataTypeSpec(type=DataType.STRING),
            required=True,
            constraints=StructFieldConstraints(
                enum=["CREDIT_CARD", "DEBIT_CARD", "BANK_TRANSFER", "PAYPAL"]
            ),
        ),
        StructTypeField(
            api_name="lastFourDigits",
            display_name="Last Four Digits",
            data_type=DataTypeSpec(type=DataType.STRING),
            required=True,
            constraints=StructFieldConstraints(
                pattern=r"^\d{4}$",
                min_length=4,
                max_length=4,
            ),
        ),
        StructTypeField(
            api_name="expiryDate",
            display_name="Expiry Date",
            data_type=DataTypeSpec(type=DataType.STRING),
            required=False,
            constraints=StructFieldConstraints(
                pattern=r"^\d{2}/\d{2}$"  # MM/YY format
            ),
        ),
    ],
)
```

### Using Factory Methods

```python
from ontology_definition.types.struct_type import CommonStructTypes

# 표준 구조 타입 사용
address = CommonStructTypes.address()
geo = CommonStructTypes.geo_coordinate()
money = CommonStructTypes.monetary_amount(currencies=["USD", "KRW", "JPY"])
contact = CommonStructTypes.contact_info()

# 필드 접근
street_field = address.get_field("street")
required_fields = address.get_required_fields()
```

---

# Part 3: ValueType

## Definition

ValueType은 기본 타입(primitive type)에 제약 조건을 추가한 사용자 정의 타입입니다. 동일한 제약 조건을 여러 Property에 반복 정의하지 않고 재사용할 수 있습니다.

**핵심 가치:**
- **DRY 원칙**: 제약 조건 정의의 중복 제거
- **시맨틱 네이밍**: 타입 이름으로 의미 전달 (예: `EmailAddress`, `PositiveInteger`)
- **일관된 검증**: 한 곳에서 변경하면 모든 참조에 적용

## Core Concepts

### Constrained Type Derivation

ValueType은 기본 타입을 확장하여 제약 조건을 추가합니다:

```python
# 기본 STRING에 이메일 패턴 제약 추가
email_type = ValueType(
    api_name="EmailAddress",
    display_name="Email Address",
    base_type=ValueTypeBaseType.STRING,
    constraints=ValueTypeConstraints(
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        max_length=255,
        email_format=True,
    ),
)
```

### DRY Constraint Definitions

Property에서 `valueTypeRef`로 참조:

```python
# ValueType 없이 (반복)
email1 = PropertyDef(
    api_name="personalEmail",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(pattern="...", max_length=255),  # 반복
)
email2 = PropertyDef(
    api_name="workEmail",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(pattern="...", max_length=255),  # 반복
)

# ValueType 사용 (재사용)
email1 = PropertyDef(
    api_name="personalEmail",
    data_type=DataTypeSpec(type=DataType.STRING, value_type_ref="EmailAddress"),
)
email2 = PropertyDef(
    api_name="workEmail",
    data_type=DataTypeSpec(type=DataType.STRING, value_type_ref="EmailAddress"),
)
```

### Semantic Naming

타입 이름으로 의미를 명확하게 전달:

| ValueType | Meaning |
|-----------|---------|
| `EmailAddress` | 이메일 형식 문자열 |
| `PositiveInteger` | 양의 정수 |
| `Percentage` | 0-100 사이의 백분율 |
| `Priority` | LOW/MEDIUM/HIGH/CRITICAL 열거형 |
| `UUID` | UUID 형식 문자열 |

## ValueTypeBaseType Enum

ValueType이 확장할 수 있는 9가지 기본 타입:

| Base Type | Description | Use Case |
|-----------|-------------|----------|
| `STRING` | 문자열 | 이메일, URL, UUID 등 |
| `INTEGER` | 32비트 정수 | 양의 정수, 우선순위 등 |
| `LONG` | 64비트 정수 | 큰 숫자 |
| `FLOAT` | 32비트 부동소수점 | 단정밀도 숫자 |
| `DOUBLE` | 64비트 부동소수점 | 백분율, 좌표 등 |
| `BOOLEAN` | 불리언 | - |
| `DATE` | 날짜 (시간 없음) | ISO 날짜 형식 |
| `TIMESTAMP` | 타임스탬프 | - |
| `DATETIME` | 날짜+시간 | - |

**제한:** ARRAY, STRUCT 등 복합 타입은 ValueType의 기본 타입으로 사용 불가

## ValueTypeConstraints

ValueType을 정의하는 제약 조건. **최소 1개의 제약 조건이 필수**입니다.

### Enumeration Constraint

```python
enum: Optional[list[Any]] = Field(
    default=None,
    description="Allowed values for this ValueType.",
)
```

사용 예:
```python
ValueTypeConstraints(enum=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
```

### Numeric Constraints

| Field | Type | Alias | Description |
|-------|------|-------|-------------|
| `min_value` | `int | float` | `minValue` | 최소값 (inclusive) |
| `max_value` | `int | float` | `maxValue` | 최대값 (inclusive) |

사용 예:
```python
# 양의 정수
ValueTypeConstraints(min_value=1)

# 백분율 (0-100)
ValueTypeConstraints(min_value=0.0, max_value=100.0)
```

### String Constraints

| Field | Type | Alias | Description |
|-------|------|-------|-------------|
| `min_length` | `int` | `minLength` | 최소 문자열 길이 |
| `max_length` | `int` | `maxLength` | 최대 문자열 길이 |
| `pattern` | `str` | - | 정규식 패턴 |

사용 예:
```python
# 이메일 패턴
ValueTypeConstraints(
    pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    max_length=255,
)
```

### Format Flags

| Field | Type | Alias | Description |
|-------|------|-------|-------------|
| `rid_format` | `bool` | `ridFormat` | RID 형식 검증 |
| `uuid_format` | `bool` | `uuidFormat` | UUID 형식 검증 |
| `email_format` | `bool` | `emailFormat` | 이메일 형식 검증 |
| `url_format` | `bool` | `urlFormat` | URL 형식 검증 |
| `date_format` | `str` | `dateFormat` | 날짜 형식 문자열 (예: "YYYY-MM-DD") |

사용 예:
```python
# URL 형식
ValueTypeConstraints(url_format=True, max_length=2048)

# UUID 형식
ValueTypeConstraints(
    uuid_format=True,
    pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
)
```

## Validation Rules

### At Least One Constraint Required

```python
@model_validator(mode="after")
def validate_at_least_one_constraint(self) -> "ValueTypeConstraints":
    has_constraint = any([
        self.enum is not None,
        self.min_value is not None,
        self.max_value is not None,
        self.min_length is not None,
        self.max_length is not None,
        self.pattern is not None,
        self.rid_format,
        self.uuid_format,
        self.email_format,
        self.url_format,
        self.date_format is not None,
    ])
    if not has_constraint:
        raise ValueError("ValueTypeConstraints must specify at least one constraint")
    return self
```

### Constraints Must Match Base Type

```python
@model_validator(mode="after")
def validate_constraints_match_base_type(self) -> "ValueType":
    c = self.constraints
    bt = self.base_type

    # String constraints only for STRING type
    string_constraints = [c.min_length, c.max_length, c.pattern,
                        c.email_format, c.url_format, c.rid_format,
                        c.uuid_format, c.date_format]
    if any(string_constraints) and bt != ValueTypeBaseType.STRING:
        # date_format is also valid for DATE/DATETIME/TIMESTAMP
        if c.date_format and bt in (
            ValueTypeBaseType.DATE, ValueTypeBaseType.DATETIME, ValueTypeBaseType.TIMESTAMP
        ):
            pass  # OK
        else:
            # Check non-date string constraints
            non_date_string_constraints = [
                c.min_length, c.max_length, c.pattern,
                c.email_format, c.url_format, c.rid_format, c.uuid_format
            ]
            if any(non_date_string_constraints):
                raise ValueError(
                    f"String constraints are only valid for STRING base type, not {bt.value}"
                )

    # Numeric constraints only for numeric types
    numeric_types = {
        ValueTypeBaseType.INTEGER, ValueTypeBaseType.LONG,
        ValueTypeBaseType.FLOAT, ValueTypeBaseType.DOUBLE
    }
    if (c.min_value is not None or c.max_value is not None):
        if bt not in numeric_types:
            raise ValueError(
                f"Numeric constraints are only valid for numeric base types, not {bt.value}"
            )

    return self
```

### Min/Max Consistency

```python
@model_validator(mode="after")
def validate_min_max_consistency(self) -> "ValueTypeConstraints":
    if self.min_value is not None and self.max_value is not None:
        if self.min_value > self.max_value:
            raise ValueError(f"min_value ({self.min_value}) cannot be greater than max_value")

    if self.min_length is not None and self.max_length is not None:
        if self.min_length > self.max_length:
            raise ValueError(f"min_length ({self.min_length}) cannot be greater than max_length")

    return self
```

## ValueTypeStatus Enum

| Status | Description |
|--------|-------------|
| `DRAFT` | 초안 상태 |
| `EXPERIMENTAL` | 실험적 (기본값) |
| `ALPHA` | 알파 버전 |
| `BETA` | 베타 버전 |
| `ACTIVE` | 활성 상태 |
| `STABLE` | 안정 버전 |
| `DEPRECATED` | 더 이상 사용 권장하지 않음 |
| `SUNSET` | 종료 예정 |
| `ARCHIVED` | 보관됨 |
| `DELETED` | 삭제됨 |

## CommonValueTypes Factory

### email_address()

이메일 주소 타입:

```python
@staticmethod
def email_address() -> ValueType:
    return ValueType(
        api_name="EmailAddress",
        display_name="Email Address",
        description="Valid email address format.",
        base_type=ValueTypeBaseType.STRING,
        constraints=ValueTypeConstraints(
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            max_length=255,
            email_format=True,
        ),
        status=ValueTypeStatus.ACTIVE,
    )
```

**Constraints:**
| Constraint | Value |
|------------|-------|
| pattern | 이메일 정규식 |
| maxLength | 255 |
| emailFormat | true |

### positive_integer()

양의 정수 타입:

```python
@staticmethod
def positive_integer() -> ValueType:
    return ValueType(
        api_name="PositiveInteger",
        display_name="Positive Integer",
        description="Integer greater than zero.",
        base_type=ValueTypeBaseType.INTEGER,
        constraints=ValueTypeConstraints(min_value=1),
        status=ValueTypeStatus.ACTIVE,
    )
```

**Constraints:**
| Constraint | Value |
|------------|-------|
| minValue | 1 |

### priority()

우선순위 타입 (커스터마이즈 가능):

```python
@staticmethod
def priority(levels: Optional[list[str]] = None) -> ValueType:
    if levels is None:
        levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    return ValueType(
        api_name="Priority",
        display_name="Priority Level",
        description="Task or item priority level.",
        base_type=ValueTypeBaseType.STRING,
        constraints=ValueTypeConstraints(enum=levels),
        status=ValueTypeStatus.ACTIVE,
    )
```

**기본 허용 값:** `["LOW", "MEDIUM", "HIGH", "CRITICAL"]`

### url()

URL 타입:

```python
@staticmethod
def url() -> ValueType:
    return ValueType(
        api_name="URL",
        display_name="URL",
        description="Valid URL format.",
        base_type=ValueTypeBaseType.STRING,
        constraints=ValueTypeConstraints(
            url_format=True,
            max_length=2048,
        ),
        status=ValueTypeStatus.ACTIVE,
    )
```

**Constraints:**
| Constraint | Value |
|------------|-------|
| urlFormat | true |
| maxLength | 2048 |

### uuid()

UUID 타입:

```python
@staticmethod
def uuid() -> ValueType:
    return ValueType(
        api_name="UUID",
        display_name="UUID",
        description="Valid UUID format.",
        base_type=ValueTypeBaseType.STRING,
        constraints=ValueTypeConstraints(
            uuid_format=True,
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        ),
        status=ValueTypeStatus.ACTIVE,
    )
```

**Constraints:**
| Constraint | Value |
|------------|-------|
| uuidFormat | true |
| pattern | UUID 정규식 |

### percentage()

백분율 타입 (0-100):

```python
@staticmethod
def percentage() -> ValueType:
    return ValueType(
        api_name="Percentage",
        display_name="Percentage",
        description="Percentage value between 0 and 100.",
        base_type=ValueTypeBaseType.DOUBLE,
        constraints=ValueTypeConstraints(
            min_value=0.0,
            max_value=100.0,
        ),
        status=ValueTypeStatus.ACTIVE,
    )
```

**Constraints:**
| Constraint | Value |
|------------|-------|
| minValue | 0.0 |
| maxValue | 100.0 |

## Helper Methods

### is_enum_type()

열거형 타입인지 확인:

```python
def is_enum_type(self) -> bool:
    return self.constraints.enum is not None
```

### is_range_constrained()

숫자 범위 제약이 있는지 확인:

```python
def is_range_constrained(self) -> bool:
    return (
        self.constraints.min_value is not None
        or self.constraints.max_value is not None
    )
```

### is_pattern_constrained()

패턴 제약이 있는지 확인:

```python
def is_pattern_constrained(self) -> bool:
    return self.constraints.pattern is not None
```

### get_allowed_values()

열거형의 허용 값 목록 반환:

```python
def get_allowed_values(self) -> Optional[list[Any]]:
    return self.constraints.enum
```

## Examples

### Custom ValueType

```python
from ontology_definition.types.value_type import ValueType, ValueTypeBaseType, ValueTypeConstraints

# 전화번호 타입
phone_number = ValueType(
    api_name="PhoneNumber",
    display_name="Phone Number",
    description="International phone number format.",
    base_type=ValueTypeBaseType.STRING,
    constraints=ValueTypeConstraints(
        pattern=r"^\+[1-9]\d{1,14}$",  # E.164 format
        min_length=8,
        max_length=16,
    ),
)

# 금액 타입 (양수)
positive_money = ValueType(
    api_name="PositiveMoney",
    display_name="Positive Money Amount",
    description="Monetary amount greater than zero.",
    base_type=ValueTypeBaseType.DOUBLE,
    constraints=ValueTypeConstraints(
        min_value=0.01,  # 최소 0.01
    ),
)

# 작업 상태 타입
task_status = ValueType(
    api_name="TaskStatus",
    display_name="Task Status",
    description="Status of a task in the workflow.",
    base_type=ValueTypeBaseType.STRING,
    constraints=ValueTypeConstraints(
        enum=["PENDING", "IN_PROGRESS", "REVIEW", "COMPLETED", "CANCELLED"]
    ),
)
```

### Using Factory Methods

```python
from ontology_definition.types.value_type import CommonValueTypes

# 표준 ValueType 사용
email = CommonValueTypes.email_address()
positive = CommonValueTypes.positive_integer()
url = CommonValueTypes.url()
uuid = CommonValueTypes.uuid()
percent = CommonValueTypes.percentage()

# 커스텀 우선순위
custom_priority = CommonValueTypes.priority(
    levels=["P0", "P1", "P2", "P3", "P4"]
)

# 타입 검사
print(email.is_pattern_constrained())  # True
print(positive.is_range_constrained())  # True
print(custom_priority.is_enum_type())  # True
print(custom_priority.get_allowed_values())  # ['P0', 'P1', 'P2', 'P3', 'P4']
```

---

## API Reference

### SharedProperty

#### to_foundry_dict()

Palantir Foundry 호환 딕셔너리로 변환:

```python
def to_foundry_dict(self) -> dict[str, Any]:
    result = super().to_foundry_dict()

    result["$type"] = "SharedProperty"
    result["dataType"] = self.data_type.to_foundry_dict()
    result["status"] = self.status.value

    if self.constraints:
        result["constraints"] = self.constraints.to_foundry_dict()

    if self.is_mandatory_control:
        result["isMandatoryControl"] = True
        if self.mandatory_control_config:
            result["mandatoryControlConfig"] = self.mandatory_control_config.to_foundry_dict()

    if self.semantic_type:
        result["semanticType"] = self.semantic_type.value

    if self.used_by_object_types:
        result["usedByObjectTypes"] = self.used_by_object_types

    return result
```

**출력 예시:**
```json
{
  "$type": "SharedProperty",
  "apiName": "createdAt",
  "displayName": "Created At",
  "description": "Timestamp when this object was created.",
  "dataType": { "type": "TIMESTAMP" },
  "constraints": { "required": true, "immutable": true },
  "semanticType": "CREATED_AT",
  "status": "ACTIVE"
}
```

#### from_foundry_dict()

Foundry JSON에서 SharedProperty 생성:

```python
@classmethod
def from_foundry_dict(cls, data: dict[str, Any]) -> "SharedProperty":
    constraints = None
    if data.get("constraints"):
        constraints = PropertyConstraints.from_foundry_dict(data["constraints"])

    mandatory_control_config = None
    if data.get("mandatoryControlConfig"):
        mandatory_control_config = MandatoryControlConfig.from_foundry_dict(
            data["mandatoryControlConfig"]
        )

    semantic_type = None
    if data.get("semanticType"):
        semantic_type = SemanticType(data["semanticType"])

    return cls(
        rid=data.get("rid", generate_rid("ontology", "shared-property")),
        api_name=data["apiName"],
        display_name=data["displayName"],
        description=data.get("description"),
        data_type=DataTypeSpec.from_foundry_dict(data["dataType"]),
        constraints=constraints,
        is_mandatory_control=data.get("isMandatoryControl", False),
        mandatory_control_config=mandatory_control_config,
        semantic_type=semantic_type,
        status=SharedPropertyStatus(data.get("status", "EXPERIMENTAL")),
        used_by_object_types=data.get("usedByObjectTypes", []),
    )
```

### StructType

#### to_foundry_dict()

```python
def to_foundry_dict(self) -> dict[str, Any]:
    result = super().to_foundry_dict()

    result["$type"] = "StructType"
    result["fields"] = [f.to_foundry_dict() for f in self.fields]
    result["status"] = self.status.value

    return result
```

**출력 예시:**
```json
{
  "$type": "StructType",
  "apiName": "Address",
  "displayName": "Address",
  "description": "Physical or mailing address.",
  "fields": [
    {
      "apiName": "street",
      "displayName": "Street",
      "dataType": { "type": "STRING" },
      "required": true,
      "constraints": { "maxLength": 255 }
    },
    {
      "apiName": "city",
      "displayName": "City",
      "dataType": { "type": "STRING" },
      "required": true
    }
  ],
  "status": "ACTIVE"
}
```

#### from_foundry_dict()

```python
@classmethod
def from_foundry_dict(cls, data: dict[str, Any]) -> "StructType":
    fields = [
        StructTypeField.from_foundry_dict(f)
        for f in data["fields"]
    ]

    return cls(
        rid=data.get("rid", generate_rid("ontology", "struct-type")),
        api_name=data["apiName"],
        display_name=data["displayName"],
        description=data.get("description"),
        fields=fields,
        status=StructTypeStatus(data.get("status", "EXPERIMENTAL")),
    )
```

### ValueType

#### to_foundry_dict()

```python
def to_foundry_dict(self) -> dict[str, Any]:
    result = super().to_foundry_dict()

    result["$type"] = "ValueType"
    result["baseType"] = self.base_type.value
    result["constraints"] = self.constraints.to_foundry_dict()
    result["status"] = self.status.value

    if self.used_by_properties:
        result["usedByProperties"] = self.used_by_properties

    return result
```

**출력 예시:**
```json
{
  "$type": "ValueType",
  "apiName": "EmailAddress",
  "displayName": "Email Address",
  "description": "Valid email address format.",
  "baseType": "STRING",
  "constraints": {
    "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
    "maxLength": 255,
    "emailFormat": true
  },
  "status": "ACTIVE"
}
```

#### from_foundry_dict()

```python
@classmethod
def from_foundry_dict(cls, data: dict[str, Any]) -> "ValueType":
    return cls(
        rid=data.get("rid", generate_rid("ontology", "value-type")),
        api_name=data["apiName"],
        display_name=data["displayName"],
        description=data.get("description"),
        base_type=ValueTypeBaseType(data["baseType"]),
        constraints=ValueTypeConstraints.from_foundry_dict(data["constraints"]),
        status=ValueTypeStatus(data.get("status", "EXPERIMENTAL")),
        used_by_properties=data.get("usedByProperties", []),
    )
```

---

## Summary Comparison

| Aspect | SharedProperty | StructType | ValueType |
|--------|---------------|------------|-----------|
| **Purpose** | 속성 정의 재사용 | 중첩 구조 정의 | 제약 타입 정의 |
| **Base** | OntologyEntity | OntologyEntity | OntologyEntity |
| **Reference** | `sharedPropertyRef` | `structTypeRef` | `valueTypeRef` |
| **RID Prefix** | `shared-property` | `struct-type` | `value-type` |
| **Required Fields** | api_name, display_name, data_type | api_name, display_name, fields | api_name, display_name, base_type, constraints |
| **Constraints** | PropertyConstraints | StructFieldConstraints | ValueTypeConstraints |
| **Lifecycle** | SharedPropertyStatus | StructTypeStatus | ValueTypeStatus |
| **Special Feature** | SemanticType, MandatoryControl | Multiple fields | Primitive + constraints |
| **Factory Class** | CommonSharedProperties | CommonStructTypes | CommonValueTypes |

---

## Related Documentation

- [ObjectType Documentation](./ObjectType.md)
- [PropertyDef Documentation](./PropertyDef.md)
- [LinkType Documentation](./LinkType.md)
- [Property.schema.json](../../docs/research/schemas/Property.schema.json)
