# LLM-Native Intent Classification Implementation Plan

> **Version:** 2.0 | **Status:** COMPLETED | **Date:** 2026-01-13
> **Auto-Compact Safe:** This file persists across context compaction
> **Method:** SIMPLIFIED - LLM-Direct approach (no complex layers)

---

## Executive Summary

| Item | Value |
|------|-------|
| **Goal** | LLM에게 직접 의도 분류 위임 (키워드 감지 완전 제거) |
| **Complexity** | Medium (3 phases, 15 core tasks) |
| **Files to Create** | 6 |
| **Files to Modify** | 4 |
| **Files to DELETE** | 1 (trigger_detector.py 제거) |
| **Priority** | P0 (STAGE1 LLM-First) |
| **User Requirement** | "복잡한 과정 필요없이 LLM에게만 맡기려고 함" |

---

## User's Core Requirements (2026-01-13)

```yaml
기존_키워드_감지_로직: "완전 제거"
출력_형식: "커스텀 커맨드 고도화 (/ask, /plan, /deep-audit)"
비용_속도_우선순위: "실제 코드 수정 전까지는 LLM의 최대성능과 기능을 최대로 활용"
Claude_버전: "V2.1.4 최신 기능 반드시 사용"
```

**핵심 원칙:**
- TriggerDetector 완전 제거 (Jaccard, Regex, Keyword 모두 삭제)
- LLM에게 직접 "이 요청이 어떤 커맨드에 해당하는지" 질문
- 복잡한 Embedding Cache, Multi-layer fallback 불필요
- Claude V2.1.4: context:fork, run_in_background, resume parameter 활용

---

## Architecture: SIMPLIFIED LLM-Direct

### Before: 4-Phase Keyword Detection (TO BE DELETED)

```
┌─────────────────────────────────────────────────────────────────────┐
│              trigger_detector.py (729 lines) - DELETE              │
├─────────────────────────────────────────────────────────────────────┤
│  Phase 1: Exact Keyword Match   → REMOVE                           │
│  Phase 2: Regex Pattern Match   → REMOVE                           │
│  Phase 3: Jaccard Similarity    → REMOVE                           │
│  Phase 4: Default Fallback      → REMOVE                           │
└─────────────────────────────────────────────────────────────────────┘
```

### After: LLM-Direct Classification (SIMPLE)

```
┌─────────────────────────────────────────────────────────────────────┐
│              SIMPLIFIED LLM-DIRECT FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User: "코드 리뷰해줘" or "/ask 이 기능 분석해줘"                    │
│           │                                                         │
│           ▼                                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ IntentClassifier.classify(user_input, available_commands)    │  │
│  │                                                              │  │
│  │ → LLM receives:                                              │  │
│  │   - User input (raw)                                         │  │
│  │   - Available commands: [/ask, /plan, /audit, /deep-audit]   │  │
│  │   - Each command's semantic description                      │  │
│  │                                                              │  │
│  │ → LLM returns (structured JSON):                             │  │
│  │   { "command": "/audit", "confidence": 0.95,                 │  │
│  │     "reasoning": "User wants code review" }                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│           │                                                         │
│           ▼                                                         │
│  Execute matched command directly                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

NO COMPLEX LAYERS. NO FALLBACKS. JUST LLM.
```

---

## SIMPLIFIED Phase Overview

| Phase | Name | Tasks | Priority | Description |
|-------|------|-------|----------|-------------|
| 1 | LLM Adapter + IntentClassifier | 8 | P0 | LLM 어댑터 및 분류기 생성 |
| 2 | Router Integration + Cleanup | 4 | P0 | 라우터 통합, TriggerDetector 제거 |
| 3 | Documentation + Testing | 3 | P1 | 문서화, 테스트 |

**Total: 15 tasks** (기존 47개에서 대폭 축소)

---

## Phase 1: LLM Adapter + IntentClassifier (8 tasks)

> **Goal:** LLM 어댑터 및 의도 분류기 생성

