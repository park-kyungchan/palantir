# F51: Maps & Dictionaries (맵과 딕셔너리)

> **Concept ID**: `F51_maps_dictionaries`
> **Universal Principle**: 키-값 쌍을 저장하고 키를 통해 O(1) 또는 O(log n) 시간에 값에 접근하는 자료구조
> **Prerequisites**: F20_static_vs_dynamic_typing (키 타입), F50_arrays_lists (선형 자료구조)

---

## 1. Universal Concept (언어 무관 개념 정의)

**Map (또는 Dictionary, Associative Array, Hash Table)**은 키(key)와 값(value)의 쌍을 저장하는 자료구조입니다. 각 키는 고유하며, 해당 키를 통해 연결된 값에 빠르게 접근할 수 있습니다.

### 1.1 Mental Model: Phone Book (전화번호부)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MAP = PHONE BOOK                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Key (이름)          Value (전화번호)                               │
│  ─────────────────────────────────────                              │
│  "Alice"      →      "010-1234-5678"                                │
│  "Bob"        →      "010-8765-4321"                                │
│  "Charlie"    →      "010-1111-2222"                                │
│                                                                     │
│  전화번호부에서 "Alice"를 찾으면 즉시 전화번호를 알 수 있듯이,       │
│  Map에서 키로 값을 O(1) 시간에 조회할 수 있습니다.                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Two Implementation Strategies

```
┌─────────────────────────────────────────────────────────────────────┐
│                 HASH MAP vs TREE MAP                                 │
├───────────────────────────┬─────────────────────────────────────────┤
│       HASH MAP            │           TREE MAP                       │
│  (Unordered, O(1))        │      (Ordered, O(log n))                │
├───────────────────────────┼─────────────────────────────────────────┤
│                           │                                         │
│  ┌───┐ ┌───┐ ┌───┐       │         ┌───┐                           │
│  │ 0 │→│"B"│→│"D"│       │        │"M"│                            │
│  └───┘ └───┘ └───┘       │       /     \                           │
│  ┌───┐ ┌───┐             │    ┌───┐   ┌───┐                        │
│  │ 1 │→│"A"│             │    │"D"│   │"R"│                        │
│  └───┘ └───┘             │   /    \       \                        │
│  ┌───┐                   │ ┌───┐ ┌───┐ ┌───┐                       │
│  │ 2 │→ null             │ │"A"│ │"G"│ │"Z"│                       │
│  └───┘                   │ └───┘ └───┘ └───┘                       │
│  ┌───┐ ┌───┐             │                                         │
│  │ 3 │→│"C"│             │  Sorted by key:                         │
│  └───┘ └───┘             │  A < D < G < M < R < Z                  │
│                           │                                         │
│  hash("A") % 4 = 1       │  Binary search tree structure           │
│  hash("B") % 4 = 0       │  maintains sorted order                 │
│                           │                                         │
├───────────────────────────┼─────────────────────────────────────────┤
│  Lookup: O(1) average    │  Lookup: O(log n)                       │
│  Insert: O(1) average    │  Insert: O(log n)                       │
│  Order:  NONE            │  Order:  SORTED by key                  │
│  Memory: Less overhead   │  Memory: More overhead (tree nodes)     │
└───────────────────────────┴─────────────────────────────────────────┘
```

### 1.3 Hash Function and Collision Handling

**Hash Function**: 키를 고정 크기의 정수(버킷 인덱스)로 변환하는 함수

```
┌─────────────────────────────────────────────────────────────────────┐
│                   HASH FUNCTION PROCESS                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Key: "Alice"                                                       │
│     ↓                                                               │
│  hash("Alice") = 2081285842                                         │
│     ↓                                                               │
│  2081285842 % bucket_size(8) = 2                                    │
│     ↓                                                               │
│  Store at bucket[2]                                                 │
│                                                                     │
│  GOOD HASH FUNCTION properties:                                     │
│  1. Deterministic: Same key → same hash                             │
│  2. Uniform distribution: Keys spread evenly across buckets         │
│  3. Fast computation: O(1) time                                     │
│  4. Avalanche effect: Small key change → big hash change            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Collision Handling**: 두 개의 다른 키가 같은 버킷에 매핑될 때

```
┌─────────────────────────────────────────────────────────────────────┐
│                 COLLISION RESOLUTION                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Method 1: CHAINING (Linked List)                                   │
│  ───────────────────────────────                                    │
│  bucket[2] → ["Alice":100] → ["Eve":200] → null                    │
│                                                                     │
│  - Pros: Simple, never fills up                                     │
│  - Cons: Cache unfriendly, extra memory for pointers                │
│                                                                     │
│  Method 2: OPEN ADDRESSING (Linear Probing)                         │
│  ─────────────────────────────────────────                          │
│  bucket[2] = "Alice":100                                            │
│  bucket[3] = "Eve":200  (next empty slot)                          │
│                                                                     │
│  - Pros: Cache friendly, no extra pointers                          │
│  - Cons: Clustering, deletion is complex                            │
│                                                                     │
│  Java HashMap uses: Chaining (with tree if bucket > 8 elements)     │
│  Python dict uses: Open addressing (probing)                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.4 Time Complexity Summary

| Operation | Hash Map (avg) | Hash Map (worst) | Tree Map |
|-----------|----------------|------------------|----------|
| **Get** | O(1) | O(n) | O(log n) |
| **Put** | O(1) | O(n) | O(log n) |
| **Delete** | O(1) | O(n) | O(log n) |
| **Contains Key** | O(1) | O(n) | O(log n) |
| **Iterate All** | O(n) | O(n) | O(n) |
| **Get Min/Max Key** | O(n) | O(n) | O(log n) or O(1)* |

*O(1) if tree maintains min/max pointers

### 1.5 Why Maps Matter

| Use Case | Example |
|----------|---------|
| **Caching** | URL → HTML content |
| **Counting** | word → frequency |
| **Indexing** | userId → User object |
| **Configuration** | key → value settings |
| **Memoization** | function args → result |
| **Graph representation** | node → [neighbors] |
| **Database index simulation** | primary key → row |

---

## 2. Semantic Comparison Matrix (의미론적 비교 매트릭스)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Hash Map** | `HashMap<K,V>` | `dict` | `Map<K,V>` / `{}` | `map[K]V` | `JSONB` | `unordered_map` | `MapType` col |
| **Ordered Map** | `LinkedHashMap` | `dict` (3.7+) | `Map` (insertion) | N/A | N/A | N/A | N/A |
| **Sorted Map** | `TreeMap<K,V>` | N/A (use sorted()) | N/A | N/A | N/A | `map<K,V>` | N/A |
| **Default Value** | `getOrDefault()` | `.get(k, default)` | `??` operator | `val, ok` idiom | `COALESCE` | `[]` operator | N/A |
| **Key Requirement** | `hashCode()`/`equals()` | `__hash__`/`__eq__` | any | comparable | any | `hash`/`<` | hashable |
| **Null Key** | Yes (1 only) | N/A (None allowed) | any | zero value | NULL | N/A | NULL |
| **Thread-Safe** | `ConcurrentHashMap` | No (use locks) | No | `sync.Map` | N/A | No | N/A |
| **Literal Syntax** | No | `{k: v}` | `{k: v}` or `new Map()` | `map[K]V{k: v}` | `'{}'::jsonb` | `{{k, v}}` | N/A |

### 2.2 Detailed Code Examples

---

#### Pattern 1: Basic Map Operations (Create, Get, Set, Delete)

