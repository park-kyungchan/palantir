# PropertyDefinition

## Definition

**Property**는 ObjectType의 개별 속성을 정의하는 스키마 요소입니다. 실세계 엔티티나 이벤트의 특성을 모델링하며, 데이터 타입, 검증 규칙, 백킹 데이터셋 매핑 정보를 포함합니다.

```
PropertyDefinition = Identity + DataTypeSpec + Constraints + Mapping + Flags
```

### Key Characteristics

| Aspect | Description |
|--------|-------------|
| **Purpose** | ObjectType 내 단일 속성의 완전한 스키마 정의 |
| **Scope** | ObjectType, LinkType, StructType 내에서 사용 |
| **Data Types** | 20가지 Palantir Foundry 데이터 타입 지원 |
| **Validation** | 타입별 제약조건 + 공통 제약조건 |
| **Mapping** | 백킹 데이터셋 컬럼과의 매핑 |

---

## Core Concepts

### Property as Attribute of ObjectType

Property는 ObjectType의 구성 요소로, 실제 데이터의 특성을 모델링합니다:

```
ObjectType: Employee
├── Property: employeeId (PRIMARY KEY)
├── Property: name
├── Property: email
├── Property: department
└── Property: hireDate
```

### DataTypeSpec for Type Definition

모든 Property는 `DataTypeSpec`을 통해 데이터 타입을 명시합니다. 단순 타입부터 중첩 타입까지 지원합니다:

```python
# Simple type
DataTypeSpec(type=DataType.STRING)

# Complex type (Array of strings)
DataTypeSpec(
    type=DataType.ARRAY,
    array_item_type=DataTypeSpec(type=DataType.STRING)
)
```

### Constraints for Validation

Property에 적용되는 검증 규칙은 `PropertyConstraints`를 통해 정의됩니다:

```python
PropertyConstraints(
    required=True,
    unique=True,
    string=StringConstraints(min_length=1, max_length=100)
)
```

---

## DataTypeSpec

`DataTypeSpec`은 Property의 데이터 타입을 명시하는 모델입니다. 20가지 Palantir Foundry 데이터 타입을 지원하며, 복잡한 중첩 타입 구성이 가능합니다.

### Basic Structure

```python
class DataTypeSpec(BaseModel):
    type: DataType                           # Required: Base type identifier
    array_item_type: Optional[DataTypeSpec]  # For ARRAY type
    struct_fields: Optional[list[StructField]]  # For STRUCT type
    value_type_ref: Optional[str]            # Reference to custom ValueType
    precision: Optional[int]                 # For DECIMAL type (1-38)
    scale: Optional[int]                     # For DECIMAL type (0-38)
    vector_dimension: Optional[int]          # For VECTOR type
```

### type Field (DataType Enum)

`type` 필드는 20가지 데이터 타입 중 하나를 지정합니다:

#### Primitive Types

| Type | Description | Example |
|------|-------------|---------|
| `STRING` | 문자열 | `"Hello World"` |
| `INTEGER` | 32-bit 정수 | `42` |
| `LONG` | 64-bit 정수 | `9223372036854775807` |
| `FLOAT` | 32-bit 부동소수점 | `3.14` |
| `DOUBLE` | 64-bit 부동소수점 | `3.141592653589793` |
| `BOOLEAN` | 불리언 | `true`, `false` |
| `DECIMAL` | 고정 소수점 (금액 등) | `12345.67` |

#### Temporal Types

| Type | Description | Example |
|------|-------------|---------|
| `DATE` | 날짜 (연-월-일) | `2024-01-15` |
| `TIMESTAMP` | UTC 타임스탬프 | `2024-01-15T10:30:00Z` |
| `DATETIME` | 로컬 날짜/시간 | `2024-01-15T10:30:00` |
| `TIMESERIES` | 시계열 데이터 | Time-indexed values |

#### Complex Types

