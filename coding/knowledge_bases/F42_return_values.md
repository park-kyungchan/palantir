# F42: Return Values & Types (반환값과 타입)

> **Concept ID**: F42
> **Category**: Functions & Control Flow
> **Difficulty**: Intermediate
> **Languages**: Java, Python, TypeScript, Go, SQL, C++, Spark

---

## Section 1: Universal Concept (핵심 개념)

### What is a Return Value?

A **return value** is the output that a function produces after execution. It's the mechanism by which functions communicate results back to their callers.

**Mental Model: The Function as a Machine**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FUNCTION AS A BLACK BOX                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│       INPUTS                   FUNCTION                    OUTPUT           │
│    (Parameters)               (Processing)              (Return Value)      │
│                                                                             │
│    ┌─────────┐              ┌───────────────┐           ┌─────────┐        │
│    │  arg1   │──────────────│               │───────────│ result  │        │
│    │  arg2   │──────────────│   function    │           │         │        │
│    │  arg3   │──────────────│    body       │           │         │        │
│    └─────────┘              └───────────────┘           └─────────┘        │
│                                                                             │
│    Think of it as:                                                          │
│    • A vending machine: Insert coins → Press button → Get product          │
│    • A calculator: Enter numbers → Press = → See result                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Single vs Multiple Return Values

| Pattern | Description | Languages | Use Case |
|---------|-------------|-----------|----------|
| **Single Return** | One value returned | Java, C++, SQL (scalar) | Most function results |
| **Multiple Returns** | Multiple values natively | Go, Python (tuple) | Value + error, coordinates |
| **Wrapped Returns** | Multiple via container | Java (class), TS (object) | Complex results |
| **No Return** | void/None/undefined | All languages | Side-effect only functions |

### Return Type Inference vs Explicit Declaration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TYPE DECLARATION SPECTRUM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   EXPLICIT                                              INFERRED            │
│   ←─────────────────────────────────────────────────────────────────────→   │
│                                                                             │
│   Java (mostly)    TypeScript     Python      Go (:=)                      │
│   C++ (pre-11)     (configurable) (optional   (local only)                 │
│                                    hints)                                   │
│                                                                             │
│   EXPLICIT:                                                                 │
│   • Documentation built-in                                                  │
│   • Catches errors at compile time                                          │
│   • More verbose                                                            │
│                                                                             │
│   INFERRED:                                                                 │
│   • Less boilerplate                                                        │
│   • Can reduce clarity                                                      │
│   • Risk of unintended types                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The "No Return" Concept

Different languages express "no meaningful return value" differently:

| Language | Keyword | Meaning |
|----------|---------|---------|
| Java | `void` | Method returns nothing |
| C++ | `void` | Function returns nothing |
| Python | `None` | Implicit return value when no `return` |
| TypeScript | `void` / `undefined` | `void` = return ignored, `undefined` = actual value |
| Go | (no return type) | Function has no return values |
| SQL | N/A | Procedures vs Functions distinction |
| Spark | `None` | Python convention |

### Early Return Pattern

**The Problem: Deep Nesting**
```
function process(data) {
    if (data != null) {
        if (data.isValid()) {
            if (data.hasPermission()) {
                // Finally do the work
                return doWork(data);
            }
        }
    }
    return null;
}
```

**The Solution: Early Return (Guard Clauses)**
```
function process(data) {
    if (data == null) return null;
    if (!data.isValid()) return null;
    if (!data.hasPermission()) return null;

    return doWork(data);  // Happy path is clear
}
```

**Benefits:**
1. **Readability**: Happy path is not nested
2. **Maintainability**: Easy to add/remove conditions
3. **Debugging**: Clear exit points
4. **Cognitive Load**: Less mental stack to track

### Why Return Values Matter

1. **Functional Composition**: Chain function calls
2. **Error Handling**: Communicate success/failure
3. **State Communication**: Pass computed values
4. **Testing**: Verify function correctness
5. **Type Safety**: Catch errors at compile time

---

## Section 2: Semantic Comparison Matrix (언어별 의미 비교)

### Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **Multiple returns** | No (use class/record) | Yes (tuple) | No (tuple/object) | Yes (native!) | TABLE | No (struct/tuple) | Yes (tuple) |
| **Type inference** | `var` (local only) | No (hints optional) | Yes | `:=` (local) | N/A | `auto` | Yes |
| **Void type** | `void` | `None` | `void`/`undefined` | (omitted) | N/A | `void` | `None` |
| **Optional return** | `Optional<T>` | `T \| None` | `T \| undefined` | `(T, bool)` | NULL | `std::optional<T>` | `Optional` |
| **Never returns** | N/A | `NoReturn` | `never` | N/A | N/A | `[[noreturn]]` | N/A |
| **Covariant returns** | Yes | Yes (duck typing) | Yes | N/A | N/A | Yes (C++11) | Yes |
| **Return type docs** | Javadoc `@return` | `:rtype:` / `-> T` | JSDoc / inline | Comments | N/A | Doxygen | Docstring |

---

### Pattern 1: Basic Return Types

#### Java

```java
// ═══════════════════════════════════════════════════════════════════════════
// JAVA - Explicit return types (mandatory)
// ═══════════════════════════════════════════════════════════════════════════

public class ReturnExamples {

    // Primitive return
    public int add(int a, int b) {
        return a + b;
    }

    // Object return
    public String greet(String name) {
        return "Hello, " + name + "!";
    }

    // void - no return value
    public void logMessage(String message) {
        System.out.println(message);
        // No return statement needed (or: return;)
    }

    // var for local type inference (Java 10+)
    public String processData() {
        var result = computeResult();  // Type inferred locally
        var length = result.length();  // Also inferred
        return result;
    }

    // Generic return type
    public <T> T identity(T value) {
        return value;
    }

    // Covariant return type (subclass can return more specific type)
    public static class Animal {
        public Animal reproduce() {
            return new Animal();
        }
    }

    public static class Dog extends Animal {
        @Override
        public Dog reproduce() {  // Returns Dog, not Animal
            return new Dog();
        }
    }

    private String computeResult() {
        return "computed";
    }
}
```

#### Python

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - Dynamic typing with optional type hints
# ═══════════════════════════════════════════════════════════════════════════
from typing import Optional, TypeVar, Generic

# No type hint (dynamic)
def add(a, b):
    return a + b

# With type hints (Python 3.5+)
def add_typed(a: int, b: int) -> int:
    return a + b

# None return (explicit)
def greet(name: str) -> None:
    print(f"Hello, {name}!")
    # Implicitly returns None

# None return (implicit - same effect)
def greet_implicit(name: str):
    print(f"Hello, {name}!")

# Checking return value
result = greet("Alice")
print(result)  # None

# Union type return (Python 3.10+)
def find_user(user_id: int) -> str | None:
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)

# Generic return type
T = TypeVar('T')

def identity(value: T) -> T:
    return value

# Multiple possible return types
def parse_value(s: str) -> int | float | str:
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s
```

#### TypeScript

```typescript
// ═══════════════════════════════════════════════════════════════════════════
// TYPESCRIPT - Type inference with explicit option
// ═══════════════════════════════════════════════════════════════════════════

