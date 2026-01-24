# F43: Higher-Order Functions (고차 함수)

> **Concept ID**: `F43_higher_order_functions`
> **Universal Principle**: 함수를 값으로 다루어 인자로 받거나 반환하는 함수
> **Prerequisites**: F40_function_first_class (일급 함수), F11_closure_capture (클로저)

---

## 1. Universal Concept (언어 무관 개념 정의)

**Higher-Order Function (HOF)**은 다음 중 하나 이상을 만족하는 함수입니다:
1. **함수를 인자로 받음**: `map(fn, list)` - fn은 함수
2. **함수를 반환함**: `makeAdder(n)` - 함수를 반환

HOF는 **함수형 프로그래밍의 핵심**이며, 코드의 재사용성과 추상화 수준을 높입니다.

### 1.1 Mental Model: Function Factories & Transformers

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Higher-Order Functions                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Function as INPUT (Transformer):                                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                         │
│  │  [1,2,3] │ -> │ map(fn) │ -> │ [2,4,6] │                         │
│  └─────────┘    └────┬────┘    └─────────┘                         │
│                      │                                              │
│                 fn = x => x * 2                                     │
│                                                                     │
│  Function as OUTPUT (Factory):                                      │
│  ┌───────────────┐    ┌─────────────────────┐                      │
│  │ makeAdder(5)  │ -> │ function(x) { x+5 } │                      │
│  └───────────────┘    └─────────────────────┘                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 The Big Three HOFs

모든 언어에서 가장 중요한 3가지 HOF:

| HOF | 목적 | 입력 → 출력 |
|-----|------|-------------|
| **map** | 변환 (Transform) | `[a,b,c]` → `[f(a),f(b),f(c)]` |
| **filter** | 필터링 (Select) | `[a,b,c]` → `[x where p(x)]` |
| **reduce** | 집계 (Aggregate) | `[a,b,c]` → `single value` |

```
map:    [1, 2, 3]  ---(x*2)--->  [2, 4, 6]
filter: [1, 2, 3]  ---(x>1)--->  [2, 3]
reduce: [1, 2, 3]  ---(sum)--->  6
```

### 1.3 First-Class Functions: The Prerequisite

HOF가 가능하려면 언어가 **First-Class Functions**를 지원해야 합니다:
- 변수에 할당 가능: `const fn = x => x + 1`
- 인자로 전달 가능: `map(fn, list)`
- 반환값으로 사용 가능: `return () => x`
- 자료구조에 저장 가능: `[fn1, fn2, fn3]`

### 1.4 Why HOFs Matter

```
Without HOF (Imperative):
result = []
for item in items:
    if condition(item):
        result.append(transform(item))

With HOF (Declarative):
result = items.filter(condition).map(transform)
```

| Benefit | Explanation |
|---------|-------------|
| **Readability** | 의도가 명확: "filter then map" |
| **Reusability** | 함수 조합으로 새 기능 생성 |
| **Testability** | 순수 함수는 테스트 용이 |
| **Parallelization** | 독립적 연산은 병렬화 가능 (Spark!) |
| **Immutability** | 원본 데이터 불변 유지 |

---

## 2. Semantic Comparison Matrix (의미론적 비교 매트릭스)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **Native HOFs** | Stream API | map/filter/reduce | Array methods | No built-in | N/A (set ops) | STL algorithms | map/filter/reduce |
| **Function Type** | `Function<T,R>` | `Callable` | `(x: T) => R` | `func(T) R` | N/A | `std::function` | `Callable` |
| **Lambda Syntax** | `x -> expr` | `lambda x: expr` | `x => expr` | `func(x) {}` | N/A | `[](x) {}` | `lambda x: expr` |
| **Currying** | No (manual) | No (functools) | Yes (closures) | No (manual) | N/A | No (manual) | No |
| **Partial Application** | No | `functools.partial` | `.bind()`, closures | closures | N/A | `std::bind` | No |
| **Function Composition** | No (manual) | No (manual) | No (manual) | No (manual) | N/A | No (manual) | `.pipe()` |
| **Lazy Evaluation** | Stream (lazy) | Generator (lazy) | No | No | N/A | ranges (C++20) | **YES (critical!)** |

### 2.2 Detailed Code Examples

---

#### Pattern 1: map/filter/reduce - The Holy Trinity

**Java (Stream API)**
```java
import java.util.List;
import java.util.stream.*;
import java.util.function.*;

public class HOFDemo {
    public static void main(String[] args) {
        List<Integer> numbers = List.of(1, 2, 3, 4, 5);

        // map: Transform each element
        List<Integer> doubled = numbers.stream()
            .map(x -> x * 2)
            .collect(Collectors.toList());
        // [2, 4, 6, 8, 10]

        // filter: Keep elements matching predicate
        List<Integer> evens = numbers.stream()
            .filter(x -> x % 2 == 0)
            .collect(Collectors.toList());
        // [2, 4]

        // reduce: Aggregate to single value
        int sum = numbers.stream()
            .reduce(0, (acc, x) -> acc + x);
        // 15

        // Method references (cleaner syntax)
        int sum2 = numbers.stream()
            .reduce(0, Integer::sum);

        // Chaining: filter → map → reduce
        int sumOfDoubledEvens = numbers.stream()
            .filter(x -> x % 2 == 0)  // [2, 4]
            .map(x -> x * 2)           // [4, 8]
            .reduce(0, Integer::sum);  // 12

        // flatMap: flatten nested structures
        List<List<Integer>> nested = List.of(
            List.of(1, 2), List.of(3, 4)
        );
        List<Integer> flattened = nested.stream()
            .flatMap(List::stream)
            .collect(Collectors.toList());
        // [1, 2, 3, 4]
    }
}
```

