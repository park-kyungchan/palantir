# F31: Loops & Iteration (반복문과 순회)

> **Concept ID**: F31
> **Category**: Control Flow - Iteration
> **Difficulty**: Beginner → Intermediate
> **Interview Frequency**: ★★★★★ (Every coding interview)

---

## Section 1: Universal Concept (보편적 개념)

### 1.1 What is Iteration?

**Iteration** is the process of repeatedly executing a block of code until a condition is met. It's one of the most fundamental concepts in programming—alongside sequence and selection, it forms the backbone of all algorithms.

```
┌─────────────────────────────────────────────────────────────┐
│                    Iteration Mental Model                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   START → [Initialize] → [Check Condition] ──No──→ END     │
│                               │                             │
│                              Yes                            │
│                               ↓                             │
│                         [Execute Body]                      │
│                               ↓                             │
│                         [Update State]                      │
│                               │                             │
│                               └──────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Iteration vs Recursion

| Aspect | Iteration | Recursion |
|--------|-----------|-----------|
| **Memory** | O(1) stack space | O(n) stack space |
| **Control** | Explicit loop constructs | Function calls itself |
| **Readability** | Often clearer for linear tasks | Natural for tree/graph traversal |
| **Performance** | Generally faster (no call overhead) | May have overhead unless tail-optimized |
| **Termination** | Loop condition becomes false | Base case reached |
| **State** | Mutable variables | Function parameters |

**Interview Insight**: When asked "Can you do this iteratively?", the interviewer wants to see you understand the trade-offs and can convert between the two paradigms.

### 1.3 Loop Invariants

A **loop invariant** is a condition that:
1. Is true before the loop starts
2. Remains true after each iteration
3. Helps prove the loop's correctness

```python
# Example: Finding sum of array
# Loop invariant: total = sum of arr[0:i]
def array_sum(arr):
    total = 0  # Invariant: total = sum of arr[0:0] = 0 ✓
    for i in range(len(arr)):
        total += arr[i]  # After: total = sum of arr[0:i+1] ✓
    return total  # Invariant guarantees: total = sum of arr[0:n]
```

### 1.4 Why Loops Matter in Interviews

1. **Foundational**: Every algorithm uses loops
2. **Edge Cases**: Off-by-one errors are common bugs
3. **Optimization**: Loop optimization shows algorithmic thinking
4. **Language Mastery**: Different loop idioms across languages
5. **Complexity Analysis**: Loop structure determines time complexity

---

## Section 2: Semantic Comparison Matrix (의미론적 비교 매트릭스)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Traditional for** | `for(;;)` | N/A | `for(;;)` | `for;;{}` | N/A | `for(;;)` | N/A |
| **Range-based** | `for-each` | `for x in` | `for...of` | `for range` | N/A | `for(:)` | `.foreach()` |
| **Index iteration** | `for(i=0;...)` | `range()` | `for(i=0;...)` | `for i:=0;...` | N/A | `for(i=0;...)` | N/A |
| **while** | `while()` | `while:` | `while()` | `for{}` | N/A | `while()` | N/A |
| **do-while** | `do{}while()` | N/A | `do{}while()` | N/A | N/A | `do{}while()` | N/A |
| **foreach/map** | `forEach()` | `map()` | `forEach()` | N/A | N/A | `std::for_each` | `.map()` |
| **Iterator** | `Iterator<T>` | `__iter__` | `Symbol.iterator` | N/A | cursor | `begin()/end()` | N/A |
| **Generator** | N/A | `yield` | `function*` | N/A | N/A | coroutines | N/A |
| **for-else** | N/A | ✓ | N/A | N/A | N/A | N/A | N/A |
| **Labeled break** | ✓ | N/A | ✓ | ✓ | N/A | `goto` | N/A |

### 2.2 Detailed Code Examples by Pattern

---

#### Pattern 1: Index-Based Iteration

**Java**
```java
// Traditional for loop
int[] arr = {1, 2, 3, 4, 5};
for (int i = 0; i < arr.length; i++) {
    System.out.println(arr[i]);
}

// With step
for (int i = 0; i < 10; i += 2) {
    System.out.println(i);  // 0, 2, 4, 6, 8
}

