# F50: Arrays & Lists (배열과 리스트)

> **Concept ID**: `F50_arrays_lists`
> **Universal Principle**: 순서가 있는 동종 요소의 선형 컬렉션 (Ordered linear collections of homogeneous elements)
> **Prerequisites**: F01_variable_binding, F10_lexical_scope, F31_loops_iteration

---

## 1. Universal Concept (언어 무관 개념 정의)

### 1.1 What is an Array/List?

An **array** (or **list**) is a fundamental data structure that stores an ordered sequence of elements of the same type (or compatible types). It provides:

1. **Ordered Storage**: Elements maintain their insertion order
2. **Index-Based Access**: O(1) random access by position
3. **Contiguous Memory** (for true arrays): Adjacent memory locations for cache efficiency

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Array Memory Layout                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Index:    [0]      [1]      [2]      [3]      [4]                 │
│           ┌────┐   ┌────┐   ┌────┐   ┌────┐   ┌────┐              │
│  Memory:  │ 10 │ → │ 20 │ → │ 30 │ → │ 40 │ → │ 50 │              │
│           └────┘   └────┘   └────┘   └────┘   └────┘              │
│  Address: 0x100   0x104   0x108   0x10C   0x110                    │
│                                                                     │
│  Access arr[2]:  base_address + (2 × element_size)                 │
│                  = 0x100 + (2 × 4) = 0x108  →  30  (O(1)!)        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Array vs List vs Dynamic Array

```
┌─────────────────────────────────────────────────────────────────────┐
│              Array Types Taxonomy                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐                                               │
│  │  Fixed Array    │  - Size determined at compile/creation time   │
│  │  int arr[5]     │  - Cannot grow or shrink                      │
│  │  C, C++, Go     │  - Stored on stack (usually)                  │
│  └────────┬────────┘                                               │
│           │                                                         │
│  ┌────────▼────────┐                                               │
│  │  Dynamic Array  │  - Size can change at runtime                 │
│  │  ArrayList,     │  - Automatic resizing (amortized O(1) append) │
│  │  vector, slice  │  - Stored on heap                             │
│  └────────┬────────┘                                               │
│           │                                                         │
│  ┌────────▼────────┐                                               │
│  │  Linked List    │  - Non-contiguous memory                      │
│  │  LinkedList,    │  - O(1) insert/delete at known position       │
│  │  collections    │  - O(n) random access                         │
│  └─────────────────┘                                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Time Complexity Comparison

| Operation | Fixed Array | Dynamic Array | Linked List |
|-----------|-------------|---------------|-------------|
| **Access by index** | O(1) | O(1) | O(n) |
| **Search (unsorted)** | O(n) | O(n) | O(n) |
| **Insert at end** | N/A | O(1) amortized | O(1) if tail ptr |
| **Insert at beginning** | N/A | O(n) | O(1) |
| **Insert at middle** | N/A | O(n) | O(1) after find |
| **Delete at end** | N/A | O(1) | O(1) if tail ptr |
| **Delete at beginning** | N/A | O(n) | O(1) |
| **Delete at middle** | N/A | O(n) | O(1) after find |
| **Memory overhead** | None | ~50% extra | Per-node pointer |

### 1.4 Zero-Indexed vs One-Indexed

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Indexing Conventions                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Zero-Indexed (Most Languages):                                     │
│  ┌───┬───┬───┬───┬───┐                                             │
│  │ A │ B │ C │ D │ E │  arr[0] = 'A', arr[4] = 'E'                │
│  └───┴───┴───┴───┴───┘                                             │
│    0   1   2   3   4                                                │
│                                                                     │
│  One-Indexed (SQL, Lua, MATLAB, Fortran):                          │
│  ┌───┬───┬───┬───┬───┐                                             │
│  │ A │ B │ C │ D │ E │  arr[1] = 'A', arr[5] = 'E'                │
│  └───┴───┴───┴───┴───┘                                             │
│    1   2   3   4   5                                                │
│                                                                     │
│  ⚠️ SQL ARRAY subscripts start at 1, not 0!                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.5 Why Arrays Matter

1. **Foundation**: Every complex data structure builds on arrays
2. **Cache Efficiency**: Contiguous memory = fewer cache misses
3. **Predictable Performance**: O(1) access is guaranteed
4. **Interview Essential**: Arrays are in 70%+ of coding problems
5. **Memory Efficiency**: No per-element overhead (vs linked structures)

---

## 2. Semantic Comparison Matrix (의미론적 비교 매트릭스)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Fixed Array** | `int[]` | N/A (tuple?) | `readonly T[]` | `[N]T` | `ARRAY[N]` | `T[N]` | N/A |
| **Dynamic** | `ArrayList<T>` | `list` | `T[]` / `Array<T>` | `[]T` (slice) | `ARRAY` | `vector<T>` | `RDD` / `DataFrame` |
| **Literal Syntax** | `{1,2,3}` | `[1,2,3]` | `[1,2,3]` | `[]int{1,2,3}` | `ARRAY[1,2,3]` | `{1,2,3}` | `parallelize([1,2,3])` |
| **Type Enforcement** | Compile-time | Runtime | Compile-time | Compile-time | Runtime | Compile-time | Runtime |
| **Null/Nil** | `null` | `None` | `undefined`/`null` | `nil` slice | `NULL` | `nullptr` | `Option` |
| **Bounds Check** | Runtime | Runtime | No (unsafe) | Runtime (panic) | N/A | No (UB) | N/A |
| **Default Init** | Zero/null | N/A | N/A | Zero values | NULL | Uninitialized | N/A |
| **Mutability** | Mutable | Mutable | Mutable | Mutable | Varies | Both | **Immutable!** |
| **Resizing** | Fixed (ArrayList yes) | Auto | Auto | Manual (append) | Varies | Manual/Auto | N/A (transform) |

### 2.2 Detailed Code Examples by Pattern

---

#### Pattern 1: Array Initialization

**Java**
```java
// Fixed-size array (compile-time size)
int[] arr1 = new int[5];              // [0, 0, 0, 0, 0]
int[] arr2 = {1, 2, 3, 4, 5};         // Array literal
int[] arr3 = new int[]{1, 2, 3};      // Explicit type with literal

// Multi-dimensional array
int[][] matrix = new int[3][4];       // 3 rows, 4 columns
int[][] jagged = {                     // Jagged array
    {1, 2},
    {3, 4, 5},
    {6}
};

// ArrayList (dynamic array)
ArrayList<Integer> list = new ArrayList<>();
ArrayList<Integer> listWithCapacity = new ArrayList<>(100);  // Initial capacity
ArrayList<Integer> fromArray = new ArrayList<>(Arrays.asList(1, 2, 3));

// List.of() - immutable (Java 9+)
List<Integer> immutable = List.of(1, 2, 3);
// immutable.add(4);  // UnsupportedOperationException!

// Arrays.asList() - fixed-size wrapper
List<Integer> fixedSize = Arrays.asList(1, 2, 3);
fixedSize.set(0, 10);  // OK
// fixedSize.add(4);   // UnsupportedOperationException!

