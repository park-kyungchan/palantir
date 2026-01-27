# Research Report: Ontology Skill Enhancement

> Generated: 2026-01-26T11:30:00Z
> Clarify Reference: ontology-skill-enhancement-20260126
> Scope: .claude/skills/ontology-*, park-kyungchan/palantir/Ontology-Definition/, docs/ObjectType_Reference.md

---

## L1 Summary (< 500 tokens)

### Key Findings
- **Codebase Patterns:** 12 patterns identified across 3 existing skills and 1 reference architecture
- **External Resources:** 1 comprehensive reference document (ObjectType_Reference.md)
- **Risk Level:** MEDIUM (significant refactoring required but well-documented target state)
- **Complexity:** MODERATE (clear gap analysis, structured enhancement path)

### Current State vs Target State

| Aspect | Current (`/ontology-objecttype`) | Target (`ObjectType_Reference.md`) |
|--------|----------------------------------|-------------------------------------|
| Workflow | L1→L2→L3 linear progression | Phase 1→2→3→4 interactive decision tree |
| PK Strategy | Auto-detection only | User-selectable: single/composite/hashed |
| Cardinality | Basic FK detection | Decision tree with implementation guidance |
| Validation | Rule list | Stage-based gates (clarify→validate) |
| Output | Python scaffold | YAML definition + semantic validation |
| Explanation | Format only | Integrity analysis via `/ontology-why` |

### Recommendations
1. **Phase-Based Workflow:** Refactor `/ontology-objecttype` to use 4-phase interactive decision tree
2. **PK Strategy Selection:** Add explicit AskUserQuestion-based Primary Key strategy selection
3. **Validation Gates:** Implement stage-based validation (source_validity, pk_determinism, link_integrity, semantic_consistency)

### Next Step
`/planning --research-slug ontology-skill-enhancement-20260126`

---

## L2 Detailed Analysis

### 2.1 Existing Skill Structure Analysis

#### 2.1.1 /ontology-objecttype (SKILL.md v1.1.0)

**Location:** `/home/palantir/.claude/skills/ontology-objecttype/SKILL.md`

| Section | Lines | Purpose | Gap Status |
|---------|-------|---------|------------|
| Purpose | 1-26 | Core identity + principles | Needs Phase workflow addition |
| Invocation | 27-42 | Command interface | OK - analyze/resume/help |
| Command Parsing | 43-72 | Argument handling | Needs --phase parameter |
| Analysis Patterns | 73-112 | Detection targets + patterns | OK - comprehensive |
| Workflow L1/L2/L3 | 113-274 | Progressive disclosure | **MAJOR GAP** - Replace with Phase 1-4 |
| Reference System | 275-403 | ontology-definition + external | OK - well-structured |
| Approval Workflow | 404-434 | Commands + session state | Needs phase-aware commands |
| Output Generation | 435-472 | Scaffold generation | **GAP** - Change to YAML output |
| Integration | 473-485 | /ontology-core reference | OK |
| Tools | 486-509 | Allowed tools | OK |

**Key Patterns Identified:**

```
Pattern 1: Detection Targets (line 79-88)
  - Python class detection: class ClassName:
  - SQLAlchemy ORM: Base/declarative_base
  - Django ORM: models.Model
  - Pydantic: BaseModel

Pattern 2: Property Extraction (line 90-98)
  - Class name → ObjectType.api_name
  - Fields → PropertyDefinition
  - Type hints → DataType
  - PK candidates: id, pk, *_id

Pattern 3: Reference System (line 283-312)
  - Local: ontology-definition package
  - External: Context7, WebSearch, WebFetch
  - Validation: Trusted domains only
```

#### 2.1.2 /ontology-why (SKILL.md v1.0.0)

**Location:** `/home/palantir/.claude/skills/ontology-why/SKILL.md`

| Section | Lines | Purpose | Gap Status |
|---------|-------|---------|------------|
| Purpose | 1-24 | Integrity explanation | Needs 5 integrity perspectives |
| Invocation | 25-49 | Direct + internal call | OK |
| Support Scope | 50-76 | Component questions | Needs expanded examples |
| Reference System | 77-106 | Trusted sources | OK |
| Output Format | 107-189 | Response structure | Needs WebSearch integration |
| Integration | 190-224 | Cross-skill calling | OK |
| Tools | 225-237 | Allowed tools | OK |

