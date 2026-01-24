# /audit & /deep-audit 전체 재설계 계획

> **Version:** 1.0 | **Status:** READY_FOR_APPROVAL | **Date:** 2026-01-18
> **Scope:** 스킬 파일 + 참조문서 + 하위모듈 전체

---

## Overview

| Item | Value |
|------|-------|
| Complexity | large |
| Total Phases | 6 |
| New Files | 4 |
| Modified Files | 4 |
| Deleted Sections | ~2000 lines (중복 제거) |

## 핵심 문제점 (사용자 피드백)

| # | 문제 | 영향 |
|---|------|------|
| 1 | 기능 중복 | /audit과 /deep-audit에서 동일한 패턴 반복 |
| 2 | 요구사항 미파악 | Socratic-Questioning 없이 바로 실행 |
| 3 | 불필요한 토큰 소비 | 전체 범위 분석으로 낭비 |

---

## 재설계 목표

### `/audit` 재설계 방향
```
[현재]
User Input → 4-Stream Parallel Execution → Report

[목표]
User Input → Socratic-Questioning → Scope 최소화 →
→ Focused Execution → Report
```

**핵심 변경:**
- ClarificationTracker V2.1.8 통합
- Scope 최소화 후에만 검사 시작
- 특정 영역 집중 검사

### `/deep-audit` 재설계 방향
```
[현재]
User Input → 4-Stream Parallel → RSIL Synthesis → Report

[목표]
User Input → 3-Tier Progressive Deep-Dive → Layer Report

Tier 1: Structure (파일/디렉토리 구조)
    ↓
Tier 2: Function (API, 시그니처, 의존성)
    ↓
Tier 3: Logic (코드 라인 레벨)
    ↓
계층별 보고서
```

**핵심 변경:**
- 4-Stream → 3-Tier 전환
- 전체 실행 후 계층 보고
- Progressive Deep-Dive 방법론

---

## Implementation Phases

### Phase 1: 신규 모듈 생성

| Task | File | Description |
|------|------|-------------|
| 1.1 | `lib/oda/planning/scope_minimizer.py` | Audit용 Socratic 질문 생성기 |
| 1.2 | `lib/oda/planning/tier_analyzer.py` | 3-Tier Progressive 분석 엔진 |

**scope_minimizer.py 설계:**
```python
class ScopeMinimizer:
    """
    ClarificationTracker를 활용한 Audit Scope 최소화.
    Socratic-Questioning으로 사용자 요구사항 명확화.
    """
    def __init__(self, tracker: ClarificationTracker):
        self.tracker = tracker

    def generate_scope_questions(self, user_input: str) -> List[Question]:
        """Scope 관련 Socratic 질문 생성."""

    def minimize_scope(self, responses: Dict) -> MinimizedScope:
        """응답 기반 최소 Scope 결정."""

    def get_focused_targets(self, scope: MinimizedScope) -> List[str]:
        """최소화된 대상 경로 반환."""
```

**tier_analyzer.py 설계:**
```python
class TierLevel(Enum):
    STRUCTURE = "tier_1"  # 파일/디렉토리
    FUNCTION = "tier_2"   # API/시그니처
    LOGIC = "tier_3"      # 코드 라인

class TierAnalyzer:
    """
    3-Tier Progressive Deep-Dive 분석 엔진.
    모든 Tier 실행 후 계층별 보고.
    """
    def analyze_tier(self, tier: TierLevel, target: str) -> TierResult:
        """개별 Tier 분석 실행."""

    def execute_progressive(self, target: str) -> ProgressiveResult:
        """3-Tier 순차 실행 (전체 실행 후 보고)."""

    def generate_layer_report(self, results: List[TierResult]) -> LayerReport:
        """계층별 통합 보고서 생성."""
```

---

### Phase 2: /audit 스킬 재설계

| Task | Changes |
|------|---------|
| 2.1 | Socratic-Questioning 진입점 추가 |
| 2.2 | ScopeMinimizer 통합 |
| 2.3 | 중복 섹션 제거 (~600 lines) |

**변경 전 (audit.md 현재):**
```markdown
# 1. Pre-Mutation Zone Definition
# 2. 4-Stream Architecture
# 3. Parallel Execution Rules (중복)
# 4. Output Budget (중복)
...
~1300 lines
```

**변경 후 (audit.md 목표):**
```markdown
---
name: audit
version: "3.0"
---

# /audit Skill (V3.0)

## 1. Scope Minimization Protocol
- ScopeMinimizer integration
- Socratic questions BEFORE execution
- ClarificationTracker state machine

## 2. Focused Execution
- Minimized scope targets only
- Quality checks on confirmed areas

## 3. Quick Reference
→ .claude/references/audit-execution.md

~200 lines (압축)
```

---

### Phase 3: /deep-audit 스킬 재설계

| Task | Changes |
|------|---------|
| 3.1 | 4-Stream → 3-Tier 전환 |
| 3.2 | TierAnalyzer 통합 |
| 3.3 | RSIL → Progressive Layer Report 전환 |
| 3.4 | 중복 섹션 제거 (~800 lines) |