// Array length
System.out.println(arr1.length);      // 5 (field, not method!)
System.out.println(list.size());      // 3 (method)
```

**Python**
```python
# Python has ONLY dynamic lists, no fixed arrays
# (for true arrays, use numpy)

# List initialization
lst1 = []                              # Empty list
lst2 = [1, 2, 3, 4, 5]                 # List literal
lst3 = list()                          # Constructor
lst4 = list(range(5))                  # [0, 1, 2, 3, 4]
lst5 = [0] * 5                         # [0, 0, 0, 0, 0]

# List comprehension (Pythonic!)
squares = [x**2 for x in range(5)]     # [0, 1, 4, 9, 16]
evens = [x for x in range(10) if x % 2 == 0]  # [0, 2, 4, 6, 8]

# Generator expression (lazy, memory efficient)
gen = (x**2 for x in range(1000000))   # Generator object, not list!
first = next(gen)                       # 0

# Multi-dimensional (list of lists)
matrix = [[0] * 4 for _ in range(3)]   # 3x4 matrix
# WRONG: matrix = [[0] * 4] * 3       # Shares same inner list!

# Tuple (immutable "array")
tpl = (1, 2, 3)
# tpl[0] = 10  # TypeError!

# Length
print(len(lst2))  # 5

# Type hints (Python 3.9+)
from typing import List
numbers: List[int] = [1, 2, 3]
# Or: numbers: list[int] = [1, 2, 3]  # Python 3.9+
```

**TypeScript**
```typescript
// Array literal
const arr1: number[] = [1, 2, 3, 4, 5];
const arr2: Array<number> = [1, 2, 3];  // Generic syntax

// Empty array with type
const empty: string[] = [];
const emptyGeneric: Array<string> = [];

// Fixed length (tuple type)
const tuple: [number, string, boolean] = [1, "hello", true];
// const wrong: [number, string] = [1, "hello", true];  // Error!

// Readonly array (immutable)
const readonly: readonly number[] = [1, 2, 3];
const readonlyGeneric: ReadonlyArray<number> = [1, 2, 3];
// readonly.push(4);  // Error: push does not exist

// Array constructor
const withSize = new Array<number>(5);  // [empty × 5]
const filled = new Array(5).fill(0);    // [0, 0, 0, 0, 0]

// Array.from()
const fromString = Array.from("hello"); // ['h', 'e', 'l', 'l', 'o']
const fromRange = Array.from({length: 5}, (_, i) => i);  // [0, 1, 2, 3, 4]

// Multi-dimensional
const matrix: number[][] = [
    [1, 2, 3],
    [4, 5, 6]
];

// Length
console.log(arr1.length);  // 5

// ⚠️ TypeScript arrays can have holes (sparse)
const sparse: (number | undefined)[] = [];
sparse[5] = 10;  // [empty × 5, 10]
console.log(sparse[0]);  // undefined
```

**Go**
```go
// Fixed-size ARRAY (value type, copied on assignment!)
var arr1 [5]int                        // [0 0 0 0 0]
arr2 := [5]int{1, 2, 3, 4, 5}         // Array literal
arr3 := [...]int{1, 2, 3}              // Size inferred: [3]int

// Arrays are VALUE TYPES in Go!
original := [3]int{1, 2, 3}
copied := original  // COPY, not reference!
copied[0] = 100
fmt.Println(original)  // [1 2 3] - unchanged!

// SLICE (dynamic array, reference type) - what you usually want!
var slice1 []int                       // nil slice (nil, 0, 0)
slice2 := []int{1, 2, 3, 4, 5}         // Slice literal
slice3 := make([]int, 5)               // len=5, cap=5, [0 0 0 0 0]
slice4 := make([]int, 0, 10)           // len=0, cap=10

// Slice from array (creates a view!)
arr := [5]int{1, 2, 3, 4, 5}
slice := arr[1:4]                      // [2 3 4]
slice[0] = 100                         // Modifies arr!
fmt.Println(arr)                       // [1 100 3 4 5]

// ⭐ CRITICAL INTERVIEW TOPIC: len vs cap
s := make([]int, 3, 10)
fmt.Println(len(s), cap(s))            // 3, 10
// len: number of elements
// cap: capacity before reallocation needed

// Multi-dimensional slice
matrix := make([][]int, 3)
for i := range matrix {
    matrix[i] = make([]int, 4)
}

// Length and capacity
fmt.Println(len(slice2))               // 5
fmt.Println(cap(slice2))               // 5 (or more)
```

**SQL**
```sql
-- PostgreSQL ARRAY syntax
-- ⚠️ SQL arrays are 1-INDEXED!

-- Array literal
SELECT ARRAY[1, 2, 3, 4, 5];            -- {1,2,3,4,5}
SELECT ARRAY['a', 'b', 'c'];            -- {a,b,c}

-- Array column definition
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    tags TEXT[],                        -- Array of text
    prices NUMERIC[]                    -- Array of numbers
);

-- Insert with array
INSERT INTO products (name, tags, prices)
VALUES ('Widget', ARRAY['sale', 'new'], ARRAY[10.99, 9.99]);

-- Alternative syntax
INSERT INTO products (name, tags)
VALUES ('Gadget', '{"electronics", "popular"}');

-- Array access (1-indexed!)
SELECT tags[1] FROM products;           -- First element
SELECT tags[2:4] FROM products;         -- Slice (indices 2-4)

-- Array functions
SELECT array_length(tags, 1) FROM products;  -- Length (1st dimension)
SELECT cardinality(tags) FROM products;      -- Total elements

-- Multi-dimensional
SELECT ARRAY[[1,2,3], [4,5,6]];         -- 2x3 array

-- Fixed-size (PostgreSQL)
CREATE TABLE fixed_arrays (
    data INTEGER[3]                     -- Fixed 3-element array
);
```

**C++**
```cpp
#include <array>
#include <vector>
#include <iostream>