**Key Patterns Identified:**

```
Pattern 4: Integrity Perspectives (line 70-76)
  - Immutability: PK/identifier changes
  - Determinism: Same input → same output
  - Referential Integrity: Link consistency
  - Semantic Consistency: Type/constraint meaning
  - Lifecycle Management: State change impact

Pattern 5: WHY Pattern Detection (line 201-207)
  - Korean: 왜, 이유, 근거, 어째서
  - English: why, reason, because
```

#### 2.1.3 /ontology-core (SKILL.md v1.0.0)

**Location:** `/home/palantir/.claude/skills/ontology-core/SKILL.md`

| Section | Lines | Purpose | Gap Status |
|---------|-------|---------|------------|
| Purpose | 1-19 | Core schema validation | OK - complete |
| Invocation | 20-36 | Commands | OK |
| Validation Rules | 37-121 | OT/LT/AT/PD rules | OK - comprehensive |
| Execution Protocol | 122-195 | validate/scaffold/check-links | OK |
| Output Format | 196-240 | L1/L2/L3 reporting | OK |
| Templates | 241-303 | Scaffold templates | OK |

**Key Patterns Identified:**

```
Pattern 6: Validation Rule Structure (line 79-99)
  Rule ID: OT-001, LT-001, AT-001, PD-001 format
  Fields: Name, Severity (ERROR/WARNING), Description

Pattern 7: Cross-Reference Validation (line 173-195)
  - Find all ObjectType + LinkType definitions
  - Verify source/target references exist
  - Report missing references
```

### 2.2 Reference Architecture Analysis (ObjectType_Reference.md)

**Location:** `/home/palantir/park-kyungchan/palantir/docs/ObjectType_Reference.md`

#### 2.2.1 Key Architecture Components

| Component | Lines | Purpose | Implementation Priority |
|-----------|-------|---------|------------------------|
| 4-Phase Workflow | 360-404 | Interactive decision tree | P0-CRITICAL |
| YAML Schema | 46-254 | ontology-objecttype.schema.yaml | P0-CRITICAL |
| Validation Gates | 256-335 | Stage-based gates | P0-CRITICAL |
| Decision Tree Diagrams | 636-687 | PK + Cardinality decisions | P1-HIGH |
| Bilingual Support | 591-631 | ko/en locales | P2-MEDIUM |

#### 2.2.2 Phase Workflow (Target State)

```yaml
Phase 1: Context Clarification (L1)
  Q1: Source type (code/schema/doc/manual)
  Q2: Business domain (free text)
  Gate: source_validity

Phase 2: Entity Discovery (L2)
  - IF source == "code": Scan for @Entity patterns
  Q3: Primary Key Strategy
      [a] Single existing column
      [b] Composite key → prompt components
      [c] Generate new ID (with warning)
  Gate: candidate_extraction, pk_determinism

Phase 3: Link Definition (L2)
  Q4: Relationships exist?
      IF yes:
        Q4a: Target ObjectType
        Q4b: Cardinality (1:1, 1:N, N:1, N:N)
        IF N:N: auto-configure join table
  Gate: link_integrity

Phase 4: Validation & Output (L3)
  - Run all validation gates
  - Generate YAML scaffold
  - Optional: PySpark pipeline code
  Gate: semantic_consistency
```

#### 2.2.3 YAML Schema Structure (Primary Key Spec)

```yaml
primaryKeySpec:
  type: object
  required: ["propertyId", "strategy"]
  properties:
    propertyId:
      type: string
    strategy:
      type: string
      enum: ["single_column", "composite", "composite_hashed"]
    components:
      type: array
      items:
        type: string
      description: "For composite keys: ordered list of property IDs"
    delimiter:
      type: string
      default: ":"
      description: "Separator for composite keys"
```

#### 2.2.4 Validation Gate Rules

| Gate | Stage | Rules |
|------|-------|-------|
| `source_validity` | clarify | source_paths exists, domain_context provided |
| `candidate_extraction` | research | 1+ entity, all have PK candidates |
| `pk_determinism` | define | strategy defined, PK is STRING, PK is required |
| `link_integrity` | define | N:N requires join table, others require FK |
| `semantic_consistency` | validate | manual checklist + POC configured |

