# KB Template: Concept Dictionary Format (v1.0)

> **Purpose**: LLM 추론 기반 학습을 위한 개념 사전 템플릿
> **Design Philosophy**: 정적 콘텐츠는 최소화, LLM이 동적으로 확장
> **Target**: Palantir Dev/Delta 2026년 기준 프로그래밍 능력

---

## Template Usage

이 템플릿을 복사하여 새 KB 파일을 생성할 때 사용합니다.
파일명: `F{NN}_{concept_name}.md` (예: `F01_variable_binding.md`)

---

# F{NN}: {Concept Name}

> **Concept ID**: `F{NN}_{concept_name}`
> **Universal Principle**: {한 줄로 언어 무관 정의}
> **Prerequisites**: F{XX}, F{YY} (선수 개념, 없으면 생략)

---

## 1. Universal Concept (언어 무관 개념 정의)

{2-3 문단으로 이 개념이 무엇인지 언어에 상관없이 설명}

**Mental Model**: {이 개념을 이해하기 위한 비유나 직관적 설명}

**Why This Matters**: {왜 이 개념을 알아야 하는지, 실무에서 어떻게 쓰이는지}

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Binding/Mutation** | | | | | | | |
| **Scope/Lifetime** | | | | | | | |
| **Type Enforcement** | | | | | | | |
| **Memory/Concurrency** | | | | | | | |
| **Common Pitfalls** | | | | | | | |

### 2.2 Semantic Notes

**Binding/Mutation**:
- {각 언어에서 이 개념의 바인딩/뮤테이션 특성}

**Scope/Lifetime**:
- {스코프와 생명주기 차이점}

**Type Enforcement**:
- {타입 시스템에서의 차이점}

**Memory/Concurrency**:
- {메모리 모델과 동시성 관련 차이점}

**Common Pitfalls**:
- {각 언어에서 흔히 하는 실수들}

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS](https://docs.oracle.com/javase/specs/) | {관련 섹션} |
| Python | [Python Docs](https://docs.python.org/3/) | {관련 섹션} |
| TypeScript | [TS Handbook](https://www.typescriptlang.org/docs/) | {관련 섹션} |
| Go | [Effective Go](https://go.dev/doc/effective_go) | {관련 섹션} |
| SQL | [SQL Standard](https://www.iso.org/standard/63555.html) | {관련 섹션} |
| C++ | [cppreference](https://en.cppreference.com/) | {관련 섹션} |
| Spark | [Spark Docs](https://spark.apache.org/docs/latest/) | {관련 섹션} |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**: {이 개념이 Palantir 스택에서 어떻게 나타나는지 힌트}

**Interview Relevance**: {면접에서 이 개념이 어떻게 물어볼 수 있는지 힌트}

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F{XX}_{related_concept_1}
- → F{YY}_{related_concept_2}

### Existing KB Links
- → 00a_programming_fundamentals (기초 연결)
- → {NN}_{existing_kb} (관련 기존 KB)

---

## Template Notes

### What This Template INCLUDES (정적 저장)
- 개념의 정의와 본질
- 7개 언어 간 의미론적 차이점
- 공식 문서 링크
- 관련 개념 연결

### What This Template EXCLUDES (LLM 동적 생성)
- 코드 예제 (LLM이 실시간 생성 또는 외부 fetch)
- 연습 문제 (LLM이 사용자 수준에 맞게 생성)
- 커리큘럼/학습 순서 (LLM이 동적으로 결정)
- 상세한 설명 (요약→상세→전체 Progressive Disclosure)

### Naming Convention
```
F01-F09: Binding & Variables (바인딩과 변수)
F10-F19: Scope & Lifetime (스코프와 생명주기)
F20-F29: Type Systems (타입 시스템)
F30-F39: Memory & Concurrency (메모리와 동시성)
F40-F49: Functions & Control Flow (함수와 제어 흐름)
F50-F59: Data Structures (자료구조)
F60-F69: Error Handling (에러 처리)
F70-F79: OOP & Patterns (객체지향과 패턴)
F80-F89: Advanced Topics (고급 주제)
```

### 5-Dimension Semantic Matrix 설명

| Dimension | 정의 | 면접 포커스 |
|-----------|------|------------|
| **Binding/Mutation** | 이름 재바인딩 vs 값 변경 | `const` ≠ 불변성 |
| **Scope/Lifetime** | 블록/함수/모듈 스코프; 클로저 캡처 | 메모리 누수, stale closure |
| **Type Enforcement** | 컴파일타임 vs 런타임; nominal vs structural | TS structural typing |
| **Memory/Concurrency** | GC vs 수동; 스레드 vs async | 성능, race condition |
| **Common Pitfalls** | 초보자가 흔히 하는 실수 | 면접 트릭 질문 |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial template creation |
