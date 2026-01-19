# F44: Closures (Closures)

> **Concept ID**: F44_closures
> **Category**: Functions & Control Flow
> **Difficulty**: Intermediate -> Advanced
> **Interview Frequency**: (Critical in all languages)
> **Universal Principle**: A function bundled together with references to its surrounding state (lexical environment)
> **Prerequisites**: F10_lexical_scope, F11_closure_capture, F40_function_first_class

---

## Section 1: Universal Concept

### 1.1 What is a Closure?

A **closure** is a function that "remembers" the environment in which it was created. More precisely, a closure is a function combined with its **lexical environment** - the set of variables that were in scope at the time the function was defined.

```
+----------------------------------------------------------+
|                    CLOSURE MENTAL MODEL                   |
+----------------------------------------------------------+
|                                                          |
|   function outer() {                                     |
|       let secret = 42;        <-- Free variable          |
|                                                          |
|       return function inner() {  <-- Closure             |
|           return secret;      <-- Captures 'secret'      |
|       }                                                  |
|   }                                                      |
|                                                          |
|   const fn = outer();  // outer() returns inner          |
|   fn();  // 42 -- inner still has access to 'secret'!    |
|                                                          |
+----------------------------------------------------------+
|                                                          |
|   Think of a closure as a FUNCTION WITH A BACKPACK:      |
|   - The function is the "worker"                         |
|   - The backpack contains all the variables it needs     |
|   - Wherever the function goes, the backpack goes too    |
|   - Even after outer() finishes, the backpack persists   |
|                                                          |
+----------------------------------------------------------+
```

### 1.2 Key Terminology

| Term | Definition |
|------|------------|
| **Free Variable** | A variable used in a function but defined outside of it |
| **Bound Variable** | A variable defined within the function (parameters, locals) |
| **Lexical Environment** | The set of variable bindings available at a code location |
| **Capture** | The process of a closure "remembering" free variables |
| **Late Binding** | Variable value determined at call time (not definition time) |

### 1.3 Why Closures Matter

Closures enable powerful programming patterns:

1. **Data Privacy / Encapsulation**
   - Create private variables without classes
   - Module pattern in JavaScript
   - Factory functions

2. **State Preservation**
   - Remember state between function calls
   - Implement counters, accumulators
   - Memoization

3. **Callbacks & Event Handlers**
   - Pass context to async operations
   - Event listeners with access to outer scope

4. **Partial Application & Currying**
   - Create specialized versions of functions
   - Functional programming patterns

5. **Higher-Order Functions**
   - map, filter, reduce all rely on closures
   - Custom iterators

### 1.4 Common Interview Use Cases

```
[Closure Applications in Interviews]

1. Private Counter Pattern
   - Implement a counter with increment/decrement/get
   - No direct access to count variable

2. Event Handler with Context
   - Button click handlers that remember button ID

3. Loop Closure Bug
   - "Fix this code that prints 5,5,5,5,5"
   - var vs let in loops

4. Factory Functions
   - Create multiple similar functions with different configs

5. Memoization
   - Cache function results using closure
```

---

## Section 2: Semantic Comparison Matrix

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Closure Support** | Lambda (Java 8+) | Native (first-class) | Native (first-class) | Native (anonymous func) | N/A (procedural) | Lambda (C++11+) | Lambda (serialize!) |
| **Capture Mode** | By value (effectively final) | By reference | By reference | By reference | - | Explicit [=]/[&] | By reference (serialized) |
| **Mutable Capture** | No (effectively final) | `nonlocal` keyword | Yes | Yes | - | `mutable` keyword | No (use broadcast) |
| **Memory Concern** | GC handles | GC handles | GC handles | GC handles | - | Manual / RAII | Serialization cost! |
| **Late Binding** | No (value copy) | Yes (reference) | Yes (reference) | Yes (pointer) | - | [&] only | Yes |
| **Loop Capture Bug** | Safe (value copy) | Dangerous | var: Bug / let: Safe | Dangerous (<1.22) | - | [&]: Dangerous | Dangerous |
| **Common Pitfall** | effectively final error | Late binding trap | var loop closure | goroutine capture | - | Dangling reference | NotSerializableException |

### 2.2 Detailed Code Examples by Language

---

#### 2.2.1 Basic Closure Pattern (All Languages)

**Java - Lambda with Effectively Final**
```java
import java.util.function.Supplier;

public class ClosureDemo {
    public static Supplier<Integer> createCounter(int start) {
        // 'start' must be effectively final
        final int initial = start;  // or just use 'start' directly

        // This lambda captures 'initial'
        return () -> initial;
    }

    public static void main(String[] args) {
        Supplier<Integer> counter = createCounter(10);
        System.out.println(counter.get());  // 10
    }
}

// WHY effectively final?
// Java lambdas capture VALUES, not references
// This prevents race conditions in concurrent code
// If you need mutable state, use AtomicInteger or array wrapper

import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.IntSupplier;

public class MutableCounter {
    public static IntSupplier createMutableCounter(int start) {
        // Workaround: wrap in mutable container
        AtomicInteger count = new AtomicInteger(start);

        return () -> count.incrementAndGet();
    }

    public static void main(String[] args) {
        IntSupplier counter = createMutableCounter(0);
        System.out.println(counter.getAsInt());  // 1
        System.out.println(counter.getAsInt());  // 2
        System.out.println(counter.getAsInt());  // 3
    }
}

// Alternative: int[] wrapper
public static IntSupplier counterWithArray(int start) {
    int[] count = {start};  // Array is mutable!
    return () -> ++count[0];
}
```