// Reverse iteration
for (int i = arr.length - 1; i >= 0; i--) {
    System.out.println(arr[i]);
}
```

**Python**
```python
# Python has NO traditional for loop - use range()
arr = [1, 2, 3, 4, 5]
for i in range(len(arr)):
    print(arr[i])

# With step
for i in range(0, 10, 2):
    print(i)  # 0, 2, 4, 6, 8

# Reverse iteration
for i in range(len(arr) - 1, -1, -1):
    print(arr[i])

# Pythonic reverse
for x in reversed(arr):
    print(x)

# With index (enumerate is preferred!)
for i, val in enumerate(arr):
    print(f"Index {i}: {val}")
```

**TypeScript**
```typescript
// Traditional for loop
const arr: number[] = [1, 2, 3, 4, 5];
for (let i = 0; i < arr.length; i++) {
    console.log(arr[i]);
}

// CAUTION: Use 'let' not 'var' for block scoping
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);  // Prints 3, 3, 3 (closure bug!)
}

for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);  // Prints 0, 1, 2 (correct)
}
```

**Go**
```go
// Go only has 'for' - no 'while' keyword!
arr := []int{1, 2, 3, 4, 5}
for i := 0; i < len(arr); i++ {
    fmt.Println(arr[i])
}

// Reverse
for i := len(arr) - 1; i >= 0; i-- {
    fmt.Println(arr[i])
}
```

**C++**
```cpp
// Traditional for loop
int arr[] = {1, 2, 3, 4, 5};
int n = sizeof(arr) / sizeof(arr[0]);

for (int i = 0; i < n; i++) {
    std::cout << arr[i] << std::endl;
}

// C++20 ranges with views::iota
#include <ranges>
for (int i : std::views::iota(0, 10)) {
    std::cout << i << std::endl;
}
```

**SQL** - No index iteration! Set-based thinking.
```sql
-- SQL operates on SETS, not individual rows
-- The "loop" is implicit in SELECT
SELECT * FROM users;  -- Processes all rows

-- If you MUST iterate (avoid in production):
-- Use cursors (slow, anti-pattern)
DECLARE cursor_users CURSOR FOR SELECT id FROM users;
```

**Spark** - No explicit loops! Transformation chains.
```python
# Spark DataFrame - NO loops needed
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

df = spark.createDataFrame([(1,), (2,), (3,)], ["value"])

# WRONG: Imperative loop (kills performance)
# for row in df.collect():
#     print(row)

# CORRECT: Functional transformation
df.show()  # Action triggers computation
```

---

#### Pattern 2: Collection/Range Iteration (Enhanced For)

**Java**
```java
// Enhanced for-each (Java 5+)
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");
for (String name : names) {
    System.out.println(name);
}

// Works with any Iterable
Set<Integer> numbers = new HashSet<>(Arrays.asList(1, 2, 3));
for (int num : numbers) {
    System.out.println(num);
}

// Cannot modify collection during iteration!
// for (String name : names) {
//     names.remove(name);  // ConcurrentModificationException!
// }

// Use Iterator.remove() instead
Iterator<String> it = names.iterator();
while (it.hasNext()) {
    if (it.next().equals("Bob")) {
        it.remove();  // Safe removal
    }
}
```

**Python**
```python
# Direct iteration (Pythonic!)
names = ["Alice", "Bob", "Charlie"]
for name in names:
    print(name)

# Dict iteration
person = {"name": "Alice", "age": 30}
for key in person:  # Iterates keys by default
    print(key, person[key])

for key, value in person.items():  # Key-value pairs
    print(f"{key}: {value}")

for value in person.values():  # Values only
    print(value)

# String iteration
for char in "hello":
    print(char)

# Multiple sequences with zip
names = ["Alice", "Bob"]
ages = [25, 30]
for name, age in zip(names, ages):
    print(f"{name} is {age}")
```

**TypeScript**
```typescript
// for...of (ES6) - iterates VALUES
const arr = [1, 2, 3];
for (const value of arr) {
    console.log(value);  // 1, 2, 3
}

// for...in - iterates KEYS (indices for arrays)
for (const index in arr) {
    console.log(index);  // "0", "1", "2" (strings!)
}

// ⚠️ CRITICAL INTERVIEW TRAP: for...in vs for...of
const obj = { a: 1, b: 2 };

// for...in works on objects (iterates keys)
for (const key in obj) {
    console.log(key);  // "a", "b"
}