**Python**
```python
from functools import reduce
from typing import Callable, TypeVar, List

T = TypeVar('T')
R = TypeVar('R')

numbers = [1, 2, 3, 4, 5]

# map: Transform each element (returns iterator!)
doubled = list(map(lambda x: x * 2, numbers))
# [2, 4, 6, 8, 10]

# More Pythonic: List comprehension
doubled = [x * 2 for x in numbers]

# filter: Keep elements matching predicate
evens = list(filter(lambda x: x % 2 == 0, numbers))
# [2, 4]

# More Pythonic: List comprehension
evens = [x for x in numbers if x % 2 == 0]

# reduce: Aggregate to single value (must import!)
total = reduce(lambda acc, x: acc + x, numbers, 0)
# 15

# More Pythonic: built-in sum()
total = sum(numbers)

# Chaining with comprehensions (Pythonic way)
sum_of_doubled_evens = sum(x * 2 for x in numbers if x % 2 == 0)
# 12

# Custom HOF: Function that returns a function
def make_multiplier(n: int) -> Callable[[int], int]:
    return lambda x: x * n

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5))  # 10
print(triple(5))  # 15

# HOF that takes a function
def apply_twice(fn: Callable[[T], T], value: T) -> T:
    return fn(fn(value))

result = apply_twice(lambda x: x + 1, 5)  # 7

# Nested map: Transform nested structures
nested = [[1, 2], [3, 4]]
transformed = [list(map(lambda x: x * 2, inner)) for inner in nested]
# [[2, 4], [6, 8]]

# flatMap equivalent (flatten + map)
flattened = [x * 2 for inner in nested for x in inner]
# [2, 4, 6, 8]
```

**TypeScript**
```typescript
// Array built-in HOFs
const numbers: number[] = [1, 2, 3, 4, 5];

// map: Transform each element
const doubled: number[] = numbers.map(x => x * 2);
// [2, 4, 6, 8, 10]

// filter: Keep elements matching predicate
const evens: number[] = numbers.filter(x => x % 2 === 0);
// [2, 4]

// reduce: Aggregate to single value
const sum: number = numbers.reduce((acc, x) => acc + x, 0);
// 15

// Chaining (fluent API)
const sumOfDoubledEvens: number = numbers
    .filter(x => x % 2 === 0)  // [2, 4]
    .map(x => x * 2)           // [4, 8]
    .reduce((acc, x) => acc + x, 0);  // 12

// flatMap (ES2019)
const nested: number[][] = [[1, 2], [3, 4]];
const flattened: number[] = nested.flatMap(arr => arr.map(x => x * 2));
// [2, 4, 6, 8]

// Type-safe HOF definition
function map<T, R>(arr: T[], fn: (item: T) => R): R[] {
    return arr.map(fn);
}

function filter<T>(arr: T[], predicate: (item: T) => boolean): T[] {
    return arr.filter(predicate);
}

function reduce<T, R>(
    arr: T[],
    fn: (acc: R, item: T) => R,
    initial: R
): R {
    return arr.reduce(fn, initial);
}

// Function that returns a function (currying-like)
const makeAdder = (n: number) => (x: number): number => n + x;
const add5 = makeAdder(5);
console.log(add5(10));  // 15

// forEach: Side effects (NOT a transformation)
numbers.forEach(x => console.log(x));
// Returns undefined, used for side effects only

// find: First matching element
const firstEven: number | undefined = numbers.find(x => x % 2 === 0);
// 2

// some/every: Boolean aggregation
const hasEven: boolean = numbers.some(x => x % 2 === 0);   // true
const allPositive: boolean = numbers.every(x => x > 0);    // true
```

**Go**
```go
package main

import "fmt"

// Go has NO built-in HOFs - must implement manually!
// This is a core interview topic: "Implement map in Go"

// Generic map (Go 1.18+)
func Map[T any, R any](items []T, fn func(T) R) []R {
    result := make([]R, len(items))
    for i, item := range items {
        result[i] = fn(item)
    }
    return result
}

// Generic filter
func Filter[T any](items []T, predicate func(T) bool) []T {
    result := make([]T, 0)
    for _, item := range items {
        if predicate(item) {
            result = append(result, item)
        }
    }
    return result
}

// Generic reduce
func Reduce[T any, R any](items []T, initial R, fn func(R, T) R) R {
    result := initial
    for _, item := range items {
        result = fn(result, item)
    }
    return result
}

func main() {
    numbers := []int{1, 2, 3, 4, 5}

    // map
    doubled := Map(numbers, func(x int) int { return x * 2 })
    fmt.Println(doubled)  // [2 4 6 8 10]

    // filter
    evens := Filter(numbers, func(x int) bool { return x%2 == 0 })
    fmt.Println(evens)  // [2 4]

    // reduce
    sum := Reduce(numbers, 0, func(acc, x int) int { return acc + x })
    fmt.Println(sum)  // 15

    // Function that returns a function
    makeAdder := func(n int) func(int) int {
        return func(x int) int { return n + x }
    }
    add5 := makeAdder(5)
    fmt.Println(add5(10))  // 15

    // Passing function as parameter
    applyTwice := func(fn func(int) int, x int) int {
        return fn(fn(x))
    }
    result := applyTwice(func(x int) int { return x + 1 }, 5)
    fmt.Println(result)  // 7
}
```

**SQL** - No HOFs (Set-Based Operations Instead)
```sql
-- SQL is declarative and set-based, NOT functional
-- But we can achieve similar results:

-- "map": Transform columns (implicit for all rows)
SELECT
    id,
    price * 2 AS doubled_price,      -- "map" to double
    UPPER(name) AS upper_name        -- "map" to uppercase
FROM products;

-- "filter": WHERE clause
SELECT *
FROM products
WHERE price > 100;                   -- "filter" expensive items

-- "reduce": Aggregate functions
SELECT
    SUM(price) AS total,             -- "reduce" with sum
    AVG(price) AS average,           -- "reduce" with avg
    COUNT(*) AS count                -- "reduce" with count
FROM products;

-- Combined: filter → transform → aggregate
SELECT
    SUM(price * 2) AS doubled_total  -- filter+map+reduce
FROM products
WHERE category = 'Electronics';

-- GROUP BY: Multiple reduces
SELECT
    category,
    SUM(price) AS category_total,
    COUNT(*) AS item_count
FROM products
GROUP BY category;

-- Window functions (sophisticated "map" over partitions)
SELECT
    id,
    price,
    SUM(price) OVER (PARTITION BY category) AS category_total,
    price / SUM(price) OVER (PARTITION BY category) AS price_ratio
FROM products;
```

