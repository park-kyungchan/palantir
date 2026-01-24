# F54: Iterables & Sequences (Iterables and Sequences)

> **Concept ID**: `F54_iterables_sequences`
> **Universal Principle**: Objects that can be traversed element-by-element, with sequences providing indexed access
> **Prerequisites**: F31_loops_iteration, F43_higher_order_functions, F44_closures
> **Category**: Data Structures
> **Difficulty**: Intermediate -> Advanced
> **Interview Frequency**: (Critical - especially Python generators and Spark lazy evaluation)

---

## 1. Universal Concept (Language-Agnostic Definition)

### 1.1 What are Iterables and Sequences?

An **Iterable** is any object that can produce its elements one at a time. An **Iterator** is the mechanism that tracks the current position during traversal. A **Sequence** is a special type of iterable that provides indexed (random) access to elements.

```
+------------------------------------------------------------------+
|                ITERABLE vs ITERATOR vs SEQUENCE                    |
+------------------------------------------------------------------+
|                                                                    |
|   ITERABLE (What can be looped)                                   |
|   +----------------------------------------------------------+   |
|   |  - Can return an iterator                                 |   |
|   |  - May be traversed multiple times                        |   |
|   |  - Examples: list, set, dict, file, generator             |   |
|   +----------------------------------------------------------+   |
|                           |                                        |
|                           v                                        |
|   ITERATOR (The "cursor" that tracks position)                    |
|   +----------------------------------------------------------+   |
|   |  - Has next() method to get next element                  |   |
|   |  - Maintains internal state (position)                    |   |
|   |  - Usually single-use (exhaustible)                       |   |
|   |  - Signals end with StopIteration or null/done            |   |
|   +----------------------------------------------------------+   |
|                                                                    |
|   SEQUENCE (Special iterable with index access)                   |
|   +----------------------------------------------------------+   |
|   |  - Ordered elements                                       |   |
|   |  - O(1) index access: seq[i]                             |   |
|   |  - Has length property                                    |   |
|   |  - Examples: array, list, string, tuple                   |   |
|   +----------------------------------------------------------+   |
|                                                                    |
+------------------------------------------------------------------+
```

### 1.2 Mental Model: Book vs Bookmark

```
+------------------------------------------------------------------+
|                    THE BOOK AND BOOKMARK ANALOGY                   |
+------------------------------------------------------------------+
|                                                                    |
|   BOOK (Iterable)                                                 |
|   - Contains all the pages (elements)                             |
|   - Can be read from start to finish                              |
|   - Can have multiple bookmarks at different positions            |
|   - Some books can be re-read (list), others disappear after      |
|     reading (generator - like a self-destructing message)         |
|                                                                    |
|   BOOKMARK (Iterator)                                             |
|   - Points to current page                                        |
|   - "next()" = turn to next page and read it                     |
|   - Remembers where you are even if you close the book            |
|   - When you reach the end, bookmark becomes useless              |
|                                                                    |
|   PAGE NUMBER (Sequence Index)                                    |
|   - Can jump directly to page 42 (random access)                  |
|   - Don't need bookmark - just use the page number                |
|   - Only works for sequenced content (not all books have pages!)  |
|                                                                    |
+------------------------------------------------------------------+
```

### 1.3 Lazy Evaluation: Generate on Demand

**Lazy evaluation** means values are computed only when needed, not upfront:

```
+------------------------------------------------------------------+
|                    LAZY vs EAGER EVALUATION                        |
+------------------------------------------------------------------+
|                                                                    |
|   EAGER (List/Array):                                             |
|   data = [compute(x) for x in range(1000000)]                    |
|   # All 1 million values computed and stored NOW                  |
|   # Memory: O(n)                                                  |
|                                                                    |
|   LAZY (Generator):                                               |
|   data = (compute(x) for x in range(1000000))                    |
|   # NOTHING computed yet - just a recipe                          |
|   # Memory: O(1)                                                  |
|   # Values computed one-by-one when requested                     |
|                                                                    |
|   Why Lazy?                                                       |
|   1. Memory efficiency: Process billion rows with constant RAM    |
|   2. Early termination: Stop as soon as you find what you need   |
|   3. Infinite sequences: Can represent infinite streams           |
|   4. Pipeline optimization: Fuse transformations together         |
|                                                                    |
+------------------------------------------------------------------+
```

### 1.4 Why This Matters

| Use Case | Why Iterables Matter |
|----------|---------------------|
| **Big Data (Spark)** | Process terabytes without loading into memory |
| **File Processing** | Read line-by-line instead of loading entire file |
| **Network Streaming** | Handle continuous data streams |
| **Pipelines** | Chain transformations efficiently |
| **Infinite Sequences** | Represent mathematical sequences |
| **Resource Management** | Lazy loading of expensive resources |

---

## 2. Semantic Comparison Matrix

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **Iterable Interface** | `Iterable<T>` | `__iter__()` | `Iterable<T>` | (no interface) | cursor | `begin()/end()` | RDD/DataFrame |
| **Iterator Interface** | `Iterator<T>` | `__next__()` | `Iterator<T>` | N/A (use range) | `FETCH` | `++`, `*`, `!=` | N/A (internal) |
| **Generator Syntax** | N/A (use Stream) | `yield` | `function*` | N/A (use channels) | N/A | coroutines (C++20) | N/A |
| **Lazy by Default** | Stream only | Generators | No (Array eager) | Channels | Lazy CTE | ranges (C++20) | YES! |
| **Sequence Type** | `List<T>` | `list`, `tuple` | `Array<T>` | `[]T` (slice) | N/A | `std::vector` | N/A |
| **Index Access** | `.get(i)` | `[i]` | `[i]` | `[i]` | N/A | `[i]` | N/A |
| **Range/Enumerate** | `IntStream.range()` | `range()`, `enumerate()` | `entries()` | `for i := range` | `ROW_NUMBER()` | `std::views::iota` | N/A |
| **Iterator Utilities** | Stream API | `itertools` | N/A (lodash) | N/A | N/A | `<algorithm>` | RDD ops |

### 2.2 Detailed Code Examples

---

#### Pattern 1: Iterator Protocol Implementation

