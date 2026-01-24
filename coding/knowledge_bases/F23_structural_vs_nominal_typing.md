# F23: Structural vs Nominal Typing (구조적 타이핑 vs 명목적 타이핑)

> **Concept ID**: `F23_structural_vs_nominal_typing`
> **Universal Principle**: 타입 호환성을 구조(shape)로 판단하는가, 명시적 선언(name)으로 판단하는가
> **Prerequisites**: F20_static_vs_dynamic_typing (타입 시스템 기초)

---

## 1. Universal Concept (언어 무관 개념 정의)

**타입 호환성**을 판단하는 방식은 프로그래밍 언어의 설계 철학을 반영하는 핵심 요소입니다. 크게 두 가지 접근법이 있습니다:

### Structural Typing (구조적 타이핑)
"**오리처럼 생기고, 오리처럼 꽥꽥대면, 오리다**" (Duck Typing의 정적 버전)

구조적 타이핑에서는 타입의 **이름**이 아니라 **구조(shape)**가 일치하면 호환됩니다. 두 타입이 같은 속성과 메서드를 가지면, 명시적 선언 없이도 호환됩니다.

```
// 개념적 예시 (TypeScript 스타일)
interface Duck { quack(): void; walk(): void; }
interface Robot { quack(): void; walk(): void; }

// Duck과 Robot은 같은 구조 → 호환됨!
```

### Nominal Typing (명목적 타이핑)
"**Duck 클래스라고 선언했으니 Duck이다**"

명목적 타이핑에서는 타입의 **이름과 선언**이 일치해야 호환됩니다. 구조가 동일해도 명시적으로 `implements`나 `extends`를 선언하지 않으면 다른 타입입니다.

```
// 개념적 예시 (Java 스타일)
interface Duck { void quack(); void walk(); }
class Robot { void quack() {} void walk() {} }

// Robot은 Duck을 implements하지 않음 → 호환 안 됨!
```

### Duck Typing (동적 언어)
동적 언어(Python, JavaScript)에서는 런타임에 구조를 검사합니다. 이를 **Duck Typing**이라 합니다. 정적 타입 검사 없이 실행 시점에 해당 메서드/속성이 있으면 호출됩니다.

**Mental Model**:
```
명목적 타이핑 (Nominal)           구조적 타이핑 (Structural)
─────────────────────────────    ─────────────────────────────
     Animal (interface)                  { name: string }
         │                                     ▲
    ┌────┴────┐                         ┌─────┴─────┐
    │         │                         │           │
  Dog       Cat                    { name: "A" } { name: "B" }
(implements) (implements)           (구조 일치면 호환)

"명시적 선언이 필수"               "구조만 같으면 OK"
```

**Why This Matters**:
구조적/명목적 타이핑의 차이를 이해하지 못하면:
- TypeScript에서 왜 interface를 implements 없이 사용할 수 있는지 혼란
- Go에서 왜 interface 구현을 명시하지 않는지 이해 못함
- Java에서 같은 구조의 두 클래스가 왜 호환되지 않는지 의아함
- API 설계 시 유연성과 안전성 사이의 트레이드오프를 모름

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Typing Style** | Nominal | Duck (동적) + Protocol (3.8+) | Structural | Structural (implicit) | Schema-based (nominal) | Nominal + Concepts (C++20) | Schema-based (structural) |
| **Interface Impl** | `implements` 명시 필수 | `Protocol` 상속 또는 Duck | implicit (자동) | implicit (자동) | N/A | `virtual` 상속, `concept` | N/A (스키마 일치) |
| **Type Alias** | 새로운 nominal 타입 | 단순 alias (같은 타입) | 단순 alias (구조 동일) | 새로운 nominal 타입 (`type`) | 컬럼 타입 alias | `typedef`=alias, `using`=alias | 스키마 alias |
| **Compatibility** | 선언 기반 | 런타임 구조 | 컴파일 시 구조 | 컴파일 시 구조 | 스키마 일치 | 선언 기반 | 스키마 일치 |
| **Pitfall** | 과도한 interface 계층 | AttributeError 런타임 | excess property check | interface{} 남용 | 암묵적 형변환 | 다중 상속 복잡성 | 스키마 불일치 |