**Python - Native Closures with nonlocal**
```python
def create_counter(start: int):
    """Creates a counter closure with increment/get operations."""
    count = start  # Free variable captured by closure

    def increment():
        nonlocal count  # Required to modify outer variable!
        count += 1
        return count

    def get():
        return count  # Read-only access doesn't need nonlocal

    return increment, get

# Usage
inc, get = create_counter(0)
print(get())  # 0
print(inc())  # 1
print(inc())  # 2
print(get())  # 2

# WITHOUT nonlocal - common mistake!
def broken_counter():
    count = 0

    def increment():
        # count += 1  # UnboundLocalError: referenced before assignment
        # Python sees 'count =' and assumes it's local!
        pass

    return increment


# Factory pattern with closure
def make_multiplier(factor: int):
    """Returns a function that multiplies by factor."""
    def multiplier(x):
        return x * factor  # Captures 'factor'
    return multiplier

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))  # 10
print(triple(5))  # 15
```

**TypeScript - Full Closure Support**
```typescript
// Basic closure
function createCounter(start: number): () => number {
    let count = start;  // Captured by closure

    return () => {
        count += 1;
        return count;
    };
}

const counter = createCounter(0);
console.log(counter());  // 1
console.log(counter());  // 2
console.log(counter());  // 3

// Module pattern - data privacy
function createBankAccount(initialBalance: number) {
    let balance = initialBalance;  // Private!

    return {
        deposit(amount: number): number {
            balance += amount;
            return balance;
        },
        withdraw(amount: number): number | null {
            if (amount > balance) return null;
            balance -= amount;
            return balance;
        },
        getBalance(): number {
            return balance;
        }
        // Note: 'balance' is NOT exposed directly
    };
}

const account = createBankAccount(100);
console.log(account.getBalance());  // 100
console.log(account.deposit(50));   // 150
console.log(account.withdraw(30));  // 120
// account.balance = 1000000;  // Error! Property doesn't exist


// Arrow function closure
const makeAdder = (x: number) => (y: number) => x + y;

const add5 = makeAdder(5);
const add10 = makeAdder(10);

console.log(add5(3));   // 8
console.log(add10(3));  // 13
```

**Go - Closure with Anonymous Functions**
```go
package main

import "fmt"

// Basic closure - returns a function that increments and returns count
func createCounter(start int) func() int {
    count := start  // Captured by closure

    return func() int {
        count++  // Modifies captured variable
        return count
    }
}

func main() {
    counter := createCounter(0)
    fmt.Println(counter())  // 1
    fmt.Println(counter())  // 2
    fmt.Println(counter())  // 3

    // Each call to createCounter creates a new closure
    counter2 := createCounter(100)
    fmt.Println(counter2())  // 101
    fmt.Println(counter())   // 4 (original counter continues)
}

// Multiple closures sharing state
func createCounterPair(start int) (func() int, func() int) {
    count := start

    increment := func() int {
        count++
        return count
    }

    decrement := func() int {
        count--
        return count
    }

    return increment, decrement
}

func main2() {
    inc, dec := createCounterPair(10)
    fmt.Println(inc())  // 11
    fmt.Println(inc())  // 12
    fmt.Println(dec())  // 11
    fmt.Println(dec())  // 10
}

// Closure for configuration
func makeGreeter(greeting string) func(string) string {
    return func(name string) string {
        return fmt.Sprintf("%s, %s!", greeting, name)
    }
}

func main3() {
    sayHello := makeGreeter("Hello")
    sayHi := makeGreeter("Hi")

    fmt.Println(sayHello("Alice"))  // "Hello, Alice!"
    fmt.Println(sayHi("Bob"))       // "Hi, Bob!"
}
```

**C++ - Explicit Lambda Capture**
```cpp
#include <iostream>
#include <functional>
#include <string>

// C++ requires EXPLICIT capture specification!

int main() {
    int count = 0;

    // [=] capture by value (copy)
    auto byValue = [=]() {
        // count++;  // Error! captured by value is const
        return count;
    };

    // [&] capture by reference
    auto byRef = [&]() {
        count++;  // OK - modifying original
        return count;
    };

    // [=] mutable - allows modification of the COPY
    auto byValueMutable = [=]() mutable {
        count++;  // Modifies the copy, not original
        return count;
    };

    std::cout << byRef() << std::endl;  // 1 (original modified)
    std::cout << byRef() << std::endl;  // 2
    std::cout << count << std::endl;     // 2 (count was modified)

    std::cout << byValueMutable() << std::endl;  // 1 (copy starts at 0)
    std::cout << byValueMutable() << std::endl;  // 1 (each call gets fresh copy!)
    std::cout << count << std::endl;              // 2 (original unchanged)

    return 0;
}

// Capture modes in detail
void captureExamples() {
    int x = 10;
    int y = 20;

    // Specific variable capture
    auto f1 = [x]() { return x; };        // Capture x by value
    auto f2 = [&x]() { return x; };       // Capture x by reference
    auto f3 = [x, &y]() { return x + y; }; // Mixed capture

    // Capture all
    auto f4 = [=]() { return x + y; };    // All by value
    auto f5 = [&]() { return x + y; };    // All by reference
    auto f6 = [=, &x]() { return x + y; }; // All by value, x by reference

    // Capture 'this' in member functions
    // [this] - capture this pointer
    // [*this] - capture copy of object (C++17)
}

// Counter factory
std::function<int()> createCounter(int start) {
    int count = start;

    // Must capture by value with mutable for persistent state
    return [count]() mutable {
        return ++count;
    };
}

// DANGER: Dangling reference!
std::function<int()> dangerous() {
    int local = 42;
    return [&local]() { return local; };  // local destroyed after return!
    // This is UNDEFINED BEHAVIOR
}
```