**Java**
```java
import java.util.*;

public class MapBasics {
    public static void main(String[] args) {
        // ==================================================
        // HashMap: Most common, O(1) average
        // ==================================================
        Map<String, Integer> scores = new HashMap<>();

        // PUT: Add/update key-value pairs
        scores.put("Alice", 95);
        scores.put("Bob", 87);
        scores.put("Charlie", 92);

        // GET: Retrieve value by key
        Integer aliceScore = scores.get("Alice");  // 95
        Integer unknownScore = scores.get("Dave"); // null (not found)

        // GET with default (Java 8+)
        int daveScore = scores.getOrDefault("Dave", 0);  // 0

        // CONTAINS: Check key/value existence
        boolean hasAlice = scores.containsKey("Alice");    // true
        boolean has100 = scores.containsValue(100);        // false

        // UPDATE: put() overwrites existing value
        scores.put("Alice", 98);  // Alice now has 98

        // REMOVE: Delete by key
        Integer removed = scores.remove("Bob");  // returns 87
        scores.remove("NonExistent");            // returns null, no error

        // SIZE and EMPTY
        int size = scores.size();        // 2
        boolean empty = scores.isEmpty(); // false

        // CLEAR: Remove all entries
        // scores.clear();

        // ==================================================
        // Iteration patterns
        // ==================================================

        // Iterate keys
        for (String key : scores.keySet()) {
            System.out.println(key);
        }

        // Iterate values
        for (Integer value : scores.values()) {
            System.out.println(value);
        }

        // Iterate entries (most efficient for both key and value)
        for (Map.Entry<String, Integer> entry : scores.entrySet()) {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        }

        // Java 8+ forEach
        scores.forEach((key, value) ->
            System.out.println(key + " -> " + value));

        // ==================================================
        // Compute operations (Java 8+)
        // ==================================================

        // computeIfAbsent: Set default if key missing
        scores.computeIfAbsent("Dave", k -> 0);  // Dave -> 0

        // computeIfPresent: Update if key exists
        scores.computeIfPresent("Alice", (k, v) -> v + 5);  // Alice -> 103

        // compute: Always compute new value
        scores.compute("Charlie", (k, v) -> v == null ? 0 : v * 2);

        // merge: Combine with existing value
        scores.merge("Alice", 10, Integer::sum);  // Add 10 to Alice
    }
}
```

**Python**
```python
from typing import Dict, Optional

# ==================================================
# dict: Python's built-in hash map
# ==================================================

# CREATE: Multiple ways to create a dict
scores: Dict[str, int] = {}                          # Empty dict
scores = dict()                                       # Empty dict
scores = {"Alice": 95, "Bob": 87, "Charlie": 92}     # Dict literal
scores = dict(Alice=95, Bob=87, Charlie=92)          # Keyword arguments
scores = dict([("Alice", 95), ("Bob", 87)])          # From tuples

# PUT: Add/update key-value pairs
scores["Alice"] = 95
scores["Bob"] = 87

# GET: Retrieve value by key
alice_score = scores["Alice"]       # 95
# unknown = scores["Dave"]          # KeyError! Not found

# GET with default (SAFE - no KeyError)
dave_score = scores.get("Dave")     # None (default)
dave_score = scores.get("Dave", 0)  # 0 (custom default)

# CONTAINS: Check key existence
has_alice = "Alice" in scores       # True (O(1))
has_dave = "Dave" in scores         # False

# Check value existence (O(n) - must scan all values!)
has_95 = 95 in scores.values()      # True

# UPDATE: Direct assignment overwrites
scores["Alice"] = 98

# REMOVE: Delete by key
del scores["Bob"]                   # Removes Bob (KeyError if missing)
removed = scores.pop("Charlie")     # Returns 92, removes Charlie
removed = scores.pop("Dave", None)  # Returns None, no error

# SIZE and EMPTY
size = len(scores)                  # 1
is_empty = len(scores) == 0         # False
is_empty = not scores               # Pythonic empty check

# CLEAR
# scores.clear()

# ==================================================
# Iteration patterns
# ==================================================

# Iterate keys (default iteration)
for key in scores:
    print(key)

# Explicit keys()
for key in scores.keys():
    print(key)

# Iterate values
for value in scores.values():
    print(value)

# Iterate items (key-value pairs)
for key, value in scores.items():
    print(f"{key}: {value}")

# ==================================================
# Advanced operations
# ==================================================

# setdefault: Get value or set default if missing
score = scores.setdefault("Dave", 0)  # Returns 0, adds Dave: 0

# update: Merge another dict
scores.update({"Eve": 88, "Frank": 91})
scores |= {"Grace": 93}  # Python 3.9+ merge operator

# Merge dicts (creates new dict)
combined = scores | {"Henry": 85}  # Python 3.9+
combined = {**scores, "Henry": 85}  # Python 3.5+ unpacking

# ==================================================
# Dict comprehension (VERY IMPORTANT!)
# ==================================================

numbers = [1, 2, 3, 4, 5]

# Basic comprehension
squares = {n: n**2 for n in numbers}
# {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

# With condition
even_squares = {n: n**2 for n in numbers if n % 2 == 0}
# {2: 4, 4: 16}

# Transform existing dict
upper_scores = {k.upper(): v for k, v in scores.items()}

# Invert dict (swap keys and values)
inverted = {v: k for k, v in scores.items()}
# WARNING: Loses data if values not unique!

# Filter dict by value
high_scores = {k: v for k, v in scores.items() if v >= 90}

# ==================================================
# fromkeys: Create dict with same value
# ==================================================
keys = ["a", "b", "c"]
zeros = dict.fromkeys(keys, 0)  # {"a": 0, "b": 0, "c": 0}
```

**TypeScript**
```typescript
// ==================================================
// Object literal vs Map: WHEN TO USE WHICH?
// ==================================================

// OBJECT LITERAL: Good for simple string keys, JSON-like data
interface Scores {
    [key: string]: number;
}

const scoresObj: Scores = {
    Alice: 95,
    Bob: 87,
    Charlie: 92
};

// PUT
scoresObj["Dave"] = 88;
scoresObj.Eve = 91;  // Dot notation (string keys only)

// GET
const aliceScore: number = scoresObj["Alice"];  // 95
const unknownScore: number | undefined = scoresObj["Unknown"];  // undefined

// GET with default (nullish coalescing)
const daveScore: number = scoresObj["Dave"] ?? 0;  // 88

// CONTAINS
const hasAlice: boolean = "Alice" in scoresObj;                    // true
const hasOwnAlice: boolean = scoresObj.hasOwnProperty("Alice");   // true

// REMOVE
delete scoresObj["Bob"];

// SIZE (requires Object.keys)
const size: number = Object.keys(scoresObj).length;

// ITERATION
Object.keys(scoresObj).forEach(key => console.log(key));
Object.values(scoresObj).forEach(value => console.log(value));
Object.entries(scoresObj).forEach(([key, value]) => {
    console.log(`${key}: ${value}`);
});

// ==================================================
// MAP: Better for dynamic keys, non-string keys, size tracking
// ==================================================

const scoresMap: Map<string, number> = new Map();

// PUT
scoresMap.set("Alice", 95);
scoresMap.set("Bob", 87).set("Charlie", 92);  // Chainable!

// GET
const alice: number | undefined = scoresMap.get("Alice");  // 95
const unknown: number | undefined = scoresMap.get("Unknown");  // undefined

// GET with default
const dave: number = scoresMap.get("Dave") ?? 0;  // 0

// CONTAINS
const hasAliceMap: boolean = scoresMap.has("Alice");  // true

// REMOVE
const wasDeleted: boolean = scoresMap.delete("Bob");  // true

// SIZE (built-in!)
const mapSize: number = scoresMap.size;  // 2

// CLEAR
// scoresMap.clear();

// ITERATION (preserves insertion order!)
scoresMap.forEach((value, key) => {
    console.log(`${key}: ${value}`);
});

// Using iterators
for (const [key, value] of scoresMap) {
    console.log(`${key}: ${value}`);
}

for (const key of scoresMap.keys()) {
    console.log(key);
}

for (const value of scoresMap.values()) {
    console.log(value);
}

// ==================================================
// Map with non-string keys (Object can't do this!)
// ==================================================

interface User {
    id: number;
    name: string;
}

const user1: User = { id: 1, name: "Alice" };
const user2: User = { id: 2, name: "Bob" };

// Object as key (uses reference equality!)
const userScores: Map<User, number> = new Map();
userScores.set(user1, 95);
userScores.set(user2, 87);

console.log(userScores.get(user1));  // 95

// WARNING: Different object with same content = different key!
const user1Copy: User = { id: 1, name: "Alice" };
console.log(userScores.get(user1Copy));  // undefined!

// ==================================================
// Object vs Map: Decision Guide
// ==================================================

/*
USE OBJECT when:
- Keys are strings or symbols
- You need JSON serialization
- Simple configuration/settings
- Static, known keys

USE MAP when:
- Keys are non-strings (objects, numbers, functions)
- You need to track size (.size)
- You need guaranteed insertion order
- Frequent add/remove operations
- You need iteration methods directly
*/

// Convert between Object and Map
const obj = { a: 1, b: 2 };
const map = new Map(Object.entries(obj));  // Object → Map
const backToObj = Object.fromEntries(map); // Map → Object
```