**C++ (STL Algorithms)**
```cpp
#include <algorithm>
#include <numeric>
#include <vector>
#include <functional>
#include <iostream>

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5};

    // transform (map equivalent)
    std::vector<int> doubled(numbers.size());
    std::transform(
        numbers.begin(), numbers.end(),
        doubled.begin(),
        [](int x) { return x * 2; }
    );
    // doubled = {2, 4, 6, 8, 10}

    // copy_if (filter equivalent)
    std::vector<int> evens;
    std::copy_if(
        numbers.begin(), numbers.end(),
        std::back_inserter(evens),
        [](int x) { return x % 2 == 0; }
    );
    // evens = {2, 4}

    // accumulate (reduce equivalent)
    int sum = std::accumulate(
        numbers.begin(), numbers.end(),
        0,
        [](int acc, int x) { return acc + x; }
    );
    // sum = 15

    // std::function for storing callable
    std::function<int(int)> doubler = [](int x) { return x * 2; };
    std::cout << doubler(5) << std::endl;  // 10

    // Function returning function
    auto makeAdder = [](int n) {
        return [n](int x) { return n + x; };
    };
    auto add5 = makeAdder(5);
    std::cout << add5(10) << std::endl;  // 15

    // C++20 Ranges (more composable)
    #include <ranges>

    auto result = numbers
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::views::transform([](int x) { return x * 2; });
    // Lazy evaluation! Only computed when iterated

    for (int x : result) {
        std::cout << x << " ";  // 4 8
    }

    return 0;
}
```

**Spark (CRITICAL for Palantir Interview!)**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, udf
from pyspark.sql.types import IntegerType

spark = SparkSession.builder.appName("HOF").getOrCreate()

# =====================================================
# CRITICAL: Spark transformations are LAZY!
# Nothing executes until an ACTION is called
# =====================================================

# RDD API (lower-level)
numbers_rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5])

# map: Transform each element (LAZY - no execution yet!)
doubled_rdd = numbers_rdd.map(lambda x: x * 2)

# filter: Keep elements matching predicate (LAZY)
evens_rdd = numbers_rdd.filter(lambda x: x % 2 == 0)

# reduce: Aggregate to single value (ACTION - triggers execution!)
total = numbers_rdd.reduce(lambda a, b: a + b)  # 15

# collect: Bring results to driver (ACTION)
doubled_list = doubled_rdd.collect()  # [2, 4, 6, 8, 10]

# flatMap: flatten nested structures
nested_rdd = spark.sparkContext.parallelize([[1, 2], [3, 4]])
flattened_rdd = nested_rdd.flatMap(lambda x: x)  # [1, 2, 3, 4]

# =====================================================
# DataFrame API (preferred for interview!)
# =====================================================

data = [("Alice", 30), ("Bob", 25), ("Charlie", 35)]
df = spark.createDataFrame(data, ["name", "age"])

# "map" via withColumn (LAZY)
df_with_doubled = df.withColumn("doubled_age", col("age") * 2)

# "filter" via filter/where (LAZY)
adults = df.filter(col("age") >= 30)

# "reduce" via aggregation (ACTION when result is needed)
from pyspark.sql.functions import sum as spark_sum, avg, count

aggregated = df.agg(
    spark_sum("age").alias("total_age"),
    avg("age").alias("avg_age"),
    count("*").alias("count")
)

# Chain of transformations (ALL LAZY!)
result = (df
    .filter(col("age") >= 25)           # filter
    .withColumn("age_band",             # map (conditional)
        when(col("age") < 30, "young")
        .otherwise("senior"))
    .groupBy("age_band")                # prepare for reduce
    .agg(count("*").alias("count"))     # reduce
)

# ACTION triggers entire chain execution
result.show()  # <-- Execution happens HERE

# =====================================================
# Higher-Order Functions in Spark SQL (Spark 2.4+)
# =====================================================

# Array columns with transform (map for arrays)
from pyspark.sql.functions import transform, filter as array_filter

df_arrays = spark.createDataFrame([([1, 2, 3],), ([4, 5, 6],)], ["nums"])

# transform: map over array elements
df_doubled = df_arrays.select(
    transform("nums", lambda x: x * 2).alias("doubled")
)
# [[2, 4, 6], [8, 10, 12]]

# filter: filter array elements
df_evens = df_arrays.select(
    array_filter("nums", lambda x: x % 2 == 0).alias("evens")
)
# [[2], [4, 6]]

# aggregate: reduce over array elements
from pyspark.sql.functions import aggregate

df_sum = df_arrays.select(
    aggregate("nums", 0, lambda acc, x: acc + x).alias("sum")
)
# [6, 15]

# =====================================================
# UDF: User-Defined Functions (Custom HOF)
# =====================================================

@udf(IntegerType())
def custom_transform(x):
    return x * x + 1

df_custom = df.withColumn("transformed", custom_transform(col("age")))
```

---

#### Pattern 2: Java Functional Interfaces

**Java (Function, BiFunction, Consumer, Supplier, Predicate)**
```java
import java.util.function.*;
import java.util.*;

