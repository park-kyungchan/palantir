# F52: Sets & Collections (집합과 컬렉션)

> **Concept ID**: `F52_sets_collections`
> **Universal Principle**: 중복 없는 고유 요소의 집합과 수학적 집합 연산을 지원하는 자료구조
> **Prerequisites**: F50_arrays_sequences (배열과 시퀀스), F51_hash_maps (해시 맵)

---

## 1. Universal Concept (언어 무관 개념 정의)

**Set (집합)**은 중복을 허용하지 않는 고유한 요소들의 모음입니다. 수학적 집합 이론에서 유래했으며, 프로그래밍에서는 멤버십 테스트, 중복 제거, 집합 연산에 최적화된 자료구조입니다.

### 1.1 Set의 핵심 특성

| 특성 | 설명 | 예시 |
|------|------|------|
| **유일성 (Uniqueness)** | 중복 요소 불허 | `{1, 2, 2, 3}` → `{1, 2, 3}` |
| **순서 무관 (Unordered)** | 순서 보장 안 함 (대부분) | `{3, 1, 2}` == `{1, 2, 3}` |
| **멤버십 테스트** | O(1) 평균 시간 복잡도 | `3 in {1, 2, 3}` → `true` |
| **집합 연산** | 합집합, 교집합, 차집합, 대칭차집합 | `A ∪ B`, `A ∩ B`, `A - B`, `A △ B` |

### 1.2 Mental Model: Mathematical Sets

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SET OPERATIONS VENN DIAGRAM                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│      Set A = {1, 2, 3, 4}              Set B = {3, 4, 5, 6}        │
│                                                                     │
│         ┌─────────┐     ┌─────────┐                                │
│         │  1  2   │     │   5  6  │                                │
│         │    ┌────┼─────┼────┐    │                                │
│         │    │ 3  │  4  │    │    │                                │
│         │    └────┼─────┼────┘    │                                │
│         │         │     │         │                                │
│         └─────────┘     └─────────┘                                │
│                                                                     │
│  UNION (A ∪ B):        {1, 2, 3, 4, 5, 6}    모든 요소             │
│  INTERSECTION (A ∩ B): {3, 4}                공통 요소              │
│  DIFFERENCE (A - B):   {1, 2}                A에만 있는 요소        │
│  DIFFERENCE (B - A):   {5, 6}                B에만 있는 요소        │
│  SYMMETRIC DIFF (A △ B): {1, 2, 5, 6}        한쪽에만 있는 요소    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Hash Set vs Tree Set

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HASH SET vs TREE SET                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  HASH SET (Unordered):                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Bucket 0: [cat]                                              │   │
│  │ Bucket 1: [dog, apple]  ← Hash collision handled             │   │
│  │ Bucket 2: []                                                 │   │
│  │ Bucket 3: [banana]                                           │   │
│  │ Bucket 4: [elephant]                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ✓ O(1) average lookup, insert, delete                             │
│  ✗ No ordering guarantee                                           │
│                                                                     │
│  TREE SET (Ordered/Sorted):                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              [dog]                                           │   │
│  │             /     \                                          │   │
│  │        [banana]  [elephant]                                  │   │
│  │         /                                                    │   │
│  │     [apple]                                                  │   │
│  │       /                                                      │   │
│  │    [cat]                                                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ✓ O(log n) lookup, insert, delete                                 │
│  ✓ Sorted order iteration                                          │
│  ✓ Range queries efficient                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 Time Complexity Comparison

| Operation | Hash Set | Tree Set | Array (unsorted) |
|-----------|----------|----------|------------------|
| **Insert** | O(1) avg, O(n) worst | O(log n) | O(1) or O(n) |
| **Delete** | O(1) avg, O(n) worst | O(log n) | O(n) |
| **Contains** | O(1) avg, O(n) worst | O(log n) | O(n) |
| **Iteration** | O(n) unordered | O(n) sorted | O(n) |
| **Min/Max** | O(n) | O(log n) or O(1) | O(n) |

### 1.5 Why Sets Matter

| Use Case | Why Set? | Alternative (Worse) |
|----------|----------|---------------------|
| **중복 제거** | O(n) with set | O(n^2) with list |
| **멤버십 테스트** | O(1) average | O(n) with list |
| **집합 연산** | Native support | Manual implementation |
| **Unique constraint** | Automatic enforcement | Manual checking |

---

## 2. Semantic Comparison Matrix (의미론적 비교 매트릭스)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **Hash Set** | `HashSet<T>` | `set` | `Set<T>` | `map[T]bool` | `DISTINCT` | `unordered_set<T>` | `distinct()` |
| **Sorted Set** | `TreeSet<T>` | N/A (SortedContainers) | N/A | N/A | `ORDER BY` | `set<T>` | N/A |
| **Immutable Set** | `Set.of()` | `frozenset` | N/A (readonly) | N/A | N/A (immutable by nature) | `const set<T>` | RDD |
| **Union** | `addAll()` | `\|` or `union()` | spread/concat | manual | `UNION` | `set_union` | `union()` |
| **Intersection** | `retainAll()` | `&` or `intersection()` | manual | manual | `INTERSECT` | `set_intersection` | `intersect()` |
| **Difference** | `removeAll()` | `-` or `difference()` | manual | manual | `EXCEPT` | `set_difference` | `subtract()` |
| **Membership** | `contains()` | `in` | `has()` | `_, ok := m[k]` | `WHERE col IN (...)` | `find() != end()` | `filter()` |

### 2.2 Detailed Code Examples

---

#### Pattern 1: Set Creation and Basic Operations

**Java (HashSet & TreeSet)**
```java
import java.util.*;

public class SetBasics {
    public static void main(String[] args) {
        // ==================================================
        // HashSet: Unordered, O(1) operations
        // ==================================================

        Set<String> hashSet = new HashSet<>();

        // Adding elements
        hashSet.add("apple");
        hashSet.add("banana");
        hashSet.add("apple");  // Duplicate - ignored!
        System.out.println(hashSet);  // [banana, apple] - unordered!

        // Membership test - O(1) average
        boolean hasApple = hashSet.contains("apple");  // true

        // Removing elements
        hashSet.remove("banana");

        // Size
        int size = hashSet.size();  // 1

        // Iteration (order not guaranteed)
        for (String item : hashSet) {
            System.out.println(item);
        }

        // ==================================================
        // TreeSet: Sorted, O(log n) operations
        // ==================================================

        Set<Integer> treeSet = new TreeSet<>();
        treeSet.addAll(Arrays.asList(5, 2, 8, 1, 9, 3));
        System.out.println(treeSet);  // [1, 2, 3, 5, 8, 9] - SORTED!

        // TreeSet-specific operations (NavigableSet interface)
        NavigableSet<Integer> navSet = new TreeSet<>(treeSet);

        // First and Last
        Integer first = navSet.first();  // 1
        Integer last = navSet.last();    // 9

        // Floor and Ceiling (nearest elements)
        Integer floor = navSet.floor(4);    // 3 (largest <= 4)
        Integer ceiling = navSet.ceiling(4); // 5 (smallest >= 4)

        // Subsets
        SortedSet<Integer> sub = navSet.subSet(2, 6);  // [2, 3, 5]
        SortedSet<Integer> head = navSet.headSet(5);   // [1, 2, 3]
        SortedSet<Integer> tail = navSet.tailSet(5);   // [5, 8, 9]

        // ==================================================
        // LinkedHashSet: Maintains insertion order
        // ==================================================

        Set<String> linkedSet = new LinkedHashSet<>();
        linkedSet.add("first");
        linkedSet.add("second");
        linkedSet.add("third");
        System.out.println(linkedSet);  // [first, second, third] - insertion order!

        // ==================================================
        // Immutable Set (Java 9+)
        // ==================================================

        Set<String> immutable = Set.of("a", "b", "c");
        // immutable.add("d");  // UnsupportedOperationException!

        // ==================================================
        // Creating Set from Array/Collection
        // ==================================================

        String[] array = {"a", "b", "a", "c"};
        Set<String> fromArray = new HashSet<>(Arrays.asList(array));
        // Or: Set.of(array) for immutable

        List<Integer> list = Arrays.asList(1, 2, 2, 3, 3, 3);
        Set<Integer> fromList = new HashSet<>(list);  // {1, 2, 3}

        // ==================================================
        // EnumSet: Optimized for enum values
        // ==================================================

        enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

        Set<Day> weekend = EnumSet.of(Day.SAT, Day.SUN);
        Set<Day> weekdays = EnumSet.range(Day.MON, Day.FRI);
        Set<Day> allDays = EnumSet.allOf(Day.class);
        Set<Day> noDays = EnumSet.noneOf(Day.class);
    }
}
```

