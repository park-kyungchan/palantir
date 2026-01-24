# F40: Function Declarations (함수 선언)

> **Concept ID**: `F40_function_declarations`
> **Universal Principle**: 재사용 가능한 코드 블록을 정의하고 이름을 부여하는 메커니즘
> **Prerequisites**: F10_lexical_scope, F01_variable_binding

---

## 1. Universal Concept (언어 무관 개념 정의)

**함수 선언(Function Declaration)**은 재사용 가능한 코드 블록에 이름을 부여하고, 입력(매개변수)을 받아 출력(반환값)을 생성하는 메커니즘입니다. 함수는 프로그래밍의 가장 기본적인 추상화 단위로, 복잡한 로직을 관리 가능한 단위로 분리합니다.

### 핵심 구분: 선언 vs 정의 vs 표현식

| 개념 | 설명 | 예시 |
|------|------|------|
| **선언(Declaration)** | 함수의 존재와 시그니처를 알림 | C++: `void foo();` |
| **정의(Definition)** | 함수의 실제 구현체 제공 | C++: `void foo() { ... }` |
| **표현식(Expression)** | 값으로서의 함수 생성 | JS: `const fn = function() {}` |

대부분의 언어에서 선언과 정의가 동시에 이루어지지만, C/C++처럼 분리하는 언어도 있습니다.

### 함수의 종류

```
                        ┌── Named Function (명명 함수)
                        │   def greet(): ...
        Functions ──────┼── Anonymous Function (익명 함수)
                        │   function() { ... }
                        │
                        └── Lambda/Arrow (람다/화살표)
                            x => x * 2
```

**Mental Model**:
함수를 **"요리 레시피"**로 생각하세요:
- **선언**: 레시피에 이름 붙이기 ("김치찌개")
- **매개변수**: 재료 목록 (두부, 김치, 돼지고기)
- **본문**: 조리 방법 (볶고, 끓이고, 간 맞추기)
- **반환값**: 완성된 요리

**First-Class Functions (일급 함수)**:
일급 함수란 함수를 **값(value)**처럼 다룰 수 있다는 의미입니다:
- 변수에 할당 가능 (`const fn = myFunction`)
- 함수의 인자로 전달 가능 (`array.map(fn)`)
- 함수의 반환값으로 사용 가능 (`return () => {}`)
- 자료구조에 저장 가능 (`{ handler: fn }`)

**Why This Matters**:
함수 선언을 이해하지 못하면:
- 코드 재사용과 DRY 원칙 적용 불가
- 콜백, 이벤트 핸들러 패턴 이해 불가
- 고차 함수(map, filter, reduce) 활용 불가
- 모듈화와 테스트 가능한 코드 작성 불가

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Declaration Syntax** | Method in class | `def name():` | `function`/`=>` | `func name()` | `CREATE FUNCTION` | `RetType name()` | `def name():` (UDF) |
| **Anonymous/Lambda** | `() -> expr` | `lambda x: x` | `(x) => x` | `func(x) {}` | N/A | `[](x){...}` | `lambda x: x` |
| **First-Class** | No (method refs) | Yes | Yes | Yes | No | Yes (C++11) | Yes |
| **Hoisting** | N/A (class member) | No | `function`: Yes, `const`: No | N/A | N/A | N/A | N/A |
| **Overloading** | Yes | No (default args) | No (union types) | No | Yes | Yes | No |
| **Named Returns** | No | No (tuple unpack) | No | Yes | No | No | No |
| **Default Params** | No (overload) | Yes | Yes | No | Yes (some DB) | Yes (C++11) | Yes |
| **Variadic** | `T... args` | `*args, **kwargs` | `...args` | `...T` | N/A | `...` (C++11) | `*args` |

### 2.2 Semantic Notes

**Declaration Syntax**:
- **Java**: 메서드는 반드시 클래스 내에 정의, static 또는 인스턴스 메서드
- **Python**: `def` 키워드로 정의, 들여쓰기로 블록 구분
- **TypeScript**: `function` 선언문, `const fn = function()` 표현식, `() =>` 화살표 함수
- **Go**: `func` 키워드, 리시버를 추가하면 메서드
- **SQL**: `CREATE FUNCTION`으로 사용자 정의 함수 생성
- **C++**: 선언과 정의 분리 가능, 헤더/소스 분리
- **Spark**: Python/Scala UDF를 `spark.udf.register()`로 등록

