# F33: Pattern Matching (패턴 매칭)

> **Concept**: Pattern matching is "super-powered switch" - instead of just comparing values, it simultaneously checks structure, extracts data, and binds variables in one expression.
>
> **Mental Model**: Think of pattern matching as a "shape detector" that asks "Does this data fit this shape? If yes, pull out these parts."

---

## 1. Universal Concept

### 1.1 What is Pattern Matching?

Pattern matching is a programming technique that combines:
1. **Conditional checking**: Does the data match this pattern?
2. **Destructuring**: Extract nested values from complex structures
3. **Variable binding**: Automatically create variables from matched parts

```
Traditional approach:
  if (obj.type === "circle") {
    const radius = obj.radius;
    // use radius
  }

Pattern matching approach:
  match obj {
    Circle { radius } => // radius is already bound!
  }
```

### 1.2 Why Pattern Matching Improves Code Quality

| Benefit | Explanation |
|---------|-------------|
| **Readability** | Structure of data directly visible in code |
| **Safety** | Compiler can check exhaustiveness |
| **Conciseness** | Eliminates boilerplate extraction code |
| **Maintainability** | Adding new variants forces handling all cases |

### 1.3 Core Pattern Types

```
Literal Pattern     : matches exact value (42, "hello")
Variable Pattern    : binds any value to name (x, _)
Wildcard Pattern    : matches anything, discards (_)
Type Pattern        : matches by type (String s)
Constructor Pattern : matches structure (Point(x, y))
Guard Pattern       : pattern + condition (x if x > 0)
Or Pattern          : multiple alternatives (a | b)
```

---

## 2. Semantic Comparison Matrix

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **Match/Switch** | `switch` (21+) | `match` (3.10+) | `switch` | `switch` | `CASE WHEN` | `switch` | SQL CASE |
| **Destructuring** | Record patterns | Full support | Full support | None native | N/A | Structured bindings | N/A |
| **Guard Clauses** | `when` keyword | `if` guard | Manual | Manual | `WHEN ... AND` | N/A | `WHEN ... AND` |
| **Exhaustiveness** | Sealed classes | No | `never` type | No | No | No | No |
| **Wildcard** | `default`, `_` | `_` (wildcard) | `default` | `default` | `ELSE` | `default` | `ELSE` |
| **Type Patterns** | `instanceof` pattern | Type guards | Type guards | Type switch | N/A | `std::variant` | N/A |
| **Pitfall** | Missing sealed | No exhaustive check | Type narrowing bugs | Fallthrough | NULL handling | Complex syntax | NULL propagation |

### 2.2 Detailed Code Examples

---

#### 2.2.1 Basic Pattern Matching

**Java 21+ (Pattern Matching Switch)**
```java
// Traditional switch limitation
Object obj = "hello";

// Pattern matching switch (Java 21)
String result = switch (obj) {
    case Integer i -> "Integer: " + i;
    case String s -> "String of length: " + s.length();
    case Double d -> "Double: " + d;
    case null -> "null value";
    default -> "Unknown type";
};

// Record pattern matching
record Point(int x, int y) {}
record Circle(Point center, int radius) {}

Object shape = new Circle(new Point(0, 0), 5);

String desc = switch (shape) {
    case Circle(Point(int x, int y), int r) ->
        "Circle at (" + x + "," + y + ") with radius " + r;
    case Point(int x, int y) ->
        "Point at (" + x + "," + y + ")";
    default -> "Unknown shape";
};
// Output: "Circle at (0,0) with radius 5"
```

**Python 3.10+ (Structural Pattern Matching)**
```python
# Python match statement - structural pattern matching
def describe_value(value):
    match value:
        case int(x) if x > 0:
            return f"Positive integer: {x}"
        case int(x):
            return f"Non-positive integer: {x}"
        case str(s):
            return f"String of length {len(s)}"
        case [first, *rest]:
            return f"List starting with {first}, {len(rest)} more elements"
        case {"type": "circle", "radius": r}:
            return f"Circle with radius {r}"
        case _:
            return "Unknown"

# Examples
print(describe_value(42))                    # "Positive integer: 42"
print(describe_value(-5))                    # "Non-positive integer: -5"
print(describe_value("hello"))               # "String of length 5"
print(describe_value([1, 2, 3, 4]))          # "List starting with 1, 3 more elements"
print(describe_value({"type": "circle", "radius": 10}))  # "Circle with radius 10"
```

**TypeScript (Discriminated Unions - CRITICAL for Palantir!)**
```typescript
// Discriminated union pattern - TypeScript's pattern matching approach
type Shape =
    | { kind: 'circle'; radius: number }
    | { kind: 'rectangle'; width: number; height: number }
    | { kind: 'triangle'; base: number; height: number };

function getArea(shape: Shape): number {
    switch (shape.kind) {
        case 'circle':
            // TypeScript KNOWS shape.radius exists here!
            return Math.PI * shape.radius ** 2;
        case 'rectangle':
            // TypeScript KNOWS shape.width and shape.height exist here!
            return shape.width * shape.height;
        case 'triangle':
            return (shape.base * shape.height) / 2;
        // Exhaustiveness check with never
        default:
            const _exhaustive: never = shape;
            return _exhaustive;
    }
}

// Type narrowing in action
function processShape(shape: Shape): void {
    if (shape.kind === 'circle') {
        console.log(shape.radius);  // ✓ TypeScript knows this is valid
        // console.log(shape.width); // ✗ Compile error!
    }
}
```

**Go (Type Switch - Limited Pattern Matching)**
```go
package main

import "fmt"

// Go has no true pattern matching, but type switch provides similar functionality
func describe(i interface{}) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("Integer: %d", v)
    case string:
        return fmt.Sprintf("String of length %d", len(v))
    case bool:
        if v {
            return "Boolean: true"
        }
        return "Boolean: false"
    case []int:
        if len(v) == 0 {
            return "Empty int slice"
        }
        return fmt.Sprintf("Int slice starting with %d", v[0])
    default:
        return "Unknown type"
    }
}

// Simulating destructuring with multiple return values
type Point struct {
    X, Y int
}

func (p Point) Coords() (int, int) {
    return p.X, p.Y
}

func main() {
    p := Point{3, 4}
    x, y := p.Coords()  // Manual destructuring
    fmt.Printf("Point at (%d, %d)\n", x, y)
}
```