**Spark - Closure Serialization (CRITICAL INTERVIEW TOPIC!)**
```python
from pyspark.sql import SparkSession
from pyspark import SparkContext

spark = SparkSession.builder.getOrCreate()
sc = spark.sparkContext

# PROBLEM 1: Counter doesn't work as expected
# This is the #1 Spark closure interview question!

counter = 0
rdd = sc.parallelize([1, 2, 3, 4, 5])

def increment_counter(x):
    global counter
    counter += 1  # This modifies EXECUTOR's copy, not driver's!
    return x * 2

rdd.map(increment_counter).collect()
print(counter)  # Still 0! WHY?

"""
EXPLANATION:
1. Spark serializes the closure (including 'counter' reference)
2. Each executor gets its OWN copy of counter
3. Executors modify their local copies
4. Driver's counter is never modified
5. This is NOT a bug - it's distributed computing!

Diagram:
+--------+                 +------------+
| Driver |  serialize -->  | Executor 1 |  counter = 0 -> 1 -> 2
| counter=0               +------------+
|        |  serialize -->  | Executor 2 |  counter = 0 -> 1 -> 2
+--------+                 +------------+
    ^
    |
    counter is still 0!
"""

# SOLUTION: Use Accumulator
accumulator_counter = sc.accumulator(0)

def increment_with_accumulator(x):
    accumulator_counter.add(1)
    return x * 2

rdd.map(increment_with_accumulator).collect()
print(accumulator_counter.value)  # 5 (correct!)


# PROBLEM 2: NotSerializableException
# Closure captures non-serializable object

class DatabaseConnection:
    def __init__(self):
        self.connection = "connected"  # Imagine actual DB connection

    def query(self, x):
        return f"result: {x}"

db = DatabaseConnection()

# This will FAIL!
# rdd.map(lambda x: db.query(x)).collect()
# Error: NotSerializableException

# SOLUTION 1: Create connection inside worker
def query_in_worker(x):
    # Create connection inside the function (per-partition is better)
    local_db = DatabaseConnection()
    return local_db.query(x)

rdd.map(query_in_worker).collect()

# SOLUTION 2: Use mapPartitions for efficiency
def query_partition(partition):
    db = DatabaseConnection()  # One connection per partition
    for x in partition:
        yield db.query(x)

rdd.mapPartitions(query_partition).collect()

# SOLUTION 3: Broadcast for read-only data
config = {"multiplier": 2, "offset": 10}
broadcast_config = sc.broadcast(config)

def use_broadcast(x):
    c = broadcast_config.value
    return x * c["multiplier"] + c["offset"]

rdd.map(use_broadcast).collect()  # Works!


# PROBLEM 3: DataFrame closure with UDF
from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType

external_factor = 10

@udf(returnType=IntegerType())
def multiply(x):
    return x * external_factor  # Captures external_factor

df = spark.createDataFrame([(1,), (2,), (3,)], ["value"])
# df.withColumn("result", multiply("value")).show()
# This might work but external_factor is serialized!

# If external_factor changes after UDF definition, the UDF still uses old value
external_factor = 100
# UDF still uses 10, not 100!
```

**SQL - No Closures (Set-Based)**
```sql
-- SQL is declarative and set-based, not procedural
-- No closures in traditional SQL

-- The closest concept is correlated subquery
-- which can reference outer query's columns

SELECT e.name, e.department,
       (SELECT AVG(salary)
        FROM employees e2
        WHERE e2.department = e.department) as dept_avg  -- References outer e
FROM employees e;

-- Common Table Expressions (CTEs) provide reusable query blocks
-- but they're not closures in the functional sense

WITH dept_stats AS (
    SELECT department, AVG(salary) as avg_salary
    FROM employees
    GROUP BY department
)
SELECT e.name, d.avg_salary
FROM employees e
JOIN dept_stats d ON e.department = d.department;

-- Stored procedures/functions in procedural SQL extensions
-- (PL/SQL, T-SQL) have some closure-like behavior

-- Oracle PL/SQL example:
CREATE OR REPLACE FUNCTION make_multiplier(factor NUMBER)
RETURN SYS_REFCURSOR
IS
    result_cursor SYS_REFCURSOR;
BEGIN
    -- Not a true closure, but captures 'factor'
    OPEN result_cursor FOR
        SELECT value * factor AS result FROM numbers_table;
    RETURN result_cursor;
END;
```

---

#### 2.2.2 Loop Closure Bug (CRITICAL INTERVIEW TOPIC!)

**TypeScript/JavaScript - var vs let**
```typescript
// THE CLASSIC CLOSURE BUG - var in loop
console.log("Bug with var:");
for (var i = 0; i < 5; i++) {
    setTimeout(() => {
        console.log(i);  // What prints?
    }, 100);
}
// Output: 5, 5, 5, 5, 5
// WHY? 'var' is function-scoped, all closures share the SAME 'i'
// By the time setTimeout fires, loop has finished, i = 5

/*
Timeline:
t=0: Loop iteration 0, schedule setTimeout, i=0
t=0: Loop iteration 1, schedule setTimeout, i=1
t=0: Loop iteration 2, schedule setTimeout, i=2
t=0: Loop iteration 3, schedule setTimeout, i=3
t=0: Loop iteration 4, schedule setTimeout, i=4
t=0: Loop completes, i=5

t=100: All 5 setTimeouts fire, all read i, i is now 5
Output: 5, 5, 5, 5, 5
*/


// SOLUTION 1: Use 'let' (block-scoped)
console.log("\nFix with let:");
for (let i = 0; i < 5; i++) {
    setTimeout(() => {
        console.log(i);  // 0, 1, 2, 3, 4
    }, 100);
}
// 'let' creates a NEW binding for EACH iteration
// Each closure captures a different 'i'


// SOLUTION 2: IIFE (Immediately Invoked Function Expression)
console.log("\nFix with IIFE:");
for (var i = 0; i < 5; i++) {
    ((capturedI) => {
        setTimeout(() => {
            console.log(capturedI);  // 0, 1, 2, 3, 4
        }, 100);
    })(i);  // Pass current 'i' as argument, creating new binding
}


// SOLUTION 3: bind or closure factory
console.log("\nFix with closure factory:");
function createPrinter(value: number) {
    return () => console.log(value);
}

for (var i = 0; i < 5; i++) {
    setTimeout(createPrinter(i), 100);  // 0, 1, 2, 3, 4
}


// INTERVIEW VARIATION: forEach vs for...of
const arr = [10, 20, 30];

// forEach - callback gets its own scope
arr.forEach((val, idx) => {
    setTimeout(() => console.log(val), 100);  // 10, 20, 30 (correct)
});

// for...of with let - also safe
for (const val of arr) {
    setTimeout(() => console.log(val), 100);  // 10, 20, 30
}
```