**First-Class Functions**:
- **Java**: 진정한 일급 함수가 아님. 람다는 함수형 인터페이스의 인스턴스
- **Python/TypeScript/Go/C++**: 함수를 값처럼 자유롭게 전달 가능
- **SQL**: 함수는 값이 아닌 프로시저적 구조

**Hoisting (JavaScript/TypeScript 특수)**:
```javascript
// function 선언문: 호이스팅됨 (전체가 끌어올려짐)
sayHi();  // 작동!
function sayHi() { console.log("Hi"); }

// function 표현식: 변수 규칙 따름
// sayBye();  // TypeError: sayBye is not a function
var sayBye = function() { console.log("Bye"); };

// arrow function + const: TDZ 적용
// greet();  // ReferenceError
const greet = () => console.log("Hello");
```

**Overloading**:
- **Java/C++/SQL**: 같은 이름, 다른 매개변수로 오버로딩 지원
- **Python**: 오버로딩 없음, 기본 인자와 `*args`로 대체
- **TypeScript**: 타입 레벨 오버로드 시그니처, 런타임은 하나
- **Go**: 오버로딩 없음, 다른 이름 사용 권장

---

## 3. Code Examples by Language

### 3.1 Java: Methods in Classes

```java
// === 기본 메서드 선언 ===
public class Calculator {
    // 인스턴스 메서드
    public int add(int a, int b) {
        return a + b;
    }

    // 정적 메서드
    public static int multiply(int a, int b) {
        return a * b;
    }

    // 오버로딩: 같은 이름, 다른 매개변수
    public int add(int a, int b, int c) {
        return a + b + c;
    }

    public double add(double a, double b) {
        return a + b;
    }
}

// === Lambda 표현식 (Java 8+) ===
// 함수형 인터페이스 구현체로 동작
Comparator<String> byLength = (s1, s2) -> s1.length() - s2.length();
List<String> sorted = names.stream()
    .sorted(byLength)
    .collect(Collectors.toList());

// === 메서드 참조 (Method Reference) ===
// 기존 메서드를 람다처럼 사용
list.forEach(System.out::println);      // 인스턴스 메서드 참조
list.sort(String::compareToIgnoreCase); // 특정 타입 인스턴스 메서드

// 메서드 참조 종류:
// 1. 정적 메서드: ClassName::staticMethod
// 2. 인스턴스 메서드: instance::method
// 3. 타입의 인스턴스 메서드: ClassName::instanceMethod
// 4. 생성자: ClassName::new

// 예시
Function<String, Integer> parser = Integer::parseInt;  // 정적 메서드
Consumer<String> printer = System.out::println;        // 인스턴스 메서드
Supplier<List<String>> listFactory = ArrayList::new;   // 생성자 참조

// === Lambda vs Method Reference 차이 ===
// Lambda: 새 함수 정의
names.stream().map(s -> s.toUpperCase());

// Method Reference: 기존 메서드 참조
names.stream().map(String::toUpperCase);
```

### 3.2 Python: def and lambda

```python
# === 기본 함수 선언 ===
def greet(name: str) -> str:
    """인사말 반환 (타입 힌트 포함)"""
    return f"Hello, {name}!"

# === 기본값 매개변수 ===
def create_user(name: str, age: int = 0, active: bool = True):
    return {"name": name, "age": age, "active": active}

# === 가변 인자 ===
def sum_all(*args):           # 위치 인자 튜플
    return sum(args)

def print_info(**kwargs):     # 키워드 인자 딕셔너리
    for key, value in kwargs.items():
        print(f"{key}: {value}")

def combined(a, b, *args, key=None, **kwargs):
    # a, b: 필수 위치 인자
    # *args: 추가 위치 인자들
    # key: 키워드 전용 인자 (기본값)
    # **kwargs: 추가 키워드 인자들
    pass

# === Lambda 표현식 ===
# 단일 표현식만 가능 (statements 불가)
square = lambda x: x ** 2
add = lambda a, b: a + b

# 고차 함수와 함께 사용
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x ** 2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))

# === Lambda의 한계 (Statements 불가) ===
# 아래는 불가능:
# bad = lambda x: if x > 0: return x  # SyntaxError
# bad = lambda x: x = x + 1           # SyntaxError

# 해결: 조건식(ternary) 사용
abs_value = lambda x: x if x >= 0 else -x

# === 일급 함수로서 활용 ===
def apply_operation(func, a, b):
    return func(a, b)

result = apply_operation(lambda x, y: x * y, 3, 4)  # 12

# 함수를 반환하는 함수 (클로저)
def make_multiplier(n):
    def multiplier(x):
        return x * n
    return multiplier

double = make_multiplier(2)
double(5)  # 10
```