**Python (set & frozenset)** - INTERVIEW FAVORITE!
```python
from typing import Set, FrozenSet

# ==================================================
# Basic Set Operations
# ==================================================

# Creating sets
empty_set = set()  # NOT {} - that's an empty dict!
numbers = {1, 2, 3, 4, 5}
from_list = set([1, 2, 2, 3, 3, 3])  # {1, 2, 3}
from_string = set("hello")  # {'h', 'e', 'l', 'o'}

# Adding elements
numbers.add(6)        # Add single element
numbers.update([7, 8, 9])  # Add multiple elements
numbers.update({10}, [11], (12,))  # Mix of iterables

# Removing elements
numbers.remove(1)     # Raises KeyError if not found
numbers.discard(100)  # No error if not found
popped = numbers.pop()  # Remove and return arbitrary element
numbers.clear()       # Remove all elements

# Membership test - O(1) average
if 3 in numbers:
    print("Found!")

# ==================================================
# SET OPERATORS - Python's killer feature!
# ==================================================

A = {1, 2, 3, 4}
B = {3, 4, 5, 6}

# UNION: All elements from both sets
union1 = A | B           # {1, 2, 3, 4, 5, 6}
union2 = A.union(B)      # Same result
union3 = A.union(B, {7, 8})  # Can take multiple args

# INTERSECTION: Elements in both sets
inter1 = A & B               # {3, 4}
inter2 = A.intersection(B)   # Same result

# DIFFERENCE: Elements in A but not in B
diff1 = A - B            # {1, 2}
diff2 = A.difference(B)  # Same result

# SYMMETRIC DIFFERENCE: Elements in either, but not both
sym1 = A ^ B                         # {1, 2, 5, 6}
sym2 = A.symmetric_difference(B)     # Same result

# ==================================================
# In-place operations (modify original set)
# ==================================================

C = {1, 2, 3}
C |= {4, 5}          # Union update: C = {1, 2, 3, 4, 5}
C &= {3, 4, 5, 6}    # Intersection update: C = {3, 4, 5}
C -= {5}             # Difference update: C = {3, 4}
C ^= {4, 5, 6}       # Symmetric diff update: C = {3, 5, 6}

# Method equivalents
D = {1, 2, 3}
D.update({4, 5})
D.intersection_update({3, 4, 5})
D.difference_update({5})
D.symmetric_difference_update({3, 6})

# ==================================================
# Set Comparisons
# ==================================================

X = {1, 2}
Y = {1, 2, 3, 4}

# Subset
X.issubset(Y)    # True (X <= Y)
X <= Y           # True
X < Y            # True (proper subset)

# Superset
Y.issuperset(X)  # True (Y >= X)
Y >= X           # True
Y > X            # True (proper superset)

# Disjoint (no common elements)
{1, 2}.isdisjoint({3, 4})  # True

# ==================================================
# frozenset: Immutable Set
# ==================================================

# frozenset cannot be modified after creation
frozen = frozenset([1, 2, 3])
# frozen.add(4)  # AttributeError!

# Why frozenset matters: Can be used as dict key or set element
regular_set = {1, 2, 3}
# bad_dict = {regular_set: "value"}  # TypeError: unhashable type: 'set'

frozen_set = frozenset([1, 2, 3])
good_dict = {frozen_set: "value"}  # Works!

# Set of sets (using frozenset)
set_of_sets = {frozenset([1, 2]), frozenset([3, 4])}

# frozenset supports all non-mutating operations
f1 = frozenset([1, 2, 3])
f2 = frozenset([3, 4, 5])
f1 | f2  # frozenset({1, 2, 3, 4, 5})
f1 & f2  # frozenset({3})

# ==================================================
# Set Comprehensions
# ==================================================

# Basic comprehension
squares = {x**2 for x in range(10)}  # {0, 1, 4, 9, 16, 25, 36, 49, 64, 81}

# With condition
even_squares = {x**2 for x in range(10) if x % 2 == 0}  # {0, 4, 16, 36, 64}

# Deduplication with transformation
words = ["Hello", "HELLO", "hello", "World"]
unique_lower = {w.lower() for w in words}  # {'hello', 'world'}

# ==================================================
# Common Patterns
# ==================================================

# Find duplicates in a list
items = [1, 2, 2, 3, 3, 3, 4]
seen = set()
duplicates = set()
for item in items:
    if item in seen:
        duplicates.add(item)
    seen.add(item)
# duplicates = {2, 3}

# Alternative: one-liner with Counter
from collections import Counter
duplicates = {item for item, count in Counter(items).items() if count > 1}

# Remove duplicates while preserving order (Python 3.7+)
def remove_duplicates_ordered(items):
    return list(dict.fromkeys(items))

# Find common elements across multiple lists
lists = [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
common = set.intersection(*map(set, lists))  # {3}

# Find all unique elements across lists
all_unique = set.union(*map(set, lists))  # {1, 2, 3, 4, 5}
```

