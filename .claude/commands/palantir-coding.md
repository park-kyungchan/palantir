---
name: palantir-coding
description: |
  프로그래밍 개념 학습 및 빠른 레퍼런스를 위한 통합 커맨드.
  A+B Mode: Learning Assistant (Socratic) + Quick Reference (Direct)
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║ TOOLS: Full access for KB navigation and learning support                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
allowed-tools: Read, Grep, Glob, AskUserQuestion, Task, WebSearch, TodoWrite
---

# /palantir-coding Command

$ARGUMENTS

프로그래밍 개념 학습 및 빠른 레퍼런스 시스템:
1. **Mode A (Learning)**: Socratic 방식으로 개념 깊이 이해
2. **Mode B (Reference)**: 빠른 KB 검색 및 직접 답변

---

## Layer1: Quick Start

```bash
/palantir-coding <query>
```

**Automatic Mode Detection:**
| Query Pattern | Mode | Behavior |
|---------------|------|----------|
| "왜...", "어떻게...", "how...", "why..." | Learning (A) | Socratic dialogue |
| "빠르게...", "요약...", "quick...", "list..." | Reference (B) | Direct KB answer |
| "X vs Y", "비교...", "면접..." | Hybrid (A->B) | Learn then reference |

**Examples:**
```bash
/palantir-coding 클로저가 뭐야?        # -> Mode A (Socratic)
/palantir-coding SQL JOIN 정리해줘    # -> Mode B (Direct)
/palantir-coding const vs let 차이    # -> Hybrid
```

**KB Categories:**
| Category | Topics | Files |
|----------|--------|-------|
| Language Core | Binding, Scope, Types | F01-F24 |
| Control Flow | Conditionals, Loops, Exceptions | F30-F34 |
| Functions | Parameters, HOF, Closures | F40-F44 |
| Collections | Arrays, Maps, Sets, Strings | F50-F54 |
| Data | SQL, Spark | 10a, 11a |

**Output Formats:**
| Mode | Output Style |
|------|--------------|
| Learning | Socratic question -> Insight block -> Practice |
| Reference | Quick table -> Tip -> Related KB |
| Hybrid | Concept question -> Comparison matrix |

---

## Layer2: Detailed Reference

### Orchestration Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                   PALANTIR-CODING FLOW (A+B)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌──────────────────┐                          │
│  │   User      │ ──► │  Intent Detect   │                          │
│  │   Query     │     │  (Main Agent)    │                          │
│  └─────────────┘     └────────┬─────────┘                          │
│                               │                                     │
│              ┌────────────────┼────────────────┐                   │
│              ▼                ▼                ▼                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │  Mode A       │  │  Mode B       │  │  Hybrid       │          │
│  │  LEARNING     │  │  REFERENCE    │  │  A → B        │          │
│  │  (Socratic)   │  │  (Direct KB)  │  │  (Learn+Ref)  │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│         │                   │                  │                   │
│         ▼                   ▼                  ▼                   │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              KB System (62+ Files)                   │          │
│  │  ├── F-Series (F01-F54): 30 concept files           │          │
│  │  ├── Critical (10a, 11a): SQL/Spark                  │          │
│  │  └── Legacy (00-22): Domain-specific                 │          │
│  └─────────────────────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### KB System Overview

#### File Inventory

| Series | Files | Concepts | Quality |
|--------|-------|----------|---------|
| **F01-F05** | 5 | Binding, Mutability, Constants, Declaration, Shadowing | 100% |
| **F10-F14** | 5 | Lexical/Dynamic Scope, Block Scope, Hoisting, Closures | 100% |
| **F20-F24** | 5 | Static/Dynamic Typing, Inference, Coercion, Structural, Generics | 100% |
| **F30-F34** | 5 | Conditionals, Loops, Exceptions, Pattern Matching, Control Flow | 100% |
| **F40-F44** | 5 | Functions, Parameters, Returns, Higher-Order, Closures | 100% |
| **F50-F54** | 5 | Arrays, Maps, Sets, Strings, Iterables | 100% |
| **10a** | 1 | SQL Fundamentals (DDL, DML, Joins, Window, CTE) | 86% |
| **11a** | 1 | Spark Basics (RDD, DataFrame, Transformations) | 86% |
| **00-22** | 30 | Legacy domain-specific KBs | 60% |

#### KB Path
```
/home/palantir/park-kyungchan/palantir/coding/knowledge_bases/
```