| Type | Description | Requires |
|------|-------------|----------|
| `ARRAY` | 배열/리스트 | `array_item_type` |
| `STRUCT` | 중첩 구조체 | `struct_fields` |
| `JSON` | 자유형 JSON | - |

#### Spatial Types

| Type | Description | Example |
|------|-------------|---------|
| `GEOPOINT` | 지리적 좌표 | `{lat: 37.5, lng: 127.0}` |
| `GEOSHAPE` | 지리적 형태 | Polygon, Line, etc. |

#### Media Types

| Type | Description | Use Case |
|------|-------------|----------|
| `MEDIA_REFERENCE` | 미디어 파일 참조 | Images, Videos |
| `BINARY` | 바이너리 데이터 | Files, Blobs |
| `MARKDOWN` | 마크다운 텍스트 | Rich text content |

#### AI/ML Types

| Type | Description | Requires |
|------|-------------|----------|
| `VECTOR` | 임베딩 벡터 | `vector_dimension` |

### Array Configuration (array_item_type)

`ARRAY` 타입은 반드시 `array_item_type`을 지정해야 합니다:

```python
# Array of strings
DataTypeSpec(
    type=DataType.ARRAY,
    array_item_type=DataTypeSpec(type=DataType.STRING)
)

# Nested array: Array of Array of integers
DataTypeSpec(
    type=DataType.ARRAY,
    array_item_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.INTEGER)
    )
)
```

**Validation Rule**: `ARRAY` 타입에 `array_item_type`이 없으면 `ValueError` 발생.

### Struct Configuration (struct_fields)

`STRUCT` 타입은 반드시 `struct_fields`를 지정해야 합니다:

```python
DataTypeSpec(
    type=DataType.STRUCT,
    struct_fields=[
        StructField(name="street", data_type=DataTypeSpec(type=DataType.STRING)),
        StructField(name="city", data_type=DataTypeSpec(type=DataType.STRING), required=True),
        StructField(name="zip_code", data_type=DataTypeSpec(type=DataType.STRING)),
    ]
)
```

#### StructField Definition

```python
class StructField(BaseModel):
    name: str                    # Field name (1-255 chars)
    data_type: DataTypeSpec      # Field data type (alias: "type")
    required: bool = False       # Is this field required?
    description: Optional[str]   # Documentation
```

**Validation Rule**: `STRUCT` 타입에 `struct_fields`가 비어있거나 없으면 `ValueError` 발생.

### ValueType Reference (value_type_ref)

사용자 정의 ValueType을 참조할 수 있습니다:

```python
# Reference to custom EmailAddress ValueType
DataTypeSpec(
    type=DataType.STRING,
    value_type_ref="EmailAddress"
)
```

ValueType은 기본 타입에 추가 제약조건을 적용한 재사용 가능한 타입입니다.

### Vector Configuration (vector_dimension)

`VECTOR` 타입은 반드시 `vector_dimension`을 지정해야 합니다:

```python
# 768-dimensional embedding vector
DataTypeSpec(
    type=DataType.VECTOR,
    vector_dimension=768
)

# 1536-dimensional OpenAI embedding
DataTypeSpec(
    type=DataType.VECTOR,
    vector_dimension=1536
)
```

**Validation Rule**:
- `vector_dimension` >= 1
- `VECTOR` 타입에 `vector_dimension`이 없으면 `ValueError` 발생

### Decimal Configuration (precision, scale)

`DECIMAL` 타입은 정밀도와 스케일을 지정할 수 있습니다:

```python
# Currency with 2 decimal places
DataTypeSpec(
    type=DataType.DECIMAL,
    precision=18,  # Total digits (1-38)
    scale=2        # Digits after decimal (0-precision)
)
```

| Parameter | Range | Description |
|-----------|-------|-------------|
| `precision` | 1-38 | 전체 자릿수 |
| `scale` | 0-38 | 소수점 이하 자릿수 |

**Constraint**: `scale <= precision`

---

## PropertyDefinition Fields