**TypeScript (Set)**
```typescript
// ==================================================
// Basic Set Operations
// ==================================================

// Creating sets
const empty: Set<string> = new Set();
const numbers: Set<number> = new Set([1, 2, 3, 4, 5]);
const fromArray: Set<number> = new Set([1, 2, 2, 3, 3, 3]);  // {1, 2, 3}
const fromString: Set<string> = new Set("hello");  // {'h', 'e', 'l', 'o'}

// Adding elements
numbers.add(6);
numbers.add(6);  // Duplicate - ignored

// Removing elements
numbers.delete(6);     // Returns boolean (true if found)
numbers.clear();       // Remove all

// Membership test
const hasThree: boolean = numbers.has(3);  // true

// Size
const size: number = numbers.size;  // NOT .length!

// Iteration
for (const num of numbers) {
    console.log(num);
}

// forEach
numbers.forEach((value, _valueAgain, set) => {
    console.log(value);  // Note: Set forEach passes value twice!
});

// Convert to array
const array: number[] = [...numbers];
const array2: number[] = Array.from(numbers);

// ==================================================
// Set Operations (Manual Implementation!)
// TypeScript/JavaScript doesn't have built-in set operators
// ==================================================

const A: Set<number> = new Set([1, 2, 3, 4]);
const B: Set<number> = new Set([3, 4, 5, 6]);

// UNION: All elements from both sets
function union<T>(setA: Set<T>, setB: Set<T>): Set<T> {
    return new Set([...setA, ...setB]);
}
const unionResult: Set<number> = union(A, B);  // {1, 2, 3, 4, 5, 6}

// INTERSECTION: Elements in both sets
function intersection<T>(setA: Set<T>, setB: Set<T>): Set<T> {
    return new Set([...setA].filter(x => setB.has(x)));
}
const intersectResult: Set<number> = intersection(A, B);  // {3, 4}

// DIFFERENCE: Elements in A but not in B
function difference<T>(setA: Set<T>, setB: Set<T>): Set<T> {
    return new Set([...setA].filter(x => !setB.has(x)));
}
const diffResult: Set<number> = difference(A, B);  // {1, 2}

// SYMMETRIC DIFFERENCE: Elements in either, but not both
function symmetricDifference<T>(setA: Set<T>, setB: Set<T>): Set<T> {
    const diff1 = difference(setA, setB);
    const diff2 = difference(setB, setA);
    return union(diff1, diff2);
}
const symDiffResult: Set<number> = symmetricDifference(A, B);  // {1, 2, 5, 6}

// IS SUBSET
function isSubset<T>(setA: Set<T>, setB: Set<T>): boolean {
    return [...setA].every(x => setB.has(x));
}

// IS SUPERSET
function isSuperset<T>(setA: Set<T>, setB: Set<T>): boolean {
    return isSubset(setB, setA);
}

// ==================================================
// Set vs Array for Deduplication
// ==================================================

// Problem: Remove duplicates from array
const withDuplicates: number[] = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4];

// Solution 1: Set (recommended)
const unique1: number[] = [...new Set(withDuplicates)];  // [1, 2, 3, 4]

// Solution 2: filter with indexOf (O(n^2) - SLOW!)
const unique2: number[] = withDuplicates.filter(
    (item, index) => withDuplicates.indexOf(item) === index
);

// Performance comparison:
// Set: O(n) time complexity
// indexOf filter: O(n^2) time complexity

// ==================================================
// WeakSet: Set for Objects with Weak References
// ==================================================

const weakSet = new WeakSet();

let obj1 = { name: "object1" };
let obj2 = { name: "object2" };

weakSet.add(obj1);
weakSet.add(obj2);

console.log(weakSet.has(obj1));  // true

obj1 = null;  // obj1 can now be garbage collected
// weakSet automatically removes the reference

// WeakSet limitations:
// - Only objects (no primitives)
// - Not iterable (no forEach, no size)
// - No clear() method

// Use case: Track visited nodes, prevent memory leaks
function markVisited(node: object, visited: WeakSet<object>): boolean {
    if (visited.has(node)) return false;
    visited.add(node);
    return true;
}

// ==================================================
// Practical Patterns
// ==================================================

// Find duplicates
function findDuplicates<T>(arr: T[]): T[] {
    const seen = new Set<T>();
    const duplicates = new Set<T>();

    for (const item of arr) {
        if (seen.has(item)) {
            duplicates.add(item);
        } else {
            seen.add(item);
        }
    }

    return [...duplicates];
}

// Find intersection of multiple arrays
function intersectMultiple<T>(...arrays: T[][]): T[] {
    if (arrays.length === 0) return [];

    const sets = arrays.map(arr => new Set(arr));
    const firstSet = sets[0];

    return [...firstSet].filter(item =>
        sets.every(set => set.has(item))
    );
}

// Count unique values
interface Item {
    category: string;
    value: number;
}

const items: Item[] = [
    { category: "A", value: 1 },
    { category: "B", value: 2 },
    { category: "A", value: 3 },
];

const uniqueCategories = new Set(items.map(item => item.category));
console.log(uniqueCategories.size);  // 2
```

**Go (Implementing Set with map)** - INTERVIEW CRITICAL!
```go
package main

import "fmt"

// ==================================================
// Go has NO built-in set type!
// Implement using map[T]bool or map[T]struct{}
// ==================================================

// Option 1: map[T]bool (simpler, uses more memory)
func SetWithBool() {
    // Create set
    set := make(map[string]bool)

    // Add elements
    set["apple"] = true
    set["banana"] = true
    set["apple"] = true  // Duplicate - just overwrites

    // Membership test
    if set["apple"] {
        fmt.Println("apple is in set")
    }

    // Better pattern: use comma-ok idiom
    if _, exists := set["grape"]; !exists {
        fmt.Println("grape is NOT in set")
    }

    // Remove element
    delete(set, "banana")

    // Size
    size := len(set)
    fmt.Println("Size:", size)

    // Iterate
    for item := range set {
        fmt.Println(item)
    }
}

// Option 2: map[T]struct{} (memory-efficient, preferred)
func SetWithStruct() {
    // struct{} is zero bytes!
    set := make(map[string]struct{})

    // Add elements
    set["apple"] = struct{}{}
    set["banana"] = struct{}{}

    // Membership test
    if _, exists := set["apple"]; exists {
        fmt.Println("apple is in set")
    }

    // Remove
    delete(set, "banana")

    // Iterate
    for item := range set {
        fmt.Println(item)
    }
}

// ==================================================
// Generic Set Type (Go 1.18+)
// ==================================================

type Set[T comparable] map[T]struct{}

func NewSet[T comparable](items ...T) Set[T] {
    s := make(Set[T])
    for _, item := range items {
        s[item] = struct{}{}
    }
    return s
}

func (s Set[T]) Add(item T) {
    s[item] = struct{}{}
}

func (s Set[T]) Remove(item T) {
    delete(s, item)
}

func (s Set[T]) Contains(item T) bool {
    _, exists := s[item]
    return exists
}

func (s Set[T]) Size() int {
    return len(s)
}

func (s Set[T]) ToSlice() []T {
    result := make([]T, 0, len(s))
    for item := range s {
        result = append(result, item)
    }
    return result
}

// Set Operations
func (s Set[T]) Union(other Set[T]) Set[T] {
    result := NewSet[T]()
    for item := range s {
        result.Add(item)
    }
    for item := range other {
        result.Add(item)
    }
    return result
}

func (s Set[T]) Intersection(other Set[T]) Set[T] {
    result := NewSet[T]()
    // Iterate over smaller set for efficiency
    if len(s) > len(other) {
        s, other = other, s
    }
    for item := range s {
        if other.Contains(item) {
            result.Add(item)
        }
    }
    return result
}

func (s Set[T]) Difference(other Set[T]) Set[T] {
    result := NewSet[T]()
    for item := range s {
        if !other.Contains(item) {
            result.Add(item)
        }
    }
    return result
}

func (s Set[T]) SymmetricDifference(other Set[T]) Set[T] {
    return s.Difference(other).Union(other.Difference(s))
}

func (s Set[T]) IsSubset(other Set[T]) bool {
    for item := range s {
        if !other.Contains(item) {
            return false
        }
    }
    return true
}

func main() {
    // Using generic Set
    A := NewSet(1, 2, 3, 4)
    B := NewSet(3, 4, 5, 6)

    fmt.Println("A:", A.ToSlice())
    fmt.Println("B:", B.ToSlice())
    fmt.Println("Union:", A.Union(B).ToSlice())
    fmt.Println("Intersection:", A.Intersection(B).ToSlice())
    fmt.Println("A - B:", A.Difference(B).ToSlice())
    fmt.Println("Symmetric Diff:", A.SymmetricDifference(B).ToSlice())

    // String set
    fruits := NewSet("apple", "banana", "cherry")
    fmt.Println("Has apple:", fruits.Contains("apple"))
}

// ==================================================
// Why doesn't Go have a built-in set?
// Interview Answer:
// 1. Go philosophy: simplicity and explicitness
// 2. map[T]struct{} is efficient and idiomatic
// 3. Avoids adding another core type
// 4. Different use cases need different implementations
// ==================================================
```