### Mode Detection (Main Agent Logic)

#### User Query -> Mode Selection

```python
# Main Agent applies this decision tree:

if query contains ["왜", "why", "어떻게", "how", "원리", "개념", "설명해줘"]:
    → Mode A (Learning) - Socratic questioning

elif query contains ["차이", "비교", "vs", "difference", "versus"]:
    → Hybrid A→B - Learn concept, then reference matrix

elif query contains ["빠르게", "quick", "요약", "summary", "표", "정리"]:
    → Mode B (Reference) - Direct KB lookup

elif query contains ["면접", "interview", "질문", "자주 나오는"]:
    → Hybrid - Interview prep with KB reference

else:
    → Default: Mode B (quick answer), offer Mode A for deeper learning
```

#### Query Examples

| Query | Detected Mode | Target KB |
|-------|---------------|-----------|
| "const와 let의 차이" | Hybrid A→B | F03_constant_semantics |
| "클로저가 뭐야?" | Mode A | F44_closures |
| "Python 리스트 메서드 요약" | Mode B | F50_arrays_lists |
| "면접에서 호이스팅" | Hybrid | F13_hoisting |
| "빠르게 SQL JOIN 정리" | Mode B | 10a_sql_fundamentals |
| "왜 String은 불변이야?" | Mode A | F02_mutability_patterns |
| "7개 언어 타입 시스템 비교" | Mode B | F20_static_vs_dynamic |

### Mode A: Learning Assistant (Socratic)

#### Philosophy
- **Don't just answer - guide discovery**
- Ask questions that lead to understanding
- Use KB as foundation, not direct answer

#### Socratic Flow

```
1. Receive concept query
2. Read relevant KB (F-Series preferred)
3. Ask clarifying question based on KB content
4. Guide user to insight
5. Confirm understanding with KB reference
6. Offer practice/extension
```

#### Example Interaction

```
User: "/palantir-coding 클로저가 뭐야?"

Agent (Mode A):
┌─────────────────────────────────────────────────────┐
│ 🎓 Learning Mode: Closures                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 먼저 질문 하나 드릴게요:                              │
│                                                     │
│ 다음 코드에서 `counter`는 호출될 때마다              │
│ 어떻게 `count` 값을 기억할까요?                      │
│                                                     │
│ ```javascript                                       │
│ function makeCounter() {                            │
│   let count = 0;                                    │
│   return function() {                               │
│     return ++count;                                 │
│   };                                                │
│ }                                                   │
│ const counter = makeCounter();                      │
│ console.log(counter()); // 1                        │
│ console.log(counter()); // 2                        │
│ ```                                                 │
│                                                     │
│ 힌트: `count` 변수는 `makeCounter` 실행 후에도      │
│       메모리 어딘가에 살아있어야 합니다.              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### After User Response

```
Agent:
정확합니다! 이것이 바로 "클로저"입니다.

★ Insight ─────────────────────────────────────────────
1. 클로저 = 함수 + 그 함수가 생성될 때의 환경(스코프)
2. 내부 함수가 외부 함수의 변수를 "캡처"하여 유지
3. 이것이 가능한 이유: Lexical Scope (F10 참조)
─────────────────────────────────────────────────────

📚 더 깊이 알고 싶다면:
- F44_closures.md: 7개 언어 클로저 비교
- F10_lexical_scope.md: 왜 클로저가 작동하는지

🎯 실습 제안:
Python에서 같은 패턴을 만들어 보세요!
```

### Mode B: Quick Reference (Direct)

#### Philosophy
- **Fast, accurate, structured**
- Direct KB lookup and extraction
- Formatted for quick scanning

#### Reference Flow

```
1. Receive reference query
2. Search KB with Grep/Glob
3. Read relevant section
4. Extract and format answer
5. Provide KB source
```

#### Example Interaction

```
User: "/palantir-coding SQL JOIN 종류 정리"