// Type inferred from return statement
function add(a: number, b: number) {
    return a + b;  // Return type inferred as number
}

// Explicit return type (recommended for public APIs)
function addExplicit(a: number, b: number): number {
    return a + b;
}

// void - function doesn't return meaningful value
function logMessage(message: string): void {
    console.log(message);
    // return; is optional
}

// undefined vs void distinction
function returnsUndefined(): undefined {
    return undefined;  // Must explicitly return undefined
}

function returnsVoid(): void {
    // Can return undefined or nothing
    // But return value should be ignored by caller
}

// never - function never returns (throws or infinite loop)
function throwError(message: string): never {
    throw new Error(message);
    // Code after throw is unreachable
}

function infiniteLoop(): never {
    while (true) {
        // Runs forever
    }
}

// Use case for never: Exhaustive switch checking
type Shape = "circle" | "square" | "triangle";

function getArea(shape: Shape): number {
    switch (shape) {
        case "circle":
            return Math.PI;
        case "square":
            return 1;
        case "triangle":
            return 0.5;
        default:
            // If new shape added to union but not handled,
            // TypeScript will error here
            const _exhaustive: never = shape;
            throw new Error(`Unknown shape: ${shape}`);
    }
}

// Union return type
function parseInput(input: string): number | null {
    const parsed = parseInt(input, 10);
    return isNaN(parsed) ? null : parsed;
}

// Generic return
function identity<T>(value: T): T {
    return value;
}

// Conditional return type (advanced)
function process<T extends boolean>(flag: T): T extends true ? string : number {
    return (flag ? "yes" : 42) as T extends true ? string : number;
}
```

#### Go

```go
// ═══════════════════════════════════════════════════════════════════════════
// GO - Explicit types, famous for multiple returns
// ═══════════════════════════════════════════════════════════════════════════
package main

import (
    "errors"
    "fmt"
)

// Single return
func add(a, b int) int {
    return a + b
}

// No return (void equivalent)
func logMessage(message string) {
    fmt.Println(message)
}

// ════════════════════════════════════════════════════════════════════════════
// GO MULTIPLE RETURN VALUES - THE KILLER FEATURE!
// ════════════════════════════════════════════════════════════════════════════

// Multiple returns - the (value, error) pattern
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

// Usage of multiple returns
func main() {
    // Pattern 1: Check error immediately
    result, err := divide(10, 2)
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    fmt.Printf("Result: %f\n", result)

    // Pattern 2: Ignore error (use _ blank identifier)
    result2, _ := divide(10, 0)  // Dangerous! Don't do this usually
    fmt.Println(result2)

    // Pattern 3: Only care about error
    _, err = divide(10, 0)
    if err != nil {
        fmt.Println("An error occurred")
    }
}

// Named return values (enables "naked return")
func divideNamed(a, b float64) (result float64, err error) {
    if b == 0 {
        err = errors.New("division by zero")
        return  // Returns current values of result and err
    }
    result = a / b
    return  // Returns current values
}

// Multiple return values for coordinates
func getCoordinates(address string) (lat, lng float64, err error) {
    // Geocoding logic...
    if address == "" {
        return 0, 0, errors.New("empty address")
    }
    return 37.5665, 126.9780, nil  // Seoul coordinates
}

// Type inference with := (short variable declaration)
func typeInferenceExample() {
    // Type inferred from right side
    x := 42           // int
    y := "hello"      // string
    z := 3.14         // float64

    // But return type must be explicit in function signature
    result := add(1, 2)  // result is inferred as int
    fmt.Println(x, y, z, result)
}

// ok pattern (like Python's dict.get)
func getValue(m map[string]int, key string) (int, bool) {
    value, ok := m[key]
    return value, ok
}

// Interface return (polymorphism)
type Reader interface {
    Read() string
}

type FileReader struct{}
func (f FileReader) Read() string { return "file content" }

type NetworkReader struct{}
func (n NetworkReader) Read() string { return "network content" }

func getReader(source string) Reader {
    if source == "file" {
        return FileReader{}
    }
    return NetworkReader{}
}
```

#### SQL

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- SQL - Scalar Functions vs Table-Valued Functions
-- ═══════════════════════════════════════════════════════════════════════════

-- Scalar function: Returns single value
CREATE FUNCTION calculate_tax(price DECIMAL(10,2), tax_rate DECIMAL(4,2))
RETURNS DECIMAL(10,2)
AS
BEGIN
    RETURN price * tax_rate;
END;

-- Usage
SELECT product_name, price, calculate_tax(price, 0.10) AS tax
FROM products;

-- Table-valued function: Returns a table (multiple rows/columns)
CREATE FUNCTION get_orders_by_customer(@customer_id INT)
RETURNS TABLE
AS
RETURN (
    SELECT order_id, order_date, total_amount
    FROM orders
    WHERE customer_id = @customer_id
);

-- Usage
SELECT * FROM get_orders_by_customer(123);

-- Inline table-valued function (simpler)
CREATE FUNCTION get_high_value_products(@min_price DECIMAL)
RETURNS TABLE
AS
RETURN (
    SELECT product_id, name, price
    FROM products
    WHERE price >= @min_price
);

-- Multi-statement table-valued function (more complex)
CREATE FUNCTION get_customer_summary(@customer_id INT)
RETURNS @summary TABLE (
    customer_name VARCHAR(100),
    total_orders INT,
    total_spent DECIMAL(15,2),
    avg_order_value DECIMAL(10,2)
)
AS
BEGIN
    INSERT INTO @summary
    SELECT
        c.name,
        COUNT(o.order_id),
        SUM(o.total_amount),
        AVG(o.total_amount)
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE c.customer_id = @customer_id
    GROUP BY c.name;

    RETURN;
END;

-- NULL as return value (absence of value)
CREATE FUNCTION find_manager_name(@employee_id INT)
RETURNS VARCHAR(100)
AS
BEGIN
    DECLARE @manager_name VARCHAR(100);

    SELECT @manager_name = m.name
    FROM employees e
    JOIN employees m ON e.manager_id = m.employee_id
    WHERE e.employee_id = @employee_id;

    RETURN @manager_name;  -- Returns NULL if no manager found
END;

-- PostgreSQL: RETURNS VOID for procedures
CREATE FUNCTION log_action(action_type TEXT, details TEXT)
RETURNS VOID
AS $$
BEGIN
    INSERT INTO audit_log (action_type, details, created_at)
    VALUES (action_type, details, NOW());
END;
$$ LANGUAGE plpgsql;
```

#### C++

