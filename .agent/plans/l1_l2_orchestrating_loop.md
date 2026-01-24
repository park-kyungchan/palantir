# L1/L2 Orchestrating Loop 설계 및 구현

> **Version:** 1.2 | **Status:** COMPLETED | **Date:** 2026-01-19
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | large |
| Total Tasks | 18 |
| Files Affected | ~25 |
| Phases | 5 |

## Baseline (검토 기준)

검토/구현 기준은 아래 로컬 기준을 **source-of-truth**로 삼는다.
- 기준 디렉터리: `ontology_definition/` (WSL 기준: `/home/palantir/park-kyungchan/palantir/ontology_definition`)
- 스키마: `ontology_definition/schemas/*.schema.json`
- 정의 스펙: `ontology_definition/schemas/docs/DEFINITION_SPEC.md`
- Foundry 공식문서(로컬 미러): `ontology_definition/schemas/docs/official/palantir_foundry/INDEX.json`

모호한 부분은 Palantir 공식 문서로 재검증한다(예: ID/API name/RID, LinkType key/카디널리티, ActionType rules/function-backed).

## Requirements

Main Agent가 Subagent에게 작업 위임 시:
1. 출력을 L1(Summary+Index)과 L2(Detail)로 분리
2. L1만으로 오케스트레이션 수행
3. 필요시 L2의 정확한 섹션만 참조
4. Loop 구조로 반복 실행

## Key Decisions (Orchestrator 최적화 관점)

- **L1은 “오케스트레이션 전용” 최소 정보**(상태/요약/인덱스/포인터)만 포함한다.
- **L2는 파일로 영속화**하고, L1은 L2의 *정확한 섹션*을 가리킬 수 있어야 한다(섹션 ID/헤더 앵커/라인 범위 등).
- Ontology 리소스는 Foundry 개념을 그대로 따른다:
  - `id`(kebab-case, 앱 설정용) / `apiName`(코드/SDK용) / `rid`(시스템 생성, 옵션)
  - LinkType은 카디널리티 + 키(FOREIGN_KEY 또는 MANY↔MANY면 BACKING_TABLE)를 명시한다.
  - ActionType은 “규칙/함수/인라인 편집” 중 하나의 구현 타입을 명시한다(특히 function rule은 다른 rule과 혼용 불가).
- AIP/Foundry 권고에 맞춰, **쓰기/변경 작업은 Action(제어면) + 제안(Proposal) 패턴**을 우선 고려한다(감사/권한/안전).

## Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1.1 | Phase 1 | ObjectType: AgentOutputL1 | ✅ COMPLETED |
| 1.2 | Phase 1 | ObjectType: AgentOutputL2 | ✅ COMPLETED |
| 1.3 | Phase 1 | ObjectType: DelegationPrompt | ✅ COMPLETED |
| 1.4 | Phase 1 | ObjectType: OrchestrationState | ✅ COMPLETED |
| 2.1 | Phase 2 | LinkType: L1ReferencesL2 | ✅ COMPLETED |
| 2.2 | Phase 2 | LinkType: AgentProducesOutput | ✅ COMPLETED |
| 2.3 | Phase 2 | LinkType: StateContainsOutput | ✅ COMPLETED |
| 3.1 | Phase 3 | ActionType: DelegateToAgent | ✅ COMPLETED |
| 3.2 | Phase 3 | ActionType: ValidateL2Exists | ✅ COMPLETED |
| 3.3 | Phase 3 | ActionType: OrchestrateWithL1 | ✅ COMPLETED |
| 3.4 | Phase 3 | ActionType: RetrieveL2Section | ✅ COMPLETED |
| 3.5 | Phase 3 | ActionType: WriteL2ToFile | ✅ COMPLETED |
| 4.1 | Phase 4 | InteractionRules: OrchestrationInteractionRules | ✅ COMPLETED |
| 4.2 | Phase 4 | Validator: OutputFormatEnforcement | ✅ COMPLETED |
| 4.3 | Phase 4 | Validator: L2StorageValidation + IndexConsistency | ✅ COMPLETED |
| 5.1 | Phase 5 | Hook: pre-task-delegation | ✅ COMPLETED |
| 5.2 | Phase 5 | Hook: post-task-output | ✅ COMPLETED |
| 5.3 | Phase 5 | Hook: orchestration-loop | ✅ COMPLETED |

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Phase 1: ObjectTypes | 4 | 4 | ✅ COMPLETED |
| Phase 2: LinkTypes | 3 | 3 | ✅ COMPLETED |
| Phase 3: ActionTypes | 5 | 5 | ✅ COMPLETED |
| Phase 4: InteractionRules/Validators | 3 | 3 | ✅ COMPLETED |
| Phase 5: Stop Hooks | 3 | 3 | ✅ COMPLETED |

## Deliverables (Artifacts)

아래 산출물은 **JSON Schema 검증 가능**해야 한다.