### 1.1 Create LLMAdapter Base Interface
- **File:** `lib/oda/llm/intent_adapter.py` (NEW)
- **Purpose:** LLM-agnostic 추상 인터페이스
- **Contents:**
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional, Dict, Any
  from pydantic import BaseModel

  class IntentResult(BaseModel):
      command: str           # e.g., "/ask", "/plan", "/audit"
      confidence: float      # 0.0-1.0
      reasoning: str         # LLM's explanation
      raw_input: str         # Original user input

  class IntentAdapterBase(ABC):
      @abstractmethod
      async def classify(
          self,
          user_input: str,
          available_commands: List[Dict[str, str]],  # [{name, description}]
      ) -> IntentResult:
          """LLM에게 직접 의도 분류 요청"""
          ...
  ```
- **Status:** [ ] PENDING

### 1.2 Create ClaudeIntentAdapter
- **File:** `lib/oda/llm/adapters/claude_adapter.py` (NEW)
- **Purpose:** Claude Code 환경에서의 의도 분류
- **Note:** Claude Code에서는 Main Agent가 직접 LLM이므로, 이 어댑터는
          Tool Use를 통한 structured output 획득에 집중
- **Features:**
  - Native JSON mode (tool_use)
  - Prompt engineering for intent classification
- **Status:** [ ] PENDING

### 1.3 Create OpenAIIntentAdapter
- **File:** `lib/oda/llm/adapters/openai_adapter.py` (NEW)
- **Purpose:** GPT-4 implementation (function calling)
- **Status:** [ ] PENDING

### 1.4 Create GeminiIntentAdapter
- **File:** `lib/oda/llm/adapters/gemini_adapter.py` (NEW)
- **Purpose:** Gemini implementation
- **Status:** [ ] PENDING

### 1.5 Create LocalLLMAdapter
- **File:** `lib/oda/llm/adapters/local_adapter.py` (NEW)
- **Purpose:** Ollama/LM Studio (offline fallback)
- **Status:** [ ] PENDING

### 1.6 Create IntentClassification ObjectType
- **File:** `lib/oda/ontology/objects/intent_types.py` (NEW)
- **Purpose:** ODA ObjectType for intent tracking
- **Contents:**
  ```python
  from lib.oda.ontology.registry import register_object_type
  from lib.oda.ontology.objects.base import OntologyObject
  from enum import Enum

  class IntentMatchType(str, Enum):
      EXPLICIT = "explicit"    # User used /command directly
      SEMANTIC = "semantic"    # LLM inferred from natural language
      FALLBACK = "fallback"    # Low confidence, needs clarification

  @register_object_type
  class IntentClassification(OntologyObject):
      command: str
      confidence: float
      reasoning: str
      match_type: IntentMatchType
      user_input: str
  ```
- **Status:** [ ] PENDING

### 1.7 Create IntentClassifier Core
- **File:** `lib/oda/pai/skills/intent_classifier.py` (NEW)
- **Purpose:** TriggerDetector 대체 (단순 버전)
- **Contents:**
  ```python
  class IntentClassifier:
      """
      LLM-Direct Intent Classifier.
      No keywords, no regex, no Jaccard. Just LLM.
      """

      def __init__(self, adapter: IntentAdapterBase):
          self.adapter = adapter
          self.available_commands = self._load_commands()

      async def classify(self, user_input: str) -> IntentResult:
          # 1. Check explicit command (starts with /)
          if user_input.strip().startswith('/'):
              return self._handle_explicit_command(user_input)

          # 2. LLM classification for natural language
          return await self.adapter.classify(
              user_input=user_input,
              available_commands=self.available_commands
          )

      def _load_commands(self) -> List[Dict[str, str]]:
          """Load from .claude/skills/ directory"""
          return [
              {"name": "/ask", "description": "요구사항 분석 및 명확화, 프롬프트 엔지니어링"},
              {"name": "/plan", "description": "구현 계획 수립, 아키텍처 설계"},
              {"name": "/audit", "description": "코드 품질 검사, 3-Stage Protocol"},
              {"name": "/deep-audit", "description": "심층 분석, RSIL 방법론"},
              # ... more commands
          ]
  ```
- **Status:** [ ] PENDING

### 1.8 Create Intent Prompt Template
- **File:** `lib/oda/pai/skills/prompts/intent_prompts.py` (NEW)
- **Purpose:** LLM에게 보낼 의도 분류 프롬프트
- **Contents:**
  ```python
  INTENT_CLASSIFICATION_PROMPT = """
  You are an intent classifier for a development assistant.

  ## Available Commands
  {commands_with_descriptions}

  ## User Request
  "{user_input}"

  ## Task
  Classify this request. Which command best matches the user's intent?
  If the user's request doesn't clearly match any command, return "none".

  ## Output (JSON only)
  {"command": "/ask", "confidence": 0.95, "reasoning": "User wants clarification"}
  """
  ```
- **Status:** [ ] PENDING

---

## Phase 2: Router Integration + Cleanup (4 tasks)

> **Goal:** SkillRouter에 IntentClassifier 통합, TriggerDetector 완전 제거

### 2.1 Update SkillRouter Integration
- **File:** `lib/oda/pai/skills/router.py` (MODIFY)
- **Change:** `TriggerDetector` → `IntentClassifier` 교체
- **Before:**
  ```python
  from .trigger_detector import TriggerDetector
  self._detector = TriggerDetector()
  match = self._detector.detect(user_input)
  ```
- **After:**
  ```python
  from .intent_classifier import IntentClassifier
  self._classifier = IntentClassifier()
  result = await self._classifier.classify(user_input)
  ```
- **Status:** [ ] PENDING

### 2.2 DELETE trigger_detector.py
- **File:** `lib/oda/pai/skills/trigger_detector.py` (DELETE)
- **Lines:** 729 lines 전체 삭제
- **Reason:** 사용자 요구: "완전 제거"
- **Backup:** `.archive/deprecated/trigger_detector.py.bak`
- **Status:** [ ] PENDING

### 2.3 Update Skills __init__.py
- **File:** `lib/oda/pai/skills/__init__.py` (MODIFY)
- **Change:** Export IntentClassifier, remove TriggerDetector
- **Status:** [ ] PENDING

### 2.4 Add Low-Confidence Clarification Flow
- **File:** `lib/oda/pai/skills/router.py` (MODIFY)
- **Change:** confidence < 0.7이면 AskUserQuestion 사용
- **Contents:**
  ```python
  if result.confidence < 0.7:
      # Use native Claude capability
      return AskUserQuestion(
          question=f"이 요청이 '{result.command}'를 의미하는 건가요?",
          options=[result.command, "다른 명령"]
      )
  ```
- **Status:** [ ] PENDING

---

## Phase 3: Documentation + Testing (3 tasks)

> **Goal:** 문서화 및 기본 테스트

### 3.1 Update CLAUDE.md
- **File:** `/home/palantir/.claude/CLAUDE.md` (MODIFY)
- **Change:** LLM-Native Intent Classification 섹션 추가
- **Content:**
  - TriggerDetector 제거됨
  - IntentClassifier가 LLM 직접 호출
  - 커스텀 커맨드 고도화 설명
- **Status:** [ ] PENDING

### 3.2 Create Reference Documentation
- **File:** `.claude/references/intent-classification.md` (NEW)
- **Content:** 단순화된 아키텍처 문서
- **Status:** [ ] PENDING

### 3.3 Create Basic Tests
- **File:** `tests/oda/pai/skills/test_intent_classifier.py` (NEW)
- **Coverage:**
  - Explicit command detection (/ask, /plan)
  - LLM classification mock
  - Low confidence handling
- **Status:** [ ] PENDING

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 1 | 8 | 8 | 100% |
| 2 | 4 | 4 | 100% |
| 3 | 3 | 3 | 100% |
| **Total** | **15** | **15** | **100%** |

---

## Execution Strategy (SIMPLIFIED)

### Sequential Execution
이 작업은 순차적으로 진행 (의존성 있음):

1. **Phase 1.1-1.8**: LLM Adapter + IntentClassifier 생성
2. **Phase 2.1-2.4**: Router 통합, TriggerDetector 삭제
3. **Phase 3.1-3.3**: 문서화, 테스트

### Subagent Delegation (Minimal)

| Task Group | Subagent Type | Context | Description |
|------------|---------------|---------|-------------|
| Phase 1 | general-purpose | fork | 어댑터 및 분류기 생성 |
| Phase 2 | Direct execution | - | 파일 수정/삭제 |
| Phase 3 | general-purpose | fork | 문서화 |

---

## Quick Resume After Auto-Compact

```
1. Read: .agent/plans/llm_native_intent_classification.md
2. Check TodoWrite for current status
3. Find first PENDING task
4. Execute sequentially
```

---

## Critical File Paths (SIMPLIFIED)

```yaml
# Files to CREATE (6)
create:
  - lib/oda/llm/intent_adapter.py          # 1.1
  - lib/oda/llm/adapters/claude_adapter.py # 1.2
  - lib/oda/llm/adapters/openai_adapter.py # 1.3
  - lib/oda/llm/adapters/gemini_adapter.py # 1.4
  - lib/oda/llm/adapters/local_adapter.py  # 1.5
  - lib/oda/ontology/objects/intent_types.py # 1.6
  - lib/oda/pai/skills/intent_classifier.py  # 1.7
  - lib/oda/pai/skills/prompts/intent_prompts.py # 1.8
  - .claude/references/intent-classification.md # 3.2
  - tests/oda/pai/skills/test_intent_classifier.py # 3.3

