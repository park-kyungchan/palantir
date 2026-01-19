# F34: Control Flow Expressions & Patterns (제어 흐름 표현식과 패턴)

> **Concept ID**: F34
> **Category**: Control Flow / Code Style
> **Difficulty**: Intermediate
> **Languages**: Java, Python, TypeScript, Go, SQL, C++, Spark

---

## Section 1: Universal Concept (핵심 개념)

### Statement vs Expression: The Fundamental Distinction

Understanding the difference between **statements** and **expressions** is crucial for writing elegant, maintainable code:

| Concept | Definition | Example |
|---------|------------|---------|
| **Statement** | Performs an action, produces no value | `if (x) { doSomething(); }` |
| **Expression** | Evaluates to a value | `x > 0 ? "positive" : "non-positive"` |

**Why This Matters:**
- Expression-oriented code is often more **concise** and **composable**
- Functional programming languages favor expressions
- Modern languages increasingly support expression-based control flow

### The Guard Clause Mental Model

**The Pyramid of Doom (Anti-Pattern):**
```
function process(user) {
    if (user != null) {
        if (user.isActive()) {
            if (user.hasPermission()) {
                if (data.isValid()) {
                    // Finally do something
                    // Deeply nested
                    // Hard to read
                    // "Arrow code"
                }
            }
        }
    }
}
```

**Guard Clauses (Clean Pattern):**
```
function process(user) {
    if (user == null) return;           // Guard 1
    if (!user.isActive()) return;       // Guard 2
    if (!user.hasPermission()) return;  // Guard 3
    if (!data.isValid()) return;        // Guard 4

    // Happy path - clear and flat
    doMainWork();
}
```

**Mental Model:** Think of guards as **bouncers at a club** - they filter out invalid cases at the door, leaving only valid guests inside.

### Why Control Flow Patterns Matter

1. **Readability**: Flat code > Nested code
2. **Maintainability**: Single exit points can be harder to follow than early returns
3. **Bug Prevention**: Guard clauses catch edge cases explicitly
4. **Performance**: Short-circuit evaluation avoids unnecessary computation
5. **Null Safety**: Modern operators prevent NullPointerException/TypeError

### Core Patterns Overview

| Pattern | Purpose | Key Benefit |
|---------|---------|-------------|
| **Early Return** | Exit function when condition met | Reduces nesting |
| **Guard Clause** | Filter invalid inputs at start | Explicit edge case handling |
| **Short-Circuit** | Skip evaluation when result determined | Performance + null safety |
| **Null Coalescing** | Provide defaults for null/undefined | Concise null handling |
| **Optional Chaining** | Safe property access | Prevents null errors |
| **Fail-Fast** | Crash early on bad input | Easier debugging |

---

## Section 2: Semantic Comparison Matrix (언어별 의미 비교)

### Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **if as expression** | Ternary only | Ternary + inline if | Ternary | No | CASE WHEN | Ternary + if constexpr | when() |
| **Short-circuit &&** | `&&` | `and` | `&&` | `&&` | `AND` (impl-defined) | `&&` | `&` (col), `and` |
| **Short-circuit \|\|** | `\|\|` | `or` | `\|\|` | `\|\|` | `OR` (impl-defined) | `\|\|` | `\|` (col), `or` |
| **Null coalescing** | `Optional.orElse()` | `or` (falsy!) | `??` (nullish) | None (explicit) | `COALESCE()` | `value_or()` (C++17) | `coalesce()` |
| **Optional chaining** | `Optional.map()` | None native | `?.` | None (explicit) | None | None native | None |
| **Elvis operator** | None (`?:` proposed) | None | None (use `??`) | None | None | None | None |
| **Early return** | ✅ Full | ✅ Full | ✅ Full | ✅ Full (+ named) | N/A | ✅ Full | N/A (lazy) |
| **Pitfall** | Optional verbosity | `or` is falsy-based | `\|\|` vs `??` confusion | Verbose error handling | NULL propagation | Undefined behavior | Lazy evaluation |

### Detailed Code Examples

---

### Pattern 1: Guard Clause Refactoring

#### Java

```java
// ❌ BEFORE: Pyramid of Doom
public void processOrder(Order order) {
    if (order != null) {
        if (order.getCustomer() != null) {
            if (order.getItems() != null && !order.getItems().isEmpty()) {
                if (order.isPaymentVerified()) {
                    // Finally process
                    shipOrder(order);
                }
            }
        }
    }
}

// ✅ AFTER: Guard Clauses
public void processOrder(Order order) {
    if (order == null) return;
    if (order.getCustomer() == null) return;
    if (order.getItems() == null || order.getItems().isEmpty()) return;
    if (!order.isPaymentVerified()) return;

    shipOrder(order);  // Happy path is clear
}

// ✅ EVEN BETTER: With Optional (Java 8+)
public void processOrderModern(Order order) {
    Optional.ofNullable(order)
        .filter(o -> o.getCustomer() != null)
        .filter(o -> o.getItems() != null && !o.getItems().isEmpty())
        .filter(Order::isPaymentVerified)
        .ifPresent(this::shipOrder);
}
```

#### Python

