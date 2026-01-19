# F11: Closure Capture (클로저 캡처)

> **Concept ID**: `F11_closure_capture`
> **Universal Principle**: 함수가 자신이 정의된 스코프의 변수를 "기억"하는 메커니즘
> **Prerequisites**: F10_lexical_scope (렉시컬 스코프 이해 필수)

---

## 1. Universal Concept (언어 무관 개념 정의)

**클로저(Closure)**는 함수와 그 함수가 선언된 렉시컬 환경(Lexical Environment)의 조합입니다. 클로저는 외부 함수가 실행을 마친 후에도 외부 함수의 변수에 접근할 수 있게 합니다.

클로저의 핵심은 **"캡처(Capture)"**입니다:
- 함수가 정의될 때, 주변 스코프의 변수들에 대한 참조를 "캡처"합니다
- 이 캡처된 변수들은 외부 함수가 종료되어도 메모리에서 사라지지 않습니다
- 내부 함수가 살아있는 한, 캡처된 변수들도 함께 생존합니다

**Mental Model**:
```
function outer() {
    let x = 10;          ← 외부 변수
    return function inner() {
        return x;        ← 클로저: x를 "기억"
    }
}
const fn = outer();
fn();  // 10 ← outer가 끝났는데도 x 접근 가능!
```

클로저를 **"배낭(Backpack)"**으로 생각하세요:
- 함수가 탄생할 때, 주변 환경의 변수들을 배낭에 담습니다
- 함수가 어디로 이동하든, 배낭을 항상 가지고 다닙니다
- 필요할 때 배낭에서 변수를 꺼내 사용합니다

**Why This Matters**:
클로저를 이해하지 못하면:
- 콜백 함수에서 예상과 다른 값이 출력되는 이유를 모름
- 이벤트 핸들러에서 상태 관리가 어려움
- 고차 함수(map, filter, reduce)의 동작을 제대로 이해 못함
- 메모리 누수를 유발하는 코드를 작성할 수 있음

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Closure Support** | Lambda (Java 8+) | Native | Native | Native | N/A (절차적) | Lambda (C++11+) | Lambda (Scala/Python) |
| **Capture Mode** | Effectively Final (값 복사) | By Reference | By Reference | By Reference (주의!) | - | 명시적 선택 `[=]`, `[&]` | By Reference |
| **Mutable Capture** | 불가 (final만) | 가능 (외부 수정) | 가능 | 가능 | - | `mutable` 키워드 필요 | 가능 |
| **Late Binding** | N/A (값 캡처) | 있음 (호출 시점) | 있음 (var 사용 시) | 있음 (포인터 캡처) | - | 참조 캡처 시 있음 | 있음 |
| **Loop Pitfall** | 없음 (값 캡처) | 심각 (마지막 값) | var: 심각 / let: 안전 | 심각 (포인터 공유) | - | 참조 캡처 시 심각 | 심각 (지연 평가) |

### 2.2 Semantic Notes

**Closure Support**:
- **Java**: Lambda 표현식으로 클로저 지원, 단 `effectively final` 변수만 캡처 가능
- **Python**: 일급 함수로 네이티브 클로저 지원, `nonlocal` 키워드로 외부 변수 수정
- **TypeScript**: JavaScript 기반으로 완전한 클로저 지원
- **Go**: 익명 함수가 클로저 역할, **루프 변수 캡처 주의 필수**
- **C++**: Lambda 캡처 리스트로 명시적 제어 `[=]` 값 / `[&]` 참조
- **SQL**: 전통적 SQL은 클로저 미지원, 저장 프로시저는 제한적

**Capture Mode (값 vs 참조)**:
- **값 캡처**: 변수의 현재 값을 복사 (Java, C++ `[=]`)
- **참조 캡처**: 변수 자체를 참조 (Python, JS, Go, C++ `[&]`)

```java
// Java: 값 캡처 (effectively final)
int x = 10;
Runnable r = () -> System.out.println(x);  // x의 값 10을 캡처
// x = 20;  ← 컴파일 에러! effectively final 위반
```

```python
# Python: 참조 캡처 (Late Binding)
x = 10
fn = lambda: x  # x를 참조로 캡처
x = 20
print(fn())  # 20 출력! (10이 아님)
```

**Mutable Capture**:
- **Java**: 캡처된 변수 수정 불가 (workaround: 배열/AtomicInteger 사용)
- **Python**: `nonlocal` 선언으로 외부 변수 수정 가능
- **TypeScript**: 자유롭게 수정 가능 (주의 필요)
- **C++**: `mutable` 키워드로 람다 내부에서 캡처된 값 수정 허용

**Late Binding (지연 바인딩)**:
- 변수의 값이 함수 **정의 시점**이 아닌 **호출 시점**에 결정됨
- Python, JavaScript(var), Go에서 루프 변수 캡처 문제의 원인

