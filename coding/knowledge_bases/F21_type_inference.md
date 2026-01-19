# F21: Type Inference (타입 추론)

> **Concept ID**: `F21_type_inference`
> **Universal Principle**: 컴파일러/인터프리터가 명시적 선언 없이 타입을 자동으로 결정하는 메커니즘
> **Prerequisites**: F20_static_vs_dynamic_typing

---

## 1. Universal Concept (언어 무관 개념 정의)

### What is Type Inference?

Type inference is the automatic deduction of data types by a compiler or interpreter without explicit type annotations from the programmer. The system analyzes the context—initialization values, function return statements, and usage patterns—to determine the appropriate type.

```
┌─────────────────────────────────────────────────────────────────┐
│                    TYPE INFERENCE FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Source Code          Analysis            Inferred Type        │
│   ───────────          ────────            ─────────────        │
│                                                                 │
│   x = 42         →    Literal Analysis   →    int              │
│   y = x + 1.0    →    Expression Type    →    float            │
│   z = [1, 2, 3]  →    Collection Type    →    List[int]        │
│   f(x)           →    Constraint Solving →    Return Type       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mental Model: The Detective Compiler

```
┌─────────────────────────────────────────────────────────────────┐
│              🔍 TYPE INFERENCE AS DETECTIVE WORK                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CLUE 1: Initialization Value                                  │
│   ┌─────────────────────────────────────────┐                   │
│   │  var name = "Alice"                     │                   │
│   │       ↓                                 │                   │
│   │  "Alice" is String literal → name: String                   │
│   └─────────────────────────────────────────┘                   │
│                                                                 │
│   CLUE 2: Expression Context                                    │
│   ┌─────────────────────────────────────────┐                   │
│   │  var sum = a + b  // a: int, b: int     │                   │
│   │       ↓                                 │                   │
│   │  int + int = int → sum: int             │                   │
│   └─────────────────────────────────────────┘                   │
│                                                                 │
│   CLUE 3: Function Return                                       │
│   ┌─────────────────────────────────────────┐                   │
│   │  func getUser() { return User(...) }    │                   │
│   │       ↓                                 │                   │
│   │  return User → return type: User        │                   │
│   └─────────────────────────────────────────┘                   │
│                                                                 │
│   CLUE 4: Generic Constraints                                   │
│   ┌─────────────────────────────────────────┐                   │
│   │  List.of(1, 2, 3)                       │                   │
│   │       ↓                                 │                   │
│   │  Elements are int → List<Integer>       │                   │
│   └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Local vs Global Type Inference

```
┌─────────────────────────────────────────────────────────────────┐
│         LOCAL INFERENCE              GLOBAL INFERENCE           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Scope: Single expression/          Scope: Entire program      │
│          statement                                              │
│                                                                 │
│   ┌─────────────────────┐            ┌─────────────────────┐    │
│   │ var x = 42          │            │ // Infers from ALL  │    │
│   │ // Type known here  │            │ // usages of x      │    │
│   │ // from initializer │            │ x = 42              │    │
│   └─────────────────────┘            │ print(x + 1)        │    │
│                                      │ y = x / 2           │    │
│   Languages:                         │ // Analyzes flow    │    │
│   - Java (var)                       └─────────────────────┘    │
│   - Go (:=)                                                     │
│   - C++ (auto)                       Languages:                 │
│   - TypeScript (simple)              - Haskell                  │
│                                      - ML/OCaml                 │
│   Pros: Fast compilation             - Rust (partial)           │
│   Cons: Requires initializer                                    │
│                                      Pros: Minimal annotations  │
│                                      Cons: Slower compilation   │
│                                            Complex errors       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Hindley-Milner Type System (Advanced)

```
┌─────────────────────────────────────────────────────────────────┐
│              HINDLEY-MILNER TYPE INFERENCE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Foundation of modern type inference (ML, Haskell, Rust)       │
│                                                                 │
│   Core Idea: Constraint-based unification                       │
│                                                                 │
│   Example:                                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  let id = λx. x                                         │   │
│   │                                                         │   │
│   │  Step 1: Assign type variable                           │   │
│   │          id : α → β  (unknown α, β)                     │   │
│   │                                                         │   │
│   │  Step 2: Analyze body                                   │   │
│   │          x is returned, so β = α                        │   │
│   │                                                         │   │
│   │  Step 3: Unify                                          │   │
│   │          id : α → α  (polymorphic identity)             │   │
│   │                                                         │   │
│   │  Step 4: Generalize                                     │   │
│   │          id : ∀α. α → α                                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   Practical Impact:                                             │
│   - TypeScript uses bidirectional type checking (inspired by)   │
│   - Rust uses local inference with borrow checker constraints   │
│   - Go intentionally avoids global inference for simplicity     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why Type Inference Matters