**Go**
```go
package main

import (
    "fmt"
    "sort"
)

func main() {
    // ==================================================
    // map: Go's built-in hash map
    // ==================================================

    // CREATE: Multiple ways
    scores := make(map[string]int)                      // Empty map
    scores = map[string]int{}                           // Empty map literal
    scores = map[string]int{"Alice": 95, "Bob": 87}    // With initial values

    // PUT: Add/update
    scores["Alice"] = 95
    scores["Charlie"] = 92

    // GET: Retrieve value
    aliceScore := scores["Alice"]     // 95
    daveScore := scores["Dave"]       // 0 (zero value if missing!)

    // ==================================================
    // COMMA OK IDIOM (CRITICAL FOR INTERVIEW!)
    // ==================================================

    // How do you distinguish "key missing" from "value is zero"?
    value, exists := scores["Dave"]
    if exists {
        fmt.Println("Dave's score:", value)
    } else {
        fmt.Println("Dave not found")  // This prints
    }

    // Common pattern: Check and get in one line
    if score, ok := scores["Alice"]; ok {
        fmt.Println("Alice's score:", score)
    }

    // GET with default (manual implementation)
    getOrDefault := func(m map[string]int, key string, defaultVal int) int {
        if val, ok := m[key]; ok {
            return val
        }
        return defaultVal
    }
    daveWithDefault := getOrDefault(scores, "Dave", 0)  // 0

    // CONTAINS: Use comma ok
    _, hasAlice := scores["Alice"]  // true

    // REMOVE
    delete(scores, "Bob")           // Safe even if key doesn't exist
    delete(scores, "NonExistent")   // No error

    // SIZE
    size := len(scores)

    // ==================================================
    // Iteration (ORDER NOT GUARANTEED!)
    // ==================================================

    // Iterate key-value pairs
    for key, value := range scores {
        fmt.Printf("%s: %d\n", key, value)
    }

    // Iterate keys only
    for key := range scores {
        fmt.Println(key)
    }

    // Iterate values only (use blank identifier for key)
    for _, value := range scores {
        fmt.Println(value)
    }

    // ==================================================
    // SORTED iteration (Go maps are unordered!)
    // ==================================================

    // To iterate in sorted key order:
    keys := make([]string, 0, len(scores))
    for k := range scores {
        keys = append(keys, k)
    }
    sort.Strings(keys)

    for _, k := range keys {
        fmt.Printf("%s: %d\n", k, scores[k])
    }

    // ==================================================
    // Map with struct keys
    // ==================================================

    type Point struct {
        X, Y int
    }

    pointValues := make(map[Point]string)
    pointValues[Point{0, 0}] = "origin"
    pointValues[Point{1, 2}] = "point A"

    // Struct keys work because Point is comparable
    fmt.Println(pointValues[Point{0, 0}])  // "origin"

    // ==================================================
    // Nil map behavior (INTERVIEW TRAP!)
    // ==================================================

    var nilMap map[string]int  // nil map

    // READING from nil map is OK (returns zero value)
    val := nilMap["key"]  // val = 0, no panic

    // WRITING to nil map PANICS!
    // nilMap["key"] = 1  // panic: assignment to entry in nil map

    // Always initialize before writing:
    if nilMap == nil {
        nilMap = make(map[string]int)
    }
    nilMap["key"] = 1  // OK now

    // ==================================================
    // Map as set (common pattern)
    // ==================================================

    set := make(map[string]struct{})  // struct{} uses 0 bytes!

    // Add to set
    set["Alice"] = struct{}{}
    set["Bob"] = struct{}{}

    // Check membership
    if _, exists := set["Alice"]; exists {
        fmt.Println("Alice is in set")
    }

    // Remove from set
    delete(set, "Bob")
}
```

**SQL (PostgreSQL JSONB)**
```sql
-- ==================================================
-- JSONB: JSON Binary format with map-like operations
-- ==================================================

-- CREATE table with JSONB column
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

-- INSERT with JSONB data
INSERT INTO users (name, metadata) VALUES
    ('Alice', '{"score": 95, "level": "gold", "tags": ["vip", "active"]}'),
    ('Bob', '{"score": 87, "level": "silver"}'),
    ('Charlie', '{"score": 92, "level": "gold", "premium": true}');

-- ==================================================
-- GET: Access JSONB values
-- ==================================================

-- Get single key (returns JSONB)
SELECT metadata->'score' AS score_json FROM users;
-- Returns: "95" (as JSON)

-- Get single key as text
SELECT metadata->>'score' AS score_text FROM users;
-- Returns: 95 (as text)

-- Get nested key
SELECT metadata->'tags'->0 AS first_tag FROM users;
-- Returns: "vip"

-- Path extraction
SELECT metadata #> '{tags,0}' AS first_tag FROM users;

-- ==================================================
-- CONTAINS: Check key/value existence
-- ==================================================

-- Check if key exists
SELECT * FROM users WHERE metadata ? 'premium';
-- Returns Charlie

-- Check if ANY of keys exist
SELECT * FROM users WHERE metadata ?| array['premium', 'vip'];

-- Check if ALL keys exist
SELECT * FROM users WHERE metadata ?& array['score', 'level'];

-- Check if contains key-value pair
SELECT * FROM users WHERE metadata @> '{"level": "gold"}';
-- Returns Alice, Charlie

-- ==================================================
-- UPDATE: Modify JSONB
-- ==================================================

-- Set/update a key
UPDATE users
SET metadata = jsonb_set(metadata, '{score}', '100')
WHERE name = 'Alice';

-- Add a new key
UPDATE users
SET metadata = metadata || '{"new_key": "new_value"}'
WHERE name = 'Bob';

-- Remove a key
UPDATE users
SET metadata = metadata - 'level'
WHERE name = 'Charlie';

-- Remove nested key by path
UPDATE users
SET metadata = metadata #- '{tags,0}'
WHERE name = 'Alice';

-- ==================================================
-- DEFAULT VALUE: COALESCE
-- ==================================================

-- Get value with default (NULL handling)
SELECT
    name,
    COALESCE(metadata->>'score', '0')::int AS score,
    COALESCE(metadata->>'level', 'bronze') AS level
FROM users;

-- ==================================================
-- Iteration: Expand JSONB to rows
-- ==================================================

-- Expand top-level keys
SELECT name, key, value
FROM users, jsonb_each(metadata);

-- Expand as text
SELECT name, key, value
FROM users, jsonb_each_text(metadata);

-- Get all keys
SELECT DISTINCT jsonb_object_keys(metadata) AS keys
FROM users;

-- ==================================================
-- Aggregation with JSONB
-- ==================================================

-- Build JSONB from grouped data
SELECT
    metadata->>'level' AS level,
    jsonb_agg(name) AS names,
    jsonb_object_agg(name, metadata->>'score') AS scores_by_name
FROM users
GROUP BY metadata->>'level';

-- ==================================================
-- Indexing for performance
-- ==================================================

-- GIN index for containment queries (@>)
CREATE INDEX idx_users_metadata ON users USING GIN (metadata);

-- Expression index for specific key
CREATE INDEX idx_users_level ON users ((metadata->>'level'));
```