**Java - Implementing Iterable**
```java
import java.util.Iterator;
import java.util.NoSuchElementException;

// Custom iterable that generates Fibonacci sequence
public class FibonacciSequence implements Iterable<Long> {
    private final int count;

    public FibonacciSequence(int count) {
        this.count = count;
    }

    @Override
    public Iterator<Long> iterator() {
        return new FibonacciIterator(count);
    }

    private static class FibonacciIterator implements Iterator<Long> {
        private long a = 0, b = 1;
        private int remaining;

        FibonacciIterator(int count) {
            this.remaining = count;
        }

        @Override
        public boolean hasNext() {
            return remaining > 0;
        }

        @Override
        public Long next() {
            if (!hasNext()) {
                throw new NoSuchElementException();
            }
            remaining--;
            long result = a;
            long temp = a + b;
            a = b;
            b = temp;
            return result;
        }
    }
}

// Usage
public static void main(String[] args) {
    // For-each works because FibonacciSequence is Iterable
    for (long fib : new FibonacciSequence(10)) {
        System.out.println(fib);  // 0, 1, 1, 2, 3, 5, 8, 13, 21, 34
    }

    // Can create multiple iterators from same iterable
    FibonacciSequence fibs = new FibonacciSequence(5);
    Iterator<Long> it1 = fibs.iterator();  // Fresh iterator
    Iterator<Long> it2 = fibs.iterator();  // Another fresh iterator

    System.out.println(it1.next());  // 0
    System.out.println(it1.next());  // 1
    System.out.println(it2.next());  // 0 (independent!)
}
```

**Python - Iterator Protocol (__iter__ and __next__)**
```python
from typing import Iterator, Iterable

class FibonacciSequence:
    """Custom iterable generating Fibonacci numbers."""

    def __init__(self, count: int):
        self.count = count

    def __iter__(self) -> Iterator[int]:
        """Return a NEW iterator each time."""
        return FibonacciIterator(self.count)


class FibonacciIterator:
    """Iterator that tracks Fibonacci state."""

    def __init__(self, count: int):
        self.a, self.b = 0, 1
        self.remaining = count

    def __iter__(self) -> 'FibonacciIterator':
        """Iterators are also iterable (return self)."""
        return self

    def __next__(self) -> int:
        """Return next Fibonacci number or raise StopIteration."""
        if self.remaining <= 0:
            raise StopIteration
        self.remaining -= 1
        result = self.a
        self.a, self.b = self.b, self.a + self.b
        return result


# Usage
fibs = FibonacciSequence(10)

# For loop works because __iter__ returns an iterator
for fib in fibs:
    print(fib)  # 0, 1, 1, 2, 3, 5, 8, 13, 21, 34

# Can iterate multiple times (creates new iterator each time)
print(list(fibs))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
print(list(fibs))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34] (same!)

# Manual iteration
it = iter(fibs)
print(next(it))  # 0
print(next(it))  # 1
print(next(it))  # 1

# IMPORTANT: Built-in iter() and next() functions
numbers = [1, 2, 3]
iterator = iter(numbers)  # Calls numbers.__iter__()
print(next(iterator))     # Calls iterator.__next__()
```

**TypeScript - Symbol.iterator Protocol**
```typescript
// Custom iterable class implementing Symbol.iterator
class FibonacciSequence implements Iterable<number> {
    constructor(private count: number) {}

    [Symbol.iterator](): Iterator<number> {
        let a = 0, b = 1;
        let remaining = this.count;

        return {
            next(): IteratorResult<number> {
                if (remaining <= 0) {
                    return { value: undefined, done: true };
                }
                remaining--;
                const result = a;
                [a, b] = [b, a + b];
                return { value: result, done: false };
            }
        };
    }
}

// Usage
const fibs = new FibonacciSequence(10);

// for...of works because Symbol.iterator is defined
for (const fib of fibs) {
    console.log(fib);  // 0, 1, 1, 2, 3, 5, 8, 13, 21, 34
}

// Spread operator also works
const fibArray = [...new FibonacciSequence(5)];  // [0, 1, 1, 2, 3]

// Array.from() works
const fibList = Array.from(new FibonacciSequence(5));

// Destructuring works
const [first, second, third] = new FibonacciSequence(10);
console.log(first, second, third);  // 0 1 1

// Manual iteration
const iterator = fibs[Symbol.iterator]();
console.log(iterator.next());  // { value: 0, done: false }
console.log(iterator.next());  // { value: 1, done: false }
```

**Go - Using Channels as Iterator Pattern**
```go
package main

import "fmt"

// Go doesn't have iterator interface - use channels or callbacks

// Channel-based iterator (concurrent pattern)
func fibonacci(count int) <-chan int {
    ch := make(chan int)
    go func() {
        a, b := 0, 1
        for i := 0; i < count; i++ {
            ch <- a
            a, b = b, a+b
        }
        close(ch)  // Signal end of iteration
    }()
    return ch
}

// Callback-based iterator (more common in Go)
func fibonacciCallback(count int, fn func(int)) {
    a, b := 0, 1
    for i := 0; i < count; i++ {
        fn(a)
        a, b = b, a+b
    }
}

// Slice-returning function (eager, simple)
func fibonacciSlice(count int) []int {
    result := make([]int, count)
    a, b := 0, 1
    for i := 0; i < count; i++ {
        result[i] = a
        a, b = b, a+b
    }
    return result
}

func main() {
    // Channel-based: for range on channel
    for fib := range fibonacci(10) {
        fmt.Println(fib)
    }

    // Callback-based
    fibonacciCallback(5, func(n int) {
        fmt.Println(n)
    })

    // Slice-based: standard Go pattern
    for _, fib := range fibonacciSlice(10) {
        fmt.Println(fib)
    }
}
```