```cpp
// ═══════════════════════════════════════════════════════════════════════════
// C++ - Explicit types with auto deduction (C++11+)
// ═══════════════════════════════════════════════════════════════════════════
#include <iostream>
#include <optional>
#include <tuple>
#include <string>
#include <variant>

// Traditional explicit return type
int add(int a, int b) {
    return a + b;
}

// void return
void logMessage(const std::string& message) {
    std::cout << message << std::endl;
}

// ════════════════════════════════════════════════════════════════════════════
// C++11: auto return type deduction
// ════════════════════════════════════════════════════════════════════════════

// Trailing return type (C++11)
auto multiply(int a, int b) -> int {
    return a * b;
}

// auto deduction (C++14) - compiler infers return type
auto divide(double a, double b) {
    return a / b;  // Return type deduced as double
}

// ⚠️ TRAP: All return paths must have same type
auto processValue(int x) {
    if (x > 0) {
        return x * 2;    // int
    }
    return 0;            // int - OK, same type
    // return "error";   // ERROR! Can't return string
}

// decltype(auto) preserves references and cv-qualifiers
decltype(auto) getReference(int& x) {
    return x;  // Returns int&, not int
}

// ════════════════════════════════════════════════════════════════════════════
// C++17: std::optional for nullable returns
// ════════════════════════════════════════════════════════════════════════════

std::optional<int> findValue(const std::string& key) {
    if (key == "answer") {
        return 42;
    }
    return std::nullopt;  // No value
}

void optionalUsage() {
    auto result = findValue("answer");

    // Check if value exists
    if (result.has_value()) {
        std::cout << "Found: " << *result << std::endl;
    }

    // Or use value_or for default
    int value = result.value_or(-1);

    // Modern style: structured binding with optional
    if (auto val = findValue("key"); val) {
        std::cout << "Value: " << *val << std::endl;
    }
}

// ════════════════════════════════════════════════════════════════════════════
// C++17: std::tuple for multiple returns (like Go)
// ════════════════════════════════════════════════════════════════════════════

std::tuple<double, bool> divideWithStatus(double a, double b) {
    if (b == 0.0) {
        return {0.0, false};  // C++17 brace initialization
    }
    return {a / b, true};
}

void tupleUsage() {
    // C++17 structured bindings (like Go's multiple assignment!)
    auto [result, success] = divideWithStatus(10.0, 2.0);
    if (success) {
        std::cout << "Result: " << result << std::endl;
    }

    // Or traditional way
    double res;
    bool ok;
    std::tie(res, ok) = divideWithStatus(10.0, 0.0);
}

// ════════════════════════════════════════════════════════════════════════════
// C++11: [[noreturn]] attribute (like TypeScript's never)
// ════════════════════════════════════════════════════════════════════════════

[[noreturn]] void throwError(const std::string& message) {
    throw std::runtime_error(message);
    // Compiler knows code after this is unreachable
}

[[noreturn]] void infiniteLoop() {
    while (true) {
        // Process events forever
    }
}

// Covariant return types (C++11)
class Base {
public:
    virtual Base* clone() const {
        return new Base(*this);
    }
};

class Derived : public Base {
public:
    // Can return Derived* instead of Base* (covariance)
    Derived* clone() const override {
        return new Derived(*this);
    }
};

// C++17: std::variant for union return types
std::variant<int, double, std::string> parseInput(const std::string& input) {
    // Try to parse as int
    try {
        return std::stoi(input);
    } catch (...) {}

    // Try to parse as double
    try {
        return std::stod(input);
    } catch (...) {}

    // Return as string
    return input;
}
```

#### Spark (PySpark)

```python
# ═══════════════════════════════════════════════════════════════════════════
# SPARK - DataFrame transformations return new DataFrames
# ═══════════════════════════════════════════════════════════════════════════
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, udf, lit, when
from pyspark.sql.types import (
    IntegerType, StringType, StructType, StructField,
    ArrayType, MapType, DoubleType
)
from typing import Optional, Tuple, List

spark = SparkSession.builder.appName("ReturnValues").getOrCreate()

# ════════════════════════════════════════════════════════════════════════════
# DataFrame Return Types - Lazy Evaluation!
# ════════════════════════════════════════════════════════════════════════════

# Transformations return new DataFrames (lazy - not executed yet)
def filter_adults(df: DataFrame) -> DataFrame:
    """Return filtered DataFrame - lazy operation."""
    return df.filter(col("age") >= 18)

def add_full_name(df: DataFrame) -> DataFrame:
    """Return DataFrame with new column."""
    return df.withColumn(
        "full_name",
        col("first_name") + lit(" ") + col("last_name")
    )

# Chaining returns (fluent API)
def process_users(df: DataFrame) -> DataFrame:
    """Chain transformations - still lazy!"""
    return (
        df
        .filter(col("active") == True)
        .withColumn("age_group",
            when(col("age") < 18, "minor")
            .when(col("age") < 65, "adult")
            .otherwise("senior")
        )
        .select("id", "full_name", "age_group")
    )

# ════════════════════════════════════════════════════════════════════════════
# UDF Return Types
# ════════════════════════════════════════════════════════════════════════════

# Simple UDF with explicit return type
@udf(returnType=IntegerType())
def square(x: int) -> int:
    return x * x if x is not None else None

# UDF returning None for invalid input
@udf(returnType=StringType())
def safe_upper(s: str) -> Optional[str]:
    if s is None:
        return None
    return s.upper()

# UDF returning complex type (struct)
result_schema = StructType([
    StructField("success", IntegerType(), False),
    StructField("message", StringType(), True)
])

@udf(returnType=result_schema)
def validate_email(email: str) -> Tuple[int, str]:
    if email is None:
        return (0, "Email is null")
    if "@" not in email:
        return (0, "Invalid email format")
    return (1, None)

# UDF returning array
@udf(returnType=ArrayType(StringType()))
def split_tags(tags: str) -> List[str]:
    if tags is None:
        return []
    return tags.split(",")

# UDF returning map
@udf(returnType=MapType(StringType(), IntegerType()))
def count_words(text: str) -> dict:
    if text is None:
        return {}
    words = text.lower().split()
    return {word: words.count(word) for word in set(words)}

# ════════════════════════════════════════════════════════════════════════════
# Action Return Types - Trigger Execution!
# ════════════════════════════════════════════════════════════════════════════

def get_statistics(df: DataFrame) -> dict:
    """Actions return concrete values to driver."""
    return {
        "count": df.count(),                    # Returns int
        "first": df.first(),                    # Returns Row or None
        "sample": df.take(5),                   # Returns List[Row]
        "columns": df.columns,                  # Returns List[str]
        "schema": df.schema.json(),             # Returns str
    }

# collect() returns List[Row] - be careful with large data!
def get_all_names(df: DataFrame) -> List[str]:
    """Collect brings all data to driver - use carefully!"""
    rows = df.select("name").collect()
    return [row.name for row in rows]

# toPandas() returns pandas DataFrame
def to_pandas_df(df: DataFrame):
    """Convert to Pandas - also collects all data to driver!"""
    return df.toPandas()  # Returns pd.DataFrame

# ════════════════════════════════════════════════════════════════════════════
# Multiple Return Pattern in Spark
# ════════════════════════════════════════════════════════════════════════════

def split_by_condition(df: DataFrame, condition) -> Tuple[DataFrame, DataFrame]:
    """Return two DataFrames: matching and non-matching."""
    matching = df.filter(condition)
    non_matching = df.filter(~condition)
    return matching, non_matching

# Usage
# adults, minors = split_by_condition(users_df, col("age") >= 18)

def validate_dataframe(df: DataFrame) -> Tuple[DataFrame, DataFrame, dict]:
    """Return valid records, invalid records, and statistics."""
    valid_df = df.filter(col("email").isNotNull())
    invalid_df = df.filter(col("email").isNull())

    stats = {
        "total": df.count(),
        "valid": valid_df.count(),
        "invalid": invalid_df.count(),
    }

    return valid_df, invalid_df, stats

# ════════════════════════════════════════════════════════════════════════════
# Spark SQL Functions Return Columns
# ════════════════════════════════════════════════════════════════════════════

from pyspark.sql.functions import (
    sum, avg, max, min, count,  # Aggregations return Column
    concat, substring, length,   # String functions return Column
    year, month, dayofmonth,     # Date functions return Column
)

def add_computed_columns(df: DataFrame) -> DataFrame:
    """Functions return Column objects for lazy evaluation."""
    return df.select(
        col("id"),
        col("name"),
        length(col("name")).alias("name_length"),        # Returns Column
        year(col("created_at")).alias("year"),           # Returns Column
        concat(col("first"), lit(" "), col("last"))      # Returns Column
            .alias("full_name"),
    )
```