**Python - Late Binding Trap**
```python
# CLASSIC PYTHON CLOSURE BUG
print("Bug - all functions return 4:")
functions = []
for i in range(5):
    functions.append(lambda: i)

for f in functions:
    print(f())  # 4, 4, 4, 4, 4

# WHY? Python closures capture by REFERENCE
# When lambdas execute, they look up 'i' in enclosing scope
# By then, i = 4 (last value from loop)


# SOLUTION 1: Default argument (captures current value)
print("\nFix with default argument:")
functions = []
for i in range(5):
    functions.append(lambda x=i: x)  # x=i captures current value!

for f in functions:
    print(f())  # 0, 1, 2, 3, 4


# SOLUTION 2: Closure factory
print("\nFix with factory:")
def make_func(val):
    return lambda: val

functions = [make_func(i) for i in range(5)]
for f in functions:
    print(f())  # 0, 1, 2, 3, 4


# SOLUTION 3: functools.partial
from functools import partial

print("\nFix with partial:")
def return_value(x):
    return x

functions = [partial(return_value, i) for i in range(5)]
for f in functions:
    print(f())  # 0, 1, 2, 3, 4


# REAL INTERVIEW SCENARIO: Button handlers
class Button:
    def __init__(self, name):
        self.name = name
        self.on_click = None

# Bug: All buttons print "Button 4 clicked"
buttons = []
for i in range(5):
    btn = Button(f"Button {i}")
    btn.on_click = lambda: print(f"Button {i} clicked")  # Bug!
    buttons.append(btn)

# Fix: Capture value
buttons = []
for i in range(5):
    btn = Button(f"Button {i}")
    btn.on_click = lambda idx=i: print(f"Button {idx} clicked")  # Fixed!
    buttons.append(btn)

# Simulate clicks
for btn in buttons:
    btn.on_click()  # Button 0 clicked, Button 1 clicked, ...
```

**Go - Goroutine Closure Capture**
```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    // BUG: All goroutines print the same value
    fmt.Println("Bug - unpredictable output:")
    for i := 0; i < 5; i++ {
        go func() {
            fmt.Println(i)  // Race condition + same variable
        }()
    }
    time.Sleep(100 * time.Millisecond)
    // Output might be: 5, 5, 5, 5, 5 (or other combinations)

    // WHY?
    // 1. All goroutines capture the SAME 'i' variable
    // 2. By the time goroutines run, loop may have finished
    // 3. Race condition: goroutines reading while main modifies


    // SOLUTION 1: Pass as argument
    fmt.Println("\nFix with argument:")
    for i := 0; i < 5; i++ {
        go func(n int) {  // n is a NEW variable for each goroutine
            fmt.Println(n)
        }(i)  // Pass current i value
    }
    time.Sleep(100 * time.Millisecond)  // 0, 1, 2, 3, 4 (order may vary)


    // SOLUTION 2: Create local copy
    fmt.Println("\nFix with local copy:")
    for i := 0; i < 5; i++ {
        i := i  // Shadow 'i' with new local variable!
        go func() {
            fmt.Println(i)
        }()
    }
    time.Sleep(100 * time.Millisecond)


    // Go 1.22+ AUTOMATIC FIX
    // Starting Go 1.22, loop variables have per-iteration scope
    // The bug above is automatically fixed in Go 1.22+
    // But always be explicit for backwards compatibility!


    // BEST PRACTICE: Use WaitGroup for proper synchronization
    fmt.Println("\nProper synchronization:")
    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            fmt.Println(n)
        }(i)
    }
    wg.Wait()  // Wait for all goroutines to complete
}

// Pointer capture bug
func pointerBug() {
    var pointers []*int

    for i := 0; i < 5; i++ {
        pointers = append(pointers, &i)  // All point to same address!
    }

    for _, p := range pointers {
        fmt.Println(*p)  // 5, 5, 5, 5, 5
    }

    // Fix: Create local copy
    var fixedPointers []*int
    for i := 0; i < 5; i++ {
        v := i  // New variable each iteration
        fixedPointers = append(fixedPointers, &v)
    }

    for _, p := range fixedPointers {
        fmt.Println(*p)  // 0, 1, 2, 3, 4
    }
}
```

**C++ - Reference Capture Danger**
```cpp
#include <iostream>
#include <vector>
#include <functional>
#include <thread>

int main() {
    // BUG: Capturing loop variable by reference
    std::vector<std::function<void()>> funcs;

    for (int i = 0; i < 5; i++) {
        funcs.push_back([&i]() {  // Capture by reference
            std::cout << i << std::endl;
        });
    }

    // By now, loop has ended, 'i' is out of scope!
    // This is UNDEFINED BEHAVIOR
    for (auto& f : funcs) {
        f();  // Undefined! 'i' no longer exists
    }


    // SOLUTION 1: Capture by value
    std::vector<std::function<void()>> fixedFuncs;
    for (int i = 0; i < 5; i++) {
        fixedFuncs.push_back([i]() {  // Capture by value (copy)
            std::cout << i << std::endl;
        });
    }

    for (auto& f : fixedFuncs) {
        f();  // 0, 1, 2, 3, 4 (correct)
    }


    // SOLUTION 2: With threads - pass by value
    std::vector<std::thread> threads;
    for (int i = 0; i < 5; i++) {
        threads.emplace_back([i]() {
            std::cout << i << std::endl;
        });
    }

    for (auto& t : threads) {
        t.join();
    }

    return 0;
}

// Dangling reference example
std::function<int()> createDangerous() {
    int local = 42;
    return [&local]() {  // DANGER: local destroyed after return
        return local;
    };
}
// Calling the returned function = UNDEFINED BEHAVIOR
```