### Required Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `api_name` | `str` | 고유 식별자 (camelCase) | 1-255 chars, pattern: `^[a-zA-Z][a-zA-Z0-9_]*$` |
| `display_name` | `str` | UI 표시용 이름 | 1-255 chars |
| `data_type` | `DataTypeSpec` | 데이터 타입 명세 | Required |

#### api_name

Property의 프로그래밍적 식별자입니다:

```python
api_name="employeeId"    # Valid
api_name="employee_name" # Valid
api_name="123invalid"    # Invalid - must start with letter
api_name="my-prop"       # Invalid - hyphens not allowed
```

**Pattern**: `^[a-zA-Z][a-zA-Z0-9_]*$`
- 영문자로 시작
- 영문자, 숫자, 언더스코어만 허용

#### display_name

사용자에게 표시되는 이름입니다:

```python
display_name="Employee ID"
display_name="직원 번호"  # Unicode allowed
```

#### data_type

`DataTypeSpec` 인스턴스로 데이터 타입을 지정합니다:

```python
data_type=DataTypeSpec(type=DataType.STRING)
data_type=DataTypeSpec(type=DataType.INTEGER)
```

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | `Optional[str]` | `None` | 문서화 설명 (max 4096 chars) |
| `constraints` | `Optional[PropertyConstraints]` | `None` | 검증 제약조건 |
| `backing_column` | `Optional[str]` | `None` | 백킹 데이터셋 컬럼명 |
| `is_edit_only` | `bool` | `False` | 사용자 편집 전용 (데이터셋 없음) |
| `is_derived` | `bool` | `False` | 실시간 계산 필드 |
| `derived_expression` | `Optional[str]` | `None` | 파생 표현식/함수 참조 |
| `is_mandatory_control` | `bool` | `False` | 보안 마킹 속성 |
| `shared_property_ref` | `Optional[str]` | `None` | SharedProperty 참조 |

#### description

Property에 대한 상세 문서:

```python
description="Employee's unique identifier assigned at hire. Used for all internal systems."
```

#### constraints

`PropertyConstraints` 인스턴스로 검증 규칙 지정:

```python
constraints=PropertyConstraints(
    required=True,
    string=StringConstraints(max_length=100)
)
```

#### backing_column

백킹 데이터셋의 컬럼명:

```python
api_name="employeeName"
backing_column="employee_name"  # Dataset column name
```

**Note**: `is_edit_only=True`인 경우 `backing_column`을 설정하면 `ValueError` 발생.

#### is_edit_only

데이터셋에서 로드되지 않고 사용자 편집으로만 값이 설정되는 속성:

```python
PropertyDefinition(
    api_name="userNotes",
    display_name="User Notes",
    data_type=DataTypeSpec(type=DataType.STRING),
    is_edit_only=True,  # Not from dataset
    # backing_column=None  # Must not be set
)
```

#### is_derived / derived_expression

실시간으로 계산되는 파생 속성:

```python
PropertyDefinition(
    api_name="fullName",
    display_name="Full Name",
    data_type=DataTypeSpec(type=DataType.STRING),
    is_derived=True,
    derived_expression="concat(firstName, ' ', lastName)"
)
```

**Validation Rule**: `is_derived=True`일 때 `derived_expression`이 없으면 `ValueError` 발생.

#### is_mandatory_control

보안 마킹을 위한 필수 통제 속성:

```python
PropertyDefinition(
    api_name="securityMarkings",
    display_name="Security Markings",
    data_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING)
    ),
    constraints=PropertyConstraints(required=True),  # Must be required
    is_mandatory_control=True
)
```

**Validation Rules**:
1. `required=True` 필수
2. `default_value` 설정 불가
3. `STRING` 또는 `ARRAY[STRING]` 타입만 가능

#### shared_property_ref

SharedProperty 정의 참조:

```python
PropertyDefinition(
    api_name="createdAt",
    display_name="Created At",
    data_type=DataTypeSpec(type=DataType.TIMESTAMP),
    shared_property_ref="createdAt"  # Reference to shared definition
)
```

---