// for...of does NOT work on plain objects!
// for (const val of obj) { }  // TypeError!

// Use Object methods for objects
for (const [key, value] of Object.entries(obj)) {
    console.log(key, value);
}
```

**Go**
```go
// range for slices - returns (index, value)
arr := []int{1, 2, 3}
for i, v := range arr {
    fmt.Printf("Index %d: %d\n", i, v)
}

// Ignore index with blank identifier
for _, v := range arr {
    fmt.Println(v)
}

// range for maps - returns (key, value)
m := map[string]int{"a": 1, "b": 2}
for k, v := range m {
    fmt.Printf("%s: %d\n", k, v)
}

// range for strings - returns (index, rune)
for i, r := range "hello" {
    fmt.Printf("%d: %c\n", i, r)
}

// range for channels
ch := make(chan int, 3)
ch <- 1; ch <- 2; ch <- 3
close(ch)
for v := range ch {
    fmt.Println(v)
}
```

**C++**
```cpp
// Range-based for (C++11)
std::vector<int> vec = {1, 2, 3, 4, 5};
for (int x : vec) {
    std::cout << x << std::endl;
}

// By reference (modify in place)
for (int& x : vec) {
    x *= 2;
}

// By const reference (read-only, no copy)
for (const int& x : vec) {
    std::cout << x << std::endl;
}

// Works with arrays too
int arr[] = {1, 2, 3};
for (int x : arr) {
    std::cout << x << std::endl;
}

// Maps (structured bindings, C++17)
std::map<std::string, int> m = {{"a", 1}, {"b", 2}};
for (const auto& [key, value] : m) {
    std::cout << key << ": " << value << std::endl;
}
```

**Spark**
```python
# Spark: Transformations, not loops!
df = spark.createDataFrame([("Alice", 25), ("Bob", 30)], ["name", "age"])

# Transformation chain (lazy evaluation)
result = df.filter(df.age > 25).select("name")

# Action triggers actual processing
result.show()

# If you need per-row processing (avoid if possible):
df.foreach(lambda row: print(row))  # Runs on workers

# Collect to driver, then iterate (SMALL data only!)
for row in df.collect():
    print(row.name, row.age)
```

---

#### Pattern 3: While Loops

**Java**
```java
// while loop
int count = 0;
while (count < 5) {
    System.out.println(count);
    count++;
}

// do-while (executes at least once!)
int x = 10;
do {
    System.out.println(x);
    x--;
} while (x > 10);  // Prints 10 once even though condition is false

// Infinite loop with break
while (true) {
    String input = scanner.nextLine();
    if (input.equals("quit")) break;
    process(input);
}
```

**Python**
```python
# while loop
count = 0
while count < 5:
    print(count)
    count += 1

# Python has NO do-while! Workaround:
while True:
    x = get_input()
    if x == "quit":
        break
    process(x)

# Alternative: walrus operator (Python 3.8+)
while (line := input()) != "quit":
    process(line)

# ⭐ INTERVIEW FAVORITE: while-else
n = 10
while n > 0:
    if n == 5:
        break
    n -= 1
else:
    print("Loop completed without break")  # NOT printed

while n > 0:
    n -= 1
else:
    print("Loop completed!")  # Printed (no break occurred)
```

**TypeScript**
```typescript
// while loop
let count = 0;
while (count < 5) {
    console.log(count);
    count++;
}

// do-while
let x = 10;
do {
    console.log(x);
    x--;
} while (x > 10);  // Prints 10 once
```

**Go**
```go
// Go's "while" - just for without init and post
count := 0
for count < 5 {
    fmt.Println(count)
    count++
}

// Infinite loop
for {
    input := getInput()
    if input == "quit" {
        break
    }
    process(input)
}

// Go has NO do-while equivalent
// Workaround:
for ok := true; ok; ok = (x > 10) {
    fmt.Println(x)
    x--
}
```

**C++**
```cpp
// while loop
int count = 0;
while (count < 5) {
    std::cout << count << std::endl;
    count++;
}

// do-while
int x = 10;
do {
    std::cout << x << std::endl;
    x--;
} while (x > 10);
```

---

#### Pattern 4: Iterator Pattern

**Java**
```java
// Explicit Iterator
List<String> list = new ArrayList<>(Arrays.asList("a", "b", "c"));
Iterator<String> iterator = list.iterator();