```python
# ❌ BEFORE: Nested conditionals
def process_order(order):
    if order is not None:
        if order.customer is not None:
            if order.items:
                if order.is_payment_verified():
                    ship_order(order)

# ✅ AFTER: Guard clauses
def process_order(order):
    if order is None:
        return
    if order.customer is None:
        return
    if not order.items:
        return
    if not order.is_payment_verified():
        return

    ship_order(order)

# ✅ PYTHONIC: Using all() for multiple conditions
def process_order_pythonic(order):
    conditions = [
        order is not None,
        order and order.customer is not None,
        order and order.items,
        order and order.is_payment_verified(),
    ]

    if all(conditions):
        ship_order(order)
```

#### TypeScript

```typescript
// ❌ BEFORE: Callback hell style
function processOrder(order: Order | null): void {
    if (order !== null) {
        if (order.customer !== null) {
            if (order.items && order.items.length > 0) {
                if (order.isPaymentVerified()) {
                    shipOrder(order);
                }
            }
        }
    }
}

// ✅ AFTER: Guard clauses with type narrowing
function processOrder(order: Order | null): void {
    if (!order) return;
    if (!order.customer) return;
    if (!order.items?.length) return;  // Optional chaining!
    if (!order.isPaymentVerified()) return;

    shipOrder(order);  // TypeScript knows order is valid here
}

// ✅ MODERN: With optional chaining throughout
function processOrderModern(order: Order | null): void {
    const isValid = order?.customer &&
                    order?.items?.length &&
                    order?.isPaymentVerified?.();

    if (!isValid) return;
    shipOrder(order!);  // Non-null assertion (use carefully)
}
```

#### Go

```go
// ❌ BEFORE: Nested ifs
func processOrder(order *Order) error {
    if order != nil {
        if order.Customer != nil {
            if len(order.Items) > 0 {
                if order.IsPaymentVerified() {
                    return shipOrder(order)
                }
            }
        }
    }
    return errors.New("invalid order")
}

// ✅ AFTER: Guard clauses (idiomatic Go)
func processOrder(order *Order) error {
    if order == nil {
        return errors.New("order is nil")
    }
    if order.Customer == nil {
        return errors.New("customer is nil")
    }
    if len(order.Items) == 0 {
        return errors.New("no items in order")
    }
    if !order.IsPaymentVerified() {
        return errors.New("payment not verified")
    }

    return shipOrder(order)
}

// ✅ GO IDIOM: Named return for defer cleanup
func processOrderWithCleanup(order *Order) (result string, err error) {
    defer func() {
        if err != nil {
            log.Printf("processOrder failed: %v", err)
        }
    }()

    if order == nil {
        return "", errors.New("order is nil")
    }
    // ... guards continue

    return "success", shipOrder(order)
}
```

#### C++

```cpp
// ❌ BEFORE: Arrow code
void processOrder(Order* order) {
    if (order != nullptr) {
        if (order->customer != nullptr) {
            if (!order->items.empty()) {
                if (order->isPaymentVerified()) {
                    shipOrder(order);
                }
            }
        }
    }
}

// ✅ AFTER: Guard clauses
void processOrder(Order* order) {
    if (order == nullptr) return;
    if (order->customer == nullptr) return;
    if (order->items.empty()) return;
    if (!order->isPaymentVerified()) return;

    shipOrder(order);
}

// ✅ MODERN C++17: Using std::optional
void processOrderModern(std::optional<Order> order) {
    if (!order.has_value()) return;
    if (!order->customer.has_value()) return;
    if (order->items.empty()) return;
    if (!order->isPaymentVerified()) return;

    shipOrder(*order);
}

// ✅ C++17: if with initializer
void processOrderC17(OrderRepository& repo, int orderId) {
    if (auto order = repo.find(orderId); order != nullptr) {
        // order is scoped to this if-else block
        shipOrder(order);
    } else {
        logError("Order not found: " + std::to_string(orderId));
    }
}
```

---

### Pattern 2: Short-Circuit Evaluation

#### The Concept

Short-circuit evaluation means **stopping evaluation as soon as the result is determined**:
- `&&` / `and`: If left side is false, skip right side
- `||` / `or`: If left side is true, skip right side

#### Java

```java
// Short-circuit prevents NullPointerException
public boolean isValidUser(User user) {
    // If user is null, second condition is NOT evaluated
    return user != null && user.isActive();
}

// ❌ WRONG: This always evaluates both sides (bitwise AND)
public boolean isValidUserWrong(User user) {
    return user != null & user.isActive();  // NPE if user is null!
}

// Common pattern: Lazy initialization
private List<String> items;

public List<String> getItems() {
    // items is only created if null
    return items != null ? items : (items = new ArrayList<>());
}

// Equivalent using ||
public List<String> getItemsAlt() {
    if (items == null) {
        items = new ArrayList<>();
    }
    return items;
}
```

#### Python