int main() {
    // C-style array (avoid in modern C++)
    int carr[5] = {1, 2, 3, 4, 5};
    int carr2[] = {1, 2, 3};           // Size inferred

    // ⚠️ C arrays decay to pointers, no bounds checking!
    // std::cout << carr[100];         // Undefined behavior!

    // std::array (C++11) - fixed size, bounds checking with .at()
    std::array<int, 5> arr1 = {1, 2, 3, 4, 5};
    std::array<int, 5> arr2{};         // Zero-initialized

    // Access
    arr1[0] = 10;                       // No bounds check
    arr1.at(0) = 10;                    // Throws if out of range

    // std::vector (dynamic array) - what you usually want
    std::vector<int> vec1;              // Empty
    std::vector<int> vec2(5);           // [0, 0, 0, 0, 0]
    std::vector<int> vec3(5, 42);       // [42, 42, 42, 42, 42]
    std::vector<int> vec4{1, 2, 3, 4};  // Initializer list

    // Reserve vs resize
    std::vector<int> v;
    v.reserve(100);  // Capacity = 100, size = 0
    v.resize(50);    // Capacity >= 50, size = 50

    // Multi-dimensional
    std::vector<std::vector<int>> matrix(3, std::vector<int>(4, 0));

    // Length
    std::cout << arr1.size() << std::endl;   // 5
    std::cout << vec4.size() << std::endl;   // 4
    std::cout << vec4.capacity() << std::endl;  // Implementation-defined

    return 0;
}
```

**Spark**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import array, col, explode, size, array_contains

spark = SparkSession.builder.getOrCreate()

# =====================================================
# CRITICAL: Spark collections are IMMUTABLE!
# Every transformation creates a NEW RDD/DataFrame
# =====================================================

# RDD (Resilient Distributed Dataset)
rdd = spark.sparkContext.parallelize([1, 2, 3, 4, 5])
# rdd is IMMUTABLE - no "append", "insert", etc.

# Transformation creates NEW RDD
doubled_rdd = rdd.map(lambda x: x * 2)
# Original rdd is unchanged!

# DataFrame with array column
df = spark.createDataFrame([
    (1, [1, 2, 3]),
    (2, [4, 5, 6, 7]),
    (3, [8])
], ["id", "numbers"])

# Array functions
df.select(
    col("id"),
    size("numbers").alias("array_size"),
    array_contains("numbers", 2).alias("has_2")
).show()

# explode: Flatten array into rows
df.select(
    col("id"),
    explode("numbers").alias("number")
).show()
# id | number
# 1  | 1
# 1  | 2
# 1  | 3
# 2  | 4
# ...

# Create array from columns
df2 = spark.createDataFrame([
    (1, 10, 20),
    (2, 30, 40)
], ["id", "a", "b"])

df2.select(
    col("id"),
    array("a", "b").alias("arr")
).show()
# id | arr
# 1  | [10, 20]
# 2  | [30, 40]
```

---

#### Pattern 2: Dynamic Resizing

**Java**
```java
// ArrayList - automatic resizing
ArrayList<Integer> list = new ArrayList<>();

// Add elements (amortized O(1))
for (int i = 0; i < 10; i++) {
    list.add(i);
}

// Internal: ArrayList doubles capacity when full
// Default initial capacity: 10
// Growth: 10 → 15 → 22 → 33 → ...  (50% increase)

// Manual capacity management
ArrayList<Integer> optimized = new ArrayList<>(1000);  // Pre-allocate
optimized.ensureCapacity(2000);  // Increase capacity
optimized.trimToSize();          // Shrink to fit

// addAll - bulk add
list.addAll(Arrays.asList(100, 200, 300));
```

**Python**
```python
# Python lists auto-resize (over-allocate)
lst = []

# append - O(1) amortized
for i in range(10):
    lst.append(i)

# extend - add multiple elements
lst.extend([100, 200, 300])

# insert at position - O(n) (shifts elements)
lst.insert(0, -1)  # Insert at beginning

# Internal: Python over-allocates by ~12.5%
# Growth pattern: 0, 4, 8, 16, 24, 32, 40, 52, 64, ...

# Pre-allocation (rarely needed)
import sys
lst = [None] * 1000  # Pre-allocate
print(sys.getsizeof(lst))  # Check memory

# Concatenation creates new list
a = [1, 2, 3]
b = [4, 5, 6]
c = a + b  # New list: [1, 2, 3, 4, 5, 6]
# a and b unchanged
```

**TypeScript**
```typescript
// JavaScript arrays auto-resize
const arr: number[] = [];

// push - add to end (amortized O(1))
for (let i = 0; i < 10; i++) {
    arr.push(i);
}

// push multiple
arr.push(100, 200, 300);

// unshift - add to beginning (O(n)!)
arr.unshift(-1);  // All elements shift right

// splice - insert at position
arr.splice(5, 0, 999);  // Insert 999 at index 5, delete 0

// Spread operator - concatenation
const a = [1, 2, 3];
const b = [4, 5, 6];
const c = [...a, ...b];  // [1, 2, 3, 4, 5, 6]

// concat
const d = a.concat(b);  // [1, 2, 3, 4, 5, 6]
```

**Go (CRITICAL for Interviews!)**
```go
// ⭐ Go slice internals: (pointer, length, capacity)
//
//    ┌──────────────────────────────────┐
//    │       Slice Header               │
//    │  ┌─────┬──────┬──────────┐      │
//    │  │ ptr │ len  │ cap      │      │
//    │  └──┬──┴──────┴──────────┘      │
//    │     │                            │
//    │     ▼                            │
//    │  ┌───┬───┬───┬───┬───┬───┬───┐  │
//    │  │ 1 │ 2 │ 3 │ _ │ _ │ _ │ _ │  │  ← Underlying array
//    │  └───┴───┴───┴───┴───┴───┴───┘  │
//    │   len=3, cap=7                   │
//    └──────────────────────────────────┘

// Create with make(type, length, capacity)
s := make([]int, 3, 10)
fmt.Println(len(s), cap(s))  // 3, 10

// append - CRITICAL behavior
s = append(s, 4, 5, 6)
fmt.Println(len(s), cap(s))  // 6, 10 (no reallocation)

// What happens when capacity exceeded?
s = append(s, 7, 8, 9, 10, 11)  // Exceeds cap=10
fmt.Println(len(s), cap(s))     // 11, 20 (doubled!)

// ⭐ INTERVIEW QUESTION: "What happens with append?"
// Answer: If cap sufficient, appends in place
//         If cap exceeded, allocates NEW array (usually 2x),
//         copies old elements, returns NEW slice header

// GOTCHA: Shared underlying array
original := []int{1, 2, 3, 4, 5}
sliced := original[1:3]  // [2, 3], shares array!

sliced[0] = 100
fmt.Println(original)  // [1, 100, 3, 4, 5] - MODIFIED!

// GOTCHA: append to slice may affect original
original = []int{1, 2, 3, 4, 5}
sliced = original[1:3]  // len=2, cap=4 (room to grow!)

sliced = append(sliced, 999)
fmt.Println(original)  // [1, 2, 3, 999, 5] - original[3] changed!

// Safe copy
safeCopy := make([]int, len(sliced))
copy(safeCopy, sliced)

// Or use full slice expression to limit capacity
sliced = original[1:3:3]  // len=2, cap=2 (cap limited!)
sliced = append(sliced, 999)
fmt.Println(original)  // [1, 2, 3, 4, 5] - unchanged!
```

**C++**
```cpp
#include <vector>
#include <iostream>

int main() {
    std::vector<int> vec;

    // push_back - amortized O(1)
    for (int i = 0; i < 10; i++) {
        vec.push_back(i);
        std::cout << "Size: " << vec.size()
                  << " Capacity: " << vec.capacity() << "\n";
    }
    // Typical growth: 1, 2, 4, 8, 16... (doubles)

    // reserve - pre-allocate capacity
    std::vector<int> optimized;
    optimized.reserve(1000);  // Capacity=1000, size=0

    // shrink_to_fit - reduce capacity (C++11)
    vec.shrink_to_fit();

    // emplace_back - construct in place (more efficient)
    struct Item { int x, y; };
    std::vector<Item> items;
    items.emplace_back(1, 2);  // No temporary object

    // insert at position - O(n)
    vec.insert(vec.begin() + 5, 999);

    // erase - O(n)
    vec.erase(vec.begin());       // Remove first
    vec.erase(vec.begin(), vec.begin() + 3);  // Remove range

    return 0;
}
```

