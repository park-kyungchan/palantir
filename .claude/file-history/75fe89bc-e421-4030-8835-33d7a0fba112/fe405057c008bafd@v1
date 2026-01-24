---
name: plan-draft
description: |
  Socratic Q&A를 통해 /plan 실행을 위한 초안을 작성합니다.
  매 턴마다 2-3개 질문으로 요구사항을 명확화하고, 파일 탐색 결과를 요약합니다.
  Use when: 요구사항이 모호하거나, 계획 전 명확화가 필요할 때
allowed-tools: Read, Grep, Glob, Task, TodoWrite, AskUserQuestion, WebSearch
argument-hint: <초기 요구사항 또는 아이디어>
---

# /plan-draft Command

**목적:** `/plan` 실행 전 Socratic Questioning으로 요구사항을 명확화하고 초안을 작성합니다.

## Arguments
$ARGUMENTS - 초기 요구사항 또는 아이디어 (Korean or English)

---

## Core Principle: Index-Based Progressive Loading

Draft 파일은 **INDEX + DETAIL** 구조로 토큰 효율성을 극대화합니다:

```
draft_{slug}.md
├── INDEX (~500 tokens) ← /plan이 항상 먼저 읽음
│   ├── 요구사항 요약
│   ├── Q&A 핵심 3개
│   ├── 파일 요약
│   ├── 리스크
│   └── 다음 단계
│
└── DETAIL SECTIONS ← 필요 시만 Explore Agent가 읽음
    ├── #qa-log
    ├── #requirements
    ├── #file-analysis
    └── #risk-analysis
```

---

## Execution Flow

### Step 1: Initialize Draft File

```python
import re
from datetime import datetime

# Generate slug
slug = re.sub(r'[^a-z0-9_]', '_', requirements[:50].lower())
slug = re.sub(r'_+', '_', slug).strip('_')
draft_path = f".agent/plans/draft_{slug}.md"

# Create initial draft
Write(draft_path, DRAFT_TEMPLATE)
```

### Step 2: Socratic Q&A Loop

**매 턴마다 2-3개 질문:**

```markdown
## Socratic Questioning Protocol

1. **이해 확인 (Understanding)**
   - 내가 이해한 내용을 먼저 요약
   - "제가 이해한 바로는... 맞나요?"

2. **명확화 질문 (Clarification)**
   - 모호한 부분 2-3개 질문
   - AskUserQuestion 또는 직접 질문

3. **탐색 제안 (Exploration)**
   - 필요시 파일 탐색 제안
   - "관련 파일을 탐색해볼까요?"
```

**질문 예시:**
```
AskUserQuestion(questions=[
    {
        "question": "이 기능의 주요 사용자는 누구인가요?",
        "header": "Target User",
        "options": [
            {"label": "일반 사용자", "description": "..."},
            {"label": "관리자", "description": "..."},
            {"label": "API 클라이언트", "description": "..."}
        ],
        "multiSelect": false
    },
    {
        "question": "기존 코드와의 통합 방식은?",
        "header": "Integration",
        "options": [
            {"label": "새 모듈 생성", "description": "..."},
            {"label": "기존 모듈 확장", "description": "..."}
        ],
        "multiSelect": false
    }
])
```

### Step 3: File Exploration (필요 시)

```python
# Explore Agent로 파일 탐색 (Main Context 오염 방지)
Task(
    subagent_type="Explore",
    prompt="""
    ## Task
    다음 요구사항과 관련된 파일을 탐색하세요:
    {requirements}

    ## Output Format (요약만)
    ```yaml
    relevant_files:
      - path: "..."
        relevance: "높음/중간/낮음"
        summary: "1줄 요약"

    patterns_found:
      - pattern: "..."
        files: ["..."]

    recommendations:
      - "..."
    ```

    ## Constraint
    OUTPUT MUST NOT EXCEED 3000 TOKENS.
    """,
    description="Explore files for draft"
)
```

### Step 4: Update Draft File

**매 Q&A 라운드 후 draft 파일 업데이트:**

```python
# INDEX 섹션 업데이트
update_index(draft_path, {
    "qa_summary": [...],
    "file_summary": [...],
    "risks": [...],
    "next_steps": "..."
})

# DETAIL 섹션에 전체 로그 추가
append_detail(draft_path, "qa-log", qa_round)
```

### Step 5: Exit Condition

사용자가 다음 중 하나를 입력하면 종료:
- `/plan` - draft를 기반으로 plan 실행
- `/plan-draft 종료` - draft 저장 후 종료
- `완료`, `끝`, `done` - draft 완성으로 표시

**종료 시 안내:**
```markdown
## Draft 완성

Draft 파일이 저장되었습니다: `.agent/plans/draft_{slug}.md`

### 다음 단계
1. `/plan` 실행 시 이 draft가 자동으로 참조됩니다
2. 또는 `/plan --draft {slug}`로 명시적 지정 가능

### INDEX 요약
{index_content}
```

---

## Draft File Template