Agent (Mode B):
┌─────────────────────────────────────────────────────┐
│ 📖 Quick Reference: SQL JOINs                       │
│ 📁 Source: 10a_sql_fundamentals.md                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ | JOIN Type | 결과 | 사용 시점 |                    │
│ |-----------|------|----------|                    │
│ | INNER     | 양쪽 매칭만 | 확실한 관계 |           │
│ | LEFT      | 왼쪽 전체 + 매칭 | 마스터-디테일 |    │
│ | RIGHT     | 오른쪽 전체 + 매칭 | 거의 안씀 |      │
│ | FULL      | 양쪽 전체 | 차집합 찾을 때 |          │
│ | CROSS     | 카테시안 곱 | 조합 생성 |             │
│                                                     │
│ 💡 면접 Tip: "LEFT JOIN에서 NULL은 어디서 오나요?" │
│                                                     │
│ 🔗 Related: F51_maps_dictionaries (key-value 개념) │
└─────────────────────────────────────────────────────┘
```

### Hybrid Mode: Learning -> Reference

#### When to Use
- Concept comparisons ("X vs Y")
- Interview preparation
- Deep dive with practical summary

#### Example: Comparison Query

```
User: "/palantir-coding const와 let의 차이"

Agent (Hybrid):
┌─────────────────────────────────────────────────────┐
│ 🎓 + 📖 Hybrid: const vs let                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📚 핵심 개념 (Mode A):                              │
│                                                     │
│ 먼저, "const"가 의미하는 것이 무엇일까요?           │
│ - 값이 변하지 않는다?                               │
│ - 재할당이 불가능하다?                               │
│                                                     │
│ const obj = {a: 1};                                 │
│ obj.a = 2;  // 이건 될까요?                         │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 📊 7-Language Matrix (Mode B):                      │
│ Source: F03_constant_semantics.md                   │
│                                                     │
│ | 언어 | 키워드 | 재바인딩 | 값 변경 |              │
│ |------|--------|---------|--------|              │
│ | JS/TS | const | ✗ 불가 | ✓ 가능 |                │
│ | Java | final | ✗ 불가 | ✓ 가능 |                 │
│ | Python | 없음 | ✓ 가능 | ✓ 가능 |               │
│ | Go | const | ✗ 불가 | N/A (값타입) |             │
│ | Rust | let | ✗ 불가 | ✗ 불가 (기본) |           │
│                                                     │
│ ★ Insight: const는 "불변"이 아니라 "재바인딩 금지" │
│                                                     │
│ 🎯 면접 예상 질문:                                  │
│ "const 배열에 push()가 되는 이유는?"               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Concept -> KB Mapping

#### Quick Lookup Table

| Concept (KR) | Concept (EN) | Primary KB | Related |
|--------------|--------------|------------|---------|
| 변수 바인딩 | Variable Binding | F01 | F10 |
| 불변성/가변성 | Mutability | F02 | F03 |
| 상수 | Constants | F03 | F02 |
| 선언/정의 | Declaration/Definition | F04 | F01 |
| 섀도잉 | Shadowing | F05 | F10 |
| 렉시컬 스코프 | Lexical Scope | F10 | F11 |
| 동적 스코프 | Dynamic Scope | F11 | F10 |
| 블록 스코프 | Block Scope | F12 | F10 |
| 호이스팅 | Hoisting | F13 | F04 |
| 클로저 캡처 | Closure Capture | F14 | F44 |
| 정적/동적 타입 | Static/Dynamic Typing | F20 | F21 |
| 타입 추론 | Type Inference | F21 | F20 |
| 타입 강제변환 | Type Coercion | F22 | F20 |
| 구조적 타이핑 | Structural Typing | F23 | F20 |
| 제네릭 | Generics | F24 | F23 |
| 조건문 | Conditionals | F30 | F34 |
| 반복문 | Loops | F31 | F54 |
| 예외 처리 | Exception Handling | F32 | F42 |
| 패턴 매칭 | Pattern Matching | F33 | F30 |
| 제어 흐름 | Control Flow | F34 | F30-F33 |
| 함수 선언 | Function Declaration | F40 | F04 |
| 매개변수 | Parameters | F41 | F40 |
| 반환값 | Return Values | F42 | F40 |
| 고차 함수 | Higher-Order Functions | F43 | F44 |
| 클로저 | Closures | F44 | F14 |
| 배열/리스트 | Arrays/Lists | F50 | F54 |
| 맵/딕셔너리 | Maps/Dictionaries | F51 | F50 |
| 집합 | Sets | F52 | F51 |
| 문자열 | Strings | F53 | F50 |
| 이터러블 | Iterables | F54 | F31 |
| SQL | SQL Fundamentals | 10a | - |
| Spark | Spark Basics | 11a | 10a |

### Execution Patterns

#### Pattern 1: Single Concept Query