```python
# Short-circuit with 'and' - returns last evaluated value
def get_username(user):
    # Returns user.name if user is truthy, else returns falsy user
    return user and user.name

# Short-circuit with 'or' - returns first truthy value
def get_display_name(user):
    # Returns first truthy value
    return user.nickname or user.username or user.email or "Anonymous"

# ⚠️ TRAP: Python 'or' returns the VALUE, not boolean
result = 0 or "default"      # "default" (0 is falsy!)
result = "" or "default"     # "default" (empty string is falsy!)
result = [] or [1, 2, 3]     # [1, 2, 3] (empty list is falsy!)
result = None or "default"   # "default"

# This is different from JavaScript/TypeScript ??
# Python has no null coalescing operator - must check explicitly
value = 0
result = value if value is not None else "default"  # 0 (correct!)

# Chained comparison (Python exclusive feature!)
def is_in_range(x):
    return 0 <= x <= 100  # Equivalent to: 0 <= x and x <= 100
```

#### TypeScript (Critical for Palantir OSDK!)

```typescript
// ⚠️ THE MOST IMPORTANT DISTINCTION FOR INTERVIEWS

// || returns first TRUTHY value (falsy: false, 0, "", null, undefined, NaN)
const a = 0 || "default";       // "default" - 0 is falsy!
const b = "" || "default";      // "default" - "" is falsy!
const c = false || "default";   // "default" - false is falsy!

// ?? returns first NON-NULLISH value (nullish: null, undefined ONLY)
const d = 0 ?? "default";       // 0 - only null/undefined trigger ??
const e = "" ?? "default";      // "" - empty string is NOT nullish
const f = false ?? "default";   // false - false is NOT nullish
const g = null ?? "default";    // "default" - null IS nullish
const h = undefined ?? "default"; // "default" - undefined IS nullish

// Real-world example: API response handling
interface ApiResponse {
    count?: number;
    name?: string;
    enabled?: boolean;
}

function processResponse(response: ApiResponse) {
    // ❌ WRONG: Loses valid 0, "", and false values
    const count = response.count || 10;     // Bug if count is 0
    const name = response.name || "N/A";    // Bug if name is ""
    const enabled = response.enabled || true; // Bug if enabled is false

    // ✅ CORRECT: Only defaults for null/undefined
    const countCorrect = response.count ?? 10;     // 0 stays 0
    const nameCorrect = response.name ?? "N/A";    // "" stays ""
    const enabledCorrect = response.enabled ?? true; // false stays false
}

// Short-circuit assignment operators (ES2021)
let x: number | null = null;
x ||= 10;  // x = x || 10 (assigns if x is falsy)
x &&= 20;  // x = x && 20 (assigns if x is truthy)
x ??= 30;  // x = x ?? 30 (assigns if x is nullish)
```

#### Go

```go
// Go has NO null coalescing or optional chaining
// Must be explicit - this is intentional design

// Short-circuit works normally
func isValidUser(user *User) bool {
    return user != nil && user.IsActive()
}

// No ternary operator in Go - must use if/else
func getDisplayName(user *User) string {
    if user != nil && user.Nickname != "" {
        return user.Nickname
    }
    if user != nil && user.Username != "" {
        return user.Username
    }
    return "Anonymous"
}

// Helper function pattern (common in Go)
func coalesce(values ...string) string {
    for _, v := range values {
        if v != "" {
            return v
        }
    }
    return ""
}

// Usage
name := coalesce(user.Nickname, user.Username, "Anonymous")
```

#### SQL

```sql
-- COALESCE returns first non-NULL value
SELECT COALESCE(nickname, username, email, 'Anonymous') AS display_name
FROM users;

-- COALESCE with multiple fallbacks
SELECT
    product_name,
    COALESCE(sale_price, regular_price, 0) AS final_price
FROM products;

-- NULLIF returns NULL if two expressions are equal
-- Useful to avoid division by zero
SELECT
    total_sales / NULLIF(num_transactions, 0) AS avg_transaction
FROM daily_stats;
-- If num_transactions = 0, NULLIF returns NULL, and NULL/0 = NULL (safe)

-- CASE WHEN for complex conditions (expression-based)
SELECT
    order_id,
    CASE
        WHEN status = 'shipped' THEN 'On the way'
        WHEN status = 'delivered' THEN 'Complete'
        WHEN status = 'cancelled' THEN 'Cancelled'
        ELSE 'Processing'
    END AS status_text
FROM orders;

-- ⚠️ SQL short-circuit is NOT guaranteed!
-- The optimizer may reorder conditions
SELECT * FROM users
WHERE user_id IS NOT NULL AND expensive_function(user_id) > 0;
-- expensive_function might be called even when user_id IS NULL
-- depending on the database optimizer
```

#### C++

```cpp
// Standard short-circuit
bool isValidUser(User* user) {
    return user != nullptr && user->isActive();
}

// C++17: std::optional with value_or (null coalescing equivalent)
#include <optional>

std::optional<int> getValue();

void example() {
    std::optional<int> opt = getValue();

    // value_or provides default if empty
    int result = opt.value_or(42);  // 42 if opt is empty

    // Chaining with transform (C++23) or map
    auto doubled = opt.transform([](int x) { return x * 2; });
}

// C++17: if with initializer (prevents scope pollution)
void processUser(UserRepository& repo, int userId) {
    if (auto user = repo.find(userId); user != nullptr) {
        // user only exists in this scope
        processActiveUser(user);
    }
    // user not accessible here - clean!
}

// C++17: Structured bindings with optional
if (auto [found, value] = map.find(key); found) {
    use(value);
}
```

