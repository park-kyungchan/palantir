# Phase 2: ODA Kernel Integration Plan

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction
> **Prerequisites:** Phase 1 완료 (Ontology-Definition package, PR #8)

## Overview

| Item | Value |
|------|-------|
| Complexity | large |
| Total Tasks | 5 phases, 15+ subtasks |
| Files Affected | ~51 files (register_object_type references) |
| Estimated Reduction | 30% code reduction |

## Requirements

lib/oda/에서 Ontology-Definition 패키지로 스키마 정의를 통합:
1. 중복 타입 정의 제거 (PropertyType, PropertyDefinition)
2. foundry_mimic/ → Ontology-Definition 통합
3. 런타임 레지스트리 일원화 (OntologyRegistry)
4. Foundry 호환성 완전 확보

## Analysis Evidence

### Files Viewed (Stage A)
- `lib/oda/ontology/ontology_types.py` - PropertyType enum (line 52)
- `lib/oda/ontology/types/property_types.py` - PropertyDataType enum (line 51)
- `lib/oda/ontology/registry.py` - PropertyDefinition dataclass (line 47)
- `lib/oda/foundry_mimic/models.py` - ObjectTypeSpec, LinkTypeSpec
- `lib/oda/agent/executor.py` - ActionContext, ActionResult usage

### Critical Duplicates Found
| Type | Location 1 | Location 2 |
|------|------------|------------|
| PropertyType enum | `ontology_types.py:52` | `property_types.py:51` (as PropertyDataType) |
| PropertyDefinition | `registry.py:47` (dataclass) | `property_types.py:258` (Pydantic) |

### Import Dependency Map
- 79 files import `OntologyObject`
- 51 files use `register_object_type`
- 10+ files use `ActionContext`, `ActionResult`, `ActionType`

## Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | 2.1 | Consolidate PropertyType enum to Ontology-Definition.DataType | pending |
| 2 | 2.1 | Update 4 files importing PropertyType from ontology_types | pending |
| 3 | 2.2 | Remove unused PropertyDefinition from registry.py | pending |
| 4 | 2.2 | Migrate property_types.py → Ontology-Definition.PropertyDefinition | pending |
| 5 | 2.3 | Replace foundry_mimic/models.py specs with Ontology-Definition | pending |
| 6 | 2.3 | Update foundry_mimic/service.py to use FoundryExporter | pending |
| 7 | 2.4 | Create compatibility layer for register_object_type decorator | pending |
| 8 | 2.4 | Migrate 51 files to use OntologyRegistry | pending |
| 9 | 2.5 | Run existing tests to verify no regressions | pending |
| 10 | 2.5 | Add integration tests for Ontology-Definition imports | pending |

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 2.1 PropertyType | 2 | 0 | pending |
| 2.2 PropertyDefinition | 2 | 0 | pending |
| 2.3 foundry_mimic | 2 | 0 | pending |
| 2.4 Registry Migration | 2 | 0 | pending |
| 2.5 Testing | 2 | 0 | pending |

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/phase2_oda_kernel_integration.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

## Execution Strategy

### Parallel Execution Groups

**Group A (Independent):**
- Task 1-2: PropertyType consolidation
- Task 3-4: PropertyDefinition consolidation

**Group B (Depends on A):**
- Task 5-6: foundry_mimic integration

**Group C (Depends on B):**
- Task 7-8: Registry migration

**Group D (Depends on All):**
- Task 9-10: Testing and verification

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| Group A | general-purpose | Type consolidation | 15K tokens |
| Group B | general-purpose | Module refactoring | 15K tokens |
| Group C | Explore + general-purpose | 51 file migration | 32K tokens |
| Group D | Bash (pytest) | Test execution | N/A |

## Critical File Paths

```yaml
# Ontology-Definition (Source of Truth)
ontology_definition:
  types: Ontology-Definition/ontology_definition/types/
  registry: Ontology-Definition/ontology_definition/registry/
  export: Ontology-Definition/ontology_definition/export/

# lib/oda (Integration Targets)
lib_oda:
  ontology_types: lib/oda/ontology/ontology_types.py
  property_types: lib/oda/ontology/types/property_types.py
  registry: lib/oda/ontology/registry.py
  foundry_mimic_models: lib/oda/foundry_mimic/models.py
  foundry_mimic_service: lib/oda/foundry_mimic/service.py
```

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking imports | HIGH | Compatibility layer + gradual migration |
| Test failures | MEDIUM | Run tests after each phase |
| Runtime registry conflicts | MEDIUM | Singleton pattern verification |

## Success Criteria

- [ ] Zero duplicate type definitions
- [ ] All 51 files using OntologyRegistry
- [ ] All existing tests pass
- [ ] Foundry export/import roundtrip works
- [ ] ~30% code reduction achieved