**C++**
```cpp
#include <iostream>
#include <map>
#include <unordered_map>
#include <string>

int main() {
    // ==================================================
    // unordered_map: Hash-based, O(1) average
    // ==================================================

    std::unordered_map<std::string, int> scores;

    // INSERT / UPDATE
    scores["Alice"] = 95;
    scores["Bob"] = 87;
    scores.insert({"Charlie", 92});
    scores.insert(std::make_pair("Dave", 88));

    // insert only if key doesn't exist (returns pair<iterator, bool>)
    auto [iter, inserted] = scores.insert({"Alice", 100});
    // inserted = false (Alice already exists, value unchanged)

    // insert_or_assign: Always sets value (C++17)
    scores.insert_or_assign("Alice", 100);  // Alice now 100

    // GET
    int aliceScore = scores["Alice"];       // 100
    int unknownScore = scores["Unknown"];   // 0 (CREATES the key!)

    // SAFE GET: at() throws if not found
    try {
        int score = scores.at("NonExistent");
    } catch (const std::out_of_range& e) {
        std::cout << "Key not found" << std::endl;
    }

    // GET with default (manual)
    auto getOrDefault = [](const auto& map, const auto& key, auto defaultVal) {
        auto it = map.find(key);
        return it != map.end() ? it->second : defaultVal;
    };
    int daveScore = getOrDefault(scores, std::string("Dave"), 0);

    // CONTAINS
    bool hasAlice = scores.find("Alice") != scores.end();  // true
    bool hasAlice2 = scores.count("Alice") > 0;            // true
    bool hasAlice3 = scores.contains("Alice");             // C++20

    // REMOVE
    scores.erase("Bob");
    size_t removed = scores.erase("NonExistent");  // returns 0

    // SIZE
    size_t size = scores.size();
    bool empty = scores.empty();

    // CLEAR
    // scores.clear();

    // ==================================================
    // Iteration (order not guaranteed for unordered_map)
    // ==================================================

    for (const auto& [key, value] : scores) {  // C++17 structured binding
        std::cout << key << ": " << value << std::endl;
    }

    // C++11 style
    for (const auto& pair : scores) {
        std::cout << pair.first << ": " << pair.second << std::endl;
    }

    // ==================================================
    // map: Tree-based, O(log n), SORTED by key
    // ==================================================

    std::map<std::string, int> sortedScores;

    sortedScores["Charlie"] = 92;
    sortedScores["Alice"] = 95;
    sortedScores["Bob"] = 87;

    // Iteration is in SORTED key order
    for (const auto& [key, value] : sortedScores) {
        std::cout << key << ": " << value << std::endl;
    }
    // Output: Alice: 95, Bob: 87, Charlie: 92

    // Get min/max key
    auto minKey = sortedScores.begin()->first;   // "Alice"
    auto maxKey = sortedScores.rbegin()->first;  // "Charlie"

    // Range queries (tree map advantage!)
    auto lower = sortedScores.lower_bound("B");  // First >= "B"
    auto upper = sortedScores.upper_bound("B");  // First > "B"

    // ==================================================
    // Custom key types (need hash function for unordered_map)
    // ==================================================

    struct Point {
        int x, y;

        // For std::map (needs operator<)
        bool operator<(const Point& other) const {
            if (x != other.x) return x < other.x;
            return y < other.y;
        }

        // For std::unordered_map (needs operator== and hash)
        bool operator==(const Point& other) const {
            return x == other.x && y == other.y;
        }
    };

    // Custom hash function for Point
    struct PointHash {
        std::size_t operator()(const Point& p) const {
            return std::hash<int>()(p.x) ^ (std::hash<int>()(p.y) << 1);
        }
    };

    std::unordered_map<Point, std::string, PointHash> pointMap;
    pointMap[{0, 0}] = "origin";
    pointMap[{1, 2}] = "point A";

    std::map<Point, std::string> sortedPointMap;  // No hash needed
    sortedPointMap[{0, 0}] = "origin";

    return 0;
}
```

**Spark (PySpark)**
```python
from pyspark.sql import SparkSession
from pyspark.sql.types import MapType, StringType, IntegerType, StructType, StructField
from pyspark.sql.functions import (
    col, create_map, map_keys, map_values, map_from_entries,
    element_at, map_filter, transform_keys, transform_values,
    explode, lit, when, coalesce
)

spark = SparkSession.builder.appName("Maps").getOrCreate()

# ==================================================
# Creating DataFrames with Map columns
# ==================================================

# Schema with MapType
schema = StructType([
    StructField("name", StringType(), True),
    StructField("attributes", MapType(StringType(), IntegerType()), True)
])

data = [
    ("Alice", {"score": 95, "level": 5}),
    ("Bob", {"score": 87}),
    ("Charlie", {"score": 92, "level": 3, "bonus": 10})
]

df = spark.createDataFrame(data, schema)
df.show(truncate=False)
# +-------+--------------------------------+
# |name   |attributes                      |
# +-------+--------------------------------+
# |Alice  |{score -> 95, level -> 5}       |
# |Bob    |{score -> 87}                   |
# |Charlie|{score -> 92, level -> 3, ...}  |
# +-------+--------------------------------+

# ==================================================
# Create Map from columns
# ==================================================

df2 = spark.createDataFrame([
    ("Alice", "score", 95),
    ("Bob", "level", 3)
], ["name", "key", "value"])

df_with_map = df2.select(
    "name",
    create_map(col("key"), col("value")).alias("data")
)

# Create map from multiple columns
df3 = spark.createDataFrame([
    ("Alice", 95, 5),
    ("Bob", 87, 3)
], ["name", "score", "level"])

df_multimap = df3.select(
    "name",
    create_map(
        lit("score"), col("score"),
        lit("level"), col("level")
    ).alias("attributes")
)

# ==================================================
# GET: Access map values
# ==================================================

# element_at (1-indexed for arrays, key for maps)
df.select(
    "name",
    element_at("attributes", "score").alias("score"),
    element_at("attributes", "level").alias("level")
).show()

# Using bracket notation (Spark 3.0+)
df.select(
    "name",
    col("attributes")["score"].alias("score"),
    col("attributes")["level"].alias("level")
).show()

# GET with default (COALESCE)
df.select(
    "name",
    coalesce(col("attributes")["level"], lit(0)).alias("level_with_default")
).show()

# ==================================================
# KEYS and VALUES
# ==================================================

df.select(
    "name",
    map_keys("attributes").alias("keys"),
    map_values("attributes").alias("values")
).show(truncate=False)

# ==================================================
# Explode: Convert map to rows
# ==================================================

df.select(
    "name",
    explode("attributes").alias("key", "value")
).show()
# +-------+-----+-----+
# |name   |key  |value|
# +-------+-----+-----+
# |Alice  |score|95   |
# |Alice  |level|5    |
# |Bob    |score|87   |
# |Charlie|score|92   |
# |Charlie|level|3    |
# |Charlie|bonus|10   |
# +-------+-----+-----+

# ==================================================
# Filter and Transform maps (Spark 3.0+)
# ==================================================

# Filter map entries
df.select(
    "name",
    map_filter("attributes", lambda k, v: v > 50).alias("high_values")
).show(truncate=False)

# Transform keys
df.select(
    "name",
    transform_keys("attributes", lambda k, v: k.upper()).alias("upper_keys")
).show(truncate=False)

# Transform values
df.select(
    "name",
    transform_values("attributes", lambda k, v: v * 2).alias("doubled")
).show(truncate=False)

# ==================================================
# Broadcast variables for lookup maps (CRITICAL!)
# ==================================================

# Large lookup table should be broadcast to avoid shuffle
lookup_dict = {"gold": 100, "silver": 50, "bronze": 25}
broadcast_lookup = spark.sparkContext.broadcast(lookup_dict)

# Use in UDF
from pyspark.sql.functions import udf

@udf(IntegerType())
def get_bonus(level: str) -> int:
    return broadcast_lookup.value.get(level, 0)

df_levels = spark.createDataFrame([
    ("Alice", "gold"),
    ("Bob", "silver"),
    ("Charlie", "bronze")
], ["name", "level"])

df_levels.select(
    "name",
    "level",
    get_bonus("level").alias("bonus")
).show()

# ==================================================
# Collect as map (ACTION - careful with large data!)
# ==================================================

# Convert two columns to Python dict on driver
result_dict = dict(
    df.select("name", col("attributes")["score"])
    .rdd.map(lambda row: (row[0], row[1]))
    .collect()
)
# {"Alice": 95, "Bob": 87, "Charlie": 92}

# WARNING: collect() brings all data to driver!
# Only use for small result sets
```

