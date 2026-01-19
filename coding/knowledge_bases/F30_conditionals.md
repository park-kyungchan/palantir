# F30: Conditionals (조건문)

> **Series**: Fundamentals (F-Series) | **Level**: Foundation
> **Prerequisites**: F10_variables_types.md, F20_operators.md
> **Languages**: Java, Python, TypeScript, Go, SQL, C++, Spark

---

## 1. Universal Concept

### Definition

**Conditionals** are control flow structures that execute different code paths based on boolean expressions. They enable programs to make decisions and respond differently to varying inputs or states.

```
                    ┌─────────────────────────────────────────┐
                    │         CONDITIONAL STRUCTURE           │
                    └─────────────────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │   CONDITION     │
                              │  (Boolean Expr) │
                              └────────┬────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
              ┌─────────┐        ┌─────────┐        ┌─────────┐
              │  TRUE   │        │  FALSE  │        │ DEFAULT │
              │  Block  │        │  Block  │        │  Block  │
              └────┬────┘        └────┬────┘        └────┬────┘
                   │                  │                  │
                   └──────────────────┴──────────────────┘
                                      │
                                      ▼
                              ┌─────────────────┐
                              │   CONTINUE      │
                              │   EXECUTION     │
                              └─────────────────┘
```

### Mental Model: The Traffic Light

Think of conditionals as a **traffic light system**:

```
    🚦 TRAFFIC LIGHT MODEL

    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │    if (light == RED)     →  STOP                       │
    │    else if (light == YELLOW) →  SLOW DOWN              │
    │    else                  →  GO                          │
    │                                                         │
    │    ┌───────┐                                            │
    │    │  🔴   │  condition1 TRUE  → execute block1        │
    │    ├───────┤                                            │
    │    │  🟡   │  condition2 TRUE  → execute block2        │
    │    ├───────┤                                            │
    │    │  🟢   │  all FALSE        → execute default       │
    │    └───────┘                                            │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

### Why This Matters

**For Beginners:**
- Conditionals are the foundation of **decision-making** in code
- Without conditionals, programs would be linear and unable to adapt
- Every interactive program uses conditionals (login systems, games, calculators)

**For Interviews:**
- Understanding **short-circuit evaluation** prevents bugs
- Knowing **truthy/falsy** rules across languages avoids subtle errors
- **Switch vs if-else** trade-offs appear in system design questions

**Real-World Impact:**
```
┌─────────────────────────────────────────────────────────────┐
│  Authentication System (Palantir Foundry Example)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  if (user.isAuthenticated && user.hasPermission(resource)) │
│      → GRANT ACCESS                                         │
│  else if (user.isAuthenticated)                            │
│      → SHOW PERMISSION ERROR                               │
│  else                                                       │
│      → REDIRECT TO LOGIN                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Semantic Comparison Matrix

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **if/else syntax** | `if (cond) {}` | `if cond:` | `if (cond) {}` | `if cond {}` | `IF...THEN` | `if (cond) {}` | Python-based |
| **Parentheses required** | ✅ Yes | ❌ No | ✅ Yes | ❌ No | N/A | ✅ Yes | ❌ No |
| **Braces required** | ❌ Optional* | N/A (indent) | ❌ Optional* | ✅ Yes | N/A | ❌ Optional* | N/A (indent) |
| **switch/match** | `switch` + `case` | `match` (3.10+) | `switch` | `switch` | `CASE WHEN` | `switch` | PySpark: N/A |
| **Pattern matching** | Java 21+ | ✅ Full | ✅ Limited | ❌ No | ❌ No | ❌ No | ❌ No |
| **Ternary operator** | `? :` | `x if c else y` | `? :` | ❌ No | N/A | `? :` | `when().otherwise()` |
| **Fall-through default** | ✅ Yes | N/A | ✅ Yes | ❌ No | N/A | ✅ Yes | N/A |
| **Switch expression** | Java 14+ | N/A | ❌ No | N/A | N/A | ❌ No | N/A |

*\*Optional but strongly recommended for multi-statement blocks*

### 2.2 Truthy/Falsy Values (CRITICAL FOR INTERVIEWS)

| Language | Falsy Values | Notes |
|----------|--------------|-------|
| **Java** | Only `false` | No implicit boolean conversion! |
| **Python** | `False`, `None`, `0`, `0.0`, `""`, `[]`, `{}`, `set()` | Empty collections are falsy |
| **TypeScript** | `false`, `0`, `-0`, `""`, `null`, `undefined`, `NaN` | Same as JavaScript |
| **Go** | Only `false` | No implicit boolean conversion! |
| **SQL** | `NULL` (special 3-valued logic) | `NULL != NULL` is `NULL` |
| **C++** | `false`, `0`, `0.0`, `nullptr`, `'\0'` | Pointers can be conditions |
| **Spark** | Follows Python + `null` handling | `isNull()`, `isNotNull()` |

```
┌────────────────────────────────────────────────────────────────┐
│  ⚠️  INTERVIEW TRAP: Truthy/Falsy Differences                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  JavaScript/TypeScript:                                        │
│    if ("") { ... }       // FALSE - empty string is falsy     │
│    if ("0") { ... }      // TRUE  - non-empty string!         │
│    if ([]) { ... }       // TRUE  - empty array is truthy!    │
│                                                                │
│  Python:                                                       │
│    if "": ...            # FALSE - empty string is falsy      │
│    if "0": ...           # TRUE  - non-empty string           │
│    if []: ...            # FALSE - empty list is falsy!       │
│                                                                │
│  Java/Go:                                                      │
│    if ("") { ... }       // COMPILE ERROR - not boolean       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Detailed Code Examples

#### Java

```java
// ═══════════════════════════════════════════════════════════════
// JAVA CONDITIONALS
// ═══════════════════════════════════════════════════════════════

