# F10: Lexical Scope (렉시컬 스코프)

> **Concept ID**: `F10_lexical_scope`
> **Universal Principle**: 변수가 선언된 위치에 따라 접근 가능한 범위가 결정되는 규칙
> **Prerequisites**: F01_variable_binding (변수 바인딩 이해 필수)

---

## 1. Universal Concept (언어 무관 개념 정의)

**렉시컬 스코프(Lexical Scope)**는 변수의 접근 가능 범위가 **코드가 작성된 위치**에 의해 결정되는 규칙입니다. "정적 스코프(Static Scope)"라고도 불리며, 대부분의 현대 프로그래밍 언어가 채택하는 방식입니다.

렉시컬 스코프의 핵심은 **컴파일/파싱 시점에 스코프가 결정된다**는 것입니다. 코드가 실행되는 위치(콜스택)가 아니라, 코드가 **작성된 위치**(소스코드 구조)가 변수 접근을 결정합니다.

반대 개념인 **동적 스코프(Dynamic Scope)**는 호출 시점의 콜스택에 따라 변수를 찾습니다. Bash, Emacs Lisp 등 일부 언어에서만 사용되며, 예측하기 어렵고 버그 유발이 쉬워 현대 언어에서는 대부분 사용하지 않습니다.

**Mental Model**:
```
외부 스코프 (Global/Module)
    └─ 함수 스코프
        └─ 블록 스코프 (if/for/while)
            └─ 더 내부 블록
                └─ 변수 x 참조 → 안에서 바깥으로 검색
                    (찾을 때까지 상위 스코프로 올라감)
```

변수를 찾을 때는 **안쪽에서 바깥쪽으로** 스코프 체인을 따라 검색합니다. 가장 먼저 발견된 바인딩이 사용됩니다.

**Why This Matters**:
렉시컬 스코프를 이해하지 못하면:
- 클로저(Closure)가 왜 외부 변수를 "기억"하는지 이해 못함
- 변수 섀도잉(Shadowing)으로 인한 버그를 만들 수 있음
- 호이스팅(Hoisting) 관련 문제를 디버깅할 수 없음
- 모듈 시스템의 private/public 개념을 이해하지 못함

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Scope Type** | Block + Class | Function + Module (LEGB) | Block (let/const) | Block + Package | Query/Subquery | Block + Namespace | DataFrame/Session |
| **Lookup Order** | Inner→Outer→Class→Package | LEGB: Local→Enclosing→Global→Built-in | Scope Chain (ES6) | Inner→Package | Inner Query→Outer | Inner→Outer→Namespace | Local→Session→Catalog |
| **Closure Support** | Yes (effectively final) | Yes (자유 캡처) | Yes (자유 캡처) | Yes (값/참조 선택) | No (서브쿼리로 유사) | Yes (명시적 캡처) | No (분산 실행 제약) |
| **Static vs Dynamic** | Static (Lexical) | Static (Lexical) | Static (Lexical) | Static (Lexical) | Static (Lexical) | Static (Lexical) | Static (Lexical) |
| **Pitfall** | effectively final 제약 | nonlocal/global 혼란 | var 호이스팅 | 짧은 변수명 섀도잉 | 상관 서브쿼리 혼란 | 람다 캡처 모드 | 직렬화 클로저 실패 |

### 2.2 Semantic Notes

**Scope Type**:
- **Java**: 블록 스코프 기본. 클래스 멤버와 패키지 스코프 추가
- **Python**: 함수 스코프 기본. `if/for` 블록은 새 스코프 생성 안 함!
- **TypeScript**: `let/const`는 블록 스코프, `var`는 함수 스코프 (레거시)
- **Go**: 블록 스코프. 패키지 레벨에서 대문자 = public, 소문자 = private
- **C++**: 블록 스코프 + 네임스페이스로 모듈화
- **SQL**: 쿼리 단위 스코프. 서브쿼리가 외부 참조 가능 (상관 서브쿼리)
- **Spark**: DataFrame 변수는 세션 스코프, 컬럼은 DataFrame 스코프

**Lookup Order**:
- **Python LEGB**: `Local → Enclosing → Global → Built-in` 순서로 검색
- **JavaScript/TypeScript**: 스코프 체인 따라 상위로 검색
- **Go**: 블록 → 함수 → 패키지 순서 (import된 패키지는 명시적 접근)

**Closure Support**:
- **Java**: 클로저에서 외부 변수는 "effectively final"이어야 함
- **Python/TypeScript**: 자유롭게 캡처, 수정 가능 (Python은 `nonlocal` 필요)
- **Go**: 캡처할 변수를 값/참조로 선택 가능
- **C++**: `[=]` 값 캡처, `[&]` 참조 캡처, `[x, &y]` 혼합 가능
- **Spark**: 클로저 직렬화 필요 → 외부 객체 참조 시 직렬화 실패 주의

**Common Pitfalls**:
- **Python**: `for i in range(3): funcs.append(lambda: i)` → 모두 2 출력 (late binding)
- **JavaScript/TypeScript**: `var`와 `let`의 루프 캡처 차이
- **Java**: 람다에서 지역 변수 수정 시도 → 컴파일 에러
- **Go**: `:=`로 의도치 않게 외부 변수 섀도잉
- **Spark**: 클로저에서 외부 객체 참조 → `NotSerializableException`

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.6](https://docs.oracle.com/javase/specs/jls/se21/html/jls-6.html) | Names, Scope |
| Python | [Execution Model](https://docs.python.org/3/reference/executionmodel.html) | Naming and binding |
| TypeScript | [Variable Scope](https://www.typescriptlang.org/docs/handbook/variable-declarations.html#scoping-rules) | Scoping rules |
| Go | [Declarations and Scope](https://go.dev/ref/spec#Declarations_and_scope) | Scope of identifiers |
| SQL | [ISO SQL](https://www.iso.org/standard/63555.html) | Scope of column references |
| C++ | [cppreference Scope](https://en.cppreference.com/w/cpp/language/scope) | Scope |
| Spark | [Spark Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html#understanding-closures-) | Understanding closures |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- TypeScript OSDK에서 클로저를 활용한 콜백 패턴 이해 필수
- Python transforms에서 LEGB 스코프 규칙 이해 필요
- Spark 기반 transforms에서 클로저 직렬화 문제 자주 발생
- Java 서비스에서 effectively final 제약 이해 중요

**Interview Relevance**:
- "Python의 LEGB 규칙을 설명하세요"
- "JavaScript에서 `var`와 `let`의 스코프 차이는?"
- "클로저가 외부 변수를 어떻게 '기억'하나요?"
- "왜 for 루프에서 람다를 만들면 같은 값을 참조하나요?"
- "Spark에서 클로저 직렬화 문제를 어떻게 해결하나요?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F01_variable_binding (바인딩과 스코프의 관계)
- → F05_shadowing (스코프 내에서 이름 가리기)
- → F11_closure_capture (클로저와 스코프 캡처)
- → F12_hoisting (선언 끌어올림과 스코프)
- → F13_module_scope (모듈 레벨 스코프)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00e_typescript_intro (TypeScript의 let/const/var)
- → 22_java_kotlin_backend_foundations (Java 스코프 규칙)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