public class FunctionalInterfaces {
    public static void main(String[] args) {
        // Function<T, R>: Takes T, returns R
        Function<String, Integer> strlen = s -> s.length();
        System.out.println(strlen.apply("hello"));  // 5

        // Composition with andThen
        Function<Integer, Integer> doubler = x -> x * 2;
        Function<String, Integer> strlenDoubled = strlen.andThen(doubler);
        System.out.println(strlenDoubled.apply("hello"));  // 10

        // Composition with compose (reverse order)
        Function<Integer, String> intToStr = x -> "Number: " + x;
        Function<Integer, String> composed = intToStr.compose(doubler);
        System.out.println(composed.apply(5));  // "Number: 10"

        // BiFunction<T, U, R>: Takes T and U, returns R
        BiFunction<Integer, Integer, Integer> add = (a, b) -> a + b;
        System.out.println(add.apply(3, 5));  // 8

        // Consumer<T>: Takes T, returns void (side effects)
        Consumer<String> printer = s -> System.out.println(s);
        printer.accept("Hello");  // prints "Hello"

        // Chaining consumers
        Consumer<String> logger = s -> System.out.println("[LOG] " + s);
        Consumer<String> both = printer.andThen(logger);
        both.accept("Message");  // prints both

        // Supplier<T>: Takes nothing, returns T
        Supplier<Double> randomSupplier = () -> Math.random();
        System.out.println(randomSupplier.get());  // random number

        // Predicate<T>: Takes T, returns boolean
        Predicate<Integer> isPositive = x -> x > 0;
        Predicate<Integer> isEven = x -> x % 2 == 0;

        // Predicate composition
        Predicate<Integer> isPositiveAndEven = isPositive.and(isEven);
        Predicate<Integer> isPositiveOrEven = isPositive.or(isEven);
        Predicate<Integer> isNotPositive = isPositive.negate();

        System.out.println(isPositiveAndEven.test(4));   // true
        System.out.println(isPositiveAndEven.test(-2));  // false
        System.out.println(isPositiveOrEven.test(-2));   // true

        // UnaryOperator<T>: Function<T, T> shorthand
        UnaryOperator<Integer> increment = x -> x + 1;
        System.out.println(increment.apply(5));  // 6

        // BinaryOperator<T>: BiFunction<T, T, T> shorthand
        BinaryOperator<Integer> max = (a, b) -> a > b ? a : b;
        System.out.println(max.apply(3, 7));  // 7

        // Using with streams
        List<String> names = Arrays.asList("Alice", "Bob", "Charlie");

        names.stream()
            .map(strlen)                    // Function
            .filter(isPositive)             // Predicate
            .forEach(printer);              // Consumer
    }

    // HOF: Function that returns a Function
    public static Function<Integer, Integer> makeAdder(int n) {
        return x -> x + n;
    }

    // HOF: Function that takes a Function
    public static <T, R> List<R> myMap(List<T> list, Function<T, R> fn) {
        List<R> result = new ArrayList<>();
        for (T item : list) {
            result.add(fn.apply(item));
        }
        return result;
    }
}
```

---

#### Pattern 3: Python functools (partial, reduce, lru_cache)

**Python (functools module)**
```python
from functools import partial, reduce, lru_cache, wraps
from typing import Callable, TypeVar, Any
import time

# ==================================================
# partial: Pre-fill some arguments
# ==================================================

def power(base: int, exponent: int) -> int:
    return base ** exponent

# Create specialized functions
square = partial(power, exponent=2)
cube = partial(power, exponent=3)

print(square(5))  # 25
print(cube(3))    # 27

# Partial with positional args
def greet(greeting: str, name: str, punctuation: str = "!") -> str:
    return f"{greeting}, {name}{punctuation}"

say_hello = partial(greet, "Hello")
print(say_hello("Alice"))  # "Hello, Alice!"

formal_hello = partial(greet, "Hello", punctuation=".")
print(formal_hello("Dr. Smith"))  # "Hello, Dr. Smith."

# ==================================================
# reduce: Left fold with optional initial value
# ==================================================

numbers = [1, 2, 3, 4, 5]

# Sum (prefer built-in sum())
total = reduce(lambda acc, x: acc + x, numbers)  # 15

# Product
product = reduce(lambda acc, x: acc * x, numbers)  # 120

# With initial value
total_with_init = reduce(lambda acc, x: acc + x, numbers, 100)  # 115

# Flatten nested list
nested = [[1, 2], [3, 4], [5]]
flattened = reduce(lambda acc, x: acc + x, nested, [])  # [1, 2, 3, 4, 5]

# Max (prefer built-in max())
maximum = reduce(lambda a, b: a if a > b else b, numbers)  # 5

# Build dictionary from list of tuples
pairs = [("a", 1), ("b", 2), ("c", 3)]
dictionary = reduce(
    lambda d, kv: {**d, kv[0]: kv[1]},
    pairs,
    {}
)  # {"a": 1, "b": 2, "c": 3}

# ==================================================
# lru_cache: Memoization decorator (HOF!)
# ==================================================

@lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# First call: computes recursively
print(fibonacci(100))  # Instant! Without cache would be exponential

# Check cache stats
print(fibonacci.cache_info())
# CacheInfo(hits=98, misses=101, maxsize=128, currsize=101)

# Clear cache
fibonacci.cache_clear()

# ==================================================
# Creating your own HOF decorator
# ==================================================

T = TypeVar('T')

def retry(max_attempts: int = 3, delay: float = 1.0):
    """HOF: Returns a decorator that retries failed functions"""
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)  # Preserve function metadata
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    time.sleep(delay)
            raise last_error
        return wrapper
    return decorator

@retry(max_attempts=3, delay=0.5)
def unstable_api_call(url: str) -> dict:
    # Simulated unreliable function
    import random
    if random.random() < 0.7:
        raise ConnectionError("Network issue")
    return {"status": "ok"}

# ==================================================
# Composing functions
# ==================================================

def compose(*functions):
    """Compose multiple functions right-to-left"""
    def composed(x):
        result = x
        for fn in reversed(functions):
            result = fn(result)
        return result
    return composed

# Usage
add_one = lambda x: x + 1
double = lambda x: x * 2
square = lambda x: x ** 2

# Reads: square(double(add_one(x)))
pipeline = compose(square, double, add_one)
print(pipeline(3))  # (3+1)*2)^2 = 64

# Alternative: pipe (left-to-right composition)
def pipe(*functions):
    """Compose multiple functions left-to-right"""
    return lambda x: reduce(lambda acc, fn: fn(acc), functions, x)

# Reads: add_one → double → square
pipeline2 = pipe(add_one, double, square)
print(pipeline2(3))  # ((3+1)*2)^2 = 64
```

---

#### Pattern 4: TypeScript Currying and Partial Application

**TypeScript (Currying, Partial Application, Composition)**
```typescript
// ==================================================
// Currying: Transform f(a, b, c) into f(a)(b)(c)
// ==================================================

// Non-curried function
function add(a: number, b: number, c: number): number {
    return a + b + c;
}