| Benefit | Without Inference | With Inference |
|---------|-------------------|----------------|
| **Verbosity** | `Map<String, List<Integer>> m = new HashMap<String, List<Integer>>();` | `var m = new HashMap<String, List<Integer>>();` |
| **Refactoring** | Change type in 2 places | Change type in 1 place |
| **Readability** | Type dominates, logic hidden | Logic clear, type implicit |
| **Safety** | Same (compile-time checked) | Same (compile-time checked) |

---

## 2. Semantic Comparison Matrix (의미론적 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|----|----|-----|-------|
| **Inference Keyword** | `var` (10+) | N/A (dynamic) | `let`/`const` | `:=` | implicit | `auto` | implicit |
| **Function Return** | No inference | N/A | Yes (inferred) | Yes (required explicit) | N/A | Yes (`auto`) | Yes |
| **Generic Inference** | Diamond `<>` | TypeVar hints | Full inference | No generics* | N/A | Template deduction | DataFrame schema |
| **Bidirectional** | Limited | N/A | Yes (contextual) | No | N/A | Limited | No |
| **Lambda Params** | Contextual | N/A | Contextual | N/A | N/A | `auto` (C++14) | Contextual |
| **Pitfall** | Primitive literals | N/A | `any` escape | Interface{} | Silent coercion | Reference decay | Schema mismatch |

*Go 1.18+ has type parameters but limited inference

### 2.2 Semantic Notes

#### Java: `var` (Local Variable Type Inference, Java 10+)

```java
// ✅ GOOD: Clear initialization
var names = new ArrayList<String>();     // ArrayList<String>
var count = 42;                          // int (not Integer)
var user = userRepository.findById(id);  // Optional<User>

// ✅ Diamond with var
var map = new HashMap<String, List<Integer>>();  // Full type inferred

// ❌ FAILS: No initializer
var x;  // Compile error: cannot infer type

// ❌ FAILS: Null initializer
var y = null;  // Compile error: cannot infer type

// ❌ FAILS: Lambda expressions
var fn = (x) -> x * 2;  // Compile error: lambda needs target type

// ⚠️ CAUTION: Primitive vs Boxed
var i = 42;      // int (primitive)
var j = (Integer) 42;  // Integer (boxed)

// ⚠️ CAUTION: Interface vs Implementation
var list = new ArrayList<String>();  // ArrayList<String>, not List<String>
// If you need List<String>:
List<String> list = new ArrayList<>();

// Function return type: NOT inferred
String getName() { return "Alice"; }  // Must declare String
```

#### Python: Dynamic Typing (No Traditional Inference)

```python
# Python is dynamically typed - no compile-time inference
x = 42          # Runtime type: int
x = "hello"     # Now runtime type: str (no error)

# Type hints are OPTIONAL and not enforced at runtime
def greet(name: str) -> str:
    return f"Hello, {name}"

greet(42)  # No runtime error! Type hints are documentation only

# Type inference with mypy/pyright (static analyzers)
from typing import reveal_type

x = [1, 2, 3]
reveal_type(x)  # mypy: list[int]

# Generic inference with type checkers
from typing import TypeVar, Generic

T = TypeVar('T')

class Box(Generic[T]):
    def __init__(self, item: T):
        self.item = item

box = Box(42)  # mypy infers Box[int]

# ⚠️ PITFALL: Type hints don't prevent runtime errors
def add(a: int, b: int) -> int:
    return a + b

add("hello", "world")  # Returns "helloworld" at runtime!
```

#### TypeScript: Comprehensive Inference