## PropertyConstraints

`PropertyConstraints`는 Property의 검증 규칙을 정의합니다.

### Common Flags

#### required

값이 null/empty일 수 없음:

```python
PropertyConstraints(required=True)
```

- `True`: 값 필수
- `False` (default): null 허용

#### immutable

초기 설정 후 변경 불가:

```python
PropertyConstraints(immutable=True)
```

- 생성 시에만 값 설정 가능
- 이후 수정 시도 시 오류

#### unique

모든 인스턴스에서 값이 고유해야 함:

```python
PropertyConstraints(unique=True)
```

- Primary Key 후보
- 인덱싱에 유리

#### default_value

값이 없을 때 사용할 기본값:

```python
PropertyConstraints(default_value="ACTIVE")
PropertyConstraints(default_value=0)
PropertyConstraints(default_value=["tag1", "tag2"])
```

**Note**: `is_mandatory_control=True`인 경우 `default_value` 설정 불가.

### String Constraints

`StringConstraints`는 STRING 타입에 적용되는 제약조건입니다:

```python
class StringConstraints(BaseModel):
    min_length: Optional[int]   # Minimum length (>= 0)
    max_length: Optional[int]   # Maximum length (>= 0)
    pattern: Optional[str]      # Regex pattern
    rid_format: bool = False    # Must be valid RID
    uuid_format: bool = False   # Must be valid UUID
    email_format: bool = False  # Must be valid email
    url_format: bool = False    # Must be valid URL
```

#### min_length / max_length

```python
StringConstraints(min_length=1, max_length=255)
```

**Validation**: `min_length <= max_length`

#### pattern

정규표현식 패턴:

```python
StringConstraints(pattern=r"^[A-Z]{2}\d{6}$")  # e.g., "AB123456"
```

#### Format Validations

| Flag | Description | Example |
|------|-------------|---------|
| `rid_format` | Palantir RID 형식 | `ri.ontology.main.object.12345` |
| `uuid_format` | UUID 형식 | `550e8400-e29b-41d4-a716-446655440000` |
| `email_format` | 이메일 형식 | `user@example.com` |
| `url_format` | URL 형식 | `https://example.com` |

### Numeric Constraints

`NumericConstraints`는 INTEGER, LONG, FLOAT, DOUBLE, DECIMAL 타입에 적용됩니다:

```python
class NumericConstraints(BaseModel):
    min_value: Optional[Union[int, float]]    # Minimum (inclusive by default)
    max_value: Optional[Union[int, float]]    # Maximum (inclusive by default)
    exclusive_min: bool = False               # Make min exclusive
    exclusive_max: bool = False               # Make max exclusive
    multiple_of: Optional[Union[int, float]]  # Must be multiple of this
```

#### min_value / max_value

```python
NumericConstraints(min_value=0, max_value=100)  # 0 <= value <= 100
NumericConstraints(min_value=1, exclusive_min=False)  # value >= 1
NumericConstraints(min_value=0, exclusive_min=True)   # value > 0
```

**Validation**: `min_value <= max_value`

#### multiple_of

```python
NumericConstraints(multiple_of=5)  # 5, 10, 15, ...
NumericConstraints(multiple_of=0.01)  # Currency precision
```

### Array Constraints

`ArrayConstraints`는 ARRAY 타입에 적용됩니다:

```python
class ArrayConstraints(BaseModel):
    min_items: Optional[int]   # Minimum items (>= 0)
    max_items: Optional[int]   # Maximum items (>= 0)
    unique_items: bool = False # All items must be unique
```

#### min_items / max_items

```python
ArrayConstraints(min_items=1, max_items=10)  # 1-10 items required
```

**Validation**: `min_items <= max_items`

#### unique_items

```python
ArrayConstraints(unique_items=True)  # No duplicates allowed
```

### Enum Values

허용되는 값의 목록을 지정:

```python
PropertyConstraints(
    enum=["DRAFT", "ACTIVE", "ARCHIVED"]
)

PropertyConstraints(
    enum=[1, 2, 3, 5, 8, 13]  # Numeric enum
)
```

**Validation**: `enum` 리스트는 비어있을 수 없음.

### Complete Constraints Example

```python
PropertyConstraints(
    required=True,
    unique=True,
    immutable=True,
    string=StringConstraints(
        min_length=1,
        max_length=100,
        pattern=r"^EMP\d{6}$"
    ),
    default_value=None
)
```

---

## Semantic Properties

### Primary Key Properties

ObjectType의 Primary Key로 사용되는 Property:

```python
# Property definition
employee_id = PropertyDefinition(
    api_name="employeeId",
    display_name="Employee ID",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(
        required=True,
        unique=True,
        immutable=True
    ),
    backing_column="employee_id"
)

# Primary Key reference
primary_key = PrimaryKeyDefinition(
    property_api_name="employeeId",
    backing_column="employee_id"
)
```

**Primary Key Requirements**:
- `required=True` (null 불가)
- `unique=True` (고유성)
- `immutable=True` (변경 불가 권장)

### Foreign Key Properties

다른 ObjectType을 참조하는 Property:

```python
# FK property pointing to Department
department_id = PropertyDefinition(
    api_name="departmentId",
    display_name="Department ID",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(required=True),
    backing_column="department_id"
)
```

Foreign Key는 LinkType 정의에서 참조됩니다.

### Mandatory Control Properties

Row-level security를 위한 필수 통제 속성:

```python
security_markings = PropertyDefinition(
    api_name="securityMarkings",
    display_name="Security Markings",
    description="Mandatory control property for row-level security based on user markings.",
    data_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING)
    ),
    constraints=PropertyConstraints(
        required=True,
        array=ArrayConstraints(unique_items=True)
    ),
    is_mandatory_control=True
)
```

**Control Types** (`ControlType` enum):
- `MARKINGS`: Security markings (most common)
- `ORGANIZATIONS`: Organization membership
- `CLASSIFICATIONS`: Classification-based (government)

---

## Validation Rules

### Type-Specific Validation

#### ARRAY Type

```python
# Valid
DataTypeSpec(type=DataType.ARRAY, array_item_type=DataTypeSpec(type=DataType.STRING))

# Invalid - missing array_item_type
DataTypeSpec(type=DataType.ARRAY)  # ValueError
```

#### STRUCT Type

```python
# Valid
DataTypeSpec(
    type=DataType.STRUCT,
    struct_fields=[StructField(name="x", data_type=DataTypeSpec(type=DataType.FLOAT))]
)

# Invalid - empty struct_fields
DataTypeSpec(type=DataType.STRUCT, struct_fields=[])  # ValueError
DataTypeSpec(type=DataType.STRUCT)  # ValueError
```

#### VECTOR Type

```python
# Valid
DataTypeSpec(type=DataType.VECTOR, vector_dimension=768)

# Invalid - missing vector_dimension
DataTypeSpec(type=DataType.VECTOR)  # ValueError
```

#### DECIMAL Type

```python
# Valid
DataTypeSpec(type=DataType.DECIMAL, precision=18, scale=2)

# Invalid - scale > precision
DecimalConstraints(precision=5, scale=10)  # ValueError
```

### Cross-Field Validation

#### Mandatory Control Rules

```python
@model_validator(mode="after")
def validate_mandatory_control_rules(self) -> "PropertyDefinition":
    if self.is_mandatory_control:
        # 1. Must be required
        if not self.constraints or not self.constraints.required:
            raise ValueError("Mandatory control property must have required=True")

        # 2. Cannot have default value
        if self.constraints and self.constraints.default_value is not None:
            raise ValueError("Mandatory control property cannot have a default value")

        # 3. Must be STRING or ARRAY[STRING]
        valid = (
            self.data_type.type == DataType.STRING
            or (
                self.data_type.type == DataType.ARRAY
                and self.data_type.array_item_type
                and self.data_type.array_item_type.type == DataType.STRING
            )
        )
        if not valid:
            raise ValueError("Mandatory control property must be STRING or ARRAY[STRING]")
```

#### Derived Property Rules

```python
@model_validator(mode="after")
def validate_derived_expression(self) -> "PropertyDefinition":
    if self.is_derived and not self.derived_expression:
        raise ValueError("Derived property must have derived_expression defined")
```

#### Edit-Only Property Rules

```python
@model_validator(mode="after")
def validate_edit_only_backing(self) -> "PropertyDefinition":
    if self.is_edit_only and self.backing_column:
        raise ValueError("Edit-only property should not have backing_column")
```

### Constraint Validation

#### Range Validations

| Constraint | Rule |
|------------|------|
| NumericConstraints | `min_value <= max_value` |
| StringConstraints | `min_length <= max_length` |
| ArrayConstraints | `min_items <= max_items` |
| DecimalConstraints | `scale <= precision` |

#### Enum Validation

```python
@field_validator("enum")
def validate_enum_not_empty(cls, v):
    if v is not None and len(v) == 0:
        raise ValueError("enum list cannot be empty")
    return v
```

---

## Examples

### Simple String Property

```python
from ontology_definition.types.property_def import PropertyDefinition, DataTypeSpec
from ontology_definition.core.enums import DataType
from ontology_definition.constraints.property_constraints import (
    PropertyConstraints,
    StringConstraints,
)

name_property = PropertyDefinition(
    api_name="employeeName",
    display_name="Employee Name",
    description="Full legal name of the employee.",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(
        required=True,
        string=StringConstraints(min_length=1, max_length=200)
    ),
    backing_column="employee_name"
)
```

**Foundry JSON Output**:
```json
{
    "apiName": "employeeName",
    "displayName": "Employee Name",
    "description": "Full legal name of the employee.",
    "dataType": {"type": "STRING"},
    "constraints": {
        "required": true,
        "minLength": 1,
        "maxLength": 200
    },
    "backingColumn": "employee_name"
}
```

### Array Property

```python
tags_property = PropertyDefinition(
    api_name="tags",
    display_name="Tags",
    description="Classification tags for this record.",
    data_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING)
    ),
    constraints=PropertyConstraints(
        array=ArrayConstraints(
            min_items=0,
            max_items=20,
            unique_items=True
        )
    ),
    backing_column="tags"
)
```

**Foundry JSON Output**:
```json
{
    "apiName": "tags",
    "displayName": "Tags",
    "description": "Classification tags for this record.",
    "dataType": {
        "type": "ARRAY",
        "arrayItemType": {"type": "STRING"}
    },
    "constraints": {
        "arrayMinItems": 0,
        "arrayMaxItems": 20,
        "arrayUnique": true
    },
    "backingColumn": "tags"
}
```

### Property with Full Constraints

```python
employee_id_property = PropertyDefinition(
    api_name="employeeId",
    display_name="Employee ID",
    description="Unique identifier assigned at hire. Format: EMP followed by 6 digits.",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(
        required=True,
        unique=True,
        immutable=True,
        string=StringConstraints(
            min_length=9,
            max_length=9,
            pattern=r"^EMP\d{6}$"
        )
    ),
    backing_column="employee_id"
)
```

**Foundry JSON Output**:
```json
{
    "apiName": "employeeId",
    "displayName": "Employee ID",
    "description": "Unique identifier assigned at hire. Format: EMP followed by 6 digits.",
    "dataType": {"type": "STRING"},
    "constraints": {
        "required": true,
        "unique": true,
        "immutable": true,
        "minLength": 9,
        "maxLength": 9,
        "pattern": "^EMP\\d{6}$"
    },
    "backingColumn": "employee_id"
}
```

### Struct Property (Address)

```python
from ontology_definition.types.property_def import StructField

address_property = PropertyDefinition(
    api_name="address",
    display_name="Address",
    description="Employee's primary address.",
    data_type=DataTypeSpec(
        type=DataType.STRUCT,
        struct_fields=[
            StructField(
                name="street",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
                description="Street address"
            ),
            StructField(
                name="city",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True
            ),
            StructField(
                name="state",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=False
            ),
            StructField(
                name="postalCode",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True
            ),
            StructField(
                name="country",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True
            ),
        ]
    ),
    backing_column="address_json"
)
```

### Decimal Property (Currency)

```python
salary_property = PropertyDefinition(
    api_name="salary",
    display_name="Annual Salary",
    description="Employee's annual salary in USD.",
    data_type=DataTypeSpec(
        type=DataType.DECIMAL,
        precision=12,
        scale=2
    ),
    constraints=PropertyConstraints(
        required=True,
        numeric=NumericConstraints(
            min_value=0,
            max_value=10000000
        )
    ),
    backing_column="annual_salary"
)
```

### Vector Property (Embedding)

```python
embedding_property = PropertyDefinition(
    api_name="contentEmbedding",
    display_name="Content Embedding",
    description="768-dimensional embedding vector for semantic search.",
    data_type=DataTypeSpec(
        type=DataType.VECTOR,
        vector_dimension=768
    ),
    backing_column="embedding_vector"
)
```

### Mandatory Control Property

```python
markings_property = PropertyDefinition(
    api_name="securityMarkings",
    display_name="Security Markings",
    description="Row-level security markings. Users can only see rows with markings they possess.",
    data_type=DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING)
    ),
    constraints=PropertyConstraints(
        required=True,
        array=ArrayConstraints(unique_items=True)
    ),
    is_mandatory_control=True,
    backing_column="security_markings"
)
```

### Derived Property

```python
full_name_property = PropertyDefinition(
    api_name="fullName",
    display_name="Full Name",
    description="Computed full name from first and last name.",
    data_type=DataTypeSpec(type=DataType.STRING),
    is_derived=True,
    derived_expression="concat(firstName, ' ', lastName)"
)
```

### Edit-Only Property

```python
notes_property = PropertyDefinition(
    api_name="internalNotes",
    display_name="Internal Notes",
    description="User-entered notes not stored in backing dataset.",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(
        string=StringConstraints(max_length=4000)
    ),
    is_edit_only=True
    # Note: backing_column must NOT be set
)
```

---

## API Reference

### to_foundry_dict()

PropertyDefinition을 Palantir Foundry 호환 JSON dictionary로 변환합니다.

```python
def to_foundry_dict(self) -> dict[str, Any]:
    """Export to Foundry-compatible dictionary format."""
```

**Returns**: `dict[str, Any]` - Foundry API 호환 딕셔너리

**Output Fields**:

| Field | Included When |
|-------|---------------|
| `apiName` | Always |
| `displayName` | Always |
| `dataType` | Always |
| `description` | If not None |
| `constraints` | If not None |
| `backingColumn` | If not None |
| `isEditOnly` | If True |
| `isDerived` | If True |
| `derivedExpression` | If `isDerived` and not None |
| `isMandatoryControl` | If True |
| `sharedPropertyRef` | If not None |

**Example**:

```python
prop = PropertyDefinition(
    api_name="email",
    display_name="Email",
    data_type=DataTypeSpec(type=DataType.STRING),
    constraints=PropertyConstraints(
        required=True,
        string=StringConstraints(email_format=True)
    )
)

result = prop.to_foundry_dict()
# {
#     "apiName": "email",
#     "displayName": "Email",
#     "dataType": {"type": "STRING"},
#     "constraints": {"required": true}
# }
```

### from_foundry_dict()

Foundry JSON dictionary에서 PropertyDefinition을 생성합니다.

```python
@classmethod
def from_foundry_dict(cls, data: dict[str, Any]) -> "PropertyDefinition":
    """Create from Foundry JSON format."""
```

**Parameters**:
- `data`: Foundry API 응답 형식의 딕셔너리

**Returns**: `PropertyDefinition` 인스턴스

**Example**:

```python
foundry_data = {
    "apiName": "status",
    "displayName": "Status",
    "dataType": {"type": "STRING"},
    "constraints": {
        "required": True,
        "enum": ["ACTIVE", "INACTIVE", "PENDING"]
    },
    "backingColumn": "status_code"
}

prop = PropertyDefinition.from_foundry_dict(foundry_data)
assert prop.api_name == "status"
assert prop.constraints.enum == ["ACTIVE", "INACTIVE", "PENDING"]
```

### DataTypeSpec Methods

#### to_foundry_dict()

```python
def to_foundry_dict(self) -> dict[str, Any]:
    """Export DataTypeSpec to Foundry format."""
```

**Example**:

```python
dt = DataTypeSpec(
    type=DataType.ARRAY,
    array_item_type=DataTypeSpec(type=DataType.STRING)
)
dt.to_foundry_dict()
# {"type": "ARRAY", "arrayItemType": {"type": "STRING"}}
```

#### from_foundry_dict()

```python
@classmethod
def from_foundry_dict(cls, data: dict[str, Any]) -> "DataTypeSpec":
    """Create DataTypeSpec from Foundry format."""
```

**Handles recursive parsing** for nested types:

```python
data = {
    "type": "STRUCT",
    "structFields": [
        {"name": "x", "type": {"type": "FLOAT"}},
        {"name": "y", "type": {"type": "FLOAT"}}
    ]
}
dt = DataTypeSpec.from_foundry_dict(data)
assert dt.type == DataType.STRUCT
assert len(dt.struct_fields) == 2
```

### PropertyConstraints Methods

#### to_foundry_dict()

```python
def to_foundry_dict(self) -> dict[str, Any]:
    """Export constraints to Foundry format."""
```

**Field Mapping**:

| Python Field | Foundry Field |
|--------------|---------------|
| `numeric.min_value` | `minValue` |
| `numeric.max_value` | `maxValue` |
| `string.min_length` | `minLength` |
| `string.max_length` | `maxLength` |
| `string.pattern` | `pattern` |
| `string.rid_format` | `ridFormat` |
| `string.uuid_format` | `uuidFormat` |
| `array.min_items` | `arrayMinItems` |
| `array.max_items` | `arrayMaxItems` |
| `array.unique_items` | `arrayUnique` |

#### from_foundry_dict()

```python
@classmethod
def from_foundry_dict(cls, data: dict[str, Any]) -> "PropertyConstraints":
    """Create constraints from Foundry format."""
```

**Auto-detects constraint types** based on keys present in data.

---

## Related Types

### PrimaryKeyDefinition

ObjectType의 Primary Key를 정의합니다:

```python
class PrimaryKeyDefinition(BaseModel):
    property_api_name: str      # Reference to property's apiName
    backing_column: Optional[str]  # Dataset column
```

**Example**:

```python
pk = PrimaryKeyDefinition(
    property_api_name="employeeId",
    backing_column="employee_id"
)
```

### StructField

STRUCT 타입 내의 필드를 정의합니다:

```python
class StructField(BaseModel):
    name: str                    # Field name
    data_type: DataTypeSpec      # Field type (alias: "type")
    required: bool = False       # Is required?
    description: Optional[str]   # Documentation
```

---

## Source Files

| File | Description |
|------|-------------|
| `ontology_definition/types/property_def.py` | PropertyDefinition, DataTypeSpec, StructField, PrimaryKeyDefinition |
| `ontology_definition/constraints/property_constraints.py` | PropertyConstraints and type-specific constraints |
| `ontology_definition/core/enums.py` | DataType enum and other enumerations |

---

## See Also

- [ObjectType](./ObjectType.md) - PropertyDefinition을 포함하는 상위 요소
- [LinkType](./LinkType.md) - Foreign Key Property를 사용하는 관계 정의
- [ValueType](./ValueType.md) - 재사용 가능한 커스텀 타입 정의
- [StructType](./StructType.md) - 중첩 구조체 타입 정의