---

#### Pattern 2: Python defaultdict and Counter

**Python (collections module)**
```python
from collections import defaultdict, Counter, OrderedDict
from typing import List

# ==================================================
# defaultdict: Dict with automatic default values
# ==================================================

# Problem: Counting occurrences with regular dict
words = ["apple", "banana", "apple", "cherry", "banana", "apple"]

# Regular dict - need to check if key exists
counts_manual = {}
for word in words:
    if word in counts_manual:
        counts_manual[word] += 1
    else:
        counts_manual[word] = 1
# {"apple": 3, "banana": 2, "cherry": 1}

# With get() - slightly better
counts_get = {}
for word in words:
    counts_get[word] = counts_get.get(word, 0) + 1

# With defaultdict - cleanest!
counts_default = defaultdict(int)  # int() returns 0
for word in words:
    counts_default[word] += 1  # No KeyError, auto-creates 0
# defaultdict(<class 'int'>, {"apple": 3, "banana": 2, "cherry": 1})

# ==================================================
# defaultdict factory functions
# ==================================================

# int: Default 0 (for counting)
counter = defaultdict(int)
counter["key"] += 1  # 0 + 1 = 1

# list: Default [] (for grouping)
groups = defaultdict(list)
for word in words:
    groups[word[0]].append(word)  # Group by first letter
# {"a": ["apple", "apple", "apple"], "b": ["banana", "banana"], "c": ["cherry"]}

# set: Default set() (for unique grouping)
unique_groups = defaultdict(set)
for word in words:
    unique_groups[word[0]].add(word)
# {"a": {"apple"}, "b": {"banana"}, "c": {"cherry"}}

# lambda: Custom default
prices = defaultdict(lambda: -1)  # -1 for missing items
print(prices["unknown"])  # -1

# Nested defaultdict (auto-vivification)
nested = defaultdict(lambda: defaultdict(int))
nested["users"]["Alice"] += 1
nested["users"]["Bob"] += 1
nested["admins"]["Charlie"] += 1
# {"users": {"Alice": 1, "Bob": 1}, "admins": {"Charlie": 1}}

# ==================================================
# Counter: Specialized dict for counting
# ==================================================

# Create Counter
word_counts = Counter(words)
# Counter({"apple": 3, "banana": 2, "cherry": 1})

# Counter from string (counts characters)
char_counts = Counter("abracadabra")
# Counter({"a": 5, "b": 2, "r": 2, "c": 1, "d": 1})

# Counter from dict
explicit_counts = Counter({"a": 4, "b": 2})

# ==================================================
# Counter operations
# ==================================================

# most_common: Get top N elements
top_2 = word_counts.most_common(2)
# [("apple", 3), ("banana", 2)]

# All elements sorted by count (descending)
all_sorted = word_counts.most_common()

# elements(): Iterate over elements (repeated by count)
list(word_counts.elements())
# ["apple", "apple", "apple", "banana", "banana", "cherry"]

# total(): Sum of all counts (Python 3.10+)
total = word_counts.total()  # 6

# ==================================================
# Counter arithmetic (INTERVIEW FAVORITE!)
# ==================================================

c1 = Counter({"a": 3, "b": 1})
c2 = Counter({"a": 1, "b": 2})

# Addition: Combine counts
c1 + c2  # Counter({"a": 4, "b": 3})

# Subtraction: Subtract (keeps only positive)
c1 - c2  # Counter({"a": 2})  # b disappears!

# Intersection: Minimum of each
c1 & c2  # Counter({"a": 1, "b": 1})

# Union: Maximum of each
c1 | c2  # Counter({"a": 3, "b": 2})

# Update: Add counts in-place
c1.update(c2)  # c1 now {"a": 4, "b": 3}

# subtract: Subtract counts in-place (can go negative!)
c1.subtract(c2)

# ==================================================
# Practical examples
# ==================================================

# Example 1: Find most common character in string
def most_common_char(s: str) -> str:
    if not s:
        return ""
    return Counter(s).most_common(1)[0][0]

# Example 2: Check if two strings are anagrams
def are_anagrams(s1: str, s2: str) -> bool:
    return Counter(s1.lower()) == Counter(s2.lower())

# Example 3: Group items by property
students = [
    {"name": "Alice", "grade": "A"},
    {"name": "Bob", "grade": "B"},
    {"name": "Charlie", "grade": "A"},
    {"name": "Dave", "grade": "B"},
]

by_grade = defaultdict(list)
for student in students:
    by_grade[student["grade"]].append(student["name"])
# {"A": ["Alice", "Charlie"], "B": ["Bob", "Dave"]}

# Example 4: Invert a dictionary (handle duplicate values)
original = {"a": 1, "b": 2, "c": 1}
inverted_multi = defaultdict(list)
for k, v in original.items():
    inverted_multi[v].append(k)
# {1: ["a", "c"], 2: ["b"]}
```

---

#### Pattern 3: Java HashMap vs TreeMap vs LinkedHashMap