```markdown
# Draft: {title}

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** {date}
> **Auto-Compact Safe:** This file persists across context compaction

---

## INDEX

### 요구사항 요약
{1-2문장 요약}

### Complexity
- **예상 복잡도:** {small | medium | large}
- **영향 파일:** {N}개 ([상세](#file-analysis))

### Q&A 핵심
1. **Q:** {질문1 요약} → **A:** {답변1 핵심}
2. **Q:** {질문2 요약} → **A:** {답변2 핵심}
3. **Q:** {질문3 요약} → **A:** {답변3 핵심}

### 추천 접근법
{1-2문장으로 추천 방향}

### 리스크
- {리스크1}
- {리스크2}

### 다음 단계
`/plan` 실행 권장. Draft 참조: `--draft {slug}` 또는 자동 감지.

---

## DETAIL: Q&A 전체 로그 {#qa-log}

### Round 1 ({timestamp})
**Q:** {질문}
**A:** {답변}

### Round 2 ({timestamp})
...

---

## DETAIL: 요구사항 상세 {#requirements}

### 기능 요구사항
- FR1: {설명}
- FR2: {설명}

### 비기능 요구사항
- NFR1: {성능/보안 등}

---

## DETAIL: 파일 분석 결과 {#file-analysis}

### 관련 파일 목록
| 파일 | 관련도 | 역할 |
|------|--------|------|
| {path} | 높음 | {설명} |

### 패턴 분석
{Explore Agent 결과 요약}

---

## DETAIL: 리스크 분석 {#risk-analysis}

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| {리스크} | High/Medium/Low | {방안} |

---

## Metadata

- Created: {timestamp}
- Last Updated: {timestamp}
- Q&A Rounds: {count}
- Status: IN_PROGRESS | COMPLETED | ABANDONED
```

---

## /plan Integration

### 자동 감지 모드
`/plan` 실행 시 `.agent/plans/draft_*.md` 파일 자동 검색:

```python
# /plan 시작 시
drafts = Glob(".agent/plans/draft_*.md")
if drafts:
    latest_draft = sorted(drafts, key=modification_time)[-1]
    # INDEX만 먼저 읽음
    index = Read(latest_draft, offset=0, limit=50)  # ~500 tokens

    AskUserQuestion(questions=[{
        "question": f"기존 draft를 참조할까요? ({latest_draft})",
        "header": "Draft Reference",
        "options": [
            {"label": "예, 참조", "description": "Draft INDEX 기반으로 plan 시작"},
            {"label": "아니오, 새로 시작", "description": "Draft 무시하고 새 plan"}
        ]
    }])
```

### 명시적 지정 모드
```
/plan --draft {slug}
/plan --draft user_auth_feature
```

---

## Claude-Code-Guide Integration

매 세션 시작 시 최신 기능 소개:

```python
# 첫 Q&A 라운드에서
Task(
    subagent_type="claude-code-guide",
    prompt="""
    사용자 요구사항: {requirements}

    이 요구사항 구현에 도움이 될 수 있는
    Claude Code의 최신 기능을 2-3개 추천해주세요.

    Output: 기능명 + 1줄 설명 + 활용 방법
    """,
    description="Recommend Claude Code features"
)
```

---

## Usage Examples

### 기본 사용
```
/plan-draft 사용자 인증 기능 추가하고 싶어
```

### 모호한 요청
```
/plan-draft 성능 개선이 필요해
```
→ Socratic Q&A로 "어떤 부분?", "측정 기준?", "목표 수치?" 명확화

### 복잡한 요청
```
/plan-draft 다음 기능들 구현:
1. 태그 시스템
2. 검색 기능
3. 대시보드
```
→ 각 기능별로 Q&A 진행, 우선순위 결정

---

## State Management

### Auto-Compact 대응
Draft 파일이 `.agent/plans/`에 저장되어 Auto-Compact 후에도 유지.

### 세션 재개
```python
# Auto-Compact 후 재개 시
if Read(".agent/plans/draft_{slug}.md"):
    # 마지막 Q&A 라운드 확인
    # 이어서 진행
```

---

## Quality Gates

| 게이트 | 조건 | 통과 기준 |
|--------|------|----------|
| 최소 Q&A | 2라운드 이상 | ✓ |
| 요구사항 명확성 | complexity 판단 가능 | ✓ |
| 파일 탐색 | 1회 이상 Explore | 선택 |
| 리스크 식별 | 1개 이상 | ✓ |

---

## Error Handling

| 상황 | 처리 |
|------|------|
| 사용자 무응답 | 3회 재질문 후 현재 상태로 저장 |
| Explore 실패 | 파일 탐색 없이 진행, 경고 표시 |
| Draft 파일 손상 | 백업에서 복구 또는 새로 시작 |

---

## Output Format

최종 출력:

```markdown
## /plan-draft 완료

### Draft 요약 (INDEX)
{index_content}

### 저장 위치
`.agent/plans/draft_{slug}.md`

### 다음 단계
- `/plan` 실행 시 이 draft가 자동 참조됩니다
- 또는 `/plan --draft {slug}`로 명시적 지정

### 추천
요구사항이 충분히 명확해졌습니다. `/plan` 실행을 권장합니다.
```