// --- Basic if/else ---
int score = 85;

if (score >= 90) {
    System.out.println("A");
} else if (score >= 80) {
    System.out.println("B");
} else if (score >= 70) {
    System.out.println("C");
} else {
    System.out.println("F");
}

// --- Ternary Operator ---
String result = score >= 60 ? "Pass" : "Fail";

// --- Switch Statement (Traditional) ---
// ⚠️ FALL-THROUGH: Without break, execution continues!
int day = 3;
switch (day) {
    case 1:
        System.out.println("Monday");
        break;  // Required to prevent fall-through
    case 2:
        System.out.println("Tuesday");
        break;
    case 3:
    case 4:
    case 5:
        System.out.println("Midweek");  // Intentional fall-through
        break;
    default:
        System.out.println("Weekend");
}

// --- Switch Expression (Java 14+) ---
// No fall-through, returns value directly
String dayName = switch (day) {
    case 1 -> "Monday";
    case 2 -> "Tuesday";
    case 3, 4, 5 -> "Midweek";
    default -> "Weekend";
};

// --- Pattern Matching in instanceof (Java 16+) ---
Object obj = "Hello";
if (obj instanceof String s) {
    // s is already cast to String
    System.out.println(s.length());
}

// --- Pattern Matching in Switch (Java 21+) ---
Object value = 42;
String description = switch (value) {
    case Integer i when i > 0 -> "Positive integer: " + i;
    case Integer i -> "Non-positive integer: " + i;
    case String s -> "String: " + s;
    case null -> "Null value";
    default -> "Unknown type";
};

// ═══════════════════════════════════════════════════════════════
// COMMON PITFALLS
// ═══════════════════════════════════════════════════════════════

// PITFALL 1: Assignment vs Comparison
int x = 5;
// if (x = 10) { }  // COMPILE ERROR in Java (good!)
// Unlike C/C++ where this would be valid and always true

// PITFALL 2: String Comparison
String a = "hello";
String b = new String("hello");
if (a == b) { }        // FALSE - compares references
if (a.equals(b)) { }   // TRUE  - compares content

// PITFALL 3: Null Checks
String str = null;
// if (str.equals("test")) { }  // NullPointerException!
if ("test".equals(str)) { }     // Safe - returns false
if (str != null && str.equals("test")) { }  // Also safe

// PITFALL 4: Integer Caching (-128 to 127)
Integer n1 = 127;
Integer n2 = 127;
System.out.println(n1 == n2);  // TRUE (cached)

Integer n3 = 128;
Integer n4 = 128;
System.out.println(n3 == n4);  // FALSE (not cached!)
System.out.println(n3.equals(n4));  // TRUE
```

#### Python

```python
# ═══════════════════════════════════════════════════════════════
# PYTHON CONDITIONALS
# ═══════════════════════════════════════════════════════════════

# --- Basic if/else ---
score = 85

if score >= 90:
    print("A")
elif score >= 80:
    print("B")
elif score >= 70:
    print("C")
else:
    print("F")

# --- Ternary (Conditional Expression) ---
# Syntax: value_if_true if condition else value_if_false
result = "Pass" if score >= 60 else "Fail"

# --- Chained Ternary (readable alternative) ---
grade = (
    "A" if score >= 90 else
    "B" if score >= 80 else
    "C" if score >= 70 else
    "F"
)

# --- Match Statement (Python 3.10+) ---
# Full structural pattern matching
day = 3
match day:
    case 1:
        print("Monday")
    case 2:
        print("Tuesday")
    case 3 | 4 | 5:  # Multiple patterns
        print("Midweek")
    case _:  # Default/wildcard
        print("Weekend")

# --- Pattern Matching with Guards ---
point = (0, 5)
match point:
    case (0, 0):
        print("Origin")
    case (0, y):
        print(f"On Y-axis at {y}")
    case (x, 0):
        print(f"On X-axis at {x}")
    case (x, y) if x == y:
        print(f"On diagonal at {x}")
    case (x, y):
        print(f"Point at ({x}, {y})")

# --- Structural Pattern Matching with Classes ---
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

def describe_point(p):
    match p:
        case Point(x=0, y=0):
            return "Origin"
        case Point(x=0, y=y):
            return f"Y-axis at {y}"
        case Point(x=x, y=0):
            return f"X-axis at {x}"
        case _:
            return f"Point({p.x}, {p.y})"

# ═══════════════════════════════════════════════════════════════
# TRUTHY/FALSY DEEP DIVE
# ═══════════════════════════════════════════════════════════════

# All these are FALSY in Python:
falsy_values = [False, None, 0, 0.0, 0j, "", [], {}, set(), frozenset()]

for val in falsy_values:
    if not val:
        print(f"{repr(val):20} is FALSY")

# ⚠️ INTERVIEW TRAP: Custom objects
class Empty:
    def __bool__(self):
        return False  # Custom falsy behavior

    def __len__(self):
        return 0  # Alternative: __len__ returning 0 makes it falsy

# ═══════════════════════════════════════════════════════════════
# COMMON PITFALLS
# ═══════════════════════════════════════════════════════════════

# PITFALL 1: Mutable Default Arguments
def add_item(item, lst=[]):  # ⚠️ DANGEROUS
    lst.append(item)
    return lst

