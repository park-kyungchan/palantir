# Phase 1: Ontology-Definition/ Core Implementation Plan

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Target Package | `/home/palantir/park-kyungchan/palantir/Ontology-Definition/` |
| Complexity | medium |
| Total LOC (estimated) | ~2,800 |
| Files to Create | 35+ Python modules |
| Implementation Time | 5-6 weeks |
| Alignment Target | 78% → 95%+ |

## Requirements Summary

### Primary Objective
Palantir AIP/Foundry 정확한 구현을 위한 독립 패키지 생성

### Scope
1. **스키마 정의**: ObjectType, LinkType, ActionType, Property, Interface, Struct
2. **JSON Schema 기반 검증**: Draft 2020-12
3. **런타임 레지스트리**: Singleton pattern with decorators
4. **Foundry 호환 계층**: Export/Import, API compatibility

### Breaking Changes
- 전면 수정 허용 (대규모 리팩토링)
- PAI 모듈 전체 제거
- Evidence 시스템 제거
- MCP 도구 제거

## Dual-Path Analysis Results

### Path 1: ODA Stage A Analysis (ab5089b) ✅

**Files to Extract (13 files, ~2,800 LOC):**

| Priority | File | Purpose | LOC |
|----------|------|---------|-----|
| CRITICAL | `ontology_types.py` | Core types (Cardinality, PropertyType, ObjectStatus) | 300 |
| CRITICAL | `registry.py` | Central registry for ObjectTypes/LinkTypes | 150 |
| CRITICAL | `protocols/base.py` | 3-Stage Protocol base classes | 250 |
| CRITICAL | `action.py` | Action pydantic model | 50 |
| HIGH | `protocols/decorators.py` | Protocol enforcement decorators | 200 |
| HIGH | `validators/schema_validator.py` | Schema validation | 200 |
| HIGH | `foundry_mimic/models.py` | Foundry spec models | 400 |
| HIGH | `foundry_mimic/service.py` | Export/Import logic | 250 |
| HIGH | `objects/core_definitions.py` | Core object definitions | 300 |
| MEDIUM | `validators/status_validator.py` | Status lifecycle | 100 |
| MEDIUM | `objects/task_types.py` | Task/Agent ObjectTypes | 200 |
| MEDIUM | `objects/proposal.py` | Proposal definitions | 150 |
| MEDIUM | `link_registry.py` | LinkType registry | 600 |

**Files to DELETE:**

| Directory | Files | Reason |
|-----------|-------|--------|
| `lib/oda/pai/` | ~40 | Out of scope (Agent orchestration) |
| `lib/oda/ontology/evidence/` | 3 | Application layer |
| `lib/oda/ontology/storage/` | 16 | SQLite persistence (separate concern) |
| `lib/oda/mcp/` | 2 | MCP integration |
| `lib/oda/ontology/learning/` | 12 | Learning subsystem |
| `lib/oda/ontology/governance/` | 4 | Governance enforcement |
| `lib/oda/ontology/jobs/` | 3 | Job scheduling |

**Key Findings:**
- NO circular dependencies detected - safe to extract
- Core schema is clean and well-separated
- Registry system is robust but link_registry.py is large (optimize)

### Path 2: Plan Subagent Architecture (a3fd3f6) ✅

**Recommended Directory Structure:**

```
Ontology-Definition/
├── pyproject.toml              # PEP 517/518 package config
├── ontology_definition/        # Main package
│   ├── core/                   # Base classes, enums
│   ├── types/                  # ObjectType, LinkType, ActionType, etc.
│   ├── constraints/            # PropertyConstraints, MandatoryControl
│   ├── security/               # RestrictedViewPolicy (P1-CRITICAL)
│   ├── registry/               # OntologyRegistry singleton
│   ├── validation/             # JSON Schema + Pydantic validation
│   ├── export/                 # Foundry/JSON Schema export
│   ├── import_/                # Foundry import + migration
│   └── schemas/                # Bundled JSON Schema files
└── tests/
```

**Critical Trade-offs:**
1. **Pydantic v2**: Use for model definitions (existing pattern)
2. **Module-level Singleton**: Thread-safe registry
3. **Dual-layer Validation**: Pydantic + JSON Schema
4. **Foundry-first Export**: Primary format matches Foundry JSON
5. **Cardinality Indicator**: 1:1 is indicator only by default

## Synthesized Implementation Plan

### Phase 1.1: Core Foundation (Week 1-2) - P1-CRITICAL

| # | Task | Files | Est. LOC | Gap Addressed |
|---|------|-------|----------|---------------|
| 1 | Package setup (pyproject.toml, __init__.py) | 3 | 50 | - |
| 2 | OntologyEntity base class with audit fields | `core/base.py` | 100 | - |
| 3 | All enums (DataType 20종, Cardinality, Status) | `core/enums.py` | 150 | GAP-011 |
| 4 | RID, apiName, UUID identifiers | `core/identifiers.py` | 80 | GAP-010 |
| 5 | AuditMetadata, ExportMetadata | `core/metadata.py` | 100 | - |
| 6 | PropertyConstraints model | `constraints/property_constraints.py` | 200 | - |
| 7 | **MandatoryControlConfig** | `constraints/mandatory_control.py` | 100 | **GAP-002** |
| 8 | Bundle JSON Schema files | `schemas/` | 0 (copy) | - |