---

#### 2.2.3 Counter/Factory Pattern

**Private Counter with Closures**

```typescript
// TypeScript - Private counter
function createCounter() {
    let count = 0;  // Private!

    return {
        increment(): number { return ++count; },
        decrement(): number { return --count; },
        get(): number { return count; },
        reset(): void { count = 0; }
    };
}

const counter = createCounter();
console.log(counter.get());       // 0
console.log(counter.increment()); // 1
console.log(counter.increment()); // 2
console.log(counter.decrement()); // 1
counter.reset();
console.log(counter.get());       // 0
// console.log(counter.count);    // Error! 'count' is not accessible
```

```python
# Python - Private counter
def create_counter():
    count = 0

    def increment():
        nonlocal count
        count += 1
        return count

    def decrement():
        nonlocal count
        count -= 1
        return count

    def get():
        return count

    def reset():
        nonlocal count
        count = 0

    return {
        'increment': increment,
        'decrement': decrement,
        'get': get,
        'reset': reset
    }

counter = create_counter()
print(counter['get']())        # 0
print(counter['increment']())  # 1
print(counter['increment']())  # 2
print(counter['decrement']())  # 1
counter['reset']()
print(counter['get']())        # 0
```

```java
// Java - Counter with AtomicInteger wrapper
import java.util.function.IntSupplier;
import java.util.function.IntConsumer;
import java.util.concurrent.atomic.AtomicInteger;

public class CounterFactory {
    public record Counter(
        IntSupplier get,
        IntSupplier increment,
        IntSupplier decrement,
        Runnable reset
    ) {}

    public static Counter createCounter() {
        AtomicInteger count = new AtomicInteger(0);

        return new Counter(
            count::get,
            count::incrementAndGet,
            count::decrementAndGet,
            () -> count.set(0)
        );
    }

    public static void main(String[] args) {
        Counter counter = createCounter();
        System.out.println(counter.get().getAsInt());       // 0
        System.out.println(counter.increment().getAsInt()); // 1
        System.out.println(counter.increment().getAsInt()); // 2
        System.out.println(counter.decrement().getAsInt()); // 1
        counter.reset().run();
        System.out.println(counter.get().getAsInt());       // 0
    }
}
```

```go
// Go - Counter struct with closure
package main

import "fmt"

type Counter struct {
    Increment func() int
    Decrement func() int
    Get       func() int
    Reset     func()
}

func NewCounter() Counter {
    count := 0

    return Counter{
        Increment: func() int { count++; return count },
        Decrement: func() int { count--; return count },
        Get:       func() int { return count },
        Reset:     func() { count = 0 },
    }
}

func main() {
    counter := NewCounter()
    fmt.Println(counter.Get())       // 0
    fmt.Println(counter.Increment()) // 1
    fmt.Println(counter.Increment()) // 2
    fmt.Println(counter.Decrement()) // 1
    counter.Reset()
    fmt.Println(counter.Get())       // 0
}
```

```cpp
// C++ - Counter with lambda
#include <iostream>
#include <functional>

struct Counter {
    std::function<int()> increment;
    std::function<int()> decrement;
    std::function<int()> get;
    std::function<void()> reset;
};

Counter createCounter() {
    auto count = std::make_shared<int>(0);  // Shared ownership

    return Counter{
        [count]() { return ++(*count); },
        [count]() { return --(*count); },
        [count]() { return *count; },
        [count]() { *count = 0; }
    };
}

int main() {
    auto counter = createCounter();
    std::cout << counter.get() << std::endl;       // 0
    std::cout << counter.increment() << std::endl; // 1
    std::cout << counter.increment() << std::endl; // 2
    std::cout << counter.decrement() << std::endl; // 1
    counter.reset();
    std::cout << counter.get() << std::endl;       // 0
    return 0;
}
```

---

#### 2.2.4 C++ Lambda Capture Modes (Comprehensive)

