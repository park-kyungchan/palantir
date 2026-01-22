# F01: Variable Binding (변수 바인딩)

> **Concept ID**: `F01_variable_binding`
> **Universal Principle**: 이름(식별자)과 값(데이터)을 연결하는 메커니즘
> **Prerequisites**: None (기초 개념)

---

## 1. Universal Concept (언어 무관 개념 정의)

**변수 바인딩**은 프로그래밍에서 가장 근본적인 개념입니다. "이름"을 "값"에 연결하는 행위를 말합니다.

모든 프로그래밍 언어는 이 바인딩을 구현하는 방식이 다릅니다:
- 어떤 언어는 "상자에 값을 넣는다"고 생각 (Java의 primitive)
- 어떤 언어는 "이름표를 값에 붙인다"고 생각 (Python)
- 어떤 언어는 "포인터로 가리킨다"고 생각 (C++)

**Mental Model**:
- **상자 모델**: 변수 = 값을 담는 상자. 상자 크기(타입)가 정해져 있음.
- **이름표 모델**: 변수 = 값에 붙이는 이름표. 같은 값에 여러 이름표 가능.
- **포인터 모델**: 변수 = 메모리 주소를 가리키는 화살표.

**Why This Matters**:
변수 바인딩의 의미론을 이해하지 못하면:
- 왜 Python에서 리스트를 "복사"했는데 원본이 바뀌는지 모름
- 왜 Java에서 String이 immutable인지 혼란
- 왜 Go에서 `:=`와 `=`가 다른지 이해 못함

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Binding Model** | 상자 (primitive) / 참조 (object) | 이름표 (모두 객체) | 참조 (JS 기반) | 값 복사 기본 | 컬럼 바인딩 | 값/참조/포인터 선택 | DataFrame 지연 평가 |
| **Declaration** | `Type name;` 필수 | 선언 없음 | `let/const name: Type` | `var name Type` 또는 `:=` | `DECLARE @name TYPE` | `Type name;` | `val/var` (Scala) |
| **Rebinding** | 가능 (final 아니면) | 항상 가능 | let 가능, const 불가 | 가능 | SET으로 재할당 | 가능 | val 불가, var 가능 |
| **Type Binding** | 정적 (컴파일) | 동적 (런타임) | 정적 (컴파일) | 정적 (컴파일) | 정적 (스키마) | 정적 (컴파일) | 정적 (스키마 추론) |
| **Pitfall** | null 참조 | mutable default arg | any 남용 | 제로값 혼란 | NULL 삼항논리 | 초기화 안 된 변수 | 지연 평가 오해 |

### 2.2 Semantic Notes

**Binding Model**:
- **Java**: primitive(`int`, `boolean`)는 값 자체 저장, object는 힙 참조 저장
- **Python**: 모든 것이 객체. `x = 5`는 정수 객체 5에 이름 x를 바인딩
- **TypeScript**: JavaScript 의미론 계승. 모든 객체는 참조로 전달
- **Go**: 기본적으로 값 복사. 포인터(`*T`)로 명시적 참조
- **C++**: 프로그래머가 값/참조/포인터 중 선택 가능

**Declaration**:
- **Java/C++/Go**: 타입 선언 필수 (정적 타이핑)
- **Python**: 선언 개념 없음. 할당이 곧 선언
- **TypeScript**: 타입 추론 가능하지만 명시 권장

**Rebinding**:
- `const`/`final`/`val`은 **재바인딩** 금지이지 **불변성** 보장 아님
- `const obj = {a: 1}; obj.a = 2;` ← TypeScript에서 합법!

**Type Binding**:
- 정적 타입: 컴파일 시점에 타입 결정 (Java, Go, TypeScript)
- 동적 타입: 런타임에 타입 결정 (Python)

**Common Pitfalls**:
- Java: `Integer a = null; int b = a;` → NullPointerException
- Python: `def f(lst=[]): lst.append(1)` → 같은 리스트 재사용
- Go: `var x int` → 자동으로 0 초기화 (의도치 않은 제로값)

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.4](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) | Types, Values, and Variables |
| Python | [Data Model](https://docs.python.org/3/reference/datamodel.html) | Objects, values and types |
| TypeScript | [Variable Declarations](https://www.typescriptlang.org/docs/handbook/variable-declarations.html) | let, const, var |
| Go | [Variables](https://go.dev/ref/spec#Variables) | Variable declarations |
| SQL | [ISO SQL](https://www.iso.org/standard/63555.html) | Variable declaration (vendor-specific) |
| C++ | [cppreference](https://en.cppreference.com/w/cpp/language/declarations) | Declarations |
| Spark | [Spark SQL](https://spark.apache.org/docs/latest/sql-ref.html) | DataFrame variables |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- TypeScript OSDK에서 객체 참조 이해 필수
- Python transforms에서 DataFrame 바인딩 이해 필요
- Java 서비스에서 null safety 중요

**Interview Relevance**:
- "Python에서 `a = b = []`를 하면 무슨 일이 일어나나요?"
- "Java의 primitive와 wrapper 차이를 설명하세요"
- "const가 왜 불변성을 보장하지 않나요?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F02_mutability_patterns (바인딩된 값의 변경)
- → F03_constant_semantics (재바인딩 금지)
- → F10_lexical_scope (바인딩의 유효 범위)
- → F23_null_safety (바인딩되지 않은 상태 처리)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00e_typescript_intro (TypeScript의 let/const)
- → 22_java_kotlin_backend_foundations (Java 변수 선언)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