while (iterator.hasNext()) {
    String item = iterator.next();
    System.out.println(item);
    if (item.equals("b")) {
        iterator.remove();  // Safe removal during iteration
    }
}

// ListIterator (bidirectional)
ListIterator<String> listIt = list.listIterator();
while (listIt.hasNext()) {
    listIt.next();
}
while (listIt.hasPrevious()) {
    System.out.println(listIt.previous());  // Reverse
}

// Custom Iterable
public class Range implements Iterable<Integer> {
    private final int start, end;

    public Range(int start, int end) {
        this.start = start;
        this.end = end;
    }

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<Integer>() {
            private int current = start;

            @Override
            public boolean hasNext() { return current < end; }

            @Override
            public Integer next() { return current++; }
        };
    }
}

// Usage
for (int i : new Range(0, 5)) {
    System.out.println(i);  // 0, 1, 2, 3, 4
}
```

**Python**
```python
# Python Iterator Protocol: __iter__ and __next__
class Range:
    def __init__(self, start, end):
        self.current = start
        self.end = end

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.end:
            raise StopIteration
        result = self.current
        self.current += 1
        return result

# Usage
for i in Range(0, 5):
    print(i)  # 0, 1, 2, 3, 4

# Manual iteration
it = iter([1, 2, 3])
print(next(it))  # 1
print(next(it))  # 2
print(next(it))  # 3
# next(it)  # StopIteration!

# Separate iterable and iterator (better pattern)
class CountUp:
    def __init__(self, limit):
        self.limit = limit

    def __iter__(self):
        return CountUpIterator(self.limit)

class CountUpIterator:
    def __init__(self, limit):
        self.current = 0
        self.limit = limit

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.limit:
            raise StopIteration
        self.current += 1
        return self.current - 1
```

**TypeScript**
```typescript
// Symbol.iterator protocol
class Range {
    constructor(private start: number, private end: number) {}

    [Symbol.iterator](): Iterator<number> {
        let current = this.start;
        const end = this.end;

        return {
            next(): IteratorResult<number> {
                if (current < end) {
                    return { value: current++, done: false };
                }
                return { value: undefined, done: true };
            }
        };
    }
}

// Usage
for (const i of new Range(0, 5)) {
    console.log(i);  // 0, 1, 2, 3, 4
}

// Spread works too
const arr = [...new Range(0, 5)];  // [0, 1, 2, 3, 4]
```

**Go**
```go
// Go has no iterator interface - use channels or callbacks
// Channel-based iterator pattern
func iterate(data []int) <-chan int {
    ch := make(chan int)
    go func() {
        for _, v := range data {
            ch <- v
        }
        close(ch)
    }()
    return ch
}

// Usage
for v := range iterate([]int{1, 2, 3}) {
    fmt.Println(v)
}

// Callback pattern (more common)
func forEach(data []int, fn func(int)) {
    for _, v := range data {
        fn(v)
    }
}

forEach([]int{1, 2, 3}, func(v int) {
    fmt.Println(v)
})
```

**C++**
```cpp
// C++ iterators: begin() and end()
#include <vector>
#include <iterator>

std::vector<int> vec = {1, 2, 3, 4, 5};

// Using iterators explicitly
for (auto it = vec.begin(); it != vec.end(); ++it) {
    std::cout << *it << std::endl;
}

// Reverse iterators
for (auto it = vec.rbegin(); it != vec.rend(); ++it) {
    std::cout << *it << std::endl;
}

// Custom iterator (simplified)
class Range {
public:
    class Iterator {
        int current;
    public:
        Iterator(int val) : current(val) {}
        int operator*() const { return current; }
        Iterator& operator++() { ++current; return *this; }
        bool operator!=(const Iterator& other) const {
            return current != other.current;
        }
    };

    Range(int start, int end) : start_(start), end_(end) {}
    Iterator begin() const { return Iterator(start_); }
    Iterator end() const { return Iterator(end_); }

private:
    int start_, end_;
};

// Usage
for (int i : Range(0, 5)) {
    std::cout << i << std::endl;
}
```

---

#### Pattern 5: Generators and Yield

**Python**
```python
# Generator function (lazy evaluation!)
def count_up(limit):
    n = 0
    while n < limit:
        yield n
        n += 1