```cpp
#include <iostream>
#include <vector>
#include <functional>

class Example {
    int member = 100;

public:
    void demonstrateCaptureOptions() {
        int x = 10;
        int y = 20;
        int z = 30;

        // [=] : Capture all by value (copy)
        auto f1 = [=]() {
            std::cout << x << ", " << y << ", " << z << std::endl;
            // x = 5;  // Error! Cannot modify (unless mutable)
        };

        // [&] : Capture all by reference
        auto f2 = [&]() {
            x = 100;  // Modifies original!
            std::cout << x << ", " << y << ", " << z << std::endl;
        };

        // [x] : Capture x by value only
        auto f3 = [x]() {
            std::cout << x << std::endl;
            // std::cout << y << std::endl;  // Error! y not captured
        };

        // [&x] : Capture x by reference only
        auto f4 = [&x]() {
            x = 200;  // Modifies original x
        };

        // [x, &y] : Mixed - x by value, y by reference
        auto f5 = [x, &y]() {
            y = x + 10;  // y modified, x is just read
        };

        // [=, &x] : All by value, except x by reference
        auto f6 = [=, &x]() {
            x = y + z;  // y, z are copies; x is reference
        };

        // [&, x] : All by reference, except x by value
        auto f7 = [&, x]() {
            y = x;  // y is reference, x is copy
        };

        // [this] : Capture this pointer (access member variables)
        auto f8 = [this]() {
            std::cout << member << std::endl;  // Access through this->
            member = 50;  // Can modify!
        };

        // [*this] : Capture copy of *this (C++17)
        auto f9 = [*this]() {
            std::cout << member << std::endl;  // Copy of object
            // member = 50;  // Modifies the copy, not original
        };

        // [=] mutable : Capture by value but allow modification of copies
        auto f10 = [=]() mutable {
            x = 500;  // Modifies the copy!
            std::cout << x << std::endl;  // 500
        };
        // Original x unchanged

        // Init capture (C++14) - create new variables in capture
        auto f11 = [val = x * 2]() {
            std::cout << val << std::endl;  // 20 (x was 10)
        };

        // Move capture (C++14)
        std::vector<int> vec = {1, 2, 3};
        auto f12 = [v = std::move(vec)]() {
            // v is moved into the lambda
            for (int i : v) std::cout << i << " ";
        };
        // vec is now empty!
    }
};

// INTERVIEW QUESTION: What's the difference between [=] and [&]?
/*
[=] by value:
- Creates COPIES of all captured variables
- Safe if lambda outlives the scope
- Cannot modify originals (unless mutable)
- Higher memory usage (copies)

[&] by reference:
- Captures REFERENCES to all variables
- Dangerous if lambda outlives the scope (dangling reference!)
- Can modify original variables
- Lower memory usage

RULE OF THUMB:
- Use [=] for lambdas that might outlive current scope (callbacks, async)
- Use [&] for short-lived lambdas in same scope (algorithms, local processing)
- Be explicit when possible: [x, &y] instead of [=, &y]
*/
```

---

#### 2.2.5 Java "Effectively Final" Deep Dive

```java
import java.util.function.*;
import java.util.concurrent.atomic.*;
import java.util.*;

public class EffectivelyFinalDemo {

    public static void main(String[] args) {
        // What is "effectively final"?
        // A variable that is NEVER modified after initialization

        int x = 10;
        // x = 20;  // If uncommented, x is NOT effectively final

        // Lambda can capture effectively final variables
        Runnable r = () -> System.out.println(x);  // OK

        int y = 10;
        y = 20;  // y is modified!
        // Runnable r2 = () -> System.out.println(y);  // COMPILE ERROR!
        // "Local variable y defined in an enclosing scope must be final or effectively final"


        // WHY does Java require effectively final?
        /*
        1. THREAD SAFETY: Lambdas may run on different threads
           - If the variable could change, race conditions occur
           - By capturing VALUE (not reference), each lambda has its own copy

        2. CLOSURE SEMANTICS: Java chose "snapshot" semantics
           - Lambda captures the VALUE at creation time
           - Not the variable itself

        3. PREDICTABILITY: Behavior is deterministic
           - No surprise mutations from outside
        */


        // WORKAROUNDS for mutable state:

        // 1. AtomicInteger (thread-safe counter)
        AtomicInteger counter = new AtomicInteger(0);
        Runnable inc = () -> counter.incrementAndGet();

        // 2. Single-element array (hacky but works)
        int[] holder = {0};
        Runnable inc2 = () -> holder[0]++;

        // 3. AtomicReference for objects
        AtomicReference<String> message = new AtomicReference<>("Hello");
        Runnable update = () -> message.set("World");

        // 4. Mutable wrapper class
        class Wrapper<T> {
            T value;
            Wrapper(T value) { this.value = value; }
        }
        Wrapper<Integer> wrapper = new Wrapper<>(0);
        Runnable inc3 = () -> wrapper.value++;


        // INTERVIEW QUESTION: Why doesn't this compile?
        List<String> names = new ArrayList<>();
        names.add("Alice");
        // names = new ArrayList<>();  // If uncommented, error below!

        Consumer<String> addName = name -> names.add(name);  // OK
        // The REFERENCE 'names' is effectively final
        // The CONTENTS of the list can change!


        // This is a common source of confusion:
        final List<String> finalList = new ArrayList<>();
        finalList.add("Can");    // OK - modifying contents
        finalList.add("Add");    // OK
        finalList.clear();       // OK
        // finalList = new ArrayList<>();  // ERROR - can't reassign reference


        // LOOP VARIABLES are never effectively final
        // for (int i = 0; i < 5; i++) {
        //     Runnable r = () -> System.out.println(i);  // ERROR!
        // }
        // i changes each iteration, so it's not effectively final

        // Solution: create a new final variable each iteration
        for (int i = 0; i < 5; i++) {
            final int captured = i;  // New variable each iteration
            Runnable r3 = () -> System.out.println(captured);
        }
    }
}
```

---

### 2.3 Spark Closure Serialization (Interview Deep Dive)