---

### Pattern 2: Multiple Return Values (Critical for Go!)

#### Go - The (value, error) Pattern

```go
// ═══════════════════════════════════════════════════════════════════════════
// GO - Multiple return values are IDIOMATIC and CRITICAL
// ═══════════════════════════════════════════════════════════════════════════
package main

import (
    "encoding/json"
    "errors"
    "fmt"
    "io"
    "net/http"
    "os"
)

// ════════════════════════════════════════════════════════════════════════════
// Pattern 1: The (value, error) Pattern - Most Common!
// ════════════════════════════════════════════════════════════════════════════

// Standard library example
func readFile(filename string) ([]byte, error) {
    data, err := os.ReadFile(filename)
    if err != nil {
        return nil, fmt.Errorf("reading %s: %w", filename, err)
    }
    return data, nil
}

// Your own functions should follow this pattern
func parseJSON(data []byte) (*Config, error) {
    var config Config
    if err := json.Unmarshal(data, &config); err != nil {
        return nil, fmt.Errorf("parsing config: %w", err)
    }
    return &config, nil
}

type Config struct {
    Host string `json:"host"`
    Port int    `json:"port"`
}

// Chaining error-returning functions
func loadConfig(filename string) (*Config, error) {
    data, err := readFile(filename)
    if err != nil {
        return nil, err  // Propagate error
    }

    config, err := parseJSON(data)
    if err != nil {
        return nil, err  // Propagate error
    }

    return config, nil
}

// ════════════════════════════════════════════════════════════════════════════
// Pattern 2: The (value, ok) Pattern - Like Map Lookup
// ════════════════════════════════════════════════════════════════════════════

func getUserByID(id int) (*User, bool) {
    users := map[int]*User{
        1: {ID: 1, Name: "Alice"},
        2: {ID: 2, Name: "Bob"},
    }
    user, ok := users[id]
    return user, ok
}

type User struct {
    ID   int
    Name string
}

func main() {
    // Correct usage
    if user, ok := getUserByID(1); ok {
        fmt.Printf("Found: %s\n", user.Name)
    } else {
        fmt.Println("User not found")
    }
}

// ════════════════════════════════════════════════════════════════════════════
// Pattern 3: Multiple Values (coordinates, dimensions, etc.)
// ════════════════════════════════════════════════════════════════════════════

func getBoundingBox(points []Point) (minX, minY, maxX, maxY float64) {
    if len(points) == 0 {
        return 0, 0, 0, 0
    }

    minX, minY = points[0].X, points[0].Y
    maxX, maxY = points[0].X, points[0].Y

    for _, p := range points[1:] {
        if p.X < minX { minX = p.X }
        if p.Y < minY { minY = p.Y }
        if p.X > maxX { maxX = p.X }
        if p.Y > maxY { maxY = p.Y }
    }

    return  // Named returns allow "naked return"
}

type Point struct {
    X, Y float64
}

// ════════════════════════════════════════════════════════════════════════════
// Pattern 4: HTTP Handlers - Writing vs Returning
// ════════════════════════════════════════════════════════════════════════════

// HTTP handlers don't return - they write to ResponseWriter
func handleUser(w http.ResponseWriter, r *http.Request) {
    user, err := getUserFromDB(r.URL.Query().Get("id"))
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return  // Early return!
    }

    json.NewEncoder(w).Encode(user)
}

func getUserFromDB(id string) (*User, error) {
    if id == "" {
        return nil, errors.New("id required")
    }
    return &User{ID: 1, Name: "Test"}, nil
}

// ════════════════════════════════════════════════════════════════════════════
// Pattern 5: Defer with Named Returns (Cleanup + Error Modification)
// ════════════════════════════════════════════════════════════════════════════

func processFile(filename string) (result string, err error) {
    f, err := os.Open(filename)
    if err != nil {
        return "", fmt.Errorf("opening file: %w", err)
    }
    defer func() {
        // Modify error if close fails and we don't have another error
        if cerr := f.Close(); cerr != nil && err == nil {
            err = fmt.Errorf("closing file: %w", cerr)
        }
    }()

    data, err := io.ReadAll(f)
    if err != nil {
        return "", fmt.Errorf("reading file: %w", err)
    }

    return string(data), nil
}

// ════════════════════════════════════════════════════════════════════════════
// Anti-Patterns to Avoid
// ════════════════════════════════════════════════════════════════════════════

// ❌ BAD: Ignoring errors with _
func badExample() {
    data, _ := readFile("config.json")  // Error ignored!
    fmt.Println(string(data))           // Will panic if file doesn't exist
}

// ❌ BAD: Checking err without returning
func anotherBadExample() error {
    _, err := readFile("config.json")
    if err != nil {
        fmt.Println("Error:", err)
        // ❌ Forgot to return! Code continues...
    }
    // This code runs even on error!
    return nil
}

// ✅ GOOD: Always handle or propagate errors
func goodExample() error {
    data, err := readFile("config.json")
    if err != nil {
        return fmt.Errorf("loading config: %w", err)
    }

    config, err := parseJSON(data)
    if err != nil {
        return fmt.Errorf("parsing config: %w", err)
    }

    fmt.Printf("Loaded config: %+v\n", config)
    return nil
}
```

#### Python - Tuple Unpacking

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - Multiple returns via tuple unpacking
# ═══════════════════════════════════════════════════════════════════════════
from typing import Tuple, Optional, NamedTuple
from dataclasses import dataclass

# Basic multiple return (implicit tuple)
def get_min_max(numbers: list[int]) -> tuple[int, int]:
    return min(numbers), max(numbers)

# Usage
minimum, maximum = get_min_max([3, 1, 4, 1, 5])
print(f"Min: {minimum}, Max: {maximum}")  # Min: 1, Max: 5

# Returning tuple explicitly
def divide_with_remainder(a: int, b: int) -> tuple[int, int]:
    quotient = a // b
    remainder = a % b
    return (quotient, remainder)

q, r = divide_with_remainder(17, 5)
print(f"17 = 5 * {q} + {r}")  # 17 = 5 * 3 + 2