**SQL (Set Operations)**
```sql
-- ==================================================
-- SQL Set Operations work on RESULT SETS (rows)
-- Not on individual columns
-- ==================================================

-- Sample tables
CREATE TABLE employees_a (
    id INT,
    name VARCHAR(100),
    department VARCHAR(50)
);

CREATE TABLE employees_b (
    id INT,
    name VARCHAR(100),
    department VARCHAR(50)
);

-- ==================================================
-- DISTINCT: Remove duplicates (single table)
-- ==================================================

-- Get unique departments
SELECT DISTINCT department FROM employees_a;

-- Distinct on multiple columns
SELECT DISTINCT department, name FROM employees_a;

-- COUNT(DISTINCT ...) for counting unique values
SELECT COUNT(DISTINCT department) AS unique_departments
FROM employees_a;

-- ==================================================
-- UNION: Combine rows from two queries (removes duplicates)
-- ==================================================

-- All employees from both tables (no duplicates)
SELECT id, name, department FROM employees_a
UNION
SELECT id, name, department FROM employees_b;

-- UNION ALL: Keep duplicates (faster, no dedup overhead)
SELECT id, name, department FROM employees_a
UNION ALL
SELECT id, name, department FROM employees_b;

-- When to use which:
-- UNION:     Need unique results, can afford dedup cost
-- UNION ALL: Keep duplicates OR sure there are none

-- ==================================================
-- INTERSECT: Common rows in both queries
-- ==================================================

-- Employees in both tables
SELECT id, name, department FROM employees_a
INTERSECT
SELECT id, name, department FROM employees_b;

-- Note: Not all databases support INTERSECT
-- Alternative using JOIN:
SELECT DISTINCT a.id, a.name, a.department
FROM employees_a a
INNER JOIN employees_b b
    ON a.id = b.id AND a.name = b.name AND a.department = b.department;

-- ==================================================
-- EXCEPT (or MINUS in Oracle): Rows in first but not second
-- ==================================================

-- Employees only in table A
SELECT id, name, department FROM employees_a
EXCEPT
SELECT id, name, department FROM employees_b;

-- Alternative using LEFT JOIN:
SELECT a.id, a.name, a.department
FROM employees_a a
LEFT JOIN employees_b b
    ON a.id = b.id AND a.name = b.name AND a.department = b.department
WHERE b.id IS NULL;

-- Alternative using NOT EXISTS:
SELECT a.id, a.name, a.department
FROM employees_a a
WHERE NOT EXISTS (
    SELECT 1 FROM employees_b b
    WHERE a.id = b.id AND a.name = b.name AND a.department = b.department
);

-- ==================================================
-- IN / NOT IN: Membership testing
-- ==================================================

-- Employees in specific departments
SELECT * FROM employees_a
WHERE department IN ('Engineering', 'Sales', 'Marketing');

-- Using subquery
SELECT * FROM employees_a
WHERE id IN (SELECT id FROM employees_b);

-- NOT IN (caution with NULLs!)
SELECT * FROM employees_a
WHERE id NOT IN (SELECT id FROM employees_b WHERE id IS NOT NULL);

-- ==================================================
-- GROUP BY with aggregations (like reduce)
-- ==================================================

-- Count per department (unique grouping)
SELECT department, COUNT(*) as employee_count
FROM employees_a
GROUP BY department;

-- Multiple aggregations
SELECT
    department,
    COUNT(*) as total,
    COUNT(DISTINCT name) as unique_names,
    MIN(id) as min_id,
    MAX(id) as max_id
FROM employees_a
GROUP BY department;

-- ==================================================
-- ARRAY_AGG / COLLECT_SET (Database-specific)
-- ==================================================

-- PostgreSQL: Collect into array
SELECT department, ARRAY_AGG(DISTINCT name) as names
FROM employees_a
GROUP BY department;

-- Spark SQL: Collect into set
-- SELECT department, COLLECT_SET(name) as names
-- FROM employees_a
-- GROUP BY department;

-- ==================================================
-- Set Comparison Patterns
-- ==================================================

-- Check if two columns have same set of values
-- (Symmetric difference should be empty)
WITH
    set_a AS (SELECT DISTINCT department FROM employees_a),
    set_b AS (SELECT DISTINCT department FROM employees_b)
SELECT
    CASE
        WHEN NOT EXISTS (
            (SELECT * FROM set_a EXCEPT SELECT * FROM set_b)
            UNION
            (SELECT * FROM set_b EXCEPT SELECT * FROM set_a)
        )
        THEN 'Equal'
        ELSE 'Not Equal'
    END AS sets_equal;
```

**C++ (unordered_set & set)**
```cpp
#include <iostream>
#include <set>
#include <unordered_set>
#include <algorithm>
#include <vector>
#include <iterator>

int main() {
    // ==================================================
    // unordered_set: Hash-based, O(1) average
    // ==================================================

    std::unordered_set<int> hashSet;

    // Insert elements
    hashSet.insert(5);
    hashSet.insert(2);
    hashSet.insert(8);
    hashSet.insert(2);  // Duplicate - ignored

    // Membership test - O(1) average
    if (hashSet.find(5) != hashSet.end()) {
        std::cout << "5 found" << std::endl;
    }

    // count() returns 0 or 1
    if (hashSet.count(5) > 0) {
        std::cout << "5 found" << std::endl;
    }

    // C++20: contains() method
    // if (hashSet.contains(5)) { ... }

    // Remove element
    hashSet.erase(2);

    // Size
    std::cout << "Size: " << hashSet.size() << std::endl;

    // Iteration (unordered!)
    for (int x : hashSet) {
        std::cout << x << " ";
    }
    std::cout << std::endl;

    // Initialize from initializer list
    std::unordered_set<std::string> words = {"apple", "banana", "cherry"};

    // ==================================================
    // set (TreeSet): Red-black tree, O(log n), SORTED
    // ==================================================

    std::set<int> treeSet;
    treeSet.insert(5);
    treeSet.insert(2);
    treeSet.insert(8);
    treeSet.insert(1);

    // Iteration is SORTED
    for (int x : treeSet) {
        std::cout << x << " ";  // 1 2 5 8
    }
    std::cout << std::endl;

    // Range operations
    auto low = treeSet.lower_bound(3);   // First >= 3, points to 5
    auto up = treeSet.upper_bound(5);    // First > 5, points to 8

    // Elements in range [2, 8)
    for (auto it = treeSet.lower_bound(2); it != treeSet.upper_bound(7); ++it) {
        std::cout << *it << " ";  // 2 5
    }
    std::cout << std::endl;

    // ==================================================
    // Set Operations using STL algorithms
    // ==================================================

    std::set<int> A = {1, 2, 3, 4};
    std::set<int> B = {3, 4, 5, 6};

    std::vector<int> result;

    // UNION
    result.clear();
    std::set_union(
        A.begin(), A.end(),
        B.begin(), B.end(),
        std::back_inserter(result)
    );
    // result: {1, 2, 3, 4, 5, 6}

    // INTERSECTION
    result.clear();
    std::set_intersection(
        A.begin(), A.end(),
        B.begin(), B.end(),
        std::back_inserter(result)
    );
    // result: {3, 4}

    // DIFFERENCE (A - B)
    result.clear();
    std::set_difference(
        A.begin(), A.end(),
        B.begin(), B.end(),
        std::back_inserter(result)
    );
    // result: {1, 2}

    // SYMMETRIC DIFFERENCE
    result.clear();
    std::set_symmetric_difference(
        A.begin(), A.end(),
        B.begin(), B.end(),
        std::back_inserter(result)
    );
    // result: {1, 2, 5, 6}

    // Check if subset
    bool isSubset = std::includes(B.begin(), B.end(), A.begin(), A.end());

    // ==================================================
    // Custom comparison (sorted in reverse)
    // ==================================================

    std::set<int, std::greater<int>> reverseSet = {1, 2, 3, 4, 5};
    // Iteration: 5, 4, 3, 2, 1

    // Custom struct with comparator
    struct Person {
        std::string name;
        int age;
    };

    auto cmp = [](const Person& a, const Person& b) {
        return a.age < b.age;  // Sort by age
    };

    std::set<Person, decltype(cmp)> people(cmp);
    people.insert({"Alice", 30});
    people.insert({"Bob", 25});

    // ==================================================
    // multiset: Allows duplicates
    // ==================================================

    std::multiset<int> multiSet;
    multiSet.insert(5);
    multiSet.insert(5);
    multiSet.insert(5);

    std::cout << "Count of 5: " << multiSet.count(5) << std::endl;  // 3

    return 0;
}
```

