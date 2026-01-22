# Deep Audit Report: ODA V2.1.7 Enhancement Analysis

> **Date:** 2026-01-14
> **Protocol:** RSIL + Forked Context
> **Agents Used:** claude-code-guide, Explore (x3)
> **Evidence:** 4 parallel analysis streams

---

## Executive Summary

3가지 요구사항에 대한 종합 분석 결과:

| 요구사항 | 상태 | 발견사항 |
|----------|------|----------|
| Task 1: V2.1.7 기능 활용도 | ⚠️ Gap 발견 | Resume, TaskDecomposer 미사용 |
| Task 2: 슬래시커맨드 통합 | ✅ 기회 식별 | 5개 커맨드 자동화 가능 |
| Task 3: Context Window 관리 | ⚠️ 개선 필요 | ContextBudgetManager 설계 권장 |

---

## Task 1: Custom Agents V2.1.7 기능 활용도 분석

### 현재 상태 매트릭스

| Agent | Model | Context | V2.1.x 활용 | 미사용 기능 |
|-------|-------|---------|-------------|-------------|
| schema-validator | haiku | standard | Evidence tracking | Resume, TaskDecomposer |
| evidence-collector | haiku | standard | Anti-hallucination | Proposal workflow |
| audit-logger | haiku | standard | SQLite logging | Resume, ODA Kernel |
| action-executor | sonnet | standard | Governance checks | Resume, TaskDecomposer |
| prompt-assistant | sonnet | **fork** | Task delegation, parallel | Resume, Proposals |
| onboarding-guide | haiku | standard | None | All ODA features |

### Critical Gaps

#### 1. Resume Parameter (V2.1.1) - 0% 활용

```python
# 현재: Resume 미사용
Task(subagent_type="Explore", prompt="...")

# 권장: Resume 활용
Task(subagent_type="Explore", prompt="...", resume="agent_id_here")
```

**영향:** Auto-Compact 후 작업 손실, 재시작 비용 증가

**해결책:**
- `prompt-assistant`와 `action-executor`에 agent ID 추적 추가
- Plan 파일에 Agent Registry 섹션 활성화

#### 2. TaskDecomposer (V2.1.7) - 0% 활용

```python
# 현재: 직접 대규모 Task 호출
Task(subagent_type="Explore", prompt="전체 코드베이스 분석")

# 권장: TaskDecomposer 사용
from lib.oda.planning.task_decomposer import TaskDecomposer
decomposer = TaskDecomposer()
if decomposer.should_decompose(task):
    subtasks = decomposer.decompose(task, scope)
    for subtask in subtasks:
        Task(**subtask.to_task_params())
```

**영향:** 32K 출력 한도 초과로 결과 truncation

**해결책:**
- 모든 agent에 TaskDecomposer 참조 추가
- Scope 키워드 감지 자동화 ("전체", "모든", "all", "entire")

#### 3. ODA Kernel Proposal 워크플로우 - 부분 활용

- `action-executor`: Proposal 생성만 (승인/실행 분리 없음)
- `schema-validator`: Proposal 검증 미연동

---

## Task 2: 슬래시커맨드 → Agent Skills 통합

### 통합 가능한 커맨드 분석

| 커맨드 | 현재 상태 | 자동화 트리거 | Agent 통합 |
|--------|----------|--------------|------------|
| /protocol | 수동 호출 | 복잡한 작업 감지 시 | `general-purpose` |
| /memory | 수동 호출 | 중요 패턴 발견 시 | `evidence-collector` |
| /maintenance | 수동 호출 | 스키마 불일치 감지 시 | `schema-validator` |
| /governance | 수동 호출 | Pre-commit hook | `schema-validator` |
| /quality-check | 수동 호출 | Post-edit hook | `audit-logger` |
| /memory-sync | 수동 호출 | 세션 종료 시 | `evidence-collector` |
| /teleport | 수동 호출 | 세션 전환 요청 시 | `prompt-assistant` |
| /consolidate | 수동 호출 | 메모리 임계치 도달 시 | `evidence-collector` |
| /commit-push-pr | 수동 호출 | 변경 완료 후 | `action-executor` |
| /init | 수동 호출 | 새 워크스페이스 감지 시 | `onboarding-guide` |

### 권장 통합 설계

