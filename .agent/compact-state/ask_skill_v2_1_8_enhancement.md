# /ask Skill V2.1.8 Enhancement Plan

> **Version:** 1.0 | **Status:** READY_FOR_APPROVAL | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | medium |
| Total Phases | 6 |
| Files Affected | 5 |
| New Files | 2 |
| Modified Files | 3 |

## Core Requirements (User's Critical Feedback)

**사용자 핵심 요구사항:**
> "수치적인 것들은 의미가 없다. 반드시 **Socratic-Questioning과 Semantic Integrity**를 수행한 후에 **최종프롬프트를 승인받은 후** 너가 작업하기 위한 것이다."

| # | Requirement | Priority |
|---|-------------|----------|
| R1 | **Semantic Integrity Protocol** - AI가 이해한 바를 진술 후 모호함 제거 | **CRITICAL** |
| R2 | **User Approval Gate** - 최종 프롬프트 승인 후에만 실행 | **CRITICAL** |
| R3 | 수치 점수 제거 - clarity_score (lines 440, 460) 등 숫자 기반 판단 제거 | HIGH |
| R4 | TodoWriteTracker 통합 - 세션 추적 및 Auto-Compact 생존 | HIGH |
| R5 | Progressive-Disclosure 압축 - 686줄 → ~200줄 | MEDIUM |

---

## Dual-Path Analysis Results

### Path 1: ODA Protocol (Explore Agent aee4f6b)

**Key Findings:**
- `ask.md`: 686 lines total
- **clarity_score found at lines 440-442, 460** - uses 0.7 threshold
- Gaps identified: User Approval Gate missing, Semantic Integrity Checkpoint absent
- Pattern reference: `todowrite_tracker.py` (472 lines)

### Path 2: Plan Subagent (a3a50c5)

**Architecture Design:**
- ClarificationState enum: INITIAL → UNDERSTANDING → QUESTIONING → CLARIFIED → **APPROVED** → EXECUTING
- ClarificationTracker class with state machine
- SemanticIntegrityRecord for session persistence
- ApprovalRequest with categorical confidence (no numerical)

### Synthesis: Optimal Approach

| Aspect | Explore Finding | Plan Finding | Optimal Choice |
|--------|-----------------|--------------|----------------|
| clarity_score | Lines 440, 460 | Remove entirely | **REMOVE** |
| Approval gate | Missing | APPROVED state mandatory | **MANDATORY** |
| State tracking | TodoWriteTracker pattern | ClarificationTracker | **New module** |
| Compression | 686 lines identified | Progressive-Disclosure | **~200 lines** |

---

## Semantic Integrity Protocol (Core Design)

### Flow Diagram
```
User Input
    │
    ▼
┌─────────────────────────────────────┐
│ 1. PARSE: 의도 추출                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 2. UNDERSTAND: "내가 이해한 바로는..." │
│    → AI가 자신의 이해를 명시적 진술    │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 3. AMBIGUITY: 모호한 부분 식별        │
│    → "다음 부분이 명확하지 않습니다..." │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 4. QUESTION: AskUserQuestion         │
│    → Socratic 질문으로 명확화         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 5. CLARIFY: 답변 통합                │
│    → 추가 모호함 있으면 3으로 복귀     │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 6. APPROVE: 최종 프롬프트 승인 요청   │  ← MANDATORY
│    → 사용자가 "승인"해야만 7단계 진행   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 7. ROUTE: 적절한 스킬로 라우팅        │
└─────────────────────────────────────┘
```

### Clarification State Machine

```python
class ClarificationState(str, Enum):
    INITIAL = "initial"          # 최초 입력
    UNDERSTANDING = "understanding"  # AI 이해 진술 중
    QUESTIONING = "questioning"      # 질문 진행 중
    CLARIFIED = "clarified"          # 모호함 해소됨
    APPROVED = "approved"            # ★ 사용자 승인 완료 (MANDATORY)
    EXECUTING = "executing"          # 실행 중
```

---

## Phases

### Phase 1: ClarificationTracker Module
| Item | Detail |
|------|--------|
| **Goal** | Semantic Integrity 세션 추적 모듈 생성 |
| **Effort** | medium |
| **Files** | `lib/oda/planning/clarification_tracker.py` (NEW) |

**Key Components:**
```python
@dataclass
class ClarificationRound:
    round_number: int
    ai_understanding: str      # "내가 이해한 바로는..."
    ambiguities_identified: List[str]  # 식별된 모호함
    questions_asked: List[str]  # 질문 내용
    user_responses: Dict[str, str]  # 사용자 답변

@dataclass
class SemanticIntegrityRecord:
    original_input: str
    rounds: List[ClarificationRound]
    final_prompt: str          # 최종 명확화된 프롬프트
    approved: bool = False     # ★ 승인 여부 (MANDATORY)
    approval_timestamp: Optional[datetime] = None

class ClarificationTracker:
    MAX_ROUNDS: int = 3        # 무한 루프 방지
    def start_session(user_input: str) -> str
    def state_understanding(understanding: str) -> None
    def identify_ambiguities(ambiguities: List[str]) -> None
    def ask_questions(questions: List[str]) -> None
    def record_response(question: str, response: str) -> None
    def request_approval(final_prompt: str) -> ApprovalRequest
    def mark_approved() -> None  # ★ 승인 기록
    def is_approved() -> bool    # ★ 필수 체크
    def to_todowrite_json() -> List[Dict[str, Any]]
```