---

#### Pattern 3: Common Array Operations

**Java**
```java
import java.util.*;

public class ArrayOperations {
    public static void main(String[] args) {
        // Access
        int[] arr = {1, 2, 3, 4, 5};
        int first = arr[0];
        int last = arr[arr.length - 1];

        // Modify
        arr[2] = 100;

        // Search
        int index = -1;
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] == 100) {
                index = i;
                break;
            }
        }
        // Or use Arrays utility
        int[] sorted = {1, 2, 3, 4, 5};
        int idx = Arrays.binarySearch(sorted, 3);  // Requires sorted!

        // Contains (ArrayList)
        ArrayList<Integer> list = new ArrayList<>(Arrays.asList(1, 2, 3));
        boolean contains = list.contains(2);  // O(n)
        int indexOf = list.indexOf(2);        // 1

        // Remove
        list.remove(Integer.valueOf(2));  // Remove by value
        list.remove(0);                   // Remove by index

        // Sort
        Arrays.sort(arr);                 // In-place
        Arrays.sort(arr, 0, 3);           // Sort partial range

        Collections.sort(list);           // ArrayList
        list.sort(Comparator.naturalOrder());
        list.sort(Comparator.reverseOrder());

        // Copy
        int[] copy = Arrays.copyOf(arr, arr.length);
        int[] partial = Arrays.copyOfRange(arr, 1, 4);

        // Fill
        Arrays.fill(arr, 0);              // All zeros

        // Reverse (no built-in for array!)
        Collections.reverse(list);

        // Convert array <-> list
        Integer[] boxed = list.toArray(new Integer[0]);
        List<Integer> fromArray = Arrays.asList(boxed);

        // Sublist (view, not copy!)
        List<Integer> subList = list.subList(0, 2);
        subList.set(0, 999);  // Modifies original list!
    }
}
```

**Python**
```python
# Access
arr = [1, 2, 3, 4, 5]
first = arr[0]
last = arr[-1]          # Negative indexing!
second_last = arr[-2]   # 4

# Slicing (start:stop:step)
arr[1:4]                # [2, 3, 4] (indices 1, 2, 3)
arr[:3]                 # [1, 2, 3] (first 3)
arr[2:]                 # [3, 4, 5] (from index 2)
arr[::2]                # [1, 3, 5] (every other)
arr[::-1]               # [5, 4, 3, 2, 1] (reversed)

# Modify
arr[2] = 100

# Search
3 in arr                # True (O(n))
arr.index(3)            # 2 (ValueError if not found)

# Safer search
if 99 in arr:
    idx = arr.index(99)

# Remove
arr.remove(3)           # Remove first occurrence by value
del arr[0]              # Remove by index
popped = arr.pop()      # Remove and return last
popped = arr.pop(0)     # Remove and return first (O(n)!)

# Sort
arr.sort()              # In-place, returns None
sorted_arr = sorted(arr)  # Returns new list

arr.sort(reverse=True)
arr.sort(key=lambda x: abs(x))  # Custom key

# Copy
shallow = arr.copy()    # Or: arr[:] or list(arr)
import copy
deep = copy.deepcopy(nested_arr)  # For nested structures

# Reverse
arr.reverse()           # In-place
reversed_arr = arr[::-1]  # New list
reversed_iter = reversed(arr)  # Iterator

# Clear
arr.clear()             # Remove all elements

# Count
[1, 1, 2, 1].count(1)   # 3

# Extend vs append
a = [1, 2]
a.append([3, 4])        # [1, 2, [3, 4]]
a.extend([5, 6])        # [1, 2, [3, 4], 5, 6]
```

**TypeScript**
```typescript
// Access
const arr: number[] = [1, 2, 3, 4, 5];
const first = arr[0];
const last = arr[arr.length - 1];
const lastAt = arr.at(-1);  // ES2022: 5

// Modify
arr[2] = 100;

// Add/Remove
arr.push(6);            // Add to end, returns new length
arr.pop();              // Remove from end, returns element
arr.unshift(0);         // Add to beginning (O(n))
arr.shift();            // Remove from beginning (O(n))

// splice: insert, remove, replace
arr.splice(2, 1);       // Remove 1 element at index 2
arr.splice(2, 0, 99);   // Insert 99 at index 2
arr.splice(2, 1, 88);   // Replace element at index 2

// Search
arr.includes(3);        // true (O(n))
arr.indexOf(3);         // 2 (-1 if not found)
arr.lastIndexOf(3);     // Last occurrence
arr.find(x => x > 2);   // First element matching predicate
arr.findIndex(x => x > 2);  // Index of first match

// Filter (new array)
const evens = arr.filter(x => x % 2 === 0);

// Map (new array)
const doubled = arr.map(x => x * 2);

// Reduce
const sum = arr.reduce((acc, x) => acc + x, 0);

// Sort (in-place, returns same array)
arr.sort();             // ⚠️ Converts to string, sorts lexicographically!
arr.sort((a, b) => a - b);  // Numeric ascending
arr.sort((a, b) => b - a);  // Numeric descending

// toSorted (ES2023) - returns new array
const sorted = arr.toSorted((a, b) => a - b);

// Copy
const shallow = [...arr];           // Spread
const shallow2 = arr.slice();       // slice without args
const shallow3 = Array.from(arr);   // Array.from

// Reverse
arr.reverse();          // In-place
const reversed = arr.toReversed();  // ES2023: new array

// Slice (new array, does not modify)
const middle = arr.slice(1, 4);     // Elements 1, 2, 3

// Concat (new array)
const combined = arr.concat([6, 7]);

// Join
const str = arr.join(", ");  // "1, 2, 3, 4, 5"

// flat (ES2019)
const nested = [[1, 2], [3, [4, 5]]];
nested.flat();          // [1, 2, 3, [4, 5]]
nested.flat(2);         // [1, 2, 3, 4, 5]
nested.flat(Infinity);  // Flatten all levels

// flatMap
[1, 2, 3].flatMap(x => [x, x * 2]);  // [1, 2, 2, 4, 3, 6]

// every / some
arr.every(x => x > 0);  // true if all match
arr.some(x => x > 4);   // true if any match

// fill
arr.fill(0);            // [0, 0, 0, 0, 0]
arr.fill(9, 1, 3);      // Fill indices 1-2 with 9
```