#### Spark (PySpark & Scala)

```python
# PySpark: Column-based operations

from pyspark.sql import functions as F

# coalesce - first non-null column value
df = df.withColumn(
    "display_name",
    F.coalesce(F.col("nickname"), F.col("username"), F.lit("Anonymous"))
)

# when/otherwise - conditional expressions (like SQL CASE)
df = df.withColumn(
    "status_text",
    F.when(F.col("status") == "shipped", "On the way")
     .when(F.col("status") == "delivered", "Complete")
     .when(F.col("status") == "cancelled", "Cancelled")
     .otherwise("Processing")
)

# ⚠️ Python & and | don't short-circuit for columns!
# Use separate filter operations for clarity

# ❌ Confusing - bitwise operators on columns
df.filter((F.col("a") > 0) & (F.col("b") > 0))

# ✅ Clearer - chained filters
df.filter(F.col("a") > 0).filter(F.col("b") > 0)

# Short-circuit in driver code (Python level)
def process_row(row):
    return row.value and row.value > 0  # Standard Python short-circuit
```

```scala
// Scala Spark: Expression-based

import org.apache.spark.sql.functions._

// coalesce
val df2 = df.withColumn(
  "display_name",
  coalesce(col("nickname"), col("username"), lit("Anonymous"))
)

// when/otherwise
val df3 = df.withColumn(
  "status_text",
  when(col("status") === "shipped", "On the way")
    .when(col("status") === "delivered", "Complete")
    .when(col("status") === "cancelled", "Cancelled")
    .otherwise("Processing")
)

// Scala Option - functional null safety
val opt: Option[Int] = Some(42)
val result = opt.getOrElse(0)  // 42
val empty: Option[Int] = None
val result2 = empty.getOrElse(0)  // 0

// Option chaining with map/flatMap
case class User(name: String, address: Option[Address])
case class Address(city: Option[String])

def getCity(user: Option[User]): Option[String] = {
  user.flatMap(_.address).flatMap(_.city)
}

// Or with for-comprehension (like optional chaining)
def getCityAlt(user: Option[User]): Option[String] = {
  for {
    u <- user
    a <- u.address
    c <- a.city
  } yield c
}
```

---

### Pattern 3: Optional Chaining (Critical for TypeScript/OSDK)

#### TypeScript (Most Important for Palantir!)

```typescript
// The problem: Deep property access can fail
interface User {
    profile?: {
        address?: {
            city?: string;
            coordinates?: {
                lat: number;
                lng: number;
            };
        };
    };
}

// ❌ OLD WAY: Verbose null checking
function getCityOld(user: User | null): string | undefined {
    if (user &&
        user.profile &&
        user.profile.address &&
        user.profile.address.city) {
        return user.profile.address.city;
    }
    return undefined;
}

// ✅ MODERN: Optional chaining (?.)
function getCity(user: User | null): string | undefined {
    return user?.profile?.address?.city;
}

// Optional chaining with method calls
interface Api {
    getUser?: () => User | undefined;
}

const api: Api = {};
const user = api.getUser?.();  // undefined if getUser doesn't exist

// Optional chaining with bracket notation
const key = "city";
const city = user?.profile?.address?.[key];

// Combining ?. and ?? for defaults
function getCityWithDefault(user: User | null): string {
    return user?.profile?.address?.city ?? "Unknown";
}

// ⚠️ IMPORTANT: ?. short-circuits the entire chain
const coords = user?.profile?.address?.coordinates;
// If any part is null/undefined, coords is undefined
// coordinates.lat is NOT accessed if chain breaks

// Real OSDK Example (Palantir Foundry)
interface OntologyObject {
    properties?: {
        [key: string]: unknown;
    };
    links?: {
        relatedObjects?: () => Promise<OntologyObject[]>;
    };
}

async function getRelatedObjectProperty(
    obj: OntologyObject | null,
    propertyName: string
): Promise<unknown | undefined> {
    const related = await obj?.links?.relatedObjects?.();
    return related?.[0]?.properties?.[propertyName];
}
```

#### Java (Using Optional)

```java
// Java doesn't have ?. but has Optional<T>

// ❌ NULL-CHECKING HELL
public String getCityOld(User user) {
    if (user != null) {
        Profile profile = user.getProfile();
        if (profile != null) {
            Address address = profile.getAddress();
            if (address != null) {
                return address.getCity();
            }
        }
    }
    return null;
}

// ✅ USING OPTIONAL: Functional chaining
public Optional<String> getCity(User user) {
    return Optional.ofNullable(user)
        .map(User::getProfile)
        .map(Profile::getAddress)
        .map(Address::getCity);
}

// With default value
public String getCityOrDefault(User user) {
    return Optional.ofNullable(user)
        .map(User::getProfile)
        .map(Profile::getAddress)
        .map(Address::getCity)
        .orElse("Unknown");
}

// ⚠️ orElse vs orElseGet - IMPORTANT DISTINCTION
public String example(User user) {
    // orElse: Default is ALWAYS computed (even if not needed)
    return getCity(user).orElse(computeExpensiveDefault());

    // orElseGet: Default computed ONLY if needed (lazy)
    return getCity(user).orElseGet(() -> computeExpensiveDefault());
}

// Interview question: What's printed?
public void orElseVsOrElseGet() {
    Optional<String> opt = Optional.of("value");

    // This PRINTS "Computing..." even though value exists!
    String result1 = opt.orElse(expensiveCall());

    // This does NOT print "Computing..." - lazy evaluation
    String result2 = opt.orElseGet(() -> expensiveCall());
}

private String expensiveCall() {
    System.out.println("Computing...");
    return "default";
}
```

