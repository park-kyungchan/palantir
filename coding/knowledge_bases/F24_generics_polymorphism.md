# F24: Generics & Type Polymorphism (제네릭과 타입 다형성)

> **Concept ID**: `F24_generics_polymorphism`
> **Universal Principle**: 타입을 매개변수화하여 재사용 가능한 타입-안전 코드 작성
> **Prerequisites**: F20_static_vs_dynamic_typing, F23_structural_vs_nominal_typing

---

## 1. Universal Concept (언어 무관 개념 정의)

**제네릭(Generics)**은 타입을 매개변수로 받아 재사용 가능한 코드를 작성하는 메커니즘입니다. "어떤 타입이든 담을 수 있는 상자"를 만드는 것이라고 생각할 수 있습니다.

### 1.1 Parametric Polymorphism vs Ad-hoc Polymorphism

**Parametric Polymorphism (파라메트릭 다형성)**:
- 타입에 관계없이 동일한 코드가 동작
- `List<T>`는 T가 무엇이든 같은 방식으로 동작
- 타입 안전성 보장: 컴파일 시점에 타입 체크

**Ad-hoc Polymorphism (애드혹 다형성)**:
- 타입에 따라 다른 구현이 동작
- 메서드 오버로딩, 연산자 오버로딩
- 같은 이름, 다른 행동

```
// Parametric: 모든 T에 대해 동일한 로직
function identity<T>(x: T): T { return x; }

// Ad-hoc: 타입마다 다른 로직
function add(a: number, b: number): number;
function add(a: string, b: string): string;
```

### 1.2 Type Erasure vs Reification

**Type Erasure (타입 소거)**:
- 컴파일 후 제네릭 타입 정보가 사라짐
- Java, TypeScript가 이 방식 사용
- 런타임에 `List<String>`과 `List<Integer>` 구분 불가

**Reification (타입 구체화)**:
- 런타임에도 제네릭 타입 정보 유지
- C#, Go, C++(템플릿)가 이 방식 사용
- 런타임 타입 체크 가능

### 1.3 Bounded Generics (제약 있는 제네릭)

타입 파라미터에 제약을 걸어 특정 능력을 보장:

```
// Java: T는 반드시 Comparable을 구현해야 함
<T extends Comparable<T>>

// Go: T는 반드시 ordered 제약 만족해야 함
[T constraints.Ordered]

// TypeScript: T는 반드시 length 속성을 가져야 함
<T extends { length: number }>
```

### 1.4 Variance (변성): Covariance, Contravariance, Invariance

타입 파라미터의 상속 관계가 제네릭 타입의 상속 관계에 어떻게 영향을 미치는가?

**Invariance (무공변)**:
- `List<Dog>`는 `List<Animal>`이 아님
- 대부분의 제네릭 컨테이너의 기본 동작
- 가장 안전하지만 유연성 제한

**Covariance (공변, 출력 위치)**:
- `Dog`가 `Animal`의 하위 타입이면, `Producer<Dog>`도 `Producer<Animal>`의 하위 타입
- "읽기 전용"일 때 안전
- Java: `? extends T`, Kotlin: `out T`, C#: `out T`

**Contravariance (반공변, 입력 위치)**:
- `Dog`가 `Animal`의 하위 타입이면, `Consumer<Animal>`이 `Consumer<Dog>`의 하위 타입
- "쓰기 전용"일 때 안전
- Java: `? super T`, Kotlin: `in T`, C#: `in T`

**Mental Model - PECS (Producer Extends, Consumer Super)**:
```
// Producer (출력) - Covariant (extends/out)
List<? extends Animal> animals = new ArrayList<Dog>(); // OK
Animal a = animals.get(0); // OK - 꺼내기 가능
animals.add(new Dog()); // COMPILE ERROR - 넣기 불가

// Consumer (입력) - Contravariant (super/in)
List<? super Dog> dogs = new ArrayList<Animal>(); // OK
dogs.add(new Dog()); // OK - 넣기 가능
Dog d = dogs.get(0); // COMPILE ERROR - 타입 모름
```

### 1.5 Why This Matters