**SQL (CASE WHEN - Limited Pattern Matching)**
```sql
-- SQL's CASE WHEN is a limited form of pattern matching
SELECT
    product_name,
    price,
    CASE
        WHEN price > 100 THEN 'Premium'
        WHEN price > 50 THEN 'Standard'
        WHEN price > 0 THEN 'Budget'
        WHEN price IS NULL THEN 'No Price'
        ELSE 'Free'
    END AS price_category,
    -- Searched CASE for complex conditions
    CASE category
        WHEN 'Electronics' THEN price * 0.9
        WHEN 'Clothing' THEN price * 0.8
        WHEN 'Books' THEN price * 0.95
        ELSE price
    END AS discounted_price
FROM products;

-- Pattern-like matching with LIKE
SELECT *
FROM customers
WHERE
    CASE
        WHEN email LIKE '%@gmail.com' THEN 'Gmail'
        WHEN email LIKE '%@outlook.com' THEN 'Outlook'
        WHEN email LIKE '%@%.edu' THEN 'Education'
        ELSE 'Other'
    END = 'Gmail';
```

**C++ (Structured Bindings + std::variant)**
```cpp
#include <iostream>
#include <variant>
#include <string>
#include <tuple>
#include <map>

// C++17 Structured Bindings - form of destructuring
void structured_bindings_demo() {
    // Array destructuring
    int arr[] = {1, 2, 3};
    auto [a, b, c] = arr;

    // Tuple destructuring
    std::tuple<int, std::string, double> person{25, "Alice", 5.5};
    auto [age, name, height] = person;

    // Map iteration with destructuring
    std::map<std::string, int> scores{{"Alice", 100}, {"Bob", 85}};
    for (const auto& [name, score] : scores) {
        std::cout << name << ": " << score << "\n";
    }

    // Struct destructuring
    struct Point { int x, y; };
    Point p{3, 4};
    auto [x, y] = p;
}

// std::variant - C++ discriminated union (C++17)
using Shape = std::variant<
    struct Circle { double radius; },
    struct Rectangle { double width, height; }
>;

// Actually, struct inside variant doesn't work well
// Better approach:
struct Circle { double radius; };
struct Rectangle { double width; double height; };
using ShapeVariant = std::variant<Circle, Rectangle>;

double getArea(const ShapeVariant& shape) {
    return std::visit([](auto&& arg) -> double {
        using T = std::decay_t<decltype(arg)>;
        if constexpr (std::is_same_v<T, Circle>) {
            return 3.14159 * arg.radius * arg.radius;
        } else if constexpr (std::is_same_v<T, Rectangle>) {
            return arg.width * arg.height;
        }
    }, shape);
}

// Pattern matching proposal (C++23/26 - not yet standard)
// double getArea(const ShapeVariant& shape) {
//     inspect (shape) {
//         <Circle c> => 3.14159 * c.radius * c.radius;
//         <Rectangle r> => r.width * r.height;
//     }
// }
```

**Spark SQL (Pattern Matching in Data)**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, regexp_extract, lit

spark = SparkSession.builder.appName("PatternMatching").getOrCreate()

# Sample DataFrame
data = [
    ("Alice", 30, "Engineering"),
    ("Bob", 25, "Marketing"),
    ("Charlie", None, "Engineering"),
    ("Diana", 35, "Sales")
]
df = spark.createDataFrame(data, ["name", "age", "dept"])

# CASE WHEN - SQL pattern matching
result = df.withColumn(
    "age_group",
    when(col("age").isNull(), "Unknown")
    .when(col("age") < 30, "Junior")
    .when(col("age") < 35, "Mid")
    .otherwise("Senior")
)

# Using SQL expression
df.createOrReplaceTempView("employees")
spark.sql("""
    SELECT
        name,
        CASE
            WHEN age IS NULL THEN 'Unknown'
            WHEN age < 30 THEN 'Junior'
            WHEN age < 35 THEN 'Mid'
            ELSE 'Senior'
        END AS age_group,
        CASE dept
            WHEN 'Engineering' THEN 1.2
            WHEN 'Sales' THEN 1.1
            ELSE 1.0
        END AS bonus_multiplier
    FROM employees
""").show()

# Regex pattern matching
logs = spark.createDataFrame([
    ("ERROR: Connection failed",),
    ("INFO: User logged in",),
    ("WARNING: Memory low",),
], ["log_message"])

logs.withColumn(
    "log_level",
    when(col("log_message").startswith("ERROR"), "ERROR")
    .when(col("log_message").startswith("WARNING"), "WARNING")
    .when(col("log_message").startswith("INFO"), "INFO")
    .otherwise("UNKNOWN")
).show()
```

---

#### 2.2.2 Destructuring in Function Parameters

**Java (Record Patterns in instanceof)**
```java
// Java doesn't support destructuring in method parameters directly
// But can use records and pattern matching in body

record User(String name, int age, Address address) {}
record Address(String city, String country) {}

// Traditional approach
void processUser(User user) {
    String name = user.name();
    int age = user.age();
    String city = user.address().city();
    // use extracted values
}

// With pattern matching in local scope (Java 21)
void processUserModern(Object obj) {
    if (obj instanceof User(String name, int age, Address(String city, _))) {
        System.out.println(name + " from " + city);
    }
}

// Lambda with var (closest to destructuring)
List<User> users = List.of(new User("Alice", 30, new Address("Seoul", "Korea")));
users.forEach(user -> {
    var name = user.name();  // Not true destructuring, but readable
    System.out.println(name);
});
```

**Python (Full Destructuring Support)**
```python
from dataclasses import dataclass
from typing import Tuple, List, Dict

@dataclass
class Point:
    x: int
    y: int

@dataclass
class User:
    name: str
    age: int

# Function parameter destructuring - tuple
def process_point(point: Tuple[int, int]) -> int:
    x, y = point  # Unpack in body
    return x + y

# More Pythonic - unpack in signature (only for known-length sequences)
def add_coordinates(*args):
    if len(args) == 2:
        x, y = args
        return x + y
    return sum(args)

# Dict destructuring in function
def process_config(**kwargs):
    host = kwargs.get('host', 'localhost')
    port = kwargs.get('port', 8080)
    return f"{host}:{port}"

# With match statement (Python 3.10+)
def handle_command(command: dict):
    match command:
        case {"action": "move", "x": x, "y": y}:
            return f"Moving to ({x}, {y})"
        case {"action": "resize", "width": w, "height": h}:
            return f"Resizing to {w}x{h}"
        case {"action": action, **rest}:
            return f"Unknown action: {action}, extra: {rest}"
        case _:
            return "Invalid command"