# Files to MODIFY (3)
modify:
  - lib/oda/pai/skills/router.py          # 2.1
  - lib/oda/pai/skills/__init__.py        # 2.3
  - /home/palantir/.claude/CLAUDE.md      # 3.1

# Files to DELETE (1)
delete:
  - lib/oda/pai/skills/trigger_detector.py # 2.2 (729 lines)
```

---

## Risk Register (SIMPLIFIED)

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM latency | LOW | 커스텀 커맨드는 명시적 (/로 시작), LLM 호출 최소화 |
| TriggerDetector 제거 후 호환성 | LOW | 사용자가 "완전 제거" 명시, 호환성 불필요 |
| Context compaction | HIGH | 이 plan 파일 + TodoWrite로 상태 유지 |

---

## Comparison: Before vs After

### User Input: "코드 리뷰해줘"

**Before (Keyword Detection - 729 lines):**
```
Phase 1 (Exact): "코드 리뷰해줘" not in keywords → NO MATCH
Phase 2 (Regex): No pattern matches → NO MATCH
Phase 3 (Jaccard): {"코드"} / words = low score → NO MATCH
Phase 4 (Default): general_skill → POOR ROUTING
```

**After (LLM-Direct - ~50 lines):**
```
1. Check explicit: "코드 리뷰해줘" doesn't start with / → LLM classification
2. LLM receives:
   - User input: "코드 리뷰해줘"
   - Available: [/ask, /plan, /audit, /deep-audit]
