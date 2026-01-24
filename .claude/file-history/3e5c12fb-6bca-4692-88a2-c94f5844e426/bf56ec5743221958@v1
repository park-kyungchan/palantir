# Ontology-Definition Documentation Index

**Version:** 1.0.0
**Generated:** 2026-01-17
**Palantir Alignment Score:** 78% (Target: 95%)

---

## Overview

이 문서는 Palantir AIP/Foundry Ontology 구조를 기반으로 한 Ontology-Definition 프로젝트의 종합 문서입니다.
모든 요소들의 정의, 메타데이터, 검증 규칙, 예제를 포함합니다.

---

## Document Structure

```
docs/elements/
├── INDEX.md                           # 이 문서 (종합 인덱스)
├── QUICK_REFERENCE.md                 # 빠른 참조 가이드
│
├── Core Elements
│   ├── ObjectType.md                  # 객체 타입 정의
│   ├── LinkType.md                    # 관계 타입 정의
│   ├── ActionType.md                  # 액션 타입 정의
│   └── Interface.md                   # 인터페이스 정의
│
├── Property System
│   ├── PropertyDefinition.md          # 속성 정의
│   ├── DataTypes_Enums.md             # 데이터 타입 및 열거형
│   └── SharedProperty_StructType_ValueType.md  # 재사용 가능 타입
│
├── Advanced Topics
│   ├── Constraints_Security.md        # 제약조건 및 보안
│   ├── InteractionRules.md            # 요소간 상호작용 규칙
│   └── Metadata.md                    # 메타데이터 타입
```

---

## Core Elements

### [ObjectType](./ObjectType.md)
> **"An ObjectType is the schema definition of a real-world entity or event"**

| Aspect | Details |
|--------|---------|
| Primary Key | Required, unique identifier |
| Properties | DataTypeSpec based definitions |
| Security | Mandatory Control, Restricted Views |
| Status | DRAFT → ACTIVE → DEPRECATED (+ ENDORSED for ObjectType only) |

**Key Features:**
- 실세계 엔티티 모델링
- 속성 기반 스키마 정의
- 행 수준 보안 지원
- 데이터셋 백킹 구성

---

### [LinkType](./LinkType.md)
> **"A LinkType is the schema definition of a relationship between two ObjectTypes"**

| Aspect | Details |
|--------|---------|
| Cardinality | ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY |
| Implementation | FOREIGN_KEY, BACKING_TABLE |
| Cascade | CASCADE, SET_NULL, RESTRICT, NO_ACTION |
| Status | No ENDORSED status |

**Key Features:**
- 관계 모델링 (1:1, 1:N, N:1, N:N)
- Foreign Key vs Backing Table 구현
- Cascade 정책
- ONE_TO_ONE은 indicator only (not enforced)

---

### [ActionType](./ActionType.md)
> **"An ActionType is the schema definition of a change or edit a user can make to the Ontology"**

| Aspect | Details |
|--------|---------|
| Implementation | DECLARATIVE, FUNCTION_BACKED, INLINE_EDIT |
| Parameters | STRING, INTEGER, OBJECT_PICKER, OBJECT_SET 등 |
| Side Effects | NOTIFICATION, WEBHOOK, EMAIL, AUDIT_LOG |
| Status | No ENDORSED status |

**Key Features:**
- 사용자 편집 작업 정의
- 선언적/함수 기반 구현
- 제출 조건 (Submission Criteria)
- 감사 및 실행취소 지원

---

### [Interface](./Interface.md)
> **"An Interface defines a contract that ObjectTypes can implement, enabling polymorphism"**

| Aspect | Details |
|--------|---------|
| Inheritance | extends mechanism |
| Properties | Required property requirements |
| Actions | Interface-level action definitions |
| Status | No ENDORSED status |

**Key Features:**
- 계약 기반 설계
- 다형성 지원
- 인터페이스 상속
- 구현 ObjectType 검증

---

## Property System

### [PropertyDefinition](./PropertyDefinition.md)
속성 정의의 완전한 구조:
- DataTypeSpec (타입 명세)
- PropertyConstraints (제약조건)
- Semantic properties (의미론적 속성)

### [DataTypes_Enums](./DataTypes_Enums.md)
모든 데이터 타입 및 열거형:

| Category | Types |
|----------|-------|
| Primitive | STRING, INTEGER, LONG, FLOAT, DOUBLE, BOOLEAN |
| Temporal | DATE, TIMESTAMP, DATETIME, TIMESERIES |
| Complex | ARRAY, STRUCT, JSON |
| Spatial | GEOPOINT, GEOSHAPE |
| Media | MEDIA_REFERENCE, MARKDOWN |
| AI/ML | VECTOR |
| ⚠️ Extension | DECIMAL, BINARY (NOT valid Palantir types) |

### [SharedProperty_StructType_ValueType](./SharedProperty_StructType_ValueType.md)
재사용 가능한 타입 정의:
- **SharedProperty**: 여러 ObjectType에서 재사용
- **StructType**: 중첩 구조 정의 (Address, MonetaryAmount 등)
- **ValueType**: 제약 기반 파생 타입 (EmailAddress, PositiveInteger 등)