# List destructuring
def first_and_rest(items: List[int]) -> Tuple[int, List[int]]:
    match items:
        case [first, *rest]:
            return (first, rest)
        case []:
            raise ValueError("Empty list")

print(first_and_rest([1, 2, 3, 4]))  # (1, [2, 3, 4])
```

**TypeScript (Comprehensive Destructuring)**
```typescript
// Object destructuring in parameters
interface Config {
    host: string;
    port: number;
    secure?: boolean;
}

function createConnection({ host, port, secure = false }: Config): string {
    const protocol = secure ? 'https' : 'http';
    return `${protocol}://${host}:${port}`;
}

// Array destructuring in parameters
function processCoordinates([x, y, z = 0]: number[]): string {
    return `Point at (${x}, ${y}, ${z})`;
}

// Nested destructuring
interface User {
    name: string;
    address: {
        city: string;
        country: string;
    };
    tags: string[];
}

function formatUser({
    name,
    address: { city, country },
    tags: [primaryTag, ...otherTags]
}: User): string {
    return `${name} from ${city}, ${country}. Primary: ${primaryTag}`;
}

// Rest parameters with destructuring
function mergeObjects<T>({ id, ...rest }: T & { id: number }): Omit<T, 'id'> {
    console.log(`Processing id: ${id}`);
    return rest as Omit<T, 'id'>;
}

// Rename during destructuring
function displayPerson({ name: fullName, age: years }: { name: string; age: number }) {
    console.log(`${fullName} is ${years} years old`);
}

// Default values with destructuring
function fetchData({
    url,
    method = 'GET',
    headers = {}
}: {
    url: string;
    method?: string;
    headers?: Record<string, string>
}): void {
    console.log(`${method} ${url}`);
}
```

**Go (No Native Destructuring - Manual)**
```go
package main

// Go requires manual "destructuring"
type User struct {
    Name    string
    Age     int
    Address Address
}

type Address struct {
    City    string
    Country string
}

// Cannot destructure in parameter - must do in body
func processUser(user User) string {
    // Manual extraction
    name := user.Name
    city := user.Address.City
    return name + " from " + city
}

// Common pattern: return multiple values for "destructuring"
func getUserInfo(user User) (string, int, string) {
    return user.Name, user.Age, user.Address.City
}

func main() {
    u := User{
        Name: "Alice",
        Age:  30,
        Address: Address{City: "Seoul", Country: "Korea"},
    }

    // "Destructuring" via multiple return values
    name, age, city := getUserInfo(u)
    _ = name
    _ = age
    _ = city
}
```

**C++ (Structured Bindings)**
```cpp
#include <tuple>
#include <string>
#include <utility>

struct User {
    std::string name;
    int age;
};

// C++17 structured bindings in function
void processUsers() {
    std::vector<std::pair<std::string, int>> users = {
        {"Alice", 30},
        {"Bob", 25}
    };

    // Destructure in range-for
    for (const auto& [name, age] : users) {
        std::cout << name << ": " << age << "\n";
    }
}

// Return tuple for "multi-return destructuring"
std::tuple<std::string, int, bool> getUserData() {
    return {"Alice", 30, true};
}

void useDestructuring() {
    // Structured binding
    auto [name, age, active] = getUserData();

    // Can also ignore with std::ignore (pre-C++17)
    // std::tie(name, std::ignore, active) = getUserData();
}

// Template parameter pack "destructuring"
template<typename... Args>
void printAll(Args... args) {
    ((std::cout << args << " "), ...);  // Fold expression
}
```

---

#### 2.2.3 Nested Patterns

**Java 21 (Nested Record Patterns)**
```java
record Point(int x, int y) {}
record Circle(Point center, int radius) {}
record Rectangle(Point topLeft, Point bottomRight) {}

sealed interface Shape permits Circle, Rectangle {}

// Deep nested pattern matching
String describeShape(Shape shape) {
    return switch (shape) {
        // Nested destructuring: Circle -> Point -> x, y
        case Circle(Point(int x, int y), int r) when r > 10 ->
            "Large circle centered at (" + x + "," + y + ")";
        case Circle(Point(int x, int y), int r) ->
            "Small circle at (" + x + "," + y + ") with radius " + r;
        // Multiple nested patterns
        case Rectangle(Point(int x1, int y1), Point(int x2, int y2)) ->
            "Rectangle from (" + x1 + "," + y1 + ") to (" + x2 + "," + y2 + ")";
    };
}

// Three levels deep
record Company(String name, Department dept) {}
record Department(String name, Employee manager) {}
record Employee(String name, int id) {}

void processCompany(Company company) {
    if (company instanceof Company(
            String companyName,
            Department(String deptName, Employee(String mgrName, int mgrId))
    )) {
        System.out.println(companyName + " -> " + deptName + " -> " + mgrName);
    }
}
```

**Python 3.10+ (Deep Structural Matching)**
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Address:
    street: str
    city: str
    country: str

@dataclass
class Person:
    name: str
    age: int
    address: Optional[Address]

@dataclass
class Company:
    name: str
    ceo: Person
    employees: List[Person]

def analyze_company(company):
    match company:
        # Deep nested pattern with guards
        case Company(
            name=company_name,
            ceo=Person(name=ceo_name, age=age, address=Address(city=city))
        ) if age > 50:
            return f"{company_name} has senior CEO {ceo_name} from {city}"

        # Match on nested list structure
        case Company(
            employees=[Person(name=first), Person(name=second), *rest]
        ):
            return f"Company with employees: {first}, {second}, and {len(rest)} more"

        # Handle None in nested structure
        case Company(ceo=Person(address=None)):
            return "CEO has no address on file"

        case _:
            return "Unknown company structure"

# Matching nested dictionaries (common in APIs)
def parse_api_response(response: dict):
    match response:
        case {
            "status": "success",
            "data": {
                "user": {"id": user_id, "profile": {"name": name}},
                "permissions": [first_perm, *_]
            }
        }:
            return f"User {name} (ID: {user_id}) with permission: {first_perm}"

        case {"status": "error", "message": msg}:
            return f"Error: {msg}"

        case {"status": status}:
            return f"Unknown status: {status}"

# List of tuples with nested matching
def process_transactions(transactions):
    results = []
    for tx in transactions:
        match tx:
            case ("transfer", {"from": src, "to": dst, "amount": amt}) if amt > 1000:
                results.append(f"Large transfer: {src} -> {dst}: ${amt}")
            case ("transfer", {"from": src, "to": dst, "amount": amt}):
                results.append(f"Transfer: {src} -> {dst}: ${amt}")
            case ("deposit", {"account": acc, "amount": amt}):
                results.append(f"Deposit to {acc}: ${amt}")
            case _:
                results.append("Unknown transaction")
    return results
```