**Java**
```java
import java.util.*;

public class MapComparison {
    public static void main(String[] args) {
        // ==================================================
        // HashMap: Unordered, O(1) operations
        // ==================================================
        Map<String, Integer> hashMap = new HashMap<>();
        hashMap.put("Charlie", 3);
        hashMap.put("Alice", 1);
        hashMap.put("Bob", 2);

        System.out.println("HashMap iteration (NO guaranteed order):");
        for (String key : hashMap.keySet()) {
            System.out.println(key);  // Could be any order!
        }

        // ==================================================
        // LinkedHashMap: Insertion order preserved, O(1)
        // ==================================================
        Map<String, Integer> linkedHashMap = new LinkedHashMap<>();
        linkedHashMap.put("Charlie", 3);
        linkedHashMap.put("Alice", 1);
        linkedHashMap.put("Bob", 2);

        System.out.println("\nLinkedHashMap iteration (INSERTION order):");
        for (String key : linkedHashMap.keySet()) {
            System.out.println(key);  // Charlie, Alice, Bob
        }

        // Access order mode (for LRU cache implementation!)
        Map<String, Integer> accessOrderMap =
            new LinkedHashMap<>(16, 0.75f, true);  // true = access order
        accessOrderMap.put("A", 1);
        accessOrderMap.put("B", 2);
        accessOrderMap.put("C", 3);

        accessOrderMap.get("A");  // Access A, moves to end

        System.out.println("\nAccess-order LinkedHashMap:");
        for (String key : accessOrderMap.keySet()) {
            System.out.println(key);  // B, C, A (A moved to end)
        }

        // ==================================================
        // TreeMap: Sorted by key, O(log n) operations
        // ==================================================
        Map<String, Integer> treeMap = new TreeMap<>();
        treeMap.put("Charlie", 3);
        treeMap.put("Alice", 1);
        treeMap.put("Bob", 2);

        System.out.println("\nTreeMap iteration (SORTED by key):");
        for (String key : treeMap.keySet()) {
            System.out.println(key);  // Alice, Bob, Charlie
        }

        // TreeMap-specific methods (NavigableMap interface)
        TreeMap<String, Integer> navMap = new TreeMap<>(treeMap);

        // First and last
        String first = navMap.firstKey();   // "Alice"
        String last = navMap.lastKey();     // "Charlie"

        // Floor and ceiling (INTERVIEW FAVORITE!)
        String floor = navMap.floorKey("Bravo");    // "Bob" (≤ Bravo)
        String ceiling = navMap.ceilingKey("Bravo"); // "Charlie" (≥ Bravo)

        // Lower and higher
        String lower = navMap.lowerKey("Bob");   // "Alice" (< Bob)
        String higher = navMap.higherKey("Bob"); // "Charlie" (> Bob)

        // Range queries (subMap, headMap, tailMap)
        SortedMap<String, Integer> subMap =
            navMap.subMap("Alice", "Charlie");  // Alice, Bob (exclusive end)

        NavigableMap<String, Integer> subMap2 =
            navMap.subMap("Alice", true, "Charlie", true);  // Inclusive both

        // Descending order
        NavigableMap<String, Integer> descending = navMap.descendingMap();

        // Poll (remove and return) first/last
        Map.Entry<String, Integer> polledFirst = navMap.pollFirstEntry();

        // ==================================================
        // Performance comparison
        // ==================================================
        /*
        | Operation    | HashMap | LinkedHashMap | TreeMap  |
        |--------------|---------|---------------|----------|
        | get/put      | O(1)    | O(1)          | O(log n) |
        | containsKey  | O(1)    | O(1)          | O(log n) |
        | remove       | O(1)    | O(1)          | O(log n) |
        | iteration    | O(n)    | O(n)          | O(n)     |
        | first/last   | O(n)    | O(1)*         | O(log n) |
        | floor/ceiling| N/A     | N/A           | O(log n) |

        * LinkedHashMap first/last via iterator.next() and keep reference
        */

        // ==================================================
        // Custom comparator for TreeMap
        // ==================================================

        // Reverse order
        TreeMap<String, Integer> reverseMap =
            new TreeMap<>(Comparator.reverseOrder());

        // Case-insensitive
        TreeMap<String, Integer> caseInsensitiveMap =
            new TreeMap<>(String.CASE_INSENSITIVE_ORDER);

        // Custom object with comparator
        TreeMap<Person, Integer> personMap = new TreeMap<>(
            Comparator.comparing(Person::getAge)
                      .thenComparing(Person::getName)
        );

        // ==================================================
        // When to use which?
        // ==================================================
        /*
        USE HashMap when:
        - Order doesn't matter
        - Need fastest operations
        - Memory efficiency matters

        USE LinkedHashMap when:
        - Need insertion order preserved
        - Building LRU cache (access-order mode)
        - Predictable iteration order

        USE TreeMap when:
        - Need sorted keys
        - Need range queries (floor, ceiling, subMap)
        - Need first/last element quickly
        */
    }
}

class Person {
    private String name;
    private int age;

    // Constructor, getters, setters...
    public String getName() { return name; }
    public int getAge() { return age; }
}
```

---

#### Pattern 4: C++ unordered_map vs map

**C++**
```cpp
#include <iostream>
#include <map>
#include <unordered_map>
#include <chrono>
#include <random>

int main() {
    // ==================================================
    // unordered_map: Hash table, O(1) average
    // ==================================================

    std::unordered_map<std::string, int> hashMap;

    // O(1) average insert
    hashMap["Charlie"] = 3;
    hashMap["Alice"] = 1;
    hashMap["Bob"] = 2;

    std::cout << "unordered_map (NO guaranteed order):\n";
    for (const auto& [key, value] : hashMap) {
        std::cout << key << ": " << value << "\n";
    }
    // Output order is unpredictable

    // Bucket interface (implementation detail exposure)
    std::cout << "\nBucket count: " << hashMap.bucket_count() << "\n";
    std::cout << "Load factor: " << hashMap.load_factor() << "\n";

    // Reserve to prevent rehashing
    hashMap.reserve(1000);

    // ==================================================
    // map: Red-black tree, O(log n)
    // ==================================================

    std::map<std::string, int> treeMap;

    // O(log n) insert
    treeMap["Charlie"] = 3;
    treeMap["Alice"] = 1;
    treeMap["Bob"] = 2;

    std::cout << "\nmap (SORTED by key):\n";
    for (const auto& [key, value] : treeMap) {
        std::cout << key << ": " << value << "\n";
    }
    // Output: Alice, Bob, Charlie (sorted)

    // ==================================================
    // map-specific operations (sorted)
    // ==================================================

    // First and last element
    auto first = treeMap.begin();
    auto last = std::prev(treeMap.end());
    std::cout << "\nFirst: " << first->first << "\n";
    std::cout << "Last: " << last->first << "\n";

    // lower_bound: First >= key
    auto lower = treeMap.lower_bound("Bravo");
    if (lower != treeMap.end()) {
        std::cout << "lower_bound('Bravo'): " << lower->first << "\n";
        // "Charlie" (first >= "Bravo")
    }

    // upper_bound: First > key
    auto upper = treeMap.upper_bound("Bob");
    if (upper != treeMap.end()) {
        std::cout << "upper_bound('Bob'): " << upper->first << "\n";
        // "Charlie" (first > "Bob")
    }

    // equal_range: Range of elements with key
    auto range = treeMap.equal_range("Bob");

    // ==================================================
    // Performance benchmark
    // ==================================================

    const int N = 1000000;
    std::vector<int> keys(N);
    std::iota(keys.begin(), keys.end(), 0);

    // Shuffle for realistic access pattern
    std::random_device rd;
    std::mt19937 g(rd());
    std::shuffle(keys.begin(), keys.end(), g);

    std::unordered_map<int, int> um;
    std::map<int, int> m;

    // Insert benchmark
    auto start = std::chrono::high_resolution_clock::now();
    for (int key : keys) {
        um[key] = key;
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto umInsert = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    start = std::chrono::high_resolution_clock::now();
    for (int key : keys) {
        m[key] = key;
    }
    end = std::chrono::high_resolution_clock::now();
    auto mInsert = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "\nInsert " << N << " elements:\n";
    std::cout << "unordered_map: " << umInsert.count() << "ms\n";
    std::cout << "map: " << mInsert.count() << "ms\n";

    /*
    Typical results (N = 1,000,000):
    unordered_map: ~150ms
    map: ~400ms

    unordered_map is ~2-3x faster for insertion
    */

    // ==================================================
    // Memory comparison
    // ==================================================

    /*
    unordered_map memory overhead:
    - Hash table buckets array
    - Each bucket is a linked list
    - Node overhead: ~24-32 bytes per entry

    map memory overhead:
    - Tree nodes with left/right/parent pointers
    - Color bit (red/black)
    - Node overhead: ~40-48 bytes per entry

    map uses MORE memory but provides ordering
    */

    // ==================================================
    // When to use which?
    // ==================================================

    /*
    USE unordered_map when:
    - Order doesn't matter
    - Need O(1) operations
    - Keys have good hash distribution
    - No range queries needed

    USE map when:
    - Need sorted iteration
    - Need range queries (lower_bound, upper_bound)
    - Need first/last element access
    - Keys don't have good hash function
    - Worst-case O(log n) is acceptable

    INTERVIEW TIP: Know both, explain trade-offs!
    */

    return 0;
}
```

