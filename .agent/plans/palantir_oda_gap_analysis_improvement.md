# Palantir AIP/Foundry ODA Gap Analysis 대규모 개선 계획

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-14
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | LARGE |
| Total Phases | 4 |
| Total Tasks | 32 |
| Files Affected | 25+ |
| Current Implementation Score | 4.2/5 |
| Target Score | 4.8/5 |

## Requirements Summary

Gap Analysis를 통해 식별된 Palantir AIP/Foundry ODA 개념들의 대규모 개선:
1. **Interfaces** - ObjectType 다형성 (Polymorphism)
2. **Extended Statuses** - 리소스 라이프사이클 상태
3. **Full RBAC** - ObjectType 레벨 접근 제어
4. **Shared Properties** - 공유 속성 메커니즘
5. **Ontology Branching** - Git-like 버전 관리
6. **Pipeline Builder** - 데이터 파이프라인 DSL

---

## Phase 1: Interfaces (Priority: HIGH)

**Goal:** ObjectType 다형성을 위한 Interface 정의 시스템 구현

### Tasks

| # | Task | Status | File Path |
|---|------|--------|-----------|
| 1.1 | InterfaceDefinition 모델 생성 | PENDING | `lib/oda/ontology/types/interface_types.py` |
| 1.2 | InterfaceRegistry 추가 | PENDING | `lib/oda/ontology/registry.py` |
| 1.3 | @implements_interface 데코레이터 | PENDING | `lib/oda/ontology/decorators/interface_decorator.py` |
| 1.4 | OntologyObject interface 지원 | PENDING | `lib/oda/ontology/ontology_types.py` |
| 1.5 | Interface 검증 Action 등록 | PENDING | `lib/oda/ontology/actions/interface_actions.py` |
| 1.6 | Unit tests 작성 | PENDING | `tests/ontology/test_interfaces.py` |

### Key Models

```python
class InterfaceDefinition(BaseModel):
    interface_id: str  # e.g., "IVersionable"
    description: str
    required_properties: List[PropertySpec]
    required_methods: List[MethodSpec]
    extends: Optional[List[str]] = None  # Interface 상속
```

### Actions to Register

| api_name | Hazardous | Description |
|----------|-----------|-------------|
| `interface.register` | No | 인터페이스 등록 |
| `interface.validate` | No | 구현 검증 |
| `interface.export` | No | 스키마 내보내기 |

---

## Phase 2: Extended Statuses (Priority: HIGH)

**Goal:** 리소스 라이프사이클 상태 관리 시스템

### Tasks

| # | Task | Status | File Path |
|---|------|--------|-----------|
| 2.1 | ResourceLifecycleStatus enum 생성 | PENDING | `lib/oda/ontology/types/status_types.py` |
| 2.2 | StatusTransition 검증기 | PENDING | `lib/oda/ontology/validators/status_validator.py` |
| 2.3 | StatusMixin 구현 | PENDING | `lib/oda/ontology/mixins/status_mixin.py` |
| 2.4 | 상태 이력 추적 | PENDING | `lib/oda/ontology/tracking/status_history.py` |
| 2.5 | Status Action 등록 | PENDING | `lib/oda/ontology/actions/status_actions.py` |
| 2.6 | Unit tests 작성 | PENDING | `tests/ontology/test_status_lifecycle.py` |

### Status Enum

```python
class ResourceLifecycleStatus(str, Enum):
    # Development
    DRAFT = "draft"
    EXPERIMENTAL = "experimental"
    ALPHA = "alpha"
    BETA = "beta"

    # Production
    ACTIVE = "active"
    STABLE = "stable"

    # Deprecation
    DEPRECATED = "deprecated"
    SUNSET = "sunset"

    # End of Life
    ARCHIVED = "archived"
    DELETED = "deleted"
```

### Transition Rules

| From | Allowed To |
|------|-----------|
| DRAFT | EXPERIMENTAL, ACTIVE, DELETED |
| EXPERIMENTAL | ALPHA, DEPRECATED |
| ALPHA | BETA, DEPRECATED |
| BETA | ACTIVE, DEPRECATED |
| ACTIVE | STABLE, DEPRECATED |
| DEPRECATED | SUNSET, ARCHIVED |