**TypeScript (Nested Type Guards)**
```typescript
// TypeScript uses type narrowing rather than true nested patterns
// But we can simulate with discriminated unions

interface Address {
    street: string;
    city: string;
}

interface BasicUser {
    type: 'basic';
    name: string;
}

interface PremiumUser {
    type: 'premium';
    name: string;
    address: Address;
    subscription: {
        plan: 'monthly' | 'yearly';
        active: boolean;
    };
}

type User = BasicUser | PremiumUser;

// Nested type checking requires multiple levels
function processUser(user: User): string {
    switch (user.type) {
        case 'basic':
            return `Basic user: ${user.name}`;
        case 'premium':
            // TypeScript now knows user is PremiumUser
            const { address, subscription } = user;
            if (subscription.plan === 'yearly' && subscription.active) {
                return `Premium yearly subscriber ${user.name} from ${address.city}`;
            }
            return `Premium user ${user.name}`;
    }
}

// Custom type guards for nested structures
interface APIResponse {
    status: 'success' | 'error';
    data?: {
        users?: Array<{
            id: number;
            profile?: {
                name: string;
                verified: boolean;
            };
        }>;
    };
    error?: string;
}

function isVerifiedUser(
    response: APIResponse
): response is APIResponse & {
    status: 'success';
    data: { users: Array<{ profile: { verified: true } }> };
} {
    return (
        response.status === 'success' &&
        response.data?.users?.some(u => u.profile?.verified === true) === true
    );
}

// Using the type guard
function handleResponse(response: APIResponse): void {
    if (isVerifiedUser(response)) {
        // TypeScript knows the structure is verified
        const firstUser = response.data.users[0];
        console.log(`Verified user found`);
    }
}
```

---

#### 2.2.4 Guard Expressions

**Java 21 (when clause)**
```java
// Guard clauses with 'when' keyword
String categorize(Object obj) {
    return switch (obj) {
        case Integer i when i < 0 -> "Negative integer: " + i;
        case Integer i when i == 0 -> "Zero";
        case Integer i when i > 0 && i < 100 -> "Small positive: " + i;
        case Integer i -> "Large positive: " + i;
        case String s when s.isEmpty() -> "Empty string";
        case String s when s.length() < 10 -> "Short string: " + s;
        case String s -> "Long string of length " + s.length();
        case null -> "Null value";
        default -> "Unknown";
    };
}

// Multiple guards with records
record Transaction(String type, double amount, String currency) {}

String processTransaction(Transaction tx) {
    return switch (tx) {
        case Transaction(var type, var amt, var curr)
                when type.equals("withdrawal") && amt > 10000 ->
            "Large withdrawal: " + amt + " " + curr + " - requires approval";
        case Transaction(var type, var amt, _)
                when type.equals("withdrawal") && amt > 1000 ->
            "Medium withdrawal: " + amt;
        case Transaction("deposit", var amt, _) when amt > 0 ->
            "Deposit: " + amt;
        case Transaction t ->
            "Standard transaction: " + t;
    };
}
```

**Python (if guards)**
```python
from dataclasses import dataclass
from typing import Union, List

@dataclass
class Order:
    items: List[str]
    total: float
    priority: bool = False

def process_order(order: Order) -> str:
    match order:
        # Guard with complex condition
        case Order(items=items, total=total, priority=True) if total > 1000:
            return f"URGENT VIP order: {len(items)} items, ${total}"

        case Order(items=items, total=total) if total > 1000:
            return f"Large order: {len(items)} items, ${total}"

        case Order(items=[single_item], total=total) if total < 10:
            return f"Small single-item order: {single_item}"

        case Order(items=[], total=_):
            return "Empty order"

        case Order(items=items) if len(items) > 10:
            return f"Bulk order with {len(items)} items"

        case _:
            return "Standard order"

# Guards with type checking
def validate_input(data: Union[int, str, list]) -> str:
    match data:
        case int(n) if n < 0:
            return "Negative numbers not allowed"
        case int(n) if n > 1000:
            return "Number too large"
        case int(n):
            return f"Valid number: {n}"
        case str(s) if len(s) == 0:
            return "Empty string not allowed"
        case str(s) if not s.isalnum():
            return "String must be alphanumeric"
        case str(s):
            return f"Valid string: {s}"
        case list(items) if len(items) == 0:
            return "Empty list not allowed"
        case list(items) if len(items) > 100:
            return "List too long"
        case _:
            return "Valid input"

# Multiple conditions in guard
def categorize_point(point: tuple) -> str:
    match point:
        case (x, y) if x == 0 and y == 0:
            return "Origin"
        case (x, y) if x == 0:
            return f"On Y-axis at y={y}"
        case (x, y) if y == 0:
            return f"On X-axis at x={x}"
        case (x, y) if x > 0 and y > 0:
            return f"Quadrant I: ({x}, {y})"
        case (x, y) if x < 0 and y > 0:
            return f"Quadrant II: ({x}, {y})"
        case (x, y) if x < 0 and y < 0:
            return f"Quadrant III: ({x}, {y})"
        case (x, y):
            return f"Quadrant IV: ({x}, {y})"
```

**TypeScript (Manual Guards with Type Predicates)**
```typescript
// TypeScript doesn't have native guard clauses
// Use type predicates and conditional logic

interface Order {
    id: string;
    total: number;
    items: string[];
    status: 'pending' | 'processing' | 'shipped' | 'delivered';
    priority?: boolean;
}

// Type predicate as guard
function isHighValueOrder(order: Order): order is Order & { total: number } {
    return order.total > 1000;
}

function isPriorityOrder(order: Order): order is Order & { priority: true } {
    return order.priority === true;
}

// Combining guards
function processOrder(order: Order): string {
    // Guard-like pattern with early returns
    if (order.status === 'delivered') {
        return 'Order already delivered';
    }

    if (isPriorityOrder(order) && isHighValueOrder(order)) {
        return `URGENT VIP: Order ${order.id} - $${order.total}`;
    }

    if (isHighValueOrder(order)) {
        return `High value order: $${order.total}`;
    }

    if (order.items.length === 0) {
        return 'Empty order';
    }

    return `Standard order: ${order.items.length} items`;
}

// Using discriminated unions with computed guards
type Result<T> =
    | { success: true; data: T }
    | { success: false; error: string };

function handleResult<T>(
    result: Result<T>,
    validator: (data: T) => boolean
): string {
    if (!result.success) {
        return `Error: ${result.error}`;
    }

    // Guard-like validation
    if (!validator(result.data)) {
        return 'Data validation failed';
    }

    return 'Success';
}

// Exhaustive pattern with guards
type HTTPStatus = 200 | 201 | 400 | 401 | 404 | 500;

function handleStatus(status: HTTPStatus, retryCount: number): string {
    switch (status) {
        case 200:
        case 201:
            return 'Success';
        case 400:
            return 'Bad request - check input';
        case 401:
            // Guard-like condition
            if (retryCount < 3) {
                return 'Unauthorized - will retry';
            }
            return 'Unauthorized - max retries exceeded';
        case 404:
            return 'Not found';
        case 500:
            if (retryCount < 5) {
                return 'Server error - retrying';
            }
            return 'Server error - giving up';
        default:
            const _exhaustive: never = status;
            return _exhaustive;
    }
}
```