**C++ - begin/end Iterator Pattern**
```cpp
#include <iostream>
#include <iterator>

// Custom iterator class
class FibonacciIterator {
public:
    using iterator_category = std::forward_iterator_tag;
    using value_type = long long;
    using difference_type = std::ptrdiff_t;
    using pointer = const long long*;
    using reference = const long long&;

    FibonacciIterator(int count = 0)
        : a_(0), b_(1), remaining_(count) {}

    reference operator*() const { return a_; }
    pointer operator->() const { return &a_; }

    FibonacciIterator& operator++() {
        long long temp = a_ + b_;
        a_ = b_;
        b_ = temp;
        --remaining_;
        return *this;
    }

    bool operator!=(const FibonacciIterator& other) const {
        return remaining_ != other.remaining_;
    }

    bool operator==(const FibonacciIterator& other) const {
        return remaining_ == other.remaining_;
    }

private:
    mutable long long a_ = 0, b_ = 1;
    int remaining_;
};

// Iterable class
class FibonacciSequence {
public:
    FibonacciSequence(int count) : count_(count) {}

    FibonacciIterator begin() const { return FibonacciIterator(count_); }
    FibonacciIterator end() const { return FibonacciIterator(0); }

private:
    int count_;
};

int main() {
    // Range-based for loop works with begin()/end()
    for (auto fib : FibonacciSequence(10)) {
        std::cout << fib << " ";  // 0 1 1 2 3 5 8 13 21 34
    }
    std::cout << std::endl;

    return 0;
}
```

**SQL - Cursor-Based Iteration (Generally Avoid!)**
```sql
-- SQL is SET-based, not iterator-based
-- Cursors exist but are ANTI-PATTERNS for most cases

-- Cursor example (avoid in production!)
DECLARE @id INT;
DECLARE user_cursor CURSOR FOR
    SELECT id FROM users WHERE status = 'active';

OPEN user_cursor;
FETCH NEXT FROM user_cursor INTO @id;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- Process each row (SLOW!)
    PRINT @id;
    FETCH NEXT FROM user_cursor INTO @id;
END;

CLOSE user_cursor;
DEALLOCATE user_cursor;

-- BETTER: Set-based operations
-- Use JOINs, subqueries, and window functions instead
SELECT
    id,
    ROW_NUMBER() OVER (ORDER BY created_at) AS row_num
FROM users
WHERE status = 'active';
```

**Spark - RDD and DataFrame Iteration (Distributed!)**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.appName("Iterator").getOrCreate()

# =====================================================
# CRITICAL: Spark iteration is DISTRIBUTED and LAZY
# =====================================================

# Create RDD from list
numbers_rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5])

# .map() is a transformation (LAZY - nothing executes!)
doubled_rdd = numbers_rdd.map(lambda x: x * 2)

# .collect() is an action (triggers execution, brings to driver)
result = doubled_rdd.collect()  # [2, 4, 6, 8, 10]

# DataFrame iteration
df = spark.createDataFrame([(1, "a"), (2, "b"), (3, "c")], ["id", "name"])

# WRONG: Never iterate with collect() on large data!
# for row in df.collect():  # OOM risk!
#     print(row)

# CORRECT: Use Spark operations
df.show()  # Action: display on driver
df.foreach(lambda row: print(row))  # Action: execute on workers

# foreach vs foreachPartition
def process_partition(partition):
    # Called once per partition with iterator of rows
    for row in partition:
        print(row)

df.foreachPartition(process_partition)

# Iterator access within partition (memory efficient)
def partition_iterator(iterator):
    # Process one row at a time
    for row in iterator:
        yield row.id * 2

result_rdd = df.rdd.mapPartitions(partition_iterator)
```

---

#### Pattern 2: Python Generators with yield (INTERVIEW CRITICAL!)

**Python - Generator Functions**
```python
from typing import Generator, Iterator, Any

# =====================================================
# GENERATOR FUNCTION: Uses 'yield' instead of 'return'
# =====================================================

def count_up(limit: int) -> Generator[int, None, None]:
    """Generator that yields numbers 0 to limit-1."""
    n = 0
    while n < limit:
        yield n  # Suspend here, return n, resume on next()
        n += 1
    # Implicit StopIteration when function ends

# Usage
gen = count_up(5)
print(type(gen))  # <class 'generator'>

print(next(gen))  # 0
print(next(gen))  # 1
print(next(gen))  # 2

# Can use in for loop
for num in count_up(3):
    print(num)  # 0, 1, 2


# =====================================================
# INFINITE GENERATOR: Represents infinite sequence
# =====================================================

def infinite_fibonacci() -> Generator[int, None, None]:
    """Infinite Fibonacci sequence - LAZY, O(1) memory!"""
    a, b = 0, 1
    while True:  # Infinite!
        yield a
        a, b = b, a + b

# Take first N from infinite sequence
def take(gen: Iterator[int], n: int) -> list[int]:
    """Take first n elements from generator."""
    result = []
    for _ in range(n):
        try:
            result.append(next(gen))
        except StopIteration:
            break
    return result

fibs = infinite_fibonacci()
print(take(fibs, 10))  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


# =====================================================
# GENERATOR EXPRESSION: Inline lazy evaluation
# =====================================================

# List comprehension (EAGER - computes all at once)
squares_list = [x**2 for x in range(1000000)]  # 1M items in memory!

# Generator expression (LAZY - computes on demand)
squares_gen = (x**2 for x in range(1000000))  # O(1) memory!

# Only compute what you need
print(next(squares_gen))  # 0
print(next(squares_gen))  # 1


# =====================================================
# yield from: Delegation to sub-generator
# =====================================================

def flatten(nested: list) -> Generator:
    """Flatten nested lists using yield from."""
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)  # Delegate to recursive call
        else:
            yield item

nested = [1, [2, [3, 4]], 5, [6]]
print(list(flatten(nested)))  # [1, 2, 3, 4, 5, 6]


# =====================================================
# GENERATOR AS COROUTINE: Two-way communication
# =====================================================

def accumulator() -> Generator[int, int, None]:
    """Generator that receives values via send()."""
    total = 0
    while True:
        value = yield total  # Yield current total, receive new value
        if value is not None:
            total += value

gen = accumulator()
next(gen)           # Initialize (must call first!)
print(gen.send(10)) # 10
print(gen.send(20)) # 30
print(gen.send(15)) # 45


# =====================================================
# GENERATOR FOR FILE PROCESSING (Real-world use!)
# =====================================================