**Spark (distinct and set-like operations)** - CRITICAL FOR PALANTIR!
```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, IntegerType

spark = SparkSession.builder.appName("SetOperations").getOrCreate()

# ==================================================
# DataFrame Set Operations
# ==================================================

# Sample DataFrames
data_a = [(1, "Alice"), (2, "Bob"), (3, "Charlie"), (4, "Diana")]
data_b = [(3, "Charlie"), (4, "Diana"), (5, "Eve"), (6, "Frank")]

df_a = spark.createDataFrame(data_a, ["id", "name"])
df_b = spark.createDataFrame(data_b, ["id", "name"])

# ==================================================
# DISTINCT: Remove duplicate rows
# ==================================================

# Distinct on all columns
df_distinct = df_a.distinct()

# Distinct on specific columns using dropDuplicates
df_unique_names = df_a.dropDuplicates(["name"])

# Count distinct values
distinct_count = df_a.select(F.countDistinct("name")).collect()[0][0]

# Approximate distinct (faster for large datasets)
approx_count = df_a.select(F.approx_count_distinct("name")).collect()[0][0]

# ==================================================
# UNION: Combine rows (keeps duplicates by default)
# ==================================================

# Union (keeps all rows, including duplicates)
union_df = df_a.union(df_b)
union_df.show()
# +---+-------+
# | id|   name|
# +---+-------+
# |  1|  Alice|
# |  2|    Bob|
# |  3|Charlie|
# |  4|  Diana|
# |  3|Charlie|  <- Duplicate
# |  4|  Diana|  <- Duplicate
# |  5|    Eve|
# |  6|  Frank|
# +---+-------+

# Union with deduplication
union_distinct = df_a.union(df_b).distinct()

# unionByName (matches columns by name, not position)
union_by_name = df_a.unionByName(df_b)

# ==================================================
# INTERSECT: Common rows
# ==================================================

intersect_df = df_a.intersect(df_b)
intersect_df.show()
# +---+-------+
# | id|   name|
# +---+-------+
# |  3|Charlie|
# |  4|  Diana|
# +---+-------+

# intersectAll preserves duplicates (Spark 2.4+)
intersect_all = df_a.intersectAll(df_b)

# ==================================================
# SUBTRACT (EXCEPT): Rows in A but not in B
# ==================================================

subtract_df = df_a.subtract(df_b)
subtract_df.show()
# +---+-----+
# | id| name|
# +---+-----+
# |  1|Alice|
# |  2|  Bob|
# +---+-----+

# exceptAll preserves duplicates
except_all = df_a.exceptAll(df_b)

# ==================================================
# Array Column Set Operations (Spark 2.4+)
# ==================================================

# Sample data with array columns
array_data = [
    (1, [1, 2, 3, 4], [3, 4, 5, 6]),
    (2, [10, 20], [20, 30, 40]),
]
array_df = spark.createDataFrame(array_data, ["id", "arr_a", "arr_b"])

# array_distinct: Remove duplicates within array
data_with_dups = [(1, [1, 2, 2, 3, 3, 3])]
dup_df = spark.createDataFrame(data_with_dups, ["id", "arr"])
dup_df.select("id", F.array_distinct("arr").alias("unique_arr")).show()
# +---+----------+
# | id|unique_arr|
# +---+----------+
# |  1| [1, 2, 3]|
# +---+----------+

# array_union: Union of two arrays
array_df.select(
    "id",
    F.array_union("arr_a", "arr_b").alias("union")
).show()
# +---+------------------+
# | id|             union|
# +---+------------------+
# |  1|[1, 2, 3, 4, 5, 6]|
# |  2|  [10, 20, 30, 40]|
# +---+------------------+

# array_intersect: Intersection of two arrays
array_df.select(
    "id",
    F.array_intersect("arr_a", "arr_b").alias("intersect")
).show()
# +---+---------+
# | id|intersect|
# +---+---------+
# |  1|   [3, 4]|
# |  2|     [20]|
# +---+---------+

# array_except: Difference of two arrays
array_df.select(
    "id",
    F.array_except("arr_a", "arr_b").alias("diff")
).show()
# +---+------+
# | id|  diff|
# +---+------+
# |  1|[1, 2]|
# |  2|  [10]|
# +---+------+

# ==================================================
# collect_set: Aggregate to set (removes duplicates)
# ==================================================

# Sample data
sales_data = [
    ("Alice", "Electronics"),
    ("Bob", "Electronics"),
    ("Alice", "Books"),
    ("Charlie", "Electronics"),
    ("Alice", "Electronics"),  # Duplicate
]
sales_df = spark.createDataFrame(sales_data, ["name", "category"])

# Group and collect unique categories per person
sales_df.groupBy("name").agg(
    F.collect_set("category").alias("categories"),
    F.collect_list("category").alias("all_categories")  # Keeps duplicates
).show(truncate=False)
# +-------+---------------------+---------------------------+
# |name   |categories           |all_categories             |
# +-------+---------------------+---------------------------+
# |Alice  |[Electronics, Books] |[Electronics, Books, Elec..]|
# |Bob    |[Electronics]        |[Electronics]              |
# |Charlie|[Electronics]        |[Electronics]              |
# +-------+---------------------+---------------------------+

# ==================================================
# RDD Set Operations
# ==================================================

rdd_a = spark.sparkContext.parallelize([1, 2, 3, 4])
rdd_b = spark.sparkContext.parallelize([3, 4, 5, 6])

# distinct
rdd_a.distinct().collect()  # [1, 2, 3, 4]

# union (keeps duplicates)
rdd_a.union(rdd_b).collect()  # [1, 2, 3, 4, 3, 4, 5, 6]

# intersection
rdd_a.intersection(rdd_b).collect()  # [3, 4]

# subtract
rdd_a.subtract(rdd_b).collect()  # [1, 2]

# ==================================================
# Performance Considerations (INTERVIEW CRITICAL!)
# ==================================================

# 1. distinct() causes shuffle - expensive!
# Use dropDuplicates() on specific columns when possible

# 2. intersect/subtract are expensive - cause multiple shuffles
# Alternative: Use join for better control
df_a.alias("a").join(
    df_b.alias("b"),
    (F.col("a.id") == F.col("b.id")) & (F.col("a.name") == F.col("b.name")),
    "inner"  # For intersection
    # "left_anti"  # For subtract
).select("a.*")

# 3. collect_set on large cardinality columns can cause memory issues
# Use approx_count_distinct for cardinality estimation first

# 4. Broadcast smaller DataFrame in set operations
from pyspark.sql.functions import broadcast
df_a.intersect(broadcast(df_b))
```