```typescript
// Local inference from initializer
let name = "Alice";     // string
const age = 30;         // 30 (literal type due to const)
let count = 42;         // number

// Function return type inference
function getUser() {
    return { name: "Alice", age: 30 };
}  // Return type: { name: string; age: number; }

// Generic inference
const numbers = [1, 2, 3];           // number[]
const mixed = [1, "two", true];      // (string | number | boolean)[]

// Bidirectional (contextual) typing
const handler: (e: MouseEvent) => void = (e) => {
    console.log(e.clientX);  // e is MouseEvent (from context)
};

// Array method inference
const doubled = [1, 2, 3].map(x => x * 2);  // number[]

// ⚠️ PITFALL: `any` escapes type checking
const data: any = fetchData();
const name = data.name;  // any - no inference, no safety

// ⚠️ PITFALL: Empty array inference
const items = [];  // any[] - loses type info
const items: string[] = [];  // Explicit is better

// ⚠️ PITFALL: Object literal excess property check bypass
interface User { name: string; }
const obj = { name: "Alice", age: 30 };  // { name: string; age: number }
const user: User = obj;  // OK - structural typing allows this
```

#### Go: Short Variable Declaration (`:=`)

```go
// Short declaration infers type
name := "Alice"     // string
count := 42         // int
ratio := 3.14       // float64

// Function return types MUST be explicit
func GetUser() User {  // Return type required
    return User{Name: "Alice"}
}

// Multiple return values
func divide(a, b int) (int, error) {  // Must declare both
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// Inference in short declaration
result, err := divide(10, 2)  // int, error inferred from function

// ⚠️ FAILS: Must have initializer
var x  // Compile error: missing type or initializer

// ⚠️ PITFALL: interface{}/any loses type info
func process(data interface{}) {
    // Must type assert to use
    if str, ok := data.(string); ok {
        fmt.Println(str)
    }
}

// Go 1.18+ Type Parameters (limited inference)
func Min[T constraints.Ordered](a, b T) T {
    if a < b { return a }
    return b
}

result := Min(1, 2)      // T inferred as int
result := Min[int](1, 2) // Explicit (sometimes required)

// ⚠️ PITFALL: Numeric literal defaults
x := 42      // int (not int32, int64)
y := 3.14    // float64 (not float32)
```

#### SQL: Implicit Type Inference

```sql
-- Column types inferred from expressions
SELECT
    1 + 1 AS sum,           -- INTEGER
    'Hello' AS greeting,    -- VARCHAR/TEXT
    1.5 * 2 AS product,     -- DECIMAL/NUMERIC
    NOW() AS current_time;  -- TIMESTAMP

-- CASE expression inference
SELECT
    CASE
        WHEN status = 1 THEN 'Active'
        WHEN status = 0 THEN 'Inactive'
        ELSE NULL
    END AS status_text;  -- VARCHAR (from string literals)

-- ⚠️ PITFALL: Implicit coercion can surprise
SELECT 1 + '2';       -- Some DBs: 3, others: '12', others: ERROR

-- ⚠️ PITFALL: NULL type inference
SELECT COALESCE(NULL, NULL);  -- Type unknown, may need CAST

-- Aggregate function inference
SELECT
    COUNT(*) AS cnt,           -- BIGINT
    SUM(price) AS total,       -- Same as price column type
    AVG(price) AS average;     -- DECIMAL (for precision)

-- CTE type inference
WITH user_stats AS (
    SELECT user_id, COUNT(*) as order_count  -- Types from base tables
    FROM orders
    GROUP BY user_id
)
SELECT * FROM user_stats;
```

#### C++: `auto` (C++11+)