**Go**
```go
package main

import (
    "fmt"
    "sort"
)

func main() {
    // Access
    arr := []int{1, 2, 3, 4, 5}
    first := arr[0]
    last := arr[len(arr)-1]

    // Modify
    arr[2] = 100

    // Append
    arr = append(arr, 6, 7)

    // Insert at index (no built-in!)
    idx := 2
    arr = append(arr[:idx+1], arr[idx:]...)
    arr[idx] = 999

    // Remove at index
    arr = append(arr[:idx], arr[idx+1:]...)

    // Search (no built-in for unsorted!)
    target := 3
    found := -1
    for i, v := range arr {
        if v == target {
            found = i
            break
        }
    }

    // Binary search (sorted only)
    sorted := []int{1, 2, 3, 4, 5}
    idx = sort.SearchInts(sorted, 3)  // Returns insertion point

    // Sort
    sort.Ints(arr)                    // In-place
    sort.Sort(sort.Reverse(sort.IntSlice(arr)))  // Descending

    // Custom sort
    type Person struct {
        Name string
        Age  int
    }
    people := []Person{{"Bob", 30}, {"Alice", 25}}
    sort.Slice(people, func(i, j int) bool {
        return people[i].Age < people[j].Age
    })

    // Copy
    dst := make([]int, len(arr))
    copy(dst, arr)  // Returns number copied

    // Contains (no built-in!)
    contains := func(slice []int, val int) bool {
        for _, v := range slice {
            if v == val {
                return true
            }
        }
        return false
    }
    fmt.Println(contains(arr, 3))

    // Reverse (no built-in!)
    for i, j := 0, len(arr)-1; i < j; i, j = i+1, j-1 {
        arr[i], arr[j] = arr[j], arr[i]
    }

    // Clear (set length to 0, keep capacity)
    arr = arr[:0]

    // Filter (no built-in!)
    filter := func(slice []int, predicate func(int) bool) []int {
        result := make([]int, 0)
        for _, v := range slice {
            if predicate(v) {
                result = append(result, v)
            }
        }
        return result
    }
    evens := filter([]int{1, 2, 3, 4, 5}, func(x int) bool { return x%2 == 0 })
}
```

**SQL**
```sql
-- PostgreSQL array operations

-- Access (1-indexed!)
SELECT (ARRAY[10, 20, 30])[1];         -- 10 (first element)
SELECT (ARRAY[10, 20, 30])[3];         -- 30 (last)

-- Slice
SELECT (ARRAY[10, 20, 30, 40, 50])[2:4];  -- {20,30,40}

-- Array length
SELECT array_length(ARRAY[1, 2, 3], 1);   -- 3 (first dimension)
SELECT cardinality(ARRAY[1, 2, 3]);       -- 3

-- Contains
SELECT 3 = ANY(ARRAY[1, 2, 3]);           -- true
SELECT ARRAY[1, 2] <@ ARRAY[1, 2, 3];     -- true (subset)
SELECT ARRAY[1, 2, 3] @> ARRAY[2, 3];     -- true (contains)

-- Concatenate
SELECT ARRAY[1, 2] || ARRAY[3, 4];        -- {1,2,3,4}
SELECT ARRAY[1, 2] || 3;                  -- {1,2,3}
SELECT 0 || ARRAY[1, 2];                  -- {0,1,2}

-- Append / Prepend
SELECT array_append(ARRAY[1, 2], 3);      -- {1,2,3}
SELECT array_prepend(0, ARRAY[1, 2]);     -- {0,1,2}

-- Remove
SELECT array_remove(ARRAY[1, 2, 3, 2], 2);  -- {1,3} (all occurrences!)

-- Replace
SELECT array_replace(ARRAY[1, 2, 2, 3], 2, 9);  -- {1,9,9,3}

-- Position (find)
SELECT array_position(ARRAY['a', 'b', 'c'], 'b');  -- 2

-- Unnest (explode to rows)
SELECT unnest(ARRAY[1, 2, 3]);  -- Returns 3 rows: 1, 2, 3

-- Aggregate back to array
SELECT array_agg(x) FROM unnest(ARRAY[3, 1, 2]) AS x;

-- Sort array (via unnest/aggregate)
SELECT array_agg(x ORDER BY x)
FROM unnest(ARRAY[3, 1, 2]) AS x;  -- {1,2,3}

-- Distinct
SELECT array_agg(DISTINCT x)
FROM unnest(ARRAY[1, 2, 2, 3]) AS x;  -- {1,2,3}
```

**C++**
```cpp
#include <vector>
#include <algorithm>
#include <iostream>
#include <numeric>

int main() {
    std::vector<int> vec = {5, 2, 8, 1, 9, 3};

    // Access
    int first = vec[0];        // No bounds check
    int safe = vec.at(0);      // Throws if out of range
    int front = vec.front();   // First element
    int back = vec.back();     // Last element

    // Modify
    vec[2] = 100;

    // Add
    vec.push_back(6);          // Add to end
    vec.emplace_back(7);       // Construct in place

    // Insert
    vec.insert(vec.begin() + 2, 99);  // Insert at index 2

    // Remove
    vec.pop_back();            // Remove last
    vec.erase(vec.begin() + 2);  // Remove at index
    vec.erase(vec.begin(), vec.begin() + 3);  // Remove range

    // Remove by value (erase-remove idiom)
    vec.erase(
        std::remove(vec.begin(), vec.end(), 3),
        vec.end()
    );

    // Remove if predicate
    vec.erase(
        std::remove_if(vec.begin(), vec.end(),
            [](int x) { return x % 2 == 0; }),
        vec.end()
    );

    // Search
    auto it = std::find(vec.begin(), vec.end(), 5);
    if (it != vec.end()) {
        std::cout << "Found at index " << (it - vec.begin()) << "\n";
    }

    // Binary search (sorted only)
    std::sort(vec.begin(), vec.end());
    bool exists = std::binary_search(vec.begin(), vec.end(), 5);

    // Sort
    std::sort(vec.begin(), vec.end());  // Ascending
    std::sort(vec.begin(), vec.end(), std::greater<int>());  // Descending

    // Partial sort
    std::partial_sort(vec.begin(), vec.begin() + 3, vec.end());

    // Reverse
    std::reverse(vec.begin(), vec.end());

    // Copy
    std::vector<int> copy = vec;  // Copy constructor
    std::vector<int> copy2;
    std::copy(vec.begin(), vec.end(), std::back_inserter(copy2));

    // Transform (map)
    std::vector<int> doubled;
    std::transform(vec.begin(), vec.end(),
        std::back_inserter(doubled),
        [](int x) { return x * 2; });

    // Filter (copy_if)
    std::vector<int> evens;
    std::copy_if(vec.begin(), vec.end(),
        std::back_inserter(evens),
        [](int x) { return x % 2 == 0; });

    // Reduce (accumulate)
    int sum = std::accumulate(vec.begin(), vec.end(), 0);
    int product = std::accumulate(vec.begin(), vec.end(), 1,
        std::multiplies<int>());

    // All/Any/None
    bool allPositive = std::all_of(vec.begin(), vec.end(),
        [](int x) { return x > 0; });
    bool anyEven = std::any_of(vec.begin(), vec.end(),
        [](int x) { return x % 2 == 0; });

    // Min/Max
    auto minIt = std::min_element(vec.begin(), vec.end());
    auto maxIt = std::max_element(vec.begin(), vec.end());

    return 0;
}
```

**Spark**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