def read_large_file(filepath: str) -> Generator[str, None, None]:
    """Memory-efficient file reading."""
    with open(filepath, 'r') as f:
        for line in f:  # File object is already iterable!
            yield line.strip()

# Process billion-line file with O(1) memory
# for line in read_large_file("huge_file.txt"):
#     process(line)


# =====================================================
# INTERVIEW QUESTION: "Why use generator over list?"
# =====================================================

# Answer:
# 1. Memory: Generator uses O(1) vs list O(n)
# 2. Speed: Generator computes lazily (fast if you don't need all)
# 3. Infinite: Generator can represent infinite sequences
# 4. Pipeline: Chain generators for memory-efficient pipelines

# Pipeline example
def numbers(limit):
    for i in range(limit):
        yield i

def double(gen):
    for x in gen:
        yield x * 2

def filter_even(gen):
    for x in gen:
        if x % 2 == 0:
            yield x

# Chain: numbers -> double -> filter_even
pipeline = filter_even(double(numbers(10)))
print(list(pipeline))  # [0, 4, 8, 12, 16]
# Only 3 items in memory at any time!
```

---

#### Pattern 3: JavaScript/TypeScript Generators

**TypeScript - Generator Functions**
```typescript
// =====================================================
// GENERATOR FUNCTION: function* syntax
// =====================================================

function* countUp(limit: number): Generator<number, void, unknown> {
    let n = 0;
    while (n < limit) {
        yield n;
        n++;
    }
}

// Usage
const gen = countUp(5);
console.log(gen.next());  // { value: 0, done: false }
console.log(gen.next());  // { value: 1, done: false }
console.log(gen.next());  // { value: 2, done: false }
console.log(gen.next());  // { value: 3, done: false }
console.log(gen.next());  // { value: 4, done: false }
console.log(gen.next());  // { value: undefined, done: true }

// for...of works with generators
for (const num of countUp(3)) {
    console.log(num);  // 0, 1, 2
}


// =====================================================
// INFINITE GENERATOR
// =====================================================

function* infiniteFibonacci(): Generator<number, never, unknown> {
    let a = 0, b = 1;
    while (true) {
        yield a;
        [a, b] = [b, a + b];
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

const fibs = infiniteFibonacci();
console.log(take(fibs, 10));  // [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


// =====================================================
// yield* : Delegation to another iterable
// =====================================================

function* flatten(arr: any[]): Generator<number> {
    for (const item of arr) {
        if (Array.isArray(item)) {
            yield* flatten(item);  // Delegate to recursive call
        } else {
            yield item;
        }
    }
}

const nested = [1, [2, [3, 4]], 5];
console.log([...flatten(nested)]);  // [1, 2, 3, 4, 5]


// =====================================================
// ASYNC GENERATOR (ES2018) - For async iteration
// =====================================================

async function* fetchPages(urls: string[]): AsyncGenerator<string> {
    for (const url of urls) {
        const response = await fetch(url);
        yield await response.text();
    }
}

// for await...of with async generators
async function processPages() {
    const urls = ['url1', 'url2', 'url3'];
    for await (const content of fetchPages(urls)) {
        console.log(content.length);
    }
}


// =====================================================
// GENERATOR WITH send() - Two-way communication
// =====================================================

function* accumulator(): Generator<number, void, number> {
    let total = 0;
    while (true) {
        const value = yield total;  // Receive value from send()
        if (value !== undefined) {
            total += value;
        }
    }
}

const acc = accumulator();
acc.next();               // Initialize
console.log(acc.next(10)); // { value: 10, done: false }
console.log(acc.next(20)); // { value: 30, done: false }
console.log(acc.next(15)); // { value: 45, done: false }
```

---

#### Pattern 4: Java Stream as Lazy Iterable

**Java - Stream Lazy Evaluation**
```java
import java.util.stream.*;
import java.util.*;

public class StreamLaziness {
    public static void main(String[] args) {
        // =====================================================
        // STREAMS ARE LAZY - Operations build a pipeline
        // =====================================================

        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

        // This builds a pipeline but executes NOTHING
        Stream<Integer> pipeline = numbers.stream()
            .filter(x -> {
                System.out.println("Filter: " + x);
                return x % 2 == 0;
            })
            .map(x -> {
                System.out.println("Map: " + x);
                return x * 2;
            });

        System.out.println("Pipeline created, nothing executed yet!");

        // Terminal operation triggers execution
        List<Integer> result = pipeline.collect(Collectors.toList());
        // Output shows interleaved filter/map (lazy, fused)

        // =====================================================
        // INFINITE STREAM with Stream.iterate()
        // =====================================================

        // Infinite Fibonacci sequence
        Stream<long[]> fibStream = Stream.iterate(
            new long[]{0, 1},
            arr -> new long[]{arr[1], arr[0] + arr[1]}
        );

        List<Long> first10 = fibStream
            .limit(10)  // Take only 10 (short-circuit!)
            .map(arr -> arr[0])
            .collect(Collectors.toList());
        // [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

        // =====================================================
        // Stream.generate() - Supplier-based infinite stream
        // =====================================================

        Stream<Double> randoms = Stream.generate(Math::random);
        List<Double> first5Random = randoms.limit(5).collect(Collectors.toList());

        // =====================================================
        // IntStream, LongStream, DoubleStream - Primitive streams
        // =====================================================

        IntStream range = IntStream.range(0, 100);  // 0 to 99
        IntStream rangeClosed = IntStream.rangeClosed(1, 100);  // 1 to 100

        int sum = IntStream.range(1, 101).sum();  // 5050

        // =====================================================
        // Stream from Iterator (bridge)
        // =====================================================

        Iterator<Integer> iterator = Arrays.asList(1, 2, 3).iterator();
        Spliterator<Integer> spliterator = Spliterators.spliteratorUnknownSize(
            iterator, Spliterator.ORDERED
        );
        Stream<Integer> streamFromIter = StreamSupport.stream(spliterator, false);

        // =====================================================
        // WHY STREAM IS CALLED "LAZY"
        // =====================================================
        //
        // 1. Intermediate operations (filter, map, flatMap, etc.)
        //    just record what to do, don't execute
        //
        // 2. Terminal operations (collect, forEach, reduce, etc.)
        //    trigger actual computation
        //
        // 3. Short-circuit operations (findFirst, limit, anyMatch)
        //    can stop early without processing all elements
        //
        // 4. Operations are FUSED - filter-then-map processes
        //    each element through both in one pass
    }
}
```

---

#### Pattern 5: Go Channels as Iterator-Like Pattern

**Go - Channels for Iteration**
```go
package main

import (
    "context"
    "fmt"
    "time"
)

// =====================================================
// CHANNEL AS ITERATOR: Go's concurrent iteration
// =====================================================

// Basic generator pattern
func generateNumbers(n int) <-chan int {
    ch := make(chan int)
    go func() {
        for i := 0; i < n; i++ {
            ch <- i
        }
        close(ch)  // Signal iteration complete
    }()
    return ch
}

// Infinite generator with cancellation
func infiniteFibonacci(ctx context.Context) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch)
        a, b := 0, 1
        for {
            select {
            case <-ctx.Done():
                return  // Stop on cancellation
            case ch <- a:
                a, b = b, a+b
            }
        }
    }()
    return ch
}