3. LLM returns: {command: "/audit", confidence: 0.92, reasoning: "코드 리뷰 요청"}
4. Execute /audit
```

---

## Claude V2.1.4 Features to Use

| Feature | Usage |
|---------|-------|
| `context:fork` | IntentClassifier를 isolated context에서 실행 |
| `run_in_background` | 대규모 분석 시 background agent 활용 |
| `resume` parameter | Agent 상태 복원 |
| `AskUserQuestion` | Low confidence 시 명확화 질문 |
| Structured output | Intent classification JSON 획득 |

---

## Approval Gate

- [x] 사용자 요구 확인: "완전 제거", "커스텀 커맨드 고도화"
- [x] Phase 1 구현 (LLM Adapter + IntentClassifier)
- [x] Phase 2 구현 (TriggerDetector 삭제, Router 통합)
- [x] Phase 3 구현 (문서화, 테스트)

---

> **Generated:** 2026-01-13 by Main Agent Orchestrator
> **Version:** 2.0 (SIMPLIFIED)
> **User Requirements:**
>   - "복잡한 과정 필요없이 LLM에게만 맡기려고 함"
>   - "완전 제거" (TriggerDetector)
>   - "커스텀 커맨드 고도화"
>   - "실제 코드 수정 전까지는 LLM의 최대성능과 기능을 최대로 활용"