---

#### Pattern 2: Java Collections Framework Overview

**Java (List, Set, Map, Queue - The Big Picture)**
```java
import java.util.*;

/*
 * Java Collections Framework Hierarchy:
 *
 *                    Iterable<T>
 *                         │
 *                    Collection<T>
 *                    ┌────┴────┐
 *                    │         │
 *              List<T>       Set<T>         Queue<T>
 *                │             │               │
 *         ┌──────┼──────┐   ┌──┴───┐      ┌───┴───┐
 *      ArrayList   LinkedList  HashSet  TreeSet  PriorityQueue
 *                               │
 *                         LinkedHashSet
 *
 * Separate hierarchy:
 *                     Map<K,V>
 *              ┌────────┼────────┐
 *           HashMap   TreeMap   LinkedHashMap
 */

public class CollectionsOverview {
    public static void main(String[] args) {

        // ==================================================
        // LIST: Ordered, allows duplicates, index access
        // ==================================================

        // ArrayList: Dynamic array, O(1) random access, O(n) insert/delete
        List<String> arrayList = new ArrayList<>();
        arrayList.add("first");
        arrayList.add("second");
        arrayList.add("first");  // Allows duplicate
        arrayList.get(0);        // O(1) access

        // LinkedList: Doubly-linked, O(n) access, O(1) insert/delete at ends
        List<String> linkedList = new LinkedList<>();
        ((LinkedList<String>) linkedList).addFirst("front");
        ((LinkedList<String>) linkedList).addLast("back");

        // When to use which:
        // ArrayList: Random access, iteration, rarely insert in middle
        // LinkedList: Frequent add/remove at ends, implement queue/deque

        // ==================================================
        // SET: Unique elements, fast lookup
        // ==================================================

        // HashSet: O(1) ops, unordered
        Set<String> hashSet = new HashSet<>();
        hashSet.add("apple");
        hashSet.add("apple");  // Ignored - duplicate
        hashSet.contains("apple");  // O(1)

        // TreeSet: O(log n) ops, sorted
        Set<String> treeSet = new TreeSet<>();
        // Iteration is sorted

        // LinkedHashSet: O(1) ops, maintains insertion order
        Set<String> linkedHashSet = new LinkedHashSet<>();

        // ==================================================
        // MAP: Key-Value pairs
        // ==================================================

        // HashMap: O(1) ops, unordered
        Map<String, Integer> hashMap = new HashMap<>();
        hashMap.put("key", 1);
        hashMap.get("key");           // 1
        hashMap.getOrDefault("x", 0); // 0 if not found
        hashMap.containsKey("key");   // true
        hashMap.containsValue(1);     // true (O(n)!)

        // TreeMap: O(log n) ops, sorted by key
        Map<String, Integer> treeMap = new TreeMap<>();

        // LinkedHashMap: O(1) ops, maintains insertion order
        Map<String, Integer> linkedHashMap = new LinkedHashMap<>();

        // ==================================================
        // QUEUE & DEQUE: FIFO and double-ended
        // ==================================================

        // Queue: FIFO
        Queue<String> queue = new LinkedList<>();
        queue.offer("first");   // Add to tail
        queue.peek();           // View head (null if empty)
        queue.poll();           // Remove head (null if empty)

        // PriorityQueue: Heap-based, sorted order
        Queue<Integer> pq = new PriorityQueue<>();
        pq.offer(3);
        pq.offer(1);
        pq.offer(2);
        pq.poll();  // Returns 1 (smallest)

        // Deque: Double-ended queue
        Deque<String> deque = new ArrayDeque<>();
        deque.addFirst("front");
        deque.addLast("back");
        deque.pollFirst();  // Remove from front
        deque.pollLast();   // Remove from back

        // ==================================================
        // Choosing the Right Collection
        // ==================================================

        /*
         * Need unique elements?
         *   YES → Set
         *     Need sorted order? → TreeSet
         *     Need insertion order? → LinkedHashSet
         *     Just uniqueness? → HashSet
         *   NO → List or other
         *
         * Need key-value mapping?
         *   YES → Map
         *     Need sorted keys? → TreeMap
         *     Need insertion order? → LinkedHashMap
         *     Just mapping? → HashMap
         *
         * Need FIFO order?
         *   YES → Queue/Deque
         *     Need priority? → PriorityQueue
         *     Need double-ended? → ArrayDeque
         */

        // ==================================================
        // Immutable Collections (Java 9+)
        // ==================================================

        List<String> immutableList = List.of("a", "b", "c");
        Set<String> immutableSet = Set.of("a", "b", "c");
        Map<String, Integer> immutableMap = Map.of("a", 1, "b", 2);

        // ==================================================
        // Conversion Between Collections
        // ==================================================

        List<String> list = Arrays.asList("a", "b", "a", "c");

        // List to Set (deduplicate)
        Set<String> set = new HashSet<>(list);

        // Set to List
        List<String> backToList = new ArrayList<>(set);

        // Array to List
        String[] array = {"x", "y", "z"};
        List<String> fromArray = Arrays.asList(array);  // Fixed size!
        List<String> mutableFromArray = new ArrayList<>(Arrays.asList(array));

        // List to Array
        String[] backToArray = list.toArray(new String[0]);
    }
}
```

---

### 2.3 Common Pitfalls by Language

#### Java Pitfalls
```java
// 1. HashSet with mutable objects
class Person {
    String name;
    // hashCode depends on name
}
Set<Person> people = new HashSet<>();
Person p = new Person();
p.name = "Alice";
people.add(p);
p.name = "Bob";  // Modifying after adding - BAD!
people.contains(p);  // May return false!
// Solution: Use immutable objects or don't modify after adding

// 2. TreeSet with incomparable elements
Set<Object> bad = new TreeSet<>();
bad.add("string");
bad.add(123);  // ClassCastException! Can't compare String to Integer
// Solution: Use single type or provide custom Comparator

// 3. null handling differences
Set<String> hashSet = new HashSet<>();
hashSet.add(null);  // OK!

Set<String> treeSet = new TreeSet<>();
// treeSet.add(null);  // NullPointerException! (can't compare null)

// 4. ConcurrentModificationException
Set<Integer> set = new HashSet<>(Arrays.asList(1, 2, 3, 4, 5));
for (Integer n : set) {
    if (n % 2 == 0) {
        set.remove(n);  // ConcurrentModificationException!
    }
}
// Solution: Use Iterator.remove() or collect to remove later
Iterator<Integer> it = set.iterator();
while (it.hasNext()) {
    if (it.next() % 2 == 0) {
        it.remove();  // Safe!
    }
}
```

#### Python Pitfalls
```python
# 1. Confusing {} with empty set
empty = {}          # This is an empty DICT!
empty_set = set()   # This is an empty set

# 2. Unhashable types in sets
# bad_set = {[1, 2, 3]}  # TypeError! Lists are unhashable
good_set = {(1, 2, 3)}   # Tuples are OK

# 3. Modifying set during iteration
s = {1, 2, 3, 4, 5}
# for x in s:
#     if x % 2 == 0:
#         s.remove(x)  # RuntimeError!
# Solution: Create copy or collect items first
s = {x for x in s if x % 2 != 0}  # Set comprehension

# 4. frozenset is not the same as set
regular = {1, 2, 3}
frozen = frozenset([1, 2, 3])
regular == frozen  # True (value equality)
type(regular) == type(frozen)  # False

# 5. Set operations create new sets
a = {1, 2, 3}
b = a | {4, 5}
# a is unchanged! b is new set
# Use |= for in-place update
a |= {4, 5}  # Now a is modified
```