### 3.3 TypeScript: function vs Arrow (this 바인딩 차이!)

```typescript
// === Function Declaration (함수 선언문) ===
// 호이스팅됨: 선언 전에 호출 가능
sayHello("World");  // 작동!

function sayHello(name: string): string {
    return `Hello, ${name}!`;
}

// === Function Expression (함수 표현식) ===
// 호이스팅 안됨 (변수 규칙 따름)
// greet("World");  // Error: greet is not defined
const greet = function(name: string): string {
    return `Hi, ${name}!`;
};

// === Arrow Function (화살표 함수) ===
const add = (a: number, b: number): number => a + b;
const square = (x: number): number => x * x;

// 단일 표현식은 중괄호/return 생략 가능
const double = (x: number) => x * 2;

// 복잡한 로직은 중괄호 사용
const calculate = (x: number): number => {
    const temp = x * 2;
    return temp + 1;
};

// === 중요: this 바인딩 차이 ===
class Counter {
    count = 0;

    // 일반 메서드: this가 동적 바인딩
    incrementRegular() {
        setTimeout(function() {
            // this가 undefined 또는 window!
            // this.count++;  // Error!
        }, 100);
    }

    // Arrow Function: this가 렉시컬 바인딩 (정의 시점의 this)
    incrementArrow() {
        setTimeout(() => {
            this.count++;  // 올바르게 Counter의 this 참조
        }, 100);
    }
}

// === 콜백에서의 this 문제 ===
const obj = {
    name: "Alice",
    friends: ["Bob", "Charlie"],

    // 잘못된 패턴: function은 자신만의 this를 가짐
    printFriendsBad() {
        this.friends.forEach(function(friend) {
            // console.log(this.name + " knows " + friend);
            // this.name은 undefined!
        });
    },

    // 올바른 패턴 1: Arrow Function 사용
    printFriendsArrow() {
        this.friends.forEach(friend => {
            console.log(this.name + " knows " + friend);  // 정상 작동
        });
    },

    // 올바른 패턴 2: bind 사용 (레거시)
    printFriendsBind() {
        this.friends.forEach(function(friend) {
            console.log(this.name + " knows " + friend);
        }.bind(this));
    }
};

// === 오버로드 시그니처 (타입 레벨만) ===
function padLeft(value: string, padding: number): string;
function padLeft(value: string, padding: string): string;
function padLeft(value: string, padding: number | string): string {
    if (typeof padding === "number") {
        return " ".repeat(padding) + value;
    }
    return padding + value;
}

// === 제네릭 함수 ===
function identity<T>(value: T): T {
    return value;
}

const result = identity<string>("hello");
const inferred = identity(42);  // T가 number로 추론됨

// === 타입 가드 함수 ===
function isString(value: unknown): value is string {
    return typeof value === "string";
}
```

### 3.4 Go: Named Return Values (고유 기능!)