### 2.2 Semantic Notes

**TypeScript - 대표적 구조적 타이핑**:
```typescript
// 같은 구조면 호환 (이름 무관)
interface Point { x: number; y: number; }
interface Coordinate { x: number; y: number; }

function plot(p: Point) { console.log(p.x, p.y); }

const coord: Coordinate = { x: 1, y: 2 };
plot(coord);  // OK! 구조가 같으므로 호환

// 심지어 interface 없이도 가능
plot({ x: 3, y: 4 });  // OK! 객체 리터럴도 구조 일치
```

**Go - 암묵적 인터페이스 구현**:
```go
// interface 정의
type Writer interface {
    Write([]byte) (int, error)
}

// 아무 선언 없이 메서드만 구현하면 자동으로 Writer 구현체
type MyWriter struct{}

func (m MyWriter) Write(data []byte) (int, error) {
    return len(data), nil
}

// MyWriter는 Writer interface를 "암묵적으로" 구현
var w Writer = MyWriter{}  // 컴파일 OK
```

**Java - 명시적 implements 필수**:
```java
interface Drawable { void draw(); }

class Circle {
    public void draw() { System.out.println("Circle"); }
}

class Square implements Drawable {
    public void draw() { System.out.println("Square"); }
}

// Circle은 draw()가 있지만 Drawable이 아님!
Drawable d1 = new Circle();  // 컴파일 에러!
Drawable d2 = new Square();  // OK
```

**Python Protocol - 구조적 서브타이핑 (PEP 544, Python 3.8+)**:
```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

class Circle:
    def draw(self) -> None:
        print("Circle")

def render(obj: Drawable) -> None:
    obj.draw()

# Circle은 Drawable을 상속하지 않았지만 구조가 일치
render(Circle())  # mypy 통과! (구조적 서브타이핑)
```

**C++ Concepts (C++20) - 제약 기반 구조적 타이핑**:
```cpp
#include <concepts>

template<typename T>
concept Drawable = requires(T t) {
    { t.draw() } -> std::same_as<void>;
};

struct Circle {
    void draw() { std::cout << "Circle\n"; }
};

template<Drawable T>
void render(T& obj) { obj.draw(); }

// Circle은 Drawable concept을 만족 (구조적)
Circle c;
render(c);  // OK
```

**SQL - 스키마 기반 (명목적 경향)**:
```sql
-- 테이블은 명시적으로 정의된 스키마를 가짐
CREATE TABLE employees (id INT, name VARCHAR(100));
CREATE TABLE contractors (id INT, name VARCHAR(100));

-- 같은 구조지만 다른 테이블 = 다른 타입
-- UNION은 컬럼 타입이 호환되면 가능 (구조적 요소)
SELECT * FROM employees
UNION
SELECT * FROM contractors;  -- OK (같은 구조)
```