```yaml
# Agent Skills Integration (proposed)

schema-validator:
  auto_triggers:
    - pre_edit_hook        # Edit/Write 전 자동 실행
    - governance_check     # /governance 자동 호출
  skills_accessible:
    - oda-governance
    - maintenance

evidence-collector:
  auto_triggers:
    - post_read_hook       # Read/Grep 후 증거 수집
    - session_end          # /memory-sync 자동 호출
    - memory_threshold     # /consolidate 자동 호출
  skills_accessible:
    - memory
    - memory-sync
    - consolidate

action-executor:
  auto_triggers:
    - edit_complete        # /commit-push-pr 제안
    - quality_gate_pass    # /quality-check 완료 후
  skills_accessible:
    - commit-push-pr
    - quality-check

prompt-assistant:
  auto_triggers:
    - user_confusion       # 도움 필요 감지
    - session_transfer     # /teleport 제안
    - complex_request      # /protocol 제안
  skills_accessible:
    - teleport
    - protocol
    - ask

onboarding-guide:
  auto_triggers:
    - new_workspace        # /init 자동 실행
    - first_session        # 온보딩 시작
  skills_accessible:
    - init
```

### 구현 우선순위

1. **High Priority (즉시 효과)**
   - `/governance` → `schema-validator` Pre-Edit Hook
   - `/quality-check` → `audit-logger` Post-Edit Hook
   - `/commit-push-pr` → `action-executor` 변경 완료 트리거

2. **Medium Priority (편의성 향상)**
   - `/memory-sync` → `evidence-collector` 세션 종료 트리거
   - `/init` → `onboarding-guide` 새 워크스페이스 감지

3. **Low Priority (고급 자동화)**
   - `/teleport` → 세션 전환 감지
   - `/consolidate` → 메모리 임계치 모니터링

---

## Task 3: Context Window 관리 & Auto-Compact 해결

### 현재 메커니즘 분석

#### 1. TaskDecomposer (lib/oda/planning/task_decomposer.py)

```python
# 32K 하드코딩된 출력 제한
@dataclass
class TokenBudget:
    explore: int = 5000        # Explore: 5K tokens
    plan: int = 10000          # Plan: 10K tokens
    general_purpose: int = 15000  # general-purpose: 15K tokens
```

**문제:** 고정 예산, 런타임 조정 불가

#### 2. SessionHealthMonitor (lib/oda/claude/session_health.py)

```python
# Context 사용량 추정 (휴리스틱 기반)
context_usage: float = 0.0  # 0-1, tool call 당 ~1.5% 추정
```

**문제:** 실제 토큰이 아닌 추정치, 정확도 낮음

#### 3. PreCompact Hook (.claude/hooks/pre-compact.sh)

- Todo 스냅샷 저장
- Plan 파일 보존
- Agent Registry 유지

**문제:** 사전 감지 불가 (발생 후 복구만)

### 식별된 Gap

| Gap | 영향 | 심각도 |
|-----|------|--------|
| 실시간 Context API 없음 | 정확한 잔여 컨텍스트 모름 | HIGH |
| Agent ID 중앙 저장소 없음 | Resume 불가능 | HIGH |
| Pre-Compact 감지 없음 | 선제적 대응 불가 | MEDIUM |
| 고정 토큰 예산 | 상황별 최적화 불가 | MEDIUM |
| Cross-Agent 인식 없음 | 병렬 실행 시 과다 사용 | LOW |

### 권장 솔루션: ContextBudgetManager