제네릭을 이해하지 못하면:
- 타입 안전하지 않은 코드 작성 (`Object` 남용, 형변환 지옥)
- Java의 unchecked warning 무시하다 런타임 `ClassCastException`
- 라이브러리 API 설계 시 유연성과 안전성 균형 실패
- Variance 이해 없이 컬렉션 API 오용

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Generic Syntax** | `<T>` | `[T]` (3.12+) / `Generic[T]` | `<T>` | `[T]` (1.18+) | N/A | `template<typename T>` | N/A |
| **Type Erasure** | Yes (런타임 정보 소실) | N/A (동적 타입) | Yes (JS로 컴파일) | No (monomorphization) | N/A | No (monomorphization) | N/A |
| **Bounded Generics** | `extends` / `super` | `TypeVar(bound=...)` | `extends` | type constraints | N/A | concepts (C++20) | N/A |
| **Variance** | wildcards `? extends/super` | 제한적 지원 | `in`/`out` (함수) | Invariant only | N/A | Template specialization | N/A |
| **Multiple Bounds** | `<T extends A & B>` | `TypeVar(bound=...)` | `<T extends A & B>` | `[T A | B]` (union) | N/A | `requires` (C++20) | N/A |
| **Type Inference** | Diamond `<>` (Java 7+) | 자동 | 대부분 자동 | 자동 | N/A | `auto` (C++11+) | N/A |
| **Pitfall** | Type erasure, raw types | 런타임 체크 없음 | `any` 오용 | 복잡한 constraints | N/A | Code bloat | N/A |

### 2.2 Semantic Notes

**Java Generics (Type Erasure 핵심)**:
```java
// 컴파일 시 - 타입 체크
List<String> strings = new ArrayList<>();
strings.add("hello");
String s = strings.get(0); // 자동 캐스팅

// 런타임 시 - 타입 소거됨
List strings = new ArrayList(); // List<String> → List
strings.add("hello");
String s = (String) strings.get(0); // 명시적 캐스팅 삽입

// 타입 소거의 결과
List<String> a = new ArrayList<>();
List<Integer> b = new ArrayList<>();
a.getClass() == b.getClass(); // true! 둘 다 ArrayList.class

// 런타임 타입 체크 불가
if (list instanceof List<String>) {} // COMPILE ERROR
```

**Java Wildcards (PECS 원칙)**:
```java
// Upper Bounded (Producer) - 읽기 전용
public void printAll(List<? extends Animal> animals) {
    for (Animal a : animals) { // OK
        System.out.println(a);
    }
    // animals.add(new Dog()); // COMPILE ERROR
}

// Lower Bounded (Consumer) - 쓰기 전용
public void addDogs(List<? super Dog> list) {
    list.add(new Dog()); // OK
    list.add(new Puppy()); // OK (Puppy extends Dog)
    // Dog d = list.get(0); // COMPILE ERROR - Object만 보장
}

// Unbounded - 읽기만 (Object로)
public void process(List<?> list) {
    Object o = list.get(0); // OK
    // list.add(anything); // COMPILE ERROR (null 제외)
}
```

**Go 1.18+ Generics (늦게 추가된 이유)**:
```go
// Go의 설계 철학: 단순함 > 기능
// 10년간 제네릭 없이 interface{}와 type assertion으로 버팀

// 제네릭 없던 시절
func PrintAll(items []interface{}) {
    for _, item := range items {
        fmt.Println(item) // 타입 안전성 없음
    }
}

// Go 1.18+ 제네릭
func PrintAll[T any](items []T) {
    for _, item := range items {
        fmt.Println(item)
    }
}

// Type Constraints (제약 조건)
type Number interface {
    ~int | ~int64 | ~float64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

// Go는 monomorphization - 타입별로 코드 생성
// Sum[int]와 Sum[float64]는 별개의 함수로 컴파일
```

**Go가 제네릭을 늦게 추가한 이유**:
1. **단순함 우선**: Go의 핵심 가치는 "less is more"
2. **Interface로 충분**: 많은 경우 interface{}로 해결 가능했음
3. **컴파일 시간**: 제네릭은 컴파일 시간 증가 우려
4. **설계 신중함**: 잘못된 제네릭 설계는 되돌리기 어려움

**TypeScript Generics (컴파일 타임 전용)**:
```typescript
// 컴파일 시점에만 존재
function identity<T>(arg: T): T {
    return arg;
}

// 컴파일 후 JavaScript
function identity(arg) {
    return arg;
}

// Constraints
interface HasLength {
    length: number;
}

function logLength<T extends HasLength>(arg: T): number {
    return arg.length; // length 접근 보장
}

// Conditional Types (고급)
type NonNullable<T> = T extends null | undefined ? never : T;

// Mapped Types
type Readonly<T> = {
    readonly [P in keyof T]: T[P];
};
```