# Built-in divmod does this
q, r = divmod(17, 5)  # Same result

# ════════════════════════════════════════════════════════════════════════════
# Named Tuple for More Clarity
# ════════════════════════════════════════════════════════════════════════════

class DivisionResult(NamedTuple):
    quotient: int
    remainder: int
    is_exact: bool

def divide_detailed(a: int, b: int) -> DivisionResult:
    q, r = divmod(a, b)
    return DivisionResult(
        quotient=q,
        remainder=r,
        is_exact=(r == 0)
    )

result = divide_detailed(17, 5)
print(f"Quotient: {result.quotient}")  # Access by name
print(f"Is exact: {result.is_exact}")

# Can still unpack
q, r, exact = divide_detailed(20, 5)

# ════════════════════════════════════════════════════════════════════════════
# Dataclass for Complex Returns
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    processed_value: Optional[str] = None

def validate_email(email: str) -> ValidationResult:
    errors = []
    warnings = []

    if not email:
        return ValidationResult(False, ["Email is required"], [])

    if "@" not in email:
        errors.append("Missing @ symbol")

    if "." not in email.split("@")[-1]:
        errors.append("Missing domain extension")

    if email != email.lower():
        warnings.append("Email was converted to lowercase")

    if errors:
        return ValidationResult(False, errors, warnings)

    return ValidationResult(True, [], warnings, email.lower())

# Usage
result = validate_email("Test@Example")
if result.is_valid:
    print(f"Valid email: {result.processed_value}")
else:
    print(f"Invalid: {result.errors}")

# ════════════════════════════════════════════════════════════════════════════
# Go-style (value, error) Pattern in Python
# ════════════════════════════════════════════════════════════════════════════

def safe_divide(a: float, b: float) -> tuple[float, Optional[str]]:
    """Go-style return: (value, error)."""
    if b == 0:
        return 0.0, "division by zero"
    return a / b, None

# Usage
result, err = safe_divide(10, 0)
if err is not None:
    print(f"Error: {err}")
else:
    print(f"Result: {result}")

# But Pythonic way is usually exceptions:
def pythonic_divide(a: float, b: float) -> float:
    """Pythonic: raise exception for errors."""
    if b == 0:
        raise ValueError("division by zero")
    return a / b

try:
    result = pythonic_divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")

# ════════════════════════════════════════════════════════════════════════════
# Ignoring Some Return Values
# ════════════════════════════════════════════════════════════════════════════

# Use _ for values you don't need
_, maximum = get_min_max([1, 2, 3])  # Only need max

# Multiple ignores
first, *_, last = [1, 2, 3, 4, 5]  # first=1, last=5

# Extended unpacking
head, *middle, tail = [1, 2, 3, 4, 5]  # head=1, middle=[2,3,4], tail=5
```

---

### Pattern 3: Optional/Nullable Return Types

#### Java - Optional<T>

```java
// ═══════════════════════════════════════════════════════════════════════════
// JAVA - Optional<T> for nullable returns (Java 8+)
// ═══════════════════════════════════════════════════════════════════════════
import java.util.Optional;
import java.util.List;
import java.util.Map;

public class OptionalExamples {

    // ════════════════════════════════════════════════════════════════════════
    // Creating Optional values
    // ════════════════════════════════════════════════════════════════════════

    // Return Optional instead of null
    public Optional<User> findUserById(int id) {
        User user = database.get(id);
        return Optional.ofNullable(user);  // Handles null safely
    }

    // When you know value exists
    public Optional<String> getRequiredConfig(String key) {
        String value = config.get(key);
        if (value == null) {
            throw new IllegalStateException("Missing required config: " + key);
        }
        return Optional.of(value);  // Throws if null!
    }

    // Explicit empty
    public Optional<User> getAnonymousUser() {
        return Optional.empty();
    }

    // ════════════════════════════════════════════════════════════════════════
    // Consuming Optional - CORRECT patterns
    // ════════════════════════════════════════════════════════════════════════

    public void correctPatterns() {
        Optional<User> userOpt = findUserById(1);

        // Pattern 1: ifPresent - execute if value exists
        userOpt.ifPresent(user -> {
            System.out.println("Found: " + user.getName());
        });

        // Pattern 2: ifPresentOrElse (Java 9+)
        userOpt.ifPresentOrElse(
            user -> System.out.println("Found: " + user.getName()),
            () -> System.out.println("User not found")
        );

        // Pattern 3: map - transform value if present
        Optional<String> nameOpt = userOpt.map(User::getName);

        // Pattern 4: flatMap - for nested Optionals
        Optional<String> cityOpt = userOpt
            .flatMap(User::getAddress)      // User -> Optional<Address>
            .flatMap(Address::getCity);     // Address -> Optional<String>

        // Pattern 5: orElse - default value
        String name = userOpt
            .map(User::getName)
            .orElse("Anonymous");

        // Pattern 6: orElseGet - lazy default (computed only if needed)
        String nameOrComputed = userOpt
            .map(User::getName)
            .orElseGet(() -> computeDefaultName());

        // Pattern 7: orElseThrow - throw if empty
        User user = userOpt.orElseThrow(() ->
            new UserNotFoundException("User not found"));

        // Pattern 8: filter - conditional extraction
        Optional<User> activeUser = userOpt
            .filter(User::isActive);

        // Pattern 9: or (Java 9+) - provide alternative Optional
        Optional<User> result = userOpt
            .or(() -> findUserByEmail("default@example.com"));
    }

    // ════════════════════════════════════════════════════════════════════════
    // ANTI-PATTERNS - Don't do these!
    // ════════════════════════════════════════════════════════════════════════

    public void antiPatterns() {
        Optional<User> userOpt = findUserById(1);

        // ❌ BAD: Using isPresent() + get()
        if (userOpt.isPresent()) {
            User user = userOpt.get();  // Defeats the purpose of Optional!
        }

        // ❌ BAD: Passing Optional as parameter
        // public void process(Optional<User> user) { }  // Don't do this!

        // ❌ BAD: Storing Optional in fields
        // private Optional<User> currentUser;  // Don't do this!

        // ❌ BAD: Using Optional for collections
        // Optional<List<User>> users;  // Use empty list instead!

        // ❌ BAD: Using get() without checking
        // User user = userOpt.get();  // Throws NoSuchElementException if empty!
    }

    // ════════════════════════════════════════════════════════════════════════
    // orElse vs orElseGet - CRITICAL INTERVIEW QUESTION!
    // ════════════════════════════════════════════════════════════════════════

    public void orElseVsOrElseGet() {
        Optional<String> opt = Optional.of("value");

        // orElse: default is ALWAYS evaluated!
        String result1 = opt.orElse(expensiveOperation());
        // expensiveOperation() is called even though opt has a value!

        // orElseGet: default is evaluated ONLY if needed (lazy)
        String result2 = opt.orElseGet(() -> expensiveOperation());
        // Lambda is not called because opt has a value!
    }

    private String expensiveOperation() {
        System.out.println("Expensive operation called!");
        return "default";
    }

    // ════════════════════════════════════════════════════════════════════════
    // Optional with Streams
    // ════════════════════════════════════════════════════════════════════════