// Pipeline: Chain channels for data processing
func double(input <-chan int) <-chan int {
    output := make(chan int)
    go func() {
        for n := range input {
            output <- n * 2
        }
        close(output)
    }()
    return output
}

func filterEven(input <-chan int) <-chan int {
    output := make(chan int)
    go func() {
        for n := range input {
            if n%2 == 0 {
                output <- n
            }
        }
        close(output)
    }()
    return output
}

func main() {
    // Basic channel iteration
    for n := range generateNumbers(5) {
        fmt.Println(n)  // 0, 1, 2, 3, 4
    }

    // Infinite generator with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel()

    count := 0
    for fib := range infiniteFibonacci(ctx) {
        fmt.Println(fib)
        count++
        if count >= 10 {
            break
        }
    }

    // Pipeline: generate -> double -> filterEven
    pipeline := filterEven(double(generateNumbers(10)))
    for n := range pipeline {
        fmt.Println(n)  // 0, 4, 8, 12, 16
    }
}
```

---

#### Pattern 6: Spark Lazy Transformations vs Actions (INTERVIEW CRITICAL!)

**Spark - Transformations and Actions**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, udf, sum as spark_sum
from pyspark.sql.types import IntegerType

spark = SparkSession.builder.appName("LazyEval").getOrCreate()

# =====================================================
# CRITICAL CONCEPT: TRANSFORMATIONS vs ACTIONS
# =====================================================
#
# TRANSFORMATIONS (LAZY):
#   - map, flatMap, filter, groupBy, select, withColumn, join, etc.
#   - Build a DAG (Directed Acyclic Graph) of operations
#   - Nothing executes until an action is called
#
# ACTIONS (EAGER):
#   - collect, count, show, write, save, reduce, first, take, etc.
#   - Trigger execution of the DAG
#   - Return results to driver or write to storage
#

# Create DataFrame
data = [(1, "Alice", 100), (2, "Bob", 200), (3, "Charlie", 150)]
df = spark.createDataFrame(data, ["id", "name", "score"])

# =====================================================
# ALL TRANSFORMATIONS - NOTHING EXECUTES!
# =====================================================

# Transformation 1: filter
filtered = df.filter(col("score") > 100)

# Transformation 2: add column
with_category = filtered.withColumn(
    "category",
    when(col("score") > 180, "high").otherwise("medium")
)

# Transformation 3: select
final = with_category.select("name", "category")

print("Transformations complete - but NOTHING has executed!")
print(f"Query plan:\n{final.explain()}")  # Shows DAG, still no execution

# =====================================================
# ACTION TRIGGERS EXECUTION
# =====================================================

# NOW it executes!
final.show()
#   +-------+--------+
#   |   name|category|
#   +-------+--------+
#   |    Bob|  medium|
#   +-------+--------+

# =====================================================
# MULTIPLE ACTIONS = MULTIPLE EXECUTIONS (cache to avoid!)
# =====================================================

expensive_df = df.filter(col("score") > 50).withColumn("doubled", col("score") * 2)

# Each action triggers re-computation!
expensive_df.count()   # Computes filter + withColumn
expensive_df.show()    # Computes filter + withColumn AGAIN!
expensive_df.collect() # Computes filter + withColumn AGAIN!

# SOLUTION: Cache intermediate results
expensive_df.cache()   # Mark for caching
expensive_df.count()   # First action: computes and caches
expensive_df.show()    # Uses cached data (fast!)
expensive_df.collect() # Uses cached data (fast!)

# =====================================================
# RDD-LEVEL LAZY EVALUATION
# =====================================================

rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5])

# Transformation chain (LAZY)
doubled_rdd = rdd.map(lambda x: x * 2)      # LAZY
filtered_rdd = doubled_rdd.filter(lambda x: x > 4)  # LAZY
final_rdd = filtered_rdd.map(lambda x: x + 1)      # LAZY

# Nothing has executed yet!

# Action triggers entire chain
result = final_rdd.collect()  # [5, 7, 9, 11]
# Computation: 1*2=2 (filtered), 2*2=4 (filtered), 3*2=6>4 -> 6+1=7, etc.

# =====================================================
# INTERVIEW QUESTION: "When does Spark compute?"
# =====================================================
#
# Answer: ONLY when an ACTION is called!
#
# Transformations:
#   - map, flatMap, filter, select, where, groupBy
#   - withColumn, join, union, distinct, sort
#   - ALL are lazy - just build the execution plan
#
# Actions:
#   - collect(), show(), count(), first(), take(n)
#   - write(), save(), saveAsTextFile()
#   - reduce(), aggregate(), foreach()
#   - These TRIGGER execution of all pending transformations
#

# =====================================================
# WHY LAZY EVALUATION MATTERS
# =====================================================
#
# 1. OPTIMIZATION: Catalyst optimizer can optimize entire pipeline
#    - Predicate pushdown: Move filters closer to data source
#    - Column pruning: Only read needed columns
#    - Join reordering: Choose optimal join order
#
# 2. EFFICIENCY: Avoid intermediate materialization
#    - Without lazy: filter -> write -> map -> write -> reduce
#    - With lazy: filter+map+reduce in single pass
#
# 3. RESILIENCE: DAG enables recomputation on failure
#    - If partition fails, Spark can recompute from lineage
#
```