---

### 2.3 Common Pitfalls by Language

#### Java Pitfalls
```java
// 1. Using get() without null check
Map<String, Integer> map = new HashMap<>();
map.put("Alice", 95);
int score = map.get("Bob");  // NullPointerException! (unboxing null)

// Fix: Use getOrDefault or check for null
int score = map.getOrDefault("Bob", 0);

// 2. Modifying map during iteration
for (String key : map.keySet()) {
    if (key.startsWith("A")) {
        map.remove(key);  // ConcurrentModificationException!
    }
}

// Fix: Use iterator with remove() or create copy
Iterator<String> iter = map.keySet().iterator();
while (iter.hasNext()) {
    if (iter.next().startsWith("A")) {
        iter.remove();  // Safe
    }
}

// 3. Mutable keys in HashMap
List<String> key = new ArrayList<>();
key.add("hello");
map.put(key, 100);
key.add("world");  // Modifying key after insert!
map.get(key);      // null! Hash code changed

// 4. hashCode/equals contract violation
class BadKey {
    int id;

    @Override
    public boolean equals(Object o) {
        return ((BadKey) o).id == this.id;
    }
    // Missing hashCode()! Two equal objects may have different hashes
}
```

#### Python Pitfalls
```python
# 1. KeyError on missing key
d = {"Alice": 95}
score = d["Bob"]  # KeyError!

# Fix: Use get() or check with 'in'
score = d.get("Bob", 0)  # Returns 0
if "Bob" in d:
    score = d["Bob"]

# 2. Mutable default argument (CLASSIC TRAP!)
def add_item(item, items={}):  # WRONG! {} is shared across calls
    items[item] = True
    return items

add_item("a")  # {"a": True}
add_item("b")  # {"a": True, "b": True} - Unexpected!

# Fix: Use None as default
def add_item(item, items=None):
    if items is None:
        items = {}
    items[item] = True
    return items

# 3. Iterating and modifying
d = {"a": 1, "b": 2, "c": 3}
for key in d:
    if d[key] < 2:
        del d[key]  # RuntimeError: dictionary changed size during iteration

# Fix: Iterate over copy of keys
for key in list(d.keys()):
    if d[key] < 2:
        del d[key]

# 4. Using unhashable types as keys
d = {}
d[[1, 2, 3]] = "list"  # TypeError: unhashable type: 'list'
d[{"a": 1}] = "dict"   # TypeError: unhashable type: 'dict'

# Fix: Use tuples (immutable) or frozenset
d[(1, 2, 3)] = "tuple"      # OK
d[frozenset([1, 2])] = "fs" # OK
```

#### Go Pitfalls
```go
// 1. Writing to nil map (PANICS!)
var m map[string]int
m["key"] = 1  // panic: assignment to entry in nil map

// Fix: Initialize first
m = make(map[string]int)
m["key"] = 1

// 2. Assuming order in range iteration
m := map[string]int{"a": 1, "b": 2, "c": 3}
for k := range m {
    fmt.Println(k)  // Order varies between runs!
}

// Fix: Sort keys if order matters
keys := make([]string, 0, len(m))
for k := range m {
    keys = append(keys, k)
}
sort.Strings(keys)
for _, k := range keys {
    fmt.Println(k, m[k])
}

// 3. Not using comma-ok idiom
m := map[string]int{"key": 0}
val := m["key"]        // val = 0
val := m["missing"]    // val = 0 - Can't tell if key exists!

// Fix: Always use comma-ok for existence check
val, ok := m["key"]
if ok {
    fmt.Println("Found:", val)
} else {
    fmt.Println("Not found")
}

// 4. Concurrent map access (RACE CONDITION!)
m := make(map[string]int)
go func() { m["a"] = 1 }()
go func() { m["b"] = 2 }()  // Data race!

// Fix: Use sync.Map or mutex
var mu sync.Mutex
go func() { mu.Lock(); m["a"] = 1; mu.Unlock() }()
go func() { mu.Lock(); m["b"] = 2; mu.Unlock() }()
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Documentation | Key Section |
|----------|---------------|-------------|
| **Java** | [HashMap Javadoc](https://docs.oracle.com/javase/8/docs/api/java/util/HashMap.html) | Hash table based implementation |
| **Java** | [TreeMap Javadoc](https://docs.oracle.com/javase/8/docs/api/java/util/TreeMap.html) | Red-black tree implementation |
| **Python** | [dict Documentation](https://docs.python.org/3/library/stdtypes.html#mapping-types-dict) | Mapping types |
| **Python** | [collections module](https://docs.python.org/3/library/collections.html) | defaultdict, Counter, OrderedDict |
| **TypeScript** | [Map](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map) | MDN Map reference |
| **Go** | [Maps in Action](https://go.dev/blog/maps) | Official Go blog on maps |
| **Go** | [Effective Go](https://go.dev/doc/effective_go#maps) | Idiomatic map usage |
| **SQL** | [PostgreSQL JSON Functions](https://www.postgresql.org/docs/current/functions-json.html) | JSONB operations |
| **C++** | [std::unordered_map](https://en.cppreference.com/w/cpp/container/unordered_map) | Hash table |
| **C++** | [std::map](https://en.cppreference.com/w/cpp/container/map) | Red-black tree |
| **Spark** | [MapType](https://spark.apache.org/docs/latest/sql-ref-datatypes.html) | Map column type |

---

## 4. Palantir Context Hint (팔란티어 맥락 힌트)

### 4.1 TypeScript OSDK: Object Types and Map Usage

```typescript
// Foundry OSDK - Working with Object properties that act like maps

import { Objects } from "@foundry/ontology-api";

// Object type with map-like properties
interface FlightProperties {
    attributes: { [key: string]: string };
    delays: Map<string, number>;
}

// Querying and transforming objects with properties
const flights = await Objects.search(Flight)
    .filter(f => f.status === "delayed")
    .execute();

// Process as map operations
const delaysByAirport: Map<string, number[]> = new Map();

flights.data.forEach(flight => {
    const airport = flight.origin;
    if (!delaysByAirport.has(airport)) {
        delaysByAirport.set(airport, []);
    }
    delaysByAirport.get(airport)!.push(flight.delay || 0);
});

// Compute averages
const avgDelays: Map<string, number> = new Map(
    [...delaysByAirport.entries()].map(([airport, delays]) => [
        airport,
        delays.reduce((a, b) => a + b, 0) / delays.length
    ])
);
```

### 4.2 Spark: MapType Columns and Broadcast Variables

```python
# Broadcast variables for lookup tables (CRITICAL for performance!)

# BAD: Join with large lookup table (causes shuffle)
lookup_df = spark.table("code_mappings")  # Millions of rows
result = main_df.join(lookup_df, "code")  # Expensive shuffle!