# CORRECT:
def add_item_safe(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst

# PITFALL 2: Identity vs Equality
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)   # True  - equal content
print(a is b)   # False - different objects

# But for small integers and interned strings:
x = 256
y = 256
print(x is y)   # True  - Python caches small integers

x = 257
y = 257
print(x is y)   # False - not cached (implementation dependent)

# PITFALL 3: Chained Comparisons (Python-specific)
x = 5
if 1 < x < 10:  # Valid! Equivalent to (1 < x) and (x < 10)
    print("x is between 1 and 10")

# PITFALL 4: None Checks
value = None
# Use 'is' for None, not '=='
if value is None:  # Correct
    pass
if value == None:  # Works but not Pythonic
    pass

# PITFALL 5: Short-circuit with 'or'
name = ""
display = name or "Anonymous"  # "Anonymous" (empty string is falsy)

name = "Alice"
display = name or "Anonymous"  # "Alice"
```

#### TypeScript

```typescript
// ═══════════════════════════════════════════════════════════════
// TYPESCRIPT CONDITIONALS
// ═══════════════════════════════════════════════════════════════

// --- Basic if/else ---
const score: number = 85;

if (score >= 90) {
    console.log("A");
} else if (score >= 80) {
    console.log("B");
} else if (score >= 70) {
    console.log("C");
} else {
    console.log("F");
}

// --- Ternary Operator ---
const result: string = score >= 60 ? "Pass" : "Fail";

// --- Nested Ternary (use sparingly) ---
const grade: string =
    score >= 90 ? "A" :
    score >= 80 ? "B" :
    score >= 70 ? "C" : "F";

// --- Switch Statement ---
const day: number = 3;
switch (day) {
    case 1:
        console.log("Monday");
        break;
    case 2:
        console.log("Tuesday");
        break;
    case 3:
    case 4:
    case 5:
        console.log("Midweek");
        break;
    default:
        console.log("Weekend");
}

// --- Type Guards (TypeScript-specific) ---
interface Cat {
    meow(): void;
}

interface Dog {
    bark(): void;
}

function isCat(pet: Cat | Dog): pet is Cat {
    return (pet as Cat).meow !== undefined;
}

function makeSound(pet: Cat | Dog) {
    if (isCat(pet)) {
        pet.meow();  // TypeScript knows pet is Cat here
    } else {
        pet.bark();  // TypeScript knows pet is Dog here
    }
}

// --- Discriminated Unions ---
type Shape =
    | { kind: "circle"; radius: number }
    | { kind: "square"; size: number }
    | { kind: "rectangle"; width: number; height: number };

function getArea(shape: Shape): number {
    switch (shape.kind) {
        case "circle":
            return Math.PI * shape.radius ** 2;
        case "square":
            return shape.size ** 2;
        case "rectangle":
            return shape.width * shape.height;
        // TypeScript ensures exhaustive checking
    }
}

// --- Nullish Coalescing (??) vs OR (||) ---
const value1: string | null = null;
const value2: string = "";

// || returns right side for ANY falsy value
console.log(value1 || "default");  // "default"
console.log(value2 || "default");  // "default" (empty string is falsy!)

// ?? returns right side ONLY for null/undefined
console.log(value1 ?? "default");  // "default"
console.log(value2 ?? "default");  // "" (preserves empty string!)

// --- Optional Chaining (?.) ---
interface User {
    name: string;
    address?: {
        city?: string;
    };
}

const user: User = { name: "Alice" };
// Safe property access - returns undefined if any part is null/undefined
const city = user.address?.city ?? "Unknown";

// ═══════════════════════════════════════════════════════════════
// TRUTHY/FALSY IN TYPESCRIPT/JAVASCRIPT
// ═══════════════════════════════════════════════════════════════

// FALSY values: false, 0, -0, 0n, "", null, undefined, NaN
const falsyValues = [false, 0, -0, 0n, "", null, undefined, NaN];

// ⚠️ TRUTHY surprises:
console.log(Boolean([]));        // true - empty array is TRUTHY!
console.log(Boolean({}));        // true - empty object is TRUTHY!
console.log(Boolean("0"));       // true - non-empty string
console.log(Boolean("false"));   // true - non-empty string
console.log(Boolean(new Boolean(false)));  // true - object wrapper!

// ═══════════════════════════════════════════════════════════════
// COMMON PITFALLS
// ═══════════════════════════════════════════════════════════════

// PITFALL 1: Loose Equality (==) vs Strict Equality (===)
console.log(0 == "0");     // true  - type coercion
console.log(0 === "0");    // false - no coercion
console.log(null == undefined);   // true
console.log(null === undefined);  // false

// PITFALL 2: Type Narrowing with typeof
function process(value: string | number) {
    if (typeof value === "string") {
        console.log(value.toUpperCase());  // value is string here
    } else {
        console.log(value.toFixed(2));     // value is number here
    }
}

// PITFALL 3: Truthiness in conditionals
function greet(name?: string) {
    // ⚠️ This won't distinguish empty string from undefined
    if (name) {
        console.log(`Hello, ${name}`);
    } else {
        console.log("Hello, stranger");
    }
}

greet("");        // "Hello, stranger" - might not be intended
greet(undefined); // "Hello, stranger"

// Better approach:
function greetBetter(name?: string) {
    if (name !== undefined) {
        console.log(`Hello, ${name}`);  // Allows empty string
    }
}

