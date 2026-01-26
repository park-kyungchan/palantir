# /ontology-objecttype - ObjectType Definition Assistant

> **Version:** 1.1.0
> **Model:** opus
> **User-Invocable:** true

---

## 1. Purpose

기존 프로젝트를 **Ontology-Driven-Architecture (ODA)**로 마이그레이션하는 첫 단계:
**"무엇을 ObjectType으로 정의할 것인가?"**를 도출하고 승인받는 Interactive Assistant.

### 핵심 원칙: 실시간 추론 기반 분석

| 원칙 | 설명 |
|------|------|
| **목적** | **Ontology ObjectType을 정확히 정의**하기 위한 분석 |
| **방식** | 미리 정의된 답이 아닌, **매 프롬프트마다 실시간 추론** |
| **범위** | 해당 클래스가 ObjectType인가? DataType은? Cardinality는? |
| **출력** | L1→L2→L3 Progressive Disclosure + 판단 근거 |

> **Note**: Palantir AIP/Foundry를 사용하는 기업들처럼, 각 클래스와 속성을
> **그때그때 조사/분석**하여 ObjectType 정의의 정확성을 높입니다.

---

## 2. Invocation

```bash
# 프로젝트 분석 시작
/ontology-objecttype analyze /home/palantir/my-project

# 특정 파일만 분석
/ontology-objecttype analyze /home/palantir/my-project/models.py

# 이전 분석 이어서 진행
/ontology-objecttype resume <session-id>

# 도움말
/ontology-objecttype help
```

---

## 3. Command Parsing

```python
args = "{user_args}"
command = args.split()[0] if args else "help"

commands = {
    "analyze": "프로젝트/파일 분석하여 ObjectType 후보 도출",
    "resume": "이전 분석 세션 이어서 진행",
    "help": "사용법 안내"
}

if command == "analyze":
    target_path = args.split()[1] if len(args.split()) > 1 else None
    if not target_path:
        # Prompt for path
        pass
    # Start analysis workflow

elif command == "resume":
    session_id = args.split()[1] if len(args.split()) > 1 else None
    # Load session state

elif command == "help":
    # Show usage
    pass
```

---

## 4. Analysis Patterns

### 4.1 Detection Targets

| Pattern | Detection Method | Example |
|---------|-----------------|---------|
| **Python class** | `class ClassName:` | `class Employee:` |
| **SQLAlchemy ORM** | `Base` 또는 `declarative_base()` 상속 | `class User(Base):` |
| **Django ORM** | `models.Model` 상속 | `class Article(models.Model):` |
| **Pydantic** | `BaseModel` 상속 | `class Config(BaseModel):` |

### 4.2 Property Extraction

각 클래스에서 추출하는 정보:

| 항목 | Source | Foundry Mapping |
|------|--------|-----------------|
| **클래스명** | Class definition | `ObjectType.api_name` |
| **필드/속성** | Class attributes | `PropertyDefinition` |
| **타입 힌트** | Type annotations | `DataType` |
| **PK 후보** | `id`, `pk`, `*_id` 패턴 | `primary_key` |
| **FK/관계** | ForeignKey, relationship | `LinkType` 후보 |

### 4.3 Grep Patterns

```python
PATTERNS = {
    "python_class": r"^class\s+([A-Z][a-zA-Z0-9_]*)\s*[:\(]",
    "sqlalchemy": r"class\s+(\w+)\s*\(\s*(?:Base|.*declarative_base)",
    "django": r"class\s+(\w+)\s*\(\s*models\.Model\s*\)",
    "pydantic": r"class\s+(\w+)\s*\(\s*(?:BaseModel|.*BaseModel)",
    "field_def": r"^\s+(\w+)\s*[=:]\s*",
    "type_hint": r":\s*([A-Za-z_][A-Za-z0-9_\[\], ]*)",
    "foreign_key": r"ForeignKey\s*\(\s*['\"]?(\w+)",
    "relationship": r"relationship\s*\(\s*['\"](\w+)"
}
```

---

## 5. Workflow: Phase 1 → 2 → 3 → 4 Interactive Decision Tree

**전환 핵심**: L1→L2→L3 선형 진행 → Phase별 인터랙티브 의사결정 트리

| Phase | 목적 | 사용자 의사결정 | Validation Gate |
|-------|------|----------------|-----------------|
| **Phase 1** | Context Clarification | Source Type, Domain | source_validity |
| **Phase 2** | Entity Discovery | PK Strategy, Properties | candidate_extraction, pk_determinism |
| **Phase 3** | Link Definition | Relationships, Cardinality | link_integrity |
| **Phase 4** | Validation & Output | YAML Generation | semantic_consistency |

---

### 5.1 Phase 1: Context Clarification

**목적**: 분석 소스와 비즈니스 도메인 명확화

```python
# AskUserQuestion을 통한 인터랙티브 질문
result = AskUserQuestion({
    questions: [
        {
            question: "What is your source for this ObjectType definition?",
            header: "Source Type",
            options: [
                {
                    label: "Existing source code",
                    description: "분석할 소스 코드가 있음 (Python, Java, TypeScript 등)"
                },
                {
                    label: "Database schema",
                    description: "데이터베이스 스키마에서 추출 (SQL DDL, ORM models)"
                },
                {
                    label: "Business requirements",
                    description: "비즈니스 요구사항 문서 기반 정의"
                },
                {
                    label: "Manual definition",
                    description: "수동으로 직접 정의 (새로운 도메인 모델)"
                }
            ],
            multiSelect: false
        },
        {
            question: "What is the business domain for this ObjectType?",
            header: "Domain",
            options: [
                { label: "HR & Employee Management", description: "인사/직원 관리" },
                { label: "Finance & Accounting", description: "재무/회계" },
                { label: "Supply Chain & Logistics", description: "공급망/물류" },
                { label: "Customer & Sales", description: "고객/영업" }
            ],
            multiSelect: false
        }
    ]
})

source_type = result["Source Type"]
domain = result["Domain"]
```

**📌 Validation Gate: source_validity**
- IF source == "code" → 파일 경로 접근 가능 여부 확인
- IF source == "schema" → DDL 파싱 가능 여부 확인
- IF source == "manual" → 기본 스키마 템플릿 제공

**Output**:
```
╔═══════════════════════════════════════════╗
║  Phase 1 Complete                         ║
╠═══════════════════════════════════════════╣
║  ✅ Source Type: Existing source code     ║
║  ✅ Domain: HR & Employee Management      ║
║  ✅ Gate: source_validity PASSED          ║
╚═══════════════════════════════════════════╝

→ Proceeding to Phase 2: Entity Discovery
```

---

### 5.2 Phase 2: Entity Discovery

**목적**: Entity 후보 추출 + Primary Key Strategy 결정 + Property 타입 매핑

#### 5.2.1 Entity Candidate Extraction (source == "code"인 경우)

```python
# 코드 스캔으로 Entity 후보 추출
candidates = scan_source_code(source_path, patterns={
    "python_class": r"^class\s+([A-Z][a-zA-Z0-9_]*)\s*[:\(]",
    "sqlalchemy": r"class\s+(\w+)\s*\(\s*(?:Base|.*declarative_base)",
    "django": r"class\s+(\w+)\s*\(\s*models\.Model\s*\)",
    "field_def": r"^\s+(\w+)\s*[=:]\s*",
    "foreign_key": r"ForeignKey\s*\(\s*['\"]?(\w+)"
})

# 실시간 추론: ObjectType 적합 여부 판단
for candidate in candidates:
    is_objecttype = analyze_candidate(candidate)
    # 판단 기준: Entity vs DTO vs Helper vs Config
```