// Manually curried
function addCurried(a: number): (b: number) => (c: number) => number {
    return (b: number) => (c: number) => a + b + c;
}

console.log(addCurried(1)(2)(3));  // 6

// Arrow function version (cleaner)
const addCurriedArrow = (a: number) => (b: number) => (c: number) =>
    a + b + c;

// Partial application via currying
const add10 = addCurriedArrow(10);      // (b) => (c) => 10 + b + c
const add10and20 = add10(20);           // (c) => 10 + 20 + c
console.log(add10and20(30));            // 60

// ==================================================
// Generic curry function
// ==================================================

type Curry<P extends any[], R> =
    P extends [infer H, ...infer T]
        ? (arg: H) => Curry<T, R>
        : R;

function curry<P extends any[], R>(
    fn: (...args: P) => R
): Curry<P, R> {
    return function curried(...args: any[]): any {
        if (args.length >= fn.length) {
            return fn(...args as P);
        }
        return (...more: any[]) => curried(...args, ...more);
    } as Curry<P, R>;
}

// Usage
const curriedAdd = curry(add);
console.log(curriedAdd(1)(2)(3));  // 6

// Partial application
const addTen = curriedAdd(10);
console.log(addTen(20)(30));  // 60

// ==================================================
// Partial Application with bind
// ==================================================

function multiply(a: number, b: number, c: number): number {
    return a * b * c;
}

// Using bind for partial application
const multiplyBy2 = multiply.bind(null, 2);
console.log(multiplyBy2(3, 4));  // 24

const multiplyBy2And3 = multiply.bind(null, 2, 3);
console.log(multiplyBy2And3(4));  // 24

// ==================================================
// Function Composition
// ==================================================

// Type-safe compose (right to left)
function compose<A, B, C>(
    f: (b: B) => C,
    g: (a: A) => B
): (a: A) => C {
    return (a: A) => f(g(a));
}

// Variadic compose
type Fn = (x: any) => any;

function composeMany<R>(...fns: Fn[]): (x: any) => R {
    return (x: any) =>
        fns.reduceRight((acc, fn) => fn(acc), x);
}

// pipe (left to right - more readable)
function pipe<R>(...fns: Fn[]): (x: any) => R {
    return (x: any) =>
        fns.reduce((acc, fn) => fn(acc), x);
}

// Usage
const addOne = (x: number): number => x + 1;
const double = (x: number): number => x * 2;
const square = (x: number): number => x ** 2;
const toString = (x: number): string => `Result: ${x}`;

const pipeline = pipe<string>(
    addOne,   // 3 + 1 = 4
    double,   // 4 * 2 = 8
    square,   // 8^2 = 64
    toString  // "Result: 64"
);

console.log(pipeline(3));  // "Result: 64"

// ==================================================
// Point-free style (tacit programming)
// ==================================================

const numbers = [1, 2, 3, 4, 5];

// Point-free: functions without explicit arguments
const isEven = (x: number): boolean => x % 2 === 0;
const doubleIt = (x: number): number => x * 2;

// Instead of: numbers.filter(x => isEven(x))
const evens = numbers.filter(isEven);       // Point-free
const doubled = numbers.map(doubleIt);      // Point-free

// ==================================================
// Real-world example: API request handler
// ==================================================

type RequestConfig = {
    baseUrl: string;
    headers: Record<string, string>;
};

type Endpoint = {
    path: string;
    method: 'GET' | 'POST';
};

// Curried API client factory
const createApiClient = (config: RequestConfig) =>
    (endpoint: Endpoint) =>
        async <T>(body?: unknown): Promise<T> => {
            const url = `${config.baseUrl}${endpoint.path}`;
            const response = await fetch(url, {
                method: endpoint.method,
                headers: config.headers,
                body: body ? JSON.stringify(body) : undefined,
            });
            return response.json();
        };

// Usage
const apiClient = createApiClient({
    baseUrl: 'https://api.example.com',
    headers: { 'Authorization': 'Bearer token' }
});

const getUsers = apiClient({ path: '/users', method: 'GET' });
const createUser = apiClient({ path: '/users', method: 'POST' });

// Later: getUsers<User[]>() or createUser<User>({ name: 'Alice' })
```

---

#### Pattern 5: Stream API - Intermediate vs Terminal Operations (INTERVIEW CRITICAL)

**Java (Lazy Evaluation in Streams)**
```java
import java.util.stream.*;
import java.util.*;