**Go (Switch with Conditions)**
```go
package main

import "fmt"

type Order struct {
    ID       string
    Total    float64
    Items    []string
    Priority bool
}

// Go doesn't have pattern matching guards
// Use switch true pattern for guard-like behavior
func processOrder(order Order) string {
    switch {
    case order.Priority && order.Total > 1000:
        return fmt.Sprintf("URGENT VIP: Order %s - $%.2f", order.ID, order.Total)
    case order.Total > 1000:
        return fmt.Sprintf("High value: $%.2f", order.Total)
    case len(order.Items) == 0:
        return "Empty order"
    case len(order.Items) == 1:
        return fmt.Sprintf("Single item: %s", order.Items[0])
    default:
        return fmt.Sprintf("Standard: %d items", len(order.Items))
    }
}

// Type switch with additional conditions
func describe(i interface{}) string {
    switch v := i.(type) {
    case int:
        // Nested switch for guards
        switch {
        case v < 0:
            return "Negative integer"
        case v == 0:
            return "Zero"
        case v < 100:
            return "Small positive"
        default:
            return "Large positive"
        }
    case string:
        if len(v) == 0 {
            return "Empty string"
        }
        return fmt.Sprintf("String: %s", v)
    default:
        return "Unknown type"
    }
}
```

---

#### 2.2.5 Type-Based Matching

**Java (instanceof Pattern Matching)**
```java
// Traditional instanceof
void oldStyle(Object obj) {
    if (obj instanceof String) {
        String s = (String) obj;  // Explicit cast required
        System.out.println(s.length());
    }
}

// Pattern matching for instanceof (Java 16+)
void newStyle(Object obj) {
    if (obj instanceof String s) {  // Pattern variable 's' bound
        System.out.println(s.length());  // No cast needed!
    }

    // Can use with && but not ||
    if (obj instanceof String s && s.length() > 5) {
        System.out.println("Long string: " + s);
    }
}

// Type pattern in switch (Java 21)
String getTypeName(Object obj) {
    return switch (obj) {
        case Integer i -> "Integer: " + i;
        case Long l -> "Long: " + l;
        case Double d -> "Double: " + d;
        case String s -> "String: " + s;
        case int[] arr -> "int array of length " + arr.length;
        case Object[] arr -> "Object array of length " + arr.length;
        case null -> "null";
        default -> "Unknown: " + obj.getClass().getSimpleName();
    };
}

// Sealed classes for exhaustive type matching
sealed interface Animal permits Dog, Cat, Bird {}
record Dog(String name) implements Animal {}
record Cat(String name, boolean indoor) implements Animal {}
record Bird(String name, boolean canFly) implements Animal {}

String describeAnimal(Animal animal) {
    return switch (animal) {
        case Dog(String name) -> name + " is a dog";
        case Cat(String name, true) -> name + " is an indoor cat";
        case Cat(String name, false) -> name + " is an outdoor cat";
        case Bird(String name, boolean flies) ->
            name + (flies ? " can fly" : " cannot fly");
        // No default needed - compiler knows all cases covered!
    };
}
```

**Python (Type Guards and Match)**
```python
from typing import Union, TypeGuard, Any
from dataclasses import dataclass

# Type guard function
def is_string_list(val: list[Any]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)

def process_list(items: list[Any]) -> str:
    if is_string_list(items):
        # Type checker knows items is list[str] here
        return ", ".join(items)
    return str(items)

# Match with type patterns
def describe_type(obj: Any) -> str:
    match obj:
        case bool():  # Must come before int (bool is subclass of int)
            return f"Boolean: {obj}"
        case int():
            return f"Integer: {obj}"
        case float():
            return f"Float: {obj}"
        case str():
            return f"String of length {len(obj)}"
        case list():
            return f"List with {len(obj)} elements"
        case dict():
            return f"Dict with {len(obj)} keys"
        case tuple():
            return f"Tuple with {len(obj)} elements"
        case None:
            return "None value"
        case _:
            return f"Unknown type: {type(obj).__name__}"

# Class-based pattern matching
@dataclass
class Point:
    x: float
    y: float

@dataclass
class Circle:
    center: Point
    radius: float

@dataclass
class Rectangle:
    top_left: Point
    bottom_right: Point

Shape = Union[Point, Circle, Rectangle]

def get_area(shape: Shape) -> float:
    match shape:
        case Point():
            return 0.0
        case Circle(radius=r):
            return 3.14159 * r * r
        case Rectangle(top_left=Point(x=x1, y=y1), bottom_right=Point(x=x2, y=y2)):
            return abs((x2 - x1) * (y2 - y1))
        case _:
            raise ValueError(f"Unknown shape: {shape}")

# Runtime type checking with isinstance
def safe_process(data: Any) -> str:
    match data:
        case _ if isinstance(data, (int, float)) and data < 0:
            return "Negative number"
        case _ if isinstance(data, str) and data.isupper():
            return "UPPERCASE STRING"
        case _ if hasattr(data, '__iter__') and not isinstance(data, str):
            return f"Iterable with {len(list(data))} items"
        case _:
            return str(data)
```