```go
package main

import (
    "errors"
    "fmt"
)

// === 기본 함수 선언 ===
func add(a, b int) int {
    return a + b
}

// === 다중 반환값 ===
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// === Named Return Values (명명된 반환값) - Go 고유 기능! ===
// 반환 변수가 함수 시작 시 선언되고 zero value로 초기화됨
func rectangleStats(width, height float64) (area, perimeter float64) {
    area = width * height
    perimeter = 2 * (width + height)
    return  // "naked return" - 명명된 변수들이 자동 반환
}

// Named Return의 장점:
// 1. 문서화: 반환값의 의미가 명확
// 2. defer에서 수정 가능
func readFile() (content string, err error) {
    defer func() {
        if err != nil {
            err = fmt.Errorf("readFile failed: %w", err)
        }
    }()
    // ... 파일 읽기 로직
    return
}

// 3. zero value 자동 초기화
func getDefaults() (name string, age int, active bool) {
    // name = "", age = 0, active = false 로 초기화됨
    name = "Default"
    return  // age=0, active=false 반환
}

// Named Return 주의사항:
// - 짧은 함수에서만 사용 권장
// - 긴 함수에서는 명시적 return이 더 명확

// === 가변 인자 (Variadic) ===
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

// 호출: sum(1, 2, 3) 또는 sum(slice...)
// numbers := []int{1, 2, 3}
// sum(numbers...)

// === 익명 함수 (Function Literal) ===
func main() {
    // 변수에 할당
    double := func(x int) int {
        return x * 2
    }
    fmt.Println(double(5))  // 10

    // 즉시 실행 (IIFE)
    result := func(a, b int) int {
        return a + b
    }(3, 4)

    // 클로저로 사용
    counter := makeCounter()
    fmt.Println(counter())  // 1
    fmt.Println(counter())  // 2
}

// 클로저 반환 함수
func makeCounter() func() int {
    count := 0
    return func() int {
        count++
        return count
    }
}

// === 메서드 (리시버가 있는 함수) ===
type Rectangle struct {
    Width, Height float64
}

// 값 리시버 (복사본에서 작동)
func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

// 포인터 리시버 (원본 수정 가능)
func (r *Rectangle) Scale(factor float64) {
    r.Width *= factor
    r.Height *= factor
}
```

### 3.5 SQL: CREATE FUNCTION

```sql
-- === PostgreSQL: Scalar Function ===
CREATE OR REPLACE FUNCTION calculate_tax(price NUMERIC, rate NUMERIC DEFAULT 0.1)
RETURNS NUMERIC AS $$
BEGIN
    RETURN price * rate;
END;
$$ LANGUAGE plpgsql;

-- 사용
SELECT calculate_tax(100);        -- 10.0 (기본 rate 0.1)
SELECT calculate_tax(100, 0.15);  -- 15.0

-- === PostgreSQL: Table-Valued Function ===
CREATE OR REPLACE FUNCTION get_employees_by_dept(dept_id INT)
RETURNS TABLE(id INT, name VARCHAR, salary NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT e.id, e.name, e.salary
    FROM employees e
    WHERE e.department_id = dept_id;
END;
$$ LANGUAGE plpgsql;

-- 사용
SELECT * FROM get_employees_by_dept(10);

-- === SQL Server: Inline Table-Valued Function ===
CREATE FUNCTION dbo.GetOrdersByCustomer(@CustomerID INT)
RETURNS TABLE
AS
RETURN (
    SELECT OrderID, OrderDate, TotalAmount
    FROM Orders
    WHERE CustomerID = @CustomerID
);
GO

-- === MySQL: Stored Function ===
DELIMITER //
CREATE FUNCTION full_name(first_name VARCHAR(50), last_name VARCHAR(50))
RETURNS VARCHAR(101)
DETERMINISTIC
BEGIN
    RETURN CONCAT(first_name, ' ', last_name);
END //
DELIMITER ;

-- 사용
SELECT full_name('John', 'Doe');

-- === 오버로딩 (PostgreSQL) ===
-- 같은 이름, 다른 매개변수 타입
CREATE FUNCTION format_value(val INT) RETURNS TEXT AS $$
BEGIN RETURN val::TEXT; END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION format_value(val DATE) RETURNS TEXT AS $$
BEGIN RETURN TO_CHAR(val, 'YYYY-MM-DD'); END;
$$ LANGUAGE plpgsql;

-- PostgreSQL은 인자 타입으로 적절한 함수 선택
SELECT format_value(42);           -- '42'
SELECT format_value('2024-01-15'::DATE);  -- '2024-01-15'
```

### 3.6 C++: Declaration/Definition Separation & Lambda