**Common Pitfalls (루프 변수 캡처)**:
```javascript
// JavaScript 클래식 실수
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// 예상: 0, 1, 2
// 실제: 3, 3, 3 (var는 함수 스코프, 모든 클로저가 같은 i 참조)

// 해결책 1: let 사용 (블록 스코프)
for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// 출력: 0, 1, 2

// 해결책 2: IIFE로 값 캡처
for (var i = 0; i < 3; i++) {
    ((j) => setTimeout(() => console.log(j), 100))(i);
}
```

```python
# Python 클래식 실수
funcs = []
for i in range(3):
    funcs.append(lambda: i)

[f() for f in funcs]  # [2, 2, 2] - 마지막 i 값

# 해결책: 기본 인자로 값 캡처
funcs = []
for i in range(3):
    funcs.append(lambda x=i: x)  # x=i가 현재 값을 캡처

[f() for f in funcs]  # [0, 1, 2]
```

```go
// Go 클래식 실수 (Go 1.21 이전)
for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i)  // 모든 고루틴이 같은 i 참조
    }()
}
// 출력: 3, 3, 3 (또는 예측 불가)

// 해결책: 파라미터로 값 전달
for i := 0; i < 3; i++ {
    go func(n int) {
        fmt.Println(n)
    }(i)  // 현재 i 값을 n으로 복사
}

// Go 1.22+: 루프 변수가 반복마다 새로 생성됨 (문제 해결!)
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Lambda Expressions](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27) | Capturing Variables |
| Python | [Execution Model](https://docs.python.org/3/reference/executionmodel.html) | Naming and binding |
| TypeScript | [Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html) | Closures |
| Go | [Function Literals](https://go.dev/ref/spec#Function_literals) | Closures |
| SQL | - | N/A (절차적 언어) |
| C++ | [Lambda Expressions](https://en.cppreference.com/w/cpp/language/lambda) | Capture clause |
| Spark | [RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html) | Closures (Understanding closures) |

---

## 4. Palantir Context Hint

**Foundry/OSDK Relevance**:
- **TypeScript OSDK**: 이벤트 핸들러와 비동기 콜백에서 클로저 패턴 빈번하게 사용
- **Python Transforms**: Spark에서 클로저 직렬화 이슈 (driver vs executor 변수)
- **Java Services**: 람다 표현식에서 effectively final 규칙 준수 필수

**Spark 특수 케이스 (면접 빈출)**:
```python
# Spark에서 클로저 실수
counter = 0
rdd.foreach(lambda x: counter += 1)  # counter는 driver에서 0 유지!

# 이유: 클로저가 executor로 직렬화되면서 driver의 counter와 분리됨
# 해결: Accumulator 사용
from pyspark import SparkContext
counter = sc.accumulator(0)
rdd.foreach(lambda x: counter.add(1))
```

**Interview Relevance**:
- "클로저가 무엇이고, 왜 메모리 누수를 유발할 수 있나요?"
- "JavaScript/Python에서 루프 변수 캡처 문제를 설명하고 해결하세요"
- "Java에서 왜 람다가 effectively final 변수만 캡처하나요?"
- "Spark에서 클로저와 Accumulator의 차이를 설명하세요"
- "Go 1.22에서 루프 변수 동작이 어떻게 바뀌었나요?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F10_lexical_scope (클로저의 기반이 되는 렉시컬 스코프)
- → F05_shadowing (클로저 내부에서의 변수 섀도잉)
- → F40_higher_order_functions (클로저를 활용하는 고차 함수)
- → F12_lifetime_management (클로저로 인한 변수 생명주기 연장)
- → F31_gc_reference_counting (클로저와 가비지 컬렉션)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00e_typescript_intro (TypeScript 클로저)
- → 01_python_foundations (Python 클로저, nonlocal)
- → 24_distributed_data_processing (Spark 클로저 직렬화)

---

## 6. Quick Cheat Sheet (빠른 참조)

### 언어별 클로저 캡처 요약

| 언어 | 캡처 문법 | 값/참조 | 루프 안전 | 수정 가능 |
|------|-----------|---------|-----------|-----------|
| **Java** | 자동 | 값 (effectively final) | Safe | No |
| **Python** | 자동 | 참조 (late binding) | Unsafe | Yes (`nonlocal`) |
| **TypeScript** | 자동 | 참조 | `let`: Safe / `var`: Unsafe | Yes |
| **Go** | 자동 | 참조 | 1.21-: Unsafe / 1.22+: Safe | Yes |
| **C++** | `[=]` / `[&]` / `[x]` | 명시적 선택 | `[=]`: Safe / `[&]`: Unsafe | `mutable` 필요 |
| **Spark** | 자동 | 참조 (직렬화됨) | Unsafe (driver/executor 분리) | Accumulator 필요 |

### 루프 캡처 문제 해결 패턴

```
문제: 모든 클로저가 같은 변수를 참조
원인: Late Binding (호출 시점에 변수 평가)

해결책:
1. 블록 스코프 변수 사용 (JS: let, Go 1.22+)
2. 함수 파라미터로 값 전달 (모든 언어)
3. 기본 인자로 즉시 평가 (Python: lambda x=i: x)
4. IIFE 패턴 (JS: ((i) => ...)(i))
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