---

## Advanced Topics

### [Constraints_Security](./Constraints_Security.md)
제약조건 및 보안 모델:
- PropertyConstraints (required, immutable, unique, etc.)
- MandatoryControlConfig (MARKINGS, ORGANIZATIONS, CLASSIFICATIONS)
- RestrictedViews (GAP-001: Not yet implemented)

### [InteractionRules](./InteractionRules.md)
요소간 상호작용 규칙:
- ObjectType-LinkType interactions
- ActionType-ObjectType interactions
- Cascade effects
- Security interactions
- Validation order

### [Metadata](./Metadata.md)
메타데이터 타입:
- OntologyMetadata (전체 온톨로지)
- AuditLog (불변 감사 로그)
- ChangeSet (트랜잭션 변경)
- ExportMetadata (내보내기)
- ProposalMetadata (제안서 워크플로우)

---

## Palantir Alignment Summary

### Current Score: 78%

| Feature | Score | Status |
|---------|-------|--------|
| ObjectType System | 95% | ✅ Excellent |
| LinkType System | 90% | ✅ Good |
| ActionType System | 90% | ✅ Good |
| Property System | 95% | ✅ Excellent |
| Governance | 95% | ✅ Excellent |
| RBAC | 90% | ✅ Good |

### Critical Gaps (P1)

| Gap ID | Name | Status |
|--------|------|--------|
| GAP-001 | Restricted Views (Row-Level Security) | ❌ Not Implemented |
| GAP-002 | Mandatory Control Properties | ⚠️ Partial |
| GAP-003 | Schema Export to Foundry Format | ⚠️ Partial |

### High Priority Gaps (P2)

| Gap ID | Name | Status |
|--------|------|--------|
| GAP-004 | Interface Type Support | ⚠️ Partial |
| GAP-005 | ENDORSED Status for ObjectTypes | ❌ Missing |
| GAP-006 | Value Type Constraint System | ⚠️ Partial |
| GAP-007 | One-to-One Cardinality Indicator Only | ❌ Not Implemented |

---

## Quick Links

### Implementation Files

| Element | Implementation Path |
|---------|-------------------|
| ObjectType | `ontology_definition/types/object_type.py` |
| LinkType | `ontology_definition/types/link_type.py` |
| ActionType | `ontology_definition/types/action_type.py` |
| Interface | `ontology_definition/types/interface.py` |
| PropertyDefinition | `ontology_definition/types/property_def.py` |
| Enums | `ontology_definition/core/enums.py` |
| SharedProperty | `ontology_definition/types/shared_property.py` |
| StructType | `ontology_definition/types/struct_type.py` |
| ValueType | `ontology_definition/types/value_type.py` |
| Constraints | `ontology_definition/constraints/` |

### Research Sources

| Source | Path |
|--------|------|
| DOCX Extraction | `/docs/research/analysis/docx_extraction.json` |
| Gap Analysis | `/docs/research/analysis/gap_analysis.json` |
| ObjectType Schema | `/docs/research/schemas/ObjectType.schema.json` |
| LinkType Schema | `/docs/research/schemas/LinkType.schema.json` |
| ActionType Schema | `/docs/research/schemas/ActionType.schema.json` |
| Property Schema | `/docs/research/schemas/Property.schema.json` |
| Metadata Schema | `/docs/research/schemas/Metadata.schema.json` |
| Interaction Schema | `/docs/research/schemas/Interaction.schema.json` |

### External References

| Reference | Path |
|-----------|------|
| Palantir External Reference | `.agent/reports/palantir_external_reference_2026_01_17.md` |
| Deep Audit Synthesis | `.agent/reports/deep_audit_final_synthesis_2026_01_17.md` |

---

## Remediation Roadmap

### Phase 1: Critical Foundation (4-6 weeks)
- GAP-002: Mandatory Control Properties
- GAP-003: Foundry-compatible Schema Export
- GAP-001: Restricted Views

**Expected Gain: 78% → 90%**

### Phase 2: High Priority (2-3 weeks)
- GAP-005: ENDORSED status
- GAP-007: 1:1 cardinality indicator
- GAP-004: Interface enhancements
- GAP-006: ValueType system

**Expected Gain: 90% → 94%**

### Phase 3: Polish (1-2 weeks)
- Medium/Low priority gaps

**Expected Gain: 94% → 96%**

---

## Document Statistics

| Document | Lines | Size |
|----------|-------|------|
| ObjectType.md | ~900 | 26 KB |
| LinkType.md | ~750 | 21 KB |
| ActionType.md | ~1100 | 32 KB |
| Interface.md | ~730 | 24 KB |
| PropertyDefinition.md | ~1000 | 31 KB |
| DataTypes_Enums.md | ~850 | 25 KB |
| SharedProperty_StructType_ValueType.md | ~1400 | 48 KB |
| Constraints_Security.md | ~950 | 31 KB |
| InteractionRules.md | ~900 | 29 KB |
| Metadata.md | ~900 | 29 KB |
| **Total** | **~9500** | **~296 KB** |

---

*Generated by ODA Deep Audit Documentation System*
*Palantir AIP/Foundry Alignment: 78%*
*Target: 95%*