// PITFALL 4: Switch without break
const fruit = "apple";
switch (fruit) {
    case "apple":
        console.log("Red");
        // Missing break! Falls through to next case
    case "banana":
        console.log("Yellow");
        break;
}
// Output: "Red" then "Yellow" (unintended!)
```

#### Go

```go
// ═══════════════════════════════════════════════════════════════
// GO CONDITIONALS
// ═══════════════════════════════════════════════════════════════

package main

import "fmt"

func main() {
    // --- Basic if/else ---
    // NOTE: No parentheses around condition, braces REQUIRED
    score := 85

    if score >= 90 {
        fmt.Println("A")
    } else if score >= 80 {
        fmt.Println("B")
    } else if score >= 70 {
        fmt.Println("C")
    } else {
        fmt.Println("F")
    }

    // --- If with Short Statement ---
    // Variable scoped to if block only
    if grade := calculateGrade(score); grade == "A" {
        fmt.Println("Excellent!")
    } else {
        fmt.Printf("Grade: %s\n", grade)
    }
    // grade is NOT accessible here

    // --- Switch Statement ---
    // NOTE: No break needed! Go has IMPLICIT break
    day := 3
    switch day {
    case 1:
        fmt.Println("Monday")
    case 2:
        fmt.Println("Tuesday")
    case 3, 4, 5:  // Multiple values in one case
        fmt.Println("Midweek")
    default:
        fmt.Println("Weekend")
    }

    // --- Switch with fallthrough (explicit) ---
    value := 1
    switch value {
    case 1:
        fmt.Println("One")
        fallthrough  // Explicit fall-through
    case 2:
        fmt.Println("One or Two")
    }

    // --- Switch without expression (like if-else chain) ---
    switch {
    case score >= 90:
        fmt.Println("A")
    case score >= 80:
        fmt.Println("B")
    default:
        fmt.Println("Below B")
    }

    // --- Type Switch ---
    var i interface{} = "hello"

    switch v := i.(type) {
    case int:
        fmt.Printf("Integer: %d\n", v)
    case string:
        fmt.Printf("String: %s\n", v)
    case bool:
        fmt.Printf("Boolean: %t\n", v)
    default:
        fmt.Printf("Unknown type: %T\n", v)
    }
}

func calculateGrade(score int) string {
    if score >= 90 {
        return "A"
    } else if score >= 80 {
        return "B"
    }
    return "C"
}

// ═══════════════════════════════════════════════════════════════
// GO HAS NO TERNARY OPERATOR
// ═══════════════════════════════════════════════════════════════

// ❌ This does NOT work in Go:
// result := score >= 60 ? "Pass" : "Fail"

// ✅ Use if-else or a helper function:
func ternary(condition bool, ifTrue, ifFalse string) string {
    if condition {
        return ifTrue
    }
    return ifFalse
}

// Usage:
// result := ternary(score >= 60, "Pass", "Fail")

// ═══════════════════════════════════════════════════════════════
// COMMON PITFALLS
// ═══════════════════════════════════════════════════════════════

// PITFALL 1: No implicit boolean conversion
func checkValue(value int) {
    // if value { }  // ❌ COMPILE ERROR: non-bool value
    if value != 0 { }  // ✅ Correct
}

// PITFALL 2: Short-circuit evaluation
func example() {
    var ptr *int = nil

    // Safe: short-circuit prevents nil dereference
    if ptr != nil && *ptr > 0 {
        fmt.Println(*ptr)
    }

    // ⚠️ Would panic if we used non-short-circuit &
    // (but Go only has && and ||, not & and | for booleans)
}

// PITFALL 3: Variable shadowing in if
func shadowExample() {
    x := 10
    if x := 20; x > 15 {  // New 'x' shadows outer 'x'
        fmt.Println(x)  // Prints 20
    }
    fmt.Println(x)  // Prints 10 - outer x unchanged
}

// PITFALL 4: Comparing interfaces
func compareInterfaces() {
    var a interface{} = []int{1, 2}
    var b interface{} = []int{1, 2}

    // ❌ RUNTIME PANIC: slices are not comparable
    // fmt.Println(a == b)

    // ✅ Use reflect.DeepEqual for slices, maps, etc.
    // fmt.Println(reflect.DeepEqual(a, b))  // true

    // However, some interfaces can be compared:
    var c interface{} = 42
    var d interface{} = 42
    fmt.Println(c == d)  // true - ints are comparable
}
```

#### SQL

```sql
-- ═══════════════════════════════════════════════════════════════
-- SQL CONDITIONALS
-- ═══════════════════════════════════════════════════════════════

-- --- CASE Expression (Standard SQL) ---
SELECT
    name,
    score,
    CASE
        WHEN score >= 90 THEN 'A'
        WHEN score >= 80 THEN 'B'
        WHEN score >= 70 THEN 'C'
        ELSE 'F'
    END AS grade
FROM students;

-- --- Simple CASE (Value Matching) ---
SELECT
    day_of_week,
    CASE day_of_week
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        ELSE 'Weekend'
    END AS day_name
FROM calendar;

-- --- CASE in WHERE Clause ---
SELECT *
FROM orders
WHERE
    CASE
        WHEN @filter_type = 'pending' THEN status = 'pending'
        WHEN @filter_type = 'completed' THEN status = 'completed'
        ELSE 1=1  -- Return all
    END;

-- --- CASE in ORDER BY ---
SELECT name, priority
FROM tasks
ORDER BY
    CASE priority
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END;

-- --- COALESCE (First Non-NULL) ---
SELECT
    COALESCE(nickname, first_name, 'Anonymous') AS display_name
FROM users;

-- --- NULLIF (Return NULL if equal) ---
SELECT
    total / NULLIF(count, 0) AS average  -- Prevents division by zero