**변경 전 (deep-audit.md 현재):**
```markdown
# 1. Skill Overview
# 2. 4 Parallel Analysis Streams
# 3. RSIL Synthesis Algorithm (5 phases)
# 4. Parallel Execution Rules (중복)
# 5. Block Enforcement
...
~1555 lines
```

**변경 후 (deep-audit.md 목표):**
```markdown
---
name: deep-audit
version: "2.0"
---

# /deep-audit Skill (V2.0)

## 1. 3-Tier Progressive Deep-Dive
- Tier 1: Structure (files/directories)
- Tier 2: Function (APIs, signatures)
- Tier 3: Logic (code lines)

## 2. Execution Flow
- Execute ALL tiers sequentially
- Collect findings per tier
- Generate layer report

## 3. Block Enforcement
- CRITICAL/ERROR blocking rules
- Override policies

## 4. Quick Reference
→ .claude/references/deep-audit-execution.md

~250 lines (압축)
```

---

### Phase 4: 참조문서 생성/업데이트

| Task | File | Content |
|------|------|---------|
| 4.1 | `.claude/references/audit-execution.md` | 상세 실행 패턴 |
| 4.2 | `.claude/references/deep-audit-execution.md` | 3-Tier 상세 구현 |
| 4.3 | `.claude/references/parallel-execution.md` | 공통 패턴 통합 (중복 제거) |

**parallel-execution.md (공통화):**
```markdown
# Parallel Execution Patterns (Shared)

## Boris Cherny Pattern
- run_in_background=true MANDATORY
- Output budget constraints
- TodoWrite progress tracking

Used by: /audit, /deep-audit, /plan
```

---

### Phase 5: __init__.py 및 통합

| Task | File | Changes |
|------|------|---------|
| 5.1 | `lib/oda/planning/__init__.py` | Export ScopeMinimizer, TierAnalyzer |
| 5.2 | ExecutionOrchestrator | Integration hooks |

---

### Phase 6: E2E 검증

| Scenario | Expected |
|----------|----------|
| /audit without scope | Socratic questions 발생 |
| /audit with scope | Focused execution |
| /deep-audit full | 3-Tier 순차 실행 |
| /deep-audit tier report | 계층별 보고서 |

---

## Critical File Paths

```yaml
new_files:
  - lib/oda/planning/scope_minimizer.py      # Scope 최소화 모듈
  - lib/oda/planning/tier_analyzer.py        # 3-Tier 분석 엔진
  - .claude/references/audit-execution.md    # /audit 상세
  - .claude/references/deep-audit-execution.md  # /deep-audit 상세

modified_files:
  - .claude/skills/audit.md                  # 1300→200 lines
  - .claude/skills/deep-audit.md             # 1555→250 lines
  - lib/oda/planning/__init__.py             # New exports
  - .claude/references/parallel-execution.md # 공통 패턴 통합

integration_dependencies:
  - lib/oda/planning/clarification_tracker.py  # V2.1.8
  - lib/oda/planning/task_decomposer.py        # 32K compliance
  - lib/oda/planning/execution_orchestrator.py # Main facade
```

---

## Execution Strategy

| Phase | Effort | Subagent | Context |
|-------|--------|----------|---------|
| Phase 1 | medium | general-purpose | fork |
| Phase 2 | medium | Direct | standard |
| Phase 3 | medium | Direct | standard |
| Phase 4 | small | Direct | standard |
| Phase 5 | small | Direct | standard |
| Phase 6 | small | Direct | standard |

---

## Success Criteria

- [ ] /audit: Socratic-Questioning 후에만 실행
- [ ] /audit: Scope 최소화로 토큰 절약
- [ ] /deep-audit: 3-Tier Progressive 구현
- [ ] /deep-audit: 계층별 보고서 출력
- [ ] 중복 코드 ~2000 lines 제거
- [ ] 스킬 파일 크기 70%+ 압축

---

## Risk Register

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | Socratic 질문 과다 | MEDIUM | MAX_ROUNDS=3 제한 |
| R2 | Tier 분석 시간 증가 | LOW | 병렬 실행 유지 |
| R3 | 기존 워크플로우 호환성 | MEDIUM | 점진적 마이그레이션 |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT                                │
└─────────────────────────────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│    /audit       │                 │  /deep-audit    │
│   (V3.0)        │                 │    (V2.0)       │
└─────────────────┘                 └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│ ScopeMinimizer  │                 │  TierAnalyzer   │
│ + Clarification │                 │ 3-Tier Engine   │
│    Tracker      │                 │                 │
└─────────────────┘                 └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│ Socratic Q's    │                 │ Tier 1:Structure│
│ → Minimize      │                 │ Tier 2:Function │
│ → Focus         │                 │ Tier 3:Logic    │
└─────────────────┘                 └─────────────────┘
         │                                   │
         ▼                                   ▼
┌─────────────────┐                 ┌─────────────────┐
│ Focused Audit   │                 │ Layer Report    │
│ (minimal scope) │                 │ (tier-by-tier)  │
└─────────────────┘                 └─────────────────┘
```

---

> **핵심 설계 원칙:**
> - /audit = Scope 최소화 → 집중 검사
> - /deep-audit = 3-Tier 전체 실행 → 계층 보고
> - 중복 제거 → 공통 참조문서로 통합