    public Optional<User> findFirstActiveUser(List<User> users) {
        return users.stream()
            .filter(User::isActive)
            .findFirst();  // Returns Optional<User>
    }

    public List<String> getAllActiveUserNames(List<User> users) {
        return users.stream()
            .filter(User::isActive)
            .map(User::getName)
            .toList();
    }

    // Java 9+: Optional.stream() for flatMap operations
    public List<String> getAllEmails(List<User> users) {
        return users.stream()
            .map(User::getEmail)        // Stream<Optional<String>>
            .flatMap(Optional::stream)  // Stream<String> (filters empty)
            .toList();
    }

    // Placeholder implementations
    private Map<Integer, User> database = Map.of();
    private Map<String, String> config = Map.of();
    private String computeDefaultName() { return "Default"; }

    static class User {
        public String getName() { return ""; }
        public boolean isActive() { return true; }
        public Optional<Address> getAddress() { return Optional.empty(); }
        public Optional<String> getEmail() { return Optional.empty(); }
    }

    static class Address {
        public Optional<String> getCity() { return Optional.empty(); }
    }

    static class UserNotFoundException extends RuntimeException {
        public UserNotFoundException(String msg) { super(msg); }
    }
}
```

---

### Pattern 4: Early Return Pattern

```java
// ═══════════════════════════════════════════════════════════════════════════
// JAVA - Early Return Pattern
// ═══════════════════════════════════════════════════════════════════════════

public class EarlyReturnExamples {

    // ❌ BAD: Deep nesting
    public String processOrderBad(Order order) {
        if (order != null) {
            if (order.getItems() != null && !order.getItems().isEmpty()) {
                if (order.getCustomer() != null) {
                    if (order.getCustomer().isActive()) {
                        if (order.isPaid()) {
                            return "Order processed: " + order.getId();
                        } else {
                            return "Payment required";
                        }
                    } else {
                        return "Customer inactive";
                    }
                } else {
                    return "Customer required";
                }
            } else {
                return "Items required";
            }
        } else {
            return "Order is null";
        }
    }

    // ✅ GOOD: Early returns (guard clauses)
    public String processOrderGood(Order order) {
        if (order == null) return "Order is null";
        if (order.getItems() == null || order.getItems().isEmpty()) return "Items required";
        if (order.getCustomer() == null) return "Customer required";
        if (!order.getCustomer().isActive()) return "Customer inactive";
        if (!order.isPaid()) return "Payment required";

        return "Order processed: " + order.getId();
    }

    // ✅ BETTER: With validation method
    public String processOrderBetter(Order order) {
        String validationError = validateOrder(order);
        if (validationError != null) {
            return validationError;
        }

        return "Order processed: " + order.getId();
    }

    private String validateOrder(Order order) {
        if (order == null) return "Order is null";
        if (order.getItems() == null || order.getItems().isEmpty()) return "Items required";
        if (order.getCustomer() == null) return "Customer required";
        if (!order.getCustomer().isActive()) return "Customer inactive";
        if (!order.isPaid()) return "Payment required";
        return null;  // Valid
    }
}
```

```typescript
// ═══════════════════════════════════════════════════════════════════════════
// TYPESCRIPT - Early Return with Type Narrowing
// ═══════════════════════════════════════════════════════════════════════════

interface Order {
    id: string;
    items: Item[];
    customer: Customer | null;
    isPaid: boolean;
}

interface Item {
    name: string;
    price: number;
}

interface Customer {
    name: string;
    isActive: boolean;
}

// Early returns narrow types automatically!
function processOrder(order: Order | null): string {
    if (!order) return "Order is null";
    // TypeScript now knows: order is Order (not null)

    if (order.items.length === 0) return "Items required";
    // TypeScript knows: order.items has items

    if (!order.customer) return "Customer required";
    // TypeScript now knows: order.customer is Customer (not null)

    if (!order.customer.isActive) return "Customer inactive";
    // TypeScript knows: customer.isActive is true (by inference)

    if (!order.isPaid) return "Payment required";

    // All validations passed - happy path is clear
    return `Order processed: ${order.id}`;
}

// Type guard with early return
function assertNonNull<T>(value: T | null | undefined, message: string): asserts value is T {
    if (value === null || value === undefined) {
        throw new Error(message);
    }
}

function processOrderWithAssertions(order: Order | null): string {
    assertNonNull(order, "Order is null");
    // TypeScript now knows: order is Order

    assertNonNull(order.customer, "Customer required");
    // TypeScript now knows: order.customer is Customer

    return `Order ${order.id} for ${order.customer.name}`;
}
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - Early Return Pattern
# ═══════════════════════════════════════════════════════════════════════════
from typing import Optional
from dataclasses import dataclass

@dataclass
class Customer:
    name: str
    is_active: bool

@dataclass
class Order:
    id: str
    items: list[str]
    customer: Optional[Customer]
    is_paid: bool

# Early returns for validation
def process_order(order: Optional[Order]) -> str:
    if order is None:
        return "Order is null"

    if not order.items:
        return "Items required"

    if order.customer is None:
        return "Customer required"

    if not order.customer.is_active:
        return "Customer inactive"

    if not order.is_paid:
        return "Payment required"

    return f"Order processed: {order.id}"

# Alternative: Raise exceptions for validation
class ValidationError(Exception):
    pass

def validate_order(order: Optional[Order]) -> Order:
    """Validate and return order, or raise ValidationError."""
    if order is None:
        raise ValidationError("Order is null")
    if not order.items:
        raise ValidationError("Items required")
    if order.customer is None:
        raise ValidationError("Customer required")
    if not order.customer.is_active:
        raise ValidationError("Customer inactive")
    if not order.is_paid:
        raise ValidationError("Payment required")
    return order

def process_order_with_exception(order: Optional[Order]) -> str:
    try:
        validated = validate_order(order)
        return f"Order processed: {validated.id}"
    except ValidationError as e:
        return str(e)
```

```go
// ═══════════════════════════════════════════════════════════════════════════
// GO - Early Return is Idiomatic!
// ═══════════════════════════════════════════════════════════════════════════
package main

import (
    "errors"
    "fmt"
)

type Customer struct {
    Name     string
    IsActive bool
}

type Order struct {
    ID       string
    Items    []string
    Customer *Customer
    IsPaid   bool
}

// Go's if err != nil is essentially early return pattern
func processOrder(order *Order) (string, error) {
    if order == nil {
        return "", errors.New("order is nil")
    }

    if len(order.Items) == 0 {
        return "", errors.New("items required")
    }

    if order.Customer == nil {
        return "", errors.New("customer required")
    }

    if !order.Customer.IsActive {
        return "", errors.New("customer inactive")
    }

    if !order.IsPaid {
        return "", errors.New("payment required")
    }

    return fmt.Sprintf("Order processed: %s", order.ID), nil
}

// Combining with error wrapping
func processOrderChain(order *Order) (string, error) {
    if err := validateOrder(order); err != nil {
        return "", fmt.Errorf("validation failed: %w", err)
    }

    if err := chargePayment(order); err != nil {
        return "", fmt.Errorf("payment failed: %w", err)
    }

    if err := updateInventory(order); err != nil {
        return "", fmt.Errorf("inventory update failed: %w", err)
    }

    return fmt.Sprintf("Order %s completed", order.ID), nil
}