FROM metrics;

-- --- IIF (SQL Server, SQLite) ---
SELECT
    name,
    IIF(score >= 60, 'Pass', 'Fail') AS result
FROM students;

-- --- IF (MySQL) ---
SELECT
    name,
    IF(score >= 60, 'Pass', 'Fail') AS result
FROM students;

-- ═══════════════════════════════════════════════════════════════
-- THREE-VALUED LOGIC (NULL Handling)
-- ═══════════════════════════════════════════════════════════════

-- ⚠️ CRITICAL: NULL is UNKNOWN, not a value

-- FALSE examples (might be surprising):
SELECT * FROM t WHERE NULL = NULL;      -- Returns NOTHING
SELECT * FROM t WHERE NULL <> NULL;     -- Returns NOTHING
SELECT * FROM t WHERE NULL = 1;         -- Returns NOTHING
SELECT * FROM t WHERE NOT (NULL = 1);   -- Returns NOTHING!

-- Correct NULL checks:
SELECT * FROM t WHERE column IS NULL;
SELECT * FROM t WHERE column IS NOT NULL;

-- Truth table for AND with NULL:
-- TRUE  AND NULL  = NULL (unknown)
-- FALSE AND NULL  = FALSE
-- NULL  AND NULL  = NULL

-- Truth table for OR with NULL:
-- TRUE  OR  NULL  = TRUE
-- FALSE OR  NULL  = NULL (unknown)
-- NULL  OR  NULL  = NULL

-- ═══════════════════════════════════════════════════════════════
-- COMMON PITFALLS
-- ═══════════════════════════════════════════════════════════════

-- PITFALL 1: NOT IN with NULL
SELECT * FROM orders
WHERE customer_id NOT IN (
    SELECT customer_id FROM blacklist
);
-- ⚠️ If blacklist contains ANY NULL, returns NOTHING!

-- Fix: Add NULL check
SELECT * FROM orders
WHERE customer_id NOT IN (
    SELECT customer_id FROM blacklist WHERE customer_id IS NOT NULL
);
-- Or use NOT EXISTS instead

-- PITFALL 2: Aggregate functions ignore NULL
SELECT AVG(score) FROM students;  -- NULL scores are ignored
SELECT COUNT(score) FROM students;  -- Counts non-NULL only
SELECT COUNT(*) FROM students;  -- Counts all rows

-- PITFALL 3: String comparison with NULL
SELECT * FROM users WHERE name = '';    -- Empty string
SELECT * FROM users WHERE name IS NULL; -- NULL (different!)

-- PITFALL 4: CASE without ELSE returns NULL
SELECT
    CASE status
        WHEN 'active' THEN 'A'
        WHEN 'inactive' THEN 'I'
        -- No ELSE: returns NULL for any other value
    END AS code
FROM users;
```

#### C++

```cpp
// ═══════════════════════════════════════════════════════════════
// C++ CONDITIONALS
// ═══════════════════════════════════════════════════════════════

#include <iostream>
#include <optional>
#include <variant>
#include <string>

int main() {
    // --- Basic if/else ---
    int score = 85;

    if (score >= 90) {
        std::cout << "A" << std::endl;
    } else if (score >= 80) {
        std::cout << "B" << std::endl;
    } else if (score >= 70) {
        std::cout << "C" << std::endl;
    } else {
        std::cout << "F" << std::endl;
    }

    // --- if with Initializer (C++17) ---
    if (int grade = calculateGrade(score); grade >= 60) {
        std::cout << "Passed with grade: " << grade << std::endl;
    }
    // grade is not accessible here

    // --- Ternary Operator ---
    std::string result = score >= 60 ? "Pass" : "Fail";

    // --- Switch Statement ---
    // ⚠️ Fall-through is DEFAULT behavior (like Java)
    int day = 3;
    switch (day) {
        case 1:
            std::cout << "Monday" << std::endl;
            break;
        case 2:
            std::cout << "Tuesday" << std::endl;
            break;
        case 3:
        case 4:
        case 5:
            std::cout << "Midweek" << std::endl;
            break;
        default:
            std::cout << "Weekend" << std::endl;
    }

    // --- Switch with Initializer (C++17) ---
    switch (int computed = compute(); computed) {
        case 0:
            std::cout << "Zero" << std::endl;
            break;
        default:
            std::cout << "Non-zero: " << computed << std::endl;
    }

    // --- [[fallthrough]] Attribute (C++17) ---
    // Explicitly marks intentional fall-through
    int value = 1;
    switch (value) {
        case 1:
            std::cout << "One" << std::endl;
            [[fallthrough]];  // Suppresses compiler warning
        case 2:
            std::cout << "One or Two" << std::endl;
            break;
    }

    // --- constexpr if (C++17) - Compile-time branching ---
    if constexpr (sizeof(int) == 4) {
        std::cout << "32-bit integers" << std::endl;
    } else {
        std::cout << "Non-32-bit integers" << std::endl;
    }

    return 0;
}

// --- std::optional Conditionals (C++17) ---
void processOptional() {
    std::optional<int> maybeValue = getValue();

    if (maybeValue.has_value()) {
        std::cout << "Value: " << *maybeValue << std::endl;
    }

    // Or using value_or
    int value = maybeValue.value_or(0);
}

// --- std::variant with std::visit (C++17) ---
void processVariant() {
    std::variant<int, std::string, double> var = "hello";

    std::visit([](auto&& arg) {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, int>) {
            std::cout << "Integer: " << arg << std::endl;
        } else if constexpr (std::is_same_v<T, std::string>) {
            std::cout << "String: " << arg << std::endl;
        } else if constexpr (std::is_same_v<T, double>) {
            std::cout << "Double: " << arg << std::endl;
        }
    }, var);
}