---

#### Pattern 7: Python itertools Module (Interview Essential!)

**Python - itertools for Efficient Iteration**
```python
import itertools
from typing import Iterable, Iterator, TypeVar

T = TypeVar('T')

# =====================================================
# itertools.chain: Flatten multiple iterables
# =====================================================

list1 = [1, 2, 3]
list2 = [4, 5, 6]
list3 = [7, 8, 9]

# Chain them together (lazy!)
chained = itertools.chain(list1, list2, list3)
print(list(chained))  # [1, 2, 3, 4, 5, 6, 7, 8, 9]

# chain.from_iterable: Flatten iterable of iterables
nested = [[1, 2], [3, 4], [5, 6]]
flattened = itertools.chain.from_iterable(nested)
print(list(flattened))  # [1, 2, 3, 4, 5, 6]


# =====================================================
# itertools.cycle: Infinite cycling over iterable
# =====================================================

colors = itertools.cycle(['red', 'green', 'blue'])
for i, color in enumerate(colors):
    print(f"Item {i}: {color}")
    if i >= 5:
        break
# Item 0: red, Item 1: green, Item 2: blue, Item 3: red, ...


# =====================================================
# itertools.repeat: Repeat value (optionally limited)
# =====================================================

# Infinite repeat
# ones = itertools.repeat(1)  # 1, 1, 1, 1, ...

# Limited repeat
threes = itertools.repeat(3, times=5)
print(list(threes))  # [3, 3, 3, 3, 3]


# =====================================================
# itertools.islice: Slice an iterator (like list slicing)
# =====================================================

# Can't do normal slicing on generators!
gen = (x**2 for x in range(100))
# gen[5:10]  # TypeError!

# Use islice instead
gen = (x**2 for x in range(100))
sliced = itertools.islice(gen, 5, 10)
print(list(sliced))  # [25, 36, 49, 64, 81]

# islice(iterable, stop)
# islice(iterable, start, stop)
# islice(iterable, start, stop, step)


# =====================================================
# itertools.groupby: Group consecutive elements
# =====================================================

# IMPORTANT: Data must be SORTED by key first!
data = [
    ('A', 1), ('A', 2), ('A', 3),
    ('B', 4), ('B', 5),
    ('A', 6)  # New 'A' group (not merged with earlier!)
]

for key, group in itertools.groupby(data, key=lambda x: x[0]):
    print(f"{key}: {list(group)}")
# A: [('A', 1), ('A', 2), ('A', 3)]
# B: [('B', 4), ('B', 5)]
# A: [('A', 6)]

# Sort first for proper grouping
sorted_data = sorted(data, key=lambda x: x[0])
for key, group in itertools.groupby(sorted_data, key=lambda x: x[0]):
    print(f"{key}: {list(group)}")
# A: [('A', 1), ('A', 2), ('A', 3), ('A', 6)]
# B: [('B', 4), ('B', 5)]


# =====================================================
# itertools.count: Infinite counter
# =====================================================

counter = itertools.count(start=10, step=2)
print(next(counter))  # 10
print(next(counter))  # 12
print(next(counter))  # 14


# =====================================================
# itertools.takewhile / dropwhile
# =====================================================

numbers = [1, 3, 5, 2, 4, 6, 8]

# Take while condition is true
taken = itertools.takewhile(lambda x: x < 5, numbers)
print(list(taken))  # [1, 3]

# Drop while condition is true
dropped = itertools.dropwhile(lambda x: x < 5, numbers)
print(list(dropped))  # [5, 2, 4, 6, 8]


# =====================================================
# itertools.accumulate: Running totals
# =====================================================

numbers = [1, 2, 3, 4, 5]
running_sum = itertools.accumulate(numbers)
print(list(running_sum))  # [1, 3, 6, 10, 15]

# With custom function
running_max = itertools.accumulate(numbers, max)
print(list(running_max))  # [1, 2, 3, 4, 5]


# =====================================================
# itertools.product: Cartesian product
# =====================================================

colors = ['red', 'blue']
sizes = ['S', 'M', 'L']

for combo in itertools.product(colors, sizes):
    print(combo)
# ('red', 'S'), ('red', 'M'), ('red', 'L'),
# ('blue', 'S'), ('blue', 'M'), ('blue', 'L')


# =====================================================
# itertools.permutations / combinations
# =====================================================

items = [1, 2, 3]

# All orderings (permutations)
perms = itertools.permutations(items, 2)
print(list(perms))  # [(1,2), (1,3), (2,1), (2,3), (3,1), (3,2)]

# Unique selections (combinations) - order doesn't matter
combs = itertools.combinations(items, 2)
print(list(combs))  # [(1,2), (1,3), (2,3)]

# With replacement
combs_rep = itertools.combinations_with_replacement(items, 2)
print(list(combs_rep))  # [(1,1), (1,2), (1,3), (2,2), (2,3), (3,3)]


# =====================================================
# itertools.zip_longest: Zip with fill value
# =====================================================

a = [1, 2, 3]
b = [10, 20]

# Regular zip stops at shortest
print(list(zip(a, b)))  # [(1, 10), (2, 20)]

# zip_longest fills missing values
print(list(itertools.zip_longest(a, b, fillvalue=0)))
# [(1, 10), (2, 20), (3, 0)]


# =====================================================
# itertools.starmap: Apply function with unpacked args
# =====================================================

pairs = [(2, 3), (4, 5), (6, 7)]
products = itertools.starmap(lambda x, y: x * y, pairs)
print(list(products))  # [6, 20, 42]


# =====================================================
# itertools.tee: Create multiple independent iterators
# =====================================================

gen = (x**2 for x in range(5))
gen1, gen2, gen3 = itertools.tee(gen, 3)

print(list(gen1))  # [0, 1, 4, 9, 16]
print(list(gen2))  # [0, 1, 4, 9, 16]
print(list(gen3))  # [0, 1, 4, 9, 16]
```

