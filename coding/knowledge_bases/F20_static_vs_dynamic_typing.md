# F20: Static vs Dynamic Typing (정적 타이핑 vs 동적 타이핑)

> **Concept ID**: `F20_static_vs_dynamic_typing`
> **Universal Principle**: 타입 검사가 언제 발생하는가 - 컴파일 타임 vs 런타임
> **Prerequisites**: F01_variable_binding

---

## 1. Universal Concept (언어 무관 개념 정의)

**정적 타이핑(Static Typing)**과 **동적 타이핑(Dynamic Typing)**은 프로그램의 타입 검사가 **언제** 수행되는지를 결정하는 근본적인 언어 설계 선택입니다.

- **정적 타이핑**: 타입 검사가 **컴파일 타임/실행 전**에 수행됩니다. 프로그램이 실행되기 전에 타입 오류를 발견합니다.
- **동적 타이핑**: 타입 검사가 **런타임/실행 중**에 수행됩니다. 실제로 코드가 실행될 때 타입 오류가 발생합니다.

이 두 접근법 사이에는 **점진적 타이핑(Gradual Typing)**이 존재합니다. TypeScript의 `any`, Python의 type hints처럼 정적 검사와 동적 유연성을 혼합하는 방식입니다.

**Mental Model**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    타입 검사 타이밍 스펙트럼                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    컴파일 타임                                      런타임       │
│    (실행 전)                                       (실행 중)    │
│        │                                              │        │
│        ▼                                              ▼        │
│   ┌─────────┐    ┌─────────────┐    ┌──────────┐    ┌───────┐  │
│   │  Java   │    │ TypeScript  │    │  Python  │    │Python │  │
│   │  Go     │    │  (strict)   │    │  (hints) │    │(raw)  │  │
│   │  C++    │    │             │    │          │    │       │  │
│   └─────────┘    └─────────────┘    └──────────┘    └───────┘  │
│        │                │                │              │      │
│    완전 정적        점진적 타이핑       힌트 기반       완전 동적  │
│                                                                 │
│   "실행 전 모든     "대부분 검사,      "선택적 검사"  "실행해봐야 │
│    오류 발견"       탈출구 있음"                       알 수 있음"│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**간단한 비유**:
- **정적 타이핑**: 비행기 이륙 전 철저한 안전 점검. 문제 발견 시 이륙 불가.
- **동적 타이핑**: 비행 중 문제 발생 시 그때 대응. 빠른 출발, 하지만 리스크.
- **점진적 타이핑**: 핵심 부품만 사전 점검, 나머지는 비행 중 모니터링.

**Why This Matters**:
정적/동적 타이핑의 차이를 이해하지 못하면:
- 왜 Java에서는 컴파일 에러가 나는데 Python에서는 런타임에 터지는지 모름
- TypeScript의 `any`를 남발하여 정적 타입의 이점을 모두 잃음
- mypy나 tsc의 경고를 무시하고 배포 후 프로덕션에서 타입 에러 발생
- IDE의 자동완성과 리팩토링 기능을 제대로 활용하지 못함

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Typing Discipline** | 정적, 명목적 | 동적, 덕 타이핑 | 정적, 구조적 (any로 탈출) | 정적, 구조적 (인터페이스) | 정적, 스키마 기반 | 정적, 명목적 | 정적, 스키마 추론 |
| **Type Declaration** | 필수 (`int x`) | 선택적 힌트 (`x: int`) | 추론 가능, 명시 권장 | 필수 또는 `:=` 추론 | 컬럼 정의 필수 | 필수 (`int x`) | 스키마 자동 추론 |
| **Type Errors** | 컴파일 에러 | RuntimeError/TypeError | 컴파일 에러 (tsc) | 컴파일 에러 | 쿼리 분석 에러 | 컴파일 에러 | 분석 계획 에러 |
| **Type Hints/Annotations** | 언어 기본 | PEP 484 (선택적) | 언어 기본 | 언어 기본 | N/A | 언어 기본 | 스키마 API |
| **Gradual Typing** | 없음 (raw types 제외) | mypy, pyright | any, unknown | 없음 | 없음 | auto, 템플릿 | N/A |
| **Pitfall** | 제네릭 타입 소거 | 런타임까지 타입 에러 숨김 | any 남용 | 빈 interface{} 남용 | 암묵적 타입 변환 | 템플릿 에러 메시지 | 스키마 불일치 |

### 2.2 Semantic Notes

**Typing Discipline**:
- **Java**: 정적 + 명목적. 클래스 이름이 타입 정체성 결정. `ArrayList<String>`은 컴파일 시 검사됨
- **Python**: 동적 + 덕 타이핑. "오리처럼 걷고 꽥꽥거리면 오리다". 런타임에 속성 존재 여부만 확인
- **TypeScript**: 정적 + 구조적. 이름이 아닌 구조(shape)로 호환성 결정. `any`로 동적 세계 탈출 가능
- **Go**: 정적 + 구조적 인터페이스. 명시적 `implements` 없이 메서드 시그니처만 일치하면 구현
- **SQL**: 정적 + 스키마 기반. 테이블/컬럼 정의 시 타입 고정
- **C++**: 정적 + 명목적 (템플릿은 구조적). 컴파일 타임에 모든 타입 결정
- **Spark**: 정적 + 스키마 추론. DataFrame의 컬럼 타입은 추론되지만 정적으로 관리됨

**Type Errors - When They Strike**:

```java
// Java - 컴파일 에러 (실행 전 발견)
String x = 123;  // error: incompatible types
```