- Ontology 정의(JSON 인스턴스): `ontology_definition/instances/oda_orchestration/*.json`
  - `ObjectType.AgentOutputL1.json`
  - `ObjectType.AgentOutputL2.json`
  - `ObjectType.DelegationPrompt.json`
  - `ObjectType.OrchestrationState.json`
  - `LinkType.L1ReferencesL2.json`
  - `LinkType.AgentProducesOutput.json` (전제: `ObjectType.Agent`는 기존 정의를 참조/존재)
  - `LinkType.StateContainsOutput.json`
  - `ActionType.DelegateToAgent.json`
  - `ActionType.ValidateL2Exists.json`
  - `ActionType.OrchestrateWithL1.json`
  - `ActionType.RetrieveL2Section.json`
  - `ActionType.WriteL2ToFile.json`
  - `Interaction.OrchestrationInteractionRules.json` (단일 문서; `Interaction.schema.json` 검증)

- Hooks: `.claude/hooks/` (Stop Hooks pattern)

## Definition Outline (Draft)

아래는 “필수 최소치” 초안이다. (세부 필드는 구현 중 조정 가능하지만, **스키마 required**는 반드시 만족)

### Phase 1: ObjectTypes (최소 스펙)

**ObjectType: AgentOutputL1**
- 목적: Main Agent 오케스트레이션에 필요한 최소 정보(요약+인덱스+포인터)
- 권장 메타:
  - `id`: `agent-output-l1`
  - `apiName`: `AgentOutputL1`
  - `displayName`: `Agent Output (L1)`
- 최소 속성(예시):
  - `outputId` (PK, `STRING`, required/unique)
  - `agentId` (`STRING`, required)
  - `agentType` (`STRING`, required)
  - `status` (`STRING`, required)
  - `summary` (`STRING`, required; 짧게)
  - `l2Path` (`STRING`, required; `.agent/outputs/...`)
  - `index` (`STRING`, required; JSON/YAML 인덱스 직렬화 — *L1 토큰 최소화 우선*)
  - `createdAt` (`TIMESTAMP`, required)

**ObjectType: AgentOutputL2**
- 목적: 상세 보고서/증거/근거(파일로 영속화된 L2)와 그 메타데이터
- 권장 메타:
  - `id`: `agent-output-l2`
  - `apiName`: `AgentOutputL2`
  - `displayName`: `Agent Output (L2)`
- 최소 속성(예시):
  - `outputId` (PK, `STRING`, required/unique)
  - `agentId` (`STRING`, required)
  - `contentPath` (`STRING`, required; L2 파일 경로)
  - `sectionIndex` (`STRING`, optional; anchor/line-range 포함)
  - `contentHash` (`STRING`, optional)
  - `createdAt` (`TIMESTAMP`, required)

**ObjectType: DelegationPrompt**
- 목적: 위임 프롬프트/컨텍스트/예산/출력규약을 재현 가능하게 저장
- 최소 속성(예시):
  - `promptId` (PK, `STRING`, required/unique)
  - `taskId` (`STRING`, required)
  - `subagentType` (`STRING`, required)
  - `budgetTokens` (`INTEGER`, required)
  - `promptText` (`STRING`, required; 길면 L2로 분리 가능)
  - `createdAt` (`TIMESTAMP`, required)

**ObjectType: OrchestrationState**
- 목적: 루프 실행 상태(현재 단계/결정/보류 작업/재시도)를 저장
- 최소 속성(예시):
  - `runId` (PK, `STRING`, required/unique)
  - `planPath` (`STRING`, required)
  - `currentPhase` (`INTEGER`, optional)
  - `status` (`STRING`, required)
  - `lastUpdatedAt` (`TIMESTAMP`, required)

### Phase 2: LinkTypes (최소 스펙)

**LinkType: L1ReferencesL2**
- Source: `AgentOutputL1` → Target: `AgentOutputL2`
- Cardinality: `ONE_TO_ONE` (Foundry 관례상 indicator-only; `enforced: false` 권장)
- Implementation: `FOREIGN_KEY` (예: L1에 `l2OutputId` FK)

**LinkType: AgentProducesOutput**
- Source: `Agent` → Target: `AgentOutputL1`(또는 Output 상위 타입)
- 전제: `ObjectType.Agent`가 기존 Ontology에 존재하거나 이번 스코프에 포함되어야 함
- Cardinality: `ONE_TO_MANY`
- Implementation: `FOREIGN_KEY` (예: Output에 `agentId` FK)

**LinkType: StateContainsOutput**
- Source: `OrchestrationState` → Target: `AgentOutputL1`
- Cardinality: `ONE_TO_MANY`
- Implementation: `FOREIGN_KEY` (예: Output에 `runId` FK)

### Phase 3: ActionTypes (권장: FUNCTION_BACKED)

오케스트레이터 내부 동작(위임/검증/검색/저장)은 **function-backed**로 정의하는 편이 일관적이다.
- `DelegateToAgent`: 위임 프롬프트/상태 업데이트 (필요시 Proposal 경유)
- `ValidateL2Exists`: L2 파일 존재/크기/해시 검증
- `OrchestrateWithL1`: L1 인덱스만으로 다음 행동 결정
- `RetrieveL2Section`: L2에서 필요한 섹션만 추출(앵커/라인 범위 기반)
- `WriteL2ToFile`: L2 영속화 + 메타 기록