---

### 2.3 Common Pitfalls by Language

#### Java Pitfalls
```java
// 1. Stream is single-use!
Stream<Integer> stream = numbers.stream();
stream.forEach(System.out::println);
// stream.count();  // IllegalStateException!

// 2. Iterator exhaustion
Iterator<Integer> it = list.iterator();
while (it.hasNext()) {
    System.out.println(it.next());
}
// Iterator is exhausted - can't reuse

// 3. ConcurrentModificationException
List<String> names = new ArrayList<>(Arrays.asList("a", "b", "c"));
for (String name : names) {
    names.remove(name);  // Exception!
}
// Fix: Use iterator.remove() or removeIf()
```

#### Python Pitfalls
```python
# 1. Generator exhaustion
gen = (x for x in range(5))
print(list(gen))  # [0, 1, 2, 3, 4]
print(list(gen))  # [] - exhausted!

# 2. Modifying while iterating
items = [1, 2, 3, 4, 5]
for item in items:
    if item % 2 == 0:
        items.remove(item)  # Skips elements!
# Fix: Iterate over copy or use comprehension
items = [x for x in items if x % 2 != 0]

# 3. Late binding in generator expressions
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])  # [2, 2, 2] not [0, 1, 2]!
# Fix: Capture value
funcs = [lambda i=i: i for i in range(3)]
```

#### TypeScript/JavaScript Pitfalls
```typescript
// 1. Generator exhaustion (same as Python)
function* gen() { yield 1; yield 2; }
const g = gen();
console.log([...g]);  // [1, 2]
console.log([...g]);  // [] - exhausted!

// 2. for...in vs for...of on arrays
const arr = [10, 20, 30];
for (const x in arr) console.log(x);    // "0", "1", "2" (indices!)
for (const x of arr) console.log(x);    // 10, 20, 30 (values!)

// 3. forEach doesn't work with async
async function wrong() {
    [1, 2, 3].forEach(async (n) => {
        await delay(n);
    });
    console.log("done");  // Prints before awaits complete!
}
// Fix: Use for...of
async function correct() {
    for (const n of [1, 2, 3]) {
        await delay(n);
    }
}
```

#### Go Pitfalls
```go
// 1. Loop variable capture in goroutines (fixed in Go 1.22)
for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i)  // All print 3!
    }()
}
// Fix (before Go 1.22): Pass as argument
for i := 0; i < 3; i++ {
    go func(n int) {
        fmt.Println(n)
    }(i)
}

// 2. range returns copy, not reference
type Item struct{ value int }
items := []Item{{1}, {2}}
for _, item := range items {
    item.value = 0  // Modifies copy!
}
// Fix: Use index
for i := range items {
    items[i].value = 0
}
```

#### Spark Pitfalls
```python
# 1. Forgetting laziness
df = spark.read.parquet("huge.parquet")
filtered = df.filter(col("x") > 0)
# Nothing happened yet!

# 2. Collecting large data
# result = df.collect()  # OOM if data is large!

# 3. Multiple actions re-compute
df2 = df.filter(col("x") > 0)
df2.count()    # Computes
df2.show()     # Computes AGAIN!
# Fix: df2.cache()

# 4. Closure serialization issues
counter = 0
df.foreach(lambda row: counter += row.x)  # counter stays 0!
# Use Accumulators instead
```

---