```python
# Python - 런타임 에러 (실행 중 발견)
def greet(name: str) -> str:
    return "Hello, " + name

greet(123)  # TypeError at runtime! (힌트만으로는 막지 못함)
```

```typescript
// TypeScript - 컴파일 에러 (tsc 실행 시)
const x: string = 123;  // error TS2322: Type 'number' is not assignable to type 'string'
```

```go
// Go - 컴파일 에러
var x string = 123  // cannot use 123 (type int) as type string
```

```sql
-- SQL - 쿼리 분석 에러
SELECT name + 100 FROM users;  -- 문자열과 숫자 연산 에러 (DB마다 다름)
```

```cpp
// C++ - 컴파일 에러
std::string x = 123;  // error: no viable conversion from 'int' to 'std::string'
```

```python
# Spark - 분석 계획 에러
df.withColumn("result", col("string_col") + 100)  # AnalysisException (스키마 불일치)
```

**Gradual Typing in Practice**:

```typescript
// TypeScript - 점진적 타이핑
const strict: string = "hello";    // 엄격한 타입
const loose: any = "anything";     // 탈출구
const better: unknown = getData(); // any보다 안전한 unknown

// any는 타입 검사를 완전히 비활성화
loose.nonExistentMethod();  // 컴파일 에러 없음, 런타임에 터짐!

// unknown은 사용 전 타입 체크 강제
if (typeof better === "string") {
    console.log(better.toUpperCase());  // 안전하게 사용
}
```

```python
# Python - mypy로 점진적 타이핑
from typing import Any

def process(data):      # 타입 힌트 없음 - mypy 무시
    return data + 1

def process_typed(data: int) -> int:  # mypy가 검사
    return data + 1

def escape_hatch(data: Any) -> Any:   # Any로 검사 우회
    return data.whatever()  # mypy가 검사하지 않음
```

**Common Pitfalls by Language**:

- **Java**: 제네릭 타입 소거. `List<String>`과 `List<Integer>`는 런타임에 같은 `List`
  ```java
  // 컴파일은 되지만 런타임에 ClassCastException 가능
  List<String> strings = new ArrayList<>();
  List raw = strings;  // raw type 경고
  raw.add(123);        // 허용됨!
  String s = strings.get(0);  // ClassCastException!
  ```

- **Python**: 타입 힌트는 문서화 목적. 런타임 검사 없음
  ```python
  def add(a: int, b: int) -> int:
      return a + b

  add("hello", "world")  # 런타임에 정상 동작! 타입 힌트 무시됨
  ```

- **TypeScript**: `any`의 전염성
  ```typescript
  function unsafe(x: any) { return x; }
  const result = unsafe(123);  // result의 타입도 any
  result.toUpperCase();  // 에러 없음, 런타임에 터짐
  ```

- **Go**: 빈 인터페이스 남용
  ```go
  func process(data interface{}) {
      // 타입 단언 없이 사용 불가
      data.SomeMethod()  // 컴파일 에러

      // 매번 타입 단언 필요
      if str, ok := data.(string); ok {
          fmt.Println(str)
      }
  }
  ```

- **C++**: 템플릿 에러 메시지의 난해함
  ```cpp
  std::vector<std::string> v;
  std::sort(v.begin(), v.end(), [](int a, int b) { return a < b; });
  // 엄청나게 긴 컴파일 에러 메시지...
  ```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.4](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) | Types, Values, and Variables |
| Python | [PEP 484](https://peps.python.org/pep-0484/) | Type Hints |
| TypeScript | [TypeScript Handbook - Type System](https://www.typescriptlang.org/docs/handbook/2/types-from-types.html) | The Type System |
| Go | [Go Spec - Types](https://go.dev/ref/spec#Types) | Types |
| SQL | [ISO SQL Standard](https://www.iso.org/standard/63555.html) | Data Types |
| C++ | [cppreference - Type](https://en.cppreference.com/w/cpp/language/type) | Type system |
| Spark | [Spark SQL Data Types](https://spark.apache.org/docs/latest/sql-ref-datatypes.html) | Supported Data Types |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- **TypeScript OSDK**: `strict: true` 설정으로 완전한 정적 타입 검사 활성화. `any` 사용 지양.
- **Python Transforms**: mypy 또는 pyright로 타입 검사. Foundry의 `@transform` 데코레이터는 런타임 스키마 검증 제공.
- **Java Services**: 제네릭 타입 소거 주의. 런타임 타입 정보가 필요하면 `Class<T>` 토큰 패턴 사용.
- **Spark**: DataFrame 스키마는 정적으로 관리. `StructType` 명시적 정의로 스키마 불일치 방지.

**Interview Relevance**:
- "왜 TypeScript를 사용하나요? JavaScript와 비교해서 장점은?"
- "Python 타입 힌트의 장단점은 무엇인가요?"
- "정적 타이핑과 동적 타이핑의 트레이드오프를 설명하세요"
- "점진적 타이핑(Gradual Typing)이란 무엇인가요?"
- "mypy를 프로젝트에 도입하는 이유는?"
- "TypeScript의 `any`와 `unknown`의 차이점은?"

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F01_variable_binding (바인딩 시점과 타입 결정)
- → F21_type_inference (타입 추론 메커니즘)
- → F22_generic_types (제네릭과 타입 파라미터)
- → F23_structural_vs_nominal_typing (타입 호환성 결정 방식)
- → F24_duck_typing (동적 타이핑의 핵심 개념)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00e_typescript_intro (TypeScript의 타입 시스템)
- → 22_java_kotlin_backend_foundations (Java의 정적 타이핑)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