// ═══════════════════════════════════════════════════════════════
// COMMON PITFALLS
// ═══════════════════════════════════════════════════════════════

void pitfalls() {
    // PITFALL 1: Assignment in condition (valid but dangerous!)
    int x = 5;
    if (x = 10) {  // ⚠️ Always true! Assigns 10, then checks if non-zero
        // This runs even though x was 5
    }
    // Use: if (x == 10) for comparison
    // Modern compilers warn about this

    // PITFALL 2: Dangling else
    int a = 1, b = 2;
    if (a > 0)
        if (b > 0)
            std::cout << "both positive" << std::endl;
    else  // ⚠️ Belongs to inner if, not outer!
        std::cout << "a is not positive" << std::endl;
    // Always use braces to avoid confusion

    // PITFALL 3: Floating-point comparison
    double d = 0.1 + 0.2;
    if (d == 0.3) {  // ⚠️ May be FALSE due to floating-point precision
        // ...
    }
    // Use: if (std::abs(d - 0.3) < 1e-9)

    // PITFALL 4: Implicit bool conversion
    int* ptr = nullptr;
    if (ptr) {  // Valid: nullptr converts to false
        // ...
    }

    int count = 0;
    if (count) {  // Valid: 0 converts to false
        // ...
    }

    // PITFALL 5: Switch with enum class
    enum class Color { Red, Green, Blue };
    Color c = Color::Red;

    switch (c) {
        case Color::Red:  // Must use fully qualified name
            break;
        case Color::Green:
            break;
        case Color::Blue:
            break;
        // Compiler warns if cases are missing
    }
}
```

#### Spark (PySpark)

```python
# ═══════════════════════════════════════════════════════════════
# SPARK/PYSPARK CONDITIONALS
# ═══════════════════════════════════════════════════════════════

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

spark = SparkSession.builder.appName("Conditionals").getOrCreate()

# Sample DataFrame
df = spark.createDataFrame([
    (1, "Alice", 85, None),
    (2, "Bob", 92, "premium"),
    (3, "Charlie", 78, "basic"),
    (4, "Diana", None, "premium"),
], ["id", "name", "score", "tier"])

# --- when/otherwise (Ternary-like) ---
# Equivalent to CASE WHEN in SQL
df_graded = df.withColumn(
    "grade",
    F.when(F.col("score") >= 90, "A")
     .when(F.col("score") >= 80, "B")
     .when(F.col("score") >= 70, "C")
     .otherwise("F")
)

# --- when with Multiple Conditions ---
df_status = df.withColumn(
    "status",
    F.when(
        (F.col("score") >= 80) & (F.col("tier") == "premium"),
        "VIP"
    ).when(
        F.col("score") >= 80,
        "High Performer"
    ).otherwise("Standard")
)

# --- Null Handling with coalesce ---
df_filled = df.withColumn(
    "tier_filled",
    F.coalesce(F.col("tier"), F.lit("free"))  # First non-null
)

# --- Null Checks ---
df_null_check = df.filter(
    F.col("score").isNotNull() & F.col("tier").isNull()
)

# --- isnull / isnan Functions ---
df_clean = df.filter(
    ~F.isnull("score") & ~F.isnan("score")  # Not null and not NaN
)

# --- nanvl (Replace NaN with value) ---
# Useful for float columns
df_nan_handled = df.withColumn(
    "score_clean",
    F.nanvl(F.col("score"), F.lit(0))
)

# --- expr for SQL-like Conditionals ---
df_expr = df.withColumn(
    "grade",
    F.expr("""
        CASE
            WHEN score >= 90 THEN 'A'
            WHEN score >= 80 THEN 'B'
            WHEN score >= 70 THEN 'C'
            WHEN score IS NULL THEN 'N/A'
            ELSE 'F'
        END
    """)
)

# ═══════════════════════════════════════════════════════════════
# CONDITIONAL FILTERING
# ═══════════════════════════════════════════════════════════════

# --- filter/where with conditions ---
premium_high_scorers = df.filter(
    (F.col("tier") == "premium") & (F.col("score") > 80)
)

# --- Multiple OR conditions ---
special_users = df.filter(
    (F.col("tier") == "premium") |
    (F.col("score") >= 90) |
    (F.col("name").isin(["Alice", "Bob"]))
)

# --- Negation ---
non_premium = df.filter(~(F.col("tier") == "premium"))

# --- Between ---
mid_scorers = df.filter(F.col("score").between(70, 89))

# ═══════════════════════════════════════════════════════════════
# CONDITIONAL AGGREGATION
# ═══════════════════════════════════════════════════════════════

# --- Count with condition ---
result = df.agg(
    F.count(F.when(F.col("score") >= 80, True)).alias("high_scorers"),
    F.count(F.when(F.col("tier") == "premium", True)).alias("premium_count"),
    F.avg(F.when(F.col("tier") == "premium", F.col("score"))).alias("premium_avg")
)

# --- Sum with condition ---
sales_df = spark.createDataFrame([
    ("Q1", "Product A", 100),
    ("Q1", "Product B", 200),
    ("Q2", "Product A", 150),
], ["quarter", "product", "sales"])

q1_sales = sales_df.agg(
    F.sum(F.when(F.col("quarter") == "Q1", F.col("sales")).otherwise(0)).alias("q1_total")
)