public class StreamOperations {
    public static void main(String[] args) {
        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

        // ==================================================
        // INTERMEDIATE operations: Return Stream, LAZY
        // ==================================================

        Stream<Integer> stream = numbers.stream()
            .filter(x -> {
                System.out.println("Filtering: " + x);
                return x % 2 == 0;
            })
            .map(x -> {
                System.out.println("Mapping: " + x);
                return x * 2;
            });

        // Nothing printed yet! Operations are LAZY
        System.out.println("Stream created, but nothing executed yet");

        // ==================================================
        // TERMINAL operations: Return non-Stream, TRIGGER execution
        // ==================================================

        List<Integer> result = stream.collect(Collectors.toList());
        // NOW it executes! Output shows interleaved filter/map
        // Filtering: 1
        // Filtering: 2
        // Mapping: 2
        // Filtering: 3
        // ...

        // ==================================================
        // Intermediate Operations (return Stream<T>)
        // ==================================================

        numbers.stream()
            .filter(x -> x > 0)           // Predicate<T>
            .map(x -> x * 2)              // Function<T, R>
            .flatMap(x -> Stream.of(x, x))// Function<T, Stream<R>>
            .distinct()                    // Remove duplicates
            .sorted()                      // Natural order
            .sorted(Comparator.reverseOrder())  // Custom order
            .peek(x -> System.out.println(x))   // Debug (side effect)
            .limit(5)                      // Take first 5
            .skip(2)                       // Skip first 2
            .takeWhile(x -> x < 10)        // Java 9+
            .dropWhile(x -> x < 5);        // Java 9+

        // ==================================================
        // Terminal Operations (trigger execution, return result)
        // ==================================================

        // Collecting
        List<Integer> list = numbers.stream().collect(Collectors.toList());
        Set<Integer> set = numbers.stream().collect(Collectors.toSet());
        Map<Integer, String> map = numbers.stream()
            .collect(Collectors.toMap(x -> x, x -> "v" + x));

        // Reducing
        int sum = numbers.stream().reduce(0, Integer::sum);
        Optional<Integer> max = numbers.stream().max(Integer::compareTo);
        Optional<Integer> min = numbers.stream().min(Integer::compareTo);
        long count = numbers.stream().count();

        // Matching
        boolean anyMatch = numbers.stream().anyMatch(x -> x > 5);
        boolean allMatch = numbers.stream().allMatch(x -> x > 0);
        boolean noneMatch = numbers.stream().noneMatch(x -> x < 0);

        // Finding
        Optional<Integer> first = numbers.stream().findFirst();
        Optional<Integer> any = numbers.stream().findAny();

        // Iteration
        numbers.stream().forEach(System.out::println);

        // ==================================================
        // CRITICAL: Stream can only be consumed ONCE!
        // ==================================================

        Stream<Integer> singleUse = numbers.stream();
        singleUse.forEach(System.out::println);
        // singleUse.forEach(System.out::println);  // IllegalStateException!

        // ==================================================
        // Short-circuiting operations (optimization)
        // ==================================================

        // findFirst/findAny: Stops as soon as match found
        Optional<Integer> found = numbers.stream()
            .filter(x -> x > 5)
            .findFirst();  // Doesn't process all elements!

        // limit: Stops after N elements
        List<Integer> firstThree = numbers.stream()
            .limit(3)
            .collect(Collectors.toList());

        // anyMatch: Stops when true found
        boolean hasLarge = numbers.stream()
            .anyMatch(x -> x > 5);  // Stops at 6
    }
}
```

---

#### Pattern 6: map vs flatMap (INTERVIEW FAVORITE)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    map vs flatMap                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  map:     [1, 2, 3] → map(x → [x, x]) → [[1,1], [2,2], [3,3]]      │
│                       (nested result)                               │
│                                                                     │
│  flatMap: [1, 2, 3] → flatMap(x → [x, x]) → [1, 1, 2, 2, 3, 3]     │
│                       (flattened result)                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**All Languages Comparison**
```java
// Java
List<List<Integer>> nested = Arrays.asList(
    Arrays.asList(1, 2), Arrays.asList(3, 4)
);

// map: [[1,2], [3,4]] → [Stream([1,2]), Stream([3,4])]
Stream<Stream<Integer>> mapped = nested.stream()
    .map(List::stream);

// flatMap: [[1,2], [3,4]] → [1, 2, 3, 4]
List<Integer> flattened = nested.stream()
    .flatMap(List::stream)
    .collect(Collectors.toList());
```

```python
# Python
nested = [[1, 2], [3, 4]]

# map: Result is iterator of lists
mapped = list(map(lambda x: [i * 2 for i in x], nested))
# [[2, 4], [6, 8]]

# flatMap equivalent (list comprehension)
flattened = [i * 2 for sublist in nested for i in sublist]
# [2, 4, 6, 8]

# Using itertools.chain
from itertools import chain
flattened = list(chain.from_iterable(
    map(lambda x: [i * 2 for i in x], nested)
))
```

```typescript
// TypeScript
const nested: number[][] = [[1, 2], [3, 4]];

// map: [[1,2], [3,4]] → [[2,4], [6,8]]
const mapped: number[][] = nested.map(arr => arr.map(x => x * 2));

// flatMap: [[1,2], [3,4]] → [2, 4, 6, 8]
const flattened: number[] = nested.flatMap(arr => arr.map(x => x * 2));
```

```python
# Spark (CRITICAL!)
rdd = spark.sparkContext.parallelize([[1, 2], [3, 4]])

# map: Each element transformed, structure preserved
mapped = rdd.map(lambda x: [i * 2 for i in x])
# [[2, 4], [6, 8]]

# flatMap: Transform + flatten
flattened = rdd.flatMap(lambda x: [i * 2 for i in x])
# [2, 4, 6, 8]

# Common use case: Split lines into words
lines = spark.sparkContext.parallelize([
    "hello world",
    "foo bar baz"
])

# map would give: [["hello", "world"], ["foo", "bar", "baz"]]
# flatMap gives: ["hello", "world", "foo", "bar", "baz"]
words = lines.flatMap(lambda line: line.split(" "))
```

---

### 2.3 Common Pitfalls by Language

#### Java Pitfalls
```java
// 1. Reusing consumed stream
Stream<Integer> stream = numbers.stream();
stream.forEach(System.out::println);
// stream.count();  // IllegalStateException!

// 2. Side effects in map (anti-pattern)
List<Integer> results = new ArrayList<>();
numbers.stream()
    .map(x -> {
        results.add(x);  // WRONG: Side effect!
        return x * 2;
    })
    .collect(Collectors.toList());

// 3. Modifying source during stream
// numbers.stream().forEach(x -> numbers.remove(x));  // ConcurrentModificationException

// 4. Confusing intermediate vs terminal
numbers.stream()
    .filter(x -> x > 0);  // Returns Stream, nothing happens!
// Need terminal operation to execute
```

#### Python Pitfalls
```python
# 1. map/filter return iterators, not lists
result = map(lambda x: x * 2, [1, 2, 3])
# result is <map object>, not [2, 4, 6]
# Need: list(result) or [*result]

# 2. Iterator exhaustion
mapped = map(lambda x: x * 2, [1, 2, 3])
list(mapped)  # [2, 4, 6]
list(mapped)  # [] - exhausted!

# 3. Lambda limitations (single expression only)
# fn = lambda x:
#     if x > 0:
#         return x * 2
#     else:
#         return 0
# SyntaxError! Use ternary or def instead
fn = lambda x: x * 2 if x > 0 else 0

# 4. reduce not built-in (must import)
# sum = reduce(lambda a, b: a + b, numbers)  # NameError
from functools import reduce
total = reduce(lambda a, b: a + b, numbers)
```

#### TypeScript/JavaScript Pitfalls
```typescript
// 1. forEach returns undefined (can't chain)
const result = [1, 2, 3]
    .forEach(x => console.log(x))
    .map(x => x * 2);  // Error: forEach returns undefined!