# DataFrame with array column
df = spark.createDataFrame([
    (1, [1, 2, 3, 4, 5]),
    (2, [10, 20, 30]),
    (3, [100])
], ["id", "arr"])

# Array functions

# Size
df.select("id", size("arr").alias("len")).show()

# Access element (0-indexed in Spark SQL functions!)
df.select("id", element_at("arr", 1).alias("first")).show()  # 1-indexed for element_at!
df.select("id", col("arr")[0].alias("first")).show()  # 0-indexed for subscript

# Slice
df.select("id", slice("arr", 1, 2).alias("first_two")).show()

# Contains
df.select("id", array_contains("arr", 2).alias("has_2")).show()

# Append
df.select("id", array_append("arr", 999).alias("appended")).show()

# Concat arrays
df.select("id", concat("arr", array(lit(6), lit(7))).alias("extended")).show()

# Remove
df.select("id", array_remove("arr", 2).alias("removed_2")).show()

# Distinct
df.select("id", array_distinct(concat("arr", "arr")).alias("unique")).show()

# Sort
df.select("id", sort_array("arr").alias("sorted")).show()
df.select("id", sort_array("arr", asc=False).alias("sorted_desc")).show()

# Reverse
df.select("id", reverse("arr").alias("reversed")).show()

# Transform (map over array elements)
df.select(
    "id",
    transform("arr", lambda x: x * 2).alias("doubled")
).show()

# Filter array elements
df.select(
    "id",
    filter("arr", lambda x: x > 2).alias("filtered")
).show()

# Aggregate (reduce)
df.select(
    "id",
    aggregate("arr", lit(0), lambda acc, x: acc + x).alias("sum")
).show()

# Exists (any)
df.select(
    "id",
    exists("arr", lambda x: x > 100).alias("has_large")
).show()

# Forall (all)
df.select(
    "id",
    forall("arr", lambda x: x > 0).alias("all_positive")
).show()

# Zip arrays
df2 = spark.createDataFrame([
    (1, ["a", "b", "c"]),
], ["id", "letters"])

df.join(df2, "id").select(
    "id",
    arrays_zip("arr", "letters").alias("zipped")
).show()

# Flatten nested arrays
nested_df = spark.createDataFrame([
    (1, [[1, 2], [3, 4]]),
], ["id", "nested"])

nested_df.select("id", flatten("nested").alias("flat")).show()
```

---

#### Pattern 4: ArrayList vs LinkedList (Java Interview Critical!)

**Java**
```java
import java.util.*;

public class ListComparison {
    public static void main(String[] args) {
        /*
         * ArrayList vs LinkedList - Time Complexity
         *
         * Operation           | ArrayList | LinkedList
         * --------------------|-----------|------------
         * get(index)          | O(1)      | O(n)
         * add(element)        | O(1)*     | O(1)
         * add(index, element) | O(n)      | O(n)**
         * remove(index)       | O(n)      | O(n)**
         * remove(element)     | O(n)      | O(n)
         * contains            | O(n)      | O(n)
         * iterator.remove()   | O(n)      | O(1)
         *
         * * amortized (may need to grow array)
         * ** O(n) to find position, O(1) to modify
         *
         * Memory:
         * ArrayList: ~4 bytes per element (reference)
         * LinkedList: ~24 bytes per element (node overhead)
         */

        // When to use ArrayList:
        // - Random access needed
        // - Mostly reading
        // - Adding primarily at end
        // - Memory efficiency matters
        ArrayList<Integer> arrayList = new ArrayList<>();

        // When to use LinkedList:
        // - Frequent insertions/deletions at beginning
        // - Implementing queue/deque
        // - Iterator-based removal during traversal
        LinkedList<Integer> linkedList = new LinkedList<>();

        // LinkedList as Deque (double-ended queue)
        LinkedList<Integer> deque = new LinkedList<>();
        deque.addFirst(1);      // O(1)
        deque.addLast(2);       // O(1)
        deque.removeFirst();    // O(1)
        deque.removeLast();     // O(1)
        deque.peekFirst();      // O(1)
        deque.peekLast();       // O(1)

        // Benchmark: Random access
        int n = 100000;
        ArrayList<Integer> al = new ArrayList<>();
        LinkedList<Integer> ll = new LinkedList<>();
        for (int i = 0; i < n; i++) {
            al.add(i);
            ll.add(i);
        }

        // ArrayList random access: ~0ms
        long start = System.nanoTime();
        for (int i = 0; i < 1000; i++) {
            al.get(n / 2);
        }
        System.out.println("ArrayList get: " + (System.nanoTime() - start) / 1e6 + "ms");

        // LinkedList random access: ~200ms (must traverse!)
        start = System.nanoTime();
        for (int i = 0; i < 1000; i++) {
            ll.get(n / 2);
        }
        System.out.println("LinkedList get: " + (System.nanoTime() - start) / 1e6 + "ms");

        // Interview tip: For most use cases, ArrayList is better!
        // LinkedList is rarely the right choice in practice.
    }
}
```

---

#### Pattern 5: vector vs array vs std::array (C++)

**C++**
```cpp
#include <array>
#include <vector>
#include <iostream>

/*
 * C++ Array Types Comparison
 *
 * Type          | Size      | Bounds Check | Storage  | Use Case
 * --------------|-----------|--------------|----------|------------------
 * T[]           | Fixed     | NO (UB)      | Stack    | Legacy, avoid
 * std::array    | Fixed     | .at() yes    | Stack    | Fixed size known at compile
 * std::vector   | Dynamic   | .at() yes    | Heap     | Most common, dynamic size
 *
 * Performance:
 * - C array / std::array: No overhead, inline
 * - std::vector: Slight overhead for heap allocation
 *
 * Stack vs Heap:
 * - Stack: Fast allocation, limited size (~1MB default)
 * - Heap: Slower allocation, large sizes OK
 */

int main() {
    // C-style array - AVOID in modern C++
    int carr[5] = {1, 2, 3, 4, 5};
    // Problems:
    // - Decays to pointer when passed to function
    // - No bounds checking
    // - Size not stored

    // std::array (C++11) - Fixed size, known at compile time
    std::array<int, 5> arr = {1, 2, 3, 4, 5};
    // Benefits:
    // - Doesn't decay to pointer
    // - Has .size() method
    // - Works with STL algorithms
    // - Bounds checking with .at()

    arr[10] = 0;       // Undefined behavior!
    // arr.at(10) = 0; // Throws std::out_of_range

    // std::vector - Dynamic size, most common
    std::vector<int> vec = {1, 2, 3, 4, 5};
    // Benefits:
    // - Can grow/shrink
    // - Heap allocated (can be large)
    // - All STL algorithms work

    // Size comparison
    std::cout << "C array size: " << sizeof(carr) << "\n";           // 20 bytes (5 * 4)
    std::cout << "std::array size: " << sizeof(arr) << "\n";         // 20 bytes (no overhead!)
    std::cout << "std::vector size: " << sizeof(vec) << "\n";        // 24 bytes (pointer + size + capacity)

    // Recommendation:
    // - Use std::vector by default
    // - Use std::array when size is fixed and small
    // - Avoid C-style arrays unless interfacing with C

    return 0;
}
```

---

#### Pattern 6: Python List Comprehension vs Generator Expression

**Python**
```python
import sys