**Deliverables:** Base types + MandatoryControlConfig (P1-CRITICAL)

### Phase 1.2: Type Definitions (Week 2-3) - P2-HIGH

| # | Task | Files | Est. LOC | Gap Addressed |
|---|------|-------|----------|---------------|
| 1 | ObjectType with securityConfig, endorsed | `types/object_type.py` | 250 | GAP-005 |
| 2 | LinkType with cardinality, backing table | `types/link_type.py` | 200 | GAP-007 |
| 3 | ActionType with parameters, side effects | `types/action_type.py` | 300 | GAP-008 |
| 4 | PropertyDefinition with all flags | `types/property_def.py` | 150 | - |
| 5 | Interface with inheritance | `types/interface.py` | 100 | GAP-004 |
| 6 | ValueType (reusable constraints) | `types/value_type.py` | 80 | - |
| 7 | StructType (nested structure) | `types/struct_type.py` | 80 | - |
| 8 | SharedProperty with semanticType | `types/shared_property.py` | 100 | GAP-015 |

**Deliverables:** All 8 type models fully implemented

### Phase 1.3: Security Features (Week 3-4) - P1-CRITICAL

| # | Task | Files | Est. LOC | Gap Addressed |
|---|------|-------|----------|---------------|
| 1 | **RestrictedViewPolicy** | `security/restricted_view.py` | 200 | **GAP-001** |
| 2 | PolicyTerm with AND/OR operators | `security/policy_term.py` | 100 | GAP-001 |
| 3 | AccessLevel enum, security policies | `security/access_control.py` | 100 | - |

**Deliverables:** RestrictedViewPolicy (P1-CRITICAL), row-level security

### Phase 1.4: Registry and Validation (Week 4-5) - P2-HIGH

| # | Task | Files | Est. LOC | Gap Addressed |
|---|------|-------|----------|---------------|
| 1 | OntologyRegistry singleton | `registry/ontology_registry.py` | 250 | - |
| 2 | @register_object_type decorators | `registry/decorators.py` | 100 | - |
| 3 | InterfaceRegistry (inheritance) | `registry/interface_registry.py` | 100 | GAP-004 |
| 4 | Registry query methods | `registry/query.py` | 80 | - |
| 5 | JSON Schema validation | `validation/schema_validator.py` | 150 | - |
| 6 | Cross-reference validation | `validation/cross_ref_validator.py` | 150 | - |
| 7 | Pydantic runtime validation | `validation/runtime_validator.py` | 100 | - |

**Deliverables:** Registry + dual-layer validation

### Phase 1.5: Export/Import (Week 5-6) - P2-HIGH

| # | Task | Files | Est. LOC | Gap Addressed |
|---|------|-------|----------|---------------|
| 1 | **Foundry JSON export** | `export/foundry_exporter.py` | 250 | **GAP-003** |
| 2 | JSON Schema export | `export/json_schema_exporter.py` | 150 | - |
| 3 | LLM-friendly schema export | `export/llm_schema_exporter.py` | 100 | GAP-013 |
| 4 | Foundry JSON import | `import_/foundry_importer.py` | 200 | - |
| 5 | Version migration utilities | `import_/migration.py` | 100 | - |

**Deliverables:** Round-trip Foundry compatibility (P2-HIGH)

## Critical Gap Coverage

| Gap ID | Name | Priority | Phase | Status |
|--------|------|----------|-------|--------|
| GAP-001 | Restricted Views (Row-Level Security) | **P1-CRITICAL** | 1.3 | PENDING |
| GAP-002 | Mandatory Control Properties | **P1-CRITICAL** | 1.1 | PENDING |
| GAP-003 | Ontology Schema JSON Export | P2-HIGH | 1.5 | PENDING |
| GAP-004 | Interface Inheritance | P2-HIGH | 1.4 | PENDING |
| GAP-005 | ENDORSED Status (ObjectType Only) | P2-HIGH | 1.2 | PENDING |
| GAP-007 | 1:1 Cardinality Indicator | P3-MEDIUM | 1.2 | PENDING |
| GAP-008 | ActionType Parameters/Side Effects | P3-MEDIUM | 1.2 | PENDING |

## Dependencies

```toml
[project]
name = "ontology-definition"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0,<3.0",
    "jsonschema>=4.20.0",
]
```

## Reference Files

| File | Purpose |
|------|---------|
| `docs/research/schemas/ObjectType.schema.json` | Canonical ObjectType schema |
| `docs/research/schemas/LinkType.schema.json` | LinkType with cardinality |
| `docs/research/schemas/ActionType.schema.json` | ActionType with parameters |
| `docs/research/schemas/Property.schema.json` | Property/ValueType/StructType |
| `docs/research/analysis/gap_analysis.json` | 16 gaps with implementation details |
| `docs/research/analysis/refactoring_plan.json` | Original 4-phase plan |

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Output Path |
|------|----------|--------|-------------|
| ODA Stage A Scan | ab5089b | completed | `/tmp/claude/-home-palantir/tasks/ab5089b.output` |
| Plan Architecture | a3fd3f6 | completed | `/tmp/claude/-home-palantir/tasks/a3fd3f6.output` |

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/phase_1_ontology_definition_core.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING phase in sequence
4. Reference files in `docs/research/schemas/` for schema definitions

## Approval Required

- [ ] Proceed with Phase 1 implementation?