#### TypeScript Pitfalls
```typescript
// 1. Set only checks reference equality for objects
const set = new Set<{ id: number }>();
set.add({ id: 1 });
set.add({ id: 1 });  // Added! Different object references
console.log(set.size);  // 2, not 1!

// Solution: Use primitive values or manage references
const map = new Map<number, { id: number }>();
map.set(1, { id: 1 });
map.set(1, { id: 1 });  // Overwrites, size stays 1

// 2. No built-in set operations
const a = new Set([1, 2, 3]);
const b = new Set([3, 4, 5]);
// const union = a.union(b);  // Error! No such method

// Must implement manually or use libraries

// 3. forEach signature is weird
const set2 = new Set(['a', 'b', 'c']);
set2.forEach((value, valueAgain, set) => {
    // Both value and valueAgain are the same!
    // This matches Map's forEach signature
});

// 4. Cannot use Set as object key
const obj: { [key: string]: number } = {};
const set3 = new Set([1, 2, 3]);
// obj[set3] = 1;  // set3 becomes "[object Set]" string
```

#### Go Pitfalls
```go
// 1. Map iteration order is random
set := map[string]bool{"a": true, "b": true, "c": true}
for k := range set {
    fmt.Println(k)  // Different order each run!
}
// Solution: Sort keys if order matters

// 2. Zero value confusion
set2 := make(map[string]bool)
fmt.Println(set2["nonexistent"])  // false (zero value of bool)
// Is it in the set with value false, or not in set?
// Solution: Use comma-ok idiom
if _, exists := set2["key"]; exists {
    // Actually in set
}

// 3. Nil map panic
var nilMap map[string]bool
// nilMap["key"] = true  // panic: assignment to nil map
// Solution: Always initialize
nilMap = make(map[string]bool)
```

---

## 3. Design Philosophy Links (공식 문서 출처)