# =====================================================
# List Comprehension: Creates list in memory
# =====================================================

# Basic comprehension
squares = [x**2 for x in range(10)]  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# With condition
evens = [x for x in range(20) if x % 2 == 0]

# Nested comprehension (matrix)
matrix = [[i * j for j in range(4)] for i in range(3)]

# Flatten nested
nested = [[1, 2], [3, 4], [5]]
flat = [x for sublist in nested for x in sublist]  # [1, 2, 3, 4, 5]

# Multiple iterables
pairs = [(x, y) for x in range(3) for y in range(3)]

# With function call
words = ["hello", "world"]
lengths = [len(w) for w in words]

# =====================================================
# Generator Expression: Lazy evaluation, memory efficient
# =====================================================

# Same syntax, but with parentheses
squares_gen = (x**2 for x in range(10))  # Generator object

# Memory comparison
big_list = [x for x in range(1000000)]
big_gen = (x for x in range(1000000))

print(f"List: {sys.getsizeof(big_list):,} bytes")   # ~8,000,056 bytes
print(f"Generator: {sys.getsizeof(big_gen)} bytes") # ~112 bytes

# Usage: Iterate once
for val in big_gen:
    pass  # Process each value

# ⚠️ Generator exhaustion
gen = (x for x in range(3))
print(list(gen))  # [0, 1, 2]
print(list(gen))  # [] - exhausted!

# =====================================================
# When to use which?
# =====================================================

# Use LIST COMPREHENSION when:
# - You need to access elements multiple times
# - You need len(), indexing, or slicing
# - The result is small enough for memory
# - You need to pass to function expecting list

# Use GENERATOR EXPRESSION when:
# - Processing large data
# - You only iterate once
# - Memory is a concern
# - Passing to functions accepting iterables (sum, max, min, etc.)

# Example: sum() works with both
total_list = sum([x for x in range(1000000)])   # Creates list first
total_gen = sum(x for x in range(1000000))      # Memory efficient!

# Note: No need for double parentheses
sum((x for x in range(10)))  # Explicit generator
sum(x for x in range(10))    # Generator expression as argument - preferred

# =====================================================
# Dictionary and Set Comprehensions
# =====================================================