```python
# User: "호이스팅이 뭐야?"
# → Mode A (Learning)

1. Glob("**/F13*.md")  # Find hoisting KB
2. Read(F13_hoisting.md)  # Load content
3. Extract Mental Model section
4. Formulate Socratic question
5. Wait for user response
6. Provide insight + KB reference
```

#### Pattern 2: Comparison Query

```python
# User: "Java vs Python 타입 시스템"
# → Hybrid (A→B)

1. Grep("Static.*Dynamic|Java.*Python", knowledge_bases/)
2. Read(F20_static_vs_dynamic.md)
3. Extract comparison matrix
4. Ask: "왜 Java는 컴파일 타임에 타입을 체크할까?"
5. Provide matrix after user engagement
```

#### Pattern 3: Quick Reference

```python
# User: "빠르게 Python dict 메서드"
# → Mode B (Direct)

1. Read(F51_maps_dictionaries.md)
2. Extract Python section
3. Format as quick reference table
4. Add common pitfall
5. Suggest related KB
```

#### Pattern 4: Interview Prep

```python
# User: "면접에서 클로저 질문"
# → Hybrid + Interview Focus

1. Read(F44_closures.md)
2. Extract "Interview Relevance" section
3. Generate practice questions
4. Provide model answers with KB references
```

### Error Handling

| 상황 | 처리 방법 |
|------|----------|
| 개념이 KB에 없음 | Legacy KB 검색 → 없으면 WebSearch |
| 모호한 질문 | AskUserQuestion으로 명확화 |
| 7개 언어 중 특정 언어만 요청 | 해당 언어 컬럼만 추출 |
| 복합 개념 요청 | TodoWrite로 분해 후 순차 답변 |

### Integration Points

#### With Other Commands

| 시나리오 | 연계 커맨드 |
|---------|------------|
| 개념 학습 후 코드 리뷰 | `/palantir-coding` → `/audit` |
| 개념 기반 구현 계획 | `/palantir-coding` → `/plan` |
| 심층 분석 필요 | `/palantir-coding` → `/deep-audit` |

#### KB Expansion Workflow

새 개념 KB 추가 시:
1. KB_TEMPLATE.md 복사
2. F-Series 번호 할당
3. 5-Component 구조 작성
4. 이 커맨드의 매핑 테이블 업데이트

### Output Format Templates

#### Mode A (Learning) Output

```markdown
┌─────────────────────────────────────────────────────┐
│ 🎓 Learning Mode: {CONCEPT}                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│ {Socratic Question}                                 │
│                                                     │
│ ```{language}                                       │
│ {Code Example}                                      │
│ ```                                                 │
│                                                     │
│ 힌트: {Guided Hint}                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### Mode B (Reference) Output

```markdown
┌─────────────────────────────────────────────────────┐
│ 📖 Quick Reference: {CONCEPT}                       │
│ 📁 Source: {KB_FILE}                                │
├─────────────────────────────────────────────────────┤
│                                                     │
│ {Formatted Table or List}                           │
│                                                     │
│ 💡 Tip: {Common Pitfall or Interview Note}          │
│                                                     │
│ 🔗 Related: {Related KB Files}                      │
└─────────────────────────────────────────────────────┘
```

#### Insight Block (Always Include)

```markdown
★ Insight ─────────────────────────────────────────────
1. {Key Learning Point 1}
2. {Key Learning Point 2}
3. {Key Learning Point 3}
─────────────────────────────────────────────────────
```

### Usage Examples

```bash
# Learning Mode
/palantir-coding 클로저가 뭐야?
/palantir-coding 왜 String은 불변으로 설계했을까?
/palantir-coding 호이스팅의 원리를 설명해줘

# Reference Mode
/palantir-coding 빠르게 SQL JOIN 정리
/palantir-coding Python 리스트 메서드 요약
/palantir-coding 7개 언어 타입 시스템 비교표

# Hybrid Mode
/palantir-coding const vs let 차이
/palantir-coding 면접에서 자주 나오는 클로저 질문
/palantir-coding Java와 Python의 예외 처리 비교

# Specific Language
/palantir-coding TypeScript에서 제네릭 사용법
/palantir-coding Go의 defer 동작 원리
/palantir-coding Spark DataFrame 기본 연산
```

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-01-18 | Add Layer1/Layer2 structure for progressive disclosure |
| 1.0 | 2026-01-18 | Initial A+B mode creation |