# Usage
for i in count_up(5):
    print(i)  # 0, 1, 2, 3, 4

# Generator is LAZY - memory efficient
gen = count_up(1000000000)  # No memory allocated yet!
print(next(gen))  # 0 - computed on demand

# Generator expression (like list comprehension, but lazy)
squares = (x**2 for x in range(1000000))  # Generator object
print(next(squares))  # 0
print(next(squares))  # 1

# Infinite generator
def infinite_sequence():
    n = 0
    while True:
        yield n
        n += 1

# Two-way communication with send()
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is not None:
            total += value

gen = accumulator()
next(gen)  # Initialize
print(gen.send(10))  # 10
print(gen.send(20))  # 30

# yield from (delegation)
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item

list(flatten([1, [2, [3, 4]], 5]))  # [1, 2, 3, 4, 5]
```

**TypeScript**
```typescript
// Generator function
function* countUp(limit: number): Generator<number> {
    let n = 0;
    while (n < limit) {
        yield n;
        n++;
    }
}

// Usage
for (const i of countUp(5)) {
    console.log(i);  // 0, 1, 2, 3, 4
}

// Infinite generator
function* infiniteSequence(): Generator<number> {
    let n = 0;
    while (true) {
        yield n++;
    }
}

// Take first N from infinite
function take<T>(gen: Generator<T>, n: number): T[] {
    const result: T[] = [];
    for (let i = 0; i < n; i++) {
        const { value, done } = gen.next();
        if (done) break;
        result.push(value);
    }
    return result;
}

take(infiniteSequence(), 5);  // [0, 1, 2, 3, 4]

// yield* (delegation)
function* flatten(arr: any[]): Generator<number> {
    for (const item of arr) {
        if (Array.isArray(item)) {
            yield* flatten(item);
        } else {
            yield item;
        }
    }
}

[...flatten([1, [2, [3, 4]], 5])];  // [1, 2, 3, 4, 5]

// Async generator (ES2018)
async function* asyncCounter(limit: number): AsyncGenerator<number> {
    for (let i = 0; i < limit; i++) {
        await new Promise(resolve => setTimeout(resolve, 100));
        yield i;
    }
}

// Usage
for await (const i of asyncCounter(5)) {
    console.log(i);
}
```

**C++ (Coroutines - C++20)**
```cpp
// C++20 coroutines are complex - simplified example
#include <coroutine>
#include <generator>  // C++23

// C++23 std::generator (when available)
std::generator<int> countUp(int limit) {
    for (int i = 0; i < limit; i++) {
        co_yield i;
    }
}

// Usage
for (int i : countUp(5)) {
    std::cout << i << std::endl;
}
```

**Java** - No native generators, but can simulate:
```java
// Java has no yield - use Stream or custom Iterator
// Stream approach
IntStream.range(0, 5).forEach(System.out::println);

// Infinite stream
Stream.iterate(0, n -> n + 1)
      .limit(5)
      .forEach(System.out::println);
```

---

#### Pattern 6: Loop Control Flow (break, continue, labeled)

**Java**
```java
// break - exit loop
for (int i = 0; i < 10; i++) {
    if (i == 5) break;
    System.out.println(i);  // 0, 1, 2, 3, 4
}

// continue - skip iteration
for (int i = 0; i < 10; i++) {
    if (i % 2 == 0) continue;
    System.out.println(i);  // 1, 3, 5, 7, 9
}

// Labeled break (nested loops)
outer:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (i == 1 && j == 1) break outer;
        System.out.println(i + "," + j);
    }
}
// 0,0  0,1  0,2  1,0

// Labeled continue
outer:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (j == 1) continue outer;
        System.out.println(i + "," + j);
    }
}
// 0,0  1,0  2,0
```

**Python**
```python
# break and continue
for i in range(10):
    if i == 5:
        break
    print(i)  # 0, 1, 2, 3, 4

for i in range(10):
    if i % 2 == 0:
        continue
    print(i)  # 1, 3, 5, 7, 9

# ⭐ UNIQUE: for-else and while-else
# else runs if loop completes WITHOUT break

# Search pattern with for-else
def find_prime_factor(n):
    for i in range(2, n):
        if n % i == 0:
            print(f"Found factor: {i}")
            break
    else:
        print(f"{n} is prime!")