```cpp
// Basic auto inference
auto x = 42;           // int
auto y = 3.14;         // double
auto s = "hello";      // const char* (NOT std::string!)
auto str = std::string("hello");  // std::string

// Range-based for with auto
std::vector<int> nums = {1, 2, 3};
for (auto n : nums) { /* int */ }
for (auto& n : nums) { /* int& - reference */ }
for (const auto& n : nums) { /* const int& */ }

// Function return type deduction (C++14)
auto add(int a, int b) {
    return a + b;  // Return type: int
}

// Template argument deduction
template<typename T>
void process(T value) { /* ... */ }

process(42);       // T = int
process("hello");  // T = const char*

// Lambda with auto parameters (C++14)
auto lambda = [](auto x, auto y) { return x + y; };
lambda(1, 2);      // int
lambda(1.5, 2.5);  // double

// ⚠️ PITFALL: Reference/const decay
int& getRef();
auto x = getRef();        // int (NOT int&!) - reference decays
auto& y = getRef();       // int& (explicit reference)

const int ci = 42;
auto z = ci;              // int (NOT const int!) - const decays

// ⚠️ PITFALL: Initializer list
auto list = {1, 2, 3};    // std::initializer_list<int>
// NOT std::vector<int>!

// decltype for preserving exact type
decltype(auto) perfect = getRef();  // int& preserved
```

#### Spark: Schema Inference

```python
# Spark DataFrame schema inference from data
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# JSON schema inference
df = spark.read.json("data.json")
df.printSchema()
# root
#  |-- name: string (nullable = true)
#  |-- age: long (nullable = true)  # Note: long, not int

# CSV with inferred types
df = spark.read.option("inferSchema", True).csv("data.csv")

# ⚠️ PITFALL: Inference samples only (default 1000 rows)
df = spark.read \
    .option("inferSchema", True) \
    .option("samplingRatio", 0.5) \
    .json("large_data.json")

# ⚠️ PITFALL: Inconsistent data causes wrong inference
# Row 1: {"value": 42}      -> inferred as long
# Row 1000: {"value": "N/A"} -> fails at runtime!

# BEST PRACTICE: Explicit schema
from pyspark.sql.types import StructType, StructField, StringType, LongType

schema = StructType([
    StructField("name", StringType(), True),
    StructField("age", LongType(), True)
])
df = spark.read.schema(schema).json("data.json")

# Column type inference in expressions
df = df.withColumn("age_plus_one", df.age + 1)  # LongType inferred

# UDF return type MUST be explicit
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

@udf(returnType=StringType())  # Must specify!
def format_name(name):
    return name.upper()

# Catalyst optimizer inference
df.filter(df.age > 18).select("name")  # Types propagated through plan
```

### 2.3 When Inference Fails (Explicit Types Required)

```
┌─────────────────────────────────────────────────────────────────┐
│              WHEN EXPLICIT TYPES ARE NEEDED                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. No Initializer                                             │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Java:   var x;           // ❌ Error                   │   │
│   │  Go:     var x            // ❌ Error                   │   │
│   │  C++:    auto x;          // ❌ Error                   │   │
│   │  Fix:    int x = 0;       // ✅ Explicit                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   2. Null/Empty Initialization                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Java:   var x = null;    // ❌ Error                   │   │
│   │  TS:     let x = [];      // any[] - loses type         │   │
│   │  Fix:    String x = null; // ✅                         │   │
│   │          let x: string[] = [];                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   3. Lambda/Closure Parameters                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Java:   var f = x -> x*2; // ❌ No target type         │   │
│   │  Fix:    Function<Integer, Integer> f = x -> x*2;       │   │
│   │          Or: IntUnaryOperator f = x -> x*2;             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   4. Ambiguous Overloads                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  void process(int x) { }                                │   │
│   │  void process(long x) { }                               │   │
│   │  process(42);  // Ambiguous in some contexts            │   │
│   │  Fix: process((int) 42);                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   5. API Boundaries (Public Interfaces)                         │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  // Public API should be explicit for documentation     │   │
│   │  public User getUser(String id) { ... }  // Not var     │   │
│   │  // Internal: var acceptable                            │   │
│   │  var user = repository.find(id);                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Design Philosophy Links (공식 문서 출처)

| Language | Primary Source | Key Section |
|----------|----------------|-------------|
| Java | [JEP 286: Local-Variable Type Inference](https://openjdk.org/jeps/286) | Style Guidelines |
| Python | [PEP 484: Type Hints](https://peps.python.org/pep-0484/) | Type Inference section |
| TypeScript | [TypeScript Handbook: Type Inference](https://www.typescriptlang.org/docs/handbook/type-inference.html) | Best Common Type |
| Go | [Go Spec: Short Variable Declarations](https://go.dev/ref/spec#Short_variable_declarations) | Type Inference rules |
| SQL | [SQL Standard ISO/IEC 9075](https://www.iso.org/standard/76583.html) | Data Type Determination |
| C++ | [C++ Reference: auto](https://en.cppreference.com/w/cpp/language/auto) | Placeholder type specifiers |
| Spark | [Spark SQL Guide: Schema Inference](https://spark.apache.org/docs/latest/sql-data-sources-json.html) | Automatically Inferred Schema |

---

## 4. Palantir Context Hint

### Foundry/OSDK Relevance

**TypeScript in OSDK:**
```typescript
// OSDK generated types are fully inferred
const objects = await client.objects.Employee.all();
// objects: Employee[] - inferred from SDK