**TypeScript (Type Guards and Discriminated Unions)**
```typescript
// Type predicates for runtime type checking
function isString(value: unknown): value is string {
    return typeof value === 'string';
}

function isNumber(value: unknown): value is number {
    return typeof value === 'number';
}

function isArray<T>(value: unknown, itemGuard: (item: unknown) => item is T): value is T[] {
    return Array.isArray(value) && value.every(itemGuard);
}

// Using type guards
function processValue(value: unknown): string {
    if (isString(value)) {
        return value.toUpperCase();  // TypeScript knows it's string
    }
    if (isNumber(value)) {
        return value.toFixed(2);  // TypeScript knows it's number
    }
    if (isArray(value, isString)) {
        return value.join(', ');  // TypeScript knows it's string[]
    }
    return String(value);
}

// Discriminated unions (preferred approach)
type Result<T, E = Error> =
    | { type: 'success'; value: T }
    | { type: 'error'; error: E }
    | { type: 'loading' }
    | { type: 'idle' };

function handleResult<T>(result: Result<T>): string {
    switch (result.type) {
        case 'success':
            return `Got: ${result.value}`;  // TypeScript knows value exists
        case 'error':
            return `Error: ${result.error.message}`;  // TypeScript knows error exists
        case 'loading':
            return 'Loading...';
        case 'idle':
            return 'Ready';
        default:
            // Exhaustiveness check
            const _exhaustive: never = result;
            return _exhaustive;
    }
}

// 'in' operator type narrowing
interface Dog { bark(): void; breed: string; }
interface Cat { meow(): void; indoor: boolean; }
interface Bird { fly(): void; wingspan: number; }

type Pet = Dog | Cat | Bird;

function interactWithPet(pet: Pet): void {
    if ('bark' in pet) {
        pet.bark();  // TypeScript knows it's Dog
        console.log(pet.breed);
    } else if ('meow' in pet) {
        pet.meow();  // TypeScript knows it's Cat
    } else {
        pet.fly();  // TypeScript knows it's Bird
    }
}

// Class-based type checking
class User {
    constructor(public name: string, public email: string) {}
}

class Admin extends User {
    constructor(name: string, email: string, public permissions: string[]) {
        super(name, email);
    }
}

function greet(user: User): string {
    if (user instanceof Admin) {
        return `Hello Admin ${user.name}, you have ${user.permissions.length} permissions`;
    }
    return `Hello ${user.name}`;
}
```

**Go (Type Switch)**
```go
package main

import (
    "fmt"
    "reflect"
)

// Basic type switch
func describe(i interface{}) string {
    switch v := i.(type) {
    case nil:
        return "nil"
    case bool:
        return fmt.Sprintf("bool: %t", v)
    case int, int8, int16, int32, int64:
        return fmt.Sprintf("integer: %v", v)
    case uint, uint8, uint16, uint32, uint64:
        return fmt.Sprintf("unsigned integer: %v", v)
    case float32, float64:
        return fmt.Sprintf("float: %v", v)
    case string:
        return fmt.Sprintf("string of length %d: %s", len(v), v)
    case []int:
        return fmt.Sprintf("int slice of length %d", len(v))
    case []string:
        return fmt.Sprintf("string slice: %v", v)
    case map[string]interface{}:
        return fmt.Sprintf("map with %d keys", len(v))
    default:
        return fmt.Sprintf("unknown type: %s", reflect.TypeOf(i))
    }
}

// Interface-based type switch
type Animal interface {
    Speak() string
}

type Dog struct{ Name string }
type Cat struct{ Name string }
type Bird struct{ Name string }

func (d Dog) Speak() string { return "Woof!" }
func (c Cat) Speak() string { return "Meow!" }
func (b Bird) Speak() string { return "Tweet!" }

func describeAnimal(a Animal) string {
    switch pet := a.(type) {
    case Dog:
        return fmt.Sprintf("%s the dog says %s", pet.Name, pet.Speak())
    case Cat:
        return fmt.Sprintf("%s the cat says %s", pet.Name, pet.Speak())
    case Bird:
        return fmt.Sprintf("%s the bird says %s", pet.Name, pet.Speak())
    default:
        return "Unknown animal"
    }
}

// Type assertion with ok pattern
func tryAsString(i interface{}) (string, bool) {
    s, ok := i.(string)
    return s, ok
}

// Combining type switch with conditions
func process(data interface{}) string {
    switch v := data.(type) {
    case int:
        if v < 0 {
            return "negative int"
        }
        return "non-negative int"
    case string:
        if v == "" {
            return "empty string"
        }
        return "non-empty string"
    case []byte:
        if len(v) == 0 {
            return "empty bytes"
        }
        return fmt.Sprintf("%d bytes", len(v))
    default:
        return "other"
    }
}
```

**C++ (std::variant and std::visit)**
```cpp
#include <variant>
#include <string>
#include <iostream>
#include <vector>

// Define variant type (discriminated union)
struct Circle { double radius; };
struct Rectangle { double width, height; };
struct Triangle { double base, height; };

using Shape = std::variant<Circle, Rectangle, Triangle>;

// Visitor pattern for type-based matching
struct AreaVisitor {
    double operator()(const Circle& c) const {
        return 3.14159 * c.radius * c.radius;
    }
    double operator()(const Rectangle& r) const {
        return r.width * r.height;
    }
    double operator()(const Triangle& t) const {
        return 0.5 * t.base * t.height;
    }
};

double getArea(const Shape& shape) {
    return std::visit(AreaVisitor{}, shape);
}

// Lambda overload pattern (C++17)
template<class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template<class... Ts> overloaded(Ts...) -> overloaded<Ts...>;

void describeShape(const Shape& shape) {
    std::visit(overloaded{
        [](const Circle& c) {
            std::cout << "Circle with radius " << c.radius << "\n";
        },
        [](const Rectangle& r) {
            std::cout << "Rectangle " << r.width << "x" << r.height << "\n";
        },
        [](const Triangle& t) {
            std::cout << "Triangle with base " << t.base << "\n";
        }
    }, shape);
}

// Type checking with std::holds_alternative
void checkType(const Shape& shape) {
    if (std::holds_alternative<Circle>(shape)) {
        auto& circle = std::get<Circle>(shape);
        std::cout << "It's a circle with radius " << circle.radius << "\n";
    }
}

// Generic variant with any type
using Value = std::variant<int, double, std::string, std::vector<int>>;

std::string describeValue(const Value& v) {
    return std::visit(overloaded{
        [](int i) { return "int: " + std::to_string(i); },
        [](double d) { return "double: " + std::to_string(d); },
        [](const std::string& s) { return "string: " + s; },
        [](const std::vector<int>& vec) {
            return "vector of " + std::to_string(vec.size()) + " ints";
        }
    }, v);
}
```

---

### 2.3 Exhaustiveness Checking (Critical for TypeScript!)