find_prime_factor(7)   # "7 is prime!"
find_prime_factor(12)  # "Found factor: 2"

# Python has NO labeled break!
# Workaround 1: Exception
class BreakOuter(Exception): pass

try:
    for i in range(3):
        for j in range(3):
            if i == 1 and j == 1:
                raise BreakOuter
except BreakOuter:
    pass

# Workaround 2: Function with return
def search_matrix(matrix, target):
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val == target:
                return (i, j)
    return None
```

**TypeScript**
```typescript
// break and continue - same as Java
for (let i = 0; i < 10; i++) {
    if (i === 5) break;
    console.log(i);
}

// Labeled statements (rarely used)
outer:
for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
        if (i === 1 && j === 1) break outer;
        console.log(i, j);
    }
}
```

**Go**
```go
// break and continue
for i := 0; i < 10; i++ {
    if i == 5 {
        break
    }
    fmt.Println(i)
}

// Labeled break (Go supports labels!)
outer:
for i := 0; i < 3; i++ {
    for j := 0; j < 3; j++ {
        if i == 1 && j == 1 {
            break outer
        }
        fmt.Println(i, j)
    }
}

// Also works with switch and select
```

**C++**
```cpp
// break and continue
for (int i = 0; i < 10; i++) {
    if (i == 5) break;
    std::cout << i << std::endl;
}

// C++ has no labeled break - use goto (carefully!)
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) {
        if (i == 1 && j == 1) goto end_loops;
        std::cout << i << "," << j << std::endl;
    }
}
end_loops:
// Code after loops

// Better: Extract to function
```

---

### 2.3 Common Pitfalls by Language

#### Java Pitfalls
```java
// 1. Modifying collection during enhanced for
List<Integer> nums = new ArrayList<>(Arrays.asList(1, 2, 3));
// WRONG: for (int n : nums) { if (n == 2) nums.remove(n); }
// Use removeIf() or Iterator

nums.removeIf(n -> n == 2);  // Correct

// 2. Integer overflow in loop condition
for (int i = 0; i < Integer.MAX_VALUE + 1; i++) {  // Infinite loop!
    // Integer.MAX_VALUE + 1 = Integer.MIN_VALUE (overflow)
}

// 3. Using == for String comparison in loop
for (String s : strings) {
    if (s == "target") { }  // WRONG - use equals()
}
```

#### Python Pitfalls
```python
# 1. Modifying list while iterating
nums = [1, 2, 3, 4, 5]
# WRONG:
# for n in nums:
#     if n % 2 == 0:
#         nums.remove(n)  # Skips elements!

# Correct: iterate over copy or use comprehension
nums = [n for n in nums if n % 2 != 0]

# 2. Late binding in closures
funcs = []
for i in range(3):
    funcs.append(lambda: i)  # All return 2!

for f in funcs:
    print(f())  # 2, 2, 2

# Fix: capture value
funcs = []
for i in range(3):
    funcs.append(lambda i=i: i)  # Capture current value

# 3. range() is exclusive on end
for i in range(5):  # 0, 1, 2, 3, 4 (NOT 5!)
    print(i)
```

#### TypeScript/JavaScript Pitfalls
```typescript
// 1. for...in vs for...of confusion
const arr = [10, 20, 30];

// for...in gives string indices!
for (const i in arr) {
    console.log(typeof i);  // "string"
    console.log(arr[i]);    // Works but i is "0", "1", "2"
}

// for...of gives values
for (const val of arr) {
    console.log(val);  // 10, 20, 30
}

// 2. for...in iterates inherited properties
Array.prototype.customMethod = function() {};
for (const key in [1, 2, 3]) {
    console.log(key);  // "0", "1", "2", "customMethod" (!)
}

// 3. var vs let in closures (classic trap)
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}  // 3, 3, 3

for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}  // 0, 1, 2

// 4. forEach doesn't work with async/await properly
async function wrong() {
    [1, 2, 3].forEach(async (n) => {
        await delay(n);
        console.log(n);
    });
    console.log("done");  // Prints BEFORE numbers!
}

async function correct() {
    for (const n of [1, 2, 3]) {
        await delay(n);
        console.log(n);
    }
    console.log("done");  // Prints AFTER numbers
}
```

#### Go Pitfalls
```go
// 1. Loop variable capture in goroutines
for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i)  // All print 3!
    }()
}