---

### Phase 2: Reference Document
| Item | Detail |
|------|--------|
| **Goal** | 상세 내용을 별도 파일로 분리 |
| **Effort** | small |
| **Files** | `.claude/references/ask-skill-details.md` (NEW) |

**Content:**
- Semantic Integrity Protocol 상세
- Socratic Questioning 가이드라인
- Prompt Engineering 기법 참조
- 스킬 라우팅 매트릭스

---

### Phase 3: ask.md Compression (686줄 → ~200줄)
| Item | Detail |
|------|--------|
| **Goal** | Progressive-Disclosure 적용 |
| **Effort** | medium |
| **Files** | `.claude/skills/ask.md` |

**New Structure (~200 lines):**
```markdown
---
name: ask
version: "2.1.8"
---

# /ask Skill (V2.1.8)

## Core Protocol: Semantic Integrity
[7-step flow diagram]

## Execution Flow
1. Initialize ClarificationTracker
2. UNDERSTAND → AMBIGUITY → QUESTION loop
3. APPROVE (MANDATORY)
4. ROUTE

## Quick Reference Tables
[Skill routing, state machine]

## Module Reference
→ .claude/references/ask-skill-details.md
→ lib/oda/planning/clarification_tracker.py
```

**Removed Content (moved to references):**
- clarity_score logic (lines 440, 460) - **DELETED entirely**
- Detailed prompt engineering templates
- WebSearch fallback details
- Full routing decision tree

---

### Phase 4: __init__.py Export
| Item | Detail |
|------|--------|
| **Goal** | ClarificationTracker 패키지 노출 |
| **Effort** | trivial |
| **Files** | `lib/oda/planning/__init__.py` |

**Exports to Add:**
```python
from .clarification_tracker import (
    ClarificationState,
    ClarificationRound,
    SemanticIntegrityRecord,
    ApprovalRequest,
    ClarificationTracker,
    create_clarification_tracker,
)
```

---

### Phase 5: ExecutionOrchestrator Integration
| Item | Detail |
|------|--------|
| **Goal** | Clarification 세션 통합 |
| **Effort** | small |
| **Files** | `lib/oda/planning/execution_orchestrator.py` |

**Integration Points:**
```python
class ExecutionOrchestrator:
    _clarification_tracker: Optional[ClarificationTracker] = None

    def start_clarification(self, user_input: str) -> ClarificationTracker:
        """Start semantic integrity session."""
        self._clarification_tracker = ClarificationTracker(user_input)
        return self._clarification_tracker

    def is_prompt_approved(self) -> bool:
        """Check if clarification is complete and approved."""
        if self._clarification_tracker is None:
            return False
        return self._clarification_tracker.is_approved()

    def execute_with_approval_check(self, skill: str) -> None:
        """Execute skill only if approved."""
        if not self.is_prompt_approved():
            raise RuntimeError("Cannot execute: Approval required")
        # Proceed with execution
```

---

### Phase 6: Verification
| Item | Detail |
|------|--------|
| **Goal** | E2E 동작 검증 |
| **Effort** | small |

**Test Scenarios:**
1. `/ask` 호출 → Semantic Integrity flow 확인
2. 모호한 입력 → Socratic 질문 생성 확인
3. 승인 없이 실행 시도 → 블록 확인
4. 승인 후 → 정상 라우팅 확인

---

## Critical File Paths

```yaml
new_files:
  - lib/oda/planning/clarification_tracker.py
  - .claude/references/ask-skill-details.md

modified_files:
  - .claude/skills/ask.md
  - lib/oda/planning/__init__.py
  - lib/oda/planning/execution_orchestrator.py

reference_files:
  - lib/oda/planning/todowrite_tracker.py  # Pattern reference
  - .claude/skills/plan.md                  # Compression pattern
```

---

## Success Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Semantic Integrity 7-step flow 구현 | ClarificationTracker 동작 확인 |
| 2 | **승인 없이는 라우팅 불가** | is_approved() False면 블록 |
| 3 | 수치 점수 완전 제거 | clarity_score 검색 결과 0건 |
| 4 | ClarificationTracker Auto-Compact 생존 | to_json/from_json 동작 |
| 5 | ask.md < 200 lines | wc -l 확인 |
| 6 | E2E: 모호한 입력 → 명확화 → 승인 → 실행 | 수동 테스트 |

---

## Risk Register

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | 과도한 질문 반복 | MEDIUM | MAX_ROUNDS = 3 제한 |
| R2 | 승인 게이트 우회 | LOW | State machine forward-only |
| R3 | Reference file 누락 | LOW | __init__.py에서 검증 |

---

## Execution Strategy

| Phase | Effort | Subagent | Context | Budget |
|-------|--------|----------|---------|--------|
| Phase 1 | medium | general-purpose | fork | 15K |
| Phase 2 | small | Direct | standard | N/A |
| Phase 3 | medium | Direct | standard | N/A |
| Phase 4 | trivial | Direct | standard | N/A |
| Phase 5 | small | Direct | standard | N/A |
| Phase 6 | small | Direct | standard | N/A |

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Codebase Analysis | aee4f6b | completed | No |
| Architecture Design | a3a50c5 | completed | No |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/ask_skill_v2_1_8_enhancement.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING phase
4. Use subagent delegation for Phase 1 (medium effort)

---

> **Approval Required:** 이 6-Phase 구현 계획을 승인하시겠습니까?
>
> 승인 후 `/execute`로 진행합니다.