func validateOrder(order *Order) error {
    if order == nil {
        return errors.New("order is nil")
    }
    if len(order.Items) == 0 {
        return errors.New("no items")
    }
    return nil
}

func chargePayment(order *Order) error { return nil }
func updateInventory(order *Order) error { return nil }
```

---

### Pattern 5: TypeScript `never` Type

```typescript
// ═══════════════════════════════════════════════════════════════════════════
// TYPESCRIPT - The 'never' Type (Functions That Never Return)
// ═══════════════════════════════════════════════════════════════════════════

// never: Represents values that never occur

// Case 1: Function that always throws
function throwError(message: string): never {
    throw new Error(message);
    // Unreachable code after throw
}

// Case 2: Infinite loop
function infiniteLoop(): never {
    while (true) {
        // Process events forever
    }
}

// Case 3: Exhaustive checking (most practical use!)
type Shape = "circle" | "square" | "triangle";

function getArea(shape: Shape): number {
    switch (shape) {
        case "circle":
            return Math.PI;
        case "square":
            return 1;
        case "triangle":
            return 0.5;
        default:
            // If someone adds a new shape to the union but forgets
            // to add a case here, TypeScript will error!
            const _exhaustive: never = shape;
            throw new Error(`Unknown shape: ${shape}`);
    }
}

// Real-world example: Action handlers
type Action =
    | { type: "LOGIN"; username: string }
    | { type: "LOGOUT" }
    | { type: "UPDATE_PROFILE"; name: string };

function handleAction(action: Action): string {
    switch (action.type) {
        case "LOGIN":
            return `Logging in ${action.username}`;
        case "LOGOUT":
            return "Logging out";
        case "UPDATE_PROFILE":
            return `Updating profile to ${action.name}`;
        default:
            // Ensures all action types are handled
            const _never: never = action;
            throw new Error(`Unhandled action: ${JSON.stringify(action)}`);
    }
}

// never vs void
function returnsVoid(): void {
    console.log("Does something");
    // Returns undefined implicitly - function completes normally
}

function returnsNever(): never {
    throw new Error("Never returns normally");
    // Function NEVER completes - always throws or loops
}

// Type narrowing with never
function processValue(value: string | number): string {
    if (typeof value === "string") {
        return value.toUpperCase();
    }
    if (typeof value === "number") {
        return value.toString();
    }
    // At this point, value is narrowed to 'never'
    // because all cases are handled
    const _exhaustive: never = value;
    return _exhaustive;
}

// Utility type: Assert never (compile-time exhaustive check)
function assertNever(value: never): never {
    throw new Error(`Unexpected value: ${value}`);
}

// Usage in exhaustive switch
function describePet(pet: "dog" | "cat" | "bird"): string {
    switch (pet) {
        case "dog":
            return "Woof!";
        case "cat":
            return "Meow!";
        case "bird":
            return "Tweet!";
        default:
            return assertNever(pet);  // Compile error if case missing
    }
}
```

---

## Section 3: Design Philosophy Links (공식 문서)

### Official Documentation

| Language | Resource | URL |
|----------|----------|-----|
| **Java** | Methods | https://docs.oracle.com/javase/tutorial/java/javaOO/methods.html |
| **Java** | Optional | https://docs.oracle.com/javase/8/docs/api/java/util/Optional.html |
| **Python** | Defining Functions | https://docs.python.org/3/tutorial/controlflow.html#defining-functions |
| **Python** | Type Hints | https://docs.python.org/3/library/typing.html |
| **TypeScript** | Return Types | https://www.typescriptlang.org/docs/handbook/2/functions.html#return-type-annotations |
| **TypeScript** | never Type | https://www.typescriptlang.org/docs/handbook/2/narrowing.html#the-never-type |
| **Go** | Multiple Returns | https://go.dev/doc/effective_go#multiple-returns |
| **Go** | Error Handling | https://go.dev/blog/error-handling-and-go |
| **C++** | Return Type Deduction | https://en.cppreference.com/w/cpp/language/auto |
| **C++** | std::optional | https://en.cppreference.com/w/cpp/utility/optional |
| **Spark** | UDF Guide | https://spark.apache.org/docs/latest/sql-ref-functions-udf-scalar.html |

### Design Philosophy Articles

| Topic | Resource |
|-------|----------|
| **Go Error Philosophy** | [Errors are values](https://go.dev/blog/errors-are-values) - Rob Pike |
| **Java Optional Best Practices** | [Using Optional](https://www.oracle.com/technical-resources/articles/java/java8-optional.html) |
| **Martin Fowler - Guard Clauses** | [Replace Nested Conditional with Guard Clauses](https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html) |
| **TypeScript never type** | [TypeScript Deep Dive](https://basarat.gitbook.io/typescript/type-system/never) |

---

## Section 4: Palantir Context Hint (팔란티어 맥락)

### TypeScript OSDK: Handling Async Return Types

```typescript
// ═══════════════════════════════════════════════════════════════════════════
// Palantir OSDK - Promise<T> Return Types are Everywhere
// ═══════════════════════════════════════════════════════════════════════════

import { OntologyClient } from "@osdk/client";

interface Employee {
    id: string;
    name: string;
    department: string;
    managerId?: string;
}

// OSDK methods typically return Promise<T>
async function getEmployee(client: OntologyClient, id: string): Promise<Employee | null> {
    try {
        const employee = await client.objects.Employee.get(id);
        return employee ?? null;
    } catch {
        return null;
    }
}

// Handling linked objects (always async)
async function getManagerChain(
    client: OntologyClient,
    employeeId: string
): Promise<Employee[]> {
    const chain: Employee[] = [];
    let currentId: string | undefined = employeeId;

    while (currentId) {
        const employee = await getEmployee(client, currentId);
        if (!employee) break;

        chain.push(employee);
        currentId = employee.managerId;
    }

    return chain;
}

// Parallel fetching with Promise.all
async function getTeamMembers(
    client: OntologyClient,
    teamIds: string[]
): Promise<Employee[]> {
    const promises = teamIds.map(id => getEmployee(client, id));
    const results = await Promise.all(promises);
    return results.filter((e): e is Employee => e !== null);
}

// Error handling pattern
interface Result<T> {
    success: true;
    data: T;
} | {
    success: false;
    error: string;
}

async function safeGetEmployee(
    client: OntologyClient,
    id: string
): Promise<Result<Employee>> {
    try {
        const employee = await client.objects.Employee.get(id);
        if (!employee) {
            return { success: false, error: "Employee not found" };
        }
        return { success: true, data: employee };
    } catch (e) {
        return { success: false, error: String(e) };
    }
}
```

### Go Error Handling Pattern (Backend Services)

```go
// ═══════════════════════════════════════════════════════════════════════════
// Go Backend Service - The (value, error) Pattern
// ═══════════════════════════════════════════════════════════════════════════