// Fix: Pass as argument
for i := 0; i < 3; i++ {
    go func(n int) {
        fmt.Println(n)  // 0, 1, 2 (order may vary)
    }(i)
}

// Go 1.22+ fixes this automatically with loop variable scoping

// 2. Pointer to loop variable
var pointers []*int
for i := 0; i < 3; i++ {
    pointers = append(pointers, &i)  // All point to same address!
}
// Fix: Create local copy
for i := 0; i < 3; i++ {
    v := i
    pointers = append(pointers, &v)
}

// 3. Range returns copy, not reference
type Item struct{ value int }
items := []Item{{1}, {2}, {3}}
for _, item := range items {
    item.value = 0  // Modifies copy, not original!
}
// items still [{1}, {2}, {3}]

// Fix: Use index
for i := range items {
    items[i].value = 0
}
```

#### C++ Pitfalls
```cpp
// 1. Off-by-one in loop bounds
std::vector<int> vec = {1, 2, 3};
// WRONG: for (int i = 0; i <= vec.size(); i++)  // Goes one past end!
for (size_t i = 0; i < vec.size(); i++) { }  // Correct

// 2. Iterator invalidation
std::vector<int> v = {1, 2, 3, 4, 5};
for (auto it = v.begin(); it != v.end(); ++it) {
    if (*it == 3) {
        v.erase(it);  // Iterator invalidated!
    }
}
// Fix: Use return value of erase
for (auto it = v.begin(); it != v.end(); ) {
    if (*it == 3) {
        it = v.erase(it);  // Returns next valid iterator
    } else {
        ++it;
    }
}

// 3. Signed/unsigned comparison
for (int i = 0; i < vec.size(); i++) { }  // Warning: signed/unsigned comparison
for (size_t i = 0; i < vec.size(); i++) { }  // Correct
```

---

## Section 3: Design Philosophy Links (설계 철학 링크)

### Official Documentation

| Language | Loop Documentation |
|----------|-------------------|
| **Java** | [Control Flow Statements](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/flow.html) |
| **Python** | [More Control Flow Tools](https://docs.python.org/3/tutorial/controlflow.html#for-statements) |
| **TypeScript** | [Iterators and Generators](https://www.typescriptlang.org/docs/handbook/iterators-and-generators.html) |
| **Go** | [For statements](https://go.dev/ref/spec#For_statements) |
| **SQL** | [SQL Cursors (Anti-pattern)](https://learn.microsoft.com/en-us/sql/t-sql/language-elements/cursors-transact-sql) |
| **C++** | [Range-based for](https://en.cppreference.com/w/cpp/language/range-for) |
| **Spark** | [RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html) |

### Design Philosophy Quotes

> **Python**: "There should be one-- and preferably only one --obvious way to do it."
> — The Zen of Python

Python's `for...in` is THE way to iterate. No traditional C-style for loop.

> **Go**: "Do Less. Enable More."
> — Go Proverbs

Go has only `for`. No `while`, no `do-while`. One construct, multiple forms.

> **Spark**: "The best way to iterate over data is to not iterate at all."
> — Spark Best Practices

Spark uses functional transformations, not imperative loops.

---

## Section 4: Palantir Context Hint (팔란티어 맥락 힌트)

### 4.1 Foundry/OSDK Iteration Patterns

```typescript
// Foundry TypeScript Functions - Object iteration
import { Objects, Ontology } from "@foundry/ontology-api";

// ⚠️ Anti-pattern: Loading all objects into memory
const allFlights = await Objects.search(Flight).all();  // Dangerous!
for (const flight of allFlights) {
    // Process each flight
}

// ✓ Better: Use pagination
let pageToken: string | undefined;
do {
    const page = await Objects.search(Flight)
        .pageSize(100)
        .pageToken(pageToken)
        .execute();

    for (const flight of page.data) {
        // Process each flight
    }
    pageToken = page.nextPageToken;
} while (pageToken);

// ✓ Best: Use aggregations when possible (no iteration!)
const avgDelay = await Objects.search(Flight)
    .aggregate(Flight.properties.delay.avg());
```

### 4.2 Spark Lazy Evaluation

```python
# Spark: Transformations are LAZY, Actions trigger execution
from pyspark.sql import functions as F

df = spark.read.parquet("s3://bucket/large_dataset")