```python
"""
SPARK CLOSURE SERIALIZATION - THE #1 PALANTIR/SPARK INTERVIEW TOPIC

Understanding this is CRITICAL for any Spark interview.
"""

from pyspark.sql import SparkSession
from pyspark import SparkContext
import pickle

spark = SparkSession.builder.appName("ClosureDemo").getOrCreate()
sc = spark.sparkContext


# === UNDERSTANDING THE PROBLEM ===

"""
When you use a closure in Spark:

1. Your code runs on the DRIVER
2. Spark needs to send the closure to EXECUTORS (worker nodes)
3. Spark SERIALIZES the closure (converts to bytes)
4. Closure is deserialized on each executor
5. Executor runs the closure

PROBLEM: What if the closure captures something that can't be serialized?
"""

# Example 1: This works (primitives are serializable)
multiplier = 2
rdd = sc.parallelize([1, 2, 3, 4, 5])
result = rdd.map(lambda x: x * multiplier).collect()
print(result)  # [2, 4, 6, 8, 10]


# Example 2: This FAILS (database connections are not serializable)
class DatabaseConnection:
    def __init__(self):
        # Imagine this opens a real database connection
        self.socket = "Some non-serializable connection"

    def query(self, x):
        return f"Result for {x}"

db = DatabaseConnection()

# This will raise: PicklingError or NotSerializableException
# rdd.map(lambda x: db.query(x)).collect()  # FAILS!

"""
WHY?
- 'db' is captured by the lambda
- Spark tries to serialize the entire lambda including 'db'
- Database connections have sockets, file handles, etc.
- These can't be serialized!
"""


# === SOLUTIONS ===

# Solution 1: Create connection INSIDE the worker function
def process_inside(x):
    # Connection created on executor, not driver
    local_db = DatabaseConnection()
    return local_db.query(x)

result = rdd.map(process_inside).collect()
print(result)

# Problem: Creates connection for EVERY element (inefficient!)


# Solution 2: mapPartitions - one connection per partition
def process_partition(partition):
    db = DatabaseConnection()  # One connection for the whole partition
    for x in partition:
        yield db.query(x)

result = rdd.mapPartitions(process_partition).collect()
print(result)

# Much better! Only N connections where N = number of partitions


# Solution 3: Broadcast for read-only configuration
config = {
    "multiplier": 2,
    "offset": 10,
    "description": "Some config"
}

# Broadcast efficiently distributes to all executors ONCE
broadcast_config = sc.broadcast(config)

def use_config(x):
    c = broadcast_config.value  # Access broadcast value
    return x * c["multiplier"] + c["offset"]

result = rdd.map(use_config).collect()
print(result)  # [12, 14, 16, 18, 20]

# Why broadcast?
# - Without broadcast: config serialized with EVERY task
# - With broadcast: config sent to each executor ONCE
# - Huge savings for large configs or many tasks!


# Solution 4: Accumulator for aggregation (write-only from executors)
total = sc.accumulator(0)
count = sc.accumulator(0)

def process_with_accumulator(x):
    total.add(x)
    count.add(1)
    return x * 2

result = rdd.map(process_with_accumulator).collect()
print(f"Total: {total.value}, Count: {count.value}")


# === COMMON INTERVIEW TRAPS ===

# Trap 1: Modifying driver variable from executor
counter = 0
def wrong_count(x):
    global counter
    counter += 1  # DOES NOTHING to driver's counter!
    return x

rdd.map(wrong_count).collect()
print(f"Counter: {counter}")  # Still 0!


# Trap 2: Capturing SparkContext (NEVER serializable!)
# sc is special - it represents connection to cluster
# def wrong(x):
#     return sc.parallelize([x]).collect()  # ERROR!


# Trap 3: Capturing self in class methods
class Processor:
    def __init__(self, factor):
        self.factor = factor
        self.db = DatabaseConnection()  # Not serializable!

    def process(self, rdd):
        # 'self' is captured, including non-serializable db!
        # return rdd.map(lambda x: x * self.factor).collect()  # FAILS!

        # Solution: Extract only what you need
        factor = self.factor
        return rdd.map(lambda x: x * factor).collect()  # Works!


# === BEST PRACTICES ===

"""
1. NEVER capture:
   - SparkContext/SparkSession
   - Database connections
   - File handles
   - Any external resources

2. MINIMIZE closure size:
   - Extract primitives from objects
   - Use broadcast for large read-only data

3. Use mapPartitions:
   - When you need external connections
   - Resource creation once per partition

4. Use Accumulators:
   - For metrics/counters
   - Write-only from executors

5. Think "Serialize Everything":
   - If it goes in a closure, it must be serializable
   - Test with pickle.dumps() if unsure
"""

# Test if something is serializable
def is_serializable(obj):
    try:
        pickle.dumps(obj)
        return True
    except:
        return False

print(is_serializable(2))                    # True
print(is_serializable("hello"))              # True
print(is_serializable([1, 2, 3]))            # True
print(is_serializable(lambda x: x + 1))      # True (simple lambda)
print(is_serializable(DatabaseConnection())) # False (has socket)
```

---

## Section 3: Design Philosophy Links