# ═══════════════════════════════════════════════════════════════
# UDF WITH CONDITIONALS
# ═══════════════════════════════════════════════════════════════

from pyspark.sql.functions import udf

@udf(StringType())
def classify_score(score):
    """Python UDF with conditional logic"""
    if score is None:
        return "Unknown"
    elif score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    else:
        return "Needs Improvement"

df_classified = df.withColumn("classification", classify_score(F.col("score")))

# ⚠️ Note: UDFs are slower than native Spark functions
# Prefer when/otherwise over UDFs when possible

# ═══════════════════════════════════════════════════════════════
# COMMON PITFALLS
# ═══════════════════════════════════════════════════════════════

# PITFALL 1: NULL comparison
# ❌ WRONG: This will never be true for NULL values
df.filter(F.col("tier") != "premium")  # Excludes NULLs!

# ✅ CORRECT: Explicitly handle NULLs
df.filter(
    (F.col("tier") != "premium") | F.col("tier").isNull()
)

# PITFALL 2: Using Python operators with columns
# ❌ WRONG:
# df.filter(col("score") > 80 and col("tier") == "premium")

# ✅ CORRECT: Use & (not 'and') with parentheses
df.filter((F.col("score") > 80) & (F.col("tier") == "premium"))

# PITFALL 3: Type mismatch in when/otherwise
# ⚠️ All branches should return same type
df.withColumn(
    "result",
    F.when(F.col("score") >= 90, "A")  # String
     .when(F.col("score") >= 80, 2)     # Integer - type mismatch!
     .otherwise("F")
)
# Better: Ensure consistent types

# PITFALL 4: Forgetting otherwise
# If no otherwise(), unmatched values become NULL
df.withColumn(
    "partial_grade",
    F.when(F.col("score") >= 90, "A")
     .when(F.col("score") >= 80, "B")
    # No otherwise - scores below 80 become NULL
)
```

---

### 2.4 Short-Circuit Evaluation

```
┌────────────────────────────────────────────────────────────────┐
│  SHORT-CIRCUIT EVALUATION                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  AND (&&, and, &):                                             │
│  ┌───────┐     ┌───────┐                                       │
│  │ A=F   │ ──► │ STOP  │  If first is FALSE, don't eval B     │
│  └───────┘     └───────┘                                       │
│                                                                │
│  OR (||, or, |):                                               │
│  ┌───────┐     ┌───────┐                                       │
│  │ A=T   │ ──► │ STOP  │  If first is TRUE, don't eval B      │
│  └───────┘     └───────┘                                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘

| Language | Short-Circuit Ops | Non-Short-Circuit |
|----------|-------------------|-------------------|
| Java     | &&, ||            | &, |              |
| Python   | and, or           | (none)            |
| TS/JS    | &&, ||, ??        | (none)            |
| Go       | &&, ||            | (none)            |
| SQL      | AND, OR           | (depends on DBMS) |
| C++      | &&, ||            | &, |              |
| Spark    | &, |              | (always eager)    |
```

**Interview Example: Safe Null Check**

```java
// Java
if (str != null && str.length() > 0) { }  // Safe
if (str != null & str.length() > 0) { }   // ⚠️ Unsafe! Both sides evaluated

// Python
if lst and lst[0] > 0:  # Safe - short-circuits if lst is empty

// TypeScript
if (obj && obj.property) { }  // Safe
if (obj?.property) { }        // Modern: optional chaining
```

---

## 3. Design Philosophy Links

### Official Documentation

| Language | Conditionals Documentation |
|----------|---------------------------|
| **Java** | [Control Flow Statements](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/flow.html) |
| **Python** | [Compound Statements](https://docs.python.org/3/reference/compound_stmts.html) |
| **TypeScript** | [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) |
| **Go** | [Statements](https://go.dev/ref/spec#Statements) |
| **SQL (PostgreSQL)** | [Conditional Expressions](https://www.postgresql.org/docs/current/functions-conditional.html) |
| **C++** | [if statement](https://en.cppreference.com/w/cpp/language/if) |
| **Spark** | [Column Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/column.html) |

### Language Evolution

| Feature | Java | Python | TypeScript | C++ |
|---------|------|--------|------------|-----|
| **Pattern Matching** | 21+ | 3.10+ | Limited | No |
| **Switch Expression** | 14+ | N/A | No | No |
| **Nullish Coalescing** | N/A | N/A | ES2020 | C++17 `std::optional` |
| **if with init** | No | No | No | C++17 |

---

## 4. Palantir Context Hint

### 4.1 Foundry/OSDK Relevance

```
┌────────────────────────────────────────────────────────────────┐
│  FOUNDRY DATA PIPELINE CONDITIONALS                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Data Quality Checks:                                          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  df.withColumn("is_valid",                           │      │
│  │      F.when(F.col("value").isNull(), False)          │      │
│  │       .when(F.col("value") < 0, False)               │      │
│  │       .otherwise(True)                               │      │
│  │  )                                                   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                │
│  Permission Logic (OSDK):                                      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  function canAccess(user: User, resource: Resource) {│      │
│  │      return user.roles.includes('admin')             │      │
│  │          || (user.department === resource.owner      │      │
│  │              && resource.visibility !== 'private');  │      │
│  │  }                                                   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                │
│  Ontology Action Guards:                                       │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  if (action.type === 'DELETE' &&                     │      │
│  │      !user.permissions.canDelete) {                  │      │
│  │      throw new UnauthorizedError();                  │      │
│  │  }                                                   │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Interview Questions

**Level 1: Basic Understanding**