### Official Documentation

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| **Java** | [Collections Framework](https://docs.oracle.com/javase/8/docs/technotes/guides/collections/) | Set Interface |
| **Java** | [HashSet Javadoc](https://docs.oracle.com/javase/8/docs/api/java/util/HashSet.html) | Implementation Details |
| **Java** | [TreeSet Javadoc](https://docs.oracle.com/javase/8/docs/api/java/util/TreeSet.html) | NavigableSet |
| **Python** | [Sets Documentation](https://docs.python.org/3/library/stdtypes.html#set-types-set-frozenset) | Set Operations |
| **Python** | [frozenset](https://docs.python.org/3/library/stdtypes.html#frozenset) | Immutable Sets |
| **TypeScript** | [Set Reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set) | MDN |
| **TypeScript** | [WeakSet Reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakSet) | Weak References |
| **Go** | [Effective Go](https://go.dev/doc/effective_go#maps) | Maps as Sets |
| **Go** | [Maps in Action](https://go.dev/blog/maps) | Implementation Details |
| **SQL** | [SQL Standard](https://www.iso.org/standard/63555.html) | Set Operations |
| **C++** | [std::set](https://en.cppreference.com/w/cpp/container/set) | Ordered Set |
| **C++** | [std::unordered_set](https://en.cppreference.com/w/cpp/container/unordered_set) | Hash Set |
| **Spark** | [DataFrame API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/dataframe.html) | Set Operations |
| **Spark** | [Array Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html#array-functions) | Array Set Operations |

### Design Philosophy Quotes

> **Python**: "Sets are the bread and butter of computing with unique collections."
> — Raymond Hettinger, Python Core Developer

> **Java**: "The Set interface is a Collection that cannot contain duplicate elements."
> — Java Collections Framework Documentation

> **Go**: "The Go team felt that the map type was sufficient for set operations."
> — Go FAQ on why there's no built-in set

---

## 4. Palantir Context Hint (팔란티어 맥락 힌트)

### 4.1 Spark Set Operations (CRITICAL!)

```python
# Palantir Foundry heavily uses Spark for data processing
# Understanding set operations on DataFrames is ESSENTIAL

# Common pattern: Find changes between two dataset versions
previous_df = spark.read.parquet("previous_version.parquet")
current_df = spark.read.parquet("current_version.parquet")

# New records (in current but not in previous)
new_records = current_df.subtract(previous_df)

# Deleted records (in previous but not in current)
deleted_records = previous_df.subtract(current_df)

# Changed records (using unique key)
from pyspark.sql.functions import col, hash as spark_hash

# Create hash of all columns except key
prev_hashed = previous_df.withColumn("row_hash", spark_hash(*[c for c in previous_df.columns if c != "id"]))
curr_hashed = current_df.withColumn("row_hash", spark_hash(*[c for c in current_df.columns if c != "id"]))

# Join on key, filter where hash changed
changed = prev_hashed.alias("prev").join(
    curr_hashed.alias("curr"),
    col("prev.id") == col("curr.id"),
    "inner"
).filter(col("prev.row_hash") != col("curr.row_hash")).select("curr.*")
```

### 4.2 SQL Set Operations in Queries

```sql
-- Finding data discrepancies between systems
-- System A data
WITH system_a AS (
    SELECT customer_id, order_count
    FROM orders_system_a
    GROUP BY customer_id
),
-- System B data
system_b AS (
    SELECT customer_id, order_count
    FROM orders_system_b
    GROUP BY customer_id
)

-- Customers only in System A
SELECT customer_id, 'Only in A' as status
FROM system_a
EXCEPT
SELECT customer_id, 'Only in A'
FROM system_b

UNION ALL

-- Customers only in System B
SELECT customer_id, 'Only in B' as status
FROM system_b
EXCEPT
SELECT customer_id, 'Only in B'
FROM system_a;
```

### 4.3 Interview Questions (HIGHEST PRIORITY)

1. **"Implement set operations without using built-in set"**
```python
def union(list_a: list, list_b: list) -> list:
    """Union without using set - O(n^2) naive"""
    result = list_a.copy()
    for item in list_b:
        if item not in result:  # O(n) check
            result.append(item)
    return result

def union_optimized(list_a: list, list_b: list) -> list:
    """Union using dict for O(n) - simulating set behavior"""
    seen = {}
    for item in list_a:
        seen[item] = True
    for item in list_b:
        seen[item] = True
    return list(seen.keys())

def intersection(list_a: list, list_b: list) -> list:
    """Intersection without set"""
    set_b = {item: True for item in list_b}  # Convert to dict for O(1) lookup
    return [item for item in list_a if item in set_b]

def difference(list_a: list, list_b: list) -> list:
    """Difference (A - B) without set"""
    set_b = {item: True for item in list_b}
    return [item for item in list_a if item not in set_b]
```

2. **"HashSet vs TreeSet - which to use when?"**
```
HashSet:
- O(1) average for add, remove, contains
- No ordering guarantee
- Better for: Simple membership test, deduplication, when order doesn't matter
- Memory: More overhead per element (hash buckets)

TreeSet:
- O(log n) for all operations
- Sorted iteration
- Better for: Range queries, sorted data, first/last element access
- Memory: Red-black tree overhead

Decision Matrix:
┌─────────────────────────┬───────────┬───────────┐
│ Use Case                │  HashSet  │  TreeSet  │
├─────────────────────────┼───────────┼───────────┤
│ Simple contains check   │    ✓      │           │
│ Need sorted iteration   │           │    ✓      │
│ Range queries           │           │    ✓      │
│ First/last element      │           │    ✓      │
│ Null elements           │    ✓      │           │
│ Custom ordering         │           │    ✓      │
│ Maximum performance     │    ✓      │           │
└─────────────────────────┴───────────┴───────────┘
```

3. **"Why doesn't Go have a built-in set type?"**
```
Go's Design Philosophy:
1. Simplicity: Fewer core types, explicit code
2. Sufficiency: map[T]struct{} is efficient and idiomatic
3. Memory: struct{} is zero bytes, very efficient
4. Flexibility: Different use cases may need different implementations
5. Readability: Explicit is better than implicit

Idiomatic Go Set Pattern:
set := make(map[string]struct{})
set["item"] = struct{}{}     // Add
delete(set, "item")          // Remove
_, exists := set["item"]     // Contains

Why struct{} over bool?
- struct{} is literally zero bytes
- bool is 1 byte per entry
- For large sets, significant memory savings
```

4. **"Python: set vs frozenset"**
```python
# set: Mutable, cannot be used as dict key or set element
s = {1, 2, 3}
s.add(4)        # OK
# {s: "value"}  # TypeError: unhashable type: 'set'

# frozenset: Immutable, hashable, can be dict key or set element
fs = frozenset([1, 2, 3])
# fs.add(4)     # AttributeError: no add method
{fs: "value"}   # OK! frozenset is hashable

# Use cases:
# 1. Set of sets
set_of_sets = {frozenset([1,2]), frozenset([3,4])}

# 2. Dict keys
cache = {frozenset(["a","b"]): result}

# 3. Thread-safe sharing (immutable = no race conditions)
```

5. **"How does distinct() work in Spark? Performance implications?"**
```python
# distinct() causes SHUFFLE - expensive!
# It must hash all elements and redistribute across partitions

# What happens internally:
# 1. Each partition hashes its elements
# 2. Elements with same hash go to same partition (shuffle)
# 3. Within partition, remove duplicates
# 4. Result: Deduplicated RDD/DataFrame

# Performance tips:
# 1. Use dropDuplicates(subset) if only some columns matter
df.dropDuplicates(["key_column"])  # Less data to shuffle

# 2. Consider approx_count_distinct for cardinality estimation
from pyspark.sql.functions import approx_count_distinct
df.select(approx_count_distinct("column"))

# 3. Filter early to reduce data before distinct
df.filter(condition).distinct()  # Better than distinct().filter()

# 4. Cache if using distinct result multiple times
distinct_df = df.distinct().cache()
```

### 4.4 Common Interview Patterns

```python
# Pattern 1: Find first duplicate in array
def first_duplicate(arr: list) -> int:
    seen = set()
    for num in arr:
        if num in seen:
            return num
        seen.add(num)
    return -1  # No duplicate found

# Pattern 2: Two Sum using set
def has_pair_with_sum(arr: list, target: int) -> bool:
    seen = set()
    for num in arr:
        complement = target - num
        if complement in seen:
            return True
        seen.add(num)
    return False

# Pattern 3: Longest consecutive sequence
def longest_consecutive(nums: list) -> int:
    num_set = set(nums)
    longest = 0

    for num in num_set:
        # Only start counting from sequence start
        if num - 1 not in num_set:
            current = num
            length = 1
            while current + 1 in num_set:
                current += 1
                length += 1
            longest = max(longest, length)

    return longest

# Pattern 4: Check if two strings are anagrams
def are_anagrams(s1: str, s2: str) -> bool:
    # Using multiset (Counter)
    from collections import Counter
    return Counter(s1) == Counter(s2)

    # Or using set comparison (ignores frequency)
    # return set(s1) == set(s2)  # Wrong! "aab" and "ab" would be equal

# Pattern 5: Find symmetric pairs in array of pairs
def find_symmetric_pairs(pairs: list) -> list:
    seen = set()
    result = []

    for a, b in pairs:
        if (b, a) in seen:
            result.append((b, a))
        seen.add((a, b))

    return result
```

---

## 5. Cross-References (관련 개념)

### Related Knowledge Bases

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F50** | Arrays & Sequences | Lists vs Sets: ordered vs unique |
| **F51** | Hash Maps | Set uses hash table internally |
| **F43** | Higher-Order Functions | filter/map operations on sets |
| **F24** | Generics | Generic Set<T> implementations |
| **F31** | Loops & Iteration | Iterating over sets |
| **F32** | Exception Handling | Set operation exceptions |
| **00c** | Data Structures Intro | Foundation concepts |

### Algorithm Patterns Using Sets

| Pattern | Use Case | Example |
|---------|----------|---------|
| Membership test | Quick lookup | `if x in set` |
| Deduplication | Remove duplicates | `list(set(arr))` |
| Set operations | Union/Intersection/Difference | `A & B` |
| Complement | Find missing elements | `all_items - seen` |
| Visited tracking | Graph traversal | `visited.add(node)` |
| Two pointers | Find pairs | `target - x in set` |

### Set Implementation Comparison

| Feature | Hash Set | Tree Set | Bit Set |
|---------|----------|----------|---------|
| Insert | O(1) avg | O(log n) | O(1) |
| Delete | O(1) avg | O(log n) | O(1) |
| Search | O(1) avg | O(log n) | O(1) |
| Ordered | No | Yes | By index |
| Range query | No | Yes | No |
| Memory | Higher | Medium | Lowest |
| Use case | General | Sorted data | Dense integers |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SETS & COLLECTIONS CHEAT SHEET                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ SET CHARACTERISTICS:                                                 │
│   ✓ Unique elements (no duplicates)                                 │
│   ✓ O(1) average membership test (hash set)                         │
│   ✓ Mathematical set operations                                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ LANGUAGE SYNTAX:                                                     │
│   Java:       Set<T> set = new HashSet<>();                         │
│   Python:     set = {1, 2, 3} or set()                              │
│   TypeScript: const set = new Set<T>()                              │
│   Go:         set := make(map[T]struct{})                           │
│   C++:        std::unordered_set<T> / std::set<T>                   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ PYTHON SET OPERATORS (interview favorite!):                          │
│   A | B     Union (합집합)                                           │
│   A & B     Intersection (교집합)                                    │
│   A - B     Difference (차집합)                                      │
│   A ^ B     Symmetric Difference (대칭차집합)                        │
│   A <= B    Subset check                                            │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ SQL SET OPERATIONS:                                                  │
│   UNION [ALL]     Combine result sets                               │
│   INTERSECT       Common rows                                       │
│   EXCEPT/MINUS    Rows in first, not in second                      │
│   DISTINCT        Remove duplicate rows                             │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ SPARK SET OPERATIONS (Palantir Critical!):                          │
│   df.distinct()                Deduplicate rows                     │
│   df.dropDuplicates([cols])    Deduplicate on columns               │
│   df_a.union(df_b)             Union (keeps duplicates!)            │
│   df_a.intersect(df_b)         Intersection                         │
│   df_a.subtract(df_b)          Difference                           │
│   F.collect_set(col)           Aggregate to set                     │
│   F.array_distinct(col)        Distinct array elements              │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ INTERVIEW CRITICAL:                                                  │
│   ⚠️  Python: {} is empty dict, not set! Use set()                  │
│   ⚠️  Go: No built-in set - use map[T]struct{}                      │
│   ⚠️  HashSet vs TreeSet: O(1) vs O(log n), unordered vs sorted     │
│   ⚠️  frozenset: Immutable, hashable (can be dict key)              │
│   ⚠️  Spark distinct() causes SHUFFLE - expensive!                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