**C++ Templates (Monomorphization)**:
```cpp
// 템플릿 정의
template<typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

// 사용 시 타입별로 코드 생성 (monomorphization)
int m1 = max<int>(1, 2);      // max_int 함수 생성
double m2 = max<double>(1.0, 2.0); // max_double 함수 생성

// C++20 Concepts (Bounded Generics)
template<typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::same_as<T>;
};

template<Addable T>
T add(T a, T b) {
    return a + b;
}

// 타입 정보가 런타임에도 유지
// RTTI (Run-Time Type Information) 사용 가능
```

**Java vs C++ 비교**:
| 측면 | Java Generics | C++ Templates |
|------|---------------|---------------|
| 구현 | Type Erasure | Monomorphization |
| 런타임 타입 | 소실 | 유지 |
| 바이너리 크기 | 작음 | 타입별로 증가 (code bloat) |
| 컴파일 시간 | 빠름 | 느림 (타입별 생성) |
| 에러 메시지 | 비교적 명확 | 악명 높게 복잡 |
| 특수화 | 불가 | Template Specialization 가능 |

**Python Generics (typing 모듈)**:
```python
# Python 3.9 이전
from typing import Generic, TypeVar, List

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: List[T] = []

    def push(self, item: T) -> None:
        self.items.append(item)

    def pop(self) -> T:
        return self.items.pop()

# Python 3.12+ 새로운 문법
class Stack[T]:
    def __init__(self) -> None:
        self.items: list[T] = []

# Bounded TypeVar
from typing import TypeVar

T = TypeVar('T', bound='Comparable')

# 주의: Python의 타입 힌트는 런타임에 체크되지 않음!
# mypy, pyright 등 정적 분석 도구로만 체크
```

**SQL/Spark - 제네릭 N/A 이유**:

SQL과 Spark는 데이터 처리 언어/프레임워크로, 전통적인 의미의 제네릭이 없습니다:

```sql
-- SQL은 스키마 기반, 타입이 테이블 정의에 고정
CREATE TABLE users (
    id INT,
    name VARCHAR(100)
);

-- 제네릭 대신 다형성은 UNION, CASE WHEN으로 처리
SELECT
    CASE WHEN type = 'A' THEN value_a ELSE value_b END
FROM data;
```

```python
# Spark - 스키마 추론 또는 명시
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

# 제네릭 대신 스키마로 타입 정의
schema = StructType([
    StructField("id", IntegerType(), False),
    StructField("name", StringType(), True)
])

df = spark.read.schema(schema).json("data.json")

# DataFrame은 Row 타입 컬렉션 - 제네릭 불필요
# Dataset[T]는 Scala API에서 타입 파라미터 지원
```

### 2.3 Variance 비교

| Language | Covariance | Contravariance | Declaration Site vs Use Site |
|----------|------------|----------------|------------------------------|
| Java | `? extends T` | `? super T` | Use-site (사용 시점) |
| Kotlin | `out T` | `in T` | Declaration-site (선언 시점) |
| C# | `out T` | `in T` | Declaration-site |
| TypeScript | 함수 반환 | 함수 파라미터 | Structural (구조적) |
| Go | N/A | N/A | Invariant only |
| C++ | N/A | N/A | Template specialization |

**Java Use-site Variance vs Kotlin Declaration-site Variance**:
```java
// Java - 사용할 때마다 variance 지정
List<? extends Animal> readOnlyAnimals;
List<? super Dog> writeOnlyDogs;

// 매번 지정해야 해서 번거로움
public void process(List<? extends Animal> animals) {...}
```

