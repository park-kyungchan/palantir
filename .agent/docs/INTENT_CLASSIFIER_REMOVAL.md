# IntentClassifier 제거 가능성 검토

> **Status:** PENDING (유지 결정)
> **Date:** 2026-01-16
> **Version:** V2.1.7

---

## 배경

### 질문
"LLM-Native Intent Routing"에서 IntentClassifier가 왜 필요한가?
Claude Code 환경에서는 Main Agent가 직접 LLM이므로 불필요한 것 아닌가?

### 결론
**맞다.** Claude Code 전용 환경에서는 IntentClassifier가 불필요하다.
하지만 현재 `SkillRouter`가 의존하고 있어 단순 삭제 불가.

---

## 아키텍처 분석

### LLM-Native Intent Routing의 두 가지 모드

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code 환경 (현재)                       │
│                                                                 │
│  User Input → Main Agent (LLM) → 직접 추론 → Skill 호출         │
│                                                                 │
│  ✅ IntentClassifier 불필요                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    외부 스크립트/API 환경                        │
│                                                                 │
│  User Input → IntentClassifier → LLM API 호출 → Skill 결정      │
│                                                                 │
│  ✅ IntentClassifier 필수                                       │
└─────────────────────────────────────────────────────────────────┘
```

### ODA 거버넌스와의 관계

```
IntentClassifier ≠ ODA Governance

IntentClassifier = Skill 라우팅 도우미 (선택적)
ODA Proposal    = 실행 거버넌스 (필수)
```

| 컴포넌트 | 역할 | 필수 여부 |
|---------|------|----------|
| IntentClassifier | "어떤 작업을 할까?" | 선택적 |
| ODA Proposal | "어떻게 안전하게 실행할까?" | 필수 |

---

## 현재 의존성 구조

### 영향받는 파일

| 파일 | 의존 방식 | 영향도 |
|------|----------|--------|
| `lib/oda/pai/skills/__init__.py` | export | 높음 |
| `lib/oda/pai/skills/router.py` | 직접 사용 | 높음 |
| `lib/oda/pai/skills/intent_classifier.py` | 삭제 대상 | - |

### 코드 참조

**`router.py` (SkillRouter):**
```python
from .intent_classifier import IntentClassifier, IntentClassifierConfig

class SkillRouter:
    def __init__(self):
        self._classifier = IntentClassifier(
            config=IntentClassifierConfig(adapter_type="claude")
        )
```

**`__init__.py` (exports):**
```python
from lib.oda.pai.skills.intent_classifier import (
    IntentClassifier,
    IntentClassifierConfig,
    IntentResult,
    create_intent_classifier,
)

__all__ = [
    "IntentClassifier",
    "IntentClassifierConfig",
    # ...
]
```

---

## 제거 작업 계획 (향후)

### Phase 1: SkillRouter 리팩토링
```python
# Before
class SkillRouter:
    def __init__(self):
        self._classifier = IntentClassifier(...)

    async def route(self, user_input: str):
        result = await self._classifier.classify(user_input)
        return result.command

# After (Claude Code 전용)
class SkillRouter:
    def __init__(self):
        pass  # No classifier needed

    async def route(self, user_input: str):
        # Main Agent handles routing directly
        raise NotImplementedError("Use Main Agent for routing in Claude Code")
```

### Phase 2: Export 정리
```python
# __init__.py - IntentClassifier 관련 export 제거
# 또는 Optional import로 변경
```

### Phase 3: 파일 삭제
```bash
rm lib/oda/pai/skills/intent_classifier.py
rm -rf lib/oda/llm/adapters/  # 어댑터들
rm lib/oda/llm/intent_adapter.py
```

---

## 결정

### 현재 결정: 유지

**이유:**
1. 토큰 사용량 제약 (Claude Max X5)
2. SkillRouter 리팩토링 필요
3. 외부 환경 지원 유지 가능성

### 향후 액션

| 우선순위 | 작업 | 예상 토큰 |
|---------|------|----------|
| Low | SkillRouter에서 IntentClassifier 의존성 제거 | 5-8K |
| Low | __init__.py export 정리 | 1-2K |
| Low | intent_classifier.py 삭제 | 0.5K |

---

## 참고: LLM-Agnostic 설계

IntentClassifier는 LLM 독립적 설계:

```python
# Adapter Protocol (LLM-agnostic)
class IntentAdapter(Protocol):
    async def classify(self, user_input, commands) -> IntentResult:
        ...

# Concrete Adapters (LLM-specific)
- ClaudeIntentAdapter
- OpenAIIntentAdapter
- GeminiIntentAdapter
- LocalIntentAdapter
```

Claude Code 외부 환경에서 ODA를 사용할 경우, 이 설계가 유용할 수 있음.

---

## 관련 문서

- `.claude/CLAUDE.md` Section 8: PAI Integration (V4.0 LLM-Native Intent Routing)
- `lib/oda/pai/skills/intent_classifier.py`: IntentClassifier 구현
- `lib/oda/pai/skills/router.py`: SkillRouter 구현