#### Python (No Native Optional Chaining)

```python
# Python has no ?. operator - must use alternatives

# Option 1: getattr with default
def get_city(user):
    profile = getattr(user, 'profile', None)
    address = getattr(profile, 'address', None) if profile else None
    city = getattr(address, 'city', None) if address else None
    return city

# Option 2: try/except (Pythonic for "ask forgiveness")
def get_city_eafp(user):
    try:
        return user.profile.address.city
    except AttributeError:
        return None

# Option 3: Using dict.get for nested dicts
def get_nested(data, *keys, default=None):
    """Safely get nested dictionary values."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
        if data is None:
            return default
    return data

# Usage
user_data = {"profile": {"address": {"city": "Seoul"}}}
city = get_nested(user_data, "profile", "address", "city")

# Option 4: Third-party library (glom)
# pip install glom
from glom import glom, Coalesce

city = glom(user_data, "profile.address.city", default=None)

# Python 3.10+: match statement for complex patterns
def process_user(user):
    match user:
        case {"profile": {"address": {"city": city}}}:
            return f"User from {city}"
        case {"profile": {"address": _}}:
            return "User with address but no city"
        case _:
            return "User with incomplete profile"
```

---

### Pattern 4: Expression-Based Conditionals

#### Java

```java
// Ternary operator (only conditional expression)
int max = a > b ? a : b;

// ❌ Common mistake: Nested ternaries are hard to read
String grade = score >= 90 ? "A"
             : score >= 80 ? "B"
             : score >= 70 ? "C"
             : score >= 60 ? "D"
             : "F";

// ✅ Better: Use a method
public String getGrade(int score) {
    if (score >= 90) return "A";
    if (score >= 80) return "B";
    if (score >= 70) return "C";
    if (score >= 60) return "D";
    return "F";
}

// Java 14+: Switch expressions!
String dayType = switch (day) {
    case MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY -> "Weekday";
    case SATURDAY, SUNDAY -> "Weekend";
};

// Switch expression with yield (for blocks)
String description = switch (status) {
    case ACTIVE -> "User is active";
    case INACTIVE -> {
        logInactiveUser();
        yield "User is inactive";
    }
    case BANNED -> "User is banned";
};
```

#### Python

```python
# Conditional expression (ternary)
max_val = a if a > b else b

# Inline if in list comprehension
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# Multiple conditions - use function for clarity
def get_grade(score):
    return (
        "A" if score >= 90 else
        "B" if score >= 80 else
        "C" if score >= 70 else
        "D" if score >= 60 else
        "F"
    )

# Dictionary-based dispatch (expression-like)
def get_day_type(day):
    return {
        "Monday": "Weekday",
        "Tuesday": "Weekday",
        "Wednesday": "Weekday",
        "Thursday": "Weekday",
        "Friday": "Weekday",
        "Saturday": "Weekend",
        "Sunday": "Weekend",
    }.get(day, "Unknown")

# Python 3.10+: match statement (pattern matching)
def describe_point(point):
    match point:
        case (0, 0):
            return "Origin"
        case (0, y):
            return f"On Y-axis at {y}"
        case (x, 0):
            return f"On X-axis at {x}"
        case (x, y):
            return f"Point at ({x}, {y})"
        case _:
            return "Not a point"
```

#### TypeScript

```typescript
// Ternary
const max = a > b ? a : b;

// Nullish coalescing as expression
const displayName = user.name ?? "Anonymous";

// Immediately Invoked Function Expression (IIFE) for complex logic
const result = (() => {
    if (condition1) return "A";
    if (condition2) return "B";
    return "C";
})();

// Object lookup pattern (expression-based)
const dayType: Record<string, string> = {
    Monday: "Weekday",
    Tuesday: "Weekday",
    // ...
};
const type = dayType[day] ?? "Unknown";

// Type narrowing with ternary
type Status = "active" | "inactive" | "banned";

const message = (status: Status): string =>
    status === "active" ? "Welcome!" :
    status === "inactive" ? "Please verify email" :
    "Access denied";
```

#### Go

```go
// Go has NO ternary operator by design
// Must use if/else

// ❌ This doesn't exist in Go
// max := a > b ? a : b

// ✅ Must use if/else
var max int
if a > b {
    max = a
} else {
    max = b
}

// Or use a function
func Max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

// Generic max (Go 1.18+)
func Max[T constraints.Ordered](a, b T) T {
    if a > b {
        return a
    }
    return b
}

// Switch as expression (sort of)
func getDayType(day string) string {
    switch day {
    case "Monday", "Tuesday", "Wednesday", "Thursday", "Friday":
        return "Weekday"
    case "Saturday", "Sunday":
        return "Weekend"
    default:
        return "Unknown"
    }
}
```