// Every function that can fail returns (result, error)
func GetUserFromDatabase(id string) (*User, error) {
    user, err := db.Query("SELECT * FROM users WHERE id = ?", id)
    if err != nil {
        return nil, fmt.Errorf("querying user %s: %w", id, err)
    }
    return user, nil
}

// Chain multiple fallible operations
func ProcessUserRequest(userID string) (*Response, error) {
    user, err := GetUserFromDatabase(userID)
    if err != nil {
        return nil, fmt.Errorf("getting user: %w", err)
    }

    permissions, err := GetUserPermissions(user)
    if err != nil {
        return nil, fmt.Errorf("getting permissions: %w", err)
    }

    result, err := ExecuteAction(user, permissions)
    if err != nil {
        return nil, fmt.Errorf("executing action: %w", err)
    }

    return result, nil
}
```

### Spark Transformation Return Types

```python
# ═══════════════════════════════════════════════════════════════════════════
# Spark - Lazy Evaluation and Return Types
# ═══════════════════════════════════════════════════════════════════════════

# CRITICAL: Transformations return NEW DataFrames (lazy)
# Actions return concrete values (trigger computation)

def build_pipeline(input_df: DataFrame) -> DataFrame:
    """Returns DataFrame - lazy, no computation yet."""
    return (
        input_df
        .filter(col("status") == "active")
        .withColumn("score", col("value") * 2)
        .select("id", "name", "score")
    )  # Nothing computed yet!

def get_results(df: DataFrame) -> dict:
    """Actions trigger computation, return concrete values."""
    return {
        "count": df.count(),           # int
        "first_row": df.first(),       # Row
        "top_10": df.take(10),         # List[Row]
        "all_data": df.collect(),      # List[Row] - DANGEROUS for large data!
    }
```

### Interview Questions

#### Question 1: How does Go handle multiple return values?

**Answer:**
Go natively supports multiple return values as a language feature:

```go
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

result, err := divide(10, 2)
if err != nil {
    // Handle error
}
```

Key points:
1. Function signature declares multiple return types in parentheses
2. Caller uses multiple assignment with `:=` or `var`
3. The `(value, error)` pattern is idiomatic for fallible operations
4. Use `_` to ignore unwanted return values
5. Named returns allow "naked return" for cleaner code

---

#### Question 2: What is TypeScript's `never` type?

**Answer:**
`never` represents values that never occur. It's used for:

1. **Functions that throw**: Always throw, never return normally
2. **Infinite loops**: Never complete execution
3. **Exhaustive checks**: Ensure all union cases are handled

```typescript
// Throws - never returns
function fail(message: string): never {
    throw new Error(message);
}

// Exhaustive checking
type Status = "pending" | "active" | "completed";

function handleStatus(status: Status): string {
    switch (status) {
        case "pending": return "Waiting";
        case "active": return "In progress";
        case "completed": return "Done";
        default:
            // If new status added, TypeScript errors here
            const _exhaustive: never = status;
            throw new Error(`Unhandled: ${status}`);
    }
}
```

---

#### Question 3: Why use `Optional` instead of `null` in Java?

**Answer:**
`Optional<T>` provides several benefits over returning `null`:

1. **Explicit intent**: Method signature shows value might be absent
2. **Compiler assistance**: Forces caller to handle absence
3. **Functional operations**: `map`, `filter`, `flatMap` chains
4. **No NPE**: Methods like `orElse` provide safe defaults

```java
// BAD: null return
public User findUser(int id) {
    return database.get(id);  // Might be null - caller must remember to check
}

// GOOD: Optional return
public Optional<User> findUser(int id) {
    return Optional.ofNullable(database.get(id));
}

// Caller is forced to handle:
findUser(1)
    .map(User::getName)
    .orElse("Unknown");
```

Key rule: Use Optional for return types, not for fields or parameters.

---

#### Question 4: Explain early return pattern benefits

**Answer:**
Early return (guard clauses) improves code quality:

**Before (nested):**
```python
def process(data):
    if data is not None:
        if data.is_valid():
            if data.has_permission():
                return do_work(data)
    return None
```

**After (early return):**
```python
def process(data):
    if data is None: return None
    if not data.is_valid(): return None
    if not data.has_permission(): return None
    return do_work(data)
```

Benefits:
1. **Reduced nesting**: Easier to read and follow
2. **Clear preconditions**: Validations are explicit at top
3. **Happy path visible**: Main logic not buried in nesting
4. **Easier debugging**: Clear exit points
5. **Lower cognitive load**: Less mental stack tracking

---

## Section 5: Cross-References (관련 개념)

### Direct Dependencies

| Concept ID | Title | Relationship |
|------------|-------|--------------|
| **F40** | Function Declarations | Prerequisite - Function definition syntax |
| **F41** | Parameters & Arguments | Prerequisite - Input side of functions |
| **F32** | Exception Handling | Related - Error returns vs exceptions |
| **F20** | Static vs Dynamic Typing | Foundation - Type system affects return types |
| **F21** | Type Inference | Related - When return types are inferred |

### Broader Context

| Concept ID | Title | Relationship |
|------------|-------|--------------|
| **F24** | Generics & Polymorphism | Extension - Generic return types |
| **F34** | Control Flow Expressions | Related - Early return pattern |
| **F30** | Conditionals | Application - Guard clauses |
| **00b** | Functions and Scope | Foundation KB |
| **00d** | Async Basics | Extension - Promise return types |

### Pattern Relationships

```
F40 Declarations ──→ F41 Parameters ──→ F42 Return Values
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                    Function Definition
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
    F32 Errors      F21 Inference        F24 Generics
```

### Study Path Recommendations

1. **Before F42**: Ensure F40 (declarations) and F41 (parameters) are understood
2. **After F42**: Proceed to F32 (exception handling) for error patterns
3. **Interview Prep**: Focus on Go multiple returns and Java Optional
4. **OSDK Focus**: Deep dive into TypeScript async return types

---

## Summary: Key Takeaways

### The Big Picture

1. **Return values** are how functions communicate results to callers
2. **Multiple returns** are native in Go/Python, simulated in others
3. **Type inference** reduces boilerplate but explicit types aid clarity
4. **Optional types** replace null for safer nullable returns
5. **Early return** flattens code and improves readability

### Language-Specific Memory Aids

| Language | Remember This |
|----------|---------------|
| **Java** | `Optional<T>` for nullable, `orElseGet` is lazy |
| **Python** | Tuple unpacking for multiple returns |
| **TypeScript** | `never` for exhaustive checks, `Promise<T>` for async |
| **Go** | `(value, error)` is idiomatic, ALWAYS check `err != nil` |
| **SQL** | `RETURNS TABLE` for multiple rows, scalar for single value |
| **C++** | `auto` for inference, `std::optional<T>` for nullable |
| **Spark** | Transformations return DataFrame (lazy), actions return values |

### Interview Checklist

- [ ] Can explain Go's (value, error) pattern with examples
- [ ] Understand TypeScript's `never` type and its use cases
- [ ] Know Java `Optional` best practices (orElse vs orElseGet)
- [ ] Can refactor nested conditionals to early returns
- [ ] Understand difference between void and returning undefined
- [ ] Can explain lazy vs eager evaluation in return contexts

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Category: Functions & Control Flow*