# Dict comprehension
squares_dict = {x: x**2 for x in range(5)}  # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# Set comprehension
unique_lengths = {len(word) for word in ["hello", "world", "hi"]}  # {2, 5}
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Documentation | Key Section |
|----------|---------------|-------------|
| **Java** | [Arrays Tutorial](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/arrays.html) | Arrays |
| **Java** | [Collections Framework](https://docs.oracle.com/javase/8/docs/technotes/guides/collections/overview.html) | ArrayList, LinkedList |
| **Python** | [Built-in Types](https://docs.python.org/3/library/stdtypes.html#lists) | Lists |
| **Python** | [List Comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions) | Comprehensions |
| **TypeScript** | [Array Type](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#arrays) | Arrays |
| **TypeScript** | [MDN Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array) | Array methods |
| **Go** | [Arrays](https://go.dev/tour/moretypes/6) | Arrays |
| **Go** | [Slices](https://go.dev/blog/slices-intro) | Slices (CRITICAL!) |
| **Go** | [Slice Internals](https://go.dev/blog/slices) | Internal representation |
| **SQL** | [PostgreSQL Arrays](https://www.postgresql.org/docs/current/arrays.html) | Array types |
| **C++** | [std::vector](https://en.cppreference.com/w/cpp/container/vector) | vector |
| **C++** | [std::array](https://en.cppreference.com/w/cpp/container/array) | array |
| **Spark** | [RDD Programming Guide](https://spark.apache.org/docs/latest/rdd-programming-guide.html) | RDD |
| **Spark** | [Array Functions](https://spark.apache.org/docs/latest/api/sql/index.html#array-functions) | SQL array functions |

### Design Philosophy Quotes

> **Go**: "A slice is a descriptor of an array segment. It consists of a pointer to the array, the length of the segment, and its capacity."
> - Go Blog: Slices

> **Python**: "Lists are mutable sequences, typically used to store collections of homogeneous items."
> - Python Documentation

> **Spark**: "RDDs are immutable. Once created, an RDD cannot be changed. Every transformation creates a new RDD."
> - Spark Programming Guide

---

## 4. Palantir Context Hint (팔란티어 맥락 힌트)

### 4.1 Spark: RDD/DataFrame Immutability

```python
# =====================================================
# CRITICAL for Palantir: Spark collections are IMMUTABLE!
# =====================================================

# WRONG mental model (imperative, mutable):
# arr = [1, 2, 3]
# arr.append(4)  # Mutates arr

# CORRECT mental model (functional, immutable):
# Every transformation creates a NEW RDD/DataFrame

df = spark.createDataFrame([(1,), (2,), (3,)], ["value"])

# This does NOT modify df!
df.filter(col("value") > 1)  # Returns new DataFrame
df.show()  # Still shows all three rows!

# Must capture the result
filtered_df = df.filter(col("value") > 1)
filtered_df.show()  # Shows 2 and 3

# Chain transformations (all lazy!)
result = (df
    .filter(col("value") > 1)        # New DF
    .withColumn("doubled", col("value") * 2)  # New DF
    .select("doubled"))              # New DF

# Original df unchanged at every step!

# Why immutability?
# 1. Parallel processing: No race conditions
# 2. Fault tolerance: Can recompute from lineage
# 3. Optimization: Catalyst can reorder operations
```

### 4.2 TypeScript OSDK Array Patterns

```typescript
// Foundry OSDK commonly works with arrays of Objects

import { Objects, Ontology } from "@foundry/ontology-api";

// Fetching arrays of objects
const flights: Flight[] = await Objects.search(Flight)
    .filter(f => f.status === "active")
    .pageSize(100)
    .execute()
    .then(r => r.data);

// Array processing with OSDK
const totalDelay = flights
    .map(f => f.delay || 0)
    .reduce((sum, delay) => sum + delay, 0);

// Grouping (common pattern)
const byAirline = new Map<string, Flight[]>();
for (const flight of flights) {
    const airline = flight.airline || "Unknown";
    if (!byAirline.has(airline)) {
        byAirline.set(airline, []);
    }
    byAirline.get(airline)!.push(flight);
}

// Array of property values
const statuses: string[] = flights
    .map(f => f.status)
    .filter((s): s is string => s !== undefined);

// Type-safe array handling
const safeAccess = (arr: Flight[], index: number): Flight | undefined => {
    return arr[index];  // TypeScript doesn't prevent out-of-bounds!
};

// Better: use optional chaining or .at()
const maybeFlight = flights.at(100);  // Flight | undefined
```

### 4.3 Interview Questions (HIGHEST PRIORITY)

1. **"Go slice: what happens when you append beyond capacity?"**
```
Answer:
1. Go allocates a new underlying array (usually 2x capacity)
2. Copies existing elements to new array
3. Appends new element(s)
4. Returns NEW slice header pointing to new array
5. Old slice still points to old array (if referenced elsewhere)

Key insight: append() may return a slice backed by different array!
Always reassign: slice = append(slice, elem)
```

2. **"ArrayList vs LinkedList time complexity comparison"**
```
Operation           | ArrayList | LinkedList
--------------------|-----------|------------
get(index)          | O(1)      | O(n)
add(element) end    | O(1)*     | O(1)
add(index, element) | O(n)      | O(n)**
remove(index)       | O(n)      | O(n)**
iterator.remove()   | O(n)      | O(1)

* amortized due to occasional resizing
** O(n) to find position, but O(1) to insert/remove node

Interview answer: "Use ArrayList by default. LinkedList is rarely better
in practice due to poor cache locality and memory overhead."
```

3. **"Why is array access O(1)?"**
```
Answer:
Arrays use contiguous memory, so address calculation is:
  address = base_address + (index × element_size)

This is a constant-time arithmetic operation regardless of array size.
No traversal needed - direct memory access.

Bonus: This is why arrays have great cache performance!
Adjacent elements are likely in the same cache line.
```

4. **"Python list vs tuple - when to use which?"**
```
List:
- Mutable (can add, remove, change)
- Use for homogeneous collections
- Use when you need to modify
- More memory due to over-allocation

Tuple:
- Immutable (hashable, can be dict key)
- Use for heterogeneous data (like records)
- Use when data shouldn't change
- Slightly faster, less memory
- Can be used in sets, as dict keys

Interview tip: "Tuple for fixed structure (like coordinates, RGB),
list for collections that may change."
```

5. **"Implement dynamic array resizing"**
```python
class DynamicArray:
    def __init__(self):
        self.size = 0
        self.capacity = 1
        self.array = [None] * self.capacity

    def append(self, item):
        if self.size == self.capacity:
            self._resize(2 * self.capacity)
        self.array[self.size] = item
        self.size += 1

    def _resize(self, new_capacity):
        new_array = [None] * new_capacity
        for i in range(self.size):
            new_array[i] = self.array[i]
        self.array = new_array
        self.capacity = new_capacity

# Time complexity:
# - Single append: O(1) when space available, O(n) when resize needed
# - Amortized over n appends: O(1) per append
# - Total for n appends: O(n) - not O(n²)!
```

### 4.4 Common Interview Patterns

```python
# Pattern 1: Two Pointers on Array
def two_sum_sorted(arr, target):
    left, right = 0, len(arr) - 1
    while left < right:
        current = arr[left] + arr[right]
        if current == target:
            return [left, right]
        elif current < target:
            left += 1
        else:
            right -= 1
    return None

# Pattern 2: Sliding Window
def max_sum_subarray(arr, k):
    window = sum(arr[:k])
    max_sum = window
    for i in range(k, len(arr)):
        window += arr[i] - arr[i - k]
        max_sum = max(max_sum, window)
    return max_sum

# Pattern 3: In-place Modification
def remove_duplicates_sorted(arr):
    if not arr:
        return 0
    write_idx = 1
    for read_idx in range(1, len(arr)):
        if arr[read_idx] != arr[read_idx - 1]:
            arr[write_idx] = arr[read_idx]
            write_idx += 1
    return write_idx

# Pattern 4: Prefix Sum
def range_sum(arr, queries):
    prefix = [0]
    for x in arr:
        prefix.append(prefix[-1] + x)
    results = []
    for left, right in queries:
        results.append(prefix[right + 1] - prefix[left])
    return results

# Pattern 5: Dutch National Flag (3-way partition)
def sort_colors(arr):
    low, mid, high = 0, 0, len(arr) - 1
    while mid <= high:
        if arr[mid] == 0:
            arr[low], arr[mid] = arr[mid], arr[low]
            low += 1
            mid += 1
        elif arr[mid] == 1:
            mid += 1
        else:
            arr[mid], arr[high] = arr[high], arr[mid]
            high -= 1
```

---

## 5. Cross-References (관련 개념)

### Related Knowledge Bases

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F51** | Maps & Dictionaries | Key-value storage vs indexed storage |
| **F52** | Sets | Unordered unique collections |
| **F31** | Loops & Iteration | Iterating over arrays |
| **F43** | Higher-Order Functions | map, filter, reduce on arrays |
| **F11** | Closure Capture | Closures capturing loop variables |
| **F24** | Generics | Type-safe array containers |
| **00c** | Data Structures Intro | Overview of all structures |

### Algorithm Patterns Using Arrays

| Pattern | Use Case | Key Operation |
|---------|----------|---------------|
| Two Pointers | Sorted array pairs | O(n) scan |
| Sliding Window | Contiguous subarray | O(n) with fixed window |
| Prefix Sum | Range queries | O(1) per query after O(n) setup |
| Binary Search | Sorted array search | O(log n) |
| Quick Select | Kth element | O(n) average |
| Kadane's | Max subarray sum | O(n) |
| Dutch Flag | 3-way partition | O(n) single pass |

### Array Complexity Quick Reference

```
┌─────────────────────────────────────────────────────────────────────┐
│                  ARRAY/LIST CHEAT SHEET                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ TIME COMPLEXITY:                                                    │
│   Access by index:     O(1)                                        │
│   Search (unsorted):   O(n)                                        │
│   Search (sorted):     O(log n) binary search                      │
│   Insert at end:       O(1) amortized (dynamic)                    │
│   Insert at start:     O(n)                                        │
│   Insert at middle:    O(n)                                        │
│   Delete:              O(n)                                        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ LANGUAGE SYNTAX:                                                    │
│   Java:       int[] arr; ArrayList<T>                              │
│   Python:     list = [1, 2, 3]                                     │
│   TypeScript: const arr: T[] = []                                  │
│   Go:         var arr [N]T; slice []T                              │
│   SQL:        ARRAY[1, 2, 3]  (1-indexed!)                        │
│   C++:        std::vector<T>; std::array<T, N>                     │
│   Spark:      RDD, DataFrame (IMMUTABLE!)                          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ INTERVIEW CRITICAL:                                                 │
│   1. Go slice internals (len vs cap, shared backing array)         │
│   2. ArrayList vs LinkedList (use ArrayList 99% of time)           │
│   3. Array access O(1) because: base + index * size                │
│   4. Python list vs tuple (mutable vs immutable)                   │
│   5. Spark RDD/DF immutability (transformations create new)        │
│   6. SQL arrays are 1-indexed!                                     │
│   7. C++ vector vs array vs std::array                             │
│   8. JS: for...in (keys) vs for...of (values)                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ COMMON PITFALLS:                                                    │
│   - Off-by-one errors (< vs <=)                                    │
│   - Modifying while iterating (ConcurrentModification)             │
│   - JS var in loops (closure capture)                              │
│   - Go slice shared backing array                                  │
│   - Python [[0]*n]*m (shared rows!)                               │
│   - C++ iterator invalidation after insert/erase                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