#### C++

```cpp
// Ternary operator
int max = a > b ? a : b;

// C++17: Constexpr if (compile-time branching)
template<typename T>
auto getValue(T t) {
    if constexpr (std::is_pointer_v<T>) {
        return *t;  // Dereference if pointer
    } else {
        return t;   // Return value directly
    }
}

// C++17: if with initializer
if (auto it = map.find(key); it != map.end()) {
    return it->second;
}
return defaultValue;

// std::visit for variant (type-safe union)
std::variant<int, double, std::string> v = 42;

std::string result = std::visit([](auto&& arg) -> std::string {
    using T = std::decay_t<decltype(arg)>;
    if constexpr (std::is_same_v<T, int>) {
        return "int: " + std::to_string(arg);
    } else if constexpr (std::is_same_v<T, double>) {
        return "double: " + std::to_string(arg);
    } else {
        return "string: " + arg;
    }
}, v);
```

---

### Pattern 5: Fail-Fast vs Defensive Programming

#### The Philosophy Divide

| Approach | Philosophy | When to Use |
|----------|------------|-------------|
| **Fail-Fast** | Crash immediately on invalid state | Development, libraries, APIs |
| **Defensive** | Handle all possible errors gracefully | User-facing apps, critical systems |

#### Java: Fail-Fast Examples

```java
// Fail-fast: Validate at entry points
public class User {
    private final String name;
    private final int age;

    public User(String name, int age) {
        // Fail-fast: Don't allow invalid objects to exist
        this.name = Objects.requireNonNull(name, "name cannot be null");
        if (age < 0 || age > 150) {
            throw new IllegalArgumentException("Invalid age: " + age);
        }
        this.age = age;
    }
}

// Java assert (disabled by default, enable with -ea)
public void process(Order order) {
    assert order != null : "order should never be null here";
    assert order.getItems().size() > 0 : "empty order reached processor";
    // ...
}

// Guava Preconditions (popular library)
import static com.google.common.base.Preconditions.*;

public void transfer(Account from, Account to, BigDecimal amount) {
    checkNotNull(from, "from account is null");
    checkNotNull(to, "to account is null");
    checkArgument(amount.compareTo(BigDecimal.ZERO) > 0,
                  "amount must be positive: %s", amount);
    // Now safe to proceed
}
```

#### Python: Fail-Fast Examples

```python
# Fail-fast with assertions
def divide(a: float, b: float) -> float:
    assert b != 0, "Cannot divide by zero"
    return a / b

# Fail-fast with explicit exceptions
def create_user(name: str, age: int) -> User:
    if not name:
        raise ValueError("name cannot be empty")
    if not isinstance(age, int) or age < 0:
        raise ValueError(f"invalid age: {age}")
    return User(name, age)

# Pydantic (validation library) - auto fail-fast
from pydantic import BaseModel, validator, Field

class User(BaseModel):
    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0, le=150)

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('name cannot be blank')
        return v.strip()

# This raises ValidationError automatically
user = User(name="", age=-1)  # Fails fast!
```

#### TypeScript: Fail-Fast Examples

```typescript
// Type guards for fail-fast
function assertNonNull<T>(value: T | null | undefined, message: string): asserts value is T {
    if (value === null || value === undefined) {
        throw new Error(message);
    }
}

function processUser(user: User | null): void {
    assertNonNull(user, "user cannot be null");
    // TypeScript now knows user is User (not null)
    console.log(user.name);
}

// Zod (validation library) - schema-based fail-fast
import { z } from 'zod';

const UserSchema = z.object({
    name: z.string().min(1),
    age: z.number().int().min(0).max(150),
    email: z.string().email(),
});

type User = z.infer<typeof UserSchema>;

// Fails fast with detailed error
const user = UserSchema.parse({ name: "", age: -1, email: "bad" });
```

#### Go: Explicit Error Handling (Fail-Fast Culture)

```go
// Go's philosophy: Handle errors explicitly, fail when appropriate

// Fail-fast: Return error instead of continuing with bad state
func createUser(name string, age int) (*User, error) {
    if name == "" {
        return nil, errors.New("name cannot be empty")
    }
    if age < 0 || age > 150 {
        return nil, fmt.Errorf("invalid age: %d", age)
    }
    return &User{Name: name, Age: age}, nil
}

// Panic for programming errors (fail-fast in development)
func mustCreateUser(name string, age int) *User {
    user, err := createUser(name, age)
    if err != nil {
        panic(err)  // Use panic only for unrecoverable errors
    }
    return user
}

// Convention: Must* functions panic, regular functions return error
func MustCompile(pattern string) *Regexp  // Panics on bad pattern
func Compile(pattern string) (*Regexp, error)  // Returns error
```

---

## Section 3: Design Philosophy Links (공식 문서)

### Official Documentation