1. **What's the difference between `==` and `===` in JavaScript/TypeScript?**
   - Expected: `==` performs type coercion, `===` is strict equality
   - Trap: `null == undefined` is `true`, but `null === undefined` is `false`

2. **Why is `if (x = 5)` a bug in most cases?**
   - Expected: Assignment returns the assigned value, always truthy
   - Follow-up: Which language prevents this? (Java won't compile)

**Level 2: Language Comparison**

3. **Compare switch behavior in Java vs Go**
   ```
   Expected answer:
   - Java: Fall-through by default (need break)
   - Go: Implicit break (need fallthrough keyword)
   ```

4. **What's the output?**
   ```javascript
   console.log([] == false);   // ?
   console.log([] === false);  // ?
   console.log(!![]);          // ?
   ```
   - Answer: `true`, `false`, `true`
   - Explanation: `[]` coerces to `""` to `0` to `false` for `==`, but `[]` is truthy

**Level 3: Gotchas and Edge Cases**

5. **TRAP QUESTION: What's wrong with this SQL?**
   ```sql
   SELECT * FROM users WHERE status NOT IN (SELECT status FROM blacklist);
   ```
   - If `blacklist.status` contains NULL, returns nothing!
   - Fix: Add `WHERE status IS NOT NULL` in subquery

6. **TRAP QUESTION: Python gotcha**
   ```python
   x = 256
   y = 256
   print(x is y)  # ?

   x = 257
   y = 257
   print(x is y)  # ?
   ```
   - Answer: `True`, `False` (CPython caches -5 to 256)
   - Real answer: Use `==` for value comparison!

**Level 4: System Design**

7. **How would you implement a rule engine with complex conditions in a Spark pipeline?**
   ```
   Expected approach:
   - Define rules as configuration (JSON/YAML)
   - Parse rules into Spark expressions
   - Use when/otherwise chains or expr()
   - Consider broadcast variables for rule lookup
   ```

8. **Design a feature flag system that supports conditional rollout**
   ```
   Expected considerations:
   - User targeting (percentage, specific IDs, groups)
   - Environment-based conditions
   - A/B testing integration
   - Short-circuit evaluation for performance
   ```

### 4.3 Common Interview Traps

```
┌────────────────────────────────────────────────────────────────┐
│  ⚠️  TOP 5 CONDITIONAL TRAPS IN INTERVIEWS                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. Empty Array Truthiness                                     │
│     JavaScript: [] is truthy                                   │
│     Python: [] is falsy                                        │
│                                                                │
│  2. String "0" Truthiness                                      │
│     JavaScript: "0" is truthy (non-empty string)              │
│     All: "0" == 0 is true (type coercion)                     │
│                                                                │
│  3. NULL Comparisons                                           │
│     SQL: NULL = NULL is NULL, not TRUE!                       │
│     Use IS NULL, not = NULL                                    │
│                                                                │
│  4. Integer Object Equality                                    │
│     Java: new Integer(127) == new Integer(127) might be true  │
│           new Integer(128) == new Integer(128) is false       │
│     Always use .equals() for objects                          │
│                                                                │
│  5. NaN Comparisons                                            │
│     All: NaN === NaN is false!                                │
│     Use Number.isNaN() or isnan()                             │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 5. Cross-References

### Related F-Series (Fundamentals)

| KB | Topic | Relevance |
|----|-------|-----------|
| F10_variables_types.md | Variables & Types | Type system affects boolean evaluation |
| F20_operators.md | Operators | Comparison and logical operators |
| F31_loops.md | Loops | Loop conditions use same boolean logic |
| F32_functions.md | Functions | Guard clauses, early returns |
| F33_error_handling.md | Error Handling | Conditional error handling |

### Related I-Series (Intermediate)

| KB | Topic | Relevance |
|----|-------|-----------|
| I50_pattern_matching.md | Pattern Matching | Advanced conditional techniques |
| I55_null_safety.md | Null Safety | Optional types, null handling |

### Related A-Series (Advanced)

| KB | Topic | Relevance |
|----|-------|-----------|
| A70_type_guards.md | Type Guards | TypeScript narrowing |
| A75_monads.md | Monads | Maybe/Option pattern |

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│  CONDITIONALS CHEAT SHEET                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  TERNARY:                                                      │
│    Java/C++/TS:  cond ? true_val : false_val                  │
│    Python:       true_val if cond else false_val              │
│    Go:           (none - use if/else)                         │
│    Spark:        when(cond, true_val).otherwise(false_val)    │
│    SQL:          CASE WHEN cond THEN true ELSE false END      │
│                                                                │
│  NULL COALESCING:                                              │
│    Java:         Optional.orElse()                            │
│    Python:       value or default                              │
│    TypeScript:   value ?? default                              │
│    Go:           (none - use if)                               │
│    SQL:          COALESCE(value, default)                      │
│    Spark:        coalesce(col, default)                        │
│                                                                │
│  SAFE NAVIGATION:                                              │
│    Java 8+:      Optional.map().orElse()                       │
│    Python:       value and value.attr                         │
│    TypeScript:   obj?.prop                                     │
│    Go:           if obj != nil { obj.prop }                   │
│                                                                │
│  NULL CHECK:                                                   │
│    Java:         obj != null                                   │
│    Python:       obj is not None                              │
│    TypeScript:   obj !== null && obj !== undefined            │
│    Go:           obj != nil                                   │
│    SQL:          column IS NOT NULL                           │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

> **Version**: 1.0.0 | **Last Updated**: 2026-01-18
> **Maintainer**: ODA Knowledge Base System
> **Review Cycle**: Quarterly