## 3. Design Philosophy Links

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| **Java** | [Java Collections Tutorial](https://docs.oracle.com/javase/tutorial/collections/) | Iterators |
| **Java** | [Stream API](https://docs.oracle.com/javase/8/docs/api/java/util/stream/package-summary.html) | Stream operations |
| **Python** | [Iterator Types](https://docs.python.org/3/library/stdtypes.html#iterator-types) | __iter__, __next__ |
| **Python** | [itertools](https://docs.python.org/3/library/itertools.html) | Efficient iterators |
| **Python** | [Generators](https://docs.python.org/3/tutorial/classes.html#generators) | yield, generator expressions |
| **TypeScript** | [Iteration Protocols](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols) | Symbol.iterator |
| **TypeScript** | [Generators](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*) | function* |
| **Go** | [Effective Go - For](https://go.dev/doc/effective_go#for) | range |
| **Go** | [Channels](https://go.dev/tour/concurrency/2) | Channel iteration |
| **C++** | [Iterators](https://en.cppreference.com/w/cpp/iterator) | Iterator concepts |
| **C++** | [Ranges (C++20)](https://en.cppreference.com/w/cpp/ranges) | Lazy ranges |
| **Spark** | [RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html) | Transformations vs Actions |

### Design Philosophy Quotes

> **Python**: "Generators are a simple and powerful tool for creating iterators."
> -- Python Tutorial

> **Java**: "A stream pipeline consists of a source, zero or more intermediate operations, and a terminal operation."
> -- Java Stream Documentation

> **Spark**: "Transformations are lazy; nothing happens until an action is called."
> -- Spark Programming Guide

---

## 4. Palantir Context Hint

### 4.1 Spark Lazy Transformations (THE Core Concept!)

```python
# Palantir heavily uses Spark for data processing
# Understanding lazy evaluation is ESSENTIAL for interviews

df = spark.read.parquet("s3://bucket/terabytes_of_data")

# TRANSFORMATION CHAIN (all lazy - no execution!)
result = (df
    .filter(col("status") == "active")      # lazy
    .withColumn("score", col("x") * 2)      # lazy
    .groupBy("category")                     # lazy
    .agg(spark_sum("score").alias("total")) # lazy
    .orderBy(col("total").desc())           # lazy
)

# ACTION (triggers execution of entire chain)
result.show()  # <-- This is where Spark actually works!

# INTERVIEW QUESTION: "When does Spark start processing?"
# ANSWER: Only when an ACTION is called (show, collect, count, write)
```

### 4.2 Python Generators for Memory Efficiency

```python
# Processing large datasets without loading all into memory

def process_large_file(filepath):
    """Generator-based file processing."""
    with open(filepath) as f:
        for line in f:  # File is iterable, reads one line at a time
            if is_valid(line):
                yield transform(line)

# Memory-efficient pipeline
def pipeline(filepath):
    records = process_large_file(filepath)
    filtered = (r for r in records if r['score'] > 50)
    transformed = (transform(r) for r in filtered)
    return transformed

# Only processes one record at a time!
for result in pipeline("huge_file.txt"):
    send_to_api(result)
```

### 4.3 Interview Questions (HIGHEST PRIORITY)

1. **"Implement a custom iterator in Python"**
```python
class CountDown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        self.current -= 1
        return self.current + 1

# Usage: for n in CountDown(5): print(n)  # 5, 4, 3, 2, 1
```

2. **"Generator vs list comprehension - when to use which?"**
```
Generator (x for x in ...):
- Large/infinite data sets
- When you don't need all results
- Memory-constrained environments
- Pipeline processing

List [x for x in ...]:
- Small data sets
- Need random access (list[i])
- Need to iterate multiple times
- Need length without consuming
```

3. **"Explain Spark lazy evaluation"**
```
Transformations: Build a DAG (plan), don't execute
  - map, filter, groupBy, select, join, etc.

Actions: Trigger execution of the DAG
  - collect, count, show, write, etc.

Benefits:
1. Catalyst optimizer optimizes entire pipeline
2. Predicate pushdown (filter early)
3. Column pruning (read only needed columns)
4. Avoid intermediate materialization
```

4. **"Java Stream: Why is it called 'lazy'?"**
```java
// Intermediate operations are lazy - they don't execute
// They just record WHAT to do (build a pipeline)
stream.filter(...).map(...).sorted(...)
// Nothing happens yet!

// Terminal operations trigger execution
stream.collect(...)  // NOW it runs

// Benefits:
// - Short-circuit: findFirst() stops at first match
// - Fusion: filter+map processed together per element
// - Single-pass: Data flows through pipeline once
```

5. **"What's the difference between Iterable and Iterator?"**
```
Iterable:
- Has iterator() method that returns an Iterator
- Can be iterated multiple times
- Example: List, Set, array

Iterator:
- Has next() and hasNext() methods
- Single-use (exhaustible)
- Tracks current position
- Example: The cursor returned by iterator()

Analogy:
- Iterable = Book (can be read many times)
- Iterator = Bookmark (current position, single journey)
```

---

## 5. Cross-References

### Related Knowledge Bases

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F31** | Loops & Iteration | Traditional iteration constructs |
| **F43** | Higher-Order Functions | map/filter/reduce on iterables |
| **F44** | Closures | Generators capture lexical scope |
| **F50** | Arrays & Lists | Sequence implementations |
| **F51** | Maps & Dictionaries | Key-value iteration |
| **F52** | Sets | Unordered iteration |
| **00d** | Async Basics | Async iterators, for await |

### Iteration Patterns Summary

| Pattern | Use Case | Example |
|---------|----------|---------|
| **Iterator** | Sequential access | for item in collection |
| **Generator** | Lazy production | yield values on demand |
| **Stream** | Functional pipeline | filter -> map -> collect |
| **Channel** | Concurrent iteration | Go channel range |
| **Cursor** | Database iteration | SQL FETCH (avoid!) |

---

## Quick Reference Card

```
+---------------------------------------------------------------------+
|                 ITERABLES & SEQUENCES CHEAT SHEET                    |
+---------------------------------------------------------------------+
|                                                                     |
| TERMINOLOGY:                                                        |
|   Iterable   = Can be looped (has __iter__ or [Symbol.iterator])   |
|   Iterator   = Cursor tracking position (has __next__ or next())   |
|   Sequence   = Indexed iterable (list, array, tuple)               |
|   Generator  = Lazy iterator created with yield                     |
|                                                                     |
+---------------------------------------------------------------------+
|                                                                     |
| ITERATOR PROTOCOL:                                                  |
|   Python:     __iter__() returns iterator, __next__() gets element |
|   Java:       iterator() returns Iterator, hasNext()/next()        |
|   TypeScript: [Symbol.iterator]() returns { next() }               |
|   C++:        begin()/end(), ++, *, !=                             |
|   Go:         Use channels or for range                            |
|                                                                     |
+---------------------------------------------------------------------+
|                                                                     |
| GENERATOR SYNTAX:                                                   |
|   Python:     def gen(): yield x                                   |
|   TypeScript: function* gen() { yield x; }                         |
|   Java:       N/A (use Stream.iterate/generate)                    |
|   C++:        co_yield (C++20 coroutines)                          |
|                                                                     |
+---------------------------------------------------------------------+
|                                                                     |
| LAZY vs EAGER:                                                      |
|   LAZY:  Python generators, Java Streams, Spark, C++20 ranges      |
|   EAGER: Python lists, JavaScript arrays, Java collections         |
|                                                                     |
+---------------------------------------------------------------------+
|                                                                     |
| SPARK CRITICAL (INTERVIEW!):                                        |
|   - Transformations are LAZY (map, filter, groupBy, join...)       |
|   - Actions TRIGGER execution (collect, count, show, write...)     |
|   - Use .cache() to avoid re-computation                           |
|   - NEVER .collect() large datasets!                               |
|                                                                     |
+---------------------------------------------------------------------+
|                                                                     |
| PYTHON itertools (INTERVIEW FAVORITES):                             |
|   chain()      - Concatenate iterables                             |
|   cycle()      - Infinite cycling                                  |
|   islice()     - Slice an iterator                                 |
|   groupby()    - Group consecutive (sort first!)                   |
|   product()    - Cartesian product                                 |
|   permutations() - All orderings                                   |
|   combinations() - Unique selections                               |
|                                                                     |
+---------------------------------------------------------------------+
|                                                                     |
| COMMON PITFALLS:                                                    |
|   1. Generator exhaustion - can only iterate once!                 |
|   2. Modifying collection while iterating                          |
|   3. Java Stream single-use (IllegalStateException)                |
|   4. Late binding in closures (capture loop variable)              |
|   5. Spark: forgetting laziness, multiple actions = re-compute     |
|                                                                     |
+---------------------------------------------------------------------+
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