```cpp
#include <iostream>
#include <functional>
#include <vector>
#include <algorithm>

// === 선언과 정의 분리 (헤더/소스) ===
// calculator.h
int add(int a, int b);        // 선언만
double add(double a, double b); // 오버로딩

// calculator.cpp
int add(int a, int b) {       // 정의
    return a + b;
}

double add(double a, double b) {
    return a + b;
}

// === 기본 매개변수 (C++11) ===
void greet(const std::string& name = "World") {
    std::cout << "Hello, " << name << "!" << std::endl;
}

// === 람다 표현식 (C++11+) ===
int main() {
    // 기본 람다
    auto add = [](int a, int b) { return a + b; };
    std::cout << add(3, 4) << std::endl;  // 7

    // === 캡처 리스트 (Capture List) ===
    int x = 10;
    int y = 20;

    // [=] : 모든 외부 변수를 값으로 캡처
    auto byValue = [=]() { return x + y; };

    // [&] : 모든 외부 변수를 참조로 캡처
    auto byRef = [&]() { x++; return x + y; };

    // [x, &y] : x는 값, y는 참조로 캡처
    auto mixed = [x, &y]() { y++; return x + y; };

    // [this] : 현재 객체의 this 포인터 캡처 (멤버 접근용)
    // [*this] : 현재 객체를 값으로 복사 (C++17)

    // === mutable 키워드 ===
    // 값 캡처된 변수를 람다 내에서 수정하려면 mutable 필요
    int counter = 0;
    auto increment = [counter]() mutable {
        return ++counter;  // counter의 복사본 수정
    };
    std::cout << increment() << std::endl;  // 1
    std::cout << increment() << std::endl;  // 2
    std::cout << counter << std::endl;      // 0 (원본 unchanged)

    // === 제네릭 람다 (C++14) ===
    auto genericAdd = [](auto a, auto b) { return a + b; };
    std::cout << genericAdd(1, 2) << std::endl;      // 3
    std::cout << genericAdd(1.5, 2.5) << std::endl;  // 4.0

    // === STL 알고리즘과 함께 ===
    std::vector<int> nums = {1, 2, 3, 4, 5};

    // transform
    std::transform(nums.begin(), nums.end(), nums.begin(),
                   [](int x) { return x * 2; });

    // sort with custom comparator
    std::sort(nums.begin(), nums.end(),
              [](int a, int b) { return a > b; });  // 내림차순

    // find_if
    auto it = std::find_if(nums.begin(), nums.end(),
                           [](int x) { return x > 5; });

    return 0;
}

// === 함수 포인터 vs std::function ===
// 함수 포인터: C 스타일, 캡처 없는 람다만 가능
int (*funcPtr)(int, int) = [](int a, int b) { return a + b; };

// std::function: 람다, 함수 포인터, 함수 객체 모두 저장 가능
std::function<int(int, int)> func = [x](int a, int b) { return a + b + x; };
```

### 3.7 Spark: UDF Registration and Performance

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType, IntegerType, StructType, StructField

spark = SparkSession.builder.appName("UDF Demo").getOrCreate()

# === 방법 1: @udf 데코레이터 ===
@udf(returnType=StringType())
def format_name(first: str, last: str) -> str:
    return f"{last}, {first}"

# === 방법 2: udf() 함수로 래핑 ===
def calculate_age_group(age: int) -> str:
    if age < 18:
        return "minor"
    elif age < 65:
        return "adult"
    else:
        return "senior"

age_group_udf = udf(calculate_age_group, StringType())

# === 방법 3: spark.udf.register (SQL에서 사용 가능) ===
def add_tax(price: float, rate: float = 0.1) -> float:
    return price * (1 + rate)

spark.udf.register("add_tax", add_tax)

# SQL에서 사용
spark.sql("SELECT add_tax(100) AS total_price")

# === UDF 사용 예시 ===
df = spark.createDataFrame([
    ("John", "Doe", 25, 1000.0),
    ("Jane", "Smith", 17, 500.0),
], ["first_name", "last_name", "age", "salary"])

result = df.select(
    format_name(col("first_name"), col("last_name")).alias("full_name"),
    age_group_udf(col("age")).alias("age_group")
)

# === Lambda UDF (간단한 변환용) ===
upper_udf = udf(lambda x: x.upper() if x else None, StringType())
df.select(upper_udf(col("first_name")))

# === Pandas UDF (성능 최적화, Arrow 사용) ===
from pyspark.sql.functions import pandas_udf
import pandas as pd

@pandas_udf(IntegerType())
def vectorized_add(a: pd.Series, b: pd.Series) -> pd.Series:
    return a + b