# GOOD: Broadcast small lookup as dict
lookup_dict = dict(
    spark.table("code_mappings")
    .select("code", "description")
    .collect()  # Only for small tables!
)
broadcast_lookup = spark.sparkContext.broadcast(lookup_dict)

@udf(StringType())
def get_description(code: str) -> str:
    return broadcast_lookup.value.get(code, "Unknown")

result = main_df.withColumn("description", get_description("code"))
# No shuffle! Lookup runs locally on each executor

# MapType column operations
from pyspark.sql.types import MapType, StringType

# Schema with map
schema = "id INT, properties MAP<STRING, STRING>"

# Access map values
df.select(
    col("properties")["key1"],
    element_at("properties", "key2")
)

# Explode map to rows (for analysis)
df.select(explode("properties"))
```

### 4.3 Interview Questions (CRITICAL)

1. **"HashMap vs TreeMap - time complexity and ordering"**
```
HashMap:
- get/put: O(1) average, O(n) worst (hash collision)
- No ordering guarantee
- Uses hashCode() and equals()
- Null key allowed (one only)

TreeMap:
- get/put: O(log n) always
- Keys are SORTED (natural order or Comparator)
- Uses compareTo() or Comparator
- No null keys (throws NullPointerException)

Choose HashMap for:
- Fastest operations, order doesn't matter

Choose TreeMap for:
- Range queries (subMap, headMap, tailMap)
- Need min/max key quickly
- Sorted iteration required
```

2. **"Go: How do you check if a key exists in map?"**
```go
// Comma-ok idiom (THE answer!)
value, exists := myMap[key]
if exists {
    // Key found, value is valid
} else {
    // Key not found, value is zero value
}

// Why needed?
m := map[string]int{"zero": 0}
v1 := m["zero"]    // v1 = 0
v2 := m["missing"] // v2 = 0 - Same! Can't tell difference!

// With comma-ok:
v1, ok1 := m["zero"]    // v1=0, ok1=true
v2, ok2 := m["missing"] // v2=0, ok2=false - Now we know!
```

3. **"Python: defaultdict vs regular dict"**
```python
# Regular dict: KeyError on missing key
d = {}
d["count"] += 1  # KeyError!

# defaultdict: Auto-creates default value
from collections import defaultdict
d = defaultdict(int)
d["count"] += 1  # Works! d["count"] = 1

# Common factory functions:
defaultdict(int)    # 0
defaultdict(list)   # []
defaultdict(set)    # set()
defaultdict(dict)   # {}
defaultdict(lambda: "default")  # Custom

# Use case: Grouping
groups = defaultdict(list)
for item in items:
    groups[item.category].append(item)  # No KeyError!

# Use case: Counting
counts = defaultdict(int)
for word in words:
    counts[word] += 1  # No need to check existence

# But Counter is better for counting!
from collections import Counter
counts = Counter(words)  # Built for this purpose
```

4. **"What makes a good hash function?"**
```
Properties of a GOOD hash function:

1. DETERMINISTIC
   - Same input always produces same output
   - hash("hello") always returns same value

2. UNIFORM DISTRIBUTION
   - Spreads keys evenly across buckets
   - Minimizes collisions
   - Bad: hash(s) = len(s)  // Many collisions!
   - Good: Uses all characters, multiplies by primes

3. FAST COMPUTATION
   - O(1) or O(key_length) time
   - Hashing shouldn't be the bottleneck

4. AVALANCHE EFFECT
   - Small input change -> big hash change
   - "hello" and "hellp" should have very different hashes

5. CONSISTENT WITH EQUALS
   - If a.equals(b), then hash(a) == hash(b)
   - Reverse NOT required: hash(a) == hash(b) doesn't mean a.equals(b)

Common implementation (Java String):
int hash = 0;
for (char c : chars) {
    hash = 31 * hash + c;  // 31 is prime, good distribution
}
// 31 is chosen because:
// - It's prime (reduces patterns)
// - 31 * i = (i << 5) - i (fast computation)
```

---

## 5. Cross-References (관련 개념)

### Related Knowledge Bases

| KB ID | Title | Relationship |
|-------|-------|--------------|
| **F50** | Arrays & Lists | Linear data structures, map values can be arrays |
| **F52** | Sets | Set is Map without values, uses same hash/tree structures |
| **F20** | Static vs Dynamic Typing | Key and value type requirements vary by language |
| **F43** | Higher-Order Functions | map/filter/reduce operations on map entries |
| **F24** | Generics & Polymorphism | Generic map types `Map<K,V>` |
| **F32** | Exception Handling | KeyError, NullPointerException handling |
| **00d** | Async Basics | Concurrent map access patterns |

### Data Structure Evolution

```
┌─────────────────────────────────────────────────────────────────────┐
│             DATA STRUCTURE RELATIONSHIPS                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Array/List                                                         │
│      │                                                              │
│      └─── Index (int) → Value                                       │
│                │                                                    │
│                ▼                                                    │
│  Map/Dictionary                                                     │
│      │                                                              │
│      └─── Key (any) → Value                                        │
│                │                                                    │
│                ▼                                                    │
│  Set                                                                │
│      │                                                              │
│      └─── Key (any) → (exists/not exists)                          │
│           Essentially: Map where value is boolean/void              │
│                                                                     │
│  Tree Variants:                                                     │
│      Array → TreeMap (sorted by key)                               │
│      Set → TreeSet (sorted elements)                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MAPS & DICTIONARIES CHEAT SHEET                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LANGUAGE SYNTAX:                                                   │
│  Java:       Map<K,V> map = new HashMap<>(); map.put(k,v);         │
│  Python:     d = {}; d[k] = v; d.get(k, default)                   │
│  TypeScript: const m = new Map(); m.set(k,v); m.get(k) ?? default  │
│  Go:         m := make(map[K]V); m[k] = v; val, ok := m[k]         │
│  C++:        unordered_map<K,V> m; m[k] = v; m.at(k) // throws     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TIME COMPLEXITY:                                                   │
│                                                                     │
│  │ Operation │ Hash Map (avg) │ Tree Map │                         │
│  │───────────│────────────────│──────────│                         │
│  │ get/put   │ O(1)           │ O(log n) │                         │
│  │ delete    │ O(1)           │ O(log n) │                         │
│  │ contains  │ O(1)           │ O(log n) │                         │
│  │ min/max   │ O(n)           │ O(log n) │                         │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  HASH MAP vs TREE MAP:                                              │
│  Hash: Unordered, O(1), best for general use                       │
│  Tree: Sorted by key, O(log n), best for range queries             │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DEFAULT VALUE HANDLING:                                            │
│  Java:   map.getOrDefault(key, 0)                                  │
│  Python: dict.get(key, default) or defaultdict(int)                │
│  TS:     map.get(key) ?? default                                   │
│  Go:     val, ok := m[key]; if !ok { val = default }               │
│  C++:    m.count(key) ? m[key] : default                           │
│  SQL:    COALESCE(column, default)                                 │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  INTERVIEW CRITICAL:                                                │
│  1. HashMap vs TreeMap: O(1) vs O(log n), unordered vs sorted      │
│  2. Go comma-ok: val, ok := m[key] (check existence)               │
│  3. Python defaultdict: Auto-creates missing keys                  │
│  4. Good hash function: Deterministic, uniform, fast, avalanche    │
│  5. Java LinkedHashMap: Insertion order or access order (LRU!)     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PALANTIR CONTEXT:                                                  │
│  - TypeScript OSDK: Object properties as Map<string, T>            │
│  - Spark: broadcast() for lookup tables (avoid shuffle!)           │
│  - Spark: MapType columns, explode() for analysis                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Author: ODA Knowledge Base Generator*