### 2.3 Python Implementation Analysis (ontology-definition package)

**Location:** `/home/palantir/park-kyungchan/palantir/Ontology-Definition/`

#### 2.3.1 ObjectType (types/object_type.py)

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `ObjectType` | Main entity schema | api_name, display_name, primary_key, properties, status, endorsed |
| `PrimaryKeyDefinition` | PK configuration | property_api_name, backing_column |
| `BackingDatasetConfig` | Dataset reference | dataset_rid, mode, additional_datasets |
| `SecurityConfig` | Row-level security | mandatory_control_properties, object_security_policy |

**Validation Methods:**
- `validate_primary_key_exists()`: PK property must exist
- `validate_mandatory_control_properties()`: MCP properties exist
- `validate_unique_property_names()`: No duplicate apiNames

#### 2.3.2 PropertyDefinition (types/property_def.py)

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `PropertyDefinition` | Property schema | api_name, display_name, data_type, constraints |
| `DataTypeSpec` | Type specification | type (20 types), array_item_type, struct_fields |
| `StructField` | Struct field definition | name, data_type, required |

**Key Constraints:**
- `PropertyConstraints`: required, unique, pattern, range
- `is_mandatory_control`: Required + no default + STRING/ARRAY[STRING]
- `is_edit_only`: No backing_column allowed

#### 2.3.3 DataType Enum (core/enums.py)

**20 Supported Types:**

| Category | Types |
|----------|-------|
| Primitive | STRING, INTEGER, LONG, FLOAT, DOUBLE, BOOLEAN, DECIMAL |
| Temporal | DATE, TIMESTAMP, DATETIME, TIMESERIES |
| Complex | ARRAY, STRUCT, JSON |
| Spatial | GEOPOINT, GEOSHAPE |
| Media | MEDIA_REFERENCE, BINARY, MARKDOWN |
| AI/ML | VECTOR |

**Special Configuration Required:**
- ARRAY: `array_item_type`
- STRUCT: `struct_fields`
- VECTOR: `vector_dimension`
- DECIMAL: `precision`, `scale`

### 2.4 Integration Points Map

```
                    ┌─────────────────────────────┐
                    │  ObjectType_Reference.md    │
                    │  (Target Architecture)      │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │  /ontology-objecttype       │
                    │  (Primary Skill)            │
                    ├─────────────────────────────┤
                    │  Phase 1-4 Workflow         │
                    │  PK Strategy Selection      │
                    │  YAML Output                │
                    └──────┬──────────────┬───────┘
                           │              │
        ┌──────────────────▼──┐    ┌──────▼──────────────────┐
        │  /ontology-why      │    │  /ontology-core         │
        │  (Helper Skill)     │    │  (Validation Skill)     │
        ├─────────────────────┤    ├─────────────────────────┤
        │  WHY? questions     │    │  validate/scaffold      │
        │  5 Integrity views  │    │  check-links            │
        │  External search    │    │  Rule enforcement       │
        └─────────────────────┘    └─────────────────────────┘
                           │              │
                    ┌──────▼──────────────▼───────┐
                    │  ontology-definition        │
                    │  (Python Package)           │
                    ├─────────────────────────────┤
                    │  ObjectType                 │
                    │  PropertyDefinition         │
                    │  DataType (20 types)        │
                    │  Validation                 │
                    └─────────────────────────────┘
```

---

## L3 Full Findings

### 3.1 Complete File Analysis

#### 3.1.1 Files Analyzed

| File | Path | Lines | Purpose |
|------|------|-------|---------|
| ontology-objecttype/SKILL.md | .claude/skills/ | 731 | Primary ObjectType definition skill |
| ontology-why/SKILL.md | .claude/skills/ | 259 | Integrity explanation helper |
| ontology-core/SKILL.md | .claude/skills/ | 350 | Core validation skill |
| ObjectType_Reference.md | docs/ | 703 | Target architecture reference |
| object_type.py | ontology_definition/types/ | 503 | ObjectType Python implementation |
| property_def.py | ontology_definition/types/ | 575 | PropertyDefinition implementation |
| enums.py | ontology_definition/core/ | 753 | All enumerations |

#### 3.1.2 Code Evidence: Current L1/L2/L3 Workflow