# Pandas UDF는 일반 UDF보다 10-100배 빠를 수 있음!

# === UDF 성능 주의사항 ===
"""
1. UDF는 JVM -> Python -> JVM 전환 오버헤드 발생
2. 가능하면 내장 함수 (pyspark.sql.functions) 사용
3. 복잡한 로직은 Pandas UDF로 벡터화
4. UDF 내에서 외부 객체 참조 시 직렬화 문제 주의

나쁜 패턴:
    connection = database.connect()  # driver에서 생성
    @udf(...)
    def bad_udf(x):
        return connection.query(x)  # executor에서 사용 -> 직렬화 실패

좋은 패턴:
    @udf(...)
    def good_udf(x):
        connection = database.connect()  # executor에서 생성
        return connection.query(x)
"""

# === Scala UDF (참고: Spark의 네이티브 언어) ===
# Scala에서는 JVM 오버헤드 없이 더 효율적
"""
// Scala
val formatName = udf((first: String, last: String) => s"$last, $first")
df.select(formatName($"first_name", $"last_name"))
"""
```

---

## 4. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JLS Methods](https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.4) | Method Declarations |
| Python | [Defining Functions](https://docs.python.org/3/tutorial/controlflow.html#defining-functions) | Function definitions |
| TypeScript | [Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html) | Function Type Expressions |
| Go | [Function declarations](https://go.dev/ref/spec#Function_declarations) | Function types |
| SQL | [PostgreSQL CREATE FUNCTION](https://www.postgresql.org/docs/current/sql-createfunction.html) | User-defined Functions |
| C++ | [cppreference Functions](https://en.cppreference.com/w/cpp/language/function) | Function declaration |
| Spark | [UDF (Scala/Python)](https://spark.apache.org/docs/latest/sql-ref-functions-udf-scalar.html) | User Defined Scalar Functions |

**추가 자료**:
- [MDN: Functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions) - JavaScript 함수 완벽 가이드
- [Effective Go: Functions](https://go.dev/doc/effective_go#functions) - Go 함수 베스트 프랙티스

---

## 5. Palantir Context Hint

### Foundry/OSDK Relevance

**TypeScript OSDK 패턴**:
```typescript
// OSDK에서 함수 정의 패턴
import { Functions } from "@osdk/client";

// Arrow function으로 핸들러 정의 (this 바인딩 이슈 방지)
const fetchData = async (objectRid: string): Promise<OSDKObject> => {
    const client = await Client.auth(getToken);
    return await client.objects.get(objectRid);
};

// 이벤트 핸들러에서 arrow function 필수
class DataManager {
    private data: string[] = [];

    // 올바른 패턴: arrow function
    loadData = async () => {
        this.data = await fetchFromAPI();  // this 정상 작동
    };

    // 잘못된 패턴: 일반 function
    // loadDataBad() {
    //     setTimeout(function() {
    //         this.data = [];  // this가 undefined!
    //     }, 100);
    // }
}
```

**Spark UDF 성능 주의**:
```python
# Palantir Foundry Pipeline에서 UDF 사용 시
# 내장 함수로 가능한 작업은 UDF 피하기

# 나쁜 패턴 (UDF 사용)
@udf(StringType())
def concat_with_separator(a, b):
    return f"{a}_{b}"

# 좋은 패턴 (내장 함수 사용)
from pyspark.sql.functions import concat_ws
df.select(concat_ws("_", col("a"), col("b")))
```

### Interview Questions (면접 빈출)

**1. JavaScript/TypeScript:**
> "function declaration과 function expression의 차이를 설명하세요."

**모범 답안**:
- **Function Declaration**: 호이스팅됨, 선언 전에 호출 가능
- **Function Expression**: 변수 규칙 따름 (var: undefined, const: TDZ)
- **Arrow Function**: this가 렉시컬 바인딩, 콜백에 적합

**2. Python:**
> "왜 Python lambda에서 statements를 사용할 수 없나요?"

**모범 답안**:
- Lambda는 **단일 표현식(expression)**만 허용하는 **익명 함수**
- Python 디자인 철학: "명시적이 암시적보다 낫다" (if/for는 `def` 사용)
- 표현식은 값을 반환하지만, statements는 부작용(side effect)을 수행
- 복잡한 로직은 `def`로 명명된 함수 정의 권장

**3. Java:**
> "Method Reference와 Lambda Expression의 차이를 설명하세요."

**모범 답안**:
```java
// Lambda: 새 함수 로직 정의
list.forEach(s -> System.out.println(s));

