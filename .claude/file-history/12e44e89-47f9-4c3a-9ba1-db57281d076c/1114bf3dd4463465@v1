# Draft: L1/L2 런타임 통합

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-19
> **Auto-Compact Safe:** This file persists across context compaction

---

## INDEX

### 요구사항 요약
이전 세션에서 구현된 L1/L2 Orchestrating Loop의 ODA 정의(15개 JSON 인스턴스 + 6개 Hook 스크립트)를 실제 런타임에 통합하여 완전 자동화된 L1/L2 분리 시스템 구축.

### Complexity
- **예상 복잡도:** large
- **영향 파일:** ~20개 ([상세](#file-analysis))
- **기존 구현물:** 21개 파일 (15 JSON + 6 Hooks)

### Q&A 핵심
1. **Q:** 런타임 통합 범위? → **A:** 완전 자동화 (Palantir AIP/Foundry 패턴)
2. **Q:** L1/L2 분리 방식? → **A:** 병행 (프롬프트 주입 + 출력 파싱)
3. **Q:** run_in_background 강제 범위? → **A:** 모든 Task() 호출 + 기존 commands/skills 문서 수정 병행
4. **Q:** L1 Enforcement 정책? → **A:** BLOCK mode (exit code 2)
5. **Q:** Phase State 관리? → **A:** 파일 기반 `.agent/state/orchestration.json`

### 추천 접근법
PreToolUse Hook의 `updatedInput` 기능을 활용하여 모든 Task() 호출에 `run_in_background=true`를 주입하고, 기존 commands/skills 문서도 함께 수정하여 일관성 확보.

### 리스크
- Hook 실행 오류 시 fallback 처리 필요
- 기존 commands/skills와의 호환성 검증 필요
- L2 파일 경로 충돌 방지 (UUID/timestamp 포함)

### 다음 단계
`/plan` 실행 권장. Draft 참조: `--draft runtime_integration` 또는 자동 감지.

---

## DETAIL: Q&A 전체 로그 {#qa-log}

### Round 1 (2026-01-19)
**Q:** 런타임 통합의 scope는?
- 최소 검증 (수동 실행, 선택적 적용)
- 부분 자동화 (특정 subagent만)
- 완전 자동화 (모든 Task() 호출)

**A:** 완전 자동화. "Ontology-Driven-Architecture를 초기단계부터 구현하는 것임을 충분히 인지했나? Palantir AIP/Foundry 아키텍쳐와 비슷하게 진행하는 거야. 완전 자동화를 원한다."

### Round 2 (2026-01-19)
**Q:** Claude Code Hook 시스템 제약 이해?
**A:** "아니오, 자세히 설명 필요"

**설명 제공:**
- Hooks는 event listener (trigger only)
- Shell script → Python module 호출
- Exit code: 0=allow, 2=block
- **핵심 제약:** Hook은 Subagent 출력을 직접 수정 불가

**Q:** L1/L2 분리 방식?
- 프롬프트 주입 (Task 전)
- 출력 파싱 (Task 후)
- 병행 (주입 + 파싱)

**A:** "병행 (주입 + 파싱)"

### Round 3 (2026-01-19)
**Q:** Phase 전이 트리거 방식?
**A:** "1번으로 하고자하는데, 토큰소비 심하니까, 이것을 스크립트로(ODA기반)으로 구현할 수 있는 방법 찾아봐"

**핵심 발견:**
- claude-code-guide 조회 결과, PreToolUse Hook이 `updatedInput`으로 Tool 파라미터 수정 가능!
- `run_in_background=true`를 모든 Task()에 강제 주입 가능

### Round 4 (2026-01-19)
**Q:** run_in_background 적용 범위?
- 모든 Task() 호출
- 특정 subagent_type만
- 설정 파일 기반 제어

**A:** "1번으로 진행해야해. 그런데, 생각해보니 현재 /home/palantir/.claude/의 모든 커맨드/스킬도 이것이 필요하므로 작업할 때 함께 확인해보고 개선하도록 해"

### Round 5 (2026-01-19)
**Q:** 기존 commands/skills 개선 방식?
- Hook 전역 강제만
- Hook + 문서 수정 병행
- 문서만 수정 (Hook 제외)

**A:** "Hook + 문서 수정 병행"

**Q:** Draft 작성 준비 완료?
**A:** "예, Draft 작성 진행"

---

## DETAIL: 요구사항 상세 {#requirements}

### 기능 요구사항
- FR1: 모든 Task() 호출에 run_in_background=true 자동 주입
- FR2: L1 형식 검증 (summary ≤200자, l2Index[], l2Path)
- FR3: L2 파일 영속화 (.agent/outputs/{taskId}/{timestamp}.md)
- FR4: Phase 상태 관리 (.agent/state/orchestration.json)
- FR5: BLOCK mode enforcement (L1 형식 위반 시 차단)
- FR6: 기존 commands/skills의 Task() 패턴 일관성 확보

### 비기능 요구사항
- NFR1: 토큰 효율성 (bash grep 기반 검증, LLM 호출 최소화)
- NFR2: Hook 오류 시 graceful fallback (WARN mode로 전환)
- NFR3: Auto-Compact 후 복구 가능성 (파일 기반 상태 관리)

---

## DETAIL: 파일 분석 결과 {#file-analysis}

### 기존 구현물 (Phase 1-5 완료)

#### JSON Schema Instances (15개)
| 파일명 | 타입 | 역할 |
|--------|------|------|
| ObjectType.AgentOutputL1.json | ObjectType | L1 출력 구조 정의 |
| ObjectType.AgentOutputL2.json | ObjectType | L2 출력 구조 정의 |
| ObjectType.DelegationPrompt.json | ObjectType | 위임 프롬프트 구조 |
| ObjectType.OrchestrationState.json | ObjectType | 오케스트레이션 상태 |
| LinkType.L1ReferencesL2.json | LinkType | L1↔L2 참조 관계 |
| LinkType.AgentProducesOutput.json | LinkType | Agent→Output 관계 |
| LinkType.StateContainsOutput.json | LinkType | State→Output 관계 |
| ActionType.DelegateToAgent.json | ActionType | 위임 Action |
| ActionType.ValidateL2Exists.json | ActionType | L2 존재 검증 |
| ActionType.OrchestrateWithL1.json | ActionType | L1 기반 오케스트레이션 |
| ActionType.RetrieveL2Section.json | ActionType | L2 섹션 조회 |
| ActionType.WriteL2ToFile.json | ActionType | L2 파일 저장 |
| Interaction.OrchestrationInteractionRules.json | Interaction | 오케스트레이션 규칙 |
| Interaction.OutputFormatEnforcement.json | Interaction | 출력 형식 강제 |
| Interaction.L2StorageConsistency.json | Interaction | L2 저장 일관성 |

#### Hook Scripts (6개)
| 파일명 | 트리거 | 역할 |
|--------|--------|------|
| pre-task-delegation.sh | PreToolUse(Task) | Task() 호출 감지 |
| pre_task_injection.py | PreToolUse(Task) | L1/L2 프롬프트 주입 |
| post-task-output.sh | PostToolUse(Task) | L1 형식 검증 |
| post_task_validator.py | PostToolUse(Task) | Python 기반 검증 |
| orchestration-loop.sh | Phase 종료 시 | Phase 전이 결정 |
| orchestration_manager.py | Phase 종료 시 | 오케스트레이션 로직 |

### 기존 Commands/Skills Task() 사용 분석

#### run_in_background=True 이미 사용
- .claude/commands/governance.md
- .claude/commands/quality-check.md
- .claude/commands/audit.md
- .claude/commands/deep-audit.md
- .claude/commands/plan.md (부분)

#### run_in_background 미사용 (수정 필요)
- .claude/commands/interface.md
- .claude/commands/linktype.md
- .claude/commands/metadata.md
- .claude/commands/property.md
- .claude/commands/interaction.md

### 신규 구현 필요 파일

| 파일 | 용도 |
|------|------|
| .claude/hooks/l1l2/force_background.py | updatedInput으로 run_in_background 주입 |
| .agent/state/orchestration.json | Phase 상태 관리 |
| .claude/settings.json 수정 | Hook 경로 설정 (TODO 제거) |

---

## DETAIL: 리스크 분석 {#risk-analysis}

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| Hook 실행 오류 | High | try-catch + fallback to WARN mode |
| updatedInput 미지원 시나리오 | Medium | 버전 체크 + graceful degradation |
| L2 경로 충돌 | Medium | UUID + timestamp 조합 |
| 기존 commands 호환성 | Medium | 점진적 마이그레이션 + 테스트 |
| Auto-Compact 후 상태 유실 | High | 파일 기반 상태 관리 |

---

## DETAIL: 핵심 기술 발견 {#key-discovery}

### PreToolUse Hook의 updatedInput 기능

Claude Code Hook 시스템은 `hookSpecificOutput.updatedInput`으로 Tool 파라미터를 수정할 수 있음.

```python
#!/usr/bin/env python3
# force_background.py - 모든 Task()에 run_in_background=true 강제

import json
import sys

input_data = json.load(sys.stdin)
tool_name = input_data.get("tool_name", "")

if tool_name == "Task":
    current_input = input_data.get("tool_input", {})

    # run_in_background=true 강제 주입
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {
                **current_input,
                "run_in_background": True
            }
        }
    }
    print(json.dumps(output))
else:
    # Task 외 도구는 통과
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }
    }))

sys.exit(0)
```

이 패턴으로:
1. 모든 Task() 호출이 자동으로 background 실행
2. Subagent 출력은 파일로 저장
3. Main Context는 task_id만 수신
4. L1/L2 분리가 강제됨

---

## Metadata

- Created: 2026-01-19T18:50:00+09:00
- Last Updated: 2026-01-19T18:55:00+09:00
- Q&A Rounds: 5
- Status: COMPLETED
- Previous Plan: .agent/plans/l1_l2_orchestrating_loop.md (COMPLETED)
