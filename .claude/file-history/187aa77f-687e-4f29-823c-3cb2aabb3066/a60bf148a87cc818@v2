# /ask Skill V2.1.8 Enhancement Plan

> **Version:** 2.0 | **Status:** READY_FOR_APPROVAL | **Date:** 2026-01-18
> **Scope:** Semantic Integrity Protocol + TodoWriteTracker Integration

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
| R3 | 수치 점수 제거 - clarity_score 등 숫자 기반 판단 제거 | HIGH |
| R4 | TodoWriteTracker 통합 - 세션 추적 및 Auto-Compact 생존 | HIGH |
| R5 | Progressive-Disclosure 압축 - 685줄 → ~200줄 | MEDIUM |

---

## Semantic Integrity Protocol (핵심 설계)

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
| **Files** | `lib/oda/planning/clarification_tracker.py` (NEW) |

**Key Components:**
```python
@dataclass
class ClarificationRound:
    ai_understanding: str      # "내가 이해한 바로는..."
    ambiguities_identified: List[str]  # 식별된 모호함
    questions_asked: List[str]  # 질문 내용
    user_response: Optional[str]  # 사용자 답변

@dataclass
class SemanticIntegrityRecord:
    original_input: str
    rounds: List[ClarificationRound]
    final_prompt: str          # 최종 명확화된 프롬프트
    approved: bool = False     # ★ 승인 여부 (MANDATORY)
    approved_at: Optional[datetime] = None

class ClarificationTracker:
    def start_session(user_input: str) -> str
    def record_understanding(understanding: str) -> None
    def record_ambiguities(ambiguities: List[str]) -> None
    def record_questions(questions: List[str]) -> None
    def record_response(response: str) -> None
    def set_approved(final_prompt: str) -> None  # ★ 승인 기록
    def is_approved() -> bool
    def get_final_prompt() -> Optional[str]
```

---

### Phase 2: Reference Document
| Item | Detail |
|------|--------|
| **Goal** | 상세 내용을 별도 파일로 분리 |
| **Files** | `.claude/references/ask-skill-details.md` (NEW) |

**Content:**
- Semantic Integrity Protocol 상세
- Socratic Questioning 가이드라인
- Prompt Engineering 기법 참조
- 스킬 라우팅 매트릭스

---

### Phase 3: ask.md 압축 (685줄 → ~200줄)
| Item | Detail |
|------|--------|
| **Goal** | Progressive-Disclosure 적용 |
| **Files** | `.claude/skills/ask.md` |

**New Structure:**
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
```

---

### Phase 4: __init__.py Export
| Item | Detail |
|------|--------|
| **Goal** | ClarificationTracker 패키지 노출 |
| **Files** | `lib/oda/planning/__init__.py` |

---

### Phase 5: ExecutionOrchestrator Integration
| Item | Detail |
|------|--------|
| **Goal** | Clarification 세션 통합 |
| **Files** | `lib/oda/planning/execution_orchestrator.py` |

**Integration Points:**
- `_clarification_tracker` property
- `start_clarification()` method
- `is_prompt_approved()` check

---

### Phase 6: Verification
| Item | Detail |
|------|--------|
| **Goal** | E2E 동작 검증 |

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

1. [ ] Semantic Integrity 7-step flow 구현
2. [ ] **승인 없이는 라우팅 불가** (APPROVED state 필수)
3. [ ] 수치 점수 완전 제거 (clarity_score 등)
4. [ ] ClarificationTracker Auto-Compact 생존
5. [ ] ask.md < 200 lines
6. [ ] E2E: 모호한 입력 → 명확화 → 승인 → 실행

---

## Risk Register

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | 과도한 질문 반복 | MEDIUM | 3회 라운드 제한 |
| R2 | 승인 게이트 우회 | LOW | State machine 강제 |
| R3 | Reference file 누락 | LOW | __init__.py에서 검증 |

---

## Execution Strategy

| Phase | Effort | Subagent | Context |
|-------|--------|----------|---------|
| Phase 1 | medium | Direct | standard |
| Phase 2 | small | Direct | standard |
| Phase 3 | medium | Direct | standard |
| Phase 4 | trivial | Direct | standard |
| Phase 5 | small | Direct | standard |
| Phase 6 | small | Direct | standard |

**Note:** 모든 Phase가 Direct 실행 가능 (medium 이하)

---

> **핵심 설계 원칙:**
> - 수치 점수 NO → Socratic 질문 YES
> - 승인 없이 실행 NO → APPROVED state 필수
> - 긴 스킬 파일 NO → Progressive-Disclosure YES