### Official Documentation

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| **Java** | [JLS 15.27 Lambda Expressions](https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html#jls-15.27) | Lambda Body, Effectively Final |
| **Python** | [Execution Model](https://docs.python.org/3/reference/executionmodel.html) | Naming and Binding, nonlocal |
| **TypeScript** | [Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html) | Closures, this in arrow functions |
| **Go** | [Function Literals](https://go.dev/ref/spec#Function_literals) | Function literals are closures |
| **SQL** | N/A | Procedural extensions only |
| **C++** | [Lambda Expressions](https://en.cppreference.com/w/cpp/language/lambda) | Capture clause |
| **Spark** | [Understanding Closures](https://spark.apache.org/docs/latest/rdd-programming-guide.html#understanding-closures-) | Critical for distributed computing |

### Key Design Quotes

> **JavaScript/TypeScript**: "A closure is the combination of a function bundled together with references to its surrounding state."
> -- MDN Web Docs

> **Python**: "A nested function has access to variables of the enclosing scope."
> -- Python Documentation

> **Go**: "Function literals are closures: they may refer to variables defined in a surrounding function."
> -- Go Language Specification

> **Spark**: "Understanding closures is critical. Variables and methods when running on the cluster work differently."
> -- Apache Spark Documentation

---

## Section 4: Palantir Context Hint

### 4.1 Spark Interview Focus (CRITICAL!)

**The #1 Spark interview question at Palantir involves closures:**

```
QUESTION: "Why doesn't this counter work?"

counter = 0
rdd.foreach(lambda x: counter += 1)
print(counter)  # Still 0, why?

EXPECTED ANSWER:
1. Closures are serialized to executors
2. Each executor gets its own COPY of counter
3. Modifications happen on executor copies
4. Driver's counter is never touched
5. Use Accumulator instead: counter = sc.accumulator(0)
```

**Common Spark Closure Interview Questions:**

1. "What happens when a closure references a non-serializable object?"
   - `NotSerializableException` / `PicklingError`
   - Solutions: mapPartitions, broadcast, extract primitives

2. "How do you share a large lookup table across all tasks?"
   - `broadcast()` - sent to each executor once
   - Without broadcast: serialized with every task = huge overhead

3. "When would you use mapPartitions instead of map?"
   - External resource setup (DB, HTTP client)
   - Create resource once per partition, not per element

### 4.2 TypeScript OSDK Patterns

```typescript
// Foundry OSDK - Closures in event handlers
import { Objects } from "@foundry/ontology-api";

function setupFlightMonitor(flightId: string) {
    // 'flightId' captured by closure
    const updateUI = (status: string) => {
        console.log(`Flight ${flightId}: ${status}`);
    };

    // Subscribe to real-time updates
    Objects.Flight.subscribe(flightId, (flight) => {
        // Closure captures both 'flightId' and 'updateUI'
        updateUI(flight.status);
    });
}

// Closure factory for object handlers
function createObjectHandler<T>(objectType: string) {
    return (obj: T) => {
        console.log(`Processing ${objectType}: ${JSON.stringify(obj)}`);
    };
}

const handleFlight = createObjectHandler<Flight>("Flight");
const handlePassenger = createObjectHandler<Passenger>("Passenger");
```

### 4.3 Interview Questions Summary

| Topic | Typical Question | Key Answer Point |
|-------|------------------|------------------|
| **Loop Bug** | "Fix this code that prints 5,5,5,5,5" | var vs let / IIFE / default arg |
| **Java** | "Why effectively final?" | Value capture for thread safety |
| **Python** | "Why all lambdas return same value?" | Late binding / default arg fix |
| **Go** | "Fix goroutine closure bug" | Pass as argument / local copy |
| **C++** | "Difference between [=] and [&]?" | Value copy vs reference / lifetime |
| **Spark** | "Why counter stays 0?" | Serialization to executors / Accumulator |
| **General** | "Implement private counter with closure" | Module pattern |

### 4.4 Interview Coding Challenges

```python
# Challenge 1: Implement memoization with closure
def memoize(fn):
    cache = {}  # Captured by closure
    def wrapper(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]
    return wrapper

@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


# Challenge 2: Implement debounce with closure
def debounce(wait_ms):
    import time
    def decorator(fn):
        last_call = [0]  # Mutable container for closure
        def wrapper(*args, **kwargs):
            now = time.time() * 1000
            if now - last_call[0] >= wait_ms:
                last_call[0] = now
                return fn(*args, **kwargs)
        return wrapper
    return decorator


# Challenge 3: Implement once (function that only runs once)
def once(fn):
    has_run = [False]
    result = [None]
    def wrapper(*args, **kwargs):
        if not has_run[0]:
            result[0] = fn(*args, **kwargs)
            has_run[0] = True
        return result[0]
    return wrapper
```

---

## Section 5: Cross-References

### Related Concepts

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F10** | lexical_scope | Foundation for closure behavior |
| **F11** | closure_capture | Deep dive on capture mechanics |
| **F12** | block_vs_function_scope | var vs let scoping |
| **F13** | hoisting | Affects closure variable resolution |
| **F40** | function_first_class | Functions as values enable closures |
| **F43** | higher_order_functions | HOFs use closures extensively |
| **F31** | loops_iteration | Loop closure bugs |
| **F32** | async_patterns | Async closures and capture |

### Existing KB Links

| KB ID | Title | Connection |
|-------|-------|------------|
| 00b | functions_and_scope | General function concepts |
| 00d | async_basics | Async closures |
| 11 | osdk_typescript | OSDK closure patterns |
| 13 | pipeline_builder | Spark closure in transforms |
| 21 | python_backend_async | Python closure gotchas |

### Algorithm Patterns Using Closures

| Pattern | Use of Closure | Example |
|---------|----------------|---------|
| Memoization | Cache in outer scope | Fibonacci optimization |
| Factory | Config in outer scope | Make multiplier |
| Module | Private state | Counter pattern |
| Partial Application | Fix some arguments | Currying |
| Callback | Context for async | Event handlers |

---

## Summary: Closure Cheatsheet

```
+-------------------------------------------------------------------------+
|                         CLOSURE CHEATSHEET                               |
+-------------------------------------------------------------------------+
| Definition: Function + Lexical Environment (the "backpack" mental model)|
+-------------------------------------------------------------------------+
| Language    | Capture    | Mutable  | Loop Safe | Key Pitfall           |
+-------------+------------+----------+-----------+-----------------------+
| Java        | Value      | No*      | Yes       | effectively final     |
| Python      | Reference  | nonlocal | No        | Late binding          |
| TypeScript  | Reference  | Yes      | let: Yes  | var loop capture      |
| Go          | Reference  | Yes      | 1.22+:Yes | goroutine capture     |
| C++         | Explicit   | mutable  | [=]: Yes  | Dangling reference    |
| Spark       | Serialized | No       | No        | NotSerializable       |
+-------------------------------------------------------------------------+

LOOP CAPTURE FIX PATTERNS:
- TypeScript: var -> let
- Python: lambda: i  ->  lambda x=i: x
- Go: go func() {...}()  ->  go func(n int) {...}(i)
- C++: [&i]  ->  [i]

SPARK CLOSURE RULES:
1. Everything in closure must be serializable
2. Use broadcast() for large read-only data
3. Use Accumulator for counters
4. Use mapPartitions for external resources
5. Never capture SparkContext or database connections

INTERVIEW MUST-KNOWS:
1. "Fix the loop closure bug" (var vs let, default arg)
2. "Why Java requires effectively final?" (thread safety, value capture)
3. "Explain Spark closure serialization" (driver/executor separation)
4. "Implement private counter using closure" (module pattern)
5. "Go: Fix goroutine closure bug" (pass as argument)
+-------------------------------------------------------------------------+
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