---

## Phase 3: Full RBAC (Priority: HIGH)

**Goal:** ObjectType 레벨 접근 제어 확장

### Current State
- `lib/oda/agent/permissions.py`: PermissionManager, AgentRole, ActionPermission 존재
- 패턴 기반 Action 권한만 지원
- ObjectType/Instance 레벨 권한 없음

### Tasks

| # | Task | Status | File Path |
|---|------|--------|-----------|
| 3.1 | ObjectTypePermission 모델 | PENDING | `lib/oda/agent/object_permissions.py` |
| 3.2 | Team/Group 모델 | PENDING | `lib/oda/agent/teams.py` |
| 3.3 | AgentProfile 팀 멤버십 확장 | PENDING | `lib/oda/agent/permissions.py` |
| 3.4 | InstancePermission (객체별 ACL) | PENDING | `lib/oda/agent/instance_permissions.py` |
| 3.5 | PermissionResolver (상속 처리) | PENDING | `lib/oda/agent/permission_resolver.py` |
| 3.6 | RBAC Actions 등록 | PENDING | `lib/oda/ontology/actions/rbac_actions.py` |
| 3.7 | Unit tests 작성 | PENDING | `tests/agent/test_rbac_full.py` |

### Key Models

```python
class ObjectTypePermission(BaseModel):
    object_type: str  # e.g., "Task"
    role_id: str
    can_read: bool = True
    can_create: bool = False
    can_update: bool = False
    can_delete: bool = False
    can_link: bool = False
    field_restrictions: Dict[str, FieldPermission] = {}

class Team(OntologyObject):
    name: str
    members: List[str]  # agent_ids
    parent_team_id: Optional[str] = None
    permissions: List[ObjectTypePermission]
```

---

## Phase 4: Medium Priority Enhancements

### 4.1 Shared Properties

| # | Task | Status | File Path |
|---|------|--------|-----------|
| 4.1.1 | SharedPropertyDefinition 모델 | PENDING | `lib/oda/ontology/types/shared_properties.py` |
| 4.1.2 | @uses_shared_property 데코레이터 | PENDING | `lib/oda/ontology/decorators/shared_property.py` |
| 4.1.3 | Registry 내보내기 확장 | PENDING | `lib/oda/ontology/registry.py` |

### 4.2 Ontology Branching Enhancement

| # | Task | Status | File Path |
|---|------|--------|-----------|
| 4.2.1 | Merge conflict detection | PENDING | `lib/oda/transaction/conflict_detector.py` |
| 4.2.2 | Cherry-pick 지원 | PENDING | `lib/oda/transaction/cherry_pick.py` |
| 4.2.3 | Branch 비교 API | PENDING | `lib/oda/ontology/actions/branch_actions.py` |

### 4.3 Pipeline Builder

| # | Task | Status | File Path |
|---|------|--------|-----------|
| 4.3.1 | PipelineBuilder DSL | PENDING | `lib/oda/data/pipeline_builder.py` |
| 4.3.2 | PipelineStep ObjectType | PENDING | `lib/oda/ontology/objects/pipeline.py` |
| 4.3.3 | Pipeline validation actions | PENDING | `lib/oda/ontology/actions/pipeline_actions.py` |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Phase 1: Interfaces | 6 | 0 | PENDING |
| Phase 2: Statuses | 6 | 0 | PENDING |
| Phase 3: RBAC | 7 | 0 | PENDING |
| Phase 4.1: Shared Properties | 3 | 0 | PENDING |
| Phase 4.2: Branching | 3 | 0 | PENDING |
| Phase 4.3: Pipeline | 3 | 0 | PENDING |
| **Total** | **28** | **0** | **0%** |

---

## Dependency Graph