**Spark - DataFrame 스키마 (구조적)**:
```python
# Spark DataFrame은 스키마 기반 구조적 타이핑
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

schema1 = StructType([
    StructField("name", StringType()),
    StructField("age", IntegerType())
])

schema2 = StructType([
    StructField("name", StringType()),
    StructField("age", IntegerType())
])

# 스키마가 같으면 호환 (이름 무관)
df1.union(df2)  # 스키마 구조만 일치하면 OK
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.4](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) | Subtyping, implements |
| Python | [PEP 544](https://peps.python.org/pep-0544/) | Protocols: Structural subtyping |
| TypeScript | [Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) | Structural Type System |
| Go | [Effective Go](https://go.dev/doc/effective_go#interfaces) | Interfaces and implicit implementation |
| SQL | [ISO SQL](https://www.iso.org/standard/63555.html) | Type compatibility (vendor-specific) |
| C++ | [cppreference Concepts](https://en.cppreference.com/w/cpp/language/constraints) | C++20 Concepts |
| Spark | [StructType](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.types.StructType.html) | Schema compatibility |

---

## 4. Palantir Context Hint (선택적)

**Foundry/OSDK Relevance**:
- **TypeScript OSDK**: 구조적 타이핑 덕분에 Ontology 객체와 로컬 인터페이스 간 유연한 호환
- **Go 서비스**: gRPC 서비스에서 암묵적 인터페이스 구현으로 테스트 더블 쉽게 작성
- **Python transforms**: Protocol을 활용한 타입 안전 데이터 파이프라인
- **Spark Pipeline**: DataFrame 스키마 호환성 검사는 구조적 (컬럼 이름 + 타입)

**Interview Relevance**:
- "TypeScript와 Java의 interface 차이는?" → 구조적 vs 명목적
- "Go에서 interface를 implicit하게 구현하는 이유는?" → 디커플링, 테스트 용이성
- "Duck typing의 장단점은?" → 유연성 vs 런타임 에러 위험
- "Python Protocol과 ABC의 차이는?" → 구조적 vs 명목적 서브타이핑
- "TypeScript의 excess property check가 뭔가요?" → 객체 리터럴 특수 규칙
- "같은 구조의 두 타입이 왜 Java에서는 호환 안 되나요?" → Nominal typing

---

## 5. Cross-References (관련 개념)

### Related Concepts
- → F20_static_vs_dynamic_typing (정적/동적 타입의 기초)
- → F21_type_inference (타입 추론과 구조적 타이핑)
- → F24_generics_polymorphism (제네릭과 다형성)
- → F72_interfaces_protocols (인터페이스/프로토콜 심화)
- → F73_abstract_classes (추상 클래스 vs 인터페이스)

### Existing KB Links
- → 00a_programming_fundamentals (타입 시스템 기초)
- → 00e_typescript_intro (TypeScript 타입 시스템)
- → 01_language_foundation (언어별 타입 시스템)
- → 11_osdk_typescript (OSDK 인터페이스 활용)
- → 20_go_services_and_concurrency (Go 인터페이스 패턴)
- → 22_java_kotlin_backend_foundations (Java 타입 시스템)

---

## 6. Advanced: Hybrid Approaches and Edge Cases

### TypeScript의 Excess Property Check

TypeScript는 구조적 타이핑이지만, **객체 리터럴**에는 특별한 규칙이 있습니다:

```typescript
interface Point { x: number; y: number; }

// 변수를 통한 전달: 초과 속성 허용 (구조적)
const obj = { x: 1, y: 2, z: 3 };
const p: Point = obj;  // OK

// 직접 리터럴: 초과 속성 에러 (의도적 안전장치)
const p2: Point = { x: 1, y: 2, z: 3 };  // Error: 'z' does not exist
```

### Go의 Type Alias vs Type Definition

```go
// Type Alias (같은 타입)
type MyInt = int
var a int = 1
var b MyInt = a  // OK, 같은 타입

// Type Definition (새로운 nominal 타입)
type UserId int
type ProductId int
var userId UserId = 1
var productId ProductId = userId  // Error! 다른 타입
```

### TypeScript에서 Nominal 타이핑 흉내내기 (Brand Pattern)

```typescript
// 구조적 타이핑을 "브랜딩"으로 명목적으로 만들기
type UserId = number & { readonly _brand: 'UserId' };
type ProductId = number & { readonly _brand: 'ProductId' };

function getUser(id: UserId) { /* ... */ }

const userId = 123 as UserId;
const productId = 456 as ProductId;

getUser(userId);     // OK
getUser(productId);  // Error! Type 'ProductId' is not assignable
getUser(123);        // Error! Type 'number' is not assignable
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