// Method Reference: 기존 메서드 재사용 (더 간결)
list.forEach(System.out::println);

// Method Reference 종류:
// - ClassName::staticMethod (Integer::parseInt)
// - instance::method (System.out::println)
// - ClassName::instanceMethod (String::toUpperCase)
// - ClassName::new (ArrayList::new)
```

**4. Go:**
> "Named Return Values는 언제 사용하나요?"

**모범 답안**:
- **문서화 목적**: 반환값의 의미를 명확히 전달
- **defer에서 수정**: 에러 래핑, 리소스 정리 시 유용
- **짧은 함수에서만 권장**: 긴 함수에서는 명시적 return이 가독성 좋음
- **naked return 주의**: 남용하면 코드 이해 어려움

**5. 종합:**
> "First-class function이 무엇이고, 어떤 언어가 지원하나요?"

**모범 답안**:
- 함수를 **값(value)**처럼 다룰 수 있는 특성
- 변수 할당, 인자 전달, 반환값, 자료구조 저장 가능
- **완전 지원**: Python, JavaScript/TypeScript, Go, C++11+
- **부분 지원**: Java (람다는 함수형 인터페이스 인스턴스)
- **미지원**: SQL (프로시저적 구조)

---

## 6. Cross-References (관련 개념)

### Related Concepts
- → F41_parameters_arguments (매개변수와 인자)
- → F43_higher_order_functions (고차 함수)
- → F44_closures (클로저)
- → F10_lexical_scope (렉시컬 스코프)
- → F13_hoisting (호이스팅 - TS/JS)
- → F24_generics_polymorphism (제네릭 함수)

### Existing KB Links
- → 00a_programming_fundamentals (프로그래밍 기초)
- → 00b_functions_and_scope (함수와 스코프 기초)
- → 00e_typescript_intro (TypeScript 함수)
- → 11_osdk_typescript (OSDK TypeScript 패턴)
- → 13_pipeline_builder (Spark UDF)
- → 22_java_kotlin_backend_foundations (Java 메서드)

---

## 7. Quick Cheat Sheet (빠른 참조)

### 언어별 함수 선언 문법

| 언어 | 기본 선언 | 람다/익명 | 반환 타입 |
|------|-----------|-----------|-----------|
| **Java** | `RetType name(T arg)` | `(arg) -> expr` | 메서드 앞 |
| **Python** | `def name(arg):` | `lambda arg: expr` | 타입 힌트 `-> T` |
| **TypeScript** | `function name(arg: T): R` | `(arg: T) => R` | 매개변수 뒤 `: R` |
| **Go** | `func name(arg T) R` | `func(arg T) R { }` | 매개변수 뒤 |
| **SQL** | `CREATE FUNCTION name(arg T)` | N/A | `RETURNS T` |
| **C++** | `R name(T arg)` | `[capture](T arg) { }` | 함수 앞 |
| **Spark** | `@udf(returnType=T)` | `udf(lambda x: ...)` | 데코레이터/인자 |

### 호이스팅 동작 (JavaScript/TypeScript)

| 선언 방식 | 호이스팅 | 선언 전 호출 | this 바인딩 |
|-----------|----------|--------------|-------------|
| `function fn()` | Yes (전체) | 가능 | 동적 |
| `var fn = function()` | 변수만 | TypeError | 동적 |
| `const fn = function()` | No (TDZ) | ReferenceError | 동적 |
| `const fn = () => {}` | No (TDZ) | ReferenceError | 렉시컬 |

### First-Class Function 지원 비교

| 기능 | Java | Python | TS | Go | C++ | SQL |
|------|------|--------|----|----|-----|-----|
| 변수 할당 | Method Ref | Yes | Yes | Yes | Yes | No |
| 인자 전달 | Lambda | Yes | Yes | Yes | Yes | No |
| 반환값 | Lambda | Yes | Yes | Yes | Yes | No |
| 자료구조 저장 | Lambda | Yes | Yes | Yes | Yes | No |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation |
