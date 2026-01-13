---
name: memory-sync
description: Sync CLI memories to Orion semantic memory system
---

# /memory-sync Command

$ARGUMENTS

CLI에서 축적된 메모리를 Orion 시맨틱 메모리 시스템으로 동기화합니다.

---

## 동기화 대상

| 소스 | 대상 |
|------|------|
| Claude Code 대화 기록 | `.agent/memory/semantic/insights/` |
| 학습된 패턴 | `.agent/memory/semantic/patterns/` |
| 세션 트레이스 | `.agent/traces/` |

---

## 사용법

```
/memory-sync              # 전체 동기화
/memory-sync insights     # Insights만 동기화
/memory-sync patterns     # Patterns만 동기화
```

---

## 실행

```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
python scripts/memory_sync.py
```

---

## 수동 동기화 프로세스

### 1. 현재 세션에서 중요한 인사이트 추출
```python
# 현재 대화에서 학습한 내용을 인사이트로 변환
insight = {
    "id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "title": "Session Learning",
    "content": "학습한 내용 요약",
    "source": "claude_code_session",
    "tags": ["session", "learning"],
    "created_at": datetime.now(UTC).isoformat(),
    "relevance_score": 0.8
}
```

### 2. 패턴 추출
```python
# 반복되는 코드 패턴을 저장
pattern = {
    "id": f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "name": "Pattern Name",
    "description": "패턴 설명",
    "template": "패턴 템플릿 또는 코드",
    "use_cases": ["사용 케이스"],
    "examples": ["예시"],
    "created_at": datetime.now(UTC).isoformat()
}
```

### 3. 파일로 저장
```bash
# Insight 저장
echo '$INSIGHT_JSON' > .agent/memory/semantic/insights/new_insight.json

# Pattern 저장
echo '$PATTERN_JSON' > .agent/memory/semantic/patterns/new_pattern.json
```

---

## 자동 동기화 설정

Hook을 사용하여 세션 종료 시 자동 동기화:

```json
// settings.json의 hooks 섹션
{
  "SessionEnd": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "/home/palantir/park-kyungchan/palantir/scripts/memory_sync.py"
        }
      ]
    }
  ]
}
```

---

## 동기화 결과

```
=== Memory Sync Report ===
Insights synced: 5
Patterns synced: 2
Traces archived: 10
Duration: 1.2s
Status: SUCCESS
```

---

## 참조

- Insight Schema: `.agent/schemas/insight.schema.json`
- Pattern Schema: `.agent/schemas/pattern.schema.json`
- Memory Directory: `.agent/memory/semantic/`