```kotlin
// Kotlin - 선언할 때 한 번만 지정
class Producer<out T>(val value: T)  // 항상 covariant
class Consumer<in T> { fun consume(item: T) {} }  // 항상 contravariant

// 사용 시 variance 지정 불필요
fun process(producer: Producer<Animal>) {...}
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Ch.4](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html#jls-4.5) | Parameterized Types |
| Java | [Effective Java](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/) | Item 31: Use bounded wildcards |
| Python | [PEP 484](https://peps.python.org/pep-0484/) | Type Hints |
| Python | [PEP 695](https://peps.python.org/pep-0695/) | Type Parameter Syntax (3.12) |
| TypeScript | [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html) | Handbook - Generics |
| Go | [Type Parameters](https://go.dev/ref/spec#Type_parameter_declarations) | Language Spec - Generics |
| Go | [Why Generics](https://go.dev/blog/why-generics) | Design rationale |
| C++ | [Templates](https://en.cppreference.com/w/cpp/language/templates) | cppreference |
| C++ | [Concepts](https://en.cppreference.com/w/cpp/language/constraints) | C++20 Constraints |

---

## 4. Palantir Context Hint

**Foundry/OSDK Relevance**:
- TypeScript OSDK에서 제네릭 API 설계 이해 필수
- `OntologyObject<T>` 같은 제네릭 타입 활용
- Java 백엔드 서비스에서 type-safe 컬렉션 처리
- Python transforms에서 TypeVar 활용한 타입 힌팅

**Interview Relevance**:
- "Java에서 type erasure가 무엇이고, 왜 이런 설계를 했나요?"
- "List<? extends Number>와 List<Number>의 차이는 무엇인가요?"
- "PECS 원칙을 설명하고 예시를 들어주세요"
- "Go의 제네릭은 왜 10년이나 늦게 추가되었나요?"
- "TypeScript의 Generic과 Java의 차이점은 무엇인가요?"
- "C++ 템플릿과 Java 제네릭의 구현 방식 차이를 설명하세요"
- "Covariance와 Contravariance를 실제 코드로 설명해주세요"
- "왜 Java의 배열은 covariant인데 제네릭은 invariant인가요?"

**자주 나오는 함정 질문**:
```java
// Q: 이 코드가 왜 런타임 에러가 날까요?
Object[] array = new String[10];
array[0] = 42; // ArrayStoreException at runtime!

// A: Java 배열은 covariant + 런타임 체크
// 제네릭은 invariant로 이 문제를 컴파일 시점에 방지
List<Object> list = new ArrayList<String>(); // COMPILE ERROR
```

---

## 5. Cross-References

### Related Concepts
- → F20_static_vs_dynamic_typing (제네릭의 기반인 정적 타이핑)
- → F23_structural_vs_nominal_typing (TypeScript의 구조적 제네릭)
- → F70_inheritance_composition (상속과 제네릭의 관계)
- → F25_type_inference (제네릭 타입 추론)

### Design Patterns with Generics
- Factory Pattern: `Factory<T>`
- Repository Pattern: `Repository<T, ID>`
- Builder Pattern: `Builder<T>`

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 22_java_kotlin_backend_foundations (Java 제네릭 실무)
- → 00e_typescript_intro (TypeScript 제네릭)

---

## 6. Deep Dive: Type Erasure (면접 핵심)

Type erasure는 Palantir 면접에서 자주 등장하는 주제입니다.

### 6.1 왜 Java는 Type Erasure를 선택했나?

**역사적 배경 (하위 호환성)**:
```java
// Java 1.4 이전 코드
List list = new ArrayList();
list.add("hello");
String s = (String) list.get(0);

// Java 5+ 제네릭 코드
List<String> list = new ArrayList<>();
list.add("hello");
String s = list.get(0); // 컴파일러가 캐스팅 삽입

// 둘이 같은 바이트코드!
// → 기존 라이브러리와 호환 유지
```

### 6.2 Type Erasure의 한계

```java
// 1. instanceof 불가
if (obj instanceof List<String>) {} // ERROR

// 2. 제네릭 배열 생성 불가
T[] array = new T[10]; // ERROR

// 3. static 컨텍스트에서 타입 파라미터 사용 불가
class Box<T> {
    static T item; // ERROR
}

// 4. 타입 파라미터로 new 불가
T obj = new T(); // ERROR

// 5. 오버로딩 충돌
void process(List<String> list) {}
void process(List<Integer> list) {} // ERROR - 같은 시그니처
```

### 6.3 Type Erasure 우회 방법

```java
// Class<T>를 통한 런타임 타입 정보 전달
public class TypedBox<T> {
    private Class<T> type;

    public TypedBox(Class<T> type) {
        this.type = type;
    }

    public T createInstance() throws Exception {
        return type.getDeclaredConstructor().newInstance();
    }

    public boolean isInstance(Object obj) {
        return type.isInstance(obj);
    }
}

// 사용
TypedBox<String> box = new TypedBox<>(String.class);
String s = box.createInstance();
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