| Language | Resource | URL |
|----------|----------|-----|
| **Java** | Optional Documentation | https://docs.oracle.com/javase/8/docs/api/java/util/Optional.html |
| **Java** | Switch Expressions (14+) | https://openjdk.org/jeps/361 |
| **Python** | Boolean Operations | https://docs.python.org/3/reference/expressions.html#boolean-operations |
| **Python** | Match Statement (3.10+) | https://docs.python.org/3/reference/compound_stmts.html#the-match-statement |
| **TypeScript** | Optional Chaining | https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#optional-chaining |
| **TypeScript** | Nullish Coalescing | https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-7.html#nullish-coalescing |
| **Go** | Effective Go - Control | https://go.dev/doc/effective_go#control-structures |
| **SQL** | COALESCE (PostgreSQL) | https://www.postgresql.org/docs/current/functions-conditional.html#FUNCTIONS-COALESCE-NVL-IFNULL |
| **C++** | std::optional | https://en.cppreference.com/w/cpp/utility/optional |
| **C++** | if with initializer | https://en.cppreference.com/w/cpp/language/if#If_statements_with_initializer |
| **Spark** | when/otherwise | https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.functions.when.html |

### Design Philosophy Articles

- **Martin Fowler - Replace Nested Conditional with Guard Clauses**: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
- **Google Java Style Guide**: https://google.github.io/styleguide/javaguide.html
- **Effective Go**: https://go.dev/doc/effective_go
- **TypeScript Do's and Don'ts**: https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html

---

## Section 4: Palantir Context Hint (팔란티어 맥락)

### TypeScript Optional Chaining in OSDK

**Foundry's OSDK (Ontology SDK)** heavily uses TypeScript optional chaining because:

1. **Ontology objects may have optional properties**
2. **Links between objects may not exist**
3. **API responses can be partially populated**

```typescript
// OSDK Pattern: Accessing linked objects safely
import { OntologyObject } from "@foundry/ontology-api";

interface Employee extends OntologyObject {
    properties: {
        name: string;
        department?: string;
        managerId?: string;
    };
    links: {
        manager?: () => Promise<Employee | null>;
        reports?: () => Promise<Employee[]>;
    };
}

// ✅ CORRECT: Using optional chaining throughout
async function getManagerName(employee: Employee | null): Promise<string> {
    const manager = await employee?.links?.manager?.();
    return manager?.properties?.name ?? "No Manager";
}

// ✅ CORRECT: Handling array of linked objects
async function getReportCount(employee: Employee | null): Promise<number> {
    const reports = await employee?.links?.reports?.();
    return reports?.length ?? 0;
}

// ❌ INCORRECT: Not handling nullish values
async function getManagerNameBad(employee: Employee): Promise<string> {
    // This will crash if any link is missing!
    const manager = await employee.links.manager();
    return manager.properties.name;
}
```

### Interview Questions by Topic

#### 1. JavaScript/TypeScript: `??` vs `||`

**Question**: What is the output of this code?

```typescript
const a = 0 || "default";
const b = 0 ?? "default";
const c = "" || "default";
const d = "" ?? "default";
console.log(a, b, c, d);
```

**Answer**: `"default" 0 "default" ""`

**Explanation**:
- `||` returns first **truthy** value (0 and "" are falsy)
- `??` returns first **non-nullish** value (only null/undefined trigger it)

---

#### 2. Java: `orElse` vs `orElseGet`

**Question**: What's the difference and when does it matter?

```java
Optional<String> opt = Optional.of("value");
String a = opt.orElse(expensiveComputation());      // Line A
String b = opt.orElseGet(() -> expensiveComputation()); // Line B
```

**Answer**:
- Line A: `expensiveComputation()` is **always called** (eager evaluation)
- Line B: `expensiveComputation()` is **only called if opt is empty** (lazy evaluation)

**When it matters**: When the default computation is expensive, has side effects, or throws exceptions.

---

#### 3. Python's `or` Trap

**Question**: What does this print?

```python
def get_count(user_input):
    count = user_input or 10
    return count

print(get_count(0))
print(get_count(None))
print(get_count(""))
```

**Answer**: `10 10 10`

**Explanation**: Python's `or` returns first truthy value. `0`, `None`, and `""` are all falsy!

**Fix**:
```python
def get_count(user_input):
    return 10 if user_input is None else user_input
```

---

#### 4. Go's Explicit Philosophy

**Question**: Why doesn't Go have a ternary operator or null coalescing?

**Answer**: Go's design philosophy values:
1. **Readability over brevity**: Explicit if/else is clearer
2. **One obvious way**: No multiple ways to do the same thing
3. **Explicit error handling**: Forces you to handle all cases
4. **Simplicity**: Fewer language features = easier to learn/read

---

#### 5. SQL COALESCE vs NULLIF

**Question**: How do you safely calculate average avoiding division by zero?

```sql
-- Given: sales table with total_amount and num_orders
```

**Answer**:
```sql
SELECT
    date,
    total_amount / NULLIF(num_orders, 0) AS avg_order_value
FROM sales;
```

**Explanation**: `NULLIF(num_orders, 0)` returns NULL when `num_orders = 0`, and `anything / NULL = NULL` (safe, no error).

---

#### 6. TypeScript Optional Chaining Deep Dive

**Question**: What happens here if `user` is null?

```typescript
const city = user?.profile?.address?.city?.toUpperCase();
```