// Action parameters inferred
const result = await client.actions.createEmployee({
    name: "Alice",  // string inferred
    age: 30         // number inferred
});

// Strict mode recommended - no implicit any
// tsconfig.json: "strict": true
```

**Spark in Foundry Transforms:**
```python
# Schema inference gotcha in Foundry
@transform_df(
    Output("/output/path"),
    source=Input("/input/path")
)
def compute(source):
    # ⚠️ Schema inference may differ between environments
    # BEST PRACTICE: Define explicit schema
    return source.select(
        F.col("id").cast("long"),
        F.col("value").cast("double")
    )
```

**Code Repositories:**
- TypeScript repos benefit from `strict: true` for maximum inference safety
- Python repos should use type hints with mypy for inference
- Spark transforms should prefer explicit schemas over inference

### Interview Relevance

**Common Interview Questions:**

1. **"Java `var`는 언제 사용해야 하나요?"**
   - Local variables with clear initializers
   - When the type is obvious from context (e.g., `new ArrayList<>()`)
   - NOT for public API return types or parameter types
   - NOT when the inferred type would be less specific than desired

2. **"`auto` vs explicit type의 trade-off는?"**
   - Pro: Reduces verbosity, easier refactoring
   - Con: Type not visible at declaration site
   - Con: May infer unexpected type (const/reference decay)
   - Rule: Use when type is obvious, explicit when clarity needed

3. **"Spark에서 schema inference의 문제점은?"**
   - Only samples data (not full scan)
   - Inconsistent data types cause runtime errors
   - Different inference across environments
   - Solution: Always define explicit schema for production

4. **"TypeScript의 bidirectional type inference란?"**
   - Inference flows both ways: from expression to context and vice versa
   - Example: callback parameter types inferred from function signature
   - Enables concise code without sacrificing type safety

---

## 5. Cross-References

### Related Concepts

| Concept | Relationship | Description |
|---------|--------------|-------------|
| → F20_static_vs_dynamic_typing | Foundation | Inference is a static typing feature |
| → F22_type_coercion_casting | Interaction | When inference fails, explicit casting needed |
| → F24_generics_polymorphism | Enhancement | Generic inference extends basic type inference |
| → F30_null_safety | Safety | Inference must handle nullable types correctly |

### Inference Interaction with Other Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                TYPE INFERENCE ECOSYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    ┌─────────────────┐                          │
│                    │ Type Inference  │                          │
│                    │    (F21)        │                          │
│                    └────────┬────────┘                          │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐          │
│   │ Generics  │      │ Coercion  │      │   Null    │          │
│   │  (F24)    │      │  (F22)    │      │  Safety   │          │
│   │           │      │           │      │  (F30)    │          │
│   │ Diamond   │      │ Fallback  │      │ Optional  │          │
│   │ Inference │      │ when      │      │ inference │          │
│   └───────────┘      │ inference │      └───────────┘          │
│                      │ fails     │                              │
│                      └───────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Existing KB Links

- **F01_binding_overview** - Variable binding includes type association
- **F02_java_binding** - Java `var` is a binding mechanism
- **F03_python_binding** - Python's dynamic nature vs type hints
- **F10_lexical_scope** - Scope affects type visibility
- **F14_closure_scope** - Lambda type inference depends on closure context

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-18 | Initial creation with 7-language coverage |