# These are LAZY - nothing executed yet
transformed = (df
    .filter(F.col("status") == "active")
    .withColumn("processed", F.lit(True))
    .select("id", "name", "processed")
)

# ONLY when action is called, Spark plans and executes
transformed.show()  # Action!
transformed.count()  # Action!
transformed.write.parquet("output")  # Action!

# ⚠️ ANTI-PATTERN: Collecting to driver and looping
# for row in df.collect():  # OOM risk on large data!
#     process(row)

# ✓ CORRECT: Keep processing distributed
df.foreachPartition(lambda partition: process_partition(partition))
```

### 4.3 Palantir Interview Loop Questions

1. **"Implement an iterator that flattens nested lists"**
   - Tests: Iterator protocol, recursion vs iteration

2. **"Process a large file without loading it all into memory"**
   - Tests: Generator pattern, lazy evaluation

3. **"Find pairs that sum to target in sorted array"**
   - Tests: Two-pointer technique (disguised loop optimization)

4. **"Iterate over a binary tree without recursion"**
   - Tests: Using stack to simulate recursion

5. **"Why would you avoid loops in Spark?"**
   - Tests: Understanding distributed computing paradigm

### 4.4 Key Interview Patterns

```python
# Pattern: Two Pointers (efficient pair finding)
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        current_sum = arr[left] + arr[right]
        if current_sum == target:
            return [left, right]
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    return None

# Pattern: Sliding Window
def max_sum_subarray(arr, k):
    window_sum = sum(arr[:k])
    max_sum = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum

# Pattern: Fast & Slow Pointers (cycle detection)
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return True
    return False
```

---

## Section 5: Cross-References (상호 참조)

### Related Knowledge Bases

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F30** | Conditionals & Branching | Loop conditions use same boolean logic |
| **F32** | Functions & Methods | Loops often abstracted into functions |
| **F11** | Closures | Closure capture in loops (critical bug!) |
| **F33** | Recursion | Alternative to iteration, mutual conversion |
| **F50** | Collections/Arrays | What we iterate over |
| **F51** | Maps/Dictionaries | Key-value iteration patterns |
| **F60** | Streams & Functional | Declarative alternative to loops |
| **F70** | Error Handling | Breaking loops on errors |

### Algorithm Patterns Using Loops

| Pattern | Loop Type | Example |
|---------|-----------|---------|
| Linear Search | for loop | Find element in array |
| Binary Search | while loop | Find in sorted array |
| Two Pointers | while with two indices | Two sum, palindrome check |
| Sliding Window | for with window tracking | Max subarray sum |
| BFS | while with queue | Level-order traversal |
| DFS (iterative) | while with stack | Tree/graph traversal |
| Merge Sort (bottom-up) | nested for | Iterative sorting |

### Time Complexity and Loops

```
Single loop O(n):       for i in range(n): ...
Nested loops O(n²):     for i...: for j...: ...
Three nested O(n³):     for i...: for j...: for k...: ...
Loop with halving O(log n): while n > 1: n //= 2
Loop + binary search O(n log n): for i...: binary_search()
```

---

## Summary: Language Loop Cheatsheet

```
┌────────────────────────────────────────────────────────────────────────┐
│                         LOOP CHEATSHEET                                │
├─────────────┬──────────────────────────────────────────────────────────┤
│ Java        │ for(;;) | for-each | while | do-while | Iterator        │
│ Python      │ for...in | while | while-else | generators              │
│ TypeScript  │ for(;;) | for...of | for...in(keys) | while | function* │
│ Go          │ for only (all forms) | range | labeled break            │
│ SQL         │ NO LOOPS - use set operations | cursor (avoid)          │
│ C++         │ for(;;) | range-for | while | do-while | iterators      │
│ Spark       │ NO LOOPS - use transformations | actions trigger work   │
└─────────────┴──────────────────────────────────────────────────────────┘

CRITICAL INTERVIEW TRAPS:
1. Python for...else (else runs if NO break)
2. JS for...in vs for...of (in=keys, of=values)
3. Go has ONLY for (no while keyword)
4. Closure capture in loops (use let, not var in JS)
5. Go loop variable capture in goroutines
6. SQL: Think SETS, not loops
7. Spark: Think TRANSFORMATIONS, not iterations
8. Off-by-one errors in bounds
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