```python
# lib/oda/planning/context_budget_manager.py (신규 생성)

class ContextBudgetManager:
    """
    Main Agent의 Context Window 관리자

    Features:
    - Delegation 전 컨텍스트 상태 확인
    - 동적 토큰 예산 조정
    - Agent ID 레지스트리 관리
    - Auto-Compact 임박 경고
    """

    def __init__(self, session_monitor: SessionHealthMonitor):
        self.monitor = session_monitor
        self.agent_registry: Dict[str, AgentRecord] = {}

    def check_before_delegation(self, estimated_output: int) -> DelegationDecision:
        """
        Task 호출 전 컨텍스트 상태 확인

        Returns:
            DelegationDecision: PROCEED | REDUCE_SCOPE | DEFER | ABORT
        """
        health = self.monitor.evaluate()

        if health.context_usage > 0.8:
            return DelegationDecision.ABORT  # Auto-Compact 임박
        elif health.context_usage > 0.7:
            return DelegationDecision.REDUCE_SCOPE  # 예산 축소
        elif health.context_usage > 0.5:
            return DelegationDecision.PROCEED  # 주의하며 진행
        else:
            return DelegationDecision.PROCEED  # 정상 진행

    def register_agent(self, task_id: str, subagent_type: str, task_desc: str):
        """Agent ID 등록 (Resume 지원)"""
        self.agent_registry[task_id] = AgentRecord(
            id=task_id,
            type=subagent_type,
            description=task_desc,
            created_at=datetime.now(),
            resumable=True
        )

    def get_dynamic_budget(self, subagent_type: str) -> int:
        """컨텍스트 상태에 따른 동적 예산"""
        base_budget = TokenBudget().get_budget(SubagentType(subagent_type))
        health = self.monitor.evaluate()

        # 컨텍스트 사용량에 따라 예산 축소
        if health.context_usage > 0.7:
            return int(base_budget * 0.5)  # 50% 축소
        elif health.context_usage > 0.5:
            return int(base_budget * 0.75)  # 25% 축소
        else:
            return base_budget
```

### 구현 로드맵

```
Phase 1 (즉시): Pre-Delegation Check
├── SessionHealthMonitor.evaluate() 호출 추가
├── context_usage > 0.7 시 경고 메시지
└── TodoWrite로 상태 시각화

Phase 2 (단기): Agent Registry
├── ContextBudgetManager 클래스 생성
├── Task 결과에서 agent_id 추출/저장
└── Plan 파일에 Agent Registry 섹션 추가

Phase 3 (중기): Dynamic Budget
├── TaskDecomposer + ContextBudgetManager 통합
├── 런타임 예산 조정 로직
└── Cross-Agent 컨텍스트 공유

Phase 4 (장기): Predictive Compact
├── 토큰 사용 패턴 학습
├── Auto-Compact 예측 모델
└── 선제적 상태 저장
```

---

## 종합 권장사항

### 즉시 적용 (Quick Wins)

1. **CLAUDE.md 업데이트**
   ```yaml
   # 추가할 섹션
   ### 2.10 Context-Aware Delegation (NEW)

   Before ANY Task() call with large scope:
   1. Check SessionHealthMonitor.evaluate()
   2. If context_usage > 0.7: Use TaskDecomposer to split
   3. Register agent_id from Task result
   4. Update Plan file with Agent Registry
   ```

2. **Agent 정의 업데이트**
   - 모든 `.claude/agents/*.md`에 `TaskDecomposer` 참조 추가
   - `skills_accessible`에 관련 자동화 커맨드 추가

3. **Hook 추가**
   - Pre-Edit: `/governance` 자동 호출
   - Post-Edit: `/quality-check` 자동 호출

### 중기 구현

4. **ContextBudgetManager 개발**
   - `lib/oda/planning/context_budget_manager.py` 생성
   - Main Agent 위임 로직에 통합

5. **Skills 자동화**
   - Agent trigger 이벤트 시스템 구축
   - 커맨드 → Agent 매핑 자동화

### 장기 로드맵

6. **Predictive Context Management**
   - 토큰 사용 패턴 분석
   - Auto-Compact 예측 및 선제 대응

---

## Evidence Summary

```yaml
files_viewed:
  - .claude/agents/schema-validator.md
  - .claude/agents/evidence-collector.md
  - .claude/agents/audit-logger.md
  - .claude/agents/action-executor.md
  - .claude/agents/prompt-assistant.md
  - .claude/agents/onboarding-guide.md
  - .claude/skills/*.md (5 files)
  - lib/oda/planning/task_decomposer.py
  - lib/oda/claude/session_health.py
  - .claude/CLAUDE.md

agents_deployed:
  - claude-code-guide (V2.1.7 changelog search)
  - Explore (Custom Agents analysis)
  - Explore (Slash commands analysis)
  - Explore (Context management analysis)

execution_method: Parallel background (Boris Cherny Pattern)
```

---

**Report Generated:** 2026-01-14 15:13 KST
**Protocol:** RSIL + Forked Context Deep Audit
**Status:** COMPLETE