```
Phase 1 (Interfaces)
    └── 1.1 InterfaceDefinition
        └── 1.2 InterfaceRegistry
            └── 1.3 @implements_interface
                └── 1.4 OntologyObject update

Phase 2 (Statuses) [Parallel with Phase 1]
    └── 2.1 ResourceLifecycleStatus
        └── 2.2 StatusTransition validator
            └── 2.3 StatusMixin
                └── 2.4 Status history

Phase 3 (RBAC) [After Phase 1 for interface-based permissions]
    └── 3.1 ObjectTypePermission ──┐
    └── 3.2 Team model ───────────┤
        └── 3.3 AgentProfile ─────┤
            └── 3.4 InstancePermission
                └── 3.5 PermissionResolver

Phase 4 [After Phases 1-3]
    └── 4.1 Shared Properties (uses Interfaces)
    └── 4.2 Branching Enhancement
    └── 4.3 Pipeline Builder
```

---

## Parallel Execution Groups

| Group | Tasks | Can Parallelize |
|-------|-------|-----------------|
| Group A | Phase 1 + Phase 2 | YES (independent) |
| Group B | Tasks 3.1, 3.2 | YES (independent models) |
| Group C | Tasks 4.1, 4.2, 4.3 | YES (independent features) |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Interface validation overhead | MEDIUM | 30% | Cache validation results |
| RBAC complexity explosion | HIGH | 40% | Start ObjectType-level only |
| Status transition breaking changes | HIGH | 50% | Migration script |
| Breaking PermissionManager | CRITICAL | 20% | Extend, don't replace |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/palantir_oda_gap_analysis_improvement.md`
2. Check Phase/Task status table above
3. Continue from first PENDING task in sequence
4. Use Explore agent for codebase analysis before each phase
5. Create Proposals for all file modifications

---

## Subagent Delegation Strategy

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| Phase 1 Implementation | general-purpose | fork | 15K tokens |
| Phase 2 Implementation | general-purpose | fork | 15K tokens |
| Phase 3 Implementation | general-purpose | fork | 15K tokens |
| Phase 4 Implementation | general-purpose | fork | 15K tokens |
| Testing | general-purpose | fork | 10K tokens |

---

## Critical File Paths

```yaml
core_files_to_modify:
  - lib/oda/ontology/ontology_types.py  # Base OntologyObject
  - lib/oda/ontology/registry.py  # Central registry
  - lib/oda/agent/permissions.py  # Existing RBAC

new_files_to_create:
  phase_1:
    - lib/oda/ontology/types/interface_types.py
    - lib/oda/ontology/decorators/interface_decorator.py
    - lib/oda/ontology/actions/interface_actions.py

  phase_2:
    - lib/oda/ontology/types/status_types.py
    - lib/oda/ontology/validators/status_validator.py
    - lib/oda/ontology/mixins/status_mixin.py
    - lib/oda/ontology/tracking/status_history.py
    - lib/oda/ontology/actions/status_actions.py

  phase_3:
    - lib/oda/agent/object_permissions.py
    - lib/oda/agent/teams.py
    - lib/oda/agent/instance_permissions.py
    - lib/oda/agent/permission_resolver.py
    - lib/oda/ontology/actions/rbac_actions.py

  phase_4:
    - lib/oda/ontology/types/shared_properties.py
    - lib/oda/ontology/decorators/shared_property.py
    - lib/oda/transaction/conflict_detector.py
    - lib/oda/transaction/cherry_pick.py
    - lib/oda/data/pipeline_builder.py
    - lib/oda/ontology/objects/pipeline.py

reference_files:
  - lib/oda/ontology/types/link_types.py  # Pattern for InterfaceDefinition
  - lib/oda/ontology/objects/proposal.py  # State machine pattern
```

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Plan Analysis | af312b0 | completed | No |

---

## Verification Checklist

After implementation, verify:

- [ ] All 6 Interface tasks completed
- [ ] All 6 Status tasks completed
- [ ] All 7 RBAC tasks completed
- [ ] All 9 Phase 4 tasks completed
- [ ] Tests passing for each phase
- [ ] No breaking changes to existing ObjectTypes
- [ ] Proposals created for all file modifications
- [ ] Documentation updated

---

## Approval Gate

- [ ] Plan reviewed by user
- [ ] Resource allocation confirmed
- [ ] Implementation order approved