### Phase 4: InteractionRules/Validators

**InteractionRules: OrchestrationInteractionRules**
- 산출물은 단일 문서이며 `Interaction.schema.json`을 만족해야 한다.
- 본 문서는 “출력 포맷”을 정의하기보다는, ObjectType/LinkType/ActionType 간 *무결성/검증 순서*를 정의하는 용도다.

**Validator: OutputFormatEnforcement**
- L1 필수 필드(요약/인덱스/L2 포인터) 누락 시 BLOCK 또는 GUIDE.

**Validator: L2StorageValidation + IndexConsistency**
- L2 파일 존재/비어있지 않음/경로 규칙 준수
- L1 인덱스가 가리키는 앵커/라인 범위가 L2에서 재현 가능

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/l1_l2_orchestrating_loop.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

## Execution Strategy

### Phase Dependencies

```
Phase 1 (ObjectTypes) ──┐
                        ├──► Phase 2 (LinkTypes) ──┐
                        │                          │
                        └──────────────────────────┼──► Phase 3 (ActionTypes)
                                                   │           │
                                                   └───────────┼──► Phase 4 (InteractionRules/Validators)
                                                               │           │
                                                               └───────────┴──► Phase 5 (Hooks)
```

### Parallel Execution Groups

**Phase 1 (Parallel):**
- Task(general-purpose): AgentOutputL1
- Task(general-purpose): AgentOutputL2
- Task(general-purpose): DelegationPrompt
- Task(general-purpose): OrchestrationState

**Phase 2 (Parallel, after Phase 1):**
- Task(general-purpose): L1ReferencesL2
- Task(general-purpose): AgentProducesOutput
- Task(general-purpose): StateContainsOutput

**Phase 3 (Parallel, after Phase 2):**
- Task(general-purpose): All 5 ActionTypes

**Phase 4 (Parallel, after Phase 3):**
- Task(general-purpose): InteractionRules document + Validators

**Phase 5 (Sequential, after Phase 4):**
- Write Bash hooks one by one (test each)

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| ObjectTypes (4) | general-purpose | standard | 15K each |
| LinkTypes (3) | general-purpose | standard | 15K each |
| ActionTypes (5) | general-purpose | standard | 15K each |
| InteractionRules/Validators (3) | general-purpose | standard | 15K each |
| Hooks (3) | general-purpose | standard | 15K each |

## Critical File Paths

```yaml
# Schema references
objecttype_schema: ontology_definition/schemas/ObjectType.schema.json
actiontype_schema: ontology_definition/schemas/ActionType.schema.json
linktype_schema: ontology_definition/schemas/LinkType.schema.json
interaction_schema: ontology_definition/schemas/Interaction.schema.json

# Definition spec + official docs (local mirror)
definition_spec: ontology_definition/schemas/docs/DEFINITION_SPEC.md
official_docs_manifest: ontology_definition/schemas/docs/official/palantir_foundry/INDEX.json

# Proposed instance output (definitions)
instances_dir: ontology_definition/instances/oda_orchestration/

# Output locations
l2_storage: .agent/outputs/{agentType}/{agentId}.md
hooks_dir: .claude/hooks/

# Existing ODA implementation references (avoid reinvention)
output_layer_manager: lib/oda/planning/output_layer_manager.py
execution_orchestrator: lib/oda/planning/execution_orchestrator.py
```

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| ODA Protocol Analysis | acd76c5 | in_progress | Yes |
| Architecture Analysis | a4f161f | in_progress | Yes |

## Acceptance Criteria

- 각 JSON 인스턴스는 대응 스키마에 대해 검증된다(`additionalProperties: false` 준수 포함).
- L1은 “요약 + 인덱스 + L2 포인터”만으로 다음 행동을 결정할 수 있다.
- L2는 파일로 존재하며, L1 인덱스가 가리키는 섹션을 재현 가능하게 읽을 수 있다.
- Hook/Validator는 summary-only/누락된 L2/인덱스 불일치 상황에서 **BLOCK 또는 GUIDE**로 동작한다(프로젝트 정책에 맞게 선택).

## Risk Register

| Risk | Mitigation |
|------|------------|
| Schema validation failure | Use jsonschema validation before deploy |
| Hook execution blocking | Implement timeout + fallback in hooks |
| L2 storage path conflicts | `agentId`에 session/timestamp/UUID를 포함해 충돌 방지 |
| Circular references in Links | Validate cardinality constraints |
| ID/apiName 혼동 | 각 리소스에 `id`/`apiName`/`displayName`를 명시하고 규칙을 문서화 |
| LinkType “키/구현” 누락 | FOREIGN_KEY vs BACKING_TABLE를 명시하고 MANY↔MANY는 join table 필수로 검증 |

## Notes

- All ODA type definitions must pass JSON Schema validation
- Hooks use Stop Hooks pattern (exit non-zero to block)
- L1 output format is MANDATORY for all subagent responses