**TypeScript (never type for exhaustiveness)**
```typescript
// CRITICAL: The never type for exhaustive checking

// Discriminated union
type Action =
    | { type: 'INCREMENT' }
    | { type: 'DECREMENT' }
    | { type: 'RESET'; payload: number };

function reducer(state: number, action: Action): number {
    switch (action.type) {
        case 'INCREMENT':
            return state + 1;
        case 'DECREMENT':
            return state - 1;
        case 'RESET':
            return action.payload;
        default:
            // Exhaustiveness check: if we add a new action type
            // and forget to handle it, this will cause a compile error
            const _exhaustiveCheck: never = action;
            return _exhaustiveCheck;
    }
}

// Helper function for exhaustiveness
function assertNever(x: never): never {
    throw new Error(`Unexpected value: ${x}`);
}

// If we add a new action type and forget to handle it:
type ExtendedAction = Action | { type: 'DOUBLE' };

function reducerWithBug(state: number, action: ExtendedAction): number {
    switch (action.type) {
        case 'INCREMENT':
            return state + 1;
        case 'DECREMENT':
            return state - 1;
        case 'RESET':
            return action.payload;
        // Missing 'DOUBLE' case!
        default:
            // ERROR: Type '{ type: "DOUBLE"; }' is not assignable to type 'never'
            return assertNever(action);
    }
}

// Exhaustive type narrowing in conditionals
type Shape =
    | { kind: 'circle'; radius: number }
    | { kind: 'square'; side: number }
    | { kind: 'triangle'; base: number; height: number };

function getArea(shape: Shape): number {
    if (shape.kind === 'circle') {
        return Math.PI * shape.radius ** 2;
    }
    if (shape.kind === 'square') {
        return shape.side ** 2;
    }
    if (shape.kind === 'triangle') {
        return (shape.base * shape.height) / 2;
    }
    // TypeScript knows shape is never here - all cases handled
    const _check: never = shape;
    return _check;
}
```

**Java (Sealed Classes for Exhaustiveness)**
```java
// Sealed classes + pattern matching = exhaustive checking

sealed interface Result<T> permits Success, Failure {}
record Success<T>(T value) implements Result<T> {}
record Failure<T>(String error) implements Result<T> {}

// Compiler warns if not all cases handled
<T> String handleResult(Result<T> result) {
    return switch (result) {
        case Success<T>(T value) -> "Success: " + value;
        case Failure<T>(String error) -> "Error: " + error;
        // No default needed - compiler knows all cases are covered!
    };
}

// More complex sealed hierarchy
sealed interface Shape permits Circle, Rectangle, Triangle {}
record Circle(double radius) implements Shape {}
record Rectangle(double width, double height) implements Shape {}
record Triangle(double base, double height) implements Shape {}

double getArea(Shape shape) {
    return switch (shape) {
        case Circle(double r) -> Math.PI * r * r;
        case Rectangle(double w, double h) -> w * h;
        case Triangle(double b, double h) -> 0.5 * b * h;
        // Exhaustive - no default required
    };
}

// If you add a new permitted class without handling it:
sealed interface ExtendedShape permits Circle, Rectangle, Triangle, Pentagon {}
record Pentagon(double side) implements ExtendedShape {}

// Compile error: switch expression does not cover all possible input values
// double getAreaBroken(ExtendedShape shape) {
//     return switch (shape) {
//         case Circle(double r) -> Math.PI * r * r;
//         case Rectangle(double w, double h) -> w * h;
//         case Triangle(double b, double h) -> 0.5 * b * h;
//         // Missing Pentagon!
//     };
// }
```

**Python (No Native Exhaustiveness - Use typing_extensions)**
```python
from typing import Union, NoReturn, assert_never
from enum import Enum, auto
from dataclasses import dataclass

# Python 3.11+ has assert_never for exhaustiveness
# Earlier versions: from typing_extensions import assert_never

class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()

def color_to_hex(color: Color) -> str:
    match color:
        case Color.RED:
            return "#FF0000"
        case Color.GREEN:
            return "#00FF00"
        case Color.BLUE:
            return "#0000FF"
        case _ as unreachable:
            # Type checker (mypy/pyright) will error if cases are missing
            assert_never(unreachable)

# With discriminated unions (using Literal types)
from typing import Literal

@dataclass
class Circle:
    kind: Literal["circle"] = "circle"
    radius: float = 0.0

@dataclass
class Square:
    kind: Literal["square"] = "square"
    side: float = 0.0

Shape = Union[Circle, Square]

def get_area(shape: Shape) -> float:
    match shape:
        case Circle(radius=r):
            return 3.14159 * r * r
        case Square(side=s):
            return s * s
        case _ as unreachable:
            assert_never(unreachable)

# Runtime exhaustiveness with Enum
def process_color(color: Color) -> str:
    handlers = {
        Color.RED: lambda: "Stop",
        Color.GREEN: lambda: "Go",
        Color.BLUE: lambda: "Info",
    }
    # Runtime check: will KeyError if new color added
    return handlers[color]()
```

---

## 3. Design Philosophy Links

### Official Documentation