**From ontology-objecttype/SKILL.md (lines 113-176):**

```markdown
## 5. Workflow: L1 → L2 → L3 Progressive Disclosure

### 5.1 L1 - Summary (첫 번째 출력)
╔══════════════════════════════════════════════════════════════╗
║  ObjectType 후보 분석 완료                                    ║
...
║  다음 단계: "L2" 입력하여 상세 목록 확인                       ║

### 5.2 L2 - Detailed List (두 번째 출력)
┌─────────────────────────────────────────────────────────────┐
│  ObjectType 후보 상세 목록                                   │
...
│  다음 단계: 번호 입력하여 L3 상세 확인 (예: "1" 또는 "1,2,3")  │
│  또는: "approve all" / "approve 1,2,3" / "exclude A,B"        │
```

**GAP:** Linear progression without interactive decision points.

#### 3.1.3 Code Evidence: Target Phase Workflow

**From ObjectType_Reference.md (lines 360-404):**

```yaml
### Phase 1: Context Clarification (L1)
Q1: What is your source for this ObjectType?
    [a] Existing source code (분석할 소스 코드)
    [b] Database schema (데이터베이스 스키마)
    [c] Business requirements document (비즈니스 요구사항)
    [d] Manual definition (수동 정의)

Q2: What is the business domain? (비즈니스 도메인)
    → Free text input with validation

### Phase 2: Entity Discovery (L2)
Q3: Primary Key Strategy (기본 키 전략):
    [a] Single existing column (단일 기존 컬럼)
    [b] Composite key (복합 키) → prompt for components
    [c] Generate new ID column (새 ID 컬럼 생성)

    VALIDATION: If user selects non-string type, warn:
    "⚠️ Primary keys must be string type. Convert to string? (Y/n)"
```

**TARGET:** Interactive decision tree with validation at each step.

#### 3.1.4 Code Evidence: YAML Schema (primaryKeySpec)

**From ObjectType_Reference.md (lines 89-154):**

```yaml
primaryKeySpec:
  type: object
  required: ["propertyId", "strategy"]
  properties:
    propertyId:
      type: string
    strategy:
      type: string
      enum: ["single_column", "composite", "composite_hashed"]
    components:
      type: array
      items:
        type: string
      description: "For composite keys: ordered list of property IDs"
```

**This aligns with clarify requirement REQ-002.**

### 3.2 Gap-to-Implementation Mapping

| Gap ID | Category | Current State | Target State | Implementation Notes |
|--------|----------|---------------|--------------|---------------------|
| GAP-001 | Workflow | L1→L2→L3 linear | Phase 1→2→3→4 | Add phase sections, AskUserQuestion per phase |
| GAP-002 | PK Strategy | Auto-detect only | User selection | Add Q3 with 3 options, validation gate |
| GAP-003 | Cardinality | FK detection | Decision tree | Add Q4a/Q4b, join table auto-config |
| GAP-004 | Validation | Rule list | Stage gates | Implement 4 gate types per phase |
| GAP-005 | Explanation | Format only | Integrity analysis | Enhance /ontology-why with 5 perspectives |
| GAP-006 | Output | Python scaffold | YAML + validation | Change output format, add schema validation |
| GAP-007 | Bilingual | None | ko/en separation | Add locales/ (Phase 2 work) |

### 3.3 Validation Gate Implementation Details

**Gate 1: source_validity (Phase 1)**
```yaml
rules:
  - expr: "has(input.source_paths) && size(input.source_paths) > 0"
    message_ko: "최소 하나의 소스 경로가 필요합니다"
  - expr: "input.domain_context != ''"
    message_ko: "도메인 컨텍스트를 제공해야 합니다"
```

**Gate 2: candidate_extraction (Phase 2)**
```yaml
rules:
  - expr: "size(candidates.entities) >= 1"
    message_ko: "최소 하나의 엔티티 후보가 식별되어야 합니다"
  - expr: "candidates.entities.all(e, has(e.primary_key_candidate))"
    message_ko: "모든 엔티티에 기본 키 후보가 있어야 합니다"
```