// 2. reduce without initial value
const arr: number[] = [];
// const sum = arr.reduce((a, b) => a + b);  // TypeError on empty!
const sum = arr.reduce((a, b) => a + b, 0);  // Safe with initial value

// 3. map/filter don't modify original
const nums = [1, 2, 3];
nums.map(x => x * 2);  // Returns [2, 4, 6]
console.log(nums);     // Still [1, 2, 3]

// 4. Type inference issues with reduce
interface Item { price: number; }
const items: Item[] = [{ price: 10 }, { price: 20 }];

// Error: Object is of type 'unknown'
// const total = items.reduce((acc, item) => acc + item.price);

// Fix: Provide type for accumulator
const total = items.reduce((acc: number, item) => acc + item.price, 0);
```

#### Go Pitfalls
```go
// 1. No built-in HOFs - must implement everything
// numbers.map(func...)  // Doesn't exist!

// 2. Generic constraints (Go 1.18+)
// Before generics: Type-specific implementations needed
func MapInt(items []int, fn func(int) int) []int { ... }
func MapString(items []string, fn func(string) string) []string { ... }

// 3. No method chaining (by design)
// Go philosophy: explicit loops are clearer
```

#### Spark Pitfalls (CRITICAL FOR INTERVIEW)
```python
# 1. Forgetting laziness - nothing happens without action!
rdd = numbers_rdd.filter(lambda x: x > 0).map(lambda x: x * 2)
# No computation yet!
result = rdd.collect()  # NOW it executes

# 2. Collecting large datasets to driver
# WRONG: Can cause OOM
# for item in large_rdd.collect():  # Loads ALL data to driver!
#     process(item)

# CORRECT: Keep processing distributed
large_rdd.foreach(lambda x: process(x))  # Runs on workers

# 3. Closure serialization issues
external_var = 100

# This variable is serialized and sent to all workers
rdd.map(lambda x: x + external_var)  # Works but be careful!

# Problem with mutable state:
counter = 0
rdd.foreach(lambda x: counter += x)  # counter stays 0 on driver!
# Use Accumulator instead

# 4. Multiple actions trigger re-computation
rdd = spark.sparkContext.parallelize([1, 2, 3]).map(lambda x: x * 2)
rdd.count()    # Computes transformation
rdd.collect()  # Computes AGAIN!
# Use .cache() or .persist() to avoid
rdd.cache()
```

---

## 3. Design Philosophy Links (공식 문서 출처)

### Official Documentation

| Language | HOF Documentation |
|----------|-------------------|
| **Java** | [Stream API](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html) |
| **Java** | [Functional Interfaces](https://docs.oracle.com/javase/8/docs/api/java/util/function/package-summary.html) |
| **Python** | [functools module](https://docs.python.org/3/library/functools.html) |
| **Python** | [Built-in Functions (map, filter)](https://docs.python.org/3/library/functions.html) |
| **TypeScript** | [Array Methods](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array) |
| **TypeScript** | [Functions Handbook](https://www.typescriptlang.org/docs/handbook/2/functions.html) |
| **Go** | [First-Class Functions](https://go.dev/tour/moretypes/24) |
| **C++** | [Algorithms Library](https://en.cppreference.com/w/cpp/algorithm) |
| **C++** | [std::function](https://en.cppreference.com/w/cpp/utility/functional/function) |
| **Spark** | [RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html) |
| **Spark** | [SQL Functions](https://spark.apache.org/docs/latest/sql-ref-functions-builtin.html) |

### Design Philosophy Quotes

> **Java**: "Streams are designed to be lazy and only process data as needed."
> — Java Stream Documentation

> **Python**: "Prefer list comprehensions over map/filter for clarity."
> — Python Style Guide

> **Spark**: "Transformations are lazy; nothing is computed until an action is called."
> — Spark Programming Guide

---

## 4. Palantir Context Hint (팔란티어 맥락 힌트)

### 4.1 Spark Transformation Laziness (CRITICAL)

```python
# Palantir heavily uses Spark for data processing
# Understanding lazy evaluation is ESSENTIAL

# This is the most common interview question pattern:
df = spark.read.parquet("huge_dataset.parquet")

# TRANSFORMATION CHAIN (all lazy - no execution!)
result = (df
    .filter(col("status") == "active")      # lazy
    .withColumn("score", col("x") * 2)      # lazy
    .groupBy("category")                     # lazy
    .agg(sum("score").alias("total"))       # lazy
    .orderBy(col("total").desc())           # lazy
)

# ACTION (triggers execution of entire chain)
result.show()  # <-- This is where Spark actually works!

# Interview Question: "When does Spark start processing?"
# Answer: Only when an ACTION is called (show, collect, count, write)
```

### 4.2 TypeScript OSDK Patterns

```typescript
// Foundry OSDK uses functional patterns extensively
import { Objects } from "@foundry/ontology-api";

// Chaining methods on object collections (HOF pattern)
const results = await Objects.search(Flight)
    .filter(flight => flight.status === "active")           // filter HOF
    .orderBy(flight => flight.departureTime)                // sort HOF
    .pageSize(100)
    .execute();

// Processing with Array methods
const processedFlights = results.data
    .map(flight => ({                                       // map HOF
        id: flight.rid,
        route: `${flight.origin} → ${flight.destination}`
    }))
    .filter(f => f.route.includes("JFK"));                  // filter HOF

// Aggregation pattern
const totalDelay = results.data
    .map(f => f.delay || 0)
    .reduce((sum, delay) => sum + delay, 0);                // reduce HOF
```

### 4.3 Interview Questions (HIGHEST PRIORITY)

1. **"Implement reduce using only recursion"**
```typescript
function reduceRecursive<T, R>(
    arr: T[],
    fn: (acc: R, item: T) => R,
    initial: R
): R {
    if (arr.length === 0) return initial;
    const [head, ...tail] = arr;
    return reduceRecursive(tail, fn, fn(initial, head));
}