**Output (Candidate List)**:
```
┌───────────────────────────────────────────────┐
│  Found 12 Entity Candidates                   │
├───────────────────────────────────────────────┤
│  ✅ ObjectType 후보 (8개)                      │
│  1. Employee (models/employee.py:15)          │
│     └─ Properties: 6개 | PK candidate: employee_id
│  2. Department (models/department.py:8)       │
│  3. Project (models/project.py:22)            │
│  ...                                          │
│                                               │
│  ⚠️ 검토 필요 (2개) - DTO/Mixin 패턴          │
│  ❌ 제외 추천 (2개) - Helper/Config 클래스    │
└───────────────────────────────────────────────┘

Continue with: 1 (Employee) [Y/n]
```

#### 5.2.2 Primary Key Strategy Selection

**핵심 의사결정**: PK를 어떻게 구성할 것인가?

```python
# AskUserQuestion으로 PK 전략 선택
pk_strategy_result = AskUserQuestion({
    questions: [{
        question: "How should we generate the Primary Key for this ObjectType?",
        header: "PK Strategy",
        options: [
            {
                label: "single_column (단일 컬럼)",
                description: """
                기존 단일 컬럼을 PK로 사용
                ✅ Pros: 단순함, 기존 데이터 활용
                ❌ Cons: 컬럼이 유일성 보장해야 함
                Example: employee_id, user_uuid
                """
            },
            {
                label: "composite (복합 키)",
                description: """
                여러 컬럼을 조합하여 PK 생성 (구분자: '_' or '|')
                ✅ Pros: 자연키 활용, 비즈니스 의미 유지
                ❌ Cons: 조합 순서 중요, 구분자 필요
                Example: company_id + department_id → "ACME_HR"
                """
            },
            {
                label: "composite_hashed (복합 해시)",
                description: """
                복합키를 SHA256 해시로 변환 (고정 길이 64자)
                ✅ Pros: 고정 길이, 충돌 최소화, 긴 조합키 압축
                ❌ Cons: 원본 값 역추적 불가, 디버깅 어려움
                Example: sha256(f"{org}_{dept}_{emp}") → "a3f2c..."
                """
            }
        ],
        multiSelect: false
    }]
})

pk_strategy = pk_strategy_result["PK Strategy"]
```

**Implementation Code Generation**:

```python
# PK Strategy별 코드 생성 (YAML 스키마)
if pk_strategy == "single_column":
    pk_spec = f"""
    primary_key:
      source_columns: ["{pk_column}"]
      strategy: single_column
    """

elif pk_strategy == "composite":
    pk_spec = f"""
    primary_key:
      source_columns: {composite_columns}
      strategy: composite
      composite_spec:
        separator: "_"
        order: {composite_order}
    """

elif pk_strategy == "composite_hashed":
    pk_spec = f"""
    primary_key:
      source_columns: {composite_columns}
      strategy: composite_hashed
      composite_spec:
        hash_algorithm: sha256
        order: {composite_order}
    """
```

**📌 Validation Gate: pk_determinism**
- PK 컬럼이 NOT NULL인가?
- 단일 컬럼인 경우: UNIQUE 제약 존재하는가?
- 복합 컬럼인 경우: 조합이 유일성을 보장하는가?

#### 5.2.3 Property Type Mapping (REQ-003)

**20개 DataType 가이드**:

| Category | Types | Special Config |
|----------|-------|----------------|
| **Primitive** | STRING, INTEGER, LONG, FLOAT, DOUBLE, BOOLEAN, DECIMAL | DECIMAL: precision, scale 필수 |
| **Temporal** | DATE, TIMESTAMP, DATETIME, TIMESERIES | - |
| **Complex** | ARRAY, STRUCT, JSON | ARRAY: arrayItemType 필수<br>STRUCT: structFields 필수 |
| **Spatial** | GEOPOINT, GEOSHAPE | - |
| **Media** | MEDIA_REFERENCE, BINARY, MARKDOWN | - |
| **AI/ML** | VECTOR | vectorDimension 필수 |

**Type Mapping Logic**:

```python
# enums.py 기반 타입 매핑
from ontology_definition.core.enums import DataType

type_mapping = {
    "str": DataType.STRING,
    "int": DataType.INTEGER,
    "float": DataType.FLOAT,
    "bool": DataType.BOOLEAN,
    "datetime.date": DataType.DATE,
    "datetime.datetime": DataType.TIMESTAMP,
    "List[...]": DataType.ARRAY,  # → arrayItemType 추가 설정 필요
    "Dict[...]": DataType.STRUCT,  # → structFields 추가 설정 필요
}

# 실시간 추론으로 최적 타입 결정
for prop in properties:
    suggested_type = infer_best_type(prop)
    # 제약 조건 분석: nullable, unique, default_value
```

**Output**:
```
╔═══════════════════════════════════════════╗
║  Phase 2 Complete: Employee               ║
╠═══════════════════════════════════════════╣
║  ✅ PK Strategy: single_column            ║
║     └─ Column: employee_id (STRING)       ║
║  ✅ Properties: 6개 매핑 완료              ║
║     ├─ employeeId: STRING (PK)            ║
║     ├─ name: STRING (required)            ║
║     ├─ email: STRING (unique)             ║
║     ├─ departmentId: STRING (FK 후보)     ║
║     ├─ hireDate: DATE                     ║
║     └─ isActive: BOOLEAN (default: true)  ║
║  ✅ Gates: candidate_extraction,          ║
║           pk_determinism PASSED           ║
╚═══════════════════════════════════════════╝

→ Proceeding to Phase 3: Link Definition
```

---

### 5.3 Phase 3: Link Definition

**목적**: Relationship 존재 여부 확인 + Cardinality 결정 + LinkType 정의

#### 5.3.1 Relationship Detection

```python
# FK 패턴 자동 탐지
fk_candidates = detect_foreign_keys(properties, patterns={
    "sqlalchemy": r"ForeignKey\s*\(\s*['\"]?(\w+)",
    "naming": r"(\w+)_id$",  # department_id → Department
    "relationship": r"relationship\s*\(\s*['\"](\w+)"
})

# 사용자에게 관계 확인 질문
has_relationship = AskUserQuestion({
    questions: [{
        question: "Does this ObjectType have relationships to other ObjectTypes?",
        header: "Relationships",
        options: [
            { label: "Yes, define relationships now", description: "관계 정의 진행" },
            { label: "No relationships", description: "독립적인 ObjectType" },
            { label: "Skip for now", description: "나중에 정의" }
        ],
        multiSelect: false
    }]
})
```

#### 5.3.2 Cardinality Decision Tree

**핵심 의사결정**: 관계의 Cardinality는?

```python
# 각 FK 후보에 대해 Cardinality 질문
for fk in fk_candidates:
    cardinality_result = AskUserQuestion({
        questions: [{
            question: f"What is the cardinality for {source_obj} → {target_obj}?",
            header: "Cardinality",
            options: [
                {
                    label: "ONE_TO_ONE (1:1)",
                    description: """
                    한 Employee는 하나의 Badge에 대응, Badge도 하나의 Employee에만 연결
                    Implementation: FK on either side
                    """
                },
                {
                    label: "ONE_TO_MANY (1:N)",
                    description: """
                    한 Department는 여러 Employee를 가질 수 있음
                    Implementation: FK on 'many' side (Employee.departmentId)
                    """
                },
                {
                    label: "MANY_TO_ONE (N:1)",
                    description: """
                    여러 Employee가 하나의 Department에 소속
                    Implementation: FK on 'many' side (this ObjectType)
                    """
                },
                {
                    label: "MANY_TO_MANY (N:N)",
                    description: """
                    Employee ↔ Project 관계: 한 직원이 여러 프로젝트, 한 프로젝트에 여러 직원
                    Implementation: JOIN TABLE required (EmployeeProject)
                    """
                }
            ],
            multiSelect: false
        }]
    })

    cardinality = cardinality_result["Cardinality"]
```

**Cardinality별 구현 전략**:

| Cardinality | FK 위치 | Backing Table | Example |
|-------------|---------|---------------|---------|
| ONE_TO_ONE | Either side | No | Employee ↔ Badge |
| ONE_TO_MANY | "Many" side | No | Department(1) → Employee(N) |
| MANY_TO_ONE | "Many" side (this) | No | Employee(N) → Department(1) |
| MANY_TO_MANY | - | **Yes** | Employee ↔ Project |

**📌 Validation Gate: link_integrity**
- Target ObjectType이 존재하는가?
- FK 컬럼 타입이 Target PK 타입과 일치하는가?
- MANY_TO_MANY인 경우: Backing Table 자동 생성 제안

**Output**:
```
╔═══════════════════════════════════════════╗
║  Phase 3 Complete: Relationships          ║
╠═══════════════════════════════════════════╣
║  🔗 LinkType 1: EmployeeToDepartment      ║
║     ├─ Source: Employee                   ║
║     ├─ Target: Department                 ║
║     ├─ Cardinality: MANY_TO_ONE (N:1)     ║
║     ├─ FK: departmentId (on Employee)     ║
║     └─ Implementation: FOREIGN_KEY        ║
║                                           ║
║  ✅ Gate: link_integrity PASSED           ║
╚═══════════════════════════════════════════╝

→ Proceeding to Phase 4: Validation & Output
```

---

### 5.4 Phase 4: Validation & Output

**목적**: 모든 Gate 검증 + YAML 생성 + 승인 워크플로우

#### 5.4.1 Final Validation (semantic_consistency)

```python
# 모든 Validation Gate 실행
validation_results = {
    "source_validity": validate_source(source_type, source_path),
    "candidate_extraction": validate_entity_candidates(candidates),
    "pk_determinism": validate_primary_key(pk_strategy, pk_columns),
    "link_integrity": validate_relationships(links)
}

all_passed = all(validation_results.values())
```

#### 5.4.2 YAML Output Generation (Python → YAML 변경)

**Output Format**: `objecttype-{api_name}.yaml`

```yaml
# objecttype-Employee.yaml
api_name: Employee
display_name: Employee
description: "Employee entity with department relationship"
status: DRAFT

primary_key:
  source_columns:
    - employee_id
  strategy: single_column

properties:
  - api_name: employeeId
    display_name: Employee ID
    data_type: STRING
    required: true

  - api_name: name
    display_name: Name
    data_type: STRING
    required: true

  - api_name: email
    display_name: Email
    data_type: STRING
    constraints:
      unique: true

  - api_name: departmentId
    display_name: Department
    data_type: STRING
    # LinkType로 변환 예정

  - api_name: hireDate
    display_name: Hire Date
    data_type: DATE

  - api_name: isActive
    display_name: Active Status
    data_type: BOOLEAN
    default_value: true

links:
  - link_type_name: EmployeeToDepartment
    target_object_type: Department
    cardinality: MANY_TO_ONE
    foreign_key:
      source_property: departmentId
      target_property: departmentId

validation_gates:
  - source_validity: PASSED
  - candidate_extraction: PASSED
  - pk_determinism: PASSED
  - link_integrity: PASSED
  - semantic_consistency: PASSED
```

#### 5.4.3 Approval Workflow

```python
# 최종 승인 질문
approval = AskUserQuestion({
    questions: [{
        question: "Review the generated ObjectType definition. Proceed?",
        header: "Approval",
        options: [
            { label: "Approve", description: "정의 승인 및 저장" },
            { label: "Edit", description: "YAML 직접 수정" },
            { label: "Regenerate", description: "Phase 2부터 다시 시작" },
            { label: "Cancel", description: "작업 취소" }
        ],
        multiSelect: false
    }]
})

if approval["Approval"] == "Approve":
    save_yaml(output_path)
    print("✅ ObjectType definition saved to:", output_path)
```

**Final Output**:
```
╔═══════════════════════════════════════════╗
║  Phase 4 Complete: ObjectType Defined     ║
╠═══════════════════════════════════════════╣
║  📄 Output File:                          ║
║     objecttype-Employee.yaml              ║
║                                           ║
║  ✅ All Validation Gates: PASSED          ║
║  ✅ PK Strategy: single_column            ║
║  ✅ Properties: 6개 정의 완료              ║
║  ✅ Links: 1개 정의 완료                  ║
║                                           ║
║  Next Steps:                              ║
║  → Review YAML file                       ║
║  → Define LinkType separately (/ontology-linktype)
║  → Generate PySpark pipeline (optional)   ║
╚═══════════════════════════════════════════╝
```

---

## 5.5 Validation Gate 규칙 정의 (CRITICAL)

**목적**: 각 Phase 종료 시 Ontology Integrity 검증을 통해 문제를 조기 발견 (Shift-Left)

### 5.5.1 Gate 개요

```yaml
# validation-gates.yaml
# Generated by: Task #3 (Validation Gate 규칙 정의)
# Date: 2026-01-26

validation_gates:
  # ═══════════════════════════════════════════════════════════════
  # Gate 1: source_validity (Phase 1 완료 시 실행)
  # ═══════════════════════════════════════════════════════════════
  - name: source_validity
    phase: phase_1_context
    type: automated
    description: "분석 소스와 도메인 컨텍스트의 유효성 검증"
    rules:
      - id: SV-001
        expr: "has(input.source_paths) && size(input.source_paths) > 0"
        message: "At least one source path required"
        message_ko: "최소 하나의 소스 경로가 필요합니다"
        severity: ERROR

      - id: SV-002
        expr: "input.source_paths.all(p, p.startsWith('/') || p.startsWith('.'))"
        message: "All source paths must be valid absolute or relative paths"
        message_ko: "모든 소스 경로는 유효한 절대 또는 상대 경로여야 합니다"
        severity: ERROR

      - id: SV-003
        expr: "input.domain_context != '' && size(input.domain_context) >= 3"
        message: "Domain context must be provided (min 3 characters)"
        message_ko: "도메인 컨텍스트를 제공해야 합니다 (최소 3자)"
        severity: ERROR

      - id: SV-004
        expr: "input.source_type in ['code', 'schema', 'requirements', 'manual']"
        message: "Source type must be one of: code, schema, requirements, manual"
        message_ko: "소스 타입은 code, schema, requirements, manual 중 하나여야 합니다"
        severity: ERROR

  # ═══════════════════════════════════════════════════════════════
  # Gate 2: candidate_extraction (Phase 2 시작 시 실행)
  # ═══════════════════════════════════════════════════════════════
  - name: candidate_extraction
    phase: phase_2_entity
    type: automated
    description: "Entity 후보 추출의 완전성 및 유효성 검증"
    rules:
      - id: CE-001
        expr: "size(candidates.entities) >= 1"
        message: "At least one entity candidate must be identified"
        message_ko: "최소 하나의 엔티티 후보가 식별되어야 합니다"
        severity: ERROR

      - id: CE-002
        expr: "candidates.entities.all(e, has(e.class_name) && e.class_name != '')"
        message: "All entity candidates must have a class name"
        message_ko: "모든 엔티티 후보에는 클래스 이름이 있어야 합니다"
        severity: ERROR

      - id: CE-003
        expr: "candidates.entities.all(e, has(e.primary_key_candidate))"
        message: "All entities must have primary key candidates"
        message_ko: "모든 엔티티에 기본 키 후보가 있어야 합니다"
        severity: WARNING  # 경고: 수동 지정 허용

      - id: CE-004
        expr: "candidates.entities.all(e, size(e.properties) >= 1)"
        message: "All entities must have at least one property"
        message_ko: "모든 엔티티에는 최소 하나의 속성이 있어야 합니다"
        severity: ERROR

  # ═══════════════════════════════════════════════════════════════
  # Gate 3: pk_determinism (Phase 2 PK 선택 후 실행)
  # ═══════════════════════════════════════════════════════════════
  - name: pk_determinism
    phase: phase_2_entity
    type: automated
    description: "Primary Key의 Immutability와 Determinism 검증"
    rules:
      - id: PK-001
        expr: "spec.primaryKey.strategy != '' && spec.primaryKey.propertyId != ''"
        message: "Primary key strategy and property must be defined"
        message_ko: "기본 키 전략과 속성이 정의되어야 합니다"
        severity: ERROR

      - id: PK-002
        expr: "spec.primaryKey.strategy in ['single_column', 'composite', 'composite_hashed']"
        message: "Primary key strategy must be one of: single_column, composite, composite_hashed"
        message_ko: "기본 키 전략은 single_column, composite, composite_hashed 중 하나여야 합니다"
        severity: ERROR

      - id: PK-003
        expr: "!spec.properties.exists(p, p.id == spec.primaryKey.propertyId && p.dataType != 'STRING')"
        message: "Primary key must be STRING type for immutability and determinism"
        message_ko: "기본 키는 불변성과 결정성을 위해 STRING 타입이어야 합니다"
        severity: ERROR

      - id: PK-004
        expr: "spec.properties.filter(p, p.id == spec.primaryKey.propertyId)[0].required == true"
        message: "Primary key property must be required (non-null)"
        message_ko: "기본 키 속성은 필수(non-null)여야 합니다"
        severity: ERROR

      - id: PK-005
        expr: "spec.primaryKey.strategy != 'composite' || (has(spec.primaryKey.compositeSpec) && size(spec.primaryKey.compositeSpec.columns) >= 2)"
        message: "Composite key requires at least 2 columns"
        message_ko: "복합 키는 최소 2개 컬럼이 필요합니다"
        severity: ERROR

      - id: PK-006
        expr: "spec.primaryKey.strategy != 'composite_hashed' || (has(spec.primaryKey.compositeSpec) && spec.primaryKey.compositeSpec.hashAlgorithm == 'sha256')"
        message: "Composite hashed key must use SHA256 algorithm"
        message_ko: "복합 해시 키는 SHA256 알고리즘을 사용해야 합니다"
        severity: ERROR

  # ═══════════════════════════════════════════════════════════════
  # Gate 4: link_integrity (Phase 3 완료 시 실행)
  # ═══════════════════════════════════════════════════════════════
  - name: link_integrity
    phase: phase_3_link
    type: automated
    description: "LinkType 정의의 참조 무결성 검증"
    rules:
      - id: LI-001
        expr: "spec.links.all(l, l.cardinality != 'MANY_TO_MANY' || has(l.joinTable))"
        message: "Many-to-many links require join table configuration"
        message_ko: "다대다(M:N) 링크에는 조인 테이블 구성이 필요합니다"
        severity: ERROR

      - id: LI-002
        expr: "spec.links.all(l, l.cardinality == 'MANY_TO_MANY' || has(l.foreignKeyProperty))"
        message: "Non-M:N links require foreign key property specification"
        message_ko: "다대다가 아닌 링크에는 외래 키 속성 지정이 필요합니다"
        severity: ERROR

      - id: LI-003
        expr: "spec.links.all(l, l.targetObjectType != '' && l.targetObjectType != spec.apiName)"
        message: "Link target must be a different valid ObjectType"
        message_ko: "링크 대상은 유효한 다른 ObjectType이어야 합니다"
        severity: ERROR

      - id: LI-004
        expr: "spec.links.all(l, l.cardinality in ['ONE_TO_ONE', 'ONE_TO_MANY', 'MANY_TO_ONE', 'MANY_TO_MANY'])"
        message: "Link cardinality must be valid"
        message_ko: "링크 카디널리티는 유효한 값이어야 합니다"
        severity: ERROR

      - id: LI-005
        expr: "spec.links.all(l, l.cardinality != 'MANY_TO_MANY' || (has(l.joinTable.sourceColumn) && has(l.joinTable.targetColumn)))"
        message: "M:N join table must specify source and target columns"
        message_ko: "M:N 조인 테이블은 소스 및 대상 컬럼을 지정해야 합니다"
        severity: ERROR

  # ═══════════════════════════════════════════════════════════════
  # Gate 5: semantic_consistency (Phase 4 최종 검증)
  # ═══════════════════════════════════════════════════════════════
  - name: semantic_consistency
    phase: phase_4_output
    type: manual  # 자동 + 수동 체크리스트
    description: "의미론적 일관성 및 비즈니스 규칙 정합성 최종 검증"
    approvers: ["ontology-steward", "domain-expert"]
    timeout: "24h"

    # 자동 검증 규칙
    automated_rules:
      - id: SC-001
        expr: "spec.apiName.matches('^[A-Z][a-zA-Z0-9]*$')"
        message: "API name must be PascalCase"
        message_ko: "API 이름은 PascalCase여야 합니다"
        severity: ERROR

      - id: SC-002
        expr: "spec.displayName != '' && size(spec.displayName) >= 2"
        message: "Display name is required"
        message_ko: "표시 이름은 필수입니다"
        severity: ERROR

      - id: SC-003
        expr: "spec.properties.all(p, p.apiName.matches('^[a-z][a-zA-Z0-9]*$'))"
        message: "Property API names must be camelCase"
        message_ko: "속성 API 이름은 camelCase여야 합니다"
        severity: WARNING

      - id: SC-004
        expr: "spec.properties.all(p, p.dataType in VALID_DATA_TYPES)"
        message: "All properties must have valid data types"
        message_ko: "모든 속성은 유효한 데이터 타입을 가져야 합니다"
        severity: ERROR

    # 수동 체크리스트 (human review required)
    manual_checklist:
      - id: MC-001
        description: "ObjectType이 자연어 비즈니스 개념에 매핑되는가?"
        description_ko: "ObjectType이 자연어 비즈니스 개념에 매핑되는가?"

      - id: MC-002
        description: "Primary Key가 결정적(deterministic)이고 불변(immutable)인가?"
        description_ko: "Primary Key가 결정적이고 불변인가?"

      - id: MC-003
        description: "의미 있는 모든 관계가 LinkType으로 모델링되었는가?"
        description_ko: "의미 있는 모든 관계가 LinkType으로 모델링되었는가?"

      - id: MC-004
        description: "속성들이 적절한 데이터 타입을 사용하는가?"
        description_ko: "속성들이 적절한 데이터 타입을 사용하는가?"

      - id: MC-005
        description: "비즈니스 도메인의 제약 조건이 정확히 반영되었는가?"
        description_ko: "비즈니스 도메인의 제약 조건이 정확히 반영되었는가?"

# 유효한 DataType 목록 (Gate SC-004 참조)
VALID_DATA_TYPES:
  primitive:
    - STRING
    - INTEGER
    - LONG
    - FLOAT
    - DOUBLE
    - BOOLEAN
    - DECIMAL
  temporal:
    - DATE
    - TIMESTAMP
    - DATETIME
    - TIMESERIES
  complex:
    - ARRAY
    - STRUCT
    - JSON
  spatial:
    - GEOPOINT
    - GEOSHAPE
  media:
    - MEDIA_REFERENCE
    - BINARY
    - MARKDOWN
  ai_ml:
    - VECTOR
```

### 5.5.2 Gate 실행 프로토콜

```python
async def execute_validation_gate(gate_name: str, context: dict) -> ValidationResult:
    """
    Validation Gate 실행 및 결과 반환

    Args:
        gate_name: 실행할 Gate 이름
        context: 검증 대상 데이터 (spec, candidates 등)

    Returns:
        ValidationResult: passed/failed + 상세 메시지
    """

    GATES = load_validation_gates()
    gate = GATES[gate_name]

    results = []
    for rule in gate.rules:
        try:
            passed = evaluate_cel_expression(rule.expr, context)
            if not passed:
                results.append(RuleResult(
                    rule_id=rule.id,
                    passed=False,
                    message=rule.message_ko,  # 한국어 우선
                    severity=rule.severity
                ))
        except Exception as e:
            results.append(RuleResult(
                rule_id=rule.id,
                passed=False,
                message=f"규칙 평가 오류: {str(e)}",
                severity="ERROR"
            ))

    # ERROR 심각도가 하나라도 있으면 Gate 실패
    has_errors = any(r.severity == "ERROR" and not r.passed for r in results)

    return ValidationResult(
        gate_name=gate_name,
        passed=not has_errors,
        results=results,
        timestamp=datetime.now().isoformat()
    )
```

### 5.5.3 Gate 실패 시 처리

```python
async def handle_gate_failure(gate_result: ValidationResult, phase: str):
    """
    Gate 실패 시 사용자에게 명확한 오류 메시지와 해결 방안 제시
    """

    failed_rules = [r for r in gate_result.results if not r.passed]

    output = f"""
╔══════════════════════════════════════════════════════════════╗
║  ❌ Validation Gate 실패: {gate_result.gate_name}
╠══════════════════════════════════════════════════════════════╣
║  Phase: {phase}
║  실패 규칙: {len(failed_rules)}개
║
"""

    for rule in failed_rules:
        severity_icon = "🚫" if rule.severity == "ERROR" else "⚠️"
        output += f"""
║  {severity_icon} [{rule.rule_id}] {rule.severity}
║     메시지: {rule.message}
"""

    output += """
╠══════════════════════════════════════════════════════════════╣
║  💡 해결 방법:
"""

    # Gate별 해결 방안 제시
    if gate_result.gate_name == "source_validity":
        output += """
║     1. 소스 경로가 올바른지 확인하세요
║     2. 도메인 컨텍스트를 명확히 입력하세요
║     3. 소스 타입을 선택하세요 (code/schema/requirements/manual)
"""
    elif gate_result.gate_name == "pk_determinism":
        output += """
║     1. Primary Key를 STRING 타입으로 변경하세요
║     2. PK 속성을 required=true로 설정하세요
║     3. 복합 키 사용 시 최소 2개 컬럼을 지정하세요
"""
    elif gate_result.gate_name == "link_integrity":
        output += """
║     1. MANY_TO_MANY 관계에 조인 테이블을 정의하세요
║     2. 외래 키 속성을 명시하세요
║     3. 유효한 대상 ObjectType을 지정하세요
"""

    output += """
╚══════════════════════════════════════════════════════════════╝

다시 시도하시겠습니까? [Y/n]
"""

    print(output)

    # 사용자 선택 대기
    user_choice = await AskUserQuestion({
        "questions": [{
            "question": "Gate 실패를 해결하시겠습니까?",
            "header": "Action",
            "options": [
                {"label": "수정 후 재검증", "description": "문제를 수정하고 Gate를 다시 실행"},
                {"label": "무시하고 진행", "description": "경고만 있는 경우 진행 (ERROR 시 불가)"},
                {"label": "이전 Phase로", "description": "이전 단계로 돌아가기"},
                {"label": "작업 취소", "description": "전체 작업 중단"}
            ],
            "multiSelect": False
        }]
    })

    return user_choice
```

### 5.5.4 Phase-Gate 매핑 요약

| Phase | Gate | 검증 시점 | 실패 시 동작 |
|-------|------|----------|-------------|
| **Phase 1** | `source_validity` | Context 수집 완료 후 | Phase 1 재시작 |
| **Phase 2** | `candidate_extraction` | Entity 스캔 완료 후 | 소스 재분석 또는 수동 입력 |
| **Phase 2** | `pk_determinism` | PK 전략 선택 후 | PK 전략 재선택 |
| **Phase 3** | `link_integrity` | 관계 정의 완료 후 | 관계 재정의 |
| **Phase 4** | `semantic_consistency` | YAML 생성 전 | 수동 검토 + 자동 검증 |

### 5.5.5 Gate 통과 출력 형식

```
╔══════════════════════════════════════════════════════════════╗
║  ✅ Validation Gate 통과: pk_determinism                     ║
╠══════════════════════════════════════════════════════════════╣
║  Phase: phase_2_entity                                       ║
║  검증 규칙: 6개 모두 통과                                     ║
║                                                              ║
║  ✅ [PK-001] Primary key strategy defined                    ║
║  ✅ [PK-002] Valid strategy: single_column                   ║
║  ✅ [PK-003] PK type: STRING ✓                               ║
║  ✅ [PK-004] PK required: true ✓                             ║
║  ✅ [PK-005] N/A (not composite)                             ║
║  ✅ [PK-006] N/A (not composite_hashed)                      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

→ Proceeding to Phase 3: Link Definition
```

---

## 6. 실시간 추론 프로토콜

### 6.0 참조 체계 (CRITICAL)

```
┌─────────────────────────────────────────────────────────────┐
│  실시간 추론 참조 체계                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📘 ontology-definition 패키지                               │
│     /home/palantir/park-kyungchan/palantir/Ontology-Definition
│     ├── ontology_definition/types/    # 타입 정의           │
│     ├── ontology_definition/core/     # Enum, Base 클래스   │
│     └── tests/                        # 사용 예제           │
│                                                             │
│     🎯 목적: "어떻게 정의하는가" (구문, 구조, 타입)          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🌐 외부 검증된 자료 (항상 참조)                             │
│     ├── Context7 (MCP) - Palantir 공식 문서                 │
│     ├── Tavily (MCP, 차후 설치) - 검증된 기술 자료          │
│     ├── WebFetch - 특정 URL 직접 참조                       │
│     └── WebSearch - 실제 AIP/Foundry 사용 기업 사례         │
│                                                             │
│     🎯 목적: "왜 이렇게 정의해야 하는가"                     │
│        - 실제 기업의 ObjectType 정의 사례                   │
│        - 이 정의의 장점/단점 분석                           │
│        - ODA 전체 관점에서의 영향 분석                      │
│        - 결정하는데 도움 제공                               │
│                                                             │
│     ⚠️ 검증된 자료 기준 (MUST):                             │
│        아래 출처만 신뢰하고, 그 외는 참조하지 않음          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

#### 6.0.0 공신력 있는 검증된 자료 기준 (CRITICAL)

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ 신뢰할 수 있는 출처 (ONLY THESE)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ Palantir 공식 자료                                      │
│     ├── palantir.com/docs/*                                 │
│     ├── palantir.com/platforms/*                            │
│     ├── Palantir GitHub (github.com/palantir/*)             │
│     └── Palantir 공식 블로그/발표 자료                      │
│                                                             │
│  2️⃣ 공식 기술 문서                                          │
│     ├── Foundry 공식 문서                                   │
│     ├── AIP 공식 문서                                       │
│     └── Ontology SDK 문서                                   │
│                                                             │
│  3️⃣ 검증된 기업 사례 (공식 발표만)                          │
│     ├── Palantir 고객 사례 연구 (Case Studies)              │
│     ├── 기업 공식 기술 블로그 (engineering.*.com)           │
│     ├── 컨퍼런스 발표 자료 (FoundryCon, etc.)               │
│     └── 학술 논문 / 백서                                    │
│                                                             │
│  4️⃣ 신뢰할 수 있는 기술 플랫폼                              │
│     ├── Stack Overflow (높은 투표 수 답변)                  │
│     ├── GitHub Discussions (공식 저장소)                    │
│     └── 공식 커뮤니티 포럼                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  ❌ 참조 금지 (DO NOT USE)                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  • 개인 블로그 (검증되지 않은 의견)                         │
│  • Medium 일반 글 (공식 계정 제외)                          │
│  • 비공식 튜토리얼                                          │
│  • Reddit/Twitter 등 SNS (공식 계정 제외)                   │
│  • 출처 불명의 자료                                         │
│  • AI 생성 콘텐츠 (검증되지 않은)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 6.0.0.1 자료 검증 프로토콜

```python
async def verify_source_credibility(source_url):
    """
    자료 출처의 공신력을 검증한다.
    검증되지 않은 자료는 사용하지 않는다.
    """

    TRUSTED_DOMAINS = [
        "palantir.com",
        "github.com/palantir",
        "foundry.palantir.com",
        # 기업 공식 기술 블로그
        "engineering.*.com",
        "tech.*.com",
        # 학술/공식
        "arxiv.org",
        "acm.org",
        "ieee.org",
    ]

    TRUSTED_PATTERNS = [
        r"palantir\.com/docs/",
        r"palantir\.com/platforms/",
        r"github\.com/palantir/",
        r"/case-study/",
        r"/customer-stories/",
    ]

    # 1. 도메인 검증
    if not any(domain in source_url for domain in TRUSTED_DOMAINS):
        return SourceVerification(
            trusted=False,
            reason="도메인이 신뢰할 수 있는 목록에 없음"
        )

    # 2. 패턴 검증
    if not any(re.match(pattern, source_url) for pattern in TRUSTED_PATTERNS):
        return SourceVerification(
            trusted=False,
            reason="URL 패턴이 공식 자료 형식이 아님"
        )

    return SourceVerification(trusted=True)
```
```

#### 6.0.1 ontology-definition 참조

```python
# "어떻게 정의하는가" - 구문/구조 참조
DEFINITION_REFERENCES = [
    # 타입 정의
    "ontology_definition/types/object_type.py",      # ObjectType 구조
    "ontology_definition/types/property_def.py",     # PropertyDefinition
    "ontology_definition/types/link_type.py",        # LinkType (관계 분석 시)

    # Enum 정의 (DataType, Cardinality 등)
    "ontology_definition/core/enums.py",

    # 사용 예제
    "tests/test_object_type.py",
    "tests/test_automation.py",
]
```

#### 6.0.2 외부 자료 참조 (항상)

```python
# "왜 이렇게 정의해야 하는가" - 실제 사례 + 장단점 분석
async def enrich_with_real_world_context(object_type_candidate):
    """
    각 ObjectType 후보에 대해 실제 사례와 장단점을 분석하여
    사용자의 결정을 돕는다.
    """

    # 1. 실제 기업 사례 검색
    examples = await search_real_world_examples(
        object_type_name=object_type_candidate.name,
        domain=object_type_candidate.domain
    )

    # 2. 이 정의 방식의 장단점 분석
    pros_cons = await analyze_definition_tradeoffs(
        object_type_candidate,
        oda_perspective=True  # ODA 전체 관점
    )

    # 3. 결정 지원 정보 구성
    return DecisionSupport(
        examples=examples,
        pros=pros_cons.advantages,
        cons=pros_cons.disadvantages,
        oda_impact=pros_cons.oda_wide_impact,
        recommendation=pros_cons.recommendation
    )
```

#### 6.0.3 결정 지원 출력 형식

```
┌─ Employee ObjectType 정의 결정 지원 ────────────────────────┐
│                                                             │
│  📘 정의 방법 (ontology-definition 기준):                   │
│     ObjectType(api_name="Employee", ...)                    │
│                                                             │
│  🌐 실제 기업 사례:                                         │
│     [사례 1] 금융사: Employee를 Person의 하위 타입으로      │
│       정의하여 고객/직원 통합 관리                          │
│       🔗 https://palantir.com/case-studies/...              │
│                                                             │
│     [사례 2] 제조사: Employee에 조직도 Link 포함하여        │
│       계층 구조 탐색 최적화                                 │
│       🔗 https://foundrycon.palantir.com/2025/...           │
│                                                             │
│  ✅ 장점:                                                   │
│     - 독립 ObjectType으로 CRUD 단순화                       │
│     - Department와 MANY_TO_ONE Link로 조직 탐색 용이        │
│                                                             │
│  ⚠️ 단점/고려사항:                                          │
│     - 직원 수 많을 시 ObjectSet 쿼리 성능 고려 필요         │
│     - 퇴사자 처리: isActive vs 별도 ArchiveEmployee 검토    │
│                                                             │
│  🔄 ODA 전체 관점:                                          │
│     - ActionType: CreateEmployee, UpdateEmployee 필요       │
│     - LinkType: EmployeeToDepartment, EmployeeToProject     │
│     - Automation: 입사일 기준 온보딩 자동화 가능            │
│                                                             │
│  💡 권장사항:                                                │
│     현재 정의 방식 적합. 단, isActive 필드 대신             │
│     employmentStatus (ACTIVE/TERMINATED/ON_LEAVE) Enum      │
│     사용 시 더 유연한 상태 관리 가능.                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **MUST**: 실제 기업 사례 제공 시 **출처 URL 필수 포함**.
> URL이 없는 사례는 제공하지 않음.

### 6.1 분석 시 판단해야 할 질문들

각 클래스/속성을 분석할 때 **실시간으로 추론**하여 답변:

| 판단 항목 | 추론 질문 |
|----------|----------|
| **ObjectType 적합성** | 이 클래스가 비즈니스 도메인의 핵심 엔티티인가? |
| **Primary Key** | 어떤 속성이 PK로 적합한가? 그 근거는? |
| **DataType 매핑** | Python 타입 → Foundry DataType 매핑이 정확한가? |
| **Required 여부** | nullable=False인 필드가 실제로 required인가? |
| **Relationship** | FK가 어떤 Cardinality를 나타내는가? |
| **제외 판단** | Helper/DTO/Mixin인가? 왜 ObjectType이 아닌가? |

### 6.2 추론 출력 형식

```
┌─ 분석: Employee 클래스 ─────────────────────────────────────┐
│                                                             │
│  Q: 이 클래스가 ObjectType으로 적합한가?                    │
│  A: ✅ 적합함                                               │
│     - 근거 1: 비즈니스 도메인의 핵심 엔티티 (직원)          │
│     - 근거 2: 고유 식별자(employee_id) 보유                 │
│     - 근거 3: 독립적인 생명주기 (CRUD 대상)                 │
│                                                             │
│  Q: department_id는 어떤 관계를 나타내는가?                 │
│  A: MANY_TO_ONE (Employee → Department)                     │
│     - 근거: 한 부서에 여러 직원, 직원은 하나의 부서 소속    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Interactive Q&A (`?` 명령)

사용자가 `?`를 입력하면 **해당 맥락에서 실시간 추론**으로 응답.

**"왜?" 질문은 `/ontology-why` 헬퍼 스킬 호출:**

```python
async def handle_question(question, context):
    """
    사용자 질문 처리
    - "왜" 관련 → /ontology-why 헬퍼 호출
    - 그 외 → 실시간 추론
    """
    WHY_PATTERNS = [r"왜\s+", r"이유", r"근거", r"어째서", r"why\s+"]

    if any(re.search(p, question, re.I) for p in WHY_PATTERNS):
        # /ontology-why 헬퍼 호출 (Ontology Integrity 관점 설명)
        return await invoke_skill("ontology-why", {
            "question": question,
            "context": context,
            "type": "ObjectType"
        })

    # 그 외 질문: 실시간 추론
    return await realtime_analysis(question, context)
```

**예시 1: 일반 질문 (실시간 추론)**
```
> ? 이 email 필드가 unique여야 하나요?

[실시간 분석]
현재 코드: email = Column(String, unique=True)

분석 결과:
- 현재 DB 스키마에서 unique=True로 설정됨
- 비즈니스 규칙상 직원 이메일은 고유해야 함

권장: unique=True 유지
```

**예시 2: "왜" 질문 (/ontology-why 호출)**
```
> ? employeeId를 왜 String으로 정의했어?

[/ontology-why 헬퍼 호출]
╔══════════════════════════════════════════════════════════════╗
║  🔍 Ontology Integrity 분석: employeeId                      ║
╠══════════════════════════════════════════════════════════════╣
║  📐 설계 원칙:                                               ║
║  1. Immutability (불변성) - PK는 변경 불가해야 함            ║
║  2. Determinism (결정성) - 동일 입력 → 동일 PK               ║
║  3. Referential Integrity - Link 참조 무결성 보장            ║
║                                                              ║
║  📚 Palantir 공식 근거:                                      ║
║  "Primary keys should be deterministic..."                   ║
║  🔗 https://www.palantir.com/docs/foundry/...                ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 7. Approval Workflow (Phase-Aware)

### 7.1 Phase Progress Tracking

| Phase | Status | Actions Available |
|-------|--------|-------------------|
| **Phase 1** | `completed` | `continue`, `restart` |
| **Phase 2** | `in_progress` | `approve entity`, `edit pk`, `regenerate` |
| **Phase 3** | `pending` | `add link`, `skip`, `next` |
| **Phase 4** | `pending` | `approve`, `edit yaml`, `cancel` |

### 7.2 Session State (Phase-Based)

```json
{
  "session_id": "obj-a1b2c3",
  "target_path": "/home/palantir/my-project",
  "current_phase": "phase_2_entity",
  "phase_results": {
    "phase_1_context": {
      "source_type": "Existing source code",
      "domain": "HR & Employee Management",
      "status": "completed",
      "timestamp": "2026-01-26T11:00:00Z"
    },
    "phase_2_entity": {
      "entity_name": "Employee",
      "pk_strategy": "single_column",
      "pk_column": "employee_id",
      "properties": [
        {
          "api_name": "employeeId",
          "data_type": "STRING",
          "required": true,
          "is_pk": true
        },
        {
          "api_name": "name",
          "data_type": "STRING",
          "required": true
        }
      ],
      "status": "in_progress",
      "validation_gates": {
        "candidate_extraction": "passed",
        "pk_determinism": "passed"
      }
    },
    "phase_3_link": {
      "status": "pending"
    },
    "phase_4_output": {
      "status": "pending"
    }
  },
  "timestamp": "2026-01-26T11:30:00Z"
}
```

### 7.3 Phase Commands

#### Phase 2 Commands

| Command | Description |
|---------|-------------|
| `approve entity` | Entity 정의 승인, Phase 3로 진행 |
| `edit pk <strategy>` | PK 전략 재선택 (single_column/composite/composite_hashed) |
| `edit property <name>` | 특정 Property 수정 |
| `add property` | Property 추가 |
| `regenerate` | Phase 2 다시 시작 |

#### Phase 3 Commands

| Command | Description |
|---------|-------------|
| `add link` | 새 LinkType 추가 |
| `edit link <name>` | 기존 LinkType 수정 |
| `delete link <name>` | LinkType 제거 |
| `skip` | Link 정의 건너뛰기 (나중에 정의) |
| `next` | Phase 4로 진행 |

#### Phase 4 Commands

| Command | Description |
|---------|-------------|
| `approve` | YAML 승인 및 저장 |
| `edit yaml` | YAML 직접 수정 모드 |
| `preview` | YAML 미리보기 |
| `cancel` | 전체 작업 취소 |
| `back` | 이전 Phase로 돌아가기 |

---

## 8. Output Generation (YAML Format)

**핵심 변경**: Python 코드 생성 → YAML 스키마 생성

### 8.1 YAML Output Generation

```python
async def generate_yaml_output(phase_results):
    """Phase 4에서 최종 YAML 생성"""

    # 1. ObjectType YAML 생성
    objecttype_yaml = generate_objecttype_yaml(phase_results)
    output_path = f".agent/ontology/objecttype-{api_name}.yaml"
    await Write({
        "file_path": output_path,
        "content": objecttype_yaml
    })

    # 2. LinkType YAML 생성 (관계가 있는 경우)
    if phase_results["phase_3_link"]["links"]:
        for link in phase_results["phase_3_link"]["links"]:
            link_yaml = generate_linktype_yaml(link)
            link_path = f".agent/ontology/linktype-{link['name']}.yaml"
            await Write({
                "file_path": link_path,
                "content": link_yaml
            })

    # 3. Validation Report 생성
    validation_report = generate_validation_report(phase_results)
    await Write({
        "file_path": f".agent/ontology/validation-{api_name}.md",
        "content": validation_report
    })
```

### 8.2 YAML Schema Template

**ObjectType YAML Output** (`objecttype-{ApiName}.yaml`):

```yaml
# Generated by /ontology-objecttype
# Date: 2026-01-26T11:30:00Z
# Source: models/employee.py

api_name: Employee
display_name: Employee
description: "Employee entity in HR domain"
status: DRAFT

# Primary Key Configuration
primary_key:
  source_columns:
    - employee_id
  strategy: single_column
  # For composite:
  # composite_spec:
  #   separator: "_"
  #   order: ["company_id", "employee_id"]
  # For composite_hashed:
  # composite_spec:
  #   hash_algorithm: sha256
  #   order: ["field1", "field2"]

# Properties (20 DataType Support)
properties:
  - api_name: employeeId
    display_name: Employee ID
    data_type: STRING
    required: true
    description: "Primary identifier for employee"

  - api_name: name
    display_name: Full Name
    data_type: STRING
    required: true

  - api_name: email
    display_name: Email Address
    data_type: STRING
    constraints:
      unique: true
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

  - api_name: departmentId
    display_name: Department
    data_type: STRING
    description: "Foreign key to Department (will be LinkType)"

  - api_name: hireDate
    display_name: Hire Date
    data_type: DATE

  - api_name: salary
    display_name: Annual Salary
    data_type: DECIMAL
    decimal_config:
      precision: 10
      scale: 2

  - api_name: skills
    display_name: Skills
    data_type: ARRAY
    array_config:
      item_type: STRING

  - api_name: isActive
    display_name: Active Status
    data_type: BOOLEAN
    default_value: true

# Relationships (converted to LinkTypes)
links:
  - link_type_name: EmployeeToDepartment
    target_object_type: Department
    cardinality: MANY_TO_ONE
    foreign_key:
      source_property: departmentId
      target_property: departmentId
    cascade:
      on_delete: RESTRICT
      on_update: CASCADE

# Validation Gates Results
validation_gates:
  source_validity: PASSED
  candidate_extraction: PASSED
  pk_determinism: PASSED
  link_integrity: PASSED
  semantic_consistency: PASSED

# Phase Results Metadata
metadata:
  source_type: "Existing source code"
  domain: "HR & Employee Management"
  source_file: "models/employee.py"
  generated_by: "/ontology-objecttype v1.1.0"
  phase_1_timestamp: "2026-01-26T11:00:00Z"
  phase_2_timestamp: "2026-01-26T11:15:00Z"
  phase_3_timestamp: "2026-01-26T11:25:00Z"
  phase_4_timestamp: "2026-01-26T11:30:00Z"
```

**LinkType YAML Output** (`linktype-{LinkName}.yaml`):

```yaml
# Generated by /ontology-objecttype (Phase 3)
# Date: 2026-01-26T11:25:00Z

api_name: EmployeeToDepartment
display_name: Employee to Department
description: "Many-to-One relationship from Employee to Department"
status: DRAFT

# Link Configuration
source_object_type: Employee
target_object_type: Department
cardinality: MANY_TO_ONE

# Implementation
implementation:
  type: FOREIGN_KEY
  foreign_key_location: SOURCE
  source_property: departmentId
  target_property: departmentId

# Cascade Policies
cascade:
  on_delete: RESTRICT  # Department 삭제 시 Employee가 있으면 거부
  on_update: CASCADE   # Department ID 변경 시 Employee도 업데이트

# Validation
validation:
  enforce_referential_integrity: true
  allow_null_fk: false

# Metadata
metadata:
  detected_from: "models/employee.py:L8 (ForeignKey)"
  cardinality_decision: "Phase 3 User Selection"
  generated_by: "/ontology-objecttype v1.1.0"
```

### 8.3 Output Structure (YAML-Based)

```
.agent/ontology/
├── objecttype-Employee.yaml      # ObjectType YAML
├── objecttype-Department.yaml    # ObjectType YAML
├── objecttype-Project.yaml       # ObjectType YAML
├── linktype-EmployeeToDepartment.yaml
├── linktype-EmployeeToProject.yaml
├── validation-Employee.md        # Validation report
├── validation-Department.md
└── MIGRATION_SUMMARY.md          # Overall migration summary
```

### 8.4 DataType-Specific YAML Examples

**ARRAY Type**:
```yaml
- api_name: skills
  data_type: ARRAY
  array_config:
    item_type: STRING
    max_items: 50  # optional
```

**STRUCT Type**:
```yaml
- api_name: address
  data_type: STRUCT
  struct_config:
    fields:
      - name: street
        type: STRING
      - name: city
        type: STRING
      - name: zip
        type: STRING
```

**VECTOR Type** (AI/ML):
```yaml
- api_name: embeddingVector
  data_type: VECTOR
  vector_config:
    dimension: 768
    distance_metric: COSINE  # COSINE, EUCLIDEAN, DOT_PRODUCT
```

**DECIMAL Type**:
```yaml
- api_name: price
  data_type: DECIMAL
  decimal_config:
    precision: 10  # 전체 자릿수
    scale: 2       # 소수점 자릿수
```

### 8.5 Migration to Python Code (Optional)

YAML을 Python ObjectType 코드로 변환 (선택적):

```python
# Post-processing: YAML → Python Code Generation
async def generate_python_from_yaml(yaml_path):
    """
    YAML 스키마를 ontology-definition 패키지 Python 코드로 변환
    (선택적 기능, /ontology-codegen 스킬에서 처리)
    """
    yaml_data = load_yaml(yaml_path)

    python_code = f'''
from ontology_definition.types import ObjectType, PropertyDefinition
from ontology_definition.core.enums import DataType, ObjectStatus

{yaml_data["api_name"].lower()}_type = ObjectType(
    api_name="{yaml_data["api_name"]}",
    display_name="{yaml_data["display_name"]}",
    status=ObjectStatus.{yaml_data["status"]},
    primary_key=PrimaryKeyDefinition(
        property_api_name="{yaml_data["primary_key"]["source_columns"][0]}"
    ),
    properties=[
        PropertyDefinition(
            api_name="{prop["api_name"]}",
            data_type=DataType.{prop["data_type"]},
            required={prop.get("required", False)}
        )
        for prop in yaml_data["properties"]
    ]
)
'''

    output_path = yaml_path.replace(".yaml", ".py")
    await Write({"file_path": output_path, "content": python_code})

    return output_path
```

**Output Example**:
```python
# employee_type.py (Generated from YAML)
from ontology_definition.types import ObjectType, PropertyDefinition
from ontology_definition.core.enums import DataType, ObjectStatus

employee_type = ObjectType(
    api_name="Employee",
    display_name="Employee",
    status=ObjectStatus.DRAFT,
    primary_key=PrimaryKeyDefinition(
        property_api_name="employeeId"
    ),
    properties=[
        PropertyDefinition(
            api_name="employeeId",
            data_type=DataType.STRING,
            required=True
        ),
        PropertyDefinition(
            api_name="name",
            data_type=DataType.STRING,
            required=True
        ),
        # ... more properties
    ]
)
```

---

## 9. Integration with /ontology-core

```bash
# After /ontology-objecttype generates files:

# Validate generated ObjectTypes
/ontology-core validate-all .agent/ontology/

# Check link consistency
/ontology-core check-links .agent/ontology/
```

---

## 10. Tools Allowed

### 10.1 Core Tools

| Tool | Purpose |
|------|---------|
| `Read` | 소스 파일 + ontology-definition 패키지 읽기 |
| `Glob` | 프로젝트 파일 탐색 |
| `Grep` | 패턴 검색 (class, ORM 등) |
| `Write` | ObjectType scaffold 생성 |
| `AskUserQuestion` | L1/L2/L3 승인 워크플로우 |

### 10.2 Reference Tools (실시간 추론용)

| Tool | Purpose | 역할 |
|------|---------|------|
| `Read` (ontology-definition) | 로컬 패키지 타입/테스트 참조 | **"어떻게"** 정의하는가 |
| `mcp__context7__query_docs` | Palantir 공식 문서 검색 | **"왜"** + 실제 사례 |
| `WebSearch` | 실제 AIP/Foundry 사용 기업 사례 | **"왜"** + 장단점 |
| `WebFetch` | 특정 URL 직접 참조 | **"왜"** + 상세 분석 |
| `mcp__tavily__*` | 검증된 기술 자료 (차후 설치) | **"왜"** + 실제 사례 |

> **Note**: 외부 자료는 **항상** 참조하여 결정 지원 정보를 제공합니다.

---

## 11. Error Handling

| Error | Recovery |
|-------|----------|
| 경로 없음 | "경로를 찾을 수 없습니다. 확인해주세요." |
| Python 파일 없음 | "분석 가능한 Python 파일이 없습니다." |
| 클래스 없음 | "ObjectType 후보가 발견되지 않았습니다." |
| 세션 만료 | "새 분석을 시작하거나 --resume으로 재개하세요." |

---

## 12. Future Roadmap

| 스킬 | 범위 | 상태 |
|------|------|------|
| `/ontology-objecttype` | ObjectType 도출 + Learning | ✅ 현재 |
| `/ontology-linktype` | LinkType 도출 (관계 분석) | 🔜 계획됨 |
| `/ontology-actiontype` | ActionType 도출 (CRUD 분석) | 🔜 계획됨 |

---

**End of Skill Definition**