| Language | Pattern Matching Documentation |
|----------|-------------------------------|
| **Java** | [JEP 441: Pattern Matching for switch](https://openjdk.org/jeps/441) |
| **Java** | [JEP 440: Record Patterns](https://openjdk.org/jeps/440) |
| **Python** | [PEP 634: Structural Pattern Matching](https://peps.python.org/pep-0634/) |
| **Python** | [PEP 636: Tutorial](https://peps.python.org/pep-0636/) |
| **TypeScript** | [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html) |
| **TypeScript** | [Discriminated Unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions) |
| **Go** | [Type switches](https://go.dev/tour/methods/16) |
| **C++** | [Structured Bindings (C++17)](https://en.cppreference.com/w/cpp/language/structured_binding) |
| **C++** | [std::variant](https://en.cppreference.com/w/cpp/utility/variant) |
| **Spark** | [CASE WHEN](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-case.html) |

---

## 4. Palantir Context Hint

### 4.1 Critical Interview Topics

#### TypeScript Discriminated Unions (HIGHEST PRIORITY)

```typescript
// Palantir heavily uses TypeScript. Master this pattern!

// API Response pattern
type APIResponse<T> =
    | { status: 'success'; data: T; timestamp: number }
    | { status: 'error'; error: { code: number; message: string } }
    | { status: 'loading' }
    | { status: 'idle' };

// Event system pattern (common in Foundry)
type FoundryEvent =
    | { type: 'OBJECT_CREATED'; objectType: string; rid: string }
    | { type: 'OBJECT_UPDATED'; objectType: string; rid: string; changes: string[] }
    | { type: 'OBJECT_DELETED'; objectType: string; rid: string }
    | { type: 'LINK_CREATED'; sourceRid: string; targetRid: string; linkType: string };

function handleFoundryEvent(event: FoundryEvent): void {
    switch (event.type) {
        case 'OBJECT_CREATED':
            console.log(`Created ${event.objectType}: ${event.rid}`);
            break;
        case 'OBJECT_UPDATED':
            console.log(`Updated ${event.rid}: ${event.changes.join(', ')}`);
            break;
        case 'OBJECT_DELETED':
            console.log(`Deleted ${event.rid}`);
            break;
        case 'LINK_CREATED':
            console.log(`Linked ${event.sourceRid} -> ${event.targetRid}`);
            break;
        default:
            const _exhaustive: never = event;
            throw new Error(`Unhandled event: ${_exhaustive}`);
    }
}
```

### 4.2 Common Interview Questions

1. **"Implement a type-safe state machine using discriminated unions"**
```typescript
type TrafficLight =
    | { state: 'red'; countdown: number }
    | { state: 'yellow'; countdown: number }
    | { state: 'green'; countdown: number };

function nextState(light: TrafficLight): TrafficLight {
    switch (light.state) {
        case 'green':
            return { state: 'yellow', countdown: 5 };
        case 'yellow':
            return { state: 'red', countdown: 30 };
        case 'red':
            return { state: 'green', countdown: 25 };
    }
}
```

2. **"Parse a nested JSON structure using pattern matching"**
```python
def parse_config(config: dict) -> str:
    match config:
        case {"database": {"host": host, "port": port}, "cache": {"enabled": True}}:
            return f"DB at {host}:{port} with cache"
        case {"database": {"host": host, "port": port}}:
            return f"DB at {host}:{port} without cache"
        case {"database": db_config} if "connection_string" in db_config:
            return f"Using connection string"
        case _:
            raise ValueError("Invalid config")
```

3. **"How does exhaustiveness checking prevent bugs?"**
   - Answer: When you add a new variant to a union type, the compiler forces you to handle it everywhere
   - TypeScript: `never` type trick catches missing cases at compile time
   - Java: Sealed classes prevent new implementations, switch expressions require all cases

4. **"Compare pattern matching in Python vs TypeScript"**
   - Python: Runtime structural matching, more flexible patterns
   - TypeScript: Compile-time type narrowing, stricter guarantees
   - Python can match arbitrary nested structures
   - TypeScript requires discriminant property for reliable narrowing

### 4.3 Red Flags to Avoid

```typescript
// BAD: Type assertion instead of proper narrowing
function processBAD(data: unknown) {
    const typed = data as { name: string };  // Dangerous!
    console.log(typed.name);
}

// GOOD: Type guard with proper narrowing
function isNamed(data: unknown): data is { name: string } {
    return typeof data === 'object' && data !== null && 'name' in data;
}

function processGOOD(data: unknown) {
    if (isNamed(data)) {
        console.log(data.name);  // Safe!
    }
}
```

```python
# BAD: No exhaustiveness, silent failures
def get_area_bad(shape):
    if shape["type"] == "circle":
        return 3.14 * shape["radius"] ** 2
    # Forgot rectangle! Returns None silently

# GOOD: Explicit pattern matching with catch-all
def get_area_good(shape):
    match shape:
        case {"type": "circle", "radius": r}:
            return 3.14 * r * r
        case {"type": "rectangle", "width": w, "height": h}:
            return w * h
        case _:
            raise ValueError(f"Unknown shape: {shape}")
```

---

## 5. Cross-References

### 5.1 Related Knowledge Base Articles

| Article | Relevance to Pattern Matching |
|---------|------------------------------|
| **F30: Error Handling** | Pattern matching for Result/Option types |
| **F23: Data Structures** | Destructuring arrays, maps, objects |
| **F25: Type Systems** | Type narrowing and discriminated unions |
| **F31: Control Flow** | Switch/match as control flow mechanism |
| **F20: Functions** | Destructuring in function parameters |

### 5.2 Pattern Matching in Different Contexts

```
Error Handling (F30):
  - Result<T, E> pattern matching
  - Option/Maybe unwrapping
  - try/catch vs match on Result

Data Structures (F23):
  - Array destructuring [first, ...rest]
  - Object destructuring {key: value}
  - Tuple unpacking (a, b, c)

Type Systems (F25):
  - Union types and narrowing
  - Discriminated unions
  - Exhaustiveness with never

Control Flow (F31):
  - switch vs match expressions
  - Guard clauses
  - Early returns vs pattern matching
```

### 5.3 Language Feature Availability Timeline

| Feature | Java | Python | TypeScript | C++ |
|---------|------|--------|------------|-----|
| Basic switch | 1.0 | 3.10 | 1.0 | C |
| Type switch | 16 | 3.10 | 1.0 | 17 (variant) |
| Destructuring | 21 | 3.10 | 1.0 | 17 |
| Guards | 21 | 3.10 | Manual | N/A |
| Exhaustive | 21 | Manual | 2.0 | N/A |

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    PATTERN MATCHING CHEAT SHEET                  │
├─────────────────────────────────────────────────────────────────┤
│ Java 21:     switch (obj) { case Type t when guard -> ... }     │
│ Python 3.10: match obj: case Type() if guard: ...               │
│ TypeScript:  switch (obj.kind) { case 'type': ... }             │
│ Go:          switch v := obj.(type) { case Type: ... }          │
│ C++17:       std::visit(overloaded{...}, variant)               │
├─────────────────────────────────────────────────────────────────┤
│ EXHAUSTIVENESS:                                                  │
│ - TypeScript: const _: never = value                            │
│ - Java: sealed + switch expression                               │
│ - Python: assert_never(value)                                    │
├─────────────────────────────────────────────────────────────────┤
│ DESTRUCTURING:                                                   │
│ - Array:  const [a, b, ...rest] = arr                           │
│ - Object: const {x, y: renamed} = obj                           │
│ - Nested: case Circle(Point(x, y), r) ->                        │
├─────────────────────────────────────────────────────────────────┤
│ GUARD CLAUSES:                                                   │
│ - Java:   case Integer i when i > 0 ->                          │
│ - Python: case int(x) if x > 0:                                 │
│ - TS:     if (isType(x)) { /* x is narrowed */ }                │
└─────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2026-01-18*
*Knowledge Base Version: F33 v1.0*