**Answer**: `city` is `undefined`. The chain short-circuits at `user?.` and doesn't throw.

**Follow-up**: What if `city` exists but is an empty string?

**Answer**: `city` would be `""` (empty string), and `"".toUpperCase()` returns `""`. No error.

---

#### 7. C++17 if with Initializer

**Question**: What's the benefit of this syntax?

```cpp
if (auto it = map.find(key); it != map.end()) {
    return it->second;
}
```

**Answer**:
1. **Scope limitation**: `it` only exists in the if-else block
2. **No variable pollution**: Can't accidentally use `it` later
3. **Clear intent**: Initialization and condition in one statement

---

#### 8. Short-Circuit Evaluation Order

**Question**: In which cases is `expensiveCheck()` NOT called?

```javascript
const result1 = false && expensiveCheck();
const result2 = true || expensiveCheck();
const result3 = null ?? expensiveCheck();
const result4 = 0 ?? expensiveCheck();
```

**Answer**:
- `result1`: NOT called (false && ... short-circuits)
- `result2`: NOT called (true || ... short-circuits)
- `result3`: IS called (null is nullish)
- `result4`: NOT called (0 is not nullish, only null/undefined are)

---

### Coding Challenge: Refactor to Guard Clauses

**Given this code, refactor using guard clauses**:

```typescript
function processPayment(user: User | null, order: Order | null): Result {
    if (user !== null) {
        if (user.isActive) {
            if (order !== null) {
                if (order.items.length > 0) {
                    if (user.balance >= order.total) {
                        return processTransaction(user, order);
                    } else {
                        return { error: "Insufficient balance" };
                    }
                } else {
                    return { error: "Empty order" };
                }
            } else {
                return { error: "No order provided" };
            }
        } else {
            return { error: "User inactive" };
        }
    } else {
        return { error: "No user provided" };
    }
}
```

**Solution**:

```typescript
function processPayment(user: User | null, order: Order | null): Result {
    if (!user) return { error: "No user provided" };
    if (!user.isActive) return { error: "User inactive" };
    if (!order) return { error: "No order provided" };
    if (order.items.length === 0) return { error: "Empty order" };
    if (user.balance < order.total) return { error: "Insufficient balance" };

    return processTransaction(user, order);
}
```

---

## Section 5: Cross-References (관련 개념)

### Direct Dependencies

| Concept ID | Title | Relationship |
|------------|-------|--------------|
| **F30** | Operator Semantics | Prerequisite - `&&`, `\|\|`, `?:` operators |
| **F32** | Null/Optional Handling | Prerequisite - Null safety concepts |
| **F33** | Error Handling Patterns | Related - fail-fast vs exception handling |
| **F35** | Functional Patterns | Extension - monadic composition |

### Broader Context

| Concept ID | Title | Relationship |
|------------|-------|--------------|
| **F10** | Type Systems | Foundation - nullability in type systems |
| **F20** | Function Design | Application - early return in functions |
| **F40** | Code Readability | Goal - clean code through guard clauses |
| **F50** | Performance Patterns | Impact - short-circuit evaluation |

### Pattern Relationships

```
F30 Operators
    ↓
F32 Null Handling → F34 Control Flow Expressions → F35 Functional Patterns
    ↓                                                    ↓
F33 Error Handling ←─────────────────────────────────────┘
```

### Study Path Recommendations

1. **Before F34**: Master F30 (operator semantics) and F32 (null handling)
2. **After F34**: Move to F35 (functional patterns like map/flatMap chains)
3. **Interview Prep**: Focus on TypeScript `??` vs `||` and Java `Optional` patterns
4. **OSDK Focus**: Deep dive into TypeScript optional chaining examples

---

## Summary: Key Takeaways

### The Big Picture

1. **Guard clauses** flatten code and make the happy path clear
2. **Short-circuit evaluation** is both a performance optimization and a safety feature
3. **Null coalescing** differs across languages - know the semantics!
4. **Expression-oriented code** is more composable and often clearer
5. **Fail-fast** catches bugs early; use it in development and APIs

### Language-Specific Memory Aids

| Language | Remember This |
|----------|---------------|
| **Java** | `Optional.orElseGet()` is lazy, `orElse()` is eager |
| **Python** | `or` is falsy-based, not null-based (trap for 0 and "") |
| **TypeScript** | `??` for null, `\|\|` for falsy - huge difference! |
| **Go** | No shortcuts - be explicit, that's the point |
| **SQL** | `COALESCE` + `NULLIF` = safe division |
| **C++** | `std::optional::value_or()` + C++17 if-initializer |
| **Spark** | `coalesce()` for columns, `when().otherwise()` for conditions |

### Interview Checklist

- [ ] Can explain `??` vs `||` in TypeScript with examples
- [ ] Know Java `orElse` vs `orElseGet` performance implications
- [ ] Understand Python `or` trap with 0 and empty strings
- [ ] Can refactor nested conditionals to guard clauses
- [ ] Know why Go doesn't have ternary operator
- [ ] Can use SQL `COALESCE` and `NULLIF` together
- [ ] Understand short-circuit evaluation order

---

*Last Updated: 2026-01-18*
*Version: 1.0*
*Category: Control Flow / Code Style*