// Tail-recursive version (optimizable)
function reduceTailRec<T, R>(
    arr: T[],
    fn: (acc: R, item: T) => R,
    acc: R,
    index: number = 0
): R {
    if (index >= arr.length) return acc;
    return reduceTailRec(arr, fn, fn(acc, arr[index]), index + 1);
}
```

2. **"Explain Spark transformation laziness"**
```
- Transformations (map, filter, groupBy) are LAZY
- They build a DAG (Directed Acyclic Graph) of operations
- Nothing executes until an ACTION (collect, count, show, write)
- Benefits:
  * Catalyst optimizer can optimize the entire pipeline
  * Only necessary data is processed
  * Operations can be fused together
```

3. **"What's the difference between map and flatMap?"**
```
map:     Transforms each element 1-to-1
         [1, 2, 3] -> map(x => [x, x]) -> [[1,1], [2,2], [3,3]]

flatMap: Transforms and flattens
         [1, 2, 3] -> flatMap(x => [x, x]) -> [1, 1, 2, 2, 3, 3]

Use flatMap when:
- Splitting strings into words: line.flatMap(split)
- Expanding one-to-many: user.flatMap(getOrders)
- Filtering + transforming: Option.flatMap for nullable chains
```

4. **"Implement curry function in TypeScript"**
```typescript
function curry<F extends (...args: any[]) => any>(fn: F) {
    return function curried(...args: any[]): any {
        if (args.length >= fn.length) {
            return fn(...args);
        }
        return (...moreArgs: any[]) => curried(...args, ...moreArgs);
    };
}
```

5. **"Java Stream: intermediate vs terminal operations"**
```
INTERMEDIATE (return Stream, lazy):
- filter, map, flatMap, distinct, sorted, peek, limit, skip

TERMINAL (return non-Stream, trigger execution):
- forEach, collect, reduce, count, min, max, anyMatch, allMatch, findFirst

Key points:
- Streams are single-use (IllegalStateException if reused)
- Short-circuit operations (findFirst, limit, anyMatch) optimize execution
- Parallel streams can improve performance but watch for ordering
```

### 4.4 Common Interview Patterns

```python
# Pattern 1: Implement map using reduce
def map_via_reduce(fn, items):
    return reduce(lambda acc, x: acc + [fn(x)], items, [])

# Pattern 2: Implement filter using reduce
def filter_via_reduce(pred, items):
    return reduce(lambda acc, x: acc + [x] if pred(x) else acc, items, [])

# Pattern 3: Implement flatMap using reduce
def flatmap_via_reduce(fn, items):
    return reduce(lambda acc, x: acc + fn(x), items, [])

# Pattern 4: Compose multiple functions
def compose(*fns):
    return reduce(lambda f, g: lambda x: f(g(x)), fns, lambda x: x)

# Pattern 5: Pipe (left-to-right composition)
def pipe(*fns):
    return lambda x: reduce(lambda acc, fn: fn(acc), fns, x)
```

---

## 5. Cross-References (관련 개념)

### Related Knowledge Bases

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F40** | Function Declarations | First-class functions prerequisite |
| **F44** | Closures | HOFs often create closures |
| **F11** | Closure Capture | Understanding variable capture in HOFs |
| **F31** | Loops & Iteration | Imperative vs functional iteration |
| **F50** | Data Structures | Collections that HOFs operate on |
| **F32** | Exception Handling | Error handling in functional chains |
| **00d** | Async Basics | Async HOFs (Promise.then, etc.) |

### Algorithm Patterns Using HOFs

| Pattern | HOF | Example |
|---------|-----|---------|
| Transform | map | Double all numbers |
| Filter | filter | Get even numbers |
| Aggregate | reduce | Sum all numbers |
| Flatten | flatMap | Split lines into words |
| Group | groupBy (Java) | Group by category |
| Sort | sorted/sort | Order by property |
| Take | limit/take | First N elements |
| Skip | skip/drop | Skip first N elements |

### HOF Evolution Timeline

| Year | Language | Feature |
|------|----------|---------|
| 1958 | Lisp | First HOF support |
| 1995 | JavaScript | First-class functions |
| 2009 | Scala | Comprehensive FP |
| 2014 | Java 8 | Stream API, lambdas |
| 2015 | ES6 | Arrow functions, Array methods |
| 2018 | Go 1.18 | Generics enable type-safe HOFs |
| 2020 | C++20 | Ranges library |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────┐
│                 HIGHER-ORDER FUNCTIONS CHEAT SHEET                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ THE BIG THREE:                                                      │
│   map(fn):    [a,b,c] → [fn(a), fn(b), fn(c)]    Transform         │
│   filter(p):  [a,b,c] → [x where p(x)==true]     Select            │
│   reduce(fn,init): [a,b,c] → single value        Aggregate         │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ LANGUAGE SYNTAX:                                                    │
│   Java:       list.stream().map(x -> x*2).collect(toList())        │
│   Python:     list(map(lambda x: x*2, items))                      │
│   TypeScript: arr.map(x => x * 2)                                  │
│   Go:         Map(items, func(x int) int { return x*2 })           │
│   Spark:      rdd.map(lambda x: x*2)                               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ LAZY vs EAGER:                                                      │
│   LAZY:  Java Stream, Spark, Python generators                     │
│   EAGER: Python list(map(...)), TypeScript Array methods           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ map vs flatMap:                                                     │
│   map:     [[1,2], [3,4]] → map(double)  → [[2,4], [6,8]]         │
│   flatMap: [[1,2], [3,4]] → flatMap(id) → [1,2,3,4]               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ INTERVIEW CRITICAL (SPARK):                                         │
│   ⚠️  Transformations are LAZY until ACTION is called              │
│   ⚠️  Actions: collect(), count(), show(), write()                 │
│   ⚠️  Never collect() large datasets to driver!                    │
│   ⚠️  Use cache() to avoid recomputation                           │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ JAVA STREAM OPERATIONS:                                             │
│   Intermediate (lazy):  filter, map, flatMap, sorted, distinct     │
│   Terminal (trigger):   collect, reduce, forEach, count, findFirst │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