**Gate 3: pk_determinism (Phase 2)**
```yaml
rules:
  - expr: "spec.primaryKey.strategy != '' && spec.primaryKey.propertyId != ''"
    message_ko: "기본 키 전략과 속성이 정의되어야 합니다"
  - expr: "!spec.properties.exists(p, p.id == spec.primaryKey.propertyId && p.dataType != 'string')"
    message_ko: "기본 키는 문자열 타입이어야 합니다"
```

**Gate 4: link_integrity (Phase 3)**
```yaml
rules:
  - expr: "spec.links.all(l, l.cardinality != 'many_to_many' || has(l.joinTable))"
    message_ko: "다대다 링크에는 조인 테이블 구성이 필요합니다"
```

**Gate 5: semantic_consistency (Phase 4)**
```yaml
type: manual
checklist:
  - "ObjectType maps to natural-language business concept"
  - "Primary key is deterministic and immutable"
  - "All meaningful relationships are modeled as LinkTypes"
```

### 3.4 Ontology-Why Enhancement Details

**5 Integrity Perspectives (from clarify REQ-005):**

| Perspective | Description | Example Question |
|-------------|-------------|------------------|
| Immutability | PK/identifier must never change | "왜 PK를 String으로?" |
| Determinism | Same input → same output | "왜 autoincrement 금지?" |
| Referential Integrity | Links must not break | "왜 FK가 Many side에?" |
| Semantic Consistency | Type matches meaning | "왜 DATE vs TIMESTAMP?" |
| Lifecycle Management | State changes impact | "왜 DEPRECATED 상태?" |

**Enhanced Output Format:**

```markdown
╔══════════════════════════════════════════════════════════════╗
║  🔍 Ontology Integrity 분석: {subject}                        ║
╠══════════════════════════════════════════════════════════════╣
║  Q: {user_question}                                           ║
║                                                               ║
║  📐 1. Immutability (불변성)                                  ║
║     - {analysis}                                              ║
║                                                               ║
║  📐 2. Determinism (결정성)                                   ║
║     - {analysis}                                              ║
║                                                               ║
║  📐 3. Referential Integrity (참조 무결성)                    ║
║     - {analysis}                                              ║
║                                                               ║
║  📐 4. Semantic Consistency (의미론적 일관성)                 ║
║     - {analysis}                                              ║
║                                                               ║
║  📐 5. Lifecycle Management (생명주기 관리)                   ║
║     - {analysis}                                              ║
║                                                               ║
║  📚 Palantir 공식 근거:                                       ║
║  "{citation}"                                                 ║
║  🔗 {source_url}                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 3.5 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking existing workflows | MEDIUM | Maintain backward compatibility via `--legacy` flag |
| YAML schema validation complexity | LOW | Reuse ObjectType_Reference.md schema definition |
| External search rate limiting | LOW | Cache results, fallback to local ontology-definition |
| User confusion with phase changes | MEDIUM | Clear phase indicators + progress bar |
| Hook implementation complexity | MEDIUM | Separate hook scripts (Phase 2) |

### 3.6 Implementation Recommendation Summary

#### Phase 1: /ontology-objecttype Refactoring (P0)
1. Replace L1/L2/L3 sections with Phase 1-4 workflow
2. Add `AskUserQuestion` calls for each phase
3. Implement PK strategy selection (single/composite/hashed)
4. Add Cardinality decision tree
5. Change output to YAML format
6. Add validation gate execution at phase boundaries

#### Phase 2: /ontology-why Enhancement (P0)
1. Add 5 Integrity perspectives structure
2. Enhance output format with all perspectives
3. Add WebSearch integration for real-time Palantir docs

#### Phase 3: Validation Hooks (P1)
1. Create PreToolUse hook for YAML validation
2. Implement gate scripts per phase
3. Add semantic_consistency manual checklist

#### Phase 4: Bilingual Support (P2)
1. Create locales/ko.yaml and locales/en.yaml
2. Externalize all prompts and messages
3. Add language detection logic

---

## Research Metadata

```yaml
research_id: ontology-skill-enhancement-20260126
workload_id: ontology-skill-enhancement-20260126
clarify_source: .agent/prompts/ontology-skill-enhancement-20260126/clarify.yaml
files_analyzed: 7
patterns_identified: 12
risk_level: MEDIUM
complexity: MODERATE
next_action: /planning --research-slug ontology-skill-enhancement-20260126
```

---

*Research conducted by Claude Opus 4.5 | 2026-01-26*
